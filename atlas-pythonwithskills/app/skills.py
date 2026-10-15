"""Team skills: packaged policy and instructions that business and product teams own.

A skill is a folder under skills/ (next to app/, outside the code):

    skills/<skill-id>/SKILL.md      who owns it, what it changes and why, in plain English,
                                    plus optional "## Instructions for Atlas" for the AI
    skills/<skill-id>/policy.json   optional machine part: data patches, draft sections, routes

Turning a skill on applies its patches to the live policy data (rule store, CIO models,
config) in place, so every workspace that reads that data changes with no code change.
Turning it off restores the original data exactly. Order of application is the catalog
order (folder name), so two skills touching the same value resolve predictably.
Nothing here imports the rest of the app: data modules register themselves.
"""
from __future__ import annotations
import json, os, re, threading
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

SKILLS_DIR = Path(os.getenv('ATLAS_SKILLS_DIR') or Path(__file__).resolve().parent.parent / 'skills')

TARGETS: dict[str, Any] = {}          # name -> live data object (mutated in place)
BASE: dict[str, Any] = {}             # name -> pristine copy taken at registration
HOOKS: list[Callable[[], None]] = []  # recompute module-level values derived from the data
LOCK = threading.RLock()
_ACTIVE: list[str] = []
_TOUCHED: dict[str, list[str]] = {}   # target -> active skill ids that patched it
_PATHS: list[tuple[str, str, str]] = []  # (target, path, skill id) for every value a skill set

WORKSPACE_LABELS = {
    'eligibility': 'Eligibility', 'transition': 'Transition', 'conversion': 'Conversion map', 'tem': 'Tax personalization',
    'tax_desk': 'Tax Overlay Desk', 'cio_fit': 'CIO Model Fit', 'meeting_prep_draft': 'Meeting prep draft',
    'ask_atlas': 'Ask Atlas', 'cross_sell': 'Cross-sell', 'today': 'Today',
    'client': 'Client page (general answer)', 'guide': 'Atlas guide', 'skills': 'Team skills',
}


# ---------------------------------------------------------------- reading skills
def _parse_value(v: str):
    v = v.strip()
    if v.startswith('[') and v.endswith(']'):
        return [x.strip().strip('"\'') for x in v[1:-1].split(',') if x.strip()]
    if v.lower() in ('true', 'false'): return v.lower() == 'true'
    return v.strip('"\'')


def parse_skill_md(text: str) -> tuple[dict, dict, str]:
    """-> (frontmatter, sections by '## ' heading, body). Frontmatter is simple 'key: value' lines."""
    meta, body = {}, text
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)$', text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ':' in line and not line.lstrip().startswith('#'):
                k, v = line.split(':', 1); meta[k.strip()] = _parse_value(v)
        body = m.group(2)
    sections, cur = {}, None
    for line in body.splitlines():
        h = re.match(r'^##\s+(.+?)\s*$', line)
        if h: cur = h.group(1).strip(); sections[cur] = []; continue
        if cur: sections[cur].append(line)
    return meta, {k: '\n'.join(v).strip() for k, v in sections.items()}, body.strip()


def load_catalog(folder: Path | None = None) -> dict[str, dict]:
    folder = folder or SKILLS_DIR
    out = {}
    if not folder.is_dir(): return out
    for d in sorted(p for p in folder.iterdir() if p.is_dir() and (p / 'SKILL.md').exists()):
        meta, sections, body = parse_skill_md((d / 'SKILL.md').read_text(encoding='utf-8'))
        pol = json.loads((d / 'policy.json').read_text(encoding='utf-8')) if (d / 'policy.json').exists() else {}
        sid = meta.get('id') or d.name
        ws = meta.get('workspaces') or []
        out[sid] = {
            'id': sid, 'folder': d.name, 'title': meta.get('title', sid), 'team': meta.get('team', ''), 'owner': meta.get('owner', ''),
            'version': str(meta.get('version', '1.0')), 'kind': meta.get('kind', 'policy'),
            'workspaces': ws if isinstance(ws, list) else [ws], 'summary': meta.get('summary', ''),
            'status': meta.get('status', 'Illustrative'), 'default': bool(meta.get('enabled_by_default', False)),
            'prompts': meta.get('prompts') or [], 'sections': sections, 'markdown': body,
            'instructions': sections.get('Instructions for Atlas', ''),
            'patches': pol.get('patches', []), 'draft': pol.get('draft'), 'routes': pol.get('routes', []),
            'try': pol.get('try', []),
        }
    return out


CATALOG: dict[str, dict] = load_catalog()


def reload_catalog():
    global CATALOG
    with LOCK:
        CATALOG = load_catalog()
        keep = [s for s in _ACTIVE if s in CATALOG]
        _apply(keep)


# ---------------------------------------------------------------- data targets
def register_target(name: str, obj: Any):
    """Called by data modules at import. The pristine copy is what 'off' restores to."""
    TARGETS[name] = obj; BASE[name] = deepcopy(obj)


