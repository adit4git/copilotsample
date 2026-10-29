"""Validation, household comparison, proposals, policy checks and the recommended workflow.

The portfolio math matches Portfolio Review: class weights, expected return, risk = sqrt(w' S w), Sharpe against the
risk-free rate, tracking error against the target, historical event stress from security-level (or class-proxy) returns,
look-through single-name exposure, and tax on realized gains from cost basis.
"""
from __future__ import annotations

import json
import math
import re
from copy import deepcopy
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

DATA = Path(__file__).resolve().parent / 'data'
SEC = json.loads((DATA / 'securities.json').read_text())
MKT = json.loads((DATA / 'market.json').read_text())
HH = json.loads((DATA / 'households.json').read_text())['households']
APPROVED = {a['sym']: a for a in SEC['approved']}
REFERENCE = {a['sym']: a for a in SEC['reference']}
CLASSES = list(MKT['classes'])
GROUPS = {'Equity': 'equity', 'Fixed income': 'fixed', 'Cash': 'cash', 'Alternatives': 'alt'}
TODAY = date(2026, 10, 28)
STALE_DAYS = 90
TILT = {'Overweight': 1.25, 'Neutral': 1.0, 'Underweight': 0.75}

STATUS_LABEL = {'approved': 'Approved', 'review': 'Approved, under review', 'not_approved': 'Not approved', 'unrecognized': 'Not recognized',
                'held_away': 'Held away', 'cash': 'Cash', 'excluded': 'Excluded'}

# ---------------------------------------------------------------------------------------------------------------- math

def cov(a, b):
    ca, cb = MKT['classes'][a], MKT['classes'][b]
    return MKT['corr'][f'{a}|{b}'] * ca['vol'] * cb['vol']


def class_stats(w: dict) -> dict:
    er = sum(w.get(c, 0) * MKT['classes'][c]['er'] for c in CLASSES)
    var = sum(w.get(a, 0) * w.get(b, 0) * cov(a, b) for a in CLASSES for b in CLASSES)
    vol = math.sqrt(max(var, 0))
    return {'er': er, 'vol': vol, 'sharpe': (er - MKT['rf']) / vol if vol else 0}


def te(w, t):
    d = {c: w.get(c, 0) - t.get(c, 0) for c in CLASSES}
    return math.sqrt(max(0, sum(d[a] * d[b] * cov(a, b) for a in CLASSES for b in CLASSES)))


def proxy_scret(classes: dict) -> dict:
    return {s['id']: round(sum(wt * MKT['class_scret'][c][s['id']] for c, wt in classes.items()), 4) for s in MKT['scenarios']}


# ---------------------------------------------------------------------------------------------------------------- validation
NAME_HINTS = [  # (pattern, classes) - used only when a security is not on any list
    (r'target date|target retirement|20[2-6]\d fund', {'LCG': .22, 'LCV': .22, 'SMID': .06, 'INTL': .15, 'EM': .05, 'UST': .17, 'IGC': .13}),
    (r'equity index|s&p 500|total (us )?stock|total market|large cap|us stock|stock index', {'LCG': .5, 'LCV': .5}),
    (r'international|intl|developed|eafe|foreign|ex-us|world ex', {'INTL': .8, 'EM': .2}),
    (r'emerging', {'EM': 1}),
    (r'small|mid cap|smid|russell 2000', {'SMID': 1}),
    (r'high yield|high-yield|junk', {'HY': 1}),
    (r'municipal|muni|tax-exempt|tax exempt', {'IGC': 1}),
    (r'treasury|government bond|govt', {'UST': 1}),
    (r'corporate', {'IGC': 1}),
    (r'bond|fixed income|income fund|aggregate', {'UST': .6, 'IGC': .4}),
    (r'money market|cash|stable value|sweep|savings', {'CASH': 1}),
    (r'value|dividend', {'LCV': 1}),
    (r'growth|innovation|technology|tech|quantum|nasdaq|ai ', {'LCG': 1}),
    (r'real estate|reit', {'LCV': 1}),
    (r'balanced|allocation|moderate', {'LCG': .3, 'LCV': .3, 'UST': .2, 'IGC': .2}),
    (r'hedge|absolute return|multi-strategy', {'HF': 1}),
    (r'private|venture|series [a-z]\b', {'PE': 1}),
    (r'equity|stock', {'LCG': .5, 'LCV': .5}),
]
CLASS_HINTS = [(r'large cap value|value', {'LCV': 1}), (r'large cap growth|growth', {'LCG': 1}), (r'large cap|us equity|domestic equity', {'LCG': .5, 'LCV': .5}),
               (r'international|foreign', {'INTL': 1}), (r'emerging', {'EM': 1}), (r'small|mid', {'SMID': 1}), (r'municipal', {'IGC': 1}),
               (r'high yield', {'HY': 1}), (r'fixed income|bond', {'UST': .6, 'IGC': .4}), (r'cash|money market', {'CASH': 1}), (r'balanced', {'LCG': .3, 'LCV': .3, 'UST': .2, 'IGC': .2})]


def guess_classes(desc: str, cls_hint: str | None = None) -> tuple[dict, str]:
    for src, table in ((cls_hint or '', CLASS_HINTS), (desc or '', NAME_HINTS)):
        t = ' ' + src.lower() + ' '
        for pat, cl in table:
            if re.search(pat, t):
                return dict(cl), ('statement asset class' if src is cls_hint else 'name') + f' ("{src.strip()}")'
    return {'LCG': .5, 'LCV': .5}, 'default (equity) until the advisor confirms'


def name_match(desc: str) -> tuple[dict | None, float]:
    """Look up a security with no ticker by name against both lists (exact-ish names only)."""
    best, score = None, 0.0
    d = (desc or '').lower()
    for a in list(SEC['approved']) + list(SEC['reference']):
        s = SequenceMatcher(None, d, a['name'].lower()).ratio()
        if s > score:
            best, score = a, s
    return (best, score) if score >= 0.9 else (None, score)


def rule_match(desc: str):
    t = ' ' + (desc or '').lower() + ' '
    for r in SEC['category_rules']:
        if any(m in t for m in r['match']):
            return r
    return None


