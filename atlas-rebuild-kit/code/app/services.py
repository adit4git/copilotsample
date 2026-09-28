from __future__ import annotations
from typing import Any
from .data import *
from .engine import evaluate_offering,evaluate_composition

PROGRAM_LISTS={'IAP':IAP_OFFERINGS,'MGI':MGI_OFFERINGS}

def household_or_404(household_id:str):
    if household_id not in BY_ID: raise KeyError(household_id)
    return BY_ID[household_id]

def offering_result(household_id:str, offering_id:str):
    hh=household_or_404(household_id); facts=derive_facts(hh,offering_id)
    result=evaluate_offering(offering_id,facts,RULE_STORE,hh.get('program','IAP'))
    if hh.get('program','IAP')=='IAP' and offering_id!='iapEnrollment':
        pre=evaluate_offering('iapEnrollment',derive_facts(hh,offering_id),RULE_STORE,'IAP')
        result['prerequisite']=pre
    return result

def all_verdicts(household_id:str):
    hh=household_or_404(household_id)
    return {i:offering_result(household_id,i) for i in PROGRAM_LISTS[hh.get('program','IAP')] if i!='iapEnrollment'}

def composition_result(household_id:str, ids:list[str]):
    hh=household_or_404(household_id)
    facts={i:derive_facts(hh,i) for i in ids}
    return evaluate_composition(ids,facts,RULE_STORE,hh.get('program','IAP'))

def enrich(hh):
    row={**hh,'clientGL':client_gl(hh),'clientHarvest':client_harvest(hh),'taxAlpha':abs(client_harvest(hh))*.238}
    return row

def nba(kind:str,fa:str):
    book=[enrich(x) for x in my_book(fa)]
    if kind=='meetings': return sorted([x for x in book if x.get('nextMeeting')],key=lambda x:x['nextMeeting']['inDays'])[:4]
    if kind=='drift':
        rows=[]
        for x in book:
            if x['concentration']: rows.append({**x,'drift':x['concentration'][0]})
            elif abs(x['current']['cash']-x['target']['cash'])>=12: rows.append({**x,'drift':{'label':'Cash allocation','pct':x['current']['cash'],'threshold':x['target']['cash']}})
        return sorted(rows,key=lambda x:x['drift']['pct']-x['drift']['threshold'],reverse=True)[:4]
    if kind=='cio': return sorted([x for x in book if x['cio']['score']!='Low'],key=lambda x:{'High':0,'Medium':1}.get(x['cio']['score'],2))[:4]
    if kind=='deep': return sorted(book,key=lambda x:x['aum'],reverse=True)[:4]
    raise ValueError(kind)

def tax_desk(fa:str):
    rows=[]
    for hh in my_book(fa):
        row=enrich(hh); ids=['taxManagedSMA','qlhOverlay','dtlhOverlay'] if hh.get('program','IAP')=='IAP' else MGI_OFFERINGS
        row['verdicts']={i:offering_result(hh['id'],i) for i in ids}; rows.append(row)
    return sorted(rows,key=lambda x:x['taxAlpha'],reverse=True)

def _effective_eligible(result):
    return result['verdict']=='ELIGIBLE' and (not result.get('prerequisite') or result['prerequisite']['verdict']=='ELIGIBLE')

def cross_sell(fa:str):
    rows=[]
    for hh in my_book(fa):
        if hh.get('program','IAP')!='IAP': continue
        enrolled={k for k,v in {**hh.get('programs',{}),**hh.get('overlays',{})}.items() if v=='enrolled'}
        for off in ['privateBanking','trustEstate','alternatives','directIndexing','lending','insurance','charitable','taxManagedSMA','qlhOverlay','dtlhOverlay','transition','temSms']:
            r=offering_result(hh['id'],off)
            if _effective_eligible(r) and off not in enrolled:
                values={'alternatives':hh['aum']*.15*.01,'directIndexing':hh['aum']*.2*.004,'privateBanking':hh['aum']*.1*.015,'lending':hh['aum']*.2*.012,'trustEstate':15000,'insurance':12000,'charitable':10000,'taxManagedSMA':hh['aum']*.003,'qlhOverlay':hh['aum']*.0025,'dtlhOverlay':hh['aum']*.003,'transition':hh['aum']*.002,'temSms':hh['aum']*.003}
                rows.append({'household_id':hh['id'],'name':hh['name'],'offering_id':off,'label':r['label'],'estimated_value':round(values.get(off,0)),'reason':(r['reasons'][0]['message'] if r['reasons'] else 'All evaluated eligibility requirements are satisfied.'),'verdict':r['verdict']})
    return sorted(rows,key=lambda x:x['estimated_value'],reverse=True)

def book_context(fa:str):
    lines=[]
    for x in my_book(fa):
        e=enrich(x); meeting=x['nextMeeting']; concentration=x['concentration'][0]['label'] if x['concentration'] else 'none'
        lines.append(f"{x['name']} | {x['segment']} | AUM ${x['aum']:,.0f} | YTD {x['ytdReturn']}% | unrealized ${e['clientGL']:,.0f} | harvestable ${abs(e['clientHarvest']):,.0f} | meeting {meeting['inDays'] if meeting else 'none'} | concentration {concentration} | CIO {x['cio']['score']} | {x['notes']}")
    return '\n'.join(lines)

def local_answer(fa:str,message:str):
    q=message.lower(); book=my_book(fa)
    target=next((x for x in book if x['id'] in q or any(w.lower() in q for w in x['name'].split() if len(w)>3) or x['contact'].lower() in q),None)
    if target:
        e=enrich(target); meeting=target['nextMeeting']; return f"{target['name']} has ${target['aum']/1e6:.1f}M AUM, {target['risk']} risk, {target['ytdReturn']:.1f}% YTD return, and ${e['clientGL']/1e6:.2f}M unrealized P&L. " + (f"Next meeting is in {meeting['inDays']} days: {meeting['note']}" if meeting else target['notes'])
    if any(k in q for k in ['harvest','tax loss','losses','tlh']):
        rows=sorted([enrich(x) for x in book],key=lambda x:x['taxAlpha'],reverse=True)[:3];return 'Top current tax-loss opportunities: '+', '.join(f"{x['name']} (${abs(x['clientHarvest']):,.0f} losses; illustrative tax value ${x['taxAlpha']:,.0f})" for x in rows)+'.'
    if any(k in q for k in ['meeting','week','upcoming']):
        rows=nba('meetings',fa); return 'Upcoming meetings: '+(', '.join(f"{x['name']} in {x['nextMeeting']['inDays']} days" for x in rows) if rows else 'none scheduled')+'.'
    if any(k in q for k in ['eligible','cross-sell','opportunity']):
        rows=cross_sell(fa)[:5];return 'Highest reviewed opportunities: '+(', '.join(f"{x['name']} — {x['label']}" for x in rows) if rows else 'none with a clean eligible verdict')+'.'
    if any(k in q for k in ['concentration','drift','breach','overweight']):
        rows=nba('drift',fa);return 'Priority drift cases: '+(', '.join(f"{x['name']} — {x['drift']['label']} {x['drift']['pct']}% vs {x['drift']['threshold']}% limit" for x in rows) if rows else 'none')+'.'
    if any(k in q for k in ['cio','house view','align','publication']):
        rows=nba('cio',fa);return 'CIO alignment follow-ups: '+(', '.join(f"{x['name']} — {x['cio']['view']}" for x in rows) if rows else 'none')+'.'
    if any(k in q for k in ['top','largest','biggest']): return 'Largest relationships: '+', '.join(f"{x['name']} (${x['aum']/1e6:.1f}M)" for x in nba('deep',fa))+'.'
    return 'I can rank tax-loss opportunities, prepare a client meeting, show upcoming meetings, identify concentration drift, summarize CIO misalignment, or list reviewed cross-sell opportunities.'

