# LLM-assisted corpus labeling instructions

**Purpose:** create consistent provisional labels for the Wealth Intent POC corpus when qualified human annotators are unavailable.

**Important limitation:** these labels are **LLM-generated silver labels**, not independent human ground truth. They may be used to discover taxonomy gaps, prioritize parser work, and run provisional comparisons. They must not be reported as human accuracy, used as regulatory evidence, or marked `independent_review=true`. The current training gate intentionally excludes the bundled rewritten and synthetic records.

## 1. Deliverables

Produce five outputs without changing the canonical source corpus:

1. `llm_labels_pass_1.jsonl` — first blind labeling pass.
2. `llm_labels_pass_2.jsonl` — second blind labeling pass.
3. `llm_labels_pass_3.jsonl` — third blind labeling pass.
4. `llm_adjudicated_silver_labels.jsonl` — adjudicated result with disagreements and rationale.
5. `llm_labeling_report.md` — coverage, agreement, validation failures, unresolved cases, and model/prompt provenance.

Never overwrite `data/semantic_annotation_corpus.jsonl`. Join labels back to source records only by `case_id` after all passes are complete.

## 2. Inputs to freeze before labeling

Create a versioned labeling package containing:

- `data/semantic_annotation_corpus.jsonl`;
- `data/semantic_annotation_schema.json`;
- the allowed intent registry with definitions and examples;
- allowed scope, goal, output, audience, metric, subject-selection, effect, capability, and decision values;
- capability definitions, including required intent combinations, allowed scope, output contract, and required context;
- a frozen labeling guide and prompt version;
- POC version, schema version, registry digest, corpus digest, model IDs, and model release dates.

Do not include any of the following in an annotator's input:

- current POC predictions;
- `author_hypothesis`;
- workbook `Problem Solved` or `Investment Agent Output` columns;
- another annotator's labels;
- test expectations or probe-group expected results;
- labels from a previous labeling pass.

These exclusions prevent the LLM from merely copying the system being evaluated.

## 3. Privacy preparation

The bundled corpus is sanitized, but run the local privacy scanner again before any model call.

For each request:

1. Detect email addresses, phone numbers, account identifiers, monetary values, addresses, and possible names.
2. Replace them locally with typed placeholders such as `[EMAIL]`, `[ACCOUNT_REFERENCE]`, `[MONEY_AMOUNT]`, and `[POSSIBLE_NAME]`.
3. Retain only the relationship needed for labeling; for example, two occurrences of the same client may use `[CLIENT_1]` consistently.
4. Do not send client profiles, holdings, tax lots, portfolio values, entitlement records, or attachment contents.
5. Record only privacy-category counts—not original sensitive values—in the labeling output.

If organizational policy prohibits external model processing even after masking, run the exact workflow with an approved locally hosted model. Do not assume heuristic masking proves de-identification.

## 4. Unit of work and batching

The annotation unit is one complete advisor request. Use `case_id` as its identifier.

- Keep every record with the same `split_group` in the same data partition.
- Do not split paraphrases from the same source group across training and evaluation.
- Send one request per LLM call for the initial POC. This reduces cross-record contamination.
- If batching becomes necessary, use at most five unrelated requests and require a separate JSON object for each `case_id`.
- Randomize record order independently for each labeling pass.
- Start every pass in a new stateless session with no conversation history.

## 5. Independent labeling passes

Run three blind passes. Prefer three independently developed model families. If only one model is available, use three fresh sessions with different record order and do not call the resulting votes model-independent.

| Pass | Required perspective | Primary failure to avoid |
| --- | --- | --- |
| 1 — semantic analyst | Identify the work explicitly requested and its semantic dimensions | Missing legitimate multi-intent requests |
| 2 — conservative risk reviewer | Abstain on implied meaning and identify ambiguity or missing context | False confident routing |
| 3 — capability-contract auditor | Check exact capability coverage and required bindings | Matching a capability that does not cover the full request |

Use temperature 0 or the lowest deterministic setting available. Pin the model version. Disable web search, retrieval, tools, memory, and access to prior outputs.

## 6. Labeling sequence for every request

Each annotator must perform these subtasks in order:

