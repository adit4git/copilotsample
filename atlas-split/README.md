# Atlas standalone: every file and how to put them together

## Folder layout
```
atlas/
├── atlas.html
├── atlas-data.js        ← built from parts/ (step 2), or use the ready-made one
├── atlas-products.js
├── css/   (5 files)
├── js/    (14 files)
└── parts/ (16 files, only needed to rebuild atlas-data.js)
```
Open `atlas.html`. It loads everything else by relative path, so the names and folders must stay as shown.

## Steps
1. **Code:** put `atlas.html` in a folder, the 5 `.css` files in `css/` and the 14 `.js` files in `js/`.
2. **Data (`atlas-data.js`):** a text file with this first line, then the 16 part files pasted one per line in any order, then the last line:
   ```
   window.ATLAS_DATA_TEXT = String.raw`
   {"part":"core",...}
   {"part":"rules",...}
   {"part":"household-kaplan",...}
   ...
   `;
   ```
3. **Products (`atlas-products.js`):** use it as provided. It is your product list between `window.ATLAS_PRODUCTS = [` and `];`.
4. Open `atlas.html`. A banner at the top names anything missing, an incomplete line, or a missing file.

## Page and code
| File | Size | What it is |
|---|---|---|
| `atlas.html` | 5 KB | Page markup; links every file below in order |
| `css/core-1-tokens-shell-primitives.css` | 9 KB | Colours, type, light/dark tokens, app shell, buttons, pills |
| `css/core-2-today-tables-chat-client-tax.css` | 17 KB | Today, tables, Ask Atlas chat, client page, tax, agent trace |
| `css/core-3-workbenches-onboarding-mobile.css` | 19 KB | Vehicle picker, shelf, onboarding/tour, conversion map, sidebar, phone layout |
| `css/tax-personalization.css` | 13 KB | Tax personalization card, Tax Overlay Desk |
| `css/cio-model-fit.css` | 6 KB | CIO Model Fit |
| `js/standalone-api.js` | 23 KB | Reads the two data files, rebuilds records from the map, answers the app's `/api/*` requests |
| `js/app-01-foundation.js` | 19 KB | Icons, helpers, state, offering lists, verdict rendering, Explain popover, composition panel |
| `js/app-02-nav-today.js` | 9 KB | Navigation, titles, Today dashboard |
| `js/app-03-book.js` | 16 KB | Book of business |
| `js/app-04-ask-atlas.js` | 14 KB | Ask Atlas chat and agent actions |
| `js/app-05-draft-review.js` | 6 KB | Draft review |
| `js/app-06-transition-workbench.js` | 11 KB | Transition workbench |
| `js/app-07-vehicle-comparison.js` | 14 KB | Vehicle comparison, research matches |
| `js/app-08-product-shelf.js` | 7 KB | Product shelf |
| `js/app-09-conversion-map.js` | 6 KB | Brokerage-to-advisory conversion map |
| `js/app-10-onboarding-guide-tour.js` | 20 KB | How-to panels, Ask-about-this, Atlas guide, guided tour |
| `js/app-11-sidebar-router-events-boot.js` | 13 KB | Sidebar, router, events, start-up, PDF preview note |
| `js/tax-personalization.js` | 36 KB | Tax personalization workspace |
| `js/cio-model-fit.js` | 24 KB | CIO Model Fit workspace, Today-tile links |

## Data
| File | Size | What it is |
|---|---|---|
| `atlas-data.js` | 637 KB | The 16 parts below, wrapped (step 2) |
| `parts/core.json` | 9 KB | Date, advisors, offering catalog and policy status, sleeves, model portfolios, research content |
| `parts/rules.json` | 117 KB | The map: `_rules` (rule number → name and wording, 136), `_fields` (43), `_codes` (strategy types/services, 9), `_shapes` (record field lists, 163), `_texts` (shared text, 715) |
| `parts/household-montgomery.json` | 40 KB | Montgomery Family |
| `parts/household-henderson.json` | 39 KB | Henderson Family Trust |
| `parts/household-harlow.json` | 33 KB | Harlow Household |
| `parts/household-ferreira.json` | 34 KB | Ferreira Household |
| `parts/household-okoye.json` | 38 KB | Okoye Household |
| `parts/household-lindqvist.json` | 31 KB | Lindqvist Household |
| `parts/household-castellano.json` | 43 KB | Castellano Family |
| `parts/household-kaplan.json` | 35 KB | Kaplan Household |
| `parts/household-okonkwo.json` | 34 KB | Okonkwo Holdings LLC |
| `parts/household-fairbanks.json` | 36 KB | Fairbanks Family |
| `parts/household-brennan.json` | 38 KB | Brennan Household |
| `parts/household-ashford.json` | 43 KB | Ashford Household |
| `parts/advisor-dana.json` | 53 KB | Dana Whitfield: book of business, Ask Atlas answers, Tax Desk, CIO Model Fit, facts for other book households |
| `parts/advisor-marcus.json` | 13 KB | Marcus Webb: the same |
| `atlas-products.js` | 754 KB | 1,157 products, one per line |

Each household part covers that household's page, composition, transition workbench, conversion map (where it has one), draft note, eligibility verdicts, tax personalization and household facts.

## How records are written in the parts
| In the parts | Means | Looked up in |
|---|---|---|
| `["§28", 20, "IN", [...], "NONE"]` | A record: shape 28 = `field, op, expected, actual` | `_shapes` |
| `"rule_id": 120` | `taxManagedSMA.iap`, plus its wording, citations and effect | `_rules` |
| `"field": 20` | `account.program_enrollment` | `_fields` |
| `"¶0"` | Shared text, e.g. "This is a brokerage account that is not in the advisory program yet…" | `_texts` |
| `"AAPL|2"` | `AAPL|CUSTOM_MANAGED` (1 MANAGED … 6 PERSONALIZED_CLIENT, 7 TER, 8 QLH, 9 DTLH) | `_codes` |
