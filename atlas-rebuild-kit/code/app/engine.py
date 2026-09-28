from __future__ import annotations
from copy import deepcopy
from itertools import combinations
from typing import Any

UNKNOWN = object()
_RANK = {'ELIGIBLE':0,'CONDITIONAL':1,'NEEDS_REVIEW':2,'INELIGIBLE':3}
_CRANK = {'CONFIRMED_ELIGIBLE':0,'ELIGIBLE_WITH_CARVEOUT':1,'CONDITIONAL':2,'NEEDS_REVIEW':3,'CONFIRMED_INELIGIBLE':4}

def _get(facts: dict[str, Any], field: str) -> Any:
    if field in facts: return facts[field]
    cur: Any = facts
    for part in field.split('.'):
        if not isinstance(cur, dict) or part not in cur: return UNKNOWN
        cur = cur[part]
    return cur

def _unknown(value: Any) -> bool:
    return value is UNKNOWN or value is None or value == 'UNKNOWN'

def evaluate_predicate(predicate: Any, facts: dict[str, Any]) -> bool | None:
    if type(predicate) is bool: return predicate
    if not isinstance(predicate, dict): raise ValueError('Predicate must be boolean or object')
    if 'AND' in predicate:
        values=[evaluate_predicate(x,facts) for x in predicate['AND']]
        return False if False in values else None if None in values else True
    if 'OR' in predicate:
        values=[evaluate_predicate(x,facts) for x in predicate['OR']]
        return True if True in values else None if None in values else False
    if 'NOT' in predicate:
        value=evaluate_predicate(predicate['NOT'],facts)
        return None if value is None else not value
    actual=_get(facts,predicate['field']); expected=predicate.get('value'); op=predicate['op']
    if _unknown(actual): return None
    if op in {'EQ','NEQ'}:
        if type(actual) is not type(expected): return None
        result=actual==expected
        return result if op=='EQ' else not result
    if op=='IN': return expected is not None and type(actual) is str and isinstance(expected,list) and actual in expected
    if op=='CONTAINS': return actual is not None and isinstance(actual,list) and expected in actual
    if op=='GTE': return actual>=expected if type(actual) in {int,float} and type(expected) in {int,float} else None
    raise ValueError(f'Unsupported operator: {op}')

def _leaves(predicate: Any, facts: dict[str, Any]) -> list[dict[str,Any]]:
    if type(predicate) is bool: return []
    if 'field' in predicate:
        value=_get(facts,predicate['field'])
        return [{'field':predicate['field'],'op':predicate['op'],'expected':predicate.get('value'),'actual':None if value is UNKNOWN else value}]
    leaves=[]
    for value in predicate.values():
        for node in value if isinstance(value,list) else [value]: leaves.extend(_leaves(node,facts))
    return leaves

