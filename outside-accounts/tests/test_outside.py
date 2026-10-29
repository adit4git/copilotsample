import hashlib
import io
import json
import re
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.extract import extract  # noqa: E402
from app.extract.core import fix_ticker, parse_date, parse_number  # noqa: E402
from app.extract import llm  # noqa: E402
from app import engine  # noqa: E402
from tools.measure import measure  # noqa: E402

SAMPLES = ROOT / 'samples'
TRUTH = json.loads((SAMPLES / 'truth.json').read_text())


@pytest.fixture(scope='session')
def extracted():
    return {f: extract(SAMPLES / f, sid=f[:2]) for f in TRUTH}


# ------------------------------------------------------------------ extraction
def test_every_sample_field_matches_truth():
    report, tot = measure()
    assert tot['found'] == tot['holdings'] == 40
    assert tot['extra'] == 0
    assert tot['right'] == tot['fields'], [m for r in report for m in r['misses']]


def test_every_sample_reconciles(extracted):
    for f, d in extracted.items():
        assert d['reconciliation'] and d['reconciliation']['ok'], f


def test_formats_and_methods(extracted):
    kinds = {f: d['kind'] for f, d in extracted.items()}
    assert kinds['H1-harborview-brokerage-henderson.pdf'] == 'pdf-text'
    assert kinds['H5-crestmark-annuity-scan.pdf'] == 'pdf-scan'
    assert kinds['H3-northfield-holdings-export.xlsx'] == 'xlsx'
    assert kinds['R1-bayline-positions-rivera.csv'] == 'csv'
    assert kinds['H4-lakeshore-bank-photo.jpg'] == 'image'


def test_account_categories(extracted):
    cat = {f[:2]: d['account_category'] for f, d in extracted.items()}
    assert cat == {'H1': 'taxable', 'H2': 'employer-plan', 'H3': 'taxable', 'H4': 'bank', 'H5': 'annuity', 'R1': 'taxable', 'R2': 'taxable', 'R3': 'ira'}


def test_ocr_correction_is_flagged(extracted):
    d = extracted['R2-pathway-robo-screenshot.png']
    vti = next(h for h in d['holdings'] if h['sym'] == 'VTI')
    if vti['flags']:   # depends on how the OCR engine reads the glyph; when corrected it must be flagged
        assert vti['review'] and 'corrected to VTI' in vti['flags'][0]


def test_allocation_sections(extracted):
    assert [a['pct'] for a in extracted['H2-summit-401k-screenshot.png']['allocation']] == [68.0, 24.0, 8.0]
    assert [a['label'] for a in extracted['H1-harborview-brokerage-henderson.pdf']['allocation']] == ['Equities', 'Alternative investments', 'Cash and money market']


@pytest.mark.parametrize('name,scale,quality', [('H2-summit-401k-screenshot.png', .55, 60), ('R2-pathway-robo-screenshot.png', .5, 60), ('H4-lakeshore-bank-photo.jpg', .6, 40)])
def test_degraded_images_still_reconcile(tmp_path, name, scale, quality):
    im = Image.open(SAMPLES / name)
    im = im.resize((int(im.width * scale), int(im.height * scale))).convert('RGB')
    p = tmp_path / (Path(name).stem + '.jpg')
    im.save(p, quality=quality)
    d = extract(p)
    assert len(d['holdings']) == len(TRUTH[name]['holdings'])
    assert d['reconciliation']['ok']


def test_csv_with_different_headers(tmp_path):
    p = tmp_path / 'x.csv'
    p.write_text('Positions\nOwner,Jane Doe\n\nTicker,Security Description,Units,Unit Price,Current Value\nAAPL,Apple,10,200.00,"2,000.00"\nZZZZ,Mystery Fund,5,10,50\nTotal,,,,"2,050.00"\n')
    d = extract(p)
    assert [h['sym'] for h in d['holdings']] == ['AAPL', 'ZZZZ']
    assert d['stated_total'] == 2050 and d['reconciliation']['ok']


