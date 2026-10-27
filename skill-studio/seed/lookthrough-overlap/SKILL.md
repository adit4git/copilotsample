---
name: lookthrough-overlap
description: Measures how much of each candidate's top holdings the client already owns and whether it adds to the client's concentrated stock. Use inside client-fit checks.
metadata:
  type: technical
  version: 1.0.0
  owner: Portfolio Analytics
  status: approved
  uses: []
  inputs: [client, '{params.over}', concentration]
  outputs: []
  tags: [look-through, client-fit]
---

# Look-through overlap with the client's holdings

Adds three fields to every candidate: the names it shares with the client (above 1% of the account), the share of the candidate's top holdings those names represent, and whether it holds the client's largest single name.

## Logic

```yaml
op:
  name: lookthrough_overlap
  params:
    over: '{params.over}'
    min_client_weight: 0.01
params:
  over: scored
```

## Tests

```yaml
- name: A manager holding NVDA adds to Henderson's concentration
  client_id: henderson
  context:
    concentration: {top_name: NVDA, top_share: 0.229}
    scored:
    - {name: Growth SMA, top_holdings: {NVDA: 0.09, MSFT: 0.08, KO: 0.02}}
  expect:
  - {path: scored.0.adds_to_concentration, equals: true}
  - {path: scored.0.overlap_pct, equals: 0.17}
```
