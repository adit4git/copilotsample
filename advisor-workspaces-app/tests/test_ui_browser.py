"""End-to-end browser test: the page drives the whole flow through the API.
Skipped unless Playwright and its Chromium are installed (pip install playwright && playwright install chromium)."""
import socket
import subprocess
import sys
import time
from pathlib import Path
import pytest

pw = pytest.importorskip('playwright.sync_api')
ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope='module')
def base_url():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    proc = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--port', str(port)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f'http://127.0.0.1:{port}'
    for _ in range(60):
        try:
            import httpx
            if httpx.get(url + '/api/health', timeout=1).status_code == 200:
                break
        except Exception:
            time.sleep(0.25)
    yield url
    proc.terminate(); proc.wait(timeout=5)


@pytest.fixture(scope='module')
def page(base_url):
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as e:  # browser not installed
            pytest.skip(f'Chromium not available: {e}')
        pg = b.new_page(viewport={'width': 1440, 'height': 900})
        errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto(base_url); pg.wait_for_selector('tr.hrow')
        pg.errors = errors
        yield pg
        b.close()


def settle(pg, ms=400):
    pg.wait_for_timeout(ms)


def test_landing(page):
    assert page.locator('tr.hrow').count() == 6
    assert page.inner_text('.crumb .n') == '27'
    first = page.locator('tr.hrow').first.inner_text()
    assert 'Henderson Family Trust' in first and '$47.20M' in first


def test_household_flow_to_handoff(page):
    page.click('[data-hstep="assess"][data-hid="henderson"]'); settle(page)
    assert 'Potentially movable to advisory now' in page.inner_text('#stage')
    page.click('[data-hdec="ready"]'); settle(page)
    assert page.locator('.pcard2').count() == 4
    page.click('[data-hpath="managed"]'); settle(page)
    page.click('[data-hstep="proposal"].btn'); settle(page, 700)
    assert 'Client story and proposal' in page.inner_text('#stage h1')
    page.click('[data-dx="w2-prep"] summary'); settle(page, 200)
    page.select_option('select[data-rev]', 'compliance'); settle(page)
    page.click('#side .nextbtn'); settle(page)
    for cb in page.locator('[data-hdone]:not([disabled])').all():
        page.locator(f'[data-hdone="{cb.get_attribute("data-hdone")}"]').check(); settle(page, 150)
    page.click('[data-handoff]'); settle(page)
    assert 'Handed off to operations' in page.inner_text('#stage')
    assert 'Handed off: operations to enroll (prototype)' in page.inner_text('#side')


def test_checks_dialog(page):
    page.click('[data-checks]'); page.wait_for_selector('.checks-b b')
    assert page.inner_text('.checks-b b') == '30 of 30 passed'
    page.click('[data-closechecks]')


def test_tour_restores_the_view(page):
    page.evaluate("() => { S.ws = 'ws1'; S.hid = 'kaplan'; return paint(); }"); settle(page)
    page.click('#top [data-tour="start"]'); page.wait_for_selector('.tour-card')
    for _ in range(23):
        settle(page, 300); page.click('[data-tour="next"]')
    settle(page, 600)
    assert page.evaluate('() => [S.ws, S.hid, !!document.getElementById("tour")]') == ['ws1', 'kaplan', False]


def test_no_page_errors(page):
    assert page.errors == []
