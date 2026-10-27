"""Read and write SKILL.md files.

A skill is a folder holding one SKILL.md in the standard Agent Skills layout:
YAML frontmatter (name, description, metadata) and a Markdown body. Registry details
(type, version, owner, status, extends, uses, inputs, outputs) sit under `metadata`, so the
file stays valid for any tool that reads only name and description. The machine-readable
part of the skill is one fenced YAML block under "## Logic", and its examples are a fenced
YAML block under "## Tests". Everything else is prose for people and for Claude.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any
import yaml

TYPES = ('technical', 'business', 'policy', 'rules')
TYPE_LABEL = {'technical': 'Technical', 'business': 'Business', 'policy': 'Policy', 'rules': 'Rules-driven'}
_FM = re.compile(r'^---\s*\n(.*?)\n---\s*\n?(.*)$', re.S)
_SECTION = re.compile(r'^##\s+(.+?)\s*$', re.M)
_FENCE = re.compile(r'```ya?ml\s*\n(.*?)(?:\n```|\Z)', re.S)


class SkillFileError(ValueError):
    pass


@dataclass
class Skill:
    name: str
    description: str
    type: str
    version: str = '1.0.0'
    owner: str = ''
    status: str = 'draft'
    extends: str | None = None
    uses: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    title: str = ''
    prose: str = ''
    logic: dict = field(default_factory=dict)
    tests: list = field(default_factory=list)
    raw: str = ''

    def summary(self) -> dict:
        return {'name': self.name, 'description': self.description, 'type': self.type, 'type_label': TYPE_LABEL.get(self.type, self.type),
                'version': self.version, 'owner': self.owner, 'status': self.status, 'extends': self.extends, 'uses': list(self.uses),
                'inputs': list(self.inputs), 'outputs': list(self.outputs), 'tags': list(self.tags), 'title': self.title,
                'abstract': bool(self.logic.get('abstract'))}


def _sections(body: str) -> dict[str, str]:
    out: dict[str, str] = {}
    marks = list(_SECTION.finditer(body))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        out[m.group(1).strip().lower()] = body[m.end():end]
    return out


def parse(text: str) -> Skill:
    m = _FM.match(text.lstrip('﻿'))
    if not m:
        raise SkillFileError('SKILL.md must start with YAML frontmatter between --- lines')
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise SkillFileError(f'Frontmatter is not valid YAML: {e}') from e
    if not isinstance(fm, dict):
        raise SkillFileError('Frontmatter must be a mapping')
    body = m.group(2)
    md = fm.get('metadata') or {}
    if not isinstance(md, dict):
        raise SkillFileError('metadata must be a mapping')
    secs = _sections(body)
    logic, tests = {}, []
    for key, target in (('logic', 'logic'), ('tests', 'tests')):
        sec = secs.get(key)
        if sec is None:
            continue
        f = _FENCE.search(sec)
        if not f:
            continue
        try:
            val = yaml.safe_load(f.group(1))
        except yaml.YAMLError as e:
            raise SkillFileError(f'The {key} block is not valid YAML: {e}') from e
        if target == 'logic':
            if val is not None and not isinstance(val, dict):
                raise SkillFileError('The Logic block must be a YAML mapping')
            logic = val or {}
        else:
            if isinstance(val, dict) and 'tests' in val:
                val = val['tests']
            if val is not None and not isinstance(val, list):
                raise SkillFileError('The Tests block must be a YAML list')
            tests = val or []
    t = re.search(r'^#\s+(.+)$', body, re.M)
    first = _SECTION.search(body)
    prose_end = first.start() if first else len(body)
    prose = body[t.end() if t else 0:prose_end].strip()

    def lst(v):
        if v is None:
            return []
        return [str(x) for x in (v if isinstance(v, list) else [v])]
    return Skill(name=str(fm.get('name') or ''), description=' '.join(str(fm.get('description') or '').split()), type=str(md.get('type') or ''),
                 version=str(md.get('version') or '1.0.0'), owner=str(md.get('owner') or ''), status=str(md.get('status') or 'draft'),
                 extends=(str(md['extends']) if md.get('extends') else None), uses=lst(md.get('uses')), inputs=lst(md.get('inputs')),
                 outputs=lst(md.get('outputs')), tags=lst(md.get('tags')), title=(t.group(1).strip() if t else ''), prose=prose,
                 logic=logic, tests=tests, raw=text)


class _Dumper(yaml.SafeDumper):
    pass


def _str_rep(dumper, data):
    style = '|' if '\n' in data else None
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style=style)


_Dumper.add_representer(str, _str_rep)
_LOGIC_KEYS = {'==', '!=', '>', '>=', '<', '<=', 'and', 'or', '!', '!!', 'not', 'in', 'contains', 'var', 'missing', '+', '-', '*', '/',
               'min', 'max', 'if', 'count', 'abs'}


def _dict_rep(dumper, data):
    flow = len(data) == 1 and next(iter(data)) in _LOGIC_KEYS
    return dumper.represent_mapping('tag:yaml.org,2002:map', data, flow_style=True if flow else None)


_Dumper.add_representer(dict, _dict_rep)


def ydump(obj: Any) -> str:
    return yaml.dump(obj, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=110, default_flow_style=None).rstrip()


def render(s: Skill, sections: dict[str, str] | None = None) -> str:
    """Write a Skill back to SKILL.md text. `sections` adds extra prose sections before Logic."""
    md: dict[str, Any] = {'type': s.type, 'version': s.version, 'owner': s.owner, 'status': s.status}
    if s.extends:
        md['extends'] = s.extends
    md['uses'] = list(s.uses)
    md['inputs'] = list(s.inputs)
    md['outputs'] = list(s.outputs)
    if s.tags:
        md['tags'] = list(s.tags)
    fm = ydump({'name': s.name, 'description': s.description, 'metadata': md})
    parts = [f'---\n{fm}\n---\n', f'# {s.title or s.name}\n', s.prose.strip() + '\n']
    for head, text in (sections or {}).items():
        parts.append(f'## {head}\n\n{text.strip()}\n')
    parts.append('## Logic\n\n```yaml\n' + ydump(s.logic) + '\n```\n')
    if s.tests:
        parts.append('## Tests\n\n```yaml\n' + ydump(s.tests) + '\n```\n')
    return '\n'.join(parts)
