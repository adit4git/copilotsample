"""Outside Accounts: a proof of concept for bringing held-away statements into a portfolio review.

Run:  uvicorn app.main:app --port 8010    then open http://localhost:8010
"""
from __future__ import annotations

import io
import json
import subprocess
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import engine
from .extract import MAX_FILES, SUPPORTED, extract, tools_available
from .extract import llm
from .extract.core import MAX_BYTES

ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT.parent / 'samples'
SAMPLE_SETS = {
    'henderson': {'household': 'henderson', 'label': 'Henderson Family Trust (client): 5 statements',
                  'files': ['H1-harborview-brokerage-henderson.pdf', 'H2-summit-401k-screenshot.png', 'H3-northfield-holdings-export.xlsx',
                            'H4-lakeshore-bank-photo.jpg', 'H5-crestmark-annuity-scan.pdf']},
    'rivera': {'household': 'rivera', 'label': 'Rivera Household (prospect): 3 statements',
               'files': ['R1-bayline-positions-rivera.csv', 'R2-pathway-robo-screenshot.png', 'R3-harborview-ira-rivera.pdf']},
    'kaplan': {'household': 'kaplan', 'label': 'Kaplan Household (client): a 28-page consolidated statement and a 12-page scanned IRA',
               'files': ['C1-meridian-consolidated-statement-kaplan.pdf', 'C2-meridian-ira-scan-kaplan.pdf']},
}
MAX_PREVIEW_PAGES = 12
SURRENDER = {'H5': 'Surrender charge 3% through 30 Jun 2028'}

app = FastAPI(title='Outside Accounts POC', version='1.0.0')
SESSIONS: dict[str, dict] = {}
_cache: dict[str, tuple[dict, bytes | None]] = {}


def preview_png(path: Path, kind: str, page: int = 1) -> bytes | None:
    """A page as a PNG for the side-by-side review. Kept in memory; the source file is not kept."""
    try:
        if kind == 'pdf':
            with tempfile.TemporaryDirectory() as td:
                subprocess.run(['pdftoppm', '-r', '110', '-png', '-f', str(page), '-l', str(page), str(path), f'{td}/p'], check=True, timeout=60)
                return next(Path(td).glob('p*.png')).read_bytes()
        if kind == 'image':
            from PIL import Image
            im = Image.open(path).convert('RGB')
            im.thumbnail((1100, 1100))
            b = io.BytesIO(); im.save(b, 'PNG'); return b.getvalue()
    except Exception:  # preview is a convenience only
        return None
    return None


def run_extract(path: Path, sid: str, name: str) -> tuple[dict, dict]:
    st = extract(path, sid=sid, display_name=name)
    assets = st.pop('_assets', {}) or {}
    if llm.enabled() and (st['needs_review'] or not st['holdings']):
        try:
            st = llm.refine(st)
        except Exception as e:  # the deterministic result stands
            st['warnings'].append(f'Language model unavailable: {e.__class__.__name__}')
    if sid in SURRENDER:
        st['surrender'] = SURRENDER[sid]
    elif 'surrender charge' in st['text'].lower():
        import re
        m = re.search(r'surrender charge[^\n]*', st['text'], re.I)
        st['surrender'] = m.group(0).strip() if m else 'Surrender charge applies'
    kind = SUPPORTED.get(path.suffix.lower(), '')
    # page previews: page 1 plus the summary, chart and holdings pages (the pages the advisor checks against)
    keep = [1] + [p['page'] for p in st.get('page_map', []) if p['type'] in ('summary', 'chart', 'holdings') and p['page'] != 1]
    keep = keep[:MAX_PREVIEW_PAGES]
    previews = {}
    for pg in keep if kind == 'pdf' else [1]:
        png = preview_png(path, kind, pg)
        if png:
            previews[f'page-{pg}'] = png
    previews.update(assets)
    st['previews'] = sorted(previews)
    return st, previews


def session(sid: str) -> dict:
    if sid not in SESSIONS:
        raise HTTPException(404, 'Session not found')
    return SESSIONS[sid]


# ---------------------------------------------------------------------------------------------------------------- API
class NewSession(BaseModel):
    household: str


class Override(BaseModel):
    key: str
    sym: str | None = None
    desc: str | None = None
    qty: float | None = None
    price: float | None = None
    value: float | None = None
    cost: float | None = None
    status: str | None = None
    classes: dict[str, float] | None = None
    exclude: bool | None = None
    note: str | None = None


class Settings(BaseModel):
    gain_budget: float | None = None


@app.get('/api/health')
def health():
    return {'ok': True, 'tools': tools_available(), 'llm': llm.enabled(), 'max_files': MAX_FILES}


@app.get('/api/households')
def households():
    return [{'id': k, 'name': v['name'], 'relationship': v['relationship'], 'profile': v['profile'], 'meeting': v['meeting'],
             'firm_total': sum(h['mv'] for h in v['holdings'])} for k, v in engine.HH.items()]


@app.get('/api/samples')
def samples():
    return [{'id': k, **v} for k, v in SAMPLE_SETS.items()]


@app.get('/api/samples/file/{name}')
def sample_file(name: str):
    p = (SAMPLES / name).resolve()
    if p.parent != SAMPLES.resolve() or not p.exists():
        raise HTTPException(404)
    return FileResponse(p)


