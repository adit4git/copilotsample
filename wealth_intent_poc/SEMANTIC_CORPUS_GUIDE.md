# Semantic annotation corpus guide

The corpus supports independent evaluation and, only after review gates pass, training a small local semantic model. It combines sanitized registry-author rewrites of source scenarios with synthetic meaning-preservation and contrast probes. It does not contain independently adjudicated truth today.

`data/semantic_annotation_corpus.jsonl` is canonical. `semantic_annotation_template.csv` is a reviewer worksheet. `semantic_annotation_schema.json` defines the full route fields and training gate. `semantic_corpus_manifest.json` records counts and a content digest.

Keep all variants of a source scenario in the same `split_group`. Three reviewers label independently without predictions or author hypotheses. Required labels cover intents, scope, goal, output, audience, metric, subject selection, effect, capability, decision and missing context. Preserve each initial annotation and adjudicate disagreements with a written rationale.

Authored rewrites and synthetic probes are excluded from training even after someone fills their labels. Training requires at least 30 complete cases with `advisor_email` or `template_prompt` provenance, three distinct reviewer records, adjudicated status and an explicit independence assertion. Production use needs a larger risk-stratified set; 30 is only a POC refusal floor.

The trainer uses locally abstracted text, word/bigram TF-IDF and regularized logistic classifiers. The resulting trusted-local joblib artifact can be loaded through `SklearnSemanticModelProvider` and passed to `route_request`. High-confidence model fields enter the deterministic semantic validator before capability matching. The parser remains the default because this release has zero eligible training records.

Do not load an untrusted joblib file. Do not treat model probability as authority. Compare parser-only and model-assisted routes on untouched grouped cases, with special attention to negation, action effect, client scope and false capability support.
