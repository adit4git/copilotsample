"""
llm_tools.py  —  tool-calling extraction for the HYBRID engine
==============================================================
Here the skills are presented to the model as native tool schemas. The model
decides which tool fits and fills its arguments — this is usually MORE reliable
structured output than free-form JSON, because the provider enforces the schema.

BUT: we do not let the model's tool call execute anything. We intercept it as a
*proposal*:

    {"sub_intent": <tool name>, "entities": {<args>}, "confidence", "ambiguous_between"}

...which is the exact same shape the classic engine produces, so it flows through
the identical `gate.py`. The model proposes; the gate disposes. A tool call with
missing required args does not run the skill — it becomes a CLARIFY_SLOT.

Providers:
  - Anthropic tool use (default) when ANTHROPIC_API_KEY is set.
  - OpenAI function calling when PROVIDER=openai and OPENAI_API_KEY is set.
  - Deterministic MOCK otherwise, reusing the classic mock extractor and
    re-shaping its output as if it were a tool call, so the hybrid path is fully
    demoable offline and behaves consistently with the classic mock.
"""

from __future__ import annotations
import json
import os
from typing import Optional

from schema import SKILLS, SKILLS_BY_ID
from llm import _mock_extract  # reuse the same offline router for parity

PROVIDER = os.getenv("PROVIDER", "anthropic").lower()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

HYBRID_SYSTEM = (
    "You are the router for a wealth-management advisor copilot. Advisors type "
    "terse, context-free requests. Call exactly ONE tool that matches the request, "
    "filling every argument you can infer from the WHOLE conversation (including "
    "any uploaded file content). Do NOT invent argument values you weren't given — "
    "omit an argument rather than guess; the system will ask the advisor for "
    "anything required that's missing. If two tools fit almost equally, call the "
    "most likely one but keep its arguments minimal. If nothing fits, don't call a "
    "tool; reply with a short clarifying question."
)


# --- build tool schemas from the skill catalog ----------------------------
def _anthropic_tools() -> list[dict]:
    tools = []
    for s in SKILLS:
        props, required = {}, []
        for slot in s.slots:
            prop = {"type": "string", "description": slot.description}
            if slot.options:
                prop["enum"] = slot.options
            props[slot.name] = prop
            if slot.required:
                required.append(slot.name)
        tools.append({
            "name": _safe(s.id),
            "description": s.description,
            "input_schema": {"type": "object", "properties": props,
                             "required": required},
        })
    return tools


def _openai_tools() -> list[dict]:
    out = []
    for t in _anthropic_tools():
        out.append({"type": "function", "function": {
            "name": t["name"], "description": t["description"],
            "parameters": t["input_schema"]}})
    return out


def _safe(skill_id: str) -> str:
    # Tool names can't contain dots in some providers; map both ways.
    return skill_id.replace(".", "__")


def _unsafe(tool_name: str) -> str:
    return tool_name.replace("__", ".")


def _transcript(messages: list[dict], file_text: Optional[str]) -> str:
    lines = []
    for m in messages:
        who = "ADVISOR" if m["role"] == "user" else "COPILOT"
        lines.append(f"{who}: {m['content']}")
    if file_text:
        lines.append("\n[Uploaded file content]\n" + file_text[:6000])
    return "\n".join(lines)


# --- the public call -------------------------------------------------------
def propose(messages: list[dict], file_text: Optional[str] = None) -> dict:
    """Return a proposal dict in the SAME shape as llm.extract()."""
    try:
        if PROVIDER == "openai" and os.getenv("OPENAI_API_KEY"):
            return _propose_openai(messages, file_text)
        if PROVIDER == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
            return _propose_anthropic(messages, file_text)
    except Exception as e:
        print(f"[llm_tools] falling back to mock: {e}")
    return _propose_mock(messages, file_text)


def _propose_anthropic(messages: list[dict], file_text: Optional[str]) -> dict:
    import anthropic
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=ANTHROPIC_MODEL, max_tokens=1024,
        system=HYBRID_SYSTEM, tools=_anthropic_tools(),
        tool_choice={"type": "auto"},
        messages=[{"role": "user",
                   "content": _transcript(messages, file_text)}],
    )
    for block in resp.content:
        if block.type == "tool_use":
            return _shape(_unsafe(block.name), dict(block.input), 0.85)
    # No tool call -> model asked a question / nothing fit.
    text = next((b.text for b in resp.content if b.type == "text"), "")
    return _shape(None, {}, 0.0, reasoning=text[:160] or "no tool matched")


def _propose_openai(messages: list[dict], file_text: Optional[str]) -> dict:
    from openai import OpenAI
    client = OpenAI()
    resp = client.chat.completions.create(
        model=OPENAI_MODEL, tools=_openai_tools(), tool_choice="auto",
        messages=[{"role": "system", "content": HYBRID_SYSTEM},
                  {"role": "user", "content": _transcript(messages, file_text)}],
    )
    msg = resp.choices[0].message
    if msg.tool_calls:
        call = msg.tool_calls[0]
        args = json.loads(call.function.arguments or "{}")
        return _shape(_unsafe(call.function.name), args, 0.85)
    return _shape(None, {}, 0.0, reasoning=(msg.content or "")[:160])


def _propose_mock(messages: list[dict], file_text: Optional[str]) -> dict:
    """Reuse the classic mock so offline behavior is identical across engines,
    but label it as a (simulated) tool call for the trace."""
    r = _mock_extract(messages, file_text)
    r["via"] = "mock_tool_call"
    r.setdefault("reasoning", "mock keyword routing (tool-call shaped)")
    # keep only valid args for the chosen tool
    return _shape(r.get("sub_intent"), r.get("entities", {}),
                  r.get("confidence", 0.0),
                  ambiguous=r.get("ambiguous_between", []),
                  reasoning=r.get("reasoning", ""), via="mock_tool_call")


def _shape(sub_intent, entities, confidence, ambiguous=None,
           reasoning="", via="tool_call") -> dict:
    # Drop any args that aren't real slots for the chosen skill (defensive).
    if sub_intent in SKILLS_BY_ID and isinstance(entities, dict):
        valid = {s.name for s in SKILLS_BY_ID[sub_intent].slots}
        entities = {k: v for k, v in entities.items()
                    if k in valid and v not in (None, "", [])}
    intent = SKILLS_BY_ID[sub_intent].intent if sub_intent in SKILLS_BY_ID else None
    return {"intent": intent, "sub_intent": sub_intent,
            "confidence": float(confidence), "entities": entities or {},
            "ambiguous_between": ambiguous or [], "reasoning": reasoning,
            "via": via}
