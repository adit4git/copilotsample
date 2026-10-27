# Portfolio Review: rebuild brief (prototype v2)

**What this is.** A plain-language brief for a capable coding model (or a developer) to rebuild the Atlas Portfolio Review prototype as one self-contained HTML page.
- Everything is described in prose.
- The only tables are the data in the appendix and the figures to check against in section 6.
- No other file is needed.

**What to build.** One HTML file that opens from disk with no server.
- All styles and scripts are inline, and there are no outside requests.
- Fonts are named in the stylesheet but not loaded, so the page falls back to system fonts.
- Five illustrative households.
- Every figure is computed in the page from the appendix data.

**How to read it.**
- Sections 1–4 say what the tool does, how its rules work and what each screen shows.
- Section 5 covers the look. Section 6 gives the build order and the figures that prove the rebuild is right. Section 7 lists traps.
- Where exact wording matters, it appears in quotation marks. Elsewhere, write clear, plain advisor-facing text in the same spirit.
- Several rules contain small quirks: an order that matters, a rounding step, a value taken from the "wrong" place. Each is described as it is, because the check figures depend on them. Don't "fix" them.
- If this was copied by OCR, read for meaning. A number that looks garbled in a table (O.12, 1O%) is a slip; use the obvious value.

**Hard rules.**
1. **No real firm, bank, broker, vendor or fund-manager names** anywhere.
   - The product is "Atlas"; the page title is "Atlas · Portfolio Review prototype v2".
   - The house investment view is "the CIO".
   - Fund shelf entries are identified by ticker-style symbols and generic names, exactly as in the appendix.
   - The SMA and manager names in the data (Crestline, Beacon Hill, Ashcroft, Northbridge and the other briefing authors) are fictional.
2. **Use the appendix data as given,** in the order given. Several rules pick "the first fund that qualifies", so the order of the fund list changes results.
3. **Human-led and illustrative.**
   - The tool never sends or trades anything; proposals are prepared for client discussion.
   - The top bar always carries an "Illustrative" pill.
   - Every screen that shows tax, history or research carries the matching disclosure text from the appendix.
   - Acceptance is labelled "Client discussion only · prototype: not saved".
4. **Plain language, sentence case,** and no internal jargon on screen.

---

## 1. The product

Atlas Portfolio Review helps an advisor prepare for a client review meeting:
1. look at the portfolio as it is;
2. work through a set of review lenses, each of which can suggest a change;
3. collect the changes they want into one or more proposals;
4. see what each proposal does to risk, return, income, past-event losses, fund costs and tax;
5. check the proposal against policy;
6. take away editable talking points.

**Layout.** Three columns below a sticky top bar.

- **Top bar:**
  - a brand mark with "Portfolio Review" and, beneath it in small capitals, "Atlas · prototype v2";
  - a **Household** selector;
  - four facts: account value, "profile · model tier", next meeting, and "15 Oct 2026 · Positions as of";
  - the "Illustrative" pill;
  - a theme toggle.
- **Left, the journey:** ten steps in three groups, each with a status dot, the step name, a one-line verdict, and a count of the changes taken from that step.
- **Centre, the stage:** the selected step.
- **Right, the proposal panel:** proposal tabs, the name, eight KPI tiles, the "why it changes" explanation, the change list, a talking-points preview and the actions.

**The ten steps**, with the one-line description shown under each step's heading:

| Group | Step | Description |
|---|---|---|
| Explore | Portfolio at a glance | "Understand the current portfolio, its exposures and key analytics." |
| Review | Risk profile alignment | "Differences between the client risk profile and target allocation; align while controlling realized gains." |
| Review | Asset allocation gaps | "Fill underweight asset classes from available or incoming cash, or sales." |
| Review | Goal-based recommendations | "Consider changes tied to an objective, with historical limitations disclosed." |
| Review | Holdings and concentration | "Look through funds to assess individual companies, sectors and implementation costs." |
| Review | Portfolio deep dive | "Identify style, size and geographic gaps and review manager and fund research." |
| Review | Historical stress scenarios | "Illustrate how today's investments might have behaved in past events." |
| Review | Downgraded stock alternatives | "Review recently downgraded holdings and comparable alternatives." |
| Decide | Compare proposals | "Evaluate several potential portfolios side by side." |
| Decide | Client summary | "Choose and refine talking points for the client meeting." |

**The working loop.**
1. Each review step ends in a **preview card**: a suggested set of trade lines, with its effect on risk, return, income, tracking error and tax.
2. **Add to Proposal A** puts those lines into the proposal as one named change.
3. The KPI tiles, explanations and talking points update immediately.
4. Adding the same suggestion again (the same change key, section 3.11) replaces that change instead of duplicating it.
5. The advisor can edit any trade amount in the panel, remove a change, start or duplicate proposals, compare them, run the checks, and mark proposals "for client".

**Principles every screen follows:**
- Figures are illustrative estimates from the appendix data. Historical results are not a forecast.
- Every suggestion is a prompt for the advisor ("Atlas suggestion", "Atlas idea"), never a recommendation to the client.
- **A preview always measures its change against the other changes already in the proposal**, so the numbers on a preview are the marginal effect.
- Tax is estimated from tax lots with cost basis. Lots without basis are never sold, and the tool says so.
- The policy checks are a review for client discussion, not a trading approval.

---

## 2. How to build it

**One file.** Use a few script blocks inlined in order:
1. the data;
2. the portfolio engine;
3. the chart library;
4. helpers and suggestions;
5. state;
6. the screens;
7. event handling.

There is no framework. Build HTML from template strings and escape every piece of data text.

**Page skeleton:**
- an empty top bar;
- a three-column layout: journey (`nav`), stage (`main`) and proposal panel (`aside`);
- a scrim and a right-hand sheet for dialogs;
- a toast element;
- a floating tooltip element.

**Rendering.**
- One paint function redraws the top bar, the journey, the stage, the proposal panel and the sheet.
- If a screen throws, show "Unable to render this view" with the error message instead of a blank stage.
- Navigating to a step scrolls to the top. Other changes repaint in place.
- Sliders repaint about 140 ms after the last movement.

**Events.** A few delegated listeners on the document read `data-` attributes:
- clicks;
- input (sliders, editable talking points);
- change (selects, checkboxes, numbers, trade amounts, the proposal name);
- keydown: Escape closes the sheet, and Enter or Space activates drill rows and fund rows;
- mousemove, for tooltips on anything with a `data-tip` attribute.

**State.** All state lives in memory. The only thing that persists is the favourite funds, in local storage under "atlas.pr.favorites"; wrap every storage call so failures are ignored.

The state holds:
- the household and step;
- per household:
  - review settings for each step;
  - explore settings: view by, show, and the drill path;
  - the proposal set: a list, the active index and the next id;
- the selected holding card;
- which KPI the "why" box explains (default expected risk);
- which sheet is open, and the picker's state;
- the favourites (default VTV, IJH, IEFA, SCHD, AGG, MUB, VGSH);
- the mobile panel open flag;
- the exception reason typed in the check sheet.

**Proposals.**
- A proposal has an id, a name ("Proposal A" for id 1, "Proposal B" for id 2, and so on), a list of changes, optional edited talking points, and a "for client" flag.
- A change (a group) has a key, a label, the step it came from (its lens), its trade lines and some metadata.
- A trade line is a buy, a sell or a note. It has a symbol, an amount, and optionally stage 2 (paid from incoming cash) and the class it was bought for.
- Each household starts with one empty Proposal A.

**Startup.** Compute the suggestions for every household (section 3.6) once at load, then paint Henderson Family Trust on "Portfolio at a glance".

---

## 3. The rules, in plain language

Implement these faithfully. The figures in section 6 depend on them.

### 3.1 Number formats

- **Money:**
  - one million or more: dollars in millions with two decimals ("$49.70M"; one decimal where a chart centre asks for it: "$49.7M");
  - $10,000 to just under one million: thousands rounded with a separator ("$994K");
  - below $10,000: whole dollars with separators ("$5,077").
  - Negative money starts with a true minus sign (−).
- **Percent:** one decimal by default, using an ordinary hyphen for negatives ("-27.9%").
- **Point changes:** a sign, the absolute value in points to one decimal, and "pts", with a true minus sign ("+1.9 pts", "−10.0 pts").
- **Tax:** a negative tax (a saving) shows as "$4,500 saved"; otherwise as money.
- **Rounding of trade sizes:** every suggested trade amount is rounded to the nearest $1,000.

### 3.2 Portfolio math

**Asset classes and groups.**
- Eleven asset classes, each with an expected return, a volatility and a pairwise correlation (appendix A).
- They roll up into four groups: Equity (LCG, LCV, SMID, INTL, EM), Fixed income (UST, IGC, HY), Cash (CASH) and Alternatives (HF, PE).
- The risk-free rate is 3.3%.

**Weights.** For a list of holdings:
- every holding with at least one class contributes its value split by its class mix;
- class weights are those amounts divided by the value of all classified holdings;
- the account total is all holdings (every holding in the data is classified, so the two totals match).

**Expected return** is the weighted sum of class returns.

**Expected risk (volatility)** is the square root of w′Σw, where Σ is built from class volatilities and correlations. A class paired with itself has correlation 1; a missing pair has 0.

**Sharpe** is (return − 3.3%) ÷ risk.

**Tracking error** to an allocation uses the same formula applied to the difference in weights. Two versions are shown:
- versus the household's **target** on file;
- versus its **profile model**.

**Past events (stress).**
- Four events: Technology bubble, Housing and financial crisis, COVID disruption, 2022 rate shock.
- Each holding carries its own return for each event.
- A portfolio's event return is the value-weighted average of its holdings' event returns. A holding with no figure for an event counts as 0, which applies to cash created by a proposal.
- The **worst event** is the event with the lowest portfolio return, and ties keep the first in the order above.

**Contributors to an event** are each holding's value times its event return, summed by symbol.

**Income** is the sum of value × yield. Yield percent is income ÷ account total.

**Fund costs** are the value-weighted average of each holding's cost in basis points over the whole account. Cash, bonds and stocks count as 0.

**Single names, with look-through.**
- Every stock held directly counts in full.
- Every fund adds its value × each of its top-holding weights.
- Divide by the account total.
- The largest name is the top of this list.

**Sectors, as a share of equity.**
- For each holding, its equity share is its value × the sum of its weights in the five equity classes.
- That share is spread across sectors using either the stock's single sector or the fund's sector mix, normalised to sum to 1.
- The equity total counts every holding's equity share, even one with no sector data. Sector shares are divided by that total.

**U.S. style box.**
- For each holding, its U.S. equity amount is its value × (LCG + LCV + SMID weights).
- That amount is spread across its style-box cells (LV, LB, LG, MV, MB, MG, SV, SB, SG) in proportion to its cell weights.
- Holdings with no style data are skipped.
- Normalise the result so the cells sum to 1.

**Below investment grade** is the HY class weight.

**Look-through holdings by class (for drilling down).** For each class, each holding's value × its weight in that class, kept per symbol.

### 3.3 Tax lots and the sale rule

To sell an amount of a symbol:
1. Gather every lot of every **tradable** holding with that symbol, ignoring lots worth $0.50 or less.
2. A lot without cost basis is never sold; its value counts as "excluded".
3. Order the lots:
   - losses first, biggest loss first;
   - then long-term gains, smallest gain first;
   - then short-term gains, smallest gain first.

   The gain fraction is (value − basis) ÷ value.
4. Take whole or part lots in that order until the amount is met. The gain is in proportion to the part taken.
5. Tax is the gain × 23.8% for long-term lots and × 40.8% for short-term lots, because every household is taxable.

The result is the gain, the tax, the lots used, any amount that couldn't be filled, and the excluded value.

### 3.4 Applying a proposal

Applying a set of trade lines to a household's holdings returns new holdings and the totals.

1. **Sells first,** one line at a time. Each line runs the sale rule against the holdings as they stand after earlier lines.
   - Reduce the lots: a lot's basis falls in proportion to the part sold.
   - Reduce the holding's value.
   - Add the filled amount to proceeds, and add the gain and tax.
   - If a line couldn't be filled by more than $1, record "SYM: $X more than can be sold (held, or with cost basis)".
2. **Stage-1 buys** (every buy not marked stage 2) are paid first from sale proceeds, then from cash holdings in their listed order.
   - What remains unpaid is the **cash shortfall**.
   - Proceeds left over are added to the holding with symbol CASH. If there is none, create "Cash" (yield 4%, class Cash, no event returns).
3. **Every buy,** stage 1 and stage 2, is added as a new holding.
   - It copies the fund's (or stock's) record from the shelf with the bought amount as its value.
   - It has one short-term lot whose basis equals the amount.
   - An unknown symbol records "Unknown investment: SYM".
4. **Stage-2 buys** are paid by the household's incoming cash.
   - If stage-2 buys exist and the incoming cash is larger, the difference is added to CASH.
   - If there are no stage-2 buys, the incoming cash is **not** added at all.
   - The amount by which stage-2 buys exceed incoming cash is the **staged shortfall**.
5. Drop holdings worth $0.50 or less.

Also return:
- total sells, which feed turnover;
- total buys;
- amount sold by symbol.

### 3.5 Shelf funds: two different "which fund" rules

There are two rules for choosing a fund for a class. Keep them separate; both are used, and they differ for international equity.

- **Suggested fill fund** (used by the load-time suggestions: gaps, the cash plan, concentration reinvestment, the deep dive): the first fund in the shelf order whose research view is Recommended and whose weight in the class is at least 90%.
  - LCG gives VUG, LCV gives SCHD, SMID gives IJH, INTL gives **VEA**, EM gives VWO, UST gives VGSH, IGC gives MUB.
  - HY, Cash, hedge funds and private equity have no fund.