def test_qty_price_mismatch_is_flagged(tmp_path):
    p = tmp_path / 'x.csv'
    p.write_text('Symbol,Description,Quantity,Price,Market Value\nMSFT,Microsoft,10,500,9000\n')
    h = extract(p)['holdings'][0]
    assert h['review'] and 'does not match' in h['flags'][0]


def test_unsupported_type(tmp_path):
    p = tmp_path / 'x.docx'; p.write_bytes(b'x')
    assert 'Unsupported' in extract(p)['warnings'][0]


def test_helpers():
    assert parse_number('$1,234.50') == 1234.5
    assert parse_number('(12.00)') == -12
    assert parse_number('43.9%') == 43.9
    assert parse_number('1O4,562.5O') == 104562.5
    assert fix_ticker('vTl') == ('VTI', True)
    assert fix_ticker('BAL-C') == ('BAL-C', False)
    assert fix_ticker('--') == (None, False)
    assert parse_date('September 30, 2026') == '2026-09-30'
    assert parse_date('10/14/2026') == '2026-10-14'


# ------------------------------------------------------------------ validation
def test_validation_statuses(extracted):
    hh = engine.HH['henderson']
    sts = [extracted[f] for f in TRUTH if f.startswith('H')]
    pos = {(p['statement'], p['sym'] or p['name']): p['status'] for p in engine.outside_positions(sts, hh)}
    assert pos[('H1', 'NVDA')] == 'approved'
    assert pos[('H1', 'ARKK')] == 'review'
    assert pos[('H1', 'QZLGX')] == 'not_approved'
    assert pos[('H1', 'Lumina Bio Series C (private placement)')] == 'held_away'
    assert pos[('H1', 'Harborview Government Money Market')] == 'cash'
    assert pos[('H3', 'New York City GO 3.50% 08/01/2031')] == 'approved'
    assert all(s == 'held_away' for (st, _), s in pos.items() if st in ('H2', 'H5'))


def test_unrecognized_and_override(extracted):
    sts = [extracted[f] for f in TRUTH if f.startswith('R')]
    pos = engine.outside_positions(sts, engine.HH['rivera'])
    z = next(p for p in pos if p['sym'] == 'ZQXI')
    assert z['status'] == 'unrecognized' and z['classes'] == {'LCG': 1}
    pos = engine.outside_positions(sts, engine.HH['rivera'], {z['key']: {'status': 'not_approved', 'classes': {'LCG': 1}}})
    assert next(p for p in pos if p['sym'] == 'ZQXI')['status'] == 'not_approved'


# ------------------------------------------------------------------ proposals
@pytest.fixture(scope='session')
def henderson(extracted):
    return engine.analyse('henderson', [extracted[f] for f in TRUTH if f.startswith('H')])


def test_proposals_conserve_household_value(henderson):
    now = henderson['now']['total']
    for p in henderson['proposals']:
        assert abs(p['metrics']['total'] - now) < 1, p['id']


def test_proposal_rules(henderson):
    A, B, C = henderson['proposals']
    hh = henderson['household']
    assert A['tax'] == 0 and A['sold'] == 0
    assert C['tax'] == 0 and C['realized_loss'] > 0          # ARKK loss harvested
    assert B['net_gain'] <= hh['gain_budget'] + 1
    for p in (A, B, C):
        assert next(c for c in p['checks'] if c['id'] == 'approved')['ok']
        held = [a for a in p['actions'] if a['status'] == 'held_away']
        assert all(a['action'] == 'Stays outside' for a in held)
        buys = [a for a in p['actions'] if a['action'] == 'Buy']
        assert all(engine.APPROVED[a['sym']]['status'] == 'approved' for a in buys)
        keys = [a['key'] for a in p['actions'] if not a['action'].startswith(('Buy', 'Trim'))]
        assert len(keys) == len(set(keys)), f'{p["id"]}: a position has two exclusive actions'
    assert {a['sym'] for a in B['actions'] if a['action'].startswith('Sell')} >= {'QZLGX', 'TRVLX', 'ARKK', 'BAL-C'}


def test_new_money_follows_cio_tilt(henderson):
    B = henderson['proposals'][1]
    bought = {a['sym'] for a in B['actions'] if a['action'] == 'Buy'}
    assert 'VUG' not in bought            # large cap growth is over target and CIO underweight
    assert 'SCHD' in bought               # large cap value is under target and CIO overweight


