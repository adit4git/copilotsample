"""Train a small local semantic model only from independently adjudicated cases."""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wealth_intent.abstraction import prepare_semantic_input

FIELDS = ['scope','goal','output','audience','metric','subject_selection','requested_effect']
p=argparse.ArgumentParser();p.add_argument('--corpus',required=True);p.add_argument('--output',default='data/semantic_model.joblib');args=p.parse_args()
records=[json.loads(line) for line in Path(args.corpus).read_text().splitlines() if line.strip()]
eligible=[]
for r in records:
    reviewers={x.get('reviewer_id') for x in r.get('reviewer_annotations',[]) if x.get('reviewer_id')}
    allowed = r.get('provenance') in {'advisor_email','template_prompt'}
    if (r.get('annotation_status')=='adjudicated' and r.get('independent_review') is True
            and r.get('labels_complete') is True and len(reviewers)>=3 and allowed
            and set(FIELDS+['intents']) <= set(r.get('adjudicated_labels',{}))): eligible.append(r)
if len(eligible)<30:
    raise SystemExit(f'Refusing training: {len(eligible)} eligible records; at least 30 independently reviewed complete records required.')
texts=[prepare_semantic_input(r['query'])['text'] for r in eligible]
vectorizer=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True,strip_accents='unicode')
X=vectorizer.fit_transform(texts); models={}
mlb=MultiLabelBinarizer(); y=mlb.fit_transform([r['adjudicated_labels']['intents'] for r in eligible])
if min(Counter(i for r in eligible for i in r['adjudicated_labels']['intents']).values())<2:
    raise SystemExit('Refusing training: every included intent needs at least two reviewed examples.')
models['intents']=OneVsRestClassifier(LogisticRegression(max_iter=1500,class_weight='balanced')).fit(X,y)
for field in FIELDS:
    values=[r['adjudicated_labels'][field] if r['adjudicated_labels'][field] is not None else '__NONE__' for r in eligible]
    if len(set(values))<2: continue
    models[field]=LogisticRegression(max_iter=1500,class_weight='balanced').fit(X,values)
digest=hashlib.sha256(('\n'.join(sorted(r['case_id'] for r in eligible))).encode()).hexdigest()[:12]
artifact={'artifact_schema':'semantic_model.1','model_id':'local_semantic_'+digest,
          'vectorizer':vectorizer,'models':models,'intent_classes':list(mlb.classes_),
          'training_records':len(eligible),'training_case_digest':digest,
          'warning':'Load only trusted artifacts created by this script; joblib is not a safe untrusted interchange format.'}
joblib.dump(artifact,args.output);print(json.dumps({k:v for k,v in artifact.items() if k not in {'vectorizer','models'}},indent=2))
