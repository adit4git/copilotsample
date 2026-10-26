"""Screen data: everything a screen needs, computed by the rule engine and returned as JSON.
The browser only formats and lays it out. Households appear by id ("hid"); nothing here changes state."""
from __future__ import annotations
import copy
import re
from datetime import date
from .data import DATA, HHS, State, household
from . import engine as E
from . import calc as X
from . import rules as D
from . import pathway as P
from . import opportunities as Q
from .fmt import money, pct, spct, ppt, short, lc, js_round, num, nsum

TODAY = '2026-10-24'
VIEWL = {'ws1': 'Allocation and performance', 'ws2': 'Client proposal', 'ws3': 'Concentrated position', 'ws4': 'Market and research'}
HSTEPS = [['assess', 'Client case'], ['paths', 'Compare routes'], ['proposal', 'Client proposal'], ['handoff', 'Implementation handoff']]


def hh_brief(hh: dict) -> dict:
    return {'id': hh['id'], 'name': hh['name'], 'profile': hh['profile'], 'value': hh['value'], 'meeting': hh['meeting'], 'brokerage': P.amt(hh), 'band': hh['band']}


def pub(o: dict, st: State, steps: bool = False) -> dict:
    return Q.public(o, st, steps)


# ---------------------------------------------------------------- landing
def landing(st: State) -> dict:
    q = Q.all_queue(st); H = P.households(q, st)
    rows = []
    for x in H:
        prim = x['prim']
        others = [{'key': o['key'], 'kind': P.KIND.get(o['uc'], ''), 'why': P.why_of(o, st)} for o in x['open'] if o is not prim and o['uc'] != 7]
        rows.append({'hid': x['hh']['id'], 'name': x['hh']['name'], 'meeting': x['hh']['meeting'], 'ex': x['ex'], 'cues': x['cues'], 'why': x['why'], 'others': others,
                     'now': x['A']['now'], 'held': x['A']['laterSum'] + x['A']['kept'], 'path': x['path']['id'] if x['path'] else None, 'blk': x['blk'],
                     'life': x['hs']['L'], 'next': x['hs']['next'], 'filt': x['filt'], 'seg': x['seg']})
    return {'rows': rows, 'book': P.book(q, st), 'segnote': DATA['pathway']['segments']['hard'], 'nhh': len(HHS()), 'as_of': DATA['as_of']['positions']}


def workflow(st: State) -> dict:
    q = Q.all_queue(st)
    return {'rows': [{**pub(o, st), 'life': D.life(o.get('disp'))} for o in q]}


# ---------------------------------------------------------------- left list
def entries(st: State, ws: str, qv: str, o4: dict) -> dict:
    if ws == 'path' or (ws == 'queue' and qv == 'hh'):
        q = Q.all_queue(st)
        return {'kind': 'households', 'rows': [{'hid': x['hh']['id'], 'name': x['hh']['name'], 'ex': x['ex'], 'life': x['hs']['L']['state'], 'now': x['A']['now'],
                                                'path': x['path']['id'] if x['path'] else None} for x in P.households(q, st)]}
    if ws == 'queue':
        q = Q.all_queue(st)
        n = lambda g: nsum(1 for o in q if (o['grp'] != 'done' if g == 'all' else o['grp'] == g))
        return {'kind': 'groups', 'counts': {g: n(g) for g in ['all', 'action', 'specialist', 'monitor', 'done']}}
    if ws in ('ws1', 'ws2'):
        rows = []
        for hh in HHS():
            f = D.ws1(hh, D.BASE, st)
            rows.append({'hid': hh['id'], 'name': hh['name'], 'status': f['status'], 'ev': f['evidence'][0].split(',')[0]})
        pr = {'review': 3, 'specialist': 3, 'ready': 2, 'monitor': 1}
        return {'kind': 'hhlist', 'rows': sorted(rows, key=lambda r: -pr.get(r['status'], 0))}
    if ws == 'ws3':
        return {'kind': 'positions', 'th': st.th, 'rows': [{'key': p['key'], 'sym': p['sym'], 'hname': p['hh']['name'], 'share': p['share'], 'excl': p['excl'],
                                                            'insider': bool(p['flags'].get('insider'))} for p in Q.conc_list(st)]}
    if o4.get('view') == 'firm':
        C = D.catalog(); bs = [(it, D.book_status(it, st)) for it in C]; watch = set(o4.get('watch') or [])
        return {'kind': 'firm', 'types': {t: nsum(1 for it in C if t == 'all' or it['type'] == t) for t in ['all', 'market', 'cio', 'research']},
                'book': {k: nsum(1 for it, b in bs if k == 'all' or (it['id'] in watch if k == 'watch' else b['k'] == k)) for k in ['all', 'match', 'none', 'pending', 'unknown', 'na', 'watch']}}
    F = o4.get('filter') or 'all'
    evs = sorted([n for n in DATA['news'] if F == 'all' or n['type'] == F], key=lambda n: n['date'], reverse=True)
    rows = []
    for n in evs:
        mat = 0
        for hh in HHS():
            r = X.event_for_hh(n, hh)
            if r['score'] > 1 and D.ws4(n, {'hh': hh, **r}, st)['material']:
                mat += 1
        rows.append({'id': n['id'], 'headline': n['headline'], 'date': n['date'], 'type': n['type'], 'source': n['source'], 'material': mat})
    return {'kind': 'events', 'rows': rows, 'n': len(DATA['news'])}


# ---------------------------------------------------------------- household flow
def plan_rows(hh: dict) -> dict:
    tr = P.transition(hh)
    return {'rows': [{k: x[k] for k in ('sym', 'route', 'mv', 'gain', 'why')} for x in tr['r']], 'pct': tr['pct'], 'taxNet': tr['taxNet']}


def value_rows(hh: dict, st: State) -> list[list]:
    """Client value and cost, by measure; each figure tagged observed, estimate, modeled or needs validation."""
    f = P.forgone(hh); tr = P.transition(hh); R = P.remain(hh); A = P.amounts(hh)
    nm = sorted([(k, w) for k, w in E.names(hh['holdings']).items() if w > st.th], key=lambda x: -x[1])
    nm = nm[0] if nm else None
    c = X.costs(hh, max(1, D.round_k(A['now'])), DATA['fees']['brokerage']['turnover'], 0.5)
    prog = X.opt(c, 'program'); stay = X.opt(c, 'stay'); v = D.value(hh, c); b = hh['band']
    rows = [['Risk', 'mod', f"Expected volatility {pct(f['volNow'], 1)} → {pct(f['volT'], 1)} at the CIO target; profile band {pct(b['low'], 1)}–{pct(b['high'], 1)}",
             'warn' if f['volT'] > b['high'] or f['volT'] < b['low'] else ''],
            ['Expected return, gross', 'mod', f"{pct(f['erNow'], 2)} → {pct(f['erT'], 2)} before costs: an illustrative scenario difference of ≈ {'+' if f['yr'] >= 0 else '−'}{money(abs(f['yr']))} a year under capital market assumptions; not a forecast or a guaranteed benefit", '']]
    if nm:
        rows.append(['Concentration', 'obs', f'{nm[0]} is {pct(nm[1], 1)} of the account against a {pct(st.th)} guideline', ''])
    if tr['gains'] or tr['losses']:
        t = (f"≈ {money(tr['taxNet'])} after harvested losses on the phased route; ≈ {money(max(0, tr['gains'] - tr['losses']) * hh['rates']['lt'])} if rebalanced at once. "
             f"Planning level; depends on validated lots, rates and timing" + (f". Not decision-ready: {money(tr['noBasis'])} has no cost basis" if tr['noBasis'] else ''))
    else:
        t = 'No material gains to realize'
    rows.append(['Tax, year one', 'val' if tr['noBasis'] else 'est', t, 'warn' if tr['noBasis'] else ''])
    if v['diOk']:
        rows.append(['Loss harvesting', 'mod', f"≈ {money(v['harvNet'])} a year after the manager fee, on the direct-indexing route only", ''])
    rows.append(['Incremental fee', 'est', f"{money(prog['total'])} a year in the program (steady state on {money(A['now'])} from enrollment) vs {money(stay['total'])} today: +{money(prog['total'] - stay['total'])}. "
                 f"The lower-cost {R['lc']['name']} is {js_round(R['lc']['bps'])} bp", 'warn'])
    return rows


