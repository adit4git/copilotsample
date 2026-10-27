"""End-to-end in a real browser. Skipped unless Playwright and Chromium are installed."""
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import pytest

pw = pytest.importorskip('playwright.sync_api')
ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope='module')
def page():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    env = {**os.environ, 'SKILL_REGISTRY': os.path.join(tempfile.mkdtemp(), 'registry')}
    proc = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--port', str(port)], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import httpx
    for _ in range(60):
        try:
            if httpx.get(f'http://127.0.0.1:{port}/api/health', timeout=1).status_code == 200:
                break
        except Exception:
            time.sleep(0.25)
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as e:
            proc.terminate()
            pytest.skip(f'Chromium not available: {e}')
        pg = b.new_page(viewport={'width': 1440, 'height': 900})
        pg.errors = []
        pg.on('pageerror', lambda e: pg.errors.append(str(e)))
        pg.goto(f'http://127.0.0.1:{port}/#/registry'); pg.wait_for_selector('.sitem')
        yield pg
        b.close()
    proc.terminate(); proc.wait(timeout=5)


def test_registry_lists_and_opens_skills(page):
    assert page.locator('.sitem').count() == 19
    page.click('[data-open="sma-eligibility-screen"]'); page.wait_for_timeout(300)
    page.click('[data-sub="logic"]'); page.wait_for_timeout(200)
    t = page.inner_text('.panel')
    assert 'inherited from base-eligibility-screen' in t and 'overrides base-eligibility-screen' in t


def test_map_highlights_dependencies_and_impact(page):
    page.goto(page.url.split('#')[0] + '#/map'); page.wait_for_selector('svg.map')
    page.click('[data-node="client-fit-assessment"]'); page.wait_for_timeout(200)
    assert page.locator('.node.dep').count() == 3 and page.locator('.node.imp').count() == 4


def test_run_capability_shows_trace(page):
    page.goto(page.url.split('#')[0] + '#/run/manager-sma-selection'); page.wait_for_selector('[data-run]')
    page.click('[data-run]'); page.wait_for_selector('.trace')
    assert 'Delivered' in page.inner_text('.sumbar') and page.locator('.tr').count() >= 15


def test_create_from_english_and_save(page):
    page.goto(page.url.split('#')[0] + '#/create'); page.wait_for_selector('[data-ex]')
    page.click('[data-ex="0"]'); page.click('[data-generate]'); page.wait_for_selector('[data-editor]')
    assert 'esg-sma-screen' in page.input_value('[data-editor]')
    page.click('[data-save]'); page.wait_for_selector('.callout.ok')
    page.goto(page.url.split('#')[0] + '#/registry/esg-sma-screen'); page.wait_for_timeout(400)
    assert 'ESG SMA screen' in page.inner_text('h1 >> nth=1')


def test_no_page_errors(page):
    assert page.errors == []
