"""Contract tests: no oracle-label inputs, no egress, and no missing input bypass."""
import copy
import json
import socket
import pytest
from wealth_intent.classifier import IntentClassifier
from wealth_intent.datasets import import_suite
from wealth_intent.runtime import route_request, export_route, route_suite
from wealth_intent.planning import validate_graph, FUNCTIONS

CREDIT = 'How has credit spread moved for this issue, and what is driving it?'
EMAIL = 'Draft an email about recent volatility for this client.'
FLAGS = 'Flag major estimate revisions for top holdings across my prioritized clients.'


@pytest.fixture(scope='module')
def classifier():
    return IntentClassifier()


def context(*names, source='host_application', status='AVAILABLE'):
    return {name: {'status': status, 'source': source} for name in names}


def route(q, classifier, **kw):
    return route_request(q, classifier=classifier, **kw)


def test_query_only_and_no_business_label_inputs(classifier):
    r = route(CREDIT, classifier)
    assert r['capability_id'] == 'research.credit_spread_explanation'
    assert r['scope'] == 'security_or_instrument'
    assert r['goal'] == 'explain_credit_spread_change'
    assert set(r['missing_context']) == {'security_reference', 'analysis_period'}
    for key in ['problem_solved', 'investment_agent_output', 'section']:
        with pytest.raises(TypeError):
            route(CREDIT, classifier, **{key: 'Force monitor output'})
        with pytest.raises(ValueError):
            route(CREDIT, classifier, context={key: {'status': 'AVAILABLE', 'source': 'attachment'}})


def test_business_columns_do_not_change_inference(classifier):
    import csv, io
    reports = []
    for problem, output in [('Explain a signal', 'Cited explanation'), ('Create a monitor', 'Execute a trade')]:
        s = io.StringIO()
        writer = csv.writer(s)
        writer.writerow(['Advisor Query Example', 'Problem Solved', 'Investment Agent Output'])
        writer.writerow([CREDIT, problem, output])
        cases = import_suite(s.getvalue().encode(), 'test.csv')
        assert not any(key in cases[0] for key in ['Problem Solved', 'Investment Agent Output'])
        result = route_suite(cases, classifier=classifier)['rows'][0]['result']
        result.pop('latency_ms')
        reports.append(result)
    assert reports[0] == reports[1]


def test_attachment_present_is_not_resolved_instrument(classifier):
    r = route(CREDIT, classifier, context=context('attachment_reference', source='attachment'))
    assert r['context_state']['security_reference']['status'] == 'PENDING_RESOLUTION'
    assert r['context_state']['analysis_period']['status'] == 'PENDING_RESOLUTION'
    assert all(n['status'] != 'PLANNED' for n in r['capability_route']['nodes'])


def test_resolved_instrument_does_not_invent_period(classifier):
    r = route(CREDIT, classifier, context=context('security_reference', source='attachment'))
    assert r['missing_context'] == ['analysis_period']


def test_attachment_resolved_context_compiles_without_client_data(classifier):
    ctx = context('security_reference', 'analysis_period', source='attachment')
    ctx.update(context('actor_context', 'as_of'))
    r = route(CREDIT, classifier, context=ctx)
    assert r['decision'] == 'ROUTE_PREVIEW'
    assert r['missing_context'] == []
    assert all(n['status'] == 'PLANNED' for n in r['capability_route']['nodes'])
    assert not r['execution_enabled']
    assert all(e['status'] == 'PENDING_RETRIEVAL' for e in r['evidence_requirements'])
    assert not any('client_reference' in n['required_inputs'] for n in r['capability_route']['nodes'])


@pytest.mark.parametrize('status', ['CONFLICT', 'UNAVAILABLE'])
def test_attachment_conflict_or_unavailable_blocks(classifier, status):
    ctx = context('security_reference', source='attachment', status=status)
    r = route(CREDIT, classifier, context=ctx)
    assert r['decision'] == 'REVIEW'
    assert any(n['status'] == status for n in r['capability_route']['nodes'])


def test_household_has_own_resolver_and_blocks(classifier):
    r = route('Draft an email about volatility for this household.', classifier)
    assert r['scope'] == 'household'
    assert r['missing_context'] == ['household_reference']
    resolver = next(n for n in r['capability_route']['nodes'] if n['function_id'] == 'household.resolve')
    assert resolver['status'] == 'NEEDS_INPUT'
    assert not any(n['function_id'] == 'account_or_client.resolve' for n in r['capability_route']['nodes'])


def test_client_flag_does_not_satisfy_actor_or_time(classifier):
    r = route(EMAIL, classifier, context=context('client_reference'))
    assert r['decision'] == 'ROUTE_PREVIEW'
    assert r['context_state']['actor_context']['status'] == 'PENDING_RESOLUTION'
    assert r['context_state']['as_of']['status'] == 'PENDING_RESOLUTION'
    assert any(n['status'] == 'PENDING_CONTEXT' for n in r['capability_route']['nodes'])
    assert any(n['status'] == 'BLOCKED' for n in r['capability_route']['nodes'])


