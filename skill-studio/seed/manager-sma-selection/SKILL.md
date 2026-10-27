---
name: manager-sma-selection
description: Shortlists SMA managers for a client and asset class using the CIO selection process, the SMA screen, client fit, fee comparison and compliance policies, and drafts the rationale. Use when an advisor needs SMA candidates for a proposal.
metadata:
  type: business
  version: 1.4.0
  owner: CIO Manager Research
  status: approved
  extends: investment-selection-process
  uses: [sma-eligibility-screen]
  inputs: [client, request]
  outputs: [shortlist, alternative, rationale]
  tags: [capability, selection, sma]
---

# Manager and SMA selection

A capability: one request ("SMA candidates for this client in this asset class") delivered by eleven skills of all four types working together.

It adds almost nothing of its own. It extends the parent process and sets three parameters: the SMA screen, SMAs only, and three names.

## Logic

```yaml
params:
  screen: sma-eligibility-screen
  vehicles: [SMA]
  top: 3
```

## Tests

```yaml
- name: Henderson large cap value - three names, none on Watch, none failing the screens
  client_id: henderson
  expect:
  - {path: shortlist, count: 3}
  - {path: shortlist, not_contains: Ashgrove Value Equity SMA}
  - {path: shortlist, not_contains: Fernhill Deep Value SMA}
  - {path: shortlist, not_contains: Alder Peak Value Select SMA}
  - {path: rationale, contains: not a recommendation}
- name: Okonkwo (tax-exempt, Moderate) - Fernhill passes the tax rule but fails suitability
  client_id: okonkwo
  expect:
  - {path: shortlist, not_contains: Fernhill Deep Value SMA}
  - {path: shortlist, count: 3}
```
