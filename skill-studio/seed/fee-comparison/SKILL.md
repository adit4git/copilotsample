---
name: fee-comparison
description: Works out each candidate's annual fee on the amount and compares it with the lower-cost index alternative for the asset class. Use before any shortlist is shown.
metadata:
  type: technical
  version: 1.0.0
  owner: Pricing
  status: approved
  uses: []
  inputs: [request, ranked]
  outputs: [alternative]
  tags: [fees, selection]
---

# Fee comparison with the lower-cost alternative

Adds the annual fee and the extra cost over the index alternative to every candidate, and records the alternative so it can always be shown to the client.

## Logic

```yaml
op:
  name: fee_comparison
  params:
    over: ranked
```

## Tests

```yaml
- name: Henderson's large cap value alternative is the index fund
  client_id: henderson
  context:
    ranked:
    - {name: Test SMA, fee_bps: 45}
  expect:
  - {path: alternative.name, equals: Core Value Index Fund}
  - {path: ranked.0.annual_fee, equals: 23085}
```
