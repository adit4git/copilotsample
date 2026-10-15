"""TEM personalization: what each tax overlay actually does to each position and lot.

The rule engine answers "is this account eligible for TER / QLH / DTLH?". The term
sheets go further: a service applies to some investments in an account and not to
others, it works lot by lot, and some tax management is done by the strategy's
manager instead. This module applies those rules (rule-store.json ->
tem_personalization) to a household's sleeves, holdings and tax lots.
Deterministic; no AI.
"""
from __future__ import annotations
from datetime import date, timedelta
from .data import RULE_STORE, ACCOUNT_FACTS, PRODUCTS_BY_ID, FA_PROFILES, derive_facts
from .services import household_or_404, offering_result
from . import skills

T = RULE_STORE['tem_personalization']
M = T['mechanics']
AS_OF = date.fromisoformat(T['as_of'])
ST_RATE, LT_RATE = M['rates']['short_term'], M['rates']['long_term']
LT_DAYS = M['long_term_after_days']
OVERLAYS = T['overlays']
OV_BY_ID = {o['id']: o for o in OVERLAYS}
ELECT_KEY = {'TER': 'taxManagedSMA', 'QLH': 'qlhOverlay', 'DTLH': 'dtlhOverlay'}
_ETF = None


@skills.on_change
def _refresh():
    """Team skills patch rule-store.json in place; recompute the values read from it at import."""
    global T, M, AS_OF, ST_RATE, LT_RATE, LT_DAYS, OVERLAYS, OV_BY_ID
    T = RULE_STORE['tem_personalization']; M = T['mechanics']; AS_OF = date.fromisoformat(T['as_of'])
    ST_RATE, LT_RATE = M['rates']['short_term'], M['rates']['long_term']; LT_DAYS = M['long_term_after_days']
    OVERLAYS = T['overlays']; OV_BY_ID = {o['id']: o for o in OVERLAYS}


def _is_etf(h):
    global _ETF
    if _ETF is None:
        _ETF = {p['ticker'] for p in PRODUCTS_BY_ID.values() if p.get('vehicle') == 'ETF' and p.get('ticker')}
        _ETF |= {'AGG', 'ARKK', 'BND', 'ESGV', 'IEFA', 'ITOT', 'MUB', 'QQQ', 'SCHD', 'VEA', 'VGT', 'VNQ', 'VOO', 'VTEB', 'VTI', 'VUG', 'VWO', 'VXUS'}
    return (h.get('type') or '').upper() == 'ETF' or (not h.get('type') and h.get('sym') in _ETF)


def base_type(h):
    """CASH | BOND | ETF | MF | STOCK | OTHER"""
    t = (h.get('type') or '').upper()
    if h.get('sym') == 'CASH' or h.get('ac') == 'Cash' or t == 'MMF':
        return 'CASH'
    if t in ('BOND', 'CD'):
        return 'BOND'
    if t in ('ANNUITY', 'AIF', 'PRIVATE'):
        return 'OTHER'
    if t == 'MF':
        return 'MF'
    if _is_etf(h):
        return 'ETF'
    if h.get('ac') in ('Fixed Income', 'Municipal'):
        return 'BOND'
    if h.get('ac') == 'Alternatives':
        return 'OTHER'
    return 'STOCK'


def _sleeve_from_product(pid, label=None):
    p = PRODUCTS_BY_ID.get(pid)
    if not p:
        return None
    codes = set(p.get('tem_overlays') or [])
    roster = {x['product_id'] for x in T['tem_sms_roster']['strategies'] if x['product_id']}
    kind = ('PAS' if p.get('premium_access') else 'TEM_SMS' if (pid in roster or p['vehicle'] == 'DIRECT_INDEXING')
            else 'CIO_ETF' if 'D' in codes else 'SMS' if p['vehicle'] == 'SMA' else 'FUND')
    role = {'PAS': 'Premium Access Strategy', 'TEM_SMS': 'TEM Style Manager Strategy', 'CIO_ETF': 'CIO strategy, ETFs only',
            'SMS': 'Style Manager Strategy', 'FUND': 'Fund strategy'}[kind]
    return {'label': label or p.get('name') or pid, 'role': role, 'kind': kind, 'product_id': pid, 'codes': codes, 'assumed': set()}


