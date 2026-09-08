"""Versioned, inspectable intent registry. No customer data belongs here."""
from dataclasses import dataclass, asdict

REGISTRY_VERSION = "1.1.0"


@dataclass(frozen=True)
class IntentSpec:
    id: str
    family: str
    title: str
    operation: str
    service: str
    required_inputs: tuple[str, ...]
    examples: tuple[str, ...]
    patterns: tuple[str, ...]
    prerequisites: tuple[str, ...] = ()

    def to_dict(self):
        return asdict(self)


def spec(id, family, title, operation, service, inputs, examples, patterns, prerequisites=()):
    return IntentSpec(id, family, title, operation, service, tuple(inputs), tuple(examples), tuple(patterns), tuple(prerequisites))


SPECS = [
    spec("research.cio", "Research", "CIO guidance", "retrieve", "approved_research", ["current_approved_research"],
         ["What is the house view on interest rates?", "Find the latest CIO outlook for equities and bonds.", "Explain our investment office guidance on liquidity.", "What is CIO saying about retirement and private markets?"],
         [r"\bcio\b", r"\bhouse view\b", r"\bcapital market outlook\b"]),
    spec("research.change", "Research", "Compare guidance versions", "compare", "research_version_comparison", ["current_approved_research", "prior_approved_research"],
         ["Compare this month's investment guidance with last month's.", "What changed in our CIO position since the previous review?", "Identify differences between the current and prior CIO publications."],
         [r"(?:what changed|changes?|different|compare).{0,50}(?:cio|guidance|outlook)", r"(?:cio|guidance).{0,60}(?:since|last month|previous)"] ),
    spec("research.security", "Research", "Security and market research", "retrieve", "security_research", ["research_or_market_data"],
         ["When is the next earnings announcement and what is consensus?", "Explain the drivers of the technology selloff.", "Find a company's short interest and analyst price targets.", "Summarize issuer credit spread changes and rating outlooks."],
         [r"earnings|short interest|estimate revisions?|analyst.{0,20}(?:coverage|price)|credit spread|ratings? agenc|news drivers|what happened"]),
    spec("product.search", "Products", "Discover products", "screen", "product_catalog", ["approved_product_catalog"],
         ["Find approved funds for an income objective.", "Which investment strategies are offered on this platform?", "What products provide small company exposure?", "Find alternatives for a manager put on hold."],
         [r"(?:what|which|list|find).{0,35}(?:funds|products|strategies|solutions|options).{0,35}(?:available|approved|platform|objective)", r"approved (?:ways|options|solutions)", r"manager.{0,20}(?:downgraded|on hold)"] ),
    spec("product.compare", "Products", "Compare investment solutions", "compare", "product_comparison", ["approved_product_catalog", "comparison_targets"],
         ["Compare a separately managed account with an exchange traded fund.", "Contrast a municipal ladder against active bond management.", "Explain fees and tradeoffs of mutual funds versus structured notes.", "Does direct indexing make more sense than an ETF?"],
         [r"\bvs\.?\b|\bversus\b|compare.{0,50}(?:sma|etf|fund|ladder|note)|ladder.{0,30}(?:active|managed)|direct indexing.{0,40}(?:etf|versus)"] ),
    spec("product.terms", "Products", "Product terms and mechanics", "retrieve", "product_terms", ["verified_product_terms", "product_reference"],
         ["Explain this fund's subscription windows and incentive fee.", "Find the maturity terms for this market linked investment.", "How do STARS notes work and what are the share classes?", "What are the strategy fee and minimum?"],
         [r"maturity terms|incentive fee|share class|subscription window|\bstars\b|how.{0,15}(?:notes?|funds?).{0,10}work|(?:manager |strategy )?(?:fee|minimum)\b"] ),
    spec("portfolio.exposure", "Portfolio analytics", "Exposure and concentration", "calculate", "portfolio_exposure", ["authorized_scope", "positions", "security_master"],
         ["Measure interest rate sensitivity across my households.", "Which clients hold technology stocks affected by today's selloff?", "Show concentration and sector weights in the account.", "How much of this private fund is invested in a specific company?"],
         [r"concentration|concentrated|duration exposure|rate sensitivity|exposed to|who is affected|which clients.{0,25}(?:impact|expos)|impact.{0,25}(?:client|book)|top (?:10|ten) holdings|holdings and weights|international.{0,15}exposure"] ),
    spec("portfolio.drift", "Portfolio analytics", "Allocation drift", "calculate", "allocation_drift", ["authorized_scope", "positions", "target_allocation"],
         ["Check accounts outside their tactical allocation bands.", "Which portfolios have drifted away from CIO weights?", "Measure deviations from model target ranges."],
         [r"\bdrift\b|out of alignment|tactical ranges?|beyond.{0,15}(?:targets|weights)|allocation.{0,20}(?:deviation|bands)"] ),
    spec("portfolio.overlap", "Portfolio analytics", "Holdings overlap", "calculate", "holdings_overlap", ["authorized_scope", "positions", "comparison_holdings"],
         ["Measure shared holdings between the account and candidate models.", "Find overlap across two equity sleeves.", "Which SMA has the best overlap with the existing stocks?"],
         [r"\boverlap\b|shared holdings"] ),
    spec("portfolio.correlation", "Portfolio analytics", "Correlation analysis", "calculate", "return_correlation", ["return_series", "benchmark", "analysis_period"],
         ["Calculate correlation of this strategy against broad market indexes.", "Find diversification using return correlations.", "Compare three year correlation for alternative funds."],
         [r"\bcorrelat(?:ion|ed|ions)\b"] ),
    spec("performance.attribution", "Performance", "Performance and attribution", "calculate", "performance_analytics", ["authorized_scope", "verified_returns", "benchmark", "analysis_period"],
         ["Explain which sectors contributed to year to date returns.", "Analyze the portfolio's underperformance relative to its benchmark.", "Show manager performance since inception.", "Retrieve historical and back tested performance."],
         [r"performance|underperform|attribution|return drivers|back.?test|ytd.{0,20}returns"] ),
    spec("performance.reconcile", "Performance", "Reconcile reported returns", "reconcile", "performance_reconciliation", ["authorized_scope", "verified_returns", "cash_flows", "reporting_conventions"],
         ["The manager reports a gain while the account reports a loss.", "Why does the account return disagree with the manager return?", "Reconcile reporting differences including distributions and dates."],
         [r"reconcil.{0,30}(?:performance|return)|(?:manager|fund).{0,90}(?:up|gain).{0,100}(?:account|report).{0,60}(?:down|loss)|performance.{0,40}(?:reporting|diverge|discrepanc)|mechanics and performance"] ),
    spec("tax.transition", "Tax and transitions", "Tax-aware transition scenario", "simulate", "tax_transition", ["authorized_scope", "verified_tax_lots", "target_strategy", "gain_budget", "tax_assumptions"],
         ["Transition appreciated shares into a managed portfolio within a gain budget.", "Estimate capital gains from moving this portfolio to a new SMA.", "Diversify a large stock position while minimizing realized taxes.", "Move taxable bonds into municipal bonds without selling stocks."],
         [r"transition|tax impact|capital gains|cap gains|gain budget|diversif.{0,60}(?:tax|gains)|(?:tax|gains).{0,60}diversif|unrealized gain|appreciated.{0,30}(?:stock|shares)"] ),
    spec("tax.wash_sale", "Tax and transitions", "Wash-sale exposure review", "assess", "wash_sale_review", ["authorized_scope", "verified_tax_lots", "household_trade_activity", "held_away_activity"],
         ["Could dividend reinvestment in another account create a wash sale?", "Check household trading for loss harvesting conflicts.", "Evaluate substantially identical security purchases around a loss sale."],
         [r"wash.?sale|dividend.{0,15}reinvest|substantially identical"] ),
    spec("tax.planning", "Tax and transitions", "Tax planning specialist review", "assess", "tax_specialist_workflow", ["authorized_scope", "tax_assumptions", "specialist_review"],
         ["What solutions might address passive real estate losses?", "A property sale needs a tax planning discussion about DST structures.", "Find a specialist for tax deferral after a commercial real estate sale."],
         [r"passive (?:income|losses)|\bdst\b|commercial property|real estate.{0,45}(?:tax|loss)"] ),
    spec("solution.match", "Personalization", "Match solutions to objectives", "recommend_options", "solution_matching", ["authorized_scope", "client_objectives", "client_constraints", "approved_product_catalog", "eligibility_rules"],
         ["Build an investment proposal for this client's goals and restrictions.", "Suggest a portfolio balancing liquidity and yield.", "Find CIO aligned hedging approaches for concentrated stock.", "Recommend lower risk index choices for a tax-sensitive investor."],
         [r"\bproposal\b|recommendation|what reallocations|hedging|downside protection|tiered liquidity|balance.{0,20}(?:yield|liquidity)|best.{0,15}(?:strategy|solution)|fit.{0,15}(?:client|objective)|target portfolio"] ),
    spec("book.screen", "Book analytics", "Screen and prioritize households", "screen", "book_screening", ["authorized_scope", "positions", "screening_criteria", "eligibility_rules"],
         ["Identify households eligible for alternatives but not invested.", "Rank clients with high cash balances for outreach.", "Find next best actions across the advisor book."],
         [r"qualify.{0,25}alts|eligible.{0,25}alternatives|next.best.actions?|prioriti.{0,25}outreach|high cash|cash balances|across my book|across the book"] ),
    spec("practice.analytics", "Practice analytics", "Practice sales and rankings", "calculate", "practice_analytics", ["authorized_practice_scope", "sales_data", "peer_aggregation_policy", "analysis_period"],
         ["Rank our team by structured product volume against the firm.", "Report our allocations and the national total over twelve months.", "What was the practice sales volume by instrument?"],
         [r"where do we rank|firm.{0,25}(?:rank|volume|total)|sales volume|practice.{0,20}(?:sales|volume)|how much.{0,35}firm|national average"] ),
    spec("monitor.manage", "Monitoring", "Prepare monitoring rule", "configure_monitor", "monitor_rule_draft", ["authorized_scope", "trigger", "threshold_or_materiality", "cadence", "delivery_channel"],
         ["Notify me whenever allocation drift exceeds the threshold.", "Create a daily exposure alert for the client book.", "Stop these alerts or change the monitoring threshold."],
         [r"\bnotify\b|\balert\b|\balerts\b|proactively flag|daily market brief|monitor.{0,15}(?:rule|threshold)|flag major"] ),
    spec("content.draft", "Communication", "Draft or rewrite communication", "draft", "local_content_template", ["approved_source_content"],
         ["Write a client email about market volatility.", "Rewrite this paragraph in plain language.", "Prepare talking points and a voicemail script.", "Draft a client-friendly follow-up note."],
         [r"\bdraft\b|\brewrite\b|talking points|\bscript\b|\bvoicemail\b|client.facing paragraph|one.paragraph|simplify this|what (?:should|can) i say|what i should say|client.friendly|create a (?:message|version)|technical explanation"] ),
    spec("meeting.prepare", "Meeting preparation", "Assemble client review", "assemble", "meeting_book", ["authorized_scope", "client_objectives", "positions", "prior_review", "approved_source_content"],
         ["Assemble a meeting book with a portfolio review and agenda.", "What do I need to know before the client meeting?", "Prepare an annual review and describe changes since the last review."],
         [r"meeting book|annual.{0,15}review|before (?:the )?(?:meeting|client meeting)|since the last review|before the meeting|standard sections"] ),
    spec("decision.readiness", "Decision support", "Decision and disclosure checklist", "assess", "decision_checklist", ["proposal_context", "current_policy", "required_disclosures"],
         ["List the disclosures, assumptions and approvals needed for this proposal.", "Prepare a decision checklist with benefits and risks.", "What questions and tradeoffs should be discussed before presenting?"],
         [r"disclosures?|checklist|decision (?:summary|trade)|approvals.{0,25}(?:confirm|present)|assumptions|key risks,? benefits|questions.{0,25}client|follow.up tasks|compliance.friendly|trade.offs.{0,20}discuss"] ),
    spec("operations.enrollment", "Operations", "Enrollment guidance", "retrieve", "enrollment_guidance", ["current_program_guide", "platform"],
         ["How do I enroll in a managed account program?", "Can enrollment happen before cash arrives?", "What should I enter in the manager fee field during enrollment?"],
         [r"\benroll|manager fee rate|total client rate|steps.{0,20}pas account"] ),
    spec("operations.transfer", "Operations", "Transfer and custody eligibility", "assess", "transfer_review", ["authorized_scope", "position_list", "receiving_account_type", "custody_rules"],
         ["Can these private funds transfer in kind from another firm?", "Check whether the receiving account can custody these assets.", "Determine which prospect assets can be received and held."],
         [r"\btransfer\b|contra firm|receive and hold|custod|assets.{0,10}transfer"] ),
    spec("operations.order", "Operations", "Order and approval diagnosis", "diagnose", "order_status", ["authorized_scope", "order_reference", "order_status", "current_policy"],
         ["Diagnose a submitted order with an expired investor profile.", "Why is the submit button disabled and the deadline moved?", "Will an unavailable approver delay an order?", "Review entity eligibility for an offshore fund subscription."],
         [r"submitted.{0,15}order|order.{0,20}submitted|grayed out|greyed out|profile.{0,20}(?:expired|approved)|approver|sabbatical|requests to invest|offshore.{0,30}(?:entity|corporation)|us corporation"] ),
    spec("operations.distribution", "Operations", "Distribution and withholding reconciliation", "reconcile", "distribution_review", ["authorized_scope", "distribution_statement", "withholding_records", "tax_document_status"],
         ["Reconcile a distribution payment with its stated distributable amount.", "Why was tax withheld from this private fund payout?", "Check whether expired tax documentation affected a distribution."],
         [r"withhold|w.?8.?ben|distributable|amount payable|retained.{0,20}tax"] ),
    spec("instrument.payout", "Instrument analytics", "Structured-note payout", "calculate", "note_payout", ["authorized_scope", "verified_product_terms", "final_fixing", "notional", "position_quantity"],
         ["Calculate the maturity proceeds and cash available to reinvest.", "What is the realized return for the market linked note maturing tomorrow?", "Confirm the payoff after the instrument calculation date."],
         [r"maturing|maturity (?:payout|proceeds)|reinvestable|calculation date|confirm.{0,20}return|exactly how much.{0,30}receiv|\bpayoff\b"] ),
    spec("operations.data_issue", "Operations", "Product data issue", "diagnose", "data_quality_review", ["product_reference", "source_record", "data_owner"],
         ["Duplicate instrument symbols are corrupting archive return data.", "The market linked product website shows missing information.", "Report a product identifier collision in the archive."],
         [r"duplicate ticker|duplicate.{0,15}symbols|archive.{0,25}(?:missing|percentages)|data issue"] ),
    spec("directory.specialist", "Specialist routing", "Find a specialist or contact", "retrieve", "internal_directory", ["entitled_directory", "specialist_topic"],
         ["Find the product representative for a strategy.", "Connect me to a wholesaler who can answer fund questions.", "Who covers family office and philanthropic services?"],
         [r"\brep.s? name|\brepresentative\b|wholesaler|family office|philanthrop|put me in contact|somebody on your team|best way to connect|one stop shop"] ),
]

REGISTRY = {s.id: s for s in SPECS}

# Explicit dependencies are attached only when both tasks have been requested.
DEPENDENCIES = {
    "tax.transition": ("portfolio.overlap",),
    "solution.match": ("portfolio.exposure", "portfolio.drift", "tax.transition", "product.compare"),
    "content.draft": tuple(s.id for s in SPECS if s.id != "content.draft"),
    "meeting.prepare": ("performance.attribution", "portfolio.exposure", "research.cio"),
}
