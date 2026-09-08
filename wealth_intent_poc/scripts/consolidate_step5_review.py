"""Validate and consolidate the focused cross-model semantic review.

The reviewer was intentionally restricted to semantic labels. This importer
therefore never accepts capability IDs, context requirements, decisions,
functions or DAGs from the review output.
"""
import argparse
import hashlib
import io
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wealth_intent import __version__ as POC_VERSION
from wealth_intent.runtime import route_request
from wealth_intent.semantic_contract import validate_semantic

ROOT = Path(__file__).resolve().parents[1]
FIELDS = (
    "intents", "scope", "goal", "output", "audience", "metric",
    "subject_selection", "requested_effect",
)


def load_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def semantic_issues(labels):
    if labels is None:
        return []
    return validate_semantic({key: labels.get(key) for key in
                              ("intents", "scope", "subject_selection",
                               "requested_effect", "metric")})


def frame(value):
    return {field: value.get(field) for field in FIELDS}


def normalized(value, field):
    return sorted(value or []) if field == "intents" else value


def differences(left, right):
    if left is None or right is None:
        return list(FIELDS) if left != right else []
    return [field for field in FIELDS
            if normalized(left.get(field), field) != normalized(right.get(field), field)]


def load_review_contract(master_path):
    cases = {}
    schemas = []
    expected_by_chunk = {}
    with zipfile.ZipFile(master_path) as master:
        children = sorted(name for name in master.namelist() if name.endswith(".zip"))
        for child_name in children:
            match = re.search(r"chunk_(\d+)\.zip$", child_name)
            if not match:
                raise SystemExit(f"Unexpected child package name: {child_name}")
            chunk = int(match.group(1))
            with zipfile.ZipFile(io.BytesIO(master.read(child_name))) as child:
                rows = [json.loads(line) for line in
                        child.read("review_cases.jsonl").decode().splitlines() if line.strip()]
                schema = json.loads(child.read("review_output_schema.json"))
            schemas.append(schema)
            expected_by_chunk[chunk] = {row["case_id"] for row in rows}
            for row in rows:
                if row["case_id"] in cases:
                    raise SystemExit(f"Duplicate issued case: {row['case_id']}")
                cases[row["case_id"]] = {**row, "chunk": chunk}
    if any(schema != schemas[0] for schema in schemas[1:]):
        raise SystemExit("Review chunks contain different output schemas.")
    return cases, expected_by_chunk, schemas[0]


def validate_results(paths, cases, expected_by_chunk, schema):
    validator = Draft202012Validator(schema)
    rows = {}
    seen_by_chunk = {}
    for path in sorted(map(Path, paths)):
        match = re.search(r"chunk_(\d+)_results\.jsonl$", path.name)
        if not match:
            raise SystemExit(f"Unexpected result filename: {path.name}")
        chunk = int(match.group(1))
        if chunk in seen_by_chunk:
            raise SystemExit(f"More than one result file for chunk {chunk:02d}.")
        parsed = load_jsonl(path)
        seen_by_chunk[chunk] = {row.get("case_id") for row in parsed}
        for line_number, row in enumerate(parsed, 1):
            errors = sorted(validator.iter_errors(row), key=lambda error: list(error.path))
            if errors:
                detail = "; ".join(error.message for error in errors)
                raise SystemExit(f"{path.name}:{line_number}: schema error: {detail}")
            case_id = row["case_id"]
            if case_id in rows:
                raise SystemExit(f"Duplicate returned case: {case_id}")
            issued = cases.get(case_id)
            if issued is None or issued["chunk"] != chunk:
                raise SystemExit(f"{case_id} was not issued in chunk {chunk:02d}.")
            options = {item["option_id"]: item["semantic_labels"]
                       for item in issued["candidate_options"]}
            resolution = row["resolution"]
            if resolution == "SELECT_OPTION":
                selected = row["selected_option_id"]
                if selected not in options:
                    raise SystemExit(f"{case_id}: selected option is not an issued candidate.")
                if row["semantic_labels"] != options[selected]:
                    raise SystemExit(f"{case_id}: selected labels differ from the candidate.")
            elif resolution == "REVISED_FRAME":
                if row["selected_option_id"] is not None or row["semantic_labels"] is None:
                    raise SystemExit(f"{case_id}: invalid REVISED_FRAME payload.")
            elif row["selected_option_id"] is not None or row["semantic_labels"] is not None:
                raise SystemExit(f"{case_id}: unresolved/taxonomy results cannot assert labels.")
            rows[case_id] = row
    if set(seen_by_chunk) != set(expected_by_chunk):
        raise SystemExit("The returned chunk numbers do not match the issued packages.")
    for chunk, expected in expected_by_chunk.items():
        if seen_by_chunk[chunk] != expected:
            missing = sorted(expected - seen_by_chunk[chunk])
            extra = sorted(seen_by_chunk[chunk] - expected)
            raise SystemExit(f"Chunk {chunk:02d} coverage mismatch; missing={missing}, extra={extra}")
    if set(rows) != set(cases):
        raise SystemExit("Returned case IDs do not cover the review package exactly.")
    return rows