# ---- Draft review (human-in-the-loop) ----
# In-memory only: a real deployment would persist this per-household/kind draft
# and its approve/decline/edit history in a database, keyed by advisor + household.
DRAFT_STORE: dict[str, dict] = {}

def draft_key(household_id: str, kind: str) -> str:
    return f"{household_id}:{kind}"

def household_draft_context(household_id: str) -> str:
    """Rich, single-household context for drafting — deliberately more detailed
    than book_context(), which is built for ranking across an entire book."""
    hh = household_or_404(household_id); e = enrich(hh)
    meeting = hh.get('nextMeeting')
    concentration = hh['concentration'][0] if hh.get('concentration') else None
    enrolled = {**hh.get('programs', {}), **hh.get('overlays', {})}
    elig_lines = []
    for off in PROGRAM_LISTS.get(hh.get('program', 'IAP'), []):
        if off == 'iapEnrollment': continue
        try:
            r = offering_result(household_id, off)
            if _effective_eligible(r) and enrolled.get(off) != 'enrolled':
                elig_lines.append(f"  - {r['label']}: eligible, not yet enrolled")
        except Exception:
            pass
    holdings_lines = '\n'.join(
        f"  - {h['sym']} ({h['name']}): {h['ac']}, ${h['mv']:,.0f}" for h in hh['holdings'][:12]
    )
    return f"""HOUSEHOLD: {hh['name']}
Entity: {hh['entity']} | Segment: {hh['segment']} | Client since: {hh['since']} | Risk mandate: {hh['risk']}
Primary contact(s): {hh['contact']}
AUM: ${hh['aum']:,.0f} | Annual revenue: ${hh['rev']:,.0f} | YTD return: {hh['ytdReturn']}%
Unrealized gain/loss: ${e['clientGL']:,.0f} | Harvestable losses: ${abs(e['clientHarvest']):,.0f} (~${e['taxAlpha']:,.0f} illustrative tax alpha)
Next meeting: {(str(meeting['inDays']) + ' days from now — ' + meeting['type'] + '. Advisor note: ' + (meeting.get('note') or 'none')) if meeting else 'None currently scheduled'}
Concentration/policy: {(concentration['label'] + ' at ' + str(concentration['pct']) + '% vs a ' + str(concentration['threshold']) + '% policy limit') if concentration else 'No policy breaches flagged'}
CIO alignment: {hh['cio']['score']} drift — "{hh['cio']['view']}" ({hh['cio']['pub']}). {hh['cio']['diverge']}.
Holdings (showing {min(12,len(hh['holdings']))} of {len(hh['holdings'])}):
{holdings_lines}
Eligible but unenrolled programs/services:
{chr(10).join(elig_lines) if elig_lines else '  - none currently flagged'}
Advisor notes on file: {hh.get('notes','') or 'none'}
"""

def local_meeting_prep_draft(household_id: str) -> str:
    """Deterministic, fully-grounded fallback used when no LLM key is configured
    or the live call fails — the draft feature must always work."""
    hh = household_or_404(household_id); e = enrich(hh)
    meeting = hh.get('nextMeeting')
    concentration = hh['concentration'][0] if hh.get('concentration') else None
    lines = [f"## Meeting prep — {hh['name']}"]
    if meeting:
        lines.append(f"**{meeting['type']}** · in {meeting['inDays']} days · {hh['segment']} · ${hh['aum']:,.0f} AUM\n")
    else:
        lines.append(f"{hh['segment']} · ${hh['aum']:,.0f} AUM — no meeting currently scheduled.\n")
    lines.append("### What prompted this meeting\n" + (meeting.get('note') if meeting and meeting.get('note') else "Standing scheduled review; no specific trigger on file.") + "\n")
    lines.append(f"### Portfolio snapshot\n- YTD return: {hh['ytdReturn']}%\n- Unrealized gain/loss: ${e['clientGL']:,.0f}\n- Harvestable losses: ${abs(e['clientHarvest']):,.0f} (~${e['taxAlpha']:,.0f} illustrative tax alpha)\n")
    lines.append("### Concentration & risk\n" + (f"{concentration['label']} at {concentration['pct']}% vs a {concentration['threshold']}% policy limit — worth raising directly." if concentration else "No policy breaches flagged this cycle.") + "\n")
    lines.append(f"### CIO alignment\n{hh['cio']['score']} drift. \"{hh['cio']['view']}\" {hh['cio']['diverge']}.\n")
    talking = []
    if meeting and meeting.get('note'): talking.append(meeting['note'])
    if concentration: talking.append(f"Discuss trimming {concentration['label']} toward the {concentration['threshold']}% policy target.")
    if abs(e['clientHarvest']) > 10000: talking.append(f"Flag ${abs(e['clientHarvest']):,.0f} of harvestable losses (~${e['taxAlpha']:,.0f} illustrative tax alpha) ahead of year-end.")
    if hh['cio']['score'] != 'Low': talking.append(f"Walk through the CIO's current view: {hh['cio']['view']}")
    if not talking: talking.append("Confirm goals and risk tolerance are still current; no urgent flags this cycle.")
    lines.append("### Suggested talking points\n" + '\n'.join(f"{i+1}. {t}" for i, t in enumerate(talking[:5])) + "\n")
    enrolled = {**hh.get('programs', {}), **hh.get('overlays', {})}
    elig = []
    for off in PROGRAM_LISTS.get(hh.get('program', 'IAP'), []):
        if off == 'iapEnrollment': continue
        try:
            r = offering_result(household_id, off)
            if _effective_eligible(r) and enrolled.get(off) != 'enrolled':
                elig.append(r['label'])
        except Exception:
            pass
    lines.append("### Eligible next steps\n" + ('\n'.join(f"- {x}" for x in elig) if elig else "- No unenrolled eligible programs flagged this cycle."))
    return '\n'.join(lines)

def generate_draft_local(household_id: str, kind: str) -> str:
    if kind == 'meeting_prep':
        return local_meeting_prep_draft(household_id)
    return f"Draft generation for '{kind}' is not yet supported."

# ---- Transition scenario workbench ----
# Some offerings model a real portfolio transition (trades to execute); others
# are procedural onboardings (paperwork, meetings, funding). Both kinds share
# the same top-level shape so the frontend can render them consistently.
TRADE_MODELABLE = {'directIndexing','taxManagedSMA','qlhOverlay','dtlhOverlay','temSms','transition','mgiTer','mgiQlh','mgiDtlh','dca'}
PROCEDURAL_OFFERINGS = {'alternatives','privateBanking','trustEstate','lending','insurance','charitable','iapEnrollment'}
# Illustrative ETF tickers used in this demo book. A real deployment would
# resolve this from a security master, not a hard-coded list.
_KNOWN_ETFS = {'VTI','VOO','ITOT','SCHB','SPY','IVV','VXUS','IEFA','VEA','EFA','IEMG','VWO','AGG','BND','MUB','TIP','LQD','HYG','SHY','GLD','VNQ','SCHF','IWM'}

