# API model edition 0.8.3

- Default Anthropic to forced, non-strict, data-only tool response with complete local semantic validation; retain selectable native JSON-schema mode. No tool execution, retries or extra calls.
- Show known schema field names and fixed complexity/unsupported-feature hints in errors.
- 162 mocked/offline tests pass; original native schema rejection cause remains unconfirmed.

# API model edition 0.8.2

- Replace generic HTTP errors with fixed diagnostic categories derived from provider responses; never echo arbitrary response details. Trim model IDs and keys. No retries or routing changes.
- Original reported Anthropic 400 cause remains unconfirmed; authenticated reproduction was unavailable.

# API model edition 0.8.1

- Remove the user confirmation gate; automatically show masked request text before Classify and the text used for the displayed result afterward.
- Send the locally masked preview, with no editable outbound bypass. Update JSON metadata and setup/design documentation.

# API model edition 0.8.0

- Add model_app.py and OpenAI/Anthropic structured-output adapters.
- Model path bypasses regex/TF-IDF semantic inference entirely.
- Add editable outbound text review before remote calls; heuristic masking is not a PII guarantee.
- Validate catalog semantics and ambiguity before deterministic capability/DAG compilation.
- Add environment/key controls, provider model ID selection, setup instructions and error handling.
- 144 tests pass with mocked providers; live-key verification remains pending.

# v0.7.0 — cross-model semantic review consolidation

- Validate all eight independent model-family result files against the issued schemas, chunks, case IDs, and anonymized candidates; all 86 cases are present exactly once.
- Restore hidden candidate provenance for audit analysis while excluding reviewer capability, decision, context, function, and DAG suggestions from runtime labels.
- Accept 84 contract-valid semantic frames; keep one null-scope frame pending contract review and one mixed monitoring/proposal request unresolved.
- Publish a consolidated 242-record `semantic_reviewed_silver.2` dataset with 206 usable semantic-silver records, zero human-reviewed records, and zero training-eligible records.
- Retain explicit CIO evidence tasks in composed requests, distinguish holdings selection from portfolio-exposure intent, broaden fit-oriented solution matching, and normalize scoped holdings-signal output.
- Allow `metric=null` for broad market signals instead of manufacturing an unsupported enumerated metric.
- Leave inconsistent scope/selection judgments, rating-event taxonomy, monitoring semantics, and new capability-composition contracts for separate review.
- Add a reproducible Step 5 importer, findings report, UI metrics, and regression coverage; 138 tests pass.

# v0.6.1 — semantic silver gate and explicit clarification contract

- Import the completed three-pass/adjudicated LLM run as a separate semantic-only silver dataset.
- Retain only intent, scope, goal, output, audience, metric, subject selection, and requested effect from LLM labels.
- Exclude LLM capability, decision, and missing-context labels from the quality-gated dataset.
- Assign 73 high-confidence, 89 medium-confidence, 72 no-majority diagnostic, three contract-invalid, and five unresolved records; 162 are usable for diagnostic semantic evaluation and zero for training.
- Add `clarification_required` as the canonical advisor-input subset of `context_requirements`.
- Retain `missing_context` as a deprecated schema-5.x compatibility alias.
- Add silver quality metrics to the Streamlit corpus screen and raise the runtime contract to schema 5.1 / POC 0.6.1.
- Freeze 162 usable silver records into 116 development and 46 held-out diagnostics with zero split-group leakage and intent-aware group stratification.
- Build an 86-case, eight-chunk focused review package with per-case anonymized candidate frames; keep the source-provenance map outside the upload package.

# v0.6.0 — hybrid semantic contract and review-gated corpus

- Add a local clause/role parser with negation, role, synonym, period, selection, and effect handling.
- Normalize named, selected, prioritized, and filtered multi-client requests to `subject_set`; retain selection strategy separately.
- Add deterministic semantic validation before capability matching and DAG compilation.
- Add an optional trusted-local model provider that sees only locally abstracted text, may propose controlled fields, and is disabled by default.
- Add a 242-record, lineage-preserving annotation corpus, CSV review template, schema, manifest, and guarded local trainer. No bundled record is training eligible.
- Make the holdings-signal outcome contract explicit about holding selection, materiality threshold, and analysis period.
- Reduce synthetic preserve-meaning probe flags from 16/20 groups to 3/20; remaining differences are intentional selection or presentation metadata and do not change the matched capability/DAG.
- Breaking runtime schema 5.0; versioned workflows use `.v4`.

# v0.5.0 — explicit outcomes and unverified plan previews

