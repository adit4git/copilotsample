"""Preview-only orchestration: no data retrieval, transactions or notifications."""
from .registry import REGISTRY, DEPENDENCIES


def plan_workflow(result: dict) -> dict:
    selected = result["intents"]
    pending, ordered = list(selected), []
    while pending:
        ready = [i for i in pending if all(d in ordered or d not in selected for d in DEPENDENCIES.get(i, ()))]
        if not ready:
            raise ValueError("Intent registry contains a dependency cycle.")
        for i in ready:
            ordered.append(i)
            pending.remove(i)
    tasks = []
    ids = {i: f"t{j+1}" for j, i in enumerate(ordered)}
    for i in ordered:
        spec = REGISTRY[i]
        tasks.append({"id": ids[i], "intent": i, "service": spec.service, "operation": spec.operation,
                      "depends_on": [ids[d] for d in DEPENDENCIES.get(i, ()) if d in ids],
                      "required_inputs": list(spec.required_inputs), "status": "not_executed"})
    gates = ["Resolve entities inside the trusted application.", "Check advisor entitlements before any data access.",
             "Validate source dates, required inputs, and applicable policy."]
    if result["requested_effect"] != "read_only":
        gates.append("Obtain action-specific authorization in a real execution system.")
    return {"mode": "preview_only", "tasks": tasks,
            "missing_inputs": sorted({x for t in tasks for x in t["required_inputs"]}),
            "gates": gates, "execution_enabled": False,
            "note": "All inputs are unverified: this POC is not connected to client or market systems."}
