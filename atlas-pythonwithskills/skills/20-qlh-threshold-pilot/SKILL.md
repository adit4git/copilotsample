---
id: qlh-threshold-pilot
title: QLH harvest threshold pilot: 2.5%
team: Tax Services
owner: Tax-managed solutions desk
version: 0.3
kind: policy
workspaces: [tem, tax_desk]
prompts: [chat]
status: Pilot
summary: Lowers the loss that triggers a Quarterly Loss Harvesting sale from 5% to 2.5% for a pilot group, so more lots are harvested.
---
# QLH harvest threshold pilot: 2.5%

## What it changes
- **Tax personalization, QLH tab:** lots down 2.5% or more are harvested at the next run (was 5%). The lot chart, the headline and the counts all move.
- **Tax Overlay Desk:** the book-wide chart splits losses at 2.5%.
- **Ask Atlas:** answers quote the 2.5% threshold.

## Why
The tax desk wants to see what a lower trigger would do before asking for a term sheet change. A skill lets them pilot it in Atlas for one book, see the effect lot by lot, and switch it off again.

## Instructions for Atlas
The 2.5% QLH threshold is a pilot, not the term sheet. When you quote it, say "under the 2.5% pilot threshold".

## Source
Pilot parameter from the Tax Services desk. The QLH Term Sheet in force sets 5%.
