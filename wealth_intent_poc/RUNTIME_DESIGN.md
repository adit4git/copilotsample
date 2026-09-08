# Historical runtime design — 0.4.0

This document is retained as a previous design snapshot. For current 0.7.0 behavior, use `WEALTH_INTENT_CAPABILITY_DAG_POC_REVIEW.md`. The current runtime adds a clause/role parser, semantic validation, a cross-model-reviewed silver corpus, an optional trusted-local model interface, and an explicit `clarification_required` contract under schema 5.1.

## Runtime constraint

The advisor supplies a natural-language query, optionally with application selection, conversation or attachments. The advisor does not supply Problem Solved or Investment Agent Output. These columns have no public API parameters and never enter individual or batch inference. A regression test changes their contents while keeping the query unchanged and verifies identical routing.

Offline workbook review informed the authored outcome templates. The 57 problem descriptions and 59 output descriptions are not automatically converted into classes. Row 52 associates liquidity construction with monitoring; row 65 associates client screening with product shortlists; rows 77–83 associate instrument questions with a broad portfolio output. These conflicts are recorded for review and never override query semantics. No independent human adjudication was performed.

## Processing sequence

1. Run the existing local classifier on query text.
2. Refine typed semantics using locally masked query text: scope, goal, output format, metric, audience, effect and reference needs.
3. Validate optional context states and provenance against closed enums.
4. Match authored outcomes and permitted compound policies.
5. Compile registered functions with explicit input bindings and dependency edges.
6. Derive context requirements, retrieval requirements, node states and the final decision.
7. Export allowlisted metadata and display JSON/DAG in Streamlit.

The original classifier is retained as a baseline. Its labels and traces are displayed separately from refinements; its older context rules do not control the new outcome plan.

## Semantic interpretation

Intents identify requested work. Goal describes the specific result, such as explaining credit-spread movement. Scope distinguishes instruments, products/strategies, portfolios, clients, households, books and practices. Subject selection captures prioritized clients; metric captures a controlled signal type. Output/audience distinguish cited explanations, analysis tables, email drafts, voicemail bullets and internal guidance.

Effects distinguish read-only requests, draft-only work, ambiguous flagging, monitoring specifications and operational actions. An explicit UI one-time/recurring selection can resolve flagging ambiguity. Preparing a monitor specification does not create a subscription.

This remains a local lexical system. Refinement fixes known failures, including client-book scope, voicemail containing the substring email, missing source text and security references. It is not an independently trained semantic model, and matching a template does not prove that every requested nuance was understood.

## Context contract

| State | Interpretation |
| --- | --- |
| AVAILABLE | Caller asserts the binding is resolved. No actual value is sent to the POC. |
| PENDING_RESOLUTION | A reference exists but has not been resolved. |
| NEEDS_CLARIFICATION | Additional request information is needed. |
| CONFLICT | Available evidence disagrees. |
| UNAVAILABLE | The required input cannot currently be supplied. |

Actor/time availability can only be attributed to the host application; an attachment cannot assert actor identity. Query-inferred context reports source=query and assertion=inferred_type_only, without values. Recognizing a period phrase does not implement date normalization or a market-data calendar.

The attachment UI simulates presence, identified instrument, identified instrument and period, or conflict. Merely having an attachment does not mark instrument/period available. No OCR, URL retrieval, identity lookup or actual security-master query runs. Multiple-attachment extraction and source reconciliation remain later work.

## Compiled graph

Every function input binds to a named context type, registered configuration value, compatible upstream producer or typed artifact collection. The validator rejects absent/extra inputs, unknown functions, incompatible output types, missing dependency edges, cycles and forward references.

Household resolution uses its own function and cannot pass through a client-reference loophole. A prioritized book is selected explicitly before holdings-signal retrieval. Instrument reads have a registered reference-resolution step. Private evidence has an authorization dependency. Access paths and required permissions are contract metadata; no credentials or endpoints are embedded.

Context requirements come from the compiled graph. Evidence stays PENDING_RETRIEVAL even when its producer is PLANNED. Pending host identity/time produces PENDING_CONTEXT and blocks dependent nodes. PLANNED never means executed or authorized. All nodes carry invoked=false; execution_enabled is always false.

POC methodology/configuration versions identify contracts, not implemented financial algorithms. Function type checks use nominal evidence names; complete production record schemas and cardinality/financial semantics still need implementation.

## Catalog and composition

The baseline 29 intents have authored preview task templates with evidence sources, external inputs and typed task artifacts. Specialized outcomes include credit-spread explanation, generic content transformation, general market drafting and rebalance scenarios. Analytical task outputs feed transitions, proposals, monitoring specifications and explanations through explicit artifact dependencies.

Closed composition policies allow analytical packages, operational guidance with research/drafting, and transfer guidance with proposed allocation. Multiple operational workflows or real execution requests need another supported contract. There is no arbitrary tool loop or free-form endpoint selection.

These templates increase planning coverage; they do not establish that live systems can provide every input or fulfill every financial outcome. Registry definitions require domain review. Unsupported mixtures and unclear queries remain visible.

## Examples

| Scenario | Behavior |
| --- | --- |
| Credit-spread query alone | Instrument scope; clarify instrument and comparison period. |
| Attachment present, unresolved | Resolution remains pending; do not fabricate identity. |
| Instrument resolved, period absent | Clarify period unless the query/application supplies it. |
| Instrument/period and host context available | Route preview with evidence pending retrieval. |
| Conflicting attachment evidence | Review and expose conflict in dependent inputs. |
| Volatility email for a household | Household resolver and explicit missing household binding. |
| Voicemail rewrite | Voicemail output; require source content. |
| Flag revisions for prioritized clients | Book scope and explicit subset; clarify monitoring mode. |
| One-time flagging selected | No monitoring cadence/channel requirements. |
| Recurring selected | Prepare threshold/cadence/channel specification; never schedule. |

## Privacy and delivery boundary

No model or remote embeddings are called. All composition functions are preview contracts. Raw client values and attachment text are neither accepted in the context-state API nor emitted in typed exports. Raw query processing remains local to the Streamlit host, and masking may miss sensitive details.

PII-policy strings describe intended boundaries, not working de-identification or authorization. Before adding any model, implement and test minimization and local binding separately. The fail-closed LLM gateway remains disabled.

Implemented: query-only API, semantic refinement, typed context states, authored catalog expansion, DAG input validation, unified decisions, UI context simulation, JSON exports, workbook diagnostics and tests.

Deferred: actual attachment processing, live reference resolution, authentication/entitlements, source reads, calculations, message generation, monitoring creation, durable execution and independent labeling/accuracy validation.
