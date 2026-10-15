"""TEM personalization: the TEM Guide and the TER / QLH / DTLH term sheets applied
position by position and lot by lot. The first two tests reproduce the term
sheets' own worked examples, so the rules are checked against the source."""
import pytest
from fastapi.testclient import TestClient

from app import agent
from app.main import app
from app.data import RULE_STORE, derive_facts, BY_ID
from app.tem import rank_lots, qlh_harvest, tem_personalization

client = TestClient(app)
EX = RULE_STORE['tem_personalization']['term_sheet_examples']


def test_ter_best_lot_reproduces_the_term_sheet_example():
    lots = rank_lots([{'lot_id': x['lot'], 'holding_days': x['holding_days'], 'qty': x['qty'], 'gain': x['gain']} for x in EX['ter_best_lot']['lots']])
    by = {l['lot_id']: l for l in lots}
    # Tax cost column of the term sheet (40.8% short-term, 23.8% long-term).
    assert [round(by[k]['tax_cost'], 1) for k in 'ABCD'] == [450.2, -239.7, 97.7, 142.8]
    assert [by[k]['tax_cost_per_share'] for k in 'ABCD'] == [0.90, -0.53, 0.16, 0.26]
    for x in EX['ter_best_lot']['lots']:
        assert by[x['lot']]['fifo_priority'] == x['term_sheet_fifo']
        assert by[x['lot']]['best_priority'] == x['term_sheet_best']


def test_qlh_reproduces_the_term_sheet_example():
    lots = qlh_harvest([{'lot_id': x['sym'], 'pct': x['pct']} for x in EX['qlh']['lots']])
    assert {l['lot_id'] for l in lots if l['status'] == 'HARVEST'} == {x['sym'] for x in EX['qlh']['lots'] if x['harvested']} == {'AB', 'CD', 'IJ'}
    assert next(l for l in lots if l['lot_id'] == 'MN')['status'] == 'BELOW_THRESHOLD'


def _cell(t, sym, overlay):
    key = next(h['key'] for h in t['holdings'] if h['sym'] == sym)
    return t['cells'][f'{key}|{overlay}']


def test_custom_managed_sleeves_get_different_overlays():
    t = tem_personalization('castellano')
    assert _cell(t, 'ITOT', 'DTLH')['outcome'] == 'APPLIES'
    assert _cell(t, 'ITOT', 'QLH')['outcome'] == 'SUPERSEDED'          # TEM Guide p.4
    assert _cell(t, 'JPM', 'QLH')['outcome'] == 'APPLIES'               # Style Manager SMA coded Q,T
    assert _cell(t, 'JPM', 'DTLH')['rule_id'] == 'TEM.COV.DTLH_CIO_ONLY'
    assert _cell(t, 'LCV-I', 'TER')['outcome'] == 'APPLIES'             # mutual fund sleeve
    assert _cell(t, 'NYSDA-5.0-34', 'TER')['rule_id'] == 'TEM.COV.FIXED_INCOME'
    assert _cell(t, 'AGG', 'QLH')['outcome'] == 'REVIEW'                # bond ETF: confirm
    assert _cell(t, 'CASH', 'TER')['outcome'] == 'NA'
    paths = {p['id']: p['status'] for p in t['paths']}
    assert paths['CUSTOM'] == 'CURRENT' and paths['TEM_SMS'] == 'SEPARATE_ACCOUNT'


def test_qlh_harvests_only_lots_at_5_percent_in_covered_sleeves():
    t = tem_personalization('castellano')
    q = t['qlh']
    assert {l['lot_id'] for l in q['lots'] if l['status'] == 'HARVEST'} == {'JPM-B', 'PFE-1', 'CVS-1'}
    assert q['harvest_loss'] == 41750
    # IEFA's 11% loss sits in the CIO ETF sleeve, where DTLH harvests instead.
    assert any(l['lot_id'] == 'IEFA-1' and l['outcome'] == 'SUPERSEDED' for l in q['outside'])
    # 91-day cycle from enrollment on 2026-03-02.
    assert q['last_run'] == '2026-08-31' and q['next_runs'][0] == '2026-11-30'


def test_short_term_gain_deferral_and_best_lot_in_a_real_account():
    t = tem_personalization('castellano')
    d = t['ter']['st_deferral']
    assert [(x['lot_id'], x['days_to_lt'], x['saving']) for x in d] == [('ITOT-2', 14, 1700)]
    order = [l['lot_id'] for l in sorted(t['ter']['best_lot']['lots'], key=lambda x: x['best_priority'])]
    assert order == ['JPM-B', 'JPM-D', 'JPM-C', 'JPM-A']
    assert t['ter']['term_sheet_check']['matches'] is True


def test_tem_style_manager_inside_a_tax_aware_model_is_manager_run():
    t = tem_personalization('ashford')
    for sym in ('AAPL', 'PFE', 'INTC'):
        for o in ('TER', 'QLH', 'DTLH'):
            assert _cell(t, sym, o)['outcome'] == 'MANAGER_RUN'
    assert _cell(t, 'IEFA', 'QLH')['outcome'] == 'APPLIES'
    q = t['qlh']
    assert {l['lot_id'] for l in q['lots'] if l['status'] == 'HARVEST'} == {'IEFA-1', 'VWO-1'}
    assert next(l for l in q['lots'] if l['lot_id'] == 'VWO-1')['wash_sale_risk']
    assert {l['lot_id'] for l in q['outside'] if l['outcome'] == 'MANAGER_RUN'} == {'PFE-1', 'INTC-1'}
    assert any(c['rule_id'] == 'TEM.CONS.HELD_AWAY' for c in t['considerations'])
    paths = {p['id']: p['status'] for p in t['paths']}
    assert paths['IM_MODEL'] == 'CURRENT'
    # The rule engine carves the TEM Style Manager and bond positions out of the overlays' scope.
    f = derive_facts(BY_ID['ashford'], 'qlhOverlay')
    assert {'AAPL', 'NJTA-4.0-31'} <= set(f['scope.overlay_ineligible_investment_ids'])