def test_gain_budget_changes_outcome(extracted):
    sts = [extracted[f] for f in TRUTH if f.startswith('R')]
    z = 'R3:3'
    ov = {z: {'status': 'not_approved', 'classes': {'LCG': 1}}}
    hh = engine.HH['rivera']; saved = hh['gain_budget']
    try:
        hh['gain_budget'] = 75000
        low = engine.analyse('rivera', sts, ov)['proposals'][1]
        hh['gain_budget'] = 250000
        high = engine.analyse('rivera', sts, ov)['proposals'][1]
    finally:
        hh['gain_budget'] = saved
    assert not next(c for c in low['checks'] if c['id'] == 'single')['ok']
    assert all(c['ok'] for c in high['checks'])
    assert high['tax'] > low['tax']


def test_summary_markdown(henderson):
    md = engine.summary_markdown(henderson)
    assert md.startswith('# Outside accounts review: Henderson Family Trust')
    assert '## Proposals' in md and 'Talking points' in md


# ------------------------------------------------------------------ language model reader (mocked)
def test_llm_rows_must_be_grounded(extracted):
    st = json.loads(json.dumps(extracted['R3-harborview-ira-rivera.pdf']))
    st['holdings'] = st['holdings'][:2]
    fake = json.dumps({'holdings': [{'sym': 'ZQXI', 'desc': 'Zephyr Quantum Innovation ETF', 'qty': 1500, 'price': 18.2, 'value': 27300, 'cost': 30000},
                                    {'sym': 'FAKE', 'desc': 'Invented', 'qty': 1, 'price': 999999, 'value': 999999}]})
    out = llm.refine(st, caller=lambda text: fake)
    syms = [h['sym'] for h in out['holdings']]
    assert 'ZQXI' in syms and 'FAKE' not in syms
    assert any('Invented' in w for w in out['warnings'])


# ------------------------------------------------------------------ API
@pytest.fixture(scope='module')
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


def test_api_flow(client):
    sid = client.post('/api/sessions', json={'household': 'rivera'}).json()['id']
    files = [('files', (n, (SAMPLES / n).read_bytes())) for n in TRUTH if n.startswith('R')]
    r = client.post(f'/api/sessions/{sid}/statements', files=files).json()
    assert [len(s['holdings']) for s in r['statements']] == [5, 4, 5]
    a = client.get(f'/api/sessions/{sid}/analysis').json()
    key = next(p['key'] for p in a['positions'] if p['sym'] == 'ZQXI')
    assert client.put(f'/api/sessions/{sid}/overrides', json={'key': key, 'status': 'not_approved', 'classes': {'LCG': 1}}).status_code == 200
    assert client.put(f'/api/sessions/{sid}/settings', json={'gain_budget': 250000}).json()['gain_budget'] == 250000
    a = client.get(f'/api/sessions/{sid}/analysis').json()
    assert all(c['ok'] for c in a['proposals'][1]['checks'])
    assert any(l['event'] == 'override' for l in a['log'])
    assert client.get(f'/api/sessions/{sid}/statements/S2/preview').headers['content-type'] == 'image/png'
    assert client.get(f'/api/sessions/{sid}/summary.md').text.startswith('# Outside accounts review')
    assert engine.HH['rivera']['gain_budget'] == 75000          # session setting never leaks into shared data


def test_api_limits(client):
    sid = client.post('/api/sessions', json={'household': 'henderson'}).json()['id']
    six = [('files', (f'f{i}.csv', b'Symbol,Value\n')) for i in range(6)]
    assert client.post(f'/api/sessions/{sid}/statements', files=six).status_code == 400
    r = client.post(f'/api/sessions/{sid}/statements', files=[('files', ('x.exe', b'MZ'))]).json()
    assert r['statements'] == [] and 'not supported' in r['errors'][0]
    assert client.put(f'/api/sessions/{sid}/overrides', json={'key': 'H1:1', 'status': 'bogus'}).status_code == 400
    assert client.post('/api/sessions', json={'household': 'nobody'}).status_code == 404


