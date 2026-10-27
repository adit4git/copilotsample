---
name: suitability-policy
description: Suitability policy - a candidate's risk level must not exceed the client's risk profile, and nothing is proposed while a concentration block stands. Use in every selection and proposal.
metadata:
  type: policy
  version: 1.0.0
  owner: Compliance
  status: approved
  uses: []
  inputs: [client, '{params.over}']
  outputs: [policy_checks]
  tags: [compliance, suitability]
---

# Suitability policy

Applies the client's risk profile to every candidate. Suitability itself remains the advisor's determination; this policy removes candidates that could never be suitable.

## Logic

```yaml
over: '{params.over}'
params:
  over: ranked
constraints:
- id: SUIT-01
  must: {"<=": [{"var": "item.risk"}, {"var": "client.risk_max"}]}
  severity: block
  message: '{item.name}: risk level {item.risk} is above the client''s {client.profile} profile (at most {client.risk_max})'
- id: SUIT-02
  scope: run
  must_not: {"var": "concentration_findings.blocked"}
  severity: block
  message: A concentration block stands; refer to a specialist before proposing
```

## Tests

```yaml
- name: Risk 4 is too high for a Moderate client
  item: {risk: 4}
  expect: {ok: false, violation: SUIT-01}
- name: Risk 3 is suitable for a Moderate client
  item: {risk: 3}
  expect: {ok: true}
```