def _is_single_stock(h: dict) -> bool:
    if h.get('type') == 'BOND': return False
    if h['ac'] == 'Cash': return False
    if h['ac'] == 'Municipal' and h.get('type') == 'BOND': return False
    if h['sym'] in ('CASH',): return False
    if h['sym'] in _KNOWN_ETFS: return False
    if h['ac'] == 'Fixed Income' and h['sym'] in _KNOWN_ETFS: return False
    # Individual bonds have specific ID-style tickers or type BOND
    if any(sep in h['sym'] for sep in ('-',)): return False
    return h['ac'] in ('US Equity','Intl Equity')

def _label_for_offering(offering: str) -> str:
    for _, o in RULE_STORE['offerings'].items():
        pass
    # RULE_STORE['offerings'][key]['label']
    return RULE_STORE['offerings'].get(offering, {}).get('label', offering)

def _current_state(hh, e):
    top = sorted(hh['holdings'], key=lambda h: -h['mv'])[:6]
    return {
        'aum': hh['aum'],
        'positions': len(hh['holdings']),
        'allocation': hh['current'],
        'target_allocation': hh['target'],
        'top_holdings': [{'sym': h['sym'], 'name': h['name'], 'ac': h['ac'], 'mv': h['mv'],
                          'weight': round(h['mv']/hh['aum']*100, 1),
                          'gl': (h['mv']-h['cost']) if h['cost'] is not None else None} for h in top],
        'concentration_flags': hh.get('concentration', []),
        'cash_pct': hh['current'].get('cash', 0),
        'ytd_realized_gains': hh.get('ytdRealizedGains', 0),
        'harvestable_losses': abs(e['clientHarvest']),
    }

def _gap_analysis(hh, e, offering, verdict):
    gaps = []
    prereq = (verdict or {}).get('prerequisite')
    if prereq and prereq.get('verdict') not in ('ELIGIBLE', None):
        # This offering's own rules may look clean (or merely unresolved),
        # but nothing here can actually happen until the household is
        # enrolled in the base program -- surface that first and plainly,
        # since it's the real, immediate blocker for a brokerage-only
        # prospect and must not get buried beneath the offering's own
        # unresolved-field noise.
        for r in prereq.get('reasons', []) + prereq.get('internal_only_reasons', []):
            if not r.get('missing_fields'):
                gaps.append({'severity':'required','message': f"IAP enrollment required first: {r.get('message','')}"})
    if verdict and verdict.get('verdict') in ('NEEDS_REVIEW', 'INELIGIBLE'):
        sev = 'review' if verdict['verdict'] == 'NEEDS_REVIEW' else 'required'
        for r in verdict.get('reasons', []) + verdict.get('internal_only_reasons', []):
            if not r.get('missing_fields'):
                gaps.append({'severity':sev,'message': r.get('message','')})
        for f in verdict.get('missing_fields', []):
            gaps.append({'severity':'review','message':f'Resolve unknown field: {f.replace("_"," ")}'})
    if offering == 'dtlhOverlay':
        non_etfs = [h for h in hh['holdings'] if _is_single_stock(h)]
        if non_etfs:
            gaps.append({'severity':'required',
                'message': f'Portfolio must be ETF-only for DTLH. {len(non_etfs)} non-ETF position(s) to swap: '+', '.join(h['sym'] for h in non_etfs[:5])})
    if offering in ('directIndexing','temSms'):
        conc = hh.get('concentration', [])
        if conc:
            gaps.append({'severity':'required',
                'message': f"Concentrated positions need trimming: {conc[0]['label']} at {conc[0]['pct']}% (policy limit {conc[0]['threshold']}%)."})
        if hh['current'].get('cash', 0) < 2:
            gaps.append({'severity':'recommended',
                'message':'Modest cash reserve helps stage the initial buy without forced timing.'})
    if offering == 'transition':
        missing_basis = [h for h in hh['holdings'] if h.get('cost') is None]
        indiv_fi = [h for h in hh['holdings'] if h.get('type') == 'BOND']
        if missing_basis:
            gaps.append({'severity':'scope_carveout',
                'message':f'{len(missing_basis)} lot(s) with unresolved cost basis excluded from TET scope: '+', '.join(h.get('lot_id',h['sym']) for h in missing_basis)+'.'})
        if indiv_fi:
            gaps.append({'severity':'scope_carveout',
                'message':f'{len(indiv_fi)} individual fixed-income position(s) excluded from TET scope: '+', '.join(h['sym'] for h in indiv_fi)+'.'})
        if not ACCOUNT_FACTS.get(hh['id'], {}).get('annual_transition_budget'):
            gaps.append({'severity':'recommended',
                'message':'No Annual Transition Budget has been elected yet. The Firm will produce a Service Analysis showing the impact of different budget levels \u2014 set one with the client before enrolling.'})
    if offering == 'dca':
        amt = ACCOUNT_FACTS.get(hh['id'], {}).get('dca_cash_amount')
        months = ACCOUNT_FACTS.get(hh['id'], {}).get('dca_schedule_months')
        if not amt or not months:
            gaps.append({'severity':'required',
                'message':'No DCA Cash amount and/or schedule length has been set yet \u2014 both are needed before a schedule can be modeled.'})
        else:
            gaps.append({'severity':'review',
                'message':'DCA Cash must be funded (in full or in part) within 60 days of the effective date, or the DCA Service is removed from the Account.'})
            gaps.append({'severity':'review',
                'message':'The first scheduled investment must occur within two weeks of the effective date.'})
    if not gaps:
        gaps.append({'severity':'clear','message':'No structural blockers. Ready to initiate.'})
    return gaps

