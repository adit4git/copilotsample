"""Rebuild manually rewritten, non-client demo cases and catalog fixtures.

Each query corresponds to a source worksheet row. Expected labels are proposed
POC annotations, NOT independently adjudicated gold labels. No original names,
account IDs, balances, holdings amounts, or client narratives are reproduced.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# source row | intended capabilities | newly written generic query
ROWS = """
2|research.cio|What is the current CIO view on interest rates?
3|research.cio|Summarize the latest CIO capital market outlook.
4|research.change|What changed in CIO guidance since last month?
5|research.cio,content.draft|Prepare client-friendly talking points about CIO guidance on inflation.
6|research.cio|What is the CIO view on equities versus fixed income?
7|research.cio|List the most relevant CIO investment themes today.
8|research.cio|What is the CIO case for diversification?
9|research.cio|Explain the CIO view on international equities and currency risks.
10|research.cio|Find CIO guidance for retirement planning conversations.
11|research.cio|Describe the CIO outlook on private markets.
12|research.cio|Find current CIO guidance about cash and liquidity.
13|research.cio,content.draft|What should I say about CIO guidance when investors ask about going to cash?
14|research.cio|Explain CIO duration positioning today.
15|research.cio|What risks does CIO highlight this quarter?
16|research.cio,portfolio.exposure|Find CIO guidance relevant to concentrated positions.
17|research.security,content.draft|The market declined today. Explain what happened and draft talking points.
18|portfolio.exposure|How will the technology selloff impact my client book?
19|portfolio.exposure|Which clients are exposed to today's macro market moves?
20|research.cio|What CIO market themes should I discuss this morning?
21|research.security|Where can I find analyst coverage and price targets with the research rationale?
22|product.compare|Compare municipal bond laddering versus active bond management.
23|product.search|Find the approved model portfolio referred to in a research article.
24|portfolio.correlation|Find asset classes whose returns are less correlated.
25|content.draft|Draft an email about recent volatility for this client.
26|content.draft|Prepare talking points for an afternoon client call.
27|content.draft|Simplify this explanation for a novice investor.
28|content.draft|Rewrite this paragraph as a more technical explanation.
29|content.draft|Write a one-paragraph market update for an email.
30|content.draft|Draft a follow-up email after a volatile week.
31|content.draft|Create a script for inbound calls about market movements.
32|content.draft|Turn an approved explanation into a voicemail script.
33|content.draft|Draft a client-friendly explanation about remaining invested.
34|research.cio,content.draft|Draft a quarterly recap using approved CIO guidance.
35|content.draft|Create a message suitable for a tax-sensitive investor.
36|content.draft|Create a version for a very risk-averse investor.
37|content.draft,decision.readiness|Draft a follow-up email with a checklist of pros, cons and next steps.
38|research.cio,content.draft|Convert CIO guidance into a client-facing paragraph.
39|content.draft|Draft a client note on interest rates and cash yields.
40|content.draft,solution.match|Prepare talking points for a structured-note reinvestment proposal.
41|product.compare,content.draft|Compare SMA versus ETF approaches in client-friendly language.
42|portfolio.exposure,research.cio,content.draft|Explain international exposure versus CIO guidance and draft talking points.
43|performance.reconcile|The manager says the fund is up but account reports are down. Reconcile the returns.
44|performance.reconcile|Explain differences in the mechanics and performance reporting of a strategy.
45|research.security,directory.specialist|Find research on software industry risks and the best way to connect to a specialist.
46|operations.distribution|Reconcile the distributable amount with a payment and check withholding and W8BEN status.
47|product.search|What approved large cap growth funds are available?
48|product.search|What approved ways provide small cap exposure?
49|product.compare,solution.match|Compare SMA versus ETF versus mutual fund options that fit this client.
50|product.search,solution.match|Which approved strategies fit an income objective?
51|solution.match|What investment options balance yield and liquidity for this client?
52|solution.match|Design tiered liquidity using short, medium and longer investment horizons.
53|product.compare|Compare direct indexing versus ETF investing for tax efficiency.
54|product.search|Find approved products for tax-efficient small company exposure.
55|product.search|Which approved alternatives options are available on the platform?
56|solution.match,portfolio.exposure|Find CIO-aligned hedging approaches for concentrated positions.
57|solution.match,research.cio|Build a proposal using the current CIO model allocation.
58|product.search,solution.match|List products that fit this objective and include eligibility constraints.
59|solution.match|Recommend an investment proposal to reduce volatility while maintaining income.
60|product.search|Which approved strategies diversify equity exposure across regions?
61|product.search|A manager is on hold. Find approved alternatives.
62|solution.match|Help identify the best solution for this client's objectives.
63|product.search|Which strategies are available on the platform for an income objective?
64|product.compare|Compare a structured note versus an SMA.
65|book.screen|Which clients qualify for alts but do not currently use them?
66|performance.attribution|Explain the main performance drivers in this portfolio.
67|performance.attribution|Which sector allocations contributed to YTD performance?
68|performance.attribution,research.cio|Explain portfolio underperformance with CIO guidance and benchmark data.
69|portfolio.drift,solution.match|Show allocation drift and a proposal to rebalance toward CIO targets.
70|portfolio.exposure|Calculate rate sensitivity and duration exposure for this client.
71|portfolio.exposure,research.cio|Explain concentration risk using CIO guidance.
72|portfolio.drift,book.screen|Find portfolios out of alignment with tactical ranges and prioritize outreach.
73|performance.attribution|Explain a performance outlier in an account group.
74|solution.match|What reallocations would reduce risk while preserving the intended allocation?
75|portfolio.exposure|Which clients are exposed to interest rates moving higher?
76|portfolio.exposure|Who is affected by today's technology selloff?
77|research.security|How did analyst estimate revisions change over the last quarter?
78|research.security|Summarize the latest earnings call and major risks.
79|research.security|When is the next earnings date and what is consensus expecting?
80|research.security|Explain the recent credit spread movement for this bond issuer.
81|research.security|Did a ratings agency change the outlook for this issuer?
82|research.security|How has short interest changed for this company?
83|research.security|What news drivers affect this security today?
84|practice.analytics|Compare practice sales volume with the firm total and show where we rank over twelve months.
85|portfolio.correlation|Run a correlation analysis of a strategy against broad market benchmarks.
86|portfolio.overlap,tax.transition|Find the best holdings overlap for a tax-aware transition into an SMA.
87|performance.attribution,research.cio,meeting.prepare|Prepare an annual review of manager performance and current CIO guidance.
88|solution.match|Build an investment proposal around tax management, lower volatility and income.
89|tax.transition|Plan a transition from taxable bonds to munis without selling stocks and realizing gains.
90|tax.transition,solution.match|Build a tax-aware diversification proposal for concentrated stock with unrealized gains.
91|portfolio.overlap,tax.transition|Run overlap analysis against two strategies and estimate the transition tax impact.
92|tax.transition,solution.match|Prepare a direct-indexing proposal for appreciated stock and future tax-loss harvesting.
93|tax.transition,portfolio.overlap|Transition a self-directed account into a managed strategy and evaluate holdings overlap.
94|tax.transition,product.terms|Find a transition path for an appreciated account below the strategy minimum.
95|product.compare|Compare laddered versus actively managed municipal bonds on cost and performance.
96|performance.attribution|Find back-tested and full-cycle performance for a tax-aware model.
97|portfolio.overlap,portfolio.exposure|Measure overlap and international exposure across two blended equity strategies.
98|portfolio.exposure,solution.match|Suggest a proposal with less technology concentration and similar tax-management objectives.
99|portfolio.correlation,performance.attribution|Compile alternative-fund performance and correlation over several horizons.
100|portfolio.exposure|Provide a private fund's top ten holdings and weights.
101|portfolio.exposure,book.screen,research.cio|Which clients are impacted by the CIO update and what next-best-actions should be considered?
102|monitor.manage,portfolio.drift,content.draft|Notify me when portfolios drift beyond CIO targets and draft a client explanation.
103|book.screen,content.draft|Show clients with high cash balances and draft outreach talking points.
104|monitor.manage,portfolio.exposure|Alert me to concentration risk above a threshold.
105|book.screen,solution.match|Which clients qualify for alts but do not use them, and what proposal fits their objectives?
106|monitor.manage,solution.match|Proactively flag rising portfolio volatility and prepare a risk-mitigation proposal.
107|book.screen,research.cio|Surface next-best-actions across my book with CIO citations.
108|monitor.manage,research.security|Alert me when a ratings agency changes an issuer outlook.
109|monitor.manage,research.change|Notify me when changes in CIO guidance are material for clients.
110|monitor.manage,portfolio.exposure|Create a daily market brief showing client exposure to market events.
111|monitor.manage|Alert me if a closed-end fund discount widens beyond my threshold.
112|monitor.manage,product.terms|Notify me when the manager fee changes for a strategy.
113|monitor.manage|Alert me when a fund research rating changes.
114|monitor.manage,research.security|Flag major estimate revisions for top holdings.
115|instrument.payout|Calculate the maturity proceeds and return for a note maturing after its calculation date.
116|product.terms|Retrieve the maturity terms for two structured notes.
117|operations.data_issue|Duplicate ticker symbols in the product archive are distorting percentages.
118|decision.readiness|Summarize the decision trade-offs to discuss with a client.
119|decision.readiness|List key risks, benefits and required disclosures for a proposal.
120|decision.readiness|Which approvals should I confirm before presenting this recommendation?
121|decision.readiness|What disclosures should accompany this recommendation?
122|decision.readiness|Create a decision summary for documentation after the meeting.
123|decision.readiness|Generate follow-up tasks and a checklist of next steps.
124|content.draft|Draft a post-meeting recap and next steps note.
125|decision.readiness|What questions is the client likely to ask about this proposal?
126|decision.readiness|Which assumptions affect the recommendation most?
127|decision.readiness,content.draft|Draft a compliance-friendly rationale for client notes.
128|solution.match,research.cio|What portfolio proposal makes sense given current CIO guidance and client objectives?
129|portfolio.exposure,book.screen,solution.match|Identify concentration risks across my book and prepare a mitigation proposal.
130|meeting.prepare|Generate a meeting book with standard sections and custom content.
131|operations.transfer,solution.match|Can the prospect assets transfer and what target portfolio should we propose?
132|meeting.prepare|What changed since the last review?
133|meeting.prepare,portfolio.exposure|Before the meeting, review the client's concentration in market-linked investments.
134|portfolio.exposure|Analyze concentration across several accounts using a statement.
135|solution.match,portfolio.exposure|Find downside protection strategies for a concentrated position.
136|product.terms|Explain STARS notes, their mechanics and applicable investor characteristics.
137|tax.transition,solution.match|Prepare a transition proposal for company shares after a lockup expires.
138|tax.planning|A commercial property sale needs tax planning and consideration of a DST.
139|product.search|Find approved platform options for investing in a private company.
140|tax.planning|Which approaches address passive income needs and passive real estate losses?
141|directory.specialist|Find a specialist for family office and philanthropic services.
142|product.terms|Compare incentive fees, share classes and subscription windows for private funds.
143|directory.specialist|Find a product representative for a direct-indexing strategy.
144|tax.wash_sale|Could dividend reinvestment in another account create a wash sale?
145|operations.enrollment|Explain how to enroll clients in an approved MLP strategy.
146|operations.enrollment|Can we enroll in a tax overlay before the cash arrives?
147|operations.enrollment|During enrollment, what goes in the manager fee rate field versus the total client rate?
148|operations.enrollment|What are the steps to enroll in a PAS account?
149|directory.specialist|Put me in contact with a wholesaler for a private fund.
150|operations.transfer|Can these alternative-fund positions transfer in kind from a contra firm?
151|operations.order|Diagnose a submitted order with a grayed out submit button and an expired profile.
152|operations.order|Review entity eligibility for requests to invest through a US corporation.
153|operations.order|Will an approver's sabbatical affect an order already submitted?
154|tax.transition,solution.match,portfolio.exposure|Prepare a tax-aware diversification proposal for concentrated stock holdings with capital gains.
""".strip()


def main():
    cases = []
    for line in ROWS.splitlines():
        row, labels, query = line.split("|", 2)
        cases.append({"id": f"source_row_{row}", "source_row": int(row), "query": query,
                      "expected_intents": labels.split(","), "annotation_status": "proposed_required_labels",
                      "origin": "manually_rewritten_from_source_scenario"})
    assert len(cases) == 153
    (ROOT / "data" / "query_suite.json").write_text(json.dumps(cases, indent=2), encoding="utf-8")
    # Synthetic fixtures exercise actual screening logic; no real-world product claims.
    demo = [
        dict(id="DEMO-A", manager="Demo Cedar", strategy="Core Equity", platform="IAP", index="S&P 500", minimum=100000, fee_bps=20, permits_etf=True, permits_mutual_fund=False, max_concentration=0.20, source_verified=True, synthetic=True),
        dict(id="DEMO-B", manager="Demo Harbor", strategy="Flexible Equity", platform="IAP", index="S&P 500", minimum=250000, fee_bps=25, permits_etf=True, permits_mutual_fund=True, max_concentration=0.40, source_verified=True, synthetic=True),
        dict(id="DEMO-C", manager="Demo Juniper", strategy="Core Equity", platform="PAS", index="S&P 500", minimum=500000, fee_bps=18, permits_etf=False, permits_mutual_fund=False, max_concentration=0.20, source_verified=True, synthetic=True),
        dict(id="DEMO-D", manager="Demo Cedar", strategy="International Equity", platform="IAP", index="MSCI EAFE", minimum=400000, fee_bps=30, permits_etf=None, permits_mutual_fund=False, max_concentration=None, source_verified=True, synthetic=True),
    ]
    for item in demo:
        item.update(source="Synthetic POC fixture", source_location="data/sma_catalog.json", effective_date="demo_only")
    # Only the clearly transcribed S&P 500 minimum and core manager fee are used.
    snapshot = []
    managers = [("Franklin Templeton",175000,15), ("PGIM",100000,28), ("Natixis/AIA",100000,20),
                ("Parametric/Eaton Vance",250000,18), ("Goldman Sachs",250000,20), ("Aperio",250000,18)]
    for j,(manager,minimum,fee) in enumerate(managers):
        snapshot.append(dict(id=f"SNAP-IAP-{j+1}", manager=manager, strategy="Tax Managed Core", platform="IAP", index="S&P 500",
                             minimum=minimum, fee_bps=fee, permits_etf=None, permits_mutual_fund=None, max_concentration=None,
                             source_verified=False, synthetic=False, source="tax_managed_sma_visible_rows(2).xlsx",
                             source_location="Tax Managed SMA Core, rows 4, 5, 8", effective_date=None))
    for j,manager in enumerate(["Franklin Templeton", "PGIM"]):
        snapshot.append(dict(id=f"SNAP-PAS-{j+1}", manager=manager, strategy="Tax Managed PAS", platform="PAS", index="S&P 500",
                             minimum=500000, fee_bps=None, permits_etf=None, permits_mutual_fund=None, max_concentration=None,
                             source_verified=False, synthetic=False, source="tax_managed_sma_visible_rows(2).xlsx",
                             source_location="PAS Detail, rows 4 and 8", effective_date=None))
    (ROOT / "data" / "sma_catalog.json").write_text(json.dumps(demo + snapshot, indent=2), encoding="utf-8")
    print(f"Built {len(cases)} generic cases and {len(demo)+len(snapshot)} catalog records.")


if __name__ == "__main__":
    main()
