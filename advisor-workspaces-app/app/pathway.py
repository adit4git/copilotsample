"""The advisory pathway: every opportunity leads, in the same six steps, to an advisory path or an explicit alternative.
Trigger, size the gap, value the gap, match options, plan transition, client story. Also: exclusive buckets and amounts,
priority cues, ranking, transition routes with feasibility and approvers, the handoff, the book view and the five stages.
Key controls: lower-cost alternative always shown; fit before tax; no tax estimate without basis; advisor review before
anything is sent; no autonomous execution or enrollment."""
from __future__ import annotations
import math
import re
from datetime import date
from .data import DATA, HHS, State
from . import engine as E
from . import calc as X
from . import rules as D
from .fmt import money, pct, js_round, num, nsum

UC = {1: 'Allocation and risk alignment gap', 2: 'Embedded gains and loss harvesting', 3: 'Individual bonds and maturities', 4: 'Excess cash', 5: 'High-cost funds',
      7: 'Advisory value narrative', 8: 'Concentrated stock', 10: 'News, CIO and research views', 12: 'Trading economics'}
KIND = {1: 'Allocation gap', 2: 'Embedded gains and losses', 3: 'Individual bonds', 4: 'Excess cash', 5: 'High-cost funds', 7: 'Advisory proposal',
        8: 'Concentrated stock', 10: 'Market or research event', 12: 'Trading costs'}
FLOW = {'shift': 'Shift', 'lift': 'Revenue lift', 'both': 'Shift and revenue lift', 'na': 'Entry point'}
SEG = {'low': ['Low', 'neutral'], 'medium': ['Medium', 'warn'], 'hard': ['Hard', 'bad']}
PSHORT = {'rebalance': 'Transfer and rebalance now', 'phased': 'Phased, tax-aware transition', 'managed': 'Tax-managed SMA and direct indexing', 'specialist': 'Specialist route'}
MONTHS = ['Nov 2026', 'Dec 2026', 'Jan 2027', 'Feb 2027', 'Mar 2027', 'Apr 2027']


def s_(n) -> str:
    return '' if n == 1 else 's'


def amt(hh: dict) -> float:
    return nsum(h['mv'] for h in X.scope(hh, 'brokerage'))


def transition(hh: dict) -> dict:
    """The conversion map summarised: how each holding moves and how much is aligned in year one."""
    r = X.routing(hh); lt = hh['rates']['lt']
    sm = lambda k: nsum(x['mv'] for x in r if x['route'] == k)
    gains = nsum(max(0, x['gain']) for x in r if x['route'] == 'transfer')
    y1g = min(gains, hh['gain_budget']) if hh.get('gain_budget') is not None else gains
    tr_mv = sm('transfer'); sold = tr_mv * y1g / gains if gains else 0
    losses = nsum(-min(0, x['gain']) for x in r if x['route'] == 'harvest')
    parts = {k: sm(k) for k in ['inkind', 'swap', 'transfer', 'harvest', 'instep', 'basis', 'stay', 'reserve']}
    total = nsum(parts.values()); moveable = total - parts['stay'] - parts['reserve']
    aligned = parts['inkind'] + parts['swap'] + parts['harvest'] + parts['instep'] + sold
    trade_amt = 2 * (sold + parts['harvest'] + parts['swap']) + parts['instep']
    return {'r': r, 'parts': parts, 'total': total, 'moveable': moveable, 'aligned': aligned, 'pct': aligned / moveable if moveable else 0, 'sold': sold,
            'gains': gains, 'y1g': y1g, 'losses': losses, 'taxGross': y1g * lt, 'taxNet': max(0, y1g - losses) * lt, 'carry': max(0, losses - y1g),
            'trading': trade_amt * DATA['pathway']['trading_cost_bps'] / 1e4, 'noBasis': parts['basis']}


def segment(hh: dict) -> str:
    a = amt(hh) or 1
    g = nsum(max(0, x.get('gain') or 0) for x in X.routing(hh)) / a
    A = any(h.get('share_class') == 'A' for h in hh['holdings'])
    return 'hard' if hh['age'] >= 80 or g >= 0.15 or (A and g >= 0.03) else 'medium' if g >= 0.03 else 'low'


def forgone(hh: dict) -> dict:
    """Expected return at the CIO target vs today, and the five-year scenario difference (capital market assumptions)."""
    g = X.gap(hh, 'brokerage', 'tactical'); a = amt(hh)
    return {'erNow': g['st']['er'], 'erT': g['stT']['er'], 'volNow': g['st']['vol'], 'volT': g['stT']['vol'], 'yr': (g['stT']['er'] - g['st']['er']) * a,
            'five': a * ((1 + g['stT']['er']) ** 5 - (1 + g['st']['er']) ** 5)}


def gap_text(hh: dict) -> str:
    g = X.gap(hh, 'brokerage', 'tactical'); w = E.groups(g['w']); t = E.groups(g['t'])
    from .fmt import to_fixed
    pt = lambda x: to_fixed(abs(x) * 100, 1) + ' pts'
    bits = []
    if w['cash'] - t['cash'] > 0.01: bits.append(f"{pt(w['cash'] - t['cash'])} excess cash")
    if t['equity'] - w['equity'] > 0.01: bits.append(f"a {pt(t['equity'] - w['equity'])} equity underweight")
    if w['equity'] - t['equity'] > 0.01: bits.append(f"a {pt(w['equity'] - t['equity'])} equity overweight")
    if t['fixed'] - w['fixed'] > 0.01: bits.append(f"a {pt(t['fixed'] - w['fixed'])} fixed income underweight")
    if w['fixed'] - t['fixed'] > 0.01: bits.append(f"a {pt(w['fixed'] - t['fixed'])} fixed income overweight")
    if bits:
        s = ' and '.join(bits)
        return s[0].upper() + s[1:]
    return f"{g['out']} asset classes outside tolerance"


