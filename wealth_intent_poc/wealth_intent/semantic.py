"""Local clause/role semantic parser; business spreadsheet labels are never inputs."""
import re
from .registry import REGISTRY

CONTEXT_TYPES = {
    'actor_context', 'as_of', 'client_reference', 'household_reference', 'subject_set_reference',
    'advisor_book_scope', 'practice_scope', 'portfolio_reference', 'security_reference',
    'issuer_reference', 'product_reference', 'strategy_reference', 'comparison_targets',
    'market_signal_reference', 'attachment_reference', 'source_content', 'analysis_period',
    'benchmark', 'prioritized_client_set', 'client_objectives', 'client_constraints',
    'proposal_reference', 'prior_review_reference', 'order_reference', 'monitor_mode',
    'materiality_threshold', 'monitoring_cadence', 'delivery_channel', 'screening_criteria',
    'holding_selection', 'ranking_basis', 'meeting_reference', 'platform', 'specialist_topic',
    'gain_budget', 'transition_horizon', 'tax_assumptions',
}
CONTEXT_STATES = {'AVAILABLE', 'PENDING_RESOLUTION', 'NEEDS_CLARIFICATION', 'CONFLICT', 'UNAVAILABLE'}
CONTEXT_SOURCES = {'host_application', 'attachment', 'conversation', 'advisor_selection'}


def validate_context(context):
    if context is None: return {}
    if not isinstance(context, dict) or not set(context) <= CONTEXT_TYPES:
        raise ValueError('Context accepts registered binding types only; business labels and raw values are not runtime inputs.')
    clean = {}
    for key, value in context.items():
        if (not isinstance(value, dict) or set(value) != {'status', 'source'}
                or value['status'] not in CONTEXT_STATES or value['source'] not in CONTEXT_SOURCES):
            raise ValueError('Use only a registered context status and source; identifiers and attachment text are not accepted.')
        if key in {'actor_context', 'as_of'} and value['source'] != 'host_application':
            raise ValueError('Actor and observation-time bindings must come from the host application.')
        clean[key] = dict(value)
    return clean


def _clauses(text):
    values = [x.strip() for x in re.split(r'(?<=[.!?;])\s+|\n+|\b(?:and then|then)\b', text) if x.strip()]
    positive, negative = [], []
    for value in values or [text]:
        if re.search(r"\b(?:do not|don't|never|no need to|without)\b|\bno\s+(?:article|attachment|email|message)\b", value):
            negative.append(value)
        else: positive.append(value)
    return ' '.join(positive), ' '.join(negative)


def _has(text, pattern): return bool(re.search(pattern, text, re.I))


