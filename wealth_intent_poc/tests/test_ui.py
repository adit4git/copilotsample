from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def app():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    return at


def button(at, label):
    return next(b for b in at.button if b.label == label)


def test_classify_ui_and_privacy():
    at = app()
    at.text_area(key="query").set_value("Client Avery Example, account 999-00123: run overlap and transition tax impact.")
    button(at, "Classify request").click().run()
    assert not at.exception
    r = at.session_state["result"]
    assert {"portfolio.overlap", "tax.transition"} <= set(r["intents"])
    assert "999-00123" not in r["masked_text"]
    assert len(at.dataframe) >= 3


def test_client_context_ui():
    at = app()
    at.text_area(key="query").set_value("Draft an email about recent volatility for this client.")
    button(at, "Classify request").click().run()
    assert at.session_state["result"]["decision"] == "CLARIFY"
    assert at.session_state["result"]["missing_context"] == ["client_reference"]
    next(x for x in at.checkbox if x.label.startswith("A trusted client")).check().run()
    button(at, "Classify request").click().run()
    assert at.session_state["result"]["decision"] == "ROUTE_PREVIEW"
    assert at.session_state["result"]["missing_context"] == []


def test_capability_dag_and_registry_ui():
    at = app()
    at.text_area(key="query").set_value("Draft an email about recent volatility for this client.")
    button(at, "Classify request").click().run()
    assert not at.exception
    assert any("communication.client_market_update" in metric.value for metric in at.metric)
    at.radio(key="page").set_value("Capability registry").run()
    assert not at.exception
    at.selectbox(key="registry_capability").set_value("research.credit_spread_explanation").run()
    assert not at.exception
    assert at.selectbox(key="registry_capability").value == "research.credit_spread_explanation"
    assert at.selectbox(key="registry_function").value == "account_or_client.resolve"


def test_batch_ui():
    at = app()
    at.radio(key="page").set_value("Test a query suite").run()
    button(at, "Apply annotation metadata").click().run()
    assert not at.exception
    button(at, "Run suite").click().run()
    assert not at.exception
    assert at.session_state["batch"]["summary"]["cases"] == 153
    assert at.session_state["batch"]["summary"]["reviewed_cases"] == 0
    assert at.session_state['outcome_batch']['inference_columns'] == ['query']
    at.checkbox(key="missing_only").check().run()
    assert not at.exception


def test_attachment_simulation_changes_context_not_intent():
    at = app()
    at.text_area(key='query').set_value('How has credit spread moved for this issue, and what is driving it?')
    button(at, 'Classify request').click().run()
    assert at.session_state['result']['decision'] == 'CLARIFY'
    at.selectbox(key='attachment_state').set_value('Instrument and period identified')
    at.checkbox(key='host_present').check()
    button(at, 'Classify request').click().run()
    r = at.session_state['result']
    assert r['decision'] == 'ROUTE_PREVIEW'
    assert r['intents'] == ['research.security']
    assert r['missing_context'] == []
    at.selectbox(key='attachment_state').set_value('Conflicting instruments')
    button(at, 'Classify request').click().run()
    assert at.session_state['result']['decision'] == 'REVIEW'
    assert not at.exception


def test_flagging_mode_ui():
    at = app()
    at.text_area(key='query').set_value('Flag major estimate revisions for top holdings across my prioritized clients.')
    at.selectbox(key='monitoring_mode').set_value('one_time')
    button(at, 'Classify request').click().run()
    r = at.session_state['result']
    assert r['scope'] == 'subject_set'
    assert 'monitor.manage' not in r['intents']
    assert 'monitoring_cadence' not in r['context_requirements']
    assert not at.exception


def test_annotation_protocol_ui():
    at = app()
    at.radio(key="page").set_value("Annotation protocol").run()
    assert not at.exception
    assert any("three independent reviewers" in m.value for m in at.markdown)


def test_semantic_corpus_ui():
    at = app()
    at.radio(key="page").set_value("Semantic corpus").run()
    assert not at.exception
    values = {m.label: m.value for m in at.metric}
    assert values["Records"] == "242"
    assert values["Training eligible"] == "0"
    assert any(b.label == "Download annotation template CSV" for b in at.download_button)


def test_ambiguous_monitor_ui_has_question_and_no_graph():
    at = app()
    at.text_area(key='query').set_value('Flag major estimate revisions for top holdings across my prioritized clients.')
    button(at, 'Classify request').click().run()
    assert not at.exception
    assert at.session_state['result']['capability_route']['nodes'] == []
    assert any('one-time' in w.value for w in at.warning)


def test_tax_proposal_simulation_stays_unverified():
    at = app()
    at.text_area(key='query').set_value('Prepare a tax-aware transition proposal for concentrated stock for this client.')
    next(x for x in at.checkbox if x.label.startswith('A trusted client')).check()
    at.checkbox(key='host_present').check()
    at.multiselect(key='resolved_types').set_value(['gain_budget', 'transition_horizon', 'tax_assumptions',
                                                  'comparison_targets', 'client_objectives', 'client_constraints'])
    button(at, 'Classify request').click().run()
    assert not at.exception
    result = at.session_state['result']
    assert result['output'] == 'tax_aware_transition_proposal'
    assert result['missing_context'] == []
    assert result['verification_status'] == 'UNVERIFIED'
    assert not result['execution_ready']


def test_registry_ui_and_clear():
    at = app()
    at.radio(key="page").set_value("Intent registry").run()
    at.selectbox(key="registry_intent").set_value("tax.transition").run()
    assert not at.exception
    button(at, "Clear session data").click().run()
    assert not at.exception
    assert at.radio(key="page").value == "Classify a request"
