import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from app import agent
from app.main import app

client = TestClient(app)


def _tool_use(id_, name, inp):
    return {'type': 'tool_use', 'id': id_, 'name': name, 'input': inp}


class ScriptedModel:
    """Stands in for the Anthropic Messages API. Each call returns the next
    scripted response and records the payload it was sent, so tests can
    assert on exactly what the loop sent back to the model."""

    def __init__(self, script):
        self.script = list(script)
        self.payloads = []

    async def __call__(self, payload):
        self.payloads.append(json.loads(json.dumps(payload, default=str)))
        step = self.script.pop(0)
        return step(self.payloads[-1]) if callable(step) else step


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-key')
    monkeypatch.delenv('ATLAS_AGENT_MODE', raising=False)
    monkeypatch.delenv('ATLAS_AGENT_MODEL', raising=False)
    return monkeypatch


def test_live_loop_executes_tools_and_returns_navigation(live):
    def compare_step(payload):
        # The model reads the search_products result from the previous turn
        # and uses the real product_id it returned -- proving tool results are
        # actually fed back into the conversation.
        tool_result = payload['messages'][-1]['content'][0]
        found = json.loads(tool_result['content'])['products']
        voo = next(p['product_id'] for p in found if p['ticker'] == 'VOO')
        return {'stop_reason': 'tool_use', 'usage': {'input_tokens': 900, 'output_tokens': 60}, 'content': [
            _tool_use('t2', 'compare_vehicles', {'household_id': 'henderson', 'product_ids': [voo, 'RESEARCH_GROWTH-SMA-01']}),
            _tool_use('t3', 'open_workspace', {'workspace': 'vehicle_compare', 'household_id': 'henderson',
                                               'product_ids': [voo, 'RESEARCH_GROWTH-SMA-01'], 'auto_open': True})]}

    fake = ScriptedModel([
        {'stop_reason': 'tool_use', 'usage': {'input_tokens': 800, 'output_tokens': 40},
         'content': [{'type': 'text', 'text': 'Let me look that up.'}, _tool_use('t1', 'search_products', {'query': 'VOO'})]},
        compare_step,
        {'stop_reason': 'end_turn', 'usage': {'input_tokens': 1500, 'output_tokens': 120},
         'content': [{'type': 'text', 'text': 'VOO costs 4 bps versus 40 bps for the SMA.'}]},
    ])
    live.setattr(agent, '_anthropic_call', fake)
    out = asyncio.run(agent.run_agent('dana', 'Open a comparison of VOO against the SMA for Henderson', [],
                                      {'household_id': 'henderson', 'view': 'client'}))

    assert out['mode'] == f'live:{agent.DEFAULT_AGENT_MODEL}'
    assert out['content'].startswith('VOO costs 4 bps')
    assert [s['tool'] for s in out['steps']] == ['search_products', 'compare_vehicles', 'open_workspace']
    assert out['actions'][0]['workspace'] == 'vehicle_compare' and out['actions'][0]['auto_open'] is True
    assert out['usage'] == {'input_tokens': 3200, 'output_tokens': 220}
    first = fake.payloads[0]
    assert first['model'] == 'claude-haiku-4-5-20251001'
    assert {t['name'] for t in first['tools']} == set(agent.TOOL_IMPLS)
    assert 'henderson' in first['system'] and 'currently looking at household' in first['system']
    # tool_result blocks must reference the tool_use ids the model issued
    ids = [b['tool_use_id'] for b in fake.payloads[2]['messages'][-1]['content']]
    assert ids == ['t2', 't3']


def test_live_loop_reports_tool_errors_to_the_model(live):
    fake = ScriptedModel([
        {'stop_reason': 'tool_use', 'content': [_tool_use('e1', 'get_household', {'household_id': 'duarte'})]},
        {'stop_reason': 'end_turn', 'content': [{'type': 'text', 'text': "That household isn't in your book."}]},
    ])
    live.setattr(agent, '_anthropic_call', fake)
    out = asyncio.run(agent.run_agent('dana', 'Tell me about Duarte', []))
    result_block = fake.payloads[1]['messages'][-1]['content'][0]
    assert result_block['is_error'] is True
    assert "not in this advisor's book" in json.loads(result_block['content'])['error']
    assert out['steps'][0]['summary'].startswith('error')


