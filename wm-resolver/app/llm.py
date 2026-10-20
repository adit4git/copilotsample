"""
llm.py
======
Thin wrapper around an LLM for structured extraction.

- Uses Anthropic by default (ANTHROPIC_API_KEY). Optionally OpenAI (OPENAI_API_KEY)
  if PROVIDER=openai.
- If no key is present, falls back to a deterministic MOCK extractor so the POC
  runs end-to-end offline. The mock is good enough to demo every scenario in the
  README without burning tokens.

The only thing the rest of the app needs is `extract()`, which always returns a
dict matching the schema in `RESOLUTION_SCHEMA`.
"""

from __future__ import annotations
import json
import os
import re
from typing import Any, Optional

from schema import catalog_for_prompt, SKILLS_BY_ID

PROVIDER = os.getenv("PROVIDER", "anthropic").lower()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# The shape every extraction must return.
RESOLUTION_SCHEMA = {
    "intent": "string | null",
    "sub_intent": "string (a skill id) | null",
    "confidence": "float 0..1 - how sure about sub_intent",
    "entities": "object - slot_name -> value for anything found",
    "ambiguous_between": "array of skill ids when two+ skills fit similarly",
    "reasoning": "one short sentence - why this routing",
}

SYSTEM_PROMPT = f"""You are the intent & entity resolver for a wealth-management \
advisor copilot. Advisors type terse, context-free requests. Your job each turn \
is to map the conversation so far to exactly one skill (sub-intent) and extract \
its entities, OR say what is missing.

Skill catalog:
{catalog_for_prompt()}

Rules:
- Pick the single best `sub_intent` (a skill id from the catalog). If two skills \
fit almost equally, set `confidence` below 0.6 and list them in `ambiguous_between`.
- Extract every entity you can into `entities`, keyed by the slot name used in the \
catalog. Normalize where obvious (e.g. "last quarter" stays as-is; a client name \
stays as written; "15%" -> "15%").
- Do NOT invent entities. If a required slot is not present in the text, leave it out.
- Use the WHOLE conversation: a later turn may supply a slot the first turn lacked, \
or may just be an answer to your own clarifying question.
- If the latest turn includes extracted file content, treat it as a source of \
entities too (e.g. holdings/balances from a statement).
- Respond with ONLY a JSON object matching this schema (no prose, no markdown):
{json.dumps(RESOLUTION_SCHEMA, indent=2)}
"""


def _client_anthropic():
    import anthropic
    return anthropic.Anthropic()


def _extract_anthropic(messages: list[dict], file_text: Optional[str]) -> dict:
    client = _client_anthropic()
    user_turns = _as_text_transcript(messages, file_text)
    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_turns}],
    )
    text = resp.content[0].text
    return _loads_lenient(text)


def _extract_openai(messages: list[dict], file_text: Optional[str]) -> dict:
    from openai import OpenAI
    client = OpenAI()
    user_turns = _as_text_transcript(messages, file_text)
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_turns},
        ],
    )
    return _loads_lenient(resp.choices[0].message.content)


def _as_text_transcript(messages: list[dict], file_text: Optional[str]) -> str:
    """Flatten the turn history into a single prompt block."""
    lines = ["Conversation so far (oldest first):"]
    for m in messages:
        who = "ADVISOR" if m["role"] == "user" else "COPILOT"
        lines.append(f"{who}: {m['content']}")
    if file_text:
        lines.append("\nExtracted content from the advisor's uploaded file:")
        lines.append(file_text[:6000])
    lines.append("\nReturn the JSON resolution for the CURRENT state.")
    return "\n".join(lines)


def _loads_lenient(text: str) -> dict:
    """Parse JSON even if the model wrapped it in prose/fences."""
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        text = m.group(0)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"intent": None, "sub_intent": None, "confidence": 0.0,
                "entities": {}, "ambiguous_between": [],
                "reasoning": "parse_error"}


def extract(messages: list[dict], file_text: Optional[str] = None) -> dict:
    """Return a resolution dict for the current conversation state."""
    try:
        if PROVIDER == "openai" and os.getenv("OPENAI_API_KEY"):
            return _normalize(_extract_openai(messages, file_text))
        if PROVIDER == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
            return _normalize(_extract_anthropic(messages, file_text))
    except Exception as e:  # network/SDK/parse failures degrade to mock
        print(f"[llm] falling back to mock: {e}")
    return _normalize(_mock_extract(messages, file_text))


def _normalize(r: dict) -> dict:
    r.setdefault("intent", None)
    r.setdefault("sub_intent", None)
    r.setdefault("confidence", 0.0)
    r.setdefault("entities", {})
    r.setdefault("ambiguous_between", [])
    r.setdefault("reasoning", "")
    # Coerce confidence
    try:
        r["confidence"] = float(r["confidence"])
    except Exception:
        r["confidence"] = 0.0
    # Keep only entities that are real slots for the chosen skill (defensive).
    if r["sub_intent"] in SKILLS_BY_ID and isinstance(r["entities"], dict):
        valid = {s.name for s in SKILLS_BY_ID[r["sub_intent"]].slots}
        r["entities"] = {k: v for k, v in r["entities"].items()
                         if k in valid and v not in (None, "", [])}
    return r


