import json
from pathlib import Path
import pytest
from wealth_intent.runtime import route_request, export_route
from wealth_intent.semantic_model import SemanticModelProvider, SemanticModelProposal

NAMED = "Flag major estimate revisions for top holdings across John, Smith and Rita's accounts"
PRIORITIZED = "Flag major estimate revisions for top holdings across my prioritized clients"


def shape(result):
    plan=result['capability_route']; functions={n['id']:n['function_id'] for n in plan['nodes']}
    return {'intents':sorted(result['intents']),'scope':result['scope'],'metric':result['metric'],
            'capability':result['capability_id'],'missing':result['missing_context'],
            'functions':[n['function_id'] for n in plan['nodes']],
            'edges':sorted((functions[d],n['function_id']) for n in plan['nodes'] for d in n['depends_on'])}


def test_named_and_prioritized_population_share_analytical_plan():
    a=route_request(NAMED,monitor_mode='one_time');b=route_request(PRIORITIZED,monitor_mode='one_time')
    assert a['subject_selection']=='explicit_subject_references'
    assert b['subject_selection']=='prioritized_clients'
    assert shape(a)==shape(b)
    assert a['scope']=='subject_set'
    assert a['missing_context']==['analysis_period','holding_selection','materiality_threshold']


@pytest.mark.parametrize('query',[
    'Draft an email explaining volatility to this client.',
    'Draft an email explaining volatility to the selected client.',
    'Draft an email explaining volatility to this customer.',
])
def test_client_aliases_keep_client_context(query):
    r=route_request(query)
    assert r['scope']=='account_or_client' and r['audience']=='client'
    assert r['capability_id']=='communication.client_market_update'
    assert 'client_reference' in r['missing_context']


def test_clause_negation_controls_metric_and_attachment():
    r=route_request('Do not explain credit spread. Explain earnings for this issue.')
    assert r['metric']=='earnings' and r['capability_id']=='research.security_explanation'
    r=route_request('Explain credit spread for this issue. No article is attached.')
    assert 'attachment_reference' not in r['context_state']
    assert {'security_reference','analysis_period'} <= set(r['missing_context'])


@pytest.mark.parametrize('query', ['Could you enroll this client in PAS?', 'I would like you to enroll this client in PAS.'])
def test_polite_enrollment_is_operational(query):
    r=route_request(query)
    assert r['requested_effect']=='operational_action'
    assert r['capability_status']=='CAPABILITY_GAP'


@pytest.mark.parametrize('query',[
    'Explain performance for this portfolio YTD.',
    'Explain performance for this portfolio year to date.',
    'Explain performance for this portfolio from the start of this year through today.',
    'Explain performance for this portfolio since January 1 of this year.',
])
def test_ytd_variants_supply_period(query):
    assert 'analysis_period' not in route_request(query)['missing_context']


def test_explicit_output_and_parameters_are_independent():
    r=route_request('Explain portfolio performance in a table for this client.')
    assert r['output']=='analysis_table'
    five=route_request('Flag estimate revisions above 5% for the top 5 holdings across my prioritized clients.',monitor_mode='one_time')
    twenty=route_request('Flag estimate revisions above 20% for the top 10 holdings across my prioritized clients.',monitor_mode='one_time')
    assert shape(five)==shape(twenty)
    assert five['semantic_parameters']['top_n']['value']==5
    assert twenty['semantic_parameters']['materiality_percent']['value']==20.0
    assert 'holding_selection' not in five['missing_context'] and 'materiality_threshold' not in five['missing_context']


class FakeLocalModel(SemanticModelProvider):
    trusted_local=True;model_id='fake.local.1'
    def __init__(self): self.received=None
    def predict(self,text):
        self.received=text
        return SemanticModelProposal({'scope':'account_or_client'},{'scope':.95},self.model_id)


def test_model_sees_abstracted_text_and_validator_remains_in_path():
    model=FakeLocalModel()
    r=route_request('Client Avery Example, email avery@example.test, account 999-00123: explain performance.',semantic_model=model)
    assert 'Avery Example' not in model.received and 'avery@example.test' not in model.received and '999-00123' not in model.received
    assert r['semantic_engine']['model_provider']=='fake.local.1'
    assert r['semantic_engine']['model_applied_fields']==['scope']
    assert 'text' not in r['semantic_engine']['model_input']
    out=json.dumps(export_route(r))
    assert 'Avery Example' not in out and 'avery@example.test' not in out


def test_untrusted_model_provider_rejected():
    class Remote(SemanticModelProvider):
        def predict(self,text): return SemanticModelProposal({}, {}, self.model_id)
    with pytest.raises(ValueError,match='trusted-local'):
        route_request('Explain earnings.',semantic_model=Remote())


def test_corpus_has_no_training_eligible_authored_cases():
    path=Path(__file__).resolve().parents[1]/'data/semantic_annotation_corpus.jsonl'
    rows=[json.loads(x) for x in path.read_text().splitlines()]
    assert len(rows)>=240 and len({r['case_id'] for r in rows})==len(rows)
    assert all(not r['training_eligible'] for r in rows)
    assert all(r['split_group'] for r in rows)


