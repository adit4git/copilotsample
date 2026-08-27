# Proposed Approach: Intent Classification for the Advisor-Agent Catalog (v2)

*Revision of v1, incorporating external review. Changes from v1 are summarized at the end.*

> **Note on examples.** All example queries in this document use placeholder
> tokens — `[ACCOUNT-1]`, `[AMOUNT]`, `[SECURITY]`, `[CLIENT]` — in place of
> account numbers, dollar figures, tickers, and client identifiers. The
> placeholders stand in for the slot values the classifier is expected to
> extract; the intent-routing logic they illustrate is unaffected by the
> substitution.

## The core problem

The catalog defines 57 intents across 7 categories, with composite intents (one
request that bundles several capabilities), specializations, and multiple pairs
of intents that look almost identical on the surface but differ in a subtle,
meaningful way. Two things make this hard to solve with rules:

- **The discriminating signal is usually semantic, not lexical.** "What are my
  options for this concentrated position?" and "Build a plan to transition this
  position into munis" use almost the same vocabulary but need different intents
  (a menu of options vs. a committed execution plan). No keyword list or regex
  reliably separates them.
- **A single query often needs several intents in sequence, not one.** "Client is
  adding [AMOUNT], move the taxable position toward munis without selling stock"
  isn't one classification decision — it requires a transition analysis, then a
  vehicle screen, then an eligibility check, then a client-ready explanation, in
  dependency order.

That reframes the task: it is not "pick one bucket," it is **multi-label intent
detection, with dependency ordering, plus slot extraction**.

One clarification that shapes everything downstream: the output is a **dependency
graph (DAG), not a list.** Some steps are strictly sequential (eligibility must
precede the plan that depends on it); others are genuinely parallel — the
catalog's own composition strings say so explicitly, one of them reading "per
manager, parallel." Treating the output as a total order is a modeling error that
propagates into the metrics (see Evaluation).

## Why not keyword/regex (rejected)

"What's the exposure here" could mean a single-account rebalance scenario (I-29)
or a book-wide exposure screen (I-31). The catalog's own discriminator is *"one
account → I-29; book-wide → I-31,"* which depends on whether a specific
client/account is in context — not on any word in the sentence. A regex cannot
represent "check the conversation's client-context state." A classifier told this
rule in plain language applies it directly.

## Why not "let the LLM pick tools directly" (rejected)

"Show me next-best-actions for my book with supporting CIO citations" and "Which
clients qualify for alts but aren't using them, and what's the CIO-aligned
action?" may call similar tools. But the first is one ask matching a single
composite's definition; the second has two distinguishable asks and needs the
chain broken out explicitly — because **compliance gating and disclosure wrapping
attach to which intent fired, not to which tools happened to run.** Collapsing to
tool selection loses that distinction and the audit trail a regulated domain
requires.

## The proposed architecture: three tiers, escalating only when needed

### Tier 1 — LLM classifier, prompted directly from the catalog

**What it does:** an LLM reads the catalog's descriptions, examples, and routing
discriminators (rendered into its prompt) and returns structured JSON: which
intents are needed, their dependency order, extracted slots, and whether the
query is out-of-scope or genuinely ambiguous.

**Why this approach:** the catalog has ~2–3 example queries per intent — far too
few to train a classifier from scratch, but exactly the shape of information an
LLM uses natively as few-shot context. The routing discriminators are written as
short conditional rules; an LLM applies them directly, whereas a trained encoder
would first need them re-expressed as labeled examples that don't exist yet.

**Example:** *"Account [ACCOUNT-1]: adding [AMOUNT] in new cash, move the taxable
position toward munis without selling any stock."* A keyword system sees "munis"
and routes to a vehicle lookup. The catalog-grounded classifier produces the
chain: transition-lever analysis (I-35) → muni implementation screen, since
"toward munis" is an open vehicle choice (I-15) → eligibility check on the chosen
option (I-22) → the client-facing explanation the advisor needs to deliver it
(I-09). Getting the *chain* rather than the nearest single label is this tier's
entire reason to exist.

