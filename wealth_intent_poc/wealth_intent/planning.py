"""Versioned outcome templates and typed data-flow validation. Metadata only.

Every input has a type and explicit context/config/upstream binding. No callable
adapter, credentials, network client, financial computation or model execution.
"""
from dataclasses import dataclass, asdict
from .registry import REGISTRY

VERSION = '4.0.0'

# Authored preview contracts: these establish output coverage, not financial validity.
OUTCOME_CONTRACTS = {
    'portfolio.tax_aware_concentration_transition': {
        'version': '1.0.0',
        'intents': ['portfolio.exposure', 'tax.transition', 'solution.match'],
        'output': 'tax_aware_transition_proposal',
        'required_sections': ['concentration_assessment', 'transition_scenarios',
                              'realized_gain_estimates', 'candidate_solution_comparison',
                              'assumptions_and_limitations'],
        'request_inputs': ['comparison_targets', 'gain_budget', 'transition_horizon',
                           'tax_assumptions', 'client_objectives', 'client_constraints'],
        'support_level': 'CONTRACTED_COMPOSITION_PREVIEW',
    },
    'book.holdings_signal_analysis': {
        'version': '1.0.0', 'output': 'holdings_signal_analysis',
        'required_sections': ['scoped_holdings', 'market_signals', 'affected_subjects'],
        'request_inputs': ['holding_selection', 'materiality_threshold', 'analysis_period'],
        'support_level': 'CONTRACTED_COMPOSITION_PREVIEW',
    },
}


def support_metadata(capability):
    if capability is None:
        return {'support_level': 'UNSUPPORTED', 'contract_status': 'NO_OUTCOME_CONTRACT'}
    return {'support_level': OUTCOME_CONTRACTS.get(capability, {}).get('support_level', 'AUTHORED_TASK_PREVIEW'),
            'contract_status': 'AUTHORED_NOT_DOMAIN_VALIDATED',
            'payload_validation': 'NOMINAL_TYPES_ONLY',
            'verification_status': 'UNVERIFIED', 'execution_ready': False}


@dataclass(frozen=True)
class Function:
    id: str
    inputs: tuple
    outputs: tuple
    function_class: str
    access_path: str
    permission: str = 'none'
    pii_policy: str = 'trusted_boundary_only'
    execution_class: str = 'deterministic'
    version: str = '1.0.0'


FUNCTIONS = {}
def register(id, inputs, outputs, cls, path, permission='none', pii='trusted_boundary_only'):
    spec = Function(id, tuple(inputs), tuple(outputs), cls, path, permission, pii)
    if id in FUNCTIONS:
        raise ValueError('Duplicate function registration.')
    FUNCTIONS[id] = spec
    return id


SCOPE_BINDINGS = {'account_or_client': 'client_reference', 'household': 'household_reference',
                  'subject_set': 'subject_set_reference',
                  'advisor_book': 'advisor_book_scope', 'portfolio': 'portfolio_reference',
                  'practice': 'practice_scope'}
for scope, binding in SCOPE_BINDINGS.items():
    register(f'{scope}.resolve', [binding], [f'resolved_{scope}'], 'read', 'trusted_host_context')
    register(f'{scope}.authorize', ['actor_context', f'resolved_{scope}', 'capability_id'],
             [f'authorized_{scope}'], 'decide', 'policy_decision_point', 'subject.read')
    register(f'{scope}.snapshot', [f'authorized_{scope}', 'as_of'], ['subject_snapshot'],
             'read', 'client_portfolio_gateway', 'subject.read')
register('research.authorize', ['actor_context', 'capability_id'], ['research_entitlement'],
         'decide', 'policy_decision_point', 'research.read')

