# Step 5: focused semantic disagreement review

## Objective

Use a model family different from Claude Opus 4.x to review only the cases where the prior LLM passes, semantic contract, or deterministic POC materially disagree. Select the semantic interpretation best supported by the masked advisor request. Do not classify capabilities, context requirements, decisions, functions, or DAGs.

The result remains an LLM silver review, not human ground truth.

## Input packages

Extract `step5_disagreement_review_packages.zip`. It contains numbered child ZIPs such as `step5_review_chunk_01.zip`. Upload one child ZIP at a time to a new model family.

Each child ZIP contains:

- `TASK.md` — exact task and output filename;
- `review_cases.jsonl` — masked query, review reason codes, and anonymized candidate semantic frames;
- `controlled_vocabulary.json` — allowed values and short definitions;
- `review_output_schema.json` — required output structure.

Candidate IDs are randomized separately for every case. They do not reveal whether a proposal came from the POC or an earlier LLM pass.

## Recommended model/session settings

- Do not use Claude Opus 4.x for this review.
- Use a stateless session with memory, web search, tools, and retrieval disabled.
- Use temperature 0 or the lowest available setting.
- Upload only one numbered child ZIP at a time.
- Do not provide the original POC output, earlier labeling report, or source-provenance map.

## Copy/paste request

> Follow TASK.md exactly. Review each masked request against its anonymized semantic candidates and the controlled vocabulary. Return the requested JSONL file as an attachment, not inline. Do not infer capabilities, missing context, routing decisions, functions, or DAGs.

## Review method

For each case:

1. Read the masked request literally.
2. Identify positive requested work and ignore negated work.
3. Compare each candidate across intent set, scope, goal, output, audience, metric, subject selection, and requested effect.
4. Select a candidate only if the complete semantic frame is supported.
5. Use `REVISED_FRAME` if every candidate has a correctable semantic error.
6. Use `TAXONOMY_ISSUE` when the query is understandable but the controlled vocabulary cannot express it, or when identical semantic candidates imply different downstream routes.
7. Use `UNRESOLVED` when the wording genuinely permits materially different semantic interpretations.
8. Give only a short evidence-based rationale; do not provide chain-of-thought.

## Resolution values

| Resolution | Meaning |
| --- | --- |
| `SELECT_OPTION` | One supplied candidate is the best complete frame |
| `REVISED_FRAME` | A corrected controlled frame is required |
| `TAXONOMY_ISSUE` | The semantic vocabulary or downstream contract needs review |
| `UNRESOLVED` | The request itself is materially ambiguous |

For `SELECT_OPTION`, provide `selected_option_id` and copy that option exactly into `semantic_labels`. For `REVISED_FRAME`, use a null option ID and provide a complete controlled semantic frame. For `TAXONOMY_ISSUE` or `UNRESOLVED`, both may be null when no safe frame can be selected.

## Key interpretation rules

- Label only the advisor's requested work, not likely implementation steps.
- A client mention does not make the audience client-facing unless communication is requested.
- “Draft” is not “send.”
- “How do I enroll?” is read-only guidance; “enroll this client” is an operational action.
- Named, selected, prioritized, and filtered multi-client populations use `subject_set`; `subject_selection` preserves how the set is obtained.
- “Top holdings,” time periods, and materiality percentages are parameters, not intents.
- “Flag” without recurrence language may be a one-time screen; if the wording does not resolve one-time versus recurring, use `ambiguous_monitor` or `UNRESOLVED` as appropriate.
- Attachment presence does not prove that an instrument or period was resolved.
- Do not select a capability or try to make the semantics fit a desired route.

## Required output

Return one JSON object per input line:

```json
{
  "case_id": "base_114",
  "resolution": "SELECT_OPTION",
  "selected_option_id": "option_2",
  "semantic_labels": {
    "intents": ["research.security"],
    "scope": "subject_set",
    "goal": "screen_market_signals_for_client_holdings",
    "output": "holdings_signal_analysis",
    "audience": "advisor",
    "metric": "estimate_revisions",
    "subject_selection": "prioritized_clients",
    "requested_effect": "ambiguous_monitor"
  },
  "ambiguous_fields": ["requested_effect"],
  "confidence": "medium",
  "taxonomy_issue": null,
  "short_rationale": "The request identifies a client population and estimate-revision signal, but flagging mode is not explicit."
}
```

## Completion and return

Save each result using the filename specified in its `TASK.md`. If a chunk fails validation, retry only that chunk once. After all chunks are complete, return the files for deterministic validation and de-anonymization. Do not merge or average fields across candidates yourself.

