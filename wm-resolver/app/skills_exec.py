"""
skills_exec.py
==============
Mock "skill" implementations. In production each of these would call a
portfolio engine, a custodian API, a planning engine, or a document service.
Here they return believable fabricated data so the resolution flow can be
demoed end-to-end.

Each skill takes the resolved `entities` dict and returns:
    { "summary": str, "data": {...} }
"""

from __future__ import annotations
from typing import Any

# A tiny fake book of business so results reference consistent "clients".
_BOOK = {
    "henderson": {"aum": 4_200_000, "model": "Growth 80/20", "top": ("NVDA", 0.19)},
    "patel":     {"aum": 2_800_000, "model": "Balanced 60/40", "top": ("AAPL", 0.11)},
    "okafor":    {"aum": 6_500_000, "model": "Conservative 40/60", "top": ("MSFT", 0.22)},
    "kim":       {"aum": 1_500_000, "model": "Growth 80/20", "top": ("AMZN", 0.09)},
    "lee":       {"aum": 3_100_000, "model": "Balanced 60/40", "top": ("GOOGL", 0.14)},
    "garcia":    {"aum": 2_200_000, "model": "Target 2035 Glide", "top": ("VTI", 0.3)},
}


def _book(client: Any) -> dict:
    key = str(client or "").lower().rstrip("s")
    for k, v in _BOOK.items():
        if k in key or key in k:
            return {"name": str(client).title(), **v}
    return {"name": str(client).title() or "Client", "aum": 2_000_000,
            "model": "Balanced 60/40", "top": ("SPY", 0.08)}


def run(skill_id: str, entities: dict, file_text: str | None = None) -> dict:
    fn = _REGISTRY.get(skill_id, _unimplemented)
    return fn(entities, file_text)


# --- individual skills -----------------------------------------------------
def _performance(e, _f):
    b = _book(e.get("client"))
    tr = e.get("time_range", "the period")
    bench = e.get("benchmark", "absolute")
    ret, bret = 7.4, 6.1
    return {"summary": f"{b['name']}: +{ret}% for {tr} vs {bench} "
                       f"({'+' if bret>=0 else ''}{bret}%). Driven by tech overweight; "
                       f"top contributor {b['top'][0]}.",
            "data": {"client": b["name"], "return_pct": ret, "benchmark": bench,
                     "benchmark_pct": bret, "time_range": tr}}


def _concentration(e, _f):
    b = _book(e.get("client"))
    thr = e.get("threshold", "10%")
    tick, w = b["top"]
    flagged = w >= float(str(thr).rstrip("%")) / 100
    return {"summary": f"{b['name']}: largest position {tick} at {w*100:.0f}% "
                       f"({'OVER' if flagged else 'under'} the {thr} limit)."
                       + (f" Recommend trimming ~{(w-float(str(thr).rstrip('%'))/100)*b['aum']:,.0f}."
                          if flagged else " No action needed."),
            "data": {"client": b["name"], "top_position": tick,
                     "weight_pct": round(w*100, 1), "threshold": thr, "flagged": flagged}}


def _drift(e, _f):
    b = _book(e.get("client"))
    tax = e.get("tax_aware", "tax-aware")
    return {"summary": f"{b['name']} vs {b['model']}: equity +6.2pts, bonds -4.8pts, "
                       f"cash -1.4pts. Proposed {tax} rebalance: sell $118k equities, "
                       f"buy $92k fixed income, $26k to cash. 3 lots flagged for wash-sale.",
            "data": {"client": b["name"], "model": b["model"], "tax_aware": tax,
                     "trades": [{"action": "SELL", "amt": 118000, "asset": "equities"},
                                {"action": "BUY", "amt": 92000, "asset": "fixed income"}]}}


def _tlh(e, _f):
    b = _book(e.get("client"))
    floor = e.get("min_loss", "$3,000")
    return {"summary": f"{b['name']}: 4 harvestable lots totaling $47,300 in losses "
                       f"(min {floor}/lot). Suggested pairs avoid wash sales via ETF swaps. "
                       f"Est. tax benefit ~$11,200 at a 23.8% rate.",
            "data": {"client": b["name"], "harvestable_loss": 47300, "lots": 4,
                     "est_benefit": 11200}}


def _realized(e, _f):
    b = _book(e.get("client"))
    tr = e.get("time_range", "2025")
    return {"summary": f"{b['name']} realized ({tr}): ST +$14,200, LT +$63,800. "
                       f"Est. federal liability ~$18,900. $9k of carryforward losses available.",
            "data": {"client": b["name"], "st_gain": 14200, "lt_gain": 63800,
                     "time_range": tr}}


def _retirement(e, _f):
    b = _book(e.get("client"))
    age = e.get("retirement_age", "?")
    spend = e.get("annual_spend", "their target")
    prob = 84
    return {"summary": f"{b['name']} retiring at {age}, spending {spend}/yr: "
                       f"Monte Carlo success probability {prob}% (2,000 paths). "
                       f"Shortfall risk concentrated in first-5-year sequence; "
                       f"consider a 2-yr cash buffer.",
            "data": {"client": b["name"], "retirement_age": age,
                     "annual_spend": spend, "success_prob": prob}}


def _cashflow(e, _f):
    b = _book(e.get("client"))
    amt = e.get("amount", "the amount")
    when = e.get("by_when", "")
    return {"summary": f"{b['name']} needs {amt}{' by ' + when if when else ''}. "
                       f"Raise from: $160k money-market, $140k trim of overweight {b['top'][0]} "
                       f"(gain-aware), $100k pending dividend sweep. Net tax drag ~$6k.",
            "data": {"client": b["name"], "amount": amt, "by_when": when}}


def _account_status(e, _f):
    b = _book(e.get("client"))
    field = e.get("field", "balance")
    facts = {"balance": f"${b['aum']:,}", "available cash": f"${int(b['aum']*0.04):,}",
             "pending acats": "1 inbound ACATS, ~$310k, settles T+2 (2 days left)",
             "beneficiaries": "Primary: spouse (100%). Contingent: 2 children (50/50)."}
    key = next((k for k in facts if k in str(field).lower()), "balance")
    return {"summary": f"{b['name']} — {key}: {facts[key]}.",
            "data": {"client": b["name"], "field": key, "value": facts[key]}}


def _doc_extract(e, file_text):
    body = (file_text or "")[:400]
    found = "balances and holdings" if file_text else "no file content received"
    return {"summary": f"Read the uploaded document. Extracted {found}. "
                       f"(Preview parsed below.) Ready to import as held-away assets.",
            "data": {"target_fields": e.get("target_fields", "all"),
                     "preview": body}}


def _unimplemented(e, _f):
    return {"summary": "That skill isn't wired up in this POC yet.", "data": {}}


_REGISTRY = {
    "portfolio_analysis.performance": _performance,
    "portfolio_analysis.concentration_check": _concentration,
    "portfolio_analysis.drift_rebalance": _drift,
    "tax.loss_harvest": _tlh,
    "tax.realized_gains": _realized,
    "planning.retirement_readiness": _retirement,
    "planning.cash_flow": _cashflow,
    "service.account_status": _account_status,
    "service.document_extract": _doc_extract,
}
