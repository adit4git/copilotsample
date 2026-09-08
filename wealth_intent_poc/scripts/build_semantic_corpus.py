"""Build an annotation-ready corpus from rewritten source fixtures and probes."""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wealth_intent.privacy import mask

ROOT = Path(__file__).resolve().parents[1]
BASE = json.loads((ROOT/'data/query_suite.json').read_text())
PROBES_PATH = ROOT/'data/synthetic_semantic_queries.json'
PROBES = json.loads(PROBES_PATH.read_text()) if PROBES_PATH.exists() else {'groups': []}
LABEL_FIELDS = ['intents','scope','goal','output','audience','metric','subject_selection',
                'requested_effect','capability_id','decision','missing_context']


def normalized(text): return re.sub(r'\s+', ' ', text.strip().lower())


records, seen = [], set()
def add(case_id, query, source_rows, provenance, generation_method, group, relationship, hypothesis):
    key = normalized(query)
    if key in seen: return
    seen.add(key)
    findings = mask(query).findings
    records.append({
        'case_id': case_id, 'source_group_id': group, 'source_rows': source_rows,
        'split_group': group, 'query': query, 'provenance': provenance,
        'generation_method': generation_method, 'relationship': relationship,
        'privacy_findings': findings, 'author_hypothesis': hypothesis,
        'annotation_status': 'unlabeled', 'independent_review': False,
        'reviewer_annotations': [], 'adjudicated_labels': {}, 'adjudication_rationale': None,
        'labels_complete': False, 'training_eligible': False,
    })

for case in BASE:
    row = case.get('source_row')
    add('base_'+str(row), case['query'], [row], 'rewritten_fixture',
        'registry_author_rewrite', 'source_row_'+str(row), 'source_scenario_rewrite',
        {'intents': case.get('expected_intents', [])})
for group in PROBES['groups']:
    for i, query in enumerate(group['queries'], 1):
        rows = group['source_rows']; split = 'source_rows_'+'_'.join(map(str, rows))
        add(group['id'].lower()+'_'+str(i), query, rows, 'synthetic_probe',
            'meaning_variation_probe', split, group['relationship'], group.get('expected') or {})

out = ROOT/'data/semantic_annotation_corpus.jsonl'
out.write_text(''.join(json.dumps(r)+'\n' for r in records))
columns = ['case_id','source_group_id','source_rows','split_group','query','provenance',
           'generation_method','relationship','reviewer_id','review_round',*LABEL_FIELDS,
           'labels_complete','reviewer_notes']
with (ROOT/'data/semantic_annotation_template.csv').open('w', newline='') as f:
    w=csv.DictWriter(f, fieldnames=columns); w.writeheader()
    for r in records:
        w.writerow({**{k:r.get(k,'') for k in columns}, 'source_rows':'|'.join(map(str,r['source_rows']))})
schema = {
 'schema_version':'semantic_annotation.1', 'label_fields':LABEL_FIELDS,
 'multi_value_separator':'|',
 'required_independent_reviews':3,
 'training_gate':{'annotation_status':'adjudicated','independent_review':True,
                  'labels_complete':True,'minimum_distinct_reviewers':3,
                  'excluded_provenance':['rewritten_fixture','synthetic_probe']},
 'allowed_provenance':['advisor_email','template_prompt','rewritten_fixture','synthetic_probe','unknown'],
 'note':'Author hypotheses and business workbook columns are never training labels.'}
(ROOT/'data/semantic_annotation_schema.json').write_text(json.dumps(schema,indent=2))
manifest={'schema_version':'semantic_corpus.1','records':len(records),
          'source_groups':len({r['split_group'] for r in records}),
          'training_eligible':0,'source_inputs':['data/query_suite.json',str(PROBES_PATH.name)],
          'corpus_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
          'note':'All records require independent annotation; current authored/synthetic records are excluded from model training.'}
(ROOT/'data/semantic_corpus_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
