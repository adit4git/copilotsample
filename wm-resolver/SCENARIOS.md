# Worked scenarios

Realistic requests a busy advisor types between meetings, and how the resolver
handles each. `✓` = slot filled, `✗` = required slot missing. Actions:
`CLARIFY_INTENT`, `CLARIFY_SLOT`, `EXECUTE`, `FALLBACK`.

All of these are reproducible against the running POC (mock mode included). They
behave the **same under both engines** (classic JSON extraction and hybrid
tool-calling) — scenarios 9–10 show the engine difference and the confirm gate.

---

### 1 · Single-turn resolve (everything present)

> **Advisor:** is the Okafor account too concentrated

- route → `portfolio_analysis.concentration_check` (conf ~0.80)
- slots → `client=Okafor ✓`, `threshold=(optional, default 10%)`
- **EXECUTE** → *"Okafor: largest position MSFT at 22% (OVER the 10% limit). Recommend trimming ~$780,000."*

One message in, one answer out. No questions needed.

---

### 2 · Task without a client → one clarification

> **Advisor:** rebalance the portfolio

- route → `portfolio_analysis.drift_rebalance`
- slots → `client ✗`
- **CLARIFY_SLOT** → *"Which client or household is this for?"*

> **Advisor:** the Hendersons

- slots → `client=Hendersons ✓` (all required present)
- rebalance is side-effecting → **CONFIRM** → *"…produce trade orders… Run it?"*

> **Advisor:** yes → **EXECUTE** → drift + proposed tax-aware rebalance trades.

The task was understood on turn 1; only the missing entity was elicited, then the
money-moving action was gated behind a confirmation.

---

### 3 · Two missing slots → asked one at a time

> **Advisor:** can the Garcias retire

- route → `planning.retirement_readiness`
- slots → `client=Garcias ✓`, `retirement_age ✗`, `annual_spend ✗`
- **CLARIFY_SLOT** → *"At what age do they plan to retire?"*

> **Advisor:** at 62   → `retirement_age=62 ✓` (note: not mis-read as $62)
- **CLARIFY_SLOT** → *"What's the target annual spending in retirement?"*

> **Advisor:** 150k per year → `annual_spend=$150,000 ✓`
- **EXECUTE** → *"Garcias retiring at 62, spending $150,000/yr: Monte Carlo success probability 84%…"*

Entities **accumulate** — turn 3 still remembers the client and age from turns 1–2.

---

### 4 · Client without a task → disambiguate the intent

> **Advisor:** look at the Lees

- `client=Lees ✓` but no task keyword; the model flags several portfolio skills
- **CLARIFY_INTENT** → *"I can take this a couple of ways — which did you mean?"*
  with chips: **Performance review · Concentration check · Drift & rebalance**

> **Advisor:** *(clicks)* Drift check & rebalance proposal
- **EXECUTE** → rebalance for the Lees.

The chips come straight from `ambiguous_between` in the resolution.

---

### 5 · Intent switch mid-conversation

> **Advisor:** rebalance the Kims → **EXECUTE** (drift/rebalance)
> **Advisor:** actually just check their concentration

- the model is confident this is a *different* skill → resolver switches to
  `portfolio_analysis.concentration_check`, **keeps `client=Kims`**, and (since
  a new skill = new slot set) surfaces a **CLARIFY_INTENT/SLOT** for the new path
  rather than silently continuing the old one.

Guard in `resolver.py`: a terse answer won't re-route, but a clear new intent will.

---

### 6 · Performance with an optional benchmark captured inline

> **Advisor:** ytd performance for the Patels vs the s&p

- route → `portfolio_analysis.performance`
- slots → `client=Patels ✓`, `time_range=ytd ✓`, `benchmark=S&P 500 ✓` (optional)
- **EXECUTE** → *"Patels: +7.4% for ytd vs S&P 500 (+6.1%)…"*

Optional slots are filled when present but never block execution.

---

### 7 · Liquidity need parsed from one line

> **Advisor:** the Lees need 400k for a house down payment

- route → `planning.cash_flow`
- slots → `client=Lees ✓`, `amount=$400,000 ✓`, `by_when (optional) ✗`
- **EXECUTE** → where to raise the cash, gain-aware, with tax drag estimate.

`by_when` is optional, so the skill runs; the advisor can add timing to refine.

---

### 8 · File-assisted resolution (screenshot / statement upload)

> **Advisor:** *(📎 attaches a held-away 401(k) statement)* pull the holdings off this

- `files.py` turns the upload into text (direct read / PDF text / vision OCR)
- route → `service.document_extract`, slot `document=uploaded_file ✓`
- **EXECUTE** → extracts balances & holdings, echoes a parsed preview, ready to
  import as held-away assets.

A file can also *fill a slot in another skill* — e.g. an uploaded statement that
supplies the `annual_spend` or outside-holdings an analysis needs — because the
file's extracted text is fed into the same LLM extraction step.

---

### 9 · Confirmation gate on a side-effecting skill (both engines)

A skill that would place trades or move cash never runs straight from the model.
`gate.py` inserts a `CONFIRM` step.

> **Advisor:** rebalance the Hendersons

- `client=Hendersons ✓`, all required slots present
- skill `portfolio_analysis.drift_rebalance` is in `SIDE_EFFECTING`
- **CONFIRM** → *"Ready to generate a rebalance proposal for **Hendersons** (tax-aware). This will produce trade orders for your review. Run it?"* with chips **Yes, run it · Cancel**

> **Advisor:** *(clicks)* Yes, run it → **EXECUTE**
> *(or)* Cancel → **FALLBACK**, skill + slots cleared

Read-only skills (performance, concentration, account lookup) skip this and
execute immediately. The set is one line to edit in `gate.py`.

---

### 10 · Same request, classic vs hybrid engine

> **Advisor:** rebalance the Kims

| | Classic | Hybrid |
|---|---|---|
| model output | JSON `{"sub_intent":"portfolio_analysis.drift_rebalance","entities":{"client":"Kims"}}` | **tool call** `portfolio_analysis__drift_rebalance(client="Kims")` |
| trace shows | *proposed via: JSON extract* | *proposed via: tool call* |
| gate result | **CONFIRM** → (yes) → **EXECUTE** | **CONFIRM** → (yes) → **EXECUTE** |

Identical outcome and identical control flow — only the extraction mechanism and
the trace label differ. That's the point: the engine is swappable, the gate isn't.

---

## Reproduce from the command line (mock mode)

```bash
cd app && python3 - <<'PY'
import resolver as R
def turn(sid, text, file=None):
    a = R.resolve_turn(R.get_session(sid), text, file_text=file)
    s = a["state"]
    print(f'[{a["action"]:<14}] {text!r}')
    print(f'    skill={s["skill_id"]}  entities={s["entities"]}  missing={s["missing_slots"]}')
    print(f'    copilot> {a["message"][:80]}')
turn("a","can the Garcias retire"); turn("a","at 62"); turn("a","150k a year")
turn("b","rebalance the portfolio"); turn("b","the Hendersons"); turn("b","yes")  # CONFIRM->EXECUTE
turn("c","look at the Lees")
PY
```

Run the **hybrid** engine instead by importing `resolver_hybrid as R` — the same
calls produce the same actions, with the trace labelled *via tool call*.