def rate(count, total):
    return round(count / total, 4) if total else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", nargs="+", required=True)
    parser.add_argument("--master-package", default=str(ROOT.parent / "step5_disagreement_review_packages.zip"))
    parser.add_argument("--provenance", default="data/DO_NOT_UPLOAD_disagreement_review_provenance_map_v1.json")
    parser.add_argument("--silver", default="data/semantic_silver_labels_v1.jsonl")
    parser.add_argument("--corpus", default="data/semantic_annotation_corpus.jsonl")
    parser.add_argument("--output", default="data/semantic_reviewed_silver_labels_v2.jsonl")
    args = parser.parse_args()

    issued, expected_by_chunk, schema = load_review_contract(Path(args.master_package))
    reviews = validate_results(args.results, issued, expected_by_chunk, schema)
    provenance = json.loads(Path(args.provenance).read_text())["cases"]
    baseline_rows = load_jsonl(args.silver)
    baseline = {row["case_id"]: row for row in baseline_rows}
    corpus_rows = load_jsonl(args.corpus)
    corpus = {row["case_id"]: row for row in corpus_rows}
    if set(baseline) != set(corpus):
        raise SystemExit("Baseline silver and corpus IDs do not match.")
    if set(reviews) != set(provenance):
        raise SystemExit("Review results and hidden provenance IDs do not match.")

    adjudicated = []
    resolution_counts = Counter()
    confidence_counts = Counter()
    acceptance_counts = Counter()
    selected_source_counts = Counter()
    baseline_field_changes = Counter()
    baseline_exact = 0
    pre_poc_field_agreement = Counter()
    post_poc_field_agreement = Counter()
    pre_poc_exact = 0
    post_poc_exact = 0

    for case_id in sorted(reviews):
        review = reviews[case_id]
        resolution_counts[review["resolution"]] += 1
        confidence_counts[review["confidence"]] += 1
        labels = review["semantic_labels"]
        issues = semantic_issues(labels)
        if review["resolution"] in {"SELECT_OPTION", "REVISED_FRAME"} and not issues:
            acceptance = "ACCEPTED_SEMANTIC_SILVER"
        elif issues:
            acceptance = "PENDING_CONTRACT_REVIEW"
        elif review["resolution"] == "TAXONOMY_ISSUE":
            acceptance = "PENDING_TAXONOMY_REVIEW"
        else:
            acceptance = "PENDING_UNRESOLVED"
        acceptance_counts[acceptance] += 1

        sources = []
        reported_routes = []
        if review["resolution"] == "SELECT_OPTION":
            selected = provenance[case_id][review["selected_option_id"]]
            sources = selected["sources"]
            reported_routes = selected["reported_routes"]
            selected_source_counts[" + ".join(sources)] += 1

        old = baseline[case_id]["semantic_labels"]
        old_differences = differences(old, labels)
        if acceptance == "ACCEPTED_SEMANTIC_SILVER":
            if not old_differences:
                baseline_exact += 1
            else:
                baseline_field_changes.update(old_differences)

        poc_option_id = next(option_id for option_id, value in provenance[case_id].items()
                             if "POC_0.6.1" in value["sources"])
        old_poc = next(option["semantic_labels"] for option in issued[case_id]["candidate_options"]
                       if option["option_id"] == poc_option_id)
        new_poc = frame(route_request(corpus[case_id]["query"]))
        if acceptance == "ACCEPTED_SEMANTIC_SILVER":
            before_diff = differences(old_poc, labels)
            after_diff = differences(new_poc, labels)
            if not before_diff:
                pre_poc_exact += 1
            if not after_diff:
                post_poc_exact += 1
            for field in FIELDS:
                if field not in before_diff:
                    pre_poc_field_agreement[field] += 1
                if field not in after_diff:
                    post_poc_field_agreement[field] += 1

        adjudicated.append({
            "schema_version": "step5_semantic_review.1",
            "case_id": case_id,
            "chunk": issued[case_id]["chunk"],
            "masked_request": issued[case_id]["masked_request"],
            "review_reasons": issued[case_id]["review_reasons"],
            "resolution": review["resolution"],
            "confidence": review["confidence"],
            "semantic_labels": labels,
            "semantic_contract_issues": issues,
            "acceptance_status": acceptance,
            "selected_candidate_sources": sources,
            "selected_candidate_reported_routes_not_imported": reported_routes,
            "ambiguous_fields": review["ambiguous_fields"],
            "taxonomy_issue": review["taxonomy_issue"],
            "short_rationale": review["short_rationale"],
            "baseline_quality_tier": baseline[case_id]["quality_tier"],
            "differs_from_baseline_fields": old_differences,
            "human_reviewed": False,
            "training_eligible": False,
            "excluded_review_fields": ["capability_id", "decision", "context_requirements",
                                       "clarification_required", "functions", "dag"],
        })

    adjudicated_by_id = {row["case_id"]: row for row in adjudicated}
    consolidated = []
    for base in baseline_rows:
        case_id = base["case_id"]
        review = adjudicated_by_id.get(case_id)
        if review is None:
            selected_labels = base["semantic_labels"]
            quality = base["quality_tier"]
            review_status = "NOT_SELECTED_FOR_STEP5"
        elif review["acceptance_status"] == "ACCEPTED_SEMANTIC_SILVER":
            selected_labels = review["semantic_labels"]
            quality = ("CROSS_MODEL_REVIEW_HIGH_CONFIDENCE" if review["confidence"] == "high"
                       else "CROSS_MODEL_REVIEW_MEDIUM_CONFIDENCE")
            review_status = review["acceptance_status"]
        else:
            selected_labels = None
            quality = review["acceptance_status"]
            review_status = review["acceptance_status"]
        consolidated.append({
            **base,
            "schema_version": "semantic_reviewed_silver.2",
            "semantic_labels": selected_labels,
            "quality_tier": quality,
            "label_source": "cross_model_llm_silver" if review else base["label_source"],
            "step5_review_status": review_status,
            "step5_review": None if review is None else {
                key: review[key] for key in (
                    "resolution", "confidence", "acceptance_status",
                    "semantic_contract_issues", "ambiguous_fields", "taxonomy_issue",
                    "short_rationale", "selected_candidate_sources",
                    "differs_from_baseline_fields",
                )
            },
            "independent_llm_review": review is not None,
            "independent_review": False,
            "human_reviewed": False,
            "training_eligible": False,
        })

    adjudicated_path = ROOT / "data/step5_semantic_review_adjudicated_v1.jsonl"
    adjudicated_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in adjudicated))
    output_path = Path(args.output)
    output_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in consolidated))

    accepted = acceptance_counts["ACCEPTED_SEMANTIC_SILVER"]
    usable_tiers = {"HIGH_CONFIDENCE_SILVER", "MEDIUM_CONFIDENCE_SILVER",
                    "CROSS_MODEL_REVIEW_HIGH_CONFIDENCE", "CROSS_MODEL_REVIEW_MEDIUM_CONFIDENCE"}
    quality_counts = Counter(row["quality_tier"] for row in consolidated)
    usable = sum(row["quality_tier"] in usable_tiers for row in consolidated)
    accepted_rows = [row for row in adjudicated if row["acceptance_status"] == "ACCEPTED_SEMANTIC_SILVER"]
    accepted_baseline_exact = sum(not row["differs_from_baseline_fields"] for row in accepted_rows)
    report = {
        "schema_version": "step5_review_analysis.1",
        "review_cases_issued": len(issued),
        "review_cases_returned": len(reviews),
        "coverage_complete": set(issued) == set(reviews),
        "resolution_counts": dict(sorted(resolution_counts.items())),
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "acceptance_counts": dict(sorted(acceptance_counts.items())),
        "selected_candidate_source_combinations": dict(selected_source_counts.most_common()),
        "accepted_choice_includes_issued_poc": sum(
            row["acceptance_status"] == "ACCEPTED_SEMANTIC_SILVER"
            and "POC_0.6.1" in row["selected_candidate_sources"] for row in adjudicated),
        "accepted_baseline_exact": accepted_baseline_exact,
        "accepted_baseline_exact_rate": rate(accepted_baseline_exact, accepted),
        "accepted_baseline_changed": accepted - accepted_baseline_exact,
        "baseline_changed_field_counts": dict(baseline_field_changes.most_common()),
        "poc_comparison": {
            "accepted_cases": accepted,
            "issued_poc_version": "0.6.1",
            "current_poc_version": POC_VERSION,
            "pre_change_exact": pre_poc_exact,
            "pre_change_exact_rate": rate(pre_poc_exact, accepted),
            "current_exact": post_poc_exact,
            "current_exact_rate": rate(post_poc_exact, accepted),
            "pre_change_field_agreement": {field: {"count": pre_poc_field_agreement[field],
                                                    "rate": rate(pre_poc_field_agreement[field], accepted)}
                                           for field in FIELDS},
            "current_field_agreement": {field: {"count": post_poc_field_agreement[field],
                                                 "rate": rate(post_poc_field_agreement[field], accepted)}
                                        for field in FIELDS},
            "interpretation": "Agreement with targeted LLM silver labels, not accuracy or financial validation.",
        },
        "consolidated_records": len(consolidated),
        "consolidated_usable_semantic_silver_records": usable,
        "consolidated_quality_tiers": dict(sorted(quality_counts.items())),
        "human_reviewed_records": 0,
        "training_eligible_records": 0,
        "reviewer_routing_fields_imported": False,
        "adjudicated_sha256": hashlib.sha256(adjudicated_path.read_bytes()).hexdigest(),
        "consolidated_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
    }
    report_path = ROOT / "data/step5_review_analysis_v1.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    manifest = {
        "schema_version": "semantic_reviewed_silver_manifest.2",
        "records": len(consolidated),
        "quality_tiers": dict(sorted(quality_counts.items())),
        "usable_semantic_silver_records": usable,
        "step5_cases": len(reviews),
        "accepted_step5_cases": accepted,
        "pending_step5_cases": len(reviews) - accepted,
        "independent_llm_reviewed_records": len(reviews),
        "human_reviewed_records": 0,
        "training_eligible_records": 0,
        "llm_routing_fields_excluded": True,
        "dataset_sha256": report["consolidated_sha256"],
        "assurance": "CROSS_MODEL_LLM_SILVER_ONLY_NOT_HUMAN_GROUND_TRUTH",
    }
    output_path.with_name("semantic_reviewed_silver_manifest_v2.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
