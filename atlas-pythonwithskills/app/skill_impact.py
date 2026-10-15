"""Before/after snapshots of what an advisor sees, used to show what a team skill changes.

Each snapshot entry is keyed so the same thing can be compared with and without a skill:
    key -> {order, workspace, household_id, subject, what, value, open}
Only the workspaces the skill says it shapes are computed, so a preview stays quick.
"""
from __future__ import annotations
from . import skills
from .data import my_book, BY_ID, RULE_STORE
from .services import all_verdicts, conversion_map, generate_draft_local, nba, cross_sell

OUTCOME = {'HOLD': 'Held as-is', 'SELL': 'Sold on entry', 'EXCHANGE': 'Share-class exchange', 'MOVE_OUT': 'Stays in brokerage', 'REVIEW': 'Needs confirming'}
VERDICT = {'ELIGIBLE': 'Eligible', 'CONDITIONAL': 'Conditional', 'NEEDS_REVIEW': 'Needs review', 'INELIGIBLE': 'Ineligible'}
money = lambda n: f"${n:,.0f}"
pct = lambda x: f"{x * 100:.1f}%"


def snapshot(fa: str, workspaces: set[str], examples: list[str] | None = None) -> dict:
    out, n = {}, [0]

    def put(key, workspace, subject, what, value, hid=None, open_=None):
        n[0] += 1
        out[key] = {'order': n[0], 'workspace': workspace, 'household_id': hid, 'subject': subject, 'what': what, 'value': value, 'open': open_}

    book = my_book(fa)
    if workspaces & {'eligibility', 'transition', 'cross_sell', 'tax_desk'}:
        for hh in book:
            for off, r in all_verdicts(hh['id']).items():
                put(f"elig|{hh['id']}|{off}", 'eligibility', hh['name'], r['label'], VERDICT.get(r['verdict'], r['verdict']), hh['id'],
                    {'workspace': 'eligibility', 'household_id': hh['id']})
    if 'cross_sell' in workspaces:
        for i, r in enumerate(cross_sell(fa)[:8]):
            put(f"xsell|{i}", 'cross_sell', f"Opportunity #{i + 1}", 'Ranked opportunity', f"{BY_ID[r['household_id']]['name']}: {r['label']} ({money(r['estimated_value'])})")
    if 'conversion' in workspaces:
        for hh in book:
            m = conversion_map(hh['id'], fa)
            if not m['applicable']: continue
            S = {s['strategy']: s for s in m['strategies']}
            o = {'workspace': 'conversion', 'household_id': hh['id']}
            put(f"conv|{hh['id']}|rec", 'conversion', hh['name'], 'Strategy type Atlas suggests', S[m['recommended']]['label'], hh['id'], o)
            put(f"conv|{hh['id']}|rate", 'conversion', hh['name'], 'Tax rate on gains realized at entry', f"{m['tax_rate'] * 100:.2f}".rstrip('0').rstrip('.') + '%', hh['id'], o)
            for s in m['strategies']:
                put(f"conv|{hh['id']}|{s['strategy']}|kept", 'conversion', hh['name'], f"{s['short']}: comes over without a sale", money(s['hold_mv'] + s['exchange_mv']), hh['id'], o)
                put(f"conv|{hh['id']}|{s['strategy']}|tax", 'conversion', hh['name'], f"{s['short']}: estimated entry tax", money(s['est_tax']), hh['id'], o)
            for k, c in m['cells'].items():
                sym, st = k.split('|')
                put(f"conv|{hh['id']}|cell|{k}", 'conversion', hh['name'], f"{sym} under {S[st]['short']}", OUTCOME.get(c['outcome'], c['outcome']), hh['id'], o)
                for note in c['notes']:
                    put(f"conv|{hh['id']}|cellnote|{k}|{note['rule_id']}", 'conversion', hh['name'], f"{sym} under {S[st]['short']}: note", note['message'][:90] + ('…' if len(note['message']) > 90 else ''), hh['id'], o)
            for note in m['notes']:
                put(f"conv|{hh['id']}|note|{note['rule_id']}", 'conversion', hh['name'], 'Program note shown', note['message'][:90] + ('…' if len(note['message']) > 90 else ''), hh['id'], o)
    if workspaces & {'tem', 'tax_desk'}:
        from .tem import tem_personalization, book_harvest
        for hh in book:
            try: t = tem_personalization(hh['id'])
            except Exception: continue
            if not t.get('applicable') or t.get('blocked'): continue
            o = {'workspace': 'tem', 'household_id': hh['id']}
            q = t['qlh']
            put(f"tem|{hh['id']}|qlh_n", 'tem', hh['name'], 'QLH lots harvested at the next run', f"{q['harvest_count']} lots ({money(q['harvest_loss'])})", hh['id'], {**o, 'offering_id': 'qlhOverlay'})
            put(f"tem|{hh['id']}|qlh_thr", 'tem', hh['name'], 'QLH loss threshold', f"{q['threshold'] * 100:g}%", hh['id'], {**o, 'offering_id': 'qlhOverlay'})
            for c in t['considerations']:
                put(f"tem|{hh['id']}|cons|{c['rule_id']}|{c['message'][:20]}", 'tem', hh['name'], 'Worth raising', c['message'][:110] + ('…' if len(c['message']) > 110 else ''), hh['id'], o)
            put(f"tem|{hh['id']}|sms", 'tem', hh['name'], 'TEM Style Manager shortlist', ', '.join(x['name'] for x in t['tem_sms_options']) or 'none', hh['id'], {**o, 'offering_id': 'temSms'})
            for p in t['paths']:
                put(f"tem|{hh['id']}|path|{p['id']}", 'tem', hh['name'], f"Option: {p['label']}", p['status'].replace('_', ' ').lower(), hh['id'], {**o, 'offering_id': 'temSms'})
        if 'tax_desk' in workspaces:
            for r in book_harvest(fa):
                put(f"desk|{r['household_id']}", 'tax_desk', r['name'], 'Losses at or past the QLH threshold', money(r['at_threshold']), r['household_id'], {'workspace': 'tax_desk'})
    if 'cio_fit' in workspaces:
        from .cio import fit_book
        accts = fit_book(fa)['accounts']
        for rank, a in enumerate(accts, 1):
            hid = a['household_id']; o = {'workspace': 'cio_fit', 'household_id': hid}
            put(f"cio|{hid}|model", 'cio_fit', a['name'], 'CIO model', a['model']['label'], hid, o)
            put(f"cio|{hid}|er", 'cio_fit', a['name'], 'Expected return: holdings / model', f"{pct(a['current']['expected_return'])} / {pct(a['model_stats']['expected_return'])}", hid, o)
            put(f"cio|{hid}|sharpe", 'cio_fit', a['name'], 'Sharpe: holdings / model', f"{a['current']['sharpe']:.2f} / {a['model_stats']['sharpe']:.2f}", hid, o)
            put(f"cio|{hid}|rank", 'cio_fit', a['name'], 'Position in the list (widest Sharpe gap first)', f"#{rank}", hid, o)
            put(f"cio|{hid}|flags", 'cio_fit', a['name'], 'Flags', ', '.join(f['id'].replace('_', ' ') for f in a['flags']) or 'none', hid, o)
    if 'meeting_prep_draft' in workspaces:
        for hh in nba('meetings', fa)[:3]:
            d = generate_draft_local(hh['id'], 'meeting_prep')
            heads = [l[4:] for l in d.splitlines() if l.startswith('### ')]
            put(f"draft|{hh['id']}", 'meeting_prep_draft', hh['name'], 'Sections in the meeting prep draft', ' · '.join(heads), hh['id'],
                {'workspace': 'meeting_prep_draft', 'household_id': hh['id']})
    if 'ask_atlas' in workspaces and examples:
        from .agent import run_local
        for ex in examples:
            r = run_local(fa, ex, None)
            opened = next((a for a in r['actions'] if a.get('auto_open')), None) or (r['actions'][0] if r['actions'] else None)
            ws = skills.WORKSPACE_LABELS.get(opened['workspace'], opened['workspace'].replace('_', ' ')) if opened else 'answers in chat only'
            put(f"ask|{ex}", 'ask_atlas', f"“{ex}”", 'Where Ask Atlas takes the advisor', ws, None, {'workspace': 'ask', 'q': ex})
    return out


def skill_impact(sid: str, fa: str) -> dict:
    s = skills.CATALOG[sid]
    ws = set(s['workspaces'])
    examples = [e for r in s['routes'] for e in r.get('examples', [])]
    res = skills.impact(sid, lambda: snapshot(fa, ws, examples))
    res['fa'] = fa
    return res
