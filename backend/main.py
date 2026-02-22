import os
import shutil
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from connectors.sqlite import SQLiteConnector
from connectors.postgres_db import PostGresConnector
from monitoring.sql_health import SQLHealthChecker
from monitoring.scheduler import HealthMonitor
from monitoring.storage import FileHealthStorage

from exporters import json_exp, markdown_exp, llm_exp, diagram_exp
from exporters.ai_summary import generate_ai_summaries


load_dotenv()

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ACTIVE_CONNECTOR = None
ACTIVE_MONITOR = None


ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", "artifacts")
HEALTH_LOG_FILE = os.getenv("HEALTH_LOG_FILE", "health_logs.jsonl")
AI_ENABLE = os.getenv("AI_ENABLE", "false").lower() == "true"
LIGHT_INTERVAL = int(os.getenv("LIGHT_INTERVAL", 600))
DEEP_INTERVAL = int(os.getenv("DEEP_INTERVAL", 86400))


class URIConnectRequest(BaseModel):
    uri: str


# -------------------------------------------------------
# Core Export Pipeline (Matches app.py)
# -------------------------------------------------------
def run_full_pipeline(connector, db_identifier: str):

    schema = connector.extract_schema()

    # Build output directory
    db_name = os.path.splitext(os.path.basename(db_identifier))[0]
    out_dir = os.path.join(ARTIFACTS_DIR, db_name)
    os.makedirs(out_dir, exist_ok=True)

    # 1️⃣ Schema Exports
    json_exp.export_schema(schema, os.path.join(out_dir, f"{db_name}_schema.json"))
    markdown_exp.export_schema(schema, os.path.join(out_dir, f"{db_name}_schema.md"))
    llm_exp.export_llm_schema(schema, os.path.join(out_dir, f"{db_name}_llm_schema.txt"))
    diagram_exp.export_diagram(schema, os.path.join(out_dir, f"{db_name}_er_diagram"))

    # 2️⃣ Health Checks
    checker = SQLHealthChecker(connector)

    light = checker.run_light()
    json_exp.export_health(light, os.path.join(out_dir, f"{db_name}_health_light.json"))
    markdown_exp.export_health(light, os.path.join(out_dir, f"{db_name}_health_light.md"))

    deep = checker.run_deep()
    json_exp.export_health(deep, os.path.join(out_dir, f"{db_name}_health_deep.json"))
    markdown_exp.export_health(deep, os.path.join(out_dir, f"{db_name}_health_deep.md"))

    # 3️⃣ AI Summaries
    if AI_ENABLE:
        summaries = generate_ai_summaries(schema, quality=deep.metrics["tables"])

        json_exp.export_ai_summary(
            summaries, os.path.join(out_dir, f"{db_name}_ai_summary.json")
        )

        markdown_exp.export_ai_summary(
            summaries, os.path.join(out_dir, f"{db_name}_ai_summary.md")
        )

        markdown_exp.append_ai_summaries_to_schema_md(
            summaries,
            os.path.join(out_dir, f"{db_name}_schema_with_ai.md")
        )

    return {
        "artifacts_dir": out_dir,
        "schema_tables": len(schema["tables"])
    }


# -------------------------------------------------------
# Background Monitor
# -------------------------------------------------------
def start_monitor(connector):
    global ACTIVE_MONITOR

    storage = FileHealthStorage(HEALTH_LOG_FILE)
    checker = SQLHealthChecker(connector)

    monitor = HealthMonitor(
        checker=checker,
        storage=storage,
        light_interval=LIGHT_INTERVAL,
        deep_interval=DEEP_INTERVAL
    )

    monitor.start()
    ACTIVE_MONITOR = monitor


def stop_monitor():
    global ACTIVE_MONITOR
    if ACTIVE_MONITOR:
        ACTIVE_MONITOR.stop()
        ACTIVE_MONITOR = None


# -------------------------------------------------------
# Connect via SQLite Upload
# -------------------------------------------------------
@app.post("/api/connect/sqlite")
async def connect_sqlite(file: UploadFile = File(...)):
    global ACTIVE_CONNECTOR

    stop_monitor()

    os.makedirs("uploads", exist_ok=True)
    upload_path = f"uploads/{file.filename}"

    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    connector = SQLiteConnector(filepath=upload_path)
    connector.connect()

    ACTIVE_CONNECTOR = connector

    result = run_full_pipeline(connector, file.filename)

    start_monitor(connector)

    return {
        "status": "connected",
        "artifacts": result
    }


# -------------------------------------------------------
# Connect via URI
# -------------------------------------------------------
@app.post("/api/connect/uri")
async def connect_uri(payload: URIConnectRequest):
    global ACTIVE_CONNECTOR

    stop_monitor()

    uri = payload.uri.lower()

    if uri.startswith("sqlite"):
        connector = SQLiteConnector(uri=payload.uri)
        db_identifier = connector.engine.url.database
    elif uri.startswith("postgresql"):
        connector = PostGresConnector(uri=payload.uri)
        db_identifier = connector.engine.url.database
    else:
        raise HTTPException(status_code=400, detail="Unsupported URI")

    connector.connect()
    ACTIVE_CONNECTOR = connector

    result = run_full_pipeline(connector, db_identifier)

    start_monitor(connector)

    return {
        "status": "connected",
        "artifacts": result
    }


@app.post("/api/disconnect")
async def disconnect():
    global ACTIVE_CONNECTOR
    stop_monitor()

    if ACTIVE_CONNECTOR:
        ACTIVE_CONNECTOR.close()
        ACTIVE_CONNECTOR = None

    return {"status": "disconnected"}