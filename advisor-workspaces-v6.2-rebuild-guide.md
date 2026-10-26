# Advisor Workspaces prototype v6.2: how to rebuild it

**Audience.** A Sonnet-class coding model, or a developer, with Python 3 or Node and ideally a headless browser for testing.

**Self-contained.** This file is everything needed. It holds the market and household data, the portfolio math, the charts, the design tokens and every screen. No other document, zip or data file is required.

**Goal.** Build **one self-contained HTML file**, `advisor-workspaces-v6.2.html`. It:
- runs offline with no server;
- covers six illustrative households;
- reproduces the reference figures in section 9.

**How this file works.**
- It describes the product, the data additions, the rules, the screens and the look in plain language, with small reference tables. There are no code dumps.
- Where something must be exact (data values, formulas, thresholds, the order of rules, wording the checks rely on), it says so.
- Everything else (spacing, exact colors of minor elements, the precise layout of secondary tables) is described well enough to rebuild faithfully. Small visual differences are fine.

**If this file was copied by OCR:**
- A misread character in prose is harmless; read for meaning.
- In tables, a number that looks wrong (`O.12`, `1O%`) is an OCR slip; fix it to the obvious value.
- Symbols that matter:
  - "≈" means approximately;
  - "→" means "changes to";
  - "−" is a minus sign;
  - "·" is a separator dot used in labels.

**Order of work** (details in section 10):
1. The data (section 3).
2. The base engine (4.0).
3. The rules (section 4), checked against section 9.
4. The shell, top bar and left list.
5. The landing page and the household flow.
6. The analysis views (allocation, concentrated position, client proposal, market and research).
7. The task panel, guided tour and in-page checks.
8. Polish and scans.

**Hard rules.**
1. **No firm names.** No real bank, broker, wealth-firm, vendor or fund-manager names anywhere: code, text, comments or file names.
   - Use "Atlas" for the product.
   - Use these neutral names:

     | Use | For |
     |---|---|
     | "Advisory program" | the fee-based program |
     | "Tax-efficient transition" | the move of appreciated holdings in kind, sold over time |
     | "Invest in steps" | staged investing of cash |
     | "Research" | the research department |
     | "CIO" | the house investment view |

   - Program acronyms never appear.
   - The managers in the data are fictional: Crestline, Beacon Hill, Ashcroft.
2. **Data comes from this guide.** Don't invent holdings, values, limits or thresholds.
3. **One file.** Inline the CSS and all scripts. The only external request allowed is the Google Fonts stylesheet, and the page must look right without it.
4. **Illustrative and human-led.** The top bar carries a "Prototype · checks" pill.
   - Every money figure is labelled as observed, estimate, modeled or needs validation.
   - Nothing is ever sent, enrolled or traded by the tool.
   - Decisions are "kept in this page only".
5. **Plain language.** Labels are sentence case and written for an advisor.
   - Internal use-case numbers never appear on screen.
   - Firm economics appear only in the internal management view.

---

## 1. What the product is

Advisor Workspaces is a book-level tool for an advisor. It finds brokerage households where an advisory relationship could genuinely help, explains why, and takes the advisor through five operating stages. The advisor decides at every stage.

**The five stages** (shown as a ladder in the task panel; each has "what the tool does", "what the advisor decides" and a "key control"):

| Stage | What the tool does | Advisor decides | Key control |
|---|---|---|---|
| Identify | Ranked opportunity with conversion potential | Advisor or specialist picks it up | Approved thresholds; data masking |
| Analyze | Household positioning against goals and the CIO target | Advisor decides to pursue | Approved content; lower-cost alternative shown |
| Design | Matches options on suitability and overlap; builds the transition plan | Advisor selects strategy and pace | Fit before tax; no tax estimate without basis |
| Propose | Builds the client story and proposal | Advisor approves and presents | Advisor review; never sent automatically |
| Implement | Prepares the enrollment, transition and invest-in-steps hand-off | Advisor and operations enroll | No autonomous execution or enrollment |

**The flow the advisor sees.**
1. **My book** (landing; Identify): one row per household, ranked by actionability. Each row shows why now, the amount potentially movable now, a starting route, the main constraint with its owner, and one next step.
2. **Household flow:** a four-step stepper.
   - *Client case* (Analyze);
   - *Compare routes* (Design);
   - *Client proposal* (Propose);
   - *Implementation handoff* (Implement).
3. **Analysis views**, one click away from a household:
   - Allocation and performance;
   - Concentrated position;
   - Market and research, with two tabs, *My book impact* and *Firm intelligence*;
   - the six-step worked example (Trigger → Size the gap → Value the gap → Match options → Plan transition → Client story).
4. **Task panel** (right): the current task, owner, what is blocking, status, and one primary action. The story draft, the full stage ladder and the decision controls sit in collapsed sections.
5. **Guided tour:** 23 steps that spotlight live screens.
6. **Prototype checks:** a dialog that runs 30 engine checks in the browser.

**Use cases behind the screens.** These are internal; never show the numbers. They appear on screen only as the plain "kind" labels below.

| id | Kind label (visible) | Where it comes from |
|---|---|---|
| 1 | Allocation gap | the allocation review |
| 2 | Embedded gains and losses | pathway screen |
| 3 | Individual bonds | pathway screen |
| 4 | Excess cash | pathway screen, or the allocation review when its finding is "cash" |
| 5 | High-cost funds | pathway screen |
| 7 | Advisory proposal | the value-story row |
| 8 | Concentrated stock | the concentrated-position review |
| 10 | Market or research event | events |
| 12 | Trading costs | pathway screen; no household triggers it |

**Principles that drive every screen.**
- Value first, then cost:
  - expected return at the CIO allocation and tax management come before the fee;
  - the lower-cost index-only option and "Stay in brokerage" are always shown;
  - staying is a legitimate, recordable outcome.
- One eligibility rule everywhere: a household with more than 50% in one security, counting direct holdings plus look-through into funds, is not eligible. It gets only the specialist route.
- One canonical investable-cash figure, used by routing, screens, paths, proposal and handoff.
- Every brokerage dollar sits in exactly one bucket: moves now, held for cost basis, kept in brokerage, or excluded. Bond calls and maturities are timing notes, never extra amounts.
- Account movement (in kind, at enrollment) is distinct from portfolio trading (repositioning over time).
- A ranking or a "starting point" is a prompt for review, not a suitability conclusion.
- An assessment does not close work. Closing needs an outcome, or a reason for stay, not suitable or defer.

---

## 2. Architecture

**Pieces, inlined in this order into one HTML file.** A short build script that reads them and writes the page is fine.

| Piece | Global | Contents |
|---|---|---|
| app.css + ws.css + ws2.css | — | tokens and base components, then the workspace components (section 6) |
| data | `DATA` | `const DATA = {...}`: section 3 |
| engine.js | `E` | portfolio math, `GROUPS`, `GROUP_OF`, `EQ` (4.0) |
| charts.js | `CH` | base SVG charts, shared tooltip, `CH.esc` (section 5) |
| wsx.js | `X` | CIO targets, gaps, attribution, fees, cash split, routing, event impact, sale plan; adds `CH.bands`, `CH.line`, `CH.tree` |
| wsy.js | `D` and constants | eligibility, readiness, the allocation finding, the position and event rules, value, firm intelligence, lifecycle, the shared queue |
| wsp.js | `P` and constants | the advisory pathway: screens, steps, transition, buckets and amounts, cues, ranking, paths, handoff, book, stages |
| ws_v2.js | — | formatting helpers, state `S`, base screens, left list, base task panel, top bar, events, `paint()` |
| wsv6.js | — | v6 overrides: landing, household flow, task panel, left list, decision context; its own events; calls `paint()` |
| wstour.js | — | guided tour; wraps the top bar and landing |
| wsz.js | — | prototype checks dialog |

**Page body:**
- `<header class="top" id="top">`;
- `<div class="layout">` holding:
  - `<nav class="card journey" id="journey" aria-label="Ranked list">`;
  - `<main class="card stage" id="stage">`;
  - `<aside class="card side" id="side" aria-label="Decision">`;
- `<div class="toast" id="toast" role="status">`.

**Title:** "Advisor workspaces · prototype v6.2". **Fonts:** Public Sans, Newsreader and IBM Plex Mono from Google Fonts (section 6).

**Rendering model.**
- There is no framework; build HTML with template strings and escape every data string.
- `paint()` = `paintTop()` + `paintMain()`.
- `paintMain()` does three things:
  - fills `#journey` from `entries()`;
  - fills `#stage` from the view function for `S.ws`;
  - calls `paintSide()`.
- The view functions per value of `S.ws`:

  | `S.ws` | View function |
  |---|---|
  | queue | QUEUE |
  | path | PATH |
  | ws1 | WS1 |
  | ws2 | WS2 |
  | ws3 | WS3 |
  | ws4 | WS4 |

- `paintMain()` keeps the scroll position. Navigation actions scroll to top.
- One delegated `click`, `change`, `input`, `keydown` and `toggle` listener set on `document` dispatches on `data-*` attributes (list in section 8).
- The v6 file adds its own click listener in the **capture** phase for its attributes, so they win over the base handlers.

**The override pattern.**
- Later files replace earlier functions by reassignment. Capture the old function first when it is still needed.
  - Example: keep the old queue as `_QUEUE`, then set a new `QUEUE` that calls `_QUEUE()` for the workflow view.
- So declare the base view functions in a way that allows reassignment: plain `function` declarations, or `let`.
- Overridden in v6:
  - `QUEUE` (landing);
  - `PATH` (household flow);
  - `WS2` (adds the stepper);
  - `decision`;
  - `paintSide`;
  - `entries`.
- The tour wraps `paintTop` (adds the Tour button) and `QUEUE` (adds the hint line).

**The memoized queue.** `allQueue()` is expensive, so cache it.
- The signature is the JSON of: the dispositions object `S.disp`, the keys of `S.promo`, the concentration alert threshold `S.o3.th`, and the household ids.
- Return the cached list while the signature is unchanged.
- `allQueue()`:
  1. builds the base queue `D.queue()`;
  2. appends any promoted firm-intelligence items;
  3. appends any rows the advisor assessed that are not in the base queue, so no recorded decision disappears;
  4. enriches each row (`P.enrich`);
  5. sorts closed rows last, then by priority, descending.

**State `S`** (in memory only; nothing persists across reloads):

| Field | Default | Meaning |
|---|---|---|
| ws | queue | current view |
| hid | henderson | current household |
| qv | hh | landing view: households, or "opp" for all opportunities (workflow) |
| hf | all | landing filter: all, discuss, waiting, propose, done |
| hstep | assess | household step: assess, paths, handoff (the proposal step is `ws = ws2`) |
| mgmt | false | show the internal management view on the landing |
| disp | {} | dispositions by key: `{status, set, reason, ws, at, closed?:{outcome, at}}` |
| choice | {} | recorded choices by key; for households `hh:<id>` holds the chosen route id |
| done, handed | {} | handoff checklist ticks by household; handed-off flags by household |
| o1 | scope brokerage, basis tactical, lvl L1, period 3Y | allocation view settings |
| o2 | {} | client proposal settings per household (created on first visit; see 7.8) |
| o3 | th = 0.10 | concentration alert threshold; per-position plan settings under the position key |
| o4 | view book, filter all, ft all, fb all, q "", sel null, hh null, all false | market and research settings |
| ev, pos, popp | n1, henderson:NVDA, null | current event, position, opportunity in the worked example |
| story | {} | talking points ("clips") per household |
| open | empty set | ids of expandable sections that are open |
| intelRun, watch, promo | {}, empty set, {} | firm intelligence: analyzed items, watchlist, items added as opportunities |

---

## 3. Data

### 3.0 Base market and household data

Type everything in section 3 into one object, `DATA`. Field names in `code` are the ones the rules use.

**Asset classes (`DATA.classes`, key → `{label, group, er, vol}`).** These are the capital market assumptions.

| Key | Label | Group | Expected return | Volatility |
|---|---|---|---|---|
| LCG | U.S. Large Cap Growth | Equity | 6.6% | 17.5% |
| LCV | U.S. Large Cap Value | Equity | 7.0% | 15.5% |
| SMID | U.S. Small/Mid Cap | Equity | 7.6% | 20.5% |
| INTL | International Developed Equity | Equity | 7.4% | 17.0% |
| EM | Emerging Markets Equity | Equity | 8.2% | 22.0% |
| UST | U.S. Treasuries | Fixed income | 4.1% | 5.5% |
| IGC | U.S. Corporates (IG) | Fixed income | 4.9% | 7.0% |
| HY | U.S. High Yield | Fixed income | 6.1% | 9.5% |
| CASH | Cash | Cash | 3.3% | 0.6% |
| HF | Hedge Funds | Alternatives | 5.8% | 7.5% |
| PE | Private Equity | Alternatives | 9.6% | 23.0% |

The risk-free rate (`DATA.rf`) is 3.3%.

**Correlations (`DATA.corr`).**
- Store them as keys "A|B" (for example "LCG|LCV" = 0.833).
- The matrix is symmetric, and the diagonal is 1.
- Each row lists that class's correlations in the column order LCG, LCV, SMID, INTL, EM, UST, IGC, HY, CASH, HF, PE:

| Row | LCG | LCV | SMID | INTL | EM | UST | IGC | HY | CASH | HF | PE |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LCG | 1.000 | 0.833 | 0.820 | 0.741 | 0.675 | −0.188 | 0.162 | 0.526 | −0.005 | 0.565 | 0.656 |
| LCV | 0.833 | 1.000 | 0.807 | 0.730 | 0.668 | −0.140 | 0.215 | 0.555 | 0.000 | 0.570 | 0.650 |
| SMID | 0.820 | 0.807 | 1.000 | 0.719 | 0.666 | −0.187 | 0.189 | 0.564 | −0.005 | 0.571 | 0.648 |
| INTL | 0.741 | 0.730 | 0.719 | 1.000 | 0.596 | −0.125 | 0.195 | 0.500 | 0.000 | 0.510 | 0.580 |
| EM | 0.675 | 0.668 | 0.666 | 0.596 | 1.000 | −0.166 | 0.174 | 0.506 | −0.005 | 0.489 | 0.546 |
| UST | −0.188 | −0.140 | −0.187 | −0.125 | −0.166 | 1.000 | 0.713 | 0.077 | 0.095 | −0.058 | −0.163 |
| IGC | 0.162 | 0.215 | 0.189 | 0.195 | 0.174 | 0.713 | 1.000 | 0.480 | 0.080 | 0.265 | 0.170 |
| HY | 0.526 | 0.555 | 0.564 | 0.500 | 0.506 | 0.077 | 0.480 | 1.000 | 0.020 | 0.520 | 0.495 |
| CASH | −0.005 | 0.000 | −0.005 | 0.000 | −0.005 | 0.095 | 0.080 | 0.020 | 1.000 | 0.005 | −0.005 |
| HF | 0.565 | 0.570 | 0.571 | 0.510 | 0.489 | −0.058 | 0.265 | 0.520 | 0.005 | 1.000 | 0.477 |
| PE | 0.656 | 0.650 | 0.648 | 0.580 | 0.546 | −0.163 | 0.170 | 0.495 | −0.005 | 0.477 | 1.000 |

**Past events (`DATA.scenarios`, `{id, label, window}`):**

| id | Label | Window |
|---|---|---|
| dotcom | Technology bubble | 24 Mar 2000 to 9 Oct 2002 |
| gfc | Housing and financial crisis | 9 Oct 2007 to 9 Mar 2009 |
| covid | COVID disruption | 19 Feb 2020 to 23 Mar 2020 |
| y2022 | 2022 rate shock | Calendar year 2022 |

**Sector names (`DATA.sectors`):**

| Key | Name |
|---|---|
| TECH | Information Technology |
| COMM | Communication Services |
| DISC | Consumer Discretionary |
| FIN | Financials |
| HLTH | Health Care |
| INDU | Industrials |
| STAP | Consumer Staples |
| ENER | Energy |
| UTIL | Utilities |
| REAL | Real Estate |
| MATL | Materials |

**Equity benchmark sector weights:** TECH 27.0%, FIN 17.0%, DISC 11.0%, INDU 11.0%, HLTH 9.0%, COMM 8.0%, STAP 6.0%, ENER 4.0%, MATL 3.5%, UTIL 2.5%, REAL 2.0%.

**Style cells:** LV, LB, LG, MV, MB, MG, SV, SB, SG (Large/Mid/Small × value/blend/growth).

**Dates:**
- `DATA.as_of`: positions 2026-10-15, research 2026-10-15, look-through 2026-09-30.
- `business_date`: 2026-10-16.
- The page's "today" for screens is 2026-10-24 (`DATA.pathway.as_of`, 3.11).

**Disclosures (`DATA.disclosures`).** Show these verbatim where the figure is used.
- **history:** "Historical stress results apply rounded, approximate index moves from past events to today's holdings. They are illustrative, are not a forecast, and do not include fees, rebalancing or the path within each window. Individual securities, especially single stocks, can fall much further than their sector or asset class did. Past performance does not guarantee future results."
- **tax:** "Tax figures are illustrative estimates from cost basis on file and the rates shown; they are not tax advice. Lots without cost basis are excluded. Confirm with the client's tax advisor before trading."
- **research:** "Research ratings, fund reports and manager briefings shown are illustrative demo content. Alternatives are surfaced for advisor consideration, not as recommendations to the client."

**Fund shelf (`DATA.funds`, keyed by symbol).**
- Fields: sym, name, kind (etf or mf), classes, expense_bps, yield, holdings_count, top10_share, muni (true for MUB and VTEB), `report` (`{view, summary, strengths[], risks[], date}`, or null), `scret` (returns in the four past events, `{dotcom, gfc, covid, y2022}`), and the look-through fields below.
- Only `report.view` drives the rules. Write a neutral one-sentence summary for each report.

| Sym | Name | Kind | Classes | Cost (bp) | Yield | Holdings | Top-10 | Research view | Past events (dotcom / gfc / covid / 2022) |
|---|---|---|---|---|---|---|---|---|---|
| VTI | US Total Market ETF | etf | LCG 45%, LCV 45%, SMID 10% | 3 | 1.2% | 3600 | 31% | Recommended | −0.473 / −0.551 / −0.340 / −0.182 |
| ITOT | Core S&P Total US Stock ETF | etf | LCG 45%, LCV 45%, SMID 10% | 3 | 1.2% | 2500 | 33% | Recommended | −0.473 / −0.551 / −0.340 / −0.182 |
| VOO | S&P 500 ETF | etf | LCG 50%, LCV 50% | 3 | 1.2% | 503 | 37% | Recommended | −0.47 / −0.55 / −0.34 / −0.18 |
| IVV | Core S&P 500 ETF | etf | LCG 50%, LCV 50% | 3 | 1.2% | 503 | 37% | no report | −0.47 / −0.55 / −0.34 / −0.18 |
| IDX-I | S&P 500 Index Fund, institutional class | mf | LCG 50%, LCV 50% | 4 | 1.2% | 503 | 37% | Recommended | −0.473 / −0.551 / −0.340 / −0.182 |
| ESGV | ESG US Equity ETF | etf | LCG 50%, LCV 40%, SMID 10% | 9 | 1.0% | 1400 | 36% | Neutral | −0.50 / −0.56 / −0.33 / −0.22 |
| QQQ | Nasdaq-100 ETF | etf | LCG 100% | 20 | 0.6% | 101 | 52% | Neutral | −0.62 / −0.52 / −0.31 / −0.26 |
| VGT | Info Tech ETF | etf | LCG 100% | 9 | 0.5% | 320 | 60% | Neutral | −0.80 / −0.53 / −0.30 / −0.28 |
| ARKK | Innovation ETF | etf | LCG 60%, SMID 40% | 75 | 0.0% | 35 | 62% | Not recommended | −0.50 / −0.54 / −0.32 / −0.23 |
| VUG | Growth ETF | etf | LCG 100% | 4 | 0.5% | 170 | 60% | Recommended | −0.60 / −0.54 / −0.32 / −0.27 |
| SCHG | US Large-Cap Growth ETF | etf | LCG 100% | 4 | 0.4% | 230 | 58% | no report | −0.60 / −0.54 / −0.32 / −0.27 |
| LCG-A | Large-Cap Growth Fund, Class A (front-end load) | mf | LCG 100% | 95 | 0.1% | 70 | 55% | Neutral | −0.599 / −0.539 / −0.319 / −0.268 |
| SCHD | US Dividend Equity ETF | etf | LCV 100% | 6 | 3.7% | 100 | 41% | Recommended | −0.28 / −0.50 / −0.37 / 0.03 |
| DGRO | Core Dividend Growth ETF | etf | LCV 70%, LCG 30% | 8 | 2.2% | 410 | 27% | no report | −0.35 / −0.54 / −0.35 / −0.08 |
| VTV | Value ETF | etf | LCV 100% | 4 | 2.3% | 330 | 22% | Recommended | −0.30 / −0.56 / −0.37 / −0.05 |
| LCV-I | US Large Cap Value Fund (Institutional shares) | mf | LCV 100% | 55 | 2.0% | 90 | 30% | Recommended | −0.299 / −0.561 / −0.370 / −0.054 |
| IJH | Core S&P Mid-Cap ETF | etf | SMID 100% | 5 | 1.4% | 400 | 7% | Recommended | −0.29 / −0.59 / −0.38 / −0.12 |
| VXUS | Total International Stock ETF | etf | INTL 75%, EM 25% | 5 | 2.9% | 8500 | 10% | Recommended | −0.472 / −0.610 / −0.325 / −0.155 |
| VEA | Developed Markets ETF | etf | INTL 100% | 3 | 3.0% | 3900 | 11% | Recommended | −0.48 / −0.61 / −0.33 / −0.14 |
| IEFA | Core MSCI EAFE ETF | etf | INTL 100% | 7 | 3.0% | 2700 | 12% | Recommended | −0.480 / −0.610 / −0.330 / −0.140 |
| VWO | Emerging Markets ETF | etf | EM 100% | 7 | 3.0% | 5900 | 20% | Recommended | −0.45 / −0.61 / −0.31 / −0.20 |
| IEMG | Core MSCI Emerging Markets ETF | etf | EM 100% | 9 | 2.8% | 2900 | 22% | Recommended | −0.45 / −0.61 / −0.31 / −0.20 |
| VNQ | Real Estate ETF | etf | LCV 50%, SMID 50% | 13 | 3.8% | 155 | 47% | Neutral | 0.35 / −0.70 / −0.41 / −0.26 |
| BAL-C | Balanced Income Fund, Class C (12b-1 fee) | mf | LCG 30%, LCV 30%, UST 12%, IGC 16%, HY 12% | 170 | 2.5% | 400 | 25% | Not recommended | −0.219 / −0.355 / −0.237 / −0.163 |
| AGG | US Aggregate Bond ETF | etf | UST 60%, IGC 40% | 3 | 4.1% | 12000 | — | Recommended | 0.276 / 0.072 / −0.006 / −0.138 |
| BND | US Bond Market ETF | etf | UST 60%, IGC 40% | 3 | 4.1% | 11000 | — | Recommended | 0.276 / 0.072 / −0.006 / −0.138 |
| LQD | Investment Grade Corporate Bond ETF | etf | IGC 100% | 14 | 5.0% | 2900 | — | Neutral | 0.24 / −0.03 / −0.09 / −0.16 |
| VGSH | Short-Term Treasury ETF | etf | UST 100% | 4 | 3.9% | 95 | — | Recommended | 0.30 / 0.14 / 0.05 / −0.12 |
| MUB | National Muni Bond ETF | etf | IGC 100% | 5 | 3.1% | 6000 | — | Recommended | 0.220 / 0.010 / −0.090 / −0.085 |
| VTEB | Tax-Exempt Bond ETF | etf | IGC 100% | 3 | 3.1% | 9000 | — | Recommended | 0.22 / 0.01 / −0.09 / −0.09 |

**Stocks** are also entries in `DATA.funds`, with kind "stock", a `sector` (not `sectors`), no expense ratio and no report:

| Sym | Name | Sector |
|---|---|---|
| NVDA | NVIDIA Corp | TECH |
| MSFT | Microsoft Corp | TECH |
| AAPL | Apple Inc | TECH |
| AMZN | Amazon.com Inc | DISC |
| GOOG | Alphabet Inc | COMM |
| TSLA | Tesla Inc | DISC |
| COST | Costco Wholesale Corp | STAP |
| JPM | JPMorgan Chase | FIN |
| PFE | Pfizer Inc | HLTH |
| CVX | Chevron Corp | ENER |
| CVS | CVS Health | HLTH |
| JNJ | Johnson & Johnson | HLTH |
| PG | Procter & Gamble | STAP |
| KO | Coca-Cola Co | STAP |
| UNH | UnitedHealth Group | HLTH |
| HD | Home Depot | DISC |
| INTC | Intel Corp | TECH |
| TXN | Texas Instruments | TECH |
| QCOM | Qualcomm Inc | TECH |
| ADI | Analog Devices | TECH |
| MRK | Merck & Co | HLTH |
| ABBV | AbbVie Inc | HLTH |
| CI | Cigna Group | HLTH |
| ELV | Elevance Health | HLTH |
| BKNG | Booking Holdings | DISC |
| LOW | Lowe's Companies | DISC |

**Classes:** `{LCG: 1}` for the growth names (NVDA, MSFT, AAPL, AMZN, GOOG, TSLA, COST, BKNG); `{LCV: 1}` for the rest.

**Past-event rows** (dotcom / gfc / covid / 2022):

