"""Decision rules: one eligibility function, readiness, the allocation finding, the concentrated-position and event
rules, advisory value, the workflow lifecycle, and the firm-intelligence catalog.
Every benefit names its own measure: single-name concentration is not portfolio volatility, which is not tracking error."""
from __future__ import annotations
import re
from .data import DATA, HHS, State
from . import engine as E
from . import calc as X
from .fmt import money, pct, spct, ppt, cls, short, lc, nsum

STATUS = {'review': ['Review needed', 'warn', 'Review'], 'ready': ['Ready for client discussion', 'good', 'Discuss'], 'specialist': ['Specialist review', 'info', 'Specialist'],
          'blocked': ['Not eligible', 'bad', 'Not eligible'], 'monitor': ['Monitor', 'neutral', 'Monitor'], 'none': ['No action', 'neutral', 'No action'],
          'stay': ['Stay in brokerage', 'neutral', 'Stay'], 'defer': ['Defer', 'neutral', 'Defer'], 'unsuitable': ['Not suitable', 'neutral', 'Not suitable'],
          'respond': ['Respond to client', 'warn', 'Respond']}
ELIG = {'eligible': ['Eligible in principle', 'good', 'Eligible in principle'], 'conditions': ['Eligible in principle, with conditions', 'warn', 'Eligible · conditions'],
        'specialist': ['Requires specialist review', 'info', 'Specialist review'], 'ineligible': ['Not eligible for the program', 'bad', 'Not eligible']}
DISPOSITIONS = ['ready', 'review', 'specialist', 'stay', 'monitor', 'defer', 'unsuitable']
CLOSE_OUTCOMES = ['Discussed with the client', 'Proposal submitted for review', 'Referred to the specialist', 'Client declined', 'No action needed after review']
REASON_NEEDED = ['stay', 'unsuitable', 'defer']
REASONS = ['Tax cost too high', 'Trading restriction', 'Insufficient client value', 'Poor fit for the client', 'Client declined', 'Missing data', 'Timing: revisit later', 'Other']
BASE = {'scope': 'brokerage', 'basis': 'tactical', 'period': '3Y'}


def top_name(hh: dict):
    t = ('', 0)
    for s, v in E.names(hh['holdings']).items():
        if v > t[1]:
            t = (s, v)
    return t


def direct_share(hh: dict, sym: str) -> float:
    tot = nsum(h['mv'] for h in hh['holdings']) or 1
    return nsum(h['mv'] for h in hh['holdings'] if h['sym'] == sym and h.get('kind') == 'stock') / tot


def costs_default(hh: dict):
    amt = nsum(h['mv'] for h in X.scope(hh, 'brokerage'))
    return X.costs(hh, amt, DATA['fees']['brokerage']['turnover'], 0.5) if amt else None


def default_costs(hh: dict, amount: float | None = None) -> dict:
    """Costs at the brokerage amount rounded to $1,000 (or the given amount), default turnover and SMA share."""
    amt = round_k(nsum(h['mv'] for h in X.scope(hh, 'brokerage'))) if amount is None else amount
    return X.costs(hh, max(1, amt), DATA['fees']['brokerage']['turnover'], 0.5)


def round_k(x: float) -> int:
    from .fmt import js_round
    return js_round(x / 1000) * 1000


# ---------- the one eligibility function ----------
def elig(hh: dict) -> dict:
    sym, share = top_name(hh); lim = DATA['concentration']['exclude_over']; cond = []
    no_basis = nsum(l['mv'] for h in hh['holdings'] for l in (h.get('lots') or []) if l.get('cost') is None)
    insiders = [k.split(':')[1] for k, v in DATA['concentration']['positions'].items() if k.startswith(hh['id'] + ':') and v.get('insider')]
    mgr = list((hh.get('manager_run') or {}).keys())
    if insiders:
        cond.append({'t': f"Insider rules for {', '.join(insiders)}: pre-clearance and trading windows", 'owner': 'Compliance'})
    if no_basis:
        cond.append({'t': f'{money(no_basis)} without cost basis cannot be sold or planned', 'owner': 'Operations'})
    if mgr:
        cond.append({'t': f"{', '.join(mgr)} are run by a manager; the manager decides", 'owner': 'Manager'})
    dsh = direct_share(hh, sym)
    via = 'all through funds' if dsh <= 0 else (f'{pct(dsh, 1)} direct, {pct(share - dsh, 1)} through funds' if share - dsh > 0.0005 else 'held directly')
    if share > lim:
        return {'state': 'ineligible', 'sym': sym, 'share': share, 'direct': dsh, 'via': via,
                'reason': f'{sym} is {pct(share, 1)} of the account ({via}), above the {pct(lim)} single-security limit', 'route': 'Concentrated stock specialist',
                'cond': cond, 'blocks': ['Advisory program', 'CIO model portfolio', 'SMA and direct indexing', 'Tax-efficient transition']}
    return {'state': 'conditions' if cond else 'eligible', 'sym': sym, 'share': share, 'direct': dsh, 'via': via, 'cond': cond, 'blocks': []}


