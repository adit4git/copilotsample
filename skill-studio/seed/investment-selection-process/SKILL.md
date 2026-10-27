---
name: investment-selection-process
description: The CIO's standard selection process as an abstract parent - load the approved list, screen, score, check client fit, compare fees, apply suitability and approved-list policies, shortlist and explain. Extend it for a specific vehicle by naming the screen.
metadata:
  type: business
  version: 2.0.0
  owner: CIO Manager Research
  status: approved
  uses: [load-approved-list, '{params.screen}', score-candidates, client-fit-assessment, fee-comparison, suitability-policy, approved-list-policy, write-selection-rationale]
  inputs: [client, request]
  outputs: [shortlist, alternative, rationale]
  tags: [process, parent]
---

# Investment selection process (parent)

This skill is **abstract**: it defines the process once and cannot run on its own. Each child names its screen and vehicles, and inherits every step, so a change to the process (say, a new policy step) reaches every selection capability at once.

The order matters: policies run on the ranked list *before* the shortlist is taken, so a removed name is replaced by the next one rather than leaving a gap.

## Logic

```yaml
abstract: true
params:
  screen: base-eligibility-screen
  vehicles: [SMA, Fund]
  top: 3
steps:
- use: load-approved-list
  with: {vehicles: '{params.vehicles}'}
- use: '{params.screen}'
- use: score-candidates
- use: client-fit-assessment
- use: fee-comparison
- use: suitability-policy
- use: approved-list-policy
- take: {from: ranked, top: '{params.top}', into: shortlist}
- use: write-selection-rationale
```

## Tests

```yaml
- name: Abstract; tested through manager-sma-selection and fund-selection
```