# Each read source has a distinct evidence type and explicit reference contract.
SOURCES = {
    'approved_market_content': ('approved_research_gateway', []),
    'cio_current': ('approved_research_gateway', []),
    'cio_prior': ('approved_research_gateway', ['analysis_period']),
    'security_research': ('approved_research_gateway', ['security_reference']),
    'spread_history': ('market_data_gateway', ['security_reference', 'analysis_period']),
    'benchmark_curve': ('market_data_gateway', ['security_reference', 'analysis_period']),
    'issuer_events': ('approved_research_gateway', ['security_reference', 'analysis_period']),
    'return_series': ('market_data_gateway', ['strategy_reference', 'analysis_period']),
    'benchmark_returns': ('market_data_gateway', ['benchmark', 'analysis_period']),
    'approved_catalog': ('product_catalog_gateway', []),
    'product_terms': ('product_terms_gateway', ['product_reference']),
    'strategy_holdings': ('strategy_holdings_gateway', ['strategy_reference']),
    'comparison_holdings': ('strategy_holdings_gateway', ['comparison_targets']),
    'target_allocation': ('approved_research_gateway', ['strategy_reference']),
    'performance_history': ('performance_gateway', ['portfolio_reference', 'analysis_period']),
    'tax_lots': ('tax_lot_gateway', ['portfolio_reference']),
    'household_activity': ('household_trade_gateway', ['household_reference', 'analysis_period']),
    'current_policy': ('policy_content_gateway', []),
    'prior_review': ('review_archive_gateway', ['prior_review_reference']),
    'order_status': ('order_gateway', ['order_reference']),
    'program_guide': ('operations_guide_gateway', ['platform']),
    'directory_evidence': ('entitled_directory_gateway', ['specialist_topic']),
    'sales_data': ('practice_analytics_gateway', ['analysis_period']),
    'distribution_records': ('distribution_gateway', ['portfolio_reference']),
    'pricing_inputs': ('market_data_gateway', ['product_reference']),
}
PRIVATE_SOURCES = {'performance_history', 'tax_lots', 'household_activity', 'prior_review',
                   'order_status', 'sales_data', 'distribution_records'}
REFERENCE_TYPES = {'security_reference', 'product_reference', 'strategy_reference',
                   'comparison_targets', 'benchmark'}
for ref in sorted(REFERENCE_TYPES):
    register('reference.resolve_'+ref, [ref, 'research_entitlement'], ['resolved_'+ref],
             'read', 'security_master_gateway' if ref == 'security_reference' else 'reference_resolution_gateway', 'reference.read')
for name, (path, refs) in SOURCES.items():
    typed_refs = ['resolved_'+ref if ref in REFERENCE_TYPES else ref for ref in refs]
    register(f'evidence.{name}', ['research_entitlement', 'as_of', *typed_refs], [name], 'read', path, 'evidence.read')
    if name in PRIVATE_SOURCES:
        register(f'evidence.authorize_{name}', ['actor_context', *refs, 'capability_id'],
                 [f'{name}_entitlement'], 'decide', 'policy_decision_point', f'{name}.read')
        original = FUNCTIONS[f'evidence.{name}']
        FUNCTIONS[original.id] = Function(original.id, (*original.inputs, f'{name}_entitlement'),
                                         original.outputs, original.function_class, original.access_path,
                                         f'{name}.read')

# Sources are proposed evidence contracts, not statements that data is accessible.
TEMPLATES = {
    'research.cio': ('research.cio_guidance', ['cio_current'], []),
    'research.change': ('research.guidance_comparison', ['cio_current', 'cio_prior'], []),
    'research.security': ('research.security_explanation', ['security_research'], []),
    'product.search': ('product.approved_discovery', ['approved_catalog'], []),
    'product.compare': ('product.comparison', ['approved_catalog'], ['comparison_targets']),
    'product.terms': ('product.terms_explanation', ['product_terms'], []),
    'portfolio.exposure': ('portfolio.client_exposure_analysis', [], []),
    'portfolio.drift': ('portfolio.drift_analysis', ['target_allocation'], []),
    'portfolio.overlap': ('portfolio.overlap_analysis', ['comparison_holdings'], []),
    'portfolio.correlation': ('portfolio.correlation_analysis', ['return_series', 'benchmark_returns'], []),
    'performance.attribution': ('performance.driver_explanation', ['performance_history'], []),
    'performance.reconcile': ('performance.return_reconciliation', ['performance_history', 'distribution_records'], []),
    'tax.transition': ('tax.transition_scenario', ['tax_lots', 'current_policy'], ['comparison_targets']),
    'tax.wash_sale': ('tax.wash_sale_review', ['tax_lots', 'household_activity', 'current_policy'], []),
    'tax.planning': ('tax.planning_guidance', ['current_policy'], ['client_objectives']),
    'solution.match': ('solution.objective_proposal', ['approved_catalog', 'current_policy'], ['client_objectives', 'client_constraints']),
    'book.screen': ('book.household_screening', ['approved_catalog', 'current_policy'], ['screening_criteria']),
    'practice.analytics': ('practice.sales_ranking', ['sales_data'], []),
    'monitor.manage': ('monitor.specification', ['current_policy'], ['screening_criteria']),
    'content.draft': ('communication.client_market_update', ['approved_market_content'], []),
    'meeting.prepare': ('meeting.review_package', ['cio_current', 'prior_review'], ['meeting_reference']),
    'decision.readiness': ('decision.readiness_package', ['current_policy'], ['proposal_reference']),
    'operations.enrollment': ('operations.enrollment_guidance', ['program_guide'], []),
    'operations.transfer': ('operations.transfer_assessment', ['current_policy'], []),
    'operations.order': ('operations.order_diagnosis', ['order_status', 'current_policy'], []),
    'operations.distribution': ('operations.distribution_reconciliation', ['distribution_records', 'current_policy'], []),
    'instrument.payout': ('instrument.maturity_analysis', ['product_terms', 'pricing_inputs'], []),
    'operations.data_issue': ('operations.data_diagnosis', ['product_terms'], []),
    'directory.specialist': ('directory.specialist_lookup', ['directory_evidence'], []),
}
assert set(TEMPLATES) == set(REGISTRY)

