"""Reference figures and business rules, written out so a reader can see what the engine promises."""
import pytest
from app.data import DATA, State, household
from app import calc as X, rules as D, pathway as P, engine as E, opportunities as Q
from app.checks import run_checks

ST = State.from_dict({})


def test_portfolio_math_reference():
    exp = {'henderson': (5.64, 9.24), 'kaplan': (5.86, 10.45), 'castellano': (6.29, 11.09), 'okonkwo': (5.23, 6.54), 'brennan': (6.60, 15.31)}
    for hid, (er, vol) in exp.items():
        m = E.metrics(household(hid), household(hid)['holdings'])
        assert round(m['er'] * 100, 2) == er and round(m['vol'] * 100, 2) == vol


def test_tax_lot_rule_nvda():
    p = E.sell_plan(household('henderson'), household('henderson')['holdings'], 'NVDA', 1e6)
    assert round(p['gain']) == 801887 and round(p['tax']) == 190849 and p['excluded'] == 400000


def test_program_fee_tiers():
    assert [round(X.program_fee(a)['fee']) for a in (1e6, 5e6, 47.2e6)] == [10000, 42000, 260500]


def test_one_eligibility_rule_with_look_through():
    e = D.elig(household('delgado'))
    assert e['state'] == 'ineligible' and e['sym'] == 'COST' and e['via'] == '58.2% direct, 0.2% through funds'
    assert D.elig(household('okonkwo'))['state'] == 'eligible'
    assert [D.elig(household(h))['state'] for h in ('henderson', 'kaplan', 'castellano', 'brennan')] == ['conditions'] * 4


def test_canonical_investable_cash():
    cs = X.cash_split(household('henderson'))
    assert (round(cs['target']), round(cs['reserve']), round(cs['investable'])) == (3230500, 1000000, 3069500)
    assert round(X.cash_split(household('okonkwo'))['investable']) == 11422000
    assert X.cash_split(household('castellano'))['investable'] == 0


def test_buckets_reconcile_and_headline_amounts():
    A = P.amounts(household('henderson'))
    assert (A['now'], A['laterSum'], A['kept'], A['identified']) == (47200000, 400000, 2100000, 49700000)
    assert round(A['alignY1'], 3) == 0.695
    d = P.amounts(household('delgado'))
    assert d['ex'] and d['now'] == 0 and d['excluded'] == 1650000


def test_routes_and_starting_points():
    picks = {h: next(p['id'] for p in P.paths(household(h), ST) if p['suggested']) for h in DATA['households']}
    assert picks == {'henderson': 'managed', 'kaplan': 'managed', 'castellano': 'rebalance', 'okonkwo': 'phased', 'brennan': 'managed', 'delgado': 'specialist'}
    spec = P.paths(household('delgado'), ST)
    assert len(spec) == 1 and spec[0]['cost'] == '$1,650 a year in brokerage today'


def test_value_story_net():
    net = {h: round(D.value(household(h), D.default_costs(household(h)))['net']) for h in ('henderson', 'kaplan', 'castellano', 'okonkwo', 'brennan')}
    assert net == {'henderson': 66801, 'kaplan': -26008, 'castellano': -16194, 'okonkwo': 396280, 'brennan': -213}


def test_ranking_queue_and_book():
    q = Q.all_queue(ST)
    assert len(q) == 27 and sum(o['grp'] == 'action' for o in q) == 25
    assert [x['hh']['id'] for x in P.households(q, ST)] == ['henderson', 'okonkwo', 'kaplan', 'castellano', 'brennan', 'delgado']
    B = P.book(q, ST)
    assert round(B['scope']) == 85211000 and round(B['bpsNow'], 1) == 9.0 and round(B['bpsAdv'], 1) == 59.8


def test_assessment_does_not_close_work():
    k = 'ws3:henderson:NVDA'
    grp = lambda d: next(o['grp'] for o in Q.queue(State.from_dict({'disp': {k: d}})) if o['key'] == k)
    assert grp({'status': 'review', 'set': True}) == 'action'
    assert grp({'status': 'stay', 'set': True, 'reason': ''}) == 'action'
    assert grp({'status': 'stay', 'set': True, 'reason': 'Client declined'}) == 'done'
    assert grp({'status': 'defer', 'set': True, 'reason': 'Timing: revisit later'}) == 'monitor'


def test_household_flow_follows_decisions():
    st = State.from_dict({'disp': {'hh:henderson': {'status': 'ready', 'set': True}}, 'choice': {'hh:henderson': 'managed'}, 'o2': {'henderson': {'rev': 'compliance'}},
                          'handed': {'henderson': True}})
    assert P.hstate(household('henderson'), st)['step'] == 'handoff'
    assert P.stages(household('henderson'), 'hh:henderson', st)[4]['note'] == 'Handed off: operations to enroll (prototype)'
    assert P.hstate(household('delgado'), ST)['next'] == ['Request specialist', 'assess']


def test_intelligence_never_adds_work_unless_promoted():
    base = len(Q.all_queue(State.from_dict({})))
    assert len(Q.all_queue(State.from_dict({'intel_run': {'f1': True, 'f2': True}}))) == base
    assert len(Q.all_queue(State.from_dict({'promo': {'f1:castellano': {'id': 'f1', 'hid': 'castellano'}}}))) == base + 1


def test_all_30_checks_pass():
    r = run_checks()
    assert len(r) == 30 and all(x['pass'] for x in r), [x for x in r if not x['pass']]
