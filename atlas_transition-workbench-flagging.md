# How the Transition Workbench Flags Proposals

This document explains, with real output from two actual households, exactly how the transition scenario workbench decides what to flag as a gap, what trades to propose, and how it computes the resulting target-state numbers. Both examples below are genuine API responses from `GET /api/transition/{household_id}?offering={offering}` — nothing here is illustrative prose; every number is what the running system actually returns.

The two households were deliberately chosen because they land on opposite ends of the workbench's behavior:

- **Henderson Family Trust → Direct Indexing**: a household with a real concentration breach, triggering a `required` gap and a large, multi-line trade proposal.
- **Sørensen Living Trust → Quarterly Loss Harvesting (QLH) Overlay**: a clean household with nothing to flag, triggering the `clear` gap state and a light, harvest-only trade proposal with zero sells.

---

## 1. The two-stage flagging pipeline

Every transition scenario runs through two independent stages, in this order:

1. **Gap analysis** (`_gap_analysis`) — answers "is there anything blocking, or worth noting before, this transition?" Produces a list of severity-tagged messages. This runs regardless of offering kind and never returns an empty list — see §4.
2. **Trade proposal** (`_propose_trades`) — answers "if this transition happens, what actually gets bought, sold, or harvested?" Only runs for `trade_modelable` offerings (§2 below); offerings that are purely relationship/paperwork-based get an onboarding checklist instead (not covered by this document, since it contains no "flagging" logic — it's a fixed per-offering step list).

The two stages are independent: a gap can be flagged even when zero trades are needed (Sørensen has a `clear` gap and 3 harvest trades — no sells at all), and gaps don't suppress trade generation — they're advisory information shown alongside the proposal, not a gate that blocks it.

---

## 2. Which offerings get trade proposals at all

```python
TRADE_MODELABLE = {'directIndexing','taxManagedSMA','qlhOverlay','dtlhOverlay','temSms','transition','mgiTer','mgiQlh','mgiDtlh'}
```

Only offerings in this set generate `proposed_trades` + `target_state`. Everything else (`alternatives`, `privateBanking`, `trustEstate`, `lending`, `insurance`, `charitable`, `iapEnrollment`) is treated as `kind: "procedural"` and gets a checklist instead — a portfolio-restructuring trade table would be meaningless for, say, opening a securities-based line of credit.

Both examples in this document — Direct Indexing and QLH Overlay — are `trade_modelable`.

---

## 3. Example A: Henderson Family Trust → Direct Indexing

### 3.1 Starting position

Henderson holds 9 positions worth $49.7M. The workbench's current-state summary surfaces the top 6 by market value:

| Symbol | Asset class | Market value | Weight | Unrealized G/L |
|---|---|---|---|---|
| NVDA | US Equity | $10.6M | 21.3% | +$8.5M |
| MUB | Municipal | $9.8M | 19.7% | −$0.6M |
| CASH | Cash | $7.3M | 14.7% | $0 |
| VTI | US Equity | $6.2M | 12.5% | +$1.1M |
| AGG | Fixed Income | $5.1M | 10.3% | −$0.5M |
| MSFT | US Equity | $4.9M | 9.9% | +$2.5M |

The household's own data already carries a concentration flag:

```json
"concentration_flags": [
  { "label": "NVDA single-stock", "pct": 22, "threshold": 10 }
]
```

### 3.2 What gets flagged, and why

```json
"gap_analysis": [
  {
    "severity": "required",
    "message": "Concentrated positions need trimming: NVDA single-stock at 22% (policy limit 10%)."
  }
]
```

**Why `required` specifically:** for `directIndexing` (and `temSms`), the gap-analysis function checks `hh['concentration']` directly — if the household's own concentration-flags list is non-empty, it emits a `required`-severity gap naming the exact position, its current percentage, and the policy limit, pulled straight from the household's own data (not recomputed or estimated). This is a `required` gap, not a `recommended` one, because a Direct Indexing transition cannot proceed with a >2x-over-limit single-stock position sitting inside it — the transition itself is precisely what's meant to fix this, so the gap is really saying "here is the concentration problem this transition addresses," not "here is a reason to decline."

For this same offering family, a second check would fire if cash allocation were under 2% (`recommended` severity — "Modest cash reserve helps stage the initial buy without forced timing") — it didn't fire here because Henderson is sitting at 13% cash, comfortably above that threshold.

### 3.3 How the trade list is built

For `directIndexing` (and `temSms`, `mgiDtlh`), the algorithm is **full equity-sleeve replacement**:

1. **Every US/Intl equity holding is sold.** Each sell's *reason* text depends on whether that specific position is itself a concentration problem:
   - If the position is a single stock **and** its weight exceeds 5%, the reason is `"Trim concentration (X% → basket weight)."`
   - Otherwise, the reason is the generic `"Reallocate into direct-indexed broad-market sleeve."`

   Henderson's actual sell list, with the reason each one got:

   | Sell | Value | G/L | Reason given |
   |---|---|---|---|
   | NVDA | $10.6M | +$8.5M | *Trim concentration (21.3% → basket weight).* — flagged because it's a single stock over 5% |
   | MSFT | $4.9M | +$2.5M | *Trim concentration (9.9% → basket weight).* — same reason, even though MSFT wasn't in the concentration_flags list itself; **any** single stock over 5% gets the concentration-framed reason, not just the one the household's data explicitly flagged |
   | VTI | $6.2M | +$1.1M | *Reallocate into direct-indexed broad-market sleeve.* — this is an ETF, not a single stock, so it gets the generic reason regardless of its 12.5% weight |
   | VXUS | $4.3M | −$0.6M | *Reallocate into direct-indexed broad-market sleeve.* — same, ETF |
   | NVDA (legacy gift lot, basis unresolved) | $0.4M | *(null)* | *Reallocate into direct-indexed broad-market sleeve.* — this is a **second, separate NVDA lot** with no cost basis on file; because `gl` can't be computed (`cost` is `null`), it never gets evaluated against the ">5% single-stock" concentration-reason check at all — that check needs a real weight/G/L to reason about, so an unresolved-basis lot always falls through to the generic sell reason no matter how large it is |

   This last row is worth dwelling on: the flagging logic is deliberately conservative about what it claims. It will *say* "trim concentration" only when it can actually support that claim with a computed value; an unresolved-basis lot gets sold (because it's still equity being reallocated) but gets the generic, non-committal reason rather than a concentration claim it can't back up with a number.

2. **Every *non-equity* holding already sitting at a loss over $1,000 gets harvested** (not sold-and-gone — `harvest` is its own action type, distinct from `sell`, meaning "realize this loss deliberately to offset the gains above, then carry the loss forward"):

   | Harvest | Value | Loss realized | Reason given |
   |---|---|---|---|
   | MUB | $9.8M | −$0.6M | *Harvest $600,000 of losses at onboarding; carry forward.* |
   | AGG | $5.1M | −$0.5M | *Harvest $500,000 of losses at onboarding; carry forward.* |

   Note what's *not* harvested: CASH (not a loss position, and cash is never a candidate), and the equity positions themselves aren't double-counted as harvests even though VXUS is at a loss — VXUS already appears above as a `sell` (it's equity, in scope for the sleeve replacement), so it isn't separately flagged as a harvest opportunity; the harvest pass only looks at positions *outside* the equity sleeve being sold.

3. **One consolidated buy** absorbs all the sell proceeds:

   ```json
   {
     "action": "buy", "sym": "SMA*",
     "name": "Direct-indexed broad-market SMA sleeve (~200 lines, illustrative universe)",
     "value": 26400000, "gl": null,
     "reason": "Basis reset at trade date. Overlay begins next business day."
   }
   ```

   `$26.4M` is exactly the sum of the five sells above ($10.6M + $6.2M + $4.9M + $4.3M + $0.4M). The `SMA*` ticker and the `"(~200 lines, illustrative universe)"` label are deliberate — the system is explicit that it cannot enumerate a real several-hundred-line direct-indexing basket without a real security master, so it says so directly in the buy row's own name rather than pretending precision it doesn't have.

### 3.4 Target-state math

```json
"target_state": {
  "realized_gain": 12100000,
  "harvest_offset": 1100000,
  "net_taxable_gain": 11000000,
  "estimated_ongoing_annual_tax_alpha": 343910,
  "sells_total": 26400000,
  "buys_total": 26400000
}
```

- **`realized_gain` ($12.1M)** = the sum of every *positive* G/L across the sell rows only: $8.5M (NVDA) + $2.5M (MSFT) + $1.1M (VTI) = $12.1M. VXUS's −$0.6M is a sell too, but only positive G/L sells count toward realized *gain* — a losing sell doesn't add to this figure (it just doesn't subtract from it either; it's simply excluded). The unresolved-basis NVDA lot contributes `null`, so it's excluded from the sum entirely (Python's `t.get('gl') or 0` treats `null` as `0` here, contributing nothing either way).
- **`harvest_offset` ($1.1M)** = the sum of the *magnitude* of every harvest row's loss: $0.6M (MUB) + $0.5M (AGG) = $1.1M.
- **`net_taxable_gain` ($11M)** = `max(0, realized_gain − harvest_offset)` = `max(0, 12.1M − 1.1M)` = $11M. This is why the number is never negative — if harvesting fully covered the realized gain, this would floor at 0, not go negative (excess losses simply aren't reflected at this summary level).
- **`estimated_ongoing_annual_tax_alpha` ($343,910)** = the household's own baseline `taxAlpha` figure (its harvestable-losses-derived illustrative tax value) multiplied by Direct Indexing's specific ongoing-capture factor of **0.85** — i.e. the workbench asserts that once running, an actively-managed direct-indexed sleeve captures about 85% of the household's theoretical ongoing tax-alpha opportunity, a lower factor than a daily-cadence overlay would get (see §5.2) but higher than a one-time-only transition event like TET (which gets a flat 0, since it isn't an ongoing overlay at all).
- **`notes`** — two lines, both conditionally assembled: a wash-sale/basis-reset caveat (always shown for `directIndexing`/`temSms`), and, because `net_taxable_gain > 0`, an explicit illustrative dollar estimate at the flat 23.8% blended rate the system uses everywhere: $11,000,000 × 0.238 ≈ **$2,618,000**.

---

## 4. Example B: Sørensen Living Trust → QLH Overlay

### 4.1 Starting position

Sørensen holds 6 positions worth $27.3M, no concentration flags at all, and a modest 7% cash position:

| Symbol | Asset class | Market value | Weight | Unrealized G/L |
|---|---|---|---|---|
| MUB | Municipal | $9.4M | 34.4% | −$0.5M |
| VTI | US Equity | $6.1M | 22.3% | +$1.4M |
| BND | Fixed Income | $4.1M | 15.0% | −$0.3M |
| SCHD | US Equity | $3.3M | 12.1% | +$0.4M |
| VXUS | Intl Equity | $2.6M | 9.5% | −$0.2M |
| CASH | Cash | $1.8M | 6.6% | $0 |

### 4.2 What gets flagged, and why

```json
"gap_analysis": [
  { "severity": "clear", "message": "No structural blockers. Ready to initiate." }
]
```

QLH Overlay isn't Direct Indexing or TEM, so the concentration/cash checks in §3.2 don't even run for it — and it isn't DTLH (no ETF-only requirement) or TET (no basis/individual-fixed-income scope carve-outs either). None of the offering-specific checks apply, and the eligibility engine itself returned a clean `ELIGIBLE` with no `NEEDS_REVIEW`-level reasons to surface. **This is the one case where the gap list would otherwise be genuinely empty** — and that's exactly the case the system refuses to leave blank: when nothing else has been appended to the gap list by the time every check has run, it appends this single explicit `clear`-severity row instead of returning `[]`. An advisor scanning quickly sees a positive, stated confirmation ("ready to initiate") rather than an ambiguous empty space that could just as easily mean "this feature didn't run."

### 4.3 How the trade list is built

QLH Overlay belongs to the second algorithm family — `taxManagedSMA`, `qlhOverlay`, `mgiTer`, `mgiQlh` — **overlay on the existing sleeve, no sells at all**. The logic is deliberately minimal: this kind of offering doesn't replace anything, it just starts actively managing what's already there. So the only thing the trade-proposal step does is a **one-time harvest scan**: every position already sitting at a loss over $1,000, anywhere in the portfolio (not just outside some sleeve, since there's no sleeve being carved out here):

| Harvest | Value | Loss realized | Reason given |
|---|---|---|---|
| MUB | $9.4M | −$0.5M | *Onboarding harvest: realize $500,000, carry loss forward.* |
| VXUS | $2.6M | −$0.2M | *Onboarding harvest: realize $200,000, carry loss forward.* |
| BND | $4.1M | −$0.3M | *Onboarding harvest: realize $300,000, carry loss forward.* |

VTI (+$1.4M) and SCHD (+$0.4M) are both at a gain, so neither is touched — nothing is ever sold purely to realize a gain under this algorithm family; only losses get proactively harvested. If Sørensen had held nothing at a loss at all, this list would instead contain a single explicit row: `{"action": "note", "name": "No trades required at onboarding", "reason": "Existing sleeve stays in place; overlay begins with next dividend/rebalance event."}` — the same "never show an empty state" discipline as the gap list, applied to the trade table too.

### 4.4 Target-state math

```json
"target_state": {
  "realized_gain": 0,
  "harvest_offset": 1000000,
  "net_taxable_gain": 0,
  "estimated_ongoing_annual_tax_alpha": 166600,
  "sells_total": 0,
  "buys_total": 0,
  "notes": ["Overlay is applied to the existing sleeve; harvested losses carry forward."]
}
```

- **`realized_gain` is $0`** — there are no `sell`/`stage_sell` rows at all (this algorithm family never produces any), so there's nothing to sum.
- **`harvest_offset` ($1M)** = $0.5M + $0.2M + $0.3M, the three harvest rows above.
- **`net_taxable_gain`** = `max(0, 0 − 1,000,000)` = **$0**, floored — the $1M of harvested losses isn't "wasted," it simply doesn't produce a negative number at this level; it carries forward per the note, but that downstream carry-forward accounting is outside what this summary figure represents.
- **`estimated_ongoing_annual_tax_alpha` ($166,600)** = Sørensen's baseline `taxAlpha` × QLH's capture factor of **0.7** — notably lower than DTLH's 0.9 (§5.2), reflecting that a quarterly-cadence harvesting overlay is a real but less-frequent scan than a daily one.
- Only one note is shown — the wash-sale caveat that fires for `directIndexing`/`temSms` doesn't apply here (nothing is being repurchased into a new sleeve), and the "net taxable event" dollar-estimate note that appeared for Henderson doesn't fire either, because it's conditional on `net_taxable_gain > 0`, which is false here.

---

## 5. Reference: the complete flagging rules

### 5.1 Gap-analysis severities and exactly when each fires

| Severity | Fires when | Example message |
|---|---|---|
| `required` | (a) the eligibility engine itself returned `NEEDS_REVIEW`-level reasons; or (b) `directIndexing`/`temSms` and the household has a concentration flag; or (c) `dtlhOverlay` and the household holds any non-ETF position | *"Concentrated positions need trimming: NVDA single-stock at 22% (policy limit 10%)."* |
| `recommended` | `directIndexing`/`temSms` and current cash allocation is under 2% | *"Modest cash reserve helps stage the initial buy without forced timing."* |
| `scope_carveout` | `transition` (TET) and the household has any lot with unresolved cost basis, or any individual (non-ETF) fixed-income position | *"2 lot(s) with unresolved cost basis excluded from TET scope: ..."* |
| `review` | a rule-engine reason with a `missing_fields` marker | *"Resolve unknown field: account offering profile requirements met"* |
| `clear` | nothing above fired — the list would otherwise be empty | *"No structural blockers. Ready to initiate."* |

The list is built by running every applicable check in this order and appending whatever fires; `clear` is the fallback appended only if the list is still empty after every other check has run — it never appears alongside a real flag.

### 5.2 Ongoing tax-alpha capture factor, by offering

| Offering | Factor | Algorithm family |
|---|---|---|
| `dtlhOverlay` | 0.90 | ETF-only conversion |
| `directIndexing` | 0.85 | Full sleeve replacement |
| `mgiDtlh` | 0.75 | Full sleeve replacement |
| `qlhOverlay` | 0.70 | Overlay-on-existing |
| `temSms` | 0.70 | Full sleeve replacement |
| `taxManagedSMA` | 0.60 | Overlay-on-existing |
| `mgiQlh` | 0.55 | Overlay-on-existing |
| `mgiTer` | 0.50 | Overlay-on-existing |
| `transition` (TET) | 0.00 | Staged one-time transition — not an ongoing overlay, so no ongoing figure applies |

### 5.3 Trade action types

| Action | Meaning | Color in the UI |
|---|---|---|
| `sell` | Position is fully disposed of as part of the transition | Red |
| `stage_sell` | Position is queued for a *paced* sell against a budget (TET only) — not an immediate sell | Blue |
| `harvest` | A loss position is deliberately realized to offset gains elsewhere, then carried forward | Amber |
| `buy` | The consolidated replacement sleeve (only appears in the full-sleeve-replacement family) | Brand teal |
| `note` | Explicit "nothing to do" placeholder, shown instead of an empty trade table | Muted gray |