# A closed task-artifact contract allows composition without arbitrary tool calls.
TASK_INPUTS = {}
for intent, (_, sources, external) in TEMPLATES.items():
    inputs = list(sources) + list(external) + ['methodology_version']
    if intent in {'portfolio.exposure', 'portfolio.drift', 'portfolio.overlap', 'book.screen',
                  'practice.analytics', 'operations.transfer', 'instrument.payout'}:
        inputs.append('subject_snapshot')
    if intent == 'content.draft':
        inputs += ['safe_composition_input']
    if intent in {'meeting.prepare', 'decision.readiness', 'monitor.manage', 'content.draft', 'solution.match', 'tax.transition'}:
        inputs += ['upstream_artifacts']
    TASK_INPUTS[intent] = inputs
    register(f'task.{intent}', inputs, ['task_artifact'],
             'compose' if intent == 'content.draft' else 'compute' if intent.startswith(('portfolio.', 'performance.', 'tax.', 'instrument.')) else 'read',
             'local_composition_preview' if intent == 'content.draft' else REGISTRY[intent].service)

register('market.credit_spread', ['spread_history', 'benchmark_curve', 'issuer_events', 'methodology_version'],
         ['task_artifact'], 'compute', 'market_analytics_preview')
register('artifact.collect', ['task_artifacts'], ['upstream_artifacts'], 'compose', 'trusted_result_binder')
register('privacy.prepare_composition', ['approved_market_content', 'source_content', 'upstream_artifacts'],
         ['safe_composition_input'], 'compute', 'trusted_privacy_boundary', pii='no_model_egress')
register('result.validate', ['task_artifacts', 'output_contract_version', 'requested_output'], ['validated_result'], 'verify', 'trusted_result_verifier')

CONFIG = {'methodology_version': 'poc_methodology_contract.v1', 'output_contract_version': 'poc_output_contract.v1'}