def validate_row(h: dict, category: str, override: dict | None = None) -> dict:
    """Decide what a statement row is, which asset classes it carries, and whether it can come to the firm."""
    out = {'status': None, 'reason': '', 'classes': {}, 'class_source': '', 'match': None, 'match_name': None, 'kind': None, 'view': None,
           'expense_bps': None, 'yield': 0.0, 'scret': None, 'top_holdings': None, 'rule': None, 'fill': None}
    sym = h.get('sym')
    sec = APPROVED.get(sym) if sym else None
    ref = REFERENCE.get(sym) if sym else None
    if not sec and not ref and not sym:
        m, _ = name_match(h.get('desc'))
        if m:
            sec, ref = (m, None) if m['sym'] in APPROVED else (None, m)
    elif not sec and not ref and sym:
        # a symbol nobody knows, but the name matches a known security whose symbol is one or two characters away:
        # usually an OCR misread (VWO read as VVWO). Use the known security and say so.
        d = (h.get('desc') or '').lower()
        best = None
        for a in list(SEC['approved']) + list(SEC['reference']):
            ns = SequenceMatcher(None, d, a['name'].lower()).ratio()
            ss = SequenceMatcher(None, sym, a['sym']).ratio()
            if ns >= 0.85 and ss >= 0.5 and (best is None or ns + ss > best[0]):
                best = (ns + ss, a)
        if best:
            a = best[1]
            sec, ref = (a, None) if a['sym'] in APPROVED else (None, a)
            out['symbol_fix'] = f'Symbol read as {sym}; matched to {a["sym"]} by name'
    rule = rule_match(h.get('desc')) if not sec and not ref else None
    if sec:
        out.update(status='review' if sec['status'] == 'review' else 'approved', match=sec['sym'], match_name=sec['name'], kind=sec['kind'], view=sec['view'],
                   classes=dict(sec['classes']), class_source='approved list', expense_bps=sec.get('expense_bps'), scret=sec.get('scret'),
                   top_holdings=sec.get('top_holdings'), **{'yield': sec.get('yield', 0)})
        out['reason'] = (f"On the approved list; Research rates it {sec['view']}" if sec['view'] not in ('Covered', None) else 'On the approved list (covered stock)')
        if out['status'] == 'review':
            out['reason'] = f"On the approved list but Research rates it {sec['view']}: keep under review or replace"
    elif ref:
        out.update(status='held_away' if ref['kind'] == 'plan' else 'not_approved', match=ref['sym'], match_name=ref['name'], kind=ref['kind'],
                   classes=dict(ref['classes']), class_source='reference data', expense_bps=ref.get('expense_bps'), reason=ref['reason'], **{'yield': ref.get('yield', 0)})
    elif rule:
        out.update(status=rule['outcome'], classes=dict(rule['classes']), class_source=f"category rule {rule['id']}", kind=rule['kind'], rule=rule['id'],
                   reason=rule['reason'], expense_bps=0 if rule['kind'] in ('cash', 'bond') else None, **{'yield': 0.04 if rule['kind'] == 'cash' else 0.035 if rule['kind'] == 'bond' else 0})
    else:
        cl, src = guess_classes(h.get('desc'), h.get('cls_hint'))
        out.update(status='unrecognized', classes=cl, class_source=src, kind='unknown',
                   reason='Not on the approved list or in reference data: confirm the security and its asset class before it is used')
    # account type decides whether the position can move at all
    if category == 'employer-plan':
        out['reason'] = 'Employer retirement plan: investments stay in the plan while the client is employed.' + (' Asset classes estimated from the fund name.' if out['status'] == 'unrecognized' else '')
        out['status'] = 'held_away'
    elif category == 'annuity':
        out['status'] = 'held_away'
        out['reason'] = 'Annuity subaccount: stays in the contract (surrender charges and a 1035 exchange review come first)'
        if out['kind'] in (None, 'unknown'):
            out['kind'] = 'annuity'
    if out['status'] == 'cash' and out['kind'] == 'cash':
        out['classes'] = {'CASH': 1}
    if override:
        if override.get('classes'):
            out['classes'] = {k: float(v) for k, v in override['classes'].items() if float(v) > 0}
            out['class_source'] = 'set by the advisor'
        if override.get('status'):
            out['status'] = override['status']
            out['reason'] = 'Set by the advisor: ' + (override.get('note') or STATUS_LABEL.get(override['status'], ''))
    if not out['scret']:
        out['scret'] = proxy_scret(out['classes']) if out['classes'] else {}
        out['scret_proxy'] = True
    main = max(out['classes'], key=out['classes'].get) if out['classes'] else None
    out['fill'] = MKT['fill'].get(main) if main else None
    return out


# ---------------------------------------------------------------------------------------------------------------- household
def owner_matches(owner: str | None, hh: dict) -> bool:
    if not owner:
        return False
    sur = re.findall(r'[A-Z][a-z]+', hh['name'])
    return any(s.lower() in owner.lower() for s in sur if s.lower() not in ('household', 'family', 'trust', 'holdings', 'llc'))


def statement_checks(st: dict, hh: dict) -> list[dict]:
    out = []
    rec = st.get('reconciliation')
    if rec:
        out.append({'id': 'reconcile', 'ok': rec['ok'], 'text': f"Rows add up to the statement total (${rec['stated']:,.0f})" if rec['ok']
                    else f"Rows add up to ${rec['extracted']:,.0f}; statement total ${rec['stated']:,.0f}"})
    else:
        out.append({'id': 'reconcile', 'ok': None, 'text': 'No statement total found to reconcile against'})
    if st.get('as_of'):
        age = (TODAY - date.fromisoformat(st['as_of'])).days
        out.append({'id': 'fresh', 'ok': age <= STALE_DAYS, 'text': f'Statement dated {st["as_of"]} ({age} days old)' + ('' if age <= STALE_DAYS else ': ask for a current one')})
    else:
        out.append({'id': 'fresh', 'ok': None, 'text': 'Statement date not found'})
    om = owner_matches(st.get('owner'), hh)
    out.append({'id': 'owner', 'ok': om, 'text': f"Owner \"{st.get('owner') or 'not found'}\" " + ('matches the household' if om else 'does not match the household name: confirm')})
    secs = st.get('sections') or []
    if secs:
        bad = [x for x in secs if not x['ok']]
        out.append({'id': 'sections', 'ok': not bad, 'text': f'{len(secs)} section subtotals match their rows' if not bad else
                    '; '.join(f"{x['label']}: rows {x['sum']:,.0f} vs {x['stated']:,.0f}" for x in bad)})
    pm = st.get('page_map') or []
    if len(pm) > 1:
        used = [p for p in pm if p['type'] in ('summary', 'holdings', 'chart')]
        hold = [p['page'] for p in pm if p['type'] == 'holdings']
        out.append({'id': 'pages', 'ok': True, 'text': f"{len(pm)} pages: holdings on {_span(hold) if hold else 'none'}; {len(pm) - len(used)} pages of activity, fee tables and disclosures skipped"})
    low = sum(1 for h in st['holdings'] if h.get('review'))
    out.append({'id': 'confidence', 'ok': low == 0, 'text': 'All rows read with high confidence' if low == 0 else f'{low} row(s) need a second look'})
    return out


