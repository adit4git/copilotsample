import json
import pytest
from wealth_intent.runtime import route_request, export_route, route_suite
from wealth_intent.planning import capability_catalog, validate_graph

TAX = 'Client Avery Example, email avery@example.test, account 999-00123, has $750,000. Prepare a tax-aware transition proposal for concentrated stock.'


def test_transition_outcome_covers_sections_and_assumptions():
    r = route_request(TAX)
    assert r['capability_id'] == 'portfolio.tax_aware_concentration_transition'
    assert r['output'] == 'tax_aware_transition_proposal'
    assert {'gain_budget', 'transition_horizon', 'tax_assumptions'} <= set(r['missing_context'])
    assert 'portfolio_reference' not in r['missing_context']
    assert r['plan_status'] == 'PROVISIONAL_MISSING_BINDINGS'
    plan = r['capability_route']
    validate_graph(plan['nodes'], plan['context'], plan['configuration'])
    lots = next(n for n in plan['nodes'] if n['function_id'] == 'evidence.tax_lots')
    assert lots['inputs']['portfolio_reference']['source'] == 'upstream'
    assert 'realized_gain_estimates' in plan['output_contract']['required_sections']
    safe = json.dumps(export_route(r))
    for text in ['Avery Example', 'avery@example.test', '999-00123', '$750,000']:
        assert text not in safe


@pytest.mark.parametrize('query', [
    'Run overlap and transition tax impact for this client.',
    'Show concentration and correlation for this client.',
])
def test_unsupported_compositions_have_no_graph(query):
    r = route_request(query)
    assert r['capability_status'] == 'CAPABILITY_GAP'
    assert r['support_level'] == 'UNSUPPORTED'
    assert r['capability_route']['nodes'] == []
    assert r['uncovered_intents']


def test_known_scope_missing_identity_preserves_provisional_plan():
    r = route_request('Draft an email about recent volatility for this client.')
    assert r['plan_status'] == 'PROVISIONAL_MISSING_BINDINGS'
    assert r['capability_route']['nodes']


def test_available_never_means_verified_or_execution_ready():
    context = {k: {'status': 'AVAILABLE', 'source': 'host_application'}
               for k in ['security_reference', 'analysis_period', 'actor_context', 'as_of']}
    r = route_request('How has credit spread moved for this issue, and what is driving it?', context=context)
    exported = export_route(r)
    assert exported['schema_version'] == '5.1'
    assert exported['verification_status'] == 'UNVERIFIED'
    assert not exported['execution_ready']
    for n in exported['capability_route']['nodes']:
        assert n['verification_status'] == 'UNVERIFIED'
        assert not n['execution_ready'] and not n['invoked']


def test_catalog_ids_and_workflow_versions_match_runtime():
    catalog = {c['id']: c for c in capability_catalog()}
    assert 'analysis.explanation_package' not in catalog
    r = route_request(TAX)
    assert r['workflow_id'] == catalog[r['capability_id']]['workflow_id']


def test_context_requirements_are_separate_from_user_clarification():
    context = {k: {'status': 'AVAILABLE', 'source': 'host_application'}
               for k in ['security_reference', 'analysis_period', 'actor_context', 'as_of']}
    ready = route_request('How has credit spread moved for this issue?', context=context)
    assert {'security_reference', 'analysis_period', 'actor_context', 'as_of'} <= set(ready['context_requirements'])
    assert ready['clarification_required'] == []
    assert ready['missing_context'] == ready['clarification_required']
    assert ready['deprecated_fields']['missing_context'].startswith('Use clarification_required')

    needs_user = route_request('Draft an email about volatility for this client.')
    assert needs_user['clarification_required'] == ['client_reference']
    assert needs_user['decision'] == 'CLARIFY'


def test_negated_proposal_does_not_activate_specialization():
    r = route_request('Do not prepare a proposal. Show concentration for this client.')
    assert r['capability_id'] != 'portfolio.tax_aware_concentration_transition'


def test_runtime_modes_keep_unknown_provenance_and_report_support():
    cases = [{'id': 'a', 'query': 'Explain credit spread movement for this issue.'}]
    for mode in ['hybrid', 'rules_only']:
        report = route_suite(cases, mode=mode)
        assert 'unknown' in report['provenance_decisions']
        assert report['support_distribution']
        assert report['mode'] == mode


def test_evaluation_does_not_claim_accuracy_or_feed_labels_to_router():
    from wealth_intent.outcome_evaluation import evaluate_outcomes
    case = {'id': 'x', 'query': 'Explain credit spread movement for this issue.',
            'expected_route': {'intents': ['content.draft']}, 'provenance': 'unknown'}
    r = evaluate_outcomes([case])
    for config in r['reports']:
        stratum = config['strata'][0]
        assert stratum['reviewed_cases'] == 0
        assert stratum['exact_route_matches'] is None
        assert 'research.credit_spread_explanation' in stratum['capabilities']