# ---------- readiness: discussion, proposal, implementation ----------
def ready(hh: dict, ctx: dict | None = None) -> list[dict]:
    ctx = ctx or {}; e = elig(hh); prop, impl = [], []
    if e['state'] == 'ineligible':
        prop.append({'t': e['reason'], 'owner': 'Specialist'})
    prop.append({'t': 'Suitability determination', 'owner': 'Advisor'})
    if ctx.get('risk'):
        prop.append({'t': 'Confirm the risk profile is current', 'owner': 'Advisor'})
    if ctx.get('product'):
        prop.append({'t': 'Product eligibility for SMA or direct indexing', 'owner': 'Product team'})
    for c in e['cond']:
        (prop if c['owner'] == 'Operations' else impl).append(c)
    impl += [{'t': 'Client agreement', 'owner': 'Client'}, {'t': 'Validated trade plan (this page shows planning estimates only)', 'owner': 'Portfolio management'},
             {'t': 'Compliance review of client materials', 'owner': 'Compliance'}, {'t': 'Supervisory approval', 'owner': 'Supervision'}]
    ex = e['state'] == 'ineligible'
    return [{'stage': 'Client discussion', 'state': 'ready', 'note': 'Ready: discuss the position and the specialist route' if ex else 'Ready: options and trade-offs can be discussed', 'items': []},
            {'stage': 'Proposal', 'state': 'blocked' if ex else 'pending', 'note': 'Blocked: no program proposal above the limit' if ex else f'Not ready: {len(prop)} to clear', 'items': prop},
            {'stage': 'Implementation', 'state': 'blocked', 'note': f'Not cleared: {len(impl)} prerequisites outstanding', 'items': impl}]