def _span(pages):
    pages = sorted(pages)
    return f'page {pages[0]}' if len(pages) == 1 else f'pages {pages[0]}-{pages[-1]}' if pages[-1] - pages[0] == len(pages) - 1 else 'pages ' + ', '.join(map(str, pages))


CHART_GROUPS = {'us_eq': ('LCG', 'LCV', 'SMID'), 'intl': ('INTL', 'EM'), 'fixed': ('UST', 'IGC', 'HY'), 'cash': ('CASH',), 'alt': ('HF', 'PE')}


def chart_vs_holdings(st: dict, pos: list[dict]) -> dict | None:
    """Compare an allocation read from a chart with the same split computed from the statement's own validated rows."""
    from .extract.charts import label_group
    pie = next((c for c in st.get('charts') or [] if c['type'] == 'pie'), None)
    rows = [p for p in pos if p['statement'] == st['id']]
    if not pie or not rows:
        return None
    groups = {v['label']: label_group(v['label']) for v in pie['values']}
    if any(g is None for g in groups.values()):
        return {'id': 'chart', 'ok': None, 'text': f"Chart on page {pie['page']} read; its categories could not all be matched to asset classes"}
    tot = sum(p['mv'] for p in rows)
    diffs = []
    for v in pie['values']:
        cls = CHART_GROUPS[groups[v['label']]]
        mine = sum(p['mv'] * sum(p['classes'].get(c, 0) for c in cls) for p in rows) / tot * 100
        diffs.append((v['label'], v['pct'], mine))
    worst = max(diffs, key=lambda d: abs(d[1] - d[2]))
    ok = abs(worst[1] - worst[2]) <= 2.0
    return {'id': 'chart', 'ok': ok, 'detail': [{'label': l, 'chart': round(a, 1), 'holdings': round(b, 1)} for l, a, b in diffs],
            'text': (f"Pie chart on page {pie['page']} agrees with the holdings within {abs(worst[1] - worst[2]):.1f} pts" if ok else
                     f"Pie chart on page {pie['page']} and holdings differ: {worst[0]} {worst[1]:.1f}% in the chart vs {worst[2]:.1f}% from holdings")}


def outside_positions(statements: list[dict], hh: dict, overrides: dict | None = None) -> list[dict]:
    overrides = overrides or {}
    pos = []
    for st in statements:
        cat = st.get('account_category') or 'taxable'
        for h in st['holdings']:
            key = f"{st['id']}:{h['row']}"
            ov = overrides.get(key)
            if ov and ov.get('exclude'):
                continue
            hv = dict(h)
            if ov:
                for f in ('sym', 'desc', 'qty', 'price', 'value', 'cost'):
                    if ov.get(f) not in (None, ''):
                        hv[f] = ov[f] if f in ('sym', 'desc') else float(ov[f])
            v = validate_row(hv, cat, ov)
            cost = hv.get('cost')
            flags = list(h.get('flags', []))
            if v.get('symbol_fix'):
                flags.append(v['symbol_fix'])
            pos.append({'key': key, 'statement': st['id'], 'institution': st.get('institution'), 'account_type': st.get('account_type'),
                        'account': st.get('account'), 'category': cat, 'location': 'outside', 'sym': v['match'] if v.get('symbol_fix') else (hv.get('sym') or v['match']),
                        'name': hv.get('desc') or v['match_name'] or hv.get('sym'), 'mv': float(hv['value']), 'qty': hv.get('qty'), 'cost': cost,
                        'confidence': h.get('confidence'), 'extract_flags': flags, **{k: x for k, x in v.items() if k != 'symbol_fix'},
                        'taxable': cat == 'taxable', 'surrender': st.get('surrender')})
    return pos


def inside_positions(hh: dict) -> list[dict]:
    out = []
    for h in hh['holdings']:
        sec = APPROVED.get(h['sym'])
        cost = None
        if h.get('lots') and all(l.get('cost') is not None for l in h['lots']):
            cost = sum(l['cost'] for l in h['lots'])
        out.append({'key': f"in:{h['sym']}:{len(out)}", 'statement': None, 'institution': 'Firm', 'account_type': 'Firm advisory', 'account': None,
                    'category': 'firm', 'location': 'firm', 'sym': h['sym'], 'name': h['name'], 'mv': h['mv'], 'qty': None, 'cost': cost,
                    'status': 'cash' if h.get('cash') else 'approved', 'reason': 'Held at the firm', 'classes': h['classes'], 'class_source': 'firm records',
                    'kind': h['kind'], 'view': sec['view'] if sec else None, 'expense_bps': h.get('expense_bps', 0), 'yield': h.get('yield', 0),
                    'scret': h.get('scret') or proxy_scret(h['classes']), 'top_holdings': h.get('top_holdings'), 'taxable': hh['rates'].get('taxable', True),
                    'lots': h.get('lots')})
    return out


def look_through(pos: list[dict]) -> dict:
    names: dict = {}
    for p in pos:
        if p['kind'] == 'stock' and p.get('sym'):
            names.setdefault(p['sym'], {'direct': 0, 'via': 0})['direct'] += p['mv']
        for n, w in (p.get('top_holdings') or {}).items():
            names.setdefault(n, {'direct': 0, 'via': 0})['via'] += p['mv'] * w
    return names


