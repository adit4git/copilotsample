# Wealth Intent Lab — API model edition 0.8.3

Start with **MODEL_SETUP.md** and run `python -m streamlit run model_app.py` after installing `requirements-models.txt`. OpenAI and Anthropic interpret approved minimized text as the primary semantic engine. Keys alone do not create a local model; these are remote API calls.

The sections below describe the retained offline comparison app (0.7.0), launched with `app.py`. Its no-egress claims apply only to that offline path.

# Wealth Intent Lab — POC 0.7.0

**Start with `WEALTH_INTENT_CAPABILITY_DAG_POC_REVIEW.md` for the standalone current architecture and feedback disposition.**

Schema 5.1 adds an explicit distinction between all workflow `context_requirements` and the subset requiring advisor input in `clarification_required`. The former `missing_context` field is retained as a deprecated compatibility alias. The local model remains disabled by default and never selects a capability, function, decision, or DAG.

Python/Streamlit: advisor query → semantic interpretation → registered outcome → typed function DAG → JSON preview.

**Runtime input is the advisor query plus optional application/attachment context. `Problem Solved` and `Investment Agent Output` are neither required nor accepted by the runtime API.** The worksheet columns inform offline catalog design and review only.

## Run

Use Python 3.11+ (tested with Python 3.12):

```bash
cd wealth_intent_poc
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows activate with `.venv/Scripts/Activate.ps1`. Run from the project root to use loopback binding and disabled telemetry. Open http://localhost:8501. Inference needs no API key, model download or network call; installing dependencies requires package access.

## Query-only public API

```python
from wealth_intent.runtime import route_request, export_route

result = route_request(
    "How has credit spread moved for this issue, and what is driving it?",
    context={
        "security_reference": {"status": "AVAILABLE", "source": "attachment"},
        "analysis_period": {"status": "AVAILABLE", "source": "attachment"},
        "actor_context": {"status": "AVAILABLE", "source": "host_application"},
        "as_of": {"status": "AVAILABLE", "source": "host_application"},
    },
)
print(export_route(result))
```

These are simulated resolution-state assertions, not instrument values or proof of authorization. The query works alone; without those bindings it returns `CLARIFY` for instrument and comparison period. An attachment that is present but unresolved produces `PENDING_RESOLUTION`, never a fabricated identity.

Context accepts registered type/status/source triples only. Raw values, client IDs, attachment text, arbitrary keys and business-label keys are rejected. `export_route()` excludes raw and masked query text. Set `monitor_mode="one_time"` or `"recurring"` to clarify flagging; the default is `"unspecified"`.

## Output contract — schema 5.1 (experimental)

New fields include `semantic_engine`, `semantic_validation`, and `semantic_parameters`; workflow IDs use `.v4`. `subject_set` provides a common planning scope for named client/account sets, selected clients, prioritized clients, and book subsets, while `subject_selection` preserves how the set was chosen. Consumers must accept empty node lists and null workflow IDs.

The result retains original classifier evidence separately and adds goal, audience, metric, subject selection, semantic status, capability status/ID, workflow ID, context states, evidence requirements and the compiled capability route.

| Field | Meaning |
| --- | --- |
| `intents`, `scope`, `goal`, `output` | Query-derived task and outcome interpretation. |
| `baseline` | Original classifier result, before semantic refinement. |
| `context_requirements` | External context required by the selected workflow. |
| `context_actions` | Registered read/authorization functions derived from the plan. |
| `context_state` | Available, pending, missing, conflicting or unavailable binding states. |
| `clarification_required` | Request-specific inputs the advisor must clarify; drives `CLARIFY`. |
| `missing_context` | Deprecated schema-5.x alias of `clarification_required`. |
| `evidence_requirements` | Evidence types, producers and `PENDING_RETRIEVAL` status. |
| `capability_route.nodes` | Function versions, access paths, permissions, PII policies, typed bindings and dependencies. |
| `decision` | `CLARIFY`, `REVIEW`, `CAPABILITY_GAP`, or `ROUTE_PREVIEW`. |
| `execution_enabled` | Always false; every node reports `invoked: false`. |

Semantic ambiguity, capability coverage and data availability are separate. A capability can match while a reference needs clarification. `ROUTE_PREVIEW` can still contain pending host-context nodes; it is not operational readiness.

## Screens

| Screen | Purpose |
| --- | --- |
| Classify a request | Query-only routing, context simulation, semantic dimensions, JSON and DAG. |
| Test a query suite | Original baseline comparison plus a separate schema-5.0 outcome report. |
| Semantic corpus | Corpus manifest, training gate, and downloadable annotation artifacts. |
| Annotation protocol | Independent labeling, adjudication and evaluation requirements. |
| Intent registry | Original 29-label baseline definitions. |
| Capability registry | Expanded outcome templates, functions and access paths. |

Attachment controls simulate resolution outcomes. No URL fetching, screenshot OCR, instrument lookup or entitlement verification is performed. No business-purpose or expected-output fields appear in the runtime form.

## Planning

Every function input binds to explicit context, configuration, an upstream output, or a typed artifact collection. Validation checks registered function IDs, complete inputs, producer/consumer compatibility, dependency edges, cycles and forward references. Types are controlled nominal fact names, not production payload schemas for financial records.

Node states are `PLANNED`, `NEEDS_INPUT`, `PENDING_CONTEXT`, `BLOCKED`, `CONFLICT`, and `UNAVAILABLE`. `PLANNED` means included in a valid preview with supplied or planned input bindings; it does not mean a permission was granted or data was retrieved.

All 29 original intents have authored preview task templates. Specialized templates include credit-spread explanation, content transformation and rebalance scenarios. Only explicitly contracted task combinations can be composed; generic analytical/operations fallback packages are no longer routable. Actual operational execution and unsupported mixtures return capability gaps. Validation is structural and nominal, not field-level financial payload validation.

## Source diagnostics and tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python scripts/review_outcomes.py --input /path/to/visible_rows_investment_agent.xlsx
python scripts/evaluate_outcomes.py --input /path/to/visible_rows_investment_agent.xlsx --sensitivity
```