def fit_strategies(hh: dict, g: dict, a: dict, e: dict | None) -> list[dict]:
    under = [r['k'] for r in g['rows'] if r['g'] < -0.01]
    det_cls = list(dict.fromkeys(k for d in a['det'] for k in ((next((h for h in hh['holdings'] if h['sym'] == d['sym']), {}) or {}).get('classes') or {})))
    gain_heavy = nsum(r['mv'] for r in X.routing(hh) if r['route'] == 'transfer') > 0.25 * g['ct']
    conc = any(v > DATA['concentration']['threshold'] for v in E.names(hh['holdings']).values())
    out = []
    for s in DATA['strategies']:
        sc = 0.0; why = []
        cov = [k for k in under if k in s['covers']]
        if cov:
            from .fmt import short
            sc += 0.15 * len(cov); why.append('Closes gaps in ' + ', '.join(short(k) for k in cov))
        dc = [k for k in det_cls if k in s['covers']]
        if dc:
            from .fmt import short
            sc += 0.2; why.append('Replaces detractors in ' + ', '.join(short(k) for k in dc))
        if s.get('tax') and gain_heavy:
            sc += 0.25; why.append('Manages embedded gains over time')
        if s.get('exclude') and conc:
            sc += 0.25; why.append('Can exclude the concentrated stock')
        if s['id'] == 'cio-model':
            sc += 0.3; why.append('Follows the CIO allocation for the profile')
        if s['min'] > g['ct'] * 0.6:
            sc -= 0.5; why.append(f"Minimum {money(s['min'])} is large for this portfolio")
        if all(k in ('HF', 'PE') for k in s['covers']) and not any(k in ('HF', 'PE') for k in under):
            sc -= 0.4
        if e and e['state'] == 'ineligible':
            out.append({**s, 'score': 0, 'blocked': True, 'why': [f"Not available: {e['reason']}"]}); continue
        out.append({**s, 'score': max(0, min(1, sc)), 'why': why or ['General fit']})
    return sorted(out, key=lambda x: -x['score'])[:4]


def options(hh: dict) -> list[dict]:
    e = D.elig(hh)
    if e['state'] == 'ineligible':
        return []
    g = X.gap(hh, 'brokerage', 'tactical')
    return [x for x in fit_strategies(hh, g, X.attribution(hh, 'brokerage', '3Y'), e) if not x.get('blocked') and x['score'] > 0.05][:4]


def lower_cost(hh: dict) -> dict:
    return X.opt(D.default_costs(hh, D.round_k(amt(hh)) or 1), 'index')


def _days(a: str, b: str) -> float:
    return (date.fromisoformat(a) - date.fromisoformat(b)).days


