"""Team skills: loading, applying, reverting exactly, and what each demo skill changes."""
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import skills
from app.data import RULE_STORE, CONFIG
from app import cio
from app.services import offering_result, conversion_map, generate_draft_local
from app.tem import tem_personalization, book_harvest
from app.agent import run_local
from app.skill_impact import skill_impact

c = TestClient(app)


@pytest.fixture(autouse=True)
def all_off():
    skills.set_active([])
    yield
    skills.set_active([])


def test_catalog_loads_every_skill_with_owner_and_workspaces():
    assert len(skills.CATALOG) == 12
    for s in skills.CATALOG.values():
        assert s['title'] and s['team'] and s['owner'] and s['workspaces'] and s['summary']
        assert 'What it changes' in s['sections'] and 'Why' in s['sections']


def test_all_skills_apply_cleanly_together():
    assert skills.set_active(list(skills.CATALOG)) == {}
    assert skills.active() == list(skills.CATALOG)


def test_turning_everything_off_restores_the_data_exactly():
    base = deepcopy(RULE_STORE), deepcopy(cio.C), deepcopy(CONFIG)
    ids = (id(RULE_STORE['tem_personalization']), id(cio.C['thresholds']))
    skills.set_active(list(skills.CATALOG))
    assert RULE_STORE != base[0] and cio.C != base[1]
    skills.set_active([])
    assert (RULE_STORE, cio.C, CONFIG) == base
    assert ids == (id(RULE_STORE['tem_personalization']), id(cio.C['thresholds']))   # same objects: references elsewhere stay valid


def test_every_skill_changes_something_in_danas_book():
    for sid in skills.CATALOG:
        r = skill_impact(sid, 'dana')
        assert r['changes'], sid
        assert skills.active() == []          # measuring never leaves a skill on


def test_rule_pack_skill_changes_verdict_and_names_itself():
    assert offering_result('okoye', 'qlhOverlay')['verdict'] == 'ELIGIBLE'
    skills.set_active(['qlh-term-sheet-2027'])
    v = offering_result('okoye', 'qlhOverlay')
    assert v['verdict'] == 'INELIGIBLE'
    assert any(t['rule_id'] == 'qlhOverlay.minimum_2027' and t['skills'] == ['qlh-term-sheet-2027'] for t in v['trace'])
    assert v['rule_pack_skills'] == ['qlh-term-sheet-2027']
    assert any('held-away' in d['message'] for d in offering_result('castellano', 'qlhOverlay')['disclosures'])


def test_qlh_threshold_pilot_reaches_lots_headline_and_desk():
    before = tem_personalization('okoye')['qlh']
    skills.set_active(['qlh-threshold-pilot'])
    t = tem_personalization('okoye')
    assert t['qlh']['threshold'] == 0.025 and t['qlh']['harvest_count'] > before['harvest_count']
    assert '2.5%+' in t['headline'] and t['policy_skills']['qlh_threshold'][0]['id'] == 'qlh-threshold-pilot'
    assert c.get('/api/tem-book?fa=dana').json()['threshold'] == 0.025
    assert sum(r['at_threshold'] for r in book_harvest('dana')) > 0


def test_year_end_playbook_adds_considerations_and_draft_section():
    skills.set_active(['year-end-tax-playbook'])
    cons = tem_personalization('okoye')['considerations']
    assert {'YE.GAINS_ELSEWHERE', 'YE.BELOW_THRESHOLD'} <= {x['rule_id'] for x in cons}
    assert all(x['skills'][0]['team'] == 'Wealth Planning' for x in cons if x['rule_id'].startswith('YE.'))
    assert '### Year-end tax check' in generate_draft_local('okoye', 'meeting_prep')


def test_shortlist_skill_changes_tem_style_manager_options():
    before = [x['name'] for x in tem_personalization('okoye')['tem_sms_options']]
    skills.set_active(['tem-sms-shortlist'])
    t = tem_personalization('okoye')
    assert [x['name'] for x in t['tem_sms_options']] != before
    assert 'GLOBAL' in t['tem_sms_selection']['families'] and t['tem_sms_selection']['per_family'] == 1


