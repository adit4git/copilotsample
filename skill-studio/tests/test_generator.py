"""English in, SKILL.md out: every example, change requests, and the end-to-end path into a running capability."""
import httpx
import pytest
from app.generator import Generator
from app.runtime import Runner, make_context
from app.validate import validate
from app.skillfile import parse

CASES = [
    ('Create a rules skill called esg-sma-screen that extends the SMA eligibility screen. Exclude any manager whose ESG score is below 50. Flag managers with tracking error above 4%. Owner: Sustainability Office.',
     'rules', 'esg-sma-screen'),
    ('A compliance policy: never shortlist a manager with fees above 55 bp, and always show the lower-cost index alternative. Owned by Compliance.', 'policy', 'fee-policy'),
    ('A policy for client letters: never use the words "guaranteed" or "beat the market". Always include "past performance".', 'policy', 'wording-policy'),
    ('Technical skill to calculate a weighted score: information ratio 40% higher is better, fees 30% lower is better, ESG score 30%.', 'technical', 'information-ratio-fee-score'),
    ('A capability for growth SMAs that reuses the standard selection process with the SMA screen and the top 2 names.', 'business', 'growth-sma-selection'),
    ('Business process called muni-ladder-selection: first load the approved list, then run the fund screen, then score candidates, then check client fit, then compare fees, then apply the approved list policy, then take the top 2, then write the selection rationale.',
     'business', 'muni-ladder-selection'),
]


@pytest.mark.parametrize('text,typ,name', CASES, ids=[c[2] for c in CASES])
def test_examples_generate_valid_tested_skills(reg, text, typ, name):
    res = Generator(reg).generate(text)
    assert res['ok'] and res['type'] == typ and res['name'] == name
    v = validate(reg, res['skill_md'])
    assert v['ok'], v['errors']
    assert v['tests'] and all(t['ok'] for t in v['tests'])


def test_rules_are_read_sentence_by_sentence(reg):
    res = Generator(reg).generate(CASES[0][0])
    s = parse(res['skill_md'])
    assert s.extends == 'sma-eligibility-screen' and s.owner == 'Sustainability Office'
    assert [(r['id'], r['outcome'], r['when']) for r in s.logic['rules']] == [
        ('ESS-01', 'exclude', {'<': [{'var': 'item.esg_score'}, 50]}), ('ESS-02', 'flag', {'>': [{'var': 'item.te'}, 4.0]})]


def test_unreadable_sentences_are_reported_not_guessed(reg):
    res = Generator(reg).generate('Create a rules skill. Exclude managers that feel risky. Flag managers with fees above 70 bp.')
    assert res['ok']
    unused = [n for n in res['notes'] if not n['used']]
    assert unused and 'feel risky' in unused[0]['sentence']
    assert len(parse(res['skill_md']).logic['rules']) == 1
    assert not Generator(reg).generate('Make sure managers are good.')['ok']


def test_contract_check_catches_a_missing_step(reg):
    text = CASES[5][0].replace('then compare fees, ', '')
    v = validate(reg, Generator(reg).generate(text)['skill_md'])
    assert not v['ok'] and any(e['layer'] == 'contract' and 'alternative' in e['message'] for e in v['errors'])


def test_change_request_creates_a_new_version_with_impact(reg):
    res = Generator(reg).generate('Raise the SMA track record minimum to 5 years.')
    assert res['kind'] == 'update' and res['name'] == 'sma-eligibility-screen' and res['change'] == {'param': 'min_track_years', 'old': 3, 'new': 5}
    v = validate(reg, res['skill_md'])
    assert v['ok'] and v['is_update'] and {d['name'] for d in v['impact']} >= {'manager-sma-selection'}
    saved = reg.save(res['skill_md'])
    assert saved.version == '1.3.0' and saved.status == 'draft' and reg.history('sma-eligibility-screen')[0]['version'] == '1.2.0'
    w = Generator(reg).generate('Change the fee weight in the CIO scoring to 30.')
    assert w['change'] == {'param': 'weights.fee_bps', 'old': 25, 'new': 30}


def test_english_to_running_capability(reg):
    """Write a new screen in English, build a capability on it in English, then run it."""
    g = Generator(reg)
    reg.save(g.generate(CASES[0][0])['skill_md'])
    cap = g.generate('A capability for value SMAs called esg-value-sma-selection that reuses the standard selection process with the ESG SMA screen and the top 3 names.')
    assert parse(cap['skill_md']).logic['params']['screen'] == 'esg-sma-screen'
    assert validate(reg, cap['skill_md'])['ok']
    reg.save(cap['skill_md'])
    res = Runner(reg).run('esg-value-sma-selection', make_context('henderson'))
    assert res['ok']
    shortlist = [s['name'] for s in res['context']['shortlist']]
    assert 'Kestrel Point Dividend Value SMA' not in shortlist        # ESG 48, excluded by the new rule
    assert ('ESS-01', 'exclude', 'Kestrel Point Dividend Value SMA') in [(d['rule'], d['outcome'], d['item']) for e in res['trace'] for d in e['decisions']]


def test_claude_mode_falls_back_without_a_key(reg):
    res = Generator(reg).generate(CASES[2][0], mode='claude')
    assert res['ok'] and res['mode'] == 'offline' and 'Claude was not used' in res['notes'][0]['reading']


def test_claude_mode_output_goes_through_the_same_validation(reg, monkeypatch):
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-key')
    sample = reg.get('disclosure-policy').raw.replace('name: disclosure-policy', 'name: letter-disclosure-policy')

    class R:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return {'content': [{'type': 'text', 'text': '```markdown\n' + sample + '\n```'}]}
    seen = {}
    def fake_post(url, **kw):
        seen.update(kw)
        return R()
    monkeypatch.setattr(httpx, 'post', fake_post)
    res = Generator(reg).generate('A wording policy for letters', mode='claude')
    assert res['ok'] and res['mode'] == 'claude' and res['name'] == 'letter-disclosure-policy'
    assert 'Registry:' in seen['json']['system'] and validate(reg, res['skill_md'])['ok']
