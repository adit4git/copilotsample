"""Workspace calculations: CIO targets and gaps, attribution, fees and the four cost options, the canonical
investable cash, where each brokerage holding goes, event impact, and the multi-year sale plan. Illustrative."""
from __future__ import annotations
from .data import DATA
from . import engine as E
from .fmt import money, pct, nsum


def cio_target(hh: dict, basis: str) -> dict:
    """Strategic = the profile model; tactical = model + CIO tilts (for classes the model holds), floored at 0 and renormalised."""
    base = dict(hh['model_w'])
    if basis != 'tactical':
        return base
    t = {}
    for k in dict.fromkeys(list(base) + list(DATA['cio']['tactical'])):
        if not (base.get(k, 0) > 0):
            continue
        t[k] = max(0, base[k] + DATA['cio']['tactical'].get(k, 0))
    s = nsum(t.values()) or 1
    return {k: v / s for k, v in t.items()}


def scope(hh: dict, sc: str) -> list[dict]:
    return [h for h in hh['holdings'] if h.get('acct') == 'brokerage'] if sc == 'brokerage' else hh['holdings']


def gap(hh: dict, sc: str, basis: str) -> dict:
    hs = scope(hh, sc)
    W = E.weights(hs); w, ct = W['w'], W['ct']
    t = cio_target(hh, basis); tol = DATA['cio']['tolerance']
    keys = [k for k in DATA['classes'] if w.get(k, 0) > 0.0005 or t.get(k, 0) > 0]
    rows = []
    for k in keys:
        g = w.get(k, 0) - t.get(k, 0)
        rows.append({'k': k, 'w': w.get(k, 0), 't': t.get(k, 0), 'g': g, 'usd': g * ct, 'out': abs(g) > tol['class'] + 1e-9})
    gw, gt = E.groups(w), E.groups(t)
    grps = [{'k': g, 'label': l, 'w': gw[g], 't': gt[g], 'g': gw[g] - gt[g], 'usd': (gw[g] - gt[g]) * ct,
             'out': abs(gw[g] - gt[g]) > tol['group'] + 1e-9} for g, l in E.GROUPS]
    return {'hs': hs, 'w': w, 'ct': ct, 't': t, 'rows': rows, 'groups': grps, 'st': E.stats(w), 'stT': E.stats(t),
            'out': nsum(1 for r in rows if r['out']), 'outG': nsum(1 for r in grps if r['out']), 'te': E.te(w, t)}


def sec_ret(sym: str, period: str, h: dict | None = None) -> float:
    p = DATA['perf']['sec'].get(sym)
    if p:
        return p[period]
    cl = (h or {}).get('classes') or {}
    return nsum(w * DATA['perf']['bench'][k][period] for k, w in cl.items())


def attribution(hh: dict, sc: str, period: str) -> dict:
    """Brinson-Fachler against the CIO strategic allocation, holding today's weights over the period."""
    hs = [h for h in scope(hh, sc) if h.get('classes')]
    W = E.weights(hs); w, ct = W['w'], W['ct']
    wb = cio_target(hh, 'strategic')
    Rb = lambda k: DATA['perf']['bench'][k][period]
    num: dict = {}; den: dict = {}
    for h in hs:
        r = sec_ret(h['sym'], period, h)
        for k, f in h['classes'].items():
            num[k] = num.get(k, 0) + h['mv'] * f * r
            den[k] = den.get(k, 0) + h['mv'] * f
    keys = list(dict.fromkeys(list(w) + list(wb)))
    Rp = lambda k: num[k] / den[k] if den.get(k) else Rb(k)
    RB = nsum(wb.get(k, 0) * Rb(k) for k in keys)
    RP = nsum(w.get(k, 0) * Rp(k) for k in keys)
    rows = []
    for k in keys:
        wp, b = w.get(k, 0), wb.get(k, 0)
        rows.append({'k': k, 'wp': wp, 'wb': b, 'rp': Rp(k), 'rb': Rb(k), 'alloc': (wp - b) * (Rb(k) - RB),
                     'sel': b * (Rp(k) - Rb(k)), 'inter': (wp - b) * (Rp(k) - Rb(k))})
    det = []
    for h in hs:
        bm = nsum(f * Rb(k) for k, f in h['classes'].items()); r = sec_ret(h['sym'], period, h)
        det.append({'sym': h['sym'], 'name': h['name'], 'mv': h['mv'], 'r': r, 'bm': bm, 'ex': r - bm, 'cost': h.get('expense_bps')})
    det = sorted([x for x in det if x['ex'] < -0.01 and x['sym'] != 'cash'], key=lambda x: x['ex'] * x['mv'])
    s = lambda f: nsum(r[f] for r in rows)
    return {'RB': RB, 'RP': RP, 'active': RP - RB, 'alloc': s('alloc'), 'sel': s('sel'), 'inter': s('inter'), 'rows': rows, 'det': det, 'ct': ct}


