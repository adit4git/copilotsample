"""Atlas agent: a tool-using advisor copilot.

Two execution paths share ONE tool registry, so every answer -- live or
fallback -- is grounded in the same deterministic service functions:

1. Live path: the Anthropic Messages API with tool use (Haiku-class model by
   default). The model plans, calls tools, reads results, and may call the
   open_workspace tool to drive the UI to a workspace.
2. Fallback path: a deterministic planner used when no API key is configured
   or the live call fails. It recognizes a bounded set of intents and calls
   the same tools. It is intentionally narrower than the live model and says
   so when a question falls outside what it can plan.

No figure in any answer is produced by the model itself: numbers come from
tool results, which come from the rule engine and service layer.
"""
from __future__ import annotations
import json
import os
import re
from typing import Any

import httpx

from .data import BY_ID, FA_PROFILES, RULE_STORE, PRODUCTS_BY_ID, MODELS_BY_ID, my_book
from .services import (
    all_verdicts, offering_result, cross_sell, nba, tax_desk, enrich,
    transition_scenario, search_products, build_vehicle_brief, content_search,
    _effective_eligible, PROGRAM_LISTS,
)

DEFAULT_AGENT_MODEL = 'claude-haiku-4-5-20251001'
MAX_TOOL_ROUNDS = 6
WORKSPACES = ('client', 'eligibility', 'transition', 'vehicle_compare', 'product_shelf', 'cross_sell',
              'tax_desk', 'meeting_prep_draft', 'book', 'today')
# What each workspace actually shows. Given to the model verbatim so it never
# describes a workspace as containing something it doesn't.
WORKSPACE_GUIDE = {
    'client': "one household's profile: holdings and tax lots, allocation vs CIO target, next best actions",
    'eligibility': "one household's rule-engine verdict for every program and overlay, with the rule trace behind each",
    'transition': 'the trades, gaps, realized gain and tax impact of moving one household into one offering',
    'vehicle_compare': "side-by-side fees, performance, flags and breakeven for chosen products, for one household's capital",
    'product_shelf': 'the full product shelf (every ETF, SMA and direct-indexing product) with filters for vehicle, sleeve, minimum, fee and TLH; no household needed',
    'cross_sell': 'every eligibility-screened cross-sell opportunity across the book',
    'tax_desk': 'the whole book ranked by tax-loss harvesting opportunity',
    'meeting_prep_draft': 'an AI-drafted meeting brief for one household, which the advisor approves, edits or declines',
    'book': 'the list of households with AUM, returns and meetings (no products)',
    'today': 'the daily briefing and ranked next best actions',
}

# ---------------------------------------------------------------- helpers
def _money(n: float | None) -> str:
    if n is None:
        return '\u2014'
    n = float(n)
    if abs(n) >= 1e6:
        v = n/1e6; return f"${v:.1f}M" if round(v, 1) != int(v) else f"${int(v)}M"
    if abs(n) >= 1e3:
        v = n/1e3; return f"${v:.0f}K" if v == int(v) else f"${v:.1f}K"
    return f"${n:,.0f}"

def _when(days: int) -> str:
    return 'today' if days == 0 else ('tomorrow' if days == 1 else f'in {days} days')

def _in_book(fa: str, household_id: str) -> dict:
    hh = BY_ID.get(household_id)
    if not hh or hh['advisor_id'] != fa:
        raise LookupError(f"Household '{household_id}' is not in this advisor's book.")
    return hh

def _offering_label(off: str) -> str:
    return RULE_STORE['offerings'].get(off, {}).get('label', off)

# ------------------------------------------------------------ tool impls
# Each tool returns a compact, JSON-serializable dict (kept small so tool
# results don't balloon the context of a Haiku-class model).
def t_search_households(fa, query: str = '', **_):
    q = query.lower().strip()
    out = []
    for hh in my_book(fa):
        hay = ' '.join([hh['id'], hh['name'], hh.get('contact', ''), hh.get('segment', '')]).lower()
        score = sum(1 for w in re.findall(r'[a-z\u00e0-\u00ff]+', q) if len(w) > 2 and w in hay)
        if not q or score:
            out.append({'household_id': hh['id'], 'name': hh['name'], 'aum': hh['aum'], 'segment': hh['segment'],
                        'next_meeting_in_days': (hh.get('nextMeeting') or {}).get('inDays'), 'score': score})
    out.sort(key=lambda x: (-x['score'], -x['aum']))
    return {'households': out[:8]}

def t_get_household(fa, household_id: str, **_):
    hh = _in_book(fa, household_id); e = enrich(hh)
    top = sorted(hh['holdings'], key=lambda h: -h['mv'])[:5]
    return {
        'household_id': hh['id'], 'name': hh['name'], 'segment': hh['segment'], 'program': hh.get('program', 'IAP'),
        'aum': hh['aum'], 'ytd_return_pct': hh['ytdReturn'], 'risk': hh['risk'],
        'unrealized_gl': e['clientGL'], 'harvestable_losses': abs(e['clientHarvest']), 'illustrative_tax_alpha': e['taxAlpha'],
        'next_meeting': hh.get('nextMeeting'), 'concentration': hh.get('concentration', []),
        'cio': {'drift': hh['cio']['score'], 'view': hh['cio']['view']},
        'top_holdings': [{'sym': h['sym'], 'mv': h['mv'], 'weight_pct': round(h['mv'] / hh['aum'] * 100, 1)} for h in top],
        'incoming_capital': hh.get('incoming_capital'), 'current_model_id': hh.get('current_model_id'),
        'current_implementation': hh.get('current_implementation'),
    }