def interpret(query, base):
    text = query.lower().replace('’', "'")
    affirmative, negated = _clauses(text)
    intents, trace = list(base['intents']), []
    for intent in list(intents):
        patterns = REGISTRY[intent].patterns
        if any(_has(negated, p) for p in patterns) and not any(_has(affirmative, p) for p in patterns):
            intents.remove(intent); trace.append({'rule': 'clause_negation_veto', 'intent': intent})

    def add(intent, pattern, rule):
        if _has(affirmative, pattern):
            if intent not in intents: intents.append(intent)
            trace.append({'rule': rule, 'intent': intent})

    add('content.draft', r'(?:explain|frame).{0,65}(?:to (?:a|the|this) .{0,25}client|to clients)|what.{0,15}(?:say|talking)|turn this into|make this.{0,20}into|create talking points|client.ready (?:rationale|explanation)', 'audience_explanation')
    # CIO evidence remains an explicit task when guidance is used to build a
    # proposal, analysis or communication. A guidance-version comparison owns
    # its current/prior retrieval and therefore does not add research.cio.
    if 'research.change' not in intents:
        add('research.cio', r'\bcio\b|\bhouse view\b|\bcapital market outlook\b', 'cio_evidence_reference')
    add('portfolio.drift', r'before.and.after|rebalance toward|out of alignment|outside.{0,20}(?:tactical )?(?:ranges|bands)|deviat(?:e|ed|ing).{0,30}(?:allocation|cio)|(?:weights?|allocation).{0,20}(?:drifted|outside)', 'drift_concept')
    add('portfolio.exposure', r'(?:selloff|market moves?).{0,60}(?:client|book)|(?:clients|client book).{0,45}(?:impacted|exposed)|(?:holdings|portfolios).{0,35}(?:rising volatility|risk)|concentrated (?:stock|position)|concentration.{0,35}(?:client|portfolio|account)', 'portfolio_exposure_concept')
    add('research.security', r'credit rating|estimate revisions?|analysts?.{0,20}(?:estimates?|forecasts?)|consensus earnings forecasts?|short interest|credit spread|spread over treasur|spread.{0,20}(?:widen|tighten)|earnings|tech selloff|(?:interest rates?|macro).{0,30}(?:moving|moves?)|market moves?', 'market_signal')
    add('book.screen', r'(?:which|show me|identify|list|find).{0,35}clients|prioritize.{0,40}outreach|high cash balances|large cash positions|excessive cash allocations|cash.heavy clients', 'client_set_screen')
    add('meeting.prepare', r'last review|before the meeting|before.{0,20}client.{0,20}meeting', 'review_context')
    add('solution.match', r'tiered liquidity|(?:objectives are|objectives:).{0,100}|(?:best|right).{0,20}(?:solution|strategy)|fit.{0,30}(?:this|the|a)?\s*(?:client|objective)|\bproposal\b', 'objective_solution')
    add('tax.transition', r'tax.aware transition|tax.sensitive diversification|diversif.{0,50}(?:minimiz|realized tax|capital gain)|transition.{0,50}(?:gain budget|concentrated)', 'tax_transition_concept')

    selection = 'unspecified'
    set_pattern = r'across.{0,70}(?:accounts?|clients?|portfolios?)|selected clients\b|these (?:three|four|five|\d+) clients?|clients? (?:with|holding)|cash.heavy clients?|my (?:prioritized |top )?clients?|my client book|\bmy book\b|which clients?|who is affected|\bportfolios\b|account group|group of accounts'
    if _has(affirmative, set_pattern):
        scope = 'subject_set'
        if _has(affirmative, r'prioritized clients?|top clients?'): selection = 'prioritized_clients'
        elif _has(affirmative, r'clients? (?:with|holding)|cash.heavy clients?|high cash|large cash|excessive cash|which clients?|who is affected'): selection = 'criteria_filtered_book'
        elif _has(affirmative, r'across.{0,70}(?:accounts?|clients?)|selected clients\b|these (?:three|four|five|\d+) clients?|account group|group of accounts'): selection = 'explicit_subject_references'
        else: selection = 'entire_book'
    elif _has(affirmative, r'\bhousehold\b|family.s accounts'):
        scope, selection = 'household', 'single_subject'
    elif _has(affirmative, r'this client|my client|the client|selected client|this customer|client\s+(?:[a-z][a-z .-]{1,30}|\[(?:possible_name|custom_term)\])|this account|account\s+(?:[a-z0-9]+[- ]\d+)|\[account\]|\[customer_id\]|prospect'):
        scope, selection = 'account_or_client', 'single_subject'
    elif _has(affirmative, r'this portfolio|client.s portfolio'):
        scope, selection = 'portfolio', 'single_subject'
    elif _has(affirmative, r'practice.{0,20}(?:sales|rank)|where do we rank|firm.{0,30}(?:total|rank)') or 'practice.analytics' in intents: scope = 'practice'
    elif _has(affirmative, r'this (?:issue|stock|company|bond|issuer|holding|security)|credit spread|spread over treasur|short interest|earnings|bond issuer'):
        scope, selection = 'security_or_instrument', 'single_subject'
    elif _has(affirmative, r'\bstrateg(?:y|ies)\b|\bfunds?\b|\bsma\b|\betf\b|structured notes?|maturity terms'): scope = 'product_or_strategy'
    else: scope = 'general'
    # Selecting holdings to inspect is a parameter/access-path concern, not a
    # separate exposure intent. Keep exposure only when the request explicitly
    # asks to calculate exposure, concentration, weights, allocation or duration.
    if (scope == 'subject_set' and 'research.security' in intents and 'portfolio.exposure' in intents
            and _has(affirmative, r'\b(?:top\s+(?:(?:\d+|ten)\s+)?holdings?|holdings? across)\b')
            and not _has(affirmative, r'concentration|concentrated|expos(?:ure|ed)|weights?|allocation|duration|rate sensitivity')):
        intents.remove('portfolio.exposure'); trace.append({'rule': 'holdings_selection_not_exposure_intent', 'intent': 'portfolio.exposure'})
    if set(intents) <= {'operations.enrollment', 'product.terms'} and _has(affirmative, r'how|what|do we need|can we enroll'):
        scope, selection = 'product_or_strategy', 'unspecified'

    if _has(affirmative, r'\bvoicemail\b'): output = 'voicemail_bullets' if _has(affirmative, r'bullets') else 'voicemail_script'
    elif _has(affirmative, r'\b(?:table|tabular)\b'): output = 'ranked_table' if _has(affirmative, r'rank|prioriti') else 'analysis_table'
    elif 'content.draft' in intents: output = 'email_draft' if _has(affirmative, r'\bemail\b') else 'talking_points'
    elif 'meeting.prepare' in intents: output = 'review_comparison' if _has(affirmative, r'changed since|current vs prior|last review') else 'meeting_book'
    elif _has(affirmative, r'what.{0,15}driving|explain|why|summarize'): output = 'cited_explanation'
    elif (scope in {'subject_set', 'advisor_book'} and 'research.security' in intents
          and _has(affirmative, r'holdings?|which clients?|who is affected|expos(?:ure|ed)|estimate revisions?|market moves?')):
        output = 'holdings_signal_analysis'
    elif 'book.screen' in intents or 'practice.analytics' in intents: output = 'ranked_table'
    elif any(i.startswith(('portfolio.', 'performance.', 'tax.')) for i in intents): output = 'analysis_table'
    elif 'product.compare' in intents: output = 'comparison_table'
    elif any(i in intents for i in ('product.search', 'solution.match')): output = 'solution_shortlist'
    elif any(i.startswith('operations.') for i in intents): output = 'guidance_or_diagnostic_checklist'
    elif 'decision.readiness' in intents: output = 'decision_summary'
    else: output = 'cited_answer'

    recurring = 'monitor.manage' in intents
    ambiguous_monitor = recurring and _has(affirmative, r'\bflag\b') and not _has(affirmative, r'proactively|whenever|daily|every|notify|alert|monitor')
    effect, lifecycle = 'read_only', None
    guidance = _has(affirmative, r'^(?:please )?(?:explain|tell me|show me)|^(?:how|what) (?:do|can|should)|steps? to')
    action = _has(affirmative, r'^(?:(?:please|kindly)\s+|could you\s+|can you\s+|i would like you to\s+)?(?:execute|submit|buy|sell|enroll|send|wire)\b')
    if recurring:
        lifecycle = base.get('monitor_lifecycle') or 'create'; effect = 'ambiguous_monitor' if ambiguous_monitor else 'monitor_specification'
    elif action and not guidance: effect = 'operational_action'
    elif 'content.draft' in intents: effect = 'draft_only'

    metric = next((name for name, pattern in (
        ('credit_spread', r'credit spread|spread over treasur|spread.{0,20}(?:widen|tighten)'),
        ('estimate_revisions', r'estimate revisions?|analysts?.{0,20}(?:earnings )?estimates?|consensus earnings forecasts?|(?:upgrades?|downgrades?).{0,25}earnings estimates?'),
        ('credit_rating', r'credit rating|ratings? agenc|watch status'), ('short_interest', r'short interest'),
        ('earnings', r'earnings'), ('duration', r'duration|rate sensitivity|interest rates?.{0,25}(?:moving|higher|rising)'), ('sector_exposure', r'tech selloff|sector|international exposure'),
    ) if _has(affirmative, pattern)), None)

    parameters = {}
    top = re.search(r'\btop\s+(\d+)\b', affirmative)
    if top: parameters['top_n'] = {'status': 'AVAILABLE', 'source': 'query', 'value': int(top.group(1))}
    elif _has(affirmative, r'\btop holdings?\b'): parameters['top_n'] = {'status': 'NEEDS_CLARIFICATION', 'source': 'query'}
    pct = re.search(r'\b(?:above|over|exceeds?|beyond)\s+(\d+(?:\.\d+)?)\s*%', affirmative)
    if pct: parameters['materiality_percent'] = {'status': 'AVAILABLE', 'source': 'query', 'value': float(pct.group(1))}
    elif _has(affirmative, r'\bmajor\b') and metric: parameters['materiality_percent'] = {'status': 'NEEDS_CLARIFICATION', 'source': 'query'}
    period = next((name for name, pattern in (
        ('YTD', r'\bytd\b|year.to.date|start of this year|since january 1'), ('last_quarter', r'last quarter'),
        ('last_month', r'last month'), ('today', r'\btoday\b|this morning'), ('since_inception', r'since inception'),
        ('twelve_months', r'(?:last|past|previous) 12 months|twelve months'),
    ) if _has(affirmative, pattern)), None)
    if period: parameters['analysis_period'] = {'status': 'AVAILABLE', 'source': 'query', 'normalized': period}

    goal = ('explain_credit_spread_change' if metric == 'credit_spread'
            else 'review_changes' if output == 'review_comparison'
            else 'screen_market_signals_for_client_holdings' if metric and scope in {'subject_set', 'advisor_book'}
            else 'compare_rebalance_scenario' if _has(affirmative, r'before.and-after|before.and.after|rebalance toward')
            else 'transform_supplied_content' if _has(affirmative, r'rewrite|simplify|turn this|make this.{0,20}into|convert')
            else 'draft_client_market_update' if 'content.draft' in intents and scope == 'account_or_client'
            else 'interpret_market_signal' if metric and 'research.security' in intents else 'fulfill_registered_tasks')
    if {'portfolio.exposure', 'tax.transition', 'solution.match'} <= set(intents) and _has(affirmative, r'\bproposal\b'):
        goal, output = 'design_tax_aware_concentrated_stock_transition', 'tax_aware_transition_proposal'

    inferred = {}
    def fact(name, status='AVAILABLE'): inferred[name] = {'status': status, 'source': 'query', 'assertion': 'inferred_type_only'}
    if period: fact('analysis_period')
    if _has(affirmative, r'(?:to|versus|against|vs).{0,25}(?:s&p|russell|benchmark)|broad market benchmarks'): fact('benchmark', 'PENDING_RESOLUTION')
    if _has(affirmative, r'\bvs\b|\bversus\b|against two|compare.{0,35}(?:sma|etf|fund)|overlap.{0,30}(?:two|strategies)'): fact('comparison_targets', 'PENDING_RESOLUTION')
    if _has(affirmative, r'\battached\b|attachment|screenshot|https?://|this article|enclosed article|uploaded'): fact('attachment_reference', 'PENDING_RESOLUTION')
    if scope == 'subject_set': fact('subject_set_reference', 'PENDING_RESOLUTION')
    if selection == 'prioritized_clients': fact('prioritized_client_set', 'PENDING_RESOLUTION')
    if 'top_n' in parameters: fact('holding_selection', 'AVAILABLE' if parameters['top_n']['status']=='AVAILABLE' else 'NEEDS_CLARIFICATION')
    if 'materiality_percent' in parameters: fact('materiality_threshold', 'AVAILABLE' if parameters['materiality_percent']['status']=='AVAILABLE' else 'NEEDS_CLARIFICATION')
    if _has(affirmative, r'daily|every day|weekly|monthly'): fact('monitoring_cadence')
    if _has(affirmative, r'qualify.{0,20}alts|eligible.{0,20}alternatives|high cash|large cash|excessive cash|cash.heavy|tactical ranges|estimate revisions|concentration risk'): fact('screening_criteria')
    if _has(affirmative, r'\b(?:pas|iap|pgim)\b'): fact('platform', 'PENDING_RESOLUTION')
    if _has(affirmative, r'\bml[a-z]{3}\b|\b\d{2}[a-z]\d{5}\b'): fact('product_reference', 'PENDING_RESOLUTION')
    if 'directory.specialist' in intents and _has(affirmative, r'\bfor\b|\babout\b|wholesaler|family office|philanthrop'): fact('specialist_topic', 'PENDING_RESOLUTION')

    audience = 'advisor'
    if 'content.draft' in intents and _has(affirmative, r'client.ready|client.friendly|client.facing|(?:email|message|note).{0,50}(?:to|for|addressed to) (?:(?:the selected|this|the|my|a|selected) (?:client|customer)|client \[(?:possible_name|custom_term)\])|to clients'):
        audience = 'client'
    return {'intents': intents, 'scope': scope, 'goal': goal, 'output': output, 'audience': audience,
            'metric': metric, 'requested_effect': effect, 'monitor_lifecycle': lifecycle,
            'subject_selection': selection, 'semantic_parameters': parameters,
            'requires_source_content': _has(affirmative, r'rewrite|simplify this|turn this|make this.{0,20}into|this explanation|convert.{0,20}guidance'),
            'semantic_trace': trace}, inferred
