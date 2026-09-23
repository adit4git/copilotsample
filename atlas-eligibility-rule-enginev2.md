# Atlas — Next Iteration: Externalizing Eligibility into a Rule Engine

**Status: implemented and shipped.** Sections 1–10 below are the original design plan. Everything in them has been built and is live in the published console (`advisor-console-rule-engine.html`, toggle "Rule engine ON" in the top bar). **Section 11** documents Version 2 (12 offerings, a second FA with a scoped book, the explain popover). **Section 12** documents Version 3: a real, independently-sourced policy pack was integrated in place of several v2 assumptions it corrected. Read section 12 first if you want the current state.

---


## 1. The problem with today's model

Atlas currently stores eligibility as a **verdict someone typed by hand**:

```js
programs: { privateBanking:'enrolled', directIndexing:'eligible', lending:'eligible', ... }
overlays: { taxManagedSMA:'enrolled', tlhOverlay:'eligible', ... }
```

`eligible` is an assertion with no derivation, no reason, no source, and no way to replay "why." When policy changes (a minimum moves, a tax rule tightens), every household record must be re-typed, and nothing can answer *why* Okonkwo is eligible for direct indexing or *what* would change that. The cross-sell radar and tax desk read these strings directly, so a wrong string silently produces a wrong recommendation. This is exactly the anti-pattern the rule-store schema exists to remove: **eligibility should be computed, sourced, and versioned — not stored as a bare status.**

---

## 2. Target architecture (from the schema docs)

Four moving parts, each with a single responsibility. The key discipline is that the **kernel is a flat predicate walk** — all the "how do we know" logic is pushed into the derive layer, and all cross-offering logic is pushed into a separate composition pass.

1. **Derive layer (SD layer).** Turns raw client data (holdings, allocation, account attributes) into flat **derived fields** — `account.tax_status`, `account.is_all_etf`, `account.alt_capacity_pct`, `fa.qualified_for_offering`, etc. Fail-closed: an unknown field is never guessed.
2. **Rule store (data, not code).** Per-offering rule lists. Each rule is a `{predicate, effect}` pair with a `source_doc` and a `compile_source`. Editing eligibility means editing JSON, not shipping code.
3. **Kernel.** Evaluates one offering's rules against one evaluation tuple → a per-offering verdict (`ELIGIBLE / CONDITIONAL / INELIGIBLE / NEEDS_REVIEW`) carrying reasons, disclosures, and scope carve-outs.
4. **Composition pass.** Runs *after* all per-offering verdicts exist, applying offering×offering rules (`SUPERSEDES`, `INCOMPATIBLE_WITH`, `COMPATIBLE_WITH`, `SCOPE_CARVEOUT_WITHIN_COMPOSITION`) to produce the final composition verdict.

```
raw household ──▶ derive layer ──▶ facts ──▶ kernel (per offering) ──▶ composition pass ──▶ VerdictBundle
                (SORs / holdings)          (flat predicate walk)     (offering × offering)
```

### Effect types the kernel understands

| Effect | Meaning | Verdict impact |
|---|---|---|
| `REQUIREMENT` | predicate must be true | false → `INELIGIBLE` |
| `CONDITION` | must be satisfied / disclosed | softens to `CONDITIONAL`, attaches disclosure |
| `SCOPE_CARVEOUT` | a subset is out of scope | verdict unchanged; annotates excluded holdings |
| `NEEDS_REVIEW` | route to a human desk | → `NEEDS_REVIEW` |
| `DISCLOSURE` | mandatory language | none |

### `failure_class` — who sees the reason

This is the subtlest requirement and the one Atlas most needs. A failed requirement's reason is routed by `failure_class`:

| `failure_class` | Verdict | Client-facing? |
|---|---|---|
| `CLIENT_ELIGIBILITY` | `INELIGIBLE` | Yes — the real reason renders |
| `FA_SCOPE` | `INELIGIBLE` | **No** — diverted to `internal_only_reasons`; client sees a generic message |
| `MANAGER_ADJUDICATION` | `NEEDS_REVIEW` | **No** — routed to the SMA/credit/insurance desk |

The engine keeps `reasons` and `internal_only_reasons` on separate fields so the chat/narration layer can never leak an FA-internal reason to a client.

---

## 3. Mapping Atlas's current fields to the new model

Every `eligible|enrolled|na` string becomes a *computed* per-offering verdict. The programs and overlays Atlas already shows map one-to-one to offerings in the rule store:

| Atlas today | Becomes offering | Illustrative derived predicates |
|---|---|---|
| `programs.directIndexing` | `directIndexing` (`DIRECT_INDEX_SMA`) | taxable · ≥ $250K · IAP enrolled · FA qualified · restriction feasibility (review) |
| `overlays.tlhOverlay` | `tlhOverlay` (QLH-class) | taxable · IAP · US resident · has harvestable equity · not TEM SMS · FI carve-out |
| `overlays.taxManagedSMA` | `temOverlay`/`TER`-class | same base + strategy-universe lookup |
| *(new)* | `dtlhOverlay` (`DTLH`) | taxable · CIO ETF model · **is_all_etf** · in DTLH universe |
| `programs.alternatives` | `alternatives` | qualified purchaser · sleeve capacity (`target.alt − current.alt`) · ≥ $5M |
| `programs.privateBanking` | `privateBanking` | cash ≥ $1M |
| `programs.lending` | `lending` | pledgeable value ≥ $250K · low-basis → manager review |
| `programs.trustEstate` | `trustEstate` | segment ∈ {Private Wealth, HNW} |
| `programs.insurance` | `insurance` | protection gap → specialist review |