def program_fee(amount: float) -> dict:
    left, prev, fee, parts = amount, 0.0, 0.0, []
    for cap, rate in DATA['fees']['program']['tiers']:
        top = float('inf') if cap is None else cap
        slab = max(0, min(left, top - prev))
        if slab > 0:
            fee += slab * rate
            parts.append({'from': prev, 'to': cap, 'rate': rate, 'slab': slab, 'fee': slab * rate})
        left -= slab; prev = top
        if left <= 0:
            break
    return {'fee': fee, 'parts': parts}


def costs(hh: dict, amount: float, turnover: float, sma_share: float) -> dict:
    """The four options: stay in brokerage, the program with the CIO model, with SMA managers, and index-only."""
    hs = scope(hh, 'brokerage'); tot = nsum(h['mv'] for h in hs) or 1; f = DATA['fees']
    fund_bps = nsum(h['mv'] * (h.get('expense_bps') or 0) for h in hs) / tot
    gB = gap(hh, 'brokerage', 'tactical'); stS = gap(hh, 'brokerage', 'strategic')['stT']
    pf = program_fee(amount); eq = E.groups(gB['t'])['equity']
    opt = [
        {'id': 'stay', 'name': 'Stay in brokerage', 'parts': [['Fund expenses', amount * fund_bps / 1e4], ['Commissions', amount * turnover * f['brokerage']['commission']]],
         'er': gB['st']['er'], 'vol': gB['st']['vol'], 'note': f['brokerage']['note']},
        {'id': 'program', 'name': 'Advisory program: CIO model', 'parts': [['Program fee', pf['fee']], ['Fund expenses', amount * f['model_fund_bps'] / 1e4]],
         'er': gB['stT']['er'], 'vol': gB['stT']['vol'], 'note': f['program']['note'], 'rec': True},
        {'id': 'sma', 'name': 'Advisory program with SMA managers', 'parts': [['Program fee', pf['fee']], ['SMA manager fees', amount * eq * sma_share * f['sma_bps'] / 1e4],
         ['Fund expenses', amount * (1 - eq * sma_share) * f['model_fund_bps'] / 1e4]], 'er': gB['stT']['er'], 'vol': gB['stT']['vol'],
         'note': 'Equity sleeve run by separate account managers; tax management available.'},
        {'id': 'index', 'name': f['lower_cost']['name'], 'parts': [['Program fee', amount * f['lower_cost']['rate']], ['Fund expenses', amount * f['lower_cost']['fund_bps'] / 1e4]],
         'er': stS['er'], 'vol': stS['vol'], 'note': f['lower_cost']['note'], 'comp': True}]
    for o in opt:
        o['total'] = nsum(p[1] for p in o['parts']); o['bps'] = o['total'] / amount * 1e4; o['net'] = o['er'] - o['total'] / amount
    return {'opt': opt, 'fundBps': fund_bps, 'pf': pf, 'amount': amount}


def opt(c: dict, oid: str) -> dict:
    return next(o for o in c['opt'] if o['id'] == oid)


def cash_split(hh: dict) -> dict:
    """Canonical investable cash: brokerage cash above the CIO cash target, after the liquidity reserve and 2027 needs."""
    hs = scope(hh, 'brokerage'); amt = nsum(h['mv'] for h in hs); total = nsum(h['mv'] for h in hs if h.get('cash'))
    g = gap(hh, 'brokerage', 'tactical') if amt else None
    t_pct = next((r['t'] for r in g['rows'] if r['k'] == 'CASH'), 0) if g else 0
    target = min(total, t_pct * amt)
    needs = nsum(v for y, v in ((DATA['concentration'].get('cash_needs') or {}).get(hh['id']) or {}).items() if int(y) <= 2027)
    reserve = min(total - target, (hh.get('liquidity_reserve') or 0) + needs)
    return {'total': total, 'target': target, 'reserve': reserve, 'needs': needs, 'reserveBase': hh.get('liquidity_reserve') or 0,
            'investable': max(0, total - target - reserve)}


ROUTES = {'reserve': ['Kept as liquidity reserve', 'var(--c-other)'], 'transfer': ['Tax-efficient transition', 'var(--c1)'], 'instep': ['Invest in steps', 'var(--c3)'],
          'harvest': ['Sell and harvest loss', 'var(--c6)'], 'swap': ['Replace high-cost class', 'var(--c2)'], 'inkind': ['Move in kind', 'var(--c7)'],
          'basis': ['Hold until basis found', 'var(--c4)'], 'stay': ['Stays where it is', 'var(--c-other)']}


