"""Governed capability matching and preview-only DAG compilation.

The registry contains contracts, not callable client-system integrations. A
compiled node describes the only function and access path that a future runtime
may invoke. This POC never executes a node.
"""
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class FunctionSpec:
    id: str
    version: str
    function_class: str
    execution_class: str
    access_path: str
    required_inputs: tuple[str, ...]
    produces: tuple[str, ...]
    pii_policy: str
    side_effect_class: str = "none"


@dataclass(frozen=True)
class WorkflowNode:
    id: str
    function_id: str
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class CapabilitySpec:
    id: str
    version: str
    workflow_id: str
    outcome: str
    required_intents: tuple[str, ...]
    supported_intents: tuple[str, ...]
    scopes: tuple[str, ...]
    output_types: tuple[str, ...]
    nodes: tuple[WorkflowNode, ...]


def fn(id, function_class, execution_class, access_path, required_inputs, produces,
       pii_policy="no_client_data"):
    return FunctionSpec(id, "1.0.0", function_class, execution_class, access_path,
                        tuple(required_inputs), tuple(produces), pii_policy)


FUNCTION_SPECS = (
    fn("client.resolve", "read", "deterministic", "trusted_host_context",
       ["client_reference"], ["resolved_client_reference"], "trusted_boundary_only"),
    fn("access.authorize_client_read", "decide", "deterministic", "policy_decision_point",
       ["actor_context", "resolved_client_reference", "capability_id"],
       ["authorized_client_scope"], "identifiers_allowed_inside_trusted_boundary"),
    fn("client.read_communication_context", "read", "deterministic", "client_context_gateway",
       ["authorized_client_scope", "as_of"],
       ["client_profile", "portfolio_exposure", "communication_preferences"],
       "trusted_boundary_only"),
    fn("research.retrieve_approved_market_content", "read", "deterministic",
       "approved_research_gateway", ["as_of"], ["approved_market_content"],
       "approved_non_client_content_only"),
    fn("privacy.prepare_drafting_input", "compute", "deterministic", "trusted_privacy_boundary",
       ["client_profile", "portfolio_exposure", "communication_preferences",
        "approved_market_content"], ["model_safe_context", "binding_tokens"],
       "remove_or_tokenize_client_data"),
    fn("content.draft", "model_assisted", "bounded_model", "model_gateway_pii_blocked",
       ["model_safe_context"], ["draft_with_binding_tokens"], "no_raw_pii"),
    fn("content.bind_locally_and_validate", "compose", "deterministic", "trusted_composer",
       ["draft_with_binding_tokens", "binding_tokens", "approved_market_content"],
       ["validated_client_draft"], "trusted_boundary_only"),

    fn("portfolio.read_positions", "read", "deterministic", "portfolio_data_gateway",
       ["authorized_client_scope", "as_of"], ["positions_snapshot"], "trusted_boundary_only"),
    fn("portfolio.calculate_exposure", "compute", "deterministic", "portfolio_compute_service",
       ["positions_snapshot", "methodology_version"], ["signed_exposure_artifact"],
       "pseudonymous_subject_reference"),
    fn("artifact.verify", "verify", "deterministic", "artifact_verifier",
       ["signed_exposure_artifact"], ["verified_exposure_artifact"],
       "pseudonymous_subject_reference"),

    fn("book.resolve", "read", "deterministic", "trusted_host_context",
       ["advisor_book_scope"], ["resolved_book_scope"], "trusted_boundary_only"),
    fn("access.authorize_book_read", "decide", "deterministic", "policy_decision_point",
       ["actor_context", "resolved_book_scope", "capability_id"], ["authorized_book_scope"],
       "identifiers_allowed_inside_trusted_boundary"),
    fn("book.read_portfolios", "read", "deterministic", "portfolio_data_gateway",
       ["authorized_book_scope", "as_of"], ["book_portfolio_snapshot"],
       "trusted_boundary_only"),
    fn("book.screen_households", "compute", "deterministic", "screening_engine",
       ["book_portfolio_snapshot", "screening_criteria", "rule_set_version"],
       ["screening_results"], "pseudonymous_subject_reference"),
    fn("book.rank_results", "compute", "deterministic", "ranking_engine",
       ["screening_results", "ranking_policy"], ["ranked_screening_results"],
       "pseudonymous_subject_reference"),
)

