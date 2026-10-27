---
name: client-fit-assessment
description: Adjusts candidate scores for this client - overlap with what the client already owns and whether a candidate adds to the concentrated stock - then ranks them. A sub-skill used by every selection capability.
metadata:
  type: business
  version: 1.2.0
  owner: Advice Methodology
  status: approved
  uses: [concentration-facts, concentration-rules, lookthrough-overlap]
  inputs: [client, scored]
  outputs: [concentration, concentration_findings, ranked]
  tags: [sub-skill, client-fit]
---

# Client fit

A sub-skill: it is not useful alone, but every selection capability needs it. It combines two technical skills and one rules skill, then applies the fit adjustment:

fit score = score − overlap × 100 − 10 if the candidate holds the client's largest name.

## Logic

```yaml
params:
  overlap_penalty: 100
  concentration_penalty: 10
steps:
- use: concentration-facts
- use: concentration-rules
- use: lookthrough-overlap
  with: {over: scored}
- set:
    over: scored
    field: fit_score
    label: score less overlap and concentration penalties
    value: {"-": [{"-": [{"var": "item.score"}, {"*": [{"var": "item.overlap_pct"}, {"var": "params.overlap_penalty"}]}]}, {"if": [{"var": "item.adds_to_concentration"}, {"var": "params.concentration_penalty"}, 0]}]}
- rank: {over: scored, by: {"var": "item.fit_score"}, into: ranked, label: fit score}
```

## Tests

```yaml
- name: Kaplan's AAPL exposure lowers a growth manager that holds AAPL
  client_id: kaplan
  context:
    scored:
    - {name: Holds AAPL, score: 80, top_holdings: {AAPL: 0.07}}
    - {name: No overlap, score: 75, top_holdings: {KO: 0.01}}
  expect:
  - {path: ranked.0.name, equals: No overlap}
```
