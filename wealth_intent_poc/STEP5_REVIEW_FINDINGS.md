# Step 5 independent LLM review — findings and disposition

## Outcome

All eight result files passed structural validation. They cover all 86 issued case IDs exactly once, remain in their assigned chunks, and contain no unexpected records. All 85 `SELECT_OPTION` records identify an issued anonymized option and reproduce its semantic frame exactly. One record was returned as `UNRESOLVED`.

The review is independent at the model-family level, but it is still LLM-generated silver evidence. It is not human ground truth, is not suitable for financial validation, and does not make any record training eligible.

| Result | Count |
| --- | ---: |
| Issued and returned | 86 |
| `SELECT_OPTION` | 85 |
| `UNRESOLVED` | 1 |
| Accepted semantic silver | 84 |
| Pending contract review | 1 |
| Pending unresolved | 1 |
| Human reviewed | 0 |
| Training eligible | 0 |

`base_114` remains pending because the selected frame has `scope=null`, which violates the runtime semantic contract. `base_106` remains unresolved because the request mixes proactive monitoring and proposal preparation without enough scope or output detail. Neither record is silently coerced into a valid label.

## What was consolidated

`data/semantic_reviewed_silver_labels_v2.jsonl` contains all 242 corpus records in canonical order. The 84 accepted Step 5 frames replace their earlier semantic labels. Unselected records retain their v1 status and labels. The two pending records have no selected v2 semantic frame.

The consolidated pool contains 206 usable semantic-silver records, up from 162. Every record remains:

- `training_eligible=false`;
- `human_reviewed=false`;
- `independent_review=false`, where this field continues to mean independent human review;
- free of imported capability IDs, routing decisions, context requirements, function choices, and DAGs.

An additional `independent_llm_review` field records whether Step 5 examined the case without implying human validation.

## Agreement and change profile

Among the 84 accepted cases, 45 exactly match the prior selected semantic frame and 39 change at least one field.

| Changed semantic field | Accepted cases |
| --- | ---: |
| Intents | 32 |
| Scope | 17 |
| Subject selection | 15 |
| Goal | 12 |
| Audience | 8 |
| Output | 7 |
| Metric | 5 |
| Requested effect | 5 |

The strongest repeated intent patterns were:

| Review pattern | Cases | Disposition |
| --- | ---: | --- |
| Add `research.cio` when CIO guidance supplies a proposal, analysis, or draft | 10 | Parser rule added, except pure guidance-version comparison |
| Treat holdings selection as an access/parameter concern rather than `portfolio.exposure` | 8 | Parser rule added; explicit exposure/concentration language still retains the exposure intent |
| Add `solution.match` to fit-oriented discovery or comparison | 6 | Fit-language rule broadened |
| Add `research.security` to an explicit interest-rate exposure signal | 1 | Narrow market-signal rule added |

The holdings change does not remove holdings access from the DAG. For a book- or subject-set-scoped security signal, the capability planner still resolves and authorizes the subject set, reads its holdings snapshot, and then applies the signal analysis. Semantic intent and data-access dependencies remain separate.

## Contract correction

The controlled vocabulary allowed `metric=null`, while the semantic validator rejected every book-level security signal without a registered metric. The high-confidence review of “Which clients are exposed to today's macro market moves?” showed why that was too strict: a broad market signal can be meaningful without mapping to one enumerated metric.

The validator now permits a null metric. The capability and context layers may still request market-signal evidence or screening criteria; they may not manufacture an unsupported metric label.

## POC comparison

On the 84 accepted targeted cases, exact semantic-frame agreement with the reviewed silver labels remains 29/84. This is expected because the changes were deliberately limited to repeated, contract-safe patterns rather than fitting every individual LLM choice.

Field agreement changed as follows:

| Field | POC 0.6.1 | POC 0.7.0 |
| --- | ---: | ---: |
| Intents | 44/84 | 44/84 |
| Scope | 54/84 | 54/84 |
| Goal | 71/84 | 72/84 |
| Output | 48/84 | 58/84 |
| Audience | 82/84 | 82/84 |
| Metric | 81/84 | 82/84 |
| Subject selection | 64/84 | 64/84 |
| Requested effect | 82/84 | 82/84 |

These are agreement measurements on a deliberately difficult, selected challenge set—not accuracy, production performance, or proof that the reviewer is correct.

## Changes deliberately not automated

- Scope and subject-selection choices were not globally fitted. The review treats similar “which clients” constructions inconsistently across `advisor_book`, `subject_set`, `entire_book`, and `criteria_filtered_book`.
- `research.change` was not expanded to rating-agency events. That intent currently means CIO-guidance version comparison; broadening it requires a taxonomy decision.
- `monitor.manage` was not removed merely because several reviewed frames combine `ambiguous_monitor` with no monitoring intent. With `monitor_mode=one_time`, the POC already removes monitoring and produces the same holdings-signal capability and DAG for equivalent population phrasings.
- Multi-intent capability gaps were not automatically converted into composition contracts. The Step 5 reviewer was explicitly prohibited from deciding capabilities, access paths, functions, or DAGs. Outcome owners must review any new composition contract separately.

## Reproducibility

Run `scripts/consolidate_step5_review.py` with the eight result files. The importer validates the issued schema and exact case coverage, verifies option identity, restores hidden source provenance, applies the semantic contract, writes the adjudicated review, builds the 242-record v2 dataset and manifest, and produces `data/step5_review_analysis_v1.json`.
