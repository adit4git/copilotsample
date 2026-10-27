---
name: concentrated-position-review
description: Reviews the client's single-company concentration against the guideline and the program limit and lists the options for advisor review. Use before a meeting or proposal when a name is above 10%.
metadata:
  type: business
  version: 1.0.0
  owner: Advice Methodology
  status: approved
  uses: [concentration-facts, concentration-rules, disclosure-policy]
  inputs: [client]
  outputs: [concentration, concentration_findings, position_summary]
  tags: [capability, concentration]
---

# Concentrated position review

A second capability that reuses skills from the selection process: the same concentration facts, the same concentration rules and the same disclosure policy, pointed at different text.

## Logic

```yaml
steps:
- use: concentration-facts
- use: concentration-rules
- compose:
    into: position_summary
    intro: 'Concentration review for {client.name}: the largest single-company exposure is {concentration.top_name} at {concentration.top_share:pct1} of the account (guideline {concentration.threshold:pct}).'
    when:
    - if: {"var": "concentration_findings.blocked"}
      say: Above the program limit. Refer to the concentrated-stock specialist before any program proposal.
    - if: {"and": [{">": [{"var": "concentration.top_share"}, {"var": "concentration.threshold"}]}, {"!": {"var": "concentration_findings.blocked"}}]}
      say: 'Options for advisor review: gift low-basis lots, a tax-managed SMA transition, direct indexing with the stock excluded, or a staged sale within the {client.gain_budget:money} gain budget.'
    - if: {">": [{"count": {"var": "concentration.over_threshold"}}, 1]}
      say: 'Also above the guideline: {concentration.over_threshold:list}.'
    - if: {"<=": [{"var": "concentration.top_share"}, {"var": "concentration.threshold"}]}
      say: No single company is above the guideline; no concentration action is needed.
    outro: Illustrative planning view for the advisor; not a recommendation.
- use: disclosure-policy
  with: {text_key: position_summary}
```

## Tests

```yaml
- name: Henderson gets options and the second name
  client_id: henderson
  expect:
  - {path: position_summary, contains: Options for advisor review}
  - {path: position_summary, contains: 'MSFT'}
- name: Okonkwo needs no action
  client_id: okonkwo
  expect:
  - {path: position_summary, contains: no concentration action}
```
