# Advisor Copilot — Entity & Intent Resolution POC

A proof-of-concept for the hard part of a wealth-management agentic chatbot:
**turning a busy advisor's terse, context-free request into the right skill with
the right parameters — asking follow-up questions only when it has to.**

```
advisor: "rebalance the Hendersons"
   └─ intent: portfolio_analysis
      └─ sub-intent (skill): portfolio_analysis.drift_rebalance
         └─ slots: client=Hendersons ✓   model=(optional)   tax_aware=(optional)
            └─ all required slots filled → RUN SKILL

advisor: "can the Garcias retire"
   └─ skill: planning.retirement_readiness
      └─ slots: client=Garcias ✓  retirement_age=✗  annual_spend=✗
         └─ missing required slot → ASK: "At what age do they plan to retire?"
            advisor: "at 62"      → age=62 ✓, still missing spend → ASK again
            advisor: "150k/year"  → all filled → RUN SKILL
```

## Why multi-turn

Advisors don't write well-formed queries. They write fragments between client
meetings. A single-shot "classify + extract" pass is wrong a lot of the time
because the first message frequently:

- names the task but not the client (`"rebalance the portfolio"`),
- names the client but not the task (`"look at the Lees"`),
- is genuinely ambiguous between sibling skills (`"check the Kims"` →
  performance? concentration? drift?),
- or needs a number the advisor hasn't given yet (retirement age, cash amount).

So resolution is modeled as a **slot-filling state machine over a dialogue**,
not a one-shot classifier. Each turn the LLM re-resolves against the *entire*
conversation, entities **accumulate** across turns, and the machine asks for at
most one missing thing at a time.

## Two engines, one gate (side-by-side)

The POC ships **two resolution engines** you can switch between live (toggle in
the header). They differ only in *how the model's intent/entities are obtained*;
everything after that — slot accounting, the clarify/execute decision, and the
confirmation gate for actions that move money — is **shared code** (`gate.py`).

| | **Classic** (`resolver.py`) | **Hybrid** (`resolver_hybrid.py`) |
|---|---|---|
| Model's role | returns free-form **JSON** `{sub_intent, entities, …}` | emits a native **tool call**; args are the entities |
| Structured output | prompt-enforced | **provider-enforced** schema (usually more reliable) |
| Who executes a skill | **your code** (the gate) | **your code** (the same gate) |
| Missing required arg | → `CLARIFY_SLOT` | → `CLARIFY_SLOT` (the tool call does **not** run) |
| Side-effecting skill | → `CONFIRM` before running | → `CONFIRM` before running |
| Extraction module | `llm.py` | `llm_tools.py` |

**The hybrid thesis:** use tool-calling for reliable structured *output*, but
keep execution *control* in deterministic code. A proposed tool call is treated
as exactly that — a proposal — and flows through the identical gate. This is why
a rebalance or cash-raise never fires straight from the model: the gate inserts a
`CONFIRM` step (see `SIDE_EFFECTING` in `gate.py`).

## Architecture

```
┌─────────────┐  POST /api/message {engine}   ┌─────────────────────────────────────┐
│  HTML chat  │ ────────────────────────────▶ │  FastAPI (main.py)  — engine switch │
│  + engine   │  POST /api/upload {engine}    │                                     │
│  toggle     │ ◀──────────────────────────── │  resolver.py ─┐   resolver_hybrid.py│
│  + trace    │   action + resolution+via     │   (JSON)      │      (tool call)    │
└─────────────┘                               │     llm.py    │      llm_tools.py   │
                                              │               ▼            ▼        │
                                              │          ┌─────────────────────┐   │
                                              │          │   gate.py (SHARED)  │   │
                                              │          │  slots · decide ·   │   │
                                              │          │  CONFIRM · execute  │   │
                                              │          └─────────┬───────────┘   │
                                              │   schema.py  files.py  skills_exec.py│
                                              └─────────────────────────────────────┘
```