def test_silver_dataset_is_semantic_only_and_quality_gated():
    root=Path(__file__).resolve().parents[1]/'data'
    rows=[json.loads(x) for x in (root/'semantic_silver_labels_v1.jsonl').read_text().splitlines()]
    manifest=json.loads((root/'semantic_silver_manifest_v1.json').read_text())
    assert len(rows)==242 and manifest['usable_semantic_silver_records']==162
    assert manifest['training_eligible']==0
    assert all(not row['training_eligible'] and not row['independent_review'] for row in rows)
    assert all(field not in (row['semantic_labels'] or {})
               for row in rows for field in ('capability_id','decision','missing_context'))


def test_silver_diagnostic_split_has_no_group_leakage():
    root=Path(__file__).resolve().parents[1]/'data'
    rows=[json.loads(x) for x in (root/'semantic_silver_diagnostic_eval_v1.jsonl').read_text().splitlines()]
    manifest=json.loads((root/'semantic_silver_diagnostic_eval_manifest_v1.json').read_text())
    assert len(rows)==162 and manifest['group_leakage']==0
    assert manifest['split_counts']=={'development_diagnostic':116,'heldout_diagnostic':46}
    groups={}
    for row in rows:
        groups.setdefault(row['split_group'],set()).add(row['diagnostic_split'])
        assert not row['training_eligible'] and not row['independent_review']
    assert all(len(splits)==1 for splits in groups.values())


def test_disagreement_review_manifest_is_focused_and_anonymized():
    root=Path(__file__).resolve().parents[1]/'data'
    manifest=json.loads((root/'disagreement_review_manifest_v1.json').read_text())
    assert manifest['cases']==86 and manifest['chunks']==8
    assert manifest['maximum_cases_per_chunk']==12
    assert manifest['candidate_sources_anonymized'] is True
    assert manifest['reason_counts']['unresolved']==5


@pytest.mark.parametrize('query,additional_intent', [
    ('Build a proposal using the current CIO model allocation.', 'solution.match'),
    ('Convert CIO guidance into a client-facing paragraph.', 'content.draft'),
    ('Explain portfolio underperformance with CIO guidance and benchmark data.', 'performance.attribution'),
])
def test_cio_evidence_is_retained_in_composed_requests(query, additional_intent):
    result = route_request(query)
    assert {'research.cio', additional_intent} <= set(result['intents'])


@pytest.mark.parametrize('query', [
    'Flag major estimate revisions for top holdings across my prioritized clients.',
    'Flag estimate revisions above 5% for holdings across my prioritized clients.',
    'Flag major estimate revisions for the top 10 holdings across the selected clients.',
])
def test_holdings_selection_does_not_manufacture_exposure_intent(query):
    result = route_request(query, monitor_mode='one_time')
    assert result['intents'] == ['research.security']
    assert result['output'] == 'holdings_signal_analysis'
    assert result['capability_id'] == 'book.holdings_signal_analysis'
    assert any(node['function_id'] == 'subject_set.snapshot'
               for node in result['capability_route']['nodes'])


def test_explicit_exposure_request_keeps_exposure_and_market_research():
    result = route_request('Which clients are exposed to interest rates moving higher?')
    assert {'portfolio.exposure', 'research.security'} <= set(result['intents'])
    assert result['output'] == 'holdings_signal_analysis'


@pytest.mark.parametrize('query,expected', [
    ('Which approved strategies fit an income objective?', {'product.search', 'solution.match'}),
    ('List products that fit this objective and include eligibility constraints.', {'product.search', 'solution.match'}),
    ('Compare SMA versus ETF options that fit this client.', {'product.compare', 'solution.match'}),
])
def test_fit_language_composes_discovery_or_comparison_with_solution_match(query, expected):
    assert expected <= set(route_request(query)['intents'])


def test_broad_book_market_signal_does_not_require_registered_metric():
    result = route_request("Which clients are exposed to today's macro market moves?")
    assert result['metric'] is None
    assert result['capability_id'] == 'book.holdings_signal_analysis'
    assert result['decision'] != 'REVIEW'


def test_cross_model_review_is_complete_semantic_only_and_not_training_gold():
    root = Path(__file__).resolve().parents[1] / 'data'
    reviews = [json.loads(x) for x in
               (root / 'step5_semantic_review_adjudicated_v1.jsonl').read_text().splitlines()]
    labels = [json.loads(x) for x in
              (root / 'semantic_reviewed_silver_labels_v2.jsonl').read_text().splitlines()]
    manifest = json.loads((root / 'semantic_reviewed_silver_manifest_v2.json').read_text())
    assert len(reviews) == 86 and len({row['case_id'] for row in reviews}) == 86
    assert len(labels) == 242 and len({row['case_id'] for row in labels}) == 242
    assert manifest['accepted_step5_cases'] == 84
    assert manifest['pending_step5_cases'] == 2
    assert manifest['usable_semantic_silver_records'] == 206
    assert manifest['human_reviewed_records'] == 0
    assert manifest['training_eligible_records'] == 0
    assert {row['case_id'] for row in reviews
            if row['acceptance_status'] != 'ACCEPTED_SEMANTIC_SILVER'} == {'base_106', 'base_114'}
    assert all(not row['training_eligible'] and not row['independent_review']
               and not row['human_reviewed'] for row in labels)
    assert all(field not in (row['semantic_labels'] or {}) for row in labels
               for field in ('capability_id', 'decision', 'missing_context', 'functions', 'dag'))