def test_threshold_bracket_and_deferral_for_okoye():
    t = tem_personalization('okoye')
    st = {l['lot_id']: l['status'] for l in t['qlh']['lots']}
    assert st['JNJ-1'] == 'HARVEST' and st['UNH-1'] == 'HARVEST'
    assert st['JNJ-2'] == 'BELOW_THRESHOLD' and st['PG-1'] == 'BELOW_THRESHOLD'
    assert any(c['rule_id'] == 'TEM.CONS.BRACKET' for c in t['considerations'])
    assert [x['lot_id'] for x in t['ter']['st_deferral']] == ['HD-2']
    assert next(c for c in t['coverage'] if c['overlay'] == 'DTLH')['applies_mv'] == 0


@pytest.mark.parametrize('hid,gate', [('lindqvist', 'TEM.GATE.US'), ('montgomery', 'TEM.GATE.PROGRAM'), ('bianchi', 'TEM.GATE.NOT_PAS')])
def test_account_gates_block_every_overlay(hid, gate):
    t = tem_personalization(hid)
    assert t['blocked'] and any(g['rule_id'] == gate and g['passed'] is False for g in t['gates'])
    assert all(c['outcome'] == 'BLOCKED' for c in t['cells'].values())


def test_tem_api():
    r = client.get('/api/tem/castellano'); assert r.status_code == 200 and r.json()['applicable']
    assert client.get('/api/tem/nope').status_code == 404
    assert client.get('/api/tem/sato').json()['applicable'] is False
    rows = client.get('/api/tem-book?fa=dana').json()['rows']
    assert rows and all(r['at_threshold'] + r['below_threshold'] > 0 for r in rows)


TEM_TOUR = [
    ("Open Castellano's tax personalization", 'castellano', None),
    ("Which of Okoye's lots would QLH harvest? Open his tax personalization", 'okoye', 'qlhOverlay'),
    ("Open Ashford's tax personalization", 'ashford', None),
    ("Can Castellano add a TEM Style Manager Strategy? Open his tax personalization", 'castellano', 'temSms'),
]


@pytest.mark.parametrize('message,household,tab', TEM_TOUR)
def test_tem_tour_requests_open_the_tax_personalization(monkeypatch, message, household, tab):
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    r = agent.run_local('dana', message, None)
    auto = [a for a in r['actions'] if a['auto_open']]
    assert len(auto) == 1 and auto[0]['workspace'] == 'tem' and auto[0]['household_id'] == household and auto[0]['offering_id'] == tab


def test_tem_intent_does_not_capture_existing_requests(monkeypatch):
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    for q in ['Is Ferreira eligible for DCA?', 'Where are my biggest tax-loss harvesting opportunities?', 'Model a tax efficient transition for Montgomery']:
        assert not any(a['workspace'] == 'tem' for a in agent.run_local('dana', q, None)['actions']), q


def test_strategies_on_the_tem_guide_list_are_tem_style_manager_strategies():
    from app.tem import _sleeve_from_product
    assert _sleeve_from_product('CAT-FRANKLIN-DJ-US-DIV-SELECT-CANVAS-TM-SMA')['kind'] == 'TEM_SMS'   # an SMA, but on the TEM Guide p.5 list
    assert _sleeve_from_product('CAT-EATON-VANCE-LARGE-CAP-VALUE-SMA')['kind'] == 'SMS'
    assert _sleeve_from_product('CAT-CIO-EQUITY-ETF-CORE')['kind'] == 'CIO_ETF'
    roster = RULE_STORE['tem_personalization']['tem_sms_roster']['strategies']
    assert len(roster) == 35 and all(x['in_catalog'] for x in roster)


def test_overlay_eligibility_questions_open_the_tax_personalization_card(monkeypatch):
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    nav = [a for a in agent.run_local('dana', 'Is Okoye eligible for DTLH?', None)['actions'] if a['workspace'] in ('tem', 'eligibility')]
    assert nav and nav[0]['workspace'] == 'tem' and nav[0]['offering_id'] == 'dtlhOverlay'
    # Non-tax offerings keep the eligibility screen.
    assert any(a['workspace'] == 'eligibility' for a in agent.run_local('dana', 'Is Ferreira eligible for DCA?', None)['actions'])


def test_tet_interactions_and_labels_live_in_the_card():
    t = tem_personalization('castellano')
    rel = {n['overlay']: n['relation'] for n in t['tet']['notes']}
    assert rel == {'DTLH': 'INCOMPATIBLE_WITH', 'TER': 'SCOPE_CARVEOUT_WITHIN_COMPOSITION', 'QLH': 'SCOPE_CARVEOUT_WITHIN_COMPOSITION'}
    assert tem_personalization('lindqvist')['tet'] is None          # blocked accounts show no TET note
    assert RULE_STORE['offerings']['taxManagedSMA']['label'] == 'Tax Efficient Rebalancing (TER)'
    okoye = {c['overlay']: c for c in tem_personalization('okoye')['coverage']}
    assert okoye['QLH']['can_model'] and not okoye['DTLH']['can_model']