`enrolled` stops being an eligibility state — it's an *enrollment fact* that lives on the account and is read by the composition pass (e.g. "already enrolled in TLH; now considering DTLH"). Eligibility answers "may they enroll"; enrollment answers "are they enrolled."

### Derived fields Atlas can compute today vs. must start sourcing

The derive layer computes most fields straight from the existing holdings model: `is_all_etf`, `contains_fixed_income`, `has_harvestable_equity` (any equity lot with `mv < cost`), `cash_value`, `alt_capacity_pct`, `has_low_basis_position`, `advisory_value = aum`. Six fields are **new inputs the next iteration must source** (they don't exist in the current mock, and guessing them would defeat the point):

`account.tax_status` · `account.program_enrollment` (IAP managed/custom) · `client.residency_country` · `client.qualified_purchaser` · `account.strategy_type` + `in_universe_DTLH`/`is_tem_sms` (models & programs SOR) · `fa.qualified_for_offering` (FA licensing SOR).

Until those feeds exist, the derive layer defaults them explicitly (and visibly), never silently.

---

## 4. Versioned eligible-universe tables

"Consult your advisor for the list of eligible strategies" means the eligible set is a **curated, dated list** maintained on its own schedule — it must be versioned separately from the rule that references it, so "was this strategy DTLH-eligible on June 11?" is reconstructable. The rule store carries `eligible_universe_versions` with `effective_date` (the "as of" in the document) and `published_date` (the document's own date) stored separately for bitemporal replay. The kernel never reads these tables directly — the derive layer resolves membership into a boolean (`account.in_universe_DTLH`) before evaluation, keeping the predicate flat (`in_universe_DTLH == true`).

---

## 5. Composition pass — the offering×offering rules Atlas needs

Per-offering verdicts can't express "DTLH supersedes TLH" or "overlays can't touch TEM SMS holdings." Those run in the composition pass over the full set of an account's verdicts:

- **`SUPERSEDES`** — on a CIO all-ETF sleeve, `dtlhOverlay` supersedes `tlhOverlay`; TLH stays individually eligible but its composition verdict becomes `SUPERSEDED` with a "enroll in DTLH only" note.
- **`INCOMPATIBLE_WITH`** — overlays vs. TEM SMS holdings → `CONFIRMED_INELIGIBLE`.
- **`COMPATIBLE_WITH`** — explicit positive confirmation ("TLH and DTLH can be combined"), so the chat answers "can I stack these?" affirmatively instead of silence-equals-yes.

Composition verdicts: `CONFIRMED_ELIGIBLE`, `ELIGIBLE_WITH_CARVEOUT`, `SUPERSEDED`, `CONFIRMED_INELIGIBLE`, `NEEDS_REVIEW`.

---

## 6. Proof: the reference engine on real Atlas households

`next-iteration/` contains a dependency-free implementation — `eligibility-engine.js` (kernel + composition), `rule-store.json` (the externalized rules), `derive.js` (fact derivation), and `demo.js`. Running it against four Atlas households (`node demo.js`) produces, verbatim:

- **Henderson (taxable, $48.2M):** Direct Indexing ✓; TLH ✓ **with a `FIXED_INCOME_HOLDINGS` carve-out**; DTLH ✗ (holds MUB/AGG → not solely ETFs, not in the DTLH universe); Lending → **NEEDS_REVIEW** with the low-basis reason kept **FA-internal**.
- **Okonkwo (taxable, $31.6M):** TLH ✗ — *"No harvestable equity positions"* (every equity lot is at a gain), the kind of derivation a typed status silently gets wrong.
- **Reyes-Marín (taxable, all-ETF CIO model, in DTLH universe):** DTLH ✓; **TLH `SUPERSEDED`** by DTLH via the composition pass; Alternatives ✗ (not a qualified purchaser).
- **Delacroix IRA (tax-deferred, $2.1M):** Direct Indexing / TLH / DTLH all ✗ on `tax_status`; the DI FA-scope failure is correctly diverted to `[FA-internal]` and never shown as a client reason; Trust & Estate ✗ on segment.

Every verdict carries its reason, its source clause, and (where relevant) its carve-out and composition note — none of which the current string model can produce.

---

## 7. What changes in the Atlas app

1. **Drop the `programs`/`overlays` status maps** from each household; add the small `account` fact block (tax status, IAP enrollment, residency, QP, strategy classification) the derive layer needs.
2. **Bundle the three engine files** and call `evaluateAccount(deriveFacts(hh), ruleStore)` once per household; memoize per render.
3. **Cross-Sell Radar** reads `composition_verdict === 'CONFIRMED_ELIGIBLE'` (an eligible-but-not-enrolled opening) instead of the `'eligible'` string, and shows the rule-sourced *reason* in the "Why it fits" column — grounded, not hand-written.
4. **Tax Overlay Desk** reads `tlhOverlay` / `dtlhOverlay` verdicts and surfaces the `FIXED_INCOME_HOLDINGS` carve-out and the held-away wash-sale disclosure the rules attach.
5. **Ask Atlas** grounds eligibility answers on verdict objects, citing the rule and `source_doc`, and honors the client-facing/FA-internal split when it narrates. A new **`composition_check`** intent answers "can I stack X and Y?" from the composition pass.
6. **`bookContext()`** serializes the derived verdicts (with reasons) instead of the raw strings, so the live model is grounded on computed eligibility.

---

## 8. The boundary: eligibility vs. service behavior

The schema draws a hard line Atlas must respect: **if a clause determines whether enrollment is permitted, it is eligibility (a rule). If it describes how the service behaves after enrollment, it is not.** Atlas's tax-alpha math, the `TAX_RATE` blend, wash-sale screening, harvest-year running balances, and replacement-security selection are **service behavior** — they belong to a Tax Engine lane (deterministic, signed, methodology-versioned, as in `tax_engine_worked_examplejune24.md`), never the rule store. Concretely, the rule store decides *whether* a household is eligible for the TLH overlay; the Tax Engine decides *how much* tax alpha the harvest produces. Keeping these apart is what lets the eligibility kernel stay a flat, replayable predicate walk.

Three things the docs name as **stubbed, visible, not load-bearing** — carry them the same way: a **Harvest Ledger** (per-account, per-tax-year running balances), a **Substantially-Identical registry** (VOO/IVV = identical; AAPL/MSFT = not; unmapped → `UNKNOWN`, never guessed), and a **wash-sale scope** model that honestly distinguishes book-scope (the firm can screen) from client-scope (held-away accounts are the client's Form 8949 responsibility). The mandatory `held_away_wash_sale_disclosure` CONDITION already rides on every overlay/DI verdict in the reference rule store.

---

## 9. Shelf comparison (optional, from the SMA spreadsheet)

`tax_managed_sma_visible_rows.xlsx` is a cross-manager grid (Franklin Templeton, PGIM, Parametric/Eaton Vance, Aperio, Goldman, Natixis, Columbia) with fee bps, minimums, TLH frequency, tracking error, and concentration limits. That's a `SHELF_CATALOG_VERSION` — distinct from eligibility (it compares *products*, not gates a client) — feeding a `solution_compare` capability: "when does direct indexing make sense vs. an ETF for this client?" answered as criteria + the client's actual eligibility verdicts + catalog comparison + citations, never a bare recommendation. Structured cells compile as catalog rows; prose cells ("High Level View") are cited at query time, not copied into the table. This is a natural follow-on once eligibility is externalized, but not required for the core migration.

---

## 10. Suggested sequence

1. Land the engine + rule store as-is (done, `next-iteration/`); wire `deriveFacts`/`evaluateAccount` into Atlas behind a flag, rendering verdicts beside the current strings to diff them.
2. Add the `account` fact block to the data model; stand up the six new derived fields as explicit stubs.
3. Flip Cross-Sell Radar, Tax Desk, and the client deep-dive to read verdicts; delete the `programs`/`overlays` strings.
4. Ground Ask Atlas on verdicts; add the `composition_check` intent.
5. (Optional) Add the shelf catalog + `solution_compare`.

Items 1–3 are the core of "externalize eligibility into a rule engine"; 4–5 are the payoff that a typed-status model could never support.

---

## 11. Version 2 — what actually shipped, and how eligibility works now

Version 1 wired one engine into the console with 4 offerings on 8 households. Version 2, in response to "add a few more DTLH/QLH/TEM cases, more tax-management and IAP-eligibility cases, 2x the households, and add another FA," rebuilt the rule store, the book, and the eligibility surface around a **second advisor with a different license scope** — which turned out to be the most revealing addition, because it's the first thing that makes the `failure_class` routing (§7, §11.4 below) actually *matter* rather than just being correct in principle.

### 11.1 The offering set: 4 → 12

Every household-eligible "thing" in Atlas is now one entry in `RULE_STORE.offerings`, each a `{label, rules[]}` — a flat list of `{rule_id, effect, predicate, ...}` records, exactly the shape in §2. Twelve offerings now exist:

| Offering id | Label | New in v2? |
|---|---|---|
| `directIndexing` | Direct Indexing | — |
| `tlhOverlay` | Tax-Loss Harvesting Overlay | — |
| **`qlhOverlay`** | **Quarterly Loss Harvesting (QLH)** | ✅ new |
| `taxManagedSMA` | Tax-Managed SMA (TER) | retrofitted (see 11.2) |
| **`temSms`** | **TEM Style Manager Strategy** | ✅ new |
| `dtlhOverlay` | Direct TLH Overlay (DTLH) | retrofitted |
| `transition` | Transition Management | — |
| `charitable` | Charitable / Gifting Overlay | — |
| `alternatives` | Alternatives | — |
| `privateBanking` | Private Banking | — |
| `lending` | Securities-Based Lending | — |
| `trustEstate` | Trust & Estate | — |
| `insurance` | Insurance / Annuity | — |

**`qlhOverlay`** mirrors TER's structure but gates strategy eligibility with an **OR predicate** — the first place this engine uses a compound predicate instead of a flat AND chain:

```js
predicate: { OR: [
  { AND: [ {field:'account.strategy_type', op:'IN', value:['STYLE_MANAGER_EQUITY','MUTUAL_FUND_SLEEVE']},
           {field:'account.in_universe_QLH', op:'EQ', value:true} ] },
  { field:'account.strategy_type', op:'IN', value:['CIO_ETF_MODEL','CIO_MIXED_MODEL'] }
]}
```
Read as: *a style-manager or mutual-fund sleeve qualifies only if it's on the QLH-eligible universe list; a CIO ETF or mixed model qualifies unconditionally.* The kernel's `evalPredicate` already supported `AND`/`OR`/`NOT` nodes recursively (§2's "flat AST walk" claim holds — nesting predicates doesn't change the kernel, it's still one dispatcher), so this needed zero kernel changes, only a new rule.

**`temSms`** answers a different question than the overlays. The overlays ask *"can this overlay be applied to this account's existing holdings?"* — TEM SMS asks *"can this account invest into a TEM Style Manager Strategy in the first place?"* Its rules:
```
SMS.req.fa        — FA must be licensed for temSms
SMS.req.taxable   — taxable accounts only
SMS.req.us        — US residents only
SMS.req.iap       — must be enrolled in the advisory program
SMS.req.not_custom — REQUIREMENT: program_enrollment != IAP_CUSTOM_MANAGED
SMS.req.roster    — REQUIREMENT: is_tem_sms == true (the strategy must be on the TEM SMS roster)
```
`SMS.req.not_custom` is the schema's Gap-1 nuance (§8.5 of `rule_store_schema_extension_tem.md`): Custom Managed Strategies block **TEM SMS specifically**, but do *not* block TER/QLH/DTLH. Two households make this concrete — `eshun` (Custom Managed, wants TER) is **eligible**; `duarte` (Custom Managed, wants TEM SMS) is **ineligible**, with the message *"TEM Style Manager Strategies are stand-alone investments and are not available within Custom Managed Strategies."* Same `program_enrollment` value, opposite outcome, because it's a different offering asking a different question — that contrast is the whole point of keeping eligibility externalized instead of a single enrollment flag.

`taxManagedSMA` (TER) and `dtlhOverlay` (DTLH) were **retrofitted**, not just left alone: TER gained the same OR-gated strategy-eligibility check as QLH (previously it had no strategy gate at all — any taxable, IAP-enrolled account was TER-eligible, which was too permissive), and both TER and DTLH gained an explicit `not_sms` requirement (previously only `tlhOverlay` blocked TEM-SMS holdings; now TER, QLH, and DTLH all do, matching the schema's "all TEM Overlay Services" language).

### 11.2 FA-scope is now enforced on every offering, not just one

This was a real gap in the first pass, caught by testing rather than by re-reading the schema: only `directIndexing` had an FA-qualification rule. Every other offering had no `fa.*` predicate at all, so an advisor's licensing scope was invisible everywhere except Direct Indexing. Version 2 adds one `<PREFIX>.req.fa` `REQUIREMENT` to **all twelve offerings**:

```js
{rule_id:'DTLH.req.fa', effect:'REQUIREMENT',
 predicate:{field:'fa.qualified_for_offering', op:'CONTAINS', value:'dtlhOverlay'},
 failure_class:'FA_SCOPE',
 failure_message:'This offering is not in your current qualification scope. Contact your branch manager to request access.',
 source_doc:'tem §7'}
```
Same rule shape, one line, one offering id substituted, twelve times over. This is the section 7 `failure_class` mechanism finally doing real work: when this rule fails, the reason is diverted to `internal_only_reasons` and never appears in the client-facing `reasons` array — confirmed directly against the engine's own output (not just the UI) for the two clearest cases:

```json
// farkas (Marcus's client) on dtlhOverlay — client-level facts are all fine
{ "verdict": "INELIGIBLE", "reasons": [], "internal_only_reasons": [
    { "rule_id": "DTLH.req.fa", "failure_class": "FA_SCOPE",
      "message": "This offering is not in your current qualification scope..." } ] }

// giordano (Marcus's client) on alternatives — same shape, different offering
{ "verdict": "INELIGIBLE", "reasons": [], "internal_only_reasons": [
    { "rule_id": "ALT.req.fa", "failure_class": "FA_SCOPE", ... } ] }
```
`reasons` is empty in both — there is nothing to show a client here, because the client didn't fail anything; their own advisor's license did. The explain popover (§11.5) renders this distinction visibly: the top red "reason" callout, which only reads from `reasons`, stays blank, and the FA-internal message appears lower down, explicitly labeled, in the Notes section.

### 11.3 The book: 8 → 16 households, across two advisors

`ACCOUNT_FACTS` (the per-household fact overrides the derive layer reads) now covers all 16 households, and every household object in `BOOK_ALL` carries a new top-level field, `advisor_id`, fixing which advisor services it:

| Advisor | Households |
|---|---|
| **Dana Whitfield** — Sr. Wealth Advisor, full 13-offering license | henderson, okonkwo, reyes, sorensen, abernathy, kaplan, nakamura, delacroix, bianchi, callahan |
| **Marcus Webb** — Associate Advisor, missing `dtlhOverlay`, `qlhOverlay`, `alternatives` | duarte, eshun, farkas, giordano, han, ibarra |

`myBook()` — new — is `BOOK_ALL.filter(c => c.advisor_id === state.fa)`. Every book-wide aggregate that used to be a `const` computed once at load (`totalAUM`, `totalRev`, `totalHarvest`, `meetings`, `drifts`, `cioMisaligned`, `topClients`, `crossSell`) is now a **zero-arg function** that recomputes from `myBook()` on every call, so switching the active FA and re-rendering is enough to refilter the entire app — Today's hero stats, the NBA cards, Book of Business, Cross-Sell Radar, the Tax Overlay Desk, and the chat's grounding context all flow from the same `myBook()` call. `byId` and the underlying `BOOK_ALL` array are the only things that still see the *full* 16-household roster — needed so `viewClient` can tell the difference between "no such client" and "that client belongs to the other advisor" (see 11.6).

Each new household was built to exercise a specific rule, and the household's **actual holdings**, not just its `ACCOUNT_FACTS` override, have to back that up — see 11.7 for why that distinction turned out to matter:

| Household | Advisor | Demonstrates |
|---|---|---|
| `sorensen` | Dana | QLH eligible via the universe list; TER ineligible (not on TER's list) — same strategy type, opposite verdict per offering |
| `abernathy` | Dana | A **Private Foundation** (a genuinely tax-exempt entity type) — ineligible for every tax-managed offering on `tax_status` alone |
| `kaplan` | Dana | `program_enrollment: 'NONE'` — not enrolled in the advisory program at all, blocking every IAP-gated offering |
| `nakamura` | Dana | A CIO *mixed* model (one non-ETF fund) — eligible for TER/QLH via the CIO branch of the OR-gate, but ineligible for DTLH specifically, because DTLH's `is_all_etf` gate is strict |
| `bianchi` | Dana | Already holds a TEM SMS position — blocks TER, TLH, QLH, *and* DTLH simultaneously via the shared `not_sms` requirement |
| `callahan` | Dana | The inverse of bianchi: not yet in any TEM strategy, wants to invest *into* one — `temSms` offering itself is eligible |
| `duarte` | Marcus | Custom Managed + wants TEM SMS → ineligible (`SMS.req.not_custom`) |
| `eshun` | Marcus | Custom Managed + wants TER → eligible (Custom Managed only blocks TEM SMS, not TER) |
| `farkas` | Marcus | Client-eligible for both QLH and DTLH on an all-ETF CIO sleeve — but Marcus isn't licensed for either, so both come back `Ineligible` / FA-internal |
| `giordano` | Marcus | Qualified purchaser with open alternatives capacity — client-eligible, FA-blocked (Marcus isn't licensed for alternatives) |
| `han` | Marcus | Relocated abroad — ineligible for every US-resident-only offering (TER/QLH/DTLH/TEM SMS); Direct Indexing has no residency gate, so it stays eligible |
| `ibarra` | Marcus | Restriction request beyond shelf tolerance → Direct Indexing `NEEDS_REVIEW`/`MANAGER_ADJUDICATION`; a low-basis position → Lending `NEEDS_REVIEW` too |

### 11.4 Composition rules extended for QLH

§6's composition pass (`SUPERSEDES` / `INCOMPATIBLE_WITH` / `COMPATIBLE_WITH`) now covers QLH alongside TLH and DTLH:

- `COMP-001b`: **DTLH supersedes QLH** on a CIO ETF sleeve (mirrors the existing DTLH-over-TLH rule) — this is the schema's actual documented relationship; the original TLH-vs-DTLH pairing was always a simplification since generic `tlhOverlay` isn't a named schema offering.
- `COMP-003b` / `COMP-003c` / `COMP-003d`: QLH, DTLH, and TER are each independently marked `INCOMPATIBLE_WITH` TEM-SMS holdings (alongside the original TLH rule) — belt-and-suspenders with the `not_sms` requirement already on each offering, matching the schema's "defense in depth" language in §8.2.
- `COMP-005` / `COMP-006` / `COMP-007`: the full TER↔QLH↔DTLH compatibility trio, so a "can I stack these?" question returns an explicit affirmative rather than silence.

`farkas` (all-ETF CIO sleeve, on both the DTLH and QLH universe lists) is the household that exercises `COMP-001b` end to end: QLH is eligible on its own facts, but its `composition_verdict` resolves to `SUPERSEDED` once DTLH is in play — before the FA-scope layer separately blocks both from ever reaching Marcus's clients (11.2).

### 11.5 The explain popover: verdict, reason, and the exact fields behind it

Every verdict in the deep-dive grids, the Cross-Sell Radar, and the Tax Overlay Desk now has a small **ⓘ** button. Clicking it opens a popover built directly from a new `trace[]` array the kernel now records — one entry per rule evaluated, each carrying its `rule_id`, `effect`, `passed` boolean, `source_doc`, and (via a new `explainLeaves()` walker that recurses through `AND`/`OR`/`NOT` nodes) every **leaf predicate** it touched: the field name, the operator, the expected value, and the account's *actual* value for that field.

The popover shows, in order: the verdict pill; the client-facing reason (if any); an **"Inputs evaluated"** table of every derived field the offering's rules read, with a ✓/✗ per row so a failing field is visually obvious; then a Notes section for scope carve-outs, composition notes, disclosures, and FA-internal reasons (each labeled). This is the direct payoff of externalizing eligibility: nothing in this popover is written by hand per-household — it's the same `trace` the kernel produces for every verdict, rendered generically.

### 11.6 Book isolation: `viewClient` now checks ownership, not just existence

Before v2, `viewClient(id)` only checked `if (!c) return viewBook()`. With two advisors sharing one underlying roster (`BOOK_ALL`), that's not enough — Marcus could otherwise open a deep-dive for one of Dana's clients via a stale link. The guard is now:

```js
function viewClient(id){
  const c = byId(id);
  if (!c || c.advisor_id !== state.fa) return viewBook();
  ...
```
Switching the FA also clears `state.client` and resets to the Today view, and clears the engine's verdict cache (`_engCache`) — cheap, and defensive against any future change that makes a verdict depend on *who's viewing* rather than only on *who services the account* (today it doesn't: `fa.qualified_for_offering` is resolved from the household's own `advisor_id` via `FA_PROFILES`, not from `state.fa`, so a household's verdicts are identical no matter who's looking — only which households are visible changes per viewer).

### 11.7 Two bugs worth naming, because the fixes are the interesting part

**An empty book crashed the Today view.** `drifts()`, `cioMisaligned()`, and two chat responses all did `someArray[0].field` on the assumption the array was never empty. Marcus's six households happen to have zero concentration/allocation breaches and zero CIO-misaligned portfolios (all six were written with `concentration:[]` and `cio.score:'Low'`), so switching to his book threw `Cannot read properties of undefined (reading 'c')` the first time it was tried. Fixed by guarding every `[0]` access with a length check and rendering an explicit empty state ("No concentration or allocation breaches in this book right now.") instead of assuming non-empty. This is a generic lesson for anything that aggregates a *filtered* subset rather than the whole roster: the moment the book can be scoped (by advisor, by segment, by anything), "the top item" needs a defined behavior for zero items.

**A household's claimed strategy classification contradicted its own holdings — and the engine caught it.** `reyes` was initially given `strategy_type: 'CIO_ETF_MODEL'`, `is_all_etf: true` in `ACCOUNT_FACTS`, to build a second DTLH-supersede demo. But `reyes`'s actual `holdings[]` include **TSLA**, a single stock, and **ARKK**, a thematic ETF outside the recognized set — so the derive layer's holdings-based `is_all_etf` computation (which scans real positions, not the override) correctly came back `false`, and DTLH correctly returned `Ineligible` on "holds one or more non-ETF securities," contradicting the household's own claimed classification. The fix was not to override the engine — it was to fix the *data*: `reyes` is now honestly classified `STYLE_MANAGER_EQUITY`, not on either the TER or QLH universe, which matches an aggressive concentrated stock-picker far better anyway. The DTLH-supersede demonstration lives entirely on `farkas`, whose holdings (`VTI, VXUS, AGG, CASH` — all genuinely ETFs) actually back up the classification. The lesson, and the reason this is worth documenting rather than quietly fixing: **a rule engine that trusts a claimed classification over the underlying facts isn't actually protecting anything** — `is_all_etf` deriving from real holdings rather than from an assertable flag is exactly the fail-closed discipline §1's "eligibility should be computed, not stored as a bare status" was arguing for in the first place, and it worked as designed even against data I wrote myself.

---

## 12. Version 3 — a real, independently-sourced policy pack replaces several v2 assumptions

Version 2 built a plausible rule store from a schema *description*. Version 3 integrates an actual **policy pack** — `atlas-rule-store.json`, a dependency-free reference engine (`engine.mjs`), a JSON Schema, a 23-test suite, and worked examples — extracted from three real Merrill documents (an IAP wrap-fee brochure, a TET term sheet, and a Tax-Efficient Management guide for Guided Investing). Its own README is explicit that it is "an extracted draft, not an approved firm policy," and — more importantly for this project — that it **corrects several v2 design decisions that were never actually sourced from anything**. This section documents what changed, why, and what broke along the way.

### 12.1 The corrections, named plainly

The pack's `unresolved_issues` list (`G01`–`G15`) calls out exactly which v2 assumptions were invented rather than sourced. Five of them directly contradict what shipped in Version 2:

| v2 assumption | Pack's finding (`unresolved_issues`) | What changed |
|---|---|---|
| Every offering has its own FA-license gate (`ALT.req.fa`, `DTLH.req.fa`, …, added to all 12 offerings) | **G05**: "Every offering requires a distinct FA license — only designated products/strategies actually require one" | FA-scope now runs through **one** gate, `iapEnrollment`, checked per target strategy (§12.4) |
| DTLH supersedes QLH/TLH; a TER↔QLH↔DTLH compatibility trio | **G03**: "DTLH supersedes QLH/TLH and all IAP overlays can stack — unverified in supplied sources" | Replaced with the pack's 4 sourced composition rules; an unspecified pairing now returns `NEEDS_REVIEW`, never assumed-compatible |
| An existing TEM SMS holding blocks every overlay; Custom Managed blocks TEM SMS enrollment | **G04**: "Not [validated] in supplied PDFs" | Both rules removed; `bianchi`/`duarte` (built to demonstrate them) were re-homed onto rules the pack does source (§12.5) |
| Direct Indexing has a $250K minimum | **G07**: "No universal $250K figure — that number came from a different firm's public marketing page" | Replaced with `target_strategy.in_approved_directIndexing_roster`, an external, versioned catalog check |
| `is_all_etf` computed from a ticker allowlist | **G10**: "Classify instrument type from a security master, independent of asset class" | DTLH's ETF-only requirement is now an authoritative fact (MGI's `target_strategy.is_eligible_cio_etf_strategy`), not a computed heuristic |

None of this is a small correction. It's the difference between a rule store that *reads* like real policy and one that is traceable, clause by clause, to an actual document — with the gaps in that traceability written down as gaps, not silently smoothed over.

### 12.2 The kernel became three-valued

The single biggest behavioral change: **missing data is no longer treated as `false`.** The v2 kernel's `evalPredicate` returned `false` for an undefined field, which meant an unpopulated fact silently produced `INELIGIBLE` — indistinguishable from a fact that was actually checked and failed. The pack's reference evaluator (`engine.mjs`) instead returns `null` (UNKNOWN) for a missing/null/`'UNKNOWN'` fact, and threads that third value through `AND`/`OR`/`NOT` correctly (`false` always dominates; `null` only propagates when nothing is definitively `false` or `true`). An UNKNOWN `REQUIREMENT` routes to `NEEDS_REVIEW`, not `INELIGIBLE` — the system's way of saying "I don't know" instead of quietly guessing "no." This was ported byte-for-byte into the browser kernel (`evalPredicate`, `evaluateOffering` in `advisor-console-rule-engine.html`), including the strict `typeof`-checked `EQ`/`NEQ` (a type mismatch is also UNKNOWN, not a definite answer) and the narrowed operator set (`EQ`, `NEQ`, `IN`, `CONTAINS`, `GTE` — the pack's schema deliberately doesn't support `LT`/`GT`/`EXISTS`/etc., forcing every threshold to be pre-resolved into a boolean by the derive layer rather than compared inline).

One consequence worth naming: most of the book is **deliberately left with unverified offering profiles**. `policy.offering_profile_verified` and `account.offering_profile_requirements_met` default to `false`/`null` for every household except a small, explicitly-commented set of "synthetic fixture" demo cases — exactly mirroring how the pack's own `test.mjs` labels its fixtures ("All true approvals below are synthetic external-profile fixtures, not policy supplied by PDFs"). A household with no override doesn't show a clean verdict; it shows `NEEDS_REVIEW`, with the trace naming exactly which field is unresolved. That's not a gap in the demo — it's the demo. A rule engine that defaulted every unpopulated household to "eligible" would be worse than the typed-string model it replaced.

### 12.3 Two new offerings, and what they actually ask

**`transition`** is now **Tax Efficient Transition (TET)** — the pack's real offering, not the two-rule placeholder v2 had under that id. TET asks a materially different question from the overlays: not "can this overlay apply to what's already held" but "can this account transition into a new target strategy tax-efficiently." Its rules check domesticity, a PAS exclusion, an explicit Direct-Indexing-target exclusion, a target-strategy universe check, minimums, and a required budget election — and three `SCOPE_CARVEOUT`s (missing cost basis, individual fixed income, TMA income cash) that exclude specific lots **without rejecting the whole account**, matching the pack's explicit instruction: "Missing basis excludes the affected securities from TET at enrollment, not automatically the entire account."

**`iapEnrollment`** is the pack's actual prerequisite gate — six rules (agreement executed, account type eligible, separate account per strategy, strategy minimums met, PAS contract executed, and the one FA-scope check) that every other IAP offering implicitly depends on but none of them re-check.

**`mgiTer`/`mgiQlh`/`mgiDtlh`** put a second **program namespace** (`MGI`, Guided Investing) into the same rule store as `IAP`, each offering declaring `program_scope`. `evaluateOffering` checks this before evaluating a single rule: an MGI offering evaluated against an IAP account returns `INELIGIBLE`/`PROGRAM_SCOPE` immediately, and vice versa — proven directly (`sato.taxManagedSMA → INELIGIBLE, reason: PROGRAM_SCOPE`) and matching the pack's own test, `'MGI cannot be evaluated under IAP'`.

### 12.4 FA-scope, corrected: one gate, checked per target strategy

The pack's actual mechanism is a single `OR` predicate on `iapEnrollment`: `strategy.requires_qualified_advisor == false` **OR** `fa.qualified_for_selected_strategy == true`. Both facts are contextual to *which strategy is being considered*, not fixed properties of the account. Version 3 implements this generically rather than per-household:

```js
const REQUIRES_QUALIFIED_ADVISOR = new Set(['dtlhOverlay','qlhOverlay','alternatives']);
// in deriveFacts(hh, offeringId):
strategy: { requires_qualified_advisor: REQUIRES_QUALIFIED_ADVISOR.has(offeringId) },
fa: { qualified_for_selected_strategy: faProfile.qualified_for_offering.includes(offeringId) }
```
`deriveFacts` now takes the **offering id being evaluated**, not just the household — because the pack's own `offering_facts` pattern (seen in `example-input.json`) means facts genuinely vary by which offering is in view, not only by which client. Any offering's popover for an IAP household now also evaluates `iapEnrollment` in that offering's specific context and surfaces the result as a **separate prerequisite note** — deliberately not folded into the offering's own trace, so the pack's rule bodies stay byte-faithful to source. This is verified directly: `farkas` (Marcus's client) shows DTLH itself as `Eligible` — every client-level fact passes — while the prerequisite note reads *"Prerequisite (IAP enrollment) · Qualification is required for designated strategy types/products…"*, correctly separating "is the client eligible" from "is the advisor licensed," which the v2 per-offering duplicate gate could not do.

`alternatives`/`lending`/`privateBanking`/`trustEstate`/`insurance`/`charitable` — offerings the pack explicitly says it doesn't cover — keep their own v2-style FA gates. That's a legitimate house-policy choice, not a corrected error, so it's left alone.

### 12.5 Re-homing the two demo cases the pack invalidated

`bianchi` and `duarte` were built in Version 2 to demonstrate rules `G04` says were never sourced. Rather than delete the cases, they were moved onto rules the pack *does* source:

- **`bianchi`** now demonstrates `account.has_pas_strategy == true` — a real IAP-brochure rule ("MAA TEM overlays are unavailable for accounts invested in a PAS Style Manager Strategy") — blocking TER, QLH, DTLH, and TET simultaneously.
- **`duarte`** now demonstrates `temSms`'s roster check failing outright (`target_strategy.in_approved_temSms_roster: false`), a clean, singular `INELIGIBLE` distinct from `bianchi`'s PAS block.
- **`callahan`**'s story ("not yet in a TEM strategy, wants to invest into one") is unaffected — it never depended on the invalidated rules — and now runs through the pack's real `temSms.roster` check instead of the old `is_tem_sms` flag, which no rule in the pack reads at all and was removed from `ACCOUNT_FACTS` as dead data.

### 12.6 Composition: a fourth relation, and "unknown means review"

The pack's 4 composition rules use a different, flatter shape than v2's (`{offerings:[a,b], relation, message}` vs. v2's `offering_a`/`offering_b`/`scope_condition`), and a materially stricter default: **an offering pair with no matching rule elevates to `NEEDS_REVIEW`**, not silent compatibility. `evaluateComposition` was rewritten to match this exactly, including excluding `iapEnrollment` from pairwise composition (it's a prerequisite check, not a stackable service — the pack's own comment: *"not a stackable tax service"*).

Because composition only makes sense over a *specific set* under consideration — never "all offerings this household could ever have" — it's surfaced as a distinct **"TET-family service composition"** panel on the client deep-dive (IAP households only), evaluating `{transition, taxManagedSMA, qlhOverlay, dtlhOverlay}` together. `henderson` — independently eligible for TER and TET — proves the sharpest case in the whole rewrite: TET+TER and TET+QLH each resolve to `ELIGIBLE_WITH_CARVEOUT` (`COMP.TET.TER`/`COMP.TET.QLH`, both scope carve-outs), but the panel's overall verdict is **`CONFIRMED_INELIGIBLE`**, because `COMP.TET.DTLH` is a hard `INCOMPATIBLE_WITH` and the worst outcome always wins — exactly the pack's own test, *"TET + DTLH blocked."*

### 12.7 Holdings, honestly, again

`henderson`'s TET scope carve-outs are backed by two new holdings, not asserted flags — the same discipline the `reyes` lesson (§11.7) established: a legacy gift lot with `cost: null` (`scope.has_tet_missing_basis`, computed as "any lot with a null cost basis") and a genuine individual municipal bond, tagged `type: 'BOND'` so it's distinguishable from the household's *other* muni holding, `MUB`, which is a fund and correctly does **not** trigger the carve-out. Both scope-exclusion lot IDs shown in the popover (`LOT_HEND_GIFT_2011`, `AUSTIN-4.0-32`) are real holdings, not fabricated identifiers.

### 12.8 What this means for the app, concretely

- **16 households, unchanged in count**, plus one new one: `sato`, on `program: 'MGI'`, proving namespace separation (`mgiQlh` eligible, `mgiTer`/`mgiDtlh` ineligible on the same account).
- **16 offerings** now live in `RULE_STORE`: the pack's 10 (`iapEnrollment`, `taxManagedSMA`, `qlhOverlay`, `dtlhOverlay`, `transition`, `directIndexing`, `temSms`, `mgiTer`, `mgiQlh`, `mgiDtlh`) plus 6 house-policy offerings never claimed to be PDF-sourced (`alternatives`, `privateBanking`, `lending`, `trustEstate`, `insurance`, `charitable`).
- **A generic `tlhOverlay` offering no longer exists** — the pack has no such id, and no v2 offering silently aliases to `QLH` or `TER` in its place (the pack's own instruction: *"Generic `tlhOverlay` has no silent alias to QLH"*). It was removed from `overlayList` rather than left pointing at nothing.
- **Two bugs surfaced and fixed while wiring this in**, beyond the `bianchi`/`duarte` re-homing: a `SCOPE_CARVEOUT`'s `scope_key` lookup used flat-key indexing (`facts[r.scope_key]`) against a nested facts object — silently returning `undefined` for every scope check until caught by direct testing and fixed to use the same nested-path resolver (`_get`) as everything else; and a stray `fa.qualified_for_selected_strategy` fact was initially written as a flat top-level key instead of nested under `fa:{...}`, which would have made the kernel's nested-path lookup silently treat it as always-missing.

### 12.9 What's still explicitly out of scope

The pack's own README lists 15 unresolved issues; the ones most likely to matter next: eligible-universe membership (`in_universe_TER`/`QLH`/`DTLH`/`TET`) is still supplied as an override, not resolved against a real, versioned strategy catalog — the `universe_contract` from §4 still applies and isn't wired to a live catalog service. `service_behaviors` (32 specifications — TET budget defaults, wash-sale mechanics, replacement-security rules) remain outside the eligibility kernel entirely, as they must; nothing in this console executes them. And the pack's own instruction to **never send raw trace or internal reasons to a client-facing LLM** is implemented as `clientSafeView` in the kernel but isn't yet wired to anywhere in Atlas that talks to a client directly — Ask Atlas is advisor-facing, so today nothing in the app actually calls it. Wiring a genuinely client-facing surface to `clientSafeView` instead of raw verdicts would be the natural next step if that surface is ever built.


