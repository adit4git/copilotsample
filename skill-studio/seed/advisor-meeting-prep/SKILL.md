---
name: advisor-meeting-prep
description: Prepares an advisor's meeting brief by composing two capabilities - the concentrated position review and the manager and SMA selection - into one checked document. Use before a client review meeting.
metadata:
  type: business
  version: 1.0.0
  owner: Advice Methodology
  status: draft
  uses: [concentrated-position-review, manager-sma-selection, disclosure-policy]
  inputs: [client, request]
  outputs: [position_summary, shortlist, rationale, meeting_brief]
  tags: [capability, meeting]
---

# Advisor meeting preparation

A capability made of capabilities. It shows the deepest dependency chain in the registry: meeting prep → manager selection → selection process → client fit → concentration rules → concentration facts.

It is still a **draft**, to show the approval workflow: drafts can run here but are marked in every trace.

## Logic

```yaml
steps:
- use: concentrated-position-review
- use: manager-sma-selection
- compose:
    into: meeting_brief
    intro: 'Meeting brief: {client.name} - {client.next_meeting}. Prepared for advisor review; illustrative figures, not a recommendation.'
    when:
    - if: {"var": "position_summary"}
      say: '1. Concentration. {position_summary}'
    - if: {"var": "rationale"}
      say: '2. Manager candidates. {rationale}'
    - if: {"var": "manual_steps"}
      say: 'Manual steps outstanding: {manual_steps:list}.'
    outro: 'Checks run: {policy_checks:count} policy checks. Suitability remains the advisor''s determination.'
- use: disclosure-policy
  with: {text_key: meeting_brief}
```

## Tests

```yaml
- name: Henderson brief has both sections
  client_id: henderson
  expect:
  - {path: meeting_brief, contains: 1. Concentration.}
  - {path: meeting_brief, contains: 2. Manager candidates.}
```
