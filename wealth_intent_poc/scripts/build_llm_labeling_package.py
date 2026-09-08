"""Build a prediction-free, masked package for blind LLM corpus annotation."""
import hashlib
import json
import random
import shutil
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wealth_intent.planning import capability_catalog, function_catalog
from wealth_intent.privacy import mask
from wealth_intent.registry import REGISTRY_VERSION, SPECS
from wealth_intent.semantic import CONTEXT_TYPES

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "semantic_annotation_corpus.jsonl"
OUT = ROOT.parent / "llm_labeling_package_v1"
ZIP = ROOT.parent / "llm_labeling_package_v1"
PACKAGE_VERSION = "wealth-llm-label-package.1"
PROMPT_VERSION = "wealth-label-v1"
BATCH_SIZE = 5


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_jsonl(path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(value, sort_keys=True) + "\n" for value in values))


def grouped_batches(records, seed):
    groups = defaultdict(list)
    for record in records:
        groups[record["split_group"]].append(record)
    keys = sorted(groups)
    random.Random(seed).shuffle(keys)
    ordered = []
    for key in keys:
        group = list(groups[key])
        random.Random(f"{seed}:{key}").shuffle(group)
        ordered.extend(group)
    return [ordered[index:index + BATCH_SIZE] for index in range(0, len(ordered), BATCH_SIZE)]


def output_schema(capabilities, vocabulary):
    labels = ["intents", "scope", "goal", "output", "audience", "metric",
              "subject_selection", "requested_effect", "capability_id", "decision",
              "missing_context"]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "wealth-llm-label-output-v1",
        "type": "object",
        "additionalProperties": False,
        "required": ["case_id", "prompt_version", "model_id", "labels", "evidence",
                     "uncertain_fields", "alternatives", "capability_coverage_check",
                     "privacy_category_counts", "labeler_notes"],
        "properties": {
            "case_id": {"type": "string"},
            "prompt_version": {"const": PROMPT_VERSION},
            "model_id": {"type": "string", "minLength": 1},
            "labels": {
                "type": "object", "additionalProperties": False, "required": labels,
                "properties": {
                    "intents": {"type": "array", "items": {"enum": [s.id for s in SPECS]}, "uniqueItems": True},
                    "scope": {"enum": [*vocabulary["scope"], None]},
                    "goal": {"enum": [*vocabulary["goal"], None]},
                    "output": {"enum": [*vocabulary["output"], None]},
                    "audience": {"enum": [*vocabulary["audience"], None]},
                    "metric": {"enum": [k for k in vocabulary["metric"] if k != "null"] + [None]},
                    "subject_selection": {"enum": [*vocabulary["subject_selection"], None]},
                    "requested_effect": {"enum": [*vocabulary["requested_effect"], None]},
                    "capability_id": {"enum": [c["id"] for c in capabilities] + [None]},
                    "decision": {"enum": [*vocabulary["decision"], None]},
                    "missing_context": {"type": "array", "items": {"enum": sorted(CONTEXT_TYPES)}, "uniqueItems": True},
                },
            },
            "evidence": {"type": "object"},
            "uncertain_fields": {"type": "array", "items": {"type": "string"}, "uniqueItems": True},
            "alternatives": {"type": "object"},
            "capability_coverage_check": {
                "type": "object", "additionalProperties": False,
                "required": ["covers_complete_request", "uncovered_work"],
                "properties": {
                    "covers_complete_request": {"type": "boolean"},
                    "uncovered_work": {"type": "array", "items": {"type": "string"}},
                },
            },
            "privacy_category_counts": {"type": "object"},
            "labeler_notes": {"type": "string"},
        },
    }