def t_check_eligibility(fa, household_id: str, offering_id: str | None = None, **_):
    hh = _in_book(fa, household_id)
    enrolled = {**hh.get('programs', {}), **hh.get('overlays', {})}
    if offering_id:
        if offering_id not in RULE_STORE['offerings']:
            raise LookupError(f"Unknown offering '{offering_id}'.")
        r = offering_result(household_id, offering_id)
        # Separate KNOWN failed requirements from UNRESOLVED fields, and state
        # what the verdict means, so the model can't read an unknown field as
        # "eligibility can't be determined" when a known failure already
        # decides it (the engine's AND: a known False outranks an unknown).
        blocking = [x['message'] for x in r['reasons'] + r['internal_only_reasons'] if not x.get('missing_fields')]
        unresolved = r['missing_fields'][:4]
        meaning = {
            'ELIGIBLE': 'Eligible: every applicable requirement is satisfied.',
            'INELIGIBLE': ('Ineligible: at least one requirement is known to fail. This is a final answer; resolving the '
                           'unresolved fields alone would NOT make the household eligible.' if unresolved else
                           'Ineligible: at least one requirement is known to fail.'),
            'NEEDS_REVIEW': 'Not ineligible and not confirmed: a human review or the unresolved fields must be cleared before it can be offered.',
            'CONDITIONAL': 'Eligible subject to the listed conditions being met.',
        }.get(r['verdict'], r['verdict'])
        return {'household_id': household_id, 'offering_id': offering_id, 'label': r['label'], 'verdict': r['verdict'],
                'meaning': meaning, 'enrolled': enrolled.get(offering_id) == 'enrolled',
                'failed_requirements': blocking[:4], 'unresolved_fields': unresolved,
                'iap_enrollment_prerequisite_met': (None if not r.get('prerequisite') else r['prerequisite']['verdict'] == 'ELIGIBLE')}
    rows = []
    for off, r in all_verdicts(household_id).items():
        rows.append({'offering_id': off, 'label': r['label'], 'verdict': r['verdict'],
                     'enrolled': enrolled.get(off) == 'enrolled'})
    return {'household_id': household_id, 'verdicts': rows}

def t_find_cross_sell(fa, household_id: str | None = None, **_):
    rows = cross_sell(fa)
    if household_id:
        _in_book(fa, household_id)
        rows = [r for r in rows if r['household_id'] == household_id]
    return {'opportunities': [{'household_id': r['household_id'], 'name': r['name'], 'offering_id': r['offering_id'],
                               'label': r['label'], 'estimated_annual_value': r['estimated_value']} for r in rows[:10]],
            'total': len(rows)}

def t_rank_book(fa, ranking: str, **_):
    if ranking == 'tax_loss':
        rows = tax_desk(fa)[:6]
        return {'ranking': ranking, 'rows': [{'household_id': r['id'], 'name': r['name'],
                'harvestable_losses': abs(r['clientHarvest']), 'illustrative_tax_alpha': r['taxAlpha']} for r in rows]}
    kind = {'meetings': 'meetings', 'drift': 'drift', 'cio': 'cio', 'largest': 'deep'}.get(ranking)
    if not kind:
        raise LookupError(f"Unknown ranking '{ranking}'.")
    rows = nba(kind, fa)[:6]
    out = []
    for r in rows:
        item = {'household_id': r['id'], 'name': r['name'], 'aum': r['aum']}
        if kind == 'meetings': item['meeting'] = r['nextMeeting']
        if kind == 'drift': item['drift'] = r['drift']
        if kind == 'cio': item['cio'] = {'drift': r['cio']['score'], 'view': r['cio']['view']}
        out.append(item)
    return {'ranking': ranking, 'rows': out}

def t_model_transition(fa, household_id: str, offering_id: str, **_):
    _in_book(fa, household_id)
    s = transition_scenario(household_id, offering_id)
    out = {'household_id': household_id, 'offering_id': offering_id, 'label': s['offering_label'], 'kind': s['kind'],
           'eligibility_verdict': s['eligibility_verdict'], 'currently_enrolled': s['currently_enrolled'],
           'gaps': [f"{g['severity']}: {g['message']}" for g in s['gap_analysis']]}
    if s['kind'] == 'trade_modelable':
        ts = s['target_state']
        out.update({'trade_count': len(s['proposed_trades']), 'sells_total': ts['sells_total'],
                    'realized_gain': ts['realized_gain'], 'harvest_offset': ts['harvest_offset'],
                    'net_taxable_gain': ts['net_taxable_gain'],
                    'est_ongoing_tax_alpha_per_year': ts['estimated_ongoing_annual_tax_alpha']})
    else:
        out['onboarding_steps'] = s['steps']
    return out

def t_search_products(fa, query: str = '', vehicle: str | None = None, sleeve: str | None = None,
                      max_minimum: float | None = None, min_minimum: float | None = None,
                      max_fee_bps: float | None = None, tlh_capable: bool | None = None, **_):
    filters = dict(vehicle=vehicle, sleeve=sleeve, max_minimum=max_minimum, min_minimum=min_minimum,
                   max_fee_bps=max_fee_bps, tlh_capable=tlh_capable)
    allm = search_products(query, limit=10000, **filters)
    out = {'total_matching': len(allm), 'products': [
        {k: p[k] for k in ('product_id', 'name', 'ticker', 'vehicle', 'sleeve', 'fee_bps', 'minimum', 'tlh_capable', 'client_presentable')}
        for p in allm[:12]]}
    if len(allm) > 12:
        out['note'] = f"Showing 12 of {len(allm)}; open the product_shelf workspace to browse all."
    if not allm and any(v is not None for v in (max_minimum, min_minimum, max_fee_bps)):
        # Zero matches on a numeric filter: report what the shelf actually has
        # without it, so the answer can be "none -- they are all $X" rather
        # than a vague "I couldn't find any".
        relaxed = search_products(query, limit=10000, vehicle=vehicle, sleeve=sleeve, tlh_capable=tlh_capable)
        if relaxed:
            mins = sorted({p['minimum'] for p in relaxed})
            fees = sorted({p['fee_bps'] for p in relaxed if p['fee_bps'] is not None})
            out['without_numeric_filters'] = {'count': len(relaxed), 'minimums': mins[:12],
                'fee_bps_range': [fees[0], fees[-1]] if fees else None,
                'products_without_published_fee': sum(1 for p in relaxed if p['fee_bps'] is None)}
    return out

def t_compare_vehicles(fa, household_id: str, product_ids: list[str] | None = None,
                       model_id: str | None = None, amount: float | None = None, **_):
    _in_book(fa, household_id)
    b = build_vehicle_brief(household_id, model_id, amount, product_ids or None)
    c = b['comparison']
    return {'household_id': household_id, 'label': c['model_label'], 'amount': c['amount'],
            'implementations': [{'product_id': r['product_id'], 'name': r['name'], 'vehicle': r['vehicle'],
                                 'fee_bps': r['fee_bps'], 'annual_fee': r['annual_fee_dollars'],
                                 'return_1y': (r['performance'] or {}).get('returns', {}).get('1y'), 'return_3y': (r['performance'] or {}).get('returns', {}).get('3y'),
                                 'tem_overlays': r.get('tem_overlays'), 'minimum': r['minimum'],
                                 'tlh_capable': r['tlh_capable'],
                                 'flags': [f['message'] for f in r['flags']][:2]} for r in c['implementations']],
            'breakevens': [{'product': x['product_name'], 'vs': x['vs_product_name'], 'fee_premium_bps': x['fee_premium_bps'],
                            'breakeven_harvest_pct': x['breakeven_harvest_needed_pct_of_assets'], 'assessment': x['assessment']}
                           for x in c['breakevens']],
            'client_content': [h['title'] for h in b['client_content']][:4], 'content_gap': b['content_gap'],
            'product_ids': [r['product_id'] for r in c['implementations']], 'model_id': c['model_id']}