def _propose_trades(hh, e, offering):
    trades = []
    holdings = hh['holdings']
    if offering in ('directIndexing','temSms','mgiDtlh'):
        # Replace equity sleeve with a broad SMA basket
        equity = [h for h in holdings if h['ac'] in ('US Equity','Intl Equity')]
        proceeds = 0
        for h in sorted(equity, key=lambda x: -x['mv']):
            weight = h['mv']/hh['aum']*100
            gl = (h['mv']-h['cost']) if h['cost'] is not None else None
            reason = (f'Trim concentration ({weight:.1f}% \u2192 basket weight).'
                if _is_single_stock(h) and weight > 5
                else 'Reallocate into direct-indexed broad-market sleeve.')
            trades.append({'action':'sell','sym':h['sym'],'name':h['name'],'value':h['mv'],'gl':gl,'reason':reason})
            proceeds += h['mv']
        # Harvest losses at onboarding to offset gains
        for h in holdings:
            if h.get('cost') is not None and (h['mv']-h['cost']) < -1000 and h not in equity:
                trades.append({'action':'harvest','sym':h['sym'],'name':h['name'],'value':h['mv'],
                    'gl':h['mv']-h['cost'],
                    'reason':f'Harvest ${abs(h["mv"]-h["cost"]):,.0f} of losses at onboarding; carry forward.'})
        if proceeds > 0:
            label = 'Direct-indexed broad-market SMA sleeve' if offering=='directIndexing' else 'Style-manager SMA sleeve'
            trades.append({'action':'buy','sym':'SMA*','name':f'{label} (~200 lines, illustrative universe)',
                'value':proceeds,'gl':None,'reason':'Basis reset at trade date. Overlay begins next business day.'})
    elif offering in ('taxManagedSMA','mgiTer'):
        # TER is PASSIVE (TER Term Sheet): no onboarding trades and no
        # proactive harvesting. It governs future trading -- best tax lot
        # selection, account-level wash sale protection, short-term gain
        # deferral and tax-prioritized withdrawals. Show the withdrawal order
        # TER would use today so the advisor sees what it actually changes.
        trades.append({'action':'note','sym':'','name':'No trades at enrollment','value':0,'gl':None,
            'reason':'TER is passive: it applies best tax lot selection, wash sale protection and short-term gain deferral whenever trading occurs.'})
        eligible = [h for h in holdings if h.get('cost') and h['ac'] not in ('Fixed Income','Municipal','Cash') and h.get('type') != 'BOND']
        ranked = sorted(eligible, key=lambda h: (h['mv']-h['cost'])/h['cost'])
        for i, h in enumerate(ranked[:4], start=1):
            pct = (h['mv']-h['cost'])/h['cost']*100
            trades.append({'action':'note','sym':h['sym'],'name':h['name'],'value':0,'gl':None,
                'reason':f'Tax-prioritized withdrawal order #{i}: {pct:+.1f}% unrealized (largest % losses are sold first).'})
    elif offering in ('qlhOverlay','mgiQlh'):
        # QLH Term Sheet: harvest lots with losses of 5% or more, every 91
        # days, subject to a turnover limit; not applied to fixed income.
        # Conservative reading: bond funds/ETFs are treated as fixed income too.
        for h in holdings:
            if not h.get('cost') or h['ac'] in ('Fixed Income','Municipal','Cash') or h.get('type') == 'BOND':
                continue
            pct = (h['mv']-h['cost'])/h['cost']*100
            if pct <= -5:
                trades.append({'action':'harvest','sym':h['sym'],'name':h['name'],'value':h['mv'],'gl':h['mv']-h['cost'],
                    'reason':f'{pct:.1f}% lot loss meets the 5% threshold: harvested in the next 91-day cycle; proceeds go to a replacement ETF for the 30-day wash sale period.'})
            elif pct < 0:
                trades.append({'action':'note','sym':h['sym'],'name':h['name'],'value':0,'gl':None,
                    'reason':f'{pct:.1f}% loss is below the 5% threshold: not harvested this cycle.'})
        if not any(t['action'] == 'harvest' for t in trades):
            trades.append({'action':'note','sym':'','name':'Nothing to harvest this cycle','value':0,'gl':None,
                'reason':'No eligible lot is down 5% or more; QLH re-checks every 91 days from enrollment.'})
    elif offering == 'dtlhOverlay':
        # Swap non-ETFs to ETF equivalents, then harvest
        for h in holdings:
            if _is_single_stock(h):
                gl = (h['mv']-h['cost']) if h['cost'] is not None else None
                trades.append({'action':'sell','sym':h['sym'],'name':h['name'],'value':h['mv'],'gl':gl,
                    'reason':'DTLH requires ETF-only positions.'})
                # Suggest a broad-market ETF as the replacement sleeve rather than a per-stock swap
        non_etf_mv = sum(h['mv'] for h in holdings if _is_single_stock(h))
        if non_etf_mv > 0:
            trades.append({'action':'buy','sym':'ITOT','name':'US broad-market ETF (equivalent exposure)',
                'value':non_etf_mv,'gl':None,'reason':'Preserves equity exposure while enabling DTLH.'})
        # Harvest on ETF losses
        for h in holdings:
            if not _is_single_stock(h) and h.get('cost') is not None and (h['mv']-h['cost']) < -1000:
                trades.append({'action':'harvest','sym':h['sym'],'name':h['name'],'value':h['mv'],
                    'gl':h['mv']-h['cost'],'reason':'Initial daily-cadence DTLH harvest at onboarding.'})
    elif offering == 'transition':
        # TET: the Annual Transition Budget is the client-elected annual net
        # LT-capital-gains ceiling (see the TET Term Sheet's own worked
        # example: $100K embedded gain, $40K budget -> $40K/$40K/$20K across
        # three years). Program-ineligible/no-cost-basis lots are excluded
        # elsewhere by the SCOPE_CARVEOUT gaps; here we stage the remaining
        # gain positions, largest first, against the real budget number
        # rather than a flat per-position threshold.
        budget = ACCOUNT_FACTS.get(hh['id'], {}).get('annual_transition_budget')
        gain_lots = sorted(
            [h for h in holdings if h.get('cost') is not None and h.get('type') != 'BOND' and (h['mv']-h['cost']) > 0],
            key=lambda h: -(h['mv']-h['cost']))
        if budget and budget > 0:
            year, remaining_this_year = 1, budget
            for h in gain_lots:
                gl = h['mv']-h['cost']
                staged_gain, portion_left = 0, gl
                pieces = []
                while portion_left > 0:
                    take = min(portion_left, remaining_this_year) if remaining_this_year > 0 else 0
                    if take <= 0:
                        year += 1; remaining_this_year = budget; continue
                    pieces.append((year, take))
                    portion_left -= take; remaining_this_year -= take
                    if portion_left > 0 and remaining_this_year <= 0:
                        year += 1; remaining_this_year = budget
                for yr, amt in pieces:
                    frac = amt/gl
                    trades.append({'action':'stage_sell','sym':h['sym'],'name':h['name'],'value':round(h['mv']*frac,2),'gl':round(amt,2),
                        'reason':f'Year {yr} of the Annual Transition Budget (${budget:,.0f}/yr): stage ${amt:,.0f} of this position\u2019s ${gl:,.0f} embedded gain.'})
        else:
            # No budget elected yet -- this is itself a gap (see
            # _gap_analysis), so fall back to a single illustrative pass over
            # the largest gain positions rather than silently proposing
            # nothing, since a scenario still needs to be shown.
            for h in gain_lots:
                gl = h['mv']-h['cost']
                if gl > 25000:
                    trades.append({'action':'stage_sell','sym':h['sym'],'name':h['name'],'value':h['mv'],'gl':gl,
                        'reason':f'No Annual Transition Budget elected yet \u2014 illustrative single-year sale of ~${gl:,.0f} embedded gain pending that election.'})
        for h in holdings:
            if h.get('cost') is not None and (h['mv']-h['cost']) < -1000:
                trades.append({'action':'harvest','sym':h['sym'],'name':h['name'],'value':h['mv'],
                    'gl':h['mv']-h['cost'],
                    'reason':f'Realize ${abs(h["mv"]-h["cost"]):,.0f} of losses to offset staged gains.'})
    elif offering == 'dca':
        # DCA deploys CASH into the strategy over time -- the mirror image of
        # TET's staged sells. No existing holdings are touched; this models
        # periodic buys of the DCA Cash into a placeholder strategy sleeve.
        f = ACCOUNT_FACTS.get(hh['id'], {})
        amt, months = f.get('dca_cash_amount'), f.get('dca_schedule_months')
        freq = (f.get('dca_frequency') or 'MONTHLY').upper()
        if amt and months:
            n = dca_installments(months, freq)
            per_period = round(amt / n, 2)
            label = DCA_FREQ_LABEL.get(freq, freq.lower())
            for m in range(1, n + 1):
                value = round(amt - per_period * (n - 1), 2) if m == n else per_period  # last absorbs rounding
                trades.append({'action':'stage_buy','sym':'DCA*','name':'Selected Investment Strategy (illustrative sleeve)',
                    'value':value,'gl':None,
                    'reason':f'Contribution {m} of {n} ({label}): invest ${value:,.0f} of DCA Cash into the selected Investment Strategy.'})
    return trades

