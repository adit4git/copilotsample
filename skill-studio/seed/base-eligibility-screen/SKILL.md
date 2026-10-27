---
name: base-eligibility-screen
description: The firm-wide eligibility screen every manager or fund must pass. Excludes terminated and closed strategies and minimums above the amount, and flags Watch-list names. Use directly, or extend it for a vehicle-specific screen.
metadata:
  type: rules
  version: 1.3.0
  owner: Investment Policy
  status: approved
  uses: []
  inputs: ['{params.over}', request]
  outputs: ['{params.into}']
  tags: [screen, parent]
---

# Base eligibility screen

The parent screen. Vehicle-specific screens extend it: they inherit these rules, can add their own, override one by giving the same id, or switch one off with `disable: true`.

An excluded candidate leaves the list with the rule that removed it. A flagged candidate stays, carrying the flag to later steps, so a policy can make the final call.

## Logic

```yaml
over: '{params.over}'
into: '{params.into}'
params:
  over: candidates
  into: eligible
rules:
- id: BASE-01
  when: {"==": [{"var": "item.status"}, "Terminated"]}
  outcome: exclude
  message: '{item.name}: terminated by research'
- id: BASE-02
  when: {"!": {"var": "item.accepting_new"}}
  outcome: exclude
  message: '{item.name}: closed to new accounts'
- id: BASE-03
  when: {">": [{"var": "item.min_usd"}, {"var": "request.amount"}]}
  outcome: exclude
  message: '{item.name}: minimum {item.min_usd:money} is above the amount {request.amount:money}'
- id: BASE-04
  when: {"==": [{"var": "item.status"}, "Watch"]}
  outcome: flag
  message: '{item.name} is on the research Watch list'
```

## Tests

```yaml
- name: Terminated is excluded
  item: {status: Terminated}
  expect: {outcome: exclude, rule: BASE-01}
- name: Watch is flagged, not excluded
  item: {status: Watch}
  expect: {outcome: flag, rule: BASE-04}
- name: Closed is excluded
  item: {accepting_new: false}
  expect: {outcome: exclude, rule: BASE-02}
- name: A recommended open manager passes
  item: {}
  expect: {outcome: pass}
```