def t_search_content(fa, query: str, model_id: str | None = None, **_):
    hits = content_search(query, model_id=model_id, limit=6)
    return {'documents': [{'title': h['title'], 'page': h['page'], 'client_safe': h['client_safe'],
                           'flags': [f['severity'] for f in h['flags']], 'snippet': h['snippet'][:220]} for h in hits]}

def t_open_workspace(fa, workspace: str, household_id: str | None = None, offering_id: str | None = None,
                     product_ids: list[str] | None = None, model_id: str | None = None,
                     auto_open: bool = False, label: str | None = None,
                     shelf_query: str | None = None, vehicle: str | None = None, sleeve: str | None = None,
                     max_minimum: float | None = None, amount: float | None = None, **_):
    """Validates a UI navigation request and turns it into an action the
    frontend executes. Nothing is navigated server-side."""
    if workspace not in WORKSPACES:
        raise LookupError(f"Unknown workspace '{workspace}'. Valid: {', '.join(WORKSPACES)}.")
    needs_hh = workspace in ('client', 'eligibility', 'transition', 'vehicle_compare', 'meeting_prep_draft')
    if needs_hh:
        if not household_id:
            raise LookupError(f"Workspace '{workspace}' needs a household_id.")
        hh = _in_book(fa, household_id)
    if workspace == 'transition':
        if offering_id not in RULE_STORE['offerings']:
            raise LookupError('Transition workspace needs a valid offering_id.')
    if workspace == 'meeting_prep_draft' and not hh.get('nextMeeting'):
        raise LookupError(f"{hh['name']} has no scheduled meeting to prepare for.")
    if workspace == 'vehicle_compare':
        if product_ids:
            bad = [p for p in product_ids if p not in PRODUCTS_BY_ID]
            if bad:
                raise LookupError(f"Unknown product_ids: {', '.join(bad)}")
        elif not (model_id or hh.get('current_model_id')):
            raise LookupError('Vehicle comparison needs product_ids or a model_id for this household.')
    default_labels = {
        'client': 'Open client profile', 'eligibility': 'Open eligibility screen', 'transition': f"Open transition workbench \u00b7 {_offering_label(offering_id) if offering_id else ''}",
        'vehicle_compare': 'Open vehicle comparison', 'cross_sell': 'Open Cross-Sell Radar', 'tax_desk': 'Open Tax Overlay Desk',
        'meeting_prep_draft': 'Open meeting-prep draft', 'book': 'Open Book of Business', 'today': 'Open Today',
        'product_shelf': 'Open Product Shelf',
    }
    action = {'type': 'navigate', 'workspace': workspace, 'household_id': household_id, 'offering_id': offering_id,
              'product_ids': product_ids or None, 'model_id': model_id, 'auto_open': bool(auto_open),
              'label': label or default_labels[workspace],
              'amount': amount if workspace == 'vehicle_compare' else None,
              'shelf_filters': ({'q': shelf_query or '', 'vehicle': vehicle, 'sleeve': sleeve, 'max_minimum': max_minimum}
                                if workspace == 'product_shelf' else None)}
    return {'ok': True, 'action': action}

TOOL_IMPLS = {
    'search_households': t_search_households, 'get_household': t_get_household,
    'check_eligibility': t_check_eligibility, 'find_cross_sell': t_find_cross_sell,
    'rank_book': t_rank_book, 'model_transition': t_model_transition,
    'search_products': t_search_products, 'compare_vehicles': t_compare_vehicles,
    'search_content': t_search_content, 'open_workspace': t_open_workspace,
}

# Anthropic tool schemas (input_schema is JSON Schema).
TOOL_SCHEMAS = [
    {'name': 'search_households', 'description': "Find households in the advisor's book by name, contact or id. Use when the user names a client you have not resolved to a household_id yet.",
     'input_schema': {'type': 'object', 'properties': {'query': {'type': 'string'}}, 'required': ['query']}},
    {'name': 'get_household', 'description': 'Snapshot of one household: AUM, returns, top holdings, concentration, CIO drift, next meeting, tax figures, incoming capital, current research model.',
     'input_schema': {'type': 'object', 'properties': {'household_id': {'type': 'string'}}, 'required': ['household_id']}},
    {'name': 'check_eligibility', 'description': 'Rule-engine eligibility verdicts (ELIGIBLE / INELIGIBLE / NEEDS_REVIEW / CONDITIONAL). Pass offering_id for one offering with reasons, or omit it for every offering.',
     'input_schema': {'type': 'object', 'properties': {'household_id': {'type': 'string'}, 'offering_id': {'type': 'string'}}, 'required': ['household_id']}},
    {'name': 'find_cross_sell', 'description': 'Eligibility-screened cross-sell opportunities (eligible, not enrolled), book-wide or for one household.',
     'input_schema': {'type': 'object', 'properties': {'household_id': {'type': 'string'}}}},
    {'name': 'rank_book', 'description': 'Rank the whole book. ranking: meetings (soonest first), drift (concentration breaches), cio (house-view drift), largest (by AUM), tax_loss (harvesting opportunity).',
     'input_schema': {'type': 'object', 'properties': {'ranking': {'type': 'string', 'enum': ['meetings', 'drift', 'cio', 'largest', 'tax_loss']}}, 'required': ['ranking']}},
    {'name': 'model_transition', 'description': 'Model moving a household into an offering: gap analysis plus proposed trades, realized gain, harvest offset, net taxable gain, ongoing tax alpha (or onboarding steps for procedural offerings).',
     'input_schema': {'type': 'object', 'properties': {'household_id': {'type': 'string'}, 'offering_id': {'type': 'string'}}, 'required': ['household_id', 'offering_id']}},
    {'name': 'search_products', 'description': "Search or filter the full product shelf (ETFs, SMAs, direct indexing). query matches ticker, fund name, manager, sleeve or asset class and may be empty to list by filters alone. Filters: vehicle, sleeve, min/max account minimum in dollars, max fee in bps, tlh_capable. Returns product_ids (for compare_vehicles), each product's minimum and fee, and total_matching. If a numeric filter matches nothing, 'without_numeric_filters' reports the actual minimums and fees on the shelf -- use it to answer precisely (e.g. 'none; all SMAs have a $250,000 minimum').",
     'input_schema': {'type': 'object', 'properties': {'query': {'type': 'string'}, 'vehicle': {'type': 'string', 'enum': ['ETF', 'SMA', 'DIRECT_INDEXING']},
                      'sleeve': {'type': 'string'}, 'min_minimum': {'type': 'number'}, 'max_minimum': {'type': 'number'},
                      'max_fee_bps': {'type': 'number'}, 'tlh_capable': {'type': 'boolean'}}}},
    {'name': 'compare_vehicles', 'description': "Compare investment vehicles for a household's capital: fees in bps and dollars, matched-basis performance, TLH capability, compliance flags, breakeven harvesting vs the cheapest ETF, and client-approved content. Pass product_ids from search_products, or a model_id, or neither to use the household's current research model.",
     'input_schema': {'type': 'object', 'properties': {'household_id': {'type': 'string'}, 'product_ids': {'type': 'array', 'items': {'type': 'string'}},
                      'model_id': {'type': 'string'}, 'amount': {'type': 'number'}}, 'required': ['household_id']}},
    {'name': 'search_content', 'description': 'Search CIO / marketing content. Each result says whether it is client-safe (approved, unexpired). Never offer a non-client-safe document for a client.',
     'input_schema': {'type': 'object', 'properties': {'query': {'type': 'string'}, 'model_id': {'type': 'string'}}, 'required': ['query']}},
    {'name': 'open_workspace', 'description': "Offer (or, with auto_open, perform) navigation to an Atlas workspace. Use after gathering facts so the advisor can act. Set auto_open=true only when the user explicitly asked to open / go to / take them somewhere. For product_shelf you may pass shelf_query, vehicle, sleeve and max_minimum to pre-filter it. Workspaces: " + '; '.join(f"{k} = {v}" for k, v in WORKSPACE_GUIDE.items()),
     'input_schema': {'type': 'object', 'properties': {
         'workspace': {'type': 'string', 'enum': list(WORKSPACES)}, 'household_id': {'type': 'string'},
         'offering_id': {'type': 'string'}, 'product_ids': {'type': 'array', 'items': {'type': 'string'}},
         'model_id': {'type': 'string'}, 'auto_open': {'type': 'boolean'}, 'label': {'type': 'string'},
         'shelf_query': {'type': 'string'}, 'vehicle': {'type': 'string', 'enum': ['ETF', 'SMA', 'DIRECT_INDEXING']},
         'sleeve': {'type': 'string'}, 'max_minimum': {'type': 'number'},
         'amount': {'type': 'number', 'description': 'Dollar amount under consideration, for vehicle_compare.'}}, 'required': ['workspace']}},
]