- **Working fund for a class** (used by risk alignment, the gap filler, the heat-map stars and buys the advisor adjusts):
  1. if the advisor picked a fund for that class in the fund picker, use it;
  2. otherwise, among funds with at least 90% in the class, the first that is a favourite and Recommended;
  3. otherwise the first Recommended;
  4. otherwise the first such fund.

  With the default favourites this gives the same answers except INTL, which gives **IEFA**.

### 3.6 Suggestions computed at load

For every household, compute the base metrics (section 3.2) and the following.

**Projected excess cash** is the value of the cash holdings minus the target cash weight × the account's classified total. It can be negative.

**Gaps.**
- A class is a gap when its target weight exceeds its current weight by at least one point.
- The gap's dollars are the shortfall × total.
- Sort gaps by dollars, largest first.
- Each gap carries its suggested fill fund, which can be none.

**Cash plan.**
1. Available cash = max(0, projected excess cash) + incoming cash.
2. Over the gaps that have a fund: total = the sum of their dollars; budget = the smaller of total and available.
3. "In hand" starts at max(0, projected excess cash).
4. For each such gap in order:
   - amount = the budget × this gap's share of total, rounded to $1,000; skip it below $1,000;
   - the part covered by cash in hand is a stage-1 buy, and in-hand cash goes down by that part;
   - the rest is a stage-2 buy, paid from incoming cash;
   - drop either part below $1,000.

**Funding sources** (offered when a gap is paid by selling). Every non-cash holding, with:
- whether it is tradable;
- its tax per $100,000 sold: the tax from the sale rule on min($100,000, value), shown per $100K;
- whether its main class is overweight, meaning more than one point above target.

**Holding and exposure items** (for "Holdings and concentration"), in this order:
1. **Single companies above 10%,** including look-through, largest first. For each:
   - the amount held directly (all stock holdings of that symbol, including lots without basis);
   - the suggested sale: the smaller of the direct amount and (share − 10%) × total;
   - its tax plan;
   - a staging line: "{excluded} has no cost basis and is excluded. Estimated {N} tax year(s) at the annual gain budget.", where N is the gain ÷ the gain budget rounded up, and at least 1;
   - alternatives to mention: "Consider an exchange fund where eligible", "Gift appreciated shares", "Consider a protective collar", "Evaluate a direct-indexing sleeve".

   The title is "{SYM}: {share} of the account including look-through", with the rule "Single company limit 10%".
2. **Sectors above twice their benchmark weight** (a missing benchmark counts as 10%). Title: "{Sector}: {share, no decimals} of equity vs {benchmark, no decimals} in the benchmark". Rule: "Sector above 2× benchmark".
3. **Funds (ETF or mutual fund) above 25% of the account.** Title: "{SYM}: {share} of the account". Rule: "Single fund limit 25%".
   - These need action unless the fund is a broad index fund: ITOT, VTI, VOO, IVV or IDX-I.
4. **Held stocks with a research change** (from the downgrades list). Title: "{SYM}: research view changed". These don't need action.
5. **Funds costing 50 bp or more.** Title: "{SYM}: review {bp} bp fund cost". Rule: "Fund cost review". These need action.

**Deep dive.**
- From the style box:
  - growth = the three growth cells; value = the three value cells;
  - large, mid and small = the sums of each row.
- Geography = U.S., International and Emerging shares of equity, today and for the target.
- Three dimensions:
  - **"U.S. equity style"** has a gap when growth and value differ by more than 30 points. The underrepresented side is value if growth is larger, otherwise growth.
  - **"Company size"** has a gap when mid is below 7% or small is below 4%. The underrepresented side is always "mid".
  - **"Geography"** has a gap when any region differs from target by more than 5 points. The underrepresented side is the region furthest below target ("us", "intl" or "em").
- For each dimension with a gap, buy a fill fund:
  - style gives LCV or LCG;
  - size gives SMID;
  - geography gives EM for "em", INTL for "intl", and LCG otherwise.
- The amount is min(max(0, projected excess cash), 3.5% of the account), rounded to $1,000. **Every dimension gets that same amount**, not a share of it. Drop amounts of $1,000 or less.

**Stress.** When today's worst-event return is below the household's target return for that event:
1. Take the largest negative contributor in that event that is tradable.
2. Sell min(20% of its value, 4% of the account), rounded.
3. Buy AGG and VGSH, each half of that, each rounded.

Otherwise there is no stress suggestion.

### 3.7 Risk alignment planner

**Settings:**
- **Align to:** "Target on file" (default) or "Profile model".
- **How far toward the chosen allocation:** 0–100% in steps of 5, default 50%.
- **"Within this year's {gain budget} gain budget":** on by default.
- **"Don't sell" chips:** one per tradable symbol, each toggling a lock.

The planner builds trade lines in four stages.

**1. Classes with no fund.**
- A class is "dead" when the chosen allocation gives it weight, it has no working fund, and the household holds none of it today. In the data that means HY, HF and PE, and Cash never.
- If any are dead:
  1. Remember the chosen allocation's expected risk, then set the dead classes to zero.
  2. Spread their weight across the remaining equity and fixed-income classes, keeping each side's internal proportions.
  3. Choose the equity fraction by halving the interval 30 times, so the rebuilt allocation's expected risk matches the remembered risk.

     The equity side gets fraction f of (equity + fixed + dead weight), and fixed income gets 1 − f. Search f from 0 to 1, moving toward whichever end brings risk closer.
- The dead weight is reported in the preview note.

**2. The wanted allocation.** Wanted weight = today's weight + slider × (chosen − today), for every class.

**3. Sales.**
- For every class except Cash where today exceeds wanted by more than $1,000, take the excess in dollars, largest first.
- For each such class, the sellers are tradable, unlocked holdings with at least 30% in that class. Order them by tax per dollar of a sale of min(value, $100,000). This uses the sale rule, and the division is always by $100,000 less any unfilled amount, even for smaller holdings.
- For each seller, while at least $1,000 of excess remains:
  - the amount is the smaller of its remaining value and the remaining excess ÷ its weight in the class;
  - if the gain budget is on and the household has a budget, compare **the gain of selling this amount on its own** against the budget left:
    - if it exceeds it, find by halving (22 times) the largest extra amount whose **added** gain (on top of what this symbol already sells) fits;
    - mark the plan as scaled;
  - round to $1,000 and skip if below $1,000;
  - add a sell line, add the added gain to the running total, and reduce the excess by amount × class weight.
- If excess above $1,000 remains after all sellers, mark the plan scaled.

**4. Buys.**
1. Money available = sale proceeds + max(0, cash held − wanted cash).
2. For every class except Cash where wanted exceeds today by more than $1,000 and a working fund exists:
   - the need is that excess;
   - buy the working fund for need × min(1, available ÷ total needs), rounded.