def metrics(pos: list[dict], hh: dict) -> dict:
    tot = sum(p['mv'] for p in pos) or 1
    w = {c: 0.0 for c in CLASSES}
    for p in pos:
        for c, x in p['classes'].items():
            w[c] += p['mv'] * x / tot
    st = class_stats(w)
    stress = {s['id']: sum(p['mv'] * (p['scret'] or {}).get(s['id'], 0) for p in pos) / tot for s in MKT['scenarios']}
    fee_known = [p for p in pos if p.get('expense_bps') is not None]
    fees = sum(p['mv'] * p['expense_bps'] / 1e4 for p in fee_known)
    fee_unknown = sum(p['mv'] for p in pos if p.get('expense_bps') is None)
    income = sum(p['mv'] * (p.get('yield') or 0) for p in pos)
    lt = look_through(pos)
    top = sorted(((n, (x['direct'] + x['via']) / tot, x['direct'] / tot) for n, x in lt.items()), key=lambda r: -r[1])[:6]
    groups = {}
    for c in CLASSES:
        g = MKT['classes'][c]['group']
        groups[g] = groups.get(g, 0) + w[c]
    tgt_groups = {}
    for c in CLASSES:
        g = MKT['classes'][c]['group']
        tgt_groups[g] = tgt_groups.get(g, 0) + hh['target'].get(c, 0)
    return {'total': tot, 'weights': w, 'groups': groups, 'target_groups': tgt_groups, 'er': st['er'], 'vol': st['vol'], 'sharpe': st['sharpe'],
            'te': te(w, hh['target']), 'band': hh['band'], 'in_band': hh['band'][0] - 1e-9 <= st['vol'] <= hh['band'][1] + 1e-9, 'stress': stress,
            'fees': fees, 'fee_bps': fees / (tot - fee_unknown) * 1e4 if tot > fee_unknown else 0, 'fee_unknown': fee_unknown, 'income': income,
            'top_names': [{'name': n, 'weight': x, 'direct': d} for n, x, d in top]}


def comparison(hh: dict, pos: list[dict]) -> dict:
    """Internal vs external, by asset class, against the target and the CIO view."""
    inside = [p for p in pos if p['location'] == 'firm']
    outside = [p for p in pos if p['location'] == 'outside']
    tot = sum(p['mv'] for p in pos) or 1
    rows = []
    for c in CLASSES:
        i = sum(p['mv'] * p['classes'].get(c, 0) for p in inside)
        o = sum(p['mv'] * p['classes'].get(c, 0) for p in outside)
        t = hh['target'].get(c, 0)
        rows.append({'cls': c, 'label': MKT['classes'][c]['label'], 'group': MKT['classes'][c]['group'], 'inside': i, 'outside': o, 'weight': (i + o) / tot,
                     'target': t, 'gap': (i + o) / tot - t, 'cio': MKT['cio']['classes'].get(c), 'stance_fit': stance_fit((i + o) / tot - t, MKT['cio']['classes'].get(c))})
    # securities held on both sides, and single names that only become large once outside accounts are added
    syms_in = {p['sym'] for p in inside if p.get('sym')}
    overlap = sorted({p['sym'] for p in outside if p.get('sym') in syms_in})
    lt_in = look_through(inside)
    lt_all = look_through(pos)
    tot_in = sum(p['mv'] for p in inside) or 1
    conc = []
    lim = hh['limits']['single_stock']
    for n, x in lt_all.items():
        all_w = (x['direct'] + x['via']) / tot
        in_w = (lt_in.get(n, {'direct': 0, 'via': 0})['direct'] + lt_in.get(n, {'direct': 0, 'via': 0})['via']) / tot_in if inside else 0
        out_direct = sum(p['mv'] for p in outside if p.get('sym') == n and p['kind'] == 'stock')
        if all_w >= lim * 0.5 or out_direct / tot >= 0.02:
            conc.append({'name': n, 'inside_weight': in_w, 'household_weight': all_w, 'outside_direct': out_direct, 'over_limit': all_w > lim})
    conc.sort(key=lambda r: -r['household_weight'])
    out_funds = [p for p in outside if p.get('expense_bps') is not None and p['kind'] in ('mf', 'etf', 'plan')]
    fee_rows = []
    for p in out_funds:
        main = max(p['classes'], key=p['classes'].get)
        if p['classes'][main] < 0.6:
            continue
        alt = APPROVED.get(MKT['fill'].get(main) or '')
        if alt and p['expense_bps'] - alt['expense_bps'] >= 10:
            fee_rows.append({'sym': p['sym'], 'name': p['name'], 'bps': p['expense_bps'], 'alt': alt['sym'], 'alt_bps': alt['expense_bps'],
                             'saving': p['mv'] * (p['expense_bps'] - alt['expense_bps']) / 1e4})
    out_cash = sum(p['mv'] for p in outside if p['classes'].get('CASH', 0) >= 0.99)
    by_status = {}
    for p in outside:
        by_status.setdefault(p['status'], {'count': 0, 'value': 0})
        by_status[p['status']]['count'] += 1
        by_status[p['status']]['value'] += p['mv']
    return {'rows': rows, 'inside_total': sum(p['mv'] for p in inside), 'outside_total': sum(p['mv'] for p in outside), 'overlap': overlap,
            'concentration': conc[:6], 'fees': fee_rows, 'outside_cash': out_cash, 'by_status': by_status,
            'held_away': sum(p['mv'] for p in outside if p['status'] == 'held_away')}


def stance_fit(gap, stance):
    if stance is None:
        return ''
    if abs(gap) <= 0.02:
        return 'In line' if stance == 'Neutral' else ('Short of view' if stance == 'Overweight' else 'Above view')
    over = gap > 0
    if stance == 'Neutral':
        return 'Off neutral'
    if stance == 'Overweight':
        return 'With view' if over else 'Against view'
    return 'With view' if not over else 'Against view'


# ---------------------------------------------------------------------------------------------------------------- proposals
PROPOSALS = {
    'A': {'name': 'Transfer what is approved', 'idea': 'Move approved positions in kind and transferable cash; leave everything else where it is. No sales, no tax.'},
    'B': {'name': 'Consolidate and align', 'idea': 'Move transferable accounts, replace positions that are not approved or under review, trim single names over the limit within the gain budget, and invest proceeds toward the target using the CIO view.'},
    'C': {'name': 'Tax-aware phased move', 'idea': 'Move approved positions in kind; sell only where it costs no tax (retirement accounts, losses, small gains); leave the rest outside for a later phase.'},
}


def gain_of(p):
    return None if p.get('cost') is None else p['mv'] - p['cost']


