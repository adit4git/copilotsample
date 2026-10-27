"""Skill Studio: FastAPI routes for the registry, capability runs and the English-to-skill generator."""
from __future__ import annotations
import os
from pathlib import Path
from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .generator import Generator
from .ops import OPS
from .registry import Registry, load_json
from .runtime import Runner, make_context, run_tests
from .skillfile import TYPE_LABEL, TYPES, SkillFileError, parse
from .validate import validate

STATIC = Path(__file__).resolve().parent / 'static'
app = FastAPI(title='Skill Studio', version='1.0.0',
              description='A registry of technical, business, policy and rules-driven skills that build on each other. Illustrative data only.')
REG = Registry()


class RunReq(BaseModel):
    skill: str
    client: str = 'henderson'
    asset_class: str | None = None
    amount: float | None = Field(default=None, ge=0)


class TextReq(BaseModel):
    text: str = Field(min_length=1, max_length=20000)


class GenReq(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    mode: str = 'offline'


def _skill(name: str):
    s = REG.get(name)
    if s is None:
        raise HTTPException(404, f'No skill called {name}')
    return s


@app.get('/api/health')
def health():
    return {'status': 'ok', 'skills': len(REG.skills), 'capabilities': len(REG.capabilities()), 'load_errors': REG.load_errors}


@app.get('/api/meta')
def meta():
    return {'types': [{'id': t, 'label': TYPE_LABEL[t]} for t in TYPES], 'ops': {k: v[1] for k, v in OPS.items()},
            'clients': [{'id': c['id'], 'name': c['name'], 'profile': c['profile'], 'request': c['request']} for c in load_json('clients.json')['clients']],
            'asset_classes': {k: v['label'] for k, v in load_json('asset_classes.json').items()},
            'claude_available': bool(os.environ.get('ANTHROPIC_API_KEY')), 'registry_path': str(REG.path)}


@app.get('/api/skills')
def list_skills():
    g = REG.graph()
    used_by = {n['name']: n['used_by'] for n in g['nodes']}
    return [{**s.summary(), 'used_by': used_by.get(n, 0), 'capability': REG.is_capability(n), 'tests': len(s.tests)} for n, s in sorted(REG.skills.items())]


@app.get('/api/skills/{name}')
def get_skill(name: str):
    s = _skill(name)
    r = REG.resolve(name)
    own_ids = {x.get('id') for k in ('rules', 'constraints') for x in s.logic.get(k) or []}
    return {**s.summary(), 'prose': s.prose, 'raw': s.raw, 'logic': s.logic, 'tests': s.tests, 'resolved': r, 'own_ids': sorted(i for i in own_ids if i),
            'capability': REG.is_capability(name), 'depends_on': REG.closure(name), 'direct': [{'name': d, 'kind': k} for d, k in REG.direct_deps(name)],
            'dependents': REG.dependents(name), 'history': REG.history(name), 'test_results': run_tests(REG, s)}


@app.get('/api/skills/{name}/raw', response_class=PlainTextResponse)
def raw_skill(name: str):
    return _skill(name).raw


@app.get('/api/graph')
def graph():
    return REG.graph()


@app.post('/api/run')
def run(req: RunReq):
    s = _skill(req.skill)
    if s.logic.get('abstract'):
        raise HTTPException(422, f'{req.skill} is an abstract parent; run a skill that extends it')
    try:
        ctx = make_context(req.client, req.asset_class, req.amount)
    except KeyError as e:
        raise HTTPException(404, f'Unknown client or asset class: {e}') from e
    return Runner(REG).run(req.skill, ctx)


@app.post('/api/generate')
def generate(req: GenReq):
    res = Generator(REG).generate(req.text, req.mode)
    if res.get('ok'):
        res['validation'] = validate(REG, res['skill_md'])
    return res


@app.post('/api/validate')
def validate_text(req: TextReq):
    return validate(REG, req.text)


@app.post('/api/skills')
def save_skill(req: TextReq):
    v = validate(REG, req.text)
    if not v['ok']:
        raise HTTPException(422, {'message': 'The skill has errors; fix them before saving', 'validation': v})
    try:
        s = REG.save(req.text)
    except SkillFileError as e:
        raise HTTPException(422, str(e)) from e
    return {'saved': s.summary(), 'validation': v}


@app.post('/api/skills/{name}/approve')
def approve(name: str, body: dict = Body(default={})):
    s = _skill(name)
    v = validate(REG, s.raw)
    tests = v['tests']
    if not v['ok'] or not tests or not all(t['ok'] for t in tests):
        raise HTTPException(422, {'message': 'Approval needs a valid skill with at least one passing test', 'validation': v})
    drafts = [d for d in REG.closure(name) if REG.get(d) and REG.get(d).status == 'draft']
    if drafts:
        raise HTTPException(422, {'message': 'Approve its dependencies first: ' + ', '.join(drafts), 'validation': v})
    return REG.set_status(name, 'approved').summary()


@app.post('/api/skills/{name}/retire')
def retire(name: str):
    _skill(name)
    users = [d['name'] for d in REG.dependents(name, direct=True) if REG.get(d['name']).status != 'retired']
    if users:
        raise HTTPException(422, {'message': 'Still used by: ' + ', '.join(users)})
    return REG.set_status(name, 'retired').summary()


@app.get('/api/skills/{name}/history/{version}', response_class=PlainTextResponse)
def history_version(name: str, version: str):
    f = REG.path / name / 'history' / f'{version}.md'
    if not f.exists() or '/' in version:
        raise HTTPException(404, 'No such version')
    return f.read_text()


@app.get('/api/export', response_class=PlainTextResponse)
def export_all():
    """Every skill in one plain-text Markdown file, for reading or moving without a zip."""
    parts = ['# Skill registry export', '', f'{len(REG.skills)} skills. Each section below is one complete SKILL.md.', '']
    for n, s in sorted(REG.skills.items(), key=lambda kv: (TYPES.index(kv[1].type) if kv[1].type in TYPES else 9, kv[0])):
        parts += [f'\n\n<!-- ===== {n}/SKILL.md ===== -->\n', '~~~~markdown', s.raw.rstrip(), '~~~~']
    return '\n'.join(parts) + '\n'


@app.post('/api/reset')
def reset():
    REG.reset()
    REG.reload()
    return {'skills': len(REG.skills)}


@app.get('/')
def index():
    return FileResponse(STATIC / 'index.html')


app.mount('/static', StaticFiles(directory=STATIC), name='static')