@app.post('/api/sessions')
def new_session(body: NewSession):
    if body.household not in engine.HH:
        raise HTTPException(404, 'Unknown household')
    sid = uuid.uuid4().hex[:10]
    SESSIONS[sid] = {'id': sid, 'household': body.household, 'statements': [], 'previews': {}, 'overrides': {},
                     'gain_budget': engine.HH[body.household]['gain_budget'], 'log': []}
    return {'id': sid, 'household': body.household}


def _add(s: dict, st: dict, previews: dict):
    s['statements'].append(st)
    s['previews'][st['id']] = previews or {}
    s['log'].append({'event': 'extracted', 'statement': st['id'], 'file': st['file'], 'rows': len(st['holdings'])})


def _next_id(s):
    return f"S{len(s['statements']) + 1}"


@app.post('/api/sessions/{sid}/statements')
async def upload(sid: str, files: list[UploadFile] = File(...)):
    s = session(sid)
    if len(files) > MAX_FILES:
        raise HTTPException(400, f'Upload up to {MAX_FILES} statements at a time')
    out, errors = [], []
    for f in files:
        ext = Path(f.filename or '').suffix.lower()
        if ext not in SUPPORTED:
            errors.append(f'{f.filename}: file type not supported'); continue
        data = await f.read()
        if len(data) > MAX_BYTES:
            errors.append(f'{f.filename}: larger than {MAX_BYTES // 1024 // 1024} MB'); continue
        with tempfile.TemporaryDirectory() as td:   # the uploaded file is deleted as soon as it is read
            p = Path(td) / f'upload{ext}'
            p.write_bytes(data)
            st, pv = run_extract(p, _next_id(s), f.filename)
        _add(s, st, pv)
        out.append(st)
    return {'statements': out, 'errors': errors}


@app.post('/api/sessions/{sid}/samples/{set_id}')
def load_samples(sid: str, set_id: str):
    s = session(sid)
    if set_id not in SAMPLE_SETS:
        raise HTTPException(404)
    out = []
    for name in SAMPLE_SETS[set_id]['files']:
        key = name
        if key not in _cache:
            _cache[key] = run_extract(SAMPLES / name, name[:2], name)
        st, pv = _cache[key]
        st = json.loads(json.dumps(st))
        st['id'] = name[:2]
        if any(x['id'] == st['id'] for x in s['statements']):
            continue
        _add(s, st, pv)
        out.append(st)
    return {'statements': out, 'errors': []}


@app.delete('/api/sessions/{sid}/statements/{stid}')
def remove_statement(sid: str, stid: str):
    s = session(sid)
    s['statements'] = [x for x in s['statements'] if x['id'] != stid]
    s['previews'].pop(stid, None)
    s['overrides'] = {k: v for k, v in s['overrides'].items() if not k.startswith(stid + ':')}
    return {'ok': True}


@app.get('/api/sessions/{sid}/statements/{stid}/preview')
def statement_preview(sid: str, stid: str):
    png = session(sid)['previews'].get(stid, {}).get('page-1')
    if not png:
        raise HTTPException(404)
    return Response(png, media_type='image/png')


@app.get('/api/sessions/{sid}/statements/{stid}/preview/{key}')
def statement_preview_item(sid: str, stid: str, key: str):
    png = session(sid)['previews'].get(stid, {}).get(key)
    if not png:
        raise HTTPException(404)
    return Response(png, media_type='image/png')


@app.put('/api/sessions/{sid}/overrides')
def set_override(sid: str, body: Override):
    s = session(sid)
    d = {k: v for k, v in body.model_dump().items() if v is not None and k != 'key'}
    if body.status and body.status not in engine.STATUS_LABEL:
        raise HTTPException(400, 'Unknown status')
    if d:
        s['overrides'][body.key] = {**s['overrides'].get(body.key, {}), **d}
    else:
        s['overrides'].pop(body.key, None)
    s['log'].append({'event': 'override', 'row': body.key, 'change': d})
    return {'ok': True, 'overrides': s['overrides']}


@app.delete('/api/sessions/{sid}/overrides/{key}')
def clear_override(sid: str, key: str):
    s = session(sid)
    s['overrides'].pop(key, None)
    return {'ok': True}


@app.put('/api/sessions/{sid}/settings')
def settings(sid: str, body: Settings):
    s = session(sid)
    if body.gain_budget is not None:
        s['gain_budget'] = max(0.0, body.gain_budget)
        s['log'].append({'event': 'gain_budget', 'value': s['gain_budget']})
    return {'ok': True, 'gain_budget': s['gain_budget']}


def _analyse(s):
    hh = engine.HH[s['household']]
    saved = hh['gain_budget']
    hh['gain_budget'] = s['gain_budget']
    try:
        return engine.analyse(s['household'], s['statements'], s['overrides'])
    finally:
        hh['gain_budget'] = saved


@app.get('/api/sessions/{sid}/analysis')
def analysis(sid: str):
    s = session(sid)
    r = _analyse(s)
    r['overrides'] = s['overrides']
    r['log'] = s['log'][-30:]
    return JSONResponse(r)


@app.get('/api/sessions/{sid}/summary.md')
def summary(sid: str):
    s = session(sid)
    r = _analyse(s)
    return Response(engine.summary_markdown(r), media_type='text/markdown')


@app.get('/', response_class=HTMLResponse)
def index():
    return (ROOT / 'static' / 'index.html').read_text()


app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')