def execute_tool(fa: str, name: str, args: dict) -> tuple[dict, dict | None]:
    """Run one tool. Returns (result, action). Errors become a structured
    {'error': ...} result the model can read and recover from -- never an
    exception that kills the conversation."""
    fn = TOOL_IMPLS.get(name)
    if not fn:
        return {'error': f"Unknown tool '{name}'."}, None
    try:
        res = fn(fa, **(args or {}))
    except (LookupError, KeyError, TypeError, ValueError) as e:
        return {'error': str(e).strip("'\"")}, None
    action = res.get('action') if name == 'open_workspace' else None
    return res, action

def _step_summary(name: str, args: dict, res: dict) -> str:
    if 'error' in res:
        return f"error: {res['error']}"
    if name == 'search_households':
        return ', '.join(h['name'] for h in res['households'][:3]) or 'no matches'
    if name == 'get_household':
        return f"{res['name']} \u00b7 {_money(res['aum'])} AUM"
    if name == 'check_eligibility':
        return f"{res['label']}: {res['verdict']}" if 'verdict' in res else f"{len(res['verdicts'])} offerings screened"
    if name == 'find_cross_sell':
        return f"{res['total']} opportunities"
    if name == 'rank_book':
        return f"{res['ranking']}: " + ', '.join(r['name'] for r in res['rows'][:3])
    if name == 'model_transition':
        return f"{res['label']} \u00b7 {res['kind'].replace('_', ' ')}" + (f" \u00b7 net taxable {_money(res.get('net_taxable_gain'))}" if res['kind'] == 'trade_modelable' else '')
    if name == 'search_products':
        return ', '.join((p['ticker'] or p['vehicle']) for p in res['products'][:5]) or 'no matches'
    if name == 'compare_vehicles':
        return f"{len(res['implementations'])} vehicles \u00b7 {_money(res['amount'])}"
    if name == 'search_content':
        return f"{len(res['documents'])} documents"
    if name == 'open_workspace':
        return res['action']['label']
    return 'done'

# ----------------------------------------------------------- live path
def _system_prompt(fa: str, context: dict | None) -> str:
    prof = FA_PROFILES[fa]
    book = my_book(fa)
    hh_lines = '\n'.join(f"- {h['id']}: {h['name']} ({h['segment']}, {_money(h['aum'])})" for h in book)
    off_lines = '\n'.join(f"- {k}: {v['label']}" for k, v in RULE_STORE['offerings'].items())
    model_lines = '\n'.join(f"- {k}: {m['label']}" for k, m in MODELS_BY_ID.items())
    ctx = context or {}
    focus = ctx.get('household_id')
    focus_line = (f"The advisor is currently looking at household '{focus}' ({BY_ID[focus]['name']}) in the "
                  f"'{ctx.get('view', 'unknown')}' view. Resolve 'this client', 'they', 'them' to it unless the user names someone else."
                  if focus in BY_ID and BY_ID[focus]['advisor_id'] == fa else
                  "No household is in focus; ask or search if the user refers to a client ambiguously.")
    return f"""You are Atlas, an agentic copilot for {prof['name']}, a senior wealth advisor. You work inside the Atlas advisor console.

Rules:
- Every number, verdict, fee, return and trade you state must come from a tool result in this conversation. Never estimate or invent figures, holdings, eligibility or policy.
- Eligibility is decided by the rule engine (check_eligibility). Report ELIGIBLE, INELIGIBLE, NEEDS_REVIEW and CONDITIONAL exactly; NEEDS_REVIEW is not ineligible.
- For vehicle questions (ETF vs SMA vs direct indexing), resolve products with search_products, then call compare_vehicles. Never present hypothetical/backtested performance or non-client-safe content as something to give a client.
- When the advisor asks you to compare, model, draft, prepare or open something, do the work, then call open_workspace for that workspace with auto_open=true. The workspace shows the detail, so keep your chat reply to 2-4 sentences with the key numbers. Do not reproduce comparison tables in chat.
- For informational questions, answer in chat and call open_workspace (auto_open=false) to offer the most useful next workspace.
- When the advisor states an amount (e.g. "1m incoming"), pass it as amount to compare_vehicles and open_workspace.
- Harvestable losses in a household's existing holdings do not offset fees on new money. Never say a fee premium "pays for itself"; report the breakeven and its assessment exactly as the tool gives them.
- For eligibility, state the verdict and its 'meaning' field faithfully. INELIGIBLE with a failed requirement is final even if some fields are unresolved; do not describe it as undetermined.
- Only describe a workspace using the workspace descriptions below. Never claim a workspace shows something it does not. Products live in product_shelf (no household needed), not in book.
- Never mention tool or function names (like search_products) to the advisor; describe what you did in plain language.
- Try the tools' filters before saying you can't answer. If a filter returns nothing, say so and report what the data does show.
- Don't narrate your process ("Let me check..."); gather what you need, then answer.
- Be concise: short paragraphs or a few bullets, lead with the answer. Use markdown bold sparingly.
- If a request is outside the advisor's book or what the tools can support, say so plainly.

{focus_line}

Households in this advisor's book (household_id: name):
{hh_lines}

Offerings (offering_id: label):
{off_lines}

Research models (model_id: label):
{model_lines}

Workspaces (what each one shows):
{chr(10).join(f"- {k}: {v}" for k, v in WORKSPACE_GUIDE.items())}
"""

