# Ask Atlas: notes for rebuilding it with another LLM

**Companion to:** `ask-atlas-changes.md` (what it does). This file is about **how it behaves**: the rules in `atlas-console-book-view.html` that a new implementation has to keep.

**How the prototype works:** every answer comes from rules over the page's figures. In a rebuild, the model should write the words and choose the actions. Figures, routing guards and citations come from tools.

**Where the code is:** inside the HTML, in five blocks.

| Block | What it holds |
|---|---|
| The Ask Atlas page and the panel beside each screen | The context, openers, routing, citations and panel modes |
| The workflow | Its thread, the workflow questions, and "explain the change in…" |
| The decision guide | Its questions and scoring, and the knowledge base with its sources |
| The Advisory module | Its risk and tax figures |
| Portfolio at a glance | The CIO view and the risk measures |

---

## 1. Two kinds of thread

| Thread | Used on | Holds |
|---|---|---|
| **Shared** | Ask Atlas home page, Book view, Client dashboard, client deep dive | User and Atlas messages; openers are marked as automatic and carry a screen tag |
| **Per workflow** (one per household and opportunity) | The three-step workflow | Messages, the decision guide's place and answers, the selected option, the gain budget, the open question section |

- **No sharing:** the workflow thread never appears in the shared thread.
- **The link between them is the draft:** once an option is selected, the client's opener mentions it and points to the next open item, and Book view lists all drafts.

## 2. What Atlas is looking at: send it with every request

The context is built from the screen, never inferred from the conversation.

