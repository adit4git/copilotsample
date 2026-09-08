import json
import pytest
from wealth_intent.classifier import IntentClassifier, safe_export
from wealth_intent.corpus import prepare_cases, apply_annotations, metadata_rows
from wealth_intent.datasets import evaluate, import_suite, load_demo_suite
from wealth_intent.capabilities import compile_capability_plan, match_capability


@pytest.fixture(scope="module")
def classifier():
    return IntentClassifier()


def case(query="Run overlap analysis.", **extra):
    return dict(id="test", query=query, expected_intents=["portfolio.overlap"], **extra)


def test_separate_evidence(classifier):
    r=classifier.classify("Run overlap analysis.")
    assert r["rule_decisions"]
    assert all("score" not in c for c in r["candidates"])
    assert r["settings_status"] == "unvalidated_placeholders"
    assert len(r["registry_digest"]) == 16


def test_more_than_five_tasks_retained(classifier):
    r=classifier.classify("Run overlap analysis. Calculate correlation. Explain performance. Retrieve maturity terms. Find a wholesaler. Draft an email.")
    assert len(r["intents"]) >= 6
    assert "five" not in r["reason"]


def test_clause_specificity_retains_separate_guidance(classifier):
    r=classifier.classify("What changed in CIO guidance? Retrieve the current CIO outlook.")
    assert {"research.change","research.cio"} <= set(r["intents"])


def test_negation_local_to_clause(classifier):
    r=classifier.classify("Do not draft an email. Run overlap analysis.")
    assert "content.draft" not in r["intents"]
    assert "portfolio.overlap" in r["intents"]
    assert any(x['decision']=='negation_veto' for x in r['rule_decisions'])


def test_product_code_invariance(classifier):
    a=classifier.classify("What are the maturity terms for MLAAA?")
    b=classifier.classify("What are the maturity terms for MLZZZ?")
    assert a['intents']==b['intents']
    assert a['candidates']==b['candidates']


def test_trace_export_has_no_raw_text(classifier):
    r=classifier.classify("secretaliasomega wants overlap. Email is private@example.test.")
    out=json.dumps(safe_export(r))
    assert 'secretaliasomega' not in out and 'private@example.test' not in out


def test_thread_confirmation_and_quarantine():
    a=case(id_unused="unused", suggested_thread="g", source_rows=[43])
    b=case("Explain reporting.", suggested_thread="g", source_rows=[44])
    assert all(c['quarantined'] for c in prepare_cases([a,b]))
    p=prepare_cases([a,b],True)
    assert len(p)==1 and p[0]['source_rows']==[43,44]
    assert not p[0]['independent_review']
    b.update(quarantined=True,quarantine_reasons=['incomplete_source_transcription'])
    assert prepare_cases([a,b],True)[0]['quarantined']


def test_duplicate_conflicting_labels_quarantined():
    a=case()
    b=case()
    b['expected_intents']=['tax.transition']
    p=prepare_cases([a,b])
    assert len(p)==1 and p[0]['quarantined']


def test_fixtures_never_accuracy(classifier):
    p=load_demo_suite()[:2]
    for c in p:
        c.update(annotation_status='adjudicated',independent_review=True,provenance='advisor_email')
    r=evaluate(p,classifier)
    assert r['summary']['reviewed_cases']==0
    assert all(x['required_label_recall'] is None for x in r['strata'])


def test_exhaustive_empty_set_is_scored(classifier):
    p=case('Purple elephants paint teapots.', annotation_status='adjudicated',independent_review=True,
           label_semantics='exhaustive',provenance='advisor_email')
    p['expected_intents']=[]
    r=evaluate([p],classifier)
    assert r['summary']['reviewed_cases']==1
    assert r['strata'][0]['exact_set_rate']==1
    assert r['strata'][0]['exact_set_wilson_95'] is not None


def test_provenance_not_length(classifier):
    p=case('Hello. '*100+'Run overlap analysis.',annotation_status='unlabeled')
    r=evaluate([p],classifier)
    assert all(s['provenance']=='unknown' and s['length_band']=='over_400' for s in r['strata'])


def test_required_labels_not_exact_metrics(classifier):
    p=case(annotation_status='adjudicated',independent_review=True,provenance='advisor_email',label_semantics='required')
    r=evaluate([p],classifier)
    assert r['strata'][0]['required_label_recall']==1
    assert r['strata'][0]['exact_set_rate'] is None
    assert {x['mode'] for x in r['rows']}=={'hybrid','rules_only'}


def test_quarantine_not_evaluated(classifier):
    r=evaluate([case(quarantined=True)],classifier)
    assert r['summary']['evaluated_cases']==0
    assert r['summary']['quarantined_cases']==1


def test_annotation_contract():
    p=prepare_cases([case()])
    rows=metadata_rows(p)
    rows[0].update(annotation_status='adjudicated',independent_review=True,provenance='advisor_email')
    assert apply_annotations(p,rows)[0]['independent_review']
    rows[0]['expected_intents']='invented_service'
    with pytest.raises(ValueError):apply_annotations(p,rows)