async def _anthropic_call(payload: dict) -> dict:
    """Single Messages API request. Kept as its own function so tests can
    replace it with a scripted fake and exercise the full tool loop."""
    timeout = float(os.getenv('ATLAS_LLM_TIMEOUT', '20'))
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post('https://api.anthropic.com/v1/messages',
                              headers={'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01',
                                       'content-type': 'application/json'}, json=payload)
        r.raise_for_status()
        return r.json()

def live_enabled() -> bool:
    return bool(os.getenv('ANTHROPIC_API_KEY')) and os.getenv('ATLAS_AGENT_MODE', 'auto').lower() != 'local'

async def run_live(fa: str, message: str, history: list[dict], context: dict | None) -> dict:
    messages = []
    for h in (history or [])[-8:]:
        role = 'assistant' if h.get('role') in ('assistant', 'bot') else 'user'
        text = (h.get('content') or '').strip()
        if text:
            if messages and messages[-1]['role'] == role:
                messages[-1]['content'] += '\n\n' + text
            else:
                messages.append({'role': role, 'content': text})
    if messages and messages[0]['role'] == 'assistant':
        messages = messages[1:]
    if messages and messages[-1]['role'] == 'user':
        messages[-1]['content'] += '\n\n' + message
    else:
        messages.append({'role': 'user', 'content': message})
    system = _system_prompt(fa, context)
    model = os.getenv('ATLAS_AGENT_MODEL', DEFAULT_AGENT_MODEL)
    steps, actions, work, texts = [], [], [], []
    usage = {'input_tokens': 0, 'output_tokens': 0}
    for _ in range(MAX_TOOL_ROUNDS):
        resp = await _anthropic_call({'model': model, 'max_tokens': 1024, 'system': system,
                                      'tools': TOOL_SCHEMAS, 'messages': messages})
        u = resp.get('usage') or {}
        usage['input_tokens'] += u.get('input_tokens', 0); usage['output_tokens'] += u.get('output_tokens', 0)
        blocks = resp.get('content', [])
        # Keep text from EVERY round: the model often writes its answer, then
        # calls a tool (e.g. open_workspace), then adds a closing line. Keeping
        # only the last round's text silently dropped the actual answer.
        round_text = '\n'.join(b.get('text', '') for b in blocks if b.get('type') == 'text').strip()
        tool_uses = [b for b in blocks if b.get('type') == 'tool_use']
        if round_text and not (tool_uses and _is_narration(round_text)):
            texts.append(round_text)
        if resp.get('stop_reason') != 'tool_use' or not tool_uses:
            return {'content': '\n\n'.join(texts) or 'Done.', 'mode': f'live:{model}', 'steps': steps,
                    'actions': finalize_actions(fa, message, work, actions), 'usage': usage}
        messages.append({'role': 'assistant', 'content': blocks})
        results = []
        for b in tool_uses:
            res, action = execute_tool(fa, b['name'], b.get('input') or {})
            if action:
                actions.append(action)
            work.append((b['name'], b.get('input') or {}, res))
            steps.append({'tool': b['name'], 'input': b.get('input') or {}, 'summary': _step_summary(b['name'], b.get('input') or {}, res)})
            results.append({'type': 'tool_result', 'tool_use_id': b['id'], 'content': json.dumps(res, default=str)[:6000],
                            **({'is_error': True} if 'error' in res else {})})
        messages.append({'role': 'user', 'content': results})
    return {'content': '\n\n'.join(texts + ['I hit my step limit before finishing; the workspace links below still apply.']),
            'mode': f'live:{model}', 'steps': steps, 'actions': finalize_actions(fa, message, work, actions), 'usage': usage}

# ------------------------------------------------------- fallback planner
OFFERING_ALIASES = {
    'transition': ['tax efficient transition', 'tax-efficient transition', 'tet'],
    'directIndexing': ['direct indexing', 'direct-indexing', 'direct index'],
    'taxManagedSMA': ['tax efficient rebalancing', 'tax-managed sma', 'tax managed sma', 'ter'],
    'qlhOverlay': ['quarterly loss harvesting', 'qlh'],
    'dtlhOverlay': ['dynamic tax loss harvesting', 'daily tax loss harvesting', 'dtlh'],
    'temSms': ['tem style manager', 'style manager', 'tem sms'],
    'mgiTer': ['guided investing ter', 'mgi ter'], 'mgiQlh': ['guided investing qlh', 'mgi qlh'],
    'mgiDtlh': ['guided investing dtlh', 'mgi dtlh'],
    'alternatives': ['alternatives', 'alternative investments', 'alts'],
    'privateBanking': ['private banking', 'private bank'], 'trustEstate': ['trust and estate', 'trust & estate', 'estate planning'],
    'lending': ['securities based lending', 'securities-based lending', 'lending', 'credit line', 'sbl'],
    'insurance': ['insurance', 'annuity'], 'charitable': ['charitable', 'gifting', 'donor advised', 'daf'],
    'iapEnrollment': ['iap enrollment', 'iap agreement'],
}

