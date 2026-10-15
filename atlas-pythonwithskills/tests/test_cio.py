"""CIO Model Fit: brokerage accounts vs the CIO strategic model they should map to."""
import math
import pytest
from fastapi.testclient import TestClient

from app import agent
from app.main import app
from app.cio import C, CLS, RF, stats, profile_for, tier_for, account_fit, fit_book

client = TestClient(app)


def test_correlation_matrix_is_valid():
    """Cholesky succeeds only for a positive-definite matrix, so the risk math can't go negative."""
    M = C['cma']['correlation']['matrix']; n = len(M); L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        assert M[i][i] == 1 and all(M[i][j] == M[j][i] for j in range(n))
        for j in range(i + 1):
            s = sum(L[i][k] * L[j][k] for k in range(j))
            if i == j:
                assert M[i][i] - s > 0; L[i][j] = math.sqrt(M[i][i] - s)
            else:
                L[i][j] = (M[i][j] - s) / L[j][j]


def test_stats_math():
    one = stats({'LCV': 1.0})
    assert one['expected_return'] == CLS['LCV']['expected_return'] and one['volatility'] == CLS['LCV']['volatility']
    assert one['sharpe'] == round((CLS['LCV']['expected_return'] - RF) / CLS['LCV']['volatility'], 3)
    two = stats({'LCV': 0.5, 'UST': 0.5})          # diversification: below the weighted-average volatility
    assert two['volatility'] < 0.5 * CLS['LCV']['volatility'] + 0.5 * CLS['UST']['volatility']
    for m in C['models']:
        assert abs(sum(m['weights'].values()) - 1) < 1e-9


def test_profile_grid_and_liquidity_tiers():
    assert profile_for('Moderate', 'Intermediate (3-10 years)') == 'Moderate'
    assert profile_for('Aggressive', 'Short (under 3 years)') == 'Moderate'
    assert tier_for(None) == (0, True) and tier_for('Low') == (2, False)
    t2 = {m['profile']: m['weights'] for m in C['models'] if m['tier'] == 2}
    t3 = {m['profile']: m['weights'] for m in C['models'] if m['tier'] == 3}
    assert t2 == t3                                   # Tier 2 and Tier 3 are currently identical


def test_margin_debit_is_excluded_and_reported():
    a = account_fit('kaplan')
    assert a['coverage']['margin_debit'] == 250000 and a['coverage']['pct'] == 1
    assert a['coverage']['total_mv'] == 8_700_000      # the debit doesn't reduce the allocation base
    assert any(f['id'] == 'margin' for f in a['flags']) and any(f['id'] == 'tier23' for f in a['flags'])
    assert a['setup']['profile'] == 'Moderate' and a['setup']['desc_matches'] is False


def test_margin_credit_counts_as_cash_and_unclassified_lowers_coverage():
    a = account_fit('brennan')
    cash = next(r for r in a['allocation'] if r['class'] == 'CASH')['current']
    assert cash == round((30000 + 20000 + 15000) / a['coverage']['covered_mv'], 4)
    assert a['coverage']['unclassified_mv'] == 150000   # balanced fund (no look-through) + private placement
    assert a['performance']['return_3y'] is None and any(f['id'] == 'history' for f in a['flags'])


def test_blank_liquidity_defaults_to_tier_0_and_low_coverage_is_flagged():
    a = account_fit('fairbanks')
    assert a['setup']['tier'] == 0 and a['setup']['tier_defaulted'] and a['model']['model_id'] == 'CIO-C-T0'
    assert a['coverage']['pct'] == 0.625 and any(f['id'] == 'coverage' for f in a['flags'])
    assert a['muni_proxy_share'] == round(500000 / 1500000, 4)


def test_proxies_core_split_and_concentration():
    a = account_fit('montgomery')
    vti = next(h for h in a['holdings'] if h['sym'] == 'VTI')
    assert vti['classes'] == {'LCG': 150000, 'LCV': 150000}
    assert next(h for h in a['holdings'] if h['sym'] == 'AUSTIN-6.0-31')['method'] == 'PROXY_MUNI'
    assert a['concentration']['sym'] == 'COST' and any(f['id'] == 'concentration' for f in a['flags'])
    assert a['model']['label'] == 'CIO Aggressive, Tier 2'


def test_scope_and_api():
    assert account_fit('henderson')['in_scope'] is False
    b = client.get('/api/cio-fit?fa=dana').json()
    assert {a['household_id'] for a in b['accounts']} == {'montgomery', 'fairbanks', 'brennan', 'kaplan'}
    assert client.get('/api/cio-fit?fa=marcus').json()['accounts'] == []
    assert client.get('/api/cio-fit/kaplan').json()['model']['label'] == 'CIO Moderate, Tier 2'


@pytest.mark.parametrize('message,household', [
    ('Show the CIO model fit for my brokerage accounts', None),
    ("Compare Montgomery's account with its CIO model", 'montgomery'),
])
def test_cio_requests_open_the_workspace(monkeypatch, message, household):
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    r = agent.run_local('dana', message, None)
    auto = [a for a in r['actions'] if a['auto_open']]
    assert len(auto) == 1 and auto[0]['workspace'] == 'cio_fit' and auto[0]['household_id'] == household


def test_cio_intent_leaves_other_requests_alone(monkeypatch):
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    for q in ["Compare vehicles for Henderson's $5M incoming capital", 'Who is breaching concentration limits?']:
        assert not any(a['workspace'] == 'cio_fit' for a in agent.run_local('dana', q, None)['actions']), q