def test_live_failure_falls_back_to_grounded_planner(live):
    async def boom(payload):
        raise RuntimeError('network down')
    live.setattr(agent, '_anthropic_call', boom)
    out = asyncio.run(agent.run_agent('dana', 'Is Henderson eligible for direct indexing?', []))
    assert out['mode'] == 'local-planner (live model unavailable)'
    assert 'ELIGIBLE' in out['content']


def test_open_workspace_validates_targets():
    res, action = agent.execute_tool('dana', 'open_workspace', {'workspace': 'transition', 'household_id': 'henderson'})
    assert 'error' in res and action is None
    res, action = agent.execute_tool('dana', 'open_workspace', {'workspace': 'meeting_prep_draft', 'household_id': 'reyes'})
    assert ('error' in res) == (agent.BY_ID['reyes'].get('nextMeeting') is None)
    res, action = agent.execute_tool('dana', 'open_workspace', {'workspace': 'transition', 'household_id': 'henderson', 'offering_id': 'transition'})
    assert action['workspace'] == 'transition'


def test_offering_resolution_does_not_confuse_the_word_transition_with_tet():
    assert agent.resolve_offering('Model a direct indexing transition for Henderson') == 'directIndexing'
    assert agent.resolve_offering('model a tax efficient transition') == 'transition'
    assert agent.resolve_offering('is she eligible for QLH?') == 'qlhOverlay'
    assert agent.resolve_offering('how do I transition this client') is None


def test_local_planner_routes_by_intent_and_uses_client_context(monkeypatch):
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    r = agent.run_local('dana', 'what is this client eligible for?', {'household_id': 'kaplan'})
    assert r['steps'][0]['tool'] == 'check_eligibility' and 'Kaplan' in r['content']
    r = agent.run_local('dana', 'Where are my biggest tax loss harvesting opportunities?', None)
    assert r['steps'][0]['tool'] == 'rank_book'
    r = agent.run_local('dana', 'Compare VOO, QQQ and the SMA for Henderson', None)
    ids = r['actions'][0]['product_ids']
    assert 'RESEARCH_GROWTH-SMA-01' in ids and 'ROSTER-ETF-QQQ' in ids


def test_agent_and_product_endpoints(monkeypatch):
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    r = client.post('/api/agent', json={'fa': 'dana', 'message': 'Model a direct indexing transition for Henderson'})
    assert r.status_code == 200 and r.json()['actions'][0]['offering_id'] == 'directIndexing'
    r = client.get('/api/products/search', params={'q': 'vanguard growth'})
    assert r.json()['results'][0]['ticker'] == 'VUG'
    r = client.get('/api/compare/henderson', params={'products': 'ROSTER-ETF-VTI,RESEARCH_GROWTH-SMA-01'})
    assert r.status_code == 200 and len(r.json()['comparison']['implementations']) == 2
    assert client.get('/api/compare/henderson', params={'products': 'NOPE'}).status_code == 404


# ---- regressions found by running the live agent against the real API ----

def test_numeric_shelf_filter_reports_actual_values_when_nothing_matches():
    # Against the real MLIAP Strategy Catalog, the lowest SMA minimum is $7,500,
    # so "SMAs with a minimum of $5,000 or less" must be answered "none" together
    # with the real minimums -- never an empty list with no explanation.
    res, _ = agent.execute_tool('dana', 'search_products', {'vehicle': 'SMA', 'max_minimum': 5000})
    assert res['total_matching'] == 0
    w = res['without_numeric_filters']
    assert w['count'] > 500 and w['minimums'][0] == 7500
    res, _ = agent.execute_tool('dana', 'search_products', {'vehicle': 'SMA', 'max_minimum': 100000})
    assert res['total_matching'] > 200 and all(p['minimum'] <= 100000 for p in res['products'])