# ---------- the allocation finding from the active settings ----------
def ws1(hh: dict, o: dict | None = None, st: State | None = None) -> dict:
    o = o or BASE; st = st or State()
    sc = 'all' if o['scope'] == 'brokerage' and not X.scope(hh, 'brokerage') else o['scope']
    basis, period = o['basis'], o['period']; perL = 'three years' if period == '3Y' else 'one year'
    g = X.gap(hh, sc, basis); a = X.attribution(hh, sc, period); b = hh['band']; e = elig(hh)
    sym, share = e['sym'], e['share']; th = st.th; tot = nsum(h['mv'] for h in hh['holdings'])
    cash_tot = nsum(h['mv'] for h in hh['holdings'] if h.get('cash')) / tot
    risk = 'above' if g['st']['vol'] > b['high'] else 'below' if g['st']['vol'] < b['low'] else 'inside'
    tL = 'CIO tactical target' if basis == 'tactical' else 'CIO strategic target'
    top = sorted(a['rows'], key=lambda y: -abs(y['alloc'] + y['sel'] + y['inter']))[0]
    r = X.routing(hh); gains = nsum(max(0, x['gain']) for x in r if x['route'] == 'transfer')
    y1gain = min(gains, hh['gain_budget']) if hh.get('gain_budget') is not None else gains
    c = costs_default(hh); prog = X.opt(c, 'program') if c else None; stay = X.opt(c, 'stay') if c else None
    from .fmt import js_round
    r1 = lambda x: js_round(x * 1000)
    vol_up = r1(g['stT']['vol']) > r1(g['st']['vol']); gw, gt = E.groups(g['w']), E.groups(g['t'])
    mix_why = ('holds less cash than the portfolio does today' if gt['cash'] < gw['cash'] - 0.03 else
               'holds more stocks than the portfolio does today' if gt['equity'] > gw['equity'] + 0.03 else 'has a different mix')
    v0, v1 = pct(g['st']['vol'], 1), pct(g['stT']['vol'], 1)
    if e['state'] == 'ineligible':
        kind, status, finding = 'gate', 'specialist', f"{e['reason']} for the advisory program"
        nxt = f"Refer to the concentrated stock specialist; revisit the program once {sym} is below {pct(DATA['concentration']['exclude_over'])}."
    elif risk == 'above':
        kind, status = 'risk', 'review'
        finding = f"Expected volatility {v0} is above the {hh['profile']} band ({pct(b['low'], 1)}–{pct(b['high'], 1)})" + (f'; {sym} is {pct(share, 1)} of the account' if share > th else '')
        nxt = 'Review how to bring volatility back into the band after taxes and fees; compare staying in brokerage with a transition.'
    elif risk == 'below' and cash_tot > 0.2:
        kind, status = 'cash', 'review'
        finding = f"Expected volatility {v0} is below the {hh['profile']} band; {pct(cash_tot)} of the account is in cash"
        nxt = "Discuss investing the cash in steps toward the CIO allocation for the client's profile."
    elif share > th:
        kind, status = 'conc', 'ready'
        finding = f'{sym} is {pct(share, 1)} of the account: single-company concentration warrants a discussion'
        nxt = f'Review whether reducing {sym} is worth the taxes and fees; compare alternatives before suggesting a transition.'
    elif a['active'] < -0.01:
        kind, status = 'perf', 'review'
        finding = f"Trailing the CIO allocation by {ppt(-a['active'])} a year over {perL}, mostly from {'fund selection' if abs(a['sel']) > abs(a['alloc']) else 'allocation'}"
        nxt = 'Review the detracting funds and whether lower-cost or managed alternatives fit.'
    elif g['out'] > 0:
        kind, status = 'drift', 'monitor'
        finding = f"Drift from the {tL} ({g['out']} asset class{'' if g['out'] == 1 else 'es'} outside tolerance), with volatility inside the profile band"
        nxt = 'Rebalance at the next scheduled review; no change needed now.'
    else:
        kind, status, finding, nxt = 'none', 'none', f'In line with the {tL} and the risk profile', 'No action.'
    shock = 0.3 * share * tot
    if kind == 'conc':
        lead = (f"The portfolio has outperformed ({ppt(a['active'])} a year over {perL}) and volatility is inside the profile band, but the result rests on {sym}."
                if a['active'] > 0 else f'The result depends heavily on {sym}.')
        if vol_up:
            tail = f'Moving to the {tL} would cut single-company risk but raise expected portfolio volatility slightly ({v0} → {v1}), because the target {mix_why}: the case is about concentration, not lower volatility.'
        elif r1(g['stT']['vol']) < r1(g['st']['vol']):
            tail = f'Moving to the {tL} would also lower expected volatility ({v0} → {v1}).'
        else:
            tail = f'Expected portfolio volatility would stay about the same at the {tL} ({v0} → {v1}): the case is about single-company concentration, not lower volatility.'
        why = f'{lead} A 30% fall in {sym} would cost about {money(shock)}. {tail}'
    else:
        why = {'risk': f"Volatility above the agreed profile is a suitability matter, regardless of past returns. At the {tL} expected volatility would be {v1}.",
               'cash': f"Much less volatility than the profile implies may leave the client short of their return objective; expected return {pct(g['st']['er'], 1)} against {pct(g['stT']['er'], 1)} at the {tL}.",
               'gate': 'Above this limit the program is not available; the first step is a specialist plan for the position.',
               'perf': 'Persistent underperformance against the CIO allocation, after costs, is worth explaining to the client.',
               'drift': 'Differences from the CIO model alone are not proof that a change would help the client.'}.get(kind, 'Nothing material to raise.')
    trade = [
        ['Single-company concentration', f'{sym} {pct(share, 1)}; guideline {pct(th)}' if share > th else f'largest {sym} {pct(share, 1)}', 'warn' if share > th else ''],
        ['Portfolio volatility', f'{v0} → {v1} at the {basis} target', 'warn' if vol_up else 'good' if g['stT']['vol'] < g['st']['vol'] - 0.0005 else ''],
        ['Tracking error to the CIO target', f"{pct(g['te'], 1)} → 0%", ''],
        ['Suitability (profile band)', f"{risk} the band ({pct(b['low'], 1)}–{pct(b['high'], 1)})", 'good' if risk == 'inside' else 'bad'],
        ['Estimated gains, year one (planning)', 'n/a: transition not available' if e['state'] == 'ineligible' else (f"{money(y1gain)}; tax ≈ {money(y1gain * hh['rates']['lt'])}" if y1gain else 'none needed'),
         'warn' if y1gain and e['state'] != 'ineligible' else ''],
        ['Fees (illustrative)', f"{money(prog['total'])} in the program vs {money(stay['total'])} a year today" if prog else '—', 'warn' if prog and prog['total'] > stay['total'] else '']]
    choices = ([['Specialist review', 'recommended'], ['Stay in brokerage', ''], ['Advisory program', 'blocked']] if kind == 'gate' else
               [['Monitor', 'recommended'], ['Rebalance in brokerage', ''], ['Advisory program', 'suitability dependent']] if kind in ('none', 'drift') else
               [['Review alternatives', 'recommended'], ['Stay in brokerage', ''], ['Advisory program', 'with conditions' if e['state'] == 'conditions' else 'suitability dependent'], ['Monitor', '']])
    return {'kind': kind, 'status': status, 'finding': finding, 'why': why, 'next': nxt, 'g': g, 'a': a, 'sym': sym, 'share': share, 'risk': risk, 'cash': cash_tot,
            'elig': e, 'scope': sc, 'basis': basis, 'period': period, 'ready': ready(hh, {'risk': kind == 'risk', 'product': kind == 'conc'}),
            'assumptions': f"{'Brokerage accounts' if sc == 'brokerage' else 'Whole household'} · {tL} · {'3-year' if period == '3Y' else '1-year'} performance",
            'baseline': sc == BASE['scope'] and basis == BASE['basis'] and period == BASE['period'],
            'evidence': [f"Expected volatility {v0}, band {pct(b['low'], 1)}–{pct(b['high'], 1)} ({risk})",
                         f"{g['out']} asset class{'' if g['out'] == 1 else 'es'} outside tolerance of the {tL}; tracking error {pct(g['te'], 1)}",
                         f"{'3-year' if period == '3Y' else '1-year'} return {spct(a['active'])} vs the CIO allocation, mostly {lc(short(top['k']))}"],
            'trade': trade, 'choices': choices}


