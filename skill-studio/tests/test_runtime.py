"""Running skills: each executor, whole capabilities for each client, and each skill's own tests."""
from app.runtime import Runner, make_context, run_tests
from app.skillfile import parse


def names(res, key='shortlist'):
    return [x['name'] for x in res['context'][key]]


def decisions(res):
    return [(d['rule'], d['outcome'], d['item']) for e in res['trace'] if e['kind'] == 'skill' for d in e['decisions']]


def test_sma_selection_for_henderson(reg):
    res = Runner(reg).run('manager-sma-selection', make_context('henderson'))
    assert res['ok'] and not res['context'].get('blocked')
    assert names(res) == ['Crestline Large Cap Value SMA', 'Kestrel Point Dividend Value SMA', 'Linden Row Value Opportunities SMA']
    d = decisions(res)
    assert ('SMA-03', 'exclude', 'Fernhill Deep Value SMA') in d          # rules: tax management
    assert ('SMA-02', 'exclude', 'Alder Peak Value Select SMA') in d       # rules: track record
    assert ('BASE-04', 'flag', 'Ashgrove Value Equity SMA') in d           # inherited rule flags
    assert ('AP-01', 'removed', 'Ashgrove Value Equity SMA') in d          # policy removes
    assert res['context']['alternative']['name'] == 'Core Value Index Fund'
    assert 'not a recommendation' in res['context']['rationale']
    types = {e['type'] for e in res['trace'] if e['kind'] == 'skill'}
    assert types == {'technical', 'rules', 'policy', 'business'}


def test_same_capability_takes_a_different_path_per_client(reg):
    ok = Runner(reg).run('manager-sma-selection', make_context('okonkwo'))
    d = decisions(ok)
    assert not any(r == 'SMA-03' for r, _, _ in d)                         # tax-exempt: tax rule does not fire
    assert ('SUIT-01', 'removed', 'Fernhill Deep Value SMA') in d           # but suitability removes it
    kap = Runner(reg).run('manager-sma-selection', make_context('kaplan'))
    assert names(kap) == ['Brightfield Quality Growth SMA', 'Northgate Growth Leaders SMA']
    assert all(any(f['rule'] == 'AP-03' for f in s['flags']) for s in kap['context']['shortlist'])  # both add to AAPL


def test_fund_selection_reuses_the_process(reg):
    res = Runner(reg).run('fund-selection', make_context('henderson'))
    assert res['ok'] and len(res['context']['shortlist']) == 2
    assert ('FUND-02', 'exclude', 'Active Value Fund, institutional class') in decisions(res)
    assert not any(r == 'BASE-03' for r, _, _ in decisions(res))


def test_capability_of_capabilities(reg):
    res = Runner(reg).run('advisor-meeting-prep', make_context('henderson'))
    brief = res['context']['meeting_brief']
    assert res['ok'] and '1. Concentration.' in brief and '2. Manager candidates.' in brief
    assert max(e['depth'] for e in res['trace']) == 3  # meeting prep → selection → client fit → facts


def test_abstract_parent_cannot_run(reg):
    res = Runner(reg).run('investment-selection-process', make_context('henderson'))
    assert not res['ok'] and 'abstract' in res['error']


def test_policy_blocks_text_with_banned_wording(reg):
    r = Runner(reg)
    r.ctx = {**make_context('henderson'), 'rationale': 'We guarantee results.', 'policy_checks': []}
    r.trace, r._done = [], set()
    r.exec('disclosure-policy', 0)
    assert {b['rule'] for b in r.ctx['blocked']} >= {'PHRASE-BAN-1', 'PHRASE-REQ-1'}


def test_all_seed_skill_tests_pass(reg):
    results = {n: run_tests(reg, s) for n, s in reg.skills.items()}
    assert sum(len(v) for v in results.values()) >= 37
    assert [(n, t) for n, v in results.items() for t in v if not t['ok']] == []


def test_skill_tests_catch_a_broken_change(reg):
    broken = parse(reg.get('manager-sma-selection').raw.replace('screen: sma-eligibility-screen', 'screen: base-eligibility-screen'))
    assert not all(t['ok'] for t in run_tests(reg, broken))