| File | Role |
|------|------|
| `app/schema.py` | Source of truth: intents, sub-intents (=skills), required/optional **slots**. Renders the catalog for the JSON prompt **and** the tool schemas. |
| `app/gate.py` | **Shared** engine-agnostic gate: slot accounting, the `CLARIFY_INTENT/CLARIFY_SLOT/CONFIRM/EXECUTE/FALLBACK` decision, the side-effect confirmation, session state, skill dispatch. |
| `app/llm.py` | **Classic** extraction → JSON `{sub_intent, entities, confidence, ambiguous_between}`. Anthropic default, OpenAI optional, **deterministic mock** offline. |
| `app/llm_tools.py` | **Hybrid** extraction → exposes skills as tool schemas, runs the tool-call turn, returns a proposal in the *same shape*. Mock reuses the classic router for parity. |
| `app/resolver.py` | Classic engine turn loop + the shared in-memory session store. |
| `app/resolver_hybrid.py` | Hybrid engine turn loop (shares the store and the gate). |
| `app/skills_exec.py` | Mock skill implementations returning believable fabricated data. Swap for real custodian / planning / portfolio APIs. |
| `app/files.py` | Uploaded statement/screenshot → text (direct read, PDF text, or LLM vision OCR). |
| `app/main.py` | FastAPI endpoints (take `engine=classic|hybrid`) + serves the UI. |
| `static/index.html` | Chat UI: engine toggle, clarification **chips**, file upload, and a live **resolution panel** (engine, proposed-via, skill, filled/missing slots, confidence, why). |

## The resolution state machine

```
            ┌──────────────── new advisor turn (+ optional file) ───────────────┐
            ▼                                                                    │
  LLM extract over full history  →  {sub_intent, entities, confidence, ambig}   │
            │                                                                    │
            ▼                                                                    │
  merge entities into session (accumulate, never blank-overwrite)               │
            │                                                                    │
            ▼                                                                    │
   ┌──────────────── decide ────────────────┐                                   │
   │ no skill & ambiguous      → CLARIFY_INTENT (show skill chips)              ─┤
   │ skill & conf < floor & amb→ CLARIFY_INTENT                                 ─┤
   │ skill & required slot gap → CLARIFY_SLOT   (ask one slot, maybe chips/file)─┤
   │ skill side-effecting      → CONFIRM        (preview + Yes/Cancel chips)
   │ skill & all slots filled  → EXECUTE        (run skill, return result)       │
   │ nothing matched           → FALLBACK       (ask to rephrase w/ examples)   ─┘
   └─────────────────────────────────────────┘
```

Thresholds and the side-effecting skill set live at the top of `gate.py`
(`CONFIDENCE_FLOOR`, `SIDE_EFFECTING`). Entity memory, single-slot prompting, the
intent-switch guard (don't re-route on a terse slot answer unless the LLM is
clearly confident about a *different* skill), and the `CONFIRM` gate are all
shared by **both** engines.

## Run it

```bash
cd wm-resolver
pip install -r requirements.txt
cd app
uvicorn main:app --reload --port 8000
# open http://localhost:8000
```

Use the **engine toggle** in the header to switch between `classic` and `hybrid`
at any time (switching starts a fresh conversation so you don't land mid-slot-fill).

**Offline (no API key):** it just works — both engines fall back to a rule-based
mock extractor that covers every scenario below (the hybrid mock shapes the same
routing as a simulated tool call). The header shows `mode: mock`.

**Live inference (recommended):**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
export ANTHROPIC_MODEL=claude-sonnet-4-5     # or your preferred model
uvicorn main:app --reload --port 8000        # header shows mode: live
```
To use OpenAI instead:
```bash
export PROVIDER=openai
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o-mini
```
For real PDF/image handling, uncomment `pdfplumber` in `requirements.txt`; image
OCR uses the Anthropic vision model automatically when a key is present.

> The mock is only for the demo. With a key set, the *same* resolver runs on real
> LLM extraction — the mock's keyword rules are never used.

## Example scenarios

See **`SCENARIOS.md`** for 8 worked advisor conversations (single-turn resolve,
two-slot elicitation, ambiguity disambiguation, intent switch mid-flow, and
file-assisted resolution), each with the expected action trace.

## Taking this to production

- **Entity grounding:** resolve `client="Hendersons"` → a real household id via a
  CRM lookup, and handle the "which Henderson?" disambiguation (multiple matches).
- **Skills as tools:** replace `skills_exec.py` with real tool calls; both engines
  already produce a clean `{skill_id, entities}` you can dispatch on. The hybrid
  engine already hands the catalog to the model as tool schemas — but note it treats
  the tool call as a *proposal* and still gates execution, which is what you want for
  anything with side effects.
- **State store:** swap the in-memory `SESSIONS` dict for Redis/DB keyed by advisor
  + conversation.
- **Guardrails:** the `EXECUTE` step is where you add confirmation for anything that
  places trades or moves money, plus entitlement checks (can this advisor see this
  household?) and an audit log of every resolution.
- **Confidence calibration:** log `confidence` vs. whether the advisor accepted the
  route, and tune `CONFIDENCE_FLOOR` from real data.
