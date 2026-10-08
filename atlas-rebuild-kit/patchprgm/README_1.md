# Standalone HTML: tax personalization delta

Base file: your `atlas-tour-standalone-scoped.html` **after the conversion-map delta** (11 clients). The rail-collapse change is optional; this delta works with or without it.

## Steps (in the folder with the HTML)
`tax-personalization.patch` is **inclusive**: it carries the tax personalization card from the previous delta *and* this round's clean-up, so you need only this one patch on a file that has the conversion-map delta.
```bash
patch -p1 --dry-run < tax-personalization.patch     # should say: patching file atlas-tour-standalone-scoped.html
patch -p1 < tax-personalization.patch               # 1. code (one block added just before </body>)
python3 embed_data.py atlas-standalone-data.json atlas-tour-standalone-scoped.html   # 2. data
```
Do both steps. If `patch` complains, open `tem-addon.html`, copy all of it, and paste it on the line just before `</body>` near the end of the HTML; then run step 2. (If patch leaves an `.orig` file behind, delete it.)

Already applied the tax-personalization patch from the last delivery? Use `tax-personalization-update.patch` instead in step 1 (it swaps that block for the new one). The data hasn't changed since that delivery, so step 2 is optional in that case.

## What changes
- **Tax personalization card** on the client page, with five tabs:
  - **Coverage**: one bar per overlay (TER, QLH, DTLH) showing how much of the account it applies to, is superseded on, leaves to a TEM Style Manager's manager, or doesn't touch; then every position against all three overlays. Click any cell for the rule and the term sheet page.
  - **QLH lots**: every tax lot against the 5% loss threshold, the next 12 months of 91-day runs with their 30-day wash sale periods, and the losses QLH won't harvest, and why.
  - **TER lots**: oldest-first vs best-tax-lot sell order (checked against the TER term sheet's own example), short-term gain deferral, and the loss-first withdrawal order.
  - **DTLH**: what DTLH covers and is watching, plus the term sheet's example as a chart.
  - **Personalization options**: four selectable cards (overlays on the current strategy, Custom Managed sleeves, a TEM Style Manager Strategy, an Investment Manager Model that can hold one), each with its status for the client. Only the selected option's detail shows below; the matching TEM Style Manager Strategies appear only under option 3 and the six models only under option 4. It opens on the option that applies to the account now.
- **Tax Overlay Desk**: a new chart of harvestable losses lot by lot, split at the QLH 5% threshold.
- **No duplicate tax sections**: TER, QLH, DTLH and TEM Style Manager rows are removed from the old "Tax & overlay services" card, which becomes **Other tax services** (TET, DCA, charitable). The "TET-family service composition" card is gone; its TET rules now appear as a "With TET" note inside the personalization card. Each overlay's rule-engine verdict sits on its coverage bar and at the top of its tab, with the **i** button for the full rule trace and **Model transition** where it applies. TER's label drops "(legacy Atlas ID)".
- **Ask Atlas**: "Is Okoye eligible for DTLH?"-style questions about TER, QLH, DTLH or TEM Style Manager Strategies now open the personalization card on the matching tab; other offerings still open the eligibility screen.
- **Tour**: the Okoye and Lindqvist steps now land on the personalization card. The Castellano step becomes three steps (Castellano's sleeves, Okoye's lots, Ashford's tax-aware model). 13 steps.
- **Ask Atlas**: "Open Castellano's tax personalization", "Which of Okoye's lots would QLH harvest?", "Open Ashford's tax personalization", and a new guide entry.
- **Clients in full**: 12 (adds Ashford Household). Castellano and Okoye now have tax lots and sleeves.

## Files
| File | What it is |
|---|---|
| `tax-personalization.patch` | Code only: one block added before `</body>`. Never touches the data or PDF lines. |
| `tax-personalization-update.patch` | Only for files that already have the block from the last delivery: swaps it for the new one. |
| `tem-addon.html` | The same block, for pasting by hand. |
| `atlas-standalone-data.json` | The complete new data for the file, plain JSON (3.2 MB). Replaces the embedded data. |
| `embed_data.py` | Puts the JSON into the HTML (gzip + base64, as the page expects). Fails loudly if the JSON is damaged. |
| `atlas-data-updates.json` | The raw rule, client and account-fact changes behind this feature, for the Python app's `app/data/*.json`. |
| `tax-personalization-rules.md` | What was missing, every rule with its source page, and what is still not modeled. |

## How this was checked
The inclusive patch was applied to a copy of the file with different line numbers and different embedded data, and the update patch to a file carrying the previous block; after embedding the data, both results are byte-for-byte the file assembled directly. Opened from disk in Chromium: all 13 tour steps land on the right client and tab, the new prompts answer, the guide lists the new capability, the desk chart renders, out-of-scope clients still show the short note, no console errors.
