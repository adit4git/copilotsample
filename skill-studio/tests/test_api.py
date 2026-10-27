"""The HTTP API: browsing, running, generating, saving, approving, retiring and exporting."""
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)


def test_health_meta_and_list(reg):
    assert c.get('/api/health').json()['skills'] == 19
    m = c.get('/api/meta').json()
    assert [t['id'] for t in m['types']] == ['technical', 'business', 'policy', 'rules'] and len(m['clients']) == 3
    lst = c.get('/api/skills').json()
    assert len(lst) == 19 and next(s for s in lst if s['name'] == 'concentration-facts')['used_by'] >= 2


def test_skill_detail(reg):
    d = c.get('/api/skills/manager-sma-selection').json()
    assert d['capability'] and d['resolved']['chain'][1] == 'investment-selection-process' and all(t['ok'] for t in d['test_results'])
    assert c.get('/api/skills/manager-sma-selection/raw').text.startswith('---\nname: manager-sma-selection')
    assert c.get('/api/skills/nope').status_code == 404


def test_run(reg):
    r = c.post('/api/run', json={'skill': 'manager-sma-selection', 'client': 'kaplan'}).json()
    assert r['ok'] and r['request']['asset_class'] == 'LCG' and len(r['context']['shortlist']) == 2
    assert c.post('/api/run', json={'skill': 'investment-selection-process'}).status_code == 422
    assert c.post('/api/run', json={'skill': 'manager-sma-selection', 'client': 'nobody'}).status_code == 404


def test_generate_save_approve_flow(reg):
    g = c.post('/api/generate', json={'text': 'A policy for client letters: never use the words "guaranteed". Always include "past performance".'}).json()
    assert g['ok'] and g['validation']['ok']
    saved = c.post('/api/skills', json={'text': g['skill_md']}).json()['saved']
    assert saved['status'] == 'draft'
    assert c.post(f"/api/skills/{saved['name']}/approve", json={}).json()['status'] == 'approved'
    bad = c.post('/api/skills', json={'text': g['skill_md'].replace('type: policy', 'type: magic')})
    assert bad.status_code == 422


def test_approval_waits_for_draft_dependencies(reg):
    r = c.post('/api/skills/advisor-meeting-prep/approve', json={})
    assert r.status_code == 200  # its dependencies are all approved
    upd = c.post('/api/generate', json={'text': 'Raise the SMA track record minimum to 4 years.'}).json()
    c.post('/api/skills', json={'text': upd['skill_md']})
    blocked = c.post('/api/skills/manager-sma-selection/approve', json={})
    assert blocked.status_code == 422 and 'sma-eligibility-screen' in blocked.json()['detail']['message']
    assert c.get('/api/skills/sma-eligibility-screen').json()['history'][0]['version'] == '1.2.0'
    assert c.get('/api/skills/sma-eligibility-screen/history/1.2.0').text.count('min_track_years: 3') == 1


def test_retire_only_unused_skills(reg):
    assert c.post('/api/skills/concentration-facts/retire').status_code == 422
    assert c.post('/api/skills/advisor-meeting-prep/retire').json()['status'] == 'retired'


def test_export_is_one_plain_text_file(reg):
    t = c.get('/api/export').text
    assert t.count('~~~~markdown') == 19 and 'name: manager-sma-selection' in t


def test_static_page(reg):
    r = c.get('/')
    assert r.status_code == 200 and 'Skill Studio' in r.text
    for f in ('app.js', 'styles.css'):
        assert c.get('/static/' + f).status_code == 200
