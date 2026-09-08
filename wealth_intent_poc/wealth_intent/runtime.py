"""Public query-only routing API. No workbook business labels or LLM egress."""
from time import perf_counter
from .classifier import IntentClassifier, safe_export
from .semantic import interpret, validate_context
from .planning import compile_plan, match, support_metadata
from .privacy import EgressGateway
from .abstraction import prepare_semantic_input
from .semantic_model import request_proposal, apply_proposal
from .semantic_contract import validate_semantic


def route_request(query, *, context=None, monitor_mode='unspecified', classifier=None,
                  sensitive_terms=(), threshold=0.23, margin=0.035, prior_intents=(), mode='hybrid',
                  semantic_model=None, semantic_model_threshold=.80, model_frame=None):
    """Context contains TYPE/status/source only. No labels, identifiers or content.

    AVAILABLE denotes a caller assertion in this POC, not verified entitlement.
    Unknown kwargs (including problem_solved and investment_agent_output) fail.
    """
    started = perf_counter()
    declared = validate_context(context)
    if monitor_mode not in {'unspecified', 'one_time', 'recurring'}:
        raise ValueError('Select a registered monitoring mode.')
    prepared = prepare_semantic_input(query, sensitive_terms)
    if model_frame is None:
        base = (classifier or IntentClassifier()).classify(
            query, sensitive_terms=sensitive_terms, threshold=threshold, margin=margin, mode=mode,
            prior_intents=prior_intents,
            trusted_context=tuple(k for k, v in declared.items() if v['status'] == 'AVAILABLE'
                                  and k in {'client_reference', 'household_reference', 'advisor_book_scope', 'practice_scope'}))
        semantic, inferred = interpret(base['masked_text'], base)
        proposal = request_proposal(semantic_model, prepared)
        semantic, model_applied_fields = apply_proposal(semantic, proposal, semantic_model_threshold)
    else:
        from .remote_semantic import validate_frame
        validate_frame(model_frame)
        base = dict(intents=[], scope='general', decision='MODEL_PRIMARY', reason='',
                    unresolved_clauses=[], followup=False)
        proposal, model_applied_fields, inferred = None, list(model_frame), {}
        semantic = dict(model_frame)
        semantic.pop('ambiguous_fields')
        semantic.update(semantic_parameters={}, monitor_lifecycle='create' if 'monitor.manage' in semantic['intents'] else None,
                        semantic_trace=[{'rule': 'catalog_model_primary'}])
    if 'monitor.manage' in semantic['intents']:
        if monitor_mode == 'one_time':
            semantic['intents'].remove('monitor.manage')
            if semantic['scope'] == 'advisor_book' and 'book.screen' not in semantic['intents']:
                semantic['intents'].append('book.screen')
            semantic['requested_effect'] = 'read_only'
            semantic['monitor_lifecycle'] = None
        elif monitor_mode == 'recurring':
            semantic['requested_effect'] = 'monitor_specification'
    semantic_issues = validate_semantic(semantic)
    refinement_resolved_empty_baseline = (not base['intents'] and bool(semantic['intents'])
                                          and bool(semantic['semantic_trace']))
    unresolved_interpretation = ((bool(base['unresolved_clauses']) and not refinement_resolved_empty_baseline)
                                 or not semantic['intents'] or bool(semantic_issues))
    if base['followup'] and not prior_intents:
        unresolved_interpretation = True
    questions = []
    if model_frame is not None:
        for field in model_frame['ambiguous_fields']:
            questions.append({'type': field, 'question': 'Please clarify the requested ' + field + '.'})
    if unresolved_interpretation:
        questions.append({'type': 'requested_tasks', 'question': 'Which unresolved task should this request perform?'})
    for issue in semantic_issues:
        questions.append({'type': issue['field'], 'question': 'Resolve semantic consistency issue: '+issue['code']+'.'})
    if semantic['requested_effect'] == 'ambiguous_monitor':
        questions.append({'type': 'monitor_mode', 'question': 'Is this a one-time analysis or recurring monitoring?'})
    if questions:
        capability, match_reason = match(semantic)
        states = {q['type']: {'status': 'NEEDS_CLARIFICATION', 'source': 'unspecified'} for q in questions}
        plan = {'mode': 'preview_only', 'match': {'status': 'MATCHED' if capability else 'CAPABILITY_GAP',
                 'reason': match_reason, 'candidates': []}, 'capability_id': capability,
                'workflow_id': None, 'nodes': [], 'context': states, 'context_requirements': list(states),
                'context_actions': [], 'clarification_required': list(states),
                'missing_context': list(states), 'access_paths': [],
                'configuration': {}, 'evidence_requirements': [], 'execution_enabled': False,
                'uncovered_intents': [] if capability else semantic['intents'], **support_metadata(capability)}
    else:
        plan = compile_plan(semantic, declared, inferred)
    plan['plan_status'] = ('NOT_COMPILED_SEMANTIC_CLARIFICATION' if questions else
                           'NOT_COMPILED_CAPABILITY_GAP' if not plan['capability_id'] else
                           'PROVISIONAL_MISSING_BINDINGS' if plan['clarification_required'] else 'PREVIEW_ONLY')
    context = plan['context']
    if base['decision'] == 'REVIEW' and base['reason'].startswith('Possible instruction override'):
        decision, reason = 'REVIEW', base['reason']
    elif any(v['status'] in {'CONFLICT', 'UNAVAILABLE'} for v in context.values()):
        decision, reason = 'REVIEW', 'Required context is conflicting or unavailable.'
    elif unresolved_interpretation or plan['clarification_required']:
        decision, reason = 'CLARIFY', 'Clarify unresolved request details or the listed missing context.'
    elif plan['match']['status'] == 'CAPABILITY_GAP':
        decision, reason = 'CAPABILITY_GAP', plan['match']['reason']
    elif semantic['requested_effect'] in {'monitor_specification', 'operational_action'}:
        decision, reason = 'REVIEW', 'Action-related specification requires governed review; nothing executes.'
    else:
        decision, reason = 'ROUTE_PREVIEW', 'Registered outcome and input bindings compiled; pending context and retrieval remain explicit.'
    # Preserve baseline evidence separately; the public decision and context are
    # derived once, from the semantic interpretation and compiled plan.
    output = dict(base)
    output.update(semantic)
    output['egress'] = EgressGateway.preview(semantic['intents'])
    output.update(schema_version='5.1', poc_version='0.7.0', decision=decision, reason=reason,
                  semantic_engine={'deterministic_parser': 'clause_role_parser.v1',
                    'model_provider': proposal.model_id if proposal else None,
                    'model_applied_fields': model_applied_fields,
                    'model_input': {k:v for k,v in prepared.items() if k != 'text'}},
                  semantic_validation=semantic_issues,
                  plan_status=plan['plan_status'], support_level=plan['support_level'],
                  verification_status='UNVERIFIED', execution_ready=False,
                  clarification_questions=questions, uncovered_intents=plan['uncovered_intents'],
                  context_requirements=plan['context_requirements'], context_actions=plan['context_actions'],
                  clarification_required=plan['clarification_required'],
                  missing_context=plan['clarification_required'],
                  deprecated_fields={'missing_context': 'Use clarification_required; retained through schema 5.x.'},
                  capability_status=plan['match']['status'],
                  capability_id=plan['capability_id'], workflow_id=plan['workflow_id'],
                  context_state=plan['context'], evidence_requirements=plan.get('evidence_requirements', []),
                  execution_enabled=False, capability_route=plan,
                  semantic_status='NEEDS_CLARIFICATION' if questions else 'INTERPRETED',
                  baseline={'intents': base['intents'], 'scope': base['scope'], 'decision': base['decision']},
                  input_contract='query_and_optional_typed_context_only',
                  latency_ms=round((perf_counter()-started)*1000, 1))
    return output


