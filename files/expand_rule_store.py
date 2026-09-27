"""Rebuild rule-store.json from rule_store_offerings.csv + rule_store_composition.csv.
Usage: python3 expand_rule_store.py  (reads the two CSVs in the same folder, writes rule-store.json)
"""
import json, csv

PACK_ID = 'atlas..tax-services.2026-09-20'
STATUS = 'POC_DRAFT_NOT_APPROVED_POLICY'

def build(offerings_csv='rule_store_offerings.csv', composition_csv='rule_store_composition.csv'):
    offerings = {}
    with open(offerings_csv, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['offering_id'] not in offerings:
                off = {'label': r['offering_label'], 'program_scope': json.loads(r['program_scope'])}
                if r['coverage_note']: off['coverage_note'] = r['coverage_note']
                off['rules'] = []
                offerings[r['offering_id']] = off
            off = offerings[r['offering_id']]
            rule = {
                'rule_id': r['rule_id'], 'effect': r['effect'],
                'predicate': json.loads(r['predicate_json']),
                'failure_class': r['failure_class'],
            }
            if r['routing']: rule['routing'] = r['routing']
            if r['scope_key']: rule['scope_key'] = r['scope_key']
            rule['message'] = r['message']
            rule['source_doc'] = json.loads(r['source_doc_json'])
            rule['compile_source'] = {'kind': r['compile_kind'], 'review_status': r['review_status']}
            off['rules'].append(rule)
    composition_rules = []
    with open(composition_csv, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            c = {'rule_id': r['rule_id'], 'relation': r['relation'], 'offerings': json.loads(r['offerings_json'])}
            if r['scope']: c['scope'] = r['scope']
            c['message'] = r['message']
            c['source_doc'] = json.loads(r['source_doc_json'])
            c['compile_source'] = {'kind': r['compile_kind'], 'review_status': r['review_status']}
            composition_rules.append(c)
    return {'pack_id': PACK_ID, 'status': STATUS, 'offerings': offerings, 'composition_rules': composition_rules}

if __name__ == '__main__':
    rs = build()
    json.dump(rs, open('rule-store.json', 'w'), indent=2)
    print('wrote rule-store.json:', len(rs['offerings']), 'offerings,',
          sum(len(o['rules']) for o in rs['offerings'].values()), 'rules,',
          len(rs['composition_rules']), 'composition rules')
