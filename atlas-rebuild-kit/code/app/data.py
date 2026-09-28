from __future__ import annotations
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

DATA_DIR=Path(__file__).parent/'data'
RULE_STORE=json.loads((DATA_DIR/'rule-store.json').read_text())
CONFIG=json.loads((DATA_DIR/'fa-and-facts.json').read_text())
BOOK_ALL=json.loads((DATA_DIR/'households.json').read_text())
PRODUCT_SHELF=json.loads((DATA_DIR/'product-shelf.json').read_text())
RESEARCH_MODELS=json.loads((DATA_DIR/'research-models.json').read_text())
CONTENT_CATALOG=json.loads((DATA_DIR/'content-catalog.json').read_text())
FA_PROFILES=CONFIG['fa_profiles']; ACCOUNT_FACTS=CONFIG['account_facts']; ACCOUNT_OFFERING_FACTS=CONFIG['account_offering_facts']
OFFERING_MINIMUMS=CONFIG['offering_minimums']; REQUIRES_QUALIFIED_ADVISOR=set(CONFIG['requires_qualified_advisor'])
IAP_OFFERINGS=[x for x,o in RULE_STORE['offerings'].items() if 'IAP' in o['program_scope']]
MGI_OFFERINGS=[x for x,o in RULE_STORE['offerings'].items() if 'MGI' in o['program_scope']]
ALL_OFFERINGS=list(RULE_STORE['offerings'])
BY_ID={x['id']:x for x in BOOK_ALL}
PRODUCTS_BY_ID={p['product_id']:p for p in PRODUCT_SHELF}
MODELS_BY_ID={m['model_id']:m for m in RESEARCH_MODELS}
CONTENT_BY_ID={c['doc_id']:c for c in CONTENT_CATALOG}