def sleeves_for(hh):
    """Sleeves with the catalog codes that decide which overlays reach them.
    Explicit sleeves (account facts) win; otherwise the strategy on file; otherwise
    funds are assumed to sit in an eligible strategy and stocks are unassigned."""
    a = ACCOUNT_FACTS.get(hh['id'], {})
    out = []
    if a.get('tem_sleeves'):
        for s in a['tem_sleeves']:
            base = _sleeve_from_product(s['product_id']) if s.get('product_id') else None
            codes = base['codes'] if base else ({'T', 'Q'} if s['kind'] == 'FUND' else set())
            out.append({**s, 'codes': codes, 'assumed': set()})
        return out
    strat = _sleeve_from_product(a.get('current_strategy_product_id')) if a.get('current_strategy_product_id') else None
    syms = [h['sym'] for h in hh['holdings'] if base_type(h) not in ('CASH', 'BOND', 'OTHER')]
    if strat:
        out.append({**strat, 'sleeve_id': 'strategy', 'syms': syms})
        return out
    codes, assumed = set(), set()
    for key, code in (('in_universe_TER', 'T'), ('in_universe_QLH', 'Q')):
        v = a.get(key)
        if v is True or v is None:
            codes.add(code)
            if v is None:
                assumed.add(code)
    if a.get('in_universe_DTLH') is True:
        codes.add('D')
    funds = [h['sym'] for h in hh['holdings'] if base_type(h) in ('ETF', 'MF')]
    if funds:
        out.append({'sleeve_id': 'funds', 'label': 'ETFs and funds', 'role': 'No strategy on file', 'kind': 'CIO_ETF' if 'D' in codes else 'FUND',
                    'product_id': None, 'codes': codes, 'assumed': assumed, 'syms': funds})
    return out


def classify(hh):
    sleeves = sleeves_for(hh)
    where = {}
    for s in sleeves:
        for sym in s['syms']:
            where.setdefault(sym, s)
    rows = []
    for i, h in enumerate(hh['holdings']):
        bt = base_type(h); s = where.get(h['sym'])
        fi = h.get('ac') in ('Fixed Income', 'Municipal')
        if bt == 'CASH': kind = 'CASH'
        elif bt == 'BOND': kind = 'FIXED_INCOME'
        elif s and s['kind'] == 'TEM_SMS': kind = 'TEM_SMS'
        elif s and s['kind'] == 'PAS': kind = 'PAS'
        elif bt == 'OTHER': kind = 'OTHER'
        elif s: kind = 'STRATEGY'
        elif bt in ('ETF', 'MF'): kind = 'STRATEGY'
        else: kind = 'UNASSIGNED'
        rows.append({'key': f"{h['sym']}#{i}", 'sym': h['sym'], 'name': h['name'], 'ac': h.get('ac'), 'mv': h['mv'], 'cost': h.get('cost'),
                     'base_type': bt, 'kind': kind, 'fi': fi and bt in ('ETF', 'MF'),
                     'sleeve_id': s['sleeve_id'] if s else ('bonds' if bt == 'BOND' else 'cash' if bt == 'CASH' else 'none'),
                     'codes': set(s['codes']) if s else set(), 'assumed': set(s['assumed']) if s else set(), 'holding': h})
    return sleeves, rows


def match_coverage(row, overlay):
    code = OV_BY_ID[overlay]['code']
    for r in T['coverage_rules']:
        w = r['when']
        if 'kind' in w and row['kind'] not in w['kind']: continue
        if 'overlay' in w and overlay not in w['overlay']: continue
        if 'fi' in w and bool(row['fi']) != w['fi']: continue
        need = code if w.get('code') == '$' else w.get('code')
        if need and need not in row['codes']: continue
        if w.get('not_code') and w['not_code'] in row['codes']: continue
        return r
    return None


def _lots(h):
    if h.get('lots'):
        return h['lots']
    return [{'lot_id': h['sym'], 'acquired': h.get('acquired'), 'qty': h.get('qty'), 'cost': h.get('cost'), 'mv': h['mv']}]


