---
name: approved-list-policy
description: Compliance policy for any shortlist - no Watch or Terminated names, the lower-cost alternative is always shown, and a warning when a candidate adds to the client's concentrated stock. Use before a shortlist leaves the advisor's desk.
metadata:
  type: policy
  version: 2.0.0
  owner: Compliance
  status: approved
  uses: []
  inputs: ['{params.over}', alternative]
  outputs: [policy_checks]
  tags: [compliance, selection]
---

# Approved-list policy

A policy is a control, independent of the screens. The base screen only *flags* Watch-list names; this policy is what keeps them off a shortlist. If a screen is later changed or a new screen forgets a rule, the policy still holds.

- **AP-01 (blocks):** never shortlist a Watch or Terminated name.
- **AP-02 (blocks the run):** the lower-cost alternative must be present.
- **AP-03 (warns):** say so when a candidate holds the client's largest single name.

## Logic

```yaml
over: '{params.over}'
params:
  over: ranked
constraints:
- id: AP-01
  must_not: {"in": [{"var": "item.status"}, ["Watch", "Terminated"]]}
  severity: block
  message: '{item.name} is on the {item.status} list and cannot be shortlisted'
- id: AP-02
  scope: run
  must: {"!!": {"var": "alternative"}}
  severity: block
  message: The lower-cost alternative must be shown with any shortlist
- id: AP-03
  must_not: {"var": "item.adds_to_concentration"}
  severity: warn
  message: '{item.name} holds {concentration.top_name}, which would add to the client''s concentrated position'
```

## Tests

```yaml
- name: A Watch-list manager violates AP-01
  item: {status: Watch}
  expect: {ok: false, violation: AP-01}
- name: Adding to the concentrated name violates AP-03
  item: {adds_to_concentration: true}
  expect: {ok: false, violation: AP-03}
- name: A recommended manager is compliant
  item: {}
  expect: {ok: true}
```