# --------------------------------------------------------------------------
# MOCK extractor -- rule-based, only for offline demos / no API key.
# It is intentionally simple but covers the README scenarios deterministically.
# --------------------------------------------------------------------------
_KEYWORDS = [
    # (regex, skill_id, base_confidence)   -- stems use a leading \b only,
    # no trailing \b, so "rebalance"/"concentrated"/"performance" all match.
    (r"\b(rebalanc|drift|back to (target|model))", "portfolio_analysis.drift_rebalance", 0.82),
    (r"\b(concentrat|single[- ]stock|overweight|too much)", "portfolio_analysis.concentration_check", 0.8),
    (r"\b(perform|returns?\b|did .* do|vs (the )?(s&p|benchmark)|ytd)", "portfolio_analysis.performance", 0.7),
    (r"\b(harvest|tlh|tax[- ]loss)", "tax.loss_harvest", 0.85),
    (r"\b(realized|cap gains|capital gains|gain/?loss)", "tax.realized_gains", 0.8),
    (r"\b(retire|retirement|monte ?carlo|readiness)", "planning.retirement_readiness", 0.83),
    (r"\b(raise cash|need.{0,12}cash|liquidity|down payment|need\s+\$?\d)", "planning.cash_flow", 0.78),
    (r"\b(balance|cash on hand|pending|acats?|beneficiar|cost basis|how much cash)", "service.account_status", 0.7),
    (r"\b(pull|extract|read this|statement|screenshot|held[- ]away|this (file|image|doc))", "service.document_extract", 0.72),
]

# Known households in the demo book; matched case-insensitively even when bare.
_KNOWN_CLIENTS = r"hendersons?|patels?|okafor'?s?|kims?|lees?|garcias?|hartwells?"
_CLIENT_CTX_RE = re.compile(
    r"\b(?:the\s+)?([A-Z][a-z]+(?:s|ez|as)?)\s+"
    r"(?:account|trust|portfolio|household|family|joint)")
_PCT_RE = re.compile(r"(\d{1,2})\s?%")
# Money must have a $ or a magnitude word, so a bare "62" isn't mistaken for cash.
_MONEY_RE = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)\s?(k|m|thousand|million)?|"
                       r"\b(\d[\d,]*(?:\.\d+)?)\s?(k|m|thousand|million)\b", re.I)
_AGE_RE = re.compile(r"\b(?:at|age|retire at)\s?(\d{2})\b")
_TIME_RE = re.compile(r"\b(ytd|last (quarter|month|year)|this year|q[1-4]|since inception|\d{4})\b", re.I)


def _mock_extract(messages: list[dict], file_text: Optional[str]) -> dict:
    text = " ".join(m["content"] for m in messages if m["role"] == "user").lower()
    raw = " ".join(m["content"] for m in messages if m["role"] == "user")

    hits = [(sid, conf) for pat, sid, conf in _KEYWORDS if re.search(pat, text)]
    sub_intent, confidence, ambiguous = None, 0.0, []
    if hits:
        hits.sort(key=lambda x: x[1], reverse=True)
        sub_intent, confidence = hits[0]
        close = [sid for sid, c in hits if abs(c - confidence) <= 0.06 and sid != sub_intent]
        if close:
            ambiguous = [sub_intent] + close
            confidence = min(confidence, 0.55)

    entities: dict[str, Any] = {}
    # client -- known surname anywhere, else a name followed by account/trust/etc.
    mk = re.search(_KNOWN_CLIENTS, raw, re.I)
    mc = _CLIENT_CTX_RE.search(raw)
    if mk:
        entities["client"] = mk.group(0).rstrip("'").title()
    elif mc:
        entities["client"] = mc.group(1)
    # percent -> threshold
    mp = _PCT_RE.search(text)
    if mp and sub_intent in ("portfolio_analysis.concentration_check",):
        entities["threshold"] = f"{mp.group(1)}%"
    # time range
    mt = _TIME_RE.search(text)
    if mt:
        entities["time_range"] = mt.group(1)
    # benchmark (optional, performance skill)
    if sub_intent == "portfolio_analysis.performance":
        if re.search(r"s&p|sp500|500", text):
            entities["benchmark"] = "S&P 500"
        elif "60/40" in text:
            entities["benchmark"] = "60/40"
    # age (parse before money so "at 62" isn't read as a dollar amount)
    ma = _AGE_RE.search(text)
    if ma and sub_intent == "planning.retirement_readiness":
        entities["retirement_age"] = int(ma.group(1))
    # money -> amount / annual_spend
    mm = _MONEY_RE.search(raw)
    if mm and sub_intent in ("planning.cash_flow", "planning.retirement_readiness"):
        val = (mm.group(1) or mm.group(3)).replace(",", "")
        mult = {"k": 1e3, "thousand": 1e3, "m": 1e6, "million": 1e6}.get(
            (mm.group(2) or mm.group(4) or "").lower(), 1)
        amt = f"${int(float(val) * mult):,}"
        entities["amount" if sub_intent == "planning.cash_flow" else "annual_spend"] = amt

    if file_text:
        entities["document"] = "uploaded_file"
        if sub_intent is None:
            sub_intent, confidence = "service.document_extract", 0.7

    # Client named but no task keyword -> genuinely ambiguous across the
    # portfolio skills. Surface a disambiguation instead of falling back.
    if sub_intent is None and entities.get("client") and not file_text:
        ambiguous = ["portfolio_analysis.performance",
                     "portfolio_analysis.concentration_check",
                     "portfolio_analysis.drift_rebalance"]
        confidence = 0.4

    intent = SKILLS_BY_ID[sub_intent].intent if sub_intent in SKILLS_BY_ID else None
    return {
        "intent": intent,
        "sub_intent": sub_intent,
        "confidence": confidence,
        "entities": entities,
        "ambiguous_between": ambiguous,
        "reasoning": "mock keyword routing",
    }