def test_ineligible_with_unresolved_fields_is_reported_as_final():
    # A known failed requirement decides the verdict; unresolved fields must not
    # read as "eligibility can't be determined".
    res, _ = agent.execute_tool('dana', 'check_eligibility', {'household_id': 'kaplan', 'offering_id': 'qlhOverlay'})
    assert res['verdict'] == 'INELIGIBLE'
    assert res['failed_requirements'] and res['unresolved_fields']
    assert 'final answer' in res['meaning'] and 'NOT make the household eligible' in res['meaning']


def test_product_shelf_is_a_real_workspace_needing_no_household():
    res, action = agent.execute_tool('dana', 'open_workspace', {'workspace': 'product_shelf', 'vehicle': 'SMA', 'max_minimum': 100000})
    assert action['workspace'] == 'product_shelf'
    assert action['shelf_filters'] == {'q': '', 'vehicle': 'SMA', 'sleeve': None, 'max_minimum': 100000}


def test_system_prompt_describes_workspaces_and_forbids_tool_names():
    prompt = agent._system_prompt('dana', None)
    assert 'product_shelf:' in prompt and 'book: the list of households' in prompt
    assert 'Never mention tool or function names' in prompt
    assert 'Never claim a workspace shows something it does not' in prompt


def test_local_planner_answers_the_minimum_question_and_opens_filtered_shelf(monkeypatch):
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    r = agent.run_local('dana', 'which SMAs have minimum of 5000', None)
    assert r['content'].startswith('None.') and '$7.5K' in r['content']
    assert r['actions'][0]['workspace'] == 'product_shelf'
    assert r['actions'][0]['shelf_filters']['vehicle'] == 'SMA'
    r = agent.run_local('dana', 'which SMAs have minimum of 10000', None)
    assert 'None bps' not in r['content'] and 'fee per Strategy Profile' in r['content']


# ---- regressions from the second live run (Reyes / Kaplan transcript) ----

def _text(s):
    return {'type': 'text', 'text': s}


def test_answer_written_before_a_tool_call_is_not_dropped(live):
    # Haiku wrote the answer, called open_workspace, then added a closing
    # question. Only the closing question used to survive.
    fake = ScriptedModel([
        {'stop_reason': 'tool_use', 'content': [_text('Kaplan is eligible for Alternatives and Private Banking.'),
                                                _tool_use('c1', 'open_workspace', {'workspace': 'cross_sell', 'auto_open': True})]},
        {'stop_reason': 'end_turn', 'content': [_text('Would you like to explore the full radar?')]},
    ])
    live.setattr(agent, '_anthropic_call', fake)
    out = asyncio.run(agent.run_agent('dana', 'what are products eligible for kaplan', []))
    assert 'Alternatives and Private Banking' in out['content'] and 'full radar' in out['content']
    # an informational question never jumps screens, even if the model asked to
    assert out['actions'][0]['workspace'] == 'cross_sell' and out['actions'][0]['auto_open'] is False


def test_compare_request_opens_the_workspace_with_the_stated_amount(live):
    # The model compared but never called open_workspace; the server must still
    # open the comparison, for Reyes, at $1M -- not at Reyes's $12.4M AUM.
    fake = ScriptedModel([
        {'stop_reason': 'tool_use', 'content': [_tool_use('v1', 'compare_vehicles', {'household_id': 'reyes', 'amount': 1000000})]},
        {'stop_reason': 'end_turn', 'content': [_text('Direct indexing costs 17 bps more than the cheapest ETF.')]},
    ])
    live.setattr(agent, '_anthropic_call', fake)
    hist = [{'role': 'user', 'content': 'for reyes i am expecting 1m in assets incoming.. what are my options?'},
            {'role': 'assistant', 'content': 'Reyes has several eligible options.'}]
    out = asyncio.run(agent.run_agent('dana', 'yes compare options for deploying 1m', hist))
    a = out['actions'][0]
    assert a['workspace'] == 'vehicle_compare' and a['household_id'] == 'reyes'
    assert a['amount'] == 1000000 and a['auto_open'] is True and a['product_ids']