FUNCTION_REGISTRY = {spec.id: spec for spec in FUNCTION_SPECS}


CAPABILITY_SPECS = (
    CapabilitySpec(
        id="communication.client_market_update",
        version="1.0.0",
        workflow_id="client_market_update.v1",
        outcome="Create an exposure-aware client market communication draft",
        required_intents=("content.draft",),
        supported_intents=("content.draft", "research.cio", "research.security"),
        scopes=("account_or_client", "household"),
        output_types=("email_draft", "talking_points"),
        nodes=(
            WorkflowNode("resolve_client", "client.resolve"),
            WorkflowNode("authorize_client", "access.authorize_client_read", ("resolve_client",)),
            WorkflowNode("read_client_context", "client.read_communication_context", ("authorize_client",)),
            WorkflowNode("retrieve_market_content", "research.retrieve_approved_market_content"),
            WorkflowNode("prepare_model_input", "privacy.prepare_drafting_input",
                         ("read_client_context", "retrieve_market_content")),
            WorkflowNode("draft", "content.draft", ("prepare_model_input",)),
            WorkflowNode("bind_and_validate", "content.bind_locally_and_validate",
                         ("draft", "prepare_model_input", "retrieve_market_content")),
        ),
    ),
    CapabilitySpec(
        id="portfolio.client_exposure_analysis",
        version="1.0.0",
        workflow_id="client_exposure_analysis.v1",
        outcome="Calculate and verify client portfolio exposure",
        required_intents=("portfolio.exposure",),
        supported_intents=("portfolio.exposure",),
        scopes=("account_or_client", "household"),
        output_types=("analysis_table", "workflow_plan"),
        nodes=(
            WorkflowNode("resolve_client", "client.resolve"),
            WorkflowNode("authorize_client", "access.authorize_client_read", ("resolve_client",)),
            WorkflowNode("read_positions", "portfolio.read_positions", ("authorize_client",)),
            WorkflowNode("calculate_exposure", "portfolio.calculate_exposure", ("read_positions",)),
            WorkflowNode("verify_artifact", "artifact.verify", ("calculate_exposure",)),
        ),
    ),
    CapabilitySpec(
        id="book.household_screening",
        version="1.0.0",
        workflow_id="household_screening.v1",
        outcome="Screen and rank households within an entitled advisor book",
        required_intents=("book.screen",),
        supported_intents=("book.screen", "portfolio.drift", "portfolio.exposure"),
        scopes=("advisor_book",),
        output_types=("ranked_table", "analysis_table", "workflow_plan"),
        nodes=(
            WorkflowNode("resolve_book", "book.resolve"),
            WorkflowNode("authorize_book", "access.authorize_book_read", ("resolve_book",)),
            WorkflowNode("read_portfolios", "book.read_portfolios", ("authorize_book",)),
            WorkflowNode("screen_households", "book.screen_households", ("read_portfolios",)),
            WorkflowNode("rank_results", "book.rank_results", ("screen_households",)),
        ),
    ),
)

CAPABILITY_REGISTRY = {spec.id: spec for spec in CAPABILITY_SPECS}


def _candidate(spec, result):
    selected = set(result["intents"])
    required = set(spec.required_intents)
    unsupported = selected - set(spec.supported_intents)
    scope_ok = result["scope"] in spec.scopes
    output_ok = result["output"] in spec.output_types
    return {
        "capability_id": spec.id,
        "required_intents_present": required <= selected,
        "scope_supported": scope_ok,
        "output_supported": output_ok,
        "uncovered_intents": sorted(unsupported),
        "eligible": required <= selected and scope_ok and output_ok and not unsupported,
    }