def resolve_offering(text: str) -> str | None:
    """Longest-alias match on word boundaries. Deliberately does NOT treat the
    bare word 'transition' as TET: 'model a direct indexing transition'
    must resolve to directIndexing, not to the TET offering whose id happens
    to be 'transition' -- a bug found in an earlier reconstruction of this
    agent, where plain substring matching sent that request to TET."""
    t = ' ' + re.sub(r'[^a-z0-9&\- ]', ' ', text.lower()) + ' '
    best, best_len = None, 0
    for off, aliases in OFFERING_ALIASES.items():
        for a in aliases:
            if re.search(r'(?<![a-z])' + re.escape(a) + r'(?![a-z])', t) and len(a) > best_len:
                best, best_len = off, len(a)
    return best

def resolve_household(fa: str, text: str, context: dict | None) -> tuple[str | None, bool]:
    """Returns (household_id, came_from_context)."""
    low = text.lower()
    best, best_score = None, 0
    for hh in my_book(fa):
        names = [w for w in re.findall(r"[a-z\u00e0-\u00ff\-]+", (hh['name'] + ' ' + hh.get('contact', '')).lower())
                 if len(w) > 3 and w not in ('family', 'household', 'trust', 'holdings', 'living', 'foundation', 'paul', 'margaret')]
        score = sum(3 for w in names if re.search(r'(?<![a-z])' + re.escape(w) + r"s?(?![a-z])", low))
        if hh['id'] in low: score += 5
        if score > best_score:
            best, best_score = hh['id'], score
    if best:
        return best, False
    ctx_id = (context or {}).get('household_id')
    if ctx_id in BY_ID and BY_ID[ctx_id]['advisor_id'] == fa:
        return ctx_id, True
    return None, False

def resolve_products(text: str) -> list[str]:
    """Tickers mentioned in the message. Short tickers must be written in
    capitals (so 'shy' or 'tip' as English words don't match); 4+ letter
    tickers match case-insensitively."""
    tickers = {p['ticker']: p['product_id'] for p in PRODUCTS_BY_ID.values() if p.get('ticker') and p['client_presentable']}
    found = []
    for tok in re.findall(r'\b[A-Za-z]{2,5}\b', text):
        up = tok.upper()
        if up in tickers and (tok.isupper() or len(tok) >= 4) and tickers[up] not in found:
            found.append(tickers[up])
    return found

EXPLICIT_NAV = re.compile(r'\b(open|take me|go to|goto|navigate|pull up|bring up|show me the|launch)\b', re.I)
# Requests that ask Atlas to DO workspace work (not just answer a question).
# For these the matching workspace opens automatically once the work is done.
WORK_INTENT = re.compile(r'\b(compare|comparison|model|modell?ing|draft|prep|prepare|deploy|walk me through|proposal|open|take me|go to|pull up|bring up|show me the|launch)\b', re.I)

NARRATION = re.compile(r"^(let me|let's|i'll|i will|i'm going to|i am going to|now i'll|now let me|first,? i'll|checking|looking (?:that|this|it) up|one moment)\b", re.I)

def _is_narration(text: str) -> bool:
    """'Let me look that up.' -- a short, single-sentence preamble to a tool
    call, not part of the answer."""
    s = text.strip()
    return len(s) < 140 and s.count('. ') == 0 and '\n' not in s and bool(NARRATION.match(s))

def wants_navigation(message: str) -> bool:
    return bool(WORK_INTENT.search(message or ''))

def finalize_actions(fa: str, message: str, work: list[tuple[str, dict, dict]], actions: list[dict]) -> list[dict]:
    """Make navigation deterministic instead of relying on the model to call
    open_workspace. For the most recent successful compare_vehicles or
    model_transition: add the matching workspace action if missing, carry the
    exact products and amount into it, and auto-open it when the advisor asked
    for that work. Informational questions still get buttons, never a jump."""
    actions = list(actions)
    primary = None
    for name, args, res in reversed(work):
        if 'error' in res:
            continue
        if name == 'compare_vehicles':
            spec = {'workspace': 'vehicle_compare', 'household_id': res['household_id'],
                    'product_ids': res['product_ids'], 'model_id': res['model_id'], 'amount': res['amount']}
        elif name == 'model_transition':
            spec = {'workspace': 'transition', 'household_id': res['household_id'], 'offering_id': res['offering_id']}
        else:
            continue
        existing = next((a for a in actions if a['workspace'] == spec['workspace'] and a.get('household_id') == spec['household_id']), None)
        if existing:
            for k, v in spec.items():          # fill anything the model left out (e.g. amount)
                if existing.get(k) in (None, [], '') and v not in (None, []):
                    existing[k] = v
            primary = existing
        else:
            _, act = execute_tool(fa, 'open_workspace', spec)
            if act:
                actions.insert(0, act); primary = act
        break
    if wants_navigation(message):
        if primary is not None:
            for a in actions:
                a['auto_open'] = a is primary
        elif actions and not any(a['auto_open'] for a in actions):
            actions[0]['auto_open'] = True
    else:
        for a in actions:
            a['auto_open'] = False
    seen, out = set(), []
    for a in actions:
        key = (a['workspace'], a.get('household_id'), a.get('offering_id'), tuple(a.get('product_ids') or ()))
        if key not in seen:
            seen.add(key); out.append(a)
    return out

def parse_amount(text: str) -> float | None:
    """'1m', '$1,000,000', '2.5 million', '750k' -> dollars. Ignores small
    numbers (under $10K) so '3y' or '5 accounts' are never read as amounts."""
    for m in re.finditer(r'\$?\s*(\d[\d,]*(?:\.\d+)?)\s*(k|m|mm|mn|million|thousand)?\b', text.lower()):
        n = float(m.group(1).replace(',', ''))
        n *= {'k': 1e3, 'thousand': 1e3, 'm': 1e6, 'mm': 1e6, 'mn': 1e6, 'million': 1e6}.get(m.group(2) or '', 1)
        if n >= 10_000:
            return n
    return None