def screens(hh: dict) -> list[dict]:
    """Data-ready screens on the existing holdings: gains and losses, bonds, excess cash, high-cost funds, trading costs."""
    out = []; T = DATA['pathway']['thresholds']; e = D.elig(hh); tr = transition(hh); a = amt(hh); lt = hh['rates']['lt']
    if e['state'] == 'ineligible' or not a:
        return out
    act = [D.ELIG[e['state']][2], D.ELIG[e['state']][1]]
    if hh['rates'].get('taxable') and (tr['gains'] >= T['gains_min'] or tr['losses'] >= T['losses_min']):
        syms = [x['sym'] for x in tr['r'] if x['route'] in ('transfer', 'harvest')]
        out.append({'uc': 2, 'ws': 'path', 'key': 'p2:' + hh['id'], 'hh': hh, 'type': 'Embedded gains and loss harvesting',
                    'trigger': f"Taxable account: {money(tr['gains'])} of long-term gains" + (f" and {money(tr['losses'])} of unrealized losses" if tr['losses'] else '') + f" ({', '.join(syms)})",
                    'size': f"{money(tr['gains'])} embedded gains" + (f"; {money(tr['losses'])} harvestable losses" if tr['losses'] else ''),
                    'impact': f"{money(tr['gains'])} gains · {money(tr['losses'])} losses",
                    'value': f"Tax spread over time: year one ≈ {money(tr['taxNet'])} after losses, not ≈ {money(tr['gains'] * lt)} at once" if tr['gains'] else f"{money(tr['losses'] * lt)} of tax value from harvested losses",
                    'pathway': 'Tax-efficient transition into managed accounts; direct indexing and loss harvesting', 'flow': 'both',
                    'next': 'Review the transition plan and the gain budget', 'status': 'ready', 'pri': 2.4, 'act': act, 'rel': []})
    bonds = [h for h in hh['holdings'] if h.get('kind') == 'bond' and h.get('acct') == 'brokerage']
    if bonds:
        soon = [b for b in bonds if b.get('call_date') and _days(b['call_date'], DATA['pathway']['as_of']) <= T['call_days']]
        mv = nsum(b['mv'] for b in bonds)
        out.append({'uc': 3, 'ws': 'path', 'key': 'p3:' + hh['id'], 'hh': hh,
                    'type': f"{soon[0]['sym']} callable on {soon[0]['call_date']}" if soon else 'Unmanaged individual bonds',
                    'trigger': f"{len(bonds)} unmanaged individual bond{s_(len(bonds))} ({money(mv)})" + (f"; {', '.join(b['sym'] for b in soon)} callable within {T['call_days']} days" if soon else ''),
                    'size': f'{money(mv)} in individual bonds, {pct(mv / a, 1)} of brokerage', 'impact': f'{money(mv)} unmanaged bonds' + (' · call soon' if soon else ''),
                    'value': f"Call proceeds of {money(nsum(b['mv'] for b in soon))} need reinvesting; a managed ladder reinvests and monitors credit" if soon else 'Credit monitoring and laddered reinvestment instead of ad-hoc replacement',
                    'pathway': 'Managed fixed income SMA (individual-bond ladder); call and maturity proceeds go into it', 'flow': 'shift',
                    'next': 'Plan reinvestment before the call date' if soon else 'Review a managed ladder', 'status': 'review' if soon else 'ready', 'pri': 2.3 if soon else 1.4, 'act': act, 'rel': []})
    cs = X.cash_split(hh); excess = cs['investable']; f = forgone(hh); cr = DATA['perf']['bench']['CASH']['1Y']
    if excess > T['excess_cash_pct'] * a and not any(o['uc'] == 4 for o in out):
        out.append({'uc': 4, 'ws': 'path', 'key': 'p4:' + hh['id'], 'hh': hh, 'type': 'Excess cash above target',
                    'trigger': f"Cash {money(cs['total'])}: {money(excess)} is above the CIO target after a {money(cs['reserve'])} reserve" + (" (including next year's needs)" if cs['needs'] else ''),
                    'size': f'{money(excess)} excess cash, {pct(excess / a, 1)} of brokerage', 'impact': f'{money(excess)} excess cash',
                    'value': f"Scenario: ≈ {money(excess * max(0, f['erT'] - cr))} a year of expected return at the CIO allocation ({pct(f['erT'], 1)}) vs cash ({pct(cr, 1)}), under capital market assumptions; not a forecast",
                    'pathway': 'CIO-aligned advisory strategy, invested in steps', 'flow': 'shift', 'next': 'Agree the reserve and the pace of investing', 'status': 'ready', 'pri': 2.2, 'act': act, 'rel': []})
    hc = [h for h in hh['holdings'] if h.get('acct') == 'brokerage' and (h.get('expense_bps') or 0) >= T['high_cost_bps'] and not h.get('cash')]
    if hc:
        mv = nsum(h['mv'] for h in hc); cost = nsum(h['mv'] * h['expense_bps'] / 1e4 for h in hc); alt = mv * DATA['fees']['model_fund_bps'] / 1e4
        trig = ', '.join(f"{h['sym']} {num(h['expense_bps'])} bp" + (f" ({h['share_class']} shares)" if h.get('share_class') else '') for h in hc)
        out.append({'uc': 5, 'ws': 'path', 'key': 'p5:' + hh['id'], 'hh': hh, 'type': 'High-cost funds', 'trigger': f"{trig}: above the {T['high_cost_bps']} bp threshold",
                    'size': f'{money(mv)} in funds costing {js_round(cost / mv * 1e4)} bp on average', 'impact': f'{money(cost - alt)} a year in fund costs above model funds',
                    'value': f"≈ {money(cost - alt)} a year less in fund expenses with model funds ({DATA['fees']['model_fund_bps']} bp), before the program fee",
                    'pathway': 'Equivalent advisory strategy via tax-efficient transition', 'flow': 'shift', 'next': 'Compare the equivalent strategy, after taxes', 'status': 'ready', 'pri': 1.6, 'act': act, 'rel': []})
    comm = a * DATA['fees']['brokerage']['turnover'] * DATA['fees']['brokerage']['commission']; pf = X.program_fee(a)['fee']
    if comm >= T['trading_rival'] * pf:
        out.append({'uc': 12, 'ws': 'path', 'key': 'p12:' + hh['id'], 'hh': hh, 'type': 'Commissions rival the program fee',
                    'trigger': f'Commissions {money(comm)} a year vs program fee {money(pf)}', 'size': f'{pct(comm / pf)} of the fee', 'impact': f'{money(comm)} commissions',
                    'value': 'Trading included in the program', 'pathway': 'Advisory enrollment (decision support)', 'flow': 'shift', 'next': 'Show the cost comparison', 'status': 'ready', 'pri': 1.5, 'act': act, 'rel': []})
    return out


def steps(o: dict, st: State) -> list[dict]:
    """The six steps for any opportunity."""
    hh = o['hh']; e = D.elig(hh); tr = transition(hh); f = forgone(hh); opts = options(hh); lc = lower_cost(hh); story = st.rev(hh['id'])
    blocked = e['state'] == 'ineligible'
    parts = [f"Invest in steps for {money(tr['parts']['instep'])} of cash" if tr['parts']['instep'] else None,
             f"tax-efficient transition for {money(tr['parts']['transfer'])} of appreciated holdings" if tr['parts']['transfer'] else None,
             f"{money(tr['parts']['inkind'] + tr['parts']['swap'])} moves in kind or swaps" if tr['parts']['inkind'] + tr['parts']['swap'] else None]
    plan = (f"Not available: {e['reason']}. Specialist plan first; staged sales in brokerage." if blocked else
            '; '.join(p for p in parts if p) + f"; ≈{js_round(tr['pct'] * 100)}% aligned in year one; tax {'not estimated for lots without basis; ' if tr['noBasis'] else ''}≈ {money(tr['taxNet'])} after losses, trading ≈ {money(tr['trading'])}")
    swaps = ', '.join(x['sym'] for x in tr['r'] if x['route'] == 'swap') or 'within the gain budget'
    lead = ('The bonds are held to their call or maturity; the proceeds go into a managed ladder instead of sitting in cash. Household: ' if o['uc'] == 3 else
            f'High-cost funds are swapped into the equivalent strategy ({swaps}). Household: ' if o['uc'] == 5 else
            'Cash moves in monthly steps over six months. Household: ' if o['uc'] == 4 else '')
    opt = ('Program, SMA and direct-indexing paths blocked; specialist route' if blocked else
           f"{len(opts)} fitting strateg{'y' if len(opts) == 1 else 'ies'}: {', '.join(x['name'] for x in opts)}; lower-cost alternative shown: {lc['name']} ({js_round(lc['bps'])} bp)")
    val = o.get('value') or (f"Illustrative scenario difference (modeled): ≈ {pct(f['erT'] - f['erNow'], 2)} a year of expected return, ≈ {money(f['five'])} over 5 years; not a forecast"
                             if f['yr'] > 0 else 'Value rests on advice and risk management')
    story_t = ('Story explains the specialist route first' if blocked else 'Submitted for compliance review' if story == 'compliance' else
               'Advisor reviewed; ready to present' if story == 'advisor' else 'Proposal and story drafted, ready for advisor review')
    return [{'n': 1, 'k': 'Trigger', 'v': o.get('trigger') or o['type']}, {'n': 2, 'k': 'Size the gap', 'v': o.get('size') or o['impact']},
            {'n': 3, 'k': 'Value the gap', 'v': val}, {'n': 4, 'k': 'Match options', 'v': opt},
            {'n': 5, 'k': 'Plan transition', 'v': plan if blocked else lead + plan}, {'n': 6, 'k': 'Client story', 'v': story_t}]