# ---------- concentrated position ----------
def ws3(p: dict, plan: dict, hh: dict) -> dict:
    e = elig(hh); lim = DATA['concentration']['exclude_over']; f = p.get('flags') or {}
    lots = [l for h in hh['holdings'] if h['sym'] == p['sym'] for l in (h.get('lots') or [])]
    no_basis = nsum(l['mv'] for l in lots if l.get('cost') is None)
    over = e['state'] == 'ineligible' and e['sym'] == p['sym']; gates = []
    if over:
        gates.append(['bad', f"Not eligible for the program: above the {pct(lim)} single-security limit. Program, SMA and direct-indexing paths are blocked until {p['sym']} is below {pct(lim)}."])
    if f.get('insider'):
        gates.append(['warn', f"Insider: {f.get('restricted') or 'pre-clearance and trading windows apply'} (owner: Compliance)"])
    if no_basis:
        gates.append(['bad', f'{money(no_basis)} has no cost basis on file: it cannot be sold or planned until basis is found (owner: Operations).'])
    status = 'specialist' if over else 'review' if f.get('insider') else 'ready'; y1 = plan['years'][0]
    tot = nsum(h['mv'] for h in hh['holdings'])
    reach = f"reaches {pct(plan['target'], 1)} by {plan['reach']}" if plan['reach'] else f"is still above {pct(plan['target'], 1)} after {len(plan['years'])} years"
    act = {'staged': ['After pre-clearance', 'warn'] if f.get('insider') else ['Advisor can act', 'good'],
           'tm-sma': ['Not eligible: program limit', 'bad'] if e['state'] == 'ineligible' else ['Product eligibility to confirm', 'info'],
           'di': ['Not eligible: program limit', 'bad'] if e['state'] == 'ineligible' else ['Product eligibility to confirm', 'info'],
           'gift': ['Client and tax advisor decide', 'info'], 'hedge': ['Specialist review', 'info']}
    return {'status': status, 'gates': gates, 'elig': e, 'ready': ready(hh, {'product': not over}),
            'finding': f"{p['sym']} is {pct(p['share'], 1)} of {hh['name']}'s account ({money(p['direct'])} direct, {money(plan['via'])} through funds)",
            'why': 'Above the program limit, the first step is a specialist plan for the position.' if over else f"A 30% fall in {p['sym']} would cost the household about {money(0.3 * p['share'] * tot)}.",
            'next': (f"Refer to the concentrated stock specialist; staged sales in brokerage can start{' after pre-clearance' if f.get('insider') else ''}." if over
                     else f'Agree a target and pace with the client: the planning scenario {reach} within the gain budget.'),
            'evidence': [f"Share {pct(p['share'], 1)} (direct and look-through)", f"Planning scenario, year one: sell {money(y1['sold'])}, estimated tax {money(y1['tax'])} → {pct(y1['share'], 1)}",
                         'Insider rules apply' if f.get('insider') else 'No trading restrictions on file'],
            'act': act}