def household_view(hid: str, st: State) -> dict:
    hh = household(hid); q = Q.all_queue(st); ops = [o for o in q if o['hh']['id'] == hid]; open_ = [o for o in ops if o['grp'] != 'done']
    prim = P.primary(open_ or ops); A = P.amounts(hh); H = P.hstate(hh, st); e = D.elig(hh)
    A_pub = {k: v for k, v in A.items() if k != 'buckets'}
    K = A['buckets']
    return {'hh': hh_brief(hh), 'elig': e, 'eligLabel': D.ELIG[e['state']], 'H': {k: H[k] for k in ('k', 'd', 'L', 'path', 'rev', 'step', 'next')},
            'prim': pub(prim, st) if prim else None, 'cat': P.catalyst(hh, open_), 'A': A_pub, 'blk': P.blocker(hh), 'valueRows': value_rows(hh, st),
            'others': [{'key': o['key'], 'kind': P.KIND.get(o['uc'], ''), 'why': P.why_of(o, st)} for o in open_ if o is not prim and o['uc'] != 7],
            'ops': [pub(o, st, True) for o in ops],
            'buckets': {'rows': [{k: r[k] for k in ('sym', 'bucket', 'label', 'mv', 'route', 'overlay')} for r in K['rows']], 'move': K['move'], 'gated': K['gated'],
                        'kept': K['kept'], 'excluded': K['excluded'], 'total': K['total'], 'labels': K['labels']},
            'plan': plan_rows(hh), 'handed': bool(st.handed.get(hid)),
            'evidence': {'positions': DATA['as_of']['positions'], 'returns': DATA['perf']['as_of'], 'cio': DATA['cio']['updated'], 'research': DATA['as_of']['research'],
                         'look_through': DATA['as_of']['look_through'], 'note': DATA['pathway']['note']}}


def paths_view(hid: str, st: State) -> dict:
    hh = household(hid); H = P.hstate(hh, st); R = P.remain(hh); c = D.default_costs(hh); v = value_case(hh, c, st); tr = P.transition(hh)
    return {'hh': hh_brief(hh), 'paths': P.paths(hh, st), 'H': {'path': H['path'], 'd': H['d'], 'step': H['step']}, 'remain': R, 'stayR': v['stayR'],
            'options': [{k: x[k] for k in ('name', 'kind', 'why', 'min')} for x in P.options(hh)], 'noBasis': tr['noBasis'], 'plan': plan_rows(hh), 'handed': bool(st.handed.get(hid))}


def handoff_view(hid: str, st: State) -> dict:
    hh = household(hid); h = P.handoff(hh, st); H = P.hstate(hh, st)
    return {'hh': hh_brief(hh), 'items': h['items'], 'steps': h['steps'], 'now': h['A']['now'], 'later': h['A']['later'], 'kept': h['A']['kept'], 'path': h['path'],
            'ex': D.elig(hh)['state'] == 'ineligible', 'handed': bool(st.handed.get(hid)), 'plan': plan_rows(hh), 'H': {'step': H['step']}}


# ---------------------------------------------------------------- client proposal
def why_now(hh: dict, st: State) -> list[dict]:
    f = D.ws1(hh, D.BASE, st); conc = [p for p in Q.conc_list(st) if p['hh']['id'] == hh['id']]; out = []
    if f['status'] != 'none':
        out.append({'key': 'ws1', 'title': 'Allocation review', 'text': f['finding'] + '.', 'src': f"Allocation review · positions {DATA['as_of']['positions']}"})
    for p in conc:
        if not (f['kind'] == 'conc' and f['sym'] == p['sym']):
            out.append({'key': 'conc:' + p['sym'], 'title': f"{p['sym']} concentration", 'text': f"{p['sym']} is {pct(p['share'], 1)} of the account including funds, above the {pct(st.th)} guideline.",
                        'src': f"Concentrated position · positions {DATA['as_of']['positions']}"})
    a = f['a']
    if a['active'] < -0.005:
        out.append({'key': 'perf', 'title': 'Trailing the CIO allocation', 'text': f"Over three years the portfolio returned {pct(a['RP'], 1)} a year against {pct(a['RB'], 1)} for the CIO allocation.",
                    'src': f"Return history · {DATA['perf']['as_of']}"})
    for n in DATA['news']:
        r = X.event_for_hh(n, hh)
        if r['score'] > 1 and D.ws4(n, {'hh': hh, **r}, st)['material']:
            out.append({'key': 'ev:' + n['id'], 'title': n['headline'], 'text': n['house'], 'src': f"{n['source']} · {n['date']}"})
    return out


def topics_for(hh: dict, st: State, clips: list) -> list[str]:
    t = ['value', 'fees', 'fiduciary']
    if any(p['hh']['id'] == hh['id'] for p in Q.conc_list(st)):
        t += ['concentrated', 'tax']
    r = X.routing(hh)
    if any(x['route'] == 'transfer' for x in r): t += ['transition', 'tax']
    if any(x['route'] == 'instep' for x in r): t.append('cash')
    if any(c.get('ws') == 'ws4' for c in clips): t += ['market', 'cio']
    t.append('sma')
    return list(dict.fromkeys(t))


