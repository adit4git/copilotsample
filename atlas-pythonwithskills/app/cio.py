"""CIO Model Fit: brokerage accounts against the CIO strategic model they should map to.

For each account in scope (brokerage, Bridgewater NJ market, over $50K as of 8/31) it puts
four things side by side: how the account is set up, how it actually performed (ex post),
what it holds today rolled up into CIO capital market asset classes, and the expected return,
risk and Sharpe of those holdings vs the matched CIO model, both from the 2026 CMA.
Deterministic; no AI. Data: app/data/cio-models.json (illustrative assumptions).
"""
from __future__ import annotations
import json, math
from pathlib import Path
from .data import BY_ID, FA_PROFILES

from . import skills

C = json.loads((Path(__file__).parent / 'data' / 'cio-models.json').read_text())
skills.register_target('cio', C)        # CIO-office skills (CMA updates, flag thresholds) patch this in place


@skills.on_change
def _refresh():
    global CLS, ORDER, CORR, RF, MODELS, TH
    CLS = {c['id']: c for c in C['cma']['classes']}
    ORDER = C['cma']['correlation']['order']
    CORR = {(a, b): C['cma']['correlation']['matrix'][i][j] for i, a in enumerate(ORDER) for j, b in enumerate(ORDER)}
    RF = CLS[C['cma']['risk_free_class']]['expected_return']
    MODELS = {(m['profile'], m['tier']): m for m in C['models']}
    TH = C['thresholds']


_refresh()


def stats(weights: dict) -> dict:
    """Expected return, volatility and Sharpe of a weight vector from the CMA."""
    er = sum(w * CLS[k]['expected_return'] for k, w in weights.items())
    var = sum(weights[a] * weights[b] * CLS[a]['volatility'] * CLS[b]['volatility'] * CORR[(a, b)] for a in weights for b in weights)
    vol = math.sqrt(max(var, 0))
    return {'expected_return': round(er, 5), 'volatility': round(vol, 5), 'sharpe': round((er - RF) / vol, 3) if vol else None}


def tracking_error(w1: dict, w2: dict) -> float:
    keys = set(w1) | set(w2); d = {k: w1.get(k, 0) - w2.get(k, 0) for k in keys}
    return round(math.sqrt(max(sum(d[a] * d[b] * CLS[a]['volatility'] * CLS[b]['volatility'] * CORR[(a, b)] for a in keys for b in keys), 0)), 5)


def profile_for(risk: str, horizon: str) -> str | None:
    g = C['profile_grid']
    if risk not in g['grid'] or horizon not in g['time_horizons']: return None
    return g['grid'][risk][g['time_horizons'].index(horizon)]


def tier_for(liquidity: str | None) -> tuple[int, bool]:
    t = C['liquidity_tiers']
    if not liquidity: return t['blank_default'], True
    return t['map'][liquidity], False


def rollup(hh: dict, acct: dict) -> dict:
    """Positions -> CMA asset classes, applying the classification snapshot and the judgment calls."""
    rows, by_class = [], {}
    def add(k, v): by_class[k] = by_class.get(k, 0) + v
    for h in hh['holdings']:
        c = C['classification'].get(h['sym'], {'method': 'UNCLASSIFIED', 'why': 'Not in the 8/28 classification snapshot'})
        method = c.get('method', 'DIRECT'); alloc = {}
        if method == 'CORE_SPLIT': alloc = {'LCG': h['mv'] / 2, 'LCV': h['mv'] / 2}
        elif method == 'AGG_SPLIT': alloc = {'UST': h['mv'] * 0.6, 'IGC': h['mv'] * 0.4}
        elif method != 'UNCLASSIFIED': alloc = {c['class']: h['mv']}
        for k, v in alloc.items(): add(k, v)
        rows.append({'sym': h['sym'], 'name': h['name'], 'mv': h['mv'], 'method': method, 'method_text': C['methods'][method],
                     'why': c.get('why'), 'classes': {k: round(v, 2) for k, v in alloc.items()}})
    m = acct.get('margin_balance') or 0
    if m > 0:
        add('CASH', m)
        rows.append({'sym': 'MARGIN', 'name': 'Margin credit balance', 'mv': m, 'method': 'MARGIN_CREDIT', 'method_text': C['methods']['MARGIN_CREDIT'], 'why': None, 'classes': {'CASH': m}})
    elif m < 0:
        rows.append({'sym': 'MARGIN', 'name': 'Margin debit balance', 'mv': m, 'method': 'MARGIN_DEBIT', 'method_text': C['methods']['MARGIN_DEBIT'], 'why': None, 'classes': {}})
    total = sum(h['mv'] for h in hh['holdings']) + max(m, 0)
    covered = sum(by_class.values())
    muni = sum(r['mv'] for r in rows if r['method'] == 'PROXY_MUNI')
    return {'rows': rows, 'by_class': by_class, 'total_mv': total, 'covered_mv': covered, 'unclassified_mv': total - covered,
            'coverage': covered / total if total else 0, 'muni_mv': muni, 'muni_share': muni / covered if covered else 0,
            'margin_debit': -m if m < 0 else 0, 'margin_credit': m if m > 0 else 0}


