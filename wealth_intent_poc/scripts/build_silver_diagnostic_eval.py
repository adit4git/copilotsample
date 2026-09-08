"""Build a grouped diagnostic evaluation view from usable semantic silver labels."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

USABLE = {"HIGH_CONFIDENCE_SILVER", "MEDIUM_CONFIDENCE_SILVER"}
SPLIT_SALT = "semantic-silver-diagnostic-eval-v1"


def stable_rank(group):
    return int(hashlib.sha256(f"{SPLIT_SALT}:{group}".encode()).hexdigest()[:12], 16)


def assign_splits(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["split_group"]].append(row)
    totals = Counter(intent for row in rows for intent in row["semantic_labels"]["intents"])
    targets = {intent: max(1, round(count * .25)) if count >= 2 else 0
               for intent, count in totals.items()}
    selected, heldout_counts = set(), Counter()
    target_records = round(len(rows) * .25)
    while True:
        choices = []
        for group, items in groups.items():
            if group in selected: continue
            counts = Counter(intent for row in items for intent in row["semantic_labels"]["intents"])
            gain = sum(min(counts[intent], max(0, target-heldout_counts[intent]))
                       for intent, target in targets.items())
            if gain:
                choices.append((gain / len(items), gain, -len(items), -stable_rank(group), group, counts))
        if not choices: break
        *_, group, counts = max(choices)
        selected.add(group); heldout_counts.update(counts)
        if all(heldout_counts[intent] >= target for intent, target in targets.items()): break
    for group in sorted((g for g in groups if g not in selected), key=stable_rank):
        if sum(len(groups[g]) for g in selected) >= target_records: break
        selected.add(group)
    return {group: ("heldout_diagnostic" if group in selected else "development_diagnostic")
            for group in groups}, targets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--silver", default="data/semantic_silver_labels_v1.jsonl")
    parser.add_argument("--output", default="data/semantic_silver_diagnostic_eval_v1.jsonl")
    args = parser.parse_args()
    rows = [json.loads(line) for line in Path(args.silver).read_text().splitlines() if line.strip()]
    usable = [row for row in rows if row["quality_tier"] in USABLE]
    group_splits, heldout_targets = assign_splits(usable)
    selected = []
    for row in usable:
        split = group_splits[row["split_group"]]
        item = dict(row)
        item["schema_version"] = "semantic_silver_diagnostic_eval.1"
        item["diagnostic_split"] = split
        selected.append(item)
    if any(row["training_eligible"] or row["independent_review"] for row in selected):
        raise SystemExit("Silver diagnostics cannot be marked reviewed or training eligible.")
    leakage = defaultdict(set)
    for row in selected:
        leakage[row["split_group"]].add(row["diagnostic_split"])
    if any(len(splits) != 1 for splits in leakage.values()):
        raise SystemExit("Split-group leakage detected.")
    out = Path(args.output)
    out.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in selected))
    by_split = Counter(row["diagnostic_split"] for row in selected)
    by_tier = Counter(row["quality_tier"] for row in selected)
    intent_support = {
        split: dict(sorted(Counter(intent for row in selected if row["diagnostic_split"] == split
                                  for intent in row["semantic_labels"]["intents"]).items()))
        for split in sorted(by_split)
    }
    manifest = {
        "schema_version": "semantic_silver_diagnostic_eval_manifest.1",
        "records": len(selected), "groups": len(leakage),
        "split_method": "deterministic_group_stratified_greedy_75_25",
        "split_salt": SPLIT_SALT,
        "split_counts": dict(sorted(by_split.items())),
        "quality_tiers": dict(sorted(by_tier.items())),
        "intent_support_by_split": intent_support,
        "heldout_intent_targets": dict(sorted(heldout_targets.items())),
        "group_leakage": 0, "training_eligible": 0, "independent_review": False,
        "dataset_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "metric_status": "diagnostic_silver_agreement_only_not_human_accuracy",
    }
    manifest_path = out.with_name("semantic_silver_diagnostic_eval_manifest_v1.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