def capability_catalog():
    entries = [{'id': cap, 'version': VERSION, 'outcome': REGISTRY[i].title,
             'workflow_id': cap + '.v2', 'function_ids': ['task.'+i],
             'contract_status': 'authored_preview_not_independently_validated'}
            for i, (cap, _, _) in TEMPLATES.items()] + [
        {'id': 'research.credit_spread_explanation', 'version': VERSION,
         'outcome': 'Explain instrument spread changes and evidence-supported drivers',
         'workflow_id': 'credit_spread_explanation.v2', 'function_ids': ['market.credit_spread']},
        {'id': 'communication.content_transform', 'version': VERSION, 'outcome': 'Transform supplied text for the requested format and audience', 'workflow_id': 'content_transform.v2', 'function_ids': ['task.content.draft']},
        {'id': 'communication.general_market_update', 'version': VERSION, 'outcome': 'Draft general market communication from approved content', 'workflow_id': 'general_market_update.v2', 'function_ids': ['task.content.draft']},
        {'id': 'portfolio.rebalance_scenario', 'version': VERSION, 'outcome': 'Compare a proposed rebalance scenario with current allocation', 'workflow_id': 'rebalance_scenario.v2', 'function_ids': ['portfolio.compare_scenario']},
        {'id': 'analysis.explanation_package', 'version': VERSION, 'outcome': 'Compose registered analytical tasks and explanation', 'workflow_id': 'analysis_package.v2', 'function_ids': ['artifact.collect', 'result.validate']},
        {'id': 'monitor.book_signal_specification', 'version': VERSION, 'outcome': 'Prepare a monitoring specification from registered analyses', 'workflow_id': 'monitor_package.v2', 'function_ids': ['monitor.validate_specification']},
        {'id': 'operations.guidance_package', 'version': VERSION, 'outcome': 'Combine operational guidance with permitted research and drafting', 'workflow_id': 'operations_package.v2', 'function_ids': ['artifact.collect', 'result.validate']},
    ] + [dict(id=cap, version=VERSION, outcome=spec['output'], workflow_id=cap+'.v4',
              function_ids=['task.'+i for i in spec.get('intents', [])],
              output_contract=spec, **support_metadata(cap))
         for cap, spec in OUTCOME_CONTRACTS.items()]
    retired = {'analysis.explanation_package', 'operations.guidance_package'}
    return [dict(item, workflow_id=item['id']+'.v4', **support_metadata(item['id']))
            for item in entries if item['id'] not in retired]


def function_catalog():
    return [dict(asdict(f), contract_status='AUTHORED_PREVIEW', payload_validation='NOMINAL_TYPES_ONLY')
            for f in FUNCTIONS.values()]


def match(semantic):
    selected = set(semantic['intents'])
    if not selected or not selected <= TEMPLATES.keys():
        return None, 'No registered tasks cover the request.'
    if semantic['requested_effect'] == 'operational_action':
        return None, 'Execution of operational actions is outside the registered preview outcomes.'
    if semantic['goal'] == 'design_tax_aware_concentrated_stock_transition':
        contract = OUTCOME_CONTRACTS['portfolio.tax_aware_concentration_transition']
        if selected == set(contract['intents']):
            return 'portfolio.tax_aware_concentration_transition', 'Authored transition-proposal composition contract; not financially validated.'
        return None, 'Additional requested tasks are not covered by the transition-proposal contract.'
    # Reviewed composition policies: analytical read/draft packages; operational
    # guidance with research/drafting; transfer plus proposed allocation.
    ops = {i for i in selected if i.startswith('operations.')}
    allowed_with_ops = {'research.cio', 'research.security', 'product.terms', 'product.search',
                        'product.compare', 'content.draft', 'directory.specialist', 'decision.readiness'}
    if 'operations.transfer' in ops:
        allowed_with_ops |= {'solution.match', 'portfolio.exposure', 'tax.transition', 'portfolio.overlap'}
    if ops and not selected <= ops | allowed_with_ops:
        return None, 'The combined operational and analytical outcome has no approved composition rule.'
    if len(ops) > 1:
        return None, 'Multiple operational workflows need a reviewed composition contract.'
    if semantic['metric'] == 'credit_spread' and selected == {'research.security'}:
        return 'research.credit_spread_explanation', 'Registered credit-spread outcome.'
    if selected == {'content.draft'}:
        if semantic['requires_source_content']:
            return 'communication.content_transform', 'Registered supplied-content transformation.'
        if semantic['scope'] not in SCOPE_BINDINGS:
            return 'communication.general_market_update', 'Registered general market communication.'
    if semantic['goal'] == 'compare_rebalance_scenario' and selected <= {'portfolio.drift', 'research.cio', 'content.draft', 'decision.readiness'}:
        return 'portfolio.rebalance_scenario', 'Registered scenario-analysis composition.'
    signal_tasks = {'research.security', 'portfolio.exposure', 'book.screen'}
    if semantic['scope'] in {'subject_set', 'advisor_book'} and selected <= signal_tasks and 'research.security' in selected:
        return 'book.holdings_signal_analysis', 'Scoped holdings and market-signal composition.'
    if len(selected) == 1:
        return TEMPLATES[next(iter(selected))][0], 'Registered task outcome.'
    if 'monitor.manage' in selected and selected <= signal_tasks | {'monitor.manage'}:
        return 'monitor.book_signal_specification', 'Registered analytical monitoring-specification composition.'
    return None, 'Requested combination has no explicit outcome contract; generic packages are discovery candidates only.'