def test_samples_endpoint(client):
    sid = client.post('/api/sessions', json={'household': 'henderson'}).json()['id']
    r = client.post(f'/api/sessions/{sid}/samples/henderson').json()
    assert len(r['statements']) == 5
    assert client.get('/api/samples/file/..%2Fapp%2Fmain.py').status_code == 404


# ------------------------------------------------------------------ hygiene
# Hashes of real firm, vendor and manager names that must not appear anywhere (kept hashed so the names are not in the code).
BANNED = {'f4a027b5216940ae', 'f224c1153e340d81', 'bcb3b1ae81b9ce5a', '77f257677ce7f118', '8bfb2cf204b18795', 'b3895d06d266520d', 'f8f488b72eedab34', '2cbb9e58bf3bcbdf', 'e9b6438440bf1991', '9302cae4b3683b9d', '9c7172494b11c874', '4be312760a6df067', 'c224cc422d7cc43a', 'd98c1c698e95339d', 'd5d4f1e5cc5a6d94', '6a62362c11e91c9f', '1d58fd50d5a34ca6', 'a929c5789c0b2460', 'fffacee1653cf049', 'f611beab46437c76', '7e6578c2e34b5313'}


def _grams(text):
    words = re.findall(r"[a-z&]+", text.lower())
    for n in (1, 2, 3):
        for i in range(len(words) - n + 1):
            yield ' '.join(words[i:i + n])


def _hits(text):
    return {g for g in _grams(text) if hashlib.sha256(g.encode()).hexdigest()[:16] in BANNED}


def test_no_real_firm_or_vendor_names():
    hits = []
    for p in list((ROOT / 'app').rglob('*')) + list((ROOT / 'tools').rglob('*.py')) + [ROOT / 'README.md']:
        if p.is_file() and p.suffix in ('.py', '.js', '.html', '.css', '.json', '.md'):
            hits += [f'{p.name}: {h}' for h in _hits(p.read_text(errors='ignore'))]
    for p in SAMPLES.glob('*'):
        txt = extract(p)['text'] if p.suffix != '.json' else p.read_text()
        hits += [f'{p.name}: {h}' for h in _hits(txt)]
    assert not hits, hits


def test_banned_check_works():
    assert _hits('a note about ' + 'van' + 'guard funds')


# ------------------------------------------------------------------ long statements: page triage, multi-page tables, charts
CTRUTH = json.loads((SAMPLES / 'truth_complex.json').read_text())


@pytest.fixture(scope='session')
def complex_results():
    from tools.measure_complex import run
    return run()


def test_long_statement_text_pdf(complex_results):
    r = complex_results['C1-meridian-consolidated-statement-kaplan.pdf']
    assert r['holdings_found'] == '39/39' and r['extra_rows'] == 0      # activity, fee tables and subtotals never become holdings
    assert r['fields'] == '195/195' and r['total']['reconciles']
    assert r['page_types_right'] == '28/28'
    assert r['pie']['within_tol'] == '4/4' and r['pie']['max_err'] <= 1.0
    assert r['bar']['within_tol'] == '7/7' and r['bar']['max_err'] <= 0.1


def test_long_statement_scan(complex_results):
    r = complex_results['C2-meridian-ira-scan-kaplan.pdf']
    assert r['holdings_found'] == '18/18' and r['extra_rows'] == 0 and r['total']['reconciles']
    assert r['page_types_right'] == '12/12'
    assert r['symbols_after_validation'] == '15/15'
    assert r['pie']['within_tol'] == '4/4'


def test_scan_reads_only_needed_pages_at_full_resolution():
    d = extract(SAMPLES / 'C2-meridian-ira-scan-kaplan.pdf')
    assert d['timings']['pages_full_ocr'] == 4 and d['timings']['pages_total'] == 12
    assert [p['type'] for p in d['page_map']] == CTRUTH['C2-meridian-ira-scan-kaplan.pdf']['page_types']