def pw_of(o: dict) -> str:
    return {1: 'CIO model rebalance', 2: 'Tax-efficient transition + direct indexing', 3: 'Managed bond ladder', 4: 'Invest in steps into a CIO strategy',
            5: 'Equivalent strategy, tax-aware swap', 7: 'Client story and proposal', 8: 'Specialist route (excluded)' if o.get('flow') == 'na' else 'Tax-managed SMA + direct indexing',
            10: 'Event-led review', 12: 'Advisory enrollment'}.get(o['uc'])


def enrich(o: dict, st: State) -> dict:
    """Give rows from the four workspaces their use case, trigger, size, value and pathway."""
    if o.get('uc'):
        o['pw'] = o.get('pw') or pw_of(o); return o
    hh = o['hh']; f = forgone(hh); e = D.elig(hh)
    if o['ws'] == 'ws1':
        w = D.ws1(hh, D.BASE, st); cash_kind = w['kind'] == 'cash'; cs = X.cash_split(hh)
        o.update({'uc': 4 if cash_kind else 1,
                  'trigger': (f"Cash {money(cs['total'])} ({pct(cs['total'] / amt(hh))} of brokerage): {money(cs['investable'])} is above the CIO target after a {money(cs['reserve'])} reserve" if cash_kind else
                              f"Brokerage portfolio outside the CIO tolerance for the {hh['profile']} profile ({re.sub(r' of the CIO .*$', '', w['evidence'][1].split(';')[0])})"),
                  'size': f"{gap_text(hh)}; {w['evidence'][0].lower()}",
                  'value': (f"Illustrative scenario difference (modeled): ≈ {pct(f['erT'] - f['erNow'], 2)} a year of expected return, ≈ {money(f['five'])} over 5 years under capital market assumptions; not a forecast or a guaranteed benefit"
                            if f['yr'] > 0 else f"Expected volatility {pct(f['volNow'], 1)} vs {pct(f['volT'], 1)} at the CIO target"),
                  'pathway': 'Excluded: specialist route' if e['state'] == 'ineligible' else 'CIO-aligned advisory strategy, invested in steps' if cash_kind else 'Rebalance into the advisory program via a CIO model or managed portfolio',
                  'flow': 'na' if e['state'] == 'ineligible' else 'shift'})
    elif o['ws'] == 'ws3':
        ex = o['act'][1] == 'bad'; sym = o['pos'].split(':')[1]; tot = nsum(h['mv'] for h in hh['holdings'])
        o.update({'uc': 8, 'trigger': f"{o['type'].replace(' concentration', '')} above the {pct(st.th)} concentration threshold", 'size': o['impact'],
                  'value': f"A 30% fall would cost ≈ {money(0.3 * E.names(hh['holdings']).get(sym, 0) * tot)}",
                  'pathway': 'Excluded (above 50%): exchange fund, options overlay or staged sales in brokerage; specialist' if ex else 'Tax-managed SMA, tax-efficient transition, direct indexing with the stock excluded',
                  'flow': 'na' if ex else 'lift'})
    elif o['ws'] == 'ws4':
        o.update({'uc': 10, 'trigger': (o['rel'][0] if o['rel'] else '') + ' · ' + o['type'], 'size': o['impact'], 'value': 'Feeds the allocation or position review',
                  'pathway': 'Event-led entry to the allocation review', 'flow': 'na'})
    elif o['ws'] == 'ws2':
        v = D.value(hh, D.default_costs(hh))
        o.update({'uc': 7, 'trigger': 'Opportunity accepted: advisor positioning', 'size': f'{money(amt(hh))} brokerage assets',
                  'value': f"≈ {money(v['quant'])} a year of estimated value vs fee +{money(v['inc'])}", 'pathway': 'Advisory program: the client story and proposal', 'flow': 'shift'})
    o['pw'] = o.get('pw') or pw_of(o)
    return o


