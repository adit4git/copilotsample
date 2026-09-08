# Model edition 0.8.3 validation

162 tests passed. Anthropic compatibility and native formats are mocked; malformed, wrong-name, duplicate and truncated tool responses cannot compile a plan. Compatibility requests omit output_config and strict mode, make one call, and execute no tools. No live provider verification.

# Model edition 0.8.2 diagnostics validation

155 tests passed, including mocked billing, spend-limit, schema, model, authentication, permission, rate-limit, service and non-JSON errors. No live authenticated reproduction of the reported HTTP 400.

# Model edition 0.8.1 validation

145 tests passed on September 8, 2026. Both provider response formats were tested with mocked HTTP, along with masked outbound preview and sending without confirmation, invalid/incomplete responses, semantic ambiguity gates and model UI startup. No authenticated provider calls were made; user keys are required for live validation. Historical metrics below describe the offline parser only.

# Validation — POC 0.7.0

The final automated and source diagnostics are recorded below; older sections are historical.

- Current automated suite: **138 passed** on September 7, 2026, including cross-model-review consolidation, semantic composition, holdings-selection, broad-signal, silver-dataset, grouped-split, and clarification-contract regressions.
- Live Streamlit smoke check: health endpoint and homepage returned HTTP 200 on local port 8524.
- Semantic probes: 92 queries in 26 groups. Preserve-meaning differences fell from 16/20 groups in v0.5.0 to 3/20 in v0.6.0. The three residual groups retain an intentional selection or requested-presentation distinction while capability and DAG remain invariant.
- Corpus: 242 records in 170 source groups; zero training-eligible records. The trainer correctly refuses to fit until review gates are met.
- LLM silver import: 242/242 case IDs; 73 high-confidence, 89 medium-confidence, 72 diagnostic no-majority, three contract-invalid, and five unresolved. Only the 162 valid high/medium semantic records are considered usable diagnostics; routing labels are excluded and training eligibility remains zero.
- Diagnostic split: 116 development and 46 held-out records across 110 groups; no split-group leakage and every held-out intent target was met where the usable support allowed a target.
- Focused review input: 86 unique cases in eight ZIP chunks, at most 12 cases each; every case appears once, options are semantic-only and deduplicated, and source identities remain outside the distributed package.
- Focused review output: all 86 issued cases returned exactly once; 85 valid option selections and one unresolved response. After semantic-contract validation, 84 frames were accepted, `base_114` remains pending contract review, and `base_106` remains unresolved. The consolidated v2 pool contains 206 usable semantic-silver records; human-reviewed and training-eligible counts remain zero.
- Targeted challenge-set agreement: 45/84 accepted labels exactly match the prior selected silver frame. POC exact-frame agreement remains 29/84 after conservative changes, while output agreement improves from 48/84 to 58/84, metric from 81/84 to 82/84, and goal from 71/84 to 72/84. These are selected-set LLM-silver agreement measurements, not accuracy.
- Step 5 semantic changes retain CIO evidence in compositions, separate holdings selection from explicit exposure intent, broaden fit-oriented solution matching, normalize scoped holdings-signal output, and allow broad market signals without a fabricated metric. Scope/taxonomy disagreements and new outcome composition contracts remain deferred.
- Context contract: `context_requirements` contains all workflow bindings; `clarification_required` contains only advisor-input requirements and is the sole context list driving `CLARIFY`. The deprecated `missing_context` alias is regression-tested for equality during schema 5.x.
- Privacy regressions verify that an optional model receives abstracted rather than raw text, an untrusted provider is rejected, and exported JSON omits the model input and raw query.
- Named-client and prioritized-client estimate-revision requests now share `subject_set`, capability, missing-context contract, function sequence, and DAG; only `subject_selection` differs.
- Source rerun: 153 rows; 9 quarantined; 144 evaluated; 83 authored capability matches. Decisions: 35 `ROUTE_PREVIEW`, 59 `CLARIFY`, 50 `CAPABILITY_GAP`, and 9 `QUARANTINED`. These are routing diagnostics, not accuracy.
- `data/outcome_diagnostics.json`: current per-capability and support distributions. Generic analytical fallback matches no longer count as coverage.
- `data/runtime_evaluation.json`: ten full-runtime configurations (rules-only and nine hybrid threshold/margin combinations), with explicit provenance/outcome-family strata. Unknown metadata stays unknown. No independently adjudicated expected routes were supplied; accuracy remains unreported.
- Focused regressions cover dedicated proposal sections, assumption dependencies, derived portfolio references, unsupported task mixtures, semantic gating, unverified available context, export privacy and schema-major fields.
- No OCR, live entitlement checks, financial payloads, computations, or independent human labeling were tested.

## Historical validation — POC 0.4.0

- Automated suite: **95 passed**, including eight Streamlit AppTest cases.
- Live startup smoke check: health endpoint returned HTTP 200 with `ok`; homepage returned HTTP 200.
- Query-only API regression: changing Problem Solved and Investment Agent Output while retaining the same query produces identical routing (excluding latency). Passing business-label arguments or context keys is rejected.
- Semantic cases: credit-spread intent/goal and instrument scope, client-book scope, household resolution, prioritized-client selection, voicemail output/source content, generic enrollment and rebalance scenarios.
- Context cases: no attachment, unresolved attachment, resolved instrument without a period, resolved instrument/period, conflicting and unavailable evidence, and missing host actor/time.
- Effect cases: one-time versus recurring flagging; recurring specification never performs a write; actual operational execution yields a capability gap.
- Graph checks: registered function IDs, complete inputs, compatible producers, explicit dependencies, cycles and forward references. Each source, task and final output input has an explicit binding.
- Privacy checks: outbound sockets blocked during routing; typed exports omit fictional identifiers; raw context values rejected; attachment cannot assert actor identity. LLM gateway remains disabled.
- UI cases: classifier/privacy, client-context binding, capability registry, batch diagnostics, attachment simulation, flagging mode, annotation protocol and intent registry/session reset.

## Original workbook diagnostic

Source: visible_rows_investment_agent(3).xlsx, matching the existing recognized source digest. Default thread/transcription rules were retained.

| Measure | Count |
| --- | ---: |
| Source rows | 153 |
| Quarantined | 9 |
| Routed | 144 |
| Capability matches | 138 |
| ROUTE_PREVIEW | 39 |
| CLARIFY | 103 |
| CAPABILITY_GAP decisions | 2 |

The six rows without a capability match include four whose primary decision is CLARIFY. Capability coverage and final decision are separate dimensions. No trusted host, client, instrument or attachment bindings were supplied in this source run.

This is descriptive routing coverage of authored templates, **not accuracy**. Capability matching does not prove that classification, evidence selection, financial methodology or the eventual outcome is correct. No independent labels or production-frequency assumptions were introduced.

The report also contains a separately identified synthetic attachment scenario. With instrument/period and host actor/time supplied, the credit-spread request produces research.credit_spread_explanation and ROUTE_PREVIEW; all evidence is still pending retrieval and execution is disabled.

Historical schema-2.1 fixture/source/sensitivity reports are retained as baseline evidence. They have not been relabeled as evaluation of the new semantic runtime. Existing legacy product-helper tests remain in the test total.

## Limitations

Python 3.12 with the pinned requirements. UI validation is functional AppTest, not visual browser screenshots. Attachment-state simulation does not test OCR, URL retrieval or entity resolution. Context AVAILABLE is a caller assertion. Nominal input-type checks do not validate production financial record schemas. Function PII policies are declarations and no live model, entitlement system, calculation service or orchestrator was tested.