def export_route(result):
    """Allowlist typed results. Never export raw/masked queries or attachment data."""
    out = safe_export(result)
    for field in ('semantic_engine', 'semantic_validation', 'semantic_parameters',
                  'plan_status', 'support_level', 'verification_status', 'execution_ready',
                  'clarification_questions', 'uncovered_intents', 'poc_version', 'goal', 'audience', 'metric', 'subject_selection',
                  'clarification_required', 'deprecated_fields',
                  'semantic_status', 'semantic_trace', 'capability_status', 'capability_id',
                  'workflow_id', 'context_state', 'evidence_requirements', 'execution_enabled',
                  'capability_route', 'baseline', 'input_contract'):
        out[field] = result[field]
    return out


def route_suite(cases, *, classifier=None, threshold=0.23, margin=0.035, sensitive_terms=(), mode='hybrid'):
    """Only case.query enters interpretation. All other row fields are excluded."""
    from collections import Counter
    classifier = classifier or IntentClassifier()
    rows = []
    for case in cases:
        if case.get('quarantined', False):
            rows.append({'case': case['id'], 'decision': 'QUARANTINED'})
            continue
        result = route_request(case['query'], classifier=classifier, threshold=threshold,
                               margin=margin, sensitive_terms=sensitive_terms, mode=mode)
        rows.append({'case': case['id'], 'source_rows': case.get('source_rows', []),
                     'provenance': case.get('provenance', 'unknown'),
                     'result': export_route(result), 'decision': result['decision']})
    return {'schema_version': '5.1', 'rows': rows,
            'mode': mode,
            'capability_distribution': dict(Counter(r['result']['capability_id'] for r in rows if r.get('result', {}).get('capability_id'))),
            'support_distribution': dict(Counter(r.get('result', {}).get('support_level', 'QUARANTINED') for r in rows)),
            'provenance_decisions': {p: dict(Counter(r['decision'] for r in rows if r.get('provenance', 'unknown') == p))
                                     for p in sorted({r.get('provenance', 'unknown') for r in rows})},
            'decisions': dict(Counter(row['decision'] for row in rows)),
            'capability_matches': sum(row.get('result', {}).get('capability_status') == 'MATCHED' for row in rows),
            'metric_status': 'descriptive_only_no_independent_accuracy_claim',
            'inference_columns': ['query'], 'llm_requests': 0}