The original workbook has 153 rows. Default preparation quarantines nine rows and routes 144. Thread links require operator confirmation; incomplete source text remains quarantined. The bundled 153 rewrites are registry-author fixtures, not independent gold data.

`data/outcome_diagnostics.json` records the query-only source run, metadata conflict notes by row number, and a separate synthetic attachment-context example. Raw queries, names, financial values and business-label prose are excluded. Template matching is not proof of correct interpretation or financial feasibility. Independent labels and held-out evaluation remain required.

Historical schema-2.1 reports in `data/` describe the earlier classifier. `workflows.py` and `capabilities.py` remain legacy examples; the current UI/public entry point uses `runtime.py`, `semantic.py` and `planning.py`.

## Privacy and limitations

The actual privacy guarantee is disabled LLM egress: `EgressGateway.send()` raises. No provider or remote embeddings are integrated. Masking remains heuristic. Function PII policies describe a future boundary and are not implemented DLP or de-identification controls.

The default semantic layer is a local clause/role parser over rules and TF-IDF. An optional local model can propose only controlled fields after PII abstraction; proposals below threshold are ignored and all proposals pass deterministic validation. The model is not configured or trained in the shipped runtime. No business metadata is consulted at inference. Context availability is a caller assertion, not authenticated evidence.

## Semantic corpus and optional local model

```bash
python scripts/build_semantic_corpus.py
python scripts/train_semantic_model.py
```

The builder produces 242 grouped records from the sanitized query suite and synthetic probe set. Every record starts with `training_eligible=false`; authored hypotheses are not labels. Training requires complete adjudicated labels, an independent-review assertion, at least three distinct reviewers, approved production-like provenance, at least 30 eligible cases, and minimum per-intent support. Related requests stay in one split group. See `SEMANTIC_CORPUS_GUIDE.md`.

The initial LLM run remains in `data/semantic_silver_labels_v1.jsonl`. A different model family subsequently reviewed 86 targeted disagreement cases from anonymized candidate frames. The validated result is `data/semantic_reviewed_silver_labels_v2.jsonl`: 84 Step 5 frames were accepted, one remains contract-invalid, and one remains unresolved. The consolidated semantic-silver pool has 206 usable records. It retains only eight semantic fields and excludes LLM-generated capabilities, decisions, context requirements, functions, and DAGs. Every record remains `training_eligible=false`, `human_reviewed=false`, and `independent_review=false`; cross-model review is silver evidence, not human ground truth. See `STEP5_REVIEW_FINDINGS.md`.

Before production, validate actual attachment extraction, identity and instrument resolution, least-privilege access, real payload schemas, methodologies, evidence lineage, retention and operational controls. This release provides classification and plan previews only.