def build_proposal(pid: str, hh: dict, pos: list[dict]) -> dict:
    pos = deepcopy(pos)
    rates = hh['rates']
    actions, new_pos = [], []
    pools = {'taxable': 0.0, 'ira': 0.0}
    realized = {'gain': 0.0, 'loss': 0.0}
    budget = hh['gain_budget']
    tot = sum(p['mv'] for p in pos)
    lim = hh['limits']['single_stock']
    lt = look_through(pos)
    over = {n for n, x in lt.items() if (x['direct'] + x['via']) / tot > lim}

    def act(p, what, why, dest=None, tax=0.0, value=None):
        actions.append({'key': p['key'], 'sym': p.get('sym'), 'name': p['name'], 'value': p['mv'] if value is None else value, 'from': f"{p['institution']} {p['account_type']}",
                        'action': what, 'why': why, 'dest': dest, 'tax': tax, 'status': p['status']})

    def sell(p, why, frac=1.0):
        g = gain_of(p)
        amt = p['mv'] * frac
        tax = 0.0
        if p['category'] == 'taxable' and g is not None:
            gg = g * frac
            if gg >= 0:
                realized['gain'] += gg
            else:
                realized['loss'] += -gg
        pool = 'ira' if p['category'] == 'ira' else 'taxable'
        pools[pool] += amt
        act(p, 'Sell after transfer' if frac >= 0.999 else f'Trim {frac * 100:.0f}% after transfer', why, 'Firm IRA' if pool == 'ira' else 'Firm account', tax, value=amt)
        return amt

    keep = []
    inside = [p for p in pos if p['location'] == 'firm']
    outside = [p for p in pos if p['location'] == 'outside']
    seq = {p['key']: i for i, p in enumerate(outside)}
    # sales that release losses go first so they can offset gains
    order = sorted(outside, key=lambda p: (gain_of(p) if gain_of(p) is not None else 1e18))
    for p in order:
        dest = 'Firm IRA' if p['category'] == 'ira' else 'Firm account'
        transferable = p['category'] in ('taxable', 'ira')
        g = gain_of(p)
        st = p['status']
        if not transferable:
            why = {'employer-plan': 'Employer plan: stays while employed; revisit at separation or retirement',
                   'annuity': 'Annuity: stays in the contract; review a 1035 exchange after the surrender period',
                   'bank': 'Bank deposit: stays as the emergency reserve' + ('; revisit at CD maturity' if 'deposit' in p['name'].lower() else '')}.get(p['category'], 'Stays held away')
            act(p, 'Stays outside', why); keep.append(p); continue
        if st == 'unrecognized':
            act(p, 'Pending review', 'Security not recognized: the advisor confirms it before it is used'); keep.append(p); continue
        if st == 'held_away':
            act(p, 'Stays outside', p['reason']); keep.append(p); continue
        if st == 'cash':
            if p.get('rule') == 'CAT-CD':
                act(p, 'Transfer in kind', 'Certificate of deposit: transfer and hold to maturity', dest)
                p['location'] = 'firm'; keep.append(p); continue
            if pid == 'A':
                act(p, 'Transfer as cash', 'Cash moves with the account; invested later', dest); p['location'] = 'firm'; keep.append(p)
            else:
                pools['ira' if p['category'] == 'ira' else 'taxable'] += p['mv']
                act(p, 'Transfer and invest', 'Cash invested toward the target', dest)
            continue
        if st in ('approved',):
            single_over = p['kind'] == 'stock' and p.get('sym') in over
            if pid == 'B' and single_over:
                if p['category'] == 'ira' or g is None or g <= 0:
                    sell(p, f"{p['sym']} is over the {lim * 100:.0f}% single-name limit across the household"); continue
                room = budget - (realized['gain'] - realized['loss'])
                if room > 0:
                    frac = min(1.0, room / g)
                    sell(p, f"{p['sym']} is over the {lim * 100:.0f}% single-name limit" + ('' if frac >= 0.999 else '; trim sized to the gain budget'), frac)
                    if frac < 0.999:
                        rest = dict(p); rest['mv'] = p['mv'] * (1 - frac); rest['cost'] = (p['cost'] or 0) * (1 - frac); rest['location'] = 'firm'; keep.append(rest)
                        act(rest, 'Transfer in kind', 'Remaining shares transfer; gain budget used up', dest)
                    continue
            act(p, 'Transfer in kind', 'Approved: moves as is, no tax', dest); p['location'] = 'firm'; keep.append(p); continue
        # review or not approved
        if pid == 'A':
            if st == 'review':
                act(p, 'Transfer in kind', 'On the approved list but under review: flagged for the next review', dest); p['location'] = 'firm'; keep.append(p)
            else:
                act(p, 'Stays outside', 'Not approved: cannot be held in a firm advisory account'); keep.append(p)
            continue
        if pid == 'B':
            if g is not None and g > 0 and p['category'] == 'taxable' and (realized['gain'] - realized['loss'] + g) > budget:
                act(p, 'Stays outside', 'Selling would exceed the gain budget; replace in a later year'); keep.append(p); continue
            sell(p, ('Under review by Research' if st == 'review' else 'Not approved') + f": replaced with the approved fund for its asset class"); continue
        # C: sell only where it costs no tax
        if p['category'] == 'taxable' and g is None:
            act(p, 'Stays outside', 'Cost basis not on the statement: tax unknown, so phase 2'); keep.append(p); continue
        if p['category'] == 'ira' or g <= 0 or g <= 0.05 * p['mv']:
            why = 'Inside an IRA: no tax on the sale' if p['category'] == 'ira' else ('Sold at a loss: harvests the loss' if g <= 0 else 'Gain under 5% of value: small tax')
            sell(p, why); continue
        if st == 'review':
            act(p, 'Transfer in kind', 'Under review; selling now would realize a gain: revisit next year', dest); p['location'] = 'firm'; keep.append(p)
        else:
            act(p, 'Stays outside', 'Not approved, and selling now would realize a gain: phase 2'); keep.append(p)
    if pid == 'B':
        align(hh, inside, keep, pools, realized, act, actions)
    actions.sort(key=lambda a: seq.get(a['key'], 0))
    base = inside + keep
    # invest proceeds toward the target, tilted by the CIO view
    deployed = deploy(hh, base, pools)
    for d in deployed:
        actions.append({'key': f"buy:{d['sym']}:{d['pool']}", 'sym': d['sym'], 'name': APPROVED[d['sym']]['name'], 'value': d['mv'], 'from': 'Proceeds and cash',
                        'action': 'Buy', 'why': d['why'], 'dest': 'Firm IRA' if d['pool'] == 'ira' else 'Firm account', 'tax': 0, 'status': 'approved'})
    final = base + [d['pos'] for d in deployed]
    net = realized['gain'] - realized['loss']
    tax = max(0.0, net) * rates['lt'] if rates.get('taxable', True) else 0.0
    return {'id': pid, **PROPOSALS[pid], 'actions': actions, 'positions': final, 'realized_gain': realized['gain'], 'realized_loss': realized['loss'],
            'net_gain': net, 'tax': tax, 'moved': sum(a['value'] for a in actions if a['action'] in ('Transfer in kind', 'Transfer as cash', 'Transfer and invest')
                                                      or a['action'].startswith(('Sell', 'Trim'))),
            'sold': sum(a['value'] for a in actions if a['action'].startswith(('Sell', 'Trim')))}


