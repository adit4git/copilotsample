"""
resolver.py  —  CLASSIC engine
==============================
Engine A: the model is a *classifier/extractor*. One LLM call per turn returns
free-form JSON {sub_intent, entities, confidence, ambiguous_between}; this file
commits the skill, accumulates entities, and hands off to the shared `gate.py`
to decide the action and (maybe) execute.

The model NEVER calls a skill here. `llm.extract()` only describes; `gate.decide()`
disposes. Contrast with `resolver_hybrid.py`, which lets the model emit a native
tool call — but routes it through the exact same gate.

Session store and the public entry points (`get_session`, `resolve_turn`,
`reset`) are shared across both engines via this module.
"""

from __future__ import annotations
from typing import Any, Optional

import gate
from gate import SessionState
from llm import extract

# One in-memory session store, shared by both engines. A session remembers which
# engine it is using so the UI toggle is sticky per conversation.
SESSIONS: dict[str, SessionState] = {}


def get_session(session_id: str, engine: str = "classic") -> SessionState:
    if session_id not in SESSIONS:
        SESSIONS[session_id] = SessionState(session_id=session_id, engine=engine)
    return SESSIONS[session_id]


def reset(session_id: str) -> None:
    SESSIONS.pop(session_id, None)


def resolve_turn(state: SessionState, advisor_text: str,
                 file_text: Optional[str] = None) -> dict:
    """Process one advisor turn with the CLASSIC (JSON-extraction) engine."""
    if advisor_text:
        state.messages.append({"role": "user", "content": advisor_text})
    if file_text:
        state.last_file_text = file_text

    # If we're waiting on a yes/no for a side-effecting skill, handle it first.
    confirm_signal = False
    if state.awaiting_confirm:
        yn = gate.read_confirmation(advisor_text)
        if yn is True:
            confirm_signal = True
        elif yn is False:
            state.awaiting_confirm = False
            state.skill_id = None
            state.entities = {}
            msg = "Cancelled. What would you like to do instead?"
            state.messages.append({"role": "assistant", "content": msg})
            action = {"action": "FALLBACK", "message": msg,
                      "state": gate.public_state(state)}
            _record(state, advisor_text, {"note": "user cancelled"}, action)
            return action

    # 1. Model describes the turn (never executes).
    r = extract(state.messages, file_text=file_text or state.last_file_text)

    # 2. Commit / switch skill, then accumulate entities.
    gate.commit_skill(state, r.get("sub_intent"), r.get("confidence", 0.0))
    gate.merge_entities(state, r.get("entities"))

    # 3. Shared gate decides and (maybe) executes.
    action = gate.decide(state,
                         confidence=r.get("confidence", 0.0),
                         ambiguous_between=r.get("ambiguous_between") or [],
                         reasoning=r.get("reasoning", ""),
                         confirm_signal=confirm_signal)

    if action.get("message"):
        state.messages.append({"role": "assistant", "content": action["message"]})
    _record(state, advisor_text, r, action)
    return action


def _record(state: SessionState, advisor_text: str, resolution: dict,
            action: dict) -> None:
    state.trace.append({
        "engine": "classic",
        "advisor_text": advisor_text,
        "llm_resolution": resolution,
        "skill_id": state.skill_id,
        "entities": dict(state.entities),
        "action": action["action"],
    })
