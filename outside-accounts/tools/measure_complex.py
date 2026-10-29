"""Score extraction on the long statements (samples/truth_complex.json).  Run: python tools/measure_complex.py [--json]"""
from __future__ import annotations
import difflib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.extract.core import extract  # noqa: E402


def close(a, b, tol=0.011):
    return a is not None and b is not None and abs(a - b) <= max(tol, abs(b) * 1e-6)


def find(t, got, used):
    if t['sym']:
        for g in got:
            if id(g) not in used and g['sym'] == t['sym']:
                return g
    best, score = None, 0
    for g in got:
        if id(g) in used:
            continue
        s = difflib.SequenceMatcher(None, t['desc'].lower(), (g['desc'] or '').lower()[:len(t['desc']) + 5]).ratio()
        if s > score:
            best, score = g, s
    return best if score > 0.75 else None


def chart_score(truth, got, tol):
    if not truth:
        return None
    hits, errs = 0, []
    for t in truth:
        g = next((x for x in got if x['label'].lower() == t['label'].lower()), None)
        if g:
            errs.append(abs(g['pct'] - t['pct']))
            hits += abs(g['pct'] - t['pct']) <= tol
    return {'labels_found': f"{sum(1 for t in truth if any(x['label'].lower() == t['label'].lower() for x in got))}/{len(truth)}",
            'within_tol': f'{hits}/{len(truth)}', 'max_err': round(max(errs), 2) if errs else None}


def run():
    truth = json.loads((ROOT / 'samples' / 'truth_complex.json').read_text())
    out = {}
    for f, t in truth.items():
        t0 = time.time()
        d = extract(ROOT / 'samples' / f)
        secs = time.time() - t0
        used, right, fields, misses = set(), 0, 0, []
        for th in t['holdings']:
            g = find(th, d['holdings'], used)
            if g:
                used.add(id(g))
            for k in ('sym', 'qty', 'price', 'value', 'cost'):
                fields += 1
                ok = g is not None and (g[k] == th[k] if k == 'sym' else close(g[k], th[k]))
                right += ok
                if not ok:
                    misses.append(f"{th['sym'] or th['desc'][:28]} {k}: truth {th[k]} got {g and g[k]}")
        extra = [h['desc'] for h in d['holdings'] if id(h) not in used]
        charts = d.get('charts', [])
        pie = next((c['values'] for c in charts if c.get('type') == 'pie'), d['allocation'] if not charts else [])
        bar = next((c['values'] for c in charts if c.get('type') == 'bar'), [])
        pmap = d.get('page_map') or []
        from app.engine import outside_positions, HH
        d2 = dict(d); d2['id'] = 'X'
        pos = outside_positions([d2], HH[t['household']])
        sym_after = sum(1 for th in t['holdings'] if th['sym'] and any(p['sym'] == th['sym'] for p in pos))
        out[f] = {'symbols_after_validation': f"{sym_after}/{sum(1 for th in t['holdings'] if th['sym'])}", 'seconds': round(secs, 1), 'holdings_found': f"{len(used)}/{len(t['holdings'])}", 'extra_rows': len(extra), 'extra_examples': extra[:6],
                  'fields': f'{right}/{fields}', 'total': {'truth': t['total'], 'stated': d['stated_total'], 'extracted': d['extracted_total'],
                                                        'reconciles': bool(d['reconciliation'] and d['reconciliation']['ok'])},
                  'owner': d['owner'], 'as_of': d['as_of'], 'pie': chart_score(t['pie'], pie, 1.0), 'bar': chart_score(t['bar'], bar, 1.0),
                  'page_types_right': (f"{sum(1 for a, b in zip(t['page_types'], [p['type'] for p in pmap]) if a == b)}/{len(t['page_types'])}" if pmap else 'no page map'),
                  'misses': misses[:8], 'warnings': d['warnings'][:6]}
    return out


if __name__ == '__main__':
    print(json.dumps(run(), indent=1))