# ---------- event materiality and confidence ----------
def ws4(ev: dict, r: dict, st: State | None = None) -> dict:
    st = st or State()
    if r['kind'] == 'market':
        m = abs(r['pctAcct']); nm = E.names(r['hh']['holdings'])
        conc = any(nm.get(x['h']['sym'], 0) > st.th for x in r['rows'])
        size = f"{money(r['usd'])} ({spct(r['pctAcct'], 2)} of the account), estimated scenario impact"
        return {'material': m >= 0.005, 'conf': "Estimated scenario impact (model): the event's price moves applied to today's holdings, looking through funds. Not a realized gain or loss.",
                'status': ('review' if conc else 'ready') if m >= 0.005 else 'monitor' if m >= 0.001 else 'none',
                'action': ('Review the concentrated position' if conc else 'Contact the client') if m >= 0.005 else 'Monitor' if m >= 0.001 else 'No action', 'size': size}
    if r['kind'] == 'view':
        ag = sorted([x for x in r['rows'] if x['against']], key=lambda x: -abs(x['g'])); m = abs(ag[0]['g']) if ag else 0
        size = (', '.join(f"{lc(short(x['k']))} {ppt(x['g'], 1)}" for x in ag[:2]) + ' against the new view') if ag else 'in line with the new view'
        return {'material': m >= 0.05, 'conf': "Verified exposure: today's holdings compared with the new CIO tactical view.", 'status': 'review' if m >= 0.05 else 'monitor',
                'action': 'Reassess the allocation' if m >= 0.05 else 'Monitor', 'size': size}
    if r['kind'] == 'research':
        mgr = bool(r.get('me')) and bool(re.search('Manager', r['me']['decides'])); direct = r['direct'] > 0
        return {'material': direct, 'conf': 'Verified exposure: the stock is held directly. The rating change is dated firm research, not a price forecast.' if direct else 'Held only inside broad funds.',
                'status': ('review' if mgr else 'ready') if direct else 'none', 'action': ('Request a manager review' if mgr else 'Review alternatives') if direct else 'No action',
                'size': f"{money(r['direct'])} held directly" if direct else f"{pct(r['pctAcct'], 2)} through funds"}
    return {'material': True, 'conf': 'Client question received.', 'status': 'respond', 'action': 'Respond to the client', 'size': 'client asked'}


