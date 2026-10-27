---
name: sma-eligibility-screen
description: Eligibility screen for separately managed accounts. Extends the base screen with SMA-only rules for track record and tax management, and a stricter minimum. Use when shortlisting SMA managers.
metadata:
  type: rules
  version: 1.2.0
  owner: Investment Policy
  status: approved
  extends: base-eligibility-screen
  uses: []
  inputs: []
  outputs: []
  tags: [screen, sma]
---

# SMA eligibility screen

Inherits every base rule, then:

- adds SMA-01 to SMA-03;
- **overrides BASE-03**: an SMA needs at least twice its minimum so the manager can build the full portfolio and harvest losses.

## Logic

```yaml
params:
  min_track_years: 3
  min_multiple: 2
rules:
- id: BASE-03
  when: {">": [{"*": [{"var": "item.min_usd"}, {"var": "params.min_multiple"}]}, {"var": "request.amount"}]}
  outcome: exclude
  message: '{item.name}: needs at least {params.min_multiple}× its {item.min_usd:money} minimum to build the full portfolio'
- id: SMA-01
  when: {"!=": [{"var": "item.vehicle"}, "SMA"]}
  outcome: exclude
  message: '{item.name}: not a separately managed account'
- id: SMA-02
  when: {"<": [{"var": "item.track_years"}, {"var": "params.min_track_years"}]}
  outcome: exclude
  message: '{item.name}: {item.track_years}-year track record, under {params.min_track_years} years'
- id: SMA-03
  when: {"and": [{"var": "client.taxable"}, {"var": "client.large_embedded_gains"}, {"!": {"var": "item.tax_managed"}}]}
  outcome: exclude
  message: '{item.name}: not tax-managed, and the client has large embedded gains to move in kind'
```

## Tests

```yaml
- name: Short track record is excluded
  item: {track_years: 2}
  expect: {outcome: exclude, rule: SMA-02}
- name: Not tax-managed is excluded for a taxable client with large gains
  item: {tax_managed: false}
  expect: {outcome: exclude, rule: SMA-03}
- name: Not tax-managed is fine for a tax-exempt client
  client_id: okonkwo
  item: {tax_managed: false}
  expect: {outcome: pass}
- name: The inherited Watch flag still applies
  item: {status: Watch}
  expect: {outcome: flag, rule: BASE-04}
- name: The overridden minimum rule needs twice the minimum
  item: {min_usd: 3000000}
  expect: {outcome: exclude, rule: BASE-03}
```