def test_model_opened_compare_without_amount_gets_it_filled(live):
    fake = ScriptedModel([
        {'stop_reason': 'tool_use', 'content': [_tool_use('v1', 'compare_vehicles', {'household_id': 'reyes', 'amount': 1000000}),
                                                _tool_use('o1', 'open_workspace', {'workspace': 'vehicle_compare', 'household_id': 'reyes', 'model_id': 'research_core'})]},
        {'stop_reason': 'end_turn', 'content': [_text('Opened.')]},
    ])
    live.setattr(agent, '_anthropic_call', fake)
    out = asyncio.run(agent.run_agent('dana', 'compare vehicles for reyes 1m', []))
    assert len(out['actions']) == 1 and out['actions'][0]['amount'] == 1000000


def test_prompt_forbids_the_pays_for_itself_claim():
    p = agent._system_prompt('dana', None)
    assert 'do not offset fees on new money' in p and 'pays for itself' in p


def test_parse_amount():
    assert agent.parse_amount('expecting 1m in assets') == 1_000_000
    assert agent.parse_amount('$2,500,000 incoming') == 2_500_000
    assert agent.parse_amount('750k') == 750_000 and agent.parse_amount('1.5 million') == 1_500_000
    assert agent.parse_amount('3y return, 5 accounts') is None


def test_local_planner_follow_up_uses_chat_history_for_household_and_amount(monkeypatch):
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    hist = [{'role': 'user', 'content': 'for reyes i am expecting 1m in assets incoming'}]
    r = agent.run_local('dana', 'yes compare options for deploying it', {'household_id': 'henderson'}, hist)
    a = r['actions'][0]
    assert a['workspace'] == 'vehicle_compare' and a['household_id'] == 'reyes'
    assert a['amount'] == 1_000_000 and a['auto_open'] is True


# ---- onboarding: the guided tour depends on these exact requests routing correctly ----

TOUR_REQUESTS = [
    ("Open Montgomery's advisory conversion map", 'conversion', 'montgomery', None),
    ("Model a tax efficient transition for Montgomery", 'transition', 'montgomery', 'transition'),
    ("Compare vehicles for Henderson's $5M incoming capital", 'vehicle_compare', 'henderson', None),
    ("Model a DCA schedule for Harlow", 'transition', 'harlow', 'dca'),
    ("Is Ferreira eligible for DCA? Open her eligibility screen", 'eligibility', 'ferreira', None),
    ("Is Okoye eligible for DTLH? Open his eligibility screen", 'tem', 'okoye', 'dtlhOverlay'),
    ("Is Lindqvist eligible for QLH? Open her eligibility screen", 'tem', 'lindqvist', 'qlhOverlay'),
    ("Is Castellano eligible for direct indexing? Open his eligibility screen", 'eligibility', 'castellano', None),
    ("Open the product shelf with SMAs with a minimum of 100K", 'product_shelf', None, None),
]


@pytest.mark.parametrize('message,workspace,household,offering', TOUR_REQUESTS)
def test_every_tour_request_opens_its_workspace(monkeypatch, message, workspace, household, offering):
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    r = agent.run_local('dana', message, None)
    auto = [a for a in r['actions'] if a['auto_open']]
    assert len(auto) == 1, r['actions']
    a = auto[0]
    assert a['workspace'] == workspace and a.get('household_id') == household
    if offering: assert a['offering_id'] == offering


def test_tour_compare_step_carries_the_5m_amount(monkeypatch):
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    a = agent.run_local('dana', "Compare vehicles for Henderson's $5M incoming capital", None)['actions'][0]
    assert a['amount'] == 5_000_000


def test_dca_is_recognised_by_name_and_acronym():
    assert agent.resolve_offering('Model a DCA schedule for Harlow') == 'dca'
    assert agent.resolve_offering('set up dollar cost averaging') == 'dca'


def test_help_opens_the_guide_and_unsupported_requests_offer_it(monkeypatch):
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    r = agent.run_local('dana', 'What can you do?', None)
    assert r['actions'][0]['workspace'] == 'guide' and r['actions'][0]['auto_open'] is True
    r = agent.run_local('dana', "what's the weather in Boston", None)
    assert 'closest requests' in r['content']
    assert r['actions'][0]['workspace'] == 'guide' and r['actions'][0]['auto_open'] is False
    assert 'guide' in agent._system_prompt('dana', None)


