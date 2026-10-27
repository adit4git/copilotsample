---
name: write-selection-rationale
description: Writes the advisor-facing rationale for a shortlist - why each candidate fits, fees against the lower-cost alternative, flags and disclosures - and checks it against the disclosure policy. A sub-skill used by every selection capability.
metadata:
  type: business
  version: 1.1.0
  owner: Advice Methodology
  status: approved
  uses: [disclosure-policy]
  inputs: [client, request, shortlist, alternative]
  outputs: [rationale]
  tags: [sub-skill, writing]
---

# Write the selection rationale

Composes plain-language text from the run's results, never from memory, then hands it to the disclosure policy. In a production version this is where Claude would draft richer prose; the policy check would stay exactly the same.

## Logic

```yaml
steps:
- compose:
    into: rationale
    intro: 'Shortlist for {client.name} ({client.profile} profile): {request.amount:money} in {request.asset_class_label}. These are illustrative candidates for advisor review, not a recommendation to the client.'
    each: shortlist
    line: '{n}. {item.name} ({item.vehicle}, research {item.status}): fit score {item.fit_score:.0f}. Fee {item.fee_bps} bp, about {item.annual_fee:money} a year, {item.extra_vs_index:money} more than the index alternative. Tracking error {item.te}%, information ratio {item.ir}, {item.track_years}-year track record.'
    flag_line: ' Note: {flag_text}.'
    empty: No candidate passed the screens and policies. Consider the lower-cost alternative or widen the search.
    when:
    - if: {"var": "concentration_findings.findings.0"}
      say: 'Concentration: {concentration.top_name} is {concentration.top_share:pct1} of the account. Candidates that hold it would add to that exposure.'
    outro: 'Lower-cost alternative, always shown: {alternative.name} at {alternative.fee_bps} bp (about {alternative.annual_fee:money} a year). Figures are illustrative; suitability and the final choice remain the advisor''s decision.'
- use: disclosure-policy
  with: {text_key: rationale}
```

## Tests

```yaml
- name: Writes a compliant rationale with an empty shortlist
  client_id: henderson
  context:
    shortlist: []
    alternative: {name: Core Value Index Fund, fee_bps: 4, annual_fee: 2052}
  expect:
  - {path: rationale, contains: No candidate passed}
  - {path: blocked, count: 0}
```