def in_scope(hid: str) -> tuple[bool, str]:
    acct = C['accounts'].get(hid); hh = BY_ID.get(hid)
    s = C['scope']
    if not hh: return False, 'Household not found.'
    if not acct: return False, f"{hh['name']} has no {s['account_type'].lower()} account in the {s['market']} market in this data, so it isn't part of the CIO model comparison."
    if sum(h['mv'] for h in hh['holdings']) <= s['min_market_value']: return False, f"Under the ${s['min_market_value']:,.0f} minimum."
    return True, ''


def account_fit(hid: str) -> dict:
    ok, why = in_scope(hid)
    if not ok:
        return {'household_id': hid, 'in_scope': False, 'reason': why}
    hh, a = BY_ID[hid], C['accounts'][hid]
    profile = profile_for(a['risk_tolerance'], a['time_horizon'])
    tier, defaulted = tier_for(a.get('liquidity_needs'))
    model = MODELS[(profile, tier)]
    desc = a.get('allocation_profile_desc'); desc_profile = C['allocation_profile_desc_map'].get(desc) if desc else None
    r = rollup(hh, a)
    cur_w = {k: v / r['covered_mv'] for k, v in r['by_class'].items()} if r['covered_mv'] else {}
    cur, mod = stats(cur_w), stats(model['weights'])
    alloc = [{'class': k, 'label': CLS[k]['label'], 'group': CLS[k]['group'], 'current': round(cur_w.get(k, 0), 4),
              'model': model['weights'].get(k, 0), 'diff': round(cur_w.get(k, 0) - model['weights'].get(k, 0), 4)}
             for k in ORDER if cur_w.get(k) or model['weights'].get(k)]
    top = max((h for h in hh['holdings'] if C['classification'].get(h['sym'], {}).get('method', 'DIRECT') == 'DIRECT'
               and C['classification'].get(h['sym'], {}).get('class') != 'CASH'), key=lambda h: h['mv'], default=None)
    conc = {'sym': top['sym'], 'name': top['name'], 'share': round(top['mv'] / r['covered_mv'], 4)} if top and r['covered_mv'] else None

    flags = []
    def flag(fid, sev, text): flags.append({'id': fid, 'severity': sev, 'text': text})
    if r['coverage'] < TH['low_coverage']:
        flag('coverage', 'review', f"Only {r['coverage']:.0%} of the account is classified; ${r['unclassified_mv']:,.0f} is left out of the expected return and risk. Read the comparison with care.")
    if r['muni_share'] >= TH['muni_proxy_flag']:
        flag('muni_proxy', 'info', f"{r['muni_share']:.0%} of the classified value relies on the muni proxy (munis treated as U.S. corporates), so its risk and return are a corporate-bond stand-in and the tax advantage isn\u2019t reflected.")
    if desc_profile and desc_profile != profile:
        flag('profile', 'review', f"allocation_profile_desc says “{desc}” (reads as {desc_profile}); the risk tolerance and time horizon give {profile}. The source of that field is not confirmed.")
    elif not desc:
        flag('profile_blank', 'info', 'allocation_profile_desc is blank, so there is nothing to compare the derived profile against.')
    if defaulted:
        flag('liquidity', 'review', 'Liquidity needs are blank, so the account defaults to Tier 0, the most liquid. Confirm with the client.')
    if tier in (2, 3):
        flag('tier23', 'info', 'Tier 2 and Tier 3 targets are currently identical (confirmed), so the tier choice between them does not change the model.')
    if r['margin_debit']:
        flag('margin', 'info', f"A ${r['margin_debit']:,.0f} margin debit is left out of the allocation math and reported separately.")
    if r['margin_credit']:
        flag('margin_credit', 'info', f"A ${r['margin_credit']:,.0f} margin credit balance is counted as cash.")
    if conc and conc['share'] >= TH['concentration']:
        flag('concentration', 'review', f"{conc['sym']} is {conc['share']:.0%} of the classified value; the CMA prices it as its asset class, not as a single stock, so real risk is higher than shown.")
    if a['performance'].get('return_3y') is None:
        flag('history', 'info', f"No 3-year history; actual figures use the {a['performance']['std_basis']} basis.")

    fa = FA_PROFILES.get(hh['advisor_id'], {})
    d_er = cur['expected_return'] - mod['expected_return']; d_vol = cur['volatility'] - mod['volatility']
    headline = (f"What {hh['name'].split()[0]} holds today is expected to return {cur['expected_return']:.1%} at {cur['volatility']:.1%} risk "
                f"(Sharpe {cur['sharpe']:.2f}), against {mod['expected_return']:.1%} at {mod['volatility']:.1%} (Sharpe {mod['sharpe']:.2f}) for the {model['label']} model"
                + f": {abs(d_er) * 100:.1f} points {'more' if d_er > 0 else 'less'} expected return for {abs(d_vol) * 100:.1f} points {'more' if d_vol > 0 else 'less'} risk."
                + (f" {r['coverage']:.0%} of the account is classified." if r['coverage'] < 1 else ''))
    return {'household_id': hid, 'in_scope': True, 'name': hh['name'], 'fa': fa.get('name'), 'account_no': a['account_no'],
            'account_type': a['account_type'], 'market': a['market'],
            'setup': {'risk_tolerance': a['risk_tolerance'], 'time_horizon': a['time_horizon'], 'liquidity_needs': a.get('liquidity_needs'),
                      'tier': tier, 'tier_label': C['liquidity_tiers']['labels'][str(tier)], 'tier_defaulted': defaulted, 'profile': profile,
                      'allocation_profile_desc': desc, 'desc_profile': desc_profile, 'desc_matches': (desc_profile == profile) if desc_profile else None},
            'model': {'model_id': model['model_id'], 'label': model['label'], 'profile': profile, 'tier': tier},
            'performance': a['performance'], 'current': cur, 'model_stats': mod,
            'gap': {'expected_return': round(d_er, 5), 'volatility': round(d_vol, 5),
                    'sharpe': round(cur['sharpe'] - mod['sharpe'], 3) if cur['sharpe'] is not None else None,
                    'tracking_error': tracking_error(cur_w, model['weights'])},
            'allocation': alloc, 'holdings': r['rows'],
            'coverage': {'total_mv': r['total_mv'], 'covered_mv': r['covered_mv'], 'unclassified_mv': r['unclassified_mv'], 'pct': round(r['coverage'], 4),
                         'margin_debit': r['margin_debit'], 'margin_credit': r['margin_credit']},
            'muni_proxy_share': round(r['muni_share'], 4), 'concentration': conc, 'flags': flags, 'headline': headline,
            'skills': skills.for_workspace('cio_fit')}


def fit_book(fa: str) -> dict:
    accts = [account_fit(hid) for hid, hh in BY_ID.items() if hh['advisor_id'] == fa and hid in C['accounts']]
    accts = [a for a in accts if a['in_scope']]
    return {'scope': C['scope'], 'as_of': C['as_of'], 'cio_guidance': C['cio_guidance'], 'judgment_calls': C['judgment_calls'],
            'cma': {'classes': C['cma']['classes'], 'risk_free': RF, 'note': C['cma']['note']}, 'note': C['_note'],
            'profile_grid': C['profile_grid'], 'liquidity_tiers': C['liquidity_tiers'],
            'skills': skills.for_workspace('cio_fit'), 'thresholds': TH,
            'accounts': sorted(accts, key=lambda a: a['gap']['sharpe'] if a['gap']['sharpe'] is not None else 9)}
