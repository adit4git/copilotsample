"""The Python rule engine reproduces the reference page exactly.

tests/fixtures/parity.json was captured from the reference prototype page (v6.2). Every rule result for every household,
every opportunity with its six steps, the ranking, the book view, sale plans, events and the intelligence catalog must match
bit for bit (numbers compared exactly, text character for character)."""
import pytest
from parity_util import FIXTURE as F, ser, diff
from app.data import HHS, DATA, State
from app import calc as X, rules as D, pathway as P, engine as E, opportunities as Q

HIDS = [h['id'] for h in HHS()]
ST = State.from_dict({})


def same(expected, actual):
    d = diff(expected, ser(actual), tol=0)
    assert not d, '\n'.join(d[:10])


@pytest.mark.parametrize('hid', HIDS)
def test_household_rules(hid):
    hh = DATA['households'][hid]; f = F['hh'][hid]
    same(f['elig'], D.elig(hh)); same(f['cash'], X.cash_split(hh)); same(f['routing'], X.routing(hh))
    same(f['transition'], P.transition(hh)); same(f['segment'], P.segment(hh)); same(f['forgone'], P.forgone(hh)); same(f['gapText'], P.gap_text(hh))
    same(f['options'], P.options(hh)); same(f['lowerCost'], P.lower_cost(hh)); same(f['screens'], P.screens(hh))
    same(f['buckets'], P.buckets(hh)); same(f['amounts'], P.amounts(hh)); same(f['paths'], P.paths(hh, ST)); same(f['remain'], P.remain(hh))
    same(f['handoff'], P.handoff(hh, ST)); same(f['blocker'], P.blocker(hh)); same(f['hstate'], P.hstate(hh, ST))
    c = D.default_costs(hh); same(f['costs'], c); same(f['value'], D.value(hh, c))
    same(f['stages'], P.stages(hh, 'hh:' + hid, ST, {'product': True}))
    same(f['ready'], [D.ready(hh), D.ready(hh, {'risk': True, 'product': True})])


@pytest.mark.parametrize('hid', HIDS)
def test_portfolio_math(hid):
    hh = DATA['households'][hid]; f = F['hh'][hid]; m = E.metrics(hh, hh['holdings'])
    same(f['metrics'], {k: m[k] for k in ['er', 'vol', 'stress', 'worst', 'names', 'te_t', 'te_m']})
    for sym, v in f['sells'].items():
        same(v, E.sell_plan(hh, hh['holdings'], sym, 1e6))


@pytest.mark.parametrize('hid', HIDS)
def test_gaps_attribution_and_findings(hid):
    hh = DATA['households'][hid]; f = F['hh'][hid]
    for k, v in f['gaps'].items():
        same(v, X.gap(hh, *k.split('|')))
    for k, v in f['attr'].items():
        same(v, X.attribution(hh, *k.split('|')))
    for k, v in f['ws1'].items():
        s, b, p = k.split('|'); w = D.ws1(hh, {'scope': s, 'basis': b, 'period': p}, ST); w.pop('g'); w.pop('a')
        same(v, w)


def test_opportunity_list_ranking_and_book():
    q = Q.all_queue(ST)
    same(F['queue'], [{**o, 'steps': P.steps(o, ST), 'why': P.why_of(o, ST)} for o in q])
    H = P.households(q, ST)
    same(F['households'], [{'hid': x['hh']['id'], 'ex': x['ex'], 'scope': x['scope'], 'seg': x['seg'], 'prim': x['prim'] and x['prim']['key'], 'cat': x['cat'], 'cues': x['cues'],
                            'why': x['why'], 'blk': x['blk'], 'filt': x['filt'], 'next': x['hs']['next'], 'path': x['path'] and x['path']['id'],
                            'open': [o['key'] for o in x['open']]} for x in H])
    same(F['book'], P.book(q, ST))


def test_concentrated_positions_and_sale_plans():
    L = Q.conc_list(ST); same(F['conc'], L)
    for p in L:
        o3 = F['plans'][p['key']]['o3']
        pl = X.sale_plan(p['hh'], p['sym'], {'target': o3['target'], 'budget': o3['budget'], 'gift': o3['gift'] if o3['ans']['gift'] else 0, 'years': o3['years'],
                                             'needs': o3['needs'] if o3['ans']['cash'] else {}})
        pl['target'] = o3['target']
        same(F['plans'][p['key']]['plan'], pl); same(F['ws3'][p['key']], D.ws3(p, pl, p['hh']))


def test_events_and_intelligence():
    for k, v in F['events'].items():
        eid, hid = k.split(':'); ev = next(n for n in DATA['news'] if n['id'] == eid); hh = DATA['households'][hid]; r = X.event_for_hh(ev, hh)
        same(v, {'r': r, 'm': D.ws4(ev, {'hh': hh, **r}, ST) if r['score'] > 1 else None})
    same(F['catalog'], [{**it, 'book': D.book_status(it, ST), 'per': {hh['id']: D.intel_for(it, hh, ST) for hh in HHS()}} for it in D.catalog()])
