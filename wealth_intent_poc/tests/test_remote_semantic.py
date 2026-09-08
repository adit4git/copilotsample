import json
import pytest
from unittest.mock import Mock, patch
from wealth_intent.remote_semantic import route_remote, interpret_remote, RemoteSemanticError


def frame():
    return dict(intents=['research.cio'],scope='general',subject_selection='unspecified',
                requested_effect='read_only',goal='fulfill_registered_tasks',output='cited_answer',
                audience='advisor',metric=None,requires_source_content=False,ambiguous_fields=[])


@pytest.mark.parametrize('provider',['openai','anthropic'])
def test_provider_payload_and_primary_interpretation(provider):
    response = Mock(status_code=200)
    response.json.return_value = ({'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps(frame())}]}]}
        if provider=='openai' else {'stop_reason':'tool_use','content':[{'type':'tool_use','name':'emit_semantic_frame','input':frame()}]})
    with patch('wealth_intent.remote_semantic.requests.post',return_value=response) as post:
        r=route_remote('Explain investment office thinking',provider=provider,model='test-model',api_key='test-secret')
    assert r['intents']==['research.cio']
    assert r['capability_id']=='research.cio_guidance'
    assert r['decision']=='ROUTE_PREVIEW'
    assert r['egress']['outbound_requests']==1
    assert r['semantic_engine']['deterministic_parser']=='disabled_model_primary'
    assert 'test-secret' not in json.dumps(r)
    payload=post.call_args.kwargs['json']
    assert ('text' in payload) if provider=='openai' else ('tools' in payload)


def test_empty_masked_text_never_sent():
    with patch('wealth_intent.remote_semantic.requests.post') as post:
        with pytest.raises(RemoteSemanticError):
            interpret_remote('',provider='openai',model='test',api_key='secret')
        post.assert_not_called()


def test_invalid_or_failed_responses_never_compile_or_echo_payload():
    for status, body in [(401,{}),(200,{'status':'incomplete'}),(200,{'status':'completed','output':[]})]:
        response=Mock(status_code=status)
        response.json.return_value=body
        with patch('wealth_intent.remote_semantic.requests.post',return_value=response):
            with pytest.raises(RemoteSemanticError) as caught:
                route_remote('sensitive request',provider='openai',model='test',api_key='secret')
            assert 'sensitive request' not in str(caught.value)
            assert 'secret' not in str(caught.value)


def test_ambiguity_blocks_dag_and_scope_contract_rejects_unknown_intent():
    from wealth_intent.runtime import route_request
    f=frame(); f['ambiguous_fields']=['scope']
    r=route_request('arbitrary wording',model_frame=f)
    assert r['decision']=='CLARIFY' and not r['capability_route']['nodes']
    f['intents']=['invented.tool']
    with pytest.raises(Exception):
        route_request('arbitrary wording',model_frame=f)


def test_model_ui_starts_without_keys():
    from streamlit.testing.v1 import AppTest
    from pathlib import Path
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'model_app.py')).run()
    assert not app.exception


def test_ui_sends_preview_without_confirmation():
    from streamlit.testing.v1 import AppTest
    from pathlib import Path
    from wealth_intent.abstraction import prepare_semantic_input
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'model_app.py')).run()
    query='Client Avery Example, email avery@example.test, account 999-00123, has $750,000. Explain CIO thinking.'
    app.text_area[0].input(query).run()
    expected=prepare_semantic_input(query, [])['text']
    assert app.text_area[2].value == expected
    assert 'avery@example.test' not in expected
    assert not app.checkbox
    with patch('wealth_intent.remote_semantic.route_remote', side_effect=RemoteSemanticError('Mock provider error')) as route:
        app.button[0].click().run()
    assert not app.exception
    assert route.call_args.args[0] == expected
    assert 'approved' not in route.call_args.kwargs