def value_case(hh: dict, c: dict, st: State) -> dict:
    """The advisory value case: value first, the fee after it, and the points to weigh openly."""
    f = D.ws1(hh, D.BASE, st); val = D.value(hh, c); prog = val['prog']; stay = val['stay']; inc = val['inc']
    turnover = (st.o2.get(hh['id']) or {}).get('turnover', DATA['fees']['brokerage']['turnover'])
    stay_r = []
    if val['cover'] is not None and val['net'] < 0:
        stay_r.append(f"The benefits that can be estimated (about {money(val['quant'])} a year) cover about {js_round(val['cover'] * 100)}% of the higher fee; ongoing advice, planning and risk management make up the rest.")
    if prog['vol'] > stay['vol'] + 0.0005:
        stay_r.append(f"Expected volatility rises at the CIO allocation ({pct(stay['vol'], 1)} → {pct(prog['vol'], 1)}); the case is about diversification and advice, not lower volatility.")
    if c['fundBps'] < 15:
        stay_r.append(f"Today's funds are already low-cost (about {js_round(c['fundBps'])} bp), so fund savings are small.")
    if turnover <= 0.15:
        stay_r.append(f"Trading is light (about {pct(turnover)} of the portfolio a year), so included trading saves only about {money(val['comm'])} a year.")
    if f['elig']['state'] == 'ineligible':
        stay_r.append(f"Not eligible for the program: {f['elig']['reason']}.")
    status = 'blocked' if f['elig']['state'] == 'ineligible' else 'stay' if f['status'] in ('monitor', 'none') and val['net'] < 0 else 'ready'
    g = X.gap(hh, 'brokerage', 'tactical')
    fits = [x for x in P.fit_strategies(hh, g, X.attribution(hh, 'brokerage', '3Y'), f['elig']) if not x.get('blocked')][:3]
    plan = {'conc': f"a tax-aware plan to reduce {f['sym']}", 'risk': 'a plan to bring volatility back into the profile band', 'cash': 'a plan to invest the cash in steps toward the CIO allocation',
            'perf': 'a review of the funds trailing the CIO allocation'}.get(f['kind'], 'ongoing rebalancing to the CIO allocation')
    mgd = []
    conc = [k for k, w in sorted(E.names(hh['holdings']).items(), key=lambda x: -x[1]) if w > st.th]
    secs = list(dict.fromkeys(lc(DATA['sectors'].get(s, s)) for s in [(next((h for h in hh['holdings'] if h['sym'] == k), {}) or {}).get('sector') for k in conc] if s))
    muni = [h for h in hh['holdings'] if h.get('muni') and h.get('kind') != 'bond']; muni_mv = nsum(h['mv'] for h in muni)
    muni_loss = nsum(max(0, nsum((l.get('cost') or 0) for l in (h.get('lots') or [])) - h['mv']) for h in muni)
    trs = [x['sym'] for x in X.routing(hh) if x['route'] == 'transfer']
    if val['diOk']:
        mgd.append({'t': 'Direct indexing: losses harvested stock by stock', 'd': f"Owning the index companies directly lets the manager realize losses to offset gains elsewhere; a fund cannot pass its losses through. About {money(val['harvNet'])} a year after the {money(val['diFee'])} manager fee (planning estimate)."})
    mgd.append({'t': 'Custom exclusions and tilts', 'd': (f"Leave {' and '.join(conc)} out of the direct index" + (f" and tilt away from {' and '.join(secs)}" if secs else '') + ', so new money diversifies instead of adding to the concentration.')
                if conc else 'Leave out stocks or sectors the client chooses, for values or employer reasons; a fund must hold its whole index.'})
    if val['gains'] > 1000:
        mgd.append({'t': 'Tax-managed transition of existing stocks', 'd': f"A tax-managed SMA takes {', '.join(trs)} in as they are and sells them over time within the {money(hh['gain_budget'])} yearly gain budget, instead of a one-time sale."})
    if muni_mv > 0 and hh['rates'].get('bracket', 0) >= 0.32:
        mgd.append({'t': 'Individual municipal bond ladder', 'd': f"Replace {', '.join(h['sym'] for h in muni)} ({money(muni_mv)}) with individual bonds laddered over 1 to 10 years: known maturities and tax-exempt income"
                    + (f", and the {money(muni_loss)} loss in the fund can be harvested in the switch" if muni_loss > 1000 else '') + '.'})
    mgd.append({'t': 'Tax-aware rebalancing across accounts', 'd': "Rebalancing to the CIO allocation uses losses first, stays within the gain budget, and checks wash sales across the household's accounts."})
    return {'f': f, 'val': val, 'prog': prog, 'stay': stay, 'inc': inc, 'dNet': prog['net'] - stay['net'], 'stayR': stay_r, 'status': status, 'fits': fits, 'plan': plan, 'mgd': mgd}


def o2_defaults(hh: dict) -> dict:
    return {'amount': D.round_k(P.amt(hh)), 'turnover': DATA['fees']['brokerage']['turnover'], 'sma': 0.5, 'auto': {}, 'obj': None, 'content': None, 'note': '', 'tp': None, 'ver': 1, 'rev': 'draft'}


def build_story(hh: dict, o: dict, c: dict, wn: list, cl: list, objs: list, lib: list, v: dict) -> str:
    idx = X.opt(c, 'index'); V = v['val']; L = [f"{hh['name']}: what an advisory relationship could add", '\nWHY WE ARE TALKING NOW']
    L += ['• ' + w['text'] for w in wn if o['auto'].get(w['key'])] + ['• ' + w['text'] for w in cl]
    if v['status'] == 'blocked':
        L += ['\nWHERE WE START', f"• The advisory program is not available at present ({v['f']['elig']['reason']}). It can be revisited once the position is below the limit.",
              f"• Staying in brokerage: about {money(v['stay']['total'])} a year in fund expenses and commissions. We start with a plan for the position."]
    else:
        L.append('\nWHAT THE PROGRAM COULD DO FOR YOU')
        L.append("• A fiduciary relationship: we monitor and rebalance the portfolio to our CIO's allocation for your profile" +
                 (f", which our illustrative assumptions put about {ppt(V['erPts'], 2).replace(' pts', ' points')} a year ahead of today's mix before costs" if V['er'] > 0 else '') + '.')
        if v['f']['kind'] not in ('drift', 'none'):
            L.append(f"• {v['plan'][0].upper() + v['plan'][1:]}.")
        L.append(f"• More choices: {len(DATA['strategies'])} strategies, including CIO models, separate account managers and direct indexing" + (f"; for you, {', '.join(x['name'] for x in v['fits'])}" if v['fits'] else '') + '.')
        L.append(f"• No commissions: trading is included (about {money(V['comm'])} a year today).")
        L.append('\nWHAT ONLY A MANAGED ACCOUNT CAN DO'); L += [f"• {m['t']}. {m['d']}" for m in v['mgd']]
        r = X.routing(hh); tr = [x for x in r if x['route'] == 'transfer']; ins = nsum(x['mv'] for x in r if x['route'] == 'instep')
        L.append('\nHOW THE MOVE WOULD WORK, TAX-EFFICIENTLY')
        if tr:
            L.append(f"• {', '.join(x['sym'] for x in tr)} would move as they are, without tax on the move, and be sold over time within your {money(hh['gain_budget'])} yearly gain budget (about {money(V['y1taxNet'])} of tax in year one after harvested losses, rather than about {money(V['taxAll'])} if repositioned at once).")
        if V['lossNow'] > 1000:
            L.append(f"• About {money(V['lossNow'])} of losses would be harvested in the move, worth about {money(V['lossTax'])} in tax.")
        if ins:
            L.append(f'• {money(ins)} of cash would be invested in six monthly steps.')
        L.append('\nWHAT IT COSTS')
        L.append(f"• About {money(v['prog']['total'])} a year in the program, with no commissions, against about {money(v['stay']['total'])} today: {'+' if V['inc'] >= 0 else '−'}{money(abs(V['inc']))} a year.")
        L.append(f"• The benefits we can estimate come to about {money(V['quant'])} a year" + (f", about {money(V['net'])} more than the added fee" if V['net'] >= 0 else
                 f", about {js_round((V['cover'] or 0) * 100)}% of the added fee; the rest is the value of ongoing advice and planning") + '. These are illustrative estimates, not promises.')
        L += ['\nYOUR OPTIONS', '• Advisory program with the CIO model, as above; with direct indexing or separate account managers where they fit.',
              f"• A lower-cost index-only option: about {money(idx['total'])} a year, with fewer services; advisor compensation differs between options.",
              '• Staying as you are in brokerage: you direct the portfolio, and recommendations are made in your best interest at the time they are made.']
    if v['stayR']:
        L.append('\nTHINGS TO WEIGH'); L += ['• ' + r for r in v['stayR']]
    ob = [x for x in objs if o['obj'].get(x['id'])]
    if ob:
        L.append('\nQUESTIONS YOU MAY HAVE'); L += [f"• {x['q']} {x['a']}" for x in ob]
    at = [x for x in lib if o['content'].get(x['id'])]
    if at:
        L.append('\nENCLOSED (APPROVED MATERIALS)'); L += [f"• {x['title']} ({x['kind']})" for x in at]
    if o.get('note'):
        L.append(f"\nADVISOR NOTE (NOT PRE-APPROVED)\n• {o['note']}")
    L.append('\nFigures are illustrative estimates and do not imply future results. Draft for advisor and compliance review.')
    return '\n'.join(L)