3. Then, for each group, room = (wanted group weight − today's group weight) × total + what the sales took out of that group (each sale × the sold holding's weight in the group's classes).
4. If the group's buys exceed room + $1,000, scale them by room ÷ buys, re-round, and mark scaled.
5. Drop buys below $1,000.

The result is the sells followed by the buys.

**The preview title** is "Align {slider}% to the target" or "Align {slider}% to the profile model". Its note is:
- "{dead weight} of target classes have no shelf fund and are spread across other classes to retain risk. ", when classes were dead;
- followed by "Sales or buys scaled to respect available cash, locked holdings or gains.", when scaled.

### 3.8 Goals

**Objectives on file** are listed in the appendix; Brennan has none. Each is one of three types:
- **Return:** "Return 6.5% a year".
- **Income:** "Income $75K per year".
- **Loss limit:** "Loss no worse than 30.0% in Housing and financial crisis".

**Progress:**
- **Return:** progress = return ÷ target; met when return ≥ target; shown as the return.
- **Income:** progress = income ÷ target; met when income ≥ target; shown as the income.
- **Loss limit:** compare the event return with the limit. Progress is 1 when the loss is within the limit, otherwise limit ÷ loss; met when within the limit; shown as the event return.

**The objective being worked on:**
- by default, the first on file, or for a household with none, a return objective at return × 1.1 rounded up to the next quarter point (for example 7.5%);
- the type buttons set a fresh objective:
  - Income: today's income × 1.1, rounded to $10,000;
  - Return: today's return × 1.1, rounded up to a quarter point;
  - Loss limit: 25% in Housing and financial crisis;
- the value box edits the amount or percentage, and the past-event select edits the event.

**Suggested trades** ("Atlas suggestion: move toward the objective"). None if the objective is already met.
- **Income:**
  - sell the tradable holding with the lowest yield;
  - the amount is min(60% of it, 12% of the account, max(1.5% of the account, income shortfall ÷ max(0.5%, 0.55 × 3.7% + 0.45 × 4.1% − its yield))), rounded;
  - buy SCHD for 55% (rounded) and AGG for the rest.
- **Loss limit:**
  - sell the largest negative contributor in that event that is tradable;
  - the amount is min(45% of it, 15% of the account, max(1.5%, 0.75 × max(0.5%, loss − limit)) × account), rounded;
  - buy AGG for 55% (rounded) and VGSH for the rest.
- **Return:**
  1. gap = target − return;
  2. amount = min(15% of the account, max(0, projected excess cash), max(1.5%, gap ÷ 9%) × account), rounded;
  3. take the first two load-time gaps that have a fill fund;
  4. if the amount is at least $1,000, buy the first fund for half (rounded) and the second for the rest;
  5. otherwise, sell 12% (capped at 4% of the account) of the lowest-yield tradable bond fund, and buy the first gap's fund with it.

### 3.9 Concentration trims

For each single-company item:
- a slider "Bring {SYM} down to {x} (including look-through)", from 10% to today's share in steps of 0.1 point, default 10%;
- **Reinvest**: "Into the gaps" (default), "One fund" (default VTV, changeable through the picker), or "Hold cash".

The sale is the smaller of the direct amount and (share − chosen level) × total, rounded, and it goes through the sale rule.

Reinvestment "into the gaps" takes the **first three** load-time gaps that have a fill fund. Each gets sale × (its dollars ÷ the dollars of **all** gaps with a fill fund), rounded. The buys therefore usually add up to less than the sale, and the rest stays as cash. Keep that behaviour.

The line under the controls reads: "This year: {sale} sold · gains {gain} · tax {tax} · {N} tax years at gain budget. {excluded} without cost basis is not sold." N is the gain ÷ the budget rounded up, and can be 0. The last sentence appears only when something is excluded.

The preview is titled "Trim {SYM} to {level}", and its note is the item's staging line.

### 3.10 Step statuses (journey dots and verdicts)

**Dots:**
- red: action needed;
- amber: review;
- green: on track;
- hollow ring: a workspace step;
- grey: nothing on file.

**Each step:**
- **Portfolio at a glance** (hollow): "{total} · {equity, no decimals} stocks · TE {tracking error to target}".
- **Risk profile alignment:**
  - find the group whose weight differs most from the target's group weight;
  - red if risk is outside the band; else amber if that difference is 5 points or more; else green;
  - verdict: "Risk {risk} {inside|outside} band · {group} {points}".
- **Asset allocation gaps:**
  - amber if any gaps, else green;
  - verdict: "{n} underweight · {excess cash + incoming} cash to use". Excess cash here is never negative.
- **Goal-based recommendations:**
  - grey "No objective on file" when there is none;
  - otherwise green if the first objective is met, else amber;
  - verdict: "{objective name} · {shown value}", plus " (met)" when met.
- **Holdings and concentration:**
  - red if any item needs action (research items don't count), else green;
  - verdict: the first two such items' titles up to the colon, joined with " · ", or "No flagged concentrations".
- **Portfolio deep dive:**
  - amber if any dimension has a gap;
  - verdict: "Short {underrepresented sides joined with commas}", or "In balance".
- **Historical stress scenarios:**
  - compare today's worst-event return with the target's return for that event: red if more than 5 points worse, amber if worse, else green;
  - verdict: "{event} {return} · target {target return}".
- **Downgraded stock alternatives:**
  - amber if the household holds a downgraded stock;
  - verdict: "{symbols} downgraded" or "None held".
- **Compare proposals** (hollow): "{n} proposals · {m} picked for client".
- **Client summary** (hollow): "Talking points to edit and copy".

**The stage header** repeats the step name as the heading (serif), the description under it, and a pill on the right:
- "Action needed" (red);
- "Review" (amber);
- "On track" (green);
- "Workspace" (brand colour) for hollow and grey steps.

### 3.11 Preview cards and adding changes

A preview shows a proposed set of lines for one change key:
- **Title**, a **Preview** pill and an optional note.
- **Five effect chips:**
  - Risk, Return, Income, TE and Tax;
  - each shows the value with the change and an arrow (▲, ▼ or —) with the absolute difference;
  - Risk, Return and TE differences are in points with two decimals ("▲ 0.25 pts"); Income and Tax differences are in money.

  "With the change" means the proposal's other changes plus these lines. "Without" means the other changes alone. So the chips are always marginal.
- **A table** of action (SELL in red, BUY in green), symbol with the fund name, an "After incoming cash" pill for stage-2 lines, and the amount.
- **An empty message** when there are no lines: "No executable trade lines at these settings. Change the controls to generate a plan."
- **A footer:** "Figures compare with the other changes in {proposal name}." and a primary button, "Add to {name}" or "Update in {name}" if this key is already in the proposal. The button is disabled with no lines.

**Adding:**
- Store the lines as a change with the preview's title as its label and the step as its lens. Replace any change with the same key.
- Clear any edited talking points.
- Toast "“{label}” added in {name}" or "… updated in …", then repaint.

**Change keys:**
- risk;
- "gaps:{class}" and "gaps:all";
- goal;
- "conc:{SYM}";
- deep;
- stress;
- "dg:{SYM}".

### 3.12 The proposal panel: KPIs and "why it changes"

**Eight KPI tiles,** in a two-column grid:

| KPI | Higher is better? |
|---|---|
| Expected risk | no |
| Expected return | yes |
| Sharpe ratio | yes |
| Tracking error vs target | no |
| Income a year | yes |
| Worst past event | yes, less negative |
| Fund costs | no |
| Illustrative tax | no |

Each tile shows:
- its value for the active proposal, applied to the household;
- with changes, "▲ from {today}" or "▼ from {today}" coloured green if the move is in the good direction and red otherwise;
- with no changes, "Today".

**Two traps:**
- **Worst past event always uses today's worst event**, not the proposal's worst.
- The **expected risk tile gets a red border** when the proposal's risk is outside the band.

**The tax tile** also shows a meter of gains ÷ gain budget, capped at 100% and red when over, and "Gains {gain} / {budget}".

Clicking a tile selects it for the **"Why {kpi, lower case} changes"** box, shown only when the proposal has changes. It holds a sentence and a waterfall chart.

**The waterfall:**
- Start with today's value.
- Apply the proposal's changes one at a time, cumulatively, in the order they were added. Each step is the difference in the KPI.
- The bars are:
  - "Today" (grey) from zero to the start;
  - one bar per change, green if it moves in the good direction, red otherwise;
  - the proposal name (dark) from zero to the end.

**The sentence**, built exactly like this:
1. If the KPI barely moves: "{KPI} is unchanged at {value}."
2. Otherwise: "{KPI} {rises|falls} from {start} to {end}, mainly because “{label of the step with the largest absolute effect}” {movement} ({that step's effect})".
3. The **movement phrase describes the whole proposal**, not that step. Compare the proposal's group weights with today's and keep groups that moved half a point or more:
   - if some fell and some rose: "moves about {largest absolute group move, no decimals} of the account from {groups that fell, joined with "and"} into {groups that rose}";
   - "adds {groups}" if only rises;
   - "reduces {groups}" if only falls;
   - "swaps investments within the same asset groups" if none.
4. If some step moved the KPI the opposite way, add "; “{largest such step}” works in the other direction ({its effect})".
5. For expected risk, end with ". It stays inside the {profile} range." or ". It ends outside the {profile} range ({low}–{high})."; for every other KPI end with ".".
6. Effects are formatted as points for percentages ("+0.3 pts"), money for income and tax, "0.4 bp" for costs, and two decimals for Sharpe.

**The change list** shows each change as a box:
- its label, and the step name in small type;
- a remove button (×);
- one row per line: BUY or SELL in small capitals, the symbol, the fund or stock name (or the note text), "After incoming cash arrives" for stage 2, and an editable amount box with separators.

Editing an amount strips "$", commas and spaces, floors at zero, clears edited talking points and repaints. Under the list, in red when any apply: "Cash short by {x}." "Incoming cash short by {x}." and any unmatched messages.

With changes, the panel also shows:
- **"Client talking points"**: the first three bullets of section 3.14 in a tinted box;
- an **"Open summary →"** link.

**The footer** has "Check and propose" (primary, disabled with no changes), "Compare", and "Clear" (red, disabled with no changes). Clear empties the active proposal and drops its client pick.

**Proposal tools** at the top of the panel:
- **Tabs:** one per proposal, lettered by position ("A", "B", …, even if names differ), each with its change count, plus "✓" when for client, and a "＋" tab for a new proposal. Switching tabs resets the "why" box to expected risk.
- **The name** in an editable box. An empty name becomes "Untitled proposal".
- **"Duplicate":** copy with the next id and letter name, not for client.
- **"Delete":** disabled when only one proposal is left.
- **A pill:** "For client" or "Working".
- **Toasts:** "{name} created", "{name} duplicated".

### 3.13 Checks (the "Check and propose" sheet and the compare cards)

Seven checks, each with a group, a title, pass or fail, and a detail:

| Group | Check | Passes when | Detail |
|---|---|---|---|
| Executable | "Cash on hand and staged incoming cash" | both shortfalls are under $1 | "Cash shortfall {x}, staged shortfall {y}" |
| Executable | "Sell quantities are available with cost basis" | no unmatched messages | the messages, or "All sale quantities are available" |
| Executable | "Sales directed by advisor" | no sell line names a symbol that exists only as non-tradable holdings | those symbols, or "No manager-run or illiquid holdings sold" |
| Gain budget | "Net gains within {budget} budget" | gains ≤ budget + $1 | "Estimated gains {gain}" |
| Policy limits | "{profile} risk band {low}–{high}" | risk within the band | "Expected risk {risk}" |
| Policy limits | "Below investment grade" | HY weight ≤ the household limit | "HY {x} vs limit {limit}" |
| Policy limits | "Turnover at or under 40%" | total sells ÷ today's total ≤ 40% | "Turnover {x}" |

**The sheet:**
- Heading: "Proposal checks", then "Check and propose · {name}", then "A review for client discussion; this is not a trading approval."
- **A status pill:**
  - "Not executable as is" (red) if an Executable check fails;
  - else "Outside a guideline" (amber) if any check fails;
  - else "Executable and within policy limits" (green).
- **Each check** as a row with a green or red dot, its title in bold, and "{group} · {detail}" beneath.
- **"Points to weigh for suitability"**, as bullets:
  - "The modeled worst-event loss worsens by more than 3 points." when the proposal's return in today's worst event is more than 3 points below today's;
  - "Expected annual income falls more than 10%." when it does;
  - "Largest single company remains above the 10% guideline." when the proposal's top name is above 10%;
  - always "The 37% federal bracket and illustrative tax assumptions are on file."
- When anything fails, a text box: "Exception reason (required for policy or gain-budget exceptions)", with the placeholder "Explain the proposed exception for review."
- The tax disclosure.
- **Footer:** "Client discussion only · prototype: not saved" and "Accept for client discussion" (disabled when not executable).

**Accepting:**
- If any check fails and the reason is empty: toast "Record a reason for the exception before accepting."
- Otherwise:
  1. mark the proposal for client;
  2. close the sheet;
  3. toast "Accepted for client discussion · added to summary (not saved)".

On the compare cards, the failed count shows as "{n} checks fail" (amber), "Passes checks" (green), "Empty", or "Baseline" for Today.

### 3.14 Talking points

Built for a proposal as bullets ("• " and a blank line between):
1. "Where you are today: about {equity} stocks, {fixed} bonds, {cash} cash{ and {alt} alternatives, when above half a point}. Expected volatility is {risk} in the {low}–{high} profile range." Shares use no decimals.
2. **One bullet per change.**
   - "{sells}" lists up to four sales as "{amount} of {SYM}", after "sell". With no sales it is "no sales".
   - "{buys}" lists up to four buys as "{amount} in {SYM}", after "invest". With no buys it is "hold proceeds as cash".
   - The bullet depends on the step:

| Step | Bullet |
|---|---|
| Concentration | "Address the concentration in {SYM}: {sells}; {buys}." |
| Risk | "Move your asset mix toward the {profile model\|target portfolio}: {sells}; {buys}." |
| Gaps | "Fill an allocation gap: {buys}{ when incoming cash arrives, if any stage-2 line}." |
| Stress | "Reduce exposure to historical stress losses: {sells}; {buys}." |
| Deep dive | "Broaden the mix of sizes, styles and regions: {buys}." |
| Goal | "Work toward your stated objective: {sells}; {buys}." |
| Downgrades | "Discuss downgraded research with the investment manager: {note texts joined with "; "}." |

3. "What changes: expected return {a} to {b}; expected volatility {a} to {b}; annual income {a} to {b}; in a repeat of {today's worst event}, about {a} to {b}. Estimated tax {tax}."
4. With changes:
   - "Why risk changes: " followed by the risk sentence from section 3.12;
   - "Why income changes: " followed by the income sentence, when income moves by more than $1,000.
5. "Figures are illustrative estimates; historical results are not a forecast, and tax figures should be confirmed with your tax advisor."

**Editing:**
- Edited text is kept per proposal until "Rebuild from changes", or until any change to the proposal clears it.
- "Copy" uses the clipboard and falls back to a hidden text area. Either way, toast "Client talking points copied".

---

## 4. The screens

### 4.1 Top bar and journey

**Top bar,** left to right:
- the brand mark (a rounded square in the brand colour) with "Portfolio Review" and "Atlas · prototype v2";
- "Household" and a select listing the five households in appendix order. Changing it opens that household on "Portfolio at a glance", closes any sheet and scrolls to the top;
- the facts:
  - account value (bold) over "Account value";
  - "{profile} · {tier}" over the model name;
  - the meeting text (for example "in 2 days, Annual review") over "Next meeting";
  - "15 Oct 2026" over "Positions as of";
- the "Illustrative" pill (amber);
- the theme toggle (◐).

Each household keeps its own settings and proposals while you switch between them.

**Journey:**
- group labels "Explore", "Review" and "Decide" in small spaced capitals;
- one button per step: a dot, the step name in bold, the verdict beneath in small muted text, and on the right a small brand-coloured count of changes from that step when there are any;
- the active step has a brand-coloured left border and a tinted background.

### 4.2 Portfolio at a glance

**Lede:** "{equity} stocks, {fixed} bonds, {cash} cash{, {alt} alternatives}. Expected risk **{risk}** {inside|below|above} the profile band; tracking error to the target **{te}**; largest name **{SYM} {share}**." Shares use no decimals.

**"Allocation · drill down" panel.**

Controls:
- **"View by"**: Asset classes, Sectors or Holdings.
- **"Show"**: Today, the active proposal's name, or Target.
  - Target is offered only for asset classes.
  - The proposal option is disabled when the proposal is empty.
  - Returning to this step while the proposal is empty resets "Show" to Today.

Breadcrumbs start at "Portfolio" and are clickable back up.

**Asset classes (default).**
- **Level 1** is a sunburst:
  - inner ring: the four groups;
  - outer ring: classes, in shades of their group colour;
  - centre: the total to one decimal ("$49.7M") over "today", "proposal" or "Target" / "on file".

  The table beside it lists the groups: Exposure, Weight, Target, and Gap in points, green when under target by more than a point and red when over. Caption: "Level 1: groups · Level 2: asset classes".
- **Level 2** (click a group) is a donut of that group's classes, centred on the group's share over "of account", with the class table.
- **Level 3** (click a class) is a treemap of the holdings in that class (value × class weight), labelled with symbols and shares, plus a table of up to 12 without target columns.
  - In Target mode this level shows "The target is set at the asset-class level. Choose Today or a proposal to explore the underlying holdings."
  - Caption: "Click the chart or rows for holdings and details."

**Sectors.**
- A donut of up to 11 sectors, the first seven in the categorical colours and the rest grey, centred on the top sector's share and name.
- A table against the benchmark.
- Clicking a sector shows a treemap of the holdings behind it, with shares of equity.

**Holdings.** A treemap of every holding, coloured by its first class's group, plus a table of the 12 largest.

**Holding card.** Clicking a holding anywhere opens a card under the chart (click again to close):
- the symbol and name, with a close button;
- eight small stats:
  - Account value;
  - Share of account;
  - Unrealized gain (with " · basis missing" when a lot has none);
  - Expected return and Risk, from the holding's class mix;
  - Yield;
  - Fund costs ("— " when unknown);
  - Past-event average, the mean of its four event returns;
- "Asset classes: {class} {weight} · …" and either "{n} holdings · Top 10 {share}" or "Direct holding";
- a lot table: Lot, Term, Value, Basis ("Missing" when none), Gain;
- the research report card if any: "Illustrative fund research · {date} · {view}", the name, the summary, then "Strengths: …. Risk: …".

**"Investment analytics."** Ten tiles, each with a tooltip:
- Expected return;
- Expected risk, with "Band {low}–{high}" beneath;
- Sharpe ratio;
- Tracking error vs target;
- Tracking error vs model;
- Yield · income, with "{income} annually, before taxes." beneath;
- Fund costs;
- Largest single name;
- Worst past event, with the history disclosure in its tooltip;
- Below investment grade.

The tiles follow the "Show" choice. When the proposal is shown, expected return carries "Today {x}" beneath.

The history disclosure closes the page.

### 4.3 Risk profile alignment

**Lede:** "Expected risk is **{risk}**, {inside|below|above} the {profile} band ({low}–{high}); tracking error to the target is **{te}** and to the profile model **{te model}**." When the chosen allocation's own risk is outside the band, add an amber pill: "Target expected risk {x} is outside the band".

**Two panels side by side:**
- **"Risk against the profile band":**
  - a half-circle gauge from 0% to 20%, with the band shaded green, a dark tick for today and a brand-coloured tick for the plan;
  - the plan's risk large in the centre over "expected risk";
  - caption: "Dark tick: today · Teal tick: plan · Shaded: profile band";
  - two pills: "TE {today} → {plan}" and "Sharpe {today} → {plan}".
- **"Allocation: today → with this plan":**
  - a Groups / Classes switch (Groups by default);
  - a dumbbell chart: a hollow dot for today, a filled dot for the plan, a yellow tick for the chosen allocation, and the plan's value on the right;
  - caption: "○ Today · ● Plan · Yellow tick target".

**"Adjust alignment"** holds the settings from section 3.7. Then come the preview and the tax disclosure.

### 4.4 Asset allocation gaps

**Lede:** "**{n} asset classes are underweight**, about {total gap dollars} in total. **{excess cash}** of excess cash {and {incoming} arriving {date}} can fill gaps without selling."

**"Allocation heat map".** One tile for every class with a target or a holding:
- the class name, plus " ★" when its working fund is a favourite;
- the gap in points (target − today);
- "{today} → {target}";
- " · No shelf fund" when there is no working fund.

The tile colour is blue for underweight and orange for overweight, with intensity 8% plus up to 40% as the gap approaches 10 points. Gaps under a point are neutral.

Beneath the tiles:
- a small blue-white-orange gradient bar;
- "Blue = underweight · Orange = overweight · ★ Favorite fund".

Clicking a tile selects that class, resets the amount, and clears sell sources. The default selection is the largest gap.

**Two panels:**
- **"Underweight: today → target":** a dumbbell of the load-time gaps.
- **"{class} · {money} short of target"** or "{class} · At or above target":
  - The shortfall is measured **after the proposal's other changes**, excluding this class's change and the cash-plan change.
  - **"Invest in":** the working fund's symbol and name, with "{cost} bp · Yield {y} · {view}" beneath, and a "Choose from heat map or favorites" button that opens the picker for this class.
  - **"Amount ($)":** defaults to the shortfall, rounded.
  - **"Pay with":** "Cash on hand" (default); "Incoming cash", only when the household has incoming cash, which makes the buy stage 2; or "Sell holdings".
  - With "Sell holdings", a table of tradable funding sources sorted by tax per $100K. It has a checkbox per source, "Tax/$100K" and "Overweight" (Yes or —). The checked sources are sold in table order until the amount is covered, and each sale is rounded.
  - At or above target, the panel shows "{class} is at or over the target. Use Risk profile alignment to trim it."

**Previews:**
- **"Fill {class}"**. Its note depends on how it is paid:
  - incoming cash: "Investment staged after {incoming} arrives on {date}; not paid from today's cash.";
  - selling: "Sales fund this purchase; review cost basis and tax.";
  - cash: "Purchased with cash on hand. Exceeding available cash will be flagged.".
- **"Atlas suggestion: invest new and excess cash in the gaps"**, only when the cash plan has lines. It shows the load-time cash plan, with the note "Illustrative cash-first plan; incoming cash purchases are marked as stage two."

The tax disclosure closes the page.

### 4.5 Goal-based recommendations

**Lede:** "{objective name}: **{today}** today, **{with proposal}** with {proposal name} —" followed by a "Met" (green) or "Not yet met" (amber) pill.

**"Objectives on file":** one chip per objective; the one being worked on is highlighted.

**Two panels:**
- **"Progress toward objective":**
  - a ring chart: a grey outer ring for today's progress and a brand-coloured inner ring for the proposal's;
  - the proposal's shown value in the centre over "Objective met" or "Toward objective";
  - caption: "Outer ring: today · Inner ring: proposal".
- **"Trade-offs from the suggested changes":** a dumbbell, today against the **suggested trades applied on their own**, for four rows:
  - Expected return, marked at the target return, or at today's return for other objective types;
  - Expected risk, marked at the band's upper end;
  - Yield, marked at today's yield;
  - "{event} loss", as a positive number, marked at the loss limit or at 35%.

  Caption: "Farther right means more return or yield, but also more risk or loss."

**"Objective settings":**
- an Income / Return / Loss limit switch;
- "Annual income ($)" or "Target (%)";
- for loss limits, a "Past event" select.

Then the preview and the history disclosure. The preview's note is "Review the proposed changes alongside income, portfolio risk, market history and suitability."

### 4.6 Holdings and concentration

**Lede:** "**{n} position or exposure issue(s) need(s) a decision** once fund holdings are looked through. Guideline: one stock 10.0%, one fund 25.0%." Use the singular forms for one; n counts the items that need action, excluding research.

**Two panels:**
- **"Largest companies · including through funds":**
  - a treemap of the 14 largest names: red above 10%, blue otherwise, faded below 5%;
  - caption: "Red: over 10% single-company guideline."
- **"Sectors vs equity benchmark":** a donut of up to 10 sectors, centred on the top share over "largest sector", and a table of the top seven against the benchmark.

**"Items for advisor review":** one panel per item from section 3.6, in order.
- **Single companies:**
  - the title, with a red "Limit 10.0%" pill;
  - "Direct {x} · Through funds {y}. Single company limit 10%.";
  - the controls from section 3.9 ("Choose fund" appears when reinvesting into one fund);
  - the preview;
  - a closed "Other ways to reduce concentration" section listing the alternatives.
- **Other items:**
  - the title, with a pill holding the rule name (amber if action is needed, green if not);
  - the assessment text.
- **Sector items** add "Lower-correlation options to consider": a small table of AGG, VGSH, VTV and SCHD with their yield and research view.
- **Cost items** add "Find lower-cost alternatives", which opens the picker for the holding's first class.
- With no items: "No holdings currently trigger these concentration and credit checks."

The tax and research disclosures close the page.

### 4.7 Portfolio deep dive

**Lede:** "Explore diversification beyond headline asset allocation. {n} style, size or geography dimensions show a gap based on the reference rules."

**Two panels:**
- **"U.S. equity style box":**
  - a 3 × 3 grid of buttons with Value, Blend and Growth across and Large, Mid and Small down;
  - each cell shows its share and its code, shaded blue in proportion to its share;
  - clicking a cell opens the picker for funds with at least 20% in that cell;
  - caption: "Select a cell to compare suitable investments. Percentages reflect available look-through facts."
- **"Geography · stocks":** a donut of U.S., International and Emerging, centred on the U.S. share over "U.S. stocks", with a table against the target's equity mix.

**"Diversification opportunities":** one small panel per dimension, with a "Gap" (amber) or "In balance" (green) pill and "Underrepresented: {side}" or "Current mix near the illustrative guideline."

Then, for each suggested buy, an "idea" card:
- "Atlas idea · {class}";
- "Add {amount} of {SYM}";
- "Diversifies an underrepresented part of the portfolio.";
- "Compare {SYM} with alternatives", which opens the picker on that fund's main class.

The preview is "Broaden the investment mix", with the note "Adds gaps first from excess cash; manager briefings and fund research are illustrative." The research disclosure closes the page.

### 4.8 Historical stress scenarios

**Lede:** "Worst past event for today's holdings: **{event}, {return}**, versus {target's return} for the target on file."

**"Size of the loss in each event":** a wide dumbbell, one row per event.
- Losses are shown as positive numbers on a 0–70% scale, labelled with a minus sign.
- Each row has a hollow dot for today, a filled dot for the proposal, and a yellow tick for the target.
- Caption: "○ Current loss · ● Proposal loss · Yellow marker: target allocation. A larger number is a larger modeled loss."

**Event chips** select the event for the treemap below.
- **The default is Housing and financial crisis for every household,** even where another event is the worst (Brennan).
- The panel is "{event}: what drove the loss": a red treemap of each holding's dollar loss in that event.
- Caption: "Negative holding-level contributors to the illustrative event; select a holding for detail."

The preview is "Reduce the modeled stress loss", with the note "Consider reducing the largest negative contributor and adding aggregate and short-duration bonds." The history and tax disclosures close the page.

### 4.9 Downgraded stock alternatives

**Lede:** "**{SYM} and {SYM}** have recent research changes in this household.", or "No downgraded holdings in this household.", followed by " An update may call for a manager conversation rather than an immediate trade."

**For each held downgrade:**
- a panel titled "{SYM} · {name}", with an amber pill "{from} → {to} · {date}" and the reason beneath;
- pills: "Position {mv}", "Account {share}", "Tax to switch {tax}" (for example "$4,500 saved") and "Decides: {decides}";
- **"Similar alternatives to evaluate"**: a table of Investment, Research, Style, Beta and Yield, with ★ for favourites. Clicking a row selects it; the first is selected by default.
- **When a manager decides** ("Manager" appears in the decides text):
  - "A manager directs this holding. Next step: discuss the rating change, not place an advisor-directed trade.";
  - a primary **"Add manager discussion note"** button. It adds the change "Discuss {SYM} with manager" with one note line: "Ask {decides} about the {SYM} downgrade and {selected alternative} as an alternative."
- **When the advisor decides:** a preview "Switch {SYM} to {alternative}" that sells the position's value and buys the alternative for the same amount. Its note is "Research is a prompt for advisor consideration, not an automatic sell decision."

**"Across the book · illustrative research updates":**
- a pill per downgrade, "{SYM} · {holders' first names}";
- the note "Only five households have full portfolio information in this prototype. Additional names are included for context, not as navigable household portfolios.";
- buttons "Open {SYM} · {household}" for downgrades held by one of the five households. Each opens that household on this step.

The research disclosure closes the page.

### 4.10 Compare proposals

**Lede:** "Compare expected outcomes and implementation constraints. **{n} proposal(s) selected** for discussion with the client."

**Cards,** in a responsive grid: Today, then each proposal. Each card shows:
- the name and a status pill (section 3.13);
- a small group donut, centred on the equity share over "stocks";
- "Current holdings", or the first three change labels joined with " · ", or "No proposed changes";
- nine rows:
  - Expected risk;
  - Expected return;
  - Sharpe;
  - TE vs target;
  - Income a year;
  - "Past event: {today's worst event}";
  - Fund costs;
  - Largest name ("{SYM} {share}");
  - Tax this year.

Proposal cards also have:
- a "Take to client" checkbox chip, disabled when empty;
- "Make active" (or a disabled "Active");
- "Duplicate".

A picked card has a brand-coloured border.

**Footer:**
- "“Best” depends on the client; suitability remains the advisor's determination."
- A primary "Client summary for {n} proposal(s)" button. n is the picked proposals with changes, or 1 when there are none.

The tax and history disclosures close the page.

### 4.11 Client summary

**Which proposals are summarised:**
- the proposals marked for client that have changes;
- if none, the active proposal when it has changes;
- otherwise the message: "No proposal changes yet. Add a potential change from a review screen to create client talking points."

**Content:**
- **Lede:** "Talking points for **{names joined with "and"}**. Edit to suit the client's priorities before using in a meeting."
- **With more than one proposal,** an "Options side by side" table: Expected return, Expected risk, Income a year, Worst past event (today's worst event) and Tax this year, for Today and each proposal.
- **For each proposal,** a card with:
  - the name in a serif heading;
  - "Rebuild from changes" and a primary "Copy";
  - a tall editable text area holding the talking points. It grows with its content.
- A primary **"Print client summary"** button. Printing shows only the stage.

The tax and history disclosures close the page.

### 4.12 The fund picker (right-hand sheet)

**Opened by:**
- "Choose from heat map or favorites" (gaps, for a class);
- "Find lower-cost alternatives" (cost items, for the holding's first class);
- "Choose fund" (concentration, reinvesting in one fund);
- "Compare {SYM} with alternatives" (deep-dive ideas, for the fund's main class);
- a style-box cell (deep dive, for the cell).

**Header:**
- "Investment selection" in small capitals;
- the title: "Fill {class}", "Choose reinvestment for {SYM}", "Compare alternatives to {SYM}" or "Investment research · {cell}";
- "Illustrative fund shelf · select a row to review research and manager briefings.";
- a close button.

**Tabs:**
- **"Heat map ({n})"**: funds with at least 40% in the class, or at least 20% in the style cell, sorted by that weight, largest first, keeping shelf order for ties;
- **"★ Favorites ({n})"**: adds a box ("Add tickers, e.g. SCHD VEA") and an "Add favorites" button that accepts shelf symbols only. If none of them are on the shelf, toast "None of those are on the prototype fund shelf";
- **"All shelf funds"**.

Above the table: "Heat shading rewards stronger fit, lower tracking error and fees, research, yield, diversification and historical results. A heat map is a comparison tool—not an investment recommendation."

**The table** has a column per measure. Each cell is shaded green toward the good end and red toward the bad end, with intensity 8% plus up to 30% the further it is from the middle of its range:

| Column | Value | Range (bad → good) |
|---|---|---|
| Investment | symbol (bold, monospace) and name | — |
| Fit | weight in the class or cell (no decimals) | 0 → 100% |
| TE | tracking error of the fund's class mix against 100% in the class; "—" for a style cell | 23% → 0 |
| Cost | bp | 120 → 0 |
| Research | view: Recommended counts 1, Neutral 0.5, Not recommended 0, and anything else 0.3 | 0 → 1 |
| Sharpe | of the fund's class mix | −0.1 → 0.6 |
| Corr. | Σ over the fund's classes and the household's largest-name holding's classes of weight × weight × correlation (that holding's classes, or 100% LCG when the largest name isn't held directly) | 1 → −0.2 |
| Yield | | 0 → 5% |
| Past avg | mean of its four event returns | −50% → +10% |
| Holdings | count | — |
| ★ | a favourite toggle that saves to local storage | — |

Clicking a row selects it; the first row is selected by default.

**Below the table,** a soft panel for the selected fund:
- pills: "Cost {bp} bp", "Yield {y}", "{n} holdings", "Expected risk {x}" and "Expected return {x}";
- its research report card;
- up to two manager briefings whose classes the fund holds above 10%, each showing "Illustrative manager briefing · {date}", the manager, then the summary and positioning;
- the research disclosure.

**Footer:** "Cancel" and a primary "Use {SYM}". Using the fund:
- for a class: makes it the working fund for that class (section 3.5);
- for concentration: sets reinvestment to that one fund;
- toasts "Using {SYM} for this change".

The scrim, the close button and Escape all close the sheet.

### 4.13 Check and propose sheet

Described in section 3.13. It uses the same right-hand sheet, at most 860 px wide.

---

## 5. Look and feel

**Type:**
- the base is 14 px "Public Sans" (falling back to system UI) with tabular numbers;
- stage headings are 30 px "Newsreader" serif, weight 500;
- symbols use "IBM Plex Mono".

None of these fonts are loaded; the fallbacks are fine.

**Colour tokens.** The light theme comes first; dark values are in brackets.

| Token | Light | Dark |
|---|---|---|
| canvas | #eef0f3 | #0b0e13 |
| paper | #fff | #141922 |
| paper-2 | #f6f7f9 | #191f29 |
| inset | #eef1f4 | #10151d |
| text | #141a23 | #e6e9ef |
| text-2 | #3d4655 | #b6bdc9 |
| muted | #687282 | #8a93a1 |
| faint | #98a1ae | #5f6876 |
| line | #dde2e8 | #262e3b |
| line-2 | #e9ecf0 | #1f2631 |
| brand | #0c5d51 | #3fb7a0 |
| brand-2 | #09493f | #2f9c88 |
| brand tint | #e3f0ed | #10302a |
| good | #0b7a4b | #40c48d |
| warn | #9e5e12 | #d79a46 |
| bad | #a2323e | #e0736f |

Matching tints for good, warn and bad:
- light: #e3f3ea, #f7eedd, #f6e4e6;
- dark: #0f2a1f, #2a2214, #2c171a.

**Categorical colours:**
- light: #2a78d6, #eb6834, #1baf7a, #eda100, #e87ba4, #008300, #6250d6, #e34948, and "other" #a6acb5;
- dark: #3987e5, #d95926, #199e70, #c98500, #d55181, #008300, #9085e9, #e66767, and "other" #5e6672.

**Group colours:** Equity colour 1 (blue), Fixed income colour 2 (orange), Cash colour 3 (green), Alternatives colour 4 (amber).

**Under and over shading:** the RGB values 42,120,214 and 235,104,52; in dark, 57,135,229 and 217,89,38.

**Theme.**
- Dark mode follows the operating system unless the toggle has set a theme on the root element.
- The toggle flips between light and dark, starting from light.

**Layout.**
- Content is at most 1680 px wide.
- Three columns: 236 px, flexible, and 372 px, with 16 px gaps.
- Cards are white with a 1 px line and 14 px radius.
- The journey and the proposal panel are sticky below the top bar and scroll on their own.
- Panels have a 10 px radius. Previews, the adjust area and the soft panels use paper-2.

**Narrower screens:**
- **Below 1320 px:**
  - the journey becomes a horizontal strip of compact steps above the stage (no group labels or verdicts; the active step is underlined);
  - two columns remain: the stage and a 352 px panel;
  - two-up grids stack;
  - the top bar drops the profile and meeting facts.
- **Below 880 px:**
  - one column;
  - the top bar keeps only the brand, the household select, the pill and the toggle;
  - the proposal panel becomes a sheet fixed to the bottom, 62 px tall, showing "{name} · {n} changes" and "Open ▴". It expands to 78% of the viewport height with "Close ▾";
  - charts stack above their tables;
  - stat tiles are two-up.
- **Below 420 px:** smaller headings, and the heat map is two columns.

**Charts.** All charts are inline SVG and share these behaviours:
- every mark has a tooltip ("{label}: {value}");
- drillable marks are clickable and brighten on hover;
- text inside charts ignores the pointer.

The individual charts:
- **Donut:** a ring with a 62% hole and small gaps between slices, plus a centre label and sub-label. The label shrinks for long text.
- **Sunburst:** two rings, the inner from 34% to 62% of the radius and the outer from 64% to 100%. Outer slices are their group colour mixed with white in steps of 14%, and slices narrower than about half a degree are hidden.
- **Treemap:** squarified, so area is preserved, with 1 px gaps and rounded tiles.
  - Labels are white, with the symbol bold when the tile is wide enough and a sub-label on large tiles.
  - The default palette cycles through the categorical colours unless a colour is given.
- **Gauge:** a 180° arc, grey with the band in green, 16 px strokes, two ticks, and the value centred with "0%" and "20%" at the ends.
- **Ring:** two concentric progress rings starting at 12 o'clock.
- **Dumbbell:** four vertical grid lines with value labels across the top.
  - Each row has a label of up to 23 characters, a grey bar between today and the plan, a yellow tick for the target, a hollow dot for today, a filled brand dot for the plan, and the plan value bold on the right.
- **Waterfall:** horizontal bars as described in section 3.12. Labels are cut to 18 characters, with values on the right.

**Other details:**
- Pills are rounded, with good, warn, bad and brand variants.
- Toasts are a dark rounded bar at the bottom centre for about 3 seconds.
- Disclosures are small muted text above a hairline.
- Focus rings are a brand-coloured 3 px outline.
- When printing, only the stage shows: no buttons, segment controls, panel or journey.

---

## 6. Build order and figures to check

**Build in this order:**
1. Data and the engine.
2. Load-time suggestions.
3. The proposal model and the apply step.
4. Charts.
5. Top bar, journey and panel.
6. Each screen.
7. Sheets.
8. Responsive styles and dark theme.

After each step, compare with the figures below. They come from the reference prototype, rounded as displayed.

**Today, by household:**

| Household | Value | Stocks / bonds / cash / alts | Return | Risk | Sharpe | TE target / model | Income | Costs | Largest name | Worst event |
|---|---|---|---|---|---|---|---|---|---|---|
| Henderson Family Trust | $49.70M | 53 / 32 / 15 / 0 | 5.6% | 9.2% | 0.25 | 2.4% / 2.1% | $1.04M | 2.1 bp | NVDA 22.9% | Housing and financial crisis -27.9% |
| Kaplan Household | $8.70M | 64 / 22 / 14 / 0 | 5.9% | 10.4% | 0.25 | 1.8% / 2.5% | $185K | 2.0 bp | AAPL 28.9% | Housing and financial crisis -33.8% |
| Castellano Family | $3.20M | 71 / 24 / 5 / 0 | 6.3% | 11.1% | 0.27 | 1.7% / 2.7% | $89K | 6.6 bp | JPM 8.8% | Housing and financial crisis -40.0% |
| Okonkwo Holdings LLC | $31.60M | 30 / 15 / 45 / 10 | 5.2% | 6.5% | 0.30 | 4.2% / 5.2% | $941K | 1.7 bp | NVDA 1.3% | Housing and financial crisis -19.2% |
| Brennan Household | $900K | 84 / 4 / 6 / 7 | 6.6% | 15.3% | 0.22 | 4.2% / 4.2% | $6,508 | 36.7 bp | NVDA 32.2% | Technology bubble -56.7% |

**Journey verdicts for Henderson:**
- "$49.70M · 53% stocks · TE 2.4%";
- "Risk 9.2% inside band · Alternatives −10.0 pts" (amber);
- "8 underweight · $9.81M cash to use" (amber);
- "Return 6.5% a year · 5.6%" (amber);
- "NVDA · MSFT" (red);
- "Short value, mid, intl" (amber);
- "Housing and financial crisis -27.9% · target -34.1%" (green);
- "None held" (green);
- "1 proposals · 0 picked for client";
- "Talking points to edit and copy".

**Other households' risk and concentration verdicts:**
- Kaplan "Risk 10.4% outside band · Cash +8.8 pts" and "AAPL · Information Technology";
- Castellano "Risk 11.1% outside band · Fixed income −0.9 pts" and "Energy · LCV-I", with "Income $75K per year · $89K (met)" and "CVS, PFE downgraded";
- Okonkwo "Risk 6.5% outside band · Cash +39.9 pts" and "No flagged concentrations";
- Brennan "Risk 15.3% outside band · Alternatives +6.7 pts", "NVDA · AAPL", "No objective on file" (grey), and stress "Technology bubble -56.7% · target -35.9%" (red).

**Load-time suggestions:**
- **Henderson gaps,** largest first:
  - LCV $5.47M (SCHD);
  - SMID $2.80M (IJH);
  - UST $2.69M (VGSH);
  - HY $2.55M (no fund);
  - HF $2.49M (no fund);
  - PE $2.49M (no fund);
  - INTL $2.47M (VEA);
  - EM $635K (VWO).

  The total is $21.58M, and excess cash is $4.82M.
- **Henderson cash plan:**
  - SCHD $3,815,000;
  - IJH $1,000,000;
  - IJH $954,000 (stage 2);
  - VGSH $1,878,000 (stage 2);
  - VEA $1,725,000 (stage 2);
  - VWO $443,000 (stage 2).
- **Okonkwo cash plan,** all stage 1: VUG $2,012,000, SCHD $1,759,000, MUB $1,533,000, IJH $1,367,000, VWO $1,002,000.
- **Castellano** has no cash plan, because excess cash is $0.
- **Concentration items:**
  - Henderson:
    - "NVDA: 22.9% of the account including look-through", suggested sale $6,427,000, with "$400K has no cost basis and is excluded. Estimated 6 tax year(s) at the annual gain budget.";
    - "MSFT: 10.6% …", sale $283,000;
    - "Information Technology: 70% of equity vs 27% in the benchmark".
  - Brennan:
    - NVDA 32.2% (sale $200,000, 10 years);
    - AAPL 15.1%;
    - Information Technology 70%;
    - "LCG-A: review 95 bp fund cost";
    - "BAL-C: review 170 bp fund cost".
  - Castellano:
    - "Energy: 9% of equity vs 4% in the benchmark";
    - "ITOT: 28.1% of the account" (no action);
    - CVS and PFE research items;
    - "LCV-I: review 55 bp fund cost".
- **Deep dive:**
  - Henderson: growth 80.4% vs value 8.4%; mid 1.7%, small 1.1%; U.S. 83.7%. Ideas: SCHD, IJH and VEA at $1,740,000 each.
  - Okonkwo: style in balance (30% / 30%), short mid and em. Ideas: IJH and VWO at $1,106,000.
- **Stress suggestion:** only Castellano (sell ITOT $128,000; buy AGG and VGSH $64,000 each) and Brennan (sell NVDA $36,000; AGG and VGSH $18,000).

**Risk alignment at defaults** (target, 50%, gain budget on):

| Household | Lines | Plan risk | Gains | Note |
|---|---|---|---|---|
| Henderson | sell VTI $5,603,000, AGG $5,100,000, MUB $227,000; buy SCHD $3,360,000, IJH $1,660,000, IEFA $1,668,000, VWO $447,000, VGSH $2,129,000 | 9.5% | $480K | dead 15.1%, scaled |
| Kaplan | sell VTI $913,000; buy SCHD $381,000, IJH $248,000, IEFA $176,000, VWO $39,000, VGSH $38,000, MUB $318,000 | 10.4% | $174K | dead 10.1%, scaled |
| Castellano | sell LCV-I $250,000, ITOT $71,000, AGG $219,000, IEFA $22,000; buy VUG $143,000, IJH $98,000, VWO $72,000, VGSH $79,000 | 11.0% | $14K | dead 4.3%, not scaled |
| Okonkwo | buy VUG $1,225,000, SCHD $1,088,000, IJH $773,000, IEFA $229,000, VWO $545,000, VGSH $708,000, MUB $1,742,000 | 8.6% | $0 | "15.7% of target classes have no shelf fund…" |
| Brennan | sell BAL-C $90,000, LCG-A $58,000; buy SCHD $36,000, IJH $26,000, IEFA $42,000, VWO $13,000, VGSH $1,000, MUB $7,000 | 15.1% | $18K | scaled |

**Henderson, profile model at 100%:**
- sell VTI $5,603,000, AGG $5,100,000, MUB $1,242,000;
- buy SCHD $3,520,000, IJH $1,786,000, IEFA $1,626,000, VWO $422,000, VGSH $4,881,000;
- risk 9.5%, note "16.0% of target classes have no shelf fund…".

**Goal suggestions:**
- Henderson (return 6.5%): buy SCHD and IJH $2,374,000 each.
- Kaplan (loss no worse than 25% in the crisis): sell AAPL $573,000; buy AGG $315,000 and VGSH $258,000.
- Castellano: none (met).
- Okonkwo: buy VUG $2,227,000 and SCHD $2,226,000.
- Brennan (no objective, so return 7.5% is assumed): buy VEA $3,000 and SCHD $2,000.

**Concentration previews at defaults:**
- Henderson NVDA: sell $6,427,000; buy SCHD $2,498,000, IJH $1,280,000, VGSH $1,230,000.
- Kaplan AAPL: sell $1,648,000; buy SCHD $601,000, IJH $421,000, MUB $377,000.
- Brennan NVDA: sell $200,000; buy VEA $68,000, SCHD $59,000, IJH $42,000.

**A full Henderson walk-through:**
1. **Add the default risk alignment.** The panel reads:
   - Expected risk 9.5%;
   - Expected return 5.7%;
   - Sharpe 0.26;
   - TE 1.8%;
   - Income $1.10M;
   - Worst past event -29.7%;
   - Fund costs 2.5 bp;
   - Illustrative tax $114K, with gains $480K / $994K.

   All checks pass, and turnover is 22.0%. The why-risk sentence: "Expected risk rises from 9.2% to 9.5%, mainly because “Align 50% to the target” moves about 6% of the account from Fixed income into Cash and Equity (+0.3 pts). It stays inside the Moderate range."
2. **On Asset allocation gaps,** the default "Fill U.S. Large Cap Value" preview buys SCHD $4,627,000 (measured after step 1). Add it:
   - risk 10.8%, return 6.1%, worst -34.5%, income $1.12M;
   - the risk-band check fails ("Expected risk 10.8%");
   - why-risk names “Fill U.S. Large Cap Value” (+1.3 pts) and ends "It ends outside the Moderate range (8.3%–10.3%)."
3. **Add the default NVDA trim:**
   - risk 9.8%, return 6.0%, Sharpe 0.27, TE 1.2%, income $1.32M, worst -31.3%, costs 3.6 bp, tax $1.34M;
   - gains $5.63M fail the $994K budget;
   - turnover 34.9%;
   - the largest name becomes MSFT 9.9%;
   - the compare card reads "1 checks fail", and the goal lede reads "Return 6.5% a year: 5.6% today, 6.0% with Proposal A — Not yet met".
   - The talking points' second bullet is "Move your asset mix toward the target portfolio: sell $5.60M of VTI, $5.10M of AGG, $227K of MUB; invest $3.36M in SCHD, $1.66M in IJH, $1.67M in IEFA, $447K in VWO." (four buys at most).

**Other checks:**
- **Kaplan, adding the goal suggestion:** risk 9.4%, worst -29.6%, income $206K, tax $102K, gains $430K (fails the $174K budget).
- **Castellano, adding the stress suggestion:** risk 10.5% (still outside the band), worst -37.4%, tax $5,077.
- **The LCV picker for Henderson** lists 11 funds in this order: SCHD, VTV, LCV-I, DGRO, VOO, IVV, IDX-I, VNQ, VTI, ITOT, ESGV.
- **The Castellano downgrade cards** show "Tax to switch $4,500 saved" for CVS and "$4,900 saved" for PFE. Both are manager-decided.

---

## 7. Traps to avoid

**Fund choice and data:**
- **Two fund-choice rules** (section 3.5). Using one rule everywhere moves Henderson's international buys between VEA and IEFA and breaks the figures.
- **Holding-level data beats shelf data.** A held fund's event returns are more precise than the shelf record (VTI −47.3% in the bubble, against −47% on the shelf), and held stocks have their own yields. Castellano's manager-run stocks also have their own event returns. Buys copy the shelf record.

**Order and rounding:**
- **Shelf order matters** for every "first fund that qualifies" rule, and for the picker's tie order.
- **Rounding:** suggested trade amounts round to $1,000 at the points stated. Don't round KPI inputs.

**Measuring and attributing changes:**
- **Previews are marginal.** They are measured against the proposal's other changes, and the gap filler's shortfall is measured the same way.
- **Worst past event** on tiles, compare cards and talking points always uses today's worst event.
- **"Why it changes"** names the step with the largest effect but describes the whole proposal's net group shift. Keep that wording.
- **The deep dive gives every dimension the same amount,** and concentration reinvestment into gaps intentionally leaves part of the sale in cash.

**Cash and tax:**
- **Incoming cash** only enters the portfolio when stage-2 buys exist.
- **Lots without basis** are never sold, but they do count in "held directly" for concentration.
- **The gain budget in risk alignment** compares the stand-alone gain of a sale with the budget left, then searches for the largest added amount that fits.

**Defaults and interface:**
- **The stress treemap starts on Housing and financial crisis** for every household.
- **Tabs are lettered by position;** names are lettered by id.
- **Signs:** percentages use a hyphen for negatives; money and point changes use a true minus sign.
- **Don't add features.** There is no tour, no saving and no API. The only persistence is favourites.

---

## Appendix: data

All values are illustrative. Positions are as of 15 Oct 2026, and research and briefings as of 1 Oct 2026 unless stated. Tax rates for every household: taxable; long-term 23.8%; short-term 40.8%; federal bracket 37%.
**A. Asset classes.** Expected return and volatility, then the correlations in the order LCG, LCV, SMID, INTL, EM, UST, IGC, HY, CASH, HF, PE. Risk-free rate 3.3%.

| Class | Label | Group | Return | Vol | Correlations |
|---|---|---|---|---|---|
| LCG | U.S. Large Cap Growth | Equity | 6.6% | 17.5% | 1, 0.833, 0.82, 0.741, 0.675, −0.188, 0.162, 0.526, −0.005, 0.565, 0.656 |
| LCV | U.S. Large Cap Value | Equity | 7% | 15.5% | 0.833, 1, 0.807, 0.73, 0.668, −0.14, 0.215, 0.555, 0, 0.57, 0.65 |
| SMID | U.S. Small/Mid Cap | Equity | 7.6% | 20.5% | 0.82, 0.807, 1, 0.719, 0.666, −0.187, 0.189, 0.564, −0.005, 0.571, 0.648 |
| INTL | International Developed Equity | Equity | 7.4% | 17% | 0.741, 0.73, 0.719, 1, 0.596, −0.125, 0.195, 0.5, 0, 0.51, 0.58 |
| EM | Emerging Markets Equity | Equity | 8.2% | 22% | 0.675, 0.668, 0.666, 0.596, 1, −0.166, 0.174, 0.506, −0.005, 0.489, 0.546 |
| UST | U.S. Treasuries | Fixed income | 4.1% | 5.5% | −0.188, −0.14, −0.187, −0.125, −0.166, 1, 0.713, 0.077, 0.095, −0.058, −0.163 |
| IGC | U.S. Corporates (IG) | Fixed income | 4.9% | 7% | 0.162, 0.215, 0.189, 0.195, 0.174, 0.713, 1, 0.48, 0.08, 0.265, 0.17 |
| HY | U.S. High Yield | Fixed income | 6.1% | 9.5% | 0.526, 0.555, 0.564, 0.5, 0.506, 0.077, 0.48, 1, 0.02, 0.52, 0.495 |
| CASH | Cash | Cash | 3.3% | 0.6% | −0.005, 0, −0.005, 0, −0.005, 0.095, 0.08, 0.02, 1, 0.005, −0.005 |
| HF | Hedge Funds | Alternatives | 5.8% | 7.5% | 0.565, 0.57, 0.571, 0.51, 0.489, −0.058, 0.265, 0.52, 0.005, 1, 0.477 |
| PE | Private Equity | Alternatives | 9.6% | 23% | 0.656, 0.65, 0.648, 0.58, 0.546, −0.163, 0.17, 0.495, −0.005, 0.477, 1 |

**B. Past events** (in this order, used for every "event returns" list below):

- dotcom: Technology bubble (24 Mar 2000 to 9 Oct 2002)
- gfc: Housing and financial crisis (9 Oct 2007 to 9 Mar 2009)
- covid: COVID disruption (19 Feb 2020 to 23 Mar 2020)
- y2022: 2022 rate shock (Calendar year 2022)

**Sectors and benchmark weights** (share of equity):

- TECH: Information Technology, benchmark 27%
- COMM: Communication Services, benchmark 8%
- DISC: Consumer Discretionary, benchmark 11%
- FIN: Financials, benchmark 17%
- HLTH: Health Care, benchmark 9%
- INDU: Industrials, benchmark 11%
- STAP: Consumer Staples, benchmark 6%
- ENER: Energy, benchmark 4%
- UTIL: Utilities, benchmark 2.5%
- REAL: Real Estate, benchmark 2%
- MATL: Materials, benchmark 3.5%

**C. Fund shelf, in order.** Columns:

- symbol and name;
- type (ETF or mutual fund);
- class mix;
- cost in bp;
- yield;
- research view ("no report" means there is no report object);
- holdings count and top-10 share;
- event returns (bubble / crisis / covid / 2022);
- look-through template references: top holdings T, sectors S, style box B.

| Fund | Name | Type | Classes | Cost | Yield | View | Holdings · top 10 | Event returns | T · S · B |
|---|---|---|---|---|---|---|---|---|---|
| VTI | US Total Market ETF | ETF | LCG 45%, LCV 45%, SMID 10% | 3 | 1.2% | Recommended | 3,600 · 31% | −47% / −55% / −34% / −18% | T1 · S1 · B1 |
| ITOT | Core S&P Total US Stock ETF | ETF | LCG 45%, LCV 45%, SMID 10% | 3 | 1.2% | Recommended | 2,500 · 33% | −47% / −55% / −34% / −18% | T1 · S1 · B1 |
| VOO | S&P 500 ETF | ETF | LCG 50%, LCV 50% | 3 | 1.2% | Recommended | 503 · 37% | −47% / −55% / −34% / −18% | T2 · S1 · B2 |
| IVV | Core S&P 500 ETF | ETF | LCG 50%, LCV 50% | 3 | 1.2% | no report | 503 · 37% | −47% / −55% / −34% / −18% | T2 · S1 · B2 |
| IDX-I | S&P 500 Index Fund, institutional class | mutual fund | LCG 50%, LCV 50% | 4 | 1.2% | Recommended | 503 · 37% | −47% / −55% / −34% / −18% | T2 · S1 · B2 |
| ESGV | ESG US Equity ETF | ETF | LCG 50%, LCV 40%, SMID 10% | 9 | 1% | Neutral | 1,400 · 36% | −50% / −56% / −33% / −22% | T1 · S1 · B1 |
| QQQ | Nasdaq-100 ETF | ETF | LCG 100% | 20 | 0.6% | Neutral | 101 · 52% | −62% / −52% / −31% / −26% | T3 · S2 · B3 |
| VGT | Info Tech ETF | ETF | LCG 100% | 9 | 0.5% | Neutral | 320 · 60% | −80% / −53% / −30% / −28% | T4 · S3 · B3 |
| ARKK | Innovation ETF | ETF | LCG 60%, SMID 40% | 75 | 0% | Not recommended | 35 · 62% | −50% / −54% / −32% / −23% | — · — · — |
| VUG | Growth ETF | ETF | LCG 100% | 4 | 0.5% | Recommended | 170 · 60% | −60% / −54% / −32% / −27% | T4 · S2 · B3 |
| SCHG | US Large-Cap Growth ETF | ETF | LCG 100% | 4 | 0.4% | no report | 230 · 58% | −60% / −54% / −32% / −27% | T4 · S2 · B3 |
| LCG-A | Large-Cap Growth Fund, Class A (front-end load) | mutual fund | LCG 100% | 95 | 0.1% | Neutral | 70 · 55% | −60% / −54% / −32% / −27% | T5 · S2 · B3 |
| SCHD | US Dividend Equity ETF | ETF | LCV 100% | 6 | 3.7% | Recommended | 100 · 41% | −28% / −50% / −37% / 3% | T6 · S4 · B4 |
| DGRO | Core Dividend Growth ETF | ETF | LCV 70%, LCG 30% | 8 | 2.2% | no report | 410 · 27% | −35% / −54% / −35% / −8% | T7 · S5 · B5 |
| VTV | Value ETF | ETF | LCV 100% | 4 | 2.3% | Recommended | 330 · 22% | −30% / −56% / −37% / −5% | T7 · S5 · B5 |
| LCV-I | US Large Cap Value Fund (Institutional shares) | mutual fund | LCV 100% | 55 | 2% | Recommended | 90 · 30% | −30% / −56% / −37% / −5% | T7 · S5 · B5 |
| IJH | Core S&P Mid-Cap ETF | ETF | SMID 100% | 5 | 1.4% | Recommended | 400 · 7% | −29% / −59% / −38% / −12% | — · S6 · B6 |
| VXUS | Total International Stock ETF | ETF | INTL 75%, EM 25% | 5 | 2.9% | Recommended | 8,500 · 10% | −47% / −61% / −33% / −16% | — · S7 · B7 |
| VEA | Developed Markets ETF | ETF | INTL 100% | 3 | 3% | Recommended | 3,900 · 11% | −48% / −61% / −33% / −14% | — · S7 · B7 |
| IEFA | Core MSCI EAFE ETF | ETF | INTL 100% | 7 | 3% | Recommended | 2,700 · 12% | −48% / −61% / −33% / −14% | — · S7 · B7 |
| VWO | Emerging Markets ETF | ETF | EM 100% | 7 | 3% | Recommended | 5,900 · 20% | −45% / −61% / −31% / −20% | — · S8 · B8 |
| IEMG | Core MSCI Emerging Markets ETF | ETF | EM 100% | 9 | 2.8% | Recommended | 2,900 · 22% | −45% / −61% / −31% / −20% | — · S8 · B8 |
| VNQ | Real Estate ETF | ETF | LCV 50%, SMID 50% | 13 | 3.8% | Neutral | 155 · 47% | 35% / −70% / −41% / −26% | — · S9 · B9 |
| BAL-C | Balanced Income Fund, Class C (12b-1 fee) | mutual fund | LCG 30%, LCV 30%, UST 12%, IGC 16%, HY 12% | 170 | 2.5% | Not recommended | 400 · 25% | −22% / −35% / −24% / −16% | T8 · S1 · B2 |
| AGG | US Aggregate Bond ETF | ETF | UST 60%, IGC 40% | 3 | 4.1% | Recommended | 12,000 · — | 28% / 7% / −1% / −14% | — · — · — |
| BND | US Bond Market ETF | ETF | UST 60%, IGC 40% | 3 | 4.1% | Recommended | 11,000 · — | 28% / 7% / −1% / −14% | — · — · — |
| LQD | Investment Grade Corporate Bond ETF | ETF | IGC 100% | 14 | 5% | Neutral | 2,900 · — | 24% / −3% / −9% / −16% | — · — · — |
| VGSH | Short-Term Treasury ETF | ETF | UST 100% | 4 | 3.9% | Recommended | 95 · — | 30% / 14% / 5% / −12% | — · — · — |
| MUB | National Muni Bond ETF | ETF | IGC 100% | 5 | 3.1% | Recommended | 6,000 · — | 22% / 1% / −9% / −9% | — · — · — |
| VTEB | Tax-Exempt Bond ETF | ETF | IGC 100% | 3 | 3.1% | Recommended | 9,000 · — | 22% / 1% / −9% / −9% | — · — · — |

**Look-through templates.** A dash in the table above means the fund has none: no top holdings, no sectors or no style data.

*Top holdings (share of the fund):*

- **T1** (VTI, ITOT, ESGV): NVDA 6.4%, MSFT 5.7%, AAPL 5.6%, AMZN 3.4%, GOOG 3.3%, META 2.5%, AVGO 2.1%, TSLA 1.8%, JPM 1.3%, COST 0.9%, UNH 0.7%, JNJ 0.7%, PG 0.7%, HD 0.7%
- **T2** (VOO, IVV, IDX-I): NVDA 7.5%, MSFT 6.7%, AAPL 6.6%, AMZN 4%, GOOG 3.9%, META 2.9%, AVGO 2.5%, TSLA 2.1%, JPM 1.5%, COST 1%, UNH 0.8%, JNJ 0.8%, PG 0.8%, HD 0.8%
- **T3** (QQQ): NVDA 9.5%, MSFT 8.5%, AAPL 8%, AMZN 5.5%, GOOG 5.3%, AVGO 5%, META 3.8%, TSLA 3%, COST 2.5%
- **T4** (VGT, VUG, SCHG): NVDA 12%, MSFT 11%, AAPL 11%, AMZN 6.5%, GOOG 6%, META 4.5%, AVGO 4%, TSLA 3.5%, COST 1.5%
- **T5** (LCG-A): MSFT 9%, NVDA 8%, AAPL 7%, AMZN 6%, GOOG 5%, META 4%
- **T6** (SCHD): CVX 4.2%, KO 4.1%, PFE 4%, HD 4%
- **T7** (DGRO, VTV, LCV-I): JPM 3.5%, JNJ 2.2%, PG 2%, HD 2%, CVX 1.6%, UNH 1.5%, KO 1.3%, PFE 1%, CVS 0.6%, INTC 0.6%
- **T8** (BAL-C): NVDA 4.5%, MSFT 4.02%, AAPL 3.96%, AMZN 2.4%, GOOG 2.34%, META 1.74%, AVGO 1.5%, TSLA 1.26%, JPM 0.9%, COST 0.6%, UNH 0.48%, JNJ 0.48%, PG 0.48%, HD 0.48%

*Sector mix:*

- **S1** (VTI, ITOT, VOO, IVV, IDX-I, ESGV, BAL-C): TECH 33%, FIN 13%, DISC 10.5%, COMM 10%, HLTH 9%, INDU 8.5%, STAP 5%, ENER 3%, UTIL 2.5%, REAL 2%, MATL 2%
- **S2** (QQQ, VUG, SCHG, LCG-A): TECH 50%, DISC 17%, COMM 13%, HLTH 6%, INDU 5%, FIN 5%, STAP 2%, MATL 1%, REAL 1%
- **S3** (VGT): TECH 100%
- **S4** (SCHD): ENER 19%, STAP 19%, HLTH 16%, INDU 12%, FIN 9%, TECH 9%, DISC 8%, COMM 4%, MATL 3%, UTIL 1%
- **S5** (DGRO, VTV, LCV-I): FIN 23%, HLTH 16%, INDU 14%, TECH 10%, STAP 9%, ENER 8%, UTIL 5%, DISC 5%, COMM 4%, MATL 4%, REAL 2%
- **S6** (IJH): INDU 20%, FIN 17%, DISC 14%, TECH 11%, HLTH 9%, REAL 8%, MATL 6%, STAP 5%, ENER 5%, UTIL 3%, COMM 2%
- **S7** (VXUS, VEA, IEFA): FIN 22%, INDU 17%, TECH 11%, DISC 10%, HLTH 9%, STAP 7%, MATL 7%, COMM 5%, ENER 5%, UTIL 3%, REAL 3%
- **S8** (VWO, IEMG): TECH 24%, FIN 23%, DISC 13%, COMM 9%, MATL 7%, INDU 7%
- **S9** (VNQ): REAL 100%

*Style box (LV, LB, LG, MV, MB, MG, SV, SB, SG):*

- **B1** (VTI, ITOT, ESGV): LV 30%, LB 30%, LG 30%, MB 6%, SB 4%
- **B2** (VOO, IVV, IDX-I, BAL-C): LV 32%, LB 33%, LG 35%
- **B3** (QQQ, VGT, VUG, SCHG, LCG-A): LG 85%, LB 10%, MG 5%
- **B4** (SCHD): LV 70%, LB 20%, MV 10%
- **B5** (DGRO, VTV, LCV-I): LV 80%, LB 15%, MV 5%
- **B6** (IJH): MV 35%, MB 35%, MG 30%
- **B7** (VXUS, VEA, IEFA): LV 35%, LB 35%, LG 20%, MB 10%
- **B8** (VWO, IEMG): LV 30%, LB 30%, LG 25%, MB 15%
- **B9** (VNQ): LV 40%, MV 60%

**Research reports.** Every fund with a view other than "no report" carries a report with:

- the date 2026-10-01;
- the view;
- the summary "Illustrative research: {fund name} offers exposure to its stated mandate; review fit, concentration, liquidity and costs.";
- strengths "Transparent asset-class exposure; Documented implementation approach";
- risk "Market conditions and portfolio concentrations can change results.".

IVV, SCHG and DGRO have no report.

**D. Stocks on the shelf**, in order. Every shelf stock has:

- 100% in the class shown;
- the matching single style cell (LG for growth, LV for value);
- event returns −80% / −53% / −30% / −28%;
- a yield of 1% (META 0%);
- cost 0 bp (META and AVGO have no cost field, so their cards show "—").

| Stock | Name | Sector | Class |
|---|---|---|---|
| NVDA | NVIDIA Corp | TECH | LCG |
| MSFT | Microsoft Corp | TECH | LCG |
| AAPL | Apple Inc | TECH | LCG |
| AMZN | Amazon.com Inc | DISC | LCG |
| GOOG | Alphabet Inc | COMM | LCG |
| TSLA | Tesla Inc | DISC | LCG |
| COST | Costco Wholesale Corp | STAP | LCG |
| JPM | JPMorgan Chase | FIN | LCV |
| PFE | Pfizer Inc | HLTH | LCV |
| CVX | Chevron Corp | ENER | LCV |
| CVS | CVS Health | HLTH | LCV |
| JNJ | Johnson & Johnson | HLTH | LCV |
| PG | Procter & Gamble | STAP | LCV |
| KO | Coca-Cola Co | STAP | LCV |
| UNH | UnitedHealth Group | HLTH | LCV |
| HD | Home Depot | DISC | LCV |
| INTC | Intel Corp | TECH | LCV |
| TXN | Texas Instruments | TECH | LCV |
| QCOM | Qualcomm Inc | TECH | LCV |
| ADI | Analog Devices | TECH | LCV |
| MRK | Merck & Co | HLTH | LCV |
| ABBV | AbbVie Inc | HLTH | LCV |
| CI | Cigna Group | HLTH | LCV |
| ELV | Elevance Health | HLTH | LCV |
| BKNG | Booking Holdings | DISC | LCG |
| LOW | Lowe's Companies | DISC | LCV |
| META | Meta Platforms | COMM | LCG |
| AVGO | Broadcom | TECH | LCG |

**E. Households,** in this order. Every household has the same limits: single stock 10%, single fund 25%, turnover 40%.

**Henderson Family Trust** (id `henderson`)

- **Profile:** Moderate; tier and model name "CIO Moderate, Tier 2"; risk band 8.26%–10.35%.
- **Gain budget:** $994,000. **Below-investment-grade limit:** 8%.
- **Next meeting:** "in 2 days, Annual review".
- **Incoming cash:** $5,000,000 on 2026-11-15.
- **Objectives on file:** return 6.5% a year; loss no worse than 30% in Housing and financial crisis.
- **Target allocation:** LCG 16.61%, LCV 16.61%, SMID 6.88%, INTL 11.46%, EM 3.44%, UST 11.57%, IGC 13.29%, HY 5.14%, CASH 5%, HF 5%, PE 5%.
- **Profile model:** LCG 14.5%, LCV 14.5%, SMID 6%, INTL 10%, EM 3%, UST 13.5%, IGC 15.5%, HY 6%, CASH 7%, HF 5%, PE 5%.
- **Target allocation's event returns:** −19% / −34.1% / −21.7% / −12.2%.

| Holding | Type | Value | Yield | Tradable | Lots (basis → value, term) | Event returns | Notes |
|---|---|---|---|---|---|---|---|
| NVDA | stock | $10,600,000 | 0.03% (own) | yes | Lot 1: $2,100,000 → $10,600,000, LT | as shelf |  |
| MSFT | stock | $4,900,000 | 0.7% (own) | yes | Lot 1: $2,400,000 → $4,900,000, LT | as shelf |  |
| VTI | ETF | $6,200,000 | 1.2% | yes | Lot 1: $5,100,000 → $6,200,000, LT | −47.3% / −55.1% / −34% / −18.2% |  |
| MUB | ETF | $9,800,000 | 3.1% | yes | Lot 1: $10,400,000 → $9,800,000, LT | 22% / 1% / −9% / −8.5% |  |
| AGG | ETF | $5,100,000 | 4.1% | yes | Lot 1: $5,600,000 → $5,100,000, LT | 27.6% / 7.2% / −0.6% / −13.8% |  |
| VXUS | ETF | $4,300,000 | 2.9% | yes | Lot 1: $4,900,000 → $4,300,000, LT | −47.2% / −61% / −32.5% / −15.5% |  |
| CASH · Sweep / T-Bills | cash (CASH 100%) | $7,300,000 | 3.4% | no | Lot 1: $7,300,000 → $7,300,000, LT | 10% / 2% / 0.3% / 1.5% |  |
| AUSTIN-4.0-32 · City of Austin GO 4.0% 2032 | bond (IGC 100%) | $1,100,000 | 3.4% | no | Lot 1: $1,080,000 → $1,100,000, LT | 22% / 1% / −9% / −8.5% | Individual bond or CD: held to maturity |
| NVDA | stock | $400,000 | 0.03% (own) | yes | Lot 1: no basis → $400,000, LT | as shelf |  |

**Kaplan Household** (id `kaplan`)

- **Profile:** Moderate; tier and model name "CIO Moderate, Tier 2"; risk band 8.26%–10.35%.
- **Gain budget:** $174,000. **Below-investment-grade limit:** 8%.
- **Next meeting:** "in 1 days, Retirement planning".
- **Incoming cash:** none.
- **Objectives on file:** loss no worse than 25% in Housing and financial crisis.
- **Target allocation:** LCG 18.12%, LCV 18.12%, SMID 7.5%, INTL 12.5%, EM 3.75%, UST 11.57%, IGC 13.29%, HY 5.14%, CASH 5%, HF 2.5%, PE 2.5%.
- **Profile model:** LCG 14.5%, LCV 14.5%, SMID 6%, INTL 10%, EM 3%, UST 13.5%, IGC 15.5%, HY 6%, CASH 7%, HF 5%, PE 5%.
- **Target allocation's event returns:** −20.4% / −35.5% / −22.8% / −12.6%.

| Holding | Type | Value | Yield | Tradable | Lots (basis → value, term) | Event returns | Notes |
|---|---|---|---|---|---|---|---|
| AAPL | stock | $2,400,000 | 0.4% (own) | yes | Lot 1: $600,000 → $2,400,000, LT | as shelf |  |
| VTI | ETF | $2,100,000 | 1.2% | yes | Lot 1: $1,700,000 → $2,100,000, LT | −47.3% / −55.1% / −34% / −18.2% |  |
| VXUS | ETF | $1,100,000 | 2.9% | yes | Lot 1: $1,200,000 → $1,100,000, LT | −47.2% / −61% / −32.5% / −15.5% |  |
| BND | ETF | $1,900,000 | 4.1% | yes | Lot 1: $2,000,000 → $1,900,000, LT | 27.6% / 7.2% / −0.6% / −13.8% |  |
| CASH · Sweep / T-Bills | cash (CASH 100%) | $1,200,000 | 3.4% | no | Lot 1: $1,200,000 → $1,200,000, LT | 10% / 2% / 0.3% / 1.5% |  |

**Castellano Family** (id `castellano`)

- **Profile:** Moderate; tier and model name "CIO Moderate, Tier 2"; risk band 8.26%–10.35%.
- **Gain budget:** $64,000. **Below-investment-grade limit:** 8%.
- **Next meeting:** "in 5 days, Tax strategy review".
- **Incoming cash:** none.
- **Objectives on file:** income $75,000 a year.
- **Target allocation:** LCG 21.15%, LCV 21.15%, SMID 8.75%, INTL 14.58%, EM 4.38%, UST 9.64%, IGC 11.07%, HY 4.29%, CASH 5%, HF 0%, PE 0%.
- **Profile model:** LCG 14.5%, LCV 14.5%, SMID 6%, INTL 10%, EM 3%, UST 13.5%, IGC 15.5%, HY 6%, CASH 7%, HF 5%, PE 5%.
- **Target allocation's event returns:** −25% / −39.7% / −25.4% / −13.3%.

| Holding | Type | Value | Yield | Tradable | Lots (basis → value, term) | Event returns | Notes |
|---|---|---|---|---|---|---|---|
| ITOT | ETF | $900,000 | 1.2% | yes | Lot 1: $500,000 → $600,000, LT; Lot 2: $290,000 → $300,000, ST | −47.3% / −55.1% / −34% / −18.2% |  |
| IEFA | ETF | $520,000 | 3% | yes | Lot 1: $360,000 → $320,000, LT; Lot 2: $206,000 → $200,000, LT | as shelf |  |
| JPM | stock | $260,000 | 2.1% (own) | no | Lot 1: $64,000 → $104,000, LT; Lot 2: $70,000 → $65,000, LT; Lot 3: $48,000 → $52,000, LT; Lot 4: $38,000 → $39,000, ST | −20% / −80% / −43% / −10.5% | Manager-run: traded by Crestline Large Cap Value SMA |
| PFE | stock | $120,000 | 6.5% (own) | no | Lot 1: $93,000 → $75,000, LT; Lot 2: $46,000 → $45,000, ST | −25% / −38% / −28% / −2% | Manager-run: traded by Crestline Large Cap Value SMA |
| CVX | stock | $140,000 | 4.5% (own) | no | Lot 1: $128,000 → $140,000, LT | −25% / −53% / −57% / 66% | Manager-run: traded by Crestline Large Cap Value SMA |
| CVS | stock | $80,000 | 4.2% (own) | no | Lot 1: $99,000 → $80,000, LT | −25% / −38% / −28% / −2% | Manager-run: traded by Crestline Large Cap Value SMA |
| LCV-I | mutual fund | $250,000 | 2% | yes | Lot 1: $236,000 → $250,000, LT | −29.9% / −56.1% / −37% / −5.4% |  |
| NYSDA-5.0-34 · NY State Dormitory Authority 5.0% 2034 | bond (IGC 100%) | $450,000 | 3.5% | no | Lot 1: $462,000 → $450,000, LT | 22% / 1% / −9% / −8.5% | Individual bond or CD: held to maturity |
| AGG | ETF | $320,000 | 4.1% | yes | Lot 1: $333,000 → $320,000, LT | 27.6% / 7.2% / −0.6% / −13.8% |  |
| CASH · Sweep / T-Bills | cash (CASH 100%) | $160,000 | 3.4% | no | Lot 1: $160,000 → $160,000, LT | 10% / 2% / 0.3% / 1.5% |  |

**Okonkwo Holdings LLC** (id `okonkwo`)

- **Profile:** Moderately Aggressive; tier and model name "CIO Moderately Aggressive, Tier 2"; risk band 10.35%–12.53%.
- **Gain budget:** $632,000. **Below-investment-grade limit:** 10%.
- **Next meeting:** "in 6 days, Liquidity deployment".
- **Incoming cash:** none.
- **Objectives on file:** return 6.5% a year.
- **Target allocation:** LCG 15.48%, LCV 14.68%, SMID 6.35%, INTL 10.32%, EM 3.17%, UST 8.52%, IGC 10.8%, HY 5.68%, CASH 5%, HF 10%, PE 10%.
- **Profile model:** LCG 19.5%, LCV 18.5%, SMID 8%, INTL 13%, EM 4%, UST 7.5%, IGC 9.5%, HY 5%, CASH 5%, HF 5%, PE 5%.
- **Target allocation's event returns:** −19.9% / −34.9% / −21.3% / −11.7%.

| Holding | Type | Value | Yield | Tradable | Lots (basis → value, term) | Event returns | Notes |
|---|---|---|---|---|---|---|---|
| CASH · Sweep / T-Bills | cash (CASH 100%) | $14,200,000 | 3.4% | no | Lot 1: $14,200,000 → $14,200,000, LT | 10% / 2% / 0.3% / 1.5% |  |
| VTI | ETF | $6,400,000 | 1.2% | yes | Lot 1: $5,900,000 → $6,400,000, LT | −47.3% / −55.1% / −34% / −18.2% |  |
| IEFA | ETF | $3,100,000 | 3% | yes | Lot 1: $3,000,000 → $3,100,000, LT | as shelf |  |
| AGG | ETF | $4,700,000 | 4.1% | yes | Lot 1: $4,800,000 → $4,700,000, LT | 27.6% / 7.2% / −0.6% / −13.8% |  |
| PRIV · Private RE Interest | private (PE 100%) | $3,200,000 | 3% | no | Lot 1: $3,000,000 → $3,200,000, LT | −35% / −40% / −15% / −10% | Private real estate interest; no redemption right |

**Brennan Household** (id `brennan`)

- **Profile:** Aggressive; tier and model name "CIO Aggressive, Tier 1"; risk band 12.47%–14.7%.
- **Gain budget:** $18,000. **Below-investment-grade limit:** 12%.
- **Next meeting:** "in 6 days, Advisory proposal".
- **Incoming cash:** none.
- **Objectives on file:** none.
- **Target allocation:** LCG 27.65%, LCV 25.6%, SMID 10.24%, INTL 16.39%, EM 5.12%, UST 1.67%, IGC 3.89%, HY 4.44%, CASH 5%, HF 0%, PE 0%.
- **Profile model:** LCG 27%, LCV 25%, SMID 10%, INTL 16%, EM 5%, UST 1.5%, IGC 3.5%, HY 4%, CASH 3%, HF 5%, PE 0%.
- **Target allocation's event returns:** −35.9% / −49.4% / −30.3% / −14.3%.

| Holding | Type | Value | Yield | Tradable | Lots (basis → value, term) | Event returns | Notes |
|---|---|---|---|---|---|---|---|
| LCG-A | mutual fund | $180,000 | 0.1% | yes | Lot 1: $140,000 → $180,000, LT | −59.9% / −53.9% / −31.9% / −26.8% |  |
| BAL-C | mutual fund | $90,000 | 2.5% | yes | Lot 1: $85,000 → $90,000, LT | −21.9% / −35.5% / −23.7% / −16.3% |  |
| IDX-I | mutual fund | $150,000 | 1.2% | yes | Lot 1: $110,000 → $150,000, LT | −47.3% / −55.1% / −34% / −18.2% |  |
| NVDA | stock | $260,000 | 0.03% (own) | yes | Lot 1: $45,000 → $260,000, LT | as shelf |  |
| AAPL | stock | $110,000 | 0.4% (own) | yes | Lot 1: $70,000 → $110,000, LT | as shelf |  |
| PRIV-SERIESB · Private placement, Series B preferred (startup) | private (PE 100%) | $60,000 | 0% | no | Lot 1: $25,000 → $60,000, LT | −35% / −40% / −15% / −10% | Restricted private placement |
| MMF · Government money market fund | cash (CASH 100%) | $30,000 | 3.6% | no | Lot 1: $30,000 → $30,000, LT | 10% / 2% / 0.3% / 1.5% |  |
| CASH · Sweep / T-Bills | cash (CASH 100%) | $20,000 | 3.4% | no | Lot 1: $20,000 → $20,000, LT | 10% / 2% / 0.3% / 1.5% |  |

**Holdings and the shelf:**

- A held fund or stock copies its shelf record (classes, cost, look-through, report), except for the yield marked "(own)" and the event returns listed.
- A held fund carries its report, but no separate view field.
- Holdings that are not on the shelf (cash, bonds, private interests) carry only what is listed.
- Henderson holds NVDA twice. The second holding is $400,000 with no cost basis.
- Notes are kept in the data but not shown on screen.

**F. Research downgrades** (the reason text is shown on the card):

- **UNH · UnitedHealth Group**: Buy → Underperform on 2026-10-13. "Higher medical cost ratios and a widening regulatory review; estimates cut for 2026 and 2027."
  - Holder: Okoye household (id `okoye`); position $110,000; 11.2% of account; tax to switch −$2,400; decides "Manager (Beacon Hill Appreciation SMA)".
  - Alternatives, in order: ELV Elevance Health (Buy, Large value, beta 1.00, yield 1%); ABBV AbbVie Inc (Buy, Large value, beta 1.00, yield 1%); CI Cigna Group (Buy, Large value, beta 1.00, yield 1%); VTV Value ETF (fund, Large value, beta 1.00, yield 2.3%).
- **CVS · CVS Health**: Buy → Neutral on 2026-10-09. "Cost trends in its insurance business are running above guidance."
  - Holder: Castellano Family (id `castellano`); position $80,000; 2.5% of account; tax to switch −$4,500; decides "Manager (Crestline Large Cap Value SMA)".
  - Alternatives, in order: CI Cigna Group (Buy, Large value, beta 1.00, yield 1%); JNJ Johnson & Johnson (Buy, Large value, beta 1.00, yield 1%); MRK Merck & Co (Buy, Large value, beta 1.00, yield 1%); VTV Value ETF (fund, Large value, beta 1.00, yield 2.3%).
- **INTC · Intel Corp**: Neutral → Underperform on 2026-10-02. "Foundry customer wins slower than planned, while capital spending pressure persists."
  - Holder: Ashford household (id `ashford`); position $100,000; 2.3% of account; tax to switch −$11,900; decides "Manager (Ashcroft Large Cap Core SMA)".
  - Alternatives, in order: ADI Analog Devices (Buy, Large value, beta 1.00, yield 1%); NVDA NVIDIA Corp (Buy, Large growth, beta 1.00, yield 1%); QCOM Qualcomm Inc (Buy, Large value, beta 1.00, yield 1%); VTV Value ETF (fund, Large value, beta 1.00, yield 2.3%).
- **PFE · Pfizer Inc**: Buy → Neutral on 2026-09-29. "Two late-stage readouts missed; 2027 earnings estimates decline."
  - Holder: Castellano Family (id `castellano`); position $120,000; 3.7% of account; tax to switch −$4,900; decides "Manager (Crestline Large Cap Value SMA)".
  - Holder: Ashford household (id `ashford`); position $140,000; 3.3% of account; tax to switch −$9,500; decides "Manager (Ashcroft Large Cap Core SMA)".
  - Alternatives, in order: JNJ Johnson & Johnson (Buy, Large value, beta 1.00, yield 1%); MRK Merck & Co (Buy, Large value, beta 1.00, yield 1%); ABBV AbbVie Inc (Buy, Large value, beta 1.00, yield 1%); VTV Value ETF (fund, Large value, beta 1.00, yield 2.3%).
- **TSLA · Tesla Inc**: Neutral → Underperform on 2026-09-24. "Delivery growth slows while valuation assumes later autonomy revenue."
  - Holder: Reyes household (id `reyes`); position $1,100,000; 8.9% of account; tax to switch −$95,200; decides "Advisor".
  - Alternatives, in order: AMZN Amazon.com Inc (Buy, Large growth, beta 1.00, yield 1%); BKNG Booking Holdings (Buy, Large growth, beta 1.00, yield 1%); LOW Lowe's Companies (Buy, Large value, beta 1.00, yield 1%); VUG Growth ETF (fund, Large growth, beta 1.00, yield 0.5%).

Only CVS and PFE are held by one of the five households (Castellano). The other holders are named for context only.

**G. Manager briefings,** each dated 2026-10-01:

- Summary for all: "Illustrative positioning review across valuation, diversification and risk."
- Positioning for all: "Evaluate mandate fit, liquidity and concentration relative to the client objective."

- **Northbridge Capital**: "US Small/Mid Cap: Q3 2026 manager briefing"; covers SMID.
- **Sterling Oak Investment Management**: "International Developed: Q3 2026 manager briefing"; covers INTL.
- **Cobalt Ridge Partners**: "Emerging Markets: Q3 2026 manager briefing"; covers EM.
- **Crestline Asset Partners**: "US Large Cap Value: Q3 2026 manager briefing"; covers LCV.
- **Beacon Hill Capital Management**: "US Large Cap Growth: Q3 2026 manager briefing"; covers LCG.
- **Ashcroft Investment Group**: "US Large Cap Core: Q3 2026 manager briefing"; covers LCG, LCV.
- **Highland Peak Advisors**: "US Dividend Equity: Q3 2026 manager briefing"; covers LCV.
- **Fairview Street Capital**: "Core Fixed Income: Q3 2026 manager briefing"; covers UST, IGC.
- **Marlowe Bay Advisors**: "Municipal Fixed Income: Q3 2026 manager briefing"; covers IGC.
- **Anchor Point Capital**: "Short Duration Income: Q3 2026 manager briefing"; covers UST, CASH.

**H. Disclosures,** word for word:

- **history**: "Historical stress results apply rounded, approximate index moves from past events to today’s holdings. They are illustrative, are not a forecast, and do not include fees, rebalancing or the path within each window. Individual securities, especially single stocks, can fall much further than their sector or asset class did. Past performance does not guarantee future results."
- **tax**: "Tax figures are illustrative estimates from cost basis on file and the rates shown; they are not tax advice. Lots without cost basis are excluded. Confirm with the client’s tax advisor before trading."
- **research**: "Research ratings, fund reports and manager briefings shown are illustrative demo content. Alternatives are surfaced for advisor consideration, not as recommendations to the client."

**I. Other constants:**

- The positions date shown is "15 Oct 2026".
- Default favourites: VTV, IJH, IEFA, SCHD, AGG, MUB, VGSH.
- Broad index funds exempt from the 25% single-fund flag: ITOT, VTI, VOO, IVV, IDX-I.
- Sector fallback benchmark: 10%.
- Gain-budget meter: gains ÷ budget.
- Cash created by a proposal: symbol CASH, yield 4%, if the household has no CASH holding (all five do).
