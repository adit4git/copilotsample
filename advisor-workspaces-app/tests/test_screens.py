"""Screen text produced by the API matches the reference page word for word (tests/fixtures/screens.json)."""
import json
from pathlib import Path
import pytest
from app.data import HHS, DATA, State
from app import calc as X
from app.views import view, value_rows, for_you, why_client

SCR = json.loads((Path(__file__).parent / 'fixtures' / 'screens.json').read_text())
HIDS = [h['id'] for h in HHS()]


@pytest.mark.parametrize('hid', HIDS)
def test_client_case_value_rows(hid):
    assert value_rows(DATA['households'][hid], State.from_dict({})) == SCR['hh'][hid]['valueRows']


@pytest.mark.parametrize('hid', HIDS)
def test_proposal_story_finding_and_value_case(hid):
    d = view({'route': {'ws': 'ws2', 'hid': hid}, 'state': {}})['stage']['data']; f = SCR['hh'][hid]
    assert d['story'] == f['story']
    assert d['card']['finding'] == f['finding']
    assert d['v']['stayR'] == f['stayR'] and d['v']['mgd'] == f['mgd'] and d['v']['status'] == f['status']


@pytest.mark.parametrize('hid', HIDS)
def test_task_panel_story(hid):
    assert view({'route': {'ws': 'path', 'hstep': 'assess', 'hid': hid}, 'state': {}})['side']['story'] == SCR['hh'][hid]['side']


def test_event_explanations():
    n = 0
    for ev in DATA['news']:
        for hh in HHS():
            r = X.event_for_hh(ev, hh)
            if r['score'] > 1:
                f = SCR['ev'][ev['id'] + ':' + hh['id']]; n += 1
                assert for_you(ev, {'hh': hh, **r}) == f['you'] and why_client({'hh': hh, **r}) == f['why']
    assert n == len(SCR['ev'])