def proposal_view(hid: str, st: State, o_in: dict | None, clips: list) -> dict:
    hh = household(hid); o = {**o2_defaults(hh), **(o_in or {})}
    o['auto'] = dict(o.get('auto') or {})
    c = X.costs(hh, o['amount'] or 1, o['turnover'], o['sma'])
    st.o2[hid] = o
    v = value_case(hh, c, st); wn = why_now(hh, st); topics = topics_for(hh, st, clips)
    fits = lambda x: x.get('requires') != 'risk_down' or (v['f']['risk'] == 'above' and v['prog']['vol'] < v['stay']['vol'] - 0.0005)
    obj_all = [x for x in DATA['objections'] if any(t in topics for t in x['topics'])]
    objs = [x for x in obj_all if fits(x)]; obj_out = [x for x in obj_all if not fits(x)]
    if o.get('obj') is None:
        o['obj'] = {x['id']: True for x in objs[:3]}
    lib = [x for x in DATA['content'] if any(t in topics for t in x['topics'])]
    if o.get('content') is None:
        o['content'] = {x['id']: True for x in [x for x in lib if x['audience'] == 'client'][:3]}
    for i, w in enumerate(wn):
        if o['auto'].get(w['key']) is None:
            o['auto'][w['key']] = i < 3
    story = o['tp'] if o.get('tp') is not None else build_story(hh, o, c, wn, clips, objs, lib, v)
    V = v['val']; drivers = ' and '.join([s for s in ['the CIO allocation' if V['er'] > 0 else '', 'tax-loss harvesting' if V['diOk'] and V['harvNet'] > 0 else ''] if s])
    if v['status'] == 'blocked':
        finding = 'The advisory program is not available while one security is above 50% of the account'
    elif v['status'] == 'stay':
        finding = f"{hh['name']}'s allocation is in line, and the program's quantified benefits (about {money(V['quant'])} a year) are below its {money(V['inc'])} higher fee: staying in brokerage may suit, with the program still available"
    elif V['net'] >= 0:
        finding = f"An advisory relationship could add about {money(V['net'])} a year for {hh['name']} after its higher fee" + (f', through {drivers}' if drivers else '') + f", plus {v['plan']} (illustrative)"
    else:
        finding = (f"An advisory relationship would give {hh['name']} {v['plan']}" + (', tax-loss harvesting' if V['diOk'] else '') +
                   f" and access to {len(DATA['strategies'])} strategies; estimated benefits cover about {js_round((V['cover'] or 0) * 100)}% of the {money(V['inc'])} higher fee, with ongoing advice and planning making up the rest (illustrative)")
    trade = [['Expected return at the CIO allocation, before costs', f"{ppt(V['erPts'], 2)} ≈ {'+' if V['er'] >= 0 else '−'}{money(abs(V['er']))} a year", '' if V['er'] > 0 else 'warn'],
             ['Tax-loss harvesting with direct indexing (planning)', f"≈ {'+' if V['harvNet'] >= 0 else '−'}{money(abs(V['harvNet']))} a year after the {money(V['diFee'])} manager fee" if V['diOk'] else 'not available for this account', '']]
    if V['lossNow'] > 1000 and v['status'] != 'blocked':
        trade.append(['Losses harvested in the move (one-time, planning)', f"{money(V['lossNow'])} ≈ {money(V['lossTax'])} of tax value", ''])
    if V['gains'] > 1000 and v['status'] != 'blocked':
        trade.append(['Tax-efficient move (planning)', f"{money(V['gains'])} of gains move in kind; year-one tax ≈ {money(V['y1taxNet'])} after harvested losses ({money(V['y1tax'])} before), not {money(V['taxAll'])} at once", ''])
    if v['f']['share'] > st.th:
        trade.append(['Single-company concentration', f"{v['f']['sym']} {pct(v['f']['share'], 1)} today; reduced on a tax-aware schedule", ''])
    trade += [['Portfolio volatility', f"{pct(v['stay']['vol'], 1)} → {pct(v['prog']['vol'], 1)}", 'warn' if v['prog']['vol'] > v['stay']['vol'] + 0.0005 else 'good' if v['prog']['vol'] < v['stay']['vol'] - 0.0005 else ''],
              ['Higher fee (illustrative)', f"{'+' if V['inc'] >= 0 else '−'}{money(abs(V['inc']))} a year", 'warn' if V['inc'] > 0 else 'good'],
              ['Estimated net of the fee, per year', f"{'+' if V['net'] >= 0 else '−'}{money(abs(V['net']))} (illustrative)", 'good' if V['net'] >= 0 else 'warn']]
    sma = X.opt(c, 'sma'); idx = X.opt(c, 'index')
    svc = [['Standard of care', 'Best interest at the time of each recommendation', 'Fiduciary duty, ongoing', 'Fiduciary duty, ongoing', 'Fiduciary duty, ongoing'],
           ['Ongoing monitoring and rebalancing', 'No: client-directed', 'Yes', 'Yes', 'Yes'], ['Portfolio built to the CIO allocation', 'Client-directed', 'Yes', 'Yes, with SMA managers', 'Yes, index funds only'],
           ['Tax management', 'Ad hoc', 'Gain budget, loss harvesting', 'Custom, per manager', 'Limited'],
           ['Direct indexing, custom exclusions and tilts', 'Not available', 'Available as a sleeve', 'Available', 'Not available'],
           ['Tax-managed transition of existing stocks', 'Not available', 'Gain budget', 'Manager takes stocks in kind', 'Gain budget'],
           ['Individual municipal bond ladder', 'Buy bonds one by one', 'Available as a sleeve', 'Available', 'Not available'], ['Trading costs', 'Commission per trade', 'Included', 'Included', 'Included'],
           ['Annual cost for this client'] + [f"{money(x['total'])} ({js_round(x['bps'])} bp)" for x in (v['stay'], v['prog'], sma, idx)],
           ['Expected return · risk (illustrative)'] + [f"{pct(x['er'], 1)} · {pct(x['vol'], 1)}" for x in (v['stay'], v['prog'], sma, idx)],
           ['Advisor compensation', 'Commissions', 'Program fee', 'Program fee', 'Differs from the full program']]
    status = v['status']
    card = {'key': 'ws2:' + hid, 'title': f"{hh['name']} · Advisory discussion", 'status': status, 'finding': finding,
            'why': ('Nothing material came out of the allocation review. Present the program fairly and record the client\'s choice.' if status == 'stay' else
                    f"Not eligible for the program: {v['f']['elig']['reason']}. The value case resumes once the position is below the limit; staying in brokerage with a specialist plan comes first." if status == 'blocked' else
                    'Value figures are illustrative planning estimates: capital market assumptions, and harvestable losses of 2% a year on the direct-indexed equity. They are not promises of results.'),
            'evidence': ([w['text'] for w in wn if o['auto'].get(w['key'])] + ['', '', ''])[:3], 'elig': v['f']['elig'], 'trade': [] if status == 'blocked' else trade,
            'choices': ([['Stay in brokerage', 'recommended'], ['Specialist review', ''], ['Advisory program', 'blocked']] if status == 'blocked' else
                        [['Stay in brokerage', 'recommended'], ['Advisory: CIO model', 'suitability dependent'], ['Index-only', 'compensation differs']] if status == 'stay' else
                        [['Advisory: CIO model', 'suitability dependent'], ['With direct indexing and SMA managers', ''], ['Index-only', 'compensation differs'], ['Stay in brokerage', '']]),
            'next': ('Start with the concentrated position plan; revisit the program later.' if status == 'blocked' else
                     'Explain the comparison; record "stay in brokerage" if the client agrees.' if status == 'stay' else
                     'Prepare the value story: why now, what the client gains, how the move works, what it costs, and the alternatives.')}
    soon = lambda d: (date.fromisoformat(d) - date.fromisoformat(TODAY)).days < 90
    return {'hh': hh_brief(hh), 'o2': o, 'costs': c, 'card': card, 'strip': strip(card['key'], hid, st),
            'v': {k: v[k] for k in ('status', 'stayR', 'mgd', 'plan', 'inc', 'dNet')} | {'fits': [x['name'] for x in v['fits']], 'kind': v['f']['kind'],
                                                                                          'stay': v['stay'], 'prog': v['prog'], 'val': {k: V[k] for k in V if k not in ('prog', 'stay')}},
            'nStrategies': len(DATA['strategies']), 'svc': svc, 'whyNow': wn, 'clips': clips,
            'objs': [{**x, 'contentTitle': (next((cc for cc in DATA['content'] if cc['id'] == x['content']), {}) or {}).get('title', '')} for x in objs], 'objOut': obj_out,
            'lib': [{**x, 'soon': soon(x['expires'])} for x in lib], 'story': story, 'feeNotes': [DATA['fees']['program']['note'], DATA['fees']['brokerage']['note']]}


