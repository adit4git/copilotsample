"""Run the full runtime, including refinement and planning, with a rules-only floor."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wealth_intent.datasets import import_suite
from wealth_intent.corpus import prepare_cases
from wealth_intent.outcome_evaluation import evaluate_outcomes

parser = argparse.ArgumentParser()
parser.add_argument('--input', required=True)
parser.add_argument('--output', default='data/runtime_evaluation.json')
parser.add_argument('--sensitivity', action='store_true')
args = parser.parse_args()
source = Path(args.input)
# JSON annotation files can include complete expected_route labels; source workbooks remain unlabeled.
cases = json.loads(source.read_text()) if source.suffix == '.json' else prepare_cases(import_suite(source.read_bytes(), source.name))
settings = ([('rules_only', .23, .035)] + [('hybrid', t, m) for t in [.18, .23, .28] for m in [.02, .035, .05]]) if args.sensitivity else None
report = evaluate_outcomes(cases, settings)
Path(args.output).write_text(json.dumps(report, indent=2))
print(json.dumps({'configurations': len(report['reports']), 'output': args.output}))
