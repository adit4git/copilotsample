"""Build compact anonymized packages for focused semantic disagreement review."""
import argparse
import csv
import hashlib
import io
import json
import random
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wealth_intent.privacy import mask
from wealth_intent.registry import SPECS
from wealth_intent.runtime import route_request
from wealth_intent.semantic_contract import validate_semantic

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "step5_disagreement_review_v1"
MASTER = ROOT.parent / "step5_disagreement_review_packages.zip"
SEMANTIC_FIELDS = ("intents", "scope", "goal", "output", "audience", "metric",
                   "subject_selection", "requested_effect")
CHUNK_SIZE = 12

SCOPES = ["general", "account_or_client", "household", "subject_set", "advisor_book",
          "portfolio", "security_or_instrument", "product_or_strategy", "practice"]
SELECTIONS = ["unspecified", "single_subject", "explicit_subject_references",
              "prioritized_clients", "criteria_filtered_book", "entire_book"]
EFFECTS = ["read_only", "draft_only", "ambiguous_monitor", "monitor_specification", "operational_action"]
AUDIENCES = ["advisor", "client"]
METRICS = ["credit_spread", "estimate_revisions", "credit_rating", "short_interest",
           "earnings", "duration", "sector_exposure"]
OUTPUTS = ["cited_answer", "cited_explanation", "email_draft", "talking_points", "voicemail_script",
           "voicemail_bullets", "analysis_table", "ranked_table", "comparison_table", "solution_shortlist",
           "guidance_or_diagnostic_checklist", "decision_summary", "meeting_book", "review_comparison",
           "tax_aware_transition_proposal", "holdings_signal_analysis"]
GOALS = ["interpret_market_signal", "explain_credit_spread_change", "screen_market_signals_for_client_holdings",
         "design_tax_aware_concentrated_stock_transition", "draft_client_market_update",
         "transform_supplied_content", "compare_rebalance_scenario", "review_changes", "fulfill_registered_tasks"]


