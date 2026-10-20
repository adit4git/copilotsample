"""
main.py
=======
FastAPI backend for the wealth-management resolution copilot POC.

Supports TWO resolution engines, selectable per request (sticky per session):
  - "classic" : model returns JSON; code routes & gates & executes.
  - "hybrid"  : model emits a native tool call (proposal); the SAME code gates &
                executes. Tool calling for structured output, control kept in code.

Endpoints
---------
GET  /                         -> serves the chat UI
POST /api/message              -> one advisor turn; body includes engine
POST /api/upload               -> upload a file + a turn; form includes engine
GET  /api/catalog              -> the skill catalog (reference panel)
POST /api/reset                -> clear a session
GET  /api/health               -> provider/mode info

Run (from app/):  uvicorn main:app --reload --port 8000
"""

from __future__ import annotations
import os
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import resolver                 # classic engine + shared session store
import resolver_hybrid          # hybrid engine (shares the store)
import files as filemod
from schema import SKILLS, INTENTS
from gate import SIDE_EFFECTING

APP_DIR = Path(__file__).parent
STATIC_DIR = APP_DIR.parent / "static"
UPLOAD_DIR = APP_DIR.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="WM Resolution Copilot (POC)")


def _engine(name: str):
    """Return (get_session, resolve_turn) for the requested engine."""
    if (name or "classic").lower() == "hybrid":
        return resolver_hybrid.get_session, resolver_hybrid.resolve_turn
    return resolver.get_session, resolver.resolve_turn


class MessageIn(BaseModel):
    session_id: str | None = None
    text: str = ""
    engine: str = "classic"


@app.get("/", response_class=HTMLResponse)
def index():
    return (STATIC_DIR / "index.html").read_text()


@app.get("/api/health")
def health():
    provider = os.getenv("PROVIDER", "anthropic").lower()
    key = bool(os.getenv("ANTHROPIC_API_KEY") if provider == "anthropic"
               else os.getenv("OPENAI_API_KEY"))
    return {"provider": provider, "live_llm": key,
            "mode": "live" if key else "mock",
            "engines": ["classic", "hybrid"],
            "model": os.getenv("ANTHROPIC_MODEL" if provider == "anthropic"
                               else "OPENAI_MODEL", "default")}


@app.get("/api/catalog")
def catalog():
    return {"intents": INTENTS, "skills": [
        {"id": s.id, "intent": s.intent, "title": s.title,
         "description": s.description,
         "required_slots": [sl.name for sl in s.required_slots],
         "optional_slots": [sl.name for sl in s.slots if not sl.required],
         "side_effecting": s.id in SIDE_EFFECTING,
         "examples": s.examples}
        for s in SKILLS]}


@app.post("/api/message")
def message(inp: MessageIn):
    sid = inp.session_id or uuid.uuid4().hex[:12]
    get_session, resolve_turn = _engine(inp.engine)
    state = get_session(sid)
    action = resolve_turn(state, inp.text)
    action["session_id"] = sid
    action["engine"] = state.engine
    action["trace"] = state.trace[-1] if state.trace else None
    return JSONResponse(action)


@app.post("/api/upload")
async def upload(session_id: str = Form(...), file: UploadFile = File(...),
                 text: str = Form(""), engine: str = Form("classic")):
    sid = session_id or uuid.uuid4().hex[:12]
    dest = UPLOAD_DIR / f"{sid}_{file.filename}"
    dest.write_bytes(await file.read())
    extracted = filemod.extract_text(str(dest))

    get_session, resolve_turn = _engine(engine)
    state = get_session(sid)
    advisor_text = text or f"[uploaded {file.filename}]"
    action = resolve_turn(state, advisor_text, file_text=extracted)
    action["session_id"] = sid
    action["engine"] = state.engine
    action["file"] = {"name": file.filename, "extracted_preview": extracted[:600]}
    action["trace"] = state.trace[-1] if state.trace else None
    return JSONResponse(action)


@app.post("/api/reset")
def reset(inp: MessageIn):
    if inp.session_id:
        resolver.reset(inp.session_id)
    return {"ok": True}


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