def align(hh, inside, keep, pools, realized, act, actions):
    """Proposal B only: sell transferred positions in classes that are over target, tax-free first, within the gain budget."""
    base = inside + keep
    tot = sum(p['mv'] for p in base) + sum(pools.values())
    cur = {c: sum(p['mv'] * p['classes'].get(c, 0) for p in base) for c in CLASSES}
    drift = hh['limits'].get('drift_pts', 5) / 100 * 0.4   # aim inside the drift band, with room to spare
    over = {c: cur[c] - (hh['target'][c] + drift) * tot for c in CLASSES if cur[c] > (hh['target'][c] + drift) * tot}
    if not over:
        return
    def main(p):
        return max(p['classes'], key=p['classes'].get)
    cands = [p for p in keep if p['location'] == 'firm' and p.get('statement') and p['status'] == 'approved' and p['kind'] in ('etf', 'mf', 'stock')
             and main(p) in over and (p['classes'][main(p)] >= 0.75 or p['category'] == 'ira')]
    def tax_rank(p):
        g = gain_of(p)
        if p['category'] == 'ira':
            return -2
        if g is None:
            return 9
        return g / p['mv'] if p['mv'] else 9
    for p in sorted(cands, key=tax_rank):
        c = main(p)
        need = over.get(c, 0) / max(p['classes'][c], 1e-9)
        if need < 1000:
            continue
        frac = min(1.0, need / p['mv'])
        g = gain_of(p)
        if p['category'] == 'taxable':
            if g is None:
                continue
            if g > 0:
                room = hh['gain_budget'] - (realized['gain'] - realized['loss'])
                if room <= 0:
                    continue
                frac = min(frac, room / g)
                realized['gain'] += g * frac
            else:
                realized['loss'] += -g * frac
        amt = p['mv'] * frac
        if amt < 1000:
            continue
        pools['ira' if p['category'] == 'ira' else 'taxable'] += amt
        over[c] -= amt * p['classes'][c]
        prev = next((a for a in actions if a['key'] == p['key'] and a['action'] == 'Transfer in kind'), None)
        if prev is not None:
            if frac >= 0.999:
                actions.remove(prev)
            else:
                prev['value'] = p['mv'] * (1 - frac)
                prev['why'] = 'Remaining shares transfer in kind'
        act(dict(p), 'Sell after transfer' if frac >= 0.999 else f'Trim {frac * 100:.0f}% after transfer',
            f"{MKT['classes'][c]['label']} is over target" + (': inside an IRA, no tax' if p['category'] == 'ira' else ': within the gain budget'),
            'Firm IRA' if p['category'] == 'ira' else 'Firm account', value=amt)
        if frac >= 0.999:
            keep.remove(p)
        else:
            p['mv'] *= (1 - frac)
            if p.get('cost') is not None:
                p['cost'] *= (1 - frac)


def deploy(hh, base, pools):
    out = []
    tot = sum(p['mv'] for p in base) + sum(pools.values())
    cur = {c: sum(p['mv'] * p['classes'].get(c, 0) for p in base) for c in CLASSES}
    for pool in ('taxable', 'ira'):
        amt = pools[pool]
        if amt < 1:
            continue
        fillable = [c for c in CLASSES if MKT['fill'].get(c)]
        gaps = {c: max(0.0, hh['target'][c] * tot - cur[c]) for c in fillable}
        wts = {c: gaps[c] * TILT.get(MKT['cio']['classes'].get(c), 1) for c in fillable}
        alloc = {c: 0.0 for c in fillable}
        left = amt
        for _ in range(6):
            sw = sum(w for c, w in wts.items() if alloc[c] < gaps[c] - 1)
            if left < 1 or sw <= 0:
                break
            for c in fillable:
                if alloc[c] < gaps[c] - 1 and wts[c] > 0:
                    alloc[c] += min(gaps[c] - alloc[c], left * wts[c] / sw)
            left = amt - sum(alloc.values())
        if left >= 1:   # every gap filled: spread the rest by target weight and CIO tilt
            tw = {c: hh['target'][c] * TILT.get(MKT['cio']['classes'].get(c), 1) for c in fillable}
            s = sum(tw.values())
            for c in fillable:
                alloc[c] += left * tw[c] / s
        for c, a in alloc.items():
            if a < 500:
                continue
            sym = 'LQD' if pool == 'ira' and c == 'IGC' else MKT['fill'][c]
            sec = APPROVED[sym]
            cur[c] += a
            stance = MKT['cio']['classes'].get(c)
            why = f"{MKT['classes'][c]['label']}: below target" + (f"; CIO {stance.lower()}" if stance else '')
            out.append({'sym': sym, 'pool': pool, 'mv': a, 'why': why, 'pos': {
                'key': f'buy:{sym}:{pool}', 'statement': None, 'institution': 'Firm', 'account_type': 'Firm IRA' if pool == 'ira' else 'Firm account', 'account': None,
                'category': 'firm', 'location': 'firm', 'sym': sym, 'name': sec['name'], 'mv': a, 'qty': None, 'cost': a, 'status': 'approved', 'reason': 'New purchase',
                'classes': sec['classes'], 'class_source': 'approved list', 'kind': sec['kind'], 'view': sec['view'], 'expense_bps': sec['expense_bps'],
                'yield': sec['yield'], 'scret': sec['scret'], 'top_holdings': sec.get('top_holdings'), 'taxable': pool == 'taxable'}})
    return out


