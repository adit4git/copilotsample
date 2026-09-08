"""Small deterministic, three-state product-constraint demonstration."""
import json
import math
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"


def load_catalog():
    return json.loads((DATA / "sma_catalog.json").read_text())


def screen_product(product, *, platform, index, amount, holds_etf=False, holds_mutual_fund=False, concentration=0.0):
    if not math.isfinite(float(amount)) or not math.isfinite(float(concentration)) or amount < 0 or not 0 <= concentration <= 1:
        raise ValueError("Amount must be nonnegative and concentration must be between 0 and 1.")
    checks = []
    def add(name, verdict, reason):
        checks.append({"check": name, "result": verdict, "reason": reason})
    add("platform", "pass" if product["platform"] == platform else "fail", f"Catalog platform: {product['platform']}")
    add("index", "pass" if product["index"] == index else "fail", f"Catalog index: {product['index']}")
    minimum = product.get("minimum")
    add("minimum", "unknown" if minimum is None else ("pass" if amount >= minimum else "fail"),
        "Minimum not provided" if minimum is None else f"Catalog minimum: ${minimum:,.0f}")
    for requested, field in [(holds_etf, "permits_etf"), (holds_mutual_fund, "permits_mutual_fund")]:
        if requested:
            value = product.get(field)
            add(field, "unknown" if value is None else ("pass" if value else "fail"), "Legacy holding acceptance requires explicit evidence.")
    if concentration > 0:
        limit = product.get("max_concentration")
        add("concentration", "unknown" if limit is None else ("pass" if concentration <= limit else "fail"),
            "Limit not available" if limit is None else f"Catalog concentration limit: {limit:.0%}")
    if not product.get("source_verified"):
        status = "UNKNOWN"
        note = "Unverified screenshot transcription; verify current product terms before determining eligibility."
    elif any(c["result"] == "fail" for c in checks):
        status, note = "FAILS_DEMO_RULES", "One or more modeled conditions fail."
    elif any(c["result"] == "unknown" for c in checks):
        status, note = "UNKNOWN", "Evidence for one or more requested conditions is missing."
    else:
        status, note = "PASSES_DEMO_RULES", "Passes only the modeled conditions; this is not suitability approval."
    return {"id": product["id"], "manager": product["manager"], "platform": product["platform"],
            "index": product["index"], "minimum": minimum, "fee_bps": product.get("fee_bps"),
            "status": status, "note": note, "checks": checks, "source": product["source"],
            "source_location": product["source_location"], "effective_date": product["effective_date"]}