**Tier 1 is permanent.** It is not scaffolding to be replaced once better models
arrive — it is the only tier that assembles chains (see Tier 3).

### Tier 2 — Embedding-based semantic router (fast path)

**What it does:** pre-encode example utterances per intent; for a new query, find
the nearest match by embedding similarity. Confident, guard-passing matches route
directly. Everything else escalates to Tier 1.

**Why this approach:** most traffic will be plain single-intent questions, and
paying for a full LLM reasoning pass on each is wasteful. An embedding lookup
answers those in milliseconds at a fraction of the cost, reserving Tier 1 for
traffic that needs its reasoning.

**Example:** *"What's the CIO's latest view on rates?"* embeds close to I-01 with
a wide margin — routed directly, no LLM call. *"What should I tell my client
about their concentrated position?"* embeds ambiguously between I-18 (options)
and I-35 (execution plan) — low margin, escalate.

#### Guard 1 — Compound-signal escalation

Margin-based escalation assumes compound queries *look* ambiguous. They don't. A
multi-step request can embed with high similarity and a wide margin against a
single-intent cluster and be waved through as "easy, single-intent" — losing the
decomposition that is Tier 1's whole purpose. This is the same blind spot that
disqualified regex; margin alone does not close it.

```
escalate = (margin < THRESHOLD)
        OR compound_signal(query, context)
        OR top_match ∈ CHAIN_ANCHOR_INTENTS
```

**Compound signals** — structural markers that a query carries more than one ask:
coordinating conjunctions joining clauses that each have their own verb ("screen
for eligibility *and* draft the explanation" — noun coordination like "stocks and
bonds" does not count); sequencing language ("then," "after that," "once
you've"); multiple distinct entities implying separate operations (more than one
account, or a security *plus* a target vehicle); a goal plus a constraint that
forces intermediate work ("toward munis *without selling stock*"); an
imperative/interrogative mix; and clause count as a weak backstop only.

Note the apparent irony: several markers are lexical, and this document rejects
regex. The rejection stands — lexical patterns cannot make the *final intent
decision*. Here the detector decides nothing; it only decides **whether to
escalate to the tier that does.** A false positive costs one extra Tier-1 call; a
false negative silently ships a truncated multi-step advisory request. The
detector is deliberately biased toward over-escalation, and the threshold is
tuned against that asymmetry on the golden set's compound slice — not a guessed
default.

#### Guard 2 — Chain-anchor intents

Compound-signal detection is necessary but **not sufficient**, and this is the
most important amendment in v2. Empirically, during Phase-1/2 testing the hardest
misses had *no lexical compound marker at all*: a bulk transfer that
institutionally requires a human handoff, or a named-account transition that
implies client communication. Paraphrasing reliably stripped any explicit
"and"/"then"/"who do I loop in" phrasing, and the requirement survived anyway,
because it came from **institutional convention rather than sentence structure.**
A conjunction detector waves every one of those through.

So: mine the golden set for intents that empirically almost never appear alone
(transition-plan intents, bulk-transfer intents, prospect-intake intents). If the
top embedding match is one of them, escalate — regardless of margin and
regardless of compound signal. This list is refreshed from the same
confusion-matrix pipeline that maintains the confusable-pair list, so it stays
data-driven rather than hand-curated once and left to rot.

#### Implementation note

Two options for the compound detector: (1) a small, fast LLM pre-pass returning a
boolean "more than one distinct ask" — more robust to phrasing; (2) a structural
/ dependency-parse heuristic — zero API cost, more brittle, acceptable as a first
cut.

Option 1 carries an economic caveat worth quantifying rather than assuming: a
model call on every query partially defeats Tier 2's purpose, since a network
round-trip has been reintroduced to the fast path. It only pays if it is
dramatically cheaper and faster than the full classifier.

#### Tier 2 as shortlist, not just gate