1. **Segment the request.** Identify positive requested clauses, negated clauses, constraints, and referenced subjects.
2. **Determine requested effect.** Choose read-only guidance/analysis, draft creation, consequential action, recurring monitoring, or the controlled equivalent in the registry.
3. **Determine scope.** Identify a single client/account, household, subject set, advisor book, security/instrument, product/strategy, or other registered scope.
4. **Determine subject selection.** Distinguish single subject, explicit references, prioritized clients, criteria-filtered book, entire book, or unspecified.
5. **Assign the complete intent set.** Label all work necessary to satisfy the literal request. Do not add tasks merely because they commonly accompany the request.
6. **Assign semantic outcome fields.** Label goal, output, audience, metric, and any typed parameters supported by the text.
7. **Check capability coverage.** Select a capability only if its contract covers the complete intent set, scope, requested effect, and output. Otherwise use no capability and explain the gap.
8. **Identify context requirements.** List request-specific information that must be supplied or resolved. Do not label normal downstream retrieval as advisor clarification.
9. **Determine decision.** Select clarification, review, capability gap, or route preview according to the frozen decision policy.
10. **Cite evidence spans.** Provide short spans from the masked query supporting each intent, scope, effect, and metric.
11. **Record uncertainty.** Mark fields that cannot be determined from the query and identify the competing values. Do not guess.

## 7. Rules the LLM must follow

- Use only registered values. Never invent a new intent or capability inside a label.
- Label the advisor's requested outcome, not the likely implementation steps.
- A client mention does not automatically make the audience `client`; drafting client communication does.
- “Draft” is not “send.” “How do I enroll?” is guidance; “enroll this client” requests an action.
- Negated work is not an intent unless the remaining request explicitly requires it.
- Named clients, selected clients, and prioritized clients may share `scope=subject_set`; preserve the access strategy in `subject_selection`.
- “Top holdings,” “major,” and time phrases are parameters or missing bindings—not separate intents.
- An attachment mention does not prove that an instrument or time period was resolved.
- `ROUTE_PREVIEW` means that a registered plan can be previewed; it does not mean authorized, executable, or financially correct.
- Prefer `CLARIFY` over inventing a reference or a workflow-changing interpretation.
- Prefer `CAPABILITY_GAP` when meaning is sufficiently clear but no exact registered outcome covers it.

## 8. Required output for each blind pass

Return JSON only, using this structure:

```json
{
  "case_id": "source case ID",
  "prompt_version": "wealth-label-v1",
  "model_id": "pinned model identifier",
  "labels": {
    "intents": [],
    "scope": null,
    "goal": null,
    "output": null,
    "audience": null,
    "metric": null,
    "subject_selection": null,
    "requested_effect": null,
    "capability_id": null,
    "decision": null,
    "missing_context": []
  },
  "evidence": {
    "intents": [],
    "scope": [],
    "metric": [],
    "requested_effect": []
  },
  "uncertain_fields": [],
  "alternatives": {},
  "capability_coverage_check": {
    "covers_complete_request": false,
    "uncovered_work": []
  },
  "privacy_category_counts": {},
  "labeler_notes": "brief rationale without chain-of-thought"
}
```

`labeler_notes` should contain a short decision rationale, not hidden chain-of-thought. Evidence spans must be copied only from the masked request.

## 9. Base prompt for the three passes

Use the following prompt, inserting the frozen registry and one masked request. Change only the stated reviewer perspective for passes 1–3.

```text
You are a corpus annotator for a wealth-management request router.

Reviewer perspective: <SEMANTIC_ANALYST | CONSERVATIVE_RISK_REVIEWER | CAPABILITY_CONTRACT_AUDITOR>

Your task is annotation, not execution and not financial advice. Use only the supplied controlled vocabulary and capability contracts. Label only what the masked advisor request supports. Do not infer labels from common workflows. Treat unresolved references as missing context. Treat negated clauses as exclusions. A capability must cover the complete request.

You have no access to system predictions, author hypotheses, business-purpose columns, other reviewers, external data, or conversation history.

Return exactly one JSON object matching OUTPUT_SCHEMA. Use null when a single-valued field cannot be determined. Do not invent values. Provide short evidence spans and a brief rationale; do not provide chain-of-thought.

CONTROLLED_VOCABULARY:
<insert frozen label definitions>

CAPABILITY_CONTRACTS:
<insert frozen capability definitions>

DECISION_POLICY:
<insert frozen decision rules>

OUTPUT_SCHEMA:
<insert schema from section 8>

CASE_ID: <case_id>
MASKED_REQUEST: <masked query>
```

## 10. Automated validation after each pass

Reject and retry an annotation if any of these checks fails:

