import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import os

from connectors.sqlite import SQLiteConnector
from connectors.postgres_db import PostGresConnector
from monitoring.sql_health import SQLHealthChecker
from monitoring.scheduler import HealthMonitor
from monitoring.storage import FileHealthStorage


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ACTIVE_CONNECTOR = None
ACTIVE_MONITOR = None
SCHEMA_FILE = "schema_cache.json"


class URIConnectRequest(BaseModel):
    uri: str


def save_schema(schema: dict):
    with open(SCHEMA_FILE, "w") as f:
        json.dump(schema, f, indent=2)


def load_schema():
    if not os.path.exists(SCHEMA_FILE):
        return None
    with open(SCHEMA_FILE, "r") as f:
        return json.load(f)


def start_monitor(connector):
    global ACTIVE_MONITOR

    storage = FileHealthStorage("health_logs.jsonl")
    checker = SQLHealthChecker(connector)

    monitor = HealthMonitor(
        checker=checker,
        storage=storage,
        light_interval=600,
        deep_interval=86400
    )

    monitor.start()
    ACTIVE_MONITOR = monitor


def stop_monitor():
    global ACTIVE_MONITOR
    if ACTIVE_MONITOR:
        ACTIVE_MONITOR.stop()
        ACTIVE_MONITOR = None


# -------------------------------------------------------
# CONNECT VIA URI
# -------------------------------------------------------
@app.post("/api/connect/uri")
async def connect_via_uri(payload: URIConnectRequest):
    global ACTIVE_CONNECTOR

    stop_monitor()

    uri = payload.uri.lower()

    try:
        if uri.startswith("sqlite"):
            connector = SQLiteConnector(uri=payload.uri)
        elif uri.startswith("postgresql"):
            connector = PostGresConnector(uri=payload.uri)
        else:
            raise HTTPException(status_code=400, detail="Unsupported URI type")

        connector.connect()

        schema = connector.extract_schema()
        save_schema(schema)

        checker = SQLHealthChecker(connector)
        health = checker.run_light()

        ACTIVE_CONNECTOR = connector
        start_monitor(connector)

        return {
            "status": "connected",
            "health": health.__dict__
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------------
# CONNECT VIA SQLITE FILE
# -------------------------------------------------------
@app.post("/api/connect/sqlite")
async def connect_sqlite_file(file: UploadFile = File(...)):
    global ACTIVE_CONNECTOR

    stop_monitor()

    if not file.filename.endswith((".db", ".sqlite")):
        raise HTTPException(status_code=400, detail="Invalid SQLite file")

    os.makedirs("uploads", exist_ok=True)
    upload_path = f"uploads/{file.filename}"

    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        connector = SQLiteConnector(filepath=upload_path)
        connector.connect()

        schema = connector.extract_schema()
        save_schema(schema)

        checker = SQLHealthChecker(connector)
        health = checker.run_light()

        ACTIVE_CONNECTOR = connector
        start_monitor(connector)

        return {
            "status": "connected",
            "health": health.__dict__
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------------
# GET STORED SCHEMA
# -------------------------------------------------------
@app.get("/api/schema")
async def get_schema():
    schema = load_schema()
    if not schema:
        raise HTTPException(status_code=404, detail="No schema stored")
    return schema


# -------------------------------------------------------
# DEEP HEALTH CHECK
# -------------------------------------------------------
@app.get("/api/health/deep")
async def deep_health_check():
    if not ACTIVE_CONNECTOR:
        raise HTTPException(status_code=400, detail="No active connection")

    checker = SQLHealthChecker(ACTIVE_CONNECTOR)
    report = checker.run_deep()

    return report.__dict__


# -------------------------------------------------------
# DISCONNECT
# -------------------------------------------------------
@app.post("/api/disconnect")
async def disconnect():
    global ACTIVE_CONNECTOR

    stop_monitor()

    if ACTIVE_CONNECTOR:
        ACTIVE_CONNECTOR.close()
        ACTIVE_CONNECTOR = None

    return {"status": "disconnected"}


@app.on_event("shutdown")
def shutdown_event():
    stop_monitor()
    if ACTIVE_CONNECTOR:
        ACTIVE_CONNECTOR.close()