def validate_graph(nodes, context, config):
    """Reject cycles, unknown bindings, missing inputs and incompatible producers."""
    by_id = {n['id']: n for n in nodes}
    if len(by_id) != len(nodes):
        raise ValueError('Duplicate node ID.')
    done = set()
    for node in nodes:
        if node['function_id'] not in FUNCTIONS:
            raise ValueError('Unregistered function.')
        f = FUNCTIONS[node['function_id']]
        if set(node['inputs']) != set(f.inputs):
            raise ValueError('Missing or extra typed function inputs.')
        edges = set()
        for fact, binding in node['inputs'].items():
            kind = binding['source']
            refs = binding.get('nodes', []) if kind == 'collection' else [binding['node']] if kind == 'upstream' else []
            for ref in refs:
                if ref not in done:
                    raise ValueError('Cycle, forward reference or missing dependency.')
                producer = FUNCTIONS[by_id[ref]['function_id']]
                expected = 'task_artifact' if kind == 'collection' else fact
                if expected not in producer.outputs:
                    raise ValueError('Incompatible producer output type.')
                edges.add(ref)
            if kind == 'context' and fact not in context:
                raise ValueError('Unregistered context binding.')
            if kind == 'config' and fact not in config:
                raise ValueError('Unregistered configuration binding.')
            if kind not in {'upstream', 'collection', 'context', 'config'}:
                raise ValueError('Unsupported input binding source.')
            if kind == 'collection' and fact not in {'task_artifacts'}:
                raise ValueError('Invalid collection type.')
        if set(node['depends_on']) != edges:
            raise ValueError('Dependency graph differs from typed input edges.')
        done.add(node['id'])


