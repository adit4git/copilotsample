"""Skill files, logic, inheritance and the dependency graph."""
import pytest
from app.logic import evaluate, fmt, variables
from app.registry import CycleError
from app.skillfile import SkillFileError, parse, render


def test_seed_registry_has_all_four_types(reg):
    types = [s.type for s in reg.skills.values()]
    assert len(reg.skills) == 19 and not reg.load_errors
    assert {t: types.count(t) for t in set(types)} == {'technical': 5, 'rules': 4, 'policy': 3, 'business': 7}
    assert sorted(reg.capabilities()) == ['advisor-meeting-prep', 'concentrated-position-review', 'fund-selection', 'manager-sma-selection']


def test_every_seed_file_round_trips(reg):
    for s in reg.skills.values():
        again = parse(render(s))
        assert (again.name, again.type, again.logic, again.tests, again.uses, again.extends) == (s.name, s.type, s.logic, s.tests, s.uses, s.extends)


def test_parse_errors():
    with pytest.raises(SkillFileError):
        parse('# no frontmatter')
    with pytest.raises(SkillFileError):
        parse('---\nname: x\n---\n## Logic\n```yaml\n- a list\n```\n')
    s = parse('---\nname: x\ndescription: d\nmetadata: {type: rules}\n---\n# X\n\n## Tests\n```yaml\n- name: t\n')
    assert s.tests == [{'name': 't'}]  # an unclosed final fence is still read


def test_json_logic_and_formatting():
    d = {'item': {'fee_bps': 60, 'status': 'Watch', 'h': ['A', 'B']}, 'params': {'cap': 50}}
    assert evaluate({'>': [{'var': 'item.fee_bps'}, {'var': 'params.cap'}]}, d) is True
    assert evaluate({'in': [{'var': 'item.status'}, ['Watch', 'Terminated']]}, d) is True
    assert evaluate({'count': {'var': 'item.h'}}, d) == 2
    assert evaluate({'if': [False, 1, 2]}, d) == 2
    with pytest.raises(ValueError):
        evaluate({'exec': ['rm -rf /']}, d)
    assert variables({'and': [{'var': 'item.a'}, {'!': {'var': 'client.b'}}]}) == {'item.a', 'client.b'}
    assert fmt('{x:money} {y:pct1} {z:count} {missing}', {'x': 5130000, 'y': 0.229, 'z': [1, 2]}) == '$5.13M 22.9% 2 —'


def test_child_inherits_overrides_and_disables(reg):
    sma = reg.resolve('sma-eligibility-screen')['logic']['rules']
    by = {r['id']: r for r in sma}
    assert [r['id'] for r in sma] == ['BASE-01', 'BASE-02', 'BASE-03', 'BASE-04', 'SMA-01', 'SMA-02', 'SMA-03']
    assert by['BASE-01']['from'] == 'base-eligibility-screen' and by['SMA-02']['from'] == 'sma-eligibility-screen'
    assert by['BASE-03']['overrides'] == 'base-eligibility-screen'
    fund = {r['id']: r for r in reg.resolve('fund-eligibility-screen')['logic']['rules']}
    assert fund['BASE-03']['disabled'] is True and fund['BASE-03']['disabled_by'] == 'fund-eligibility-screen'


def test_parent_process_parameters_are_filled_by_each_child(reg):
    assert reg.resolve('investment-selection-process')['abstract'] is True
    m = reg.resolve('manager-sma-selection')
    f = reg.resolve('fund-selection')
    assert m['logic']['steps'][1]['use'] == 'sma-eligibility-screen' and f['logic']['steps'][1]['use'] == 'fund-eligibility-screen'
    assert 'sma-eligibility-screen' in m['uses'] and 'base-eligibility-screen' not in m['uses']
    assert m['chain'] == ['manager-sma-selection', 'investment-selection-process']


def test_dependencies_and_impact(reg):
    need = reg.closure('manager-sma-selection')
    assert {'concentration-facts', 'disclosure-policy', 'base-eligibility-screen', 'lookthrough-overlap'} <= set(need)
    hit = {d['name'] for d in reg.dependents('concentration-facts')}
    assert {'concentration-rules', 'client-fit-assessment', 'manager-sma-selection', 'fund-selection', 'advisor-meeting-prep'} <= hit
    caps = {d['name'] for d in reg.dependents('score-candidates') if d['capability']}
    assert caps == {'manager-sma-selection', 'fund-selection', 'advisor-meeting-prep'}


def test_graph_draws_own_dependencies_only(reg):
    g = reg.graph()
    m_edges = {(e['to'], e['kind']) for e in g['edges'] if e['from'] == 'manager-sma-selection'}
    assert m_edges == {('sma-eligibility-screen', 'uses'), ('investment-selection-process', 'extends')}
    assert not any(e['missing'] for e in g['edges'])


def test_cycles_are_caught(reg):
    s = parse(reg.get('base-eligibility-screen').raw.replace('  uses: []', '  extends: sma-eligibility-screen\n  uses: []'))
    with pytest.raises(CycleError):
        reg.resolve(s.name, s)
    loop = parse(reg.get('concentration-facts').raw.replace('  uses: []', '  uses: [concentration-rules]'))
    assert reg.find_cycle(loop) is not None
