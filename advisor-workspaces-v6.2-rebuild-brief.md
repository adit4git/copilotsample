# Advisor Workspaces: rebuild brief (prototype v6.2)

**What this is.** A plain-language brief for a capable coding model (or a developer) to rebuild the Advisor Workspaces prototype as one self-contained HTML page.
- Everything is described in prose.
- The only tables are the data in the appendix and a short list of figures to check against.
- No other file is needed.

**What to build.** One HTML file that opens from disk with no server.
- All styles and scripts are inline. The only outside request allowed is a Google Fonts stylesheet, and the page must still look right without it.
- Six illustrative households.
- Every figure is computed in the page from the appendix data.

**How to read it.**
- Sections 1–4 say what the tool does, how its rules work and what each screen shows.
- Section 5 covers the look. Section 6 gives the build order and the figures that prove the rebuild is right. Section 7 lists traps.
- Where exact wording matters, it appears in quotation marks. Elsewhere, write clear, plain advisor-facing text in the same spirit; you don't have to match it word for word.
- If this was copied by OCR, read for meaning. A number that looks garbled in a table (O.12, 1O%) is a slip; use the obvious value.

**Hard rules.**
1. **No real firm, bank, broker, vendor or fund-manager names**, and no program acronyms, anywhere.
   - The product is "Atlas".
   - The program is the "Advisory program".
   - Moving appreciated holdings in kind and selling them over time is the "Tax-efficient transition".
   - Staged investing of cash is "Invest in steps".
   - The research department is "Research"; the house investment view is "the CIO".
   - The managers in the data (Crestline, Beacon Hill, Ashcroft) are fictional.
2. **Use the appendix data as given.** Don't invent holdings, values, limits or thresholds.
3. **Human-led and illustrative.**
   - The tool never sends, enrolls or trades anything.
   - Decisions are "kept in this page only".
   - The top bar carries a "Prototype · checks" pill.
   - Every money figure says whether it is observed, an estimate, modeled, or needs validation.
4. **Plain language, sentence case.**
   - Internal use-case numbers never appear on screen.
   - Firm revenue appears only in an internal management view that is off by default.

---

## 1. The product

Atlas Advisor Workspaces helps an advisor find brokerage households where moving into an advisory relationship could genuinely help the client. It explains why, compares the ways to get there, prepares a proposal for review, and hands off to operations. The advisor decides at every step. Staying in brokerage is always a legitimate, recordable outcome, and a lower-cost index-only option is always shown.

**The five stages.** The tool follows five operating stages. Each has a line on what the tool does, what the advisor decides, and a key control:

| Stage | The tool… | The advisor… | Key control |
|---|---|---|---|
| Identify | ranks opportunities | (or a specialist) picks one up | approved thresholds and data masking |
| Analyze | positions the household against its goals and the CIO target | decides whether to pursue | approved content; lower-cost alternative shown |
| Design | matches options and builds the transition plan | selects strategy and pace | fit before tax; no tax estimate without cost basis |
| Propose | builds the client story | approves and presents | advisor review; nothing sent automatically |
| Implement | prepares the hand-off | (with operations) enrolls | no autonomous execution or enrollment |

**What the advisor sees:**
- **My book (the landing page):** one row per household, in an order that is stated and easy to explain. Each row shows:
  - why now;
  - how much could move now;
  - a starting route;
  - the main constraint and who owns it;
  - one next step.
- **The household flow:** four steps shown as a stepper.
  1. Client case
  2. Compare routes
  3. Client proposal
  4. Implementation handoff
- **Four analysis views,** one click away:
  - Allocation and performance;
  - Concentrated position;
  - Market and research, with two tabs: what affects my book, and everything published;
  - a six-step worked example per opportunity: Trigger → Size the gap → Value the gap → Match options → Plan transition → Client story.
- **A task panel** on the right: the current task, owner, blocker, status and one primary action. Supporting detail is tucked into collapsible sections.
- **A 23-step guided tour** that spotlights the live screens.
- **A "Prototype checks" dialog** that runs 30 logic checks in the browser.

**Principles every screen follows:**
- **Value first, then cost.** Expected return at the CIO allocation and tax management come before the fee. The fee is always shown.
- **One eligibility rule everywhere.** A household with more than 50% in one security, counting direct holdings plus what its funds hold, is not eligible for the program and gets only a specialist route.
- **One investable-cash figure,** used by every screen.
- **Every brokerage dollar sits in exactly one bucket:** moves now, held for cost basis, kept in brokerage, or excluded. Bond calls and maturities are timing notes, never extra amounts.
- **Moving the account (in kind, at enrollment) is not trading the portfolio** (repositioning over time). Show the two separately.
- **A ranking, or a "starting point for advisor review", is a prompt, not a suitability conclusion.**
- **Recording an assessment doesn't close work.** Closing needs an outcome, or a reason for staying, not suitable or defer.

---

## 2. How to build it

**One file, layered scripts.**
- Write the page as a few script layers inlined in order:
  1. the portfolio math;
  2. the charts;
  3. the workspace calculations;
  4. the decision rules;
  5. the pathway rules;
  6. the base screens;
  7. a layer of screen overrides;
  8. the tour;
  9. the checks.
- Later layers may replace earlier screen functions, so make those functions reassignable.
- A short Python or Node script that stitches the pieces into one HTML file is the easiest way to work. So is writing the single file directly.

**Page skeleton.**
- A top bar.
- A three-column layout: a left list, the main stage and a right task panel.
- A toast area for short confirmations.

**Rendering.**
- Use no framework. Build HTML from template strings, and escape every piece of data text.
- One paint function redraws the top bar, the left list, the stage and the task panel. Keep the scroll position on in-place changes, and scroll to the top on navigation.
- Handle all interaction with a few delegated listeners on the document that read `data-` attributes.

**State.** Keep all state in memory; nothing persists across reloads. It holds:
- the current view, household, household step and landing filter;
- the advisor's assessments and closures, keyed by item;
- chosen routes;
- handoff ticks;
- proposal settings per household;
- the concentration alert threshold;
- which collapsible sections are open;
- talking points;
- firm-intelligence watchlist and analysis flags.

**Caching.** The opportunity list is costly to compute, so cache it. Recompute only when assessments, promoted intelligence items or the alert threshold change. Always read route choices and proposal status live.

---

## 3. The rules, in plain language

Implement these faithfully. The figures in section 6 depend on them.

### 3.1 Portfolio math

**Weights and statistics.**
- A holding's value is split across asset classes by its class shares. Holdings with no classes are left out of the class weights.
- Expected return is the weighted sum of class returns.
- Volatility is the square root of the usual weighted-covariance sum. The covariance of two classes is the product of their volatilities and their correlation, which is 1 for a class with itself.
- Tracking error between two allocations is the same calculation applied to the difference in weights, over every class in either allocation.
- Group classes into equity (the five stock classes), fixed income (Treasuries, investment-grade corporates, high yield), cash, and alternatives (hedge funds, private equity).

**Look-through exposure to one name** = the value of the stock held directly, plus each fund's value times that name's weight inside the fund, all divided by the household total. This drives concentration and the 50% rule.

**Past-event loss.** Apply each holding's return in a past event to its value, over the classified holdings. The worst event is the one with the lowest result.

**Selling from tax lots.**
- Lots without a cost basis are never sold.
- Sell order:
  1. losses first, biggest loss first;
  2. then long-term lots, smallest gain ratio first;
  3. then short-term lots.
- Gain on a partial sale is proportional. Tax uses the long-term or short-term rate of each lot.

**Program fee.** Tiered by slab:

| Assets | Rate |
|---|---|
| First $1M | 1.00% |
| Up to $5M | 0.80% |
| Up to $10M | 0.65% |
| Above $10M | 0.50% |

**Four cost options** compared for an amount (default: the brokerage total, rounded to $1,000):

| Option | Cost | Return and risk |
|---|---|---|
| Stay in brokerage | today's value-weighted fund expenses, plus commissions of 0.75% on 12% turnover | today's |
| Advisory program: CIO model | program fee, plus 5 bp model funds | the CIO tactical target |
| Advisory program with SMA managers | program fee; 30 bp manager fee on half the equity; model funds on the rest | the CIO tactical target |
| Advisory program: index-only portfolio | 0.45% flat, plus 4 bp funds | the strategic target |