# ---------------------------------------------------------------- the six-step strip on summary cards
def strip(key: str, hid: str, st: State) -> dict | None:
    q = Q.all_queue(st)
    o = (next((x for x in q if x['key'] == key), None) or next((x for x in q if x['hh']['id'] == hid and x['grp'] != 'done' and x.get('flow') != 'na'), None)
         or next((x for x in q if x['hh']['id'] == hid), None))
    if not o:
        return None
    return {'key': o['key'], 'kind': P.KIND.get(o['uc'], ''), 'pathway': o.get('pathway') or '', 'steps': P.steps(o, st)}


# ---------------------------------------------------------------- allocation and performance
def allocation_view(hid: str, st: State, o1: dict) -> dict:
    hh = household(hid); o = {**{'scope': 'brokerage', 'basis': 'tactical', 'lvl': 'L1', 'period': '3Y'}, **(o1 or {})}
    f = D.ws1(hh, o, st); g = f['g']; a = f['a']
    route = X.routing(hh)
    strat = P.fit_strategies(hh, g, a, f['elig'])
    card = {k: f[k] for k in ('kind', 'status', 'finding', 'why', 'next', 'evidence', 'trade', 'choices', 'assumptions', 'baseline', 'elig')}
    card.update({'key': 'ws1:' + hid, 'title': f"{hh['name']} · Allocation review"})
    clip = [f['finding'], f"{f['why']} {f['next']}", {'key': 'ws1'}]
    return {'hh': hh_brief(hh), 'o1': o, 'card': card, 'strip': strip(card['key'], hid, st), 'tol': DATA['cio']['tolerance'],
            'gap': {k: g[k] for k in ('rows', 'groups', 'st', 'stT', 'out', 'outG', 'te', 'ct')}, 'attr': {k: a[k] for k in ('RB', 'RP', 'active', 'alloc', 'sel', 'inter', 'rows', 'det')},
            'strat': [{k: s[k] for k in ('name', 'desc', 'kind', 'min', 'fee_bps', 'why', 'score') } | {'blocked': bool(s.get('blocked'))} for s in strat],
            'routes': X.ROUTES, 'routing': [{k: r[k] for k in ('sym', 'name', 'mv', 'gain', 'route', 'why')} for r in route],
            'perfNote': DATA['perf']['note'], 'perfAsOf': DATA['perf']['as_of'], 'clip': clip}


# ---------------------------------------------------------------- concentrated position
def fund_of(k: str) -> str | None:
    f = next((f for f in DATA['funds'].values() if f['kind'] != 'stock' and (f['classes'].get(k) or 0) >= 0.9 and f.get('report') and f['report'].get('view') == 'Recommended'), None)
    return f['sym'] if f else None


def o3_defaults(key: str, st: State) -> dict:
    hid = key.split(':')[0]; hh = household(hid); fl = DATA['concentration']['positions'].get(key, {}); needs = (DATA['concentration']['cash_needs'].get(hid) or {})
    gift = 'gift' in (fl.get('intent') or [])
    return {'target': min(st.th, DATA['concentration']['threshold']), 'budget': hh['gain_budget'], 'gift': 250000 if gift else 0, 'years': 6, 'needs': dict(needs),
            'ans': {'gift': gift, 'cash': len(needs) > 0, 'keep': False}}