# ---------- advisory value: value first, then the fee ----------
def value(hh: dict, c: dict) -> dict:
    amt = c['amount']; p = X.opt(c, 'program'); s = X.opt(c, 'stay'); e = elig(hh); lt = hh['rates']['lt']
    gB = X.gap(hh, 'brokerage', 'tactical'); eq = E.groups(gB['t'])['equity'] * amt; di_amt = min(eq, amt * 0.4)
    di_ok = e['state'] != 'ineligible' and di_amt >= 250000
    er = (p['er'] - s['er']) * amt; harv_tax = 0.02 * di_amt * lt if di_ok else 0; di_fee = di_amt * DATA['fees']['di_bps'] / 1e4 if di_ok else 0; harv_net = harv_tax - di_fee
    r = X.routing(hh); gains = nsum(max(0, x['gain']) for x in r if x['route'] == 'transfer')
    y1 = min(gains, hh['gain_budget']) if hh.get('gain_budget') is not None else gains
    loss_now = nsum(-x['gain'] for x in r if x['route'] == 'harvest')
    inc = p['total'] - s['total']; quant = max(0, er) + max(0, harv_net); net = er + harv_net - inc
    return {'y1taxNet': max(0, y1 - loss_now) * lt, 'amt': amt, 'er': er, 'erPts': p['er'] - s['er'], 'harvTax': harv_tax, 'diFee': di_fee, 'harvNet': harv_net, 'diAmt': di_amt,
            'diOk': di_ok, 'gains': gains, 'taxAll': gains * lt, 'y1tax': y1 * lt, 'lossNow': loss_now, 'lossTax': loss_now * lt, 'inc': inc, 'quant': quant, 'net': net,
            'cover': quant / inc if inc > 0 else None, 'comm': s['parts'][1][1], 'prog': p, 'stay': s}


# ---------- firm intelligence: one catalog, two projections ----------
def catalog() -> list[dict]:
    def stance(n):
        dg = next((d for d in DATA['downgrades'] if d['sym'] == n.get('research')), None) if n.get('research') else None
        v = next((x for x in DATA['cio']['views'] if x['key'] == n.get('cio')), None) if n.get('view') else None
        return f"{dg['sym']}: {dg['change']['to']} (was {dg['change']['from']})" if dg else f"{cls(v['key'])}: {v['view']} (was {v['was']})" if v else None
    items = [{'id': n['id'], 'date': n['date'], 'type': n['type'], 'source': n['source'], 'headline': n['headline'], 'abstract': n['summary'], 'stance': stance(n), 'auto': True,
              'ev': n, 'status': 'Published', 'version': 'v1', 'client_use': n['type'] != 'market', 'expires': None,
              'entitled': 'All advisors (third-party news)' if n['type'] == 'market' else 'All advisors', 'tags': [cls(k) for k in [n.get('cio')] if k]}
             for n in DATA['news'] if n['type'] != 'client']
    items += [{**f, 'ev': {'id': f['id'], 'date': f['date'], 'type': f['type'], 'moves': f.get('moves') or {'names': {}, 'sectors': {}, 'classes': {}}, 'view': f.get('view'),
                           'research': f['sym'] if f['rule'] == 'research' else None, 'cio': None}} for f in DATA['intel']]
    return sorted(items, key=lambda x: x['date'], reverse=True)