def _lot_view(sym, lot):
    acq = date.fromisoformat(lot['acquired']) if lot.get('acquired') else None
    days = (AS_OF - acq).days if acq else None
    cost = lot.get('cost'); mv = lot['mv']
    gain = (mv - cost) if cost is not None else None
    pct = (gain / cost) if cost else None
    term = None if days is None else ('LT' if days > LT_DAYS else 'ST')
    lt_date = (acq + timedelta(days=LT_DAYS + 1)).isoformat() if acq else None
    return {'sym': sym, 'lot_id': lot['lot_id'], 'acquired': lot.get('acquired'), 'holding_days': days, 'qty': lot.get('qty'),
            'cost': cost, 'mv': mv, 'gain': gain, 'pct': round(pct, 4) if pct is not None else None, 'term': term, 'lt_date': lt_date}


def tax_cost(gain, holding_days):
    """TER best-lot selection: expected tax on the lot's gain (negative = tax saved)."""
    rate = ST_RATE if holding_days is not None and holding_days <= LT_DAYS else LT_RATE
    return gain * rate


def rank_lots(lots):
    """Returns lots with FIFO priority and best-tax-lot priority (lowest tax cost per share first)."""
    out = [dict(l) for l in lots]
    for l in out:
        l['tax_cost'] = round(tax_cost(l['gain'], l['holding_days']), 2)
        l['tax_cost_per_share'] = round(l['tax_cost'] / l['qty'], 2) if l.get('qty') else None
    for i, l in enumerate(sorted(out, key=lambda x: -(x['holding_days'] or 0)), 1):
        l['fifo_priority'] = i
    for i, l in enumerate(sorted(out, key=lambda x: (x['tax_cost_per_share'] if x['tax_cost_per_share'] is not None else x['tax_cost'])), 1):
        l['best_priority'] = i
    return out


def qlh_harvest(lots):
    thr = M['qlh']['loss_threshold']
    out = []
    for l in lots:
        if l['pct'] is None: status = 'NO_BASIS'
        elif l['pct'] <= -thr: status = 'HARVEST'
        elif l['pct'] < 0: status = 'BELOW_THRESHOLD'
        else: status = 'GAIN'
        out.append({**l, 'status': status})
    return out


def _gate_value(facts, g):
    v = facts.get(g['field'])
    if v is None: return None
    if g['op'] == 'EQ': return v == g['value']
    if g['op'] == 'IN': return v in g['value']
    return None


def _src_label(docs):
    return [f"{T['doc_labels'].get(d['document_id'], d['document_id'])} p.{d['pdf_page']}" for d in docs]


