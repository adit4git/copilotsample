import pytest
from app.data import RULE_STORE,BY_ID,derive_facts
from app.engine import evaluate_predicate,evaluate_offering,evaluate_composition,client_safe_view
from app.services import offering_result,composition_result

def test_pack_counts():
 assert len(RULE_STORE['offerings'])==17
 assert sum(len(x['rules']) for x in RULE_STORE['offerings'].values())==112
 assert len(RULE_STORE['composition_rules'])==16

def test_three_valued_logic():
 assert evaluate_predicate({'OR':[{'field':'missing','op':'EQ','value':True},True]}, {}) is True
 assert evaluate_predicate({'AND':[{'field':'missing','op':'EQ','value':True},False]}, {}) is False
 assert evaluate_predicate({'field':'missing','op':'EQ','value':True}, {}) is None
 assert evaluate_predicate({'field':'x','op':'EQ','value':True}, {'x':1}) is None

def test_henderson_tet_has_two_real_scope_exclusions():
 v=offering_result('henderson','transition')
 assert v['verdict']=='ELIGIBLE'
 ids={x for c in v['scope_exclusions'] for x in c['excluded_ids']}
 assert ids=={'LOT_HEND_GIFT_2011','AUSTIN-4.0-32'}

def test_sato_namespace_split():
 assert offering_result('sato','mgiQlh')['verdict']=='ELIGIBLE'
 assert offering_result('sato','mgiTer')['verdict']=='INELIGIBLE'
 wrong=offering_result('sato','taxManagedSMA')
 assert wrong['verdict']=='INELIGIBLE' and wrong['reasons'][0]['rule_id']=='PROGRAM_SCOPE'

def test_farkas_client_eligible_but_advisor_prerequisite_fails():
 v=offering_result('farkas','dtlhOverlay')
 assert v['verdict']=='ELIGIBLE'
 assert v['prerequisite']['verdict']=='INELIGIBLE'
 assert any(x['failure_class']=='FA_SCOPE' for x in v['prerequisite']['internal_only_reasons'])

def test_pas_blocks_iap_overlays():
 for x in ['taxManagedSMA','qlhOverlay','dtlhOverlay','transition']:
  assert offering_result('bianchi',x)['verdict']=='INELIGIBLE'

def test_duarte_tem_roster_fails(): assert offering_result('duarte','temSms')['verdict']=='INELIGIBLE'
def test_eshun_custom_managed_ter_is_eligible(): assert offering_result('eshun','taxManagedSMA')['verdict']=='ELIGIBLE'
def test_tet_dtlh_incompatible(): assert composition_result('henderson',['transition','dtlhOverlay'])['verdict']=='CONFIRMED_INELIGIBLE'
def test_tet_ter_scoped(): assert composition_result('henderson',['transition','taxManagedSMA'])['verdict']=='ELIGIBLE_WITH_CARVEOUT'
def test_unspecified_pair_requires_review(): assert composition_result('henderson',['qlhOverlay','dtlhOverlay'])['verdict']=='NEEDS_REVIEW'
def test_client_view_hides_internal_trace():
 v=offering_result('farkas','dtlhOverlay')['prerequisite']; safe=client_safe_view(v)
 assert 'trace' not in safe and 'internal_only_reasons' not in safe
 assert safe['generic_message']