def buckets(hh: dict) -> dict:
    """Every brokerage holding (or part of it) in exactly one bucket. Bond calls and maturities are a timing note only."""
    ex = D.elig(hh)['state'] == 'ineligible'
    B = {'move': 'Moves now (in kind)', 'gated': 'Held for cost basis', 'kept': 'Kept in brokerage', 'excluded': 'Excluded (above the 50% limit)'}
    rows = []
    for x in X.routing(hh):
        h = next((y for y in hh['holdings'] if y['sym'] == x['sym'] and y.get('acct') == 'brokerage'), {})
        b = 'excluded' if ex else 'move' if x['route'] in ('inkind', 'swap', 'transfer', 'harvest', 'instep') else 'gated' if x['route'] == 'basis' else 'kept'
        if h.get('kind') == 'bond':
            ov = (f"Callable {h['call_date']}: proceeds can be reinvested then" if h.get('call_date') else
                  f"Matures {h['maturity'][:4]}: proceeds can be reinvested then" if h.get('maturity') else '')
        else:
            ov = 'Protected reserve and near-term needs' if x['route'] == 'reserve' else ''
        rows.append({**x, 'bucket': b, 'label': B[b], 'overlay': ov})
    sm = lambda k: nsum(r['mv'] for r in rows if r['bucket'] == k)
    return {'rows': rows, 'move': sm('move'), 'gated': sm('gated'), 'kept': sm('kept'), 'excluded': sm('excluded'), 'total': nsum(r['mv'] for r in rows), 'labels': B}


def amounts(hh: dict) -> dict:
    e = D.elig(hh); ex = e['state'] == 'ineligible'; tr = transition(hh); cs = X.cash_split(hh); K = buckets(hh)
    later = [{'amt': K['gated'], 'gate': 'Cost basis on file', 'owner': 'Operations'}] if any(r['bucket'] == 'gated' for r in K['rows']) else []
    held = [{'sym': r['sym'], 'amt': r['mv'], 'why': 'awaiting cost basis' if r['bucket'] == 'gated' else 'liquidity reserve and near-term needs' if r['route'] == 'reserve'
             else re.sub(r':.*$', '', r['overlay'] or r['why']).lower()} for r in K['rows'] if r['bucket'] in ('kept', 'gated')]
    overlays = [{'sym': r['sym'], 'amt': r['mv'], 'note': r['overlay']} for r in K['rows'] if r['overlay'] and r['route'] != 'reserve']
    needs_later = nsum(v for y, v in ((DATA['concentration'].get('cash_needs') or {}).get(hh['id']) or {}).items() if int(y) > 2027)
    reserve_missing = hh.get('liquidity_reserve') is None
    conf = 'Low' if ex else 'Medium' if K['gated'] or reserve_missing else 'High'
    aligned = 0 if ex else tr['aligned']
    return {'identified': amt(hh), 'eligible': 0 if ex else K['move'] + K['gated'], 'now': 0 if ex else K['move'], 'later': later, 'laterSum': 0 if ex else K['gated'],
            'kept': 0 if ex else K['kept'], 'excluded': K['excluded'], 'reserve': cs['reserve'], 'conf': conf, 'ex': ex, 'held': held, 'overlays': overlays,
            'needsLater': needs_later, 'reserveMissing': reserve_missing, 'alignY1': 0 if ex else tr['pct'], 'repositionOverTime': 0 if ex else max(0, K['move'] - aligned), 'buckets': K}


def why_of(o: dict, st: State) -> str:
    """The one sentence that says why this household, now."""
    hh = o['hh']; cs = X.cash_split(hh); tr = transition(hh)
    if o['uc'] == 4:
        return f"{money(cs['investable'])} of cash sits above the CIO target after a {money(cs['reserve'])} reserve"
    if o['uc'] == 8:
        sym = (o.get('pos') or ':').split(':')[1]; sh = E.names(hh['holdings']).get(sym, 0)
        return f"{sym} is {pct(sh, 1)} of the account" + (', above the 50% limit' if o['act'][1] == 'bad' else '')
    if o['uc'] == 1:
        w = D.ws1(hh, D.BASE, st)
        return f"Expected volatility {pct(w['g']['st']['vol'], 1)} is above the {hh['profile']} band" if w['kind'] == 'risk' else f"The allocation is outside CIO tolerance: {gap_text(hh).lower()}"
    if o['uc'] == 2:
        return (f"{money(tr['gains'])} of embedded gains" + (f" and {money(tr['losses'])} of harvestable losses" if tr['losses'] else '') + ' call for a tax-aware transition'
                if tr['gains'] > 1000 else f"{money(tr['losses'])} of harvestable losses can offset future gains")
    if o['uc'] == 3:
        return f"{o['type']}: the proceeds need a plan" if 'callable' in o['type'] else 'Individual bonds are unmanaged'
    if o['uc'] == 5:
        mx = max(h['expense_bps'] for h in hh['holdings'] if (h.get('expense_bps') or 0) >= DATA['pathway']['thresholds']['high_cost_bps'])
        return f"Funds costing up to {num(mx)} bp where model funds cost {DATA['fees']['model_fund_bps']} bp"
    return o['type']


def catalyst(hh: dict, ops: list[dict]) -> list[str]:
    c = []
    if hh['meeting']['inDays'] <= 7:
        c.append(f"{hh['meeting']['type'].lower()} in {hh['meeting']['inDays']} day{s_(hh['meeting']['inDays'])}")
    if any(o['uc'] == 3 and 'callable' in o['type'] for o in ops): c.append('bond call within 90 days')
    if any(o['ws'] == 'ws4' and o['status'] == 'respond' for o in ops): c.append('client asked a question')
    return c


