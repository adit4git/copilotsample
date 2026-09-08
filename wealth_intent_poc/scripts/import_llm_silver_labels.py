"""Create a quality-gated semantic-only dataset from adjudicated LLM labels."""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wealth_intent.privacy import mask
from wealth_intent.semantic_contract import validate_semantic

SEMANTIC_FIELDS = (
    "intents", "scope", "goal", "output", "audience", "metric",
    "subject_selection", "requested_effect",
)
ROUTING_FIELDS_EXCLUDED = ("capability_id", "decision", "missing_context")


def load_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def semantic_only(labels):
    return {field: labels.get(field) for field in SEMANTIC_FIELDS}


def contract_issues(labels):
    required = {key: labels.get(key) for key in
                ("intents", "scope", "subject_selection", "requested_effect", "metric")}
    return validate_semantic(required)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adjudicated", required=True)
    parser.add_argument("--corpus", default="data/semantic_annotation_corpus.jsonl")
    parser.add_argument("--output", default="data/semantic_silver_labels_v1.jsonl")
    args = parser.parse_args()

    source = {row["case_id"]: row for row in load_jsonl(args.corpus)}
    adjudicated_rows = load_jsonl(args.adjudicated)
    adjudicated = {row["case_id"]: row for row in adjudicated_rows}
    if len(adjudicated) != len(adjudicated_rows):
        raise SystemExit("Duplicate case_id in adjudicated labels.")
    if set(adjudicated) != set(source):
        raise SystemExit("Adjudicated and source case IDs do not match exactly.")

    output = []
    for case_id, case in source.items():
        item = adjudicated[case_id]
        status = item.get("silver_label_status")
        labels = item.get("labels") or {}
        issues = [] if status == "UNRESOLVED" else contract_issues(labels)
        if status == "UNRESOLVED":
            tier, selected = "EXCLUDED_UNRESOLVED", None
        elif issues:
            tier, selected = "DIAGNOSTIC_ONLY_CONTRACT_INVALID", semantic_only(labels)
        elif status == "UNANIMOUS":
            tier, selected = "HIGH_CONFIDENCE_SILVER", semantic_only(labels)
        elif status == "MAJORITY_ADJUDICATED":
            tier, selected = "MEDIUM_CONFIDENCE_SILVER", semantic_only(labels)
        else:
            tier, selected = "DIAGNOSTIC_ONLY_NO_COMPLETE_MAJORITY", semantic_only(labels)

        source_annotations = {}
        for name, annotation in item.get("source_annotations", {}).items():
            source_annotations[name] = {
                "model_id": annotation.get("model_id"),
                "semantic_labels": semantic_only(annotation.get("labels", {})),
            }
        output.append({
            "schema_version": "semantic_silver.1",
            "case_id": case_id,
            "split_group": case["split_group"],
            "masked_request": mask(case["query"]).masked_text,
            "semantic_labels": selected,
            "quality_tier": tier,
            "silver_label_status": status,
            "selected_source": item.get("selected_source"),
            "disagreeing_semantic_fields": sorted(
                set(item.get("disagreeing_fields", [])) & set(SEMANTIC_FIELDS)),
            "semantic_contract_issues": issues,
            "source_annotations": source_annotations,
            "label_source": "llm_silver",
            "independent_review": False,
            "training_eligible": False,
            "excluded_llm_fields": list(ROUTING_FIELDS_EXCLUDED),
        })

    out = Path(args.output)
    out.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in output))
    counts = Counter(row["quality_tier"] for row in output)
    manifest = {
        "schema_version": "semantic_silver_manifest.1",
        "records": len(output),
        "quality_tiers": dict(sorted(counts.items())),
        "usable_semantic_silver_records": counts["HIGH_CONFIDENCE_SILVER"] + counts["MEDIUM_CONFIDENCE_SILVER"],
        "training_eligible": 0,
        "independent_review": False,
        "semantic_fields_retained": list(SEMANTIC_FIELDS),
        "llm_routing_fields_excluded": list(ROUTING_FIELDS_EXCLUDED),
        "dataset_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "note": "Capability, clarification, decision, and DAG must be derived by deterministic runtime logic.",
    }
    manifest_path = out.with_name("semantic_silver_manifest_v1.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
