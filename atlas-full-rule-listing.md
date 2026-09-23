# Atlas — Full Rule Listing (live `RULE_STORE`)

Generated directly from the rule-engine console's `RULE_STORE` object — every rule shown here is exactly what the app evaluates, not a paraphrase. `pack_id`: `atlas.merrill.tax-services.2026-09-20` · `status`: `POC_DRAFT_NOT_APPROVED_POLICY`.

**16 offerings, 92 rules, 4 composition rules.**

Each rule's `predicate` reads a *derived field* (e.g. `account.tax_status`) — never a raw UI field — computed by the derive layer per household (and, where the pack's own `offering_facts` pattern applies, per offering). `compile_source.kind` tells you whether a rule is a paraphrase of an actual clause in the three source PDFs (`PDF_CLAUSE_PARAPHRASE`), an implementation safeguard the console adds on top (`IMPLEMENTATION_GUARD`), or Atlas's own house policy never claimed to be PDF-sourced (`HOUSE_POLICY`).

## Contents
- [IAP enrollment](#iapenrollment) (`iapEnrollment`) — 6 rules
- [Tax Efficient Rebalancing (TER; legacy Atlas ID)](#taxmanagedsma) (`taxManagedSMA`) — 8 rules
- [Quarterly Loss Harvesting (QLH)](#qlhoverlay) (`qlhOverlay`) — 8 rules
- [Dynamic Tax Loss Harvesting (DTLH)](#dtlhoverlay) (`dtlhOverlay`) — 8 rules
- [Tax Efficient Transition (TET)](#transition) (`transition`) — 16 rules
- [Direct Indexing Style Manager Strategy](#directindexing) (`directIndexing`) — 6 rules
- [TEM Style Manager Strategy](#temsms) (`temSms`) — 6 rules
- [Guided Investing TER](#mgiter) (`mgiTer`) — 6 rules
- [Guided Investing QLH](#mgiqlh) (`mgiQlh`) — 6 rules
- [Guided Investing DTLH](#mgidtlh) (`mgiDtlh`) — 7 rules
- [Alternatives](#alternatives) (`alternatives`) — 4 rules
- [Private Banking](#privatebanking) (`privateBanking`) — 2 rules
- [Securities-Based Lending](#lending) (`lending`) — 3 rules
- [Trust & Estate](#trustestate) (`trustEstate`) — 2 rules
- [Insurance / Annuity](#insurance) (`insurance`) — 2 rules
- [Charitable / Gifting Overlay](#charitable) (`charitable`) — 2 rules
- [Composition rules](#composition-rules)

---

## IAP enrollment
**Offering id:** `iapEnrollment` · **Program scope:** IAP

### `IAP.agreement`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.iap_agreement_executed` **EQ** true
```
- **Message:** Enter into the IAP agreement.
- **Source:** IAP p.41 — Item 5: Client and Advisor Eligibility
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `IAP.account_type`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.iap_account_type_eligible` **EQ** true
```
- **Message:** The account type must be eligible for IAP.
- **Source:** IAP p.41 — Item 5: Client and Advisor Eligibility
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `IAP.separate`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.separate_account_per_program_strategy` **EQ** true
```
- **Message:** Use a separate account for each selected Program Strategy.
- **Source:** IAP p.41 — Item 5: Client and Advisor Eligibility
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `IAP.strategy_requirements`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.selected_strategy_requirements_met` **EQ** true
```
- **Message:** Meet the selected strategy’s investor and investment minimum requirements.
- **Source:** IAP p.42 — Program Minimums
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `IAP.fa_scope`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `FA_SCOPE` — **never shown to the client**
- **Predicate:**
```
ANY of:
  `strategy.requires_qualified_advisor` **EQ** false
  `fa.qualified_for_selected_strategy` **EQ** true
```
- **Message:** Qualification is required for designated strategy types/products; obtain the qualification policy.
- **Source:** IAP p.41 — Client and Advisor Eligibility
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `IAP.pas_contract`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
ANY of:
  `account.has_pas_strategy` **EQ** false
  `account.pas_manager_contract_executed` **EQ** true
```
- **Message:** PAS requires a separate manager/client contract.
- **Source:** IAP p.41 — Client and Advisor Eligibility
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

---

## Tax Efficient Rebalancing (TER; legacy Atlas ID)
**Offering id:** `taxManagedSMA` · **Program scope:** IAP

### `taxManagedSMA.iap`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.program_enrollment` **IN** ['IAP_MANAGED', 'IAP_CUSTOM_MANAGED']
```
- **Message:** Select an IAP Managed or Custom Managed Strategy.
- **Source:** IAP p.25 — TEM Overlay Services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `taxManagedSMA.approved_profile`
- **Effect:** NEEDS_REVIEW trigger — true → verdict elevates to NEEDS_REVIEW
- **Failure class:** `MANAGER_ADJUDICATION` — **never shown to the client**
- **Predicate:**
```
`policy.offering_profile_verified` **EQ** false
```
- **Message:** Obtain the offering-specific term sheet, approved strategy universe, minimums and applicable advisor qualification policy before confirming eligibility.
- **Source:** IAP p.42 — Program Minimums
- **Compile source:** `IMPLEMENTATION_GUARD` (POC_DESIGN)

### `taxManagedSMA.profile_requirements`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.offering_profile_requirements_met` **EQ** true
```
- **Message:** Meet all externally versioned offering/strategy requirements; do not substitute household AUM.
- **Source:** IAP p.42 — Program Minimums
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `taxManagedSMA.taxable`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.tax_status` **EQ** 'TAXABLE'
```
- **Message:** TEM overlays are available only to taxable accounts.
- **Source:** IAP p.25 — Tax Efficient Management Overlay Services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `taxManagedSMA.not_pas`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.has_pas_strategy` **EQ** false
```
- **Message:** MAA TEM overlays are unavailable for accounts invested in a PAS Style Manager Strategy.
- **Source:** IAP p.25 — Tax Efficient Management Overlay Services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `taxManagedSMA.universe`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.in_universe_TER` **EQ** true
```
- **Message:** Resolve service-specific eligible investments from an approved dated strategy list.
- **Source:** IAP p.25 — Tax Efficient Management Overlay Services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `taxManagedSMA.eligible_scope`
- **Effect:** SCOPE_CARVEOUT — true → excludes matching assets from scope (does not reject the whole account)
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`scope.has_overlay_ineligible_investments` **EQ** true
```
- **Message:** Apply the overlay only to eligible investments; a Custom Managed account may contain investments outside its scope.
- **Scope key** (asset ids excluded when this fires): `scope.overlay_ineligible_investment_ids`
- **Source:** IAP p.25 — Tax Efficient Management Overlay Services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `taxManagedSMA.wash_sale`
- **Effect:** DISCLOSURE — true → attaches mandatory language, never affects the verdict
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`true` (always attaches)
```
- **Message:** The service considers only this account. Monitor other Merrill, held-away, spouse and relevant controlled-entity accounts for wash sales and straddles; tax benefits are not guaranteed.
- **Source:** IAP p.40 — Tax Matters: TEM risks; IAP p.41 — Tax Matters: TEM risks
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

---

## Quarterly Loss Harvesting (QLH)
**Offering id:** `qlhOverlay` · **Program scope:** IAP

### `qlhOverlay.iap`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.program_enrollment` **IN** ['IAP_MANAGED', 'IAP_CUSTOM_MANAGED']
```
- **Message:** Select an IAP Managed or Custom Managed Strategy.
- **Source:** IAP p.25 — TEM Overlay Services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `qlhOverlay.approved_profile`
- **Effect:** NEEDS_REVIEW trigger — true → verdict elevates to NEEDS_REVIEW
- **Failure class:** `MANAGER_ADJUDICATION` — **never shown to the client**
- **Predicate:**
```
`policy.offering_profile_verified` **EQ** false
```
- **Message:** Obtain the offering-specific term sheet, approved strategy universe, minimums and applicable advisor qualification policy before confirming eligibility.
- **Source:** IAP p.42 — Program Minimums
- **Compile source:** `IMPLEMENTATION_GUARD` (POC_DESIGN)

### `qlhOverlay.profile_requirements`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.offering_profile_requirements_met` **EQ** true
```
- **Message:** Meet all externally versioned offering/strategy requirements; do not substitute household AUM.
- **Source:** IAP p.42 — Program Minimums
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `qlhOverlay.taxable`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.tax_status` **EQ** 'TAXABLE'
```
- **Message:** TEM overlays are available only to taxable accounts.
- **Source:** IAP p.25 — Tax Efficient Management Overlay Services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `qlhOverlay.not_pas`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.has_pas_strategy` **EQ** false
```
- **Message:** MAA TEM overlays are unavailable for accounts invested in a PAS Style Manager Strategy.
- **Source:** IAP p.25 — Tax Efficient Management Overlay Services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `qlhOverlay.universe`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.in_universe_QLH` **EQ** true
```
- **Message:** Resolve service-specific eligible investments from an approved dated strategy list.
- **Source:** IAP p.25 — Tax Efficient Management Overlay Services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `qlhOverlay.eligible_scope`
- **Effect:** SCOPE_CARVEOUT — true → excludes matching assets from scope (does not reject the whole account)
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`scope.has_overlay_ineligible_investments` **EQ** true
```
- **Message:** Apply the overlay only to eligible investments; a Custom Managed account may contain investments outside its scope.
- **Scope key** (asset ids excluded when this fires): `scope.overlay_ineligible_investment_ids`
- **Source:** IAP p.25 — Tax Efficient Management Overlay Services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `qlhOverlay.wash_sale`
- **Effect:** DISCLOSURE — true → attaches mandatory language, never affects the verdict
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`true` (always attaches)
```
- **Message:** The service considers only this account. Monitor other Merrill, held-away, spouse and relevant controlled-entity accounts for wash sales and straddles; tax benefits are not guaranteed.
- **Source:** IAP p.40 — Tax Matters: TEM risks; IAP p.41 — Tax Matters: TEM risks
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

---

## Dynamic Tax Loss Harvesting (DTLH)
**Offering id:** `dtlhOverlay` · **Program scope:** IAP

### `dtlhOverlay.iap`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.program_enrollment` **IN** ['IAP_MANAGED', 'IAP_CUSTOM_MANAGED']
```
- **Message:** Select an IAP Managed or Custom Managed Strategy.
- **Source:** IAP p.25 — TEM Overlay Services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `dtlhOverlay.approved_profile`
- **Effect:** NEEDS_REVIEW trigger — true → verdict elevates to NEEDS_REVIEW
- **Failure class:** `MANAGER_ADJUDICATION` — **never shown to the client**
- **Predicate:**
```
`policy.offering_profile_verified` **EQ** false
```
- **Message:** Obtain the offering-specific term sheet, approved strategy universe, minimums and applicable advisor qualification policy before confirming eligibility.
- **Source:** IAP p.42 — Program Minimums
- **Compile source:** `IMPLEMENTATION_GUARD` (POC_DESIGN)

### `dtlhOverlay.profile_requirements`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.offering_profile_requirements_met` **EQ** true
```
- **Message:** Meet all externally versioned offering/strategy requirements; do not substitute household AUM.
- **Source:** IAP p.42 — Program Minimums
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `dtlhOverlay.taxable`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.tax_status` **EQ** 'TAXABLE'
```
- **Message:** TEM overlays are available only to taxable accounts.
- **Source:** IAP p.25 — Tax Efficient Management Overlay Services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `dtlhOverlay.not_pas`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.has_pas_strategy` **EQ** false
```
- **Message:** MAA TEM overlays are unavailable for accounts invested in a PAS Style Manager Strategy.
- **Source:** IAP p.25 — Tax Efficient Management Overlay Services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `dtlhOverlay.universe`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.in_universe_DTLH` **EQ** true
```
- **Message:** Resolve service-specific eligible investments from an approved dated strategy list.
- **Source:** IAP p.25 — Tax Efficient Management Overlay Services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `dtlhOverlay.eligible_scope`
- **Effect:** SCOPE_CARVEOUT — true → excludes matching assets from scope (does not reject the whole account)
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`scope.has_overlay_ineligible_investments` **EQ** true
```
- **Message:** Apply the overlay only to eligible investments; a Custom Managed account may contain investments outside its scope.
- **Scope key** (asset ids excluded when this fires): `scope.overlay_ineligible_investment_ids`
- **Source:** IAP p.25 — Tax Efficient Management Overlay Services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `dtlhOverlay.wash_sale`
- **Effect:** DISCLOSURE — true → attaches mandatory language, never affects the verdict
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`true` (always attaches)
```
- **Message:** The service considers only this account. Monitor other Merrill, held-away, spouse and relevant controlled-entity accounts for wash sales and straddles; tax benefits are not guaranteed.
- **Source:** IAP p.40 — Tax Matters: TEM risks; IAP p.41 — Tax Matters: TEM risks
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

---

## Tax Efficient Transition (TET)
**Offering id:** `transition` · **Program scope:** IAP

### `transition.iap`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.program_enrollment` **IN** ['IAP_MANAGED', 'IAP_CUSTOM_MANAGED']
```
- **Message:** Select an IAP Managed or Custom Managed Strategy.
- **Source:** TET p.1 — Service overview
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `transition.approved_profile`
- **Effect:** NEEDS_REVIEW trigger — true → verdict elevates to NEEDS_REVIEW
- **Failure class:** `MANAGER_ADJUDICATION` — **never shown to the client**
- **Predicate:**
```
`policy.offering_profile_verified` **EQ** false
```
- **Message:** Obtain the offering-specific term sheet, approved strategy universe, minimums and applicable advisor qualification policy before confirming eligibility.
- **Source:** IAP p.42 — Program Minimums
- **Compile source:** `IMPLEMENTATION_GUARD` (POC_DESIGN)

### `transition.profile_requirements`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.offering_profile_requirements_met` **EQ** true
```
- **Message:** Meet all externally versioned offering/strategy requirements; do not substitute household AUM.
- **Source:** IAP p.42 — Program Minimums
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `TET.taxable`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.tax_status` **EQ** 'TAXABLE'
```
- **Message:** TET requires a taxable account.
- **Source:** TET p.4 — Account Eligibility for the Service
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `TET.domestic`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.is_domestic` **EQ** true
```
- **Message:** TET requires a domestic account; use the account master classification, not an inferred citizenship/residency proxy.
- **Source:** TET p.4 — Account Eligibility for the Service; IAP p.26 — Operation of the Account with TET
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `TET.not_pas`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.has_pas_strategy` **EQ** false
```
- **Message:** TET is not available to an account invested in a PAS Style Manager Strategy.
- **Source:** IAP p.26 — Treatment of your Account with TET
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `TET.not_direct_index`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`target_strategy.is_direct_indexing` **EQ** false
```
- **Message:** Direct Indexing target strategies are not covered by TET.
- **Source:** TET p.4 — Account Eligibility for the Service
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `TET.universe`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.in_universe_TET` **EQ** true
```
- **Message:** Select a TET-eligible target investment strategy.
- **Source:** TET p.4 — Account Eligibility for the Service
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `TET.minimum`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`transition.strategy_minimum_met` **EQ** true
```
- **Message:** Meet the target strategy investment minimum.
- **Source:** TET p.4 — Service Minimums
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `TET.budget_minimum`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`transition.budget_minimum_met` **EQ** true
```
- **Message:** Resolve the firm’s transition budget minimum; no numeric minimum is supplied.
- **Source:** TET p.4 — Service Minimums
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `TET.budget_selected`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`transition.long_term_budget_selected` **EQ** true
```
- **Message:** Select an annual net long-term capital gains transition budget.
- **Source:** TET p.3 — Setting your Annual Net Capital Gains Budget
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `TET.scope.missing_basis`
- **Effect:** SCOPE_CARVEOUT — true → excludes matching assets from scope (does not reject the whole account)
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`scope.has_tet_missing_basis` **EQ** true
```
- **Message:** Securities without cost basis at enrollment are outside TET eligibility. Do not make this an automatic whole-account rejection.
- **Scope key** (asset ids excluded when this fires): `scope.tet_missing_basis_ids`
- **Source:** IAP p.26 — Treatment of Account Assets
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `TET.scope.fixed_income`
- **Effect:** SCOPE_CARVEOUT — true → excludes matching assets from scope (does not reject the whole account)
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`scope.has_individual_fixed_income` **EQ** true
```
- **Message:** Individual fixed-income assets, excluding mutual funds/ETFs, are outside transition methodology. In-kind transfer or other disposition requires a separate plan.
- **Scope key** (asset ids excluded when this fires): `scope.individual_fixed_income_ids`
- **Source:** IAP p.26 — Treatment of Account Assets
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `TET.scope.income_cash`
- **Effect:** SCOPE_CARVEOUT — true → excludes matching assets from scope (does not reject the whole account)
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`scope.has_tma_income_cash` **EQ** true
```
- **Message:** For a Trust Management Account, exclude cash designated as income cash from TET consideration.
- **Scope key** (asset ids excluded when this fires): `scope.tma_income_cash_ids`
- **Source:** TET p.1 — Treatment of Account Assets
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `TET.inaccurate_basis`
- **Effect:** NEEDS_REVIEW trigger — true → verdict elevates to NEEDS_REVIEW
- **Failure class:** `MANAGER_ADJUDICATION` — **never shown to the client**
- **Predicate:**
```
`scope.has_inaccurate_cost_basis` **EQ** true
```
- **Message:** Resolve inaccurate cost basis before relying on the transition analysis.
- **Source:** TET p.4 — Account Activity and Transactions
- **Compile source:** `IMPLEMENTATION_GUARD_FROM_SOURCE_RISK` (POC_DESIGN)

### `TET.disclosure`
- **Effect:** DISCLOSURE — true → attaches mandatory language, never affects the verdict
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`true` (always attaches)
```
- **Message:** The annual budget is not an account-wide hard tax cap. Certain sales can exceed it and other activity is outside it. Transitioning, termination and DTLH replacement sales can create gains; tax savings are not guaranteed.
- **Source:** TET p.3 — Activity that can cause budget exceedance; TET p.4 — Excluded activity; TET p.5 — Risk of Loss and TEM services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

---

## Direct Indexing Style Manager Strategy
**Offering id:** `directIndexing` · **Program scope:** IAP
> Managed/Custom Managed lane only. PAS variants require a separate PAS policy pack and are not determined here.

### `directIndexing.iap`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.program_enrollment` **IN** ['IAP_MANAGED', 'IAP_CUSTOM_MANAGED']
```
- **Message:** Select an IAP Managed or Custom Managed Strategy.
- **Source:** IAP p.10 — Types of Style Manager Strategies; IAP p.12 — Custom Managed Strategy
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `directIndexing.approved_profile`
- **Effect:** NEEDS_REVIEW trigger — true → verdict elevates to NEEDS_REVIEW
- **Failure class:** `MANAGER_ADJUDICATION` — **never shown to the client**
- **Predicate:**
```
`policy.offering_profile_verified` **EQ** false
```
- **Message:** Obtain the offering-specific term sheet, approved strategy universe, minimums and applicable advisor qualification policy before confirming eligibility.
- **Source:** IAP p.42 — Program Minimums
- **Compile source:** `IMPLEMENTATION_GUARD` (POC_DESIGN)

### `directIndexing.profile_requirements`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.offering_profile_requirements_met` **EQ** true
```
- **Message:** Meet all externally versioned offering/strategy requirements; do not substitute household AUM.
- **Source:** IAP p.42 — Program Minimums
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `directIndexing.roster`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`target_strategy.in_approved_directIndexing_roster` **EQ** true
```
- **Message:** The selected strategy must be in the approved manager/strategy catalog.
- **Source:** IAP p.9 — Managed Strategy; IAP p.10 — Types of Style Manager Strategies
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `directIndexing.restrictions`
- **Effect:** NEEDS_REVIEW trigger — true → verdict elevates to NEEDS_REVIEW
- **Failure class:** `MANAGER_ADJUDICATION` — **never shown to the client**
- **Predicate:**
```
`target_strategy.restrictions_awaiting_manager_acceptance` **EQ** true
```
- **Message:** The strategy manager must determine whether requested restrictions are reasonable.
- **Source:** IAP p.11 — Direct Indexing/TEM Style Manager Strategy
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `directIndexing.disclosure`
- **Effect:** DISCLOSURE — true → attaches mandatory language, never affects the verdict
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`true` (always attaches)
```
- **Message:** A manager-run Direct Indexing/TEM strategy is distinct from MAA TEM overlays and from tax-aware model strategies; tax benefits and replacement security performance are not guaranteed.
- **Source:** IAP p.11 — Types of Style Manager Strategies; IAP p.40 — TEM risks
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

---

## TEM Style Manager Strategy
**Offering id:** `temSms` · **Program scope:** IAP
> Managed/Custom Managed lane only. PAS variants require a separate PAS policy pack and are not determined here.

### `temSms.iap`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.program_enrollment` **IN** ['IAP_MANAGED', 'IAP_CUSTOM_MANAGED']
```
- **Message:** Select an IAP Managed or Custom Managed Strategy.
- **Source:** IAP p.10 — Types of Style Manager Strategies; IAP p.12 — Custom Managed Strategy
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `temSms.approved_profile`
- **Effect:** NEEDS_REVIEW trigger — true → verdict elevates to NEEDS_REVIEW
- **Failure class:** `MANAGER_ADJUDICATION` — **never shown to the client**
- **Predicate:**
```
`policy.offering_profile_verified` **EQ** false
```
- **Message:** Obtain the offering-specific term sheet, approved strategy universe, minimums and applicable advisor qualification policy before confirming eligibility.
- **Source:** IAP p.42 — Program Minimums
- **Compile source:** `IMPLEMENTATION_GUARD` (POC_DESIGN)

### `temSms.profile_requirements`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.offering_profile_requirements_met` **EQ** true
```
- **Message:** Meet all externally versioned offering/strategy requirements; do not substitute household AUM.
- **Source:** IAP p.42 — Program Minimums
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `temSms.roster`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`target_strategy.in_approved_temSms_roster` **EQ** true
```
- **Message:** The selected strategy must be in the approved manager/strategy catalog.
- **Source:** IAP p.9 — Managed Strategy; IAP p.10 — Types of Style Manager Strategies
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `temSms.restrictions`
- **Effect:** NEEDS_REVIEW trigger — true → verdict elevates to NEEDS_REVIEW
- **Failure class:** `MANAGER_ADJUDICATION` — **never shown to the client**
- **Predicate:**
```
`target_strategy.restrictions_awaiting_manager_acceptance` **EQ** true
```
- **Message:** The strategy manager must determine whether requested restrictions are reasonable.
- **Source:** IAP p.11 — Direct Indexing/TEM Style Manager Strategy
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `temSms.disclosure`
- **Effect:** DISCLOSURE — true → attaches mandatory language, never affects the verdict
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`true` (always attaches)
```
- **Message:** A manager-run Direct Indexing/TEM strategy is distinct from MAA TEM overlays and from tax-aware model strategies; tax benefits and replacement security performance are not guaranteed.
- **Source:** IAP p.11 — Types of Style Manager Strategies; IAP p.40 — TEM risks
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

---

## Guided Investing TER
**Offering id:** `mgiTer` · **Program scope:** MGI, MGI_WITH_ADVISOR

### `mgiTer.taxable`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.tax_status` **EQ** 'TAXABLE'
```
- **Message:** TEM is intended for taxable accounts.
- **Source:** MGI p.2 — TEM eligibility and available services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `mgiTer.growth`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.goal_type` **EQ** 'GROWTH_FOCUSED'
```
- **Message:** TEM is unavailable for an Income-Focused goal.
- **Source:** MGI p.2 — TEM eligibility and available services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `mgiTer.not_retirement`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.is_retirement` **EQ** false
```
- **Message:** TEM is unavailable for Retirement Accounts.
- **Source:** MGI p.2 — TEM eligibility and available services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `mgiTer.strategy`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.available_tem_services` **CONTAINS** 'TER'
```
- **Message:** Use the service eligibility presented by the Program Website for the selected strategy.
- **Source:** MGI p.3 — TEM eligibility and available services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `mgiTer.full_terms`
- **Effect:** NEEDS_REVIEW trigger — true → verdict elevates to NEEDS_REVIEW
- **Failure class:** `MANAGER_ADJUDICATION` — **never shown to the client**
- **Predicate:**
```
`policy.offering_profile_verified` **EQ** false
```
- **Message:** Obtain the Guided Investing program brochure and applicable overlay term sheet; the overview alone is incomplete.
- **Source:** MGI p.3 — For additional information; MGI p.4 — Considerations
- **Compile source:** `IMPLEMENTATION_GUARD` (POC_DESIGN)

### `mgiTer.disclosure`
- **Effect:** DISCLOSURE — true → attaches mandatory language, never affects the verdict
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`true` (always attaches)
```
- **Message:** Monitor all accounts for wash sales and straddles. Lower marginal tax rates may reduce the benefit; consult the tax/legal advisor.
- **Source:** MGI p.4 — Considerations before electing TEM Overlay Services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

---

## Guided Investing QLH
**Offering id:** `mgiQlh` · **Program scope:** MGI, MGI_WITH_ADVISOR

### `mgiQlh.taxable`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.tax_status` **EQ** 'TAXABLE'
```
- **Message:** TEM is intended for taxable accounts.
- **Source:** MGI p.2 — TEM eligibility and available services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `mgiQlh.growth`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.goal_type` **EQ** 'GROWTH_FOCUSED'
```
- **Message:** TEM is unavailable for an Income-Focused goal.
- **Source:** MGI p.2 — TEM eligibility and available services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `mgiQlh.not_retirement`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.is_retirement` **EQ** false
```
- **Message:** TEM is unavailable for Retirement Accounts.
- **Source:** MGI p.2 — TEM eligibility and available services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `mgiQlh.strategy`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.available_tem_services` **CONTAINS** 'QLH'
```
- **Message:** Use the service eligibility presented by the Program Website for the selected strategy.
- **Source:** MGI p.3 — TEM eligibility and available services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `mgiQlh.full_terms`
- **Effect:** NEEDS_REVIEW trigger — true → verdict elevates to NEEDS_REVIEW
- **Failure class:** `MANAGER_ADJUDICATION` — **never shown to the client**
- **Predicate:**
```
`policy.offering_profile_verified` **EQ** false
```
- **Message:** Obtain the Guided Investing program brochure and applicable overlay term sheet; the overview alone is incomplete.
- **Source:** MGI p.3 — For additional information; MGI p.4 — Considerations
- **Compile source:** `IMPLEMENTATION_GUARD` (POC_DESIGN)

### `mgiQlh.disclosure`
- **Effect:** DISCLOSURE — true → attaches mandatory language, never affects the verdict
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`true` (always attaches)
```
- **Message:** Monitor all accounts for wash sales and straddles. Lower marginal tax rates may reduce the benefit; consult the tax/legal advisor.
- **Source:** MGI p.4 — Considerations before electing TEM Overlay Services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

---

## Guided Investing DTLH
**Offering id:** `mgiDtlh` · **Program scope:** MGI, MGI_WITH_ADVISOR

### `mgiDtlh.taxable`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.tax_status` **EQ** 'TAXABLE'
```
- **Message:** TEM is intended for taxable accounts.
- **Source:** MGI p.2 — TEM eligibility and available services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `mgiDtlh.growth`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.goal_type` **EQ** 'GROWTH_FOCUSED'
```
- **Message:** TEM is unavailable for an Income-Focused goal.
- **Source:** MGI p.2 — TEM eligibility and available services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `mgiDtlh.not_retirement`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.is_retirement` **EQ** false
```
- **Message:** TEM is unavailable for Retirement Accounts.
- **Source:** MGI p.2 — TEM eligibility and available services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `mgiDtlh.strategy`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.available_tem_services` **CONTAINS** 'DTLH'
```
- **Message:** Use the service eligibility presented by the Program Website for the selected strategy.
- **Source:** MGI p.3 — TEM eligibility and available services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `mgiDtlh.full_terms`
- **Effect:** NEEDS_REVIEW trigger — true → verdict elevates to NEEDS_REVIEW
- **Failure class:** `MANAGER_ADJUDICATION` — **never shown to the client**
- **Predicate:**
```
`policy.offering_profile_verified` **EQ** false
```
- **Message:** Obtain the Guided Investing program brochure and applicable overlay term sheet; the overview alone is incomplete.
- **Source:** MGI p.3 — For additional information; MGI p.4 — Considerations
- **Compile source:** `IMPLEMENTATION_GUARD` (POC_DESIGN)

### `mgiDtlh.disclosure`
- **Effect:** DISCLOSURE — true → attaches mandatory language, never affects the verdict
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`true` (always attaches)
```
- **Message:** Monitor all accounts for wash sales and straddles. Lower marginal tax rates may reduce the benefit; consult the tax/legal advisor.
- **Source:** MGI p.4 — Considerations before electing TEM Overlay Services
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

### `MGI.DTLH.cio`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`target_strategy.is_eligible_cio_etf_strategy` **EQ** true
```
- **Message:** DTLH is described for eligible CIO ETF strategies; membership is not proven by an ETF-only holdings test.
- **Source:** MGI p.3 — Dynamic Tax Loss Harvesting
- **Compile source:** `PDF_CLAUSE_PARAPHRASE` (DRAFT_EXTRACTED)

---

## Alternatives
**Offering id:** `alternatives` · **Program scope:** IAP

### `ALT.req.fa`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `FA_SCOPE` — **never shown to the client**
- **Predicate:**
```
`fa.qualified_for_offering` **CONTAINS** 'alternatives'
```
- **Message:** This offering is not in your current qualification scope. Contact your branch manager to request access.
- **Source:** HOUSE — Atlas house policy (not PDF-sourced)
- **Compile source:** `HOUSE_POLICY` (POC_DESIGN)

### `ALT.req.qp`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`client.qualified_purchaser` **EQ** true
```
- **Message:** Alternatives require qualified-purchaser status.
- **Source:** HOUSE — Atlas house policy (not PDF-sourced)
- **Compile source:** `HOUSE_POLICY` (POC_DESIGN)

### `ALT.req.capacity`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.alt_capacity_pct` **GTE** 0.0001
```
- **Message:** Already at/above alternatives target — no sleeve capacity.
- **Source:** HOUSE — Atlas house policy (not PDF-sourced)
- **Compile source:** `HOUSE_POLICY` (POC_DESIGN)

### `ALT.req.min`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.advisory_value` **GTE** 5000000
```
- **Message:** Below the $5M alternatives relationship minimum.
- **Source:** HOUSE — Atlas house policy (not PDF-sourced)
- **Compile source:** `HOUSE_POLICY` (POC_DESIGN)

---

## Private Banking
**Offering id:** `privateBanking` · **Program scope:** IAP

### `PB.req.fa`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `FA_SCOPE` — **never shown to the client**
- **Predicate:**
```
`fa.qualified_for_offering` **CONTAINS** 'privateBanking'
```
- **Message:** This offering is not in your current qualification scope. Contact your branch manager to request access.
- **Source:** HOUSE — Atlas house policy (not PDF-sourced)
- **Compile source:** `HOUSE_POLICY` (POC_DESIGN)

### `PB.req.cash`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.cash_value` **GTE** 1000000
```
- **Message:** Below the $1M deposit/liquidity threshold.
- **Source:** HOUSE — Atlas house policy (not PDF-sourced)
- **Compile source:** `HOUSE_POLICY` (POC_DESIGN)

---

## Securities-Based Lending
**Offering id:** `lending` · **Program scope:** IAP

### `LEND.req.fa`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `FA_SCOPE` — **never shown to the client**
- **Predicate:**
```
`fa.qualified_for_offering` **CONTAINS** 'lending'
```
- **Message:** This offering is not in your current qualification scope. Contact your branch manager to request access.
- **Source:** HOUSE — Atlas house policy (not PDF-sourced)
- **Compile source:** `HOUSE_POLICY` (POC_DESIGN)

### `LEND.req.collateral`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.pledgeable_marketable_value` **GTE** 250000
```
- **Message:** Insufficient marketable, pledgeable collateral.
- **Source:** HOUSE — Atlas house policy (not PDF-sourced)
- **Compile source:** `HOUSE_POLICY` (POC_DESIGN)

### `LEND.review.lowbasis`
- **Effect:** NEEDS_REVIEW trigger — true → verdict elevates to NEEDS_REVIEW
- **Failure class:** `MANAGER_ADJUDICATION` — **never shown to the client**
- **Predicate:**
```
`account.has_low_basis_position` **EQ** true
```
- **Message:** Low-basis collateral — route to credit for advance-rate review.
- **Source:** HOUSE — Atlas house policy (not PDF-sourced)
- **Compile source:** `HOUSE_POLICY` (POC_DESIGN)

---

## Trust & Estate
**Offering id:** `trustEstate` · **Program scope:** IAP

### `TE.req.fa`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `FA_SCOPE` — **never shown to the client**
- **Predicate:**
```
`fa.qualified_for_offering` **CONTAINS** 'trustEstate'
```
- **Message:** This offering is not in your current qualification scope. Contact your branch manager to request access.
- **Source:** HOUSE — Atlas house policy (not PDF-sourced)
- **Compile source:** `HOUSE_POLICY` (POC_DESIGN)

### `TE.req.segment`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.segment` **IN** ['Private Wealth', 'HNW']
```
- **Message:** Offered to Private Wealth and HNW households.
- **Source:** HOUSE — Atlas house policy (not PDF-sourced)
- **Compile source:** `HOUSE_POLICY` (POC_DESIGN)

---

## Insurance / Annuity
**Offering id:** `insurance` · **Program scope:** IAP

### `INS.req.fa`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `FA_SCOPE` — **never shown to the client**
- **Predicate:**
```
`fa.qualified_for_offering` **CONTAINS** 'insurance'
```
- **Message:** This offering is not in your current qualification scope. Contact your branch manager to request access.
- **Source:** HOUSE — Atlas house policy (not PDF-sourced)
- **Compile source:** `HOUSE_POLICY` (POC_DESIGN)

### `INS.review.gap`
- **Effect:** NEEDS_REVIEW trigger — true → verdict elevates to NEEDS_REVIEW
- **Failure class:** `MANAGER_ADJUDICATION` — **never shown to the client**
- **Predicate:**
```
`account.protection_gap` **EQ** true
```
- **Message:** Potential protection/annuity gap — route to insurance specialist.
- **Source:** HOUSE — Atlas house policy (not PDF-sourced)
- **Compile source:** `HOUSE_POLICY` (POC_DESIGN)

---

## Charitable / Gifting Overlay
**Offering id:** `charitable` · **Program scope:** IAP

### `CHAR.req.fa`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `FA_SCOPE` — **never shown to the client**
- **Predicate:**
```
`fa.qualified_for_offering` **CONTAINS** 'charitable'
```
- **Message:** This offering is not in your current qualification scope. Contact your branch manager to request access.
- **Source:** HOUSE — Atlas house policy (not PDF-sourced)
- **Compile source:** `HOUSE_POLICY` (POC_DESIGN)

### `CH.req.gain`
- **Effect:** REQUIREMENT — false → INELIGIBLE (or NEEDS_REVIEW if failure_class is MANAGER_ADJUDICATION); unknown → NEEDS_REVIEW
- **Failure class:** `CLIENT_ELIGIBILITY` — client-facing
- **Predicate:**
```
`account.has_low_basis_position` **EQ** true
```
- **Message:** No appreciated low-basis position well-suited to charitable gifting.
- **Source:** HOUSE — Atlas house policy (not PDF-sourced)
- **Compile source:** `HOUSE_POLICY` (POC_DESIGN)

---

## Composition rules

Evaluated pairwise over a *specific set* of offerings under consideration together (never over every offering a household could ever have). An offering pair with **no matching rule below** returns `NEEDS_REVIEW` — composition is never assumed compatible by default.

### `COMP.TET.DTLH`
- **Offerings:** transition + dtlhOverlay
- **Relation:** `INCOMPATIBLE_WITH`
- **Message:** DTLH cannot be maintained or elected while TET is active. Route a service-change plan; do not auto-cancel or trade.
- **Source:** TET p.5 — Inclusion of TEM Overlay Services; IAP p.27 — Applying TEM to a TET Service-Enrolled Account

### `COMP.TET.TER`
- **Offerings:** transition + taxManagedSMA
- **Relation:** `SCOPE_CARVEOUT_WITHIN_COMPOSITION`
- **Message:** TER applies to Investment Strategy Assets only; excludes Transition Assets. TER is default unless declined.
- **Source:** TET p.5 — Inclusion of TEM Overlay Services; IAP p.27 — Applying TEM to a TET Service-Enrolled Account

### `COMP.TET.QLH`
- **Offerings:** transition + qlhOverlay
- **Relation:** `SCOPE_CARVEOUT_WITHIN_COMPOSITION`
- **Message:** QLH may be elected on Investment Strategy Assets only; timing can interact with budget exhaustion.
- **Source:** TET p.5 — Inclusion of TEM Overlay Services; IAP p.27 — Applying TEM to a TET Service-Enrolled Account

### `COMP.MGI.HARVEST`
- **Offerings:** mgiQlh + mgiDtlh
- **Relation:** `INCOMPATIBLE_WITH`
- **Message:** Guided Investing presents either QLH or DTLH depending on strategy; this is not an IAP supersession rule.
- **Source:** MGI p.3 — Important note
