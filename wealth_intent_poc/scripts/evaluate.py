"""Evaluate the generic suite; optionally import a local workbook without storing it."""
import argparse
import csv
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wealth_intent.classifier import IntentClassifier
from wealth_intent.datasets import load_demo_suite, import_suite, evaluate
from wealth_intent.corpus import prepare_cases, apply_annotations


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="Local CSV/XLSX, held only in memory")
    parser.add_argument("--output", type=Path, help="Typed results only, without query text")
    parser.add_argument("--confirm-threads", action="store_true", help="Confirm the supplied source's suggested thread links")
    parser.add_argument("--annotations", type=Path, help="Metadata-only sidecar exported from this prepared corpus")
    parser.add_argument("--threshold",type=float,default=0.23,help="Unvalidated base fallback threshold")
    parser.add_argument("--margin",type=float,default=0.035,help="Unvalidated candidate margin")
    args = parser.parse_args()
    cases = import_suite(args.input.read_bytes(), args.input.name) if args.input else load_demo_suite()
    cases = prepare_cases(cases,args.confirm_threads)
    if args.annotations:
        with args.annotations.open(newline='',encoding='utf-8-sig') as f:
            cases = apply_annotations(cases,list(csv.DictReader(f)))
    result = evaluate(cases, IntentClassifier(),threshold=args.threshold,margin=args.margin)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