def test_csv_review_metadata(classifier):
    csv=b'query,expected_intents,annotation_status,independent_review,provenance,label_semantics\nRun overlap analysis.,portfolio.overlap,adjudicated,true,advisor_email,exhaustive\n'
    p=import_suite(csv,'reviewed.csv')
    assert evaluate(p,classifier)['summary']['reviewed_cases']==1


def test_unrecognized_workbook_does_not_get_hardcoded_threads():
    # CSV row count/column naming alone must not activate source-specific links.
    p=import_suite(('query\n'+'Find a wholesaler.\n'*50).encode(),'different.csv')
    assert not any(c['suggested_thread'] for c in p)


def test_sidecar_roundtrip_and_binding():
    import csv,io
    p=prepare_cases([case()])
    rows=metadata_rows(p)
    stream=io.StringIO()
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
    writer.writeheader();writer.writerows(rows)
    restored=list(csv.DictReader(io.StringIO(stream.getvalue())))
    assert apply_annotations(p,restored)[0]['independent_review'] is False
    p[0]['query']='A changed request'
    with pytest.raises(ValueError,match='different corpus'):
        apply_annotations(p,restored)


def test_labeled_scope_and_clarification(classifier):
    p=case('Purple elephants paint teapots.',annotation_status='adjudicated', independent_review=True,
           label_semantics='exhaustive',provenance='advisor_email',expected_scope='general',expected_decision='CLARIFY')
    p['expected_intents']=[]
    report=evaluate([p],classifier)
    assert all(s['scope_accuracy']==1 and s['decision_accuracy']==1 for s in report['strata'])


def test_invalid_thresholds(classifier):
    for threshold in [float('nan'),float('inf'),-1]:
        with pytest.raises(ValueError):classifier.classify('Run overlap analysis.',threshold=threshold)


def test_client_draft_returns_context_contract(classifier):
    result = classifier.classify("Draft an email about recent volatility for this client.")
    assert result["intents"] == ["content.draft"]
    assert result["scope"] == "account_or_client"
    assert result["context_requirements"] == [
        "client_reference", "client_profile", "portfolio_exposure",
        "communication_preferences", "approved_market_content",
    ]
    assert result["context_actions"] == [
        "resolve_client", "check_advisor_entitlement", "retrieve_relevant_client_context",
    ]
    assert result["missing_context"] == ["client_reference"]
    assert result["decision"] == "CLARIFY"


def test_trusted_client_binding_allows_preview_without_identity(classifier):
    result = classifier.classify(
        "Draft an email about recent volatility for this client.",
        trusted_context=("client_reference",),
    )
    assert result["missing_context"] == []
    assert result["decision"] == "ROUTE_PREVIEW"
    exported = safe_export(result)
    assert "client_reference" in exported["context_requirements"]
    assert "trusted_context" not in exported


def test_account_in_query_is_not_trusted_binding(classifier):
    result = classifier.classify("Draft an email for account 999-00123.")
    assert result["scope"] == "account_or_client"
    assert result["missing_context"] == ["client_reference"]
    assert result["decision"] == "CLARIFY"


def test_context_binding_allowlist(classifier):
    with pytest.raises(ValueError, match="unsupported binding"):
        classifier.classify("Draft an email for this client.", trusted_context=("client_name",))


def test_client_market_update_compiles_registered_dag(classifier):
    result = classifier.classify("Draft an email about recent volatility for this client.")
    plan = compile_capability_plan(result)
    assert plan["capability_id"] == "communication.client_market_update"
    assert plan["workflow_id"] == "client_market_update.v1"
    by_id = {node["id"]: node for node in plan["nodes"]}
    assert by_id["resolve_client"]["status"] == "NEEDS_INPUT"
    assert by_id["retrieve_market_content"]["status"] == "PLANNED"
    assert by_id["draft"]["status"] == "BLOCKED"
    assert set(by_id["prepare_model_input"]["depends_on"]) == {
        "read_client_context", "retrieve_market_content",
    }
    assert plan["execution_enabled"] is False


def test_trusted_binding_unblocks_preview_dag(classifier):
    result = classifier.classify(
        "Draft an email about recent volatility for this client.",
        trusted_context=("client_reference",),
    )
    plan = compile_capability_plan(result)
    assert all(node["status"] == "PLANNED" for node in plan["nodes"])
    assert plan["execution_enabled"] is False


def test_model_function_accepts_only_prepared_context(classifier):
    result = classifier.classify(
        "Draft an email about recent volatility for this client.",
        trusted_context=("client_reference",),
    )
    draft = next(node for node in compile_capability_plan(result)["nodes"]
                 if node["function_id"] == "content.draft")
    assert draft["execution_class"] == "bounded_model"
    assert draft["access_path"] == "model_gateway_pii_blocked"
    assert draft["required_inputs"] == ["model_safe_context"]
    assert draft["pii_policy"] == "no_raw_pii"


def test_book_screening_and_capability_gap(classifier):
    screening = compile_capability_plan(
        classifier.classify("Which clients qualify for alts but do not currently use them?")
    )
    assert screening["capability_id"] == "book.household_screening"
    assert screening["nodes"][0]["missing_inputs"] == ["advisor_book_scope"]
    gap = match_capability(classifier.classify("What is the current CIO view on rates?"))
    assert gap["status"] == "CAPABILITY_GAP"
    assert gap["capability_id"] is None
