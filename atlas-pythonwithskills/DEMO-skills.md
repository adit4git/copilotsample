# Demo: team skills shape Atlas (about 12 minutes)

Run the app with `uvicorn app.main:app`, open it, and sign in as Dana. All skills start off. **Team Skills** is in the sidebar; Turn all off resets the demo.

The point to land: **the engine stays the same and the teams own the policy.** Each skill is a short file with an owner and a version. Turning it on changes every workspace that reads that policy, and the answer names the team behind it.

## 1. The catalog (1 min)
Open **Team Skills**. There are 12 skills from 10 teams, each with the workspaces it shapes, its status and its version. Open **Read the skill** on any of them: it is plain English plus a few lines of `policy.json`.

## 2. Product & Compliance: a term sheet change (2 min)
1. Turn on **QLH term sheet update (2027 preview)**. The table shows Okoye going from Eligible to Ineligible for QLH, and Brennan from Needs review to Ineligible.
2. Click **Okoye: QLH verdict and tax personalization**. The QLH verdict is now Ineligible.
3. Click the **i** next to the verdict. It names the failing rule, `qlhOverlay.minimum_2027`, tags it **Product & Compliance skill**, and shows the new wash sale disclosure.

## 3. Tax personalization: three teams on one screen (3 min)
1. Turn on **QLH harvest threshold pilot: 2.5%** (Tax Services). On Okoye's QLH lots tab, 4 lots are harvested instead of 2, and the threshold line moves. The Tax Overlay Desk chart splits at 2.5%.
2. Turn on **Year-end tax conversation playbook** (Wealth Planning). "Worth raising" gains a year-end point tagged **Wealth Planning skill**.
3. Turn on **TEM Style Manager shortlist** (Manager Research). The Personalization options tab shows a different shortlist, with global and dividend sleeves.
4. The strip at the top of the client page lists every skill shaping it.

## 4. Brokerage-to-advisory conversion: skills that combine (3 min)
1. Turn on **Conversion playbook: managed first, within a tax budget** (Advice & Investment Solutions). For Montgomery and Fairbanks, the suggested strategy type changes to Custom Managed. Brennan stays as it was: the tax is over budget.
2. Open **Montgomery**. The map opens on Custom Managed: "entry tax about $86K, 2.7% of the account, within the 3.5% budget".
3. Turn on **Conversion tax estimate: include New Jersey tax** (Tax Services). Montgomery's entry tax becomes 34.55%, which puts it over the budget, so the suggestion falls back to Personalized (Client). Two teams' skills combine, and each part is labeled.
4. Optional:
   - **Brokered CDs held to maturity** (Program Operations): Fairbanks's CD under Custom Managed goes from Confirm to Held.
   - **Conversion guardrails** (Risk): a Risk note appears on the concentrated COST sale.

## 5. CIO office and Risk (1 min)
Turn on **Capital market assumptions: 2027 preview** and **CIO Model Fit: tighter risk flags**. CIO Model Fit re-sorts, every expected return changes, the header reads "2027 preview CMA", and Fairbanks gains a concentration flag.

## 6. Field Enablement: what a brief must contain (1 min)
Turn on **Meeting prep: fees, conflicts and a send checklist**, and open a meeting prep draft. It now has a Fees & conflicts section built from the client's numbers, and a "Before you send this" checklist. With the year-end playbook also on, it has a Year-end tax check section too. Two teams, one brief.

## 7. Atlas Product: advisors' own words (1 min)
Ask "Should the Montgomerys go fee-based?" with **Ask Atlas: advisors' own words** off, then on. Off, Atlas gives a general answer. On, it maps the conversion and offers the conversion map. "Is Montgomery's account off-model?" and "Any wash sale issues for Okoye?" work the same way.

## Talking points
- **Who changes what.** Rules, thresholds, rates, shortlists, playbooks, brief standards and phrasing all belong to the business. Only new kinds of calculation need engineering.
- **Safe to try.** Every skill reverts exactly. "What it changes" measures a skill on a real book before anyone turns it on.
- **Traceable.** Verdict traces, map cells, notes and drafts name the skill and team behind them.
- **The same file serves the AI.** "Instructions for Atlas" in a skill goes into the chat and drafting prompts when a model is connected.
