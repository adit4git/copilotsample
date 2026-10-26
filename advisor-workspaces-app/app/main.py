"""Advisor Workspaces API (FastAPI).

The browser keeps the advisor's decisions and sends them with each request; the server is stateless and never stores,
sends, enrolls or trades anything. All data is illustrative.

  GET  /                              the single-page app
  GET  /api/health                    status and counts
  GET  /api/meta                      labels and constants the page uses
  POST /api/view                      everything one screen needs (route + state in, screen data out)
  GET  /api/book                      ranked households, the opportunity list and the internal book view
  GET  /api/household/{id}            client case: amounts, buckets, value rows, six steps
  GET  /api/household/{id}/routes     transition routes and the stay-in-brokerage alternative
  GET  /api/household/{id}/handoff    handoff checklist and package
  GET  /api/allocation/{id}           allocation finding, gaps, attribution, strategies, routing
  GET  /api/proposal/{id}             value case, cost options, objections, materials, story draft
  GET  /api/position/{hid}/{sym}      concentrated-position plan, decision tree, solutions
  GET  /api/event/{id}                event impact by household
  GET  /api/intelligence              firm intelligence catalog with book status
  GET  /api/checks                    the 30 rule-engine checks
"""
from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .data import DATA, HHS, State
from . import rules as D
from . import pathway as P
from . import calc as X
from . import opportunities as Q
from . import views as V
from .checks import run_checks

app = FastAPI(title='Atlas Advisor Workspaces', version='6.2.0')
STATIC = Path(__file__).parent / 'static'
app.mount('/static', StaticFiles(directory=STATIC), name='static')


class ViewRequest(BaseModel):
    route: dict = Field(default_factory=dict)
    state: dict = Field(default_factory=dict)


def _hid(hid: str) -> str:
    if hid not in DATA['households']:
        raise HTTPException(404, 'Household not found')
    return hid


@app.get('/')
def index():
    return FileResponse(STATIC / 'index.html')


@app.get('/api/health')
def health():
    st = State.from_dict({})
    return {'status': 'ok', 'version': app.version, 'households': len(HHS()), 'opportunities': len(Q.all_queue(st)), 'as_of': DATA['as_of']['positions']}


@app.get('/api/meta')
def meta():
    return {'status': D.STATUS, 'elig': D.ELIG, 'dispositions': D.DISPOSITIONS, 'close_outcomes': D.CLOSE_OUTCOMES, 'reason_needed': D.REASON_NEEDED, 'reasons': D.REASONS,
            'kind': {str(k): v for k, v in P.KIND.items()}, 'flow': P.FLOW, 'seg': P.SEG, 'pshort': P.PSHORT, 'routes': X.ROUTES, 'hsteps': V.HSTEPS, 'viewl': V.VIEWL,
            'as_of': DATA['as_of'], 'perf_as_of': DATA['perf']['as_of'], 'cio_updated': DATA['cio']['updated'], 'threshold': DATA['concentration']['threshold'],
            'households': [{'id': h['id'], 'name': h['name']} for h in HHS()], 'news': [{'id': n['id'], 'headline': n['headline']} for n in DATA['news']], 'fees': DATA['fees'],
            'classes': {k: v['label'] for k, v in DATA['classes'].items()}, 'sectors': DATA['sectors'], 'disclosures': DATA['disclosures']}


@app.post('/api/view')
def view(req: ViewRequest):
    route = req.route or {}
    if route.get('hid') and route['hid'] not in DATA['households']:
        raise HTTPException(404, 'Household not found')
    return V.view({'route': route, 'state': req.state})


@app.get('/api/book')
def book():
    st = State.from_dict({}); q = Q.all_queue(st)
    return {'households': V.landing(st)['rows'], 'opportunities': [Q.public(o, st) for o in q], 'book': P.book(q, st)}


@app.get('/api/household/{hid}')
def household(hid: str):
    return V.household_view(_hid(hid), State.from_dict({}))


@app.get('/api/household/{hid}/routes')
def routes(hid: str):
    return V.paths_view(_hid(hid), State.from_dict({}))


@app.get('/api/household/{hid}/handoff')
def handoff(hid: str):
    return V.handoff_view(_hid(hid), State.from_dict({}))


@app.get('/api/allocation/{hid}')
def allocation(hid: str, scope: str = Query('brokerage', pattern='^(brokerage|all)$'), basis: str = Query('tactical', pattern='^(strategic|tactical)$'),
               period: str = Query('3Y', pattern='^(1Y|3Y)$')):
    return V.allocation_view(_hid(hid), State.from_dict({}), {'scope': scope, 'basis': basis, 'period': period})


@app.get('/api/proposal/{hid}')
def proposal(hid: str):
    return V.proposal_view(_hid(hid), State.from_dict({}), None, [])


@app.get('/api/position/{hid}/{sym}')
def position(hid: str, sym: str):
    st = State.from_dict({}); key = f'{_hid(hid)}:{sym}'
    if not any(p['key'] == key for p in Q.conc_list(st)):
        raise HTTPException(404, 'No concentrated position above the alert threshold')
    return V.position_view(key, st, None)


@app.get('/api/event/{eid}')
def event(eid: str):
    if not any(n['id'] == eid for n in DATA['news']):
        raise HTTPException(404, 'Event not found')
    return V.event_view(eid, State.from_dict({}), None)


@app.get('/api/intelligence')
def intelligence():
    st = State.from_dict({})
    return [{**{k: v for k, v in it.items() if k != 'ev'}, 'book': D.book_status(it, st)} for it in D.catalog()]


@app.get('/api/checks')
def checks():
    r = run_checks()
    return {'passed': sum(1 for x in r if x['pass']), 'total': len(r), 'checks': r}