def intel_for(it: dict, hh: dict, st: State | None = None) -> dict:
    tot = nsum(h['mv'] for h in hh['holdings'])
    if it.get('rule') == 'superseded':
        return {'state': 'na', 'size': 'Superseded', 'why': it['superseded_by']}
    if it.get('rule') == 'region-sector':
        f = [h for h in hh['holdings'] if (h.get('classes') or {}).get('INTL', 0) + (h.get('classes') or {}).get('EM', 0) > 0]
        mv = nsum(h['mv'] * ((h.get('classes') or {}).get('INTL', 0) + (h.get('classes') or {}).get('EM', 0)) for h in f)
        if f:
            return {'state': 'unknown', 'size': f'{money(mv)} international equity',
                    'why': f"The look-through for {', '.join(h['sym'] for h in f)} has no country-by-sector data, so {it['region']} bank exposure cannot be measured."}
        return {'state': 'none', 'size': 'no international equity', 'why': 'No international equity held.'}
    r = X.event_for_hh(it['ev'], hh)
    if it.get('auto'):
        if r['score'] <= 1:
            return {'state': 'none', 'size': 'not exposed', 'why': 'No exposure found in holdings or fund look-through.'}
        m = ws4(it['ev'], {'hh': hh, **r}, st)
        return {'state': 'matched' if m['material'] else 'monitor', 'size': m['size'], 'why': m['conf'], 'action': m['action']}
    if it.get('rule') == 'research':
        look = E.names(hh['holdings']).get(it['sym'], 0)
        if r['direct'] > 0:
            return {'state': 'matched', 'size': f"{money(r['direct'])} held directly", 'why': 'Verified exposure: held directly. A rating change is dated firm research, not a price forecast.', 'action': 'Mention at the next review'}
        if look > 0.001:
            return {'state': 'monitor', 'size': f'{pct(look, 2)} through funds', 'why': 'Held only inside funds.', 'action': 'Monitor'}
        return {'state': 'none', 'size': 'not held', 'why': 'Not held directly or in fund look-through on file.'}
    m = ws4(it['ev'], {'hh': hh, **r}, st)
    if it.get('rule') == 'view':
        if m['material']:
            return {'state': 'matched', 'size': m['size'], 'why': m['conf'], 'action': m['action']}
        if r['rows']:
            return {'state': 'monitor', 'size': m['size'], 'why': m['conf'], 'action': 'Monitor'}
        return {'state': 'none', 'size': 'no exposure to the asset class', 'why': m['conf']}
    if m['material']:
        return {'state': 'matched', 'size': m['size'], 'why': m['conf'], 'action': m['action']}
    if abs(r.get('pctAcct') or 0) >= 0.001:
        return {'state': 'monitor', 'size': m['size'], 'why': m['conf'], 'action': 'Monitor'}
    return {'state': 'none', 'size': m['size'], 'why': m['conf']}


def book_status(it: dict, st: State) -> dict:
    if it.get('rule') == 'superseded':
        return {'k': 'na', 'label': 'Superseded: not evaluated', 'n': 0}
    if not it.get('auto') and not st.intel_run.get(it['id']):
        return {'k': 'pending', 'label': 'Not yet evaluated', 'n': 0}
    res = [intel_for(it, hh, st) for hh in HHS()]
    n = nsum(1 for x in res if x['state'] == 'matched'); u = nsum(1 for x in res if x['state'] == 'unknown')
    if n:
        return {'k': 'match', 'label': f"Affects my book: {n} household{'' if n == 1 else 's'}", 'n': n}
    if u:
        return {'k': 'unknown', 'label': f"Not evaluated for {u} household{'' if u == 1 else 's'}: insufficient data", 'n': 0}
    return {'k': 'none', 'label': 'No identified impact', 'n': 0}


# ---------- lifecycle: open · monitoring · deferred · closed (separate from the assessment) ----------
def life(d: dict | None) -> dict:
    if not d:
        return {'state': 'open', 'label': 'Open', 'note': ''}
    if d.get('closed'):
        return {'state': 'closed', 'label': 'Closed', 'note': d['closed']['outcome']}
    if d.get('status') in REASON_NEEDED:
        if d.get('reason'):
            if d['status'] == 'defer':
                return {'state': 'deferred', 'label': 'Deferred', 'note': d['reason']}
            return {'state': 'closed', 'label': 'Closed', 'note': f"{STATUS[d['status']][0]}: {d['reason']}"}
        return {'state': 'open', 'label': 'Open', 'note': f"Add a reason to {'defer' if d['status'] == 'defer' else 'close'} it", 'need': True}
    if d.get('status') == 'monitor':
        return {'state': 'monitoring', 'label': 'Monitoring', 'note': d.get('reason') or ''}
    return {'state': 'open', 'label': 'Open', 'note': f"Advisor assessment: {STATUS[d['status']][0]}"}


def group(o: dict) -> str:
    L = life(o.get('disp')); s = o['disp']['status'] if o.get('disp') else o['status']
    if L['state'] == 'closed':
        return 'done'
    if L['state'] in ('deferred', 'monitoring'):
        return 'monitor'
    if s == 'specialist' or o['act'][1] == 'bad':
        return 'specialist'
    if not o.get('disp') and s in ('monitor', 'none'):
        return 'monitor'
    return 'action'
