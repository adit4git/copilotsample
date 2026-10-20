"""
resolver_hybrid.py  —  HYBRID engine
====================================
Engine B: the model emits a native TOOL CALL (skills are exposed as tool schemas
in `llm_tools.py`). We intercept that call as a *proposal* and run it through the
SAME `gate.py` the classic engine uses.

What's different from classic:
  - extraction mechanism: provider-enforced tool arguments instead of free JSON.
  - the trace shows it arrived "via tool_call".

What's identical (on purpose):
  - entity accumulation, the CLARIFY/EXECUTE decision, the confirmation gate for
    side-effecting skills, and the fact that the model never executes a skill —
    a tool call with missing required args becomes a CLARIFY_SLOT, not a run.

This is the hybrid thesis in code: use tool calling for reliable structured
*output*, keep execution *control* in deterministic code.
"""

from __future__ import annotations
from typing import Optional

import gate
from gate import SessionState
from resolver import SESSIONS            # share the single session store
from llm_tools import propose


def get_session(session_id: str) -> SessionState:
    if session_id not in SESSIONS:
        SESSIONS[session_id] = SessionState(session_id=session_id, engine="hybrid")
    SESSIONS[session_id].engine = "hybrid"
    return SESSIONS[session_id]


def resolve_turn(state: SessionState, advisor_text: str,
                 file_text: Optional[str] = None) -> dict:
    """Process one advisor turn with the HYBRID (tool-calling) engine."""
    if advisor_text:
        state.messages.append({"role": "user", "content": advisor_text})
    if file_text:
        state.last_file_text = file_text

    # Side-effect confirmation (same contract as classic).
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

    # 1. Model PROPOSES a tool call (never executes).
    r = propose(state.messages, file_text=file_text or state.last_file_text)

    # 2. Commit / switch skill, accumulate args.
    gate.commit_skill(state, r.get("sub_intent"), r.get("confidence", 0.0))
    gate.merge_entities(state, r.get("entities"))

    # 3. Same shared gate decides and (maybe) executes.
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
        "engine": "hybrid",
        "advisor_text": advisor_text,
        "llm_resolution": resolution,      # includes "via": tool_call / mock_tool_call
        "skill_id": state.skill_id,
        "entities": dict(state.entities),
        "action": action["action"],
    })
