"""
schema.py
=========
Intent / sub-intent / entity taxonomy for a wealth-management advisor copilot.

Design notes
------------
The resolution problem has three layers:

  1. INTENT         - the broad job the advisor wants done ("portfolio_analysis")
  2. SUB_INTENT     - the specific variant that maps 1:1 to a runnable skill
                      ("portfolio_analysis.concentration_check")
  3. ENTITIES/SLOTS - the parameters a skill needs before it can run
                      (client_id, holding, time_range, ...)

A query resolves only when (a) a sub-intent is chosen with enough confidence
and (b) every REQUIRED slot for that sub-intent is filled. Anything missing
triggers a clarification turn instead of a guess. This is the core reason the
system is multi-turn: advisors type terse, context-free fragments
("rebalance the Hendersons") and the missing pieces have to be elicited.

Everything here is plain data so the resolver, the LLM prompt, and the
front-end can all read from one source of truth.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# --------------------------------------------------------------------------
# Slot (entity) definitions
# --------------------------------------------------------------------------
@dataclass
class Slot:
    name: str
    description: str                 # shown to the LLM and used in clarifications
    required: bool = True
    # If the slot can be resolved from an uploaded file instead of text,
    # list the modalities the file-reader can satisfy it with.
    fillable_from_file: bool = False
    # Optional closed vocabulary. When present the resolver can validate /
    # the clarification UI can render chips instead of a free-text prompt.
    options: Optional[list[str]] = None
    # A natural clarifying question to ask when this slot is missing.
    # The LLM may rephrase it with context, but this is the deterministic fallback.
    clarify: str = ""


# --------------------------------------------------------------------------
# Skill definitions  (sub-intent == skill)
# --------------------------------------------------------------------------
@dataclass
class Skill:
    id: str                          # "portfolio_analysis.concentration_check"
    intent: str                      # "portfolio_analysis"
    title: str                       # human label
    description: str                 # what it does; used for LLM routing
    slots: list[Slot] = field(default_factory=list)
    # Example utterances help the LLM disambiguate sibling sub-intents.
    examples: list[str] = field(default_factory=list)

    @property
    def required_slots(self) -> list[Slot]:
        return [s for s in self.slots if s.required]


# Reusable slot builders -----------------------------------------------------
def client_slot(required: bool = True) -> Slot:
    return Slot(
        name="client",
        description="The client, household, or account the request is about. "
                    "A name ('the Hendersons'), an account number, or a household id.",
        required=required,
        fillable_from_file=True,
        clarify="Which client or household is this for?",
    )


def time_range_slot(required: bool = True) -> Slot:
    return Slot(
        name="time_range",
        description="The period the request covers, e.g. 'YTD', 'last quarter', "
                    "'since inception', '2025-01-01 to 2025-06-30'.",
        required=required,
        clarify="What time period should I use?",
    )


# --------------------------------------------------------------------------
# The skill catalog
# --------------------------------------------------------------------------
SKILLS: list[Skill] = [
    # ----- PORTFOLIO ANALYSIS ---------------------------------------------
    Skill(
        id="portfolio_analysis.performance",
        intent="portfolio_analysis",
        title="Performance review",
        description="Return / performance attribution for a client's portfolio "
                    "over a period, vs a benchmark.",
        slots=[
            client_slot(),
            time_range_slot(),
            Slot(name="benchmark", description="Benchmark to compare against "
                 "(e.g. S&P 500, 60/40, a model portfolio).",
                 required=False, options=["S&P 500", "60/40", "ACWI", "household IPS benchmark"],
                 clarify="Any benchmark to compare against, or just absolute return?"),
        ],
        examples=["how did the Patels do last quarter",
                  "ytd performance for the Henderson trust vs the s&p"],
    ),
    Skill(
        id="portfolio_analysis.concentration_check",
        intent="portfolio_analysis",
        title="Concentration / single-position risk",
        description="Flag over-concentrated positions, single-stock risk, or "
                    "sector overweights relative to policy limits.",
        slots=[
            client_slot(),
            Slot(name="threshold", description="Concentration threshold of concern, "
                 "as a percent of portfolio (default 10%).", required=False,
                 clarify="What concentration threshold should flag a position? (default 10%)"),
        ],
        examples=["is the Okafor account too concentrated",
                  "any single stock over 15% for my biggest client"],
    ),
    Skill(
        id="portfolio_analysis.drift_rebalance",
        intent="portfolio_analysis",
        title="Drift check & rebalance proposal",
        description="Compare current allocation to the target/model, report drift, "
                    "and propose rebalancing trades.",
        slots=[
            client_slot(),
            Slot(name="model", description="The target model or IPS allocation to "
                 "rebalance toward.", required=False,
                 clarify="Rebalance toward which model/target allocation?"),
            Slot(name="tax_aware", description="Whether to make the proposal tax-aware "
                 "(harvest losses, respect lots). true/false.", required=False,
                 options=["tax-aware", "ignore taxes"],
                 clarify="Should the rebalance be tax-aware or straight-to-target?"),
        ],
        examples=["rebalance the Hendersons", "how far has the Lee portfolio drifted"],
    ),

    # ----- TAX -------------------------------------------------------------
    Skill(
        id="tax.loss_harvest",
        intent="tax",
        title="Tax-loss harvesting scan",
        description="Find positions with unrealized losses that can be harvested, "
                    "respecting wash-sale rules.",
        slots=[
            client_slot(),
            Slot(name="min_loss", description="Minimum unrealized loss per lot to be "
                 "worth harvesting, in dollars.", required=False,
                 clarify="Minimum loss size worth harvesting? (default $3,000)"),
        ],
        examples=["any losses to harvest for the Kims before year end",
                  "tlh candidates in the joint account"],
    ),
    Skill(
        id="tax.realized_gains",
        intent="tax",
        title="Realized gain/loss summary",
        description="Summarize realized short- and long-term gains/losses for a "
                    "tax year to estimate liability.",
        slots=[client_slot(), time_range_slot()],
        examples=["realized gains for the Patels this year",
                  "what's the cap gains situation on the Okafor trust for 2025"],
    ),

    # ----- PLANNING --------------------------------------------------------
    Skill(
        id="planning.retirement_readiness",
        intent="planning",
        title="Retirement readiness",
        description="Run a retirement projection / Monte Carlo and report probability "
                    "of success given goals and spending.",
        slots=[
            client_slot(),
            Slot(name="retirement_age", description="Target retirement age.",
                 required=True, clarify="At what age do they plan to retire?"),
            Slot(name="annual_spend", description="Planned annual retirement spending "
                 "(today's dollars).", required=True,
                 fillable_from_file=True,
                 clarify="What's the target annual spending in retirement?"),
        ],
        examples=["can the Garcias retire at 62",
                  "run a monte carlo for my client retiring next year"],
    ),
    Skill(
        id="planning.cash_flow",
        intent="planning",
        title="Liquidity / cash-flow need",
        description="Assess ability to meet a one-off or recurring cash need and "
                    "recommend where to raise it from.",
        slots=[
            client_slot(),
            Slot(name="amount", description="The cash amount needed.", required=True,
                 clarify="How much cash do they need to raise?"),
            Slot(name="by_when", description="When the cash is needed.", required=False,
                 clarify="By when do they need it?"),
        ],
        examples=["the Lees need 400k for a house down payment",
                  "where do I raise cash for my client's tax bill"],
    ),

    # ----- CLIENT SERVICE / OPS -------------------------------------------
    Skill(
        id="service.account_status",
        intent="service",
        title="Account status / factual lookup",
        description="Answer a factual question about an account: balance, cash, "
                    "pending transfers, cost basis, beneficiaries.",
        slots=[
            client_slot(),
            Slot(name="field", description="Which fact is being asked for "
                 "(balance, available cash, pending ACATS, beneficiaries, etc).",
                 required=True,
                 clarify="What specifically do you want to know about the account?"),
        ],
        examples=["how much cash does the Okafor account have",
                  "is the Henderson ACAT transfer done yet"],
    ),
    Skill(
        id="service.document_extract",
        intent="service",
        title="Extract data from an uploaded document",
        description="Pull structured facts out of an uploaded statement, screenshot, "
                    "or form (held-away balances, outside holdings, a 1099).",
        slots=[
            Slot(name="document", description="The uploaded file to read.",
                 required=True, fillable_from_file=True,
                 clarify="Please attach the statement or screenshot you want me to read."),
            Slot(name="target_fields", description="What to extract "
                 "(holdings, balances, account number, cost basis...).", required=False,
                 clarify="What should I pull out of it?"),
        ],
        examples=["pull the holdings off this held-away 401k statement",
                  "what's the balance on this screenshot"],
    ),
]

# Index for O(1) lookups ----------------------------------------------------
SKILLS_BY_ID: dict[str, Skill] = {s.id: s for s in SKILLS}
INTENTS: list[str] = sorted({s.intent for s in SKILLS})


def catalog_for_prompt() -> str:
    """Compact, LLM-friendly rendering of the catalog for the router prompt."""
    lines = []
    for s in SKILLS:
        req = ", ".join(sl.name for sl in s.required_slots) or "(none)"
        opt = ", ".join(sl.name for sl in s.slots if not sl.required) or "(none)"
        ex = " | ".join(s.examples)
        lines.append(
            f"- id: {s.id}\n"
            f"    intent: {s.intent}\n"
            f"    does: {s.description}\n"
            f"    required_slots: {req}\n"
            f"    optional_slots: {opt}\n"
            f"    examples: {ex}"
        )
    return "\n".join(lines)
