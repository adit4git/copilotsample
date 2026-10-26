"""Portfolio math: class weights, expected return and volatility, tracking error, past-event results,
single-name exposure looking through funds, and the tax-lot sale rule. Illustrative capital market assumptions."""
from __future__ import annotations
import copy
import math
from .data import DATA
from .fmt import nsum

EQ = ['LCG', 'LCV', 'SMID', 'INTL', 'EM']
GROUP_OF = {'LCG': 'equity', 'LCV': 'equity', 'SMID': 'equity', 'INTL': 'equity', 'EM': 'equity',
            'UST': 'fixed', 'IGC': 'fixed', 'HY': 'fixed', 'CASH': 'cash', 'HF': 'alt', 'PE': 'alt'}
GROUPS = [('equity', 'Equity'), ('fixed', 'Fixed income'), ('cash', 'Cash'), ('alt', 'Alternatives')]


def corr(a: str, b: str) -> float:
    if a == b:
        return 1.0
    c = DATA['corr']
    v = c.get(a + '|' + b)
    if v is None:
        v = c.get(b + '|' + a)
    return 0.0 if v is None else v


def weights(hs: list[dict]) -> dict:
    by: dict = {}
    ct = un = 0.0
    for h in hs:
        cl = h.get('classes') or {}
        if not cl:
            un += h['mv']
            continue
        ct += h['mv']
        for k, f in cl.items():
            by[k] = by.get(k, 0) + h['mv'] * f
    w = {k: (v / ct if ct else 0) for k, v in by.items()}
    return {'w': w, 'ct': ct, 'total': ct + un}


def groups(w: dict) -> dict:
    g = {'equity': 0.0, 'fixed': 0.0, 'cash': 0.0, 'alt': 0.0}
    for k, v in w.items():
        g[GROUP_OF[k]] += v
    return g


def stats(w: dict) -> dict:
    C = DATA['classes']
    er = v = 0.0
    for a in w:
        er += w[a] * C[a]['er']
        for b in w:
            v += w[a] * w[b] * C[a]['vol'] * C[b]['vol'] * corr(a, b)
    return {'er': er, 'vol': math.sqrt(max(v, 0))}


def te(w1: dict, w2: dict) -> float:
    ks = list(dict.fromkeys(list(w1) + list(w2)))
    C = DATA['classes']
    v = 0.0
    for a in ks:
        for b in ks:
            v += (w1.get(a, 0) - w2.get(a, 0)) * (w1.get(b, 0) - w2.get(b, 0)) * C[a]['vol'] * C[b]['vol'] * corr(a, b)
    return math.sqrt(max(v, 0))


def stress(hs: list[dict]) -> dict:
    cls_ = [h for h in hs if h.get('classes')]
    ct = nsum(h['mv'] for h in cls_)
    out = {}
    for sc in DATA['scenarios']:
        p = nsum(h['mv'] * ((h.get('scret') or {}).get(sc['id']) or 0) for h in cls_)
        out[sc['id']] = p / ct if ct else 0
    return out


def names(hs: list[dict]) -> dict:
    """Single-name exposure as a share of the total, including what funds hold."""
    n: dict = {}
    tot = nsum(h['mv'] for h in hs)
    for h in hs:
        if h.get('kind') == 'stock':
            n[h['sym']] = n.get(h['sym'], 0) + h['mv']
        for s, w in (h.get('top_holdings') or {}).items():
            n[s] = n.get(s, 0) + h['mv'] * w
    return {k: v / (tot or 1) for k, v in n.items()}


def expense(hs: list[dict]) -> float:
    t = nsum(h['mv'] for h in hs) or 1
    return nsum(h['mv'] * (h.get('expense_bps') or 0) for h in hs) / t


