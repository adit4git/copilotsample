"""
gate.py
=======
The engine-agnostic resolution gate.

Both resolution engines -- the classic JSON-extraction resolver and the hybrid
tool-calling resolver -- produce the same thing: a committed `skill_id` and an
accumulated `entities` dict on the session. Everything *after* that point is
identical and lives here:

  - slot accounting (which required slots are filled / missing)
  - the decision (CLARIFY_INTENT / CLARIFY_SLOT / EXECUTE / FALLBACK)
  - the confirmation gate for side-effecting skills
  - skill execution dispatch
  - the public state snapshot the UI renders

Keeping this shared is the whole point of the "hybrid" argument: the model may
*propose* a skill (via JSON or via a tool call), but a skill only *runs* when
this deterministic gate says every required slot is present and, for anything
that moves money, the advisor has confirmed. The model never executes directly.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional

from schema import SKILLS_BY_ID, Skill, Slot
import skills_exec

CONFIDENCE_FLOOR = 0.60

# Skills whose execution has real-world side effects. The gate requires an
# explicit advisor confirmation before running these, regardless of engine.
# (In this POC "execution" is mocked, but the gate is where you'd enforce it.)
SIDE_EFFECTING = {
    "portfolio_analysis.drift_rebalance",   # proposes trades
    "planning.cash_flow",                   # proposes raising cash / selling
}


@dataclass
class SessionState:
    """Everything we remember about one advisor conversation."""
    session_id: str
    engine: str = "classic"                                  # classic | hybrid
    messages: list[dict] = field(default_factory=list)       # {role, content}
    skill_id: Optional[str] = None                           # committed sub-intent
    entities: dict[str, Any] = field(default_factory=dict)   # accumulated slots
    pending_slot: Optional[str] = None                       # slot we just asked for
    awaiting_confirm: bool = False                           # gate: side-effect confirm
    last_file_text: Optional[str] = None
    trace: list[dict] = field(default_factory=list)


# --- slot helpers ----------------------------------------------------------
def first_missing_required(skill: Skill, entities: dict) -> Optional[Slot]:
    for slot in skill.slots:
        if slot.required and slot.name not in entities:
            return slot
    return None


def skill_options(ids: list[str]) -> list[dict]:
    out = []
    for sid in ids:
        s = SKILLS_BY_ID.get(sid)
        if s:
            out.append({"id": s.id, "title": s.title, "description": s.description})
    return out


def merge_entities(state: SessionState, entities: dict) -> None:
    """Accumulate; never overwrite a known value with a blank."""
    for k, v in (entities or {}).items():
        if v not in (None, "", []):
            state.entities[k] = v


def commit_skill(state: SessionState, proposed_skill: Optional[str],
                 confidence: float) -> None:
    """Lock or switch the active skill with the intent-switch guard."""
    if not proposed_skill:
        return
    if state.skill_id and proposed_skill != state.skill_id:
        if confidence >= 0.75:                 # genuine intent switch
            state.skill_id = proposed_skill
            state.entities = {}                # new skill, new slot set
            state.awaiting_confirm = False
    elif not state.skill_id:
        state.skill_id = proposed_skill


# --- the decision ----------------------------------------------------------
def decide(state: SessionState, confidence: float,
           ambiguous_between: list[str], reasoning: str = "",
           confirm_signal: bool = False) -> dict:
    """Given committed skill + entities, choose the next action. Pure gate."""
    skill = SKILLS_BY_ID.get(state.skill_id) if state.skill_id else None

    # (a) No usable skill yet.
    if skill is None:
        amb = ambiguous_between or []
        if len(amb) >= 2:
            return {"action": "CLARIFY_INTENT",
                    "message": "I can take this a couple of ways — which did you mean?",
                    "options": skill_options(amb),
                    "state": public_state(state)}
        return {"action": "FALLBACK",
                "message": ("I didn't quite catch what you need. Try e.g. "
                            "“rebalance the Hendersons” or "
                            "“tax-loss harvest candidates for the Kims”."),
                "state": public_state(state)}

    # (b) Low confidence + flagged ambiguity -> confirm the route.
    if ambiguous_between and confidence < CONFIDENCE_FLOOR:
        return {"action": "CLARIFY_INTENT",
                "message": f"Did you want **{skill.title}**, or something else?",
                "options": skill_options(ambiguous_between),
                "state": public_state(state)}

    # (c) Missing a required slot -> ask for exactly one.
    missing = first_missing_required(skill, state.entities)
    if missing:
        state.pending_slot = missing.name
        opts = ([{"id": o, "title": o} for o in missing.options]
                if missing.options else None)
        return {"action": "CLARIFY_SLOT",
                "message": missing.clarify or f"What's the {missing.name}?",
                "slot": missing.name, "options": opts,
                "needs_file": missing.fillable_from_file and missing.name == "document",
                "skill": {"id": skill.id, "title": skill.title},
                "state": public_state(state)}
    state.pending_slot = None

    # (d) Side-effecting skill -> require an explicit confirmation first.
    if skill.id in SIDE_EFFECTING and not state.awaiting_confirm \
            and not confirm_signal:
        state.awaiting_confirm = True
        preview = _confirm_preview(skill, state.entities)
        return {"action": "CONFIRM",
                "message": preview,
                "skill": {"id": skill.id, "title": skill.title},
                "options": [{"id": "__confirm__", "title": "Yes, run it"},
                            {"id": "__cancel__", "title": "Cancel"}],
                "state": public_state(state)}

    # (e) Run the skill.
    state.awaiting_confirm = False
    result = skills_exec.run(skill.id, state.entities, file_text=state.last_file_text)
    return {"action": "EXECUTE",
            "skill": {"id": skill.id, "title": skill.title},
            "message": result["summary"], "result": result,
            "state": public_state(state)}


def _confirm_preview(skill: Skill, entities: dict) -> str:
    who = entities.get("client", "this client")
    if skill.id == "portfolio_analysis.drift_rebalance":
        return (f"Ready to generate a rebalance proposal for **{who}** "
                f"({entities.get('tax_aware', 'tax-aware')}). This will produce "
                f"trade orders for your review. Run it?")
    if skill.id == "planning.cash_flow":
        return (f"Ready to build a cash-raising plan for **{who}** of "
                f"{entities.get('amount', 'the requested amount')}. This may "
                f"propose selling positions. Run it?")
    return f"Ready to run **{skill.title}** for {who}. Proceed?"


def public_state(state: SessionState) -> dict:
    skill = SKILLS_BY_ID.get(state.skill_id) if state.skill_id else None
    required = [s.name for s in skill.required_slots] if skill else []
    filled = dict(state.entities)
    missing = [n for n in required if n not in filled]
    return {"session_id": state.session_id, "engine": state.engine,
            "skill_id": state.skill_id,
            "skill_title": skill.title if skill else None,
            "entities": filled, "required_slots": required,
            "missing_slots": missing, "awaiting_confirm": state.awaiting_confirm}


# --- confirmation parsing (shared) ----------------------------------------
_YES = {"yes", "y", "yes, run it", "run it", "confirm", "go", "do it",
        "__confirm__", "proceed", "ok", "okay"}
_NO = {"no", "n", "cancel", "stop", "__cancel__", "nevermind", "never mind"}


def read_confirmation(text: str) -> Optional[bool]:
    t = (text or "").strip().lower()
    if t in _YES:
        return True
    if t in _NO:
        return False
    return None
