---
name: concentration-rules
description: Applies the single-company guideline (10%) and the program eligibility gate (50%) to the client's concentration facts. Use in any client-fit check or concentrated-position review.
metadata:
  type: rules
  version: 1.1.0
  owner: Investment Policy
  status: approved
  uses: [concentration-facts]
  inputs: [concentration]
  outputs: [concentration_findings]
  tags: [concentration]
---

# Concentration rules

Runs once for the client, not per candidate. It depends on **concentration-facts**; if those facts are not in the run yet, the runtime runs that skill first.

- A *condition* needs an advisor discussion.
- A *block* stops a program proposal and routes to a specialist.

## Logic

```yaml
into: concentration_findings
params:
  single_stock_limit: 0.10
  program_gate: 0.50
rules:
- id: CONC-01
  when: {">": [{"var": "concentration.top_share"}, {"var": "params.single_stock_limit"}]}
  outcome: condition
  owner: Advisor
  message: '{concentration.top_name} is {concentration.top_share:pct1} of the account, above the {params.single_stock_limit:pct} single-company guideline'
- id: CONC-02
  when: {">": [{"var": "concentration.top_share"}, {"var": "params.program_gate"}]}
  outcome: block
  owner: Specialist
  message: '{concentration.top_name} is above the {params.program_gate:pct} program limit: refer to a specialist'
- id: CONC-03
  when: {">": [{"count": {"var": "concentration.over_threshold"}}, 1]}
  outcome: flag
  owner: Advisor
  message: 'More than one name is above the guideline: {concentration.over_threshold:list}'
```

## Tests

```yaml
- name: Henderson has two names above the guideline
  client_id: henderson
  context:
    concentration: {top_name: NVDA, top_share: 0.229, over_threshold: [NVDA, MSFT]}
  expect: {rule: CONC-03}
- name: Above 50% blocks
  context:
    concentration: {top_name: COST, top_share: 0.583, over_threshold: [COST]}
  expect: {outcome: block, rule: CONC-02}
- name: A diversified client triggers nothing
  context:
    concentration: {top_name: MSFT, top_share: 0.04, over_threshold: []}
  expect: {outcome: pass}
```