**CIO targets.**
- The strategic target is the household's profile model.
- The tactical target adds the CIO tilts to each class the model holds, floors each result at zero and rescales the total to 100%.
- A class is "outside tolerance" when it is more than 3 points from target; a group, more than 5 points.

**Attribution** against the strategic target, using today's weights over the period. Use the standard allocation, selection and interaction effects:

| Effect | Formula |
|---|---|
| Allocation | (weight difference) × (class benchmark − total benchmark) |
| Selection | target weight × (portfolio class return − class benchmark) |
| Interaction | the remainder |

- A holding's period return is its own figure when the appendix has one; otherwise its class-weighted benchmark.
- The three effects must add up exactly to the active return.

### 3.2 Investable cash (one figure everywhere)

Count cash, meaning the sweep and the money market fund, in brokerage only.
1. **Cash target** = the smaller of all cash, or the tactical cash weight × brokerage.
2. **Reserve** = the smaller of what is left after the target, or the household's liquidity reserve plus any cash needs dated 2027 or earlier.
3. **Investable** = whatever remains.

Only the investable part is invested in steps. The target part moves as the program's cash, and the reserve stays in brokerage.

### 3.3 Where each brokerage holding goes

**Cash** splits proportionally into three parts:
- invest in steps (over six months);
- move in kind (the target part);
- kept as the liquidity reserve.

**Every other holding** takes the first route that applies:
1. Not transferable (individual bonds, private assets, manager-run stocks) → stays where it is.
2. Any lot missing cost basis → held until the basis is found.
3. A loss of more than $1,000 → sell, harvest the loss and reinvest.
4. Costs at least 50 bp with a gain under 30% of value → replace with a lower-cost share class.
5. A gain above 20% of value → tax-efficient transition: move in kind and sell over time within the yearly gain budget.
6. Otherwise → move in kind.

### 3.4 Buckets and the headline amounts

**Buckets.** Every routed amount goes into one bucket:
- **Moves now (in kind):** in kind, swaps, transitions, harvests and invest-in-steps.
- **Held for cost basis:** lots missing basis.
- **Kept in brokerage:** the reserve and anything not transferable.
- **Excluded:** everything, when the household is above the 50% limit.

The buckets add back exactly to the brokerage total. A bond's call or maturity date is a note on its row ("Callable 2026-12-15: proceeds can be reinvested then"), never an amount.

**Headline amounts:**
- **Potentially movable now** = moves now.
- **Held back** = held for basis plus kept, listed with reasons: "liquidity reserve and near-term needs", "matures 2032", "awaiting cost basis".
- **Year-one alignment (phased route).** Everything moved in kind, swapped, harvested or invested in steps, plus the part of appreciated holdings sold within the year's gain budget, as a share of what can move.
- **Repositioned over time** = movable now minus what is aligned in year one.
- A confidence label: Low if excluded, Medium if anything is held for basis or the reserve is unknown, otherwise High.

**Year-one tax.**
- On the phased route: the gain realised within the budget, minus losses harvested in the move, at the long-term rate.
- Rebalancing at once: all gains minus losses.
- Trading cost: 5 bp of the amount traded, where traded = twice the sales, plus the cash invested.

### 3.5 Eligibility (one rule, used everywhere)

**The test.** Take the largest single-name exposure, direct plus through funds.
- Above 50%, the household is **not eligible**. Explain where the exposure sits, for example "58.2% direct, 0.2% through funds". The program, CIO models, SMA and direct indexing, and the tax-efficient transition are all blocked, and the route is the concentrated stock specialist.
- Otherwise it is **eligible in principle**, or **eligible in principle, with conditions** when any condition applies.

**Conditions**, each with an owner:
- Insider rules: Compliance.
- Lots missing cost basis: Operations.
- Manager-run holdings: the Manager.

**Labels** (also used as short pills):

| Status | Full label | Short label |
|---|---|---|
| Eligible | Eligible in principle | Eligible in principle |
| With conditions | Eligible in principle, with conditions | Eligible · conditions |
| Specialist | Requires specialist review | Specialist review |
| Not eligible | Not eligible for the program | Not eligible |

### 3.6 Readiness and the five stages

**Readiness** has three steps:
1. **Client discussion** is always ready.
2. **Proposal** is pending until its items clear:
   - suitability (Advisor);
   - any Operations condition;
   - product eligibility for SMA or direct indexing (Product team), where relevant.

   It is blocked outright when the household is not eligible.
3. **Implementation** always reads "Not cleared: n prerequisites outstanding" until handed off. Its items are:
   - insider and manager conditions;
   - client agreement;
   - a validated trade plan (Portfolio management);
   - compliance review of materials;
   - supervisory approval.

Never write "Not eligible yet".

**The five stages:**

| Stage | State |
|---|---|
| Identify | always ready |
| Analyze | ready once the advisor chooses to pursue; blocked if they record stay, not suitable, defer or monitor |
| Design | ready once a route is chosen; blocked if not eligible |
| Propose | ready once submitted for compliance review; blocked if not eligible |
| Implement | always blocked until the advisor hands off, then "Handed off: operations to enroll (prototype)" |

### 3.7 Workflow: assessment versus closing

**The advisor's assessment** is one of:
- Ready for client discussion;
- Review needed;
- Specialist review;
- Stay in brokerage;
- Monitor;
- Defer;
- Not suitable.

**How an assessment affects the item:**
- An assessment alone keeps the item open.
- Stay, not suitable and defer need a reason before they take effect. Until a reason is added, show "Add a reason to close it" and keep the item open.
  - With a reason, stay and not suitable close the item; defer moves it to Monitor.
- Monitor moves the item to Monitor.
- Closing with an outcome always closes it. The outcomes:
  - Discussed with the client;
  - Proposal submitted for review;
  - Referred to the specialist;
  - Client declined;
  - No action needed after review.

**Reasons to offer:**
- tax cost too high;
- trading restriction;
- insufficient client value;
- poor fit for the client;
- client declined;
- missing data;
- timing: revisit later;
- other.

**Grouping on the workflow view:**
- **Needs action:** everything else.
- **Specialist or not eligible.**
- **Monitor or deferred:** includes untouched items whose own status is monitor or no action.
- **Closed.**

### 3.8 The allocation finding (one per household)

**Settings.** Use brokerage accounts, the tactical target and three-year returns unless the advisor changes them. If the household has no brokerage holdings, use the whole household.

**The first rule that applies sets the finding:**

| # | Finding | Applies when | Status |
|---|---|---|---|
| 1 | Not eligible | above 50% | specialist review |
| 2 | Risk above the profile band | volatility above the band | review needed |
| 3 | Large cash | volatility below the band and over 20% in cash | review needed |
| 4 | Single-company concentration | the largest name above the alert threshold (default 10%) | ready for discussion |
| 5 | Trailing the CIO allocation | by more than 1 point a year | review needed |
| 6 | Drift | any class outside tolerance | monitor |
| 7 | In line | otherwise | no action |

**Explaining the finding.**
- Write a "why" sentence that names the right measure. Concentration is about one company, not portfolio volatility.
- When moving to the target would change volatility, say so with the numbers, in this exact pattern: "would also lower expected volatility (9.2% → 8.9%)", "would … raise expected portfolio volatility slightly (9.2% → 9.5%)", or "would stay about the same (… → …)".
  - Compare at one decimal.
  - When volatility rises, explain why: the target holds less cash, or more stocks, or has a different mix.
- The concentration case also states what a 30% fall in the stock would cost.

**Trade-off rows:**
- concentration against the 10% guideline;
- volatility today → target;
- tracking error → 0%;
- position against the profile band;
- "Estimated gains, year one (planning)": gains up to the budget and their tax;
- fees: program versus today.

**Choices** depend on the finding:
- specialist first when not eligible;
- monitor first when drifting or in line;
- otherwise "Review alternatives" first, then stay in brokerage, the advisory program and monitor.

### 3.9 Advisory value (value first, then the fee)

**Annual value:**
- **Expected-return gain** = (return at the tactical target − return today) × amount.
- **Direct-indexing harvest.** This applies only when the household is eligible and the equity to index is at least $250K. The equity to index is the tactical equity share of the amount, capped at 40% of the amount.
  - Tax value = 2% of that equity a year × the long-term rate.
  - Net of a 20 bp manager fee.