Rather than a binary route/escalate, Tier 2 should hand Tier 1 its **top-K
candidate intents** when it escalates. This preserves most of the cost saving (a
much smaller prompt and label space — ~10 candidates instead of 57) while never
fully bypassing the tier that does decomposition. It also directly attacks the
two error classes observed in testing: recall misses (an intent never considered
because attention went elsewhere) and precision errors (adjacent intents
over-firing on phrasing cues). Label-space reduction is a better-evidenced lever
here than additional hand-written prompt examples.

### Tier 3 — Fine-tuned multi-label encoder (calibration upgrade)

**What it does:** once enough labeled traffic exists, train a discriminative
multi-label model (SetFit or a small transformer) producing **calibrated
per-label probabilities** instead of self-reported "high/medium/low."

**Why it cannot replace Tier 1 — the key constraint.** A multi-label encoder
predicts *labels*, not *ordered chains*. It cannot output "I-35 → I-15 → I-22 →
I-09." So Tier 3 is a calibration-and-speed upgrade for label prediction sitting
*underneath* a tier that still assembles the dependency graph. It is not a
successor to Tier 1 and never becomes one.

**Why it is sequenced last.** Two reasons, and the distinction matters:

1. **Calibration needs volume.** Trusting P=0.92 as an actual 92% requires enough
   labeled outcomes to fit and validate a reliability curve. This is the primary
   reason.
2. **There is also a real training-data floor, though a lower one than "thousands."**
   SetFit is a few-shot method (roughly 8–64 examples per class), so "we lack
   thousands of examples" is *not* by itself a valid argument for deferring it —
   an earlier draft of this document made that error. But with 57 classes, even
   the few-shot floor implies ~450–900 labeled queries against a corpus of
   roughly 150, and per-class support will be highly uneven, which few-shot
   methods handle worse than an aggregate count suggests.

**Example:** for a query needing I-45 (next-best-action ranking, which drives a
client-facing recommendation), a calibrated P(I-45)=0.92 could clear an
auto-proceed bar, while P(I-45)=0.55 routes to a human before anything reaches a
client. That rule is not safely possible on self-reported confidence.

## Compliance gating before Tier 3 exists

Tier 3 arrives late, yet the argument for it — that LLM confidence is spiky and
unsafe to gate on — applies from day one. Tier 2's embedding margin is likewise
uncalibrated. Left unaddressed, that means the entire pre-Tier-3 period runs
compliance gating on exactly the signals this document says cannot be trusted.

**Resolution: do not gate compliance on model confidence at all.** Gate on
deterministic post-conditions instead:

- Disclosure wrapping, eligibility checks, suitability gates, and archival
  routing fire **deterministically from which intent was predicted**. They do not
  need to know how confident the model was.
- Anything client-facing requires human advisor review by default,
  pre-Tier-3 — no confidence threshold involved.
- Out-of-scope and clarification paths are hard stops, not confidence-weighted.

Under this design, confidence-based auto-approval becomes a **later cost
optimization**, not a safety prerequisite — which is what keeps Tier 3 correctly
sequenced last rather than promoting it to the critical path. The tension is real
but is created by assuming confidence *must* gate compliance; that is a design
choice, and this document chooses otherwise.

## Cross-cutting flags are not intents

Some compliance-relevant signals are orthogonal to intent: a vulnerability
indicator, a complaint, or advice-vs-information can ride inside *any* intent.
Modeling these as catalog entries forces a false choice between the flag and the
actual intent. They are modeled instead as **always-on flags** extracted
alongside the intent, and scored independently — a missed vulnerability flag is a
supervisory finding regardless of whether the intent was right.

## Evaluation plan

Every claim above — "Tier 1 solves decomposition," "Tier 2 safely fast-paths the
easy majority," "Tier 3 is safe to gate on" — is an empirical claim. None can be
assessed without labeled data and metrics that score what the system actually
outputs: an **ordered, multi-label intent graph with slots**, not a single label.

### Two sets, not one