| Row | dotcom | gfc | covid | 2022 |
|---|---|---|---|---|
| A | −0.80 | −0.53 | −0.30 | −0.28 |
| B | −0.40 | −0.57 | −0.34 | −0.37 |
| C | −0.70 | −0.50 | −0.30 | −0.40 |
| D | +0.05 | −0.30 | −0.24 | −0.006 |
| E | −0.25 | −0.38 | −0.28 | −0.02 |
| F | −0.20 | −0.80 | −0.43 | −0.105 |
| G | −0.25 | −0.53 | −0.57 | +0.66 |

**Yield, style-box cell and past-event row per stock:**

| Stock | Yield | Style | Row |
|---|---|---|---|
| NVDA | 0.03% | LG | A |
| MSFT | 0.7% | LG | A |
| AAPL | 0.4% | LG | A |
| AMZN | 0 | LG | B |
| GOOG | 0.4% | LG | C |
| TSLA | 0 | LG | B |
| COST | 0.5% | LG | D |
| JPM | 2.1% | LV | F |
| PFE | 6.5% | LV | E |
| CVX | 4.5% | LV | G |
| CVS | 4.2% | LV | E |
| JNJ | 3.1% | LV | E |
| PG | 2.5% | LV | D |
| KO | 2.9% | LV | D |
| UNH | 1.7% | LB | E |
| HD | 2.3% | LB | B |
| INTC | 0 | LV | A |
| TXN | 2.9% | LB | A |
| QCOM | 2.1% | LB | A |
| ADI | 1.7% | LB | A |
| MRK | 3.5% | LV | E |
| ABBV | 3.4% | LB | E |
| CI | 1.9% | LV | E |
| ELV | 1.6% | LV | E |
| BKNG | 0.7% | LG | B |
| LOW | 1.9% | LB | B |

**Fund look-through** (weights are fractions of the fund). It drives single-name exposure and event impact.

- **Total US market** (VTI, ITOT; also use for ESGV):
  - top holdings: NVDA .064, MSFT .057, AAPL .056, AMZN .034, GOOG .033, META .025, AVGO .021, TSLA .018, JPM .013, COST .009, UNH .007, JNJ .007, PG .007, HD .007;
  - style box: LV .30, LB .30, LG .30, MB .06, SB .04.
- **S&P 500** (VOO, IVV, IDX-I):
  - top holdings: NVDA .075, MSFT .067, AAPL .066, AMZN .040, GOOG .039, META .029, AVGO .025, TSLA .021, JPM .015, COST .010, UNH .008, JNJ .008, PG .008, HD .008;
  - style box: LV .32, LB .33, LG .35.
- **Broad US sectors** (all of the above, and BAL-C): TECH .33, FIN .13, DISC .105, COMM .10, HLTH .09, INDU .085, STAP .05, ENER .03, UTIL .025, REAL .02, MATL .02.
- **Balanced** (BAL-C): the S&P 500 names at 0.6 of those weights (NVDA .045, MSFT .040, AAPL .040, and so on).
- **Growth** (VUG, SCHG, LCG-A, QQQ):
  - top holdings:

    | Fund | Top holdings |
    |---|---|
    | VUG (also SCHG) | NVDA .12, MSFT .11, AAPL .11, AMZN .065, GOOG .06, META .045, AVGO .04, TSLA .035, COST .015 |
    | LCG-A | MSFT .09, NVDA .08, AAPL .07, AMZN .06, GOOG .05, META .04 |
    | QQQ | NVDA .095, MSFT .085, AAPL .08, AMZN .055, GOOG .053, AVGO .05, META .038, TSLA .03, COST .025 |

  - sectors: TECH .50, DISC .17, COMM .13, HLTH .06, INDU .05, FIN .05, STAP .02, MATL .01, REAL .01 (QQQ: TECH .52, COMM .16, DISC .14, others small);
  - style box: LG .85, LB .10, MG .05.
- **Large value** (VTV, LCV-I; DGRO similar):
  - top holdings: JPM .035, JNJ .022, PG .02, HD .02, CVX .016, UNH .015, KO .013, PFE .01, CVS .006, INTC .006;
  - sectors: FIN .23, HLTH .16, INDU .14, TECH .10, STAP .09, ENER .08, UTIL .05, DISC .05, COMM .04, MATL .04, REAL .02;
  - style box: LV .80, LB .15, MV .05.
- **Dividend** (SCHD):
  - top holdings: CVX .042, KO .041, PFE .04, HD .04;
  - sectors: ENER .19, STAP .19, HLTH .16, INDU .12, FIN .09, TECH .09, DISC .08, COMM .04, MATL .03, UTIL .01.
- **Mid cap** (IJH): sectors INDU .20, FIN .17, DISC .14, TECH .11, HLTH .09, REAL .08, MATL .06, STAP .05, ENER .05, UTIL .03, COMM .02.
- **International** (VEA, IEFA, VXUS): sectors FIN .22, INDU .17, TECH .11, DISC .10, HLTH .09, STAP .07, MATL .07, COMM .05, ENER .05, UTIL .03, REAL .03. No top holdings on file, so no country-by-sector data.
- **Emerging** (VWO, IEMG): sectors TECH .24, FIN .23, DISC .13, COMM .09, MATL .07, INDU .07.
- **Single-sector funds:** VGT is 100% TECH; VNQ is 100% REAL.
- **Bonds and cash** have no sectors, top holdings or style box.

**Look-through anchor:** Henderson's NVDA is 22.1% of the account directly and 22.9% including what VTI holds.

**Households (`DATA.households`, keyed by id).**

Fields:
- id, name, risk, profile, model;
- band `{low, high}`: the volatility band of the profile;
- value;
- rates: `{taxable: true, lt: 0.238, st: 0.408, bracket: 0.37}` for all;
- gain_budget;
- hy_limit;
- thresholds: single stock 10%, single fund 25%, turnover 40%, drift 5 points;
- incoming: Henderson only, $5.00M on 2026-11-15; it is not used by the rules here;
- meeting `{inDays, type, note}`;
- manager_run: symbol → manager name;
- target: the target on file;
- model_w: the profile model;
- holdings.

| id | Name | Profile and model | Risk band | Value | Gain budget | HY limit | Meeting |
|---|---|---|---|---|---|---|---|
| henderson | Henderson Family Trust | Moderate · CIO Moderate, Tier 2 | 8.26%–10.35% | $49.70M | $994K | 8% | in 2 days, Annual review |
| kaplan | Kaplan Household | Moderate · CIO Moderate, Tier 2 | 8.26%–10.35% | $8.70M | $174K | 8% | in 1 day, Retirement planning |
| castellano | Castellano Family | Moderate · CIO Moderate, Tier 2 | 8.26%–10.35% | $3.20M | $64K | 8% | in 5 days, Tax strategy review |
| okonkwo | Okonkwo Holdings LLC | Moderately Aggressive · CIO Moderately Aggressive, Tier 2 | 10.35%–12.53% | $31.60M | $632K | 10% | in 6 days, Liquidity deployment |
| brennan | Brennan Household | Aggressive · CIO Aggressive, Tier 1 | 12.47%–14.70% | $900K | $18K | 12% | in 6 days, Advisory proposal |

Delgado, the sixth household, is in 3.10.

**Target on file and profile model** (weights in %; blank = 0):

| id | | LCG | LCV | SMID | INTL | EM | UST | IGC | HY | CASH | HF | PE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| henderson | target | 16.61 | 16.61 | 6.88 | 11.46 | 3.44 | 11.57 | 13.29 | 5.14 | 5.00 | 5.00 | 5.00 |
| henderson | model | 14.50 | 14.50 | 6.00 | 10.00 | 3.00 | 13.50 | 15.50 | 6.00 | 7.00 | 5.00 | 5.00 |
| kaplan | target | 18.12 | 18.12 | 7.50 | 12.50 | 3.75 | 11.57 | 13.29 | 5.14 | 5.00 | 2.50 | 2.50 |
| kaplan | model | 14.50 | 14.50 | 6.00 | 10.00 | 3.00 | 13.50 | 15.50 | 6.00 | 7.00 | 5.00 | 5.00 |
| castellano | target | 21.15 | 21.15 | 8.75 | 14.58 | 4.38 | 9.64 | 11.07 | 4.29 | 5.00 | | |
| castellano | model | 14.50 | 14.50 | 6.00 | 10.00 | 3.00 | 13.50 | 15.50 | 6.00 | 7.00 | 5.00 | 5.00 |
| okonkwo | target | 15.48 | 14.68 | 6.35 | 10.32 | 3.17 | 8.52 | 10.80 | 5.68 | 5.00 | 10.00 | 10.00 |
| okonkwo | model | 19.50 | 18.50 | 8.00 | 13.00 | 4.00 | 7.50 | 9.50 | 5.00 | 5.00 | 5.00 | 5.00 |
| brennan | target | 27.65 | 25.60 | 10.24 | 16.39 | 5.12 | 1.67 | 3.89 | 4.44 | 5.00 | | |
| brennan | model | 27.00 | 25.00 | 10.00 | 16.00 | 5.00 | 1.50 | 3.50 | 4.00 | 3.00 | 5.00 | |

**Holding fields:**
- sym, name, kind (stock, etf, mf, cash, bond, alt), mv;
- `tradable`, with a `why_not` text when false;
- `cash` (true for CASH and MMF);
- expense_bps, classes, sector or sectors, top_holdings, style_box, yield;
- `muni`: true for MUB and the two individual municipal bonds;
- `scret`;
- lots `[{id, cost, mv, term, acquired}]`, where cost is null when the basis is missing;
- `manager`, for manager-run holdings.

Fund holdings (marked *fund* below) copy their facts from the shelf.

**Tradable** is false for:
- cash: routed separately;
- individual bonds: why_not "Individual bond or CD: held to maturity";
- alternatives: why_not as in the notes;
- manager-run stocks: why_not "Manager-run: traded by Crestline Large Cap Value SMA".

Everything else is tradable.

**Lots** are written as "cost/term", plus "(value x)" when a holding has several lots. "no basis" means the cost is missing; such a lot is never sold.

**Henderson Family Trust:**

| Sym | Name | Kind | Value | Classes | Yield | Lots | Past events | Notes |
|---|---|---|---|---|---|---|---|---|
| NVDA | NVIDIA Corp | stock | $10.60M | LCG 100% | 0.03% | $2.10M/LT | −0.80 / −0.53 / −0.30 / −0.28 | |
| MSFT | Microsoft Corp | stock | $4.90M | LCG 100% | 0.70% | $2.40M/LT | −0.80 / −0.53 / −0.30 / −0.28 | |
| VTI | US Total Market ETF | etf | $6.20M | LCG 45%, LCV 45%, SMID 10% | 1.20% | $5.10M/LT | shelf | fund |
| MUB | National Muni Bond ETF | etf | $9.80M | IGC 100% | 3.10% | $10.40M/LT | shelf | fund, muni |
| AGG | US Aggregate Bond ETF | etf | $5.10M | UST 60%, IGC 40% | 4.10% | $5.60M/LT | shelf | fund |
| VXUS | Total International Stock ETF | etf | $4.30M | INTL 75%, EM 25% | 2.90% | $4.90M/LT | shelf | fund |
| CASH | Sweep / T-Bills | cash | $7.30M | CASH 100% | 3.40% | $7.30M/LT | 0.10 / 0.02 / 0.003 / 0.015 | cash |
| AUSTIN-4.0-32 | City of Austin GO 4.0% 2032 | bond | $1.10M | IGC 100% | 3.40% | $1.08M/LT | 0.22 / 0.01 / −0.09 / −0.085 | not tradable, muni, 0 bp |
| NVDA | NVIDIA Corp | stock | $400K | LCG 100% | 0.03% | no basis/LT (lot id "NVDA (position 2)") | as NVDA | second position |

**Kaplan Household:**

| Sym | Name | Kind | Value | Classes | Yield | Lots | Notes |
|---|---|---|---|---|---|---|---|
| AAPL | Apple Inc | stock | $2.40M | LCG 100% | 0.40% | $600K/LT | |
| VTI | US Total Market ETF | etf | $2.10M | as shelf | 1.20% | $1.70M/LT | fund |
| VXUS | Total International Stock ETF | etf | $1.10M | as shelf | 2.90% | $1.20M/LT | fund |
| BND | US Bond Market ETF | etf | $1.90M | as shelf | 4.10% | $2.00M/LT | fund |
| CASH | Sweep / T-Bills | cash | $1.20M | CASH 100% | 3.40% | $1.20M/LT | cash |

**Castellano Family:**

| Sym | Name | Kind | Value | Classes | Yield | Lots | Notes |
|---|---|---|---|---|---|---|---|
| ITOT | Core S&P Total US Stock ETF | etf | $900K | as shelf | 1.20% | $500K/LT (value $600K); $290K/ST (value $300K) | fund |
| IEFA | Core MSCI EAFE ETF | etf | $520K | INTL 100% | 3.00% | $360K/LT (value $320K); $206K/LT (value $200K) | fund |
| JPM | JPMorgan Chase | stock | $260K | LCV 100% | 2.10% | $64K/LT (value $104K); $70K/LT (value $65K); $48K/LT (value $52K); $38K/ST (value $39K) | manager-run |
| PFE | Pfizer Inc | stock | $120K | LCV 100% | 6.50% | $93K/LT (value $75K); $46K/ST (value $45K) | manager-run |
| CVX | Chevron Corp | stock | $140K | LCV 100% | 4.50% | $128K/LT | manager-run |
| CVS | CVS Health | stock | $80K | LCV 100% | 4.20% | $99K/LT | manager-run |
| LCV-I | US Large Cap Value Fund (Institutional shares) | mf | $250K | LCV 100% | 2.00% | $236K/LT | fund, 55 bp |
| NYSDA-5.0-34 | NY State Dormitory Authority 5.0% 2034 | bond | $450K | IGC 100% | 3.50% | $462K/LT | not tradable, muni, 0 bp |
| AGG | US Aggregate Bond ETF | etf | $320K | as shelf | 4.10% | $333K/LT | fund |
| CASH | Sweep / T-Bills | cash | $160K | CASH 100% | 3.40% | $160K/LT | cash |

Castellano's `manager_run` is JPM, PFE, CVX and CVS → "Crestline Large Cap Value SMA".

**Okonkwo Holdings LLC:**

| Sym | Name | Kind | Value | Classes | Yield | Lots | Notes |
|---|---|---|---|---|---|---|---|
| CASH | Sweep / T-Bills | cash | $14.20M | CASH 100% | 3.40% | $14.20M/LT | cash |
| VTI | US Total Market ETF | etf | $6.40M | as shelf | 1.20% | $5.90M/LT | fund |
| IEFA | Core MSCI EAFE ETF | etf | $3.10M | INTL 100% | 3.00% | $3.00M/LT | fund |
| AGG | US Aggregate Bond ETF | etf | $4.70M | as shelf | 4.10% | $4.80M/LT | fund |
| PRIV | Private RE Interest | alt | $3.20M | PE 100% | 3.00% | $3.00M/LT | why_not "Private real estate interest; no redemption right"; past events −0.35 / −0.40 / −0.15 / −0.10 |

**Brennan Household:**

| Sym | Name | Kind | Value | Classes | Yield | Lots | Notes |
|---|---|---|---|---|---|---|---|
| LCG-A | Large-Cap Growth Fund, Class A (front-end load) | mf | $180K | LCG 100% | 0.10% | $140K/LT | fund, 95 bp |
| BAL-C | Balanced Income Fund, Class C (12b-1 fee) | mf | $90K | as shelf | 2.50% | $85K/LT | fund, 170 bp |
| IDX-I | S&P 500 Index Fund, institutional class | mf | $150K | LCG 50%, LCV 50% | 1.20% | $110K/LT | fund, 4 bp |
| NVDA | NVIDIA Corp | stock | $260K | LCG 100% | 0.03% | $45K/LT | |
| AAPL | Apple Inc | stock | $110K | LCG 100% | 0.40% | $70K/LT | |
| PRIV-SERIESB | Private placement, Series B preferred (startup) | alt | $60K | PE 100% | 0.00% | $25K/LT | why_not "Restricted private placement" |
| MMF | Government money market fund | cash | $30K | CASH 100% | 3.60% | $30K/LT | cash, 15 bp |
| CASH | Sweep / T-Bills | cash | $20K | CASH 100% | 3.40% | $20K/LT | cash |

**Research downgrades (`DATA.downgrades`, last 30 days).**
- Each is stored as `{sym, name, sector, change{from, to, date, why}, holders[{household_id, name, mv, share, tax_to_switch, decides}], alternatives[{sym, name, rating, yield, beta, style, why[]}]}`.
- The Okoye, Ashford and Reyes households are not among the six; they appear only in "Across the book".

| Stock | Change | Date | Why | Held by (value, share, tax to switch, who decides) | Alternatives (rating) |
|---|---|---|---|---|---|
| UNH | Buy → Underperform | 2026-10-13 | Higher medical cost ratios and a widening regulatory review; estimates cut for 2026 and 2027. | Okoye household: $110K, 11.2%, −$2.4K, "Manager (Beacon Hill Appreciation SMA)" | ELV (Buy), ABBV (Buy), CI (Buy), VTV (fund) |
| CVS | Buy → Neutral | 2026-10-09 | Cost trends in its insurance business are running above guidance; the team moves to the sidelines until next year's bids are known. | Castellano Family: $80K, 2.5%, −$4.5K, "Manager (Crestline Large Cap Value SMA)" | CI (Buy), JNJ (Buy), MRK (Buy), VTV (fund) |
| INTC | Neutral → Underperform | 2026-10-02 | Foundry customer wins are slower than planned and capital spending keeps free cash flow negative through 2027. | Ashford household: $100K, 2.3%, −$11.9K, "Manager (Ashcroft Large Cap Core SMA)" | ADI (Buy), NVDA (Buy), QCOM (Buy), VTV |
| PFE | Buy → Neutral | 2026-09-29 | Two late-stage readouts missed; the dividend looks covered but 2027 earnings estimates come down about 8%. | Castellano Family: $120K, 3.7%, −$4.9K, "Manager (Crestline Large Cap Value SMA)"; Ashford household: $140K, 3.3%, −$9.5K, "Manager (Ashcroft Large Cap Core SMA)" | JNJ (Buy), MRK (Buy), ABBV (Buy), VTV |
| TSLA | Neutral → Underperform | 2026-09-24 | Delivery growth is slowing into 2027 while the valuation still assumes autonomy revenue the team now expects later. | Reyes household: $1.10M, 8.9%, −$95.2K, "Advisor" | AMZN (Buy), BKNG (Buy), LOW (Buy), VUG (fund) |

**Applying the base data:**
1. **Meeting notes** (`meeting.note`):

   | Household | Note |
   |---|---|
   | Henderson | "Wants to revisit single-stock exposure and 2026 gifting." |
   | Kaplan | "Retiring in 18 months: income plan and a concentrated stock wind-down." |
   | Castellano | "Tax strategy review: wants to understand how each sleeve is managed for taxes." |
   | Okonkwo | "$14M of business-sale proceeds landed; needs a deployment plan." |
   | Brennan | "Tech employee with high-cost mutual funds, a large NVDA position from vesting and a private placement. Asked whether moving to an advisory account means selling everything." |
2. **Account type per holding (`acct`):**
   - "advisory" if the household's `manager_run` lists the symbol;
   - "other" for kind "alt";
   - otherwise "brokerage".

   **Brokerage scope** means holdings with `acct` = brokerage.

**Quick reference: brokerage holdings by household** (after the account types are applied):

| Household | Name | Profile | Value | Meeting (days, type) | Gain budget | Brokerage holdings (market value) |
|---|---|---|---|---|---|---|
| henderson | Henderson Family Trust | Moderate | $49.70M | 2, Annual review | $994K | NVDA $10.6M, MSFT $4.9M, VTI $6.2M, MUB $9.8M, AGG $5.1M, VXUS $4.3M, CASH $7.3M, AUSTIN-4.0-32 $1.1M, NVDA $0.4M (lot without cost basis) |
| kaplan | Kaplan Household | Moderate | $8.70M | 1, Retirement planning | $174K | AAPL $2.4M, VTI $2.1M, VXUS $1.1M, BND $1.9M, CASH $1.2M |
| castellano | Castellano Family | Moderate | $3.20M | 5, Tax strategy review | $64K | ITOT $900K, IEFA $520K, LCV-I $250K, NYSDA-5.0-34 $450K, AGG $320K, CASH $160K (plus manager-run JPM $260K, PFE $120K, CVX $140K, CVS $80K, acct advisory) |
| okonkwo | Okonkwo Holdings LLC | Moderately Aggressive | $31.60M | 6, Liquidity deployment | $632K | CASH $14.2M, VTI $6.4M, IEFA $3.1M, AGG $4.7M (plus PRIV $3.2M, acct other) |
| brennan | Brennan Household | Aggressive | $0.90M | 6, Advisory proposal | $18K | LCG-A $180K, BAL-C $90K, IDX-I $150K, NVDA $260K, AAPL $110K, MMF $30K, CASH $20K (plus PRIV-SERIESB $60K, acct other) |
| delgado | Delgado Household | Moderately Aggressive | $1.65M | 9, Retirement planning | $33K | see 3.10 |

All households are taxable at long-term 23.8% and short-term 40.8%. The federal bracket is 37%, known for Henderson, Castellano and Delgado and assumed for the others.

### 3.1 CIO (`DATA.cio`)

- **updated:** 2026-10-01.
- **Strategic target** = the household's own model weights (`model_w`).
- **Tactical tilts** are added to the strategic target, for classes the model holds:

  | Class | LCG | LCV | SMID | INTL | EM | UST | IGC | HY | CASH | HF | PE |
  |---|---|---|---|---|---|---|---|---|---|---|---|
  | Tilt | −0.02 | +0.015 | +0.005 | +0.015 | 0 | −0.01 | +0.005 | −0.005 | −0.005 | 0 | 0 |