**Totals:**
- **Quantified value** = the positive parts of both.
- **Higher fee** = program cost − today's cost.
- **Net** = return gain + harvest net − higher fee.
- **Coverage** = quantified value ÷ higher fee.

One-time items (losses harvested in the move, and tax-efficient handling of gains) are shown, but not added in.

**Status:**
- Blocked when not eligible.
- "Stay" when the allocation finding is drift or in line and the net is negative.
- Otherwise ready.

**Points to weigh openly:**
- benefits cover only part of the fee;
- volatility rises at the target;
- funds already cost under 15 bp;
- light trading;
- not eligible.

**What only a managed account can do,** applied to the client's own holdings:
- **Direct indexing with loss harvesting**, when available.
- **Custom exclusions and tilts.** Leave the concentrated names out of the index and tilt away from their sectors.
- **Tax-managed transition of existing stocks**, when there are gains.
- **An individual municipal bond ladder**, when the household holds a muni fund and its bracket is 32% or more.
- **Tax-aware rebalancing across accounts.**

### 3.10 Opportunities: what gets flagged

Build one list across the book. **For each household:**
1. **The allocation finding.** Add it unless it is "in line", or it duplicates a concentration item about the same stock.
2. **Concentrated stocks.** Add one item for each name held directly whose look-through share is above the alert threshold.
   - Above 50%: specialist route.
   - Insider stock: conditions apply.
   - Otherwise: lots and tax conditions.
3. **Material events** (rules in 3.14). If an event hits a stock that already has a concentration item, or is a CIO view for a household that already has an allocation or concentration item, add it to that item as a related note instead of a new row.
4. **Pathway screens** (eligible households only):
   - **Embedded gains and losses:** a taxable household with at least $5K of gains or $25K of losses.
   - **Individual bonds:** flagged as callable when the call is within 90 days of 24 October 2026.
   - **Excess cash:** investable cash above 5% of brokerage. Skip it when the allocation finding is already the large-cash one.
   - **High-cost funds:** 50 bp or more.
   - **Commissions:** commissions at least half the program fee. No household triggers this.
5. **An advisory-proposal item**, when the allocation status is review or ready, the household is eligible and it has at least $250K in brokerage.

Rank closed items last, then by an internal priority.

**Kinds.** Each item is shown with a plain kind label:
- Allocation gap;
- Embedded gains and losses;
- Individual bonds;
- Excess cash;
- High-cost funds;
- Advisory proposal;
- Concentrated stock;
- Market or research event;
- Trading costs.

**Six steps per item.** Each item carries a trigger, a size, a value statement, an advisory pathway and the six worked steps:

| Step | What it shows |
|---|---|
| Value the gap | an "illustrative scenario difference (modeled)" when the value is a return difference, never "growth given up" |
| Match options | lists the fitting strategies and always ends with "lower-cost alternative shown: Advisory program: index-only portfolio (49 bp)" |
| Plan transition | summarises the routing, year-one alignment, tax and trading cost; for bonds it says they are held to call or maturity and the proceeds go into a managed ladder |
| Client story | the proposal's review status |

**Strategy fit.** Score each strategy:
- points for closing underweight classes it covers;
- points for replacing classes with poor performers;
- points for tax management when gains are large;
- points for being able to exclude a concentrated stock;
- a base score for the CIO model;
- penalties when the minimum is large for the account, or for alternatives nobody needs.

Show the top four. Not-eligible households get none.

### 3.11 Ranking households, cues and the one next step

**Why now.** Each household's primary item is its weightiest open item:
1. an excluded concentration;
2. then a concentration (heavier the bigger it is);
3. large excess cash;
4. risk above the band;
5. a bond call;
6. gains;
7. high-cost funds;
8. events;
9. trading costs;
10. the advisory-proposal item.

The "why now" sentence comes from the primary item, for example "NVDA is 22.9% of the account" or "$11.42M of cash sits above the CIO target after a $1.50M reserve".

**Cues** on the landing:
- "Meeting in n days" (within 7 days);
- "Call date …";
- "Client request";
- "Tax-basis blocker";
- "Large movable amount" (at least $10M).

**Constraint and owner** (the first that applies):
1. above the 50% limit: Specialist;
2. missing basis: Operations;
3. insider rules: Compliance;
4. manager-run sleeve: Manager;
5. otherwise suitability determination: Advisor.

**Order of households.** Stated under the table:
1. households above 50% go last;
2. before them, those with a meeting within a week, a bond call or a client request come first;
3. then by amount movable now.

**Household step and next label:**

| Situation | Next label |
|---|---|
| Nothing decided yet | "Review assessment" (not-eligible households: "Request specialist") |
| Pursuing, no route chosen | "Compare paths" |
| Route chosen, proposal not submitted | "Prepare proposal" |
| Submitted for compliance | "Complete handoff" |
| An outcome recorded | the outcome itself |

**Filters** on the landing:
- Needs discussion;
- Waiting on specialist or operations;
- Ready to propose;
- Outcome recorded.

### 3.12 Routes (compare side by side)

Costs here use the amount movable now, labelled "steady state on {amount} from enrollment".

**An eligible household gets:**
- **Transfer and rebalance now.** Fastest; the highest year-one tax; full alignment in year one.
- **Phased and tax-aware transition.** Year-one tax within the gain budget; excess cash invested over six months; full alignment in about (gains ÷ budget, rounded up) years.
- **Managed accounts: tax-managed SMA and direct indexing.** Excludes the concentrated names. Offered only when direct indexing is available and there are concentrated names or large gains.

**Each route shows:**
- why it fits;
- two trade-offs;
- account movement ("moves in kind at enrollment");
- portfolio trading (the timeline);
- tax;
- steady-state cost;
- who approves;
- the feasibility checks still open, each with an owner: suitability, missing basis, insider pre-clearance, manager sleeve, and product minimums for the managed route.

**Starting point.** Exactly one route is marked "Starting point for advisor review":
- the managed route when there are concentrated names;
- otherwise phased when there are gains or excess cash;
- otherwise rebalance.

**Not-eligible households** get a single "Specialist route for the position":
- nothing moves into the program now;
- staged sales in brokerage within trading windows;
- today's cost on the full brokerage amount.

**Stay in brokerage** is always shown as a card in the same grid:
- today's cost;
- what the client would not get;
- the index-only alternative and its cost;
- up to three reasons to stay;
- buttons to remain, monitor or refer.

**The handoff checklist:**
1. strategy and pace selected (ticked automatically once a route is chosen);
2. proposal submitted for compliance (ticked automatically once submitted);
3. the implementation prerequisites;
4. a six-month invest-in-steps schedule, November 2026 to April 2027.

### 3.13 Concentrated-position plan

**Settings:**
- target 10%;
- the household's yearly gain budget;
- a $250K yearly gift when the file shows a gifting intent;
- six years;
- the cash needs on file.

**Each year from 2026:**
1. Gift the lowest-basis shares, up to the gift amount.
2. Sell the excess above target, using the lot order in 3.1, but no more gain than the budget allows.
3. If that year's cash need is larger, sell the need instead. Mark the year "over budget" when this breaks the budget.
4. Prices are held constant, and gifts and needs leave the household.

Report each year's share and the year the target is reached.

**Solutions**, each with how actionable it is and a fit score:

| Solution | Actionability |
|---|---|
| Staged sale in brokerage | after pre-clearance for insiders |
| Tax-managed SMA | blocked above 50% |
| Direct indexing with the stock excluded | blocked above 50% |
| Gift low-basis lots | client and tax advisor decide |
| Collar or exchange fund | specialist |

**A small decision tree:**
- insider?
- above 50%?
- gifting?
- cash needs?
- keep the upside?

Each yes highlights its outcome, and a result line chains them.

### 3.14 Events and firm intelligence

**Estimating a market event's effect** on each holding:
- a direct move for named stocks;
- the move scaled by the name's weight inside each fund;
- sector moves (scaled by equity share and sector weight for funds);
- class moves for bonds.

Label the total "estimated scenario impact"; it is not a realised result.

**When an event is material:**