def load(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def frame(labels):
    return {field: labels.get(field) for field in SEMANTIC_FIELDS}


def key(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def vocabulary():
    return {
        "version": "focused-semantic-review.1",
        "intents": {s.id: f"{s.title}: {s.operation}" for s in SPECS},
        "scope": {
            "general": "no specific subject", "account_or_client": "one client/account",
            "household": "related household accounts", "subject_set": "selected/named/filtered multi-subject set",
            "advisor_book": "entire advisor book", "portfolio": "portfolio as analytical subject",
            "security_or_instrument": "issuer/security/issue/note", "product_or_strategy": "product/program/strategy",
            "practice": "advisor-team business analytics"},
        "subject_selection": {
            "unspecified": "not determinable", "single_subject": "one subject",
            "explicit_subject_references": "named/enumerated/selected set",
            "prioritized_clients": "prioritized-client set", "criteria_filtered_book": "query-defined criteria",
            "entire_book": "complete advisor book"},
        "requested_effect": {
            "read_only": "research/analysis/guidance", "draft_only": "create but do not send",
            "ambiguous_monitor": "one-time versus recurring unresolved",
            "monitor_specification": "define recurring monitoring", "operational_action": "perform external action"},
        "audience": AUDIENCES, "metrics": METRICS, "outputs": OUTPUTS, "goals": GOALS,
        "null_policy": "Use null only when the request cannot support a registered single value.",
    }


def schema():
    semantic = {
        "type": ["object", "null"], "additionalProperties": False,
        "required": list(SEMANTIC_FIELDS),
        "properties": {
            "intents": {"type": "array", "items": {"enum": [s.id for s in SPECS]}, "uniqueItems": True},
            "scope": {"enum": SCOPES + [None]}, "goal": {"enum": GOALS + [None]},
            "output": {"enum": OUTPUTS + [None]}, "audience": {"enum": AUDIENCES + [None]},
            "metric": {"enum": METRICS + [None]}, "subject_selection": {"enum": SELECTIONS + [None]},
            "requested_effect": {"enum": EFFECTS + [None]},
        }}
    props = {
        "case_id": {"type": "string"},
        "resolution": {"enum": ["SELECT_OPTION", "REVISED_FRAME", "TAXONOMY_ISSUE", "UNRESOLVED"]},
        "selected_option_id": {"type": ["string", "null"]}, "semantic_labels": semantic,
        "ambiguous_fields": {"type": "array", "items": {"enum": list(SEMANTIC_FIELDS)}, "uniqueItems": True},
        "confidence": {"enum": ["high", "medium", "low"]},
        "taxonomy_issue": {"type": ["string", "null"], "maxLength": 400},
        "short_rationale": {"type": "string", "maxLength": 500},
    }
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object",
            "additionalProperties": False, "required": list(props), "properties": props}


def semantic_issues(labels):
    return validate_semantic({k: labels.get(k) for k in
                              ("intents", "scope", "subject_selection", "requested_effect", "metric")})


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", default="data/semantic_annotation_corpus.jsonl")
    p.add_argument("--pass1", required=True); p.add_argument("--pass2", required=True)
    p.add_argument("--pass3", required=True); p.add_argument("--adjudicated", required=True)
    args = p.parse_args()
    corpus = {x["case_id"]: x for x in load(args.corpus)}
    passes = [{x["case_id"]: x for x in load(path)} for path in (args.pass1, args.pass2, args.pass3)]
    adj = {x["case_id"]: x for x in load(args.adjudicated)}
    if any(set(values) != set(corpus) for values in [*passes, adj]):
        raise SystemExit("All input files must cover the corpus case IDs exactly.")

    selected = []
    hidden = {}
    for cid, source in corpus.items():
        reasons = []
        adjudicated = adj[cid]
        if adjudicated["silver_label_status"] == "UNRESOLVED": reasons.append("unresolved")
        if adjudicated.get("labels") and semantic_issues(adjudicated["labels"]): reasons.append("contract_invalid")
        if len({tuple(sorted(x[cid]["labels"]["intents"])) for x in passes}) > 1:
            reasons.append("intent_disagreement")
        pairs = {(x[cid]["labels"]["scope"], x[cid]["labels"]["capability_id"]) for x in passes}
        if len({x[0] for x in pairs}) > 1 and len({x[1] for x in pairs}) > 1:
            reasons.append("scope_changes_downstream_capability")
        poc = route_request(source["query"])
        if (adjudicated.get("labels") and poc["decision"] == "CAPABILITY_GAP"
                and adjudicated["labels"]["decision"] == "ROUTE_PREVIEW"):
            reasons.append("downstream_route_disagreement")
        if not reasons: continue

        proposals = []
        for index, values in enumerate(passes, 1):
            proposals.append({"source": f"LLM_PASS_{index}", "semantic_labels": frame(values[cid]["labels"]),
                              "reported_route": {"capability_id": values[cid]["labels"]["capability_id"],
                                                 "decision": values[cid]["labels"]["decision"]}})
        proposals.append({"source": "POC_0.6.1", "semantic_labels": frame(poc),
                          "reported_route": {"capability_id": poc["capability_id"], "decision": poc["decision"]}})
        dedup = {}
        for proposal in proposals:
            entry = dedup.setdefault(key(proposal["semantic_labels"]),
                                     {"semantic_labels": proposal["semantic_labels"], "sources": [], "routes": []})
            entry["sources"].append(proposal["source"]); entry["routes"].append(proposal["reported_route"])
        choices = list(dedup.values())
        random.Random(f"focused-review-v1:{cid}").shuffle(choices)
        public_options, provenance = [], {}
        for number, choice in enumerate(choices, 1):
            option = f"option_{number}"
            public_options.append({"option_id": option, "semantic_labels": choice["semantic_labels"]})
            provenance[option] = {"sources": choice["sources"], "reported_routes": choice["routes"]}
        hidden[cid] = provenance
        selected.append({"case_id": cid, "masked_request": mask(source["query"]).masked_text,
                         "review_reasons": reasons, "candidate_options": public_options})

    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    random.Random(4417).shuffle(selected)
    chunks = [selected[i:i+CHUNK_SIZE] for i in range(0, len(selected), CHUNK_SIZE)]
    package_rows = []
    for number, rows in enumerate(chunks, 1):
        work = OUT / "_work"; shutil.rmtree(work, ignore_errors=True); work.mkdir()
        (work / "TASK.md").write_text(
            f"# Focused semantic review — chunk {number:02d}\n\n"
            f"Review all {len(rows)} records in `review_cases.jsonl` using the supplied instructions and contracts. "
            f"Return exactly one result per case as `step5_review_chunk_{number:02d}_results.jsonl`. "
            "Do not identify candidate sources or classify capabilities, context, decisions, functions, or DAGs.\n")
        (work / "STEP5_DISAGREEMENT_REVIEW_INSTRUCTIONS.md").write_text(
            (ROOT / "STEP5_DISAGREEMENT_REVIEW_INSTRUCTIONS.md").read_text())
        (work / "review_cases.jsonl").write_text("".join(json.dumps(x, sort_keys=True)+"\n" for x in rows))
        (work / "controlled_vocabulary.json").write_text(json.dumps(vocabulary(), indent=2)+"\n")
        (work / "review_output_schema.json").write_text(json.dumps(schema(), indent=2)+"\n")
        child = OUT / f"step5_review_chunk_{number:02d}.zip"
        with zipfile.ZipFile(child, "w", zipfile.ZIP_DEFLATED) as z:
            for path in sorted(work.iterdir()): z.write(path, path.name)
        package_rows.append({"chunk": number, "package": child.name, "records": len(rows),
                             "sha256": hashlib.sha256(child.read_bytes()).hexdigest()})
    shutil.rmtree(OUT / "_work", ignore_errors=True)
    with (OUT / "PACKAGE_INDEX.csv").open("w", newline="") as f:
        writer=csv.DictWriter(f, fieldnames=package_rows[0]); writer.writeheader(); writer.writerows(package_rows)
    (OUT / "START_HERE.md").write_text(
        "# Start here\n\nExtract this master ZIP locally. Give the new model one numbered child ZIP at a time, "
        "using the copy/paste request in the included instructions. Do not upload the hidden provenance map.\n")
    with zipfile.ZipFile(MASTER, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(OUT.iterdir()): z.write(path, path.name)
    hidden_path = ROOT / "data" / "DO_NOT_UPLOAD_disagreement_review_provenance_map_v1.json"
    hidden_path.write_text(json.dumps({"schema_version": "review_provenance_map.1", "cases": hidden}, indent=2)+"\n")
    manifest = {"schema_version": "focused_disagreement_review_manifest.1", "cases": len(selected),
                "chunks": len(chunks), "maximum_cases_per_chunk": max(map(len,chunks)),
                "reason_counts": {reason: sum(reason in x["review_reasons"] for x in selected)
                                  for reason in sorted({r for x in selected for r in x["review_reasons"]})},
                "candidate_sources_anonymized": True,
                "master_sha256": hashlib.sha256(MASTER.read_bytes()).hexdigest(),
                "hidden_provenance_map": str(hidden_path.relative_to(ROOT)),
                "assurance": "LLM_SILVER_REVIEW_ONLY_NOT_HUMAN_GROUND_TRUTH"}
    (ROOT / "data" / "disagreement_review_manifest_v1.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__": main()