def position_view(pos: str | None, st: State, o3_all: dict | None, hid: str | None = None) -> dict:
    """o3_all: the advisor's plan settings by position key; only the resolved position's settings are used."""
    L = Q.conc_list(st)
    th_ctl = {'th': st.th, 'exclude_over': DATA['concentration']['exclude_over'], 'threshold': DATA['concentration']['threshold'], 'deck': DATA['concentration']['deck_threshold']}
    if not L:
        return {'empty': True, 'thCtl': th_ctl}
    p = next((x for x in L if x['key'] == pos), None) or (next((x for x in L if x['hh']['id'] == hid), None) if hid else None) or L[0]
    o3_in = (o3_all or {}).get(p['key'])  # settings belong to the position they were made for
    hh = p['hh']; o = {**o3_defaults(p['key'], st), **(o3_in or {})}; o['ans'] = {**o3_defaults(p['key'], st)['ans'], **((o3_in or {}).get('ans') or {})}
    f = p['flags']; sym = p['sym']
    hs = [h for h in hh['holdings'] if h['sym'] == sym]; lots = [dict(l) for h in hs for l in (h.get('lots') or [])]
    tot = nsum(h['mv'] for h in hh['holdings']); mv = nsum(h['mv'] for h in hs); no_basis = nsum(l['mv'] for l in lots if l.get('cost') is None)
    plan = X.sale_plan(hh, sym, {'target': o['target'], 'budget': o['budget'], 'gift': o['gift'] if o['ans']['gift'] else 0, 'years': o['years'], 'needs': o['needs'] if o['ans']['cash'] else {}})
    plan['target'] = o['target']
    dd = D.ws3(p, plan, hh); lim = dd['elig']['state'] == 'ineligible' and dd['elig']['sym'] == sym
    needs_txt = ', '.join(f'{y} {money(v)}' for y, v in o['needs'].items() if v > 0)
    steps = [{'q': 'Insider or restricted stock?', 'a': 'Yes: ' + (f.get('restricted') or 'trading rules apply') if f.get('insider') else 'No restrictions on file', 'yes': bool(f.get('insider')), 'out': 'Pre-clear trades; consider a pre-arranged sale plan'},
             {'q': 'Above the 50% program limit?', 'a': f"Yes: {pct(p['share'], 1)}" if lim else f"No: {pct(p['share'], 1)}", 'yes': lim, 'out': 'Specialist route first; program paths blocked'},
             {'q': 'Wants to give shares to family or charity?', 'a': 'Yes' if o['ans']['gift'] else 'No', 'yes': o['ans']['gift'], 'out': f"Gift lowest-basis lots first ({money(o['gift'])} a year)"},
             {'q': 'Needs cash from it in the next few years?', 'a': 'Yes: ' + needs_txt if o['ans']['cash'] else 'No', 'yes': o['ans']['cash'], 'out': 'Sell highest-basis lots to meet each year’s need'},
             {'q': 'Wants to keep the upside, or avoid selling?', 'a': 'Yes' if o['ans']['keep'] else 'No', 'yes': o['ans']['keep'], 'out': 'Collar or exchange fund (specialist referral)'}]
    result = ' → '.join(x for x in ['Pre-clearance' if f.get('insider') else None, 'specialist review' if lim else None, 'gift low-basis lots' if o['ans']['gift'] else None,
                                    'protect the rest with a collar' if o['ans']['keep'] else 'staged sale within the gain budget',
                                    'program once below 50%' if lim else 'reinvest through direct indexing with the stock excluded'] if x)
    gp = X.gap(hh, 'all', 'tactical'); gaps = [r for r in gp['rows'] if r['g'] < 0 and r['k'] != 'CASH' and fund_of(r['k'])]; gsum = nsum(-r['g'] for r in gaps) or 1

    def sim(amt):
        lines = ([{'action': 'sell', 'sym': sym, 'amount': amt}] + [{'action': 'buy', 'sym': fund_of(r['k']), 'amount': amt * (-r['g']) / gsum} for r in gaps]) if amt > 1000 else []
        return E.metrics(hh, E.apply(hh, lines)['hs'])
    full = min(max(0, p['share'] - o['target']) * tot, mv - no_basis); y1 = plan['years'][0]['sold']
    m0 = E.metrics(hh, hh['holdings']); mF = sim(full); mY = sim(y1); spF = E.sell_plan(hh, hh['holdings'], sym, full)
    sols = []
    for s in DATA['concentration']['solutions']:
        fit, why = 0.3, ''
        if s['id'] == 'staged':
            fit = 0.6; why = (f"Reaches the target by {plan['reach']}" if plan['reach'] else f"Does not reach the target in {o['years']} years") + f" within {money(o['budget'])} of gains a year."
        if s['id'] == 'tm-sma':
            fit = 0.1 if lim else 0.75 if mv >= 250000 else 0.2
            why = 'Blocked while above the program limit.' if lim else 'Large enough for the SMA minimum; shares move in kind.' if mv >= 250000 else 'Below the SMA minimum.'
        if s['id'] == 'di':
            eq = next(x for x in gp['groups'] if x['k'] == 'equity')['w'] * gp['ct']
            fit = 0.1 if lim else 0.7 if eq >= 250000 else 0.2
            why = 'Blocked while above the program limit.' if lim else f"Harvested losses, about {money(0.02 * min(eq, tot * 0.4))} a year (illustrative), can offset gains from trimming."
        if s['id'] == 'gift':
            lowb = nsum(l['mv'] for l in lots if l.get('cost') is not None and l['cost'] / l['mv'] < 0.3)
            fit = 0.9 if o['ans']['gift'] else 0.45 if lowb else 0.1
            why = f'{money(lowb)} sits in lots with basis under 30% of value.' if lowb else 'No low-basis lots.'
        if s['id'] == 'hedge':
            fit = 0.85 if lim else 0.85 if o['ans']['keep'] else 0.45 if f.get('insider') else 0.25
            why = ('Lets the client reduce risk without selling while above the limit.' if lim else 'Client wants to keep the upside.' if o['ans']['keep'] else
                   'Useful while trading windows limit sales.' if f.get('insider') else 'Consider if the client resists selling.')
        al, at = dd['act'][s['id']]
        horizon = ((f"{plan['reach'] - 2025} yr" if plan['reach'] else f"> {o['years']} yr") if s['id'] == 'staged' else 'weeks' if s['id'] == 'hedge' else 'per gift' if s['id'] == 'gift' else '1–3 yr')
        sols.append({**s, 'fit': fit, 'why': why, 'al': al, 'at': at, 'horizon': horizon})
    sols.sort(key=lambda s: -s['fit'])
    first = next((s for s in sols if s['at'] != 'bad'), None)
    choices = [[s['name'].replace(' (specialist referral)', ''), 'blocked' if s['at'] == 'bad' else 'recommended' if s is first else s['al']] for s in sols[:4]]
    y0 = plan['years'][0]
    card = {'key': 'ws3:' + p['key'], 'title': f"{hh['name']} · {sym} position", 'status': dd['status'], 'finding': dd['finding'], 'why': dd['why'], 'gates': dd['gates'],
            'evidence': dd['evidence'], 'elig': dd['elig'], 'assumptions': 'Planning scenario: prices held constant; lot order, gain budget, gifts, cash needs and trading rules applied',
            'trade': [['Single-company concentration (planning)', f"{pct(p['share'], 1)} → {pct(y0['share'], 1)} in year one; {pct(o['target'], 1)} target", ''],
                      ['Estimated tax, year one (planning)', money(y0['tax']), 'warn' if y0['tax'] else ''],
                      ['Portfolio volatility', f"{pct(m0['vol'], 1)} → {pct(mY['vol'], 1)} after year one", 'good' if mY['vol'] < m0['vol'] - 0.0005 else 'warn' if mY['vol'] > m0['vol'] + 0.0005 else ''],
                      ['Horizon', f"target by {plan['reach']}" if plan['reach'] else f"beyond {2025 + o['years']}", '']],
            'choices': choices, 'next': dd['next']}
    clip = [f'{sym} position plan', f"Bring {sym} from {pct(p['share'], 1)} toward {pct(o['target'], 1)} of the account" + (f" by {plan['reach']}" if plan['reach'] else '') +
            f": sell about {money(plan['years'][0]['sold'])} in 2026 (tax {money(plan['years'][0]['tax'])})" + (f", give {money(o['gift'])} a year of the lowest-basis shares" if o['ans']['gift'] else '') + ', within the yearly gain budget.',
            {'key': 'ws3:' + sym}]
    worst = m0['worst']
    return {'pos': p['key'], 'hid': hh['id'], 'hh': hh_brief(hh), 'sym': sym, 'share': p['share'], 'o3': o, 'plan': plan, 'card': card, 'strip': strip(card['key'], hh['id'], st), 'tree': {'steps': steps, 'result': result},
            'risk': {'m0': {'vol': m0['vol'], 'stress': m0['stress'][worst], 'share': p['share']}, 'mY': {'vol': mY['vol'], 'stress': mY['stress'][worst], 'share': plan['years'][0]['share']},
                     'mF': {'vol': mF['vol'], 'stress': mF['stress'][worst], 'share': mF['names'].get(sym, 0)}, 'worst': next(s['label'] for s in DATA['scenarios'] if s['id'] == worst),
                     'y1': y1, 'y1tax': plan['years'][0]['tax'], 'full': full, 'fullTax': spF['tax']},
            'lots': sorted(lots, key=lambda l: (l.get('cost') is None, (l['cost'] / l['mv']) if l.get('cost') is not None else 0)), 'rates': hh['rates'], 'noBasis': no_basis,
            'sols': sols, 'thCtl': th_ctl, 'taxNote': DATA['disclosures']['tax'], 'clip': clip}