def routing(hh: dict) -> list[dict]:
    """Where each brokerage holding goes in a move to the advisory program."""
    out, cs = [], cash_split(hh)
    for h in scope(hh, 'brokerage'):
        lots = h.get('lots') or []
        cost = nsum((l.get('cost') or 0) for l in lots); has_null = any(l.get('cost') is None for l in lots)
        gain = h['mv'] - cost; gp = gain / h['mv'] if cost and not has_null else None
        if h.get('cash'):
            f = h['mv'] / cs['total'] if cs['total'] else 0
            if cs['investable'] * f > 1:
                out.append({'sym': h['sym'], 'name': h['name'], 'mv': cs['investable'] * f, 'gain': 0, 'route': 'instep', 'why': 'Cash above target after the reserve: invest in monthly steps over six months.'})
            if cs['target'] * f > 1:
                out.append({'sym': h['sym'], 'name': h['name'], 'mv': cs['target'] * f, 'gain': 0, 'route': 'inkind', 'why': "Cash at the CIO target: moves as the program's cash allocation."})
            if cs['reserve'] * f > 1:
                out.append({'sym': h['sym'], 'name': h['name'], 'mv': cs['reserve'] * f, 'gain': 0, 'route': 'reserve',
                            'why': 'Liquidity reserve' + (" and next year's cash needs" if cs['needs'] else '') + ': stays in brokerage.'})
            continue
        if not h.get('tradable'):
            r, why = 'stay', h.get('why_not') or 'Not transferable.'
        elif has_null:
            r, why = 'basis', 'Cost basis missing: move in kind; no sales until basis is on file.'
        elif gain < -1000:
            r, why = 'harvest', f'Loss of {money(-gain)}: sell, harvest the loss and reinvest.'
        elif (h.get('expense_bps') or 0) >= 50 and gp is not None and gp < 0.3:
            r, why = 'swap', f"Costs {h['expense_bps']} bp with a small gain: sell and replace with a lower-cost share class."
        elif gp is not None and gp > 0.2:
            r, why = 'transfer', f'Gain {pct(gp)} of value: move in kind; sell over time within the gain budget.'
        else:
            r, why = 'inkind', 'Small gain: move in kind; sell or keep as the model needs.'
        out.append({'sym': h['sym'], 'name': h['name'], 'mv': h['mv'], 'gain': gain, 'route': r, 'why': why})
    return out


def event_impact(ev: dict, h: dict) -> dict:
    """Estimated move on one holding, looking through funds."""
    m = ev.get('moves') or {}; n = m.get('names') or {}; sct = m.get('sectors') or {}; cl = m.get('classes') or {}
    r, via = 0.0, []
    if h.get('kind') == 'stock' and n.get(h['sym']) is not None:
        r += n[h['sym']]; via.append('direct')
    for s, w in (h.get('top_holdings') or {}).items():
        if n.get(s) is not None:
            r += w * n[s]; via.append(f'{s} inside')
    eqs = nsum((h.get('classes') or {}).get(k, 0) for k in E.EQ)
    if h.get('kind') == 'stock':
        if sct.get(h.get('sector')) is not None and n.get(h['sym']) is None:
            r += sct[h['sector']]; via.append('sector')
    else:
        for s, w in (h.get('sectors') or {}).items():
            if sct.get(s) is not None:
                r += eqs * w * sct[s]
                if 'sector' not in via:
                    via.append('sector')
    for k, w in (h.get('classes') or {}).items():
        if cl.get(k) is not None:
            r += w * cl[k]
            if 'bonds' not in via:
                via.append('bonds' if E.GROUP_OF[k] == 'fixed' else 'class')
    return {'r': r, 'usd': r * h['mv'], 'via': via}