DCA_FREQ_LABEL = {'WEEKLY':'weekly','BI_WEEKLY':'bi-weekly','MONTHLY':'monthly','BI_MONTHLY':'bi-monthly'}
def dca_installments(months: int, freq: str) -> int:
    """Equal installments for a Defined Duration schedule (DCA Term Sheet)."""
    import math
    return max(1, {'WEEKLY': round(months*52/12), 'BI_WEEKLY': round(months*26/12),
                   'BI_MONTHLY': math.ceil(months/2)}.get(freq, months))

def _target_state(hh, e, offering, trades):
    sells = sum(t['value'] for t in trades if t['action'] in ('sell','stage_sell'))
    buys = sum(t['value'] for t in trades if t['action'] in ('buy','stage_buy'))
    realized_gain = sum(t.get('gl') or 0 for t in trades if t['action'] in ('sell','stage_sell') and (t.get('gl') or 0) > 0)
    harvest_offset = sum(-(t.get('gl') or 0) for t in trades if t['action'] == 'harvest' and (t.get('gl') or 0) < 0)
    net_taxable = max(0, realized_gain - harvest_offset)
    ongoing_alpha = {
        'taxManagedSMA': e['taxAlpha']*0.6,
        'qlhOverlay': e['taxAlpha']*0.7,
        'dtlhOverlay': e['taxAlpha']*0.9,
        'directIndexing': e['taxAlpha']*0.85,
        'temSms': e['taxAlpha']*0.7,
        'transition': 0,
        'mgiTer': e['taxAlpha']*0.5,
        'mgiQlh': e['taxAlpha']*0.55,
        'mgiDtlh': e['taxAlpha']*0.75,
        'dca': 0,  # DCA manages market-timing risk, not tax alpha -- no ongoing tax-alpha figure applies
    }.get(offering, 0)
    # Simulated post-allocation: unchanged for overlays; equity sleeve reshaped for SMA/DI
    post_alloc = dict(hh['current'])
    if offering in ('directIndexing','temSms','dtlhOverlay') and any(_is_single_stock(h) for h in hh['holdings']):
        # Concentration cleared but overall allocation preserved
        pass
    conc_after = [] if offering in ('directIndexing','temSms') else hh.get('concentration', [])
    notes = []
    if offering in ('directIndexing','temSms'):
        notes.append('Basis resets at trade date across the reallocated sleeve; wash-sale windows apply for 30 days on any replacement ETF held elsewhere.')
    if offering in ('qlhOverlay','taxManagedSMA','dtlhOverlay'):
        notes.append('Overlay is applied to the existing sleeve; harvested losses carry forward.')
    if offering == 'transition':
        budget = ACCOUNT_FACTS.get(hh['id'], {}).get('annual_transition_budget')
        by_year = {}
        for t in trades:
            if t['action'] == 'stage_sell':
                yr = int(t['reason'].split('Year ')[1].split(' ')[0]) if 'Year ' in t['reason'] else 1
                by_year[yr] = by_year.get(yr, 0) + (t.get('gl') or 0)
        years_breakdown = [{'year': y, 'gains_realized': round(g, 2)} for y, g in sorted(by_year.items())]
        if budget and budget > 0:
            notes.append(f'Paced against the client-elected Annual Transition Budget of ${budget:,.0f}/yr over {len(years_breakdown)} year(s); unsold lots stay in the current strategy as Transition Assets, charged the standard advisory fee (not the Program Fee) until transitioned.')
        else:
            notes.append('No Annual Transition Budget has been elected yet \u2014 set one with the client before enrolling; the figures shown assume a single-year illustrative sale.')
    if offering == 'dca':
        amt = ACCOUNT_FACTS.get(hh['id'], {}).get('dca_cash_amount')
        months = ACCOUNT_FACTS.get(hh['id'], {}).get('dca_schedule_months')
        schedule = [{'month': i, 'amount': t['value']} for i, t in enumerate(
            [x for x in trades if x['action'] == 'stage_buy'], start=1)]
        if amt and months:
            notes.append(f'${amt:,.0f} of DCA Cash deployed over {months} month(s) in {len(schedule)} {DCA_FREQ_LABEL.get((ACCOUNT_FACTS.get(hh["id"],{}).get("dca_frequency") or "MONTHLY").upper(),"monthly")} contributions (~${amt/max(1,len(schedule)):,.0f} each). '
                        f'Uninvested DCA Cash is charged the standard advisory Fee Rate; once invested, that portion moves to the Program Fee Rate.')
            notes.append('Must be funded within 60 days of the effective date and begin investing within 2 weeks of it, or the DCA Service is removed.')
            notes.append('TER applies automatically to the invested portion unless declined; QLH/DTLH may be elected too but can be less effective and produce tax-inefficient trades or wash sales during the DCA period.')
        else:
            notes.append('No DCA Cash amount or schedule length has been set yet \\u2014 the figures above are placeholders pending that election.')
    if net_taxable > 0:
        notes.append(f'Estimated net taxable event: ~${net_taxable:,.0f} of long-term gain (post-offset). Illustrative at {int(0.238*100)}% blended rate: ~${net_taxable*0.238:,.0f}.')
    return {
        'allocation_after': post_alloc,
        'concentration_after': conc_after,
        'realized_gain': realized_gain,
        'harvest_offset': harvest_offset,
        'net_taxable_gain': net_taxable,
        'estimated_ongoing_annual_tax_alpha': int(ongoing_alpha),
        'sells_total': sells, 'buys_total': buys,
        'notes': notes,
        **({'annual_transition_budget': ACCOUNT_FACTS.get(hh['id'], {}).get('annual_transition_budget'),
            'gains_realized_by_year': years_breakdown} if offering == 'transition' else {}),
        **({'dca_cash_amount': ACCOUNT_FACTS.get(hh['id'], {}).get('dca_cash_amount'),
            'dca_schedule_months': ACCOUNT_FACTS.get(hh['id'], {}).get('dca_schedule_months'),
            'dca_schedule': schedule,
            'dca_frequency': DCA_FREQ_LABEL.get((ACCOUNT_FACTS.get(hh['id'], {}).get('dca_frequency') or 'MONTHLY').upper(), 'monthly')} if offering == 'dca' else {}),
    }

