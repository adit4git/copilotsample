# Atlas Advisor Workspaces — proof of concept (v6.2)

A FastAPI app with a Python rule engine and a browser front end. It finds brokerage households where an advisory relationship could genuinely help, explains why, compares routes, prepares a proposal for review and hands off to operations. The advisor decides at every step.

All data is illustrative and fictional. The app never sends, enrolls or trades anything, and the server stores nothing. Decisions live in the browser tab and travel with each request.

## Run it (Mac or Linux, about 2 minutes)

```bash
cd advisor-workspaces-app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000. Add `#tour` to the address to start the guided tour.

**Windows:** use `.venv\Scripts\activate` instead of the `source` line.

**Requirements:** Python 3.11 or later. The only outside request is Google Fonts; the page works without it.

## Test it

```bash
pip install -r requirements.txt
python -m pytest -q                       # 118 rule, screen and API tests (+5 browser tests if Playwright is installed)
pip install playwright && playwright install chromium   # optional: enables tests/test_ui_browser.py
```

The browser tests are skipped automatically when Playwright isn't installed.

## What is where

| Path | What it does |
|---|---|
| `app/data/*.json` | Illustrative data: market assumptions, funds and look-through, six households with tax lots, research, CIO views and returns, fees and strategies, approved content, events and the intelligence catalog |
| `app/data.py` | Loads the data; defines `State`, the advisor's decisions sent by the browser |
| `app/fmt.py` | Number formatting that matches the screen exactly |
| `app/engine.py` | Portfolio math: weights, expected return and volatility, tracking error, past events, look-through exposure, the tax-lot sale rule |
| `app/calc.py` | CIO targets and gaps, attribution, fees and cost options, the canonical investable cash, routing of each holding, event impact, multi-year sale plans |
| `app/rules.py` | One eligibility rule, readiness, the allocation finding, position and event rules, advisory value, lifecycle, firm intelligence |
| `app/pathway.py` | The advisory pathway: screens, six steps, buckets and amounts, cues and ranking, routes with feasibility and approvers, handoff, five stages, book view |
| `app/opportunities.py` | The shared opportunity list across the book (duplicates merged, grouped by lifecycle) |
| `app/views.py` | Screen data: everything one screen needs, as JSON |
| `app/checks.py` | The 30 rule-engine checks shown in the "Prototype · checks" dialog |
| `app/main.py` | FastAPI routes |
| `app/static/` | The front end: `index.html`, `styles.css`, `charts.js` (SVG charts), `app.js` (screens and interactions), `tour.js` (23-step guided tour) |
| `tests/` | pytest suite and the reference fixtures |

## API

| Method and path | Returns |
|---|---|
| `GET /api/health` | status and counts |
| `GET /api/meta` | labels and constants the page uses |
| `POST /api/view` | everything one screen needs. Body: `{route, state}`; the route says which screen, the state carries the advisor's decisions |
| `GET /api/book` | ranked households, all 27 opportunities, internal book view |
| `GET /api/household/{id}` | client case: amounts, buckets, value rows, six-step examples |
| `GET /api/household/{id}/routes` | transition routes and the stay-in-brokerage alternative |
| `GET /api/household/{id}/handoff` | handoff checklist and package |
| `GET /api/allocation/{id}?scope=&basis=&period=` | allocation finding, gaps, attribution, strategies, routing |
| `GET /api/proposal/{id}` | value case, cost options, objections, approved materials, story draft |
| `GET /api/position/{id}/{symbol}` | concentrated-position plan, decision tree, solutions |
| `GET /api/event/{id}` | event impact by household |
| `GET /api/intelligence` | firm intelligence catalog with book status |
| `GET /api/checks` | the 30 checks |

FastAPI's interactive docs are at http://localhost:8000/docs.

**`state` fields** (all optional):

| Field | Holds |
|---|---|
| `disp` | assessments and closures by item key |
| `choice` | recorded choices; `hh:<id>` holds the chosen route |
| `promo` | intelligence items added as opportunities |
| `o2` | proposal settings, including review status |
| `handed` | households handed off |
| `th` | concentration alert threshold |
| `intel_run` | analyzed catalog items |
| `clips_list` | talking points by household |

## How the screens map to the operating stages

- **Identify:** My book, a ranked table of households.
- **Analyze:** Client case.
- **Design:** Compare routes, which always includes Stay in brokerage.
- **Propose:** Client proposal.
- **Implement:** Implementation handoff.

The analysis views (allocation and performance, concentrated position, market and research with firm intelligence) and the six-step worked example are one click away from each household.

## How it was verified against the reference page

- **Rules, bit for bit:** `tests/fixtures/parity.json` was captured from the v6.2 reference page. It covers:
  - every rule result for all six households;
  - all 27 opportunities with their six steps;
  - ranking, book view, sale plans, events and the intelligence catalog.

  `tests/test_parity.py` requires the Python results to match bit for bit.
- **Screen text, word for word:** `tests/fixtures/screens.json` holds the proposal story drafts, findings, value rows, task-panel stories and event explanations.
- **Full screens:** during development, all 51 screen and household combinations were compared on visible text with every section expanded, along with 66 interactive steps (decisions, routes, proposal, handoff, filters, sliders, firm intelligence). Both matched the reference page.
- **Differences on purpose:** after closing an item with a reason, and after a threshold change switches the position, the reference page left the top bar stale (open count and breadcrumb). The app refreshes it. The specialist route for Delgado shows today's cost ($1,650 a year) instead of $0.
- **Rounding:** JavaScript adds numbers left to right. Python's `sum()` compensates rounding (3.12+) and can differ in the last bit, which flips how exact ties round on screen, so the engine uses `nsum` (plain addition) to match.

## Ground rules kept in the code

- No real firm, vendor, manager or program names.
- Every money figure is tagged observed, estimate, modeled or needs validation.
- A ranking or "starting point for advisor review" is a prompt, not a suitability conclusion.
- The lower-cost index-only option and Stay in brokerage are always shown.
- An assessment never closes work by itself.
- Implementation is never cleared without people.