def on_change(fn: Callable[[], None]):
    HOOKS.append(fn); return fn


def _restore(t: Any, b: Any):
    """Make t equal to b without replacing t (or its nested dicts), so references held elsewhere stay valid."""
    if isinstance(t, dict) and isinstance(b, dict):
        for k in [k for k in t if k not in b]: del t[k]
        for k, v in b.items():
            if k in t and isinstance(t[k], (dict, list)) and type(t[k]) is type(v) and (not isinstance(v, list) or len(v) == len(t[k])):
                _restore(t[k], v)
            else:
                t[k] = deepcopy(v)
    elif isinstance(t, list) and isinstance(b, list):
        if len(t) != len(b): t[:] = deepcopy(b); return
        for i, v in enumerate(b):
            if isinstance(t[i], (dict, list)) and type(t[i]) is type(v) and (not isinstance(v, list) or len(v) == len(t[i])): _restore(t[i], v)
            else: t[i] = deepcopy(v)


_SEG = re.compile(r'\[([^=\]]+)=([^\]]+)\]|\[(\d+)\]|([^.\[\]]+)')


def _segments(path: str) -> list:
    out = []
    for m in _SEG.finditer(path):
        if m.group(1): out.append(('match', m.group(1), m.group(2)))
        elif m.group(3): out.append(('index', int(m.group(3))))
        else: out.append(('key', m.group(4)))
    return out


def _step(cur, seg, path):
    if seg[0] == 'key':
        if not isinstance(cur, dict) or seg[1] not in cur: raise KeyError(f"'{seg[1]}' not found in {path}")
        return cur[seg[1]]
    if seg[0] == 'index': return cur[seg[1]]
    hit = [x for x in cur if isinstance(x, dict) and str(x.get(seg[1])) == seg[2]]
    if len(hit) != 1: raise KeyError(f"{seg[1]}={seg[2]} matched {len(hit)} items in {path}")
    return hit[0]


def _stamp(item, sid):
    if isinstance(item, dict):
        item['skills'] = list(dict.fromkeys((item.get('skills') or []) + [sid]))


def apply_patch(root: Any, patch: dict, sid: str):
    """Ops: set (value at path), merge (dict update), append (to list; at: start), remove (matched item)."""
    op, path = patch['op'], patch['path']
    segs = _segments(path)
    parents, cur = [], root
    for seg in segs[:-1]:
        cur = _step(cur, seg, path); parents.append(cur)
    last = segs[-1]
    matched = [p for p, s in zip(parents, segs[:-1]) if s[0] == 'match']
    if op == 'set':
        if last[0] == 'key':
            if not isinstance(cur, dict): raise KeyError(f'cannot set {path}')
            cur[last[1]] = deepcopy(patch['value'])
        elif last[0] == 'index': cur[last[1]] = deepcopy(patch['value'])
        else: raise KeyError(f'set needs a key at the end of {path}')
    else:
        tgt = _step(cur, last, path)
        if last[0] == 'match': matched.append(tgt)
        if op == 'merge':
            if not isinstance(tgt, dict): raise KeyError(f'merge needs an object at {path}')
            tgt.update(deepcopy(patch['value']))
        elif op == 'append':
            if not isinstance(tgt, list): raise KeyError(f'append needs a list at {path}')
            items = patch['value'] if patch.get('many') else [patch['value']]
            for it in reversed(items) if patch.get('at') == 'start' else items:
                it = deepcopy(it); _stamp(it, sid)
                tgt.insert(0, it) if patch.get('at') == 'start' else tgt.append(it)
        elif op == 'remove':
            if last[0] != 'match': raise KeyError(f'remove needs a [key=value] selector in {path}')
            cur.remove(tgt); matched.remove(tgt)
        else:
            raise ValueError(f'unknown op {op}')
    for m in matched: _stamp(m, sid)


def _apply(active: list[str]):
    for name, obj in TARGETS.items(): _restore(obj, BASE[name])
    _TOUCHED.clear(); _PATHS.clear()
    errors = {}
    for sid in [s for s in CATALOG if s in active]:
        for p in CATALOG[sid]['patches']:
            tgt = p.get('target', 'rules')
            try:
                apply_patch(TARGETS[tgt], p, sid)
                keys = list(p['value']) if p['op'] == 'merge' and isinstance(p.get('value'), dict) else [None]
                _PATHS.extend((tgt, p['path'] + (f'.{k}' if k else ''), sid) for k in keys)
                _TOUCHED.setdefault(tgt, [])
                if sid not in _TOUCHED[tgt]: _TOUCHED[tgt].append(sid)
            except Exception as e:     # a bad patch never breaks the app: it is reported on the skill
                errors.setdefault(sid, []).append(f"{p.get('op')} {p.get('path')}: {e}")
    _ACTIVE[:] = [s for s in CATALOG if s in active]
    if 'rules' in TARGETS: TARGETS['rules']['active_skills'] = list(_TOUCHED.get('rules', []))
    for fn in HOOKS: fn()
    global ERRORS
    ERRORS = errors
    return errors