def policy_checks(hh, prop, m) -> list[dict]:
    lim = hh['limits']
    out = []
    lo, hi = hh['band']
    out.append({'id': 'risk', 'label': 'Risk inside the profile band', 'ok': m['in_band'], 'text': f"Expected risk {m['vol'] * 100:.1f}% (band {lo * 100:.1f}% to {hi * 100:.1f}%)"})
    top = m['top_names'][0] if m['top_names'] else None
    over = [n for n in m['top_names'] if n['weight'] > lim['single_stock']]
    firm_side = {}
    for p in prop['positions']:
        if p['location'] == 'firm' and p.get('category') == 'firm':
            firm_side[p['sym']] = firm_side.get(p['sym'], 0) + p['mv']
    def note(n):
        share = firm_side.get(n['name'], 0) / (n['weight'] * m['total']) if n['weight'] else 0
        return f"{n['name']} {n['weight'] * 100:.1f}%" + (' (mostly existing firm holdings: address in Portfolio Review)' if share > 0.6 else '')
    out.append({'id': 'single', 'label': f"No single name over {lim['single_stock'] * 100:.0f}%", 'ok': not over,
                'text': ', '.join(note(n) for n in over) if over else (f"Largest {top['name']} {top['weight'] * 100:.1f}%" if top else '')})
    hy = m['weights'].get('HY', 0)
    out.append({'id': 'hy', 'label': f"High yield at or under {hh['hy_limit'] * 100:.0f}%", 'ok': hy <= hh['hy_limit'] + 1e-9, 'text': f'High yield {hy * 100:.1f}%'})
    firm_bad = [p for p in prop['positions'] if p['location'] == 'firm' and p['status'] in ('not_approved', 'unrecognized')]
    out.append({'id': 'approved', 'label': 'Only approved securities in firm accounts', 'ok': not firm_bad,
                'text': 'All firm positions are approved' if not firm_bad else ', '.join(p['name'] for p in firm_bad)})
    rev = [p for p in prop['positions'] if p['location'] == 'firm' and p['status'] == 'review']
    out.append({'id': 'review', 'label': 'No firm positions under Research review', 'ok': not rev, 'warn': True,
                'text': 'None' if not rev else ', '.join(f"{p['sym']} ({p.get('view')})" for p in rev)})
    out.append({'id': 'gain', 'label': 'Realized gains within the gain budget', 'ok': prop['net_gain'] <= hh['gain_budget'] + 1,
                'text': f"Net realized gain ${prop['net_gain']:,.0f} of ${hh['gain_budget']:,.0f}"})
    turn = prop['sold'] / m['total'] if m['total'] else 0
    out.append({'id': 'turnover', 'label': f"Sales at or under {lim['turnover'] * 100:.0f}% of the household", 'ok': turn <= lim['turnover'], 'text': f'Sales {turn * 100:.1f}%'})
    pend = [a for a in prop['actions'] if a['action'] == 'Pending review']
    out.append({'id': 'pending', 'label': 'Every outside row identified', 'ok': not pend, 'warn': True,
                'text': 'All identified' if not pend else f"{len(pend)} pending: " + ', '.join(a['sym'] or a['name'] for a in pend)})
    return out


def talking_points(hh, cmp, props, ms, n_statements=0) -> list[str]:
    """Deterministic draft. In production an LLM writes these from the same figures (an AI touchpoint)."""
    pts = []
    tot_o = cmp['outside_total']
    pts.append(f"We reviewed {n_statements} outside statement{'s' if n_statements != 1 else ''} totalling ${tot_o / 1e6:,.2f}M alongside "
               + (f"${cmp['inside_total'] / 1e6:,.2f}M held with us." if cmp['inside_total'] else 'no assets held with us today.'))
    conc = [c for c in cmp['concentration'] if c['over_limit']]
    if conc:
        c = conc[0]
        pts.append(f"Across all accounts, {c['name']} is {c['household_weight'] * 100:.1f}% of the household, above the {hh['limits']['single_stock'] * 100:.0f}% single-name guideline.")
    gaps = sorted(cmp['rows'], key=lambda r: -abs(r['gap']))[:2]
    pts.append('Biggest differences from the target: ' + '; '.join(f"{r['label']} {r['weight'] * 100:.0f}% vs {r['target'] * 100:.0f}% (CIO {r['cio'].lower()})" for r in gaps) + '.')
    if cmp['fees']:
        pts.append(f"Outside funds with lower-cost approved alternatives could save about ${sum(f['saving'] for f in cmp['fees']):,.0f} a year in fund expenses.")
    b = props['B']; mb = ms['B']
    pts.append(f"Proposal B moves the household to {mb['vol'] * 100:.1f}% expected risk with an estimated ${b['tax']:,.0f} of tax; "
               f"Proposal C costs ${props['C']['tax']:,.0f} in tax and leaves more outside for a later phase.")
    pts.append(f"Market context: our CIO is {MKT['cio']['groups']['equity']['stance'].lower()} on equities, {MKT['cio']['groups']['fixed']['stance'].lower()} on bonds and "
               f"{MKT['cio']['groups']['cash']['stance'].lower()} on cash (house view as of {MKT['cio']['as_of']}).")
    return pts


# ---------------------------------------------------------------------------------------------------------------- workflow
WORKFLOW = [
    {'id': 'collect', 'label': 'Collect', 'what': 'Client consent to review outside accounts; up to 5 statements per upload (PDF, image, Excel, CSV).',
     'controls': 'Consent recorded; account numbers masked to last 4; source files deleted after extraction; extracted data retained with the review.'},
    {'id': 'extract', 'label': 'Extract', 'what': 'Text layer, OCR or cells become holdings, allocation and statement details, each with a confidence score.',
     'controls': 'Rows reconcile to the statement total; quantity x price checked; OCR corrections and low-confidence cells flagged.'},
    {'id': 'confirm', 'label': 'Review and correct', 'what': 'The advisor confirms flagged rows, edits values, sets asset classes for unrecognized securities.',
     'controls': 'Human in the loop on every flagged row; edits are logged with the original value.'},
    {'id': 'validate', 'label': 'Validate', 'what': 'Each row checked against the approved list, reference data and category rules; account type decides what can move.',
     'controls': 'Approved list is the only source of truth; exceptions need a named approver.'},
    {'id': 'compare', 'label': 'Compare', 'what': 'Inside and outside together against the target and the CIO view: allocation, single names, fees, cash, risk and stress.',
     'controls': 'All figures calculated; any narrative is drafted from them and labelled.'},
    {'id': 'propose', 'label': 'Propose', 'what': 'Three proposals side by side: transfer as is, consolidate and align, tax-aware phased move.',
     'controls': 'Firm guidance applied: CIO tilt on new money, approved funds only, gain budget, single-name and high-yield limits.'},
    {'id': 'check', 'label': 'Check and document', 'what': 'Policy checks, tax and surrender costs, suitability notes and the client summary.',
     'controls': 'Failed checks block submission; warnings need an advisor note.'},
    {'id': 'implement', 'label': 'Implement', 'what': 'Transfer requests to operations; sells after assets arrive; held-away accounts re-reviewed with the next statement.',
     'controls': 'Transfers reconcile to the statement; trades are placed only after transfer settles.'},
]


