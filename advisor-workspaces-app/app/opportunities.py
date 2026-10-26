"""The shared opportunity list across the book (baseline settings; duplicates merged; grouped by lifecycle)."""
from __future__ import annotations
import re
from .data import DATA, HHS, State, household
from . import engine as E
from . import calc as X
from . import rules as D
from . import pathway as P
from .fmt import nsum


def conc_list(st: State) -> list[dict]:
    """Positions held directly whose look-through share is above the alert threshold."""
    out = []
    for hh in HHS():
        for s, v in E.names(hh['holdings']).items():
            if v > st.th and any(h['sym'] == s for h in hh['holdings']):
                out.append({'key': hh['id'] + ':' + s, 'hh': hh, 'sym': s, 'share': v, 'direct': nsum(h['mv'] for h in hh['holdings'] if h['sym'] == s),
                            'excl': v > DATA['concentration']['exclude_over'], 'flags': DATA['concentration']['positions'].get(hh['id'] + ':' + s, {})})
    return sorted(out, key=lambda p: -p['share'])


def _sort(out: list[dict]) -> list[dict]:
    return sorted(out, key=lambda o: ((o['grp'] == 'done'), -o['pri']))


def queue(st: State) -> list[dict]:
    out = []
    conc_all = conc_list(st)
    src_l = {'market': 'market news', 'cio': 'CIO view', 'research': 'firm research', 'client': 'client'}
    for hh in HHS():
        f = D.ws1(hh, D.BASE, st); e = f['elig']; conc = [p for p in conc_all if p['hh']['id'] == hh['id']]
        if f['status'] != 'none' and not (f['kind'] in ('conc', 'gate') and any(p['sym'] == f['sym'] for p in conc)):
            out.append({'key': 'ws1:' + hh['id'], 'hh': hh, 'ws': 'ws1',
                        'type': {'risk': 'Volatility above the profile band', 'cash': 'Volatility below profile: large cash', 'perf': 'Trailing the CIO allocation',
                                 'drift': 'Drift from the CIO allocation', 'gate': 'Not eligible for the program', 'conc': 'Single-company concentration'}[f['kind']],
                        'impact': f['evidence'][0],
                        'act': ['Not eligible; specialist route', 'bad'] if f['kind'] == 'gate' else ['No action needed now', 'info'] if f['kind'] == 'drift' else [D.ELIG[e['state']][2], D.ELIG[e['state']][1]],
                        'next': f['next'], 'status': f['status'], 'pri': {'review': 3, 'specialist': 3, 'ready': 2, 'monitor': 1}.get(f['status'], 0), 'rel': []})
        for p in conc:
            over = e['state'] == 'ineligible' and e['sym'] == p['sym']
            out.append({'key': 'ws3:' + p['key'], 'hh': hh, 'ws': 'ws3', 'pos': p['key'], 'type': f"{p['sym']} concentration",
                        'impact': f"{_pct1(p['share'])} of the account, direct and look-through",
                        'act': ['Not eligible; specialist route', 'bad'] if over else ['Conditions: insider rules', 'warn'] if p['flags'].get('insider') else ['Conditions: lots and tax', 'warn'],
                        'next': 'Refer to the concentrated stock specialist' if over else 'Review staging and alternatives',
                        'status': 'specialist' if over else 'review' if p['flags'].get('insider') else 'ready', 'pri': 2.5 + p['share'] * 3,
                        'rel': ['Also flagged in the allocation review'] if f['kind'] in ('conc', 'gate') and f['sym'] == p['sym'] else []})
        for ev in DATA['news']:
            r = X.event_for_hh(ev, hh)
            if r['score'] <= 1:
                continue
            m = D.ws4(ev, {'hh': hh, **r}, st)
            if not m['material']:
                continue
            hit = sorted(r['rows'], key=lambda x: -abs(x['usd']))[0] if r['kind'] == 'market' else None
            dup = None
            if hit:
                dup = next((o for o in out if o['ws'] == 'ws3' and o['hh'] is hh and o['pos'].endswith(':' + hit['h']['sym'])), None)
            if not dup and r['kind'] == 'view':
                dup = next((o for o in out if o['ws'] == 'ws1' and o['hh'] is hh), None) or next((o for o in out if o['ws'] == 'ws3' and o['hh'] is hh), None)
            src = src_l[ev['type']]
            if dup:
                size = m['size'].replace(' of the account', '', 1).replace(', estimated scenario impact', ', estimated', 1).replace(' against the new view', ' vs view', 1)
                dup['rel'].append(f"{ev['date']} · {src}: {ev['headline']} ({size})")
                continue
            out.append({'key': 'ws4:' + ev['id'] + ':' + hh['id'], 'hh': hh, 'ws': 'ws4', 'ev': ev['id'], 'type': ev['headline'],
                        'impact': m['size'].replace(', estimated scenario impact', ' (estimated)', 1),
                        'act': ['Manager decides', 'info'] if m['status'] == 'review' and r.get('me') and re.search('Manager', r['me']['decides']) else ['Advisor can act', 'good'],
                        'next': m['action'], 'status': m['status'], 'pri': 3.2 if m['status'] == 'respond' else 2.2 if m['status'] == 'review' else 1.5, 'rel': [f"{ev['date']} · {src}"]})
        for x in P.screens(hh):
            if not (x['uc'] == 4 and f['kind'] == 'cash'):
                out.append(x)
        c = D.costs_default(hh)
        if c and f['status'] in ('review', 'ready') and e['state'] != 'ineligible' and f['g']['ct'] >= 250000:
            vq = D.value(hh, D.default_costs(hh))
            out.append({'key': 'ws2:' + hh['id'], 'hh': hh, 'ws': 'ws2', 'type': 'Advisory program discussion',
                        'impact': f"est. value {_m(vq['quant'])} vs fee {'+' if vq['inc'] >= 0 else '−'}{_m(abs(vq['inc']))} a year (illustrative)",
                        'act': [D.ELIG[e['state']][2], D.ELIG[e['state']][1]], 'next': 'Prepare the value story', 'status': 'ready', 'pri': 1.2, 'rel': []})
    for o in out:
        P.enrich(o, st)
        d = st.disp.get(o['key'])
        if d:
            o['disp'] = d
        o['grp'] = D.group(o)
    return _sort(out)