def cues(hh: dict, ops: list[dict], A: dict) -> list[list[str]]:
    c = []
    if hh['meeting']['inDays'] <= 7:
        c.append(['meet', f"Meeting in {hh['meeting']['inDays']} day{s_(hh['meeting']['inDays'])}"])
    call = next((o for o in ops if o['uc'] == 3 and 'callable' in o['type']), None)
    if call:
        m = re.search(r'\d{4}-\d{2}-\d{2}', call['type']); c.append(['date', 'Call date ' + (m.group(0) if m else '')])
    if any(o['ws'] == 'ws4' and o['status'] == 'respond' for o in ops): c.append(['ask', 'Client request'])
    if transition(hh)['noBasis']: c.append(['basis', 'Tax-basis blocker'])
    if A['now'] >= 10e6: c.append(['amt', 'Large movable amount'])
    return c


def blocker(hh: dict) -> dict:
    e = D.elig(hh); tr = transition(hh)
    ins = [k.split(':')[1] for k, v in DATA['concentration']['positions'].items() if k.startswith(hh['id'] + ':') and v.get('insider')]
    if e['state'] == 'ineligible': return {'t': 'Above the 50% single-security limit', 'owner': 'Specialist'}
    if tr['noBasis']: return {'t': f"{money(tr['noBasis'])} without cost basis", 'owner': 'Operations'}
    if ins: return {'t': f"Insider rules for {', '.join(ins)}: pre-clearance", 'owner': 'Compliance'}
    if hh.get('manager_run'): return {'t': 'Manager-run sleeve: the manager decides', 'owner': 'Manager'}
    return {'t': 'Suitability determination', 'owner': 'Advisor'}


def hstate(hh: dict, st: State) -> dict:
    """Household workflow: assess → paths → proposal → handoff, or specialist, or an outcome."""
    k = 'hh:' + hh['id']; d = st.disp.get(k); L = D.life(d); path = st.choice.get(k); rev = st.rev(hh['id']); ex = D.elig(hh)['state'] == 'ineligible'
    if L['state'] in ('closed', 'monitoring', 'deferred'): step = 'outcome'
    elif not d or d.get('status') not in ('ready', 'review', 'specialist'): step = 'assess'
    elif ex or d['status'] == 'specialist': step = 'specialist'
    elif not path: step = 'paths'
    elif rev != 'compliance': step = 'proposal'
    else: step = 'handoff'
    nxt = {'assess': ['Review assessment', 'assess'], 'paths': ['Compare paths', 'paths'], 'proposal': ['Prepare proposal', 'proposal'], 'handoff': ['Complete handoff', 'handoff'],
           'specialist': ['Request specialist', 'assess'], 'outcome': [L['label'] + (': ' + L['note'] if L['note'] else ''), 'assess']}[step]
    return {'k': k, 'd': d, 'L': L, 'path': path, 'rev': rev, 'step': step, 'next': ['Request specialist', 'assess'] if ex and step == 'assess' else nxt}


def primary(ops: list[dict]):
    def w(o):
        hh = o['hh']
        if o['uc'] == 8:
            return 4 if o['act'][1] == 'bad' else 3 + min(0.9, E.names(hh['holdings']).get((o.get('pos') or ':').split(':')[1], 0) * 2)
        return {4: 3.2 if X.cash_split(hh)['investable'] > 0.1 * amt(hh) else 1.5, 1: 2.8 if o['status'] == 'review' else 1,
                3: 2.6 if 'callable' in o['type'] else 1.2, 2: 2, 5: 1.5, 10: 0.8, 7: 0.1, 12: 0.5}.get(o['uc'], 0)
    return sorted(ops, key=lambda o: -w(o))[0] if ops else None


def households(q: list[dict], st: State) -> list[dict]:
    """Rank households: excluded last; then a dated catalyst (meeting, call, client request); then the amount movable now."""
    out = []
    for hh in HHS():
        ops = [o for o in q if o['hh']['id'] == hh['id']]; open_ = [o for o in ops if o['grp'] != 'done']
        e = D.elig(hh); A = amounts(hh); ex = e['state'] == 'ineligible'; prim = primary(open_ or ops); cat = catalyst(hh, open_); hs = hstate(hh, st)
        filt = 'waiting' if ex or hs['step'] == 'specialist' else 'propose' if hs['step'] in ('proposal', 'handoff') else 'done' if hs['L']['state'] != 'open' else 'discuss'
        out.append({'hh': hh, 'ops': ops, 'open': open_, 'ex': ex, 'e': e, 'scope': A['now'], 'seg': segment(hh), 'tr': transition(hh), 'f': forgone(hh), 'A': A,
                    'prim': prim, 'cat': cat, 'cues': cues(hh, open_, A), 'why': why_of(prim, st) if prim else '', 'blk': blocker(hh), 'hs': hs, 'filt': filt,
                    'path': next((p for p in paths(hh, st) if p.get('suggested')), None)})
    return sorted(out, key=lambda x: (x['ex'], -(len(x['cat']) > 0), -x['A']['now']))


