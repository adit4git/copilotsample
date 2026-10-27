"""The skill registry: a folder of skill folders, each holding SKILL.md.

It resolves inheritance (`extends`), builds the dependency graph (`uses`), answers
"what depends on this?" for impact analysis, and saves new versions while keeping history.
"""
from __future__ import annotations
import copy
import json
import os
import re
import shutil
from pathlib import Path
from .skillfile import Skill, SkillFileError, parse

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / 'seed'
DATA = Path(__file__).resolve().parent / 'data'
_PARAM = re.compile(r'^\{params\.(\w+)\}$')


def load_json(name: str):
    return json.loads((DATA / name).read_text())


class CycleError(ValueError):
    pass


def _merge_list(parent: list, child: list, src: str) -> list:
    out = [dict(x) for x in parent]
    idx = {x.get('id'): i for i, x in enumerate(out) if isinstance(x, dict) and x.get('id')}
    for item in child or []:
        if not isinstance(item, dict):
            continue
        it = dict(item)
        it.setdefault('from', src)
        if it.get('id') in idx:
            i = idx[it['id']]
            if it.get('disable'):
                out[i] = {**out[i], 'disabled': True, 'disabled_by': src}
            else:
                out[i] = {**out[i], **it, 'overrides': out[i].get('from'), 'from': src}
        else:
            out.append(it)
            idx[it.get('id')] = len(out) - 1
    return out


def merge_logic(parent: dict, child: dict, src: str) -> dict:
    out = copy.deepcopy(parent)
    out.pop('abstract', None)
    for k, v in (child or {}).items():
        if k in ('rules', 'constraints'):
            out[k] = _merge_list(out.get(k) or [], v or [], src)
        elif k in ('params', 'compose') and isinstance(v, dict):
            out[k] = {**(out.get(k) or {}), **copy.deepcopy(v)}
        elif k == 'op' and isinstance(v, dict) and isinstance(out.get('op'), dict):
            merged = {**out['op'], **copy.deepcopy(v)}
            merged['params'] = {**(out['op'].get('params') or {}), **(v.get('params') or {})}
            out['op'] = merged
        else:
            out[k] = copy.deepcopy(v)
    for k in ('rules', 'constraints'):
        for it in out.get(k) or []:
            if isinstance(it, dict):
                it.setdefault('from', src)
    return out


def subst(value: str, params: dict) -> str:
    m = _PARAM.match(str(value))
    return str(params.get(m.group(1), value)) if m else str(value)


