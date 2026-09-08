# Semantic silver datasets v1 and reviewed v2

This dataset is a quality-gated import of the completed three-pass LLM labeling exercise. It is diagnostic evidence, not human ground truth and not training data.

## Files

- `data/semantic_silver_labels_v1.jsonl` — 242 records in canonical corpus order.
- `data/semantic_silver_manifest_v1.json` — counts, retained/excluded fields, and content digest.
- `scripts/import_llm_silver_labels.py` — reproducible importer from an adjudicated JSONL file.
- `data/semantic_silver_diagnostic_eval_v1.jsonl` — the 162 usable records with a frozen grouped diagnostic split.
- `data/semantic_silver_diagnostic_eval_manifest_v1.json` — split counts and intent support.
- `scripts/build_silver_diagnostic_eval.py` — reproducible group-stratified diagnostic split builder.
- `data/step5_semantic_review_adjudicated_v1.jsonl` — validated, de-anonymized disposition of all 86 focused-review cases.
- `data/step5_review_analysis_v1.json` — agreement, acceptance, provenance, and POC-comparison measurements.
- `data/semantic_reviewed_silver_labels_v2.jsonl` — consolidated 242-record semantic-silver dataset after Step 5.
- `data/semantic_reviewed_silver_manifest_v2.json` — v2 quality and assurance counts.
- `scripts/consolidate_step5_review.py` — exact-coverage, schema, option, semantic-contract, provenance, and consolidation importer.

## Retained labels

Only these semantic fields are retained from the selected LLM proposal:

- intents;
- scope;
- goal;
- output;
- audience;
- metric;
- subject selection;
- requested effect.

LLM-generated capability, decision, and missing-context fields are excluded. The deterministic runtime owns capability matching, clarification, decisions, functions, and DAG construction.

## Quality tiers

| Tier | Records | Use |
| --- | ---: | --- |
| `HIGH_CONFIDENCE_SILVER` | 73 | Diagnostic semantic evaluation |
| `MEDIUM_CONFIDENCE_SILVER` | 89 | Diagnostic semantic evaluation with tier reporting |
| `DIAGNOSTIC_ONLY_NO_COMPLETE_MAJORITY` | 72 | Disagreement and taxonomy analysis only |
| `DIAGNOSTIC_ONLY_CONTRACT_INVALID` | 3 | Contract/error analysis only |
| `EXCLUDED_UNRESOLVED` | 5 | No selected semantic label |

The usable semantic diagnostic pool is 162 records. Every record reports `independent_review=false` and `training_eligible=false`.

## Cross-model reviewed v2

The focused review returned all 86 issued cases: 85 selected an anonymized candidate and one remained unresolved. After deterministic semantic-contract validation, 84 are accepted cross-model silver, one is pending contract review, and one is pending unresolved. The consolidated v2 pool contains 206 usable semantic-silver records.

Cross-model independence is recorded as `independent_llm_review`; it is not treated as human review. All v2 records remain `human_reviewed=false`, `independent_review=false`, and `training_eligible=false`. Reviewer-reported capabilities and decisions are retained only in the audit-oriented adjudication file under an explicitly not-imported field; they never enter `semantic_labels` or runtime routing.

The v1 116/46 grouped split remains the frozen diagnostic evaluation view. It is not relabeled as a clean v2 holdout because the targeted Step 5 cases and their labels have now been inspected.

## Diagnostic evaluation split

The usable records are divided at the `split_group` level:

| Split | Records | Intended use |
| --- | ---: | --- |
| `development_diagnostic` | 116 | Inspect errors and propose parser changes |
| `heldout_diagnostic` | 46 | Re-run only after changes are frozen |

The deterministic stratifier targets held-out representation for every intent with at least two usable examples. Related source requests and paraphrases never cross splits. Some low-support intents remain unsuitable for standalone metrics, and the results must be described as agreement with silver labels rather than accuracy.

## Context terminology

The runtime uses two separate concepts:

- `context_requirements`: all external bindings required by a workflow;
- `clarification_required`: only request-specific facts that require advisor input.

Pending host context or governed retrieval can appear in requirements without producing `CLARIFY`. The deprecated `missing_context` output is temporarily equal to `clarification_required` for schema-5.x compatibility.

## Rebuild

```bash
python scripts/import_llm_silver_labels.py \
  --adjudicated /path/to/llm_adjudicated_silver_labels.jsonl \
  --corpus data/semantic_annotation_corpus.jsonl \
  --output data/semantic_silver_labels_v1.jsonl

python scripts/build_silver_diagnostic_eval.py \
  --silver data/semantic_silver_labels_v1.jsonl \
  --output data/semantic_silver_diagnostic_eval_v1.jsonl

python scripts/consolidate_step5_review.py \
  --results /path/to/step5_review_chunk_01_results.jsonl \
            /path/to/step5_review_chunk_02_results.jsonl \
            /path/to/step5_review_chunk_03_results.jsonl \
            /path/to/step5_review_chunk_04_results.jsonl \
            /path/to/step5_review_chunk_05_results.jsonl \
            /path/to/step5_review_chunk_06_results.jsonl \
            /path/to/step5_review_chunk_07_results.jsonl \
            /path/to/step5_review_chunk_08_results.jsonl
```

The importer requires exact case-ID coverage, strips routing fields, validates the selected semantic frame, assigns the tier, preserves semantic-only source votes, and writes the manifest.