def test_conversion_skills_combine():
    assert conversion_map('montgomery')['recommended'] == 'PERSONALIZED_CLIENT'
    skills.set_active(['managed-first-conversion'])
    m = conversion_map('montgomery')
    assert m['recommended'] == 'CUSTOM_MANAGED' and '3.5% budget' in m['recommend_reason']
    assert conversion_map('brennan')['recommended'] == 'PERSONALIZED_CLIENT'         # over budget: falls back
    skills.set_active(['managed-first-conversion', 'conversion-nj-tax-rate'])
    m = conversion_map('montgomery')
    assert m['tax_rate'] == 0.3455 and m['recommended'] == 'PERSONALIZED_CLIENT'     # NJ tax pushes it past the budget
    assert m['policy_skills']['tax_rate'][0]['id'] == 'conversion-nj-tax-rate'
    assert conversion_map('fairbanks')['recommended'] == 'CUSTOM_MANAGED'


def test_cd_house_policy_and_risk_guardrails():
    assert conversion_map('fairbanks')['cells']['CD-2027|CUSTOM_MANAGED']['outcome'] == 'REVIEW'
    skills.set_active(['conversion-cd-hold', 'conversion-risk-guardrails'])
    cell = conversion_map('fairbanks')['cells']['CD-2027|CUSTOM_MANAGED']
    assert cell['outcome'] == 'HOLD' and cell['skills'][0]['team'] == 'Program Operations'
    m = conversion_map('montgomery')
    assert any(n['rule_id'] == 'RISK.concentrated_sale' for n in m['cells']['COST|MANAGED']['notes'])
    assert m['high_cash_share'] == 0.15


def test_cio_skills():
    base = {a['household_id']: a['current']['expected_return'] for a in cio.fit_book('dana')['accounts']}
    skills.set_active(['cio-cma-2027-preview', 'cio-risk-flags'])
    d = cio.fit_book('dana')
    assert d['as_of']['cma'] == '2027 preview' and d['thresholds']['concentration'] == 0.12
    assert {a['household_id']: a['current']['expected_return'] for a in d['accounts']} != base
    assert any(f['id'] == 'concentration' for f in cio.account_fit('fairbanks')['flags'])


def test_meeting_prep_skill_and_live_prompt_text():
    skills.set_active(['meeting-prep-fees-conflicts'])
    d = generate_draft_local('okoye', 'meeting_prep')
    assert '### Fees & conflicts' in d and '### Before you send this' in d and 'bps all-in' in d
    assert d.index('### Concentration & risk') < d.index('### Fees & conflicts') < d.index('### CIO alignment')
    assert 'Never promise or project performance' in skills.instructions('draft')


def test_routing_skill_changes_where_ask_atlas_goes():
    def where(q):
        r = run_local('dana', q, None)
        return [a['workspace'] for a in r['actions']]
    assert 'conversion' not in where('Should the Montgomerys go fee-based?')
    skills.set_active(['ask-atlas-plain-english'])
    assert where('Should the Montgomerys go fee-based?')[0] == 'conversion'
    assert where("Is Montgomery's account off-model?")[0] == 'cio_fit'
    assert where('Any wash sale issues for Okoye?')[0] == 'tem'
    assert 'fee-based' in skills.routing_hints()


def test_bad_patch_is_reported_not_fatal():
    saved = skills.CATALOG['qlh-threshold-pilot']['patches']
    try:
        skills.CATALOG['qlh-threshold-pilot']['patches'] = [{'target': 'rules', 'op': 'set', 'path': 'no_such.section.value', 'value': 1}]
        errs = skills.set_active(['qlh-threshold-pilot'])
        assert 'qlh-threshold-pilot' in errs and RULE_STORE['tem_personalization']['mechanics']['qlh']['loss_threshold'] == 0.05
    finally:
        skills.CATALOG['qlh-threshold-pilot']['patches'] = saved


def test_skills_api_and_ask_atlas():
    d = c.get('/api/skills').json()
    assert len(d['skills']) == 12 and d['active'] == []
    d = c.post('/api/skills/managed-first-conversion', json={'enabled': True}).json()
    assert d['active'] == ['managed-first-conversion']
    assert c.get('/api/conversion/montgomery').json()['recommended'] == 'CUSTOM_MANAGED'
    imp = c.get('/api/skills/managed-first-conversion/impact?fa=dana').json()
    assert imp['by_workspace'] == {'conversion': 2}
    r = c.post('/api/agent', json={'fa': 'dana', 'message': 'Which team skills are on?'}).json()
    assert 'Conversion playbook' in r['content'] and r['actions'][0]['workspace'] == 'skills'
    assert c.post('/api/skills/reset').json()['active'] == []
    assert c.post('/api/skills/nope', json={'enabled': True}).status_code == 404