def test_shelf_request_is_not_hijacked_by_an_earlier_client_in_the_chat(monkeypatch):
    # Found by running the tour live: the previous step left Castellano in the
    # history, and "SMAs" read as a comparison word, so the shelf request turned
    # into a Castellano vehicle comparison.
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    hist = [{'role': 'user', 'content': 'Is Castellano eligible for direct indexing? Open his eligibility screen'}]
    r = agent.run_local('dana', 'Open the product shelf with SMAs with a minimum of 100K', {'household_id': 'castellano'}, hist)
    a = [x for x in r['actions'] if x['auto_open']][0]
    assert a['workspace'] == 'product_shelf' and a['shelf_filters']['vehicle'] == 'SMA'


# ---- brokerage-to-advisory conversion map (rules from the IAP Brochure) ----
from app.services import conversion_map, holding_kind


def _cell(m, sym, strat):
    return m['cells'][f'{sym}|{strat}']


def test_conversion_rules_per_holding_type():
    m = conversion_map('montgomery')
    assert m['applicable'] and len(m['strategies']) == 6
    assert _cell(m, 'PG', 'MANAGED')['outcome'] == 'SELL' and _cell(m, 'PG', 'MANAGED')['tet_stageable']
    assert _cell(m, 'PG', 'PERSONALIZED_CLIENT')['outcome'] == 'HOLD'
    assert _cell(m, 'LCG-A', 'CUSTOM_MANAGED')['outcome'] == 'EXCHANGE'          # ineligible share class
    assert _cell(m, 'AUSTIN-6.0-31', 'MANAGED')['outcome'] == 'SELL'
    assert not _cell(m, 'AUSTIN-6.0-31', 'MANAGED')['tet_stageable']             # TET.scope.fixed_income
    assert _cell(m, 'COST', 'PAS')['outcome'] == 'SELL' and not _cell(m, 'COST', 'PAS')['tet_stageable']  # TET.not_pas
    assert any(n['rule_id'] == 'DCA.cash_only' for n in _cell(m, 'MMF', 'MANAGED')['notes'])
    f = conversion_map('fairbanks')
    assert _cell(f, 'VA-CONTRACT', 'PERSONALIZED_CLIENT')['outcome'] == 'HOLD'
    assert _cell(f, 'VA-CONTRACT', 'DEFINED')['outcome'] == 'MOVE_OUT'
    assert _cell(f, 'CD-2027', 'CUSTOM_MANAGED')['outcome'] == 'REVIEW'
    b = conversion_map('brennan')
    assert _cell(b, 'PRIV-SERIESB', 'PERSONALIZED_CLIENT')['outcome'] == 'MOVE_OUT' and _cell(b, 'PRIV-SERIESB', 'MANAGED')['assumption']
    assert _cell(b, 'IDX-I', 'CUSTOM_MANAGED')['outcome'] == 'HOLD'


def test_conversion_totals_reconcile_and_cite_the_brochure():
    for hid in ('montgomery', 'fairbanks', 'brennan'):
        m = conversion_map(hid)
        for s in m['strategies']:
            assert s['hold_mv'] + s['sell_mv'] + s['exchange_mv'] + s['move_out_mv'] + s['review_mv'] == m['total_mv']
        assert all(c['source_doc'] and c['source_doc'][0]['document_id'] == 'IAPB' for c in m['cells'].values())


def test_conversion_advisor_qualification_and_enrolled_clients():
    assert not next(s for s in conversion_map('brennan', 'marcus')['strategies'] if s['strategy'] == 'DEFINED')['available']
    assert next(s for s in conversion_map('brennan', 'dana')['strategies'] if s['strategy'] == 'DEFINED')['available']
    assert conversion_map('henderson')['applicable'] is False
    assert conversion_map('delacroix')['applicable'] is False      # pre-existing enrolled client, untouched


def test_conversion_requests_route_to_the_map(monkeypatch):
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    r = agent.run_local('dana', "Open Montgomery's advisory conversion map", None)
    a = [x for x in r['actions'] if x['auto_open']][0]
    assert a['workspace'] == 'conversion' and a['household_id'] == 'montgomery' and '$3.25M' in r['content']
    assert agent.run_local('dana', "Open Henderson's advisory conversion map", None)['actions'] == []
