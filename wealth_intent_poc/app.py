"""Run with: python -m streamlit run app.py"""
import json
import os
os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
import pandas as pd
import streamlit as st
from wealth_intent.classifier import IntentClassifier
from wealth_intent.registry import SPECS, REGISTRY_VERSION
from wealth_intent.planning import capability_catalog, function_catalog
from wealth_intent.runtime import route_request, route_suite, export_route
CAPABILITY_REGISTRY = {x['id']: x for x in capability_catalog()}
FUNCTION_REGISTRY = {x['id']: x for x in function_catalog()}
from wealth_intent.privacy import mask
from wealth_intent.datasets import load_demo_suite, import_suite, evaluate
from wealth_intent.corpus import prepare_cases, metadata_rows, apply_annotations
import hashlib
import csv
import io
from pathlib import Path

st.set_page_config(page_title="Wealth Intent Lab", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
:root {--ink:#132b36; --green:#117a65;}
.stApp {background:#f5f7f8; color:var(--ink);}
[data-testid="stSidebar"] {background:#e9eff1; border-right:1px solid #d7e1e4;}
.block-container {padding-top:2.3rem; max-width:1450px;}
h1,h2,h3 {letter-spacing:-0.035em;}
.eyebrow {font-size:12px; letter-spacing:.16em; color:#117a65; font-weight:700; text-transform:uppercase;}
.hero {background:linear-gradient(120deg,#132b36,#1c4953); border-radius:18px; padding:30px 34px; color:white; margin-bottom:22px;}
.hero h1 {color:white; font-size:36px; margin:4px 0 8px;}
.hero p {color:#d9e6e9; max-width:760px; margin:0; font-size:16px;}
.hero .eyebrow {color:#8fe1cb;}
.pill {display:inline-block; border:1px solid #4e777d; border-radius:30px; padding:5px 12px; margin:18px 8px 0 0; font-size:12px; color:#dcefed;}
[data-testid="stMetric"] {background:white; border:1px solid #dde5e8; border-radius:12px; padding:14px 18px;}
[data-testid="stMetricValue"] {font-size:26px;}
.stButton>button[kind="primary"] {border-radius:8px;}
[data-testid="stTabs"] {margin-top:16px;}
</style>""", unsafe_allow_html=True)


@st.cache_resource
def get_classifier():
    # Only immutable generic model definitions are shared; never user queries.
    return IntentClassifier()


def reset_session():
    for key in list(st.session_state):
        del st.session_state[key]


with st.sidebar:
    st.markdown("### ◈ Wealth Intent Lab")
    st.caption("ADVISOR WORKFLOW PROOF OF CONCEPT")
    page = st.radio("Workspace", ["Classify a request", "Test a query suite", "Semantic corpus", "Annotation protocol", "Intent registry", "Capability registry"], key="page")
    st.divider()
    st.markdown("**Local processing**")
    st.caption("No LLM provider, API key, or client-system connection. Workflow execution is disabled.")
    with st.expander("Classification settings"):
        threshold = st.slider("Similarity fallback threshold", 0.10, 0.65, 0.23, 0.01, key="threshold")
        margin = st.slider("Minimum candidate margin", 0.01, 0.20, 0.035, 0.005, key="margin")
        st.caption("Unvalidated placeholders. Medium/high-risk intent candidates add 0.07/0.15 to this base threshold. Rules are separate; no scores are probabilities.")
    with st.expander("Local privacy dictionary"):
        terms = st.text_area("Additional sensitive terms, one per line", key="sensitive_terms", height=120,
                             placeholder="Add local client or entity names")
        st.caption("Session memory only. Detection remains heuristic; unmatched sensitive text may remain.")
    sensitive_terms = [t.strip() for t in terms.splitlines() if t.strip()]
    st.button("Clear session data", on_click=reset_session, width="stretch")
    st.caption(f"Registry {REGISTRY_VERSION} · POC 0.7.0")

classifier = get_classifier()


def hero(eyebrow, title, subtitle):
    # Called only with static application-owned strings.
    st.markdown(f'<div class="hero"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{subtitle}</p>'
                '<span class="pill">Python + Streamlit</span><span class="pill">No LLM calls</span>'
                '<span class="pill">Local workflow previews</span></div>', unsafe_allow_html=True)


def show_result(result):
    plan = result['capability_route']
    cols = st.columns(4)
    cols[0].metric("Routing decision", result["decision"].replace("_", " "))
    cols[1].metric("Detected tasks", len(result["intents"]))
    cols[2].metric("LLM egress", "Disabled")
    cols[3].metric("Classification time", f"{result['latency_ms']:.0f} ms")
    if result["decision"] == "ROUTE_PREVIEW":
        st.success(result["reason"] + " Required inputs still need verification.")
    elif result["decision"] == "CLARIFY":
        st.warning(result["reason"])
    else:
        st.warning(result["reason"])
    tabs = st.tabs(["Intent & scope", "Capability & DAG", "Privacy boundary", "Decision trace"])
    with tabs[0]:
        left, right = st.columns([1.35, 1])
        with left:
            st.markdown("#### Requested capabilities")
            if result["intents"]:
                st.dataframe(pd.DataFrame([{"Task": i, "Operation": next(s.operation for s in SPECS if s.id == i)} for i in result["intents"]]), hide_index=True, width="stretch")
            else:
                st.info("Specify the analysis, product question, communication, or workflow you need.")
            st.caption("Task labels describe requested work. They do not grant access or authorize execution.")
        with right:
            st.markdown("#### Request dimensions")
            dims = {"Scope": result["scope"], "Subject selection": result["subject_selection"],
                    "Metric": result["metric"] or "Not specified",
                    "Parameters": json.dumps(result["semantic_parameters"]) if result["semantic_parameters"] else "Not specified",
                    "Topics": ", ".join(result["topics"]) or "Not specified",
                    "Constraints": ", ".join(result["constraint_types"]) or "Not specified",
                    "Time": ", ".join(result["temporal"]) or "Not specified", "Output": result["output"],
                    "Requested effect": result["requested_effect"]}
            st.dataframe(pd.DataFrame(dims.items(), columns=["Dimension", "Interpretation"]), hide_index=True, width="stretch")
        st.markdown("#### Context contract")
        st.caption("Input: advisor query plus optional typed context. Business-purpose and expected-output columns are never inference inputs.")
        st.write(f"Goal: {result['goal']} · Audience: {result['audience']} · Capability: {result['capability_status']}")
        st.caption("Semantic engine: local clause/role parser. Optional trusted-local model: " +
                   (result['semantic_engine']['model_provider'] or "not configured"))
        context_rows = [
            {"Type": "Requirement", "Value": value} for value in result["context_requirements"]
        ] + [
            {"Type": "Context action", "Value": value} for value in result["context_actions"]
        ] + [
            {"Type": "Clarification required", "Value": value} for value in result["clarification_required"]
        ]
        if context_rows:
            st.dataframe(pd.DataFrame(context_rows), hide_index=True, width="stretch")
        else:
            st.caption("No client or application-scope context is required for this request.")
        if result['context_state']:
            st.dataframe(pd.DataFrame([{'Context': k, **v} for k, v in result['context_state'].items()]), hide_index=True, width='stretch')
        if result['evidence_requirements']:
            st.dataframe(pd.DataFrame(result['evidence_requirements']), hide_index=True, width='stretch')
    with tabs[1]:
        st.info("Unverified preview. Context availability is asserted, permissions are not checked, and no function is invoked.")
        st.write('Plan status:', result['plan_status'], '· Support:', result['support_level'])
        for question in result['clarification_questions']:
            st.warning(question['question'])
        match = plan["match"]
        if match["status"] == "CAPABILITY_GAP":
            st.warning(match["reason"])
            st.dataframe(pd.DataFrame(match["candidates"]), hide_index=True, width="stretch")
        else:
            cols = st.columns(3)
            cols[0].metric("Capability", plan["capability_id"])
            cols[1].metric("Workflow", plan["workflow_id"])
            cols[2].metric("Functions", len(plan["nodes"]))
            st.caption(plan.get("outcome", "Resolve semantic questions before compiling a plan."))
            graph_lines = ["digraph workflow {", "rankdir=TB;", "node [shape=box style=rounded];"]
            for node in plan["nodes"]:
                color = {"PLANNED": "#dbeaff", "NEEDS_INPUT": "#ffe7ad", "BLOCKED": "#e7ebed", "PENDING_CONTEXT": "#dbeaff", "CONFLICT": "#ffcccc", "UNAVAILABLE": "#ffd9cc"}[node["status"]]
                graph_lines.append(f'"{node["id"]}" [label="{node["id"]}\\n{node["function_id"]}\\n{node["status"]} · UNVERIFIED" fillcolor="{color}" style="rounded,filled"];')
                for dependency in node["depends_on"]:
                    graph_lines.append(f'"{dependency}" -> "{node["id"]}";')
            graph_lines.append("}")
            if plan['nodes']:
                st.graphviz_chart("\n".join(graph_lines), width="stretch")
            rows = [{
                "Node": node["id"], "Function": node["function_id"],
                "Class": node["function_class"], "Access path": node["access_path"],
                "Depends on": ", ".join(node["depends_on"]) or "—",
                "Status": node["status"],
            } for node in plan["nodes"]]
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
            st.markdown("#### Access paths")
            st.write(" · ".join(plan["access_paths"]))
            st.caption("Access paths are registered names, not credentials or live endpoints. Function inputs and PII policies are included in the JSON export.")
        if result["monitor_lifecycle"]:
            st.caption("Monitoring lifecycle: " + result["monitor_lifecycle"] + ". Nothing is persisted or scheduled.")
    with tabs[2]:
        st.markdown("#### LLM requests are structurally disabled")
        if st.checkbox("Inspect local display masking · may still contain PII"):
            st.code(result["masked_text"], language=None, wrap_lines=True)
        st.warning("Masking is heuristic and may miss names, context or identifying financial details. This text stays inside this Streamlit instance; it is excluded from downloads.")
        left, right = st.columns(2)
        with left:
            st.markdown("**Detected categories**")
            st.json(result["privacy_findings"])
        with right:
            st.markdown("**Closed LLM gateway**")
            st.json(result["egress"])
        st.caption("The contract is illustrative only. The send method raises an error. No provider SDK or model network call is implemented.")
    with tabs[3]:
        st.markdown("#### Candidate ranking")
        st.dataframe(pd.DataFrame(result["candidates"]), hide_index=True, width="stretch")
        st.caption("Word TF-IDF cosine similarity is separate from rule selection. Risk thresholds are unvalidated placeholders; this is not confidence.")
        st.markdown("**Rule matches and vetoes**")
        st.dataframe(pd.DataFrame(result["rule_decisions"]), hide_index=True, width="stretch")
        st.markdown("**Per-clause similarity fallback**")
        st.dataframe(pd.DataFrame(result["similarity_decisions"]), hide_index=True, width="stretch")
        st.caption(f"Clauses: {result['clause_count']} · Registry fingerprint: {result['registry_digest']}")
        st.markdown('**Semantic refinements and baseline comparison**')
        st.json({'baseline': result['baseline'], 'semantic_trace': result['semantic_trace']}, expanded=False)
        exported = export_route(result)
        st.json(exported, expanded=False)
        st.download_button("Download typed request JSON", json.dumps(exported, indent=2), "capability_request.json", "application/json")
        st.caption("Contains typed metadata only; no raw request, masked request, identifiers, or financial values.")


if page == "Classify a request":
    hero("From advisor language to explicit tasks", "Understand the request. Inspect the route.",
         "Explore intent, scope, privacy findings and the required workflow before any execution system is connected.")
    demos = {
        "Credit spread + attachment context": "How has credit spread moved for this issue, and what is driving it?",
        "Prioritized-client estimate revisions": "Flag major estimate revisions for top holdings across my prioritized clients.",
        "Volatility email": "Draft an email explaining recent volatility to this client.",
        "Overlap + tax transition": "Run an overlap analysis for account 999-00123 against two approved SMA strategies and estimate the transition tax impact. Draft an email explaining the trade-offs.",
        "CIO update + client impact": "Which clients are impacted by today's CIO guidance update, and how should I prioritize outreach?",
        "Performance discrepancy": "The manager says the fund is up but the account reports are down. Reconcile the performance reporting and draft talking points.",
        "Create a drift monitor": "Notify me daily when portfolios drift beyond CIO targets and draft a client-ready explanation.",
        "Negated notification": "Do not notify me. Show which portfolios have drifted beyond target weights.",
        "PII masking · fictional values": "Client Avery Example, email avery@example.test, account 999-00123, has $750,000. Prepare a tax-aware transition proposal for concentrated stock.",
        "Ambiguous follow-up": "What about the other one?",
    }
    st.selectbox("Load a scenario", list(demos), key="demo_choice")
    if st.button("Use selected scenario"):
        st.session_state["query"] = demos[st.session_state.demo_choice]
        st.session_state.pop("result", None)
    if "query" not in st.session_state:
        st.session_state.query = demos["Overlap + tax transition"]
    with st.form("request_form"):
        query = st.text_area("Advisor request", key="query", height=150, max_chars=16000)
        follow = st.checkbox("Use the previous task type for a follow-up", value=False)
        client_selected = st.checkbox(
            "A trusted client is already selected in the host application",
            value=False,
            help="Passes only the presence of a client_reference binding. No client identifier or profile enters the classifier.",
        )
        host_present = st.checkbox('Simulate authenticated actor and observation time', key='host_present')
        supplied = st.multiselect('Other resolved context types (simulation)', [
            'household_reference', 'subject_set_reference', 'advisor_book_scope', 'portfolio_reference',
            'prioritized_client_set', 'source_content', 'analysis_period', 'benchmark',
            'strategy_reference', 'comparison_targets', 'product_reference',
            'client_objectives', 'client_constraints', 'prior_review_reference',
            'gain_budget', 'transition_horizon', 'tax_assumptions',
            'order_reference', 'proposal_reference', 'holding_selection', 'ranking_basis', 'materiality_threshold',
            'monitoring_cadence', 'delivery_channel', 'screening_criteria', 'platform',
        ], key='resolved_types')
        attachment_state = st.selectbox('Attachment context (simulation)', [
            'No attachment context', 'Attachment present, unresolved',
            'Instrument identified', 'Instrument and period identified', 'Conflicting instruments',
        ], key='attachment_state')
        monitoring_mode = st.selectbox('If relevant, interpret flagging as',
                                      ['unspecified', 'one_time', 'recurring'], key='monitoring_mode')
        submitted = st.form_submit_button("Classify request", type="primary", width="stretch")
    st.caption('Context controls simulate resolution outcomes. No article fetching, OCR, identity lookup or entitlement verification is performed. Attachment presence alone does not establish instrument identity.')
    st.caption("Use fictional data for demonstrations. Typed requests and uploads remain in this local session; no raw-query logging is implemented.")
    if submitted:
        try:
            prior = st.session_state.get("last_intents", []) if follow else []
            context = {key: {'status': 'AVAILABLE', 'source': 'host_application'} for key in supplied}
            if client_selected: context['client_reference'] = {'status': 'AVAILABLE', 'source': 'host_application'}
            if host_present:
                for key in ['actor_context', 'as_of']: context[key] = {'status': 'AVAILABLE', 'source': 'host_application'}
            if attachment_state != 'No attachment context':
                context['attachment_reference'] = {'status': 'AVAILABLE', 'source': 'attachment'}
                context['security_reference'] = {'status': 'CONFLICT' if attachment_state == 'Conflicting instruments' else 'PENDING_RESOLUTION' if attachment_state == 'Attachment present, unresolved' else 'AVAILABLE', 'source': 'attachment'}
            if attachment_state == 'Instrument and period identified':
                context['analysis_period'] = {'status': 'AVAILABLE', 'source': 'attachment'}
            r = route_request(query, context=context, monitor_mode=monitoring_mode,
                              classifier=classifier, sensitive_terms=sensitive_terms,
                              threshold=threshold, margin=margin, prior_intents=prior)
            st.session_state.result = r
            if r["decision"] != "CLARIFY":
                st.session_state.last_intents = r["intents"]
        except ValueError as e:
            st.error(str(e))
    if "result" in st.session_state:
        show_result(st.session_state.result)

elif page == "Test a query suite":
    hero("Classification evidence", "Inspect the corpus before scoring.",
         "Original wording stays local. Separate provenance, length and annotation status; compare hybrid routing with a rules-only floor.")
    source = st.radio("Suite source", ["Built-in generic suite", "Upload XLSX or CSV"], horizontal=True, key="suite_source")
    cases = load_demo_suite() if source == "Built-in generic suite" else []
    source_token = "fixtures_v2"
    if source == "Upload XLSX or CSV":
        upload = st.file_uploader("Query suite", type=["xlsx", "csv"], key="suite_upload")
        st.caption("Supports the original Visible Rows workbook. Provenance is unknown unless explicitly annotated; length is not provenance. Uploaded Section values are not gold labels.")
        if upload:
            try:
                payload = upload.getvalue()
                cases = import_suite(payload, upload.name)
                source_token = hashlib.sha256(payload).hexdigest()
            except Exception:
                st.error("Import failed. Check format, size, query header, registered labels and annotation fields.")
    merge_threads = st.checkbox("Confirm suggested source thread links (43/44 and 133/134)", key="confirm_threads")
    st.caption("Links apply only to the exact recognized source workbook. Until confirmed, linked rows are quarantined. Incomplete transcriptions remain quarantined even after merging. Exact duplicate texts collapse automatically.")
    if cases:
        prepared = prepare_cases(cases, merge_threads=merge_threads)
        token = source_token + str(merge_threads)
        if st.session_state.get("annotation_token") == token:
            prepared = st.session_state.annotated_cases
        st.caption(f"{len(cases)} input rows → {len(prepared)} request units; {sum(c.get('quarantined',False) for c in prepared)} quarantined.")
        with st.expander("Corpus metadata and reviewed labels"):
            st.warning("Built-in labels were written by the registry author. They never qualify for performance metrics. Independent review is a human assertion; the app cannot verify reviewer identity or independence.")
            metadata = pd.DataFrame(metadata_rows(prepared))
            edited = st.data_editor(metadata, hide_index=True, width="stretch", height=300, key="annotations_"+token,
                disabled=["case","source_rows","group","characters","quarantined","reasons","corpus_binding"],
                column_config={
                    "provenance":st.column_config.SelectboxColumn(options=["unknown","template_prompt","advisor_email","rewritten_fixture"]),
                    "annotation_status":st.column_config.SelectboxColumn(options=["unlabeled","proposed","adjudicated"]),
                    "label_semantics":st.column_config.SelectboxColumn(options=["required","exhaustive"]),
                    "expected_scope":st.column_config.SelectboxColumn(options=["","general","advisor_book","household","account_or_client","practice"]),
                    "expected_decision":st.column_config.SelectboxColumn(options=["","ROUTE_PREVIEW","CLARIFY","REVIEW"]),
                    "independent_review":st.column_config.CheckboxColumn()})
            if st.button("Apply annotation metadata"):
                try:
                    prepared = apply_annotations(prepared, edited.to_dict("records"))
                    st.session_state.annotated_cases = prepared
                    st.session_state.annotation_token = token
                    st.success("Annotation metadata applied to this local corpus.")
                except ValueError as e:
                    st.error(str(e))
            st.download_button("Download annotation metadata only", pd.DataFrame(metadata_rows(prepared)).to_csv(index=False), "annotation_metadata.csv", "text/csv")
            st.caption("No query text is exported. The sidecar binds labels to this exact corpus using a digest; treat metadata as controlled information.")
            sidecar = st.file_uploader("Restore annotation metadata for this corpus", type=["csv"], key="annotation_upload")
            if sidecar and st.button("Restore annotations"):
                try:
                    restored = list(csv.DictReader(io.StringIO(sidecar.getvalue().decode("utf-8-sig"))))
                    prepared = apply_annotations(prepared,restored)
                    st.session_state.annotated_cases = prepared
                    st.session_state.annotation_token = token
                    st.success("Annotations restored. Rerun evaluation to use them.")
                except (ValueError, KeyError, UnicodeError):
                    st.error("Metadata does not match this corpus or has invalid fields.")
        if st.checkbox("Inspect a query locally"):
            index = st.selectbox("Case", range(len(prepared)), format_func=lambda j: prepared[j]["id"])
            show_original = st.checkbox("Show original wording locally · potentially sensitive")
            text = prepared[index]["query"] if show_original else mask(prepared[index]["query"], sensitive_terms).masked_text
            st.code(text, language=None, wrap_lines=True)
            st.caption("Neither original nor masked text is included in evaluation downloads. Masking does not establish anonymization.")
        if st.button("Run suite", type="primary"):
            with st.spinner("Comparing local classifier paths…"):
                st.session_state.batch = evaluate(prepared, classifier, threshold, margin, sensitive_terms)
                st.session_state.batch_source = source
                st.session_state.outcome_batch = route_suite(prepared, classifier=classifier,
                                                            threshold=threshold, margin=margin, sensitive_terms=sensitive_terms)
    if "batch" in st.session_state:
        batch = st.session_state.batch
        summary = batch["summary"]
        st.caption("Last completed run: " + st.session_state.batch_source + ". Rerun after changing corpus, labels or settings.")
        cols = st.columns(4)
        cols[0].metric("Request units", summary["cases"])
        cols[1].metric("Quarantined", summary["quarantined_cases"])
        cols[2].metric("Reviewed metric cases", summary["reviewed_cases"])
        cols[3].metric("Clarifications", summary["clarify_count"])
        st.info(summary["label_caveat"])
        st.markdown("#### Stratified evidence · hybrid and rules-only")
        st.dataframe(pd.DataFrame(batch["strata"]), hide_index=True, width="stretch")
        st.caption("Unknown provenance is not inferred from length. Exact-set metrics require exhaustive labels. Wilson intervals describe only reviewed exact-set agreement, not population representativeness. Required-label recall uses label assignments as denominator.")
        df = pd.DataFrame(batch["rows"])
        only_missing = st.checkbox("Show cases with missing expected labels", key="missing_only")
        st.dataframe(df[df.missing_expected != ""] if only_missing else df, hide_index=True, width="stretch")
        st.download_button("Download routing results CSV", df.to_csv(index=False), "routing_results.csv", "text/csv")
        st.download_button("Download stratified report", json.dumps(batch, indent=2), "classification_report.json", "application/json")
        if 'outcome_batch' in st.session_state:
            outcome_batch = st.session_state.outcome_batch
            st.markdown('#### Query-only outcome routing · schema 5.1')
            st.caption('The comparison above is the original classifier baseline. These results use semantic refinement and compiled outcome plans; source business labels never enter inference.')
            st.json({k: outcome_batch[k] for k in ('decisions', 'support_distribution', 'capability_distribution', 'provenance_decisions')})
            st.dataframe(pd.DataFrame([{'Case': row['case'], 'Decision': row['decision'],
                                      'Capability': row.get('result', {}).get('capability_id'),
                                      'Scope': row.get('result', {}).get('scope')}
                                     for row in outcome_batch['rows']]), hide_index=True, width='stretch')
            st.download_button('Download outcome routing JSON', json.dumps(outcome_batch, indent=2), 'outcome_routing.json', 'application/json')

elif page == "Semantic corpus":
    hero("Review before training", "Build semantic evidence without promoting guesses to truth.",
         "The bundled corpus combines source requests and synthetic probes, preserves lineage, and starts with every record excluded from training.")
    corpus_root = Path(__file__).resolve().parent / "data"
    manifest = json.loads((corpus_root / "semantic_corpus_manifest.json").read_text())
    cols = st.columns(4)
    cols[0].metric("Records", manifest["records"])
    cols[1].metric("Source groups", manifest["source_groups"])
    cols[2].metric("Training eligible", manifest["training_eligible"])
    cols[3].metric("Required reviewers", 3)
    st.warning("Author hypotheses and synthetic expectations are review prompts, not gold labels. The trainer refuses this corpus until the independent-review gates are met.")
    st.json(manifest)
    silver_manifest_path = corpus_root / "semantic_reviewed_silver_manifest_v2.json"
    if silver_manifest_path.exists():
        silver = json.loads(silver_manifest_path.read_text())
        st.markdown("#### Cross-model semantic silver review")
        cols = st.columns(4)
        cols[0].metric("Usable semantic silver", silver["usable_semantic_silver_records"])
        cols[1].metric("Step 5 accepted", silver["accepted_step5_cases"])
        cols[2].metric("Step 5 pending", silver["pending_step5_cases"])
        cols[3].metric("Training eligible", silver["training_eligible_records"])
        st.caption("Independent model-family review remains LLM silver evidence, not human ground truth. Capability, context, decisions and DAGs were not imported.")
        st.caption("Only eight semantic fields are retained. LLM capability, decision, and missing-context labels are excluded; the deterministic runtime derives routing and clarification.")
    st.markdown("#### Review artifacts")
    st.download_button("Download annotation template CSV",
                       (corpus_root / "semantic_annotation_template.csv").read_bytes(),
                       "semantic_annotation_template.csv", "text/csv")
    st.download_button("Download annotation schema",
                       (corpus_root / "semantic_annotation_schema.json").read_bytes(),
                       "semantic_annotation_schema.json", "application/json")
    st.code("python scripts/build_semantic_corpus.py\npython scripts/train_semantic_model.py", language="bash")
    st.caption("Training is local and opt-in. A trusted-local model may propose only controlled semantic fields; deterministic validation and the capability/DAG compiler remain authoritative.")

elif page == "Annotation protocol":
    hero("Classifier scope only", "Define what a correct label means.",
         "Independent annotation and original wording are prerequisites for evaluating classification quality.")
    st.markdown("""
1. **Prepare request units.** Confirm thread links; preserve source rows; quarantine incomplete text; keep duplicates in one group.
2. **Label provenance explicitly.** Choose template prompt, advisor email, or unknown. Character count is a separate field.
3. **Use three independent reviewers.** Reviewers see original wording and the frozen label guide, but not model predictions or one another's labels.
4. **Label tasks and scope.** Distinguish required labels from an exhaustive label set. An empty exhaustive set represents an unsupported request.
5. **Adjudicate disagreements.** Record all initial label sets separately in your controlled review process. A domain lead resolves disagreements with a written rationale before setting adjudicated status.
6. **Measure agreement before model performance.** Use per-label agreement and set overlap, with support counts. Low-support or disputed labels stay provisional; do not manufacture agreement by editing labels to match predictions.
7. **Keep evaluation independent.** Split by request/thread group before generating paraphrases. Use untouched original-wording cases for acceptance.

This POC provides metadata editing and conditional scoring. It does not authenticate reviewers, retain a production query log, run a review queue, or certify independent adjudication. No independent human annotation has been performed in this build.
""")
    st.info("Success criterion: identify the requested work, scope, and need for clarification. Financial calculations, recommendation generation, specialist handoffs and operational execution are outside this update.")

elif page == "Intent registry":
    hero("A versioned capability contract", "Inspect the intent registry.",
         "Every intent maps to an operation, an approved service name and an explicit set of required inputs.")
    df = pd.DataFrame([{"Intent": s.id, "Family": s.family, "Task": s.title, "Operation": s.operation, "Service": s.service} for s in SPECS])
    st.dataframe(df, hide_index=True, width="stretch")
    selected = st.selectbox("Intent definition", [s.id for s in SPECS], key="registry_intent")
    st.json(next(s.to_dict() for s in SPECS if s.id == selected))
    st.markdown("#### What this POC establishes")
    st.write("Multi-intent routing, local minimization, explicit task dependencies, typed exports, abstention, corpus preparation, and stratified evaluation.")
    st.markdown("#### What remains before production")
    st.write("Independently labeled evaluation data; calibrated local models; robust entity resolution and NER; authenticated advisor entitlements; governed data services; current product evidence; persistent workflow controls; and security review.")
    st.caption("Only generic examples are fitted into the TF-IDF model. Uploaded data is evaluated, never used for automatic training.")

else:
    hero("Governed outcome routing", "Inspect capabilities and registered functions.",
         "Capabilities define supported outcomes. Their workflow graphs reference only registered functions and named access paths.")
    st.markdown("#### Capability contracts")
    capability_rows = [{
        "Capability": item["id"], "Version": item["version"],
        "Outcome": item["outcome"], "Workflow": item["workflow_id"],
        "Functions": len(item["function_ids"]),
    } for item in capability_catalog()]
    st.dataframe(pd.DataFrame(capability_rows), hide_index=True, width="stretch")
    selected_capability = st.selectbox("Capability definition", list(CAPABILITY_REGISTRY), key="registry_capability")
    st.json(next(item for item in capability_catalog() if item["id"] == selected_capability))
    st.markdown("#### Function contracts")
    function_rows = [{
        "Function": item["id"], "Class": item["function_class"],
        "Execution": item["execution_class"], "Access path": item["access_path"],
        "PII policy": item["pii_policy"],
    } for item in function_catalog()]
    st.dataframe(pd.DataFrame(function_rows), hide_index=True, width="stretch")
    selected_function = st.selectbox("Function definition", list(FUNCTION_REGISTRY), key="registry_function")
    st.json(next(item for item in function_catalog() if item["id"] == selected_function))
    st.caption("All functions are contract metadata in this POC. No adapter, credential, model provider, or execution runtime is connected.")
