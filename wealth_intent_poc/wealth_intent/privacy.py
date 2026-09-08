"""Local minimization. Heuristic detection is NOT a de-identification guarantee.

There is deliberately no provider client, HTTP request, or LLM integration here.
Raw values are ephemeral: returned findings contain types and counts only.
"""
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class PrivacyResult:
    masked_text: str
    findings: dict[str, int]


PATTERNS = [
    ("EMAIL", r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    ("URL", r"https?://[^\s<>]+"),
    ("SSN", r"\b\d{3}[- ]\d{2}[- ]\d{4}\b"),
    ("PHONE", r"(?<!\w)(?:\+1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}\b"),
    ("ACCOUNT", r"\b[A-Z0-9]{3}[- ]\d{5}\b"),
    ("CUSTOMER_ID", r"\b(?:fid|customer id|client id)\s*[:#-]?\s*[A-Z0-9-]{5,}\b"),
    ("ACCOUNT", r"\b(?:account|acct)\s*(?:number|no\.?|#|id)?\s*[:#-]?\s*[A-Z0-9-]*\d[A-Z0-9-]{4,}\b"),
    ("ADDRESS", r"\b\d{1,6}\s+(?:[A-Z][a-z]+\s+){1,4}(?:Street|Road|Avenue|Drive|Lane|Boulevard|St\.?|Rd\.?|Ave\.?)\b"),
    ("MONEY", r"(?:\$|USD\s*)\s*\d[\d,]*(?:\.\d+)?\s*(?:million|billion|thousand|mm|m|k)?\b"),
    ("MONEY", r"\b\d+(?:\.\d+)?\s*(?:million|billion|mm)\b"),
    ("DATE", r"\b\d{1,4}[-/]\d{1,2}[-/]\d{1,4}\b"),
    ("LONG_ID", r"\b\d{8,}\b"),
]

KNOWN_PRODUCTS = (
    "Goldman Sachs", "Franklin Templeton", "T. Rowe Price", "Russell 3000",
    "Russell 2000", "S&P 500", "Capital Group", "CIO ETF Core", "BlackRock",
    "Eaton Vance", "Columbia Threadneedle", "Tax Managed SMA",
)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", str(text))
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    return re.sub(r"[ \t]+", " ", text.replace("’", "'")).strip()


def mask(text: str, sensitive_terms=()) -> PrivacyResult:
    text = normalize(text)
    spans = []
    # A user-maintained local dictionary supplements generic patterns.
    for term in sensitive_terms:
        if term.strip():
            spans += [(m.start(), m.end(), "CUSTOM_TERM") for m in re.finditer(re.escape(term.strip()), text, re.I)]
    for kind, pattern in PATTERNS:
        spans += [(m.start(), m.end(), kind) for m in re.finditer(pattern, text, re.I)]
    # Conservative capitalization heuristic; not an NER model.
    protected = [(m.start(), m.end()) for term in KNOWN_PRODUCTS for m in re.finditer(re.escape(term), text, re.I)]
    person_input = list(text)
    for a, b in protected:
        person_input[a:b] = " " * (b-a)
    person = r"\b[A-Z][a-z]{1,}(?:[ '-][A-Z][a-z]{1,}){1,3}\b"
    for m in re.finditer(person, "".join(person_input)):
        spans.append((m.start(), m.end(), "POSSIBLE_NAME"))
    for m in re.finditer(r"\b(?:client|customer|prospect|Mrs\.?|Mr\.?)\s+(?:named\s+)?([A-Z][a-z]{1,})\b", text):
        if m.group(1).lower() not in {"has", "is", "wants", "needs", "with", "in", "the"}:
            spans.append((m.start(1), m.end(1), "POSSIBLE_NAME"))
    # Longest match at each position wins; overlapping findings count once.
    spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    accepted, end = [], -1
    for a, b, kind in spans:
        if a >= end:
            accepted.append((a, b, kind))
            end = b
    findings = Counter(kind for _, _, kind in accepted)
    out, last = [], 0
    for a, b, kind in accepted:
        out.extend([text[last:a], f"[{kind}]"])
        last = b
    out.append(text[last:])
    return PrivacyResult("".join(out), dict(findings))


class LLMDisabledError(RuntimeError):
    pass


class EgressGateway:
    """Closed boundary, including future accidental attempts to send text."""
    enabled = False

    @staticmethod
    def send(*args, **kwargs):
        raise LLMDisabledError("LLM egress is disabled in this proof of concept.")

    @staticmethod
    def preview(intent_ids: list[str]) -> dict:
        # Registry lookup is an allowlist; no caller-provided free text is copied.
        from .registry import REGISTRY
        if any(i not in REGISTRY for i in intent_ids):
            raise ValueError("Unregistered intent cannot enter the template contract.")
        return {"egress_enabled": False, "outbound_requests": 0,
                "illustrative_template_contract": {"task_ids": list(intent_ids),
                "style": "advisor_explanation", "client_data": "excluded"}}
