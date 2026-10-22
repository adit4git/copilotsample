# Portfolio Review: features, with screenshots

Screenshots are from the latest standalone Portfolio Review page (`atlas-portfolio-review.html`, 22 Oct 2026 build), including the downgrade updates.
- **Data:** illustrative; positions as of 15 Oct 2026; business date 16 Oct 2026.
- **Book:** advisor Dana Whitfield, 22 households.
- **Figures:** every amount and tax figure is illustrative and for the advisor's review. Nothing places a trade.

Portfolio Review works one household at a time. Next-best actions across the book stay in Today.

## Contents

1. [Action plan](#1-action-plan)
2. [Actions and the health check](#2-actions-and-the-health-check)
3. [Household proposals](#3-household-proposals)
4. [The decision drawer](#4-the-decision-drawer)
5. [Guarded decisions and the decision log](#5-guarded-decisions-and-the-decision-log)
6. [Downgrades](#6-downgrades)
7. [Special cases](#7-special-cases)
8. [Full analysis](#8-full-analysis)
9. [Ask Atlas](#9-ask-atlas)
10. [Guided tour](#10-guided-tour)
11. [Phone layout](#11-phone-layout)

---

## 1. Action plan

Choose a household, then the section. Under the household picker, "Recent downgrades held" opens any household that holds a recently downgraded stock (see [Downgrades](#6-downgrades)). The tabs come in two groups:
- **Decide:** the Action plan;
- **Full analysis:** the six analyses behind it.

The plan opens with:
- a one-sentence assessment;
- three key figures;
- a line naming the recommended household proposal, with a link to it;
- the next meeting;
- the data line, showing how current each feed is.

![Action plan](images/01-action-plan.png)
*Henderson Family Trust. The recommended proposal is named at the top: sales of $18.3M, $237K of tax, risk 9.1%.*

## 2. Actions and the health check

The findings from all six analyses become one ranked list of actions:
- a stock and the sector it drives are one action;
- the rebalance, the gap fill, the cash plan and the deep dive's ideas are one allocation action.

Each action shows:
- its **category:** risk resolution, economic benefit, planning conversation or information required;
- its **due date**;
- its **data readiness** or decision status;
- **this year's stage**;
- the **kind of next step**, and who owns it.

The seven health checks sit just above the list and work as filters. Each check shows how many actions it has; checks with none can't be clicked.

![Actions and health check](images/02-actions-health-check.png)
*Eight actions for Henderson, ranked. Missing cost basis appears as its own "Information required" action, owned by client service.*

![Health check filter](images/03-health-check-filter.png)
*Concentration is selected: "Showing 2 of 8 actions". "Show all 8" clears the filter.*

## 3. Household proposals

Every trade action is reconciled into one trade list per proposal. Each proposal plays its steps in order in the portfolio engine, on the holdings the previous step left, so nothing is sold twice and the gain budget is shared:
1. trims;
2. tax swaps;
3. rebalance;
4. stress changes, re-run on the result.

**Statuses.** Each proposal is one of:
- executable and within policy limits;
- outside a policy limit;
- over this year's gain budget;
- not executable as is.

Only a proposal that passes every check can be recommended. Suitability stays the advisor's determination.

**The unreconciled sum.** The total of the separate plans is a folded diagnostic, not an option.

![Household proposals](images/04-household-proposals.png)
*"Trims and rebalance, this year" takes risk to 10.8%, above the 8.3–10.3% band. It is marked "Outside a policy limit" and is never recommended.*

**Compare proposals and checks** opens a full-width comparison, with one column per proposal.

The checks come in three groups:
- **executable:** paid with cash on hand and proceeds, never more than is held, advisor-directed holdings only;
- **within the gain budget;**
- **within policy limits:** risk band, below investment grade, turnover.

Each ✗ shows the figure that fails. Below the checks are the points to weigh for suitability and the objective before and after.

![Compare proposals: checks](images/05-compare-checks.png)

The **funding ledger** shows:
- cash at the start, sale proceeds, purchases and cash at the end;
- the cash the target keeps, and any shortfall;
- targets left unfilled;
- future cash with its date. The $5M expected on 15 Nov is never used for today's trades.

Below the ledger are the figures and each proposal's trade-set version.

![Compare proposals: ledger and figures](images/06-compare-ledger.png)

Choosing a proposal shows its steps and its one trade list.

![Steps and trades](images/07-compare-steps-trades.png)
*The recommended proposal's five steps. The stress step reduces a purchase from the rebalance instead of selling it back.*

## 4. The decision drawer

Opening an action shows its parts. **Summary** separates two things:
- **Recommended next executable stage:** about $1.16M of NVDA this year, about $221K of tax;
- **Long-term objective:** $6.92M over about six tax years, $1.32M of tax.

It then shows:
- why now;
- the owner and due date;
- data readiness;
- overlaps with other actions, and how the proposals reconcile them.

![Drawer summary](images/08-drawer-summary.png)

**Evidence** shows where the exposure comes from, held directly or through funds, plus lower-correlation options and the analyses that found the issue.

![Drawer evidence](images/09-drawer-evidence.png)

**Options** compares this action's own options, computed as if it were done alone. For the allocation there are five, from "Invest excess cash now (no sales)" to "Full rebalance to the target".

![Drawer options](images/10-drawer-options.png)

**Research** lists the fund research and manager briefings for the building blocks the plan would buy.

![Drawer research](images/11-drawer-research.png)

## 5. Guarded decisions and the decision log

The decision steps follow the type of action:
- **trade review:** start review → accept for client discussion → client agreed → submit for supervisory approval. Approval to implement is a supervisor's step, by someone other than the advisor;
- **manager follow-up:** request sent → manager responded → closed;
- **client conversation:** discussed → agreed or declined;
- **data request:** requested → received.

**Accept for client discussion** needs all of:
- a started review;
- a proposal that includes the action, with its current trade-set version;
- a within-limits proposal, or an exception reason;
- ready data, or a recorded exemption;
- authority over every holding sold.

Unmet requirements are listed, and a refused step says what is still needed.

![Guarded decision](images/12-guarded-decision.png)
*Accept is refused until a data exemption is recorded, because part of the NVDA cost basis is missing.*

**Rule & history** shows:
- the playbook rule that fired, with its values;
- why the action ranks where it does: severity, materiality, benefit net of tax, timing, confidence, authority, complexity;
- the decision log.

Each log record names the proposal, the trade-set version and the exemption. A later change to the data, the policy or the trades marks the decision superseded.

![Rule, score and decision log](images/13-rule-score-decision-log.png)

Missing information is an action of its own, with an owner and a due date.

![Data request](images/14-data-request.png)

## 6. Downgrades

A downgrade is an action in the household that holds the stock.

**Finding them.** The "Recent downgrades held" line under the household picker names each recently downgraded stock with its household:
- UNH · Okoye;
- INTC, PFE · Ashford;
- TSLA · Reyes-Marín;
- CVS, PFE · Castellano.

Clicking one opens that household's action plan with the Downgrades health check selected.

![Recent downgrades held](images/28-downgrades-finder.png)

![Downgrade actions in a household](images/29-downgrades-household.png)
*Castellano: the PFE and CVS downgrades, filtered by the Downgrades health check ("Showing 2 of 6").*

**The drawer** shows:
- the rating change, with the research team's reason;
- this household's position, its lots and the illustrative tax to switch;
- who decides: the manager, here, so the next step is a request to the manager, not a trade;
- similar higher-rated alternatives, for your consideration.

![Downgrade drawer](images/30-downgrade-drawer.png)
*PFE in Castellano: Buy → Neutral on 29 Sep. Switching would save about $4,872 of tax. The Eaton Vance SMA decides. JNJ, MRK, ABBV and VTV are listed as alternatives.*

Ask Atlas still answers "Which stocks in my advisory portfolios were downgraded?" across the whole book, in the chat.

## 7. Special cases

**No compliant plan.** When no proposal passes every check, the plan says "No currently compliant combined plan: advisor decision required". It lists the failing checks, and nothing is preselected.

![No compliant plan](images/15-no-compliant-plan.png)
*Brennan Household: every proposal fails the Aggressive risk band or the $18K gain budget. The one that gets risk inside the band (13.2%) is over the gain budget, so it would need an exception reason.*

**A goal with trade-offs.** A goal that is met but makes other things worse says so in the headline, and the next step becomes a client discussion.

![Goal with trade-offs](images/16-goal-with-trade-offs.png)
*Okonkwo: return 5.2% → 6.6% (met), but the 2008-type loss goes from −19% to −40% and income falls from $941K to $765K a year.*

**Manager-run accounts.** Manager-run holdings never appear in an advisor's trade list. Every action becomes a follow-up with the manager.

![Manager-run account](images/17-manager-run.png)
*Okoye Household: four manager follow-ups, including the UNH downgrade.*

## 8. Full analysis

The six analyses are the evidence behind the actions. Each tab opens with its answer: one sentence and three figures.

**Alignment** compares risk with the profile, holdings with the target, and the target with the profile's model. It offers the tax-budgeted plan, the full rebalance and the profile model.

![Alignment](images/18-alignment.png)

**Allocation gaps** shows underweight asset classes, what new and excess cash can fill with no sales, and which holdings could fund the rest.

![Allocation gaps](images/19-allocation-gaps.png)

**Goals** plans toward an income, return or loss-limit objective.

![Goals](images/20-goals.png)
*Kaplan: a 2008-type loss of −34% today, −24% after the changes, within the 25% limit.*

**Holdings & concentration** covers:
- single stocks, including the shares held inside funds;
- sectors;
- single funds;
- below investment grade.

Each finding shows the playbook rule that fired and its solutions, with trades and tax.

![Holdings & concentration](images/21-holdings-concentration.png)

![Holdings detail](images/24-holdings-detail.png)

**Deep dive** covers style, size and geography against the target, with fund research and manager briefings.

![Deep dive](images/22-deep-dive.png)

**Stress test** shows today's holdings in four past events, what drove the losses, and suggested changes.

![Stress test](images/23-stress-test.png)

## 9. Ask Atlas

Ask Atlas answers Portfolio Review questions in the chat. Each answer has:
- "How Atlas worked this out";
- a run trace: the skill, the policy, and the completion checks;
- a button that opens the matching tab.

"Ask Atlas about [household]", next to the household picker, asks about the tab you're on.

![Ask Atlas](images/25-ask-atlas.png)

## 10. Guided tour

"Tour Portfolio Review" runs 10 steps:
1. household proposals;
2. the proposal comparison;
3. the decision drawer;
4. a goal with trade-offs;
5. alignment;
6. concentration;
7. goals;
8. stress test;
9. downgrades, opening the first holder's downgrade actions;
10. where to go next.

Steps 5 to 9 run real questions through Ask Atlas.

![Guided tour](images/26-guided-tour.png)

## 11. Phone layout

On a phone, the tab groups stack and the page fits the screen width.

![Phone](images/27-mobile.png)
