"""Full-runtime comparisons. Labels are used only after inference, never as inputs."""
from collections import Counter, defaultdict
from .classifier import IntentClassifier
from .runtime import route_request

DIMENSIONS = ('intents', 'scope', 'output', 'capability_id', 'decision', 'clarification_required')


def evaluate_outcomes(cases, settings=None):
    settings = settings or [('hybrid', .23, .035), ('rules_only', .23, .035)]
    classifier = IntentClassifier()
    reports = []
    for mode, threshold, margin in settings:
        buckets = defaultdict(list)
        for case in cases:
            if case.get('quarantined'):
                continue
            result = route_request(case['query'], classifier=classifier, mode=mode,
                                   threshold=threshold, margin=margin)
            expected = case.get('expected_route', {})
            eligible = (case.get('independent_review') is True
                        and case.get('annotation_status') == 'adjudicated'
                        and case.get('provenance') in {'advisor_email', 'template_prompt'}
                        and set(expected) == set(DIMENSIONS))
            matches = {}
            if eligible:
                for key in DIMENSIONS:
                    a, b = result[key], expected[key]
                    matches[key] = set(a) == set(b) if key in {'intents', 'clarification_required'} else a == b
            row = {'decision': result['decision'], 'support': result['support_level'],
                   'capability': result['capability_id'], 'eligible': eligible, 'matches': matches}
            # Assigned groups remain unknown until independently annotated. Never infer provenance from length.
            family = case.get('outcome_family', 'unknown')
            if family not in {'research', 'portfolio', 'tax', 'communication', 'monitoring', 'operations', 'other'}:
                family = 'unknown'
            provenance = case.get('provenance', 'unknown')
            if provenance not in {'advisor_email', 'template_prompt', 'rewritten_fixture'}:
                provenance = 'unknown'
            buckets[(provenance, family)].append(row)
        strata = []
        for (provenance, family), rows in sorted(buckets.items()):
            reviewed = [r for r in rows if r['eligible']]
            strata.append({'provenance': provenance, 'outcome_family': family, 'cases': len(rows),
                           'reviewed_cases': len(reviewed),
                           'exact_route_matches': sum(all(r['matches'].values()) for r in reviewed) if reviewed else None,
                           'dimension_correct_counts': {k: sum(r['matches'][k] for r in reviewed) for k in DIMENSIONS} if reviewed else None,
                           'decisions': dict(Counter(r['decision'] for r in rows)),
                           'support': dict(Counter(r['support'] for r in rows)),
                           'capabilities': dict(Counter(r['capability'] or 'CAPABILITY_GAP' for r in rows))})
        reports.append({'mode': mode, 'threshold': threshold, 'margin': margin, 'strata': strata})
    return {'schema_version': '5.1', 'reports': reports,
            'metric_status': 'No accuracy without independently adjudicated complete expected routes. Reviewer independence is asserted, not authenticated.',
            'inference_columns': ['query'], 'llm_requests': 0}