# ---------------------------------------------------------------- market and research
def for_you(ev: dict, r: dict) -> str:
    if r['kind'] == 'market':
        return (f"Under this illustrative scenario, your holdings would be affected by an estimated {money(r['usd'])} ({spct(r['pctAcct'], 2)} of the account), mostly through "
                f"{' and '.join(x['h']['sym'] for x in r['rows'][:2])}. This is a model estimate, not your actual result.")
    if r['kind'] == 'view':
        ag = [x for x in r['rows'] if x['against']]
        return f"Your portfolio leans against the new view: {', '.join(lc(short(x['k'])) + ' ' + ppt(x['g'], 1) for x in ag)}." if ag else 'Your portfolio is already in line with the new view.'
    if r['kind'] == 'research':
        if r.get('me'):
            return f"You hold {money(r['me']['mv'])} ({pct(r['me']['share'], 1)}). " + ('A manager runs this holding, so the next step is asking the manager for its view.' if re.search('Manager', r['me']['decides'])
                                                                                   else 'We can review similar companies with a higher rating.')
        return f"You hold it only through funds ({pct(r['pctAcct'], 2)} of the account)."
    return 'This is your own question; the concentrated position plan answers it.'


def why_client(r: dict) -> str:
    if r['kind'] == 'market':
        return '; '.join(f"{x['h']['sym']} ({', '.join(x['via'])})" for x in r['rows'][:3]) or 'no holdings move'
    if r['kind'] == 'view':
        return '; '.join(f"{short(x['k'])} {ppt(x['g'], 1)} vs target" for x in r['rows'] if x['against']) or 'already in line'
    if r['kind'] == 'research':
        return 'held directly' if r['direct'] else 'held only inside funds'
    return 'the client asked'


def _rows_pub(r: dict) -> list[dict]:
    if r['kind'] == 'view':
        return r['rows']
    return [{'sym': x['h']['sym'], 'name': x['h']['name'], 'mv': x['h']['mv'], 'via': x['via'], 'r': x['r'], 'usd': x['usd']} for x in r['rows']]


def event_view(ev_id: str, st: State, sel_hid: str | None) -> dict:
    ev = next((n for n in DATA['news'] if n['id'] == ev_id), DATA['news'][0])
    all_ = []
    for hh in HHS():
        r = X.event_for_hh(ev, hh)
        if r['score'] > 1:
            all_.append({'hh': hh, **r, 'm': D.ws4(ev, {'hh': hh, **r}, st)})
    ranked = sorted([x for x in all_ if x['m']['material']], key=lambda x: -x['score']); rest = sorted([x for x in all_ if not x['m']['material']], key=lambda x: -x['score'])
    if not sel_hid or not any(x['hh']['id'] == sel_hid for x in all_):
        sel_hid = (ranked or rest)[0]['hh']['id'] if (ranked or rest) else None
    sel = next((x for x in all_ if x['hh']['id'] == sel_hid), None)
    view = next((v for v in DATA['cio']['views'] if v['key'] == ev.get('cio')), None)
    dg = next((d for d in DATA['downgrades'] if d['sym'] == ev.get('research')), None) if ev.get('research') else None
    book = [h['name'].split(' ')[0] for h in (dg['holders'] if dg else []) if h['household_id'] not in DATA['households']]
    type_l = {'market': 'Market news (third party)', 'cio': 'Firm CIO view', 'research': 'Firm research', 'client': 'Client question'}[ev['type']]
    row = lambda x: {'hid': x['hh']['id'], 'name': x['hh']['name'], 'size': x['m']['size'], 'status': x['m']['status']}
    card = None; detail = None; clip = None
    if sel:
        acts = [sel['m']['action']] + [x for x in ['Contact the client', 'Reassess the allocation', 'Request a manager review', 'Monitor', 'No action'] if x != sel['m']['action']]
        card = {'key': 'ws4:' + ev['id'] + ':' + sel['hh']['id'], 'title': f"{sel['hh']['name']} · Event review", 'status': sel['m']['status'],
                'finding': f"{sel['m']['action']} for {sel['hh']['name']}: {sel['m']['size']}", 'why': for_you(ev, sel),
                'evidence': [f"What changed: {type_l}, {ev['date']}", f"Why this client: {why_client(sel)}", f"Confidence: {sel['m']['conf']}"],
                'choices': [[x, 'recommended' if x == sel['m']['action'] else ''] for x in acts], 'next': ev['todo'], 'elig': D.elig(sel['hh'])}
        detail = {'kind': sel['kind'], 'rows': _rows_pub(sel), 'tot': nsum(h['mv'] for h in sel['hh']['holdings'])}
        clip = [ev['headline'], f"{for_you(ev, sel)} {ev['house']}", {'key': 'ws4:' + ev['id']}]
    return {'ev': ev, 'typeL': type_l, 'ranked': [row(x) for x in ranked], 'rest': [row(x) for x in rest], 'sel': sel['hh']['id'] if sel else None,
            'selMaterial': bool(sel and sel['m']['material']), 'card': card, 'strip': strip(card['key'], sel['hh']['id'], st) if card else None, 'detail': detail,
            'view': view, 'dg': dg and {'sym': dg['sym'], 'change': dg['change'], 'buy': [x['sym'] for x in dg['alternatives'] if x.get('rating') == 'Buy']},
            'book': book, 'researchNote': DATA['disclosures']['research'], 'clip': clip, 'hh': hh_brief(sel['hh']) if sel else None}


def firm_view(st: State, o4: dict, hid: str) -> dict:
    hh = household(hid); q = (o4.get('q') or '').strip().lower(); watch = set(o4.get('watch') or []); ft = o4.get('ft') or 'all'; fb = o4.get('fb') or 'all'; sel = o4.get('sel')
    C = D.catalog(); cards = []
    for it in C:
        b = D.book_status(it, st)
        if not (ft == 'all' or it['type'] == ft):
            continue
        if not (fb == 'all' or (it['id'] in watch if fb == 'watch' else b['k'] == fb)):
            continue
        if q and q not in ' '.join([it['headline'], it.get('abstract') or '', it.get('stance') or '', ' '.join(it.get('tags') or []), it.get('sym') or '']).lower():
            continue
        run = (sel == it['id']) if it.get('auto') else (bool(st.intel_run.get(it['id'])) and sel == it['id'])
        res = []
        if run:
            order = ['matched', 'unknown', 'monitor', 'none']
            rr = [(h, D.intel_for(it, h, st)) for h in HHS()]
            rr.sort(key=lambda x: order.index(x[1]['state']) if x[1]['state'] in order else -1)
            for h, r in rr:
                e = D.elig(h)
                res.append({'hid': h['id'], 'name': h['name'], 'r': r, 'elig': D.ELIG[e['state']], 'promoted': (it['id'] + ':' + h['id']) in st.promo})
        cards.append({**{k: v for k, v in it.items() if k != 'ev'}, 'book': b, 'run': run, 'res': res, 'everRun': bool(it.get('auto') or st.intel_run.get(it['id']))})
    return {'cards': cards, 'n': len(C), 'as_of': DATA['intel_as_of'], 'first': hh['name'].split(' ')[0], 'positions': DATA['as_of']['positions'], 'hh': hh_brief(hh)}


