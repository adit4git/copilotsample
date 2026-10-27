---
name: disclosure-policy
description: Checks client-facing or advisor-facing text for the required disclosures and for wording that is never allowed (guarantees, promises to outperform). Use on any generated text before it is shown.
metadata:
  type: policy
  version: 1.1.0
  owner: Compliance
  status: approved
  uses: []
  inputs: ['{params.text_key}']
  outputs: [policy_checks]
  tags: [compliance, wording]
---

# Disclosure policy

Works on whatever text the caller names (`text_key`), so the same policy checks a selection rationale, a position summary or a meeting brief. That is reuse through parameters rather than copies.

## Logic

```yaml
text_key: '{params.text_key}'
params:
  text_key: rationale
required_phrases: [illustrative, not a recommendation, advisor]
forbidden_phrases: [guarantee, will outperform, risk-free]
```

## Tests

```yaml
- name: Compliant text passes
  text: Illustrative candidates for advisor review, not a recommendation.
  expect: {ok: true}
- name: A guarantee is not allowed
  text: Illustrative, for the advisor, not a recommendation. We guarantee returns.
  expect: {ok: false, violation: PHRASE-BAN-1}
- name: Missing disclosure is caught
  text: Here are the best managers.
  expect: {ok: false, violation: PHRASE-REQ-1}
```
