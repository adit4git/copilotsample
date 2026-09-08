# Lightweight LLM corpus-labeling instructions

## Purpose

Use two separate LLMs to create provisional semantic labels for 242 masked advisor queries without exhausting a single model session. Each LLM processes one small ZIP at a time. These are **silver labels**, not human ground truth.

## What changed from the earlier package

- Two blind passes instead of three full passes.
- Approximately 20 queries per upload instead of all 242.
- Semantic fields only; no capability, DAG, missing-context, evidence-span, or decision labeling.
- No detailed rationale unless the model is uncertain.
- Capability matching, missing context, routing decision, and DAG are derived later by deterministic POC logic.
- A third LLM call is used only for records on which Pass 1 and Pass 2 disagree.

This reduces repeated input and output while preserving a useful independent comparison.

## Files you will receive

- `llm_lightweight_pass_1_packages.zip` — chunk ZIPs for LLM 1.
- `llm_lightweight_pass_2_packages.zip` — chunk ZIPs for LLM 2.
- Each master ZIP contains a numbered sequence such as `pass_1_chunk_01.zip`.
- Every chunk ZIP is self-contained and includes:
  - `TASK.md`;
  - `queries.jsonl`;
  - `compact_vocabulary.json`;
  - `concise_output_schema.json`.

## Execution procedure

### Pass 1

1. Extract `llm_lightweight_pass_1_packages.zip` locally.
2. Start a new stateless LLM session.
3. Upload only `pass_1_chunk_01.zip`.
4. Send: **“Follow TASK.md exactly. Return the requested JSONL file as an attachment, not inline.”**
5. Save the returned file without renaming it.
6. Continue with the next numbered Pass 1 chunk. The same session may be used for successive chunks, but attach only one chunk at a time.
7. If the model begins using previous chunk content to infer labels, start a fresh session.

### Pass 2

Repeat the same procedure in a separate LLM/model session using only the Pass 2 packages. Never attach Pass 1 outputs or packages to the Pass 2 model.

### Resume after a credit or time limit

Each chunk is independent. Restart at the first chunk without a valid output file. Do not rerun completed chunks unless validation fails.

## Required concise output

The LLM returns one JSON object per query:

```json
{
  "case_id": "base_77",
  "intents": ["research.security"],
  "scope": "security_or_instrument",
  "goal": "interpret_market_signal",
  "output": "cited_answer",
  "audience": "advisor",
  "metric": "estimate_revisions",
  "subject_selection": "single_subject",
  "requested_effect": "read_only",
  "semantic_parameters": {
    "analysis_period": "last_quarter"
  },
  "uncertain_fields": []
}
```

The chunk's JSON Schema contains the allowed values. The model must use `null` when it cannot determine a single-valued field and list that field in `uncertain_fields`.

## Labeling rules

1. Label only work explicitly supported by the masked request.
2. Include every requested intent, but do not add customary downstream tasks.
3. Ignore negated work.
4. “Draft” is not “send.”
5. “How do I enroll?” is read-only guidance; “enroll this client” is an operational action.
6. Named, selected, prioritized, and criteria-filtered multi-client populations use `subject_set`; preserve how they were chosen in `subject_selection`.
7. Treat “top holdings,” percentages, and time phrases as parameters rather than intents.
8. An attachment mention does not prove the referenced instrument was resolved.
9. Do not invent new controlled values. Use `null` and `uncertain_fields`.
10. Provide no financial advice, capability selection, function choice, or DAG.

## Model settings

- Use a pinned model version where possible.
- Use temperature 0 or the lowest available setting.
- Disable web search, tools, memory, and retrieval.
- Do not upload the original workbook, POC predictions, author hypotheses, or another model's labels.

## Output validation after each chunk

Before accepting a returned file, confirm:

- filename matches the name requested in `TASK.md`;
- number of output lines equals the number of input queries;
- every line is valid JSON;
- each input `case_id` appears exactly once;
- no extra `case_id` appears;
- only schema-approved values are used;
- raw email, account, or monetary identifiers do not appear;
- the model did not add explanations before or after the JSONL.

If validation fails, give the LLM only the error list and ask it to regenerate that chunk once. If it fails again, retain the chunk for disagreement review.

## Combining the two passes

After both passes finish:

1. Combine chunk outputs for each pass in filename order.
2. Join Pass 1 and Pass 2 by `case_id`.
3. Treat exact agreement across all semantic fields as `LLM_CONSENSUS`.
4. Put every non-exact match into a disagreement file.
5. Do not vote independently by field if that creates a label combination proposed by neither model.
6. Send only disagreements to a third adjudication call, with both proposed label objects anonymized as A and B.
7. Preserve unresolved cases instead of forcing a label.

## Permitted use

Use the resulting labels to identify parser gaps, taxonomy problems, regression candidates, and cases requiring eventual domain review. Do not set `independent_review=true`, do not mark the existing corpus `training_eligible=true`, and do not report agreement with these labels as human-validated accuracy.

## Expected workload

Each pass contains the same 242 cases divided into small resumable chunks. A chunk should normally require only a few thousand tokens rather than the tens or hundreds of thousands required by the previous all-at-once workflow.