def event_for_hh(ev: dict, hh: dict) -> dict:
    tot = nsum(h['mv'] for h in hh['holdings'])
    if ev.get('view'):
        g = gap(hh, 'all', 'tactical'); score = 0.0; rows = []
        for k, d in ev['view'].items():
            r = next((x for x in g['rows'] if x['k'] == k), None)
            if not r:
                continue
            mis = -d * r['g']
            if abs(r['g']) > 0.005:
                rows.append({'k': k, 'g': r['g'], 'usd': r['usd'], 'dir': d, 'against': mis > 0})
            score += max(0, mis) * g['ct']
        return {'kind': 'view', 'score': score, 'pctAcct': score / tot, 'rows': rows}
    if ev.get('research'):
        sym = ev['research']
        dg = next((d for d in DATA['downgrades'] if d['sym'] == sym), None)
        me = next((x for x in dg['holders'] if x['household_id'] == hh['id']), None) if dg else None
        look = E.names(hh['holdings']).get(sym, 0); direct = nsum(h['mv'] for h in hh['holdings'] if h['sym'] == sym)
        imp = [{'h': h, **event_impact(ev, h)} for h in hh['holdings']]
        imp = [x for x in imp if abs(x['usd']) > 1]
        return {'kind': 'research', 'score': direct or look * tot * 0.2, 'pctAcct': look, 'direct': direct, 'me': me, 'rows': imp}
    if ev.get('household'):
        return {'kind': 'client', 'score': 1e12 if ev['household'] == hh['id'] else 0, 'pctAcct': 0, 'rows': []}
    rows = [{'h': h, **event_impact(ev, h)} for h in hh['holdings']]
    rows = sorted([x for x in rows if abs(x['usd']) > 1], key=lambda x: x['usd'])
    usd = nsum(x['usd'] for x in rows)
    return {'kind': 'market', 'score': abs(usd), 'usd': usd, 'pctAcct': usd / tot, 'rows': rows}


def sale_plan(hh: dict, sym: str, o: dict) -> dict:
    """Multi-year sale plan for one concentrated position (prices held constant; illustrative)."""
    tot0 = nsum(h['mv'] for h in hh['holdings'])
    via = E.names(hh['holdings']).get(sym, 0) * tot0 - nsum(h['mv'] for h in hh['holdings'] if h['sym'] == sym)
    lots = [dict(l) for h in hh['holdings'] if h['sym'] == sym for l in (h.get('lots') or [])]
    tot = tot0; years = []; rates = hh['rates']
    held = lambda: nsum(l['mv'] for l in lots)

    def rank(l):
        g = (l['mv'] - l['cost']) / l['mv']
        return -10 + g if g < 0 else (10 if l.get('term') == 'ST' else 0) + g

    def sell_order():
        return sorted([l for l in lots if l.get('cost') is not None and l['mv'] > 0.5], key=rank)

    def sell_gain(amt):
        left, g = amt, 0.0
        for l in sell_order():
            if left <= 0.5:
                break
            t = min(left, l['mv']); g += (l['mv'] - l['cost']) * t / l['mv']; left -= t
        return g

    def do_sell(amt):
        left, g, tax = amt, 0.0, 0.0
        for l in sell_order():
            if left <= 0.5:
                break
            t = min(left, l['mv']); gn = (l['mv'] - l['cost']) * t / l['mv']
            g += gn; tax += gn * (rates['st'] if l.get('term') == 'ST' else rates['lt']) if rates.get('taxable') else 0
            l['cost'] *= 1 - t / l['mv']; l['mv'] -= t; left -= t
        return {'sold': amt - max(0, left), 'g': g, 'tax': tax}

    def do_gift(amt):
        left, g = amt, 0.0
        for l in sorted([l for l in lots if l.get('cost') is not None and l['mv'] > 0.5], key=lambda l: l['cost'] / l['mv']):
            if left <= 0.5:
                break
            t = min(left, l['mv']); g += (l['mv'] - l['cost']) * t / l['mv']
            l['cost'] *= 1 - t / l['mv']; l['mv'] -= t; left -= t
        return {'given': amt - max(0, left), 'g': g}

    budget = o.get('budget')
    for i in range(int(o['years'])):
        y = 2026 + i
        need = float((o.get('needs') or {}).get(str(y)) or 0)
        start = held()
        goal = max(0, start + via - o['target'] * tot)
        gift = min(o.get('gift') or 0, goal); gv = do_gift(gift); tot -= gv['given']
        excess = max(0, held() + via - o['target'] * tot); amt = excess
        if budget is not None:
            lo, hi = 0.0, excess
            if sell_gain(hi) > budget:
                for _ in range(30):
                    mid = (lo + hi) / 2
                    if sell_gain(mid) <= budget:
                        lo = mid
                    else:
                        hi = mid
                amt = lo
        if need > amt:
            amt = min(need, held())
        s = do_sell(amt); tot -= min(need, s['sold'])
        years.append({'y': y, 'start': start, 'gifted': gv['given'], 'giftGain': gv['g'], 'sold': s['sold'], 'gain': s['g'], 'tax': s['tax'], 'need': need,
                      'overBudget': budget is not None and s['g'] > budget + 1, 'end': held(), 'share': (held() + via) / tot, 'tot': tot})
    reach = next((r['y'] for r in years if r['share'] <= o['target'] + 1e-6), None)
    return {'years': years, 'via': via, 'reach': reach, 'start': E.names(hh['holdings']).get(sym)}