- **Tolerance:** 3 points per asset class, 5 points per group (equity, fixed income, cash, alternatives as in the engine's `GROUPS`).
- **Views** (key, kind, view, was, date, one-line why):

| Key | Kind | View | Was | Date | Why |
|---|---|---|---|---|---|
| LCG | class | Underweight | Neutral | 2026-10-20 | Gains are concentrated in a handful of companies and valuations are stretched; earnings growth is broadening to other parts of the market. |
| LCV | class | Overweight | Neutral | 2026-10-20 | Cheaper valuations and improving earnings revisions in financials, industrials and health care. |
| INTL | class | Overweight | Neutral | 2026-10-20 | A weaker dollar and lower valuations; European and Japanese earnings are recovering. |
| SMID | class | Slight overweight | Neutral | 2026-10-01 | Rate cuts help smaller companies that borrow at floating rates. |
| UST | class | Underweight | Underweight | 2026-10-01 | Prefer high-quality corporate and municipal bonds for extra yield; keep duration near the benchmark. |
| HY | class | Slight underweight | Neutral | 2026-10-01 | Credit spreads are tight; the extra yield does not pay for the risk. |
| TECH | sector | Neutral | Overweight | 2026-10-20 | Strong fundamentals but crowded positioning and new export rules for advanced chips. |
| HLTH | sector | Overweight | Overweight | 2026-10-01 | Defensive earnings and reasonable valuations; selective within managed care. |
| ENER | sector | Underweight | Neutral | 2026-10-14 | Supply growth points to softer oil prices into 2027. |
| FIN | sector | Overweight | Neutral | 2026-10-20 | A steeper yield curve supports bank lending margins. |

### 3.2 Return history (`DATA.perf`)

- **as_of:** 2026-09-30.
- **periods:** 1Y and 3Y (3Y annualized).
- **Benchmarks by class** (1Y / 3Y):

  | Class | 1Y | 3Y |
  |---|---|---|
  | LCG | .24 | .18 |
  | LCV | .14 | .11 |
  | SMID | .10 | .07 |
  | INTL | .16 | .09 |
  | EM | .12 | .05 |
  | UST | .042 | .015 |
  | IGC | .055 | .028 |
  | HY | .08 | .06 |
  | CASH | .046 | .043 |
  | HF | .07 | .05 |
  | PE | .11 | .09 |

**Security returns (`perf.sec`), computed once when the data is built:**
- **Funds** (every non-stock in the fund shelf): the class-weighted benchmark, plus the fund's alpha, minus its expense ratio, for each period. Alphas (1Y / 3Y); all other funds 0 / 0:

  | Fund | 1Y | 3Y |
  |---|---|---|
  | LCG-A | −.035 | −.03 |
  | BAL-C | −.025 | −.022 |
  | ARKK | −.12 | −.15 |
  | LCV-I | +.004 | +.003 |
  | ESGV | −.006 | −.004 |
  | QQQ | +.02 | +.025 |
  | VGT | +.05 | +.06 |
  | SCHD | −.03 | −.01 |
  | DGRO | −.005 | 0 |
  | VNQ | −.05 | −.06 |
  | LQD | −.004 | −.004 |
  | VGSH | −.012 | 0 |

- **Stocks** (1Y / 3Y); any other stock .08 / .08:

  | Stock | 1Y | 3Y |
  |---|---|---|
  | NVDA | .38 | .72 |
  | MSFT | .12 | .21 |
  | AAPL | .09 | .17 |
  | AMZN | .18 | .20 |
  | GOOG | .26 | .22 |
  | TSLA | −.08 | .10 |
  | COST | .15 | .24 |
  | JPM | .28 | .22 |
  | PFE | −.12 | −.14 |
  | CVX | .03 | .05 |
  | CVS | −.18 | −.15 |
  | JNJ | .07 | .03 |
  | PG | .05 | .06 |
  | KO | .06 | .05 |
  | UNH | −.25 | −.06 |
  | HD | .09 | .10 |
  | INTC | −.20 | −.18 |
  | TXN | .04 | .06 |
  | QCOM | .10 | .12 |
  | ADI | .12 | .09 |
  | MRK | −.04 | 0 |
  | ABBV | .14 | .15 |
  | CI | .06 | .10 |
  | ELV | −.10 | 0 |
  | BKNG | .22 | .25 |
  | LOW | .07 | .08 |

- **Others** (1Y / 3Y):

  | Holding | 1Y | 3Y |
  |---|---|---|
  | AUSTIN-4.0-32 | .032 | .014 |
  | NYSDA-5.0-34 | .034 | .016 |
  | PRIV | .06 | .08 |
  | PRIV-SERIESB | 0 | .15 |
  | MMF | .046 | .043 |
  | CASH | .046 | .043 |

- Round to 4 decimals.
- **note:** "Illustrative returns. Attribution holds today's weights over the period; production uses the performance system's monthly holdings."

### 3.3 Fees (`DATA.fees`)

- **Program:** name "Advisory program". Tiered on assets:

  | Assets | Rate |
  |---|---|
  | first $1M | 1.00% |
  | to $5M | 0.80% |
  | to $10M | 0.65% |
  | above $10M | 0.50% |

  Note: "Tiered annual fee on assets in the program, billed quarterly; no trade commissions."
- **Lower cost:** name "Advisory program: index-only portfolio".
  - Rate 0.45% flat; funds 4 bp.
  - Note: "Lower fee with fewer services (no SMA managers or custom tax management); advisor compensation differs from the full program."
- **Managers and funds:** SMA manager fee 30 bp; direct-indexing manager fee 20 bp; model funds 5 bp.
- **Brokerage:**
  - commission 0.75% of each trade;
  - turnover 12% a year;
  - note: "Commission on each trade (illustrative full-service rate) plus the funds' own expenses, including sales loads and 12b-1 fees."

### 3.4 Strategies (`DATA.strategies`, fictional)

| id | Name | Kind | Minimum | Fee | Covers | Tax-managed | Can exclude a stock | Description |
|---|---|---|---|---|---|---|---|---|
| cio-model | CIO Model Portfolio (ETF) | Model | $50K | 5 bp | LCG LCV SMID INTL EM UST IGC HY CASH | no | no | Low-cost funds that follow the CIO strategic allocation and tactical views for the client's profile. |
| core-di | Core Equity Direct Indexing | SMA | $250K | 20 bp | LCG LCV SMID | yes | yes | Owns the index companies directly, harvests losses to offset gains, and can exclude a concentrated stock and tilt away from its sector. |
| tm-lc | Tax-Managed Large Cap SMA | SMA | $250K | 30 bp | LCG LCV | yes | no | Actively managed large-cap portfolio that takes in existing stocks and sells them over time within a gain budget. |
| value-sma | Large Cap Value SMA | SMA | $100K | 35 bp | LCV | no | no | Quality value companies with growing dividends. |
| intl-sma | International Equity SMA | SMA | $250K | 35 bp | INTL EM | no | no | Developed and emerging markets companies, actively managed. |
| muni-ladder | Municipal Ladder SMA | SMA | $250K | 20 bp | IGC UST | yes | no | Individual high-grade municipal bonds laddered over 1 to 10 years; tax-exempt income. |
| dividend | Dividend Income Model | Model | $50K | 8 bp | LCV IGC | no | no | Funds tilted to dividends and interest for clients who want income. |
| alts | Alternative Investments Platform | Fund | $250K | 100 bp | HF PE | no | no | Hedge fund and private equity access for qualified clients; limited liquidity. |

### 3.5 Approved content (`DATA.content`)

Each item has an id, title, kind, topics, audience and summary. All are approved 2026-07-15 and expire 2027-07-15 unless noted.

| id | Title | Kind | Topics | Audience | Summary |
|---|---|---|---|---|---|
| c01 | Why an advisory program: ongoing advice, one fee | Client brochure | value, fees, fiduciary | client | How an advisory program works: a fiduciary relationship, a portfolio built to the CIO's allocation, ongoing monitoring and one asset-based fee instead of commissions. |
| c02 | What you pay, and what you get | Fee disclosure | fees | client | The program fee schedule, what it includes, underlying fund expenses, and when a commission account may cost less. (approved 2026-09-01, expires 2027-03-01) |
| c03 | Moving your portfolio without a big tax bill | One-page summary | transition, tax | client | How appreciated positions move in kind and are sold over time within a yearly gain budget; losses are harvested along the way. |
| c04 | Investing cash in steps | One-page summary | cash, transition | client | Why new cash can be invested in monthly steps over six months, and what that does and does not protect against. |
| c05 | Owning the index directly | Client brochure | concentrated, tax, sma | client | How direct indexing works, how harvested losses offset gains elsewhere, and how a concentrated stock and its sector can be excluded. |
| c06 | Choices for a large single-stock position | Advisor guide | concentrated | advisor | The sell, retain-and-protect, and gift paths; insider and restricted-stock steps; when to involve the capital markets specialists. |
| c07 | House views: this quarter's CIO outlook | Client brochure | cio, market | client | The CIO's allocation calls and the reasons behind them, in plain language. (approved 2026-10-01, expires 2026-12-31) |
| c08 | How research ratings work | One-page summary | research | client | What Buy, Neutral and Underperform mean, how often ratings change, and why a rating change is a reason to review, not an instruction to trade. |
| c09 | Separately managed accounts explained | Client brochure | sma, value | client | What an SMA is, who the managers are, minimums, and how it differs from a mutual fund. |
| c10 | Talking about fees with confidence | Advisor guide | fees, value | advisor | Approved wording for explaining the program fee, comparing it fairly with a commission account, and disclosing that compensation differs between options. |
| c11 | Market update: rates, chips and oil | Client brochure | market, cio | client | This week's market moves and what the CIO thinks they mean for long-term investors. (approved 2026-10-22, expires 2026-11-22) |
| c12 | Gifting appreciated stock | One-page summary | concentrated, tax | client | Giving low-basis shares to family or charity: how it can reduce taxes and concentration at the same time. |

### 3.6 Objections (`DATA.objections`)

Each has a question, an approved answer, a content id and topics.

| id | Question | Approved answer | Content | Topics |
|---|---|---|---|---|
| o1 | Why pay an ongoing fee when I rarely trade? | The fee pays for ongoing advice, portfolio construction to the CIO's allocation, monitoring and rebalancing, and tax management, not for trades. If you truly want to buy and hold with little advice, a commission account can cost less, and we will show you both. | c10 | fees |
| o2 | Do I have to sell everything to move? | No. Most positions can move as they are. Appreciated holdings are sold over time within a yearly gain budget, and some may stay where they are. | c03 | transition, tax |
| o3 | My portfolio has done well. Why change it? | Past returns came with more risk than your profile calls for. The proposal aims for similar expected return with less risk, and a plan if markets fall. | c01 | value |
| o4 | I don't want to give up my company stock. | You don't have to sell it all. We can reduce it in steps that fit your tax position, protect part of it, or give some away, and we follow any trading rules that apply to you. | c06 | concentrated |
| o5 | Is now a bad time to invest my cash? | Nobody can time markets reliably. Investing in steps over several months spreads the entry point; it reduces regret, not long-run risk. | c04 | cash |
| o6 | Isn't a cheaper index-only option enough? | It may be. The index-only portfolio costs less but has fewer services and no custom tax management. We will show both, and how advisor compensation differs. | c02 | fees, value |

**o3 carries `requires: "risk_down"`.** It may be offered only when:
- the household's volatility is above its profile band; and
- volatility falls at the CIO target by more than 0.05 points.

Otherwise it is listed as not offered, with the reason (7.8).

### 3.7 Concentration (`DATA.concentration`)

- **Thresholds:**

  | Field | Value | Meaning |
  |---|---|---|
  | threshold | 0.10 | the alert threshold, which the advisor can adjust from 5% to 30% |
  | deck_threshold | 0.20 | "earlier material" |
  | exclude_over | 0.50 | the fixed program gate |

- **Positions** (key `household:SYM`):

  | Key | Insider | Restriction text | Intent | Note |
  |---|---|---|---|---|
  | henderson:NVDA | no | — | gift | Wants to give shares to the grandchildren's trust in 2026. |
  | henderson:MSFT | no | — | — | — |
  | kaplan:AAPL | yes | Employee: pre-clearance and quarterly trading windows apply. A pre-arranged sale plan lets sales continue through closed windows. | income | RSUs from 12 years at the company; retiring in 18 months. |
  | brennan:NVDA | yes | Employee: shares vest quarterly; trading only in open windows. | liquidity | Saving for a home down payment in 2027. |
  | brennan:AAPL | no | — | — | — |
  | delgado:COST | yes | Employee: pre-clearance required; quarterly trading windows. | — | Company stock from 25 years of employee purchase plans. |

- **Cash needs by year:**

  | Household | Needs |
  |---|---|
  | kaplan | 2027 $150K, 2028 $300K, 2029 $300K, 2030 $300K |
  | brennan | 2027 $120K |
  | delgado | 2027 $80K, 2028 $80K |
  | henderson, castellano, okonkwo | none |

- **Solutions:**

  | id | Name | Description |
  |---|---|---|
  | staged | Staged sale in brokerage | Sell the highest-basis lots first, each tax year within the gain budget. |
  | tm-sma | Tax-managed SMA through the tax-efficient transition | Move the shares in kind; the manager sells them down over time and builds a diversified portfolio around them. |
  | di | Direct indexing with the stock excluded | Harvested losses offset the gains from trimming; the index sleeve excludes the stock and leans away from its sector. |
  | gift | Gift low-basis lots | Give the lowest-basis shares to family or a donor-advised fund; removes the embedded gain from the client's tax return. |
  | hedge | Protect with a collar or exchange fund (specialist referral) | Keeps the shares but limits downside, or swaps them into a diversified pool; arranged by the capital markets specialists. |

### 3.8 News and events (`DATA.news`, nine curated items)

Each has an id, date, type (market, cio, research, client), source label, headline and summary. Each also has `moves`:
- `names`: symbol → price move;
- `sectors`: sector → move;
- `classes`: class → move.

Optional fields:
- a `view` (class → +1 or −1) for CIO items;
- a `research` symbol for research items;
- a `household` for a client question;
- `cio` (the related view key);
- `house` (the house view text);
- `todo`;
- `route` (ws1, ws2, ws3 or none).

| id | Date | Type, source | Headline | Moves / view | cio | route |
|---|---|---|---|---|---|---|
| n1 | 2026-10-22 | market, Market news | Tighter export rules for advanced AI chips | NVDA −.06, AVGO −.04, QCOM −.03 | TECH | ws3 |
| n2 | 2026-10-20 | cio, CIO | CIO moves US large-cap growth to underweight, international to overweight | view LCG −1, LCV +1, INTL +1 | LCG | ws1 |
| n3 | 2026-10-16 | market, Market news | Treasury yields jump after strong jobs report | classes UST −.012, IGC −.015, HY −.008 | UST | ws2 |
| n4 | 2026-10-14 | market, Market news | Oil falls 7% on supply outlook | CVX −.05; sector ENER −.04 | ENER | ws1 |
| n5 | 2026-10-09 | research, Research | Research cuts CVS to Neutral | CVS −.04; research CVS | HLTH | ws1 |
| n6 | 2026-09-29 | research, Research | Research cuts PFE to Neutral after trial misses | PFE −.07; research PFE | HLTH | ws1 |
| n7 | 2026-10-21 | market, Market news | Large-cap tech rallies on strong cloud earnings | MSFT +.04, AAPL +.03; sector TECH +.015 | TECH | ws3 |
| n8 | 2026-10-19 | client, Client question; household kaplan | Kaplan asks whether to sell AAPL before retiring | none | TECH | ws3 |
| n9 | 2026-09-24 | research, Research | Research cuts TSLA to Underperform | TSLA −.05; research TSLA | DISC | none |

Summaries, house views and to-dos (write them exactly):

| id | Summary | House view | To-do |
|---|---|---|---|
| n1 | New rules limit sales of the most advanced processors to several countries from January. Chip makers fell; analysts expect a modest hit to 2027 data-center revenue. | The CIO moved technology from overweight to neutral on 20 October, citing crowded positioning and this policy risk. Research keeps a Buy on NVDA but cut its 2027 estimate 4%. | Review single-stock exposure to chip makers, including through funds. |
| n2 | The quarterly allocation update trims large-cap growth by 2 points and adds to large-cap value and international developed stocks. | Growth leadership is narrow and expensive; earnings are broadening. Portfolios heavy in large-cap growth now sit further from the tactical target. | Check households overweight large-cap growth against the new tactical target. |
| n3 | The 10-year yield rose 0.25 points to 4.6% as payrolls beat expectations and rate-cut hopes faded. Bond prices fell. | The CIO keeps bond duration near the benchmark and prefers high-quality corporate and municipal bonds; higher yields improve future income. | Explain the bond moves to income-focused clients; no change in allocation needed. |
| n4 | Producers signalled higher output into 2027. Energy shares fell across the board. | The CIO moved energy to underweight on 14 October. Research keeps a Neutral on CVX. | Note energy exposure in dividend-heavy portfolios. |
| n5 | Cost trends in its insurance business are running above guidance; the team moves to the sidelines until next year's bids are known. | The CIO stays overweight health care but selective within managed care. Similar companies with Buy ratings include CI and JNJ. | Where a manager runs the holding, ask the manager for its view; otherwise review alternatives. |
| n6 | Two late-stage readouts missed; the dividend looks covered but 2027 estimates come down about 8%. | Health care remains an overweight for the CIO. Research prefers JNJ and MRK in pharmaceuticals. | Review PFE holders; for manager-run sleeves, raise it with the manager. |
| n7 | Software and device makers rose after cloud revenue beat estimates. | Strong results, but the CIO is neutral on technology after its run; gains are a chance to trim concentrated positions. | Use the rally to revisit concentrated technology positions. |
| n8 | Client email: "Should I sell my Apple shares now or wait until I retire? I don't want a huge tax bill." | Research rates AAPL Buy; the CIO is neutral on technology. AAPL is 28.9% of the account, well above the 10% guideline. | Build a multi-year sale plan that respects trading windows and the retirement income need. |
| n9 | Delivery growth is slowing into 2027 while the valuation still assumes autonomy revenue the team now expects later. | No CIO change. Exposure among your households is only through broad index funds. | No action for these households; monitor. |

### 3.9 Firm intelligence catalog (`DATA.intel`, `intel_as_of` 2026-10-23)

These are extra published items. They are evaluated against the book only when the advisor asks.

| id | Date | Type | Headline | Abstract | Stance | Rule | Client use | Expires | Entitlement |
|---|---|---|---|---|---|---|---|---|---|
| f1 | 2026-10-23 | research | Research upgrades JPM to Buy | Net interest income is holding up better than expected and capital return is rising; the team raises its 2027 estimate 5%. | Buy (was Neutral) | research, sym JPM | yes | 2027-04-23 | All advisors |
| f2 | 2026-10-23 | cio | CIO moves high-yield bonds from neutral to overweight | Default expectations have eased and yields remain above their 10-year average; the CIO adds 1 point to high yield within fixed income. | High yield: Overweight (was Neutral) | view, HY +1 | yes | — | All advisors |
| f3 | 2026-10-22 | research | European banks: sector upgraded to Overweight | Higher-for-longer rates and buybacks support earnings; the team prefers large lenders in France and Spain. | Sector: Overweight (was Neutral) | region-sector, Europe, FIN | no | 2027-01-22 | Research subscribers (you are entitled) |
| f4 | 2026-10-23 | market | Yen jumps 3% after the central bank signals higher rates | A stronger yen weighs on Japanese exporters in local terms but lifts the dollar value of unhedged Japanese holdings. | — | market, classes INTL +.006 | no | — | All advisors (third-party news) |
| f5 | 2026-09-30 | cio | CIO keeps energy at neutral | Supply discipline supports prices; the CIO holds energy at neutral. | Energy: Neutral | superseded | no | — | All advisors |

Other fields:
- Sources: "Research", "CIO" or "Market news".
- Status "Published", except f5, which is "Superseded", with superseded_by "CIO moved energy to underweight on 14 October".
- Version "v1".
- Tags:

  | Item | Tags |
  |---|---|
  | f1 | financials, banks, JPM, US large cap |
  | f2 | fixed income, high yield, credit |
  | f3 | international, Europe, financials, banks |
  | f4 | international, Japan, currency |
  | f5 | energy, sector view |

### 3.10 The Delgado household (above the program limit)

| Field | Value |
|---|---|
| id, name | delgado, Delgado Household |
| risk, profile, model, band | Moderately Aggressive; profile, model, band and model weights copied from Okonkwo |
| value | $1.65M |
| rates, thresholds | copied from Henderson |
| gain budget | $33K |
| HY limit | 0.10 |
| meeting | in 9 days, "Retirement planning", note "Long-time company employee; most of the account is company stock." |
| manager_run | none |
| incoming | none |
| target | Okonkwo's model weights |

**Holdings (all brokerage):**
- **COST, $960K.** A stock, tradable.
  - Classes LCG 100%, sector STAP, yield 0.5%, style box LG.
  - Past events: dotcom +.05, gfc −.30, covid −.24, 2022 −.006.
  - Lots:

    | Lot | Cost | Value | Term | Acquired |
    |---|---|---|---|---|
    | COST-1 | $90K | $760K | LT | 2009-03-16 |
    | COST-2 | $60K | $200K | LT | 2014-06-02 |

- **VTI, $320K.** Copy Henderson's VTI attributes. One lot: cost $250K, LT, acquired 2018-01-10.
- **AGG, $230K.** Copy Henderson's AGG. One lot: cost $240K, LT, acquired 2020-08-03.
- **CASH, $140K.** Copy Henderson's CASH. One lot: cost $140K.

COST is 58.2% direct and 0.2% through VTI's look-through, 58.3% in all, above 50%.

### 3.11 Pathway fields

**Age and liquidity reserve** (`age`, `liquidity_reserve`):

| Household | Age | Liquidity reserve |
|---|---|---|
| henderson | 72 | $1.0M |
| kaplan | 63 | $400K |
| castellano | 58 | $60K |
| okonkwo | 51 | $1.5M |
| brennan | 34 | $40K |
| delgado | 64 | $80K |

**Bonds:**
- AUSTIN-4.0-32 matures 2032-07-01, with no call.
- NYSDA-5.0-34 matures 2034-03-15 and is callable 2026-12-15.

**Share classes:** LCG-A "A"; BAL-C "C"; LCV-I "I".

**`DATA.pathway`:**
- as_of 2026-10-24.
- Thresholds:

  | Threshold | Value |
  |---|---|
  | high_cost_bps | 50 |
  | excess_cash_pct | 0.05 |
  | gains_min | $5,000 |
  | losses_min | $25,000 |
  | call_days | 90 |
  | trading_rival | 0.5 |

- trading_cost_bps 5.
- Segment notes:
  - low: "Low: cash, fixed income and C shares, with low embedded gains";
  - medium: "Medium: some embedded gains or share-class constraints";
  - hard: "Hard: taxable with high embedded gains, A shares or clients aged 80 and over".
- note: "Illustrative thresholds for the prototype; production uses the approved screen thresholds."

---

## 4. Rules: exact behaviour

Implement these exactly. Where a sentence is quoted, the on-screen wording should match; `{x}` marks a value to insert. Names in `code` are the ones later sections use.

### 4.0 Base portfolio engine (`E`): exact rules

Expose these functions on one global `E`, plus the constants. Implement them exactly as written.

**Constants:**
- `EQ` = LCG, LCV, SMID, INTL, EM: the equity classes.
- `GROUP_OF`:
  - the equity classes → "equity";
  - UST, IGC, HY → "fixed";
  - CASH → "cash";
  - HF, PE → "alt".
- `GROUPS` = equity "Equity", fixed "Fixed income", cash "Cash", alt "Alternatives".

A holding is **classified** when its `classes` object has at least one key.

**Correlation lookup (`E.corr(a, b)`):**
- 1 when a = b;
- otherwise "a|b", else "b|a", else 0.

**`E.weights(holdings)` → `{w, ct, total}`:**
- For each classified holding: ct += value, and each class k gets value × share.
- Unclassified holdings add their value to a separate sum.
- w[k] = class value ÷ ct (0 if ct is 0).
- total = ct + the unclassified sum.

**`E.groups(w)`:** sums w into equity, fixed, cash and alt (all start at 0).

**`E.stats(w)` → `{er, vol}`:**
- er = Σ w[a] × er(a).
- variance = Σ over a, Σ over b, of w[a] × w[b] × vol(a) × vol(b) × corr(a, b), where a and b run over the keys of w.
- vol = √max(variance, 0).

**`E.te(w1, w2)`, tracking error:**
- d[k] = w1[k] − w2[k] over the **union** of keys (missing = 0).
- te = √max(Σ Σ d[a] × d[b] × vol(a) × vol(b) × corr(a, b), 0).

**`E.stress(holdings)`:** for each scenario, Σ value × scret[scenario] (0 if missing) ÷ the classified total. Use classified holdings only.

**`E.names(holdings)`, single-name exposure through funds:**
- tot = Σ value over all holdings.
- A stock adds its value to its own symbol.
- Every holding with top holdings adds value × weight to each named symbol.
- Divide every entry by tot.

**`E.sellPlan(hh, holdings, sym, amount)`.** The tax-lot rule; it must match to the dollar.
1. Collect the lots of every holding with that symbol, skipping lots of $0.50 or less.
2. Gain ratio g = (value − cost) ÷ value. It is null when the cost is missing; those lots are never sold.
3. Sort the sellable lots ascending by rank:
   - −10 + g for losses, so the biggest loss goes first;
   - otherwise (10 if short-term, else 0) + g, so long-term goes by smallest gain and short-term goes last.
4. Walk the lots while more than $0.50 is left to sell. For each lot:
   - take = min(left, lot value);
   - gain += (value − cost) × take ÷ value;
   - when taxable, tax += that gain × the term's rate;
   - record the lot and the take.
5. Return the gain, the tax, the lots used, the amount unfilled, and "excluded" = the value of the no-basis lots.

**`E.fundAsHolding(sym, amount)`:** a new holding copied from the shelf entry.
- Copied fields: name, kind, classes, sectors, sector, top_holdings, expense_bps, style_box, scret, yield.
- Value = amount; tradable.
- One short-term lot with cost = value.
- Null if the symbol is unknown.

**`E.apply(hh, lines)`:** applies sell and buy lines to a deep copy of the holdings.
1. **Sells, in order.** Run `sellPlan` for each sell. Then:
   - reduce each used lot's cost proportionally and its value by the take;
   - reduce the holding's value by the take;
   - add up proceeds (amount − unfilled), gain and tax.
2. **Buys:** buys cost Σ buy amounts.
   - If proceeds don't cover them, take the rest from cash holdings in order.
   - If proceeds are left over, add them to the CASH holding, creating it if needed.
   - Then add `fundAsHolding` for each buy.
3. **Return** holdings worth more than $0.50, with proceeds, gain and tax.

**`E.metrics(hh, holdings)`:**
- w, ct, total from `weights`;
- er and vol from `stats`;
- groups;
- stress, and `worst`: the scenario with the lowest stress, scanning in order and replacing only on a strictly lower value;
- names.

**Reference figures.** Return and risk use the whole household, unclassified holdings excluded. They must match to 2 decimals:

| Household | Return | Risk |
|---|---|---|
| Henderson | 5.64% | 9.24% |
| Kaplan | 5.86% | 10.45% |
| Castellano | 6.29% | 11.09% |
| Okonkwo | 5.23% | 6.54% |
| Brennan | 6.60% | 15.31% |

**Tax check:** selling $1,000,000 of Henderson's NVDA uses only the lot with basis ($10.60M value, $2.10M cost); the $400K lot has no basis and is excluded. Gain $801,887, tax $190,849.

If return or risk is off, check the correlation lookup and that unclassified holdings are excluded.

### 4.1 Formatting helpers

**`money(n, d)`:**
- Missing or NaN → "—".
- Negative → prefix "−", the true minus sign.
- At or above $1M → "$" + n/1e6 to d decimals (default 2) + "M", for example $47.20M.
- At or above $10,000 → "$" + n/1,000 rounded + "K", for example $284K.
- Otherwise → "$" + the rounded number with thousands separators, for example $8,974.

**Percentages:**
- `pct(x, d=0)`: x×100 to d decimals plus "%", with "−" for negatives.
- `spct(x, d=1)`: always signed, "+" or "−".
- `ppt(x, d=1)`: signed points, for example "+0.51 pts".

**Labels:**
- `cls(k)`: a class label from `DATA.classes`, else a sector name from `DATA.sectors`, else the key.
- `short(k)`: `cls(k)` with these replacements:

  | From | To |
  |---|---|
  | "U.S. " | "US " |
  | "International Developed Equity" | "International developed" |
  | "Emerging Markets Equity" | "Emerging markets" |
  | "U.S. Corporates (IG)" | "IG corporates" |

- `lc(t)`: lower case, but keep "US" and "IG" upper case.

**Households:**
- `HHS()` is all households in data order: henderson, kaplan, castellano, okonkwo, brennan, delgado.
- `HH()` is the current household.

### 4.2 CIO target and allocation gap (`X.cioTarget`, `X.gap`)

**Targets:**
- **Strategic target** = the household's `model_w`.
- **Tactical target:**
  1. For every class with a strategic weight above 0, add its tilt (3.1) and floor the result at 0.
  2. Renormalise to sum to 1.
  3. Classes with no strategic weight stay out.

**`X.scope(hh, scope)`:** brokerage holdings, or all holdings.

**`X.gap(hh, scope, basis)`:**
- From the engine:
  - `E.weights(holdings)` gives class weights `w` and the scope total `ct`;
  - `E.groups` gives group weights;
  - `E.stats` gives expected return `er` and volatility `vol`;
  - `E.te(w, t)` gives tracking error.
- **Class rows:** every class with today's weight above 0.0005, or a target above 0.
  - gap g = today − target;
  - dollars = g × ct;
  - outside if |g| > 0.03.
- **Group rows:** the same, with the 0.05 tolerance.
- **Returns:** the rows, the groups, `st` (stats today), `stT` (stats at the target), `out` (classes outside), `outG` (groups outside) and `te`.

### 4.3 Attribution (`X.attribution(hh, scope, period)`), Brinson-Fachler against the strategic target

- **Holdings:** those in scope that have classes. Today's weights `w` come from them; benchmark weights `wb` are the strategic target.
- **Security return r:**
  - `perf.sec[sym][period]` when present;
  - else the holding's class-weighted benchmark.
- **Class returns:**
  - each holding contributes mv × class share × r to the numerator and mv × class share to the denominator;
  - the portfolio class return Rp(k) = numerator ÷ denominator;
  - if a class has no holdings, Rp(k) is the benchmark Rb(k).
- **Totals:**
  - RB = Σ wb·Rb;
  - RP = Σ w·Rp;
  - active = RP − RB.
- **Effects per class:**
  - allocation = (w − wb)(Rb − RB);
  - selection = wb(Rp − Rb);
  - interaction = (w − wb)(Rp − Rb).

  The sums of the three effects equal active exactly (a check tests this).
- **Detractors:**
  - per holding, excess = r − its class-weighted benchmark;
  - keep excess < −1 point;
  - sort by excess × value, ascending.

### 4.4 Fees and the four cost options (`X.programFee`, `X.costs`)

**Program fee:** the tiers in 3.3 applied slab by slab, returning the fee and the slabs. Reference fees:

| Assets | Fee |
|---|---|
| $1M | $10,000 |
| $5M | $42,000 |
| $47.2M | $260,500 |

**`X.costs(hh, amount, turnover, smaShare)`.** Fund cost today is the value-weighted expense ratio of the brokerage holdings. Each option has cost parts plus expected return and volatility:

| id | Name | Parts | Return and risk from |
|---|---|---|---|
| stay | Stay in brokerage | Fund expenses = amount × fund cost; Commissions = amount × turnover × 0.75% | today (brokerage, tactical gap `st`) |
| program | Advisory program: CIO model | Program fee; Fund expenses = amount × 5 bp | the tactical target |
| sma | Advisory program with SMA managers | Program fee; SMA manager fees = amount × equity share of the tactical target × smaShare × 30 bp; Fund expenses = amount × (1 − equity share × smaShare) × 5 bp | the tactical target |
| index | Advisory program: index-only portfolio | Program fee = amount × 0.45%; Fund expenses = amount × 4 bp | the strategic target |

For every option:
- total = Σ parts;
- bps = total ÷ amount × 10,000;
- net = er − total ÷ amount.

The defaults used everywhere unless the advisor changes them:
- amount = brokerage total rounded to $1,000;
- turnover 12%;
- smaShare 0.5.

### 4.5 Canonical investable cash (`X.cashSplit(hh)`)

This is the one cash figure used by routing, screens, paths, proposal and handoff.
- **total** = the brokerage cash holdings (CASH and MMF).
- **target** = the smaller of total, or the tactical CASH weight × brokerage total.
- **needs** = the household's cash needs dated 2027 or earlier.
- **reserve** = the smaller of (total − target), or (liquidity reserve + needs).
- **investable** = the larger of 0, or (total − target − reserve).

### 4.6 Routing: where each brokerage holding goes (`X.routing(hh)`)

**Cash holdings** are split in proportion to their share of total cash, giving up to three rows each (a row only if above $1):
- "instep": the investable part. Why: "Cash above target after the reserve: invest in monthly steps over six months."
- "inkind": the target part. Why: "Cash at the CIO target: moves as the program's cash allocation."
- "reserve": the reserve part. Why: "Liquidity reserve and next year's cash needs: stays in brokerage." Drop the needs words when there are no needs.

**Other holdings**, first rule that applies:
1. Not tradable → "stay", with the holding's `why_not` text.
2. Any lot without cost → "basis". Why: "Cost basis missing: move in kind; no sales until basis is on file."
3. Gain below −$1,000 → "harvest". Why: "Loss of {money}: sell, harvest the loss and reinvest."
4. Expense ratio at least 50 bp and a gain under 30% of value → "swap". Why: "Costs {bp} bp with a small gain: sell and replace with a lower-cost share class."
5. Gain above 20% of value → "transfer". Why: "Gain {pct} of value: move in kind; sell over time within the gain budget."
6. Otherwise → "inkind". Why: "Small gain: move in kind; sell or keep as the model needs."

Gain = value − total lot cost.

**Route labels and colors** (`X.ROUTES`):

| Route | Label | Color |
|---|---|---|
| reserve | Kept as liquidity reserve | c-other |
| transfer | Tax-efficient transition | c1 |
| instep | Invest in steps | c3 |
| harvest | Sell and harvest loss | c6 |
| swap | Replace high-cost class | c2 |
| inkind | Move in kind | c7 |
| basis | Hold until basis found | c4 |
| stay | Stays where it is | c-other |

### 4.7 Event impact (`X.eventImpact`, `X.eventForHH`)

**`X.eventImpact(ev, h)`:** the estimated move r on one holding, with "via" tags.
- A stock named in the move → add its move ("direct").
- Each look-through name in the move → add weight × move ("{SYM} inside").
- Sectors:
  - for a stock not named directly, add its sector move;
  - for a fund, add equity share × sector weight × sector move.

  Tag "sector".
- Class moves → add class share × move. Tag "bonds" for fixed-income classes, else "class".
- Dollars = r × value.

**`X.eventForHH(ev, hh)`** returns a kind and a score.
- **view** (CIO items):
  1. Use the whole-household tactical gap.
  2. For each class in the view, misalignment = −direction × gap.
  3. List a row when |gap| > 0.5 point; it is "against" when misalignment > 0.
  4. score = Σ positive misalignment × total.
- **research:**
  - direct = the household's direct holding value;
  - look = the look-through share;
  - score = direct, or look × total × 0.2 if there is no direct holding;
  - also pass the downgrade holder record for this household, if any.
- **client:** score is a very large number for the named household, else 0.
- **market:**
  - rows = holdings with |dollars| > $1, ascending;
  - dollars = their sum;
  - score = |dollars|;
  - share of the account = dollars ÷ total.

A household is considered only when its score is above 1.

### 4.8 Multi-year sale plan (`X.salePlan(hh, sym, o)`, illustrative, prices constant)

**Inputs:**

| Input | Meaning |
|---|---|
| target | target share |
| budget | yearly gain budget, or none |
| gift | yearly gift amount |
| years | number of years |
| needs | year → cash needed |

**Set-up:** take a working copy of the position's lots. "via" = the look-through exposure in dollars beyond the direct position.

**Lot orders:**
- **Sell order:**
  1. loss lots first, most negative first;
  2. then long-term lots by ascending gain ratio;
  3. then short-term lots.
- **Gift order:** ascending cost-to-value ratio, so the lowest basis goes first.
- Lots without cost are never sold or gifted.

**Each year from 2026:**
1. **Gift** up to the yearly gift amount, capped at the amount still above target. Gifted value leaves the household total.
2. **Find the excess:** excess = (held + via) − target × the current total.
3. **Apply the budget:** if selling the whole excess would realize more gain than the budget, find the largest amount whose realized gain fits (30 bisection steps).
4. **Cover cash needs:** if that year's cash need is larger, sell the need instead. This is a forced sale and may exceed the budget; mark the year "over budget".
5. **Sell** in sell order. Realized gain and tax use the lot term's rate, long-term or short-term.
6. **Shrink the household total** by the year's need.
7. **Record the year:** sold, gifted, gain, tax, need, end value, and share = (held + via) ÷ total.

**reach** = the first year whose share is at or below the target, or none.

### 4.9 One eligibility rule (`D.elig(hh)`)

**Exposure.**
- The largest single-security exposure is taken over `E.names(holdings)`: direct plus look-through, as a share of the household.
- **via** text:
  - "all through funds" when nothing is held directly;
  - "{direct%} direct, {fund%} through funds" when both exist (1 decimal);
  - "held directly" otherwise.

**Conditions**, each with an owner:
- **Insider positions:** "Insider rules for {SYM list}: pre-clearance and trading windows". Owner Compliance.
- **Lots without cost:** "{money} without cost basis cannot be sold or planned". Owner Operations.
- **Manager-run symbols:** "{list} are run by a manager; the manager decides". Owner Manager.

**State:**
- **Share above 50% → "ineligible".**
  - Reason: "{SYM} is {share%} of the account ({via}), above the 50% single-security limit".
  - Route: "Concentrated stock specialist".
  - Blocks: Advisory program, CIO model portfolio, SMA and direct indexing, Tax-efficient transition.
- **Otherwise:** "conditions" if any condition exists, else "eligible".

**Labels (`ELIG`):**

| State | Label | Tone | Short label |
|---|---|---|---|
| eligible | Eligible in principle | good | Eligible in principle |
| conditions | Eligible in principle, with conditions | warn | Eligible · conditions |
| specialist | Requires specialist review | info | Specialist review |
| ineligible | Not eligible for the program | bad | Not eligible |

### 4.10 Readiness (`D.ready(hh, ctx)`), three stages

1. **Client discussion:** always "ready".
   - Note "Ready: options and trade-offs can be discussed".
   - When not eligible: "Ready: discuss the position and the specialist route".
2. **Proposal:**
   - When not eligible: "blocked", "Blocked: no program proposal above the limit".
   - Otherwise "pending", "Not ready: {n} to clear".
   - Items:
     - the ineligible reason (Specialist), when not eligible;
     - "Suitability determination" (Advisor);
     - "Confirm the risk profile is current" (Advisor), when ctx.risk;
     - "Product eligibility for SMA or direct indexing" (Product team), when ctx.product;
     - plus any Operations condition.
3. **Implementation:** always "blocked", "Not cleared: {n} prerequisites outstanding".
   - Items: the non-Operations conditions, then:
     - "Client agreement" (Client);
     - "Validated trade plan (this page shows planning estimates only)" (Portfolio management);
     - "Compliance review of client materials" (Compliance);
     - "Supervisory approval" (Supervision).

Never use the words "Not eligible yet".

### 4.11 The allocation finding (`D.ws1(hh, settings)`)

**Settings:** scope, CIO basis and period. The baseline `BASE` is brokerage, tactical, 3Y. If brokerage scope is empty, use the whole household.

**Inputs:**
- the gap and attribution for the settings;
- risk position: above, below or inside the profile band, using today's volatility;
- cash share of the whole household;
- the largest exposure from `D.elig`;
- the alert threshold `S.o3.th`.

**The first matching rule sets the kind and status:**

| Order | Condition | Kind | Status | Finding (wording) | Next step |
|---|---|---|---|---|---|
| 1 | not eligible | gate | specialist | "{reason} for the advisory program" | "Refer to the concentrated stock specialist; revisit the program once {SYM} is below 50%." |
| 2 | volatility above band | risk | review | "Expected volatility {v} is above the {profile} band ({low}–{high})", plus "; {SYM} is {share} of the account" if above the threshold | "Review how to bring volatility back into the band after taxes and fees; compare staying in brokerage with a transition." |
| 3 | below band and cash > 20% | cash | review | "Expected volatility {v} is below the {profile} band; {cash%} of the account is in cash" | "Discuss investing the cash in steps toward the CIO allocation for the client's profile." |
| 4 | largest share > threshold | conc | ready | "{SYM} is {share} of the account: single-company concentration warrants a discussion" | "Review whether reducing {SYM} is worth the taxes and fees; compare alternatives before suggesting a transition." |
| 5 | active return < −1 point | perf | review | "Trailing the CIO allocation by {pts} a year over {three years / one year}, mostly from {fund selection / allocation}" | "Review the detracting funds and whether lower-cost or managed alternatives fit." |
| 6 | any class outside tolerance | drift | monitor | "Drift from the {CIO tactical/strategic target} ({n} asset classes outside tolerance), with volatility inside the profile band" | "Rebalance at the next scheduled review; no change needed now." |
| 7 | otherwise | none | none | "In line with the {target} and the risk profile" | "No action." |

**The "why" sentence for the concentration kind:**
- If active return > 0, it opens: "The portfolio has outperformed ({pts} a year over {period}) and volatility is inside the profile band, but the result rests on {SYM}." Otherwise: "The result depends heavily on {SYM}."
- It then states a 30% fall cost: 0.3 × share × household total.
- Volatility is compared at 0.1-point precision. The sentence depends on how volatility changes at the target:

  | At the target, volatility… | Wording |
  |---|---|
  | rises | "would cut single-company risk but raise expected portfolio volatility slightly ({a} → {b}), because the target {holds less cash / holds more stocks / has a different mix} than the portfolio does today: the case is about concentration, not lower volatility." |
  | falls | "would also lower expected volatility ({a} → {b})." |
  | is unchanged | "would stay about the same …: the case is about single-company concentration, not lower volatility." |

The checks parse these "lower / raise / stay about the same ({a}% → {b}%)" phrases, so keep them exact.

**The "why" sentence for the other kinds:**

| Kind | Why |
|---|---|
| risk | "Volatility above the agreed profile is a suitability matter, regardless of past returns. At the {target} expected volatility would be {v}." |
| cash | "Much less volatility than the profile implies may leave the client short of their return objective; expected return {a} against {b} at the {target}." |
| gate | "Above this limit the program is not available; the first step is a specialist plan for the position." |
| perf | "Persistent underperformance against the CIO allocation, after costs, is worth explaining to the client." |
| drift | "Differences from the CIO model alone are not proof that a change would help the client." |
| none | "Nothing material to raise." |

**Trade-offs: six rows (label, value, tone):**
1. **Single-company concentration:** "{SYM} {share}; guideline 10%", warn. Below the threshold: "largest {SYM} {share}".
2. **Portfolio volatility:** "{a} → {b} at the {basis} target". Warn if it rises; good if it falls.
3. **Tracking error to the CIO target:** "{te} → 0%".
4. **Suitability (profile band):** "{above/below/inside} the band ({low}–{high})". Good if inside, else bad.
5. **Estimated gains, year one (planning):**
   - not eligible: "n/a: transition not available";
   - otherwise "{min(transfer gains, gain budget)}; tax ≈ {× long-term rate}" (warn), or "none needed".

   The label must contain "planning".
6. **Fees (illustrative):** "{program total} in the program vs {stay total} a year today". Warn if higher.

**Evidence (three lines):**
- "Expected volatility {v}, band {low}–{high} ({position})";
- "{n} asset classes outside tolerance of the {target}; tracking error {te}";
- "{3-year/1-year} return {signed} vs the CIO allocation, mostly {largest-effect class in lower case}".

**Choices:**

| Kind | Choices |
|---|---|
| gate | Specialist review (recommended), Stay in brokerage, Advisory program (blocked) |
| none, drift | Monitor (recommended), Rebalance in brokerage, Advisory program (suitability dependent) |
| others | Review alternatives (recommended), Stay in brokerage, Advisory program ("with conditions" if conditions, else "suitability dependent"), Monitor |

**Also returns:**
- `ready` = `D.ready` with risk true for the risk kind, and product true for the concentration kind;
- an assumptions line, for example "Brokerage accounts · CIO tactical target · 3-year performance";
- whether the settings equal the baseline.

### 4.12 Concentrated position (`D.ws3`) and event materiality (`D.ws4`)

**`D.ws3(position, plan, hh)`:**
- **Gates:**
  - Over the limit: bad, "Not eligible for the program: above the 50% single-security limit. Program, SMA and direct-indexing paths are blocked until {SYM} is below 50%."
  - Insider: warn, "Insider: {restriction} (owner: Compliance)".
  - Lots without basis: bad, "{money} has no cost basis on file: it cannot be sold or planned until basis is found (owner: Operations)."
- **Status:** specialist if over, review if insider, else ready.
- **Finding:** "{SYM} is {share} of {name}'s account ({direct} direct, {via} through funds)".
- **Next:**
  - Over: "Refer to the concentrated stock specialist; staged sales in brokerage can start after pre-clearance". Drop "after pre-clearance" when not insider.
  - Otherwise: "Agree a target and pace with the client: the planning scenario reaches {target} by {year} within the gain budget", or "is still above {target} after {n} years".
- **Actionability per solution:**

  | Solution | Over the limit | Otherwise |
  |---|---|---|
  | staged | "After pre-clearance" (warn) if insider, else "Advisor can act" (good) | same |
  | tm-sma, di | "Not eligible: program limit" (bad) | "Product eligibility to confirm" (info) |
  | gift | "Client and tax advisor decide" (info) | same |
  | hedge | "Specialist review" (info) | same |

**`D.ws4(event, result)`:**
- **Market:**
  - material if |share of account| ≥ 0.5%;
  - status:

    | Condition | Status |
    |---|---|
    | material, and a holding in the rows is above the alert threshold (look-through) | review |
    | material, otherwise | ready |
    | ≥ 0.1% | monitor |
    | below 0.1% | none |

  - Actions: "Review the concentrated position" / "Contact the client" / "Monitor" / "No action".
  - Size: "{money} ({signed share, 2 decimals} of the account), estimated scenario impact".
  - Confidence: "Estimated scenario impact (model): the event's price moves applied to today's holdings, looking through funds. Not a realized gain or loss."
- **View:**
  - material if the largest "against" gap ≥ 5 points;
  - status review or monitor; action "Reassess the allocation" or "Monitor";
  - size: the top two against rows, "{class lower case} {signed pts}", joined by commas, plus " against the new view". If there are none: "in line with the new view".
  - Confidence "Verified exposure: today's holdings compared with the new CIO tactical view."
- **Research:**
  - material if held directly;
  - status review when the downgrade holder record says a manager decides, else ready;
  - action "Request a manager review" or "Review alternatives";
  - size "{money} held directly", or "{share} through funds";
  - confidence: "Verified exposure: the stock is held directly. The rating change is dated firm research, not a price forecast." or "Held only inside broad funds."
- **Client:** material, status "respond", action "Respond to the client", size "client asked".

### 4.13 Advisory value (`D.value(hh, costs)`) and the value case

**Inputs:** take the program and stay options from the costs.
- **Equity in the program** = equity share of the brokerage tactical target × amount.
- **Direct-indexed amount** = the smaller of that equity, or 40% of the amount.
- **Direct indexing is available** when the household is eligible and that amount is at least $250K.

**Recurring value:**
- **er** = (program er − stay er) × amount: the expected-return gain before costs.
- **Harvesting tax value** = 2% × direct-indexed amount × the long-term rate.
- **Direct-indexing fee** = direct-indexed amount × 20 bp.
- **harvNet** = tax value − fee.

Both harvesting figures are 0 when direct indexing is not available.

**One-time items** (from the routing):
- gains = positive gains on transfer rows;
- year-one gain = the smaller of gains or the gain budget;
- losses now = the losses on harvest rows;
- year-one tax before losses = year-one gain × lt;
- year-one tax after losses = max(0, year-one gain − losses now) × lt;
- tax if all at once = gains × lt.

**Fee and net:**
- inc = program total − stay total;
- quant = max(0, er) + max(0, harvNet);
- **net = er + harvNet − inc**;
- cover = quant ÷ inc, when inc > 0.

**`valueCase(hh, costs)`**: what the proposal screen uses.
- **Status:**
  - "blocked" if not eligible;
  - "stay" if the allocation finding is monitor or none and net < 0;
  - else "ready".
- **Reasons to stay** (balance, not the lead):
  - net < 0: "The benefits that can be estimated (about {quant} a year) cover about {cover%} of the higher fee; ongoing advice, planning and risk management make up the rest."
  - Volatility rises at the target: "Expected volatility rises at the CIO allocation ({a} → {b}); the case is about diversification and advice, not lower volatility."
  - Fund cost below 15 bp: "Today's funds are already low-cost (about {bp} bp), so fund savings are small."
  - Turnover 15% or less: "Trading is light (about {turnover} of the portfolio a year), so included trading saves only about {commissions} a year."
  - Not eligible: "Not eligible for the program: {reason}."
- **Fits:** the top three non-blocked strategies (4.15).
- **Plan phrase by finding kind:**

  | Kind | Plan phrase |
  |---|---|
  | conc | "a tax-aware plan to reduce {SYM}" |
  | risk | "a plan to bring volatility back into the profile band" |
  | cash | "a plan to invest the cash in steps toward the CIO allocation" |
  | perf | "a review of the funds trailing the CIO allocation" |
  | others | "ongoing rebalancing to the CIO allocation" |

- **Managed-account-only capabilities**, applied to this client:
  1. When direct indexing is available: "Direct indexing: losses harvested stock by stock". Text: owning the index companies lets the manager realize losses; a fund cannot pass its losses through; about {harvNet} a year after the {fee} manager fee (planning estimate).
  2. Always: "Custom exclusions and tilts".
     - With concentrated names (above the threshold): "Leave {names} out of the direct index and tilt away from {their sectors, lower case}, so new money diversifies instead of adding to the concentration."
     - Otherwise: "Leave out stocks or sectors the client chooses, for values or employer reasons; a fund must hold its whole index."
  3. When gains > $1,000: "Tax-managed transition of existing stocks". Text: a tax-managed SMA takes {transfer symbols} in as they are and sells them over time within the {budget} yearly gain budget, instead of a one-time sale.
  4. When the household holds a muni fund (not an individual bond) and its bracket is at least 32%: "Individual municipal bond ladder". Text: replace {funds} ({value}) with individual bonds laddered over 1 to 10 years, with known maturities and tax-exempt income; add "and the {loss} loss in the fund can be harvested in the switch" when the fund's loss is above $1,000.
  5. Always: "Tax-aware rebalancing across accounts". Text: rebalancing to the CIO allocation uses losses first, stays within the gain budget, and checks wash sales across the household's accounts.

### 4.14 Workflow lifecycle (`D.life`, `D.group`)

**Assessment statuses (`STATUS`):** label, tone, short label.

| Status | Label | Tone | Short |
|---|---|---|---|
| review | Review needed | warn | Review |
| ready | Ready for client discussion | good | Discuss |
| specialist | Specialist review | info | Specialist |
| blocked | Not eligible | bad | Not eligible |
| monitor | Monitor | neutral | Monitor |
| none | No action | neutral | No action |
| stay | Stay in brokerage | neutral | Stay |
| defer | Defer | neutral | Defer |
| unsuitable | Not suitable | neutral | Not suitable |
| respond | Respond to client | warn | Respond |

**Lists:**
- The advisor can set: ready, review, specialist, stay, monitor, defer, unsuitable.
- **Reasons:** Tax cost too high; Trading restriction; Insufficient client value; Poor fit for the client; Client declined; Missing data; Timing: revisit later; Other.
- **Close outcomes:** Discussed with the client; Proposal submitted for review; Referred to the specialist; Client declined; No action needed after review.

**Lifecycle from a disposition:**
- None → Open.
- Has a close outcome → Closed, with the outcome as the note.
- Status stay, unsuitable or defer:
  - with a reason → Deferred (defer) or Closed with "{label}: {reason}";
  - without one → still Open, flagged as needing a reason. Note: "Add a reason to defer it" or "Add a reason to close it".
- Monitor → Monitoring.
- Anything else → Open, "Advisor assessment: {label}".

**Group:**
- Closed → done.
- Deferred or monitoring → monitor.
- Status specialist, or a bad action tone → specialist.
- No disposition and status monitor or none → monitor.
- Otherwise → action.

### 4.15 The shared queue (`D.queue()`), on baseline settings

**`concList()`:** every symbol, per household, whose look-through share is above the alert threshold and that is also held directly.
- Each entry: key "hh:SYM", share, direct value, excluded flag (share > 50%), and position flags.
- Sorted by share, descending.

**Per household, add rows in this order:**

1. **Allocation row** (`ws1:<id>`): added when the finding is not "none", unless its kind is conc or gate for a symbol that already has a position row.
   - **Type:**

     | Kind | Type |
     |---|---|
     | risk | Volatility above the profile band |
     | cash | Volatility below profile: large cash |
     | perf | Trailing the CIO allocation |
     | drift | Drift from the CIO allocation |
     | gate | Not eligible for the program |
     | conc | Single-company concentration |

   - **Action pill:**
     - gate → "Not eligible; specialist route" (bad);
     - drift → "No action needed now" (info);
     - else the eligibility short label and its tone.
   - **Priority:** review 3, specialist 3, ready 2, monitor 1.
2. **Position rows** (`ws3:<id>:<SYM>`), one per concentration entry.
   - **Action:**
     - over the limit → "Not eligible; specialist route" (bad);
     - insider → "Conditions: insider rules" (warn);
     - else "Conditions: lots and tax" (warn).
   - **Status:** specialist, review or ready.
   - **Next:** "Refer to the concentrated stock specialist" or "Review staging and alternatives".
   - **Priority:** 2.5 + 3 × share.
   - **Related note:** "Also flagged in the allocation review" when the allocation finding is about the same symbol.
3. **Event rows**, for each news item with a score above 1 that is material.
   - **Merging:** an event merges into an existing row as a related line ("{date} · {source}: {headline} ({short size})") instead of adding a row, when:
     - a market event's biggest-hit holding already has a position row; or
     - a view event finds the household's allocation row, or failing that its position row.
   - **Otherwise add `ws4:<event>:<id>`:**
     - Action "Manager decides" (info) for a manager-run research review, else "Advisor can act" (good).
     - Priority: respond 3.2, review 2.2, else 1.5.
4. **Pathway screen rows** (4.17). Skip the excess-cash screen when the allocation finding is already "cash".
5. **Value row** (`ws2:<id>`), "Advisory program discussion". Added when all of these hold:
   - the allocation status is review or ready;
   - the household is eligible;
   - brokerage is at least $250K.

   Details:
   - Impact: "est. value {quant} vs fee +{inc} a year (illustrative)".
   - Next: "Prepare the value story".
   - Status: ready. Priority: 1.2.

**Then for every row:**
1. enrich it (4.18);
2. attach the advisor's disposition by key;
3. compute its group.

Sort closed last, then by priority, descending.

**Reference:** 27 rows, of which 25 are action, 1 specialist and 1 monitor.

| Kind | Rows |
|---|---|
| allocation gap | 3 |
| embedded gains and losses | 5 |
| individual bonds | 2 |
| excess cash | 2 |
| high-cost funds | 2 |
| advisory proposal | 4 |
| concentrated stock | 6 |
| events | 3 |

### 4.16 Pathway basics (`P.amt`, `P.transition`, `P.segment`, `P.forgone`, `P.gapText`, `P.options`, `P.lowerCost`)

**`P.amt(hh)`** = brokerage total.

**`P.transition(hh)`**, from the routing:
- **Parts:** the sum by route (inkind, swap, transfer, harvest, instep, basis, stay, reserve).
- **Gains:**
  - gains = positive gains on transfer rows;
  - year-one gain = the smaller of gains or the gain budget;
  - sold = transfer value × year-one gain ÷ gains;
  - losses = losses on harvest rows.
- **Alignment:**
  - movable = total − stay − reserve;
  - aligned = inkind + swap + harvest + instep + sold;
  - pct = aligned ÷ movable.
- **Tax:**
  - gross = year-one gain × lt;
  - net = max(0, year-one gain − losses) × lt;
  - carry = losses beyond the year-one gain.
- **Trading:**
  - amount traded = 2 × (sold + harvest + swap) + instep;
  - cost = amount traded × 5 bp.
- **noBasis** = the basis part.

**`P.segment(hh)`:**
- g = positive routing gains ÷ brokerage total.
- "hard" if any of these holds:
  - age is 80 or over;
  - g ≥ 15%;
  - an A share class is held and g ≥ 3%.
- "medium" if g ≥ 3%.
- "low" otherwise.

**`P.forgone(hh)`**, from the brokerage tactical gap:
- erNow and erT, volNow and volT;
- yr = (erT − erNow) × brokerage;
- five = brokerage × ((1 + erT)^5 − (1 + erNow)^5).

**`P.gapText(hh)`:** joins with " and " the group differences above 1 point, for example "a 2.3 pts equity underweight":
- "excess cash";
- "an equity underweight" or "an equity overweight";
- "a fixed income underweight" or "a fixed income overweight".

Capitalise the first letter. If there are none: "{n} asset classes outside tolerance".

**`fitStrategies(hh, gap, attribution, elig)`:** score each strategy.

| Condition | Score change | Why line |
|---|---|---|
| per underweight class it covers (gap < −1 point) | +0.15 | "Closes gaps in {classes}" |
| covers a class of a detracting holding | +0.20 | "Replaces detractors in {classes}" |
| tax-managed and transfer value > 25% of the total | +0.25 | "Manages embedded gains over time" |
| can exclude and any look-through share > 10% | +0.25 | "Can exclude the concentrated stock" |
| CIO model | +0.30 | "Follows the CIO allocation for the profile" |
| minimum above 60% of the total | −0.50 | "Minimum {money} is large for this portfolio" |
| alternatives-only when HF/PE are not underweight | −0.40 | — |

- If the household is not eligible: score 0, blocked, why "Not available: {reason}".
- Clamp the score to 0–1. With no why lines, show "General fit".
- Keep the top four by score.

**`P.options`** = the non-blocked fits with score > 0.05. Empty when not eligible.

**`P.lowerCost`** = the index option from the default costs.

### 4.17 Pathway screens (`P.screens(hh)`), use cases 2, 3, 4, 5 and 12

Run only for eligible households with brokerage assets. Every row carries the eligibility short label as its action and "ws" = path.

**Use case 2 (`p2:<id>`), embedded gains and loss harvesting.** Runs when the household is taxable and gains ≥ $5,000 or losses ≥ $25,000.
- Type: "Embedded gains and loss harvesting".
- Trigger: "Taxable account: {gains} of long-term gains and {losses} of unrealized losses ({symbols on transfer and harvest rows})". Drop the losses part when there are none.
- Size: "{gains} embedded gains; {losses} harvestable losses".
- Value:
  - with gains: "Tax spread over time: year one ≈ {tax net} after losses, not ≈ {gains × lt} at once";
  - otherwise: "{losses × lt} of tax value from harvested losses".
- Pathway: "Tax-efficient transition into managed accounts; direct indexing and loss harvesting".
- Flow: both. Next: "Review the transition plan and the gain budget". Status ready. Priority 2.4.

**Use case 3 (`p3:<id>`), individual bonds held in brokerage.**
- Soon = the bonds callable within 90 days of 2026-10-24.
- Type: "{SYM} callable on {date}" if any is soon, else "Unmanaged individual bonds".
- Trigger: "{n} unmanaged individual bond(s) ({value})", plus "; {SYMs} callable within 90 days" when any is soon.
- Size: "{value} in individual bonds, {share} of brokerage".
- Value:
  - soon: "Call proceeds of {value} need reinvesting; a managed ladder reinvests and monitors credit";
  - otherwise: "Credit monitoring and laddered reinvestment instead of ad-hoc replacement".
- Pathway: "Managed fixed income SMA (individual-bond ladder); call and maturity proceeds go into it". Flow shift.
- Next: "Plan reinvestment before the call date" or "Review a managed ladder".
- Status and priority: review and 2.3 when soon, else ready and 1.4.

**Use case 4 (`p4:<id>`), excess cash.** Runs when investable cash > 5% of brokerage.
- Type: "Excess cash above target".
- Trigger: "Cash {total}: {investable} is above the CIO target after a {reserve} reserve", plus " (including next year's needs)" when there are needs.
- Size: "{investable} excess cash, {share} of brokerage".
- Value: "Scenario: ≈ {investable × max(0, erT − cash 1Y return)} a year of expected return at the CIO allocation ({erT}) vs cash ({4.6%}), under capital market assumptions; not a forecast".
- Pathway: "CIO-aligned advisory strategy, invested in steps". Flow shift.
- Next: "Agree the reserve and the pace of investing". Priority 2.2.

**Use case 5 (`p5:<id>`), high-cost funds.** Brokerage non-cash holdings at or above 50 bp.
- Type: "High-cost funds".
- Trigger: "{SYM} {bp} bp ({class} shares), …: above the 50 bp threshold".
- Size: "{value} in funds costing {weighted bp} bp on average".
- Value: "≈ {fund cost − value × 5 bp} a year less in fund expenses with model funds (5 bp), before the program fee".
- Pathway: "Equivalent advisory strategy via tax-efficient transition". Flow shift.
- Next: "Compare the equivalent strategy, after taxes". Priority 1.6.

**Use case 12 (`p12:<id>`), commissions.** Runs when commissions (brokerage × turnover × 0.75%) are at least 50% of the program fee.
- Type: "Commissions rival the program fee". Pathway: "Advisory enrollment (decision support)".
- No household triggers it.

### 4.18 Enrichment and the six steps (`P.enrich`, `P.steps`)

**Enrichment.** Rows from the screens already carry their use case. Every other row gets these fields:
- **Allocation row:**
  - Use case 4 if its finding kind is cash, else 1.
  - Trigger:
    - cash: "Cash {total} ({share} of brokerage): {investable} is above the CIO target after a {reserve} reserve";
    - else: "Brokerage portfolio outside the CIO tolerance for the {profile} profile ({n asset classes outside tolerance})".
  - Size: "{gapText}; {first evidence line in lower case}".
  - Value: "Illustrative scenario difference (modeled): ≈ {erT − erNow, 2 decimals} a year of expected return, ≈ {five} over 5 years under capital market assumptions; not a forecast or a guaranteed benefit". When yr ≤ 0, show the volatility comparison instead.
  - Pathway:
    - not eligible: "Excluded: specialist route";
    - cash: "CIO-aligned advisory strategy, invested in steps";
    - else: "Rebalance into the advisory program via a CIO model or managed portfolio".
- **Position row:**
  - Use case 8.
  - Trigger: "{SYM} above the 10% concentration threshold".
  - Value: "A 30% fall would cost ≈ {0.3 × share × total}".
  - Pathway:
    - excluded: "Excluded (above 50%): exchange fund, options overlay or staged sales in brokerage; specialist", flow "na";
    - otherwise: "Tax-managed SMA, tax-efficient transition, direct indexing with the stock excluded", flow "lift".
- **Event row:**
  - Use case 10.
  - Trigger: "{first related line} · {headline}".
  - Value: "Feeds the allocation or position review".
  - Pathway: "Event-led entry to the allocation review". Flow na.
- **Value row:**
  - Use case 7.
  - Trigger: "Opportunity accepted: advisor positioning".
  - Size: "{brokerage} brokerage assets".
  - Value: "≈ {quant} a year of estimated value vs fee +{inc}".
  - Pathway: "Advisory program: the client story and proposal".

**Short pathway names (`pwOf`):**

| Use case | Short name |
|---|---|
| 1 | CIO model rebalance |
| 2 | Tax-efficient transition + direct indexing |
| 3 | Managed bond ladder |
| 4 | Invest in steps into a CIO strategy |
| 5 | Equivalent strategy, tax-aware swap |
| 7 | Client story and proposal |
| 8 | Tax-managed SMA + direct indexing, or "Specialist route (excluded)" |
| 10 | Event-led review |
| 12 | Advisory enrollment |

**The six steps for any row:**
1. **Trigger:** the row's trigger.
2. **Size the gap:** the row's size.
3. **Value the gap:** the row's value, else the modeled scenario sentence.
4. **Match options:**
   - "{n} fitting strategies: {names}; lower-cost alternative shown: {index name} ({bp} bp)";
   - when not eligible: "Program, SMA and direct-indexing paths blocked; specialist route".

   The checks look for "lower-cost alternative shown".
5. **Plan transition:**
   - Lead-ins:

     | Use case | Lead-in |
     |---|---|
     | 3 | "The bonds are held to their call or maturity; the proceeds go into a managed ladder instead of sitting in cash. Household: " |
     | 5 | "High-cost funds are swapped into the equivalent strategy ({swap symbols}). Household: " |
     | 4 | "Cash moves in monthly steps over six months. Household: " |

   - Then the plan: "Invest in steps for {instep} of cash; tax-efficient transition for {transfer} of appreciated holdings; {inkind + swap} moves in kind or swaps; ≈{pct}% aligned in year one; tax {not estimated for lots without basis; }≈ {tax net} after losses, trading ≈ {trading}".
   - Not eligible: "Not available: {reason}. Specialist plan first; staged sales in brokerage."
6. **Client story** (by the proposal review state):
   - "Submitted for compliance review";
   - "Advisor reviewed; ready to present";
   - "Proposal and story drafted, ready for advisor review";
   - not eligible: "Story explains the specialist route first".

### 4.19 Exclusive buckets and the amounts (`P.buckets`, `P.amounts`)

**Buckets.** Every routing row goes into exactly one bucket:

| Bucket | Label | Which rows |
|---|---|---|
| move | Moves now (in kind) | inkind, swap, transfer, harvest, instep |
| gated | Held for cost basis | basis |
| kept | Kept in brokerage | reserve and stay |
| excluded | Excluded (above the 50% limit) | everything, when the household is not eligible |

**Timing overlay** (a note only, never an amount):
- bonds:
  - "Callable {date}: proceeds can be reinvested then";
  - or "Matures {year}: proceeds can be reinvested then";
- reserve: "Protected reserve and near-term needs".

The buckets add back to the brokerage total exactly.

**Amounts:**

| Amount | Formula |
|---|---|
| identified | brokerage total |
| eligible | move + gated (0 if excluded) |
| now | move (0 if excluded) |
| later | one entry when gated > 0: amount gated, gate "Cost basis on file", owner Operations |
| kept | kept (0 if excluded) |
| excluded | excluded |
| held list | each gated or kept row with its reason, see below |
| overlays | non-reserve rows with a timing note |
| needsLater | cash needs dated after 2027 |
| reserveMissing | true when the household has no liquidity reserve on file |
| confidence | Low if excluded; Medium if anything is gated or the reserve is missing; else High |
| alignY1 | transition pct (0 if excluded) |
| repositionOverTime | max(0, move − aligned) |

Reasons in the held list:
- "awaiting cost basis";
- "liquidity reserve and near-term needs";
- the overlay or why text cut at the first colon, in lower case, for example "matures 2032", "callable 2026-12-15".

### 4.20 Why now, cues, blocker, primary (`P.whyOf`, `P.catalyst`, `P.cues`, `P.blocker`, `P.primary`)

**Why now, by use case:**

| Use case | Wording |
|---|---|
| 4 | "{investable} of cash sits above the CIO target after a {reserve} reserve" |
| 8 | "{SYM} is {share} of the account", plus ", above the 50% limit" when excluded |
| 1 | risk kind: "Expected volatility {v} is above the {profile} band"; else "The allocation is outside CIO tolerance: {gapText lower case}" |
| 2 | "{gains} of embedded gains and {losses} of harvestable losses call for a tax-aware transition" when gains > $1,000; else "{losses} of harvestable losses can offset future gains" |
| 3 | "{type}: the proceeds need a plan" when callable; else "Individual bonds are unmanaged" |
| 5 | "Funds costing up to {max bp} bp where model funds cost 5 bp" |
| others | the type |

**Catalysts** (used in the client-case headline and in the ranking):
- "{meeting type lower case} in {n} days" when the meeting is within 7 days;
- "bond call within 90 days";
- "client asked a question".

**Cues** (landing; key and label):

| Key | Label | When |
|---|---|---|
| meet | Meeting in {n} day(s) | meeting within 7 days |
| date | Call date {date} | a callable-bond row is open |
| ask | Client request | an open client-question row |
| basis | Tax-basis blocker | any basis part |
| amt | Large movable amount | now ≥ $10M |

**Blocker**, first that applies (text, owner):
1. not eligible: "Above the 50% single-security limit" (Specialist);
2. basis: "{money} without cost basis" (Operations);
3. insider: "Insider rules for {SYMs}: pre-clearance" (Compliance);
4. manager-run: "Manager-run sleeve: the manager decides" (Manager);
5. else: "Suitability determination" (Advisor).

**Primary row** = the open row with the highest weight. If no row is open, use all rows.

| Row | Weight |
|---|---|
| position, excluded | 4 |
| position, otherwise | 3 + min(0.9, 2 × share) |
| excess cash | 3.2 if investable > 10% of brokerage, else 1.5 |
| allocation | 2.8 if review, else 1 |
| bonds | 2.6 if callable, else 1.2 |
| gains | 2 |
| high-cost | 1.5 |
| event | 0.8 |
| trading | 0.5 |
| value row | 0.1 |

### 4.21 Household state and ranking (`P.hstate`, `P.households`)

**Household key:** "hh:<id>" holds the household-level disposition and the chosen route (`S.choice`).

**Step**, first that applies:
1. lifecycle is closed, monitoring or deferred → outcome;
2. no disposition, or status not in ready, review or specialist → assess;
3. not eligible, or status specialist → specialist;
4. no route chosen → paths;
5. proposal review state is not "compliance" → proposal;
6. else → handoff.

**Next label and target step:**

| Step | Next label | Goes to |
|---|---|---|
| assess | Review assessment | assess |
| paths | Compare paths | paths |
| proposal | Prepare proposal | proposal |
| handoff | Complete handoff | handoff |
| specialist | Request specialist | assess |
| outcome | "{lifecycle label}: {note}" | assess |

A not-eligible household at assess shows "Request specialist".

**Filter value per household:**
- "waiting" when excluded or at the specialist step;
- "propose" at the proposal or handoff step;
- "done" when the lifecycle is not open;
- else "discuss".

**Ranking** (auditable, stated under the table):
1. not excluded before excluded;
2. then households with any catalyst before those without;
3. then by amount movable now, descending.

Reference order: Henderson, Okonkwo, Kaplan, Castellano, Brennan, Delgado.

### 4.22 Routes (`P.paths`), stay, handoff

**Costs:** the household's costs at amount = movable now rounded to $1,000 (at least 1).

**Common feasibility checks** (text, done flag, owner):
- "Suitability determination" (Advisor, open);
- "{money} without cost basis: no sale or tax estimate until found" (Operations, open), if basis;
- "Insider shares: pre-clearance and trading windows" (Compliance, open), if insider;
- "Manager-run sleeve stays with its manager" (Manager, done), if manager-run.

**Not eligible: one route only, `specialist`.**
- Name: "Specialist route for the position".
- Why: "The program is not available above 50%".
- Trade-offs:
  - "No program fee or enrollment now";
  - "Position risk stays until a plan is in place".
- Account: "Nothing moves into the program now".
- Trading: "Staged sales in brokerage within trading windows".
- Tax: "Planned by the specialist; year one within the gain budget".
- Cost: "{stay cost on the full brokerage amount} a year in brokerage today". See pitfall 9.
- Feasibility:
  - "Concentrated stock specialist review" (Specialist);
  - "Pre-clearance" (Compliance), if insider.
- Approver: "Specialist and advisor". Suggested.

**Eligible households.** Years to align = ceiling(gains ÷ gain budget), or 1.

1. **`rebalance`: "Transfer and rebalance now".**
   - Why: "Fastest route to the CIO allocation".
   - Trade-offs:
     - "Highest year-one tax";
     - "Full alignment in year one".
   - Account: "{now} moves in kind at enrollment".
   - Trading: "Repositioned in year one (≈100% aligned)".
   - Tax:
     - "≈ {max(0, gains − losses) × lt} in year one after losses (planning; depends on validated lots and rates)";
     - or "Little or no gain to realize".
   - Cost: "{program total} a year ({bp} bp), steady state on {now} from enrollment, vs {stay total} today".
   - Feasibility: common. Approver: "Advisor; compliance reviews the proposal".
2. **`phased`.**
   - Name:
     - "Phased and tax-aware: cash in steps, appreciated holdings over time" when there is instep cash;
     - else "Phased and tax-aware transition".
   - Why:
     - "Keeps year-one tax within the gain budget" when there are gains;
     - else "Invests excess cash gradually".
   - Trade-offs:
     - "Year-one tax ≈ {tax net}";
     - "Full alignment takes about {n} years", or "About six months to align".
   - Account: as for rebalance.
   - Trading: "≈{pct}% aligned in year one; {instep} cash invested over six months; the rest over about {n} years". Leave out the parts that don't apply.
   - Tax: "≈ {tax net} in year one after losses (planning; …)".
   - Cost: as for rebalance, plus "; trading ≈ {trading}".
3. **`managed`.** Only when direct indexing is available and either:
   - there are concentrated names; or
   - gains > 10% of now.

   Fields:
   - Name: "Managed accounts: tax-managed SMA and direct indexing", plus " excluding {names}".
   - Why:
     - "Keeps {names} out of new money and harvests losses";
     - or "Harvests losses stock by stock".
   - Trade-offs:
     - "Higher cost: {sma bp} bp vs {program bp} bp";
     - "Harvesting ≈ {harvNet} a year after the manager fee (modeled)".
   - Account: "{now} moves in kind at enrollment; a manager takes existing stocks".
   - Trading: "Concentration reduced over about {n} years", or "Months".
   - Tax: "≈ {tax net} in year one; harvesting ≈ {harvNet} a year after the manager fee (planning)".
   - Cost: the SMA total, worded as for rebalance.
   - Feasibility: common, plus "Product eligibility and minimums ($250K)" (Product team, done when now ≥ $250K).
   - Approver: "Advisor; product team confirms; compliance reviews".

**Starting point** (exactly one per household):
- managed, if there are concentrated names and the managed route exists;
- else phased, if gains or instep cash > 0;
- else rebalance.

**Stay in brokerage (`P.remain`):** the stay cost and the index option at the full brokerage amount.

**Handoff (`P.handoff`):**
- **Items:**
  1. "Strategy and pace selected" (Advisor; auto-done when a route is chosen);
  2. "Proposal submitted for compliance review" (Advisor; auto-done when the proposal review state is compliance);
  3. then the implementation prerequisites from `D.ready` with product true.
- **Invest-in-steps schedule:** six equal monthly amounts, Nov 2026 to Apr 2027, when there is instep cash.

### 4.23 Five stages (`P.stages(hh, key)`)

| Stage | State | Note |
|---|---|---|
| Identify | always ready | "Opportunity found by an approved screen", or when excluded "Found, but outside the addressable universe: {reason}" |
| Analyze | ready when the disposition is ready, review, specialist or respond; blocked when stay, unsuitable, defer or monitor; else pending | "Advisor decided to pursue" / "Not pursued: {label} · {reason}" / "Advisor to decide whether to pursue" |
| Design | blocked if excluded; ready if a choice is recorded; else pending | "Program paths blocked; specialist route" / "Selected: {choice}" / "Select a strategy and pace · {n} to clear" (proposal items other than the limit) |
| Propose | blocked if excluded; ready when submitted for compliance; else pending | "No program proposal above the limit" / "Submitted for compliance review" / "Advisor reviewed; submit for compliance" / "Story and proposal drafted; advisor review needed" |
| Implement | pending once handed off, otherwise always blocked | "Handed off: operations to enroll (prototype)" / "Not cleared: {n} prerequisites outstanding" |

Each stage also carries its "does", "decide" and "control" texts from the table in section 1.

### 4.24 Internal book view (`P.book`)

- **Addressable** = Σ amount movable now over eligible households.
- **Segments** = that amount by tax difficulty (low, medium, hard).
- **Excluded** = brokerage of excluded households + "stays" parts.
- **Revenue today** = Σ now × 12% × 0.75%.
- **Revenue in the program** = Σ program fee on each household's now.
- Express both in bp of addressable.

**Reference:**
- addressable $85.21M of $91.89M brokerage;
- $3.20M excluded;
- low $26.90M, medium $2.15M, hard $56.16M;
- revenue about $77K → $509K;
- about 9 bp → 60 bp.

### 4.25 Firm intelligence (`D.catalog`, `D.intelFor`, `D.bookStatus`)

**Catalog** = the news items except the client question (auto-evaluated) plus `DATA.intel`, newest first.
- For news items:
  - stance from the downgrade ("{SYM}: {to} (was {from})") or the CIO view ("{class}: {view} (was {was})");
  - client use allowed except for market news;
  - entitlement "All advisors" or "All advisors (third-party news)".

**`D.intelFor(item, hh)`:**
- superseded → "na";
- region-sector:
  - "unknown", when the household holds international or emerging equity: "{value} international equity". Why: the look-through for {SYMs} has no country-by-sector data, so {region} bank exposure cannot be measured;
  - otherwise "none";
- auto items → the event rules (matched if material, monitor if exposed, none if not exposed);
- research:
  - "matched" if held directly ("Mention at the next review");
  - "monitor" if more than 0.1% through funds;
  - else "none";
- view and market → material is matched; any rows or exposure ≥ 0.1% is monitor; else none.

**Book status:**

| Situation | Status label |
|---|---|
| superseded | "Superseded: not evaluated" |
| not auto and not yet analyzed | "Not yet evaluated" |
| any match | "Affects my book: {n} households" |
| any unknown | "Not evaluated for {n} households: insufficient data" |
| otherwise | "No identified impact" |

Analyzing or publishing never adds rows to the queue. Only "Add to opportunities" on a material match does: key "ws4f:<item>:<id>", status review.

---

## 5. Charts

All charts are hand-written SVG with no library, so the page works offline.

**Tooltip and escaping:**
- `CH.esc` escapes &, <, > and quotes.
- Every mark carries a `data-tip`. Create one floating tooltip element once, and on mousemove over any `[data-tip]` show it 14px from the pointer, kept inside the viewport. Hide it otherwise.
- Keep `svg text { pointer-events: none }` so labels never block clicks.

**Base charts:**
- **`CH.donut(segments, {size, center, sub, label})`:** part-to-whole.
  - Outer radius size/2 − 4; inner radius 62% of that.
  - Slices start at 12 o'clock, go clockwise, and are separated by a tiny gap (about 0.012 radians).
  - Centre: a big value, shrunk to fit the hole (font size = min(24, hole radius × 1.5 ÷ (characters × 0.56))), plus a small sub-label.
  - Each segment is `{id, label, value, color, tip}`.
- **`CH.gauge({w, min, max, lo, hi, today, after, big, sub, minLab, maxLab, bandTip})`:** risk against the band.
  - A semicircle rail with the band shaded translucent green between lo and hi.
  - A dark tick for today and a thicker brand tick for the target.
  - The big value and sub-line in the centre; min and max labels under the ends.
- **`CH.waterfall({steps, start, startLab, endLab, fmt, dfmt, upGood, w, label})`:** why a figure changes.
  - Horizontal rows: a label column (about 118px; labels cut at 18 characters), the bars, and a right-aligned value.
  - First row: a gray bar to the start value.
  - Then one floating bar per step `{label, delta, tip}`, from the running value to the new one: green when the move is good, red when bad (`upGood` says which direction is good).
  - Last row: a dark bar to the end value, in bold.
  - Pad the domain by 8%.

**Heat shading** for table cells, `heat(v, bad, good)`:
- Normalise v to 0–1 between bad and good.
- Above 0.5: green, rgba(11,122,75, 0.08 + 0.3 × (t − 0.5) × 2).
- Below 0.5: red, rgba(162,50,62, 0.08 + 0.3 × (0.5 − t) × 2).
- Missing values: the inset color.

**Chart colors:**
- Categorical colors in a fixed order, never cycled: c1 blue, c2 orange, c3 aqua, c4 yellow, c5 pink, c6 green, c7 violet, c8 red; c-other gray.
- No dual axes.
- Every chart sits beside a table or legend with the numbers.

**Three workspace charts.** All of them:
- are `viewBox` based, full width up to their stated width;
- carry `role="img"` and an aria label;
- use 11px muted axis text, 12.5px row labels and bold values.

**`CH.bands(rows, {w, left, fmt, label})`: allocation against tolerance bands.** One row per class or group, 30px tall.
- Row label on the left, value text right-aligned.
- Light vertical grid at 0, half and max, with axis labels at the bottom.
- In each row:
  - a rounded tolerance band (16px tall, soft green fill) from max(0, target − tolerance) to target + tolerance;
  - a short vertical tick at the CIO target;
  - a thin link line from target to today;
  - a 6px circle at today: hollow inside the band, filled red (`bad`) outside.
- Tooltips: "tolerance a–b", "CIO target x", "today x · outside the band".
- Max = 1.08 × the largest of today or the band top.
- Use w 360 inside the two-column panel.

**`CH.line(points, {w, h, th, thLab, fmt, label})`: share by year.**
- Area plus a 2.5px line in brand color.
- Hollow point markers with tooltips.
- Year labels under each point.
- A dashed threshold line (color c4) labelled at its right end, for example "target 10.0%".
- Y from 0 to 1.12 × the largest value, with three gridlines.

**`CH.tree(steps, result, {w})`: decision path.** Each step is `{q, a, yes, out}`.
- Steps are stacked boxes on the left, 300px wide, one every 58px. Each box shows the question in bold and the answer in small muted text, cut at 46 characters.
- A connector runs down the left of the boxes.
- A horizontal connector runs to an outcome box on the right.
- When the answer is yes, the question box, the connector and the outcome box take the brand color and tint. Otherwise the outcome box is dashed and faint.
- Under the steps, a full-width brand-filled result box: a small "RECOMMENDED PATH" caption and the result text, wrapped to two lines if longer than 92 characters.

**Reconciliation bar** (HTML, not SVG):
- a 14px rounded bar split into the non-zero buckets, in brand, warn, c-other and bad, with 2px gaps;
- a legend underneath: swatch, label and bold amount;
- then "= {total} identified ✓" (or "≠" if they don't add up).

---

## 6. Visual design and layout

**Tokens.**
- Define them as CSS custom properties on `:root`.
- Redefine the dark set inside `@media (prefers-color-scheme: dark)`, guarded by `:root:not([data-theme="light"])`, and again under `:root[data-theme="dark"]`.
- Give `body` the canvas background explicitly.

| Token | Light | Dark | Use |
|---|---|---|---|
| canvas / paper / paper-2 / inset / hover | #EEF0F3 / #FFFFFF / #F6F7F9 / #EEF1F4 / #F2F5F7 | #0B0E13 / #141922 / #191F29 / #10151D / #1B222D | page, cards, soft panels, wells, hover |
| fg / fg-2 / muted / faint | #141A23 / #3D4655 / #687282 / #98A1AE | #E6E9EF / #B6BDC9 / #8A93A1 / #5F6876 | text levels |
| line / line-2 | #DDE2E8 / #E9ECF0 | #262E3B / #1F2631 | borders |
| brand / brand-2 / brand-tint / on-brand | #0C5D51 / #09493F / #E3F0ED / #F4FBF9 | #3FB7A0 / #2F9C88 / #10302A / #04140F | deep teal: primary buttons, active states |
| good / warn / bad | #0B7A4B / #9E5E12 / #A2323E | #40C48D / #D79A46 / #E0736F | status |
| good-tint / warn-tint / bad-tint | #E3F3EA / #F7EEDD / #F6E4E6 | #0F2A1F / #2A2214 / #2C171A | status backgrounds |
| c1…c8 | #2a78d6 #eb6834 #1baf7a #eda100 #e87ba4 #008300 #6250d6 #e34948 | #3987e5 #d95926 #199e70 #c98500 #d55181 #008300 #9085e9 #e66767 | chart categories |
| c-other | #A6ACB5 | #5E6672 | folded "other" |

**Scale and finish:**
- **Spacing:** 4, 8, 12, 16, 20, 24, 32px.
- **Radii:** 6px (`--r-s`), 10px (`--r-m`), 14px (`--r-l`).
- **Type scale:** 11, 12.5, 14 (base), 16, 20 and 28px.
- **Fonts:**
  - Public Sans 400/600/700 for the interface;
  - Newsreader 500 for page titles (`.serif`);
  - IBM Plex Mono for tickers (`.ticker`);
  - fall back to system-ui, Georgia and monospace.
- **Shadows:** a hairline shadow on cards (`--sh-1`); a large soft shadow (`--sh-2`) on dialogs, tooltip and the tour card.
- Numbers use `tabular-nums`.

**Base components** (the class names the screens use):
- **Top bar (`.top`):** sticky, white, with a bottom border; a flex row with a 16px gap. The brand mark is a 30px teal rounded square with a three-layer stack icon in on-brand color.
- **Layout (`.layout`):** a three-column grid with a 16px gap, a 1680px maximum width, 16px padding and `min-width: 0` on children.
  - **Cards (`.card`):** white, 1px border, 14px radius, hairline shadow.
  - The left list (`.journey`) and right panel (`.side`) are sticky below the top bar and scroll inside.
- **List entries (`.step`):** full-width buttons, each with:
  - a 10px status dot (`.dot`): red "act", amber "look", green "ok", gray "none", hollow ring "nav";
  - a 13.5px semibold title (`.t`);
  - a 12px muted sub-line (`.v`).

  The current entry (`aria-current="true"`) has a teal-tint background and a 3px teal left border. Group headings (`.grp`) are small uppercase muted labels.
- **Stage:**
  - `.stage-h`: a 28px serif h1, then a muted description (`.uc`);
  - `.lede`: a 15–17px sentence with bold numbers;
  - `.sec`: a section with a 16px top margin;
  - `.sec-h`: a flex header with an uppercase label (`.k`: 11px, bold, letter-spaced, muted) and a muted note (`.sub`);
  - `.panel`: a bordered box with a 10px radius and 12–14px padding; `.panel.soft` is paper-2;
  - `.grid2`: two equal panels;
  - `.split`: a chart beside a table;
  - `.disc`: 11.5px muted disclosure text under a hairline.
- **Buttons:**
  - `.btn`: bordered and rounded 8px, 13px semibold;
  - `.btn.primary`: teal fill with on-brand text;
  - `.btn.sm`: smaller;
  - `.link`: text button in brand color;
  - disabled buttons are faded and unclickable.
- **Pills:**
  - `.pill` is a small rounded status label, toned good, warn, bad or neutral (and `neutral info`);
  - `.act-pill` is the same shape, used for actionability and eligibility;
  - the `.xs` variant is smaller.
- **Controls:**
  - `.seg`: segmented buttons on an inset background; the pressed one (`aria-pressed="true"`) is white with a tiny shadow;
  - `.chips` / `.chip`: pill buttons, teal when pressed;
  - `.adjust`: a soft panel holding `.ctl` controls (label above with the live value in `.val`; teal range sliders about 220px; number inputs about 160px).
- **Tables (`.tbl`):**
  - 12.5px, muted headers, hairline row borders, right-aligned numbers (`.r`);
  - hover rows when clickable (`tr.click`), and a selected row (`.sel`);
  - wrapped in `.tw` for horizontal scroll;
  - 10px rounded color swatches (`.sw`);
  - `.up` is good-colored and `.down` is bad-colored text.
- **Figure rows (`.rows`):** each child is a flex row with a label on the left and a value on the right, separated by a hairline.
- **Comparison cards (`.cmp-cards` / `.pcard`):** an auto-fill grid of bordered cards at least 220px wide.
- **Research card (`.doc`):** a teal left border, a soft background and a small uppercase kicker (`.dk`).
- **Legend (`.legend`):** small inline swatches with labels.
- **Toast (`.toast`):** a dark pill at the bottom centre that fades in (`.on`).

**Responsive base:**
- **Up to 1320px:**
  - two columns (stage, then right panel at about 340px);
  - the left list spans the full width above as a horizontal scrolling strip, with group headings hidden;
  - two-panel grids stack.
- **Up to 880px:**
  - one column;
  - the right panel becomes a fixed bottom sheet showing a 54px handle with an "Open ▴" button (`.mob`), sliding up when opened (`.side.open`, max height 78vh);
  - top-bar facts are hidden.
- **Print:** hide the top bar, left list and right panel.

### Workspace layout and components

**Layout and responsive behaviour:**
- Column widths: left list 258px, stage fluid, right panel 340px.
- At 1320px and below:
  - the left list moves above as a horizontal strip;
  - the right panel is 330–352px.
- At 880px and below:
  - one column;
  - the right panel becomes the bottom sheet, with an "Open ▴ / Close ▾" toggle.

**Visual tone:** unchanged.
- light gray canvas;
- white 14px-radius cards;
- deep teal brand;
- serif page titles;
- small uppercase section labels (`.k`);
- tabular numbers.

**New components:**

| Component | Look |
|---|---|
| Breadcrumb (`.crumbs`) | 14px semibold buttons with 8px radius; the active crumb is brand text on brand tint; "›" separators in faint text; the "My book" crumb has a round brand badge with the open count |
| Market and research button (`.mr`) | outlined, 8px radius; brand border and text when active |
| Tour button | outlined brand pill, 12.5px bold |
| Prototype pill | an amber outlined pill button reading "Prototype · checks" |
| Summary card (`.sum`) | paper-2 background, brand-tinted left edge; header row with an uppercase label and a link; serif finding at about 20px; a "why" paragraph; gates as small banners (bad: red tint with "Blocker:", warn: amber tint with "Condition:"); three evidence lines; a two-column grid of trade-off rows and choice chips; a "Next step" line |
| Choice chips (`button.choice`) | rounded pills with an italic tag; the recommended one has a brand outline; pressed shows a ✓ and brand tint; blocked is disabled and faded |
| Expandable section (`details.dx`) | a full-width row with a rotating chevron, a bold title and a muted subtitle; the body is padded; its open state is remembered in `S.open` by id |
| Money tag (`.mt`) | a tiny uppercase outlined tag after a label: observed in fg-2, estimate in c1, modeled in c7, needs validation in warn on warn tint |
| Owner tag (`.own`) | a tiny bold tag in c7 on a 12% c7 tint |
| Priority cues (`.cue`) | 11px pills with a glyph: ◷ for meeting and call date (warn tint), ✉ for client request (brand tint), ! for tax-basis blocker (bad tint), $ for large amount (neutral) |
| Household stepper (`.hstep`) | four pill buttons with numbered circles joined by short lines; the current one is brand outline and tint; done ones show a ✓ on a good tint |
| Lead amount (`.lead-amt`) | two boxes side by side: a brand-tinted box with a 28px brand number, and a neutral "What stands in the way" box |
| Three-measure row (`.tri`) | three bordered boxes, label plus 17px value plus note |
| Route cards (`.pcards2`) | 2 columns by default; 3 or 4 at 1700px and wider; 1 at 700px and below. Each card is bordered and stacks label-over-value rows. The chosen card has a brand ring. The "Stay in brokerage" card has a paper-2 background. The starting-point badge is a small c1-tinted label on its own line |
| Feasibility list (`ul.feas`) | a 14px icon column: amber "…" when open, green "✓" when done |
| Task panel | key-value lines (label column 64px, muted); the five stages as small chips (green ready, red blocked, gray pending, brand outline on the current one); full-width primary next button |
| Source pills (`.src`) | market c1 tint; CIO brand tint; research warn tint; client c7 tint |
| Kind tag (`.uct`) | a small gray tag with the plain kind label |
| Intelligence card (`.icard`) | bordered card: type pill, date, status pills, book-status badge on the right (amber for a match, neutral otherwise), serif headline, abstract, house stance line, meta line, action buttons; superseded cards are faded |
| Checks dialog | a fixed overlay with a centred card (max about 720px); results grouped by area, with green ✓ and red ✕ |
| Tour | see 7.16 |

**Tone rules:**
- Amber marks a difference from the house model.
- Red is reserved for a breach of the client's risk profile, blockers and missing data.
- Never show firm revenue outside the internal management view, which carries an "internal · not client-facing" tag.

---

## 7. Screens, one by one

### 7.1 Head of every view

**`head(title, subtitle)`:**
- a serif h1;
- the subtitle, followed by an "About this workspace" link that toggles one paragraph of explanation for the current view.

**About texts:**

| View | Text |
|---|---|
| queue | A book-level opportunity scanner: approved screens across the advisor's households (allocation gap, embedded gains and loss harvesting, individual bonds, excess cash, high-cost funds, concentrated stock, news and research, trading economics). Each household's opportunities feed one advisory pathway, with the lower-cost alternative and staying in brokerage always shown. |
| ws1 | Compares each brokerage portfolio with the CIO strategic and tactical target for the client's risk profile, uses performance attribution to show which allocation and manager decisions drove under- or outperformance, sizes the gap in points and dollars, and shows what it costs in expected return and risk. |
| ws2 | Equips the advisor to tell the client a clear, balanced story about whether the advisory program is the better structure for them, covering value, pricing for value and the fiduciary model, using only approved content. |
| ws3 | Helps advisors reduce single-company risk at a pace set by the client's tax position. Accounts more than 50% in a single security are excluded from the addressable universe. |
| ws4 | Aligns market news, CIO views and research to a client's portfolio: which holdings and allocations are affected, what the CIO and research say, and what it means for the client. |
| path | Turns each opportunity into a dollar figure, a set of options and a specific, advisor-approved path into the advisory program: trigger, size, value, options, transition plan and client story. |

### 7.2 Top bar

From left to right:
1. **Brand mark:** a small brand square with a three-layer stack icon, then "Advisor workspaces" in bold over "Atlas · prototype v6.2".
2. **Breadcrumb:**
   - "My book", with the open-row count badge (27 at load);
   - on household and analysis views (not on the landing or Market and research), "› {household name}" (opens the household flow) "› {view label}";
   - view labels:

     | View | Label |
     |---|---|
     | ws1 | Allocation and performance |
     | ws2 | Client proposal |
     | ws3 | Concentrated position |
     | ws4 | Market and research |
     | household flow | the current step name, for example "Client case" |

3. **"Market and research" button**, shown active on that view.
4. A spacer.
5. **Facts:** "Illustrative data as of 2026-10-15".
6. **"Tour" button.**
7. **"Prototype · checks" pill.** Its title: "Decisions, drafts and approvals are kept in this page only; nothing is saved. Click to run the prototype checks."

There are **no use-case tabs.**

### 7.3 Left list (`entries()`)

| View | Contents |
|---|---|
| Landing (households) and household flow | Heading "Households by actionability". One button per household in ranking order: a status dot (navigation dot for excluded, hollow for an outcome recorded, amber otherwise), the name, and a sub-line ("Not eligible now", or "{now} now · {short route name}"). The current household is marked. |
| Landing (all opportunities) | "Group" entries with counts: All open, Needs action, Specialist or not eligible, Monitor or deferred, Closed. Then "Source" chips: All, Allocation, Concentration, Events, Value. |
| Allocation, Client proposal | "Households", sorted by status priority; each with "{status label} · {first evidence fragment}". |
| Concentrated position | "Positions above {threshold}": "{SYM} · {household}", with "{share} of the account", plus " · above program limit" or " · insider". |
| Market and research, My book impact | Filter chips (All sample events, Market, CIO, Research, Client). The note "A curated sample of 9 events, matched to your households. For everything published, use Firm intelligence." Events newest first: headline, then "{date} · {source pill} · {n} material" or "monitor only". |
| Market and research, Firm intelligence | "Type" chips with counts (All, Market, CIO, Research). "Book impact" entries with counts (All, Affects my book, No identified impact, Not yet evaluated, Insufficient data, Superseded, Watchlist). The note: "'No identified impact' is limited by holdings coverage, fund look-through and the matching rules on file; it does not mean no possible relevance." |

Short route names:

| Route | Short name |
|---|---|
| rebalance | Transfer and rebalance now |
| phased | Phased, tax-aware transition |
| managed | Tax-managed SMA and direct indexing |
| specialist | Specialist route |

### 7.4 Landing: "Brokerage opportunities in your book"

**Header.** Subtitle: "Which household, why now, how much could move, by which route, and what to do next." Then, in order:
1. **Tour hint:** "New to this tool? Take the guided tour (about 2 minutes)."
2. **Bar:** a two-option segmented control, "Households" or "All opportunities (workflow)", and a link "Show management view (internal)" / "Hide …".
3. **Filter chips** with counts:

   | Chip | Count at load |
   |---|---|
   | All | 6 |
   | Needs discussion | 5 |
   | Waiting on specialist or operations | 1 |
   | Ready to propose | 0 |
   | Outcome recorded | 0 |

4. **Management view** (when shown): a panel "Book view", tagged "internal · not client-facing", with three columns:
   - "Addressable brokerage assets": a big number, plus "of {brokerage} in brokerage; {excluded} excluded (above the 50% limit, or not transferable)";
   - "By tax difficulty": three horizontal bars for low, medium and hard, plus the hard-segment note;
   - "Firm value on the addressable assets": "~9 bp → ~60 bp", "{today} a year today (commissions at current trading) → {program} in the advisory program. The lower-cost alternative is shown alongside every proposal."

**Table**, fixed layout. Columns are 37%, 15%, 16%, 16% and 16%:

| Column | Contents |
|---|---|
| Household · why now | name in bold; cue pills; "WHY NOW" mini-label and the why sentence of the primary row; a "{n} other signals" disclosure listing each other open row (kind tag, its why, a "detail" link) |
| Potentially movable now | bold amount plus an "observed" tag; "held back {money}" or "nothing held back". Excluded: "—" and "Not eligible now" |
| Starting route | short route name in bold, plus "starting point for review" |
| Constraint · owner | blocker text plus owner tag |
| Next | a small button with the next label; under it "{meeting type} in {n} days". Once an outcome is recorded, a neutral pill with the lifecycle label and its note instead |

- Excluded rows are slightly faded.
- At 700px and below, the table becomes stacked blocks.
- **Note under the table:** "**Order:** households with a meeting, call date or client request coming up first, then by the amount potentially movable now; accounts above the 50% limit last. A rank is a prompt for review, not a suitability conclusion. Amounts are observed holdings; the canonical investable cash excludes the CIO cash target, the liquidity reserve and next year's needs."

### 7.5 Landing, all opportunities (workflow view)

The base queue view: title "My book".
- **Lede:** "{n} need action, {n} go to a specialist or are not eligible, {n} to monitor, across {n} households."
- **Table** grouped by Needs action, Specialist or not eligible, Monitor or deferred (and Closed only when that filter is chosen). Each group has a header row with its count. Each row has four columns:
  1. "{household} · {type}"; kind tag and flow tag; "→ {pathway}"; related lines in a "{n} related" disclosure (an event row shows its first related line inline).
  2. Impact.
  3. Next action plus the action pill.
  4. Status pill (short label), then "Advisor · " or "Suggested · " with the lifecycle label and note. Needing a reason is shown amber.
- Clicking a row opens it (8).
- **Note:** "Uses the baseline settings (brokerage accounts, CIO tactical target, 3-year performance). Ranking weighs status, materiality and concentration; related events sit under the position they concern. An advisor assessment does not remove open work: a row leaves the active groups only when it is closed with an outcome, closed as stay or not suitable with a reason, deferred with a reason, or set to monitor. **Prototype:** assessments and closures are kept in this page only."

### 7.6 Household flow, step 1: Client case (`PATH` with step assess)

**Head:** title = the household name; subtitle "{profile} · {brokerage} brokerage · {meeting type lower case} in {n} days". Then the stepper: Client case → Compare routes → Client proposal → Implementation handoff.
- Steps before the reached step show ✓; handoff shows ✓ once handed off.
- Clicking a step goes there. "Client proposal" switches to the proposal view.

**Summary card "Client case"** (eligibility pill on the right):
1. **"Why now", then a serif sentence:** the primary row's why, then "; {catalysts}", ending with a full stop.
2. **Lead amount, two boxes:**
   - "Potentially movable to advisory now" (observed tag), the big amount, and "Held back: {list}" (for example "$1.00M liquidity reserve and near-term needs · $1.10M AUSTIN-4.0-32 matures 2032 · $400K NVDA awaiting cost basis");
   - "What stands in the way": blocker plus owner tag; "Liquidity reserve not on file: confirm before sizing cash." when missing; "{needsLater} of cash needs after 2027 are not reserved; review with the client." when present.
   - Excluded: "—" and the ineligible reason.
3. **Three measures** (not for excluded), each with its tag:

   | Measure | Tag | Value | Note |
   |---|---|---|---|
   | Moves into the account at enrollment | observed | now | "in kind; no trade implied" |
   | Repositioned over time | modeled | repositionOverTime | "on the phased route, within the gain budget" |
   | Estimated target alignment, year one | modeled | "≈{alignY1}%" | "phased route; rebalancing now reaches ≈100%" |

4. **"Client value and cost, by measure"**: label-and-value rows, each label with its money tag.
   - **Risk** (modeled): "Expected volatility {now} → {target} at the CIO target; profile band {low}–{high}". Amber if the target is outside the band.
   - **Expected return, gross** (modeled): "{erNow} → {erT} before costs: an illustrative scenario difference of ≈ +{yr} a year under capital market assumptions; not a forecast or a guaranteed benefit".
   - **Concentration** (observed; only when a name is above the threshold): "{SYM} is {share} of the account against a 10% guideline".
   - **Tax, year one** (estimate; "needs validation" when basis is missing):
     - "≈ {tax net} after harvested losses on the phased route; ≈ {max(0, gains − losses) × lt} if rebalanced at once. Planning level; depends on validated lots, rates and timing", plus ". Not decision-ready: {basis} has no cost basis" when basis is missing;
     - or "No material gains to realize".
   - **Loss harvesting** (modeled; only when direct indexing is available): "≈ {harvNet} a year after the manager fee, on the direct-indexing route only".
   - **Incremental fee** (estimate, amber): "{program} a year in the program (steady state on {now} from enrollment) vs {stay} today: +{difference}. The lower-cost {index name} is {bp} bp".

   These figures use costs at movable now.
5. **"Your decision"**, tagged "prototype: kept in this page only". Four choice chips:
   - "Pursue: compare routes" (recommended outline; hidden when not eligible);
   - "Remain in brokerage";
   - "Monitor";
   - "Refer to specialist".

   Behaviour:
   - Pressing a chip records the household disposition. Pressing it again clears it.
   - "Pursue" also moves to Compare routes.
   - When the status needs a reason, a reason dropdown appears ("Reason (needed to close)…") with "A reason is needed before this is recorded as closed; until then it stays open."
   - Once not open: "Recorded: {label} · {note}. Follow-up work elsewhere stays open until it is closed separately."

**Below the card:**
- **"Other signals for this household"** ("they feed the same transition"): a list with kind tag, why sentence and an "Open the analysis" link.
- **Expandable sections:**
  - **"How the amounts reconcile"** ("every holding in exactly one bucket"): the reconciliation bar, then a table (Holding, Bucket, Value, Route label, Timing note), then "Timing notes (bond calls, maturities) describe when proceeds could be reinvested; they are not added to any total."
  - **"How it was found: trigger to client story"** ("the six-step worked example"):
    - chips for every row of the household (kind labels), the primary row selected;
    - six step cards in a row (number, title, text); the last card is brand-tinted.
  - **"Transition plan by holding"** ("≈{pct}% aligned in year one on the phased path · tax ≈ {tax net} (planning)"):
    - a table (Holding, Route, Value, Gain or loss, Why), with "basis missing" in the gain column for basis rows;
    - then "Planning estimates on today's prices; not a validated trade plan or an instruction."
    - Route wording:

      | Route | Wording |
      |---|---|
      | inkind | Move in kind |
      | swap | Replace high-cost class |
      | transfer | Tax-efficient transition (sell within the gain budget) |
      | harvest | Sell and harvest the loss |
      | instep | Invest in steps |
      | basis | Hold until basis is found |
      | stay | Stays outside the program |
      | reserve | Kept as liquidity reserve |

  - **"Evidence and sources"** ("data dates and lineage"):
    - positions as of 2026-10-15 (observed);
    - returns as of 2026-09-30;
    - CIO views updated 2026-10-01;
    - research as of 2026-10-15;
    - look-through as of 2026-09-30;
    - screen thresholds note;
    - "All data illustrative";
    - the meeting note.

### 7.7 Step 2: Compare routes

**Intro line:** "Account movement and portfolio trading are shown separately. Choosing a route records a **working choice** for the proposal; it is not a suitability approval."

**Route cards, then a "Stay in brokerage" card in the same grid.** Each route card contains:
1. The badge "Starting point for advisor review", for the suggested route only.
2. The bold name.
3. "**Why this route:** {why}".
4. Two trade-off bullets.
5. Label-over-value rows:
   - Account (observed);
   - Trading (modeled);
   - Tax (estimate, or needs validation when basis is missing);
   - Cost (estimate);
   - Approves.
6. "Still to check before it is actionable": the feasibility list with owners.
7. A button at the bottom, "Make this the working choice" or "✓ Working choice".

**Stay in brokerage card:**
- "**Why this route:** the client keeps today's structure and cost."
- Bullets:
  - "No program fee: about {stay cost} a year today";
  - "No ongoing advice, rebalancing or tax management".
- Rows:
  - Account "Nothing moves";
  - Tax "None triggered";
  - Alternative "Lower-cost {index name}: {total} ({bp} bp)".
- "Reasons the client might stay": up to three reasons-to-stay from the value case.
- Chips: Remain in brokerage, Monitor, Refer to specialist. These record the household disposition.
- The card shows as chosen when stay or monitor is recorded.

**Below the cards:**
- **"Show all alternatives"** ("{n} strategies from the approved universe, plus the lower-cost alternative"): a table of Strategy, Kind, Why it fits, Minimum; the last row is the index option with a "lower-cost alternative" pill.
- **"Transition plan by holding".**
- **A button "Next: prepare the client proposal"**, disabled until a route is chosen (title "Make a route the working choice first").

**Choosing a route:**
- records `S.choice["hh:<id>"]`;
- sets the household status to ready, unless it is already ready or review;
- toasts "Path chosen: {short name}".

### 7.8 Step 3: Client proposal (`WS2`; the stepper is inserted right after the head)

**Head.** Title "Client story and proposal"; subtitle "What an advisory relationship could add for this client, what it costs, and the alternatives, using approved content only."

**Settings per household (`S.o2[id]`), created on first visit:**
- amount = brokerage rounded to $1,000;
- turnover 12%;
- SMA share 50%;
- selected why-now items: the first three on;
- selected objections: the first three offered on;
- selected content: the first three client-audience items on;
- advisor note empty;
- draft text override none;
- draft version 1;
- review state "draft".

The page uses the costs at these settings and `valueCase`.

**Why-now items** (each with a title, text and source):
- the allocation finding, when not "none": "{finding}.", from "Allocation review · positions 2026-10-15";
- each other concentration: "{SYM} is {share} of the account including funds, above the 10% guideline.";
- when active return is below −0.5 point: "Over three years the portfolio returned {RP} a year against {RB} for the CIO allocation.";
- each material event: its house-view text, from "{source} · {date}".

**Topics:**
- always value, fees, fiduciary and sma;
- concentrated and tax when a concentration exists;
- transition and tax when any route is transfer;
- cash when any is instep;
- market and cio when talking points from events exist.

**Objections and content:**
- Objections and content are those matching the topics.
- An objection with `requires: risk_down` that does not pass is listed as not offered: "Not offered for this client: the approved answer says the move lowers risk, but expected volatility does not fall here ({a} → {b})."

**Summary card ("{name} · Advisory discussion"):**
- **Finding by status:**
  - blocked: "The advisory program is not available while one security is above 50% of the account".
  - stay: "{name}'s allocation is in line, and the program's quantified benefits (about {quant} a year) are below its {inc} higher fee: staying in brokerage may suit, with the program still available".
  - net ≥ 0: "An advisory relationship could add about {net} a year for {name} after its higher fee, through {the CIO allocation and tax-loss harvesting}, plus {plan} (illustrative)".
  - otherwise: "An advisory relationship would give {name} {plan}, tax-loss harvesting and access to 8 strategies; estimated benefits cover about {cover}% of the {inc} higher fee, with ongoing advice and planning making up the rest (illustrative)".
- **Why:**
  - stay: "Nothing material came out of the allocation review. Present the program fairly and record the client's choice."
  - blocked: "Not eligible for the program: {reason}. The value case resumes once the position is below the limit; staying in brokerage with a specialist plan comes first."
  - else: "Value figures are illustrative planning estimates: capital market assumptions, and harvestable losses of 2% a year on the direct-indexed equity. They are not promises of results."
- **Evidence:** the first three selected why-now texts.
- **Trade-off rows** (not when blocked):
  1. "Expected return at the CIO allocation, before costs": "{pts} ≈ +{er} a year";
  2. "Tax-loss harvesting with direct indexing (planning)": "≈ +{harvNet} a year after the {fee} manager fee", or "not available for this account";
  3. one-time losses, when above $1,000: "Losses harvested in the move (one-time, planning)", "{losses} ≈ {tax value} of tax value";
  4. gains, when above $1,000: "Tax-efficient move (planning)", "{gains} of gains move in kind; year-one tax ≈ {after} after harvested losses ({before} before), not {all at once} at once";
  5. concentration, when above the threshold;
  6. "Portfolio volatility";
  7. "Higher fee (illustrative)";
  8. "Estimated net of the fee, per year".
- **Choices:**

  | Status | Choices |
  |---|---|
  | blocked | Stay in brokerage (recommended), Specialist review, Advisory program (blocked) |
  | stay | Stay in brokerage (recommended), Advisory: CIO model (suitability dependent), Index-only (compensation differs) |
  | ready | Advisory: CIO model (suitability dependent), With direct indexing and SMA managers, Index-only (compensation differs), Stay in brokerage |

- **Next:**
  - blocked: "Start with the concentrated position plan; revisit the program later."
  - stay: "Explain the comparison; record "stay in brokerage" if the client agrees."
  - ready: "Prepare the value story: why now, what the client gains, how the move works, what it costs, and the alternatives."

**Then, when not blocked:**
- **Panel "Only in a managed account"** ("not available in a brokerage account · applied to {name}'s holdings"): cards for each capability (4.13), each tagged "Managed accounts only".
- **Panel "The value case"** ("illustrative; suitability is the advisor's determination"), in three columns:
  - **"What the client would gain":**
    - **A fiduciary relationship**: ongoing monitoring and rebalancing to the CIO allocation, with the expected-return gain;
    - **the plan phrase**, unless the finding is drift or none;
    - **Tax management built in**: {n} managed-account capabilities, plus losses harvested in the move;
    - **More investment choices**: 8 strategies, with the best fits;
    - **Trading included**: no commissions (about {commissions} a year today).
  - **"What it costs":** "{program} a year in the program ({bp} bp, tiered), against {stay} today: +{inc}." Then "Quantified value ≈ {quant} a year; estimated net {±net}." Then "Not counted: ongoing advice and planning, the risk reduction from the plan, and the one-time tax items."
  - **"Points to weigh openly":** the reasons to stay.
- **Disclosure:** "Illustrative fees, capital market assumptions and harvesting assumptions; not a guarantee of results. Advisor compensation differs between options. Staying in brokerage remains a legitimate choice."

**Expandable sections:**
1. **"Service-level comparison"** ("four options side by side"). Columns: Stay in brokerage, Advisory: CIO model, With SMA managers, Index-only.

   | Row | Stay in brokerage | Advisory: CIO model | With SMA managers | Index-only |
   |---|---|---|---|---|
   | Standard of care | Best interest at the time of each recommendation | Fiduciary duty, ongoing | Fiduciary duty, ongoing | Fiduciary duty, ongoing |
   | Ongoing monitoring and rebalancing | No: client-directed | Yes | Yes | Yes |
   | Portfolio built to the CIO allocation | Client-directed | Yes | Yes, with SMA managers | Yes, index funds only |
   | Tax management | Ad hoc | Gain budget, loss harvesting | Custom, per manager | Limited |
   | Direct indexing, custom exclusions and tilts | Not available | Available as a sleeve | Available | Not available |
   | Tax-managed transition of existing stocks | Not available | Gain budget | Manager takes stocks in kind | Gain budget |
   | Individual municipal bond ladder | Buy bonds one by one | Available as a sleeve | Available | Not available |
   | Trading costs | Commission per trade | Included | Included | Included |
   | Annual cost for this client | {total} ({bp} bp) | {total} ({bp} bp) | {total} ({bp} bp) | {total} ({bp} bp) |
   | Expected return · risk (illustrative) | {er} · {vol} | {er} · {vol} | {er} · {vol} | {er} · {vol} |
   | Advisor compensation | Commissions | Program fee | Program fee | Differs from the full program |

2. **"1 · Why now"** ("{k} of {n} selected · {m} talking points"):
   - checkable cards for each why-now item (title, text, source);
   - then talking points collected from other views, each with a source pill.
3. **"2 · Fee model":**
   - controls:
     - "Assets moving", a number input in $50K steps;
     - "Brokerage trading a year", a slider from 0 to 50%;
     - "Equity run by SMA managers", a slider from 0 to 100%;
   - four cost cards, each with:
     - a mini donut of the parts (88px, bp in the centre);
     - the total "a year";
     - the parts;
     - "Net of costs {pct}";
   - the program fee tier table (tier, rate, assets, fee);
   - the fee notes.
4. **"3 · Client considerations"** ("{n} objections prepared"):
   - checkable objections, each with "Approved response · {content title}";
   - then any not-offered ones.
5. **"4 · Advisor preparation: materials and draft"** ("{n} approved items · draft v{n} · {not reviewed / advisor reviewed / submitted for compliance}"):
   - Approved materials as checkable cards. Advisor-only items are disabled and carry an "advisor only" pill. Each shows "Approved {date} · expires {date}"; the expiry is red if within 90 days of 2026-10-24.
   - Draft header:
     - "Client story draft";
     - an amber pill, "Generated draft · requires advisor and compliance review";
     - "Version {n} · prototype: not saved";
     - a review-state select: Draft, Advisor reviewed, Submitted for compliance.
   - An auto-growing textarea with the draft. The advisor's edits are kept.
   - Buttons:
     - "Rebuild draft": clears edits, increments the version and resets the review state to Draft;
     - "Copy".
   - An "Advisor note (not pre-approved; marked as such)" input.
   - "Sources in this draft": a list.
   - Disclosure: "Approved materials explain the program; they do not establish that this recommendation is suitable for this client. Suitability is the advisor's determination."

**The draft text** is plain text, with uppercase section headings and "• " bullets:
1. Title line: "{name}: what an advisory relationship could add".
2. WHY WE ARE TALKING NOW: the selected why-now texts and talking points.
3. If blocked:
   - WHERE WE START: not available, with the reason; staying in brokerage at about {stay} a year; a plan for the position comes first.
4. Otherwise:
   - WHAT THE PROGRAM COULD DO FOR YOU: fiduciary relationship and return; the plan; more choices; no commissions.
   - WHAT ONLY A MANAGED ACCOUNT CAN DO: each capability.
   - HOW THE MOVE WOULD WORK, TAX-EFFICIENTLY:
     - the transfer symbols move as they are and are sold within the gain budget, with the year-one tax figure;
     - losses harvested;
     - cash in six monthly steps.
   - WHAT IT COSTS: program vs today; the estimable benefits vs the added fee.
   - YOUR OPTIONS:
     - the program;
     - "A lower-cost index-only option: about {total} a year, with fewer services; advisor compensation differs between options.";
     - "Staying as you are in brokerage: you direct the portfolio, and recommendations are made in your best interest at the time they are made."
5. THINGS TO WEIGH.
6. QUESTIONS YOU MAY HAVE.
7. ENCLOSED (APPROVED MATERIALS).
8. ADVISOR NOTE (NOT PRE-APPROVED).
9. Closing line: "Figures are illustrative estimates and do not imply future results. Draft for advisor and compliance review."

When the review state is "Submitted for compliance", the household moves to the handoff step.

### 7.9 Step 4: Implementation handoff

**Panel "Before anything moves"** ("people complete each item; the tool never enrolls or trades"):
- A large checklist of the handoff items, each with its owner tag. Auto items are disabled and ticked from the workflow, with " · from the workflow".
- When not eligible: "Not eligible for the program: the handoff applies only to a specialist plan."
- **Primary button "Hand off to operations".**
  - Enabled only when every item is done, the household is eligible and it is not yet handed off.
  - After handoff: "✓ Handed off to operations".
  - Hint, by state:
    - not ready: "Complete every item first. Prepared for review is not approved.";
    - ready: "Ready to hand off for operations to enroll.";
    - handed off: "Operations enroll and move the assets; nothing is executed by this tool (prototype: kept in this page only)."

**Panel "Handoff package"** ("path: {short name}" or "no path chosen yet"):
- Rows:
  - "Enroll now" {now};
  - "Later, when gated" (for example "$400K: Cost basis on file", or "none");
  - "Kept in brokerage" {kept}.
- "Invest in steps": a one-row table of six months with their amounts.

Then the transition plan by holding.

### 7.10 Task panel (right, on every view)

**Header:**
- "CURRENT TASK", then the household name;
- the first stage that is not ready, as "{stage}: {note}", for example "Analyze: Advisor to decide whether to pursue";
- a full-width button with the household's next label. It is the primary button, except on the handoff step, where the page's own button is primary.

**Body:**
- **Key-value lines:**
  - **Owner:** "You (advisor)", or "You, then {owner}".
  - **Blocking:** the blocker text.
  - **Status:** "{eligibility label} · {Implement note before the colon}", for example "Eligible in principle, with conditions · Not cleared".
- **The five stage chips**, with the current one outlined.
- **Collapsed "Story draft"** ("prepared for review, not approved"):
  - Eligible: "{why}. A {route name in lower case} would move about {now} into an advisory relationship with ongoing advice and tax management, at about {route cost before 'vs'}. Staying as you are remains an option."
  - Not eligible: "{why}. The advisory program is not available while the position is above 50%; the first step is a specialist plan."
  - Then "Talking points collected: {n}".
- **Collapsed "Stages, decisions and owners":** the full five-stage ladder (icon ✓ / … / ✕, stage, note, "You decide: …", "Control: …"), then "All blockers" with owners.
- **"Record a decision"**, when the view has a decision key:
  - It is open on the analysis views, or whenever a disposition exists. Its summary shows the lifecycle.
  - Contents:
    - the lifecycle state chip;
    - "set by advisor" or "suggested: {status label}";
    - the assessment select ("Set the assessment…" or "Back to suggested" plus the seven statuses);
    - a reason select for stay, defer, unsuitable or monitor (highlighted when needed);
    - a "Close with an outcome…" select, or a "Reopen" button when closed;
    - the note "An assessment alone keeps work open; closing is separate. Prototype: kept in this page only, not a CRM or audit record."

**Decision key by view:**

| View | Key |
|---|---|
| Household flow | "hh:<id>" |
| Landing | none |
| Allocation | "ws1:<id>" |
| Proposal | "ws2:<id>" |
| Concentrated position | "ws3:<id>:<SYM>" |
| Market and research | "ws4:<event>:<id>", or a promoted "ws4f:…" |

### 7.11 Allocation and performance (`WS1`)

Title "Allocation and performance"; subtitle "Brokerage portfolio against the CIO target: what needs attention, why, and the choices."

**The summary card** ("{name} · Allocation review"):
- "Based on" controls, three small segmented controls:
  - Brokerage accounts / Whole household;
  - CIO strategic / CIO tactical;
  - 1 year / 3 years.
- When the settings differ from the baseline, show the amber note "Differs from the queue baseline (brokerage · CIO tactical · 3-year)".
- The card ends with a compact six-step strip ("Advisory pathway", kind · pathway, "Open the full pathway").

**Expandable sections:**
- **"Why flagged: allocation against the CIO bands"** ("{n} classes and {m} groups outside tolerance"):
  - an L1 groups / L2 classes toggle;
  - two panels: the bands chart, with a legend; and the volatility gauge (band, today, at target), with "Amber marks a difference from the house model. Red is reserved for a breach of the client's risk profile, blockers and missing data.";
  - a table of the rows outside tolerance (today, target, band, gap, dollars).
- **"Performance attribution"** ("{period}: {active} vs the CIO allocation"):
  - the waterfall chart: CIO allocation → Allocation, Selection, Interaction → This portfolio;
  - a heat-shaded table by class;
  - detractor chips, "{SYM} {pts}", with tooltips;
  - the perf note, "Returns as of 2026-09-30. Past performance does not guarantee future results."
- **"Strategies that fit":** cards with name, fit score pill, description, type · minimum, manager fee, why bullets.
- **"Tax and implementation: how it would move":**
  - a routing donut (route colors, brokerage total in the centre) and a routing table;
  - "Invest in steps: Nov 2026 … Apr 2027" with the six amounts;
  - a red gate banner when not eligible.

Finish with "Add to talking points".

### 7.12 Concentrated position (`WS3`)

**Threshold panel:**
- "Alert threshold (analytical)" slider, 5–30% in 1% steps;
- "Program eligibility gate (fixed)": **50%** in one security, "excluded from the program; measured on direct holdings plus look-through into funds";
- explanatory text: requirements 10%, earlier material 20%; the 50% gate is a business rule; the list shows direct positions.

**Position settings** (`S.o3[key]`):
- target = the smaller of the alert threshold or 10%;
- budget = the gain budget;
- gift = $250K if the intent includes gift;
- six years;
- needs from the data;
- answers: gift (from the intent), cash (needs exist), keep the upside (no).

**Summary card** ("{name} · {SYM} position"), with the gates. Trade-offs:
- concentration "{share} → {year-one share} in year one; {target} target";
- estimated tax, year one;
- portfolio volatility today → after year one;
- horizon "target by {year}" or "beyond {2025 + years}".

Choices are the top four solutions: the first non-blocked one is recommended; blocked ones are disabled.

**"Available path"** panel ("answers come from the client file; change them here"): the decision tree with five questions.

| Question | Answer | Outcome |
|---|---|---|
| Insider or restricted stock? | "Yes: {restriction}" or "No restrictions on file" | "Pre-clear trades; consider a pre-arranged sale plan" |
| Above the 50% program limit? | "Yes: {share}" or "No: {share}" | "Specialist route first; program paths blocked" |
| Wants to give shares to family or charity? | Yes or No | "Gift lowest-basis lots first ({gift} a year)" |
| Needs cash from it in the next few years? | Yes, with the years and amounts, or No | "Sell highest-basis lots to meet each year's need" |
| Wants to keep the upside, or avoid selling? | Yes or No | "Collar or exchange fund (specialist referral)" |

- **Result:** a " → " chain of: Pre-clearance; specialist review; gift low-basis lots; "protect the rest with a collar" or "staged sale within the gain budget"; "program once below 50%" or "reinvest through direct indexing with the stock excluded".
- Chips toggle three answers: Gifting intent, Cash needs, Keep the upside.

**Expandable sections:**
- **"Risk before and after":** columns Today, Planning scenario: year one, and Illustrative full trim to target. Rows:
  - share;
  - volatility;
  - the worst past event;
  - sold · estimated tax.

  The full trim sells min(excess, sellable value) and buys the recommended single-class funds for the underweight classes, in proportion. Then the explanation.
- **"Tax lots":** a table of lots sorted with missing basis last, then by basis ratio. Columns: lot, acquired, term, value, cost, basis/value (heat-shaded), gain, tax if sold, and a tag ("blocker: find basis" or "gift candidate" when the basis ratio is below 30%).
- **"Multi-year sale plan":**
  - controls: target slider (5% to the current share, capped at 50%, in 0.5% steps), "Gains allowed a year", gift a year (when gifting), cash needed per year (when cash needs);
  - the line chart;
  - a yearly table, with "*" on over-budget gains and the note "* over the yearly gain budget because of the cash need";
  - the disclosure, with the tax disclosure.
- **"Solutions and actionability":** for each solution, name and description, actionability pill, effect text, horizon, fit score.

  | Solution | Fit | Horizon |
  |---|---|---|
  | staged | 0.6 | years to reach |
  | tm-sma | 0.1 blocked; 0.75 if the position is at least $250K; else 0.2 | 1–3 yr |
  | di | 0.1 blocked; 0.7 if equity is at least $250K; else 0.2 | 1–3 yr |
  | gift | 0.9 with gifting intent; 0.45 if there are low-basis lots; else 0.1 | per gift |
  | hedge | 0.85 when blocked or keeping the upside; 0.45 for insiders; else 0.25 | weeks |

Finish with "Add to talking points". The clip text is the plan sentence.

### 7.13 Market and research: My book impact (`WS4`)

Title "Market and research"; subtitle "Which clients an event materially affects, how sure we are, and what merits action." Two large tabs:
- "My book impact" ("events matched to your households");
- "Firm intelligence" ("everything you are entitled to read").

**Event panel:** a type pill (Market news (third party), Firm CIO view, Firm research, Client question), the date, a serif headline and the summary.

**Summary card** for the selected household ("{name} · Event review"). The default household is the top material one.
- Finding: "{action} for {name}: {size}".
- Why: the "for you" sentence:

  | Event type | For you |
  |---|---|
  | market | "Under this illustrative scenario, your holdings would be affected by an estimated {money} ({share}), mostly through {two symbols}. This is a model estimate, not your actual result." |
  | view | "Your portfolio leans against the new view: …", or "…already in line…" |
  | research | the holder sentence: a manager-run holding says the next step is asking the manager; otherwise "We can review similar companies with a higher rating." |
  | client | "This is your own question; the concentrated position plan answers it." |

- Evidence:
  - "What changed: {type}, {date}";
  - "Why this client: {holdings and via}";
  - "Confidence: {confidence}".
- Choices: the suggested action first (recommended), then Contact the client, Reassess the allocation, Request a manager review, Monitor, No action.
- Next: the event's to-do.

**"Affected households" panel:**
- material households ranked, as rows "{rank}. {name} | size | status pill"; clicking a row selects that household;
- "Monitor or no action ({n})" in a disclosure;
- "Across the book: {names} (not in this list)" for downgrade holders outside these households;
- materiality note: "Material means an estimated move of at least 0.5% of the account, a direct holding of a downgraded stock, or an asset class at least 5 points against a new CIO view. Smaller effects are listed as monitor or no action."

**Expandable sections:**
- **"How it reaches the portfolio":**
  - a market event shows a by-holding table (how, value, estimated move, dollars, share) and the estimate disclaimer;
  - a view shows the classes against or in line.
- **"House view and research":** the CIO view card and the research card ("{SYM}: {from} → {to}", why, "Similar companies rated Buy: …"), the house text, and the sources with the research disclosure.
- **"Client story draft":** What happened, The house view, For you, What to do. Buttons:
  - "Add to talking points";
  - a route button: "Open the allocation review", "Open the concentrated position" or "Open the value story".

### 7.14 Market and research: Firm intelligence

**Intro panel:** "Everything you are entitled to read, whether or not it touches your households: **13** items in this sample catalog, as of 2026-10-23. Reading or publishing an item never adds work; the opportunity count changes only when you add a material match." Then a search box ("Search titles, tickers, themes…"). Its input is debounced and keeps focus.

**One card per item**, filtered by type, book status or watchlist, and search. Each card has:
- a type pill, the date, "Superseded" and "On watchlist" pills, and the book-status badge;
- the headline, the abstract, and "HOUSE STANCE {stance}";
- a superseded banner: "{superseded_by}. Use the current view; this version cannot be analyzed or shared.";
- a meta line:
  - "Source: {source}, {date} · v1";
  - "Status: …";
  - "Client use: approved (until {date})", "third-party news, summarize in your own words" or "internal only";
  - "Entitlement: …".

**Buttons on each card:**
- "Analyze against my book", "Show book matches" or "Hide results" (disabled when superseded).
- "Add to watchlist" / "Remove from watchlist".
- "Save for {first name}'s meeting". Enabled only when the item is approved for client use and current; it adds a talking point.
- "Open approved source · not in prototype", always disabled.

**Results table**, when analyzed:
- a summary line: "{n} material · {n} monitor · {n} no identified impact · {n} not evaluated · run against positions as of 2026-10-15";
- one row per household: name link, state pill, size and why, and an action:

  | Item | Action on a material match |
  |---|---|
  | auto item | "Open in My book impact" |
  | other item | "Add to opportunities", with the eligibility pill; once added, "Added to opportunities ✓" |

- disclosure: "Only a material match can become an opportunity, and only when the advisor adds it; its eligibility comes from the same rule as everywhere else. "No identified impact" is limited by holdings coverage, look-through and matching rules; "not evaluated" means the data needed is missing."

**State pills:**

| State | Label |
|---|---|
| matched | Material match |
| monitor | Monitor |
| none | No identified impact |
| unknown | Not evaluated: insufficient data |
| na | Superseded |

### 7.15 Shared summary card and choices (allocation, proposal, position, event views)

**Header row:** the card title, and a link "Workflow, readiness and owners in the Decision panel". On mobile the link opens the sheet; on desktop it scrolls to the decision section.

**Choice chips:**
- The hint under the chips: "pick one to record it and open what supports it".
- Pressing a chip records `S.choice[key]`. Pressing it again clears it.
- It also sets an assessment and opens what supports the choice:

  | Choice | Records | Then |
  |---|---|---|
  | Stay in brokerage | stay | — |
  | Monitor | monitor | — |
  | Specialist review | specialist | — |
  | No action | closes with "No action needed after review" | — |
  | Review alternatives | review | opens "Strategies that fit" |
  | Rebalance in brokerage | review | opens the bands section |
  | Advisory (on the allocation view) | ready | goes to the proposal |
  | Advisory (on the proposal) | ready | opens the service comparison |
  | With direct indexing and SMA managers | ready | opens the service comparison |
  | Index-only | ready | opens the fee model |
  | Review the concentrated position | review | goes to the position view |
  | Reassess the allocation | review | goes to the allocation view |
  | Contact the client | ready | — |
  | Request a manager review | review | — |
  | any other choice on the position view | review | opens Solutions |

- Each choice's title attribute explains what it does, for example 'Records "Review needed" and opens Strategies that fit'.
- A toast confirms, for example "Chosen: {n} · assessment: Review needed".

### 7.16 Guided tour (23 steps)

**What a step is:** each step sets a view, spotlights one element and shows a card. It never records a decision.
- **On start:** save ws, hid, hstep, qv, mgmt, hf, about and the open sections.
- **On exit:** restore them, close the mobile sheet and repaint.
- **Every step:** forces mgmt off and filter "all".
- **Keys:** Esc exits; → or Enter goes next; ← goes back.
- **Clicks:** a capture-phase listener blocks clicks outside the tour card while the tour is open.

**Overlay:**
- a fixed full-screen layer with role dialog and aria-modal;
- a "hole" box positioned over the target with 8px padding, a 10px radius, a 2px brand outline, and a huge dark box-shadow (`0 0 0 9999px rgba(12,18,26,.58)`) that dims everything else;
- smooth 0.22s transitions, which are off for reduced motion.

**Card:** 380px wide. It contains:
- "GUIDED TOUR · {i} OF 23" in brand uppercase;
- a serif title;
- the body text;
- progress dots (the current one is a wide pill; done ones are tinted);
- buttons: Exit tour, Back (from step 2), and a primary "Start the tour" (step 1), "Next", or "Finish" (last).

**Placement:**
- No target: centred, 440px wide.
- Wider than 700px and the target taller than 55% of the viewport, or a side-panel step: the bottom-right corner (side-panel steps sit to the left of the panel).
- Otherwise: below the target. If it doesn't fit, above. If that doesn't fit either, beside it.
- At 700px and below: a bottom sheet with 12px margins.
- The target scrolls to the centre instantly. Reposition on scroll and resize.

**Entry points:**
- the "Tour" button;
- the landing hint;
- a URL hash containing "tour", which starts the tour 300ms after load.

**Steps** (view → spotlight: title). Write the bodies in the same spirit; the reference wording is summarised.

| # | View | Spotlight | Title | Body (gist) |
|---|---|---|---|---|
| 1 | landing | none | How this tool works | Finds brokerage households where an advisory relationship could genuinely help; first signal to reviewed proposal and hand-off; you decide; nothing is sent, enrolled or traded. |
| 2 | landing | the table | 1 · Identify: brokerage opportunities in your book | One row per household; order stated under the table. |
| 3 | landing | first row's cues | Why it is near the top | Cues explain the order; a rank is not a suitability conclusion. |
| 4 | landing | filter chips | Filter by what is needed | Work the list by the next thing you can do. |
| 5 | landing | first row, column 2 | Potentially movable now | Observed holdings; held-back amounts shown underneath, never added in. |
| 6 | landing | first row, column 3 | A starting route, not a recommendation | Starting point for review; constraint and owner beside it. |
| 7 | landing | first row, column 5 | One next step | One next step per household; recorded outcomes show here instead. |
| 8 | landing | management link | Management view (internal) | Firm figures off by default, labelled internal, never on client screens. |
| 9 | Henderson client case | stepper | Each household: four steps | Maps to Analyze, Design, Propose, Implement. |
| 10 | same | lead amount | 2 · Analyze: how much, and what is in the way | Answer "how much can I discuss moving, and what prevents the rest?" in seconds. |
| 11 | same | three measures | Moving the account is not trading the portfolio | Enrollment in kind vs repositioning over time; nothing implies an approved trade. |
| 12 | same | value rows | Every money figure says what it is | Observed / estimate / modeled / needs validation; scenario, not growth given up; fee always shown. |
| 13 | same, opening the reconcile section | reconcile section | Amounts that reconcile | One bucket per holding; bar adds back; timing notes never counted twice. |
| 14 | same | decision chips | Your decision | Pursue or record an outcome; a reason is needed to close. |
| 15 | Henderson compare routes | route grid | 3 · Design: compare routes side by side | What each card shows; open checks with owners. |
| 16 | same | starting-point badge (spotlight its whole card) | A starting point for your review | Choosing records a working choice, not suitability approval. |
| 17 | same | stay card | Stay in brokerage, as a real option | Cost, what the client would not get, alternative, reasons to stay. |
| 18 | Henderson proposal | summary card | 4 · Propose: the client proposal | Value first; approved materials only; review needed. |
| 19 | Henderson handoff | checklist | 5 · Implement: hand-off, never execution | Unlocks only when all are done; demonstration only. |
| 20 | Henderson client case | right panel | Your task panel | Current task, owner, blocking, status, one action. On mobile, open the sheet. |
| 21 | same | other-signals list | The analysis is still one click away | Allocation, position plan, events; six-step example in the sections. |
| 22 | landing | the checks pill | Check the logic yourself | Runs the engine checks in your browser; nothing saved. |
| 23 | landing | none | That is the flow | Your book → client case → compare routes → proposal → hand-off; reopen from "Tour". |

### 7.17 Prototype checks dialog

Clicking the "Prototype · checks" pill runs `runChecks()`:
1. Copy `S.disp`, `S.promo` and `S.intelRun`.
2. Clear them.
3. Run the checks.
4. Restore them in a finally block, so the screen never changes.

Each check has an area, a name, pass or fail, and an info line.

**Dialog:**
- "Prototype checks" and "Close";
- "{n} of {n} passed, run in this browser at {time}. Engine-level checks; nothing on screen is changed. All data is illustrative; nothing is saved.";
- the results grouped by area;
- a "Covers: …" footnote.

Clicking the backdrop closes it.

**The 30 checks** (all must pass):

| Area | Checks |
|---|---|
| Eligibility | 1–6: for each household, its allocation and value rows use its eligibility short label (ignore "No action needed now" and "Not eligible; specialist route"). 7: a synthetic household holding only a $1M fund whose look-through is 70% in one name is not eligible, via "all through funds". 8: Delgado is not eligible and its via text mentions "direct". |
| Readiness | 9: no "Not eligible yet" wording, and implementation notes start "Not cleared". 10: discussion is ready while implementation is blocked, for every household. |
| Workflow | 11: "Review needed" keeps Henderson's NVDA row in action. 12: specialist → specialist group; stay without a reason → action; stay with "Client declined" → done; defer with a reason → monitor; explicit close → done. |
| Claims | 13: over 6 households × 2 scopes × 2 bases × 2 periods (48 views), every "lower / raise / stay about the same (a% → b%)" phrase matches its numbers. 14: attribution effects sum to the active return (gap < 1e-9). 15: the year-one gains trade-off label contains "planning". |
| Value story | 16: net = er + harvNet − inc, within $1, for every household at its brokerage amount. 17: not-eligible households have no direct-indexing value. |
| Pathway | 18: every row has a use case and a pathway and renders six steps (27 rows). 19: every eligible household's step 4 contains "lower-cost alternative shown". 20: excluded households have 0 in scope. 21: every Implement stage is blocked. |
| Amounts | 22: the instep routing sum = investable = the transition's instep, and never exceeds cash − target − reserve. 23: the buckets add to identified (within $2). 24: identified ≥ eligible ≥ now. |
| Paths | 25: every route has feasibility checks and an approver; not-eligible households have only the specialist route. 26: exactly one suggested route per household. |
| Events | 27: every material market size contains "estimated scenario impact". |
| Intelligence | 28: analyzing all 13 catalog items leaves the queue count unchanged. 29: superseded is "na", and f3 gives "unknown" for at least one household. 30: every client-usable, non-superseded item is not market news. |

---

## 8. Events reference (`data-*` attributes)

| Attribute | Action |
|---|---|
| data-go="{view}" | switch view, closing About. Going to the position view picks the household's first position. Scroll to top. |
| data-phh="{id}" | open the household flow for that household (step unchanged, worked-example row reset) |
| data-hstep="{step}" data-hid | go to a household step. "proposal" switches to the proposal view. Captured before other handlers. |
| data-hdec="{status}" data-hid | toggle the household disposition. "ready" also goes to Compare routes. |
| data-hreason="{id}" (change) | set the household disposition reason |
| data-hpath="{route}" data-hid | choose the working route (see 7.7) |
| data-hdone="{item}" data-hid (change) | tick a handoff item |
| data-handoff="{id}" | mark handed off; toast "Handed off to operations (prototype)" |
| data-hf, data-qv, data-mgmt | landing filter, landing view, management view toggle |
| data-open="{row key}" | open a row's view. Position rows set the position; event rows set the event and household; promoted items open Firm intelligence with the item selected and analyzed. |
| data-popp="{row key}" | choose the row shown in the six-step example |
| data-popen | open the household flow on a given row |
| data-qf, data-qws | workflow group and source filters |
| data-hh, data-pos, data-ev | choose the household (analysis lists), the position, or the event |
| data-o1="{key}={value}" | allocation settings |
| data-o4view, data-ift, data-ifb, data-evf | market and research tab, type filter, book-status filter, event filter |
| data-drill="hh:{id}" | select the household in the affected list |
| data-ianalyze, data-iwatch, data-isave, data-promo, data-bookev | firm intelligence actions |
| data-isearch (input) | search, debounced about 140ms, keeps focus |
| data-ans | toggle a decision-tree answer (turning gifting on sets $250K if zero) |
| data-o3r, data-o3n, data-need, data-th | sale-plan slider and inputs, cash need per year, alert threshold (sliders are debounced) |
| data-o2r, data-o2n, data-o2t | proposal sliders, amount, note (each clears the draft override) |
| data-auto, data-obj, data-con | why-now, objection and material toggles (each clears the draft override) |
| data-rev (change) | proposal review state |
| data-regen2, data-copy2, data-tp2 | rebuild draft, copy, edit draft (auto-grow) |
| data-clip, data-rmclip | add or remove a talking point |
| data-choice="{key}\|{choice}" | record a choice (7.15) |
| data-disp, data-reason, data-close, data-reopen (task panel) | assessment, reason, close outcome, reopen |
| data-wf, data-sidetoggle, data-about | jump to the decision section, open or close the mobile sheet, toggle About |
| data-dx (toggle) | remember the open or closed state of an expandable section |
| data-checks, data-closechecks | open or close the checks dialog |
| data-tour="start, next, back, end" | the tour |

Enter or Space on a focused row with data-open or data-drill activates it. Toasts last about 1.9 seconds.

---

## 9. Reference figures (baseline settings; check to the dollar where shown)

**Per household:**

| | Henderson | Kaplan | Castellano | Okonkwo | Brennan | Delgado |
|---|---|---|---|---|---|---|
| Eligibility | conditions (NVDA 22.9%: 22.1% direct, 0.8% through funds; Operations) | conditions (AAPL 28.9%; Compliance) | conditions (JPM 8.8%; Manager) | eligible (NVDA 1.3%, all through funds) | conditions (NVDA 32.2%; Compliance) | ineligible (COST 58.3%: 58.2% direct, 0.2% through funds) |
| Brokerage (identified) | $49.70M | $8.70M | $2.60M | $28.40M | $840K | $1.65M |
| Cash: total / target / reserve / investable | 7.30M / 3,230,500 / 1.00M / 3,069,500 | 1.20M / 565,500 / 550,000 / 84,500 | 160K / 160K / 0 / 0 | 14.20M / 1,278,000 / 1.50M / 11,422,000 | 50K / 21K / 29K / 0 | 140K / 74,250 / 65,750 / 0 |
| Buckets: move / gated / kept / excluded | 47.20M / 400K / 2.10M / 0 | 8.15M / 0 / 550K / 0 | 2.15M / 0 / 450K / 0 | 26.90M / 0 / 1.50M / 0 | 811K / 0 / 29K / 0 | 0 / 0 / 0 / 1.65M |
| Year-one alignment (phased) | 69.5% | 73.4% | 100% | 100% | 39.8% | — |
| Repositioned over time | $14.10M | $2.17M | 0 | 0 | $488K | — |
| Gains / year-one gain / losses | 11.00M / 994K / 1.70M | 1.80M / 174K / 200K | 0 / 0 / 59K | 0 / 0 / 100K | 295K / 18K / 0 | (880K / 33K / 10K, not used) |
| Year-one tax: gross → net | 236,572 → 0 | 41,412 → 0 | 0 | 0 | 4,284 → 4,284 | — |
| Trading cost | $22,135 | $3,274 | $1,090 | $10,411 | $302 | — |
| Expected return now → target | 5.64% → 6.15% | 5.86% → 6.15% | 6.13% → 6.15% | 4.74% → 6.55% | 6.38% → 6.81% | 6.07% → 6.55% |
| Volatility now → target | 9.24% → 9.46% | 10.45% → 9.46% | 10.26% → 9.46% | 5.28% → 11.60% | 15.26% → 13.77% | 13.19% → 11.60% |
| Scenario: a year / 5 years | 254,612 / 1,600,954 | 25,207 / 159,166 | 591 / 3,751 | 514,566 / 3,205,385 | 3,579 / 23,106 | 7,938 / 50,697 |
| Segment | hard | hard | medium | low | hard | hard |
| Allocation finding | conc, ready | risk, review | drift, monitor | cash, review | risk, review | gate, specialist |
| Value story (on brokerage): stay / program | 55,170 / 297,850 (60 bp) | 9,580 / 70,400 | 4,445 / 24,100 | 31,060 / 180,700 | 4,101 / 8,820 | 1,650 / 16,025 |
| er / harvNet / inc / quant / net | 254,612 / 54,869 / 242,680 / 309,481 / +66,801 | 25,207 / 9,605 / 60,820 / 34,812 / −26,008 (57%) | 591 / 2,870 / 19,655 / 3,461 / −16,194 | 514,566 / 31,354 / 149,640 / 545,920 / +396,280 | 3,579 / 927 / 4,719 / 4,506 / −213 | 7,938 / 0 / 14,375 / 7,938 / −6,437 |
| Value-case status | ready | ready | stay | ready | ready | blocked |
| Routes (★ = starting point) | rebalance, phased, managed★ | rebalance, phased, managed★ | rebalance★, phased | rebalance, phased★ | rebalance, phased, managed★ | specialist★ |
| Route cost on "now" | program $284K (60 bp), SMA $313K (66 bp) vs $52K today | $67K (82 bp), SMA $72K (88 bp) vs $8,974 | $20K (94 bp) vs $3,676 | $172K (64 bp) vs $29K | $8,516 (105 bp), SMA $9,372 (116 bp) vs $3,959 | $1,650 a year in brokerage today (see pitfall 9) |
| Rebalance-at-once tax | ≈ $2.21M | ≈ $381K | little or no gain | little or no gain | ≈ $70K | — |
| Years to full alignment | 12 | 11 | — | — | 17 | — |
| Blocker (owner) | $400K without cost basis (Operations) | Insider rules for AAPL: pre-clearance (Compliance) | Manager-run sleeve: the manager decides (Manager) | Suitability determination (Advisor) | Insider rules for NVDA: pre-clearance (Compliance) | Above the 50% single-security limit (Specialist) |
| Landing cues | Meeting in 2 days; Tax-basis blocker; Large movable amount | Meeting in 1 day; Client request | Meeting in 5 days; Call date 2026-12-15 | Meeting in 6 days; Large movable amount | Meeting in 6 days | none |
| Why now (primary) | NVDA is 22.9% of the account | AAPL is 28.9% of the account | NYSDA-5.0-34 callable on 2026-12-15: the proceeds need a plan | $11.42M of cash sits above the CIO target after a $1.50M reserve | NVDA is 32.2% of the account | COST is 58.3% of the account, above the 50% limit |
| Held back (landing) | $2.50M | $550K | $450K | $1.50M | $29K | Not eligible now |

**Book and queue:**
- **Ranking:** Henderson, Okonkwo, Kaplan, Castellano, Brennan, Delgado.
- **Filters:** Delgado is "waiting"; all others are "discuss". Next labels: "Review assessment", or "Request specialist" for Delgado.
- **Queue:** 27 rows, in this order:
  1. Delgado COST (specialist);
  2. Brennan NVDA;
  3. Kaplan AAPL;
  4. the Kaplan client question;
  5. Henderson NVDA;
  6. Kaplan allocation;
  7. Okonkwo allocation (excess cash);
  8. Brennan allocation;
  9. Brennan AAPL;
  10. Henderson MSFT;
  11–15. gains rows for Henderson, Kaplan, Castellano, Okonkwo and Brennan;
  16. Castellano bond call;
  17. Henderson excess cash;
  18. the Castellano CVS research event;
  19. the Castellano PFE research event;
  20. Castellano high-cost funds;
  21. Brennan high-cost funds;
  22. Henderson bonds;
  23–26. value rows for Henderson, Kaplan, Okonkwo and Brennan;
  27. Castellano allocation (monitor).
- **Book view:** addressable $85.21M of $91.89M; $3.20M excluded; low $26.90M, medium $2.15M, hard $56.16M; revenue $76,690 → $509,285; 9.0 → 59.8 bp.
- **Program fee checks:** $1M → $10,000; $5M → $42,000; $47.2M → $260,500.
- **Tactical target, Moderate** (strategic → tactical):

  | Class | Strategic | Tactical |
  |---|---|---|
  | LCG | 14.5 | 12.5 |
  | LCV | 14.5 | 16.0 |
  | SMID | 6.0 | 6.5 |
  | INTL | 10.0 | 11.5 |
  | EM | 3.0 | 3.0 |
  | UST | 13.5 | 12.5 |
  | IGC | 15.5 | 16.0 |
  | HY | 6.0 | 5.5 |
  | CASH | 7.0 | 6.5 |
  | HF | 5.0 | 5.0 |
  | PE | 5.0 | 5.0 |

- **Attribution, brokerage 3Y** (RB → RP, allocation, selection):

  | Household | RB → RP | Allocation | Selection |
  |---|---|---|---|
  | Henderson | 7.67% → 21.81% | +1.95 | +5.43 |
  | Kaplan | 7.67% → 10.03% | +2.66 | +0.44 |
  | Okonkwo | 9.07% → 6.55% | −2.50 | +0.16 |

- **Strategy fits:**
  - Henderson: CIO Model 100, Core Equity Direct Indexing 80, Municipal Ladder SMA 60, Tax-Managed Large Cap SMA 40.
  - Brennan: CIO Model 100, Direct Indexing 100, Tax-Managed 60, Municipal Ladder 60.

**Sale plans** (default settings, target 10%, six years):

| Position | Reach | Year by year |
|---|---|---|
| Henderson NVDA (gift $250K a year, budget $994K) | 2030 | 2026: sell $1,239,576, gift $250K, gain $994K, tax $236,572, share 20.0%; then 17.1%, 14.2%, 11.2%, 10.0% (2030) |
| Kaplan AAPL (budget $174K, needs 2027–2030) | not reached | 2026: sell $232K, tax $41,412, share 26.3%; 2031 share 12.0% |
| Brennan NVDA (budget $18K, 2027 need $120K) | 2031 | 2026: share 29.8%; 2027: sell $120K, over budget, share 19.0% |
| Delgado COST | not reached | 43.2% in 2031 |
| Henderson MSFT | 2026 | sell $283,400, tax $34,413 |
| Brennan AAPL | 2026 | — |

**Event materiality:**

| Event | Result |
|---|---|
| n1 (chips) | Henderson −$689K (−1.39%), review; Brennan −$18K (−1.95%), review; Kaplan and Castellano monitor; others no action |
| n2 (CIO view) | review for all except Castellano (in line) |
| n5, n6 | Castellano $80K and $120K held directly, "Request a manager review" |
| n7 | Henderson +$423K, Kaplan +$93K, Brennan +$12K, review |
| n9 | no action anywhere |

**Firm intelligence at load:**

| Item | Book status |
|---|---|
| n1 | Affects my book: 2 households |
| n7 | Affects my book: 3 households |
| n2 | Affects my book: 5 households |
| n5, n6 | Affects my book: 1 household |
| n3, n4, n9 | No identified impact |
| f1–f4 | Not yet evaluated |
| f5 | Superseded: not evaluated |

After analysis:
- f1: Castellano matched ($260K held directly).
- f2: Henderson, Kaplan and Castellano matched (US high yield −5.5 pts against the new view).
- f3: unknown for Henderson, Kaplan, Castellano and Okonkwo.
- f4: no identified impact.

**Engine tax check (4.0):** NVDA, $1M sale for Henderson, gain $801,887, tax $190,849.

---

## 10. Build stages with acceptance checks

Test in headless Chromium with Playwright if you can. Fail a stage on any page error.

| Stage | Build | Accept when |
|---|---|---|
| 1 | Data (section 3), engine `E` (4.0), base charts (section 5) | Engine return and risk match 4.0 for the five base households; the NVDA tax check matches to the dollar; Delgado COST look-through 58.3% |
| 2 | `X` (4.2–4.8) | Program fee checks; cash split and routing for all six households match section 9; attribution effects sum to active |
| 3 | `D` (4.9–4.15, 4.25) | Eligibility, findings and value figures match; 27 queue rows in the stated order |
| 4 | `P` (4.16–4.24) | Buckets, amounts, routes, starting points, ranking and book view match |
| 5 | Shell, top bar, left list, landing (7.2–7.5) | Table shows six rows in ranking order with the right cues, amounts, routes, blockers and next labels; filters count 6 / 5 / 1 / 0 / 0; no horizontal scroll at 390, 1100, 1440px |
| 6 | Household flow (7.6, 7.7, 7.9) and the task panel (7.10) | Henderson client case shows $47.20M, held back $2.50M, ≈70%; pursuing goes to Compare routes; choosing a route enables the proposal button; ticking every handoff item enables the handoff; Implement then reads "Handed off: operations to enroll (prototype)" |
| 7 | Proposal (7.8) | Henderson: value rows, the five managed-account capabilities, the service table, the fee model reacting to sliders, draft rebuild and copy; Castellano shows status "stay"; Delgado blocked |
| 8 | Allocation, position, market and research, firm intelligence (7.11–7.15) | Every view renders for every household or item; event n1 ranks Henderson then Brennan; promoting f1 for Castellano adds one row |
| 9 | Tour and checks (7.16, 7.17) | All 23 tour steps find their targets at 1440px and 390px, and exiting restores the view; checks show 30 of 30 |
| 10 | Polish and scans | Firm-name and program-acronym scan of the HTML is clean; dark mode legible |

**Testing tips:**
- Re-query elements after every click; the page re-renders.
- Section labels are uppercase by CSS, so compare text case-insensitively.
- For checkboxes that re-render on change (handoff), click the label and re-query rather than calling a "check" helper.
- Reset in-page state between test scenarios (reload).
- Sliders: set the value and dispatch an `input` event.

---

## 11. Known pitfalls

1. **Overrides need reassignable functions.** If a base view is a `const`, the later file cannot replace it. Capture the old function before reassigning it, and register the v6 click handler in the capture phase.
2. **Stale queue cache.** Include dispositions, promoted items and the alert threshold in the signature. Don't cache household state, route choices or proposal review state; read them live.
3. **Double counting.**
   - Bonds held to maturity or call are "kept", with a timing note only.
   - Lots without basis are "held for cost basis", never also "moves now".
   - Never add timing notes into totals.
4. **Cash.** Use `X.cashSplit` everywhere. Only the investable part is invested in steps. The CIO cash target moves in kind, and the reserve (including next year's needs) stays.
5. **Two fee bases are intentional.**
   - The value story and the proposal use the full brokerage amount: Henderson $298K vs $55K.
   - Routes and the client case use the amount movable now, labelled "steady state on {now} from enrollment": $284K vs $52K.
6. **Account movement vs trading.** Route cards show both separately; never imply a trade is approved by moving in kind.
7. **"Suggested" wording.** Show "Starting point for advisor review", never "recommended", on routes. Choosing records a working choice, not suitability.
8. **Objection o3.** Offer it only when volatility is above the band and falls at the target. Otherwise list it as not offered, with the numbers.
9. **The specialist route's cost.** Compute the stay cost on the full brokerage amount: Delgado $1,650 a year. v6.2 computed it on the movable amount, which is 0 for an excluded household, and showed "$0 a year in brokerage today". Don't repeat that.
10. **Event merging.** A material event about a held position, or a CIO view for a household that already has an allocation or position row, becomes a related line, not a new row. Otherwise the queue is 30-plus rows and the checks' count differs.
11. **The tour.**
    - Never record decisions.
    - Restore the saved view on exit.
    - Block outside clicks in the capture phase.
    - Use instant scrolling before measuring.
    - Re-place the card on scroll and resize.
    - On phones, open the bottom sheet for the task-panel step.
12. **Long button text** in table cells must wrap (`white-space: normal`). Feasibility icons sit in their own grid column so long lines don't wrap under them.
13. **Dark mode.** Use tokens and `color-mix` with tokens only.
14. **Privacy of firm economics.** Revenue and bp lift appear only in the management view, which is off by default.

---

## 12. Deliverable checklist

- [ ] One HTML file, about 470–520 KB, opens from disk with no server, with no page errors.
- [ ] Six households; reference figures in section 9 match.
- [ ] Landing: ranked households with cues, movable amount, starting route, constraint and owner, one next step, and filters. The internal management view is off by default.
- [ ] Household flow: client case → compare routes (with Stay in brokerage) → client proposal → handoff. Money tags on every figure. The reconciliation bar adds up.
- [ ] Analysis views: allocation, concentrated position, market and research (both tabs). The six-step example opens from the client case.
- [ ] Task panel with one primary action. Record a decision works, and closing needs an outcome or a reason.
- [ ] Guided tour, 23 steps; Esc, the arrow keys and Enter work; the view is restored on exit.
- [ ] Prototype checks: 30 of 30.
- [ ] No horizontal scroll at 390, 1100 and 1440px; dark mode legible; mobile bottom sheet works.
- [ ] Firm-name and program-acronym scan prints nothing.