ERRORS: dict[str, list[str]] = {}


def init():
    with LOCK: _apply([s for s, k in CATALOG.items() if k['default']])


def set_active(ids: list[str]) -> dict:
    unknown = [s for s in ids if s not in CATALOG]
    if unknown: raise KeyError(', '.join(unknown))
    with LOCK: return _apply(list(dict.fromkeys(ids)))


def active() -> list[str]: return list(_ACTIVE)
def is_on(sid: str) -> bool: return sid in _ACTIVE


# ---------------------------------------------------------------- what the app asks of skills
def info(sid: str) -> dict:
    s = CATALOG[sid]
    return {'id': sid, 'title': s['title'], 'team': s['team'], 'version': s['version']}


def for_workspace(ws: str) -> list[dict]:
    return [info(s) for s in _ACTIVE if ws in CATALOG[s]['workspaces']]


def touched(target: str, prefix: str) -> list[dict]:
    """Active skills that set any value at or under this path (e.g. 'conversion_policy.tax_rate')."""
    ids = [sid for t, path, sid in _PATHS if t == target and (path == prefix or path.startswith(prefix + '.') or path.startswith(prefix + '['))]
    return [info(s) for s in dict.fromkeys(ids)]


def provenance(item: dict | None) -> list[dict]:
    """Skills that added or changed a rule / note, for display next to it."""
    return [info(s) for s in (item or {}).get('skills') or [] if s in CATALOG]


def instructions(scope: str) -> str:
    """Plain-English 'Instructions for Atlas' of active skills that apply to a prompt ('chat' or 'draft')."""
    parts = [f"[{CATALOG[s]['title']}, {CATALOG[s]['team']}]\n{CATALOG[s]['instructions']}"
             for s in _ACTIVE if CATALOG[s]['instructions'] and scope in CATALOG[s]['prompts']]
    return ('\n\nTeam skills in effect (follow these; they come from the teams that own the policy):\n' + '\n\n'.join(parts)) if parts else ''


def draft_additions(kind: str) -> list[tuple[str, dict]]:
    return [(s, CATALOG[s]['draft']) for s in _ACTIVE if CATALOG[s].get('draft') and CATALOG[s]['draft'].get('kind', 'meeting_prep') == kind]


def route(text: str) -> tuple[str | None, str | None]:
    """-> (workspace, skill id) when an active skill's phrasing matches the request."""
    for s in _ACTIVE:
        for r in CATALOG[s]['routes']:
            if any(re.search(p, text, re.I) for p in r['patterns']): return r['workspace'], s
    return None, None


def routing_hints() -> str:
    lines = [f"- Requests like {', '.join(repr(e) for e in r.get('examples', [])[:3])} mean the '{r['workspace']}' workspace ({CATALOG[s]['title']})."
             for s in _ACTIVE for r in CATALOG[s]['routes']]
    return ('\nRouting added by team skills:\n' + '\n'.join(lines)) if lines else ''


def public(sid: str) -> dict:
    s = CATALOG[sid]
    return {k: s[k] for k in ('id', 'title', 'team', 'owner', 'version', 'kind', 'workspaces', 'summary', 'status', 'markdown', 'try')} | {
        'enabled': sid in _ACTIVE, 'default': s['default'], 'workspace_labels': [WORKSPACE_LABELS.get(w, w) for w in s['workspaces']],
        'changes': len(s['patches']) + (len(s['draft'].get('sections', [])) + len(s['draft'].get('rules', [])) if s.get('draft') else 0) + sum(len(r['patterns']) for r in s['routes']),
        'has_instructions': bool(s['instructions']), 'errors': ERRORS.get(sid, []),
        'patches': [{k: p.get(k) for k in ('target', 'op', 'path', 'why')} for p in s['patches']]}


def catalog() -> list[dict]:
    return [public(s) for s in CATALOG]


def impact(sid: str, snapshot: Callable[[], dict]) -> dict:
    """What the skill changes, measured by running the app without it and with it (other active skills stay as they are)."""
    with LOCK:
        current = list(_ACTIVE)
        without = [x for x in current if x != sid]
        with_ = current if sid in current else current + [sid]
        try:
            _apply(without); a = snapshot()
            _apply(with_); b = snapshot()
        finally:
            _apply(current)
    rows = []
    for key in sorted(set(a) | set(b), key=lambda k: (a.get(k) or b.get(k))['order']):
        x, y = a.get(key), b.get(key)
        bv, av = (x or {}).get('value'), (y or {}).get('value')
        if bv != av:
            m = x or y
            rows.append({'workspace': m['workspace'], 'household_id': m.get('household_id'), 'subject': m['subject'],
                         'what': m['what'], 'before': bv if bv is not None else '—', 'after': av if av is not None else '—', 'open': m.get('open')})
    return {'skill': sid, 'enabled': sid in current, 'changes': rows,
            'by_workspace': {w: sum(1 for r in rows if r['workspace'] == w) for w in dict.fromkeys(r['workspace'] for r in rows)}}