@pytest.mark.parametrize('status,kind,message,category', [
    (400, 'invalid_request_error', 'Your credit balance is too low to access the Anthropic API.', 'BILLING_OR_SPEND_LIMIT'),
    (400, 'invalid_request_error', 'Workspace spend limit reached.', 'BILLING_OR_SPEND_LIMIT'),
    (400, 'invalid_request_error', 'output_config: Schema is too complex for compilation.', 'STRUCTURED_OUTPUT_REQUEST'),
    (400, 'invalid_request_error', 'model is not supported', 'MODEL_OR_RESOURCE'),
    (401, 'authentication_error', 'Invalid key', 'AUTHENTICATION'),
    (403, 'permission_error', 'Access denied', 'PERMISSION'),
    (429, 'rate_limit_error', 'Too many requests', 'RATE_LIMIT'),
    (529, 'overloaded_error', 'Overloaded', 'PROVIDER_SERVICE'),
    (400, 'invalid_request_error', 'Unknown request issue', 'REQUEST_REJECTED'),
])
def test_provider_error_diagnostics_do_not_echo_sensitive_details(status, kind, message, category):
    response = Mock(status_code=status)
    response.json.return_value = {'error': {'type':kind, 'message':message + ' private@example.test secret-key'}}
    with patch('wealth_intent.remote_semantic.requests.post', return_value=response) as post:
        with pytest.raises(RemoteSemanticError) as caught:
            route_remote('find me cio views around energy and how it impacts my top holdings',
                         provider='anthropic',model='test-model',api_key='secret-key')
    assert category in str(caught.value)
    assert 'private@example.test' not in str(caught.value)
    assert 'secret-key' not in str(caught.value)
    assert 'top holdings' not in str(caught.value)
    assert post.call_count == 1


def test_non_json_provider_error_remains_diagnostic():
    from wealth_intent.remote_semantic import provider_error_message
    response = Mock(status_code=400)
    response.json.side_effect = ValueError('private content')
    assert 'REQUEST_REJECTED' in provider_error_message(response, 'anthropic')
    assert 'private content' not in provider_error_message(response, 'anthropic')


def test_anthropic_native_mode_preserved():
    response=Mock(status_code=200)
    response.json.return_value={'stop_reason':'end_turn','content':[{'type':'text','text':json.dumps(frame())}]}
    with patch('wealth_intent.remote_semantic.requests.post',return_value=response) as post:
        result=interpret_remote('CIO outlook',provider='anthropic',model='test',api_key='secret',anthropic_response_mode='json_schema')
    assert result == frame()
    assert 'output_config' in post.call_args.kwargs['json']
    assert 'tools' not in post.call_args.kwargs['json']


def test_anthropic_tool_mode_is_data_only_and_retains_local_validation():
    response=Mock(status_code=200)
    response.json.return_value={'stop_reason':'tool_use','content':[{'type':'tool_use','name':'emit_semantic_frame','input':frame()}]}
    with patch('wealth_intent.remote_semantic.requests.post',return_value=response) as post:
        r=route_remote('CIO outlook',provider='anthropic',model='test',api_key='secret')
    body=post.call_args.kwargs['json']
    assert 'output_config' not in body
    assert 'strict' not in body['tools'][0]
    assert body['tool_choice']=={'type':'tool','name':'emit_semantic_frame','disable_parallel_tool_use':True}
    assert len(body['tools'])==1 and post.call_count==1
    assert not r['execution_enabled'] and not r['egress']['tool_execution_enabled']
    assert r['semantic_engine']['response_mode']=='tool'
    assert all(not n['invoked'] for n in r['capability_route']['nodes'])


@pytest.mark.parametrize('case',['wrong_name','multiple','invalid_enum','truncated','no_tool'])
def test_invalid_anthropic_tool_response_never_plans(case):
    f=frame()
    blocks=[{'type':'tool_use','name':'emit_semantic_frame','input':f}]
    stop='tool_use'
    if case=='wrong_name': blocks[0]['name']='execute_trade'
    if case=='multiple': blocks=blocks*2
    if case=='invalid_enum': f['intents']=['execute.trade']
    if case=='truncated': stop='max_tokens'
    if case=='no_tool': blocks=[]
    response=Mock(status_code=200)
    response.json.return_value={'stop_reason':stop,'content':blocks}
    with patch('wealth_intent.remote_semantic.requests.post',return_value=response) as post:
        with pytest.raises(RemoteSemanticError):
            route_remote('CIO outlook',provider='anthropic',model='test',api_key='secret')
    assert post.call_count==1