def paths(hh: dict, st: State) -> list[dict]:
    """Two or three credible routes, each with amount, timing, tax and cost, feasibility with owners, and an approver."""
    e = D.elig(hh); A = amounts(hh); tr = transition(hh); lt = hh['rates']['lt']; ex = e['state'] == 'ineligible'
    ins = any(k.startswith(hh['id'] + ':') and v.get('insider') for k, v in DATA['concentration']['positions'].items())
    amt_r = max(1, D.round_k(A['now'])); c = X.costs(hh, amt_r, DATA['fees']['brokerage']['turnover'], 0.5)
    prog = X.opt(c, 'program'); sma = X.opt(c, 'sma'); stay = X.opt(c, 'stay')
    conc = [k for k, w in E.names(hh['holdings']).items() if w > st.th]; v = D.value(hh, c)
    common = [{'t': 'Suitability determination', 'ok': False, 'owner': 'Advisor'}]
    if tr['noBasis']: common.append({'t': f"{money(tr['noBasis'])} without cost basis: no sale or tax estimate until found", 'ok': False, 'owner': 'Operations'})
    if ins: common.append({'t': 'Insider shares: pre-clearance and trading windows', 'ok': False, 'owner': 'Compliance'})
    if hh.get('manager_run'): common.append({'t': 'Manager-run sleeve stays with its manager', 'ok': True, 'owner': 'Manager'})
    if ex:
        return [{'id': 'specialist', 'why': 'The program is not available above 50%', 'trade': ['No program fee or enrollment now', 'Position risk stays until a plan is in place'],
                 'account': 'Nothing moves into the program now', 'trading': 'Staged sales in brokerage within trading windows', 'name': 'Specialist route for the position', 'suggested': True,
                 'rationale': f"{e['reason']}; the program is not available until the position is below 50%.", 'amount': 'Program: none now',
                 'timing': 'Specialist plan first; staged sales in brokerage within trading windows', 'tax': 'Planned by the specialist; year one within the gain budget',
                 'cost': f"{money(remain(hh)['cost'])} a year in brokerage today",
                 'feas': [{'t': 'Concentrated stock specialist review', 'ok': False, 'owner': 'Specialist'}] + ([{'t': 'Pre-clearance', 'ok': False, 'owner': 'Compliance'}] if ins else []),
                 'approver': 'Specialist and advisor', 'blocked': False}]
    full = max(0, tr['gains'] - tr['losses']) * lt
    yrs = math.ceil(tr['gains'] / hh['gain_budget']) if tr['gains'] and hh.get('gain_budget') else 1
    yy = f"{yrs} year{s_(yrs)}"; now = money(A['now']); al = js_round(tr['pct'] * 100); pbps = js_round(prog['bps'])
    steady = f"{money(prog['total'])} a year ({pbps} bp), steady state on {now} from enrollment, vs {money(stay['total'])} today"
    out = [{'id': 'rebalance', 'name': 'Transfer and rebalance now', 'rationale': 'Fastest alignment with the CIO allocation; realizes the gains needed in year one.',
            'why': 'Fastest route to the CIO allocation', 'trade': ['Highest year-one tax', 'Full alignment in year one'], 'account': f'{now} moves in kind at enrollment',
            'trading': 'Repositioned in year one (≈100% aligned)', 'amount': f'{now} now', 'timing': 'Move now; rebalance fully in year one',
            'tax': f'≈ {money(full)} in year one after losses (planning; depends on validated lots and rates)' if tr['gains'] else 'Little or no gain to realize',
            'cost': steady, 'feas': common, 'approver': 'Advisor; compliance reviews the proposal'},
           {'id': 'phased', 'why': 'Keeps year-one tax within the gain budget' if tr['gains'] else 'Invests excess cash gradually',
            'trade': [f"Year-one tax ≈ {money(tr['taxNet'])}", f'Full alignment takes about {yy}' if tr['gains'] else 'About six months to align'],
            'account': f'{now} moves in kind at enrollment',
            'trading': f'≈{al}% aligned in year one' + (f"; {money(tr['parts']['instep'])} cash invested over six months" if tr['parts']['instep'] else '') + (f'; the rest over about {yy}' if tr['gains'] else ''),
            'name': 'Phased and tax-aware: cash in steps, appreciated holdings over time' if tr['parts']['instep'] else 'Phased and tax-aware transition',
            'rationale': f"Keeps year-one tax within the {money(hh.get('gain_budget'))} gain budget" + (f" and invests {money(tr['parts']['instep'])} of excess cash over six months" if tr['parts']['instep'] else '') + '.',
            'amount': f'{now} now; ≈{al}% aligned in year one', 'timing': f'Full alignment in about {yy}' if tr['gains'] else 'About six months',
            'tax': f"≈ {money(tr['taxNet'])} in year one after losses (planning; depends on validated lots and rates)", 'cost': steady + f"; trading ≈ {money(tr['trading'])}",
            'feas': common, 'approver': 'Advisor; compliance reviews the proposal'}]
    if v['diOk'] and (conc or tr['gains'] > 0.1 * A['now']):
        cj = ' and '.join(conc); sbps = js_round(sma['bps'])
        out.append({'why': f'Keeps {cj} out of new money and harvests losses' if conc else 'Harvests losses stock by stock',
                    'trade': [f'Higher cost: {sbps} bp vs {pbps} bp', f"Harvesting ≈ {money(v['harvNet'])} a year after the manager fee (modeled)"],
                    'account': f'{now} moves in kind at enrollment; a manager takes existing stocks', 'trading': f'Concentration reduced over about {yy}' if tr['gains'] else 'Months',
                    'id': 'managed', 'name': 'Managed accounts: tax-managed SMA and direct indexing' + (f' excluding {cj}' if conc else ''),
                    'rationale': 'Harvests losses stock by stock' + (f" and keeps {', '.join(conc)} out of new money" if conc else '') + '; a manager takes existing stocks in kind.',
                    'amount': f'{now} now', 'timing': f'Concentration reduced over about {yy}' if tr['gains'] else 'Months',
                    'tax': f"≈ {money(tr['taxNet'])} in year one; harvesting ≈ {money(v['harvNet'])} a year after the manager fee (planning)",
                    'cost': f"{money(sma['total'])} a year ({sbps} bp), steady state on {now} from enrollment, vs {money(stay['total'])} today",
                    'feas': common + [{'t': f'Product eligibility and minimums ({money(250000)})', 'ok': A['now'] >= 250000, 'owner': 'Product team'}],
                    'approver': 'Advisor; product team confirms; compliance reviews'})
    pick = 'managed' if conc and any(x['id'] == 'managed' for x in out) else 'phased' if (tr['gains'] > 0 or tr['parts']['instep'] > 0) else 'rebalance'
    for x in out:
        x['suggested'] = x['id'] == pick
    return out


