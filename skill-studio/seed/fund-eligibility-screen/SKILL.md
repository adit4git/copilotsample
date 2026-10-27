---
name: fund-eligibility-screen
description: Eligibility screen for mutual funds and ETFs. Extends the base screen with a fee cap and switches off the account-minimum rule. Use when shortlisting funds.
metadata:
  type: rules
  version: 1.0.0
  owner: Investment Policy
  status: approved
  extends: base-eligibility-screen
  uses: []
  inputs: []
  outputs: []
  tags: [screen, fund]
---

# Fund eligibility screen

Inherits the base rules, adds a fee cap, and **disables BASE-03**: funds have no account minimum.

## Logic

```yaml
params:
  max_expense_bps: 50
rules:
- id: BASE-03
  disable: true
- id: FUND-01
  when: {"!=": [{"var": "item.vehicle"}, "Fund"]}
  outcome: exclude
  message: '{item.name}: not a fund'
- id: FUND-02
  when: {">": [{"var": "item.fee_bps"}, {"var": "params.max_expense_bps"}]}
  outcome: exclude
  message: '{item.name}: costs {item.fee_bps} bp, above the {params.max_expense_bps} bp cap'
```

## Tests

```yaml
- name: Expensive fund is excluded
  item: {vehicle: Fund, fee_bps: 62}
  expect: {outcome: exclude, rule: FUND-02}
- name: A fund with a high minimum is not excluded (rule switched off)
  item: {vehicle: Fund, min_usd: 99000000, fee_bps: 5}
  expect: {outcome: pass}
```
