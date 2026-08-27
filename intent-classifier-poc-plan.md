# Intent Classification POC — Wealth Management Advisory

A benchmarking POC to answer one question: **for a fixed labeled corpus, how well does each classification approach classify intent, and where does each one fail?** Built with Anthropic models, Python, and a Streamlit front end. Designed to be executed iteratively with Sonnet, phase by phase.

---

## 1. Objective and success criteria

This is a **bench, not a product**. Four classifiers behind a common interface, one evaluation harness, one Streamlit UI to run queries and read results.

Success is: for any query you type, you see all four outputs side by side with confidence and latency, and you can run the whole golden set through them to get per-intent precision/recall, confusion matrices, and a disagreement view.

Fix these interfaces up front so the four approaches stay swappable:

```python
class Classification(TypedDict):
    intents: list[IntentPrediction]   # multi-label
    slots: dict[str, Any]
    flags: dict[str, bool]            # advice_seeking, complaint, vulnerability, life_event
    confidence: float
    latency_ms: float
    raw: Any                          # for debugging

class Classifier(Protocol):
    def classify(self, query: str, history: list[Message] | None) -> Classification: ...
```

Every approach implements `Classifier`. The harness and UI never know which one they're talking to.

---

## 2. Taxonomy

Lock this before generating any data — it is the thing you iterate on most, and every other artifact depends on it.

**Primary intents** (single enum, multi-label):
`portfolio_performance`, `rebalance_recommendation`, `tax_planning`, `retirement_planning`, `account_balance`, `transaction_history`, `fund_transfer`, `product_information`, `market_information`, `fee_inquiry`, `risk_suitability`, `estate_planning`, `advisor_contact`, `out_of_scope`.

**Cross-cutting flags** (always-on detectors, *not* part of the primary enum):
`advice_seeking`, `complaint`, `vulnerability`, `life_event`.

These carry the regulatory weight, and folding them into the primary taxonomy is a mistake — a single query can be `portfolio_performance` AND advice-seeking AND contain a life event simultaneously.

**Slots to extract:**
`account_ref`, `time_period`, `security`, `amount`, `beneficiary`.

---

## 3. Arriving at the corpus

No real client data for a POC, so **synthesize with Claude and hand-curate a golden slice.** Three tiers:

### Tier 1 — head traffic (generated)
For each primary intent, prompt Sonnet to generate 30–40 realistic single-intent utterances with varied phrasing, formality, and filled slots. Bulk training/reference material for the embedding approaches.

### Tier 2 — the hard set (generated, then reviewed)
Where the POC earns its keep. Explicitly generate:
- **Compound queries** (2–3 intents with dependencies) — the "how did I do last quarter and should I rebalance given my gains" shape
- **Advice-vs-info minimal pairs** ("what is a Roth conversion" / "should I do a Roth conversion")
- **Negation and conditionals** ("should I *not* sell NVDA")
- **Ambiguous slots** ("move money from my account" when multiple exist)
- **Life events buried** inside unrelated questions
- **Out-of-scope and near-scope distractors**

### Tier 3 — golden set (hand-labeled)
Pull ~150–250 queries weighted heavily toward Tier 2, and label them **by hand** (you, since you know the domain). Generated labels are fine for training the embedding classifiers; they are **not** trustworthy as ground truth for scoring. The golden set is the only thing you score against.

**Storage:** JSONL — `{query, history, intents[], slots{}, flags{}, source_tier, notes}`. Have Sonnet generate a diversity report (intent counts, avg slots filled, % compound) so you can see gaps before you trust the corpus.

---

## 4. The four approaches

### A — LLM structured-output classifier
Claude with a forced schema via tool-use, so it can only emit valid intents/slots/flags. Use `claude-haiku-4-5-20251001` for the fast version and `claude-sonnet-5` for a "strong" variant — comparing the two *is* one of your findings. Natively produces the multi-intent task graph with dependencies, handles negation, self-reports confidence (treat with suspicion — see calibration). Slowest and priciest per call.

### B — Embedding k-NN
Embed the Tier-1/2 examples, store in an in-memory index (FAISS, or just numpy at this scale), classify by nearest-neighbor vote with a cosine threshold for abstention. Use a **local sentence-transformer** (e.g. `bge-small` / `all-MiniLM`) to keep the POC self-contained with no extra API key — or Voyage AI for a hosted option (confirm current model names when wiring). Fast, cheap, and it will visibly fail negation and minimal-pair cases — which is the point.

