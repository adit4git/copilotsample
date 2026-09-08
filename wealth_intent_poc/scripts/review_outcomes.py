"""Local diagnostic report; queries are the sole inference input.

Business columns are counted offline, never passed to route_request. Source
text, names, financial values and business-label prose are excluded from output.
Run from the project root with --input /path/to/workbook.xlsx.
"""
import argparse
from pathlib import Path
import hashlib
import json
import sys
from collections import Counter
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wealth_intent.datasets import import_suite
from wealth_intent.corpus import prepare_cases, source_manifest
from wealth_intent.runtime import route_suite, route_request, export_route


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', default='data/outcome_diagnostics.json')
    args = parser.parse_args()
    source = Path(args.input)
    payload = source.read_bytes()
    cases = prepare_cases(import_suite(payload, source.name))
    report = route_suite(cases)
    report['source_sha256'] = hashlib.sha256(payload).hexdigest()
    report['source_rows'] = len(cases)
    report['evaluation_context'] = 'No trusted application or attachment bindings supplied.'
    if source.suffix.lower() == '.xlsx':
        import openpyxl
        import io
        w = openpyxl.load_workbook(io.BytesIO(payload), read_only=True, data_only=True)
        s = w['Visible Rows'] if 'Visible Rows' in w.sheetnames else w.active
        values = list(s.values)
        heads = list(values[0])
        report['offline_metadata_counts'] = {
            name: len({r[heads.index(name)] for r in values[1:] if len(r) > heads.index(name) and r[heads.index(name)]})
            for name in ['Problem Solved', 'Investment Agent Output'] if name in heads
        }
        w.close()
    if report['source_sha256'] == source_manifest()['source_sha256']:
        # Human-written analysis notes from the workbook review; not gold labels.
        report['authored_metadata_review'] = [
            {'rows': [52], 'issue': 'liquidity_query_has_monitoring_output_metadata'},
            {'rows': [65], 'issue': 'client_screen_query_has_product_shortlist_metadata'},
            {'rows': list(range(77, 84)), 'issue': 'instrument_queries_have_broad_portfolio_output_metadata'},
            {'rows': [43, 44, 133, 134], 'issue': 'thread_reconstruction_needs_confirmation'},
        ]
    report['interpretation_status'] = 'Authored rules/templates; no independent review or accuracy claim.'
    # Synthetic typed-context example, separate from the query-only source run.
    example = route_request('How has credit spread moved for this issue, and what is driving it?', context={
        'security_reference': {'status': 'AVAILABLE', 'source': 'attachment'},
        'analysis_period': {'status': 'AVAILABLE', 'source': 'attachment'},
        'actor_context': {'status': 'AVAILABLE', 'source': 'host_application'},
        'as_of': {'status': 'AVAILABLE', 'source': 'host_application'},
    })
    report['synthetic_attachment_example'] = export_route(example)
    Path(args.output).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'decisions': report['decisions'], 'capability_matches': report['capability_matches'],
                      'source_rows': len(cases), 'output': args.output}))


if __name__ == '__main__':
    main()
