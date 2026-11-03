# Atlas console: Ask Atlas, Book view and the opportunity workflow

**File:** `atlas-console-book-view.html`. It opens from disk with no server. Fonts load from the web when they can, and fall back to system fonts when offline.

**What this is:** a new standalone version of the Atlas advisor console, built around one path through it:
1. **Ask Atlas** is the starting point.
2. **Book view** finds the clients that meet a condition.
3. The **Client dashboard** lists every household.
4. The **client deep dive** summarizes one household and shows its opportunities.
5. A **three-step workflow** turns an opportunity into a proposal.
6. Ask Atlas stays available throughout, and a **guided tour** covers all of it.

**Changes from the original console:**

| Area | Change |
|---|---|
| Landing | Ask Atlas, with a minimal chat window and two prompt bubbles |
| Book of Business | Renamed **Client dashboard** |
| Book view | New. A heat map of 12 criteria; selecting one lists the clients that meet it |
| Client deep dive | Rebuilt around **Portfolio at a glance**, the summary from Portfolio Review |
| Opportunities | New. A heat map of actions sized for one household |
| Workflow | New. What led here → Solutions → Proposal, with Ask Atlas docked beside it |
| Tour | New. 20 steps, from the top bar or the Ask Atlas page |

**Not in this file:** the other screens of the original console (Today, Tax Overlay Desk, Cross-Sell Radar, Transition, Draft review). They can be brought back in.

**What was checked:**

| Check | Result |
|---|---|
| Book view counts and dollar totals, for all 12 criteria and both advisors | Match a separate Python calculation exactly |
| Opportunities in the deep dive, all 36 households | 151 opportunities; the tile count matches the Book view checks for every household |
| Workflow options | All 476 options render all three steps |
| Trade engine | Household assets unchanged by every option (largest difference under $0.01), except gifts, which leave the household on purpose; no negative positions or cash |
| Ask Atlas in the workflow | 1,359 test questions; every one got a specific answer |
| Portfolio at a glance | 504 combinations of view and show: no errors and no blank figures |
| Guided tour | All 20 steps find their target, on desktop and on a phone |
| Display | No page errors in light, dark or phone layout; no sideways scrolling at 390 px on any screen |
| Names | Name scan clean |

**All households, people, prices, ratings and the CIO house view are made up.** The 17 households from the original console are kept. I added 19 more, so Dana Whitfield's book has 24 households and Marcus Chen's has 12. I also added sector data, research rating changes, and individual bonds and CDs with maturity dates.

---

## 1. Ask Atlas: the starting point

The console opens on a minimal chat window. The two bubbles under it, **Take me to Book view** and **Take me to Client dashboard**, open those screens.

![Ask Atlas](images/01-ask.jpg)

**What you can type:**
- **A criterion:** "who has bonds maturing over $500K in the next 6 months", "downgraded holdings", "excess cash", "meetings this week". Atlas answers with the count, the total and the top clients, plus a button that opens the matching list in Book view. Amounts and time windows in the question are applied to the list.
- **A client's name:** "open Henderson". Atlas gives a one-line summary and a button to open the client.
- **Anything else:** Atlas suggests what it can do.

In this prototype the answers come from rules over the sample book, not a language model, and the page says so.

![Ask Atlas answering](images/02-ask-chat.jpg)

## 2. Book view: criteria across the whole book

**What's on the screen:**
- **The cards:** each card is one criterion checked across the advisor's book. The big number is how many clients meet it, and the line under it is the dollars involved.
- **The heat:** the cards are white, with a thin colored left edge for the heat. A darker edge means a larger share of the book is affected (1–15% up to 60% and over).
- **Selecting a card** lists the clients that meet it. The columns change with the criterion.

![Book view](images/03-book.jpg)

**Bonds & CDs maturing** has two extra controls:
- **Minimum:** $100K, $250K, $500K or $1M.
- **Window:** 6, 12 or 24 months.

Changing either updates both the list and the card. With the default ($250K over 12 months), Dana has 10 households and $15.4M maturing.

![Bonds and CDs maturing](images/04-book-maturing.jpg)

**Downgraded holdings** lists each security with its old and new rating and the date of the change.

![Downgraded holdings](images/05-book-downgrades.jpg)

