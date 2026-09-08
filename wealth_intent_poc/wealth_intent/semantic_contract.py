"""Deterministic cross-field validation for interpreted requests."""
from .registry import REGISTRY
SCOPES = {'general', 'account_or_client', 'household', 'subject_set', 'advisor_book',
          'portfolio', 'security_or_instrument', 'product_or_strategy', 'practice'}
SELECTIONS = {'unspecified', 'single_subject', 'explicit_subject_references',
              'prioritized_clients', 'criteria_filtered_book', 'entire_book'}
EFFECTS = {'read_only', 'draft_only', 'ambiguous_monitor', 'monitor_specification', 'operational_action'}


def validate_semantic(semantic):
    issues = []
    if not set(semantic['intents']) <= set(REGISTRY):
        issues.append({'code': 'UNKNOWN_INTENT', 'field': 'intents'})
    if semantic['scope'] not in SCOPES: issues.append({'code': 'UNKNOWN_SCOPE', 'field': 'scope'})
    if semantic['subject_selection'] not in SELECTIONS: issues.append({'code': 'UNKNOWN_SELECTION', 'field': 'subject_selection'})
    if semantic['requested_effect'] not in EFFECTS: issues.append({'code': 'UNKNOWN_EFFECT', 'field': 'requested_effect'})
    if semantic['scope'] == 'subject_set' and semantic['subject_selection'] == 'unspecified':
        issues.append({'code': 'SUBJECT_SET_WITHOUT_SELECTION', 'field': 'subject_selection'})
    if semantic['subject_selection'] in {'explicit_subject_references', 'prioritized_clients', 'criteria_filtered_book', 'entire_book'} and semantic['scope'] not in {'subject_set', 'advisor_book'}:
        issues.append({'code': 'SET_SELECTION_WITH_NON_SET_SCOPE', 'field': 'scope'})
    if 'book.screen' in semantic['intents'] and semantic['scope'] not in {'subject_set', 'advisor_book'}:
        issues.append({'code': 'BOOK_TASK_WITHOUT_BOOK_SCOPE', 'field': 'scope'})
    # Metric is intentionally nullable: broad signals such as "today's macro
    # market moves" may be valid even when they do not map to one registered
    # metric. The capability layer can still require signal evidence or ask for
    # screening criteria without manufacturing a semantic label.
    if semantic['requested_effect'] == 'draft_only' and 'content.draft' not in semantic['intents']:
        issues.append({'code': 'DRAFT_EFFECT_WITHOUT_DRAFT_TASK', 'field': 'requested_effect'})
    return issues
