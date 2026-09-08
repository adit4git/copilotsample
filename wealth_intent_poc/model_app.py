"""Run: python -m streamlit run model_app.py"""
import os
import json
import streamlit as st
from wealth_intent.abstraction import prepare_semantic_input
from wealth_intent.remote_semantic import route_remote, RemoteSemanticError
from wealth_intent.runtime import export_route
from wealth_intent.semantic import CONTEXT_TYPES

st.set_page_config(page_title='Wealth Intent — Models', layout='wide')
st.title('Wealth Intent — Model-based interpretation')
st.caption('POC 0.8.3 · API model interprets the request · governed code builds a preview DAG · no functions execute')
provider = st.sidebar.selectbox('Provider', ['openai','anthropic'])
response_mode = st.sidebar.selectbox('Anthropic response mode', ['tool','json_schema'], format_func=lambda x: 'Compatibility (tool response)' if x == 'tool' else 'Native JSON schema') if provider == 'anthropic' else 'json_schema'
env_name = 'OPENAI_API_KEY' if provider == 'openai' else 'ANTHROPIC_API_KEY'
key = st.sidebar.text_input('API key (or set '+env_name+')', type='password', key=provider+'_key') or os.getenv(env_name,'')
model = st.sidebar.text_input('Model ID', value=os.getenv('OPENAI_MODEL' if provider == 'openai' else 'ANTHROPIC_MODEL',''), key=provider+'_model')
st.sidebar.caption('One paid API call per classification; no automatic retries. Keys stay in local process/session memory.')
query = st.text_area('Advisor request — masked locally before the model call', height=120)
terms = st.text_area('Sensitive names or firm terms to remove, one per line', height=70)
outbound = prepare_semantic_input(query, terms.splitlines())['text']
st.caption('Masking is heuristic and may miss PII or confidential details.')
st.text_area('Exact masked request text sent to the selected provider', value=outbound, height=140, disabled=True)
with st.form('model_request'):
    mode = st.selectbox('Flagging interpretation', ['unspecified','one_time','recurring'])
    available = st.multiselect('Available context types (simulation; no values sent)', sorted(CONTEXT_TYPES))
    run = st.form_submit_button('Classify with selected model')
if run:
    st.session_state.pop('last_result',None)
    try:
        context = {k:{'status':'AVAILABLE','source':'host_application'} for k in available}
        with st.spinner('Interpreting request and validating the plan…'):
            result = route_remote(outbound, provider=provider, model=model, api_key=key, context=context, monitor_mode=mode, anthropic_response_mode=response_mode)
        st.session_state['last_result'] = export_route(result)
        st.session_state['last_sent_text'] = outbound
    except RemoteSemanticError as exc:
        st.error(str(exc))
    except Exception:
        st.error('Validation or planning failed. No executable action was taken.')
result = st.session_state.get('last_result')
if result:
    st.caption('Masked request sent for the result below')
    st.code(st.session_state['last_sent_text'], language=None)
    st.write('Decision:', result['decision'])
    st.write('Intents:', result['intents'])
    st.write('Capability:', result['capability_id'])
    st.write('Clarification required:', result['clarification_required'])
    nodes = result['capability_route']['nodes']
    if nodes:
        lines = ['digraph G {','rankdir=TB;','node [shape=box];']
        for node in nodes:
            lines.append(json.dumps(node['id'])+' [label='+json.dumps(node['function_id']+'\\n'+node['status'])+'];')
            lines.extend(json.dumps(dep)+' -> '+json.dumps(node['id'])+';' for dep in node['depends_on'])
        st.graphviz_chart('\n'.join(lines+['}']))
    st.json(result)
    st.download_button('Download typed JSON',json.dumps(result,indent=2),'model_request.json','application/json')