def test_sections_wrapped_rows_and_chart_check():
    d = extract(SAMPLES / 'C1-meridian-consolidated-statement-kaplan.pdf', sid='C1')
    d.pop('_assets')
    assert [s['ok'] for s in d['sections']] == [True, True, True]
    bond = next(h for h in d['holdings'] if h['desc'].startswith('New York St Dorm'))
    assert bond['cusip'] == 'X9A41C7Q2' and 'Callable' in bond['detail'] and bond['section'] == 'Fixed Income'
    assert {h['page'] for h in d['holdings']} == {4, 5, 6, 7, 8}
    assert d['allocation'][0]['source'] == 'chart, page 2'
    r = engine.analyse('kaplan', [d])
    chk = next(c for c in r['statement_checks']['C1'] if c['id'] == 'chart')
    assert chk['ok'] and all(abs(x['chart'] - x['holdings']) <= 1 for x in chk['detail'])
    statuses = {p['sym'] or p['name']: p['status'] for p in r['positions']}
    assert statuses['US Treasury Note 4.125% 11/15/2032'] == 'approved' and statuses['ORGLX'] == 'unrecognized'


def test_activity_table_and_subtotals_in_text(tmp_path):
    p = tmp_path / 's.txt'
    p.write_text('\n'.join([
        'Holdings', 'Description          Symbol    Quantity    Price     Market Value',
        'EQUITIES', 'Apple Inc            AAPL      10          200.00    2,000.00', 'Microsoft Corp       MSFT      2           500.00    1,000.00',
        'Total Equities                                          3,000.00', 'Total US Stock Fund  VTI       1           300.00    300.00',
        'Total Holdings                                          3,300.00',
        'Date        Activity    Description      Symbol   Quantity   Price    Amount', '07/02/2026  Bought      Apple Inc        AAPL     5          200.00   -1,000.00']))
    d = extract(p)
    assert [h['sym'] for h in d['holdings']] == ['AAPL', 'MSFT', 'VTI']
    assert d['sections'][0]['ok'] and d['table_total'] == 3300 and d['reconciliation']['ok']


def test_symbol_misread_is_matched_by_name():
    v = engine.validate_row({'sym': 'VVWO', 'desc': 'Emerging Markets ETF'}, 'ira')
    assert v['match'] == 'VWO' and v['status'] == 'approved' and 'VVWO' in v['symbol_fix']
    assert engine.validate_row({'sym': 'ZQXI', 'desc': 'Zephyr Quantum Innovation ETF'}, 'ira')['status'] == 'unrecognized'


def test_chart_language_model_is_grounded():
    chart = {'type': 'pie', 'method': 'raster', 'note': 'm', 'confidence': 0.55, 'values': [{'label': 'Slice 1', 'pct': 70.2}, {'label': 'Slice 2', 'pct': 29.8}]}
    ok = llm.check_chart(chart, b'', caller=lambda png: '{"values":[{"label":"Stocks","pct":70},{"label":"Bonds","pct":30}]}')
    assert [v['label'] for v in ok['values']] == ['Stocks', 'Bonds'] and ok['confidence'] >= 0.8
    bad = llm.check_chart(chart, b'', caller=lambda png: '{"values":[{"label":"Stocks","pct":55},{"label":"Bonds","pct":45}]}')
    assert bad['values'][0]['label'] == 'Slice 1' and 'disagrees' in bad['note']
    off = llm.check_chart(chart, b'', caller=lambda png: '{"values":[{"label":"Stocks","pct":60},{"label":"Bonds","pct":20}]}')
    assert 'rejected' in off['note']


def test_long_statement_previews_api(client):
    sid = client.post('/api/sessions', json={'household': 'kaplan'}).json()['id']
    st = {s['id']: s for s in client.post(f'/api/sessions/{sid}/samples/kaplan').json()['statements']}
    c1 = st['C1']
    assert 'page-6' in c1['previews'] and 'page-20' not in c1['previews']           # holdings pages kept, disclosures not
    pie = next(c for c in c1['charts'] if c['type'] == 'pie')
    r = client.get(f"/api/sessions/{sid}/statements/C1/preview/{pie['asset']}")
    assert r.status_code == 200 and r.headers['content-type'] == 'image/png'
    a = client.get(f'/api/sessions/{sid}/analysis').json()
    assert any(c['id'] == 'chart' and c['ok'] for c in a['statement_checks']['C1'])