def _procedural_steps(hh, offering):
    common_kyc = 'Confirm KYC and suitability profile is current (last review within 12 months).'
    steps_by_offering = {
        'privateBanking': [common_kyc,
            'Introduce client to the Private Banking relationship manager.',
            f'Set up deposit and cash-management relationship sized to the household\'s cash position (~${hh["aum"]*hh["current"].get("cash",0)/100:,.0f}).',
            'Complete Private Banking application and beneficiary designation.',
            'Coordinate initial funding: transfer or direct-deposit new payroll/distributions.',
        ],
        'trustEstate': [common_kyc,
            'Schedule intake with the Trust & Estate specialist.',
            'Review existing will, powers of attorney, and beneficiary designations.',
            'Model gift/estate scenarios against the household\'s AUM and family structure.',
            'Draft or update trust documents; coordinate with outside counsel where applicable.',
        ],
        'alternatives': [common_kyc,
            'Confirm accredited/qualified purchaser status and liquidity budget.',
            'Model the sleeve size against the household\'s target-alt allocation and target risk profile.',
            'Present specific offerings on the approved shelf; capture subscription paperwork.',
            'Coordinate custody and capital-call cash management.',
        ],
        'lending': [common_kyc,
            'Confirm pledgeable collateral and desired credit purpose.',
            'Underwrite a securities-based line sized to advance rates on eligible holdings.',
            'Complete pledge agreement; document intended draw schedule.',
            'Confirm interest-rate/margin covenants with the client in writing.',
        ],
        'insurance': [common_kyc,
            'Review protection gap: life, disability, LTC, umbrella liability.',
            'Underwrite proposed coverage; obtain quotes and medical/financial requirements.',
            'Compare against household\'s existing coverage and beneficiary structure.',
            'Bind policies and integrate premium funding into the cash-management plan.',
        ],
        'charitable': [common_kyc,
            'Confirm charitable intent and preferred vehicle (DAF, private foundation, CRT).',
            'Identify low-basis positions that are attractive for in-kind gifting (see harvestable-losses and gain lots).',
            'Draft gift acceptance / operating documents; coordinate custodian.',
            'Schedule initial funding and set annual grant cadence.',
        ],
        'iapEnrollment': [
            'Confirm the household has an established brokerage account (e.g. CMA) \u2014 required before any IA Program enrollment.',
            'Execute the IAP Client Agreement, having reviewed the accompanying Brochure and any applicable Manager Disclosure Documents.',
            'Select an Investment Strategy (Managed Strategy or Custom Managed Strategy) that meets the household\'s goals and minimums.',
            'Choose the Authority for the account: full Firm/Manager discretion, retained-strategy-selection with granted trading authority, or full client discretion.',
            'Complete the Account Election/Signature Page: proxy voting approach and trade confirmation frequency (defaults apply if not elected).',
            'Confirm the negotiated advisory Fee Rate with the household (max 1.75%) and any applicable Style Manager Rate; this will be reflected in the Program Report.',
        ],
    }
    return steps_by_offering.get(offering, [
        common_kyc,
        f'Confirm eligibility and required documents for {_label_for_offering(offering)}.',
        'Complete application, custody setup, and initial funding.',
    ])

def transition_scenario(household_id: str, offering: str):
    if offering not in RULE_STORE['offerings']:
        raise KeyError(f'Unknown offering: {offering}')
    hh = household_or_404(household_id); e = enrich(hh)
    label = _label_for_offering(offering)
    verdict = None
    try: verdict = offering_result(household_id, offering)
    except Exception: pass
    enrolled_map = {**hh.get('programs',{}), **hh.get('overlays',{})}
    is_enrolled = enrolled_map.get(offering) == 'enrolled'
    current = _current_state(hh, e)
    gaps = _gap_analysis(hh, e, offering, verdict)
    procedural = offering in PROCEDURAL_OFFERINGS or offering not in TRADE_MODELABLE
    result = {
        'household_id': household_id, 'offering': offering, 'offering_label': label,
        'kind': 'procedural' if procedural else 'trade_modelable',
        'currently_enrolled': is_enrolled,
        'eligibility_verdict': (verdict or {}).get('verdict', 'UNKNOWN'),
        'current_state': current,
        'gap_analysis': gaps,
    }
    if procedural:
        result['steps'] = _procedural_steps(hh, offering)
    else:
        trades = _propose_trades(hh, e, offering)
        result['proposed_trades'] = trades
        result['target_state'] = _target_state(hh, e, offering, trades)
    return result

# ---- Vehicle comparison workbench (ETF vs SMA vs Direct Indexing) ----
# This subsystem answers a different question than the transition workbench:
# not "how do we move existing assets into an offering" but "which vehicle
# should *new* incoming capital use, and what firm content can we hand the
# client to explain that choice." It reuses the same fail-closed, cite-your-
# source discipline as the eligibility engine, but content approval is a
# different domain than household-offering eligibility, so it is implemented
# here as plain, explicit checks rather than forced into the RULE_STORE's
# offering-eligibility schema.
BLENDED_TAX_RATE = 0.238
# Illustrative, not a published research figure: a typical range for how much
# of a newly-funded taxable SMA's assets get harvested as losses in the first
# year. Used only to give a breakeven number qualitative context.
ILLUSTRATIVE_FIRST_YEAR_HARVEST_RANGE = (0.015, 0.03)

def _fee_bps(product: dict) -> int | None:
    """Manager fee or expense ratio in bps; None when the source doesn't state
    one (catalog SMAs: the Style Manager Rate lives in each Strategy Profile)."""
    f = product['fees']
    return f['manager_bps'] if f.get('manager_bps') is not None else f.get('expense_ratio_bps')

def _content_flags(doc: dict) -> list[dict]:
    """Fail-closed checks on one content-catalog record. Mirrors the
    eligibility engine's discipline: an unset/unknown field elevates to a
    review flag, it is never silently treated as 'safe to use'."""
    flags = []
    audience = doc.get('audience')
    if audience is None:
        flags.append({'severity':'review','message':'Content audience is not set; cannot confirm this is client-safe.'})
    elif audience != 'CLIENT_APPROVED':
        flags.append({'severity':'advisor_only','message':f'Audience is {audience} \u2014 for advisor use only, not client-presentable.'})
    expires = doc.get('expires')
    if expires:
        from datetime import date
        try:
            if date.fromisoformat(expires) < date.today():
                flags.append({'severity':'expired','message':f'Approval expired {expires} \u2014 do not use until re-approved.'})
        except ValueError:
            flags.append({'severity':'review','message':'Expiry date could not be parsed.'})
    if not doc.get('compliance_ref'):
        flags.append({'severity':'review','message':'No compliance approval reference on file.'})
    return flags

def content_search(query: str, model_id: str | None = None, topics: list[str] | None = None, limit: int = 8) -> list[dict]:
    """Deterministic metadata-filter + keyword-overlap retrieval over the
    content catalog. This stands in for a real multimodal RAG pipeline
    (Voyage text embeddings for prose, ColPali page-level retrieval for
    chart/table-heavy pages) which this environment has no network access
    to call; the metadata-filter-first, audience-and-expiry-aware shape of
    this function is exactly what should wrap the real embedding call in
    a production deployment \u2014 only the scoring step (keyword overlap
    instead of vector similarity) is a placeholder."""
    q_terms = set(w.lower() for w in query.split() if len(w) > 2)
    hits = []
    for doc in CONTENT_CATALOG:
        if model_id and model_id not in doc.get('related_models', []):
            continue
        if topics and not (set(topics) & set(doc.get('topics', []))):
            continue
        haystacks = {**{'title': doc['title']}, **doc.get('page_snippets', {})}
        best_page, best_score, best_snippet = None, 0, None
        for page, text in haystacks.items():
            text_terms = set(w.lower().strip('.,()') for w in text.split())
            score = len(q_terms & text_terms)
            if score > best_score:
                best_page, best_score, best_snippet = page, score, text
        if best_score == 0 and not (model_id or topics):
            continue  # no signal at all and nothing else narrowed the set
        hits.append({
            'doc_id': doc['doc_id'], 'title': doc['title'], 'audience': doc.get('audience'),
            'page': best_page if best_page != 'title' else None,
            'snippet': best_snippet or doc['title'],
            'score': best_score,
            'flags': _content_flags(doc),
            'pdf_url': f"/static/content-pdfs/{doc['pdf_id']}.pdf" if doc.get('pdf_id') else None,
            'pages': doc.get('pages'),
            'client_safe': doc.get('audience') == 'CLIENT_APPROVED' and not any(f['severity'] in ('expired','review') for f in _content_flags(doc)),
        })
    hits.sort(key=lambda h: (-h['score'], h['doc_id']))
    return hits[:limit]