def label_vocabulary(capabilities):
    return {
        "schema_version": "wealth-label-vocabulary.1",
        "intents": [
            {"value": s.id, "family": s.family, "definition": s.title,
             "operation": s.operation, "required_inputs": list(s.required_inputs),
             "examples": list(s.examples)} for s in SPECS
        ],
        "scope": {
            "general": "No specific client, account, instrument, product, practice, or population.",
            "account_or_client": "One client or one account.",
            "household": "A household or family relationship containing multiple related accounts.",
            "subject_set": "A selected, named, prioritized, or criteria-defined set of clients/accounts.",
            "advisor_book": "The advisor's complete book without a narrower population selection.",
            "portfolio": "A portfolio as the analytical subject when no client/account scope is stated.",
            "security_or_instrument": "One issuer, security, issue, note, or market instrument.",
            "product_or_strategy": "An investment product, program, model, or strategy.",
            "practice": "Advisor-team or practice-level business analytics.",
        },
        "subject_selection": {
            "unspecified": "No registered selection strategy can be determined.",
            "single_subject": "Exactly one client, account, portfolio, product, or instrument.",
            "explicit_subject_references": "A named, enumerated, selected, or deictic multi-subject set.",
            "prioritized_clients": "The advisor's pre-existing prioritized-client population.",
            "criteria_filtered_book": "Subjects selected by query-stated criteria.",
            "entire_book": "The complete advisor book.",
        },
        "requested_effect": {
            "read_only": "Research, analysis, explanation, comparison, guidance, or diagnosis only.",
            "draft_only": "Create content for later human review; do not send it.",
            "ambiguous_monitor": "Flag/monitor wording does not distinguish one-time analysis from recurrence.",
            "monitor_specification": "Define a recurring monitor or notification rule; nothing is scheduled by the POC.",
            "operational_action": "The user asks to perform a consequential external action.",
        },
        "audience": {
            "advisor": "The requested artifact is for advisor use.",
            "client": "The user explicitly requests client-facing communication.",
        },
        "metric": {
            "credit_spread": "Issuer or issue credit-spread level/change.",
            "estimate_revisions": "Analyst estimate or consensus forecast revisions.",
            "earnings": "Earnings, earnings event, or earnings result.",
            "short_interest": "Short-interest level or change.",
            "price_target": "Analyst price target or target revision.",
            "credit_rating": "Credit rating, watch status, or rating-agency action.",
            "duration": "Duration or interest-rate sensitivity.",
            "sector_exposure": "Sector or international exposure signal.",
            "null": "No metric is requested or the metric is indeterminate.",
        },
        "output": {
            "cited_answer": "A sourced answer without a specifically requested explanatory form.",
            "cited_explanation": "A sourced explanation of causes, changes, or drivers.",
            "email_draft": "An unsent email draft.",
            "talking_points": "Advisor talking points or general drafted communication.",
            "voicemail_script": "A complete voicemail script.",
            "voicemail_bullets": "Bullets for a voicemail.",
            "analysis_table": "Tabular analytical result.",
            "ranked_table": "Ranked or prioritized tabular result.",
            "comparison_table": "Side-by-side product or strategy comparison.",
            "solution_shortlist": "A governed list of potential products or solutions.",
            "guidance_or_diagnostic_checklist": "Procedural guidance or diagnostic checklist.",
            "decision_summary": "Decision, risk, disclosure, or approval summary.",
            "meeting_book": "Prepared client-meeting material.",
            "review_comparison": "Current-versus-prior review comparison.",
            "tax_aware_transition_proposal": "Proposal for a tax-aware concentrated-position transition.",
            "holdings_signal_analysis": "Portfolio/book holdings joined to market signals and affected subjects.",
        },
        "goal": {
            "interpret_market_signal": "Explain a market or instrument signal.",
            "explain_credit_spread_change": "Explain credit-spread movement and drivers.",
            "screen_market_signals_for_client_holdings": "Find material signals affecting holdings across a subject set/book.",
            "design_tax_aware_concentrated_stock_transition": "Construct a tax-aware transition proposal for concentrated stock.",
            "draft_client_market_update": "Prepare client-facing market content without sending.",
            "transform_supplied_content": "Rewrite or transform supplied content.",
            "compare_rebalance_scenario": "Compare the portfolio before and after a proposed rebalance.",
            "review_changes": "Compare current and prior information.",
            "fulfill_registered_tasks": "Produce the registered single-task or explicitly composed analytical outcome.",
        },
        "decision": {
            "CLARIFY": "Meaning or required request-specific information must be supplied by the user.",
            "REVIEW": "Required context conflicts/is unavailable, or a consequential action needs controlled review.",
            "CAPABILITY_GAP": "Meaning is sufficiently clear but no exact capability covers the complete request.",
            "ROUTE_PREVIEW": "A registered read-only/draft plan can be previewed; this is not execution readiness.",
        },
        "capability_ids": [c["id"] for c in capabilities],
        "missing_context_values": sorted(CONTEXT_TYPES),
        "nullable_fields": ["scope", "goal", "output", "audience", "metric",
                            "subject_selection", "requested_effect", "capability_id", "decision"],
        "note": "Use null rather than inventing a controlled value. Flag a missing vocabulary value for taxonomy review.",
    }


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    raw = [json.loads(line) for line in SOURCE.read_text().splitlines() if line.strip()]
    records = []
    for item in raw:
        masked = mask(item["query"])
        records.append({
            "case_id": item["case_id"],
            "split_group": item["split_group"],
            "masked_request": masked.masked_text,
            "privacy_category_counts": masked.findings,
        })

    capabilities = capability_catalog()
    write_jsonl(OUT / "corpus" / "labeling_corpus_masked.jsonl", records)
    for pass_number, seed in ((1, 1103), (2, 2207), (3, 3301)):
        batches = grouped_batches(records, seed)
        for index, batch in enumerate(batches, 1):
            write_jsonl(OUT / "corpus" / f"pass_{pass_number}_batches" / f"batch_{index:03d}.jsonl", batch)
        write_json(OUT / "corpus" / f"pass_{pass_number}_batch_manifest.json", {
            "pass": pass_number, "seed": seed, "batches": len(batches),
            "records": len(records), "split_group_partition_integrity": True,
            "note": "A large split group may span batches but never leaves this pass/partition.",
        })

    vocabulary = label_vocabulary(capabilities)
    write_json(OUT / "contracts" / "controlled_vocabulary.json", vocabulary)
    write_json(OUT / "contracts" / "intent_registry.json", {
        "registry_version": REGISTRY_VERSION, "intents": [s.to_dict() for s in SPECS]})
    write_json(OUT / "contracts" / "capability_contracts.json", {
        "warning": "Authored preview contracts; a match is not financial validation or execution authority.",
        "capabilities": capabilities})
    write_json(OUT / "contracts" / "function_contracts.json", {
        "instruction": "Use only to understand typed requirements; functions are not intent labels.",
        "functions": function_catalog()})
    write_json(OUT / "contracts" / "semantic_constraints.json", {
        "subject_set_requires_selection": True,
        "set_selections": ["explicit_subject_references", "prioritized_clients",
                           "criteria_filtered_book", "entire_book"],
        "set_scopes": ["subject_set", "advisor_book"],
        "book_screen_scopes": ["subject_set", "advisor_book"],
        "draft_effect_requires_intent": "content.draft",
        "subject_set_research_requires_metric": True,
        "instruction": "Reject or mark uncertain any label set that violates these cross-field constraints.",
    })
    write_json(OUT / "contracts" / "annotation_output_schema.json", output_schema(capabilities, vocabulary))
    shutil.copy2(ROOT / "LLM_ASSISTED_CORPUS_LABELING_INSTRUCTIONS.md", OUT / "LLM_ASSISTED_CORPUS_LABELING_INSTRUCTIONS.md")

    (OUT / "contracts" / "decision_policy.md").write_text("""# Frozen decision policy

Apply in this order:

1. `CLARIFY` when intent/scope/effect is materially ambiguous or request-specific information must come from the user.
2. `CAPABILITY_GAP` when meaning is clear but no capability covers the complete intent/scope/effect/output combination.
3. `REVIEW` when required context conflicts or is unavailable, or the request asks for a consequential operational action.
4. `ROUTE_PREVIEW` when an exact registered read-only or draft capability can be previewed. Pending normal host context or downstream evidence does not itself require clarification.

Never interpret `ROUTE_PREVIEW` as authorization, execution readiness, or financial correctness.
""")

    perspectives = {
        1: "SEMANTIC_ANALYST — maximize completeness of literal requested work without adding customary tasks.",
        2: "CONSERVATIVE_RISK_REVIEWER — minimize false confident routing; surface material ambiguity.",
        3: "CAPABILITY_CONTRACT_AUDITOR — require exact coverage of the complete request and bindings.",
    }
    for number, perspective in perspectives.items():
        (OUT / "prompts" / f"pass_{number}_prompt.md").parent.mkdir(parents=True, exist_ok=True)
        (OUT / "prompts" / f"pass_{number}_prompt.md").write_text(f"""# Blind labeling pass {number}

Follow `LLM_ASSISTED_CORPUS_LABELING_INSTRUCTIONS.md`.

Perspective: **{perspective}**

Process only `corpus/pass_{number}_batches/`, in numeric order. Do not inspect other pass directories. Return one consolidated artifact named `llm_labels_pass_{number}.jsonl`, with exactly one schema-valid object per input case. Do not classify from filenames, neighboring cases, author hypotheses, or imagined business context. If output limits prevent completion, return the completed JSONL checkpoint and name the next batch; do not silently omit cases.
""")

    (OUT / "prompts" / "adjudication_prompt.md").write_text("""# Silver-label adjudication

Run only after three blind pass files are complete and frozen. Follow section 12 of the instructions. Use the masked corpus, contracts, three pass outputs, and deterministic validation findings. Do not use POC predictions or author hypotheses. Return `llm_adjudicated_silver_labels.jsonl` and `llm_labeling_report.md`; preserve every source annotation and mark unresolved cases.
""")

    (OUT / "START_HERE.md").write_text("""# Start here

This package supports one blind labeling pass per stateless LLM session. It does not contain POC predictions, author hypotheses, workbook outcome columns, raw identifiers, or prior labels.

1. Upload this ZIP and the external instructions file.
2. For pass 1, ask the LLM to follow `prompts/pass_1_prompt.md`. Save its JSONL output.
3. Repeat in two new stateless sessions for passes 2 and 3. Do not attach earlier pass outputs.
4. Start a fourth stateless session, upload this package plus all three completed pass files, and follow `prompts/adjudication_prompt.md`.
5. Treat the result as provisional silver labels, never human ground truth.

The corpus is divided into grouped batches because 242 complete labels may exceed a single response limit. A capable file-producing agent may process all batches and return a consolidated file; otherwise use its checkpoint and continue the same pass without exposing other passes.
""")

    (OUT / "UPLOAD_MESSAGES.md").write_text("""# Copy/paste upload messages

Use each blind pass in a new stateless session. Attach this package and the standalone instructions file.

## Session 1

> Execute blind labeling Pass 1 exactly as defined in `prompts/pass_1_prompt.md` and `LLM_ASSISTED_CORPUS_LABELING_INSTRUCTIONS.md`. Process every Pass 1 batch in numeric order. Return the requested consolidated `llm_labels_pass_1.jsonl` as a file. Do not inspect Pass 2 or Pass 3 directories, and do not print hundreds of JSON objects into chat. If you cannot finish, return a valid checkpoint file and identify the next unprocessed batch.

## Session 2

> Execute blind labeling Pass 2 exactly as defined in `prompts/pass_2_prompt.md` and `LLM_ASSISTED_CORPUS_LABELING_INSTRUCTIONS.md`. Process every Pass 2 batch in numeric order. Return the requested consolidated `llm_labels_pass_2.jsonl` as a file. Do not inspect Pass 1 or Pass 3 directories, and do not print hundreds of JSON objects into chat. If you cannot finish, return a valid checkpoint file and identify the next unprocessed batch.

## Session 3

> Execute blind labeling Pass 3 exactly as defined in `prompts/pass_3_prompt.md` and `LLM_ASSISTED_CORPUS_LABELING_INSTRUCTIONS.md`. Process every Pass 3 batch in numeric order. Return the requested consolidated `llm_labels_pass_3.jsonl` as a file. Do not inspect Pass 1 or Pass 2 directories, and do not print hundreds of JSON objects into chat. If you cannot finish, return a valid checkpoint file and identify the next unprocessed batch.

## Session 4 — after all three outputs exist

Attach this package, the instructions, and the three completed JSONL pass files.

> Execute the adjudication procedure in `prompts/adjudication_prompt.md` and section 12 of the instructions. Validate all three pass files, calculate agreement, retain the three source annotations, adjudicate only from masked-query evidence and frozen contracts, and preserve unresolved cases. Return `llm_adjudicated_silver_labels.jsonl` and `llm_labeling_report.md` as files. Do not use or request POC predictions or author hypotheses.
""")

    write_jsonl(OUT / "output_templates" / "empty_pass_output.jsonl", [])
    write_json(OUT / "output_templates" / "empty_labeling_report.json", {
        "prompt_version": PROMPT_VERSION, "models": [], "records": 0,
        "unanimous": 0, "majority": 0, "unresolved": 0,
        "validation_failures": {}, "field_agreement": {},
    })

    files = sorted(path for path in OUT.rglob("*") if path.is_file())
    manifest = {
        "package_version": PACKAGE_VERSION,
        "poc_version": "0.6.0",
        "runtime_schema": "5.0",
        "prompt_version": PROMPT_VERSION,
        "records": len(records),
        "split_groups": len({r["split_group"] for r in records}),
        "blind_passes": 3,
        "files": {str(path.relative_to(OUT)): digest(path) for path in files},
        "exclusions": ["raw request identifiers", "POC predictions", "author hypotheses",
                       "workbook Problem Solved", "workbook Investment Agent Output", "prior labels"],
        "assurance": "LLM_SILVER_LABEL_INPUT_ONLY",
    }
    write_json(OUT / "PACKAGE_MANIFEST.json", manifest)
    archive = shutil.make_archive(str(ZIP), "zip", OUT.parent, OUT.name)
    print(json.dumps({"package": archive, "records": len(records),
                      "split_groups": manifest["split_groups"], "files": len(files) + 1}, indent=2))


if __name__ == "__main__":
    main()
