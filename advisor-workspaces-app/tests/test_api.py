"""API contract: every screen loads for every household, the API is stateless, and errors are clean."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.data import HHS

c = TestClient(app)
HIDS = [h['id'] for h in HHS()]


def test_health_and_meta():
    h = c.get('/api/health').json()
    assert h['status'] == 'ok' and h['households'] == 6 and h['opportunities'] == 27
    m = c.get('/api/meta').json()
    assert m['elig']['ineligible'][0] == 'Not eligible for the program' and len(m['hsteps']) == 4


def test_static_app():
    r = c.get('/'); assert r.status_code == 200 and 'Advisor Workspaces' in r.text
    for f in ('app.js', 'tour.js', 'charts.js', 'styles.css'):
        assert c.get('/static/' + f).status_code == 200


ROUTES = [{'ws': 'queue', 'qv': 'hh'}, {'ws': 'queue', 'qv': 'opp'}, {'ws': 'path', 'hstep': 'assess'}, {'ws': 'path', 'hstep': 'paths'}, {'ws': 'path', 'hstep': 'handoff'},
          {'ws': 'ws1'}, {'ws': 'ws2'}, {'ws': 'ws3'}, {'ws': 'ws4', 'ev': 'n2'}, {'ws': 'ws4', 'o4': {'view': 'firm', 'sel': 'n1'}}]


@pytest.mark.parametrize('hid', HIDS)
@pytest.mark.parametrize('route', ROUTES, ids=lambda r: r['ws'] + '-' + (r.get('hstep') or r.get('qv') or ''))
def test_every_screen_loads(hid, route):
    r = c.post('/api/view', json={'route': {**route, 'hid': hid}, 'state': {}})
    assert r.status_code == 200
    d = r.json(); assert d['top']['open'] == 27 and d['side']['stages'][0]['stage'] == 'Identify'


def test_stateless_decisions_travel_with_the_request():
    r = c.post('/api/view', json={'route': {'ws': 'queue', 'qv': 'hh'}, 'state': {'disp': {'ws3:kaplan:AAPL': {'status': 'stay', 'set': True, 'reason': 'Client declined'}}}}).json()
    assert r['top']['open'] == 26
    assert c.post('/api/view', json={'route': {'ws': 'queue'}, 'state': {}}).json()['top']['open'] == 27


def test_rest_endpoints():
    assert len(c.get('/api/book').json()['opportunities']) == 27
    assert c.get('/api/household/henderson').json()['A']['now'] == 47200000
    assert [p['id'] for p in c.get('/api/household/okonkwo/routes').json()['paths']] == ['rebalance', 'phased']
    assert len(c.get('/api/household/kaplan/handoff').json()['items']) == 7
    assert c.get('/api/allocation/kaplan?scope=all&basis=strategic&period=1Y').json()['card']['status'] == 'review'
    assert 'what an advisory relationship could add' in c.get('/api/proposal/okonkwo').json()['story']
    assert c.get('/api/position/henderson/NVDA').json()['plan']['reach'] == 2030
    assert c.get('/api/event/n1').json()['ranked'][0]['hid'] == 'henderson'
    assert len(c.get('/api/intelligence').json()) == 13
    assert c.get('/api/checks').json()['passed'] == 30


def test_errors():
    assert c.get('/api/household/nobody').status_code == 404
    assert c.get('/api/position/okonkwo/NVDA').status_code == 404
    assert c.get('/api/event/zz').status_code == 404
    assert c.get('/api/allocation/kaplan?scope=bad').status_code == 422
    assert c.post('/api/view', json={'route': {'ws': 'path', 'hid': 'nobody'}}).status_code == 404