def compile_plan(semantic, declared, inferred):
    capability, reason = match(semantic)
    context = {}
    nodes = []
    producers = {}
    config = dict(CONFIG, capability_id=capability, requested_output=semantic['output'],
                  signal_metric=semantic.get('metric') or 'unspecified')
    attachment = declared.get('attachment_reference', inferred.get('attachment_reference'))

    def binding(fact):
        if fact in producers:
            return {'source': 'upstream', 'node': producers[fact]}
        if fact.startswith('resolved_') and fact.removeprefix('resolved_') in REFERENCE_TYPES:
            if 'research_entitlement' not in producers: add('research.authorize')
            producer = add('reference.resolve_' + fact.removeprefix('resolved_'))
            return {'source': 'upstream', 'node': producer}
        if fact in config:
            return {'source': 'config', 'version': config[fact]}
        if fact not in context:
            value = declared.get(fact) or inferred.get(fact)
            if value is None:
                if fact in {'actor_context', 'as_of'}:
                    value = {'status': 'PENDING_RESOLUTION', 'source': 'host_application'}
                elif attachment and fact in {'security_reference', 'product_reference', 'source_content', 'analysis_period', 'strategy_reference', 'comparison_targets'}:
                    value = {'status': 'PENDING_RESOLUTION', 'source': 'attachment'}
                else:
                    value = {'status': 'NEEDS_CLARIFICATION', 'source': 'unspecified'}
            context[fact] = dict(value)
        return {'source': 'context', 'context_type': fact}

    def add(function_id, overrides=None):
        f = FUNCTIONS[function_id]
        inputs = {name: (overrides[name] if overrides and name in overrides else binding(name)) for name in f.inputs}
        deps = set()
        for item in inputs.values():
            if item['source'] == 'upstream': deps.add(item['node'])
            if item['source'] == 'collection': deps.update(item['nodes'])
        node_id = f'n{len(nodes)+1:03d}'
        nodes.append({'id': node_id, 'function_id': f.id, 'function_version': f.version,
                      'function_class': f.function_class, 'execution_class': f.execution_class,
                      'access_path': f.access_path, 'required_permission': f.permission,
                      'pii_policy': f.pii_policy, 'inputs': inputs,
                      'required_inputs': list(f.inputs), 'produces': list(f.outputs),
                      'depends_on': sorted(deps), 'invoked': False})
        for name in f.outputs: producers[name] = node_id
        return node_id

    def read(name):
        if name in producers: return
        if 'research_entitlement' not in producers:
            add('research.authorize')
        if name in PRIVATE_SOURCES:
            add('evidence.authorize_' + name)
        add('evidence.'+name)

    def snapshot():
        if 'subject_snapshot' in producers: return
        scope = semantic['scope']
        if scope in SCOPE_BINDINGS:
            add(scope+'.resolve'); add(scope+'.authorize'); add(scope+'.snapshot')
        else:
            # Strategy holdings are a portfolio subject too. Reuse a typed
            # conversion contract rather than treating an instrument as a client.
            read('strategy_holdings')
            add('strategy.snapshot')
        if semantic['subject_selection'] == 'prioritized_clients' and semantic['scope'] != 'subject_set':
            add('book.select_prioritized')

    if not capability:
        return {'mode': 'preview_only', 'match': {'status': 'CAPABILITY_GAP', 'reason': reason, 'candidates': []},
                'capability_id': None, 'workflow_id': None, 'nodes': [], 'context': {},
                'context_requirements': [], 'context_actions': [], 'clarification_required': [],
                'missing_context': [],
                'access_paths': [], 'execution_enabled': False, 'uncovered_intents': semantic['intents'],
                'configuration': config, **support_metadata(None)}

    contract = OUTCOME_CONTRACTS.get(capability)
    if contract:
        for name in contract['request_inputs']:
            binding(name)
    if capability == 'portfolio.tax_aware_concentration_transition' and semantic['scope'] in SCOPE_BINDINGS:
        snapshot()
        add('portfolio.reference_from_subject')

    selected = list(semantic['intents'])
    # Dependencies among requested work are fixed: analyses feed transitions,
    # proposals, monitors and finally communication/review outputs.
    priority = {'tax.transition': 1, 'solution.match': 2, 'monitor.manage': 3,
                'content.draft': 4, 'meeting.prepare': 5, 'decision.readiness': 5}
    selected.sort(key=lambda i: priority.get(i, 0))
    task_nodes = []
    for intent in selected:
        if intent == 'research.security' and semantic['metric'] == 'credit_spread':
            for source in ['spread_history', 'benchmark_curve', 'issuer_events']: read(source)
            task_nodes.append(add('market.credit_spread'))
            continue
        _, sources, external = TEMPLATES[intent]
        for source in sources:
            if source == 'security_research' and semantic['scope'] in {'advisor_book', 'subject_set'}:
                snapshot()
                if 'research_entitlement' not in producers: add('research.authorize')
                add('research.holdings_signals')
            else:
                read(source)
        if 'subject_snapshot' in TASK_INPUTS[intent]: snapshot()
        # A book-scoped signal needs the actual scoped holdings, even when the
        # requested business intent is research or monitoring rather than exposure.
        if intent in {'research.security', 'monitor.manage'} and semantic['scope'] in {'advisor_book', 'subject_set'}:
            snapshot()
        if 'upstream_artifacts' in TASK_INPUTS[intent]:
            add('artifact.collect', {'task_artifacts': {'source': 'collection', 'nodes': list(task_nodes)}})
        if intent == 'content.draft':
            if semantic['scope'] in SCOPE_BINDINGS:
                snapshot()
                add('communication.client_context')
                # Client-specific context is local binding input, never sent out.
            if semantic['requires_source_content']:
                binding('source_content')
            else:
                producers['source_content'] = add('content.from_approved', {'approved_market_content': binding('approved_market_content')})
            add('privacy.prepare_composition')
        task_node = add('task.'+intent)
        if intent == 'tax.transition' and capability == 'portfolio.tax_aware_concentration_transition':
            task_node = add('tax.transition_assumption_contract')
        if intent == 'portfolio.drift' and semantic['goal'] == 'compare_rebalance_scenario':
            task_node = add('portfolio.compare_scenario')
        if intent == 'monitor.manage' and semantic['requested_effect'] != 'read_only':
            if semantic['requested_effect'] == 'ambiguous_monitor':
                binding('monitor_mode')
                task_node = add('monitor.resolve_mode')
            task_node = add('monitor.validate_specification')
        if intent == 'content.draft' and 'client_communication_context' in producers:
            task_node = add('content.personalize_locally')
        task_nodes.append(task_node)
    # All requested task outputs are bound explicitly into the final deliverable.
    add('result.validate', {'task_artifacts': {'source': 'collection', 'nodes': task_nodes}})
    validate_graph(nodes, context, config)

    by_id = {}
    for node in nodes:
        direct = [name for name, b in node['inputs'].items() if b['source'] == 'context'
                  and context[name]['status'] != 'AVAILABLE']
        blocked = any(by_id[d]['status'] != 'PLANNED' for d in node['depends_on'])
        if any(context[name]['status'] == 'CONFLICT' for name in direct):
            status = 'CONFLICT'
        elif any(context[name]['status'] == 'UNAVAILABLE' for name in direct):
            status = 'UNAVAILABLE'
        elif any(context[name]['status'] == 'NEEDS_CLARIFICATION' for name in direct):
            status = 'NEEDS_INPUT'
        elif blocked:
            status = 'BLOCKED'
        elif direct:
            status = 'PENDING_CONTEXT'
        else:
            status = 'PLANNED'
        node.update(status=status, missing_inputs=direct, verification_status='UNVERIFIED',
                    execution_ready=False, contract_validation='NOMINAL_TYPES_ONLY')
        by_id[node['id']] = node
    missing = sorted(name for name, v in context.items() if v['status'] == 'NEEDS_CLARIFICATION')
    evidence = [{'type': name, 'status': 'PENDING_RETRIEVAL', 'producer': producer}
                for name, producer in producers.items() if name in SOURCES or name in {'subject_snapshot', 'client_profile', 'portfolio_exposure', 'communication_preferences'}]
    return {'mode': 'preview_only', 'match': {'status': 'MATCHED', 'reason': reason, 'candidates': []},
            'capability_id': capability, 'capability_version': VERSION, 'workflow_id': capability+'.v4',
            'output_contract': contract, **support_metadata(capability),
            'outcome': semantic['goal'], 'nodes': nodes, 'context': context,
            'context_requirements': list(context), 'context_actions': list(dict.fromkeys(n['function_id'] for n in nodes if n['function_class'] in {'read', 'decide'})),
            'clarification_required': missing,
            'missing_context': missing, 'evidence_requirements': evidence,
            'access_paths': list(dict.fromkeys(n['access_path'] for n in nodes)),
            'configuration': config, 'uncovered_intents': [], 'execution_enabled': False,
            'note': 'Valid preview contracts only. No function executed; PLANNED does not establish access or data availability.'}