- invalid JSON or wrong `case_id`;
- an unknown field or controlled value;
- duplicate intents or missing required keys;
- evidence text not present in the masked request;
- a capability that does not contain the labeled intent set;
- `subject_set` without a set-oriented `subject_selection`;
- draft effect without a drafting intent;
- recurring monitoring without the registered monitoring intent/effect;
- a non-null capability with `covers_complete_request=false`;
- a decision inconsistent with capability coverage or unresolved ambiguity;
- raw PII appearing in the output.

Retry once with only the validation errors and the original masked request. If the second result fails, mark the case `LLM_OUTPUT_INVALID` and send it to the unresolved queue.

## 11. Agreement calculation

After all three blind passes, calculate agreement without exposing one pass to another:

- exact intent-set agreement;
- per-field agreement for scope, goal, output, audience, metric, selection, effect, capability, and decision;
- Jaccard agreement for `missing_context`;
- unanimity rate;
- two-of-three majority rate;
- validation-failure rate by model and field;
- disagreement rate by intent family and source group.

Do not reduce multi-value fields to independent majority votes when the resulting combination was not proposed by any annotator. Preserve one complete proposed label set for adjudication.

## 12. LLM adjudication pass

Use a fourth stateless pass after the three blind results are frozen. The adjudicator receives:

- the masked request;
- frozen vocabulary and capability contracts;
- all three label objects, identified only as A, B, and C;
- deterministic validation findings;
- no POC prediction and no author hypothesis.

The adjudicator must:

1. list fields with disagreement;
2. compare each proposal against literal evidence and registered contracts;
3. select one complete label set or mark the case unresolved;
4. never create a hybrid combination that violates the semantic contract;
5. provide a concise field-level rationale;
6. assign `silver_label_status` as `UNANIMOUS`, `MAJORITY_ADJUDICATED`, `LLM_ADJUDICATED`, or `UNRESOLVED`.

The adjudicated output must retain all three original annotations and full model/prompt provenance.

## 13. Escalation rules

Mark a case `UNRESOLVED` instead of forcing a silver label when:

- all three intent sets differ;
- scope or requested effect has no majority;
- the capability decision is split among route, clarify, and gap;
- the request depends on firm-specific terminology absent from the registry;
- two plausible interpretations produce materially different DAGs;
- the request contains an action whose read/write meaning is unclear;
- deterministic semantic validation continues to fail;
- the query is incomplete, corrupted, or dependent on unavailable conversation context.

Maintain these cases as the highest-priority future human-review queue.

## 14. How silver labels may be used

Permitted uses:

- identify missing synonyms and parser failure families;
- identify inconsistent taxonomy or capability contracts;
- create candidate regression tests after manual engineering review;
- compare parser behavior against an LLM consensus baseline;
- prioritize future human review;
- conduct exploratory model experiments clearly labeled as weak supervision.

Do not:

- set `independent_review=true`;
- set the existing corpus `training_eligible=true`;
- describe results as human-labeled accuracy;
- use the same silver-labeled groups for both training and evaluation;
- automatically change production routing rules from LLM labels;
- use disagreement resolution to optimize against the current POC prediction.

If a separate weak-supervision experiment is approved, create a new dataset version with `label_source=llm_silver`, keep it outside the canonical human-label training path, split by `split_group`, and evaluate only on a separately reserved set. Any eventual production claim still requires qualified human review.

## 15. Completion checklist

- [ ] Registry, capability contracts, decision policy, and prompts are frozen and versioned.
- [ ] Corpus digest and model versions are recorded.
- [ ] PII scanning and local placeholder substitution completed.
- [ ] Predictions, author hypotheses, and workbook outcome columns removed from inputs.
- [ ] Three blind passes completed in isolated sessions.
- [ ] Every output passed schema, evidence, semantic, and privacy validation.
- [ ] Agreement report generated before adjudication.
- [ ] Fourth-pass adjudication completed without access to POC predictions.
- [ ] Unresolved cases retained rather than forced.
- [ ] Silver provenance is present on every adjudicated record.
- [ ] Canonical corpus remains unchanged and no record is marked human reviewed.
- [ ] Findings are reported as provisional LLM agreement, not accuracy.

## 16. Recommended POC stopping point

Complete all 242 records, but use the results first as a diagnostic study. Review the distribution of disagreements and parser deltas before considering any weakly supervised training. If the LLMs repeatedly disagree on a field, revise the label guide or taxonomy before generating more labels.