def match_capability(result: dict) -> dict:
    """Match the typed request to one complete registered business outcome."""
    candidates = [_candidate(spec, result) for spec in CAPABILITY_SPECS]
    eligible = [candidate for candidate in candidates if candidate["eligible"]]
    if not eligible:
        return {
            "status": "CAPABILITY_GAP",
            "capability_id": None,
            "capability_version": None,
            "workflow_id": None,
            "reason": "No registered capability covers the complete typed request, scope, and output.",
            "candidates": candidates,
        }
    selected = eligible[0]
    spec = CAPABILITY_REGISTRY[selected["capability_id"]]
    return {
        "status": "MATCHED",
        "capability_id": spec.id,
        "capability_version": spec.version,
        "workflow_id": spec.workflow_id,
        "reason": "The complete typed request is covered by a registered capability contract.",
        "candidates": candidates,
    }


def compile_capability_plan(result: dict) -> dict:
    """Compile the matched workflow into a validated, non-executable DAG preview."""
    match = match_capability(result)
    if match["status"] != "MATCHED":
        return {
            "mode": "preview_only",
            "match": match,
            "capability_id": None,
            "workflow_id": None,
            "nodes": [],
            "access_paths": [],
            "execution_enabled": False,
            "note": "Register or extend a CapabilitySpec before this request can be planned.",
        }

    spec = CAPABILITY_REGISTRY[match["capability_id"]]
    node_ids = {node.id for node in spec.nodes}
    if len(node_ids) != len(spec.nodes):
        raise ValueError("Capability workflow contains duplicate node IDs.")
    for node in spec.nodes:
        if node.function_id not in FUNCTION_REGISTRY:
            raise ValueError("Capability references an unregistered function.")
        if not set(node.depends_on) <= node_ids:
            raise ValueError("Capability references an unknown dependency.")

    pending = list(spec.nodes)
    ordered = []
    while pending:
        ready = [node for node in pending if all(dep in {item.id for item in ordered}
                                                  for dep in node.depends_on)]
        if not ready:
            raise ValueError("Capability workflow contains a dependency cycle.")
        for node in ready:
            ordered.append(node)
            pending.remove(node)

    missing_bindings = set(result.get("missing_context", []))
    statuses = {}
    compiled = []
    for node in ordered:
        function = FUNCTION_REGISTRY[node.function_id]
        missing_for_node = sorted(missing_bindings & set(function.required_inputs))
        if missing_for_node:
            status = "NEEDS_INPUT"
        elif any(statuses[dependency] != "PLANNED" for dependency in node.depends_on):
            status = "BLOCKED"
        else:
            status = "PLANNED"
        statuses[node.id] = status
        compiled.append({
            "id": node.id,
            "function_id": function.id,
            "function_version": function.version,
            "function_class": function.function_class,
            "execution_class": function.execution_class,
            "access_path": function.access_path,
            "depends_on": list(node.depends_on),
            "required_inputs": list(function.required_inputs),
            "produces": list(function.produces),
            "pii_policy": function.pii_policy,
            "side_effect_class": function.side_effect_class,
            "status": status,
            "missing_inputs": missing_for_node,
        })
    return {
        "mode": "preview_only",
        "match": match,
        "capability_id": spec.id,
        "capability_version": spec.version,
        "workflow_id": spec.workflow_id,
        "outcome": spec.outcome,
        "nodes": compiled,
        "access_paths": list(dict.fromkeys(node["access_path"] for node in compiled)),
        "execution_enabled": False,
        "note": "Registered functions and access paths are contracts only; no node was invoked.",
    }


def capability_catalog() -> list[dict]:
    return [{
        **{key: value for key, value in asdict(spec).items() if key != "nodes"},
        "function_ids": [node.function_id for node in spec.nodes],
    } for spec in CAPABILITY_SPECS]


def function_catalog() -> list[dict]:
    return [asdict(spec) for spec in FUNCTION_SPECS]