**The 12 criteria** (Dana's book, 24 households):

| Criterion | Rule | Clients | Amount |
|---|---|---:|---:|
| Downgraded holdings | Holds a security downgraded in the last 90 days (stock rating, fund status or credit rating) | 12 | $13.7M held |
| Bonds & CDs maturing | Individual bonds and CDs maturing in the window add up to at least the minimum | 10 | $15.4M |
| Single-stock concentration | One stock over 10% of the household (lots combined) | 6 | $18.5M |
| Excess cash | Cash more than 5 pts above target and at least $250K over | 7 | $22.9M |
| Allocation drift | An asset group more than 5 pts from target | 13 | $30.1M to rebalance |
| Behind benchmark YTD | More than 1.5 pts behind the benchmark for the risk profile | 10 | $151.7M AUM |
| Tax-loss harvesting | Unrealized losses of at least $250K | 9 | $7.5M |
| Large embedded gains | Unrealized gains over 20% of the household | 5 | $19.2M |
| Missing cost basis | A position with no cost basis on file | 3 | $1.1M |
| Meetings in 14 days | A meeting in the next 14 days | 14 | $283.5M AUM |
| Off the CIO house view | CIO alignment score High | 4 | $126.0M AUM |
| Program opportunities | Eligible for 5 or more programs not yet in use | 11 | $177.4M AUM |

## 3. Client dashboard (formerly Book of Business)

**What it shows:** every household in the book.
- **Columns:** assets, YTD return against the benchmark, unrealized gain or loss, cash, next meeting, and the number of Book view flags with the first two named.
- **Controls:** sort on any column, search by household or contact, and filter by segment.
- **Selecting a row** opens the deep dive.

![Client dashboard](images/06-dashboard.jpg)

## 4. Client deep dive: Portfolio at a glance

**The order on the page:** the client header, then Portfolio at a glance, then the household's opportunities. Portfolio at a glance follows the Portfolio Review step of the same name.

**The top of Portfolio at a glance:**
- **AI-drafted summary:** the mix, expected risk against the profile's band, tracking error to target, the largest name, the YTD result, the open opportunities and the next meeting. For Henderson: expected risk 8.7%, inside the 8–12% band; tracking error 2.2%; NVDA 22.1%.
- **Key figures:** YTD return against the benchmark, unrealized gain or loss, cash against target, largest position, estimated income and largest drift.
- **CIO view for this client:** the client's alignment score and the house view's overweights and underweights.

![Client header and summary](images/07-client-top.jpg)

**View by** has three options:
- **Asset classes:** a sunburst, with asset groups (L1) on the inner ring and asset classes (L2) on the outer ring. Next to it is a table of weight, target, gap and the CIO stance (▲ Overweight, ● Neutral, ▼ Underweight) for every group and class.
- **Sectors:** equity bars against the equity benchmark, with funds counted by the sectors they hold.
- **Holdings:** a treemap of all positions with the full holdings table.

![Sunburst and table](images/08-glance-sunburst.jpg)

**Drilling down:**
- Selecting a group shows its classes.
- Selecting a class shows its holdings, with unrealized gain, research rating (downgrades marked ↓), yield and maturity.
- The breadcrumb line takes you back up.

![A group: fixed income](images/09-glance-group.jpg)

![A class: US large cap holdings](images/10-glance-class-holdings.jpg)

![Sectors against the benchmark](images/11-glance-sectors.jpg)

**Show** switches between three versions of the portfolio:
- **Today.**
- **Target:** the target mix, available in the asset-class view.
- **Proposal:** once you choose a solution in an opportunity workflow, the whole glance shows the portfolio after the change, with today alongside (section 6.5).

![Target](images/12-glance-target.jpg)

## 5. Opportunities for this household

The opportunities use the same checks as Book view, but the tiles mean something different:

| | Book view | Household opportunities |
|---|---|---|
| A tile is | A filter across the book | One opportunity for this client |
| Title | The criterion, e.g. "Single-stock concentration" | An action, e.g. "Reduce single-stock concentration" |
| Big number | How many clients | This client's dollars ($6.0M above 10%) or timing ("In 2 days") |
| Edge color | Share of the book affected | Impact on this household (dollars as a % of its assets; urgency for meetings and the performance gap) |
| Order | Fixed | Largest impact first |
| Selecting it | Lists clients | Starts the three-step workflow |

**Henderson** has 11 opportunities. The largest are $12.0M of embedded gains, $6.0M of NVDA above 10%, $5.9M to rebalance and a meeting in 2 days. A line under the tiles lists the checks that found nothing to do.

![Opportunities for Henderson](images/13-opps.jpg)

## 6. The opportunity workflow

**The steps:** 1 What led here · 2 Solutions · 3 Proposal. The Proposal step unlocks once a solution is chosen.

**Ask Atlas** is docked on the right. On a phone or narrow screen it opens from an "Ask Atlas" button.

### 6.1 Step 1: what led here

**What's on the screen:**
- **AI-drafted recap:** built from the household's own figures, with the purple label. For Henderson's concentration: how NVDA grew from a cost of $2.1M to $11.0M and 22.1% of the household, the $6.0M above the guideline, the meeting in 2 days and the CIO view.
- **The facts and the rule** that flagged it.
- **Links:** to the holdings involved, and to the other clients in the book with the same opportunity.

![Step 1](images/14-wf-recap.jpg)

### 6.2 Step 2: solutions

Each opportunity offers 3–4 options built from the household's figures. Each card shows the estimated tax, the change in income and the drift after the change, with badges for **Lowest tax**, **Most income** and **Closest to target**.

![Options](images/15-wf-options.jpg)

**Henderson, reduce single-stock concentration:**

| Option | Est. tax | Income change | Largest drift after | NVDA after | Badges |
|---|---:|---:|---:|---:|---|
| Trim to 10% and diversify | $1.1M | +$154K | 9.7 pts | 10.0% | Most income, Closest to target |
| Phase the trim over 3 years (year one) | $370K | +$51K | 9.7 pts | 18.1% | Closest to target |
| Gift low-basis shares | $0 | −$724 | 10.4 pts | 18.2% | Lowest tax |
| Protect with a collar | $0 | $0 | 10.0 pts | 22.1% | Lowest tax |

**Selecting an option** highlights it and dims the others ("Show all options" brings them back). Below the cards, the selected option shows:
- **Trades:** sells (with the gain realized) and buys.
- **Impact on key metrics:** before, after and change for allocation, largest drift, largest stock, yield, income, estimated volatility, downgraded holdings, unrealized gain, gain realized now, estimated tax and household assets.

![Selected option](images/16-wf-selected.jpg)

![Impact on key metrics](images/17-wf-impact.jpg)

**Ask Atlas about the options.** Suggested questions change with the step:
- Step 1: "Why is this coming up now?", "What happens if we do nothing?"
- Step 2: "Compare the options", "Which option has the lowest tax?", "Which fits the CIO view best?"
- Step 3: "Summarize this for the client", "What are the risks of this proposal?"

You can also type a question about an option by name, tax, income, risk, a product ticker, or how many other clients have the same opportunity. Answers use the figures on the page.

![Ask Atlas in the workflow](images/18-wf-chat.jpg)

### 6.3 Add your own from the product shelf

**+ Add your own** opens the product shelf: 21 approved products, either ETFs or managed accounts, with class, yield, fee and research rating.
1. Pick up to 4 products and set an amount.
2. The funding comes from the opportunity itself. For Henderson it is "Sell $6.0M of NVDA"; for maturing bonds it is the proceeds; for excess cash it is the cash.
3. The choice becomes a **Your selection** card, with the same figures and impact as the other options.

![Product shelf](images/19-wf-shelf.jpg)

![Your selection as an option](images/20-wf-custom.jpg)

### 6.4 Step 3: the proposal

A report for advisor review, which you can print or save as a PDF. It has these sections:
- an AI-drafted summary;
- 1. why we are recommending this;
- 2. the proposed trades, with realized gains and estimated tax;
- 3. asset allocation (L1) before and after, as a chart and a table;
- 4. asset classes (L2) before and after;
- 5. holdings before and after, with changed rows highlighted;
- 6. key metrics;
- disclosures.

**Henderson, trim to 10% and diversify:** 10 trades realize $4.7M of gains (estimated tax $1.1M). NVDA goes from 22.1% to 10.0%, estimated income rises by $154K a year, and equity moves from 53.1% to 45.5%.

![Proposal: summary and trades](images/21-report-top.jpg)

![Proposal: allocation before and after](images/22-report-allocation.jpg)

![Proposal: holdings before and after](images/23-report-holdings.jpg)

### 6.5 The proposal back in the deep dive

The deep dive's **Show: Proposal** displays the whole Portfolio at a glance after the change, with today alongside and a link back to the report.

![Proposal at a glance](images/24-glance-proposal.jpg)

## 7. Guided tour

**Where to start it:** **▶ Tour** in the top bar, or "Take the 20-step tour" on the Ask Atlas page.

**How it works:**
- It highlights each part of the screen and moves between screens on its own.
- It walks Henderson's concentration opportunity through all three steps.
- Use Next or Back, the arrow keys, or Esc to close.
- On a phone, the explanation pins to the top or bottom of the screen so it doesn't cover the highlighted part.

| # | Step | # | Step |
|---|---|---|---|
| 1 | Welcome | 11 | Groups and classes in one picture |
| 2 | Ask Atlas is the starting point | 12 | Opportunities for this household |
| 3 | Two ways in | 13 | A three-step workflow |
| 4 | Book view: criteria as a heat map | 14 | Step 1: what led here |
| 5 | Select a card to see who meets it | 15 | Step 2: ways to address it |
| 6 | Each row is a client | 16 | See the impact before you choose |
| 7 | Client dashboard | 17 | Ask Atlas, alongside |
| 8 | Portfolio at a glance | 18 | Step 3: the proposal |
| 9 | Key figures | 19 | The proposal shows at a glance too |
| 10 | View by and show | 20 | End |

![Tour: welcome](images/25-tour-01.jpg)

![Tour: Book view](images/25-tour-04.jpg)

![Tour: groups and classes](images/25-tour-11.jpg)

![Tour: solutions](images/25-tour-15.jpg)

![Tour: Ask Atlas alongside](images/25-tour-17.jpg)

## 8. Dark mode and phone

**Dark mode:** it follows the system setting, and the moon button in the top bar switches it by hand. The heat edges have their own dark-mode colors.

![Dark: Book view](images/26-dark-book.jpg)

![Dark: Portfolio at a glance](images/27-dark-glance.jpg)

![Dark: workflow](images/28-dark-workflow.jpg)

**Phone (390 px):**
- The tabs become Ask, Book and Clients.
- Cards stack.
- Wide tables scroll inside their card, never the page.
- The workflow chat opens from a button.

![Phone: Ask Atlas](images/29-phone-ask.jpg) ![Phone: Book view](images/30-phone-book.jpg) ![Phone: Portfolio at a glance](images/31-phone-glance.jpg) ![Phone: workflow](images/32-phone-workflow.jpg) ![Phone: Ask Atlas in the workflow](images/33-phone-chat.jpg)

## 9. How the figures are calculated

**Holdings:** every figure comes from the household's holdings at security level.
- **Asset groups and classes:** each security has an asset group (L1) and an asset class (L2).
- **Sectors:** stocks have a sector, and funds are counted by the sectors they hold.
- **Lots:** lots of the same security are combined for display.

**Targets:**
- **Group targets (L1):** from the household's record.
- **Class targets (L2):** each group's target split by a fixed house model. For example, equity is 62% US large cap, 10% US small/mid cap, 20% international and 8% emerging markets.

**Book view and household opportunities** use the same rules (section 2). Opportunity heat by share of the household: ≤1%, ≤3%, ≤6%, ≤10%, over 10%. Some opportunities use a floor or a fixed level instead:

| Opportunity | Heat |
|---|---|
| Single-stock concentration | At least step 3 |
| Maturing within 60 days | At least step 4 |
| Meetings | By days away |
| Behind benchmark | By the size of the gap |
| CIO view and programs | Fixed level |
| Missing cost basis | At least step 2 |

**The trade engine:**
- **Sells** reduce each lot in proportion and realize gain on lots with a known basis. Lots without a basis are flagged.
- **Buys** are paid for by the proceeds and then by cash; household assets don't change.
- **Gifts** leave the household with no gain realized.
- **In-kind moves** (direct indexing) carry the cost basis across.

**"Fill the gaps" buys** spread the money across the asset classes below target, in proportion to each gap, using one representative product per class.

**Tax:** estimated at 23.8% of net realized gains. That is the long-term federal rate including the net investment income tax; state tax is excluded.

**Risk measures:** expected volatility and tracking error to target come from class-level volatility assumptions and a simple correlation by asset group. Expected return uses illustrative long-term assumptions per class. The worst past event replays 2008 and 2022 class returns on today's mix.

**CIO view:** an illustrative house view as of 15 Oct 2026, with a stance and a reason for every group and class.

## 10. Limits, and what production needs

**What is simulated in this prototype:**
- **AI-drafted text:** the recap, summaries and chat are built from rules over the page's figures. In production a language model would draft them, grounded on the same figures, and they would be checked before use (see the production architecture note).
- **Phased options** show the first year or first step only.
- **Gifts** don't show the charitable deduction.
- **The collar** has no pricing.
- **"Save as draft proposal"** only shows a confirmation.

**Data production needs:**
- holdings and tax lots from the systems of record;
- research ratings with their change dates;
- bond maturities;
- the approved product shelf;
- the CIO house view;
- capital-market assumptions;
- each client's targets and benchmark.

**Proposals:** they should be saved on the server with versions and an audit trail, and sent through the firm's review before anything reaches the client.
