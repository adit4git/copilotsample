"""Local request abstraction for a future trusted semantic model boundary."""
import re
from .privacy import mask, normalize


def prepare_semantic_input(text, sensitive_terms=()):
    privacy = mask(normalize(text), sensitive_terms)
    abstracted = privacy.masked_text
    parameter_types = []

    def replace(pattern, token, parameter):
        nonlocal abstracted
        if re.search(pattern, abstracted, re.I):
            parameter_types.append(parameter)
            abstracted = re.sub(pattern, token, abstracted, flags=re.I)

    replace(r'(?<!\w)\d+(?:\.\d+)?\s*%', '[PERCENT]', 'percentage')
    replace(r'\btop\s+\d+\b', 'top [COUNT]', 'top_n')
    replace(r'\b\d{1,2}\s*(?:days?|weeks?|months?|years?)\b', '[PERIOD]', 'period')
    return {'text': abstracted, 'privacy_findings': privacy.findings,
            'parameter_types': sorted(set(parameter_types)), 'raw_text_included': False,
            'privacy_assurance': 'HEURISTIC_MINIMIZATION_ONLY',
            'external_model_egress_allowed': False}