def _m(x):
    from .fmt import money, nsum
    return money(x)


def _pct1(x):
    from .fmt import pct
    return pct(x, 1)


TL = {'ws1': 'Allocation review', 'ws2': 'Advisory program discussion', 'ws3': 'Concentrated position', 'ws4': 'Event review'}


def all_queue(st: State) -> list[dict]:
    """The ranked list plus anything the advisor assessed outside it, and promoted intelligence items, so no decision disappears."""
    def build():
        q0 = queue(st); have = {o['key'] for o in q0}
        extra = []
        for k, d in st.disp.items():
            if k in have:
                continue
            p = k.split(':'); ws = p[0]
            if ws not in TL:
                continue
            hid = p[2] if ws == 'ws4' else p[1] if len(p) > 1 else None
            hh = DATA['households'].get(hid)
            if not hh:
                continue
            ev = next((n for n in DATA['news'] if n['id'] == p[1]), None) if ws == 'ws4' else None
            o = {'key': k, 'hh': hh, 'ws': ws, 'pos': p[1] + ':' + p[2] if ws == 'ws3' and len(p) > 2 else None, 'ev': ev['id'] if ev else None,
                 'type': ev['headline'] if ev else TL[ws] + (' · ' + p[2] if ws == 'ws3' and len(p) > 2 else ''), 'impact': 'raised by the advisor',
                 'next': 'Follow up on the advisor assessment', 'act': ['Advisor raised', 'info'], 'status': d.get('status') or 'review', 'disp': d, 'pri': 2, 'rel': []}
            o['grp'] = D.group(o); extra.append(o)
        promo = []
        cat = {c['id']: c for c in D.catalog()}
        for k, x in st.promo.items():
            it = cat.get(x.get('id')); hh = DATA['households'].get(x.get('hid'))
            if not it or not hh:
                continue
            r = D.intel_for(it, hh, st); e = D.elig(hh); key = 'ws4f:' + k
            o = {'key': key, 'hh': hh, 'ws': 'ws4', 'intel': it['id'], 'type': it['headline'], 'impact': r['size'], 'next': r.get('action') or 'Review with the client',
                 'act': [D.ELIG[e['state']][2], D.ELIG[e['state']][1]], 'status': 'review', 'disp': st.disp.get(key), 'pri': 2, 'rel': [f"{it['date']} · added from Firm intelligence"]}
            o['grp'] = D.group(o); promo.append(o)
        q = _sort(q0 + promo + extra)
        for o in q:
            P.enrich(o, st)
        return q
    return st.memo('all_queue', build)


def public(o: dict, st: State, with_steps: bool = False) -> dict:
    """A row as the API returns it: the household by id, with its kind, why-now and (optionally) six steps."""
    x = {k: v for k, v in o.items() if k != 'hh'}
    x['hid'] = o['hh']['id']; x['hname'] = o['hh']['name']; x['kind'] = P.KIND.get(o.get('uc'), '')
    x['why'] = P.why_of(o, st)
    if with_steps:
        x['steps'] = P.steps(o, st)
    return x