def remain(hh: dict) -> dict:
    """Staying in brokerage: always offered and always recordable."""
    c = X.costs(hh, max(1, D.round_k(amt(hh))), DATA['fees']['brokerage']['turnover'], 0.5)
    return {'cost': X.opt(c, 'stay')['total'], 'lc': X.opt(c, 'index')}


def handoff(hh: dict, st: State) -> dict:
    """What people must do before anything moves."""
    rd = D.ready(hh, {'product': True}); A = amounts(hh); tr = transition(hh); k = 'hh:' + hh['id']; path = st.choice.get(k)
    items = [{'id': 'path', 't': 'Strategy and pace selected', 'owner': 'Advisor', 'auto': bool(path)},
             {'id': 'proposal', 't': 'Proposal submitted for compliance review', 'owner': 'Advisor', 'auto': st.rev(hh['id']) == 'compliance'}]
    items += [{'id': f'i{i}', 't': x['t'], 'owner': x['owner']} for i, x in enumerate(rd[2]['items'])]
    stp = [{'m': MONTHS[i], 'amt': tr['parts']['instep'] / 6} for i in range(6)] if tr['parts']['instep'] else []
    return {'items': items, 'steps': stp, 'A': A, 'tr': tr, 'path': path}


def book(q: list[dict], st: State) -> dict:
    """Internal management view (not client-facing): addressable assets by segment and revenue before and after."""
    H = households(q, st); inc = [x for x in H if not x['ex']]; seg = {'low': 0.0, 'medium': 0.0, 'hard': 0.0}
    for x in inc: seg[x['seg']] += x['scope']
    brk = nsum(amt(hh) for hh in HHS())
    excl = nsum(amt(x['hh']) for x in H if x['ex']) + nsum(x['tr']['parts']['stay'] for x in inc)
    sc = nsum(x['scope'] for x in inc)
    rev_now = nsum(x['scope'] * DATA['fees']['brokerage']['turnover'] * DATA['fees']['brokerage']['commission'] for x in inc)
    rev_adv = nsum(X.program_fee(x['scope'])['fee'] for x in inc)
    return {'seg': seg, 'brk': brk, 'excl': excl, 'scope': sc, 'revNow': rev_now, 'revAdv': rev_adv,
            'bpsNow': rev_now / sc * 1e4 if sc else 0, 'bpsAdv': rev_adv / sc * 1e4 if sc else 0}


def stages(hh: dict, key: str, st: State, ctx: dict | None = None) -> list[dict]:
    """The five operating stages for the task panel."""
    e = D.elig(hh); d = st.disp.get(key); ch = st.choice.get(key); rev = st.rev(hh['id']); rd = D.ready(hh, ctx or {}); ex = e['state'] == 'ineligible'
    pursue = bool(d) and d.get('status') in ('ready', 'review', 'specialist', 'respond'); notp = bool(d) and d.get('status') in ('stay', 'unsuitable', 'defer', 'monitor')
    design_items = [x for x in rd[1]['items'] if 'single-security limit' not in x['t']]
    handed = bool(st.handed.get(hh['id']))
    return [
        {'stage': 'Identify', 'state': 'ready', 'note': f"Found, but outside the addressable universe: {e['reason']}" if ex else 'Opportunity found by an approved screen',
         'does': 'Ranked opportunity with conversion potential', 'decide': 'Advisor or specialist picks it up', 'control': 'Approved thresholds; data masking', 'items': []},
        {'stage': 'Analyze', 'state': 'ready' if pursue else 'blocked' if notp else 'pending',
         'note': 'Advisor decided to pursue' if pursue else (f"Not pursued: {D.STATUS[d['status']][0]}" + (' · ' + d['reason'] if d.get('reason') else '')) if notp else 'Advisor to decide whether to pursue',
         'does': 'Household positioning against goals and the CIO target', 'decide': 'Advisor decides to pursue', 'control': 'Approved content; lower-cost alternative shown', 'items': []},
        {'stage': 'Design', 'state': 'blocked' if ex else 'ready' if ch else 'pending',
         'note': 'Program paths blocked; specialist route' if ex else f'Selected: {ch}' if ch else 'Select a strategy and pace' + (f' · {len(design_items)} to clear' if design_items else ''),
         'does': 'Matches options on suitability and overlap; builds the transition plan', 'decide': 'Advisor selects strategy and pace', 'control': 'Fit before tax; no tax estimate without basis',
         'items': [{'t': 'Route: concentrated stock specialist', 'owner': 'Specialist'}] if ex else design_items},
        {'stage': 'Propose', 'state': 'blocked' if ex else 'ready' if rev == 'compliance' else 'pending',
         'note': 'No program proposal above the limit' if ex else 'Submitted for compliance review' if rev == 'compliance' else 'Advisor reviewed; submit for compliance' if rev == 'advisor' else 'Story and proposal drafted; advisor review needed',
         'does': 'Builds the client story and proposal', 'decide': 'Advisor approves and presents', 'control': 'Advisor review; never sent automatically', 'items': []},
        {'stage': 'Implement', 'state': 'pending' if handed else 'blocked',
         'note': 'Handed off: operations to enroll (prototype)' if handed else f"Not cleared: {len(rd[2]['items'])} prerequisites outstanding",
         'does': 'Prepares the enrollment, transition and invest-in-steps hand-off', 'decide': 'Advisor and operations enroll', 'control': 'No autonomous execution or enrollment', 'items': rd[2]['items']}]