class Registry:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or os.environ.get('SKILL_REGISTRY') or (ROOT / 'registry'))
        if not self.path.exists() or not any(self.path.glob('*/SKILL.md')):
            self.reset()
        self.reload()

    # ---------- files ----------
    def reset(self) -> None:
        if self.path.exists():
            shutil.rmtree(self.path)
        shutil.copytree(SEED, self.path)

    def reload(self) -> None:
        self.skills: dict[str, Skill] = {}
        self.load_errors: dict[str, str] = {}
        for f in sorted(self.path.glob('*/SKILL.md')):
            try:
                s = parse(f.read_text())
                self.skills[s.name or f.parent.name] = s
            except SkillFileError as e:
                self.load_errors[f.parent.name] = str(e)

    def get(self, name: str) -> Skill | None:
        return self.skills.get(name)

    def history(self, name: str) -> list[dict]:
        d = self.path / name / 'history'
        if not d.exists():
            return []
        out = []
        for f in sorted(d.glob('*.md'), key=lambda p: [int(x) if x.isdigit() else x for x in re.split(r'[.\-]', p.stem)]):
            try:
                s = parse(f.read_text())
                out.append({'version': s.version, 'status': s.status, 'file': f'history/{f.name}'})
            except SkillFileError:
                out.append({'version': f.stem, 'status': 'unreadable', 'file': f'history/{f.name}'})
        return out

    def save(self, text: str) -> Skill:
        """Save SKILL.md text. An existing skill keeps its previous version in history/ and gets a version bump."""
        s = parse(text)
        folder = self.path / s.name
        old = self.skills.get(s.name)
        if old is not None:
            (folder / 'history').mkdir(parents=True, exist_ok=True)
            (folder / 'history' / f'{old.version}.md').write_text(old.raw)
            if _vkey(s.version) <= _vkey(old.version):
                s = parse(_set_meta(text, version=_bump(old.version), status='draft'))
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'SKILL.md').write_text(s.raw)
        self.reload()
        return self.skills[s.name]

    def set_status(self, name: str, status: str) -> Skill:
        s = self.skills[name]
        text = _set_meta(s.raw, status=status)
        (self.path / name / 'SKILL.md').write_text(text)
        self.reload()
        return self.skills[name]

    # ---------- inheritance ----------
    def chain(self, name: str) -> list[str]:
        """The skill and its ancestors, nearest first."""
        out, cur = [], name
        while cur:
            if cur in out:
                raise CycleError(f'Inheritance cycle: {" → ".join(out + [cur])}')
            out.append(cur)
            s = self.skills.get(cur)
            if s is None:
                if cur != name:
                    break
                raise KeyError(cur)
            cur = s.extends
        return out

    def _raw(self, s: Skill, top: bool) -> dict:
        """Merge the inheritance chain without filling {params.x} placeholders, so a child's
        parameters can still change what the parent's steps call."""
        parent = None
        if s.extends:
            if s.extends == s.name:
                raise CycleError(f'{s.name} cannot extend itself')
            ps = self.skills.get(s.extends)
            if ps is not None:
                parent = self._raw(ps, False)
        logic = merge_logic(parent['logic'] if parent else {}, s.logic, s.name)
        uses = []
        for u in (parent['uses'] if parent else []) + list(s.uses):
            if u not in uses:
                uses.append(u)
        return {'logic': logic, 'uses': uses,
                'inputs': list(s.inputs) or (parent['inputs'] if parent else []),
                'outputs': list(s.outputs) or (parent['outputs'] if parent else []),
                'chain': [s.name] + (parent['chain'] if parent else ([s.extends] if s.extends else []))}

    def resolve(self, name: str, skill: Skill | None = None) -> dict:
        """The effective definition after inheritance: logic, uses, inputs and outputs, with parameters filled in."""
        s = skill or self.skills[name]
        if skill is None:
            self.chain(name)
        elif s.extends and s.extends in self.skills and s.name in self.chain(s.extends):
            raise CycleError(f'Inheritance cycle: {s.name} → {" → ".join(self.chain(s.extends))}')
        raw = self._raw(s, True)
        logic = raw['logic']
        params = logic.get('params') or {}
        uses = []
        for u in raw['uses']:
            u2 = subst(u, params)
            if u2 not in uses:
                uses.append(u2)
        if logic.get('steps'):
            steps = []
            for st in logic['steps']:
                st = dict(st)
                if 'use' in st:
                    st['use'] = subst(st['use'], params)
                steps.append(st)
            logic['steps'] = steps
        return {'name': s.name, 'type': s.type, 'logic': logic, 'uses': uses, 'inputs': raw['inputs'], 'outputs': raw['outputs'],
                'chain': raw['chain'], 'abstract': bool(s.logic.get('abstract'))}

    # ---------- dependencies ----------
    def graph(self) -> dict:
        nodes, edges = [], []
        for n, s in self.skills.items():
            # Draw only a skill's own dependencies: what it inherits is implied by its extends edge.
            try:
                params = self.resolve(n)['logic'].get('params') or {}
            except (CycleError, KeyError):
                params = s.logic.get('params') or {}
            uses = list(dict.fromkeys(subst(u, params) for u in s.uses))
            nodes.append({**s.summary(), 'used_by': len(self.dependents(n, direct=True))})
            for u in uses:
                if '{' not in u:
                    edges.append({'from': n, 'to': u, 'kind': 'uses', 'missing': u not in self.skills})
            if s.extends:
                edges.append({'from': n, 'to': s.extends, 'kind': 'extends', 'missing': s.extends not in self.skills})
        return {'nodes': nodes, 'edges': edges}

    def direct_deps(self, name: str) -> list[tuple[str, str]]:
        s = self.skills.get(name)
        if s is None:
            return []
        try:
            uses = self.resolve(name)['uses']
        except (CycleError, KeyError):
            uses = s.uses
        out = [(u, 'uses') for u in uses]
        if s.extends:
            out.append((s.extends, 'extends'))
        return out

    def closure(self, name: str) -> list[str]:
        """Everything a skill needs, transitively (uses and extends)."""
        seen: list[str] = []

        def walk(n):
            for d, _ in self.direct_deps(n):
                if d not in seen and d != name:
                    seen.append(d)
                    walk(d)
        walk(name)
        return seen

    def dependents(self, name: str, direct: bool = False) -> list[dict]:
        """Who relies on this skill: impact analysis for a change."""
        rev: dict[str, list[tuple[str, str]]] = {}
        for n in self.skills:
            for d, kind in self.direct_deps(n):
                rev.setdefault(d, []).append((n, kind))
        out, seen = [], set()
        frontier = [(name, 0)]
        while frontier:
            cur, depth = frontier.pop(0)
            for n, kind in rev.get(cur, []):
                if n in seen or n == name:
                    continue
                seen.add(n)
                out.append({'name': n, 'kind': kind, 'via': cur, 'depth': depth + 1, 'type': self.skills[n].type,
                            'capability': self.is_capability(n)})
                if not direct:
                    frontier.append((n, depth + 1))
        return out

    def find_cycle(self, extra: Skill | None = None) -> list[str] | None:
        skills = dict(self.skills)
        if extra is not None:
            skills[extra.name] = extra
        adj = {}
        for n, s in skills.items():
            params = (s.logic.get('params') or {})
            adj[n] = [subst(u, params) for u in s.uses] + ([s.extends] if s.extends else [])
        color, stack = {}, []

        def dfs(n):
            color[n] = 1
            stack.append(n)
            for d in adj.get(n, []):
                if d not in adj:
                    continue
                if color.get(d) == 1:
                    return stack[stack.index(d):] + [d]
                if not color.get(d):
                    c = dfs(d)
                    if c:
                        return c
            color[n] = 2
            stack.pop()
            return None
        for n in adj:
            if not color.get(n):
                c = dfs(n)
                if c:
                    return c
        return None

    def is_capability(self, name: str) -> bool:
        s = self.skills.get(name)
        return bool(s and s.type == 'business' and 'capability' in s.tags and not s.logic.get('abstract'))

    def capabilities(self) -> list[str]:
        return [n for n in self.skills if self.is_capability(n)]


def _vkey(v: str) -> tuple:
    try:
        return tuple(int(x) for x in str(v).split('.')[:3])
    except ValueError:
        return (0, 0, 0)


def _bump(v: str) -> str:
    a, b, _c = (list(_vkey(v)) + [0, 0, 0])[:3]
    return f'{a}.{b + 1}.0'


def _set_meta(text: str, **kv) -> str:
    """Change metadata values in SKILL.md text without disturbing the rest of the file."""
    import yaml
    from .skillfile import _FM, ydump
    m = _FM.match(text)
    fm = yaml.safe_load(m.group(1)) or {}
    fm.setdefault('metadata', {})
    fm['metadata'].update(kv)
    return f'---\n{ydump(fm)}\n---\n' + m.group(2)