### C — Linear probe on frozen embeddings (proxy for a fine-tuned encoder)
Same embeddings as B, but train a small multi-label head (one-vs-rest logistic regression, sigmoid, per-intent thresholds) on the generated corpus. Stands in for "fine-tuned encoder" without a GPU training loop, gives real calibrated-ish probabilities, typically beats raw k-NN. Label it honestly as a proxy in the UI.

### D — Hybrid router
B or C handles anything above its confidence floor; everything below falls through to A. Log every fallthrough. This is the one you'd actually ship, and the eval shows you the latency/accuracy trade it buys.

### Two shared pre-steps (implemented once, reused everywhere)
- **Contextual rewrite** — before classifying, rewrite the query against history into a standalone form ("what about last year?" → full query). Toggle on/off in the UI to measure its contribution.
- **Multi-label everywhere** — sigmoid + per-intent thresholds, never softmax, or compound queries silently lose intents.

### Task-graph output shape (Approach A)

```json
{
  "tasks": [
    {"intent": "portfolio_performance", "slots": {"period": "2026-Q2", "account": "taxable"}},
    {"intent": "rebalance_recommendation", "slots": {"account": "taxable"}, "depends_on": [0]},
    {"intent": "tax_lot_analysis", "slots": {"realized_gains_ytd": true}, "depends_on": [0]}
  ],
  "advice_seeking": true,
  "confidence": 0.83
}
```

---

## 5. Evaluation harness

Runs any classifier over the golden set and produces:

- **Per-intent precision / recall / F1** — aggregate F1 hides that complaint detection is at 60%
- **Multi-label metrics** — subset/exact-match accuracy, Hamming loss, micro/macro F1
- **Confusion matrix** — watch for intent pairs that collapse into each other (usually a taxonomy problem, not a model problem)
- **Flag detection scored separately** — advice-seeking especially
- **Abstention rate and abstention correctness**
- **Calibration** — reliability curve of reported confidence vs. actual accuracy
- **Latency** (p50/p95) and **cost per query**
- **Disagreement log** — every query where the four approaches diverge; your richest debugging artifact

---

## 6. Streamlit UI

Four tabs:

1. **Playground** — type a query (+ optional history), see all four `Classification` outputs side by side: predicted intents with confidence bars, extracted slots, flags, latency. Toggle contextual-rewrite on/off.
2. **Corpus browser** — view/filter/edit the JSONL, see the diversity report, regenerate a tier.
3. **Batch eval** — pick classifiers, run over golden set, render the metrics above with matplotlib/plotly confusion matrices and per-intent bar charts.
4. **Error explorer** — filter to misclassifications and disagreements, inspect side by side, flag corpus-labeling errors back into the golden set.

---

## 7. Repo layout

```
intent-poc/
  taxonomy.py            # enums, slot defs, single source of truth
  corpus/
    generate.py          # Claude-driven synthesis, per tier
    golden.jsonl
  classifiers/
    base.py              # Protocol + Classification type
    llm.py               # A
    embedding_knn.py     # B
    linear_probe.py      # C
    hybrid.py            # D
    rewrite.py           # shared contextual rewrite
  eval/
    harness.py
    metrics.py
  app.py                 # Streamlit
```

---

## 8. Phased build order (for iterating with Sonnet)

1. **Skeleton** — `taxonomy.py`, `base.py`, one stub classifier returning fixed output, minimal Streamlit playground wired end to end. Validate the interface renders before building anything real.
2. **Approach A** — the LLM classifier; needs no corpus and gives a working baseline immediately.
3. **Corpus** — generation scripts, then hand-label the golden set. Don't skip the hand-labeling.
4. **Approaches B and C** — embeddings, index, linear probe.
5. **Harness + eval tabs** — now you can score everything.
6. **Approach D + calibration** — tune thresholds against the golden set and your actual cost asymmetry, not a guessed 0.7.
7. **Error explorer + iterate** — the loop where taxonomy and corpus actually get fixed.

---

## 9. Two things that will bite you

- **Generated labels leaking into ground truth** — keep the golden set hand-labeled and separate, or every accuracy number is circular.
- **A taxonomy that's wrong rather than a model that's weak** — if two intents keep confusing across *all four* approaches, the fix is merging or splitting the intents, not tuning a classifier.