def sell_plan(hh: dict, hs: list[dict], sym: str, amount: float) -> dict:
    """Tax-lot sale: losses first (largest first), then long-term lots by smallest gain, short-term last; never lots without basis."""
    rates = hh['rates']
    lots = []
    for i, h in enumerate(hs):
        if h['sym'] != sym:
            continue
        for j, l in enumerate(h.get('lots') or []):
            if l['mv'] > 0.5:
                lots.append({'i': i, 'j': j, 'l': l, 'g': None if l.get('cost') is None else (l['mv'] - l['cost']) / l['mv']})
    sellable = [x for x in lots if x['g'] is not None]
    sellable.sort(key=lambda x: -10 + x['g'] if x['g'] < 0 else (10 if x['l'].get('term') == 'ST' else 0) + x['g'])
    left, gain, tax, used = amount, 0.0, 0.0, []
    for x in sellable:
        if left <= 0.5:
            break
        take = min(left, x['l']['mv'])
        gn = (x['l']['mv'] - x['l']['cost']) * (take / x['l']['mv'])
        gain += gn
        tax += gn * (rates['st'] if x['l'].get('term') == 'ST' else rates['lt']) if rates.get('taxable') else 0
        used.append({**x, 'take': take})
        left -= take
    return {'gain': gain, 'tax': tax, 'used': used, 'unfilled': max(0, left),
            'excluded': nsum(x['l']['mv'] for x in lots if x['g'] is None)}


def fund_as_holding(sym: str, amount: float) -> dict | None:
    f = DATA['funds'].get(sym)
    if not f:
        return None
    return {'sym': sym, 'name': f['name'], 'kind': f['kind'], 'mv': amount, 'tradable': True, 'classes': f['classes'],
            'sectors': f.get('sectors'), 'sector': f.get('sector'), 'yield': f.get('yield') or 0, 'top_holdings': f.get('top_holdings'),
            'expense_bps': f.get('expense_bps'), 'style_box': f.get('style_box'), 'scret': f.get('scret'),
            'lots': [{'id': sym + ' (new)', 'cost': amount, 'mv': amount, 'term': 'ST'}], 'bought': True}


def apply(hh: dict, lines: list[dict]) -> dict:
    """Apply sell and buy lines to a copy of the holdings: sells by tax lot, buys paid from proceeds, then cash."""
    hs = [{**h, 'lots': [dict(l) for l in (h.get('lots') or [])]} for h in hh['holdings']]
    proceeds = gain = tax = 0.0
    for t in [x for x in lines if x['action'] == 'sell']:
        p = sell_plan(hh, hs, t['sym'], t['amount'])
        for u in p['used']:
            h = hs[u['i']]; l = h['lots'][u['j']]; f = u['take'] / l['mv']
            if l.get('cost') is not None:
                l['cost'] *= (1 - f)
            l['mv'] -= u['take']; h['mv'] -= u['take']
        proceeds += t['amount'] - p['unfilled']; gain += p['gain']; tax += p['tax']
    buys = [x for x in lines if x['action'] == 'buy']
    need = nsum(t['amount'] for t in buys) - proceeds
    if need > 0:
        for h in [h for h in hs if h.get('cash')]:
            a = min(h['mv'], need); h['mv'] -= a; need -= a
    elif need < 0:
        c = next((h for h in hs if h['sym'] == 'CASH'), None)
        if c is None:
            c = {'sym': 'CASH', 'name': 'Cash', 'kind': 'cash', 'cash': True, 'mv': 0, 'classes': {'CASH': 1}, 'yield': 0.04, 'scret': {}, 'lots': []}
            hs.append(c)
        c['mv'] += -need
    for t in buys:
        nh = fund_as_holding(t['sym'], t['amount'])
        if nh:
            hs.append(nh)
    return {'hs': [h for h in hs if h['mv'] > 0.5], 'proceeds': proceeds, 'gain': gain, 'tax': tax}


def metrics(hh: dict, hs: list[dict]) -> dict:
    W = weights(hs); st = stats(W['w']); s = stress(hs)
    worst = DATA['scenarios'][0]
    for sc in DATA['scenarios']:
        if s[sc['id']] < s[worst['id']]:
            worst = sc
    return {'w': W['w'], 'er': st['er'], 'vol': st['vol'], 'stress': s, 'worst': worst['id'], 'names': names(hs),
            'te_t': te(W['w'], hh['target']), 'te_m': te(W['w'], hh['model_w'])}
