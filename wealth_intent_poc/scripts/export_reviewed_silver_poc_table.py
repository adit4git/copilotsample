"""Run the usable reviewed-silver corpus through the current local POC.

Only masked requests and typed outputs are exported. Original query text is
used locally for faithful parsing and is never written to the result file.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wealth_intent import __version__ as POC_VERSION
from wealth_intent.runtime import route_request

USABLE_TIERS = {
    "HIGH_CONFIDENCE_SILVER",
    "MEDIUM_CONFIDENCE_SILVER",
    "CROSS_MODEL_REVIEW_HIGH_CONFIDENCE",
    "CROSS_MODEL_REVIEW_MEDIUM_CONFIDENCE",
}


def load_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", default="data/semantic_reviewed_silver_labels_v2.jsonl")
    parser.add_argument("--corpus", default="data/semantic_annotation_corpus.jsonl")
    parser.add_argument("--output", required=True)
    parser.add_argument("--monitor-mode", choices=("unspecified", "one_time", "recurring"),
                        default="unspecified")
    args = parser.parse_args()

    labels = [row for row in load_jsonl(args.labels) if row["quality_tier"] in USABLE_TIERS]
    corpus = {row["case_id"]: row for row in load_jsonl(args.corpus)}
    if len(labels) != 206 or any(row["case_id"] not in corpus for row in labels):
        raise SystemExit("Expected the complete 206-record usable reviewed-silver set.")

    rows = []
    intent_frequency = Counter()
    decision_frequency = Counter()
    capability_frequency = Counter()
    exact_matches = 0
    for order, label in enumerate(labels, 1):
        result = route_request(corpus[label["case_id"]]["query"], monitor_mode=args.monitor_mode)
        classified = sorted(result["intents"])
        reviewed = sorted(label["semantic_labels"]["intents"])
        classified_set, reviewed_set = set(classified), set(reviewed)
        exact = classified_set == reviewed_set
        exact_matches += exact
        intent_frequency.update(classified)
        decision_frequency[result["decision"]] += 1
        capability_frequency[result["capability_id"] or "NO_MATCH"] += 1
        rows.append({
            "row": order,
            "case_id": label["case_id"],
            "masked_query": label["masked_request"],
            "poc_classified_intents": "; ".join(classified) or "NO_INTENT",
            "poc_intent_count": len(classified),
            "reviewed_silver_intents": "; ".join(reviewed),
            "intent_set_match": exact,
            "poc_extra_intents": "; ".join(sorted(classified_set - reviewed_set)),
            "poc_missing_intents": "; ".join(sorted(reviewed_set - classified_set)),
            "scope": result["scope"],
            "subject_selection": result["subject_selection"],
            "output": result["output"],
            "requested_effect": result["requested_effect"],
            "capability_id": result["capability_id"] or "NO_MATCH",
            "decision": result["decision"],
            "quality_tier": label["quality_tier"],
        })

    payload = {
        "schema_version": "reviewed_silver_poc_classification_table.1",
        "poc_version": POC_VERSION,
        "run_configuration": {
            "monitor_mode": args.monitor_mode,
            "semantic_model": "disabled",
            "llm_requests": 0,
            "input_text": "original query processed locally; masked query exported",
        },
        "summary": {
            "records": len(rows),
            "exact_intent_set_matches": exact_matches,
            "exact_intent_set_match_rate": exact_matches / len(rows),
            "intent_frequency": dict(intent_frequency.most_common()),
            "decision_frequency": dict(decision_frequency.most_common()),
            "capability_frequency": dict(capability_frequency.most_common()),
        },
        "rows": rows,
        "assurance": "Agreement with reviewed LLM silver labels is diagnostic, not accuracy or human validation.",
    }
    Path(args.output).write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()