def breakeven_tax_alpha(amount: float, sma_bps: int, etf_bps: int) -> dict:
    premium_bps = max(0, sma_bps - etf_bps)
    premium_dollars = amount * premium_bps / 10000
    breakeven_harvest_dollars = premium_dollars / BLENDED_TAX_RATE if premium_dollars else 0
    breakeven_pct = breakeven_harvest_dollars / amount if amount else 0
    lo, hi = ILLUSTRATIVE_FIRST_YEAR_HARVEST_RANGE
    if breakeven_pct <= lo:
        assessment = 'Below the typical first-year harvesting range \u2014 the fee premium is likely easy to offset.'
    elif breakeven_pct <= hi:
        assessment = 'Within the typical first-year harvesting range \u2014 plausible but not guaranteed to fully offset the fee premium.'
    else:
        assessment = 'Above the typical first-year harvesting range \u2014 the fee premium may not be fully offset by harvesting alone in year one.'
    return {
        'fee_premium_bps': premium_bps,
        'fee_premium_annual_dollars': round(premium_dollars, 2),
        'breakeven_harvest_needed_annual_dollars': round(breakeven_harvest_dollars, 2),
        'breakeven_harvest_needed_pct_of_assets': round(breakeven_pct, 4),
        'illustrative_typical_first_year_harvest_range_pct': list(ILLUSTRATIVE_FIRST_YEAR_HARVEST_RANGE),
        'assessment': assessment,
    }

def _product_label(p: dict) -> str:
    return p.get('name') or p.get('ticker') or p['product_id']

def search_products(query: str = '', vehicle: str | None = None, limit: int = 10, sleeve: str | None = None,
                    min_minimum: float | None = None, max_minimum: float | None = None, max_fee_bps: float | None = None,
                    tlh_capable: bool | None = None, client_safe_only: bool = False) -> list[dict]:
    """Roster-wide product lookup shared by the autocomplete picker, the Product
    Shelf workspace, and the agent's search_products tool. Filters are applied
    first; an empty query then lists every matching product. Scoring: exact
    ticker > ticker prefix > name / manager / fund family > sleeve / benchmark /
    model label. Deterministic, so the same query always ranks the same way."""
    q = (query or '').strip().lower()
    veh = vehicle.upper() if vehicle else None
    words = [w for w in q.replace(',', ' ').split() if w]
    vehicle_words = {'sma': 'SMA', 'smas': 'SMA', 'etf': 'ETF', 'etfs': 'ETF', 'direct': 'DIRECT_INDEXING', 'indexing': 'DIRECT_INDEXING'}
    content_words = [w for w in words if w not in vehicle_words]
    if not veh and words and not content_words:
        # A bare vehicle word ("smas", "etfs") filters by vehicle. Inside a longer
        # query it is part of a name ("CIO Equity ETF Core", "... Direct Index SMA")
        # and is scored like any other word, never used to filter results out.
        veh = vehicle_words[words[0]]
    if content_words:
        content_words = words
    results = []
    for p in PRODUCT_SHELF:
        if veh and p['vehicle'] != veh: continue
        if sleeve and sleeve.lower() not in p['sleeve'].lower(): continue
        if min_minimum is not None and p['minimum'] < min_minimum: continue
        if max_minimum is not None and p['minimum'] > max_minimum: continue
        if max_fee_bps is not None and (_fee_bps(p) is None or _fee_bps(p) > max_fee_bps): continue
        if tlh_capable is not None and p['tlh_capable'] != tlh_capable: continue
        if client_safe_only and not p['client_presentable']: continue
        ticker = (p.get('ticker') or '').lower()
        name = _product_label(p).lower()
        manager = (p.get('manager') or '').lower()
        family = (p.get('fund_family') or '').lower()
        sleeve_l = p['sleeve'].lower(); bench = p['benchmark'].lower()
        model_label = MODELS_BY_ID[p['model_id']]['label'].lower() if p.get('model_id') in MODELS_BY_ID else ''
        score = 0 if content_words else 1
        for w in content_words:
            if ticker and w == ticker: score += 100
            elif ticker and ticker.startswith(w): score += 60
            elif w in name or w in manager or w in family: score += 30
            elif w in sleeve_l or w in bench or w in model_label: score += 15
        if score == 0:
            continue
        if len(content_words) > 1 and q in name:
            score += 50  # the advisor typed (part of) the exact product name
        results.append({
            'product_id': p['product_id'], 'name': _product_label(p), 'ticker': p.get('ticker'),
            'vehicle': p['vehicle'], 'sleeve': p['sleeve'], 'model_id': p.get('model_id'),
            'model_label': MODELS_BY_ID[p['model_id']]['label'] if p.get('model_id') in MODELS_BY_ID else None,
            'fee_bps': _fee_bps(p), 'minimum': p['minimum'], 'tlh_capable': p['tlh_capable'],
            'client_presentable': p['client_presentable'], 'score': score,
            'tem_overlays': p.get('tem_overlays'), 'asset_class': p.get('asset_class'),
            'premium_access': p.get('premium_access', False), 'source': p.get('source', 'Atlas illustrative shelf'),
        })
    results.sort(key=lambda r: (-r['score'], r['fee_bps'] if r['fee_bps'] is not None else 10**9, r['name']))
    return results[:limit]

def shelf_sleeves() -> list[str]:
    return sorted({p['sleeve'] for p in PRODUCT_SHELF if '(' not in p['sleeve']})

