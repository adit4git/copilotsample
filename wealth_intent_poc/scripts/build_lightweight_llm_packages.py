"""Create two sets of small, self-contained LLM semantic-labeling packages."""
import csv
import hashlib
import json
import random
import shutil
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wealth_intent.privacy import mask
from wealth_intent.registry import SPECS
from wealth_intent.semantic import CONTEXT_TYPES

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "semantic_annotation_corpus.jsonl"
OUT = ROOT.parent / "llm_lightweight_packages_v2"
TARGET_SIZE = 20
PASS_SEEDS = {1: 7103, 2: 9209}

SCOPES = ["general", "account_or_client", "household", "subject_set", "advisor_book",
          "portfolio", "security_or_instrument", "product_or_strategy", "practice"]
SELECTIONS = ["unspecified", "single_subject", "explicit_subject_references",
              "prioritized_clients", "criteria_filtered_book", "entire_book"]
EFFECTS = ["read_only", "draft_only", "ambiguous_monitor", "monitor_specification",
           "operational_action"]
AUDIENCES = ["advisor", "client"]
METRICS = ["credit_spread", "estimate_revisions", "credit_rating", "short_interest",
           "earnings", "duration", "sector_exposure"]
OUTPUTS = ["cited_answer", "cited_explanation", "email_draft", "talking_points",
           "voicemail_script", "voicemail_bullets", "analysis_table", "ranked_table",
           "comparison_table", "solution_shortlist", "guidance_or_diagnostic_checklist",
           "decision_summary", "meeting_book", "review_comparison",
           "tax_aware_transition_proposal", "holdings_signal_analysis"]
GOALS = ["interpret_market_signal", "explain_credit_spread_change",
         "screen_market_signals_for_client_holdings",
         "design_tax_aware_concentrated_stock_transition", "draft_client_market_update",
         "transform_supplied_content", "compare_rebalance_scenario", "review_changes",
         "fulfill_registered_tasks"]
PARAMETERS = ["analysis_period", "top_n", "materiality_percent"]


def json_write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def jsonl_write(path, values):
    path.write_text("".join(json.dumps(v, sort_keys=True) + "\n" for v in values))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact_vocabulary():
    return {
        "version": "wealth-semantic-labels.2",
        "intents": {s.id: f"{s.title}: {s.operation}" for s in SPECS},
        "scope": {
            "general": "no specific subject", "account_or_client": "one client/account",
            "household": "related household accounts", "subject_set": "selected/named/filtered client-account set",
            "advisor_book": "entire advisor book", "portfolio": "portfolio as subject",
            "security_or_instrument": "issuer/security/issue/note", "product_or_strategy": "product/program/strategy",
            "practice": "advisor-team business analytics"},
        "subject_selection": {
            "unspecified": "not determinable", "single_subject": "one subject",
            "explicit_subject_references": "named/enumerated/selected set",
            "prioritized_clients": "pre-existing prioritized-client set",
            "criteria_filtered_book": "query-defined selection criteria", "entire_book": "complete book"},
        "requested_effect": {
            "read_only": "research/analysis/guidance", "draft_only": "create but do not send",
            "ambiguous_monitor": "one-time versus recurring unresolved",
            "monitor_specification": "define recurring monitoring", "operational_action": "perform external action"},
        "audience": {"advisor": "advisor-use output", "client": "explicit client-facing communication"},
        "metrics": METRICS, "outputs": OUTPUTS, "goals": GOALS,
        "semantic_parameters": {
            "analysis_period": "normalized explicit period or null",
            "top_n": "explicit integer or null when 'top' lacks a count",
            "materiality_percent": "explicit number or null when 'major/material' lacks a threshold"},
        "null_policy": "Use null and list the field in uncertain_fields when the request does not support one value.",
    }


def output_schema():
    props = {
        "case_id": {"type": "string"},
        "intents": {"type": "array", "items": {"enum": [s.id for s in SPECS]}, "uniqueItems": True},
        "scope": {"enum": SCOPES + [None]}, "goal": {"enum": GOALS + [None]},
        "output": {"enum": OUTPUTS + [None]}, "audience": {"enum": AUDIENCES + [None]},
        "metric": {"enum": METRICS + [None]}, "subject_selection": {"enum": SELECTIONS + [None]},
        "requested_effect": {"enum": EFFECTS + [None]},
        "semantic_parameters": {
            "type": "object", "additionalProperties": False,
            "properties": {"analysis_period": {"type": ["string", "null"]},
                           "top_n": {"type": ["integer", "null"], "minimum": 1},
                           "materiality_percent": {"type": ["number", "null"], "minimum": 0, "maximum": 100}},
        },
        "uncertain_fields": {"type": "array",
                             "items": {"enum": ["intents", "scope", "goal", "output", "audience",
                                                "metric", "subject_selection", "requested_effect", *PARAMETERS]},
                             "uniqueItems": True},
    }
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object",
            "additionalProperties": False, "required": list(props), "properties": props}


