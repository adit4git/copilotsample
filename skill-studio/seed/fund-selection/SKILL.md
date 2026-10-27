---
name: fund-selection
description: Shortlists mutual funds and ETFs for a client and asset class with the same CIO selection process, using the fund screen. Use when an advisor wants fund candidates or a lower-cost implementation.
metadata:
  type: business
  version: 1.0.0
  owner: CIO Manager Research
  status: approved
  extends: investment-selection-process
  uses: [fund-eligibility-screen]
  inputs: [client, request]
  outputs: [shortlist, alternative, rationale]
  tags: [capability, selection, fund]
---

# Fund selection

The second capability built on the same parent process. Only the screen, the vehicle and the number of names differ. Every other skill is reused unchanged.

## Logic

```yaml
params:
  screen: fund-eligibility-screen
  vehicles: [Fund]
  top: 2
```

## Tests

```yaml
- name: Henderson large cap value funds - the 62 bp fund is excluded
  client_id: henderson
  expect:
  - {path: shortlist, count: 2}
  - {path: shortlist, not_contains: Active Value Fund, institutional class}
```
