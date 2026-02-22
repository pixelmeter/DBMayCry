"""
FastAPI server.
Run: uv run chat/api.py
"""

import os
import sys
import uuid
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import FileResponse, PlainTextResponse

sys.path.insert(0, str(Path(__file__).parent.parent))

from chat.agent import answer, list_databases


app = FastAPI(
    title="DB Dictionary Chat API",
    description="Natural language interface over database schemas",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", "artifacts")

# ── JSON session store ────────────────────────────────────────────────────

SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)
MAX_HISTORY = 20


def _session_path(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.json"


def load_session(session_id: str) -> dict:
    path = _session_path(session_id)
    if path.exists():
        return json.loads(path.read_text())
    return {
        "session_id": session_id,
        "db_name": None,
        "created_at": datetime.utcnow().isoformat(),
        "last_active": datetime.utcnow().isoformat(),
        "history": [],
    }


def save_session(session_id: str, data: dict):
    data["last_active"] = datetime.utcnow().isoformat()
    _session_path(session_id).write_text(json.dumps(data, indent=2))


def delete_session(session_id: str):
    path = _session_path(session_id)
    if path.exists():
        path.unlink()


# ── Request/Response Models ─────────────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    db_name: str
    question: str
    session_id: str | None = None  


class ChatResponse(BaseModel):
    answer: str
    query_type: str  # global | relational | specific | conversational
    db_name: str
    session_id: str  # always returned so NextJS can persist it


class NewSessionResponse(BaseModel):
    session_id: str


# ── Endpoints ──────────────────────────────────────────────────────────────────


@app.get("/databases")
def get_databases():
    """Returns list of all ingested databases available for chat."""
    dbs = list_databases()
    return {"databases": dbs}


@app.post("/session", response_model=NewSessionResponse)
def create_session():
    """
    Creates a new chat session and returns a session_id.
    NextJS calls this when user starts a new chat.
    """
    session_id = str(uuid.uuid4())
    save_session(
        session_id,
        {
            "session_id": session_id,
            "db_name": None,
            "created_at": datetime.utcnow().isoformat(),
            "last_active": datetime.utcnow().isoformat(),
            "history": [],
        },
    )
    return {"session_id": session_id}


@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    """Clears history for a session. Call when user clicks 'New Chat'."""
    delete_session(session_id)
    return {"cleared": True, "session_id": session_id}


@app.get("/session/{session_id}/history")
def get_history(session_id: str):
    """Returns full conversation history for a session."""
    if not _session_path(session_id).exists():
        raise HTTPException(status_code=404, detail="Session not found.")
    data = load_session(session_id)
    return {"session_id": session_id, "history": data["history"]}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Main chat endpoint.

    NextJS sends:
        { db_name: "bike_store", question: "...", session_id: "uuid" }

    If session_id is None, a new session is created automatically.

    Returns:
        { answer: "...", query_type: "...", db_name: "...", session_id: "uuid" }
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    available = list_databases()
    if request.db_name not in available:
        raise HTTPException(
            status_code=404,
            detail=f"Database '{request.db_name}' not found. Available: {available}",
        )

    # Create session if not provided
    session_id = request.session_id or str(uuid.uuid4())
    data = load_session(session_id)
    history = data["history"]

    try:
        result = answer(
            db_name=request.db_name,
            question=request.question,
            history=history,
            artifacts_dir=ARTIFACTS_DIR,
        )

        # Append and trim
        history.append({"role": "user", "content": request.question})
        history.append({"role": "assistant", "content": result["answer"]})
        if len(history) > MAX_HISTORY:
            history = history[-MAX_HISTORY:]

        data["history"] = history
        data["db_name"] = request.db_name
        save_session(session_id, data)

        return ChatResponse(session_id=session_id, **result)

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def _artifacts_path(db_name: str) -> Path:
    """Handles both flat and nested artifact structures."""
    nested = Path(ARTIFACTS_DIR) / db_name
    flat = Path(ARTIFACTS_DIR)
    return nested if nested.exists() else flat


@app.get("/docs/{db_name}/files")
def list_artifacts(db_name: str):
    base = _artifacts_path(db_name)
    if not base.exists():
        raise HTTPException(status_code=404, detail="Artifacts directory not found.")
    files = [f.name for f in base.iterdir() if f.name.startswith(db_name) and f.is_file()]
    if not files:
        raise HTTPException(status_code=404, detail=f"No artifacts found for '{db_name}'.")
    return {"db_name": db_name, "files": sorted(files)}


@app.get("/docs/{db_name}/schema")
def get_schema_markdown(db_name: str):
    path = _artifacts_path(db_name) / f"{db_name}_schema.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Schema markdown not found.")
    return PlainTextResponse(path.read_text(), media_type="text/markdown")


@app.get("/docs/{db_name}/schema.json")
def get_schema_json(db_name: str):
    path = _artifacts_path(db_name) / f"{db_name}_schema.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Schema JSON not found.")
    return json.loads(path.read_text())


@app.get("/docs/{db_name}/quality")
def get_quality_markdown(db_name: str):
    path = _artifacts_path(db_name) / f"{db_name}_health_deep.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Quality report not found.")
    return PlainTextResponse(path.read_text(), media_type="text/markdown")


@app.get("/docs/{db_name}/quality.json")
def get_quality_json(db_name: str):
    path = _artifacts_path(db_name) / f"{db_name}_health_deep.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Quality JSON not found.")
    return json.loads(path.read_text())


@app.get("/docs/{db_name}/summary")
def get_ai_summary_markdown(db_name: str):
    path = _artifacts_path(db_name) / f"{db_name}_ai_summary.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="AI summary not found.")
    return PlainTextResponse(path.read_text(), media_type="text/markdown")


@app.get("/docs/{db_name}/summary.json")
def get_ai_summary_json(db_name: str):
    path = _artifacts_path(db_name) / f"{db_name}_ai_summary.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="AI summary JSON not found.")
    return json.loads(path.read_text())


@app.get("/docs/{db_name}/diagram")
def get_er_diagram(db_name: str):
    path = _artifacts_path(db_name) / f"{db_name}_er_diagram.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail="ER diagram not found.")
    return FileResponse(path, media_type="image/png")


@app.get("/docs/{db_name}/llm-schema")
def get_llm_schema(db_name: str):
    path = _artifacts_path(db_name) / f"{db_name}_llm_schema.txt"
    if not path.exists():
        raise HTTPException(status_code=404, detail="LLM schema not found.")
    return PlainTextResponse(path.read_text())


if __name__ == "__main__":
    uvicorn.run("chat.api:app", host="0.0.0.0", port=8000, reload=True)