def workflow_status(statements, pos, props, checks) -> list[dict]:
    flagged = sum(1 for p in pos if p['location'] == 'outside' and (p.get('confidence') or 1) < 0.85 or p.get('extract_flags'))
    unrec = sum(1 for p in pos if p['location'] == 'outside' and p['status'] == 'unrecognized')
    st = {
        'collect': (bool(statements), f'{len(statements)} statement(s) received'),
        'extract': (bool(statements) and all(s['holdings'] for s in statements), f"{sum(len(s['holdings']) for s in statements)} rows from {len(statements)} statement(s)"),
        'confirm': (flagged == 0, 'No rows flagged' if flagged == 0 else f'{flagged} row(s) flagged for a second look'),
        'validate': (unrec == 0, 'All rows identified' if unrec == 0 else f'{unrec} row(s) not recognized'),
        'compare': (bool(pos), 'Household view ready'),
        'propose': (bool(props), '3 proposals built'),
        'check': (all(c['ok'] or c.get('warn') for c in checks.get('B', [])), 'Proposal B passes all blocking checks' if all(c['ok'] or c.get('warn') for c in checks.get('B', [])) else 'Proposal B has a failed check'),
        'implement': (False, 'Not started (prototype)'),
    }
    return [{**w, 'done': st[w['id']][0], 'status': st[w['id']][1]} for w in WORKFLOW]


# ---------------------------------------------------------------------------------------------------------------- entry
def analyse(household_id: str, statements: list[dict], overrides: dict | None = None) -> dict:
    hh = HH[household_id]
    pos_in = inside_positions(hh)
    pos_out = outside_positions(statements, hh, overrides)
    pos = pos_in + pos_out
    cmp = comparison(hh, pos)
    m_now = metrics(pos, hh)
    props, ms, checks = {}, {}, {}
    for pid in 'ABC':
        pr = build_proposal(pid, hh, pos)
        m = metrics(pr['positions'], hh)
        props[pid], ms[pid] = pr, m
        checks[pid] = policy_checks(hh, pr, m)
    st_checks = {s['id']: statement_checks(s, hh) for s in statements}
    for s in statements:
        c = chart_vs_holdings(s, pos_out)
        if c:
            st_checks[s['id']].append(c)
    return {'household': {k: hh[k] for k in ('id', 'name', 'profile', 'model_name', 'band', 'gain_budget', 'meeting', 'relationship', 'target', 'limits', 'hy_limit')},
            'statements': [{k: v for k, v in s.items() if k != 'text'} for s in statements], 'statement_checks': st_checks,
            'positions': pos_out, 'inside_count': len(pos_in), 'comparison': cmp, 'now': strip(m_now),
            'proposals': [{**{k: v for k, v in props[p].items() if k != 'positions'}, 'metrics': strip(ms[p]), 'checks': checks[p]} for p in 'ABC'],
            'talking_points': talking_points(hh, cmp, props, ms, len(statements)), 'workflow': workflow_status(statements, pos, props, checks),
            'cio': MKT['cio'], 'scenarios': MKT['scenarios'], 'classes': MKT['classes'], 'disclosures': MKT['disclosures']}


def strip(m):
    return {k: v for k, v in m.items()}


def summary_markdown(r: dict) -> str:
    """Plain-text record of the review: what was read, what was decided and why."""
    hh = r['household']
    L = [f"# Outside accounts review: {hh['name']}", '', f"Profile {hh['profile']} ({hh['model_name']}); risk band {hh['band'][0] * 100:.1f}% to {hh['band'][1] * 100:.1f}%; "
         f"gain budget ${hh['gain_budget']:,.0f}.", '', '## Statements', '']
    for s in r['statements']:
        L.append(f"- **{s['file']}**: {s['institution']}, {s['account_type']}" + (f" (…{s['account']})" if s['account'] else '')
                 + f", as of {s['as_of']}; {len(s['holdings'])} rows, ${s['extracted_total']:,.2f}; read by {s['method']}.")
        for c in r['statement_checks'][s['id']]:
            L.append(f"  - {'OK' if c['ok'] else ('CHECK' if c['ok'] is False else 'n/a')}: {c['text']}")
    L += ['', '## Validation', '', '| Statement | Security | Value | Status | Reason |', '|---|---|---:|---|---|']
    for p in r['positions']:
        L.append(f"| {p['statement']} | {p['sym'] or ''} {p['name']} | ${p['mv']:,.0f} | {STATUS_LABEL[p['status']]} | {p['reason']} |")
    c = r['comparison']
    L += ['', '## Inside and outside against the target', '', f"Firm ${c['inside_total']:,.0f}; outside ${c['outside_total']:,.0f}; held away ${c['held_away']:,.0f}.", '',
          '| Asset class | Firm | Outside | Household | Target | CIO |', '|---|---:|---:|---:|---:|---|']
    for row in c['rows']:
        L.append(f"| {row['label']} | ${row['inside']:,.0f} | ${row['outside']:,.0f} | {row['weight'] * 100:.1f}% | {row['target'] * 100:.1f}% | {row['cio']} |")
    L += ['', '## Proposals', '']
    for p in r['proposals']:
        m = p['metrics']
        L.append(f"### {p['id']}. {p['name']}")
        L.append(f"{p['idea']}  Risk {m['vol'] * 100:.1f}%, tracking error {m['te'] * 100:.1f}%, est. tax ${p['tax']:,.0f}, fund expenses ${m['fees']:,.0f} a year.")
        for a in p['actions']:
            if a['action'] != 'Stays outside':
                L.append(f"- {a['action']}: {a['sym'] or a['name']} ${a['value']:,.0f}. {a['why']}")
        for k in p['checks']:
            L.append(f"- Check {'passed' if k['ok'] else 'FAILED'}: {k['label']} ({k['text']})")
        L.append('')
    L += ['## Talking points (draft for advisor review)', ''] + [f'- {t}' for t in r['talking_points']]
    L += ['', '---', MKT['disclosures']['tax'], '', MKT['disclosures']['history']]
    return '\n'.join(L)
