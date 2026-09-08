"""Descriptive placeholder sensitivity, not threshold tuning."""
import argparse
import csv
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from wealth_intent.datasets import import_suite,load_demo_suite,evaluate
from wealth_intent.corpus import prepare_cases,apply_annotations
from wealth_intent.classifier import IntentClassifier

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path)
    p.add_argument('--annotations',type=Path)
    p.add_argument('--confirm-threads',action='store_true')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    cases=import_suite(args.input.read_bytes(),args.input.name) if args.input else load_demo_suite()
    cases=prepare_cases(cases,args.confirm_threads)
    if args.annotations:
        with args.annotations.open(newline='',encoding='utf-8-sig') as f:
            cases=apply_annotations(cases,list(csv.DictReader(f)))
    classifier=IntentClassifier()
    grid=[]
    for threshold in [0.18,0.23,0.30]:
        for margin in [0.02,0.035,0.07]:
            report=evaluate(cases,classifier,threshold,margin,compare_baseline=False)
            grid.append({'threshold':threshold,'margin':margin,'summary':report['summary'],'strata':report['strata']})
    args.output.write_text(json.dumps({'purpose':'descriptive_sensitivity_not_tuning','grid':grid},indent=2))
    print('Saved nine descriptive settings; no optimal threshold or production accuracy is claimed.')