The v1 draft had no evaluation story at all; the review's proposed single
risk-weighted golden set fixes that, but one set cannot serve both purposes it
would be assigned.

**Set A — risk-weighted golden set (200–300 queries), for accuracy and error
analysis.** Deliberately over-samples the cases that carry risk:

| Slice | Target share | Purpose |
|---|---|---|
| Single-intent, unambiguous | ~30% | Baseline; the traffic Tier 2 fast-paths |
| Composite / multi-intent chains | ~30% | The core value claim — chain and order |
| Confusable pairs (I-29/I-31, I-18/I-35, …) | ~20% | Where regex and naive embedding fail |
| Context-dependent (same words, different intent by account state) | ~10% | The discriminator-rule cases |
| Out-of-scope / near-scope distractors | ~10% | Does the system correctly decline |

**Set B — representative sample drawn from real traffic, for operational
numbers.** Escalation rate, cost per query, and latency computed on Set A would
be badly biased, because Set A is ~70% hard cases by construction while live
traffic will be mostly the easy head. Either draw Set B separately or reweight
Set A results to a traffic prior — but do not report operational metrics off a
risk-weighted sample.

Each record carries: the query, any prior context state it depends on, the
correct intents **with their dependency edges**, correct slots, and cross-cutting
flags.

**Labels are hand-produced.** Catalog-generated examples may seed Tiers 1–2 but
must never be scored against themselves — that makes every number circular.

### Labeling requires multiple annotators, not one

"Hand-labeled by someone who knows the catalog" is insufficient for a taxonomy
this confusable: a single annotator's reading silently *becomes* ground truth,
including on pairs where two experts would legitimately disagree. Run an
**inter-annotator agreement pass on the confusable and composite slices at
minimum.** Low agreement on a pair is a *taxonomy* signal — sharpen the
discriminator or merge the intents — not a model-tuning target. Without this,
tuning cycles get burned on cases that are unresolvable in principle, with no way
to tell which ones those are.

### Split discipline and reuse policy

A single golden set read repeatedly is overfit by proxy even without formal
training on it. Required: a **dev/golden split**, a rule for how often golden may
be read (once per meaningful iteration, not per tweak), and a **regeneration
protocol** for producing fresh held-out material once a golden set has been
consulted enough to be considered spent. This is not theoretical — during
Phase-1/2 work, fresh held-out sets had to be regenerated each round for reported
numbers to stay honest.

### Validate the harness against its own ground truth

Before concluding "the model is wrong," verify the scoring logic is internally
consistent with its source data. In Phase-2 work, three entries in a hand-built
composite-expansion map disagreed with the catalog's own composition strings, and
correct predictions were scored as errors for multiple rounds; fixing the map
alone moved dev accuracy ~8 points with no model change. Treat harness validation
as a standing step, not a one-time setup task.

### Metrics — scored separately, never as one aggregate

A blended figure hides what matters: 94% aggregate can conceal 60% on confusable
pairs.

**Intent detection (multi-label):** per-intent precision/recall/F1 (so a weak
intent cannot hide behind strong ones); micro- and macro-F1; exact-set match.

**Chain structure — scored as a DAG, not a list.** This is a correction to the
reviewer's proposal, which specified exact-order match and Kendall's tau. Both
assume a total order and will penalize correct predictions that sequence
genuinely parallel steps differently — manufacturing errors that are not errors,
the same class of bug described in "validate the harness" above. Instead:

- **Edge precision/recall over dependency edges** — did the model get the
  *dependencies* right (A must precede B), ignoring order among parallel steps.
- **Exact-order match reserved for chains the catalog marks strictly
  sequential**, where a total order is genuinely the ground truth.
- **Order-correctness given correct set** — of queries where the set was right,
  how often was structure also right; isolates decomposition from ordering.
- Edit distance / tau as partial credit **only within strictly-sequential
  chains.**

**Composite equivalence:** predicting a composite and predicting its full atomic
decomposition must score as equivalent, per the catalog's own stated invariant.