def test_client_book_and_prioritized_holdings_relationship(classifier):
    r = route('Is today’s tech selloff going to impact my client book?', classifier)
    assert r['scope'] == 'subject_set'
    assert 'client_reference' not in r['context_requirements']
    r = route(FLAGS, classifier)
    assert r['scope'] == 'subject_set'
    assert r['requested_effect'] == 'ambiguous_monitor'
    assert 'monitor_mode' in r['missing_context']
    assert r['plan_status'] == 'NOT_COMPILED_SEMANTIC_CLARIFICATION'
    assert r['capability_route']['nodes'] == []
    resolved = route(FLAGS, classifier, monitor_mode='one_time')
    assert resolved['subject_selection'] == 'prioritized_clients'
    assert resolved['context_state']['subject_set_reference']['status'] == 'PENDING_RESOLUTION'
    assert any(n['function_id'] == 'subject_set.resolve' for n in resolved['capability_route']['nodes'])


def test_one_time_flagging_does_not_require_monitor_parameters(classifier):
    r = route(FLAGS, classifier, monitor_mode='one_time')
    assert 'monitor.manage' not in r['intents']
    assert r['requested_effect'] == 'read_only'
    assert not set(r['context_requirements']) & {'monitor_mode', 'monitoring_cadence', 'delivery_channel'}


def test_recurring_monitor_has_explicit_inputs_and_no_effect(classifier):
    ctx = context('actor_context', 'as_of', 'subject_set_reference', 'prioritized_client_set',
                  'holding_selection', 'analysis_period', 'materiality_threshold',
                  'monitoring_cadence', 'delivery_channel')
    r = route(FLAGS, classifier, context=ctx, monitor_mode='recurring')
    assert r['decision'] == 'REVIEW'
    assert not r['execution_enabled']
    node = next(n for n in r['capability_route']['nodes'] if n['function_id'] == 'monitor.validate_specification')
    assert {'materiality_threshold', 'monitoring_cadence', 'delivery_channel'} <= set(node['inputs'])
    assert not any(n['function_class'] == 'write' for n in r['capability_route']['nodes'])


def test_voicemail_source_and_format(classifier):
    r = route('Turn this into three bullets I can say on a voicemail.', classifier)
    assert r['output'] == 'voicemail_bullets'
    assert r['capability_id'] == 'communication.content_transform'
    assert 'source_content' in r['missing_context']


def test_generic_enrollment_does_not_need_client(classifier):
    r = route('What are the steps to enroll in a PAS Account?', classifier)
    assert 'client_reference' not in r['context_requirements']
    assert r['requested_effect'] == 'read_only'


def test_scenario_has_registered_computation(classifier):
    r = route('Show before-and-after if we rebalance toward CIO targets, and explain the trade-offs.', classifier)
    assert r['goal'] == 'compare_rebalance_scenario'
    assert r['capability_id'] == 'portfolio.rebalance_scenario'
    assert any(n['function_id'] == 'portfolio.compare_scenario' for n in r['capability_route']['nodes'])


def test_no_arbitrary_action_capability(classifier):
    r = route('Buy this fund for my client.', classifier)
    assert r['capability_status'] == 'CAPABILITY_GAP'
    assert r['capability_route']['nodes'] == []


def test_compiler_rejects_invalid_edges_and_types(classifier):
    plan = route(EMAIL, classifier)['capability_route']
    def verify(nodes): validate_graph(nodes, plan['context'], plan['configuration'])
    verify(plan['nodes'])
    nodes = copy.deepcopy(plan['nodes']); nodes[0]['inputs'].clear()
    with pytest.raises(ValueError, match='typed function inputs'): verify(nodes)
    nodes = copy.deepcopy(plan['nodes']); nodes[0]['depends_on'] = [nodes[-1]['id']]
    with pytest.raises(ValueError, match='Dependency graph'): verify(nodes)
    nodes = copy.deepcopy(plan['nodes']); nodes[0]['function_id'] = 'invented.function'
    with pytest.raises(ValueError, match='Unregistered function'): verify(nodes)
    nodes = copy.deepcopy(plan['nodes'])
    last = nodes[-1]; last['inputs']['task_artifacts']['nodes'] = [nodes[0]['id']]
    with pytest.raises(ValueError, match='Incompatible producer'): verify(nodes)
    nodes = copy.deepcopy(plan['nodes'])
    last = nodes[-1]; last['inputs']['task_artifacts']['nodes'] = [last['id']]
    with pytest.raises(ValueError, match='Cycle'): verify(nodes)


def test_every_function_input_has_binding(classifier):
    for q in [EMAIL, CREDIT, FLAGS, 'Calculate overlap and transition tax impact for this client, then draft an email.']:
        plan = route(q, classifier)['capability_route']
        validate_graph(plan['nodes'], plan['context'], plan['configuration'])
        for node in plan['nodes']:
            assert set(node['inputs']) == set(FUNCTIONS[node['function_id']].inputs)


def test_no_network_or_pii_in_typed_export(classifier, monkeypatch):
    def fail(*args, **kwargs): raise AssertionError('Unexpected network use')
    monkeypatch.setattr(socket.socket, 'connect', fail)
    q = 'Client Avery Example, avery@example.test, account 999-00123: Draft an email about volatility for this client.'
    r = route(q, classifier)
    out = json.dumps(export_route(r))
    for value in ['Avery Example', 'avery@example.test', '999-00123']:
        assert value not in out
    assert r['egress']['outbound_requests'] == 0
    with pytest.raises(ValueError):
        route(CREDIT, classifier, context={'security_reference': {'status': 'AVAILABLE', 'source': 'attachment', 'value': 'sensitive'}})


def test_attachment_cannot_assert_actor_identity(classifier):
    with pytest.raises(ValueError, match='host application'):
        route(CREDIT, classifier, context=context('actor_context', source='attachment'))
