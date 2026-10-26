"""Number and label formatting, matching the page exactly (JavaScript toFixed and Math.round semantics)."""
from __future__ import annotations
import math
from decimal import Decimal, ROUND_HALF_UP
from .data import DATA


def to_fixed(x: float, d: int = 0) -> str:
    """JavaScript Number.prototype.toFixed: round the exact binary value, ties away from zero."""
    q = Decimal(1).scaleb(-d)
    v = Decimal(x).quantize(q, rounding=ROUND_HALF_UP)
    s = format(v, 'f')
    return s.lstrip('-') if v == 0 else s


def js_round(x: float) -> int:
    """JavaScript Math.round."""
    return int(math.floor(x + 0.5))


def num(x) -> str:
    """How a JavaScript template literal prints a number."""
    if isinstance(x, bool):
        return 'true' if x else 'false'
    if isinstance(x, int):
        return str(x)
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return repr(x)


def _bad(x) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x))


def money(n, d: int | None = None) -> str:
    if _bad(n):
        return '—'
    s = '−' if n < 0 else ''
    n = abs(n)
    if n >= 1e6:
        return s + '$' + to_fixed(n / 1e6, 2 if d is None else d) + 'M'
    if n >= 1e4:
        return s + '$' + str(js_round(n / 1e3)) + 'K'
    return s + '$' + f'{js_round(n):,}'


def pct(x, d: int = 0) -> str:
    if _bad(x):
        return '—'
    return ('−' if x < 0 else '') + to_fixed(abs(x * 100), d) + '%'


def spct(x, d: int = 1) -> str:
    return ('+' if x >= 0 else '−') + to_fixed(abs(x * 100), d) + '%'


def ppt(x, d: int = 1) -> str:
    return ('+' if x >= 0 else '−') + to_fixed(abs(x * 100), d) + ' pts'


def cls(k: str) -> str:
    c = DATA['classes'].get(k)
    return c['label'] if c else DATA['sectors'].get(k, k)


def short(k: str) -> str:
    return (cls(k).replace('U.S. ', 'US ', 1).replace('International Developed Equity', 'International developed', 1)
            .replace('Emerging Markets Equity', 'Emerging markets', 1).replace('U.S. Corporates (IG)', 'IG corporates', 1))


def lc(t: str) -> str:
    import re
    t = t.lower()
    t = re.sub(r'\bus\b', 'US', t)
    return re.sub(r'\big\b', 'IG', t)


def nsum(it, start=0):
    """Left-to-right addition, like JavaScript's reduce. Python's sum() compensates rounding (3.12+) and can differ in the last bit,
    which changes how exact ties (e.g. 565,500 → $566K) round on screen."""
    s = start
    for x in it:
        s = s + x
    return s
