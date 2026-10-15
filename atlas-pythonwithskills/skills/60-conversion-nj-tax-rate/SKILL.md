---
id: conversion-nj-tax-rate
title: Conversion tax estimate: include New Jersey tax
team: Tax Services
owner: Tax policy desk
version: 1.1
kind: policy
workspaces: [conversion]
prompts: [chat]
status: Approved
summary: Estimates entry tax at 34.55% (23.8% federal plus the 10.75% top New Jersey rate) for this New Jersey market, instead of the federal rate alone.
---
# Conversion tax estimate: include New Jersey tax

## What it changes
- **Conversion map:** every "estimated entry tax" figure, and the tax shown when you click a cell. Federal 23.8% becomes 34.55%.
- With the managed-first playbook on, a higher tax estimate can push a client past the 3.5% budget, so the suggested strategy type can change too. Turn both on to see the two skills combine: at the federal rate Atlas suggests Custom Managed for Montgomery; once New Jersey tax is counted, it no longer fits the budget.

## Why
Tax Services owns the rate assumptions. New Jersey taxes capital gains as ordinary income, so a federal-only estimate understates the cost of converting for clients in this market.

## Instructions for Atlas
When quoting conversion tax, say the estimate includes New Jersey tax at the top rate and is illustrative; the client's actual rate depends on their income.

## Source
Tax policy desk rate table (illustrative): 20% federal long-term rate, plus 3.8% net investment income tax, plus 10.75% New Jersey top rate.