| Screen | Fields | Shown in the header as |
|---|---|---|
| Book view | Criterion (or none); for maturing bonds, the minimum amount and the window in months | **Book view** · *criterion* · *n* clients |
| Client dashboard | Sort column | **Client dashboard** · *n* households · sorted by *x* |
| Client deep dive | Household; view (asset groups, asset classes, sectors, holdings); drill-down (group, class, sector or an opportunity's holdings); show (today, target, proposal) | **Household** · *view* · *drill-down* · *showing proposal* |
| Workflow | Household, opportunity, step 1–3, selected option | **Household** · *opportunity* · Step *n* of 3 · *option* |

- **Context key:** screen + criterion + maturity settings / household + view + drill-down + show. This key decides when an opener fires (section 3).
- **Where the line sits:** it is the header's second line. The "Looking at" label was removed to save space and the line is cut short in the docked panel. Consider showing the label again and letting the line wrap.

## 3. Openers

**Rules:**

| Rule | Detail |
|---|---|
| When | Only when the context key changes; never on the home page or in the workflow |
| Replace, don't stack | If the last message is an unanswered opener, replace it |
| Size | One message, at most 3 priorities, plus 1–2 buttons |
| Tag | Screen name above the message (e.g. "Book view · Brokerage → Advisory program") |
| Phone | A dot on the ✦ button until the panel is opened |

**Content:**

| Screen | Content |
|---|---|
| Book view | Up to three priorities, chosen as listed below |
| A criterion | *n* of *N* households and the total; strongest case and its reason; who is next. Buttons: open the strongest case (its workflow if it has that opportunity), "Why *next client*?" |
| Client dashboard | Meetings in the next 7 days (up to 3, soonest first) and the top open item for each. Button: prepare the first |
| Deep dive, front page | "Before the *meeting* *when*:" (if within 21 days); YTD and the gap to benchmark; largest drift; any stock above 10%; biggest open item; any draft. Buttons: the next open item, "What should I raise?" |
| Group drill-down | Weight against target, CIO stance and reason, largest class gap inside |
| Class drill-down | Weight against target, CIO stance, largest holding (marks a downgrade) |
| Sector drill-down | Share of equity against the benchmark; a warning above +5 pts |
| Sectors / Holdings / Asset classes with no drill-down | Biggest over- and underweight sector / the three largest holdings / the largest class gap |
| Show target | The money to move per asset group to reach target |
| Show proposal | The draft option; drift, volatility and tax before → after |

**The three Book view priorities**, checked in this order:
1. The bond or CD maturing soonest, if within 45 days.
2. The meeting within 7 days with the most open items.
3. The largest unrealized losses, with the days to year-end.
4. The largest Advisory candidate, excluding specialist review.

The first three that exist are shown, followed by "Drafted so far: …".

**Strongest case:** sorted by the criterion's value; for the Advisory move, specialist-review households go last.

**Reason per criterion:**

| Criterion | Reason |
|---|---|
| Advisory | Brokerage $; tracking error before → after (or drift if it doesn't improve); losses to harvest in the move |
| Concentration | Stock and % of the household |
| Maturing | Total and days to the first maturity |
| Downgrades | Each holding with its rating change |
| Cash | Excess over target |
| Drift | Group and pts |
| Behind | Pts behind the benchmark |

## 4. Routing order

Order matters. Each guard below fixed a real misroute.

**Panel beside a screen:**

| # | If the question… | Then |
|---|---|---|
| 1 | Asks to go somewhere ("take me", "Book view", "client dashboard") | Navigate |
| 2 | Asks where to start / what to focus on today | The Book view priorities, on any screen |
| 3 | Mentions CIO / house view / stance and an asset group or class | The CIO view with its citation. Match the **longest** class name first ("cash & sweep" before "cash") |
| 4 | Names a client and asks for a brief ("raise", "meeting", "prepare", "tell me about") | That client's brief |
| 5 | Is asked on a client page and names no other client | Client answers: brief, drift, cash, concentration, income, performance, tax, risk, CIO, Advisory, opportunities |
| 6 | Is asked on a criterion | Strongest case / why a named client is on it / count and total |
| 7 | Is asked on the dashboard about calls, this week or open items | Households with the most open items |
| 8 | Anything else | The general answers below |

**General answers (also used on the home page):**
1. Navigation.
2. Knowledge answers, unless the question asks for a list of clients ("which clients", "who has", "my book").
3. Criteria keywords → the matching list.
4. A client named in the question → a one-line summary.
5. Knowledge answers again.
6. The "what I can do" reply.

**Workflow:**
1. "Explain the change in *metric*" → before → after and the trades that cause it.
2. Knowledge answers, except client-specific Advisory questions (client, household, apply, gains, fits, risk, shift, tax impact).
3. Guide / help me decide / which should I / recommend → start the decision guide. Not for "what would change the recommendation?".
4. Advisory-specific questions:
   - risk shift;
   - tax impact;
   - tax management services;
   - which strategy type fits;
   - eligibility;
   - cost (only if asked);
   - how each holding moves;
   - how long the transition takes;
   - why not stay in brokerage;
   - documents.
5. Generic questions:
   - compare the options;
   - tax;
   - income;
   - risk;
   - CIO;
   - what if we do nothing;
   - why now;
   - book comparison;
   - client summary;
   - what would change it;
   - a named option;
   - a product.

**Misroutes these guards fixed (use them as regression tests):**

| Question | Wrong answer it used to get |
|---|---|
| "Who is eligible to move from brokerage?" | A list of clients instead of the eligibility rules → knowledge answers before criteria |
| "Explain the conversion rules" | Caught by the risk answer → "explain" was removed from the risk trigger |
| "What would change the recommendation?" | Restarted the guide → that phrase is excluded |

## 5. Figures come from tools; the model never computes

| Proposed tool | What it covers |
|---|---|
| `household_metrics` | Allocation, targets, drift, positions, sectors, income, gains/losses, benchmark |
| `risk` | Volatility, tracking error to target, scenarios (2008, 2022), expected return |
| `criteria` / `list_for` | 13 criteria, ranked |
| `opportunities` | For one household, with reasons and the next step |
| `options` | For an opportunity, each with its trades and metrics |
| `option_metrics` | Tax, realized gain, drift, tracking error, largest stock, income, harvested loss value, tax-managed equity |
| `advisory_key_metrics` | Risk shift, tax this year, losses harvested, gains deferred, tax-managed equity, tax-efficient management lines |
| `eligibility` | Eligibility for the Advisory program |
| `conversion_matrix` | Where each brokerage holding goes |
| `latest_draft` | The draft proposal for a household, if any |
| `cio_view` | Stance, quote and page |

**Default Advisory option:** tax-efficient transition, else rebalance now, else move everything except the stock. It must be the same everywhere: recap, risk table, Book view reason, opener and chat. Otherwise the numbers disagree.

**Rules that belong in the tools, not the prompt:**
- tax at 23.8% on net realized gains;
- no buying back a security sold at a loss (wash sales);
- lots with and without cost basis routed separately;
- rebalancing gaps measured **after** the sells and capped at each asset group's gap;
- tax-efficient transition: sells non-model holdings with the least gain per dollar first, within the yearly budget;
- the overlay counts only managed strategies (CIO model, transition, direct indexing) in taxable accounts.

## 6. Actions: tools the model calls, not text

| Action | Triggered by |
|---|---|
| `navigate(route)` | Message buttons; navigation questions. The prototype waits about 0.5 s after answering |
| `ask(question)` | Follow-up buttons in messages (e.g. "What should I raise?") |
| `select_option(id)` | The guide's **Select** |
| `set_gain_budget(amount)` | The guide's tax answer: $100K for "up to about $100K", $250K for "up to about $250K" |
| `open_citation(page)` | A citation chip |
| `start_guide()` | "Guide me to a decision" |

**Message buttons:** each has a label, then either a route or a follow-up question, and one is marked primary.

## 7. Decision guide

**Questions:**

| Opportunity | Questions, in order |
|---|---|
| Advisory | 1. Tax this year: as little as possible / up to about $100K / up to about $250K / whatever it takes. 2. Who decides: a manager or the CIO model / the advisor / the client approves each trade. 3. What matters most: risk back to the profile / ongoing tax management / keep tax low. 4. Cash needs in 12 months: none / keep a reserve. 5. Direct indexing: yes / no (asked only if offered) |
| All others | Tax (same answers), then act now / phase in / not yet, then lower risk / more income / closer to target / lowest tax |

**Scoring (per option):**

| Answer | Effect |
|---|---|
| Tax above the limit | −3 − (excess ÷ $100K); otherwise +1 if the option trades |
| Tax "whatever it takes" | + drift reduction × 60 |
| Manager decides | +2 for rebalance now, transition, direct indexing |
| Advisor or client decides | +2 for the personalized option, or moving everything except the stock |
| Risk back to profile | + (tracking error cut × 40 + drift cut × 30) |
| Ongoing tax management | + up to 3 × tax-managed share; +1 for direct indexing |
| Keep tax low | − tax ÷ 1% of assets |
| Stay in brokerage | −2 when a focus is given; −1 when the household shows reasons for advice |
| Keep a cash reserve | −0.3 for rebalance now and transition |
| Direct indexing | ±2 by answer |
| Specialist route | +3 (required above 50% in one stock) |
| Other opportunities | Act now +1.5 / phase in +2 / not yet +3 for the matching option; priority weights: risk (stock × 20 + volatility × 50), income (% change × 20), target (drift × 60), tax (− tax ÷ 1% of assets) |

**Output:**
- the recommendation, with ✓ for what fits and △ for what doesn't;
- a runner-up;
- any setting it changed ("I set the yearly gain budget to $100K");
- "A recommendation for you to review, not a decision. Suitability is yours to confirm."
- buttons: Select / Compare with the runner-up / Change my answers.

**After a manual pick**, Atlas compares it with the client's answers (e.g. "tax $152K is above what the client accepts").

**On step 3**, a checklist:
- documents;
- the gain budget confirmed with a tax advisor;
- each eligibility condition and its owner;
- suitability;
- supervisory approval.

## 8. Content rules a fresh model won't know

- **Advisory moves:** lead with risk shift, tax impact and tax-efficient management. Don't explain the program's benefits or fees unless asked.
- **No real firm names** (employer, vendors, fund brands, internal program acronyms). Use:
  - "Advisory program";
  - "tax-efficient transition";
  - "tax-efficient management overlay";
  - "tax-efficient rebalancing";
  - "CIO".
  Run the name scan on every output.
- **Labels:**
  - generated text is marked "AI-drafted · review before sharing";
  - the panel says "simulated";
  - the CIO card says "the house view is published, not generated".
- **Formatting:**
  - minus sign (−), not a hyphen;
  - "pts" for percentage-point changes;
  - lowercase only the first letter of titles ("Advisory program" and "CDs" keep their caps).
- **Restraint:**
  - one opener per screen;
  - question sections folded until picked;
  - no more than 3 priorities;
  - no extra suggestions after an answer beyond 1–2 buttons.

## 9. Citations

| Item | Rule |
|---|---|
| Source | CIO House View, 15 Oct 2026 (illustrative, made-up content), 5 pages |
| Text | Stored per asset group and per class |
| Page numbers | Read from the PDF's text, not assumed. Asset groups: pp. 1–2; equity classes: p. 3; fixed income: p. 4; alternatives and cash: p. 5 |
| Answer | Stance → exact quote → fit for this household → citation chip |
| Fit wording | Overweight and below target: "adding here fits both". Underweight and above target: "trimming fits both". Overweight and above target: "in line with the CIO overweight" |
| Chip | PDF · CIO House View · 15 Oct 2026 · *asset class* · p. *n* ↗ |
| Opening | New tab at `#page=n`; if the tab is blocked, download the file |
| Knowledge answers | "Source: Program brochure / Transition term sheet / Form CRS / Atlas conversion rules / Product shelf" |
| For an LLM | Quote only retrieved text; take the page from retrieval metadata; never let the model supply a page number |

## 10. Panel modes and controls

| Mode | Behaviour |
|---|---|
| Docked (default) | Side panel; the page uses a wider layout; opportunity tiles use 3 columns |
| Collapsed | Panel hidden; an "✦ Ask Atlas" button at the bottom right with a dot for new messages; the page gets extra bottom space |
| Full screen | Over the page at reading width, page dimmed; question sections open; Esc (unless the tour is running), the shrink button, a click outside or navigating returns to docked |
| Phone | A sheet from the ✦ button; full screen fills the screen; the collapse control is hidden |

**Other controls:**
- A ✦ question asked while collapsed re-docks the panel.
- **✦ placement:**
  - next to the six key-figure labels;
  - on Book view and dashboard rows, shown on hover only;
  - in the workflow's impact and risk tables the metric name is the link, so nothing wraps.
- **Each CIO stance** in the deep dive's table is a button that asks for that stance's view.

## 11. Evaluation set to reuse

| Set | Size | Pass condition |
|---|---|---|
| Openers | 115 screens | Each screen gets one opener; an unanswered one is replaced |
| In-context questions | 2,104 | Suggested questions per screen, ✦ on key figures, "Why is *client* on this list?", "What should I raise with *client*?": none falls back to the generic reply |
| Workflow questions | 1,543 | Every section question for every opportunity: specific answer |
| Decision guide | 676 | Every opportunity × 4 answer sets: a recommendation, no error |
| Home page | 16 | Suggested questions: a specific answer, right type (knowledge vs list) |
| Routing regressions | 3 | Section 4's misroutes |
| Number agreement | — | The figure in a chat answer equals the figure on the page for the same option |

**Using it on a new model:**
- Run the same sets.
- Score routing exactly.
- Check that every number matches a tool result.