- Breaking runtime schema 4.0; versioned workflows use .v3. No legacy dual-serving.
- Remove generic analytical/operations fallback routing; expose unsupported intent combinations without DAGs.
- Add authored concentrated-stock transition-proposal and book holdings-signal composition contracts.
- Bind portfolio reference to the client snapshot; require gain budget, horizon and tax assumptions explicitly for the proposal.
- Clarify workflow-changing semantic ambiguity before compiling; retain provisional graphs for missing bindings.
- Add separate unverified/execution-readiness metadata and graph labels; no green readiness implication.
- Report support/capability distributions and full-runtime rules-only comparison with provenance/family strata and sensitivity sweeps.
- Correct classifier documentation: word TF-IDF only, distinct rule/similarity decisions, baseline participates in routing.
- Preserve no-LLM-egress, no execution and query-only inference; independent annotation and financial payload implementation remain deferred.

# v0.4.0 — query-only outcome routing and typed context

- Runtime accepts query text and optional typed context; business-purpose and expected-output columns are never inference inputs.
- Add semantic goals, audience, output, instrument/portfolio/book scope, source-content requirements and explicit flagging mode.
- Add reference-resolution and credit-spread templates, generic content transformation, rebalance scenarios, 29 authored intent templates and fixed compound policies.
- Bind every input to context, configuration or compatible upstream output; validate missing/extra inputs, dependency edges, cycles and type mismatches.
- Derive context requirements and final decision from the plan; separate clarification, pending resolution/retrieval, conflict and unavailable evidence.
- Fix household resolver mismatch; explicitly bind prioritized-client selection; keep actor/time context pending unless supplied.
- Add attachment-state simulation and per-query/batch schema-3.0 exports, retaining the original classifier as a baseline.
- Add metadata-invariance, no-egress, graph-validation, context and UI tests.
- All templates remain authored previews. No actual OCR, URL fetching, entity lookup, model calls, calculations or operational execution is connected.

# v0.3.0 — governed capability matching

## Capability and function contracts

- Add three registered business outcomes: client market communication, client exposure analysis, and advisor-book household screening.
- Add versioned function contracts with typed inputs/outputs, execution class, PII policy, side-effect class, and a named access path.
- Match a capability only when it covers the complete classified request, scope, and output; otherwise return `CAPABILITY_GAP`.
- Compile the selected workflow into a validated, topologically ordered DAG with `PLANNED`, `NEEDS_INPUT`, and `BLOCKED` node states.
- Keep execution disabled. Access paths are registry metadata and no adapter, credential, client system, calculation service, or model provider is connected.
- Restrict the model-assisted draft node to `model_safe_context`; trusted functions own client resolution, authorization, retrieval, minimization, binding, and validation.
- Add a Streamlit Capability & DAG view and a capability/function registry screen.

# v0.2.0 — classifier-focused revision

## v0.2.1 — client-context contract

- Client/account references now produce typed context requirements and context actions.
- An unresolved client reference returns `missing_context: [client_reference]` and `CLARIFY`.
- A trusted host-application selection can supply the binding type without passing a client identifier or profile into the classifier.
- Free-text account numbers never count as trusted bindings.
- Typed export schema is 2.1 and includes context-contract fields.

## Implemented

- Separate explicit rule matches/vetoes from cosine similarity; remove mixed scores and character n-grams.
- Add clause-level evidence and within-clause specificity. Remove the five-task cap without adding any execution capabilities.
- Expose unvalidated risk-tier thresholds, settings and registry fingerprint; schema 2.0 removes score.
- Recognize the exact source workbook; confirm candidate thread links; quarantine incomplete units; collapse exact duplicates and flag annotation conflicts.
- Keep original wording local; treat provenance as annotated metadata rather than inferred from length.
- Add corpus-bound annotation sidecars, expected scope and routing-state labels, and independent-review assertions.
- Report hybrid versus rules-only strata. Remove aggregate accuracy headlines. Registry-author fixtures remain regression diagnostics even if relabeled.
- Add a descriptive sensitivity grid; no parameter optimization or accuracy improvement claim.
- Make disabled LLM egress the main privacy claim; local masking inspection is opt-in.
- Replace the SMA UI page with the annotation protocol. Existing SMA helpers remain legacy code; no financial analytics, generation or handoff functions were added.

## Not established

No independent human labels or production frequencies are available. The metadata editor does not authenticate annotators or enforce blindness. Source thread links are operator-confirmed suggestions; other near-duplicates require review. Operating points are placeholders. Workflow previews do not establish authorization or readiness. No production query-retention process was introduced.

The original standalone proposal document remains historical. This README and changelog describe the updated POC.
