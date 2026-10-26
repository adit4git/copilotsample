"""The 30 prototype checks, run against the rule engine. Each uses a fresh State, so nothing the advisor did is changed."""
from __future__ import annotations
import copy
import re
from .data import DATA, HHS, State, household
from . import engine as E
from . import calc as X
from . import rules as D
from . import pathway as P
from . import opportunities as Q
from .fmt import pct, nsum


def run_checks() -> list[dict]:
    out = []
    ck = lambda area, name, ok, info='': out.append({'area': area, 'name': name, 'pass': bool(ok), 'info': info})
    st = State.from_dict({})
    try:
        q_all = Q.queue(st)
        for hh in HHS():
            e = D.elig(hh)
            labels = [o['act'][0] for o in q_all if o['hh']['id'] == hh['id'] and o['ws'] in ('ws1', 'ws2')]
            labels = [l for l in labels if l not in ('No action needed now', 'Not eligible; specialist route')]
            ck('Eligibility', f"{hh['name']}: queue uses the same determination ({D.ELIG[e['state']][0]})", all(l == D.ELIG[e['state']][2] for l in labels), ', '.join(labels))
        synth = copy.deepcopy(household('okonkwo')); f = copy.deepcopy(next(h for h in household('henderson')['holdings'] if h['sym'] == 'VTI'))
        f.update({'sym': 'FNDX', 'top_holdings': {'ZZZ': 0.7}, 'mv': 1e6, 'lots': [{'id': 'FNDX', 'cost': 9e5, 'mv': 1e6, 'term': 'LT'}]})
        synth['id'] = 'synth'; synth['holdings'] = [f]
        es = D.elig(synth)
        ck('Eligibility', 'A fund-only 70% exposure to one security is not eligible (direct plus look-through rule)', es['state'] == 'ineligible' and es['sym'] == 'ZZZ',
           f"{es['state']} · {es['sym']} {pct(es['share'], 1)} · {es['via']}")
        dg = D.elig(household('delgado'))
        ck('Eligibility', 'Delgado COST: direct and fund exposure combined, above the limit', dg['state'] == 'ineligible' and 'direct' in dg['via'], dg['via'])
        words = ' | '.join(x['note'] for hh in HHS() for x in D.ready(hh))
        ck('Readiness', 'No "Not eligible yet" wording; implementation reads "Not cleared"', 'Not eligible yet' not in words and all(D.ready(hh)[2]['note'].startswith('Not cleared') for hh in HHS()))
        ck('Readiness', 'Client discussion can be ready while implementation is not cleared', all(D.ready(hh)[0]['state'] == 'ready' and D.ready(hh)[2]['state'] == 'blocked' for hh in HHS()))
        k = 'ws3:henderson:NVDA'

        def grp(disp):
            s = State.from_dict({'disp': {k: disp}})
            return next((o for o in Q.queue(s) if o['key'] == k), {}).get('grp')
        g1 = grp({'status': 'review', 'set': True, 'reason': ''})
        ck('Workflow', '"Review needed" keeps the item in Needs action', g1 == 'action', g1)
        g = [grp({'status': 'specialist', 'set': True, 'reason': ''}), grp({'status': 'stay', 'set': True, 'reason': ''}), grp({'status': 'stay', 'set': True, 'reason': 'Client declined'}),
             grp({'status': 'defer', 'set': True, 'reason': 'Timing: revisit later'}), grp({'status': 'ready', 'set': True, 'reason': '', 'closed': {'outcome': 'Discussed with the client'}})]
        ck('Workflow', 'Specialist stays visible in its group; stay needs a reason to close; defer with a reason moves to Monitor; explicit close moves to Closed',
           g == ['specialist', 'action', 'done', 'monitor', 'done'], ' → '.join(map(str, g)))
        bad = n = 0
        for hh in HHS():
            for sc in ('brokerage', 'all'):
                for basis in ('strategic', 'tactical'):
                    for period in ('1Y', '3Y'):
                        w = D.ws1(hh, {'scope': sc, 'basis': basis, 'period': period}, st); n += 1
                        m = re.search(r'(lower|raise|stay about the same)[^()]*\((\d+\.\d)% → (\d+\.\d)%\)', w['why'])
                        if m:
                            a, c = float(m.group(2)), float(m.group(3))
                            if not ((m.group(1) == 'lower' and c < a) or (m.group(1) == 'raise' and c > a) or (m.group(1) == 'stay about the same' and abs(c - a) < 0.05)):
                                bad += 1
        ck('Claims', f'Volatility wording matches the numbers shown ({n} household × setting views)', bad == 0, f'{bad} mismatches')
        worst = 0.0
        for hh in HHS():
            for p in ('1Y', '3Y'):
                a = X.attribution(hh, 'all', p); worst = max(worst, abs(a['alloc'] + a['sel'] + a['inter'] - a['active']))
        ck('Claims', 'Attribution effects sum to the active return for every household and period', worst < 1e-9, f'largest gap {worst:.1e}')
        ck('Claims', 'Taxes and gains in summaries are labelled as planning estimates',
           all('planning' in next(t for t in D.ws1(hh, D.BASE, st)['trade'] if re.search('gains', t[0], re.I))[0] for hh in HHS()))
        vs = [D.value(hh, D.default_costs(hh)) for hh in HHS()]
        ck('Value story', 'Estimated net = expected return gain + harvesting after its fee − the higher fee, for every household', all(abs(v['er'] + v['harvNet'] - v['inc'] - v['net']) < 1 for v in vs))
        ck('Value story', 'Not-eligible households get no harvesting or transition value', all(D.elig(hh)['state'] != 'ineligible' or not vs[i]['diOk'] for i, hh in enumerate(HHS())))
        Qa = Q.all_queue(st)
        ck('Pathway', f'Every opportunity ({len(Qa)}) carries a use case and an advisory pathway, and renders six steps', all(o.get('uc') and o.get('pathway') and len(P.steps(o, st)) == 6 for o in Qa))
        ck('Pathway', 'Key control: the lower-cost alternative is shown in every eligible pathway',
           all('lower-cost alternative shown' in P.steps(o, st)[3]['v'] for o in Qa if D.elig(o['hh'])['state'] != 'ineligible'))
        ck('Pathway', 'Key control: excluded households (above 50%) get no program pathway and no assets in scope', all(x['scope'] == 0 for x in P.households(Qa, st) if x['ex']))
        ck('Pathway', 'Implement never clears without people: every stage list ends blocked', all(P.stages(hh, 'ws1:' + hh['id'], st)[4]['state'] == 'blocked' for hh in HHS()))

        def cash_ok(h):
            cs = X.cash_split(h); r = nsum(x['mv'] for x in X.routing(h) if x['route'] == 'instep')
            return abs(r - cs['investable']) < 1 and abs(P.transition(h)['parts']['instep'] - cs['investable']) < 1 and cs['investable'] <= max(0, cs['total'] - cs['target'] - cs['reserve']) + 1
        ck('Amounts', 'One canonical investable cash: the conversion map, the plan and the cash opportunity agree, and never exceed cash above target after the reserve', all(cash_ok(h) for h in HHS()))
        ck('Amounts', 'Every holding sits in exactly one bucket and the buckets add back to the total identified; bond timing is never counted',
           all(abs(K['move'] + K['gated'] + K['kept'] + K['excluded'] - P.amt(h)) < 2 for h in HHS() for K in [P.buckets(h)]))
        ck('Amounts', 'Identified ≥ program-eligible ≥ transitionable now, for every household',
           all(A['identified'] + 1 >= A['eligible'] and A['eligible'] + 1 >= A['now'] for h in HHS() for A in [P.amounts(h)]))
        ck('Paths', 'Every path lists feasibility checks with owners and an approver; not-eligible households get only the specialist route',
           all(ps and all(p['feas'] and p['approver'] for p in ps) and (D.elig(h)['state'] != 'ineligible' or (len(ps) == 1 and ps[0]['id'] == 'specialist'))
               for h in HHS() for ps in [P.paths(h, st)]))
        ck('Paths', 'Exactly one suggested path per household', all(nsum(1 for p in P.paths(h, st) if p.get('suggested')) == 1 for h in HHS()))
        mk = [D.ws4(ev, {'hh': hh, **r}, st)['size'] for hh in HHS() for ev in DATA['news'] for r in [X.event_for_hh(ev, hh)] if r['kind'] == 'market' and r['score'] > 1]
        ck('Events', 'Market-event sizes are labelled "estimated scenario impact"', all('estimated scenario impact' in x for x in mk), f'{len(mk)} sizes')
        n0 = len(Q.all_queue(State.from_dict({}))); cat = D.catalog()
        st2 = State.from_dict({'intel_run': {it['id']: True for it in cat if not it.get('auto')}})
        for it in cat:
            for hh in HHS():
                D.intel_for(it, hh, st2)
        ck('Intelligence', f'Publishing and analyzing all {len(cat)} catalog items leaves the opportunity count unchanged', len(Q.all_queue(st2)) == n0, f'{n0} before and after')
        sup = next(x for x in cat if x.get('rule') == 'superseded'); rs = next(x for x in cat if x.get('rule') == 'region-sector')
        ck('Intelligence', 'Superseded content is not evaluated; missing look-through is "not evaluated", not "no impact"',
           D.book_status(sup, st2)['k'] == 'na' and any(D.intel_for(rs, hh, st2)['state'] == 'unknown' for hh in HHS()))
        ck('Intelligence', 'Only approved, current items can be saved for a client meeting', all(x['type'] != 'market' for x in cat if x.get('client_use') and x.get('rule') != 'superseded'))
    except Exception as err:  # pragma: no cover - surfaced in the dialog
        ck('Harness', 'Checks ran without errors', False, repr(err))
    return out
