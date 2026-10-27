"""Operations that technical skills can call.

A technical skill never carries arbitrary code. It names one operation from this library and
gives it parameters, so a skill written from an English description is safe to run and review.
Each operation reads from and writes to the run context, and returns a one-line summary.
"""
from __future__ import annotations
import copy
from .logic import evaluate, money
from .registry import load_json


def _items(ctx, key):
    v = ctx.get(key)
    if not isinstance(v, list):
        raise ValueError(f"'{key}' is not available as a list in this run")
    return v


def load_dataset(ctx: dict, p: dict) -> str:
    """Load the approved list and keep the rows that match a condition."""
    rows = load_json(f"{p.get('dataset', 'managers')}.json")['managers']
    where = p.get('where')
    out = [copy.deepcopy(r) for r in rows if not where or evaluate(where, {**ctx, 'item': r, 'params': p})]
    ctx[p.get('into', 'candidates')] = out
    return f"{len(out)} of {len(rows)} rows match ({ctx['request'].get('asset_class_label', '')})"


def weighted_score(ctx: dict, p: dict) -> str:
    """Score each item 0–100 from min–max normalized fields with weights. `better` says whether high or low is good."""
    items = _items(ctx, p.get('over', 'eligible'))
    weights = p.get('weights') or {}
    better = p.get('better') or {}
    tot = sum(weights.values()) or 1
    rng = {}
    for f in weights:
        vals = [float(i.get(f) or 0) for i in items]
        rng[f] = (min(vals), max(vals)) if vals else (0, 0)
    for it in items:
        parts = {}
        for f, w in weights.items():
            lo, hi = rng[f]
            x = float(it.get(f) or 0)
            n = 0.5 if hi == lo else (x - lo) / (hi - lo)
            if better.get(f, 'high') == 'low':
                n = 1 - n
            parts[f] = round(100 * n * w / tot, 1)
        it['score_parts'] = parts
        it['score'] = round(sum(parts.values()), 1)
    items.sort(key=lambda i: -i['score'])
    ctx[p.get('into', p.get('over', 'eligible'))] = items
    top = items[0] if items else None
    return f"{len(items)} scored; highest {top['name']} ({top['score']:.0f})" if top else 'nothing to score'


def lookthrough_overlap(ctx: dict, p: dict) -> str:
    """How much of each candidate's top holdings the client already owns, and whether it adds to the concentrated name."""
    items = _items(ctx, p.get('over', 'scored'))
    exp = ctx['client'].get('exposure') or {}
    mn = float(p.get('min_client_weight', 0.01))
    conc = ctx.get('concentration') or {}
    top = conc.get('top_name') if conc.get('top_share', 0) > conc.get('threshold', 0.10) else None
    n = 0
    for it in items:
        names = [s for s in (it.get('top_holdings') or {}) if exp.get(s, 0) >= mn]
        it['overlap_names'] = names
        it['overlap_pct'] = round(sum(it['top_holdings'][s] for s in names), 4)
        it['adds_to_concentration'] = bool(top and top in (it.get('top_holdings') or {}))
        n += bool(names)
    return f"{n} of {len(items)} overlap with holdings the client already owns"


def fee_comparison(ctx: dict, p: dict) -> str:
    """Annual fee for each candidate on the amount, against the lower-cost index alternative for the asset class."""
    items = _items(ctx, p.get('over', 'ranked'))
    amt = float(ctx['request'].get('amount') or 0)
    ac = load_json('asset_classes.json')[ctx['request']['asset_class']]
    alt = next(m for m in load_json('managers.json')['managers'] if m['id'] == ac['index_alternative'])
    ctx[p.get('alternative_into', 'alternative')] = {'name': alt['name'], 'fee_bps': alt['fee_bps'], 'annual_fee': round(amt * alt['fee_bps'] / 1e4)}
    for it in items:
        it['annual_fee'] = round(amt * it['fee_bps'] / 1e4)
        it['extra_vs_index'] = it['annual_fee'] - ctx['alternative']['annual_fee']
    return f"lower-cost alternative {alt['name']} at {alt['fee_bps']} bp ({money(ctx['alternative']['annual_fee'])} a year)"


def concentration_facts(ctx: dict, p: dict) -> str:
    """The client's largest single-company exposure and every name above the threshold."""
    exp = ctx['client'].get('exposure') or {}
    th = float(p.get('threshold', 0.10))
    name, share = max(exp.items(), key=lambda kv: kv[1]) if exp else (None, 0.0)
    over = [k for k, v in sorted(exp.items(), key=lambda kv: -kv[1]) if v > th]
    ctx[p.get('into', 'concentration')] = {'top_name': name, 'top_share': share, 'over_threshold': over, 'threshold': th}
    return f"largest name {name} at {share * 100:.1f}%; {len(over)} above {th * 100:.0f}%"


OPS = {
    'load_dataset': (load_dataset, 'Load the approved list and filter it', ['request'], ['candidates']),
    'weighted_score': (weighted_score, 'Score candidates with weights', ['eligible'], ['scored']),
    'lookthrough_overlap': (lookthrough_overlap, "Check overlap with the client's holdings", ['client'], []),
    'fee_comparison': (fee_comparison, 'Compare fees with the lower-cost alternative', ['request'], ['alternative']),
    'concentration_facts': (concentration_facts, 'Find single-company concentration', ['client'], ['concentration']),
}
