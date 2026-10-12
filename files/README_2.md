# Standalone HTML: CIO Model Fit delta

Base file: your `atlas-tour-standalone-scoped.html` **with the latest tax-personalization delta applied** (the one with the one-at-a-time Personalization options).

## Steps (in the folder with the HTML)
```bash
patch -p1 --dry-run < cio-model-fit.patch          # should say: patching file atlas-tour-standalone-scoped.html
patch -p1 < cio-model-fit.patch                    # 1. code (one block added just before </body>)
python3 apply_data_delta.py atlas-data-delta-cio.json atlas-tour-standalone-scoped.html   # 2. data (37 KB, additions only)
```
**Already applied the first CIO Model Fit patch?** Run `patch -p1 < cio-model-fit-update.patch` instead of step 1, and skip step 2 because the data hasn't changed.

If `patch` complains, open `cio-addon.html`, copy all of it, and paste it on the line just before `</body>` near the end of the HTML. It replaces any earlier CIO Model Fit block. The data script first checks that your embedded data is the tax-personalization version. If it isn't, apply the earlier delta first, or embed the full file instead: `python3 embed_data.py atlas-standalone-data.json atlas-tour-standalone-scoped.html`.

## What changes
- **New workspace, "CIO Model Fit"** (left nav, under Tax Overlay Desk), covering brokerage accounts in the Bridgewater, NJ market over $50K as of 8/31:
  - **Chart:** expected risk vs return of each account's current holdings (circle) joined to its matched CIO model (square), both from the 2026 CMA. Click a point to select an account.
  - **One row per account:** profile → CIO model and tier, actual 1y/3y return, standard deviation and Sharpe, expected return/risk/Sharpe for today's holdings and for the model, Sharpe gap, coverage, muni-proxy share, flags.
  - **Account detail:** the mapping chain (risk tolerance + time horizon → profile, compared with `allocation_profile_desc`; liquidity needs → tier; → model), expected vs actual table with tracking error, flags to review, allocation by CMA asset class (today vs model), and how every holding rolls up.
  - **Judgment calls panel:** margin, proxies, core style funds, unclassified holdings, snapshot timing, plus the assumptions added for the POC.
- **Today dashboard:** on the CIO alignment tile, households in the comparison (Kaplan, Montgomery, Brennan) carry a "vs CIO model" tag and open straight to their row and detail in CIO Model Fit. Households outside it (Henderson) still open the client page.
- **Ask Atlas:** "Show the CIO model fit for my brokerage accounts", "Compare Montgomery's account with its CIO model" (and the same for Fairbanks, Brennan and Kaplan). A new guide entry.
- **Tour:** a new step before the product shelf. 14 steps.

## Files
| File | What it is |
|---|---|
| `cio-model-fit.patch` | Code only: one block added before `</body>`. Never touches the data or PDF lines. |
| `cio-model-fit-update.patch` | Only for files that already have the first CIO Model Fit block: swaps in this version, with the Today-tile links. |
| `cio-addon.html` | The same block, for pasting by hand. |
| `atlas-data-delta-cio.json`, `apply_data_delta.py` | Data added since the tax-personalization version (37 KB): the CIO comparison for each advisor and 5 new Ask Atlas answers per advisor. Nothing existing changes. |
| `atlas-standalone-data.json`, `embed_data.py` | The complete data (3.3 MB), if you'd rather replace it outright. |
| `cio-model-fit-assumptions.md` | What the workspace calculates, the judgment calls, and every assumption behind the illustrative data. |

## How this was checked
- **Patches:** the patch plus data delta was applied to a copy of the tax-personalization file, and the update patch to a file carrying the first CIO block. Both give the same code and the same data as the file assembled directly. The bytes differ only in the timestamp gzip writes.
- **In the browser,** opening the file from disk in Chromium:
  - The CIO-tile households open their CIO Model Fit row; Henderson opens the client page.
  - All 14 tour steps land, and the new prompts open the right account.
  - Light, dark and phone widths render, and there are no console errors.