def derive_facts(household: dict[str,Any], offering_id: str) -> dict[str,Any]:
    holdings=household.get('holdings',[]); total=sum(x['mv'] for x in holdings)
    is_cash=lambda x:x.get('ac')=='Cash' or x.get('sym')=='CASH'
    is_fi=lambda x:x.get('ac') in {'Fixed Income','Municipal'}
    cash=sum(x['mv'] for x in holdings if is_cash(x)); marketable=sum(x['mv'] for x in holdings if not is_cash(x))
    a=ACCOUNT_FACTS.get(household['id'],{}); o=ACCOUNT_OFFERING_FACTS.get(household['id'],{}).get(offering_id,{})
    def override(key,fallback=None): return o[key] if key in o else fallback
    # Overlay universes come from the household's actual strategy in the MLIAP
    # Strategy Catalog (D=DTLH, Q=QLH, T=TER) when one is on file; an explicit
    # per-household fact still wins, and with neither the fact stays unknown.
    strat = PRODUCTS_BY_ID.get(a.get('current_strategy_product_id')) if a.get('current_strategy_product_id') else None
    codes = set(strat.get('tem_overlays') or []) if strat else None
    def universe(key, code): return a[key] if key in a else ((code in codes) if codes is not None else None)
    months = a.get('dca_schedule_months'); freq = (a.get('dca_frequency') or 'MONTHLY').upper()
    min_months = {'WEEKLY':1,'BI_WEEKLY':1,'MONTHLY':2,'BI_MONTHLY':3}.get(freq)
    fi_lots=[x for x in holdings if is_fi(x) and x.get('type')=='BOND']; missing=[x for x in holdings if x.get('cost') is None]
    fa=FA_PROFILES.get(household['advisor_id'],FA_PROFILES['dana'])
    facts={
      'account_id':household['id'],'program':household.get('program','IAP'),
      'account.tax_status':a.get('tax_status','TAXABLE'),'account.segment':household['segment'],'account.advisory_value':household['aum'],
      'account.cash_value':cash,'account.pledgeable_marketable_value':marketable,
      'account.alt_capacity_pct':max(0,household.get('target',{}).get('alt',0)-household.get('current',{}).get('alt',0)),
      'account.has_low_basis_position':a.get('has_low_basis_position',any(x.get('cost') is not None and x['mv']>0 and x['cost']/x['mv']<.5 and x['mv']>total*.1 for x in holdings)),
      'account.protection_gap':a.get('protection_gap',False),'account.program_enrollment':a.get('program_enrollment'),
      'account.iap_agreement_executed':a.get('iap_agreement_executed',True),'account.iap_account_type_eligible':a.get('iap_account_type_eligible',True),'account.separate_account_per_program_strategy':a.get('separate_account_per_program_strategy',True),'account.selected_strategy_requirements_met':a.get('selected_strategy_requirements_met',True),
      'account.dca_cash_amount':a.get('dca_cash_amount'),'account.dca_schedule_months':a.get('dca_schedule_months'),
      'account.dca_minimum_met':(a.get('dca_cash_amount') or 0) >= OFFERING_MINIMUMS.get('dca', 3_000) if a.get('dca_cash_amount') is not None else None,
      'account.dca_timeframe_within_max':(months <= 6) if months is not None else None,
      'account.dca_timeframe_meets_min':(months >= min_months) if (months is not None and min_months is not None) else None,
      'account.dca_funding_cash_only':((a.get('dca_funding_source') or 'CASH').upper() == 'CASH') if a.get('dca_cash_amount') is not None else None,
      'account.strategy_minimum_met_before_dca':a.get('strategy_minimum_met', (household['aum'] >= (strat['minimum'] if strat else 0))),
      'account.has_pas_strategy':a.get('has_pas_strategy',False),'account.pas_manager_contract_executed':None,
      'account.is_domestic':a.get('residency_country','US')=='US',
      'account.in_universe_TER':universe('in_universe_TER','T'),'account.in_universe_QLH':universe('in_universe_QLH','Q'),'account.in_universe_DTLH':universe('in_universe_DTLH','D'),'account.in_universe_TET':a.get('in_universe_TET'),
      'account.offering_profile_requirements_met':override('account.offering_profile_requirements_met',household['aum']>=OFFERING_MINIMUMS.get(offering_id,250_000)),
      'account.goal_type':a.get('goal_type'),'account.is_retirement':a.get('is_retirement'),'account.available_tem_services':a.get('available_tem_services'),
      'client.residency_country':a.get('residency_country','US'),'client.qualified_purchaser':a.get('qualified_purchaser',household['aum']>=5_000_000),
      'fa.qualified_for_offering':fa['qualified_for_offering'],'fa.qualified_for_selected_strategy':offering_id in fa['qualified_for_offering'],
      'strategy.requires_qualified_advisor':offering_id in REQUIRES_QUALIFIED_ADVISOR,
      'policy.offering_profile_verified':override('policy.offering_profile_verified',True),
      'target_strategy.is_direct_indexing':False,
      'target_strategy.in_approved_directIndexing_roster':override('target_strategy.in_approved_directIndexing_roster'),
      'target_strategy.in_approved_temSms_roster':override('target_strategy.in_approved_temSms_roster'),
      'target_strategy.restrictions_awaiting_manager_acceptance':override('target_strategy.restrictions_awaiting_manager_acceptance'),
      'target_strategy.is_eligible_cio_etf_strategy':a.get('is_eligible_cio_etf_strategy'),
      'transition.strategy_minimum_met':override('transition.strategy_minimum_met'),'transition.budget_minimum_met':override('transition.budget_minimum_met'),'transition.long_term_budget_selected':override('transition.long_term_budget_selected'),
      'transition.annual_transition_budget':a.get('annual_transition_budget'),
      'scope.has_overlay_ineligible_investments':override('scope.has_overlay_ineligible_investments',False),'scope.overlay_ineligible_investment_ids':[],
      'scope.has_tet_missing_basis':bool(missing),'scope.tet_missing_basis_ids':[x.get('lot_id') or x['sym'] for x in missing],
      'scope.has_individual_fixed_income':bool(fi_lots),'scope.individual_fixed_income_ids':[x.get('lot_id') or x['sym'] for x in fi_lots],
      'scope.has_tma_income_cash':False,'scope.tma_income_cash_ids':[],'scope.has_inaccurate_cost_basis':False,
    }
    return facts

def client_gl(household): return sum(x['mv']-x['cost'] for x in household['holdings'] if x.get('cost') is not None)
def client_harvest(household): return sum(min(0,x['mv']-x['cost']) for x in household['holdings'] if x.get('cost') is not None)
def my_book(fa): return [deepcopy(x) for x in BOOK_ALL if x['advisor_id']==fa]
