---
name: load-approved-list
description: Loads the CIO approved list of managers and funds for one asset class, optionally limited to SMAs or funds. Use as the first step of any manager, SMA or fund selection.
metadata:
  type: technical
  version: 1.0.0
  owner: CIO Manager Research
  status: approved
  uses: []
  inputs: [request]
  outputs: [candidates]
  tags: [data, selection]
---

# Load the approved list

Reads the approved list (managers and funds the CIO's research team covers) and keeps the rows for the asset class in the request. A caller can narrow the vehicles, for example to SMAs only.

This is a technical skill: it names one operation from the safe operations library and gives it parameters. It does not judge anything; screens and policies do that.

## Logic

```yaml
op:
  name: load_dataset
  params:
    dataset: managers
    where: {"and": [{"==": [{"var": "item.asset_class"}, {"var": "request.asset_class"}]}, {"in": [{"var": "item.vehicle"}, {"var": "params.vehicles"}]}]}
    into: candidates
params:
  vehicles: [SMA, Fund]
```

## Tests

```yaml
- name: Large cap value returns SMAs and funds
  client_id: henderson
  request: {asset_class: LCV}
  expect:
  - {path: candidates, count: 10}
- name: Growth list includes the closed manager (screens remove it later)
  client_id: kaplan
  expect:
  - {path: candidates, contains: Larkspur Growth SMA}
```