def evaluate_offering(offering_id: str, facts: dict[str,Any], store: dict[str,Any], program: str) -> dict[str,Any]:
    offering=store['offerings'].get(offering_id)
    if not offering: raise KeyError(f'Unknown offering {offering_id}')
    result={'offering_id':offering_id,'label':offering['label'],'verdict':'ELIGIBLE','reasons':[],'internal_only_reasons':[],'disclosures':[],'scope_exclusions':[],'missing_fields':[],'trace':[],'rule_pack_id':store['pack_id']}
    if program not in offering['program_scope']:
        result['verdict']='INELIGIBLE'; result['reasons'].append({'rule_id':'PROGRAM_SCOPE','message':f'{offering["label"]} is unavailable in the {program} program.','failure_class':'CLIENT_ELIGIBILITY'}); return result
    def elevate(verdict: str):
        if _RANK[verdict]>_RANK[result['verdict']]: result['verdict']=verdict
    for rule in offering['rules']:
        value=evaluate_predicate(rule['predicate'],facts); leaves=_leaves(rule['predicate'],facts)
        result['trace'].append({'rule_id':rule['rule_id'],'effect':rule['effect'],'passed':value,'source_doc':rule['source_doc'],'inputs':leaves})
        reason={'rule_id':rule['rule_id'],'message':rule['message'],'source_doc':rule['source_doc'],'failure_class':rule['failure_class']}
        destination=result['reasons'] if rule['failure_class']=='CLIENT_ELIGIBILITY' else result['internal_only_reasons']
        if value is None:
            missing=sorted({x['field'] for x in leaves if _unknown(_get(facts,x['field']))})
            elevate('NEEDS_REVIEW'); result['missing_fields'].extend(missing)
            destination.append({**reason,'message':'Required input is missing or invalid; eligibility is unresolved.','missing_fields':missing}); continue
        effect=rule['effect']
        if effect=='REQUIREMENT' and not value:
            elevate('NEEDS_REVIEW' if rule['failure_class']=='MANAGER_ADJUDICATION' else 'INELIGIBLE'); destination.append(reason)
        elif effect=='NEEDS_REVIEW' and value: elevate('NEEDS_REVIEW'); destination.append(reason)
        elif effect=='CONDITION' and not value: elevate('CONDITIONAL'); destination.append(reason)
        elif effect=='DISCLOSURE' and value: result['disclosures'].append(reason)
        elif effect=='SCOPE_CARVEOUT' and value:
            ids=_get(facts,rule.get('scope_key',''))
            ids=None if ids is UNKNOWN else ids
            result['scope_exclusions'].append({**reason,'scope_key':rule.get('scope_key'),'excluded_ids':ids if isinstance(ids,list) else None})
            if not isinstance(ids,list) or not ids:
                elevate('NEEDS_REVIEW'); result['missing_fields'].append(rule.get('scope_key')); destination.append({**reason,'message':'A scope exclusion is known but its affected asset identifiers are unresolved.'})
    result['missing_fields']=sorted({x for x in result['missing_fields'] if x})
    return result

def evaluate_composition(offering_ids: list[str], facts_by_offering: dict[str,dict[str,Any]], store: dict[str,Any], program: str) -> dict[str,Any]:
    ids=list(dict.fromkeys(offering_ids)); verdicts={i:evaluate_offering(i,facts_by_offering[i],store,program) for i in ids}
    result={'verdict':'CONFIRMED_ELIGIBLE','notes':[],'offerings':ids,'offering_verdicts':verdicts}
    def elevate(verdict: str):
        if _CRANK[verdict]>_CRANK[result['verdict']]: result['verdict']=verdict
    if not ids: elevate('NEEDS_REVIEW')
    for v in verdicts.values():
        elevate('CONFIRMED_INELIGIBLE' if v['verdict']=='INELIGIBLE' else v['verdict'] if v['verdict']!='ELIGIBLE' else 'ELIGIBLE_WITH_CARVEOUT' if v['scope_exclusions'] else 'CONFIRMED_ELIGIBLE')
    for a,b in combinations([x for x in ids if x!='iapEnrollment'],2):
        matches=[r for r in store['composition_rules'] if {a,b}==set(r['offerings'])]
        if not matches:
            elevate('NEEDS_REVIEW');result['notes'].append({'offerings':[a,b],'relation':'UNRESOLVED','message':'Composition is not established by supplied sources; obtain offering-specific terms.'});continue
        for rule in matches:
            result['notes'].append(deepcopy(rule))
            if rule['relation']=='INCOMPATIBLE_WITH': elevate('CONFIRMED_INELIGIBLE')
            elif rule['relation']=='SCOPE_CARVEOUT_WITHIN_COMPOSITION': elevate('ELIGIBLE_WITH_CARVEOUT')
    return result

def client_safe_view(verdict: dict[str,Any]) -> dict[str,Any]:
    return {'offering_id':verdict['offering_id'],'label':verdict['label'],'verdict':verdict['verdict'],'reasons':[{'message':x['message'],'source_doc':x.get('source_doc',[])} for x in verdict['reasons'] if not x.get('missing_fields')],'generic_message':'Additional internal review or service arrangements are needed.' if verdict['internal_only_reasons'] else None,'disclosures':[x['message'] for x in verdict['disclosures']],'scope_notes':[x['message'] for x in verdict['scope_exclusions']]}