def run_local(fa: str, message: str, context: dict | None, history: list[dict] | None = None) -> dict:
    steps, actions, parts, work = [], [], [], []
    low = message.lower()
    auto = wants_navigation(message)

    def call(name, **args):
        res, action = execute_tool(fa, name, args)
        steps.append({'tool': name, 'input': args, 'summary': _step_summary(name, args, res)})
        work.append((name, args, res))
        if action:
            actions.append(action)
        return res

    hid, from_ctx = resolve_household(fa, message, None)
    if not hid:
        # Follow-ups like "yes, compare options for deploying 1m" name no one:
        # use the most recent household the advisor mentioned in this chat,
        # then fall back to the one open in the UI.
        for h in reversed([x for x in (history or []) if x.get('role') == 'user']):
            hid, _ = resolve_household(fa, h.get('content') or '', None)
            if hid:
                break
        if not hid:
            hid, from_ctx = resolve_household(fa, '', context)
    amount = parse_amount(message)
    if amount is None:
        for h in reversed([x for x in (history or []) if x.get('role') == 'user'][-3:]):
            amount = parse_amount(h.get('content') or '')
            if amount:
                break
    off = resolve_offering(message)
    prods = resolve_products(message)
    hname = BY_ID[hid]['name'] if hid else None
    ctx_note = f" (using {hname} from your current view)" if from_ctx else ''

    wants_compare = bool(prods) or bool(re.search(r'\b(etfs?|smas?|vehicles?|compare|comparison|versus|vs\.?|implementation|expense ratio)\b', low))
    wants_transition = bool(re.search(r'\b(transition|move (?:them|him|her|into|to)|switch|convert|model (?:a|the)?\s*\w*)\b', low)) and off is not None
    wants_elig = bool(re.search(r'\b(eligib|qualif|can (?:they|he|she)|allowed)', low))
    wants_draft = bool(re.search(r'meeting prep|prep (?:me|for)|draft', low))
    wants_tax = bool(re.search(r'harvest|tax[- ]loss|tlh|tax alpha', low))
    wants_cross = bool(re.search(r'cross[- ]?sell|upsell', low)) or (bool(re.search(r'opportunit', low)) and not wants_tax)
    wants_drift = bool(re.search(r'drift|concentrat|breach|overweight', low))
    wants_meet = bool(re.search(r'\bmeetings?\b|this week|upcoming', low)) and not wants_draft
    wants_products = (bool(re.search(r'\b(find|search|list|which|what|show)\b.*\b(etfs?|smas?|funds?|products?)\b', low))
                      or 'product shelf' in low or re.search(r'\bshelf\b', low) is not None) and not (hid and wants_compare)

    if wants_draft and hid:
        res, action = execute_tool(fa, 'open_workspace', {'workspace': 'meeting_prep_draft', 'household_id': hid, 'auto_open': True})
        steps.append({'tool': 'open_workspace', 'input': {'workspace': 'meeting_prep_draft', 'household_id': hid}, 'summary': _step_summary('open_workspace', {}, res)})
        if action: actions.append(action)
        parts.append(f"Opening a meeting-prep draft for **{hname}**{ctx_note} \u2014 you'll review, edit, approve or decline it before it's used.")
    elif wants_transition and hid:
        r = call('model_transition', household_id=hid, offering_id=off)
        if 'error' in r:
            parts.append(f"I couldn't model that: {r['error']}")
        elif r['kind'] == 'trade_modelable':
            parts.append(f"**{r['label']}** for **{hname}**{ctx_note}: eligibility {r['eligibility_verdict']}. "
                         f"{r['trade_count']} proposed trades reallocate {_money(r['sells_total'])}, realizing {_money(r['realized_gain'])} of gains "
                         f"offset by {_money(r['harvest_offset'])} of harvested losses \u2014 **{_money(r['net_taxable_gain'])} net taxable**, "
                         f"with an estimated {_money(r['est_ongoing_tax_alpha_per_year'])}/yr of ongoing tax alpha (illustrative).")
            if r['gaps']:
                parts.append('Gaps: ' + '; '.join(r['gaps'][:2]))
        else:
            parts.append(f"**{r['label']}** for **{hname}** is a procedural onboarding (eligibility {r['eligibility_verdict']}), "
                         f"{len(r['onboarding_steps'])} steps starting with: {r['onboarding_steps'][0]}")
        call('open_workspace', workspace='transition', household_id=hid, offering_id=off, auto_open=True)
    elif wants_compare and hid:
        if prods:
            mid = BY_ID[hid].get('current_model_id')
            impls = [PRODUCTS_BY_ID[p] for p in MODELS_BY_ID[mid]['implementations']] if mid in MODELS_BY_ID else []
            if re.search(r'\bsmas?\b', low):
                prods += [p['product_id'] for p in impls if p['vehicle'] == 'SMA' and p['product_id'] not in prods]
            if off == 'directIndexing' or 'direct index' in low:
                prods += [p['product_id'] for p in impls if p['vehicle'] == 'DIRECT_INDEXING' and p['product_id'] not in prods]
        r = call('compare_vehicles', household_id=hid, product_ids=prods or None, amount=amount)
        if 'error' in r:
            parts.append(f"I couldn't compare those vehicles: {r['error']}")
        else:
            tlh_tag = ' \u00b7 TLH'
            lines = [f"- **{i['name']}** ({i['vehicle'].replace('_', ' ').lower()}): " + (f"{i['fee_bps']} bps = {_money(i['annual_fee'])}/yr, " if i['fee_bps'] is not None else 'fee per Strategy Profile, ') + (f"3y {i['return_3y']*100:.1f}%" if i['return_3y'] is not None else 'no published performance') + (tlh_tag if i['tlh_capable'] else '') for i in r['implementations'][:6]]
            parts.append(f"Vehicle comparison for **{hname}** on {_money(r['amount'])}{ctx_note} ({r['label']}):\n" + '\n'.join(lines))
            if r['breakevens']:
                b = r['breakevens'][0]
                parts.append(f"{b['product']} costs {b['fee_premium_bps']} bps more than {b['vs']}; it breaks even if harvesting realizes about "
                             f"{b['breakeven_harvest_pct']*100:.2f}% of assets a year. {b['assessment']}")
            parts.append('Client-approved content: ' + (', '.join(r['client_content']) if r['client_content'] else 'none found (content gap).'))
            call('open_workspace', workspace='vehicle_compare', household_id=hid, product_ids=r['product_ids'], model_id=r['model_id'], amount=r['amount'], auto_open=True)
    elif wants_elig and hid:
        if off:
            r = call('check_eligibility', household_id=hid, offering_id=off)
            if 'error' in r:
                parts.append(r['error'])
            else:
                why = (' Failed: ' + '; '.join(x.rstrip('.') for x in r['failed_requirements'][:2]) + '.') if r['failed_requirements'] else ''
                unres = (' Unresolved data: ' + ', '.join(f.replace('account.', '').replace('_', ' ') for f in r['unresolved_fields']) + '.') if r['unresolved_fields'] else ''
                pre = " Separately, the IAP enrollment prerequisite is not met." if r.get('iap_enrollment_prerequisite_met') is False else ''
                parts.append(f"**{hname}** \u2014 {r['label']}: **{r['verdict']}**{' (already enrolled)' if r['enrolled'] else ''}. {r['meaning']}{why}{unres}{pre}{ctx_note}")
                if r['verdict'] == 'ELIGIBLE' and not r['enrolled'] and off != 'iapEnrollment':
                    call('open_workspace', workspace='transition', household_id=hid, offering_id=off, label=f"Model transition into {r['label']}")
        else:
            r = call('check_eligibility', household_id=hid)
            elig = [v['label'] for v in r['verdicts'] if v['verdict'] == 'ELIGIBLE' and not v['enrolled'] and v['offering_id'] != 'iapEnrollment']
            review = [v['label'] for v in r['verdicts'] if v['verdict'] == 'NEEDS_REVIEW']
            parts.append(f"**{hname}**{ctx_note}: eligible and not yet enrolled for {', '.join(elig) if elig else 'nothing new'}."
                         + (f" Needs review: {', '.join(review)}." if review else ''))
        call('open_workspace', workspace='eligibility', household_id=hid, auto_open=auto)
    elif wants_cross:
        r = call('find_cross_sell', household_id=hid)
        rows = r['opportunities']
        who = f" for **{hname}**" if hid else ' across your book'
        parts.append(f"{r['total']} eligibility-screened cross-sell opportunities{who}" + (':' if rows else '.'))
        if rows:
            parts.append('\n'.join(f"- {x['name']}: {x['label']}" for x in rows[:6]))
        call('open_workspace', workspace='cross_sell', auto_open=auto)
    elif wants_tax and not hid:
        r = call('rank_book', ranking='tax_loss')
        parts.append('Largest harvesting opportunities:\n' + '\n'.join(
            f"- {x['name']}: {_money(x['harvestable_losses'])} harvestable (~{_money(x['illustrative_tax_alpha'])} illustrative tax value)" for x in r['rows'][:5]))
        call('open_workspace', workspace='tax_desk', auto_open=auto)
    elif wants_drift and not hid:
        r = call('rank_book', ranking='drift')
        parts.append('Concentration breaches:\n' + '\n'.join(
            f"- {x['name']}: {x['drift']['label']} at {x['drift']['pct']}% vs {x['drift']['threshold']}% limit" for x in r['rows'][:5]))
    elif wants_meet and not hid:
        r = call('rank_book', ranking='meetings')
        parts.append('Upcoming meetings:\n' + '\n'.join(
            f"- {x['name']}: {x['meeting']['type']} {_when(x['meeting']['inDays'])}" for x in r['rows'][:6]))
    elif wants_products:
        veh = 'SMA' if re.search(r'\bsmas?\b', low) else ('ETF' if re.search(r'\betfs?\b', low) else ('DIRECT_INDEXING' if 'direct index' in low else None))
        m = re.search(r'minimum[s]?\s*(?:of|under|below|up to|<=?|at most)?\s*\$?([\d,.]+)\s*(k|m|mm)?\b', low)
        max_min = None
        if m:
            max_min = float(m.group(1).replace(',', '')) * {'k': 1e3, 'm': 1e6, 'mm': 1e6}.get(m.group(2) or '', 1)
        q = re.sub(r'minimum[s]?\s*(?:of|under|below|up to|<=?|at most)?\s*\$?[\d,.]+\s*(?:k|m|mm)?', ' ', low)
        q = re.sub(r'\b(find|search|list|which|what|show|me|the|are|is|for|a|an|have|has|with|etfs?|smas?|funds?|products?|product|shelf|on|our|all|open|it|direct|indexing)\b', ' ', q)
        q = ' '.join(re.findall(r'[a-z0-9&]+', q))
        r = call('search_products', query=q, vehicle=veh, max_minimum=max_min)
        what = {'SMA': 'SMAs', 'ETF': 'ETFs', 'DIRECT_INDEXING': 'direct-indexing products'}.get(veh, 'products')
        if r['total_matching']:
            parts.append(f"{r['total_matching']} {what} on the shelf" + (f" with a minimum of {_money(max_min)} or less" if max_min else '') + ':\n'
                         + '\n'.join(f"- {p['name']}{' (' + p['ticker'] + ')' if p['ticker'] else ''}: {(str(p['fee_bps']) + ' bps') if p['fee_bps'] is not None else 'fee per Strategy Profile'}, {_money(p['minimum']) if p['minimum'] else 'no'} minimum" for p in r['products'][:8]))
        elif r.get('without_numeric_filters'):
            w = r['without_numeric_filters']
            parts.append(f"None. No {what} on the shelf have a minimum of {_money(max_min)} or less; the lowest minimum among all {w['count']} is {_money(w['minimums'][0])}.")
        else:
            parts.append('No matching products on the shelf.')
        call('open_workspace', workspace='product_shelf', vehicle=veh, max_minimum=max_min, shelf_query=q or None, auto_open=True)
    elif hid:
        r = call('get_household', household_id=hid)
        conc = r['concentration'][0] if r['concentration'] else None
        parts.append(f"**{r['name']}**{ctx_note}: {_money(r['aum'])} AUM, {r['ytd_return_pct']}% YTD, {_money(r['unrealized_gl'])} unrealized, "
                     f"{_money(r['harvestable_losses'])} harvestable."
                     + (f" Concentration: {conc['label']} at {conc['pct']}% vs {conc['threshold']}% limit." if conc else '')
                     + (f" Next meeting {_when(r['next_meeting']['inDays'])} ({r['next_meeting']['type']})." if r['next_meeting'] else ''))
        call('open_workspace', workspace='client', household_id=hid, auto_open=auto)
    else:
        parts.append("I can screen eligibility, model transitions, compare ETFs, SMAs and direct indexing from the full shelf, "
                     "find cross-sell and harvesting opportunities, draft meeting prep, and open any of those workspaces. "
                     "Name a client or open one first so I have context.")
        parts.append("_Running without a live model, so open-ended questions beyond these tasks aren't supported. "
                     "Set ANTHROPIC_API_KEY to enable the full agent._")
    return {'content': '\n\n'.join(parts), 'mode': 'local-planner', 'steps': steps,
            'actions': finalize_actions(fa, message, work, actions), 'usage': None}

async def run_agent(fa: str, message: str, history: list[dict] | None = None, context: dict | None = None) -> dict:
    if fa not in FA_PROFILES:
        raise LookupError('Advisor not found')
    if live_enabled():
        try:
            return await run_live(fa, message, history or [], context)
        except Exception as e:  # any live failure degrades to the grounded planner
            out = run_local(fa, message, context, history)
            out['mode'] = 'local-planner (live model unavailable)'
            out['live_error'] = type(e).__name__
            return out
    return run_local(fa, message, context, history)
