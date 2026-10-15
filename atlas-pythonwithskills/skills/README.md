# Team skills

A team skill is how a business or product team changes Atlas without a code release. It holds a rule, threshold, playbook, draft standard or phrasing, and it names its owner and version. Each skill is one folder here:

```
skills/<folder>/SKILL.md      required: who owns it, what it changes and why, in plain English
skills/<folder>/policy.json   optional: the exact changes, in a form Atlas applies
```

Atlas reads this folder when it starts. Turn a skill on or off in **Team Skills** (in the sidebar), or with `POST /api/skills/<id>` and the body `{"enabled": true}`. When a skill is on, its changes go into the live policy. When it is off, the original policy is restored exactly. Skills apply in folder-name order, so when two skills touch the same value, the later folder wins.

## SKILL.md

```
---
id: qlh-threshold-pilot
title: QLH harvest threshold pilot: 2.5%
team: Tax Services
owner: Tax-managed solutions desk
version: 0.3
kind: policy                       # policy | instructions | policy + instructions
workspaces: [tem, tax_desk]        # where it shows "Shaped by team skills"; also what "What it changes" measures
prompts: [chat]                    # which AI prompts get "Instructions for Atlas": chat, draft
status: Pilot                      # free text, shown on the card
summary: One sentence an advisor would understand.
---
# Title

## What it changes
## Why
## Instructions for Atlas          (optional: added to the AI prompts listed in `prompts`)
## Source
```

Workspace names: `eligibility`, `transition`, `conversion`, `tem` (tax personalization), `tax_desk`, `cio_fit`, `meeting_prep_draft`, `ask_atlas`, `cross_sell`.

## policy.json

### `patches`: change the policy data

```json
{"patches": [
  {"target": "rules", "op": "set",    "path": "tem_personalization.mechanics.qlh.loss_threshold", "value": 0.025, "why": "shown on the card"},
  {"target": "rules", "op": "merge",  "path": "conversion_policy", "value": {"tax_rate": 0.3455}},
  {"target": "rules", "op": "append", "path": "offerings.qlhOverlay.rules", "value": { "...a rule..." }},
  {"target": "rules", "op": "append", "path": "conversion_rules", "at": "start", "value": { "...a rule..." }},
  {"target": "cio",   "op": "set",    "path": "cma.classes[id=LCG].expected_return", "value": 0.060},
  {"target": "rules", "op": "remove", "path": "conversion_rules[rule_id=CONV.custom_managed_cd]"}
]}
```

- **Targets:**
  - `rules` is `app/data/rule-store.json`: offerings and their rules, composition rules, conversion rules and notes, `conversion_policy`, and `tem_personalization`.
  - `cio` is `app/data/cio-models.json`: the CMA, models, thresholds and scope.
  - `config` is `app/data/fa-and-facts.json`: advisor profiles, account facts and offering minimums.
- **Paths:** use dots between keys. `[key=value]` picks the one item in a list whose `key` equals `value`, and `[n]` picks by position.
- **Ops:**
  - `set` replaces a value, or adds it if it isn't there yet.
  - `merge` updates some keys of an object.
  - `append` adds to a list (`"at": "start"` puts it first, which matters for conversion rules, where the first match wins).
  - `remove` deletes one matched item.
- **Provenance:** rules and notes that a skill adds or changes are marked with the skill's id. The eligibility trace, conversion cells and "Worth raising" notes then show which team the rule came from.
- **Errors:** a patch that can't apply (a wrong path, for example) is skipped and shown on the skill's card. The app keeps running.

### Rules and notes the engine understands

- **Eligibility rule** (append to `offerings.<id>.rules`):
  - `rule_id`, `effect` (`REQUIREMENT`, `NEEDS_REVIEW`, `CONDITION`, `DISCLOSURE`, `SCOPE_CARVEOUT`) and `predicate`;
  - the predicate is either `{"field", "op", "value"}`, with ops `EQ`, `NEQ`, `IN`, `CONTAINS` or `GTE`, or an `AND` / `OR` / `NOT` of those;
  - then `failure_class` (`CLIENT_ELIGIBILITY` or `MANAGER_ADJUDICATION`), `message` and `source_doc`;
  - field names are the ones `derive_facts` in `app/data.py` produces, for example `account.advisory_value`.
- **Conversion rule** (`conversion_rules`): `rule_id`, `holding_kinds`, `strategy_types`, `outcome` (`HOLD`, `SELL`, `EXCHANGE`, `MOVE_OUT` or `REVIEW`), `message`, `source_doc`, `compile_source`.
- **Conversion cell note** (`conversion_cell_notes`): `rule_id`, `message`, and optional filters: `holding_kinds`, `strategy_types`, `outcomes`, `concentrated_only`, `gain_only`.
- **Conversion policy** (`conversion_policy`):
  - `tax_rate`, `tax_rate_label` and `high_cash_share`;
  - `recommend`: `{"method": "PREFER_WITHIN_TAX_BUDGET", "prefer": ["CUSTOM_MANAGED", "MANAGED"], "max_tax_share": 0.035, "reason": "..."}`.
- **Tax personalization consideration** (`tem_personalization.considerations`):
  - `rule_id`, `message`, `source_doc` and `when`;
  - `when` is one of `always`, `qlh_harvest`, `below_threshold_losses`, `new_money`, `dtlh_elected`, `ter_not_elected`, `federal_bracket_below` (with `value`) or `held_away_overlap`;
  - messages can use `{count}`, `{loss}` and `{threshold}`.
- **TEM Style Manager shortlist** (`tem_personalization.tem_sms_selection`): `intl_family_min_share`, `per_family` and `extra_families`.
- **CIO flags** (`thresholds` in `cio`): `concentration`, `low_coverage` and `muni_proxy_flag`.

### `draft`: add to meeting prep briefs

```json
{"draft": {"kind": "meeting_prep",
  "sections": [{"title": "Fees & conflicts", "after": "Concentration & risk", "body": "- Annual revenue {rev} on {aum}: about {fee_bps} bps all-in.\n- {eligible_note}"}],
  "checklist_title": "Before you send this",
  "rules": ["Tax figures are labeled illustrative"]}}
```

The template fields are: `{name}`, `{first}`, `{segment}`, `{aum}`, `{rev}`, `{fee_bps}`, `{risk}`, `{meeting_type}`, `{harvest}`, `{tax_alpha}`, `{unrealized}`, `{concentration}`, `{eligible_count}`, `{eligible_list}`, `{eligible_note}`, `{cio_score}` and `{cio_view}`.

The brief without a model gets the sections. With a model connected, the drafter is told to write them.

### `routes`: teach Ask Atlas new phrasing

```json
{"routes": [{"workspace": "conversion", "patterns": ["fee[- ]based"], "examples": ["Should the Montgomerys go fee-based?"]}]}
```

Patterns are case-insensitive regular expressions. The workspace can be `conversion`, `cio_fit` or `tem`. The examples are what "What it changes" runs, and with a model connected they are given to it as routing hints.

### `try`: shortcuts on the card

```json
{"try": [{"label": "Montgomery: conversion map", "workspace": "conversion", "household_id": "montgomery"},
         {"label": "Ask: ...", "workspace": "ask", "q": "Should the Montgomerys go fee-based?"}]}
```

## What a skill cannot do

A skill changes data and instructions. It cannot add a new kind of calculation, a new fact about a client, or a new screen. Those still need code. When a team asks for one, the code change adds a new setting, and from then on the team owns that setting through a skill. The conversion map's `recommend` method and the shortlist's `extra_families` were added that way.