def make_chunks(records, seed):
    grouped = defaultdict(list)
    for r in records:
        grouped[r["split_group"]].append(r)
    keys = sorted(grouped)
    random.Random(seed).shuffle(keys)
    chunks, current = [], []
    for key in keys:
        group = list(grouped[key])
        random.Random(f"{seed}:{key}").shuffle(group)
        if current and len(current) + len(group) > TARGET_SIZE:
            chunks.append(current); current = []
        current.extend(group)
    if current:
        chunks.append(current)
    return chunks


def task_text(pass_number, chunk_number, count):
    role = ("Semantic analyst: capture every literal requested task without adding customary work."
            if pass_number == 1 else
            "Conservative reviewer: avoid false confident labels and use null for material ambiguity.")
    name = f"labels_pass_{pass_number}_chunk_{chunk_number:02d}.jsonl"
    return f"""# Task

Role: **{role}**

Label the {count} masked queries in `queries.jsonl` using `compact_vocabulary.json` and `concise_output_schema.json`.

Rules:

1. Work from the request only; do not invent context or customary downstream tasks.
2. Ignore negated work. Distinguish draft from send and guidance from action.
3. Return one compact JSON object per line, in input order, with no prose.
4. Return the result as `{name}`. Do not paste the full output into chat.
5. Every input `case_id` must appear exactly once. Do not include any other case.
6. Do not select capabilities, functions, missing context, decisions, or DAG nodes.
7. Use null plus `uncertain_fields` instead of guessing.

If you cannot create a file, place only the JSONL in one code block. Do not add explanations.
"""


def main():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    raw = [json.loads(line) for line in SOURCE.read_text().splitlines() if line.strip()]
    records = []
    for item in raw:
        result = mask(item["query"])
        records.append({"case_id": item["case_id"], "split_group": item["split_group"],
                        "masked_request": result.masked_text})
    vocabulary, schema = compact_vocabulary(), output_schema()
    top_manifest = {"version": "llm-lightweight-packages.2", "records": len(records),
                    "split_groups": len({r['split_group'] for r in records}), "passes": {}}
    for pass_number, seed in PASS_SEEDS.items():
        pass_dir = OUT / f"pass_{pass_number}"
        pass_dir.mkdir()
        chunks = make_chunks(records, seed)
        index_rows = []
        for number, rows in enumerate(chunks, 1):
            work = OUT / "_work"
            if work.exists(): shutil.rmtree(work)
            work.mkdir()
            jsonl_write(work / "queries.jsonl", [
                {"case_id": row["case_id"], "masked_request": row["masked_request"]} for row in rows])
            json_write(work / "compact_vocabulary.json", vocabulary)
            json_write(work / "concise_output_schema.json", schema)
            (work / "TASK.md").write_text(task_text(pass_number, number, len(rows)))
            child = pass_dir / f"pass_{pass_number}_chunk_{number:02d}.zip"
            with zipfile.ZipFile(child, "w", zipfile.ZIP_DEFLATED) as z:
                for path in sorted(work.iterdir()): z.write(path, path.name)
            index_rows.append({"chunk": number, "package": child.name, "records": len(rows),
                               "first_case": rows[0]["case_id"], "last_case": rows[-1]["case_id"],
                               "sha256": sha(child)})
        with (pass_dir / "PACKAGE_INDEX.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=index_rows[0]); writer.writeheader(); writer.writerows(index_rows)
        (pass_dir / "PASS_INSTRUCTIONS.txt").write_text(
            f"Give these {len(chunks)} packages only to LLM {pass_number}, one numbered ZIP at a time. "
            f"Collect labels_pass_{pass_number}_chunk_NN.jsonl before continuing.\n")
        master = OUT.parent / f"llm_lightweight_pass_{pass_number}_packages.zip"
        with zipfile.ZipFile(master, "w", zipfile.ZIP_DEFLATED) as z:
            for path in sorted(pass_dir.iterdir()): z.write(path, path.name)
        top_manifest["passes"][str(pass_number)] = {"chunks": len(chunks),
                                                     "maximum_records_per_chunk": max(x["records"] for x in index_rows),
                                                     "master_file": master.name, "sha256": sha(master)}
    shutil.rmtree(OUT / "_work", ignore_errors=True)
    json_write(OUT / "PACKAGE_MANIFEST.json", top_manifest)
    print(json.dumps(top_manifest, indent=2))


if __name__ == "__main__": main()
