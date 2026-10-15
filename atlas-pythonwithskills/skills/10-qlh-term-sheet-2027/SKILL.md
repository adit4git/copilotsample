---
id: qlh-term-sheet-2027
title: QLH term sheet update (2027 preview)
team: Product & Compliance
owner: Overlay Services product lead
version: 1.0
kind: policy
workspaces: [eligibility, tem, tax_desk, cross_sell]
prompts: [chat]
status: Illustrative
summary: Adds a $1,000,000 account minimum and a held-away wash sale disclosure to Quarterly Loss Harvesting, the way a new term sheet would.
---
# QLH term sheet update (2027 preview)

## What it changes
- **Eligibility:** a new requirement on the QLH Overlay: the account must hold at least $1,000,000. Accounts under that become *Ineligible* for QLH, with this rule named in the trace.
- **Eligibility:** a new disclosure on every QLH verdict about wash sales against held-away accounts.
- **Tax personalization and Cross-sell:** both read the same verdicts, so they change with no other work.

## Why
This is how a term sheet change reaches advisors: the product team compiles the new clause into a rule, and every workspace that asks "is this client eligible for QLH?" gets the new answer the day the skill is turned on. Nobody edits the engine.

## Instructions for Atlas
When QLH eligibility comes up, mention that the QLH minimum is $1,000,000 under the 2027 term sheet preview, and that this is an illustrative preview, not the term sheet in force.

## Source
Illustrative. Written the way the Overlay Services team would compile a 2027 QLH term sheet. The minimum and the disclosure are assumptions for the demo.