def tem_personalization(household_id: str):
    hh = household_or_404(household_id)
    if hh.get('program', 'IAP') != 'IAP':
        return {'household_id': household_id, 'applicable': False,
                'note': 'Guided Investing accounts get TER plus QLH or DTLH depending on the strategy; see the MGI tax services on the client page.'}
    a = ACCOUNT_FACTS.get(household_id, {})
    facts = derive_facts(hh, 'taxManagedSMA')
    total = sum(h['mv'] for h in hh['holdings']) or 1
    gates = []
    for g in T['gates']:
        ok, msg = _gate_value(facts, g), g['message']
        if g['rule_id'] == 'TEM.GATE.PROGRAM' and ok is None and facts.get('account.iap_agreement_executed') is False:
            ok, msg = False, 'This is a brokerage account that is not in the advisory program yet. ' + g['message'] + ' The conversion map shows what each strategy type would mean for the holdings.'
        gates.append({'rule_id': g['rule_id'], 'label': g['label'], 'passed': ok, 'message': msg, 'source_doc': g['source_doc'],
                      'actual': facts.get(g['field'])})
    blocked = [g for g in gates if g['passed'] is False]
    unknown = [g for g in gates if g['passed'] is None]
    elected = {k: (hh.get('overlays') or {}).get(v) == 'enrolled' for k, v in ELECT_KEY.items()}
    verdicts = {o['id']: offering_result(household_id, o['offering_id']) for o in OVERLAYS}
    sleeves, rows = classify(hh)

    cells = {}
    for r in rows:
        for o in OVERLAYS:
            if blocked:
                g = blocked[0]
                cell = {'outcome': 'BLOCKED', 'rule_id': g['rule_id'], 'message': g['message'], 'source_doc': g['source_doc'], 'assumption': False}
            else:
                rule = match_coverage(r, o['id'])
                if not rule:
                    cell = {'outcome': 'REVIEW', 'rule_id': None, 'message': 'No coverage rule matches; confirm with the policy desk.', 'source_doc': [], 'assumption': True}
                else:
                    cell = {'outcome': rule['outcome'], 'rule_id': rule['rule_id'], 'message': rule['message'], 'source_doc': rule['source_doc'],
                            'assumption': bool(rule.get('assumption')) or (rule['rule_id'] == 'TEM.COV.CODED' and o['code'] in r['assumed'])}
                    if rule['rule_id'] == 'TEM.COV.CODED' and o['code'] in r['assumed']:
                        cell['message'] = 'ETFs and mutual funds are eligible investments. No strategy is on file, so this assumes the fund sits in an eligible strategy.'
                    if cell['outcome'] == 'SUPERSEDED':
                        cell['message'] += ' DTLH is elected on this account.' if elected['DTLH'] else ' DTLH is not elected yet, so QLH covers it today.'
            cell['source'] = _src_label(cell['source_doc'])
            cells[f"{r['key']}|{o['id']}"] = cell

    coverage = []
    for o in OVERLAYS:
        by = {}
        for r in rows:
            oc = cells[f"{r['key']}|{o['id']}"]['outcome']
            by[oc] = by.get(oc, 0) + r['mv']
        v = verdicts[o['id']]
        coverage.append({'overlay': o['id'], 'label': o['label'], 'style': o['style'], 'frequency': o['frequency'], 'fee': o['fee'],
                         'approach': o['approach'], 'eligible_investments': o['eligible_investments'], 'source': _src_label(o['source_doc']),
                         'elected': elected[o['id']], 'verdict': v['verdict'], 'offering_id': o['offering_id'],
                         'by_outcome': by, 'applies_mv': by.get('APPLIES', 0), 'applies_pct': round(by.get('APPLIES', 0) / total * 100, 1),
                         'can_model': v['verdict'] in ('ELIGIBLE', 'NEEDS_REVIEW') and not elected[o['id']]})

    # ---- lots
    lots_by_key = {r['key']: [_lot_view(r['sym'], l) for l in _lots(r['holding'])] for r in rows if r['kind'] != 'CASH'}
    qlh_rows, outside = [], []
    for r in rows:
        if r['key'] not in lots_by_key: continue
        c = cells[f"{r['key']}|QLH"]
        for l in qlh_harvest(lots_by_key[r['key']]):
            if c['outcome'] == 'APPLIES':
                l['est_tax_value'] = round(-l['gain'] * (ST_RATE if l['term'] == 'ST' else LT_RATE)) if l['status'] == 'HARVEST' else 0
                l['term_assumed'] = l['term'] is None
                qlh_rows.append(l)
            elif l['gain'] is not None and l['gain'] < 0:
                why = {'TEM.COV.FIXED_INCOME': 'Individual bond: fixed income securities are excluded', 'TEM.COV.NOT_CODED': 'Strategy not eligible for QLH in the catalog',
                       'TEM.COV.OTHER': 'Not an eligible investment type', 'TEM.COV.FI_FUND': 'Bond fund: confirm whether QLH covers it',
                       'TEM.COV.UNASSIGNED': 'No strategy on file: confirm', 'TEM.COV.TEM_SMS': 'TEM Style Manager Strategy: its manager harvests',
                       'TEM.COV.QLH_SUPERSEDED': 'CIO ETF sleeve: DTLH harvests', 'TEM.COV.PAS': 'Premium Access Strategy'}.get(c['rule_id'])
                outside.append({**l, 'outcome': c['outcome'], 'rule_id': c['rule_id'],
                                'why': why or {'BLOCKED': 'Account not eligible', 'NA': 'Not applicable'}.get(c['outcome'], 'Not covered by QLH')})
    overlap = {x['sym']: x['where'] for x in a.get('held_away_overlap', [])}
    for l in qlh_rows:
        l['wash_sale_risk'] = overlap.get(l['sym'])
    harvest = [l for l in qlh_rows if l['status'] == 'HARVEST']
    q = M['qlh']
    enrolled_on = a.get('qlh_enrolled_on')
    start = date.fromisoformat(enrolled_on) if (enrolled_on and elected['QLH']) else AS_OF
    runs, k = [], 1
    while len(runs) < 4:
        d = start + timedelta(days=q['cycle_days'] * k); k += 1
        if d > AS_OF: runs.append(d.isoformat())
    last = [(start + timedelta(days=q['cycle_days'] * j)).isoformat() for j in range(1, k) if start + timedelta(days=q['cycle_days'] * j) <= AS_OF]
    qlh = {'threshold': q['loss_threshold'], 'cycle_days': q['cycle_days'], 'wash_sale_days': q['wash_sale_days'], 'elected': elected['QLH'],
           'enrolled_on': enrolled_on if elected['QLH'] else None, 'schedule_basis': 'enrollment' if (enrolled_on and elected['QLH']) else 'if_enrolled_today',
           'last_run': last[-1] if last else None, 'next_runs': runs, 'lots': sorted(qlh_rows, key=lambda x: (x['pct'] if x['pct'] is not None else 9)),
           'harvest_loss': round(-sum(l['gain'] for l in harvest)), 'harvest_tax_value': sum(l['est_tax_value'] for l in harvest),
           'harvest_count': len(harvest), 'below_threshold_loss': round(-sum(l['gain'] for l in qlh_rows if l['status'] == 'BELOW_THRESHOLD')),
           'outside': outside, 'outside_loss': round(-sum(l['gain'] for l in outside)),
           'replacement_note': 'Harvest proceeds go into a replacement ETF chosen to keep market exposure; after the 30-day wash sale period it is sold and the original securities are bought back if the strategy still holds them.',
           'source': _src_label(q['source_doc'])}

    # ---- TER
    ter_ok = [r for r in rows if cells[f"{r['key']}|TER"]['outcome'] == 'APPLIES' and r['key'] in lots_by_key]
    multi = sorted([r for r in ter_ok if len(lots_by_key[r['key']]) >= 2 and all(l.get('qty') for l in lots_by_key[r['key']])],
                   key=lambda r: (-len(lots_by_key[r['key']]), -r['mv']))
    best_lot = None
    if multi:
        r = multi[0]
        best_lot = {'sym': r['sym'], 'name': r['name'], 'lots': sorted(rank_lots(lots_by_key[r['key']]), key=lambda x: x['fifo_priority'])}
    ex = T['term_sheet_examples']['ter_best_lot']
    ex_lots = rank_lots([{'lot_id': x['lot'], 'holding_days': x['holding_days'], 'qty': x['qty'], 'gain': x['gain']} for x in ex['lots']])
    ex_check = {'atlas_order': [x['lot_id'] for x in sorted(ex_lots, key=lambda x: x['best_priority'])],
                'term_sheet_order': [x['lot'] for x in sorted(ex['lots'], key=lambda x: x['term_sheet_best'])],
                'source': _src_label(ex['source_doc'])}
    ex_check['matches'] = ex_check['atlas_order'] == ex_check['term_sheet_order']
    window = M['ter']['st_deferral_days']
    deferral = []
    for r in ter_ok:
        for l in lots_by_key[r['key']]:
            if l['term'] == 'ST' and l['gain'] and l['gain'] > 0:
                days_to_lt = (date.fromisoformat(l['lt_date']) - AS_OF).days
                if days_to_lt <= window:
                    deferral.append({**l, 'days_to_lt': days_to_lt, 'tax_if_sold_now': round(l['gain'] * ST_RATE), 'tax_after_lt': round(l['gain'] * LT_RATE),
                                     'saving': round(l['gain'] * (ST_RATE - LT_RATE))})
    withdraw = sorted([l for r in ter_ok for l in lots_by_key[r['key']] if l['pct'] is not None], key=lambda x: x['pct'])[:6]
    ter = {'elected': elected['TER'], 'best_lot': best_lot, 'term_sheet_check': ex_check, 'st_deferral': deferral, 'deferral_window_days': window,
           'deferral_note': M['ter']['note'], 'withdrawal_order': withdraw,
           'withdrawal_note': 'Tax-prioritized withdrawals sell overweight positions first, then the largest percentage losses, using best tax lots. Atlas has no security-level targets, so this shows the loss-first order.',
           'rates': {'short_term': ST_RATE, 'long_term': LT_RATE}, 'source': _src_label(M['ter']['source_doc'] + M['rates']['source_doc'])}

    # ---- DTLH
    dt_rows = [r for r in rows if cells[f"{r['key']}|DTLH"]['outcome'] == 'APPLIES']
    watch = [l for r in dt_rows for l in lots_by_key.get(r['key'], []) if l['gain'] is not None and l['gain'] < 0]
    dtlh = {'elected': elected['DTLH'], 'applies_mv': sum(r['mv'] for r in dt_rows), 'watch': sorted(watch, key=lambda x: x['pct']),
            'watch_loss': round(-sum(l['gain'] for l in watch)), 'note': M['dtlh']['note'], 'example': T['term_sheet_examples']['dtlh'],
            'removal_note': 'If DTLH is removed, replacement ETFs are sold and reinvested in the strategy, which may realize gains.',
            'source': _src_label(M['dtlh']['source_doc'] + T['term_sheet_examples']['dtlh']['source_doc'])}

    # ---- TET: how the overlays behave alongside the Tax Efficient Transition Service
    tetv = offering_result(household_id, 'transition')
    tet_elected = (hh.get('overlays') or {}).get('transition') == 'enrolled'
    tet = None
    if not blocked and (tet_elected or tetv['verdict'] in ('ELIGIBLE', 'NEEDS_REVIEW', 'CONDITIONAL')):
        names = {o['offering_id']: o['id'] for o in OVERLAYS}
        tet = {'verdict': tetv['verdict'], 'elected': tet_elected, 'notes': [
            {'rule_id': r['rule_id'], 'overlay': names[next(x for x in r['offerings'] if x in names)], 'relation': r['relation'], 'message': r['message'],
             'source': _src_label(r['source_doc'])}
            for r in RULE_STORE['composition_rules'] if 'transition' in r['offerings'] and any(x in names for x in r['offerings'])]}

    # ---- considerations
    cons = []
    for c in T['considerations']:
        msg = None
        if c['when'] == 'federal_bracket_below' and a.get('federal_bracket') is not None and a['federal_bracket'] < c['value']:
            msg = c['message'].format(bracket=f"{round(a['federal_bracket'] * 100)}% federal bracket")
        elif c['when'] == 'held_away_overlap' and a.get('held_away_overlap'):
            for x in a['held_away_overlap']:
                cons.append({'rule_id': c['rule_id'], 'message': c['message'].format(syms=x['sym'] + ' is', where=x['where']), 'source': _src_label(c['source_doc'])})
            continue
        elif c['when'] == 'new_money' and (hh.get('incoming_capital') or a.get('dca_cash_amount')):
            msg = c['message']
        elif c['when'] == 'dtlh_elected' and elected['DTLH']:
            msg = c['message']
        elif c['when'] == 'ter_not_elected' and not elected['TER'] and not blocked:
            msg = c['message']
        elif c['when'] == 'always' and not blocked:
            msg = c['message']
        elif c['when'] == 'qlh_harvest' and not blocked and qlh['harvest_count']:
            msg = c['message'].format(count=qlh['harvest_count'], loss=f"${qlh['harvest_loss']:,.0f}", threshold=f"{qlh['threshold'] * 100:g}%")
        elif c['when'] == 'below_threshold_losses' and not blocked and qlh['below_threshold_loss']:
            msg = c['message'].format(loss=f"${qlh['below_threshold_loss']:,.0f}", threshold=f"{qlh['threshold'] * 100:g}%")
        if msg:
            cons.append({'rule_id': c['rule_id'], 'message': msg, 'source': _src_label(c['source_doc']), 'skills': skills.provenance(c)})

    # ---- personalization paths
    prog = facts.get('account.program_enrollment')
    sleeve_out = []
    for s in sleeves:
        members = [r for r in rows if r['sleeve_id'] == s['sleeve_id']]
        sleeve_out.append({'sleeve_id': s['sleeve_id'], 'label': s['label'], 'role': s.get('role'), 'kind': s['kind'], 'product_id': s.get('product_id'),
                           'codes': sorted(s['codes']), 'mv': sum(r['mv'] for r in members), 'syms': [r['sym'] for r in members]})
    for sid, lbl, role in (('bonds', 'Individual bonds', 'Fixed income securities'), ('cash', 'Cash', 'Cash and money market'), ('none', 'Other holdings', 'Not in a strategy on file')):
        members = [r for r in rows if r['sleeve_id'] == sid]
        if members:
            sleeve_out.append({'sleeve_id': sid, 'label': lbl, 'role': role, 'kind': sid.upper(), 'product_id': None, 'codes': [],
                               'mv': sum(r['mv'] for r in members), 'syms': [r['sym'] for r in members]})
    temv = offering_result(household_id, 'temSms')
    fa = FA_PROFILES.get(hh['advisor_id'], {})
    equity_mv = sum(r['mv'] for r in rows if r['base_type'] in ('STOCK', 'ETF', 'MF') and not r['fi'])
    intl = sum(r['mv'] for r in rows if (r['ac'] or '').startswith('Intl') and not r['fi'])
    sel = T.get('tem_sms_selection') or {}
    fams = ['US_LARGE'] + (['INTL'] if equity_mv and intl / equity_mv >= sel.get('intl_family_min_share', 0.15) else ['US_ALL'])
    fams += [f for f in sel.get('extra_families', []) if f not in fams]
    roster = T['tem_sms_roster']['strategies']
    pick = []
    for fam in fams:
        pick += [x for x in roster if x['family'] == fam and x['in_catalog']][:sel.get('per_family', 2)]
    paths = []
    held_tem = any(s['kind'] == 'TEM_SMS' for s in sleeves)
    im = next((m for m in T['im_models']['models'] if m['id'] == a.get('im_model_id')), None)
    for p in T['paths']:
        st, why = 'AVAILABLE', ''
        if blocked:
            st, why = 'BLOCKED', blocked[0]['message']
        elif p['id'] == 'OVERLAY':
            if prog == 'IAP_CUSTOM_MANAGED':
                st, why = 'NOT_THIS_ACCOUNT', 'This is a Custom Managed account; overlays are chosen sleeve by sleeve (next option).'
            else:
                avail = [c['overlay'] for c in coverage if c['applies_mv'] > 0]
                st = 'CURRENT' if any(elected.values()) else 'AVAILABLE'
                why = (f"The strategy supports {', '.join(avail)}." if avail else 'No position in this account is covered by an overlay.')
                if not avail: st = 'NOT_THIS_ACCOUNT'
        elif p['id'] == 'CUSTOM':
            if prog == 'IAP_CUSTOM_MANAGED':
                st, why = 'CURRENT', 'This account is a Custom Managed Strategy; the coverage table shows each sleeve.'
            else:
                why = 'Would let different sleeves carry different overlays. TEM Style Manager Strategies still could not be sleeves.'
        elif p['id'] == 'TEM_SMS':
            if prog == 'IAP_CUSTOM_MANAGED':
                st, why = 'SEPARATE_ACCOUNT', 'Not available inside a Custom Managed Strategy (TEM Guide p.5). Open a separate Managed Strategy account for it.'
            elif held_tem and im:
                st, why = 'CURRENT', f"Held inside the {im['name']} model."
            elif temv['verdict'] == 'INELIGIBLE':
                st, why = 'BLOCKED', (temv['reasons'][0]['message'] if temv['reasons'] else 'Ineligible.')
            else:
                why = 'The account would move into the strategy (a transition). Overlays are not applied to it.'
            if 'temSms' not in fa.get('qualified_for_offering', []) and st not in ('BLOCKED',):
                why += ' Certain advisors may only offer designated strategies; this advisor is not set up for TEM Style Manager Strategies.'
        elif p['id'] == 'IM_MODEL':
            if im:
                st, why = 'CURRENT', f"The account is in the {im['name']} model. Overlays can cover its other eligible holdings, not the TEM Style Manager Strategy inside it."
            elif prog == 'IAP_CUSTOM_MANAGED':
                st, why = 'SEPARATE_ACCOUNT', 'An Investment Manager Model is its own Managed Strategy, so it would be a separate account.'
            else:
                why = 'The account would move into the model. The model may, but need not, hold TEM Style Manager Strategies.'
        paths.append({**{k: p[k] for k in ('id', 'label', 'what')}, 'status': st, 'why': why, 'source': _src_label(p['source_doc'])})
    sms_options = [{**x, 'meets_minimum': (x['minimum'] or 0) <= equity_mv} for x in pick]

    applies_any = sum(r['mv'] for r in rows if any(cells[f"{r['key']}|{o}"]['outcome'] == 'APPLIES' for o in ('TER', 'QLH', 'DTLH')))
    manager_run = sum(r['mv'] for r in rows if r['kind'] == 'TEM_SMS')
    if blocked:
        headline = f"No TEM Overlay Service can be used on this account yet. {blocked[0]['message']}"
    else:
        headline = (f"{round(applies_any / total * 100)}% of the account (${applies_any:,.0f}) is covered by at least one overlay"
                    + (f"; ${manager_run:,.0f} is in a TEM Style Manager Strategy whose manager handles tax management" if manager_run else '')
                    + (f". QLH would harvest {qlh['harvest_count']} lot{'s' if qlh['harvest_count'] != 1 else ''} at a {qlh['threshold'] * 100:g}%+ loss (${qlh['harvest_loss']:,.0f} of losses)" if qlh['harvest_count'] else f". No lot is at a {qlh['threshold'] * 100:g}%+ loss for QLH today")
                    + '.'
                    + (f" At the account level QLH {({'NEEDS_REVIEW': 'needs review', 'INELIGIBLE': 'is ineligible'}).get(verdicts['QLH']['verdict'], 'is conditional')}, so confirm before relying on it." if qlh['harvest_count'] and verdicts['QLH']['verdict'] != 'ELIGIBLE' else ''))
    return {'household_id': household_id, 'applicable': True, 'as_of': T['as_of'], 'total_mv': total, 'headline': headline,
            'program_enrollment': prog, 'federal_bracket': a.get('federal_bracket'), 'im_model': im,
            'gates': [{**g, 'source': _src_label(g['source_doc'])} for g in gates], 'blocked': bool(blocked), 'unknown_gates': [g['rule_id'] for g in unknown],
            'elected': elected, 'coverage': coverage, 'outcome_labels': T['outcomes'],
            'sleeves': sleeve_out,
            'holdings': [{k: r[k] for k in ('key', 'sym', 'name', 'mv', 'sleeve_id', 'kind', 'base_type', 'fi')} | {'lots': len(lots_by_key.get(r['key'], []))} for r in rows],
            'cells': cells, 'tet': tet, 'qlh': qlh, 'ter': ter, 'dtlh': dtlh, 'considerations': cons, 'paths': paths, 'tem_sms_options': sms_options,
            'tem_sms_roster_count': len(roster), 'tem_sms_roster_as_of': T['tem_sms_roster']['as_of'],
            'im_models': T['im_models']['models'], 'equity_mv': equity_mv,
            'rates': {'short_term': ST_RATE, 'long_term': LT_RATE},
            'tem_sms_selection': {'families': fams, 'per_family': sel.get('per_family', 2), 'intl_family_min_share': sel.get('intl_family_min_share', 0.15)},
            'skills': skills.for_workspace('tem'),
            'policy_skills': {'qlh_threshold': skills.touched('rules', 'tem_personalization.mechanics.qlh'),
                              'sms_shortlist': skills.touched('rules', 'tem_personalization.tem_sms_selection')}}


def book_harvest(fa: str):
    """Lot-level harvestable losses per household, split at the QLH 5% threshold (for the Tax Overlay Desk chart)."""
    from .data import my_book
    thr = M['qlh']['loss_threshold']
    out = []
    for hh in my_book(fa):
        over = under = 0.0
        for h in hh['holdings']:
            if base_type(h) == 'CASH': continue
            for l in _lots(h):
                if l.get('cost') in (None, 0): continue
                g = l['mv'] - l['cost']
                if g < 0:
                    if -g / l['cost'] >= thr: over += -g
                    else: under += -g
        if over or under:
            out.append({'household_id': hh['id'], 'name': hh['name'], 'at_threshold': round(over), 'below_threshold': round(under)})
    return sorted(out, key=lambda x: -(x['at_threshold'] + x['below_threshold']))
