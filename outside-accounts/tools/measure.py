"""Measure extraction accuracy against samples/truth.json.  Run: python tools/measure.py [--json]"""
from __future__ import annotations
import difflib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.extract.core import extract  # noqa: E402


def close(a, b, tol=0.011):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= max(tol, abs(b) * 1e-6)


def match(truth_h, got):
    if truth_h.get('sym'):
        for g in got:
            if g['sym'] == truth_h['sym']:
                return g
    best, score = None, 0
    for g in got:
        s = difflib.SequenceMatcher(None, (truth_h['desc'] or '').lower(), (g['desc'] or '').lower()).ratio()
        if s > score:
            best, score = g, s
    return best if score > 0.6 else None


def measure():
    truth = json.loads((ROOT / 'samples' / 'truth.json').read_text())
    report, tot = [], {'fields': 0, 'right': 0, 'holdings': 0, 'found': 0, 'extra': 0}
    for f, t in truth.items():
        d = extract(ROOT / 'samples' / f)
        rows, right, fields = [], 0, 0
        used = set()
        for th in t['holdings']:
            g = match(th, [x for x in d['holdings'] if id(x) not in used])
            if g:
                used.add(id(g))
            for k in ('sym', 'qty', 'price', 'value', 'cost'):
                if th.get(k) is None and k != 'sym':
                    continue
                fields += 1
                ok = g is not None and (g[k] == th[k] if k == 'sym' else close(g[k], th[k]))
                right += ok
                if not ok:
                    rows.append(f"  {th.get('sym') or th['desc'][:30]:32s} {k:6s} truth={th.get(k)} got={g and g[k]}")
        meta_ok = {'owner': (d['owner'] or '').lower() == (t['owner'] or '').lower(), 'account': d['account'] == t['account'],
                   'as_of': d['as_of'] == t['as_of'], 'total': close(d['stated_total'], t['total'])}
        for k, ok in meta_ok.items():
            fields += 1; right += ok
            if not ok:
                rows.append(f"  meta {k:10s} truth={t[k if k != 'total' else 'total']} got={d[k if k != 'total' else 'stated_total']}")
        if t['allocation']:
            fields += 1
            ok = len(d['allocation']) == len(t['allocation']) and all(close(a['pct'], b['pct'], 0.051) for a, b in zip(d['allocation'], t['allocation']))
            right += ok
            if not ok:
                rows.append(f"  allocation truth={[(a['label'], a['pct']) for a in t['allocation']]} got={[(a['label'], a['pct']) for a in d['allocation']]}")
        found = len(used)
        extra = len(d['holdings']) - found
        tot['fields'] += fields; tot['right'] += right; tot['holdings'] += len(t['holdings']); tot['found'] += found; tot['extra'] += extra
        rec = d['reconciliation']
        report.append({'file': f, 'kind': d['kind'], 'holdings': f"{found}/{len(t['holdings'])}", 'extra': extra, 'fields': f'{right}/{fields}',
                       'reconciles': bool(rec and rec['ok']), 'review': d['needs_review'], 'warnings': d['warnings'], 'misses': rows})
    return report, tot


if __name__ == '__main__':
    report, tot = measure()
    if '--json' in sys.argv:
        print(json.dumps({'report': report, 'total': tot}, indent=1)); sys.exit()
    for r in report:
        print(f"{r['file']:40s} {r['kind']:9s} holdings {r['holdings']:5s} extra {r['extra']}  fields {r['fields']:7s} reconciles {r['reconciles']!s:5s} review {r['review']}")
        for m in r['misses']:
            print(m)
        for w in r['warnings']:
            print('  warning:', w)
    print(f"\nHoldings found {tot['found']}/{tot['holdings']}, extra rows {tot['extra']}, fields correct {tot['right']}/{tot['fields']} "
          f"({tot['right'] / tot['fields'] * 100:.1f}%)")