# ---------------------------------------------------------------- task panel
def decision(route: dict, st: State) -> dict:
    ws = route.get('ws'); hid = route.get('hid'); hh = household(hid)
    if ws == 'path':
        H = P.hstate(hh, st)
        return {'key': 'hh:' + hid, 'status': (H['d'] or {}).get('status') or ('specialist' if D.elig(hh)['state'] == 'ineligible' else 'review')}
    if ws == 'queue':
        return {'key': None}
    if ws == 'ws1':
        return {'key': 'ws1:' + hid, 'status': D.ws1(hh, {**{'scope': 'brokerage', 'basis': 'tactical', 'period': '3Y'}, **(route.get('o1') or {})}, st)['status']}
    if ws == 'ws2':
        o = {**o2_defaults(hh), **((route.get('o2') or {}).get(hid) or {})}; c = X.costs(hh, o['amount'] or 1, o['turnover'], o['sma'])
        return {'key': 'ws2:' + hid, 'status': value_case(hh, c, st)['status']}
    if ws == 'ws3':
        L = Q.conc_list(st); p = next((x for x in L if x['key'] == route.get('pos')), None)
        if not p:
            return {'key': None}
        o = {**o3_defaults(p['key'], st), **((route.get('o3') or {}).get(p['key']) or {})}
        o['ans'] = {**o3_defaults(p['key'], st)['ans'], **(o.get('ans') or {})}
        pl = X.sale_plan(p['hh'], p['sym'], {'target': o['target'], 'budget': o['budget'], 'gift': o['gift'] if o['ans']['gift'] else 0, 'years': o['years'], 'needs': o['needs'] if o['ans']['cash'] else {}})
        pl['target'] = o['target']
        return {'key': 'ws3:' + p['key'], 'status': D.ws3(p, pl, p['hh'])['status']}
    if ws == 'ws4':
        o4 = route.get('o4') or {}
        if o4.get('view') == 'firm':
            k = o4.get('sel') and o4['sel'] + ':' + hid
            if k and k in st.promo:
                return {'key': 'ws4f:' + k, 'status': 'review'}
            return {'key': None}
        ev = next((n for n in DATA['news'] if n['id'] == route.get('ev')), DATA['news'][0]); r = X.event_for_hh(ev, hh)
        if r['score'] <= 1:
            return {'key': 'ws4:' + ev['id'] + ':' + hid, 'status': 'none'}
        return {'key': 'ws4:' + ev['id'] + ':' + hid, 'status': D.ws4(ev, {'hh': hh, **r}, st)['status']}
    return {'key': None}


def side(route: dict, st: State, clips_n: int) -> dict:
    hid = route['hid']; hh = household(hid); d = decision(route, st); H = P.hstate(hh, st); blk = P.blocker(hh); A = P.amounts(hh); e = D.elig(hh)
    stg = P.stages(hh, 'hh:' + hid, st, {'product': True}); cur = next((i for i, x in enumerate(stg) if x['state'] != 'ready'), -1)
    ps = P.paths(hh, st); path = next((p for p in ps if (p['id'] == H['path'] if H['path'] else p.get('suggested'))), None)
    prim = P.primary([o for o in Q.all_queue(st) if o['hh']['id'] == hid and o['grp'] != 'done'])
    why = P.why_of(prim, st) if prim else ''
    if e['state'] == 'ineligible':
        story = f"{why}. The advisory program is not available while the position is above 50%; the first step is a specialist plan."
    else:
        rn = P.PSHORT[path['id']][0].lower() + P.PSHORT[path['id']][1:] if path else 'transition'
        story = (f"{why or 'Your portfolio was reviewed'}. A {rn} would move about {money(A['now'])} into an advisory relationship with ongoing advice and tax management, at about "
                 f"{path['cost'].split(',')[0].split(' vs')[0] if path else ''}. Staying as you are remains an option.")
    blockers = [blk] + [x for x in (stg[2]['items'] or []) if x['t'] != blk['t']] + stg[4]['items']
    disp = st.disp.get(d['key']) if d.get('key') else None
    return {'hh': hh_brief(hh), 'decision': d, 'H': {'next': H['next'], 'step': H['step']}, 'blk': blk, 'elig': D.ELIG[e['state']], 'ex': e['state'] == 'ineligible',
            'stages': stg, 'cur': cur, 'story': story, 'clips': clips_n, 'blockers': blockers, 'disp': disp, 'life': D.life(disp)}


def top(st: State) -> dict:
    return {'open': nsum(1 for o in Q.all_queue(st) if o['grp'] != 'done')}


def view(req: dict) -> dict:
    """One call per paint: the top bar, the left list, the main stage and the task panel for the current route."""
    route = req.get('route') or {}; st = State.from_dict(req.get('state')); ws = route.get('ws') or 'queue'; hid = route.get('hid') or 'henderson'
    clips_all = (req.get('state') or {}).get('clips_list') or {}; clips = clips_all.get(hid) or []
    route = {**route, 'ws': ws, 'hid': hid}
    o4 = {**(route.get('o4') or {}), 'watch': (req.get('state') or {}).get('watch') or []}
    for k, v in (route.get('o2') or {}).items():
        st.o2.setdefault(k, {}).update(v)
    stage: dict = {'ws': ws}
    if ws == 'queue':
        stage['landing'] = landing(st) if route.get('qv', 'hh') == 'hh' else None
        stage['workflow'] = workflow(st) if route.get('qv') == 'opp' else None
    elif ws == 'path':
        step = route.get('hstep') or 'assess'
        stage['step'] = step
        stage['data'] = paths_view(hid, st) if step == 'paths' else handoff_view(hid, st) if step == 'handoff' else household_view(hid, st)
        stage['hstate'] = {k: v for k, v in P.hstate(household(hid), st).items() if k in ('step', 'next', 'path')}
    elif ws == 'ws1':
        stage['data'] = allocation_view(hid, st, route.get('o1'))
    elif ws == 'ws2':
        stage['data'] = proposal_view(hid, st, (route.get('o2') or {}).get(hid), clips)
        stage['hstate'] = {k: v for k, v in P.hstate(household(hid), st).items() if k in ('step', 'next', 'path')}
    elif ws == 'ws3':
        pos = route.get('pos'); o3 = (route.get('o3') or {})
        stage['data'] = position_view(pos, st, o3, hid)
        if not stage['data'].get('empty'):
            route['pos'] = stage['data']['pos']; route['hid'] = stage['data']['hid']; hid = route['hid']
            stage['data']['o3'] = stage['data']['o3']
    elif ws == 'ws4':
        if o4.get('view') == 'firm':
            stage['data'] = firm_view(st, o4, hid); stage['firm'] = True
        else:
            stage['data'] = event_view(route.get('ev') or 'n1', st, route.get('o4hh')); stage['firm'] = False
            if stage['data']['sel']:
                route['hid'] = stage['data']['sel']; hid = route['hid']
    return {'route': route, 'top': top(st), 'entries': entries(st, ws, route.get('qv', 'hh'), o4), 'stage': stage,
            'side': side(route, st, len(clips_all.get(hid) or []))}