register('strategy.snapshot', ['strategy_holdings'], ['subject_snapshot'], 'compute', 'trusted_portfolio_adapter')
register('portfolio.reference_from_subject', ['subject_snapshot'], ['portfolio_reference'], 'read', 'trusted_portfolio_adapter')
register('tax.transition_assumption_contract', ['task_artifact', 'gain_budget', 'transition_horizon', 'tax_assumptions'],
         ['task_artifact'], 'verify', 'tax_assumption_contract_preview')
register('communication.client_context', ['subject_snapshot'], ['client_communication_context', 'client_profile', 'portfolio_exposure', 'communication_preferences'], 'read', 'trusted_client_context')
register('content.from_approved', ['approved_market_content'], ['source_content'], 'compose', 'trusted_composer')
register('book.select_prioritized', ['subject_snapshot', 'prioritized_client_set'], ['subject_snapshot'], 'compute', 'trusted_subject_selector')
register('research.holdings_signals', ['subject_snapshot', 'research_entitlement', 'as_of', 'signal_metric',
                                      'holding_selection', 'materiality_threshold', 'analysis_period'],
         ['security_research'], 'read', 'entitled_market_signal_gateway', 'research.read')
register('monitor.resolve_mode', ['task_artifact', 'monitor_mode'], ['task_artifact'], 'decide', 'trusted_request_resolver')
register('monitor.validate_specification', ['task_artifact', 'materiality_threshold', 'monitoring_cadence', 'delivery_channel'], ['task_artifact'], 'verify', 'monitor_specification_preview')
register('content.personalize_locally', ['task_artifact', 'client_communication_context'], ['task_artifact'], 'compose', 'trusted_local_binder')
register('portfolio.compare_scenario', ['task_artifact', 'subject_snapshot', 'target_allocation', 'methodology_version'], ['task_artifact'], 'compute', 'portfolio_scenario_preview')
