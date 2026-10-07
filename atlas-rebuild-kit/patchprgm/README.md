# Standalone HTML: conversion-map delta

Base file: your `atlas-tour-standalone-scoped.html`, the **404 KB** version (9 clients, built from the kit plus the tour patch).

## Steps (in the folder with the HTML)
```bash
patch -p1 --dry-run < conversion-map.patch      # should say: patching file atlas-tour-standalone-scoped.html
patch -p1 < conversion-map.patch                # 1. code
python3 embed_data.py atlas-standalone-data.json atlas-tour-standalone-scoped.html   # 2. data
```
Do both steps: the new code needs the new data (conversion maps, two new clients, Montgomery's added holdings).

## What changes
- **Conversion map** on the client page for brokerage prospects: each holding against the six program strategy types, with the rule and brochure page behind every cell; click a column to compare strategy types.
- **Tour:** new step 2 opens Montgomery's conversion map; step 3 (TET) is reframed as what happens if he picks a Managed Strategy. 11 steps.
- **Starter prompt:** "Open Montgomery's advisory conversion map". Chat can open the map for any prospect.
- **Clients in full:** 11 (adds Fairbanks Family and Brennan Household). Everyone else is still listed and shows a short note if opened.

## Files
| File | What it is |
|---|---|
| `conversion-map.patch` | Code only, 196 lines. Never touches the data or PDF lines, so it applies to your file as-is. |
| `atlas-standalone-data.json` | The complete new data for the file, plain JSON (2.7 MB). Replaces the embedded data. |
| `embed_data.py` | Puts the JSON into the HTML (gzip + base64, as the page expects). Fails loudly if the JSON is damaged. |
| `atlas-data-updates.json` | The raw rule, client and account-fact changes behind this feature, for the Python app's `app/data/*.json` (24 KB). |