| Event | Material when | Then |
|---|---|---|
| Market move | at least 0.5% of the account | "review the concentrated position" if a concentrated name is involved, else "contact the client"; 0.1–0.5% is monitor |
| CIO view | an asset class at least 5 points against the new view | "reassess the allocation" |
| Research rating change | the stock is held directly | "request a manager review" if a manager runs it, else "review alternatives" |
| Client question | always | "respond to the client" |

**Firm intelligence** is a catalogue of everything the advisor may read:
- the sample events (evaluated automatically), plus five extra items;
- the extra items are evaluated only when the advisor clicks "Analyze against my book".

**Results per household:**
- material match;
- monitor;
- no identified impact;
- not evaluated: insufficient data (the European banks item cannot be measured because international funds have no country-by-sector data);
- superseded.

**Rules:**
- Reading or analysing never adds work. Only "Add to opportunities" on a material match adds an item.
- Only client-approved, current items can be saved for a client meeting.

---

## 4. The screens

### 4.1 Top bar and left list

**Top bar,** from left to right:
- a small teal brand mark, with "Advisor workspaces" over "Atlas · prototype v6.2";
- a breadcrumb: "My book", with a count of open items (27 at load), then "› household › current view" when inside a household;
- a "Market and research" button;
- "Illustrative data as of 2026-10-15";
- a "Tour" button;
- the "Prototype · checks" pill.

There are no use-case tabs.

**Left list,** by view:
- **Landing and household flow:** the households in ranking order, with "{amount} now · {starting route}" or "Not eligible now" under each name.
- **Allocation view and proposal:** the households.
- **Concentrated-position view:** the positions above the threshold.
- **Market and research:** filters and the events or catalogue.

### 4.2 Landing: "Brokerage opportunities in your book"

- **Subtitle:** "Which household, why now, how much could move, by which route, and what to do next."
- A one-line invitation to take the guided tour.
- A toggle between "Households" and "All opportunities (workflow)".
- A link to show the internal management view.
- **Filter chips** with counts. At load: all 6, needs discussion 5, waiting 1, ready to propose 0, outcome recorded 0.

**Table, one row per household:**

| Column | What it shows |
|---|---|
| Household · why now | the name; the cue pills; the why-now sentence; a small "n other signals" disclosure listing the household's other items |
| Potentially movable now | the amount with an "observed" tag; "held back {amount}" underneath. Not-eligible households show a dash and "Not eligible now" |
| Starting route | the route name and "starting point for review" |
| Constraint · owner | the blocker with its owner tag |
| Next | a button with the next step, and the meeting under it. Once an outcome is recorded, the outcome instead |

**Note under the table:** "Order: households with a meeting, call date or client request coming up first, then by the amount potentially movable now; accounts above the 50% limit last. A rank is a prompt for review, not a suitability conclusion."

**Management view (internal, off by default).** Addressable brokerage assets, the split by tax difficulty, and firm revenue in basis points before and after. It is labelled "internal · not client-facing".

| Tax difficulty | Means |
|---|---|
| Hard | age 80+, gains of 15% or more, or A shares with gains of 3% or more |
| Medium | gains of 3% or more |
| Low | otherwise |

**Workflow view.** Every item, grouped (needs action, specialist, monitor, closed), with its kind, pathway, impact, next action, status and lifecycle, plus filters by group and source.

### 4.3 Household step 1: Client case

The household name, profile, brokerage amount and meeting, then the four-step stepper (finished steps show a tick). Below that, a summary card:

1. **"Why now".** A large serif sentence: the primary reason plus any catalysts. The eligibility pill sits on the right.
2. **Two boxes:**
   - "Potentially movable to advisory now" with a large number, then "Held back: …";
   - "What stands in the way": the blocker, its owner, and any warning about a missing reserve or about cash needs after 2027 that aren't reserved.
3. **Three small measures**, each tagged:
   - "Moves into the account at enrollment" (observed; in kind, no trade implied);
   - "Repositioned over time" (modeled);
   - "Estimated target alignment, year one" (modeled; rebalancing now reaches about 100%).
4. **"Client value and cost, by measure"**, each line tagged:
   - risk, today → target, against the band;
   - expected return, gross, as an illustrative scenario difference per year;
   - concentration;
   - year-one tax, phased versus at once. Tag it "needs validation" and add "Not decision-ready" when basis is missing;
   - loss harvesting (direct-indexing route only);
   - the incremental fee, always shown in amber, with the index-only alternative's cost.
5. **"Your decision"** (prototype: kept in this page only). Four buttons:
   - "Pursue: compare routes" (hidden when not eligible);
   - "Remain in brokerage";
   - "Monitor";
   - "Refer to specialist".

   Pursue moves on to Compare routes. A choice that needs a reason shows a reason picker and stays open until one is given.

**Below the card:**
- "Other signals for this household", each with an "Open the analysis" link.
- Collapsible sections:
  - "How the amounts reconcile": a stacked bar of the four buckets that adds back to the total with a tick, and a per-holding table of bucket, route and timing note;
  - "How it was found": the six-step example, with chips to switch between the household's items;
  - "Transition plan by holding";
  - "Evidence and sources": data dates and the meeting note.

### 4.4 Step 2: Compare routes

- **Intro line:** "Account movement and portfolio trading are shown separately. Choosing a route records a working choice for the proposal; it is not a suitability approval."
- **Route cards and the Stay in brokerage card** sit in one grid: two columns on most screens, more on very wide screens, one on phones.
- **Choosing a route:**
  - marks the card;
  - records the household as pursuing;
  - enables "Next: prepare the client proposal".
- **Below:** "Show all alternatives" (the fitting strategies plus the index-only option) and the transition plan.

### 4.5 Step 3: Client proposal

**Summary card.**
- **Finding**, by situation:

  | Situation | Finding |
  |---|---|
  | Positive net | "An advisory relationship could add about {net} a year for {household} after its higher fee, through the CIO allocation and tax-loss harvesting, plus {the plan} (illustrative)" |
  | Negative net | what the client would get, and the share of the higher fee the estimated benefits cover |
  | Stay status | that staying in brokerage may suit |
  | Blocked | that the program is not available above 50% |

- **Value rows:** the return gain, the harvest net, one-time items, concentration, volatility, the higher fee and the net.
- **Choices:**
  - the CIO model;
  - with direct indexing and SMA managers;
  - index-only (compensation differs);
  - stay in brokerage.

**Then:**
- **"Only in a managed account"** cards, each tagged "Managed accounts only".
- **"The value case"** in three columns: what the client would gain; what it costs; points to weigh openly. Below it, a disclosure that staying in brokerage remains a legitimate choice.

**Collapsible sections:**
1. **A service comparison table** across the four options:
   - standard of care;
   - monitoring;
   - CIO allocation;
   - tax management;
   - direct indexing;
   - tax-managed transition;
   - municipal ladder;
   - trading costs;
   - annual cost for this client;
   - return and risk;
   - advisor compensation.
2. **"1 · Why now":** checkable reasons, each with its source, plus talking points collected elsewhere.
3. **"2 · Fee model":** controls for the amount, brokerage trading (0–50%) and the share of equity with SMA managers; four cost cards with small donuts; the program fee tier table.
4. **"3 · Client considerations":** checkable objections with their approved answers.
   - The objection "My portfolio has done well. Why change it?" claims less risk. Offer it only when risk is above the band and falls at the target.
   - Otherwise list it as not offered, with the numbers.