def _comparison_rows(products: list[dict], amount: float) -> dict:
    # The first SMA *with reported performance* sets the reference basis;
    # anything on a different basis/period is flagged. Catalog strategies carry
    # no performance (the catalog doesn't publish it), so they are flagged as
    # such rather than given a number.
    with_perf = [p for p in products if p.get('performance')]
    reference = next((p for p in with_perf if p['vehicle'] == 'SMA'), with_perf[0] if with_perf else None)
    ref_basis = reference['performance']['basis'] if reference else None
    ref_as_of = reference['performance']['as_of'] if reference else None
    sleeves = sorted({p['sleeve'] for p in products})
    rows = []
    for p in products:
        perf = p.get('performance')
        fee = _fee_bps(p)
        basis_mismatch = bool(perf and reference and (perf['basis'] != ref_basis or perf['as_of'] != ref_as_of))
        row = {
            'product_id': p['product_id'], 'name': _product_label(p), 'vehicle': p['vehicle'], 'sleeve': p['sleeve'],
            'ticker': p.get('ticker'), 'model_id': p.get('model_id'), 'fee_bps': fee,
            'annual_fee_dollars': round(amount * fee / 10000, 2) if fee is not None else None,
            'minimum': p['minimum'], 'meets_minimum': amount >= p['minimum'],
            'tlh_capable': p['tlh_capable'], 'customizable': p['customizable'],
            'tem_overlays': p.get('tem_overlays'), 'premium_access': p.get('premium_access', False),
            'performance': perf, 'performance_basis_matches_reference': not basis_mismatch,
            'client_presentable': p['client_presentable'], 'source': p.get('source', 'Atlas illustrative shelf'), 'flags': [],
        }
        if perf and perf.get('type') in ('BACKTEST', 'HYPOTHETICAL'):
            row['flags'].append({'code':'hypothetical','severity':'required','message':'Hypothetical/backtested performance \u2014 must not be shown to the client under any framing.'})
        if basis_mismatch:
            row['flags'].append({'code':'basis','severity':'review','message':f"Performance basis ({perf['basis']}, as of {perf['as_of']}) differs from the reference ({ref_basis}, as of {ref_as_of}); not a like-for-like comparison as shown."})
        if not perf:
            row['flags'].append({'code':'noperf','severity':'review','message':'No performance is published in the Strategy Catalog; see the Strategy Profile. Compare fees, minimums and overlay eligibility only.'})
        if fee is None:
            row['flags'].append({'code':'nofee','severity':'review','message':'The Style Manager Rate is set in the Strategy Profile and is not listed in the catalog.'})
        if p.get('premium_access'):
            row['flags'].append({'code':'pas','severity':'review','message':'Premium Access Strategy: dual contract with the PAS Manager; TEM Overlay Services and TET are not available.'})
        if not row['meets_minimum']:
            row['flags'].append({'code':'minimum','severity':'required','message':f"Amount (${amount:,.0f}) is below this implementation's ${p['minimum']:,.0f} minimum."})
        if len(sleeves) > 1:
            row['flags'].append({'code':'sleeves','severity':'review','message':f"Selection spans {len(sleeves)} different sleeves \u2014 fees are comparable, performance is not."})
        rows.append(row)
    # Breakeven: each client-presentable, tax-managed product with a known fee
    # against the lowest-fee ETF or ETF model in the selection.
    cheapest_etf = min((p for p in products if p['vehicle'] in ('ETF','ETF_MODEL') and p['client_presentable'] and _fee_bps(p) is not None),
                       key=_fee_bps, default=None)
    breakevens = []
    if cheapest_etf:
        for p in products:
            if (p is not cheapest_etf and p['tlh_capable'] and p['client_presentable'] and _fee_bps(p) is not None
                    and _fee_bps(p) > _fee_bps(cheapest_etf)):
                be = breakeven_tax_alpha(amount, _fee_bps(p), _fee_bps(cheapest_etf))
                breakevens.append({**be, 'product_id': p['product_id'], 'product_name': _product_label(p),
                                   'vs_product_id': cheapest_etf['product_id'], 'vs_product_name': _product_label(cheapest_etf)})
    primary = next((b for b in breakevens if PRODUCTS_BY_ID[b['product_id']]['vehicle'] == 'SMA'), breakevens[0] if breakevens else None)
    return {'rows': rows, 'reference_basis': ref_basis, 'reference_as_of': ref_as_of,
            'sleeves': sleeves, 'breakevens': breakevens, 'primary_breakeven': primary}

def shelf_compare(household_id: str, model_id: str | None = None, amount: float | None = None,
                  product_ids: list[str] | None = None) -> dict:
    """Compare either (a) every implementation of one research model, or (b)
    any advisor- or agent-selected set of shelf products from the full roster."""
    hh = household_or_404(household_id)
    if amount is None:
        ic = hh.get('incoming_capital')
        amount = ic['amount'] if ic else hh['aum']
    if product_ids:
        missing = [pid for pid in product_ids if pid not in PRODUCTS_BY_ID]
        if missing:
            raise KeyError(f"Unknown product(s): {', '.join(missing)}")
        products = [PRODUCTS_BY_ID[pid] for pid in dict.fromkeys(product_ids)]
        model_ids = {p.get('model_id') for p in products}
        if len(model_ids) == 1 and next(iter(model_ids)) in MODELS_BY_ID:
            model_id = next(iter(model_ids))
            full_set = set(MODELS_BY_ID[model_id]['implementations']) == {p['product_id'] for p in products}
            label = MODELS_BY_ID[model_id]['label'] + ('' if full_set else ' (custom selection)')
        else:
            model_id = None; label = 'Custom comparison'
    else:
        if not model_id:
            # Households with no research model on file start from the broad
            # core-equity model; the advisor can then reshape the selection.
            model_id = hh.get('current_model_id') or 'research_core'
        if model_id not in MODELS_BY_ID:
            raise KeyError(f'Unknown research model: {model_id}')
        products = [PRODUCTS_BY_ID[pid] for pid in MODELS_BY_ID[model_id]['implementations'] if pid in PRODUCTS_BY_ID]
        label = MODELS_BY_ID[model_id]['label']
    if not products:
        raise KeyError('No products to compare')
    body = _comparison_rows(products, amount)
    return {
        'household_id': household_id, 'model_id': model_id, 'model_label': label, 'amount': amount,
        'reference_basis': body['reference_basis'], 'reference_as_of': body['reference_as_of'],
        'sleeves': body['sleeves'], 'implementations': body['rows'],
        'breakevens': body['breakevens'], 'breakeven_tax_alpha': body['primary_breakeven'],
    }

def _switching_target(vehicles: set[str]) -> tuple[str, str]:
    """Which existing transition-workbench scenario best approximates moving
    already-invested SMA assets into the vehicles under consideration. This is
    an approximation, labeled as such in the response."""
    if 'DIRECT_INDEXING' in vehicles:
        return 'directIndexing', 'Modeled as a transition into Direct Indexing (a direct-indexing product is in the selection).'
    if vehicles == {'ETF'}:
        return 'dtlhOverlay', 'Modeled as an ETF-only conversion (single stocks sold into a broad-market ETF), the closest existing scenario to moving SMA assets into ETFs.'
    return 'directIndexing', 'Modeled as a transition into Direct Indexing, the closest existing full-sleeve replacement scenario.'

def build_vehicle_brief(household_id: str, model_id: str | None = None, amount: float | None = None,
                        product_ids: list[str] | None = None) -> dict:
    hh = household_or_404(household_id)
    comparison = shelf_compare(household_id, model_id, amount, product_ids)
    related = sorted({r['model_id'] for r in comparison['implementations'] if r.get('model_id')})
    label = comparison['model_label']
    query = f"{label} ETF SMA fees performance tax management"
    all_hits = []
    seen = set()
    for mid in (related or [None]):
        for h in content_search(query, model_id=mid, topics=['vehicle_comparison','performance','research_models','tax_management'], limit=12):
            if h['doc_id'] not in seen:
                seen.add(h['doc_id']); all_hits.append(h)
    all_hits.sort(key=lambda h: (-h['score'], h['doc_id']))
    client_content = [h for h in all_hits if h['client_safe']]
    advisor_content = [h for h in all_hits if not h['client_safe']]
    content_gap = len(client_content) == 0
    switching_cost = None; switching_basis = None
    if hh.get('current_implementation') == 'SMA':
        # Existing SMA assets moving elsewhere is a real transition, not a
        # new-money decision -- reuse the transition workbench directly.
        target, switching_basis = _switching_target({r['vehicle'] for r in comparison['implementations'] if r['vehicle'] != 'SMA'} or {'DIRECT_INDEXING'})
        try:
            switching_cost = transition_scenario(household_id, target)
        except Exception:
            switching_cost = None; switching_basis = None
    return {
        'household_id': household_id, 'model_id': comparison['model_id'],
        'incoming_capital': hh.get('incoming_capital'),
        'comparison': comparison,
        'client_content': client_content,
        'advisor_content': advisor_content,
        'content_gap': content_gap,
        'content_gap_message': (f"No client-approved content found for the {label} comparison. "
            f"Logging a content-gap ticket to content/marketing.") if content_gap else None,
        'switching_cost_note': ('Existing SMA assets are a separate decision from the incoming capital \u2014 '
            'see the linked transition scenario for the cost of moving assets already invested, if that is also being considered.') if switching_cost else None,
        'switching_cost_basis': switching_basis,
        'switching_cost': switching_cost,
    }
