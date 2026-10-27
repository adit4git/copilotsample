---
name: concentration-facts
description: Finds the client's largest single-company exposure, including look-through into funds, and every name above the guideline. Use before any concentration rule or review.
metadata:
  type: technical
  version: 1.0.0
  owner: Portfolio Analytics
  status: approved
  uses: []
  inputs: [client]
  outputs: [concentration]
  tags: [concentration, look-through]
---

# Concentration facts

Produces facts only: the largest name, its share of the account and the names above the threshold. Rules decide what those facts mean.

## Logic

```yaml
op:
  name: concentration_facts
  params:
    threshold: 0.10
    into: concentration
```

## Tests

```yaml
- name: Henderson's largest name is NVDA
  client_id: henderson
  expect:
  - {path: concentration.top_name, equals: NVDA}
  - {path: concentration.over_threshold, count: 2}
```