**Slot extraction:** per-slot-type precision/recall (account_ref, time_period,
security, amount, beneficiary), plus ambiguous-slot handling — when a slot is
under-specified ("my account," with several on file), did the system flag for
clarification rather than guess. Slot accuracy has to be scored explicitly:
intents can be entirely correct while a mis-parsed account ID or amount silently
corrupts every downstream tool call.

**Cross-cutting flags:** precision/recall for advice-seeking, vulnerability, and
complaint detection, scored independently of intent.

**Confusion matrix:** full intent-vs-intent. Two purposes — catch pairs that
collapse into each other (usually a taxonomy problem, not a model problem), and
**auto-populate both the confusable-pair list and the chain-anchor list** that
Tier 2's guards depend on, replacing hand-curation with a refreshable,
data-driven source.

**Abstention and escalation quality:** abstention rate and correctness; for
Tier 2, escalation rate and — the number that decides whether the fast path is
safe — the **false-fast-path rate**: queries routed directly that the golden set
says needed Tier 1. Measured specifically on the compound slice, this is the test
of whether the Guard 1 and Guard 2 rules work. It should drop sharply once the
guards are in place, at the cost of a modest, quantified rise in escalation rate.

**Calibration (gates Tier 3 readiness):** reliability curve of predicted
confidence vs. observed accuracy, per tier; and an explicit comparison of Tier 1
self-reported confidence against Tier 3 calibrated probability on the same
queries — the evidence that decides when confidence-based auto-approval can
safely replace deterministic gating.

**Operational (from Set B):** latency p50/p95 and cost per query, per tier — the
numbers that justify Tier 2 existing at all.

### How each tier is validated

- **Tier 1** — run over Set A; report intent F1, edge precision/recall,
  composite-equivalence, and slot metrics. Turns "solves decomposition" from
  assertion into a number.
- **Tier 2** — validated on false-fast-path rate and escalation quality. It may
  route directly only where doing so does not degrade Set A metrics below the
  Tier-1 baseline. Operational savings reported from Set B.
- **Tier 3** — validated primarily on the calibration curve, since calibration is
  its reason to exist; secondarily on label F1 versus Tier 2.

## Why this sequencing

Tier 1 first is a deliberate bet on where the difficulty actually lives: not "is
this fast enough" but "can it correctly decompose a request into the right
dependency graph, including catalog-specific conventions no off-the-shelf method
could know." An LLM prompted from the catalog's own language solves that with the
data that already exists. Tier 2 then optimizes cost and latency for the easy
majority *once the hard cases are handled correctly* — with guards, because a
fast path that silently truncates chains is worse than no fast path. Tier 3
optimizes calibration once real usage exists to train and validate against, and
never replaces Tier 1, because it predicts labels and the problem is graphs.

---

## Changes from v1

1. **SetFit contradiction corrected.** v1 named a few-shot method while
   justifying its deferral with "needs thousands of examples." Reframed around
   calibration, an honest (lower) training-data floor, and the stronger point
   that an encoder predicts *labels, not chains* and therefore never replaces
   Tier 1.
2. **Evaluation plan added** — the load-bearing gap in v1, which asserted Tier 1
   accuracy without any means of measuring it.
3. **Compliance-gating tension resolved** via deterministic post-condition gating
   rather than confidence thresholds, keeping Tier 3 off the critical path.
4. **Tier 2 guards added:** compound-signal escalation, plus chain-anchor
   escalation for the implicit-chain cases lexical markers cannot see.
5. **Tier 2 reframed as a shortlist provider,** not a binary gate.
6. **Ordering metrics corrected to DAG-aware** edge precision/recall; total-order
   metrics reserved for strictly-sequential chains.
7. **Two evaluation sets** separated: risk-weighted for accuracy, representative
   for operational numbers.
8. **Multi-annotator labeling with IAA** on confusable slices; split discipline
   and regeneration protocol; harness self-validation added as a standing step.
9. **Cross-cutting flags** modeled as always-on, scored independently.