5. **"4 · Advisor preparation":**
   - approved materials (advisor-only items can't be ticked; expiry within 90 days shows in red);
   - a generated client story draft in an editable box, marked "Generated draft · requires advisor and compliance review", with a version number;
   - a review status: Draft, Advisor reviewed, or Submitted for compliance;
   - "Rebuild draft" and "Copy";
   - an advisor note marked not pre-approved;
   - the sources used.

**The draft** is plain text with these sections:
1. why we are talking now;
2. what the program could do;
3. what only a managed account can do;
4. how the move would work tax-efficiently;
5. what it costs;
6. your options (including index-only and staying);
7. things to weigh;
8. questions;
9. enclosed materials;
10. the advisor note;
11. a closing line that the figures are illustrative and the draft is for review.

Setting the status to "Submitted for compliance" moves the household to the handoff step.

### 4.6 Step 4: Implementation handoff

**"Before anything moves":**
- A checklist of the handoff items with owners. The items filled from the workflow are ticked and locked.
- "Hand off to operations" unlocks only when every item is ticked and the household is eligible. After it is pressed:
  - the stage reads "Handed off: operations to enroll (prototype)";
  - the note says nothing is executed by this tool.

**"Handoff package":** the amount to enroll now, the amount later when gated, the amount kept, and the six-month invest-in-steps schedule.

### 4.7 Task panel (right)

**The visible part:**
- "Current task": the household and the current stage, with its note;
- one full-width primary button with the next step;
- Owner ("You (advisor)", or "You, then Operations");
- Blocking;
- Status (eligibility · implementation state);
- the five stages as small chips, the current one outlined.

**Collapsed underneath:**
- a short story draft, marked "prepared for review, not approved";
- the full stage ladder, with "You decide" and "Control" lines and all blockers with owners;
- "Record a decision": assessment, reason, close with an outcome, reopen. It is open by default on the analysis views. It carries the note that this is not a CRM or audit record.

On phones the panel becomes a bottom sheet with an Open/Close handle.

### 4.8 Analysis views

**Allocation and performance:**
- A summary card with three small toggles: brokerage or whole household; strategic or tactical; 1 or 3 years. It warns when the settings differ from the baseline.
- Collapsible sections:
  - **Allocation against bands:** a dot-on-band chart per group or class, a volatility gauge against the profile band, and a table of what is outside tolerance.
  - **Attribution:** a waterfall from the CIO allocation, through allocation, selection and interaction, to this portfolio; a shaded table by class; chips for the worst performers.
  - **Strategies that fit.**
  - **How it would move:** a routing donut, the table, and the invest-in-steps months.

**Concentrated position:**
- An alert-threshold slider (5–30%) beside the fixed 50% gate, which is explained as a business rule.
- A summary card with any blockers and conditions.
- The decision tree, with chips for the gifting, cash-need and keep-upside answers.
- Collapsible sections:
  - risk before and after (today, year one, and a full trim);
  - the tax-lot table (missing basis flagged as a blocker; low-basis lots marked as gift candidates);
  - the multi-year plan, with target, budget, gift and cash-need controls, a line chart of share by year with the target line, and a yearly table;
  - solutions and actionability.

**Market and research.** Two large tabs.
- **My book impact:**
  - the event headline and summary;
  - a summary card for the selected household: action, size, why this client, and confidence;
  - the affected households, ranked (material first, the rest collapsed);
  - holders outside these households, listed as "across the book";
  - how the event reaches the portfolio;
  - the house view and research;
  - a short client story with "Add to talking points".
- **Firm intelligence:**
  - "everything you are entitled to read" (13 items), with a search box and filters by type and book impact;
  - each card shows type, date, headline, abstract, house stance, client-use and entitlement status;
  - buttons on each card: Analyze, Watchlist, "Save for {client}'s meeting" (approved items only), and a disabled "Open approved source · not in prototype";
  - superseded items are faded and cannot be analysed;
  - results list each household's match, with "Add to opportunities" on material matches.

**Shared summary card** (allocation, proposal, position and event views):
- finding, why, evidence, trade-offs, choices and next step;
- a compact six-step strip.

Each choice records itself, sets a matching assessment and opens what supports it. For example, "Review alternatives" opens Strategies that fit.

### 4.9 Guided tour (23 steps)

**Behaviour:**
- Each step switches to a view and spotlights one element with a dimmed overlay and a cut-out. It never records a decision.
- On exit, restore what the advisor was looking at.
- Keys: Esc exits; Enter or → goes next; ← goes back.
- Clicks outside the tour card are blocked while the tour is open.
- The card shows "Guided tour · n of 23", a serif title, the text, progress dots, and Exit, Back and Next or Finish.
- **Placement:**
  - beside or below the target;
  - in the lower corner for tall targets;
  - centred when there is no target;
  - as a bottom sheet on phones.
- Start it from the Tour button, from the landing invitation, or by adding "#tour" to the address.

**The steps:**
1. How this tool works.
2. Identify: brokerage opportunities in your book (the table).
3. Why it is near the top (cues).
4. Filter by what is needed.
5. Potentially movable now.
6. A starting route, not a recommendation.
7. One next step.
8. Management view (internal).
9. Each household: four steps (stepper).
10. Analyze: how much, and what is in the way.
11. Moving the account is not trading the portfolio.
12. Every money figure says what it is.
13. Amounts that reconcile (open that section).
14. Your decision.
15. Design: compare routes side by side.
16. A starting point for your review.
17. Stay in brokerage, as a real option.
18. Propose: the client proposal.
19. Implement: hand-off, never execution.
20. Your task panel.
21. The analysis is still one click away.
22. Check the logic yourself (the checks pill).
23. That is the flow.

Use Henderson for the household steps.

### 4.10 Prototype checks (30)

**How it runs.** The pill runs the checks on a copy of the state and restores it, so nothing on screen changes. It shows "{n} of 30 passed", grouped by area.

**The checks:**
- **Eligibility:**
  - each household's items use its eligibility label;
  - a synthetic household with 70% of one name held only through a fund is not eligible;
  - Delgado is not eligible via direct holdings.
- **Readiness:**
  - no "Not eligible yet" wording;
  - discussion is ready while implementation is not cleared.
- **Workflow:**
  - review keeps an item in needs action;
  - specialist, stay, stay with a reason, defer with a reason and closing each land in the right group.
- **Claims:**
  - in all 48 combinations of household and setting, the volatility wording matches its numbers;
  - attribution effects sum exactly;
  - the year-one gains label says "planning".
- **Value:**
  - net = return gain + harvest − higher fee, for every household;
  - not-eligible households get no harvest value.
- **Pathway:**
  - all 27 items have a kind, a pathway and six steps;
  - every eligible pathway shows "lower-cost alternative shown";
  - excluded households have nothing in scope;
  - implementation always ends blocked.
- **Amounts:**
  - one investable-cash figure, used everywhere, and never more than cash above target after the reserve;
  - the buckets add back;
  - identified ≥ eligible ≥ movable now.
- **Routes:**
  - every route has checks with owners and an approver;
  - not-eligible households get only the specialist route;
  - exactly one starting point per household.
- **Events:** market sizes say "estimated scenario impact".
- **Intelligence:**
  - analyzing all 13 items doesn't change the item count;
  - superseded items are not evaluated, and missing look-through reads "not evaluated";
  - only approved items can be saved for a meeting.

---

## 5. Look and feel

**Overall:**
- a calm, professional finance tool;
- light gray page, white cards with 14px rounded corners and a hairline border;
- deep teal as the brand color;
- serif page titles (Newsreader);
- Public Sans for the interface, and IBM Plex Mono for tickers;
- small uppercase section labels;
- tabular numbers.

**Light theme:**

| Role | Color |
|---|---|
| Page | #EEF0F3 |
| Card | #FFFFFF |
| Soft panel | #F6F7F9 |
| Text | #141A23 |
| Secondary text | #3D4655 |
| Muted text | #687282 |
| Border | #DDE2E8 |
| Brand | #0C5D51 |
| Brand tint | #E3F0ED |
| Good | #0B7A4B |
| Warning | #9E5E12 |
| Bad | #A2323E |

The status colors each have a pale tint.

**Dark theme.** Define it with the same roles: page #0B0E13, card #141922, text #E6E9EF, brand #3FB7A0. Follow the system setting.

**Chart colors** are used in a fixed order: blue #2a78d6, orange #eb6834, aqua #1baf7a, yellow #eda100, pink #e87ba4, green #008300, violet #6250d6, red #e34948. Gray is for "other".

**Color meaning:**
- Amber marks a difference from the house model.
- Red is reserved for profile breaches, blockers and missing data.

**Small elements:**
- **Money tags:** tiny outlined uppercase labels.
- **Owner tags:** small violet chips.
- **Cue pills:** amber for dates, teal for client requests, red for basis blockers.
- **Starting-point badge:** a small blue label on its own line.

**Charts** are hand-drawn SVG: donut, semicircle gauge, horizontal waterfall, dot-on-band rows, a line chart with a target line, and the decision tree. Each has a hover tooltip and sits beside a table, so color never carries meaning alone.

**Layout and screen sizes:**
- Desktop: list 258px, stage flexible, panel 340px.
- At 1320px and below: the list becomes a strip across the top.
- At 880px and below: one column, and the panel becomes a bottom sheet.
- No horizontal scrolling at 390, 1100 or 1440px.

---

## 6. Build order and figures to check

**Build order.** Test each stage in a headless browser and treat any page error as a failure.
1. **The data** (appendix) **and the portfolio math.** Today's return and risk (whole household) must match:

   | Household | Return | Risk |
   |---|---|---|
   | Henderson | 5.64% | 9.24% |
   | Kaplan | 5.86% | 10.45% |
   | Castellano | 6.29% | 11.09% |
   | Okonkwo | 5.23% | 6.54% |
   | Brennan | 6.60% | 15.31% |

   Selling $1M of Henderson's NVDA realises a gain of $801,887 and tax of $190,849.
2. **Cash, routing, buckets, eligibility, value, the opportunity list:** match the table below.
3. **The landing page, the household flow and the task panel.**
4. **The proposal and the analysis views.**
5. **The tour and the checks:** 30 of 30 pass.
6. **Polish:** the name scan is clean, dark mode is legible, and there is no horizontal scroll.

**Figures to check (default settings):**

| | Henderson | Kaplan | Castellano | Okonkwo | Brennan | Delgado |
|---|---|---|---|---|---|---|
| Eligibility | with conditions (NVDA 22.9%) | with conditions (AAPL 28.9%) | with conditions (manager sleeve) | eligible | with conditions (NVDA 32.2%) | not eligible (COST 58.3%) |
| Brokerage | $49.70M | $8.70M | $2.60M | $28.40M | $840K | $1.65M |
| Investable cash after target and reserve | $3.07M | $84,500 | 0 | $11.42M | 0 | 0 |
| Movable now / held back | $47.20M / $2.50M | $8.15M / $550K | $2.15M / $450K | $26.90M / $1.50M | $811K / $29K | excluded |
| Year-one alignment (phased) | ≈70% | ≈73% | 100% | 100% | ≈40% | — |
| Year-one tax: phased vs at once | ≈$0 vs ≈$2.21M | ≈$0 vs ≈$381K | none | none | $4,284 vs ≈$70K | — |
| Expected return now → target | 5.64% → 6.15% | 5.86% → 6.15% | 6.13% → 6.15% | 4.74% → 6.55% | 6.38% → 6.81% | 6.07% → 6.55% |
| Value story: net a year | +$66,801 | −$26,008 (57% covered) | −$16,194 (stay) | +$396,280 | −$213 | blocked |
| Starting route | managed | managed | rebalance | phased | managed | specialist ($1,650 a year today) |
| Constraint (owner) | $400K without cost basis (Operations) | insider rules (Compliance) | manager sleeve (Manager) | suitability (Advisor) | insider rules (Compliance) | above 50% (Specialist) |

**Book-level figures:**
- Ranking: Henderson, Okonkwo, Kaplan, Castellano, Brennan, Delgado.
- 27 opportunities: 25 needing action, 1 specialist, 1 monitor.
- Henderson's program fee on $47.2M: $260,500.
- The management view: about 9 bp → 60 bp on $85.21M addressable.

---

## 7. Traps to avoid

1. **Never count a dollar twice.** Bonds held to call or maturity are kept, with a timing note. Lots without basis are held, not moving.
2. **Never invest the whole cash balance in steps.** Use the investable figure only.
3. **Two fee bases are intentional.**
   - The value story uses the whole brokerage amount: Henderson $298K vs $55K.
   - Routes use the amount movable now: $284K vs $52K.
4. **Don't call a route "recommended".** It is a "starting point for advisor review", and choosing it is a working choice.
5. **Specialist-route cost uses the full brokerage amount** ($1,650 for Delgado), not the movable amount, which is zero.
6. **Merge events into existing items** as described in 3.10. Otherwise the list grows past 27.
7. **Make screen functions reassignable,** if you use override layers.
8. **Re-query elements after every click in tests;** the page re-renders. Section labels are uppercase by CSS, so compare text case-insensitively.
9. **The tour must restore the advisor's view and never record anything.**

---

## Appendix: data

**Dates:**
- Positions as of 2026-10-15; research 2026-10-15; fund look-through 2026-09-30; returns 2026-09-30; CIO views updated 2026-10-01; intelligence catalogue 2026-10-23.
- "Today" is 2026-10-24.

**Tax rates (all households):** taxable; long-term 23.8%; short-term 40.8%; federal bracket 37%.

**A. Asset classes.** Expected return and volatility, then the correlations in the order LCG, LCV, SMID, INTL, EM, UST, IGC, HY, CASH, HF, PE. Risk-free rate 3.3%.

| Class | Label | Return | Vol | Correlations |
|---|---|---|---|---|
| LCG | U.S. Large Cap Growth | 6.6% | 17.5% | 1, .833, .820, .741, .675, −.188, .162, .526, −.005, .565, .656 |
| LCV | U.S. Large Cap Value | 7.0% | 15.5% | .833, 1, .807, .730, .668, −.140, .215, .555, 0, .570, .650 |
| SMID | U.S. Small/Mid Cap | 7.6% | 20.5% | .820, .807, 1, .719, .666, −.187, .189, .564, −.005, .571, .648 |
| INTL | International Developed Equity | 7.4% | 17.0% | .741, .730, .719, 1, .596, −.125, .195, .500, 0, .510, .580 |
| EM | Emerging Markets Equity | 8.2% | 22.0% | .675, .668, .666, .596, 1, −.166, .174, .506, −.005, .489, .546 |
| UST | U.S. Treasuries | 4.1% | 5.5% | −.188, −.140, −.187, −.125, −.166, 1, .713, .077, .095, −.058, −.163 |
| IGC | U.S. Corporates (IG) | 4.9% | 7.0% | .162, .215, .189, .195, .174, .713, 1, .480, .080, .265, .170 |
| HY | U.S. High Yield | 6.1% | 9.5% | .526, .555, .564, .500, .506, .077, .480, 1, .020, .520, .495 |
| CASH | Cash | 3.3% | 0.6% | −.005, 0, −.005, 0, −.005, .095, .080, .020, 1, .005, −.005 |
| HF | Hedge Funds | 5.8% | 7.5% | .565, .570, .571, .510, .489, −.058, .265, .520, .005, 1, .477 |
| PE | Private Equity | 9.6% | 23.0% | .656, .650, .648, .580, .546, −.163, .170, .495, −.005, .477, 1 |

**Past events:**
- Technology bubble (2000–02);
- Housing and financial crisis (2007–09);
- COVID disruption (2020);
- 2022 rate shock.

**Sectors:** TECH Information Technology, COMM Communication Services, DISC Consumer Discretionary, FIN Financials, HLTH Health Care, INDU Industrials, STAP Consumer Staples, ENER Energy, UTIL Utilities, REAL Real Estate, MATL Materials.

**B. Funds** (cost in bp, yield, research view, past-event returns in the order tech / crisis / covid / 2022):

| Fund | Name | Classes | Cost | Yield | View | Past events |
|---|---|---|---|---|---|---|
| VTI | US Total Market ETF | LCG 45, LCV 45, SMID 10 | 3 | 1.2% | Recommended | −.473 / −.551 / −.340 / −.182 |
| ITOT | Core S&P Total US Stock ETF | as VTI | 3 | 1.2% | Recommended | as VTI |
| IDX-I | S&P 500 Index Fund, institutional class | LCG 50, LCV 50 | 4 | 1.2% | Recommended | as VTI |
| LCG-A | Large-Cap Growth Fund, Class A (front-end load) | LCG 100 | 95 | 0.1% | Neutral | −.599 / −.539 / −.319 / −.268 |
| BAL-C | Balanced Income Fund, Class C (12b-1 fee) | LCG 30, LCV 30, UST 12, IGC 16, HY 12 | 170 | 2.5% | Not recommended | −.219 / −.355 / −.237 / −.163 |
| LCV-I | US Large Cap Value Fund (Institutional shares) | LCV 100 | 55 | 2.0% | Recommended | −.299 / −.561 / −.370 / −.054 |
| VXUS | Total International Stock ETF | INTL 75, EM 25 | 5 | 2.9% | Recommended | −.472 / −.610 / −.325 / −.155 |
| IEFA | Core MSCI EAFE ETF | INTL 100 | 7 | 3.0% | Recommended | −.480 / −.610 / −.330 / −.140 |
| AGG | US Aggregate Bond ETF | UST 60, IGC 40 | 3 | 4.1% | Recommended | .276 / .072 / −.006 / −.138 |
| BND | US Bond Market ETF | UST 60, IGC 40 | 3 | 4.1% | Recommended | as AGG |
| MUB | National Muni Bond ETF (muni) | IGC 100 | 5 | 3.1% | Recommended | .220 / .010 / −.090 / −.085 |
| VTV | Value ETF | LCV 100 | 4 | 2.3% | Recommended | −.30 / −.56 / −.37 / −.05 |
| VUG | Growth ETF | LCG 100 | 4 | 0.5% | Recommended | −.60 / −.54 / −.32 / −.27 |
| IJH | Core S&P Mid-Cap ETF | SMID 100 | 5 | 1.4% | Recommended | −.29 / −.59 / −.38 / −.12 |
| VEA | Developed Markets ETF | INTL 100 | 3 | 3.0% | Recommended | as IEFA |
| VWO | Emerging Markets ETF | EM 100 | 7 | 3.0% | Recommended | −.45 / −.61 / −.31 / −.20 |
| VGSH | Short-Term Treasury ETF | UST 100 | 4 | 3.9% | Recommended | .30 / .14 / .05 / −.12 |

The full-trim simulation buys the "Recommended" single-class funds: VUG, VTV, IJH, VEA, VWO, VGSH and MUB.

**Fund look-through.** Weights inside each fund.
- **VTI and ITOT:**
  - names: NVDA .064, MSFT .057, AAPL .056, AMZN .034, GOOG .033, META .025, AVGO .021, TSLA .018, JPM .013, COST .009, UNH .007, JNJ .007, PG .007, HD .007;
  - sectors: TECH .33, FIN .13, DISC .105, COMM .10, HLTH .09, INDU .085, STAP .05, ENER .03, UTIL .025, REAL .02, MATL .02.
- **IDX-I:** names NVDA .075, MSFT .067, AAPL .066, AMZN .040, GOOG .039, META .029, AVGO .025, TSLA .021, JPM .015, COST .010, UNH .008, JNJ .008, PG .008, HD .008; same sectors.
- **BAL-C:** the IDX-I names at 0.6 of those weights; same sectors.
- **LCG-A:**
  - names: MSFT .09, NVDA .08, AAPL .07, AMZN .06, GOOG .05, META .04;
  - sectors: TECH .50, DISC .17, COMM .13, HLTH .06, INDU .05, FIN .05, STAP .02, MATL .01, REAL .01.
- **LCV-I:**
  - names: JPM .035, JNJ .022, PG .02, HD .02, CVX .016, UNH .015, KO .013, PFE .01, CVS .006, INTC .006;
  - sectors: FIN .23, HLTH .16, INDU .14, TECH .10, STAP .09, ENER .08, UTIL .05, DISC .05, COMM .04, MATL .04, REAL .02.
- **VXUS and IEFA:** sectors only (FIN .22, INDU .17, TECH .11, DISC .10, HLTH .09, STAP .07, MATL .07, COMM .05, ENER .05, UTIL .03, REAL .03); no names, and no country-by-sector data.
- **Bond funds and cash:** none.

**Stocks:**
- Growth names (class LCG): NVDA, MSFT, AAPL, AMZN, GOOG, TSLA, COST, BKNG.
- Others are LCV.
- Sectors: TECH for NVDA, MSFT, AAPL, INTC, TXN, QCOM and ADI; FIN for JPM; HLTH for PFE, CVS, JNJ, UNH, MRK, ABBV, CI and ELV; ENER for CVX; STAP for COST, PG and KO; DISC for AMZN, TSLA, HD, BKNG and LOW; COMM for GOOG.

Past-event returns:

| Stock | Tech | Crisis | Covid | 2022 |
|---|---|---|---|---|
| NVDA, MSFT, AAPL | −.80 | −.53 | −.30 | −.28 |
| COST | +.05 | −.30 | −.24 | −.006 |
| JPM | −.20 | −.80 | −.43 | −.105 |
| PFE, CVS | −.25 | −.38 | −.28 | −.02 |
| CVX | −.25 | −.53 | −.57 | +.66 |

**C. Households.** The band is the volatility range for the profile. The model is the strategic target.

| Household | Profile | Band | Value | Gain budget | Age | Liquidity reserve | Meeting |
|---|---|---|---|---|---|---|---|
| Henderson Family Trust | Moderate | 8.26–10.35% | $49.70M | $994K | 72 | $1.0M | 2 days, Annual review: "Wants to revisit single-stock exposure and 2026 gifting." |
| Kaplan Household | Moderate | 8.26–10.35% | $8.70M | $174K | 63 | $400K | 1 day, Retirement planning: "Retiring in 18 months: income plan and a concentrated stock wind-down." |
| Castellano Family | Moderate | 8.26–10.35% | $3.20M | $64K | 58 | $60K | 5 days, Tax strategy review: "wants to understand how each sleeve is managed for taxes." |
| Okonkwo Holdings LLC | Moderately Aggressive | 10.35–12.53% | $31.60M | $632K | 51 | $1.5M | 6 days, Liquidity deployment: "$14M of business-sale proceeds landed; needs a deployment plan." |
| Brennan Household | Aggressive | 12.47–14.70% | $900K | $18K | 34 | $40K | 6 days, Advisory proposal: "Asked whether moving to an advisory account means selling everything." |
| Delgado Household | Moderately Aggressive | 10.35–12.53% | $1.65M | $33K | 64 | $80K | 9 days, Retirement planning: "most of the account is company stock." |

**Profile models** (strategic targets, %):

| Profile | LCG | LCV | SMID | INTL | EM | UST | IGC | HY | CASH | HF | PE |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Moderate | 14.5 | 14.5 | 6 | 10 | 3 | 13.5 | 15.5 | 6 | 7 | 5 | 5 |
| Moderately Aggressive | 19.5 | 18.5 | 8 | 13 | 4 | 7.5 | 9.5 | 5 | 5 | 5 | 5 |
| Aggressive | 27 | 25 | 10 | 16 | 5 | 1.5 | 3.5 | 4 | 3 | 5 | 0 |

**Holdings.** Value; then tax lots as cost (term). LT = long-term, ST = short-term. "No basis" means the cost is missing. Cash and money market are cash. Individual bonds, private assets and manager-run stocks are not transferable.
- **Henderson:**
  - NVDA $10.60M, cost $2.10M (LT);
  - MSFT $4.90M, cost $2.40M;
  - VTI $6.20M, cost $5.10M;
  - MUB $9.80M, cost $10.40M;
  - AGG $5.10M, cost $5.60M;
  - VXUS $4.30M, cost $4.90M;
  - cash $7.30M;
  - AUSTIN-4.0-32, City of Austin GO 4.0% 2032: individual muni bond, $1.10M, cost $1.08M, matures 2032-07-01;
  - a second NVDA position, $400K, no basis.
- **Kaplan:**
  - AAPL $2.40M, cost $600K;
  - VTI $2.10M, cost $1.70M;
  - VXUS $1.10M, cost $1.20M;
  - BND $1.90M, cost $2.00M;
  - cash $1.20M.
- **Castellano:**
  - ITOT $900K, in two lots: cost $500K on $600K (LT) and $290K on $300K (ST);
  - IEFA $520K, in two lots: $360K on $320K and $206K on $200K;
  - LCV-I $250K, cost $236K;
  - NYSDA-5.0-34, NY State Dormitory Authority 5.0% 2034: individual muni bond, $450K, cost $462K, matures 2034-03-15, callable 2026-12-15;
  - AGG $320K, cost $333K;
  - cash $160K;
  - run by Crestline Large Cap Value SMA (not the advisor's to trade):
    - JPM $260K, in four lots: $64K on $104K, $70K on $65K, $48K on $52K, and $38K on $39K (ST);
    - PFE $120K, in two lots: $93K on $75K and $46K on $45K (ST);
    - CVX $140K, cost $128K;
    - CVS $80K, cost $99K.
- **Okonkwo:**
  - cash $14.20M;
  - VTI $6.40M, cost $5.90M;
  - IEFA $3.10M, cost $3.00M;
  - AGG $4.70M, cost $4.80M;
  - PRIV, Private RE Interest: private equity class, $3.20M, cost $3.00M, "no redemption right".
- **Brennan:**
  - LCG-A $180K, cost $140K (A shares);
  - BAL-C $90K, cost $85K (C shares);
  - IDX-I $150K, cost $110K;
  - NVDA $260K, cost $45K;
  - AAPL $110K, cost $70K;
  - PRIV-SERIESB, a restricted private placement: private equity class, $60K, cost $25K;
  - government money market fund $30K (cash, 15 bp);
  - cash $20K.
- **Delgado:**
  - COST $960K, in two lots: cost $90K on $760K and $60K on $200K;
  - VTI $320K, cost $250K;
  - AGG $230K, cost $240K;
  - cash $140K.

LCV-I is I shares.

**D. Concentration flags and cash needs:**
- Alert threshold 10%; earlier material used 20%; program gate 50%.
- Henderson NVDA: intends to gift shares to the grandchildren's trust in 2026.
- Kaplan AAPL: insider, with pre-clearance and quarterly windows; a pre-arranged sale plan allows sales through closed windows.
- Brennan NVDA: insider; shares vest quarterly; trades only in open windows; saving for a home in 2027.
- Delgado COST: insider; pre-clearance and quarterly windows.
- Cash needs:

  | Household | Cash needs |
  |---|---|
  | Kaplan | 2027 $150K; 2028–2030 $300K each |
  | Brennan | 2027 $120K |
  | Delgado | 2027 and 2028 $80K each |

**E. CIO.**
- Tactical tilts, in points:

  | Class | LCG | LCV | SMID | INTL | UST | IGC | HY | CASH |
  |---|---|---|---|---|---|---|---|---|
  | Tilt | −2 | +1.5 | +0.5 | +1.5 | −1 | +0.5 | −0.5 | −0.5 |

- Tolerance: 3 points per class, 5 per group.
- Views:

  | Area | View | Was | Date |
  |---|---|---|---|
  | Large-cap growth | Underweight | Neutral | 20 Oct |
  | Large-cap value | Overweight | Neutral | 20 Oct |
  | International | Overweight | Neutral | 20 Oct |
  | Small/mid | Slight overweight | Neutral | 1 Oct |
  | Treasuries | Underweight | Underweight | 1 Oct |
  | High yield | Slight underweight | Neutral | 1 Oct |
  | Technology | Neutral | Overweight | 20 Oct |
  | Health care | Overweight | Overweight | 1 Oct |
  | Energy | Underweight | Neutral | 14 Oct |
  | Financials | Overweight | Neutral | 20 Oct |

  Give each view a one-line reason.

**F. Returns.**
- Class benchmarks, 1-year / 3-year:

  | Class | 1-year | 3-year |
  |---|---|---|
  | LCG | 24% | 18% |
  | LCV | 14% | 11% |
  | SMID | 10% | 7% |
  | INTL | 16% | 9% |
  | EM | 12% | 5% |
  | UST | 4.2% | 1.5% |
  | IGC | 5.5% | 2.8% |
  | HY | 8% | 6% |
  | CASH | 4.6% | 4.3% |
  | HF | 7% | 5% |
  | PE | 11% | 9% |

- A fund's return is its class benchmark + its excess − its cost. Excess, 1-year / 3-year (others 0):

  | Fund | 1-year | 3-year |
  |---|---|---|
  | LCG-A | −3.5 | −3 |
  | BAL-C | −2.5 | −2.2 |
  | LCV-I | +0.4 | +0.3 |

- Stocks, 1-year / 3-year (others 8% / 8%):

  | Stock | 1-year | 3-year |
  |---|---|---|
  | NVDA | 38% | 72% |
  | MSFT | 12% | 21% |
  | AAPL | 9% | 17% |
  | COST | 15% | 24% |
  | JPM | 28% | 22% |
  | PFE | −12% | −14% |
  | CVX | 3% | 5% |
  | CVS | −18% | −15% |

- Bonds: Austin 3.2% / 1.4%; NYSDA 3.4% / 1.6%.
- Private: PRIV 6% / 8%; PRIV-SERIESB 0% / 15%.
- Cash and money market: 4.6% / 4.3%.

**G. Fees and thresholds:**
- Fees as in 3.1, plus:
  - SMA manager fee 30 bp;
  - direct indexing 20 bp;
  - model funds 5 bp;
  - commissions 0.75% on 12% turnover;
  - trading cost 5 bp.
- Screen thresholds:
  - high cost 50 bp;
  - excess cash 5% of brokerage;
  - gains $5K;
  - losses $25K;
  - call window 90 days;
  - commissions at half the program fee.

**H. Strategies** (minimum, fee, classes covered):

| Strategy | Minimum | Fee | Covers | Notes |
|---|---|---|---|---|
| CIO Model Portfolio (ETF) | $50K | 5 bp | all except HF and PE | |
| Core Equity Direct Indexing | $250K | 20 bp | LCG, LCV, SMID | tax-managed; can exclude a stock |
| Tax-Managed Large Cap SMA | $250K | 30 bp | LCG, LCV | tax-managed |
| Large Cap Value SMA | $100K | 35 bp | LCV | |
| International Equity SMA | $250K | 35 bp | INTL, EM | |
| Municipal Ladder SMA | $250K | 20 bp | IGC, UST | tax-managed |
| Dividend Income Model | $50K | 8 bp | LCV, IGC | |
| Alternative Investments Platform | $250K | 100 bp | HF, PE | |

**I. Events:**

| Date | Type | Event | Moves / view | Route |
|---|---|---|---|---|
| 22 Oct | market | Tighter export rules for advanced AI chips | NVDA −6%, AVGO −4%, QCOM −3% | position |
| 20 Oct | CIO | CIO moves US large-cap growth to underweight, international to overweight | LCG against, LCV and INTL for | allocation |
| 16 Oct | market | Treasury yields jump after strong jobs report | UST −1.2%, IGC −1.5%, HY −0.8% | proposal |
| 14 Oct | market | Oil falls 7% on supply outlook | CVX −5%; energy sector −4% | allocation |
| 9 Oct | research | Research cuts CVS to Neutral | CVS −4%; held by Castellano through the manager sleeve | allocation |
| 29 Sep | research | Research cuts PFE to Neutral after trial misses | PFE −7%; held by Castellano through the manager sleeve | allocation |
| 21 Oct | market | Large-cap tech rallies on strong cloud earnings | MSFT +4%, AAPL +3%; tech sector +1.5% | position |
| 19 Oct | client | Kaplan asks whether to sell AAPL before retiring | — | position |
| 24 Sep | research | Research cuts TSLA to Underperform | TSLA −5%; held only through funds | — |

Give each event a two-sentence summary, a house-view line and a to-do.

**Firm intelligence extras:**

| Item | Rule | Client use |
|---|---|---|
| Research upgrades JPM to Buy | held directly | approved |
| CIO moves high yield to overweight | a view, HY for | approved |
| European banks upgraded to Overweight | needs country-by-sector data; not available | internal |
| Yen jumps 3% | INTL +0.6% | third-party news |
| CIO keeps energy at neutral | superseded by the 14 Oct move | — |

**J. Approved content and objections.**
- Twelve fictional approved materials. Each has a title, kind, topics, audience (client or advisor), approval date and expiry date. Two are advisor-only: the large single-stock guide and the fee talking guide.
- Six objections, each with an approved answer:
  - "Why pay an ongoing fee when I rarely trade?"
  - "Do I have to sell everything to move?"
  - "My portfolio has done well. Why change it?" (offered only when risk falls from above the band)
  - "I don't want to give up my company stock."
  - "Is now a bad time to invest my cash?"
  - "Isn't a cheaper index-only option enough?"

  Each answer must be honest, and where true it must say that a commission account or the index-only option can cost less.
