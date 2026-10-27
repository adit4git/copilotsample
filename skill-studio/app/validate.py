"""Validate a SKILL.md before it is saved or approved.

Five layers, each reported separately:
1. format   - frontmatter, name, description, type, version
2. links    - extends and uses point at real skills of the right type, with no cycles
3. logic    - the Logic block fits the skill type (known operations, valid rules and constraints)
4. contract - for business skills, every step has the data it needs from earlier steps
5. tests    - the skill's own examples run and pass
"""
from __future__ import annotations
import re
from .logic import OPS as LOGIC_OPS, variables, placeholders
from .ops import OPS
from .registry import CycleError, Registry, load_json, subst
from .runtime import param_value, run_tests
from .skillfile import TYPES, Skill, SkillFileError, parse

NAME = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
SEMVER = re.compile(r'^\d+\.\d+\.\d+$')
OUTCOMES = {'exclude', 'flag', 'condition', 'block'}
BASE_KEYS = {'client', 'request', 'policy_checks'}


def _walk_ops(rule, out: list):
    if isinstance(rule, list):
        for r in rule:
            _walk_ops(r, out)
    elif isinstance(rule, dict):
        for op, args in rule.items():
            if op not in LOGIC_OPS:
                out.append(op)
            if op != 'var':
                _walk_ops(args, out)


def known_fields() -> dict[str, set[str]]:
    f = load_json('fields.json')
    out = {k: set(v) for k, v in f.items()}
    out['item'] |= {'id', 'firm', 'asset_class', 'top_holdings', 'overlap_names', 'adds_to_concentration', 'fit_score', 'annual_fee',
                    'extra_vs_index', 'flags', 'score_parts'}
    out['client'] |= {'id', 'name', 'profile', 'exposure', 'gain_budget', 'next_meeting'}
    out['request'] |= {'asset_class', 'asset_class_label'}
    out['concentration'] |= {'top_name', 'over_threshold', 'threshold'}
    return out


def validate(reg: Registry, text: str, run_skill_tests: bool = True) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []

    def err(layer, msg):
        errors.append({'layer': layer, 'message': msg})

    def warn(layer, msg):
        warnings.append({'layer': layer, 'message': msg})
    try:
        s = parse(text)
    except SkillFileError as e:
        return {'ok': False, 'errors': [{'layer': 'format', 'message': str(e)}], 'warnings': [], 'tests': [], 'contract': [], 'skill': None}

    # 1. format
    if not s.name:
        err('format', 'name is missing')
    elif not NAME.match(s.name) or len(s.name) > 64:
        err('format', f"name '{s.name}' must be lowercase words joined by hyphens, at most 64 characters")
    elif re.search(r'claude|anthropic', s.name):
        err('format', 'name cannot contain reserved words')
    if not s.description:
        err('format', 'description is missing: it is how the skill gets chosen')
    elif len(s.description) > 1024:
        err('format', f'description is {len(s.description)} characters; the limit is 1024')
    elif not re.search(r'\b(use|used|extend)\b', s.description.lower()):
        warn('format', 'description should say when to use the skill ("Use when …")')
    if s.type not in TYPES:
        err('format', f"type '{s.type}' must be one of: {', '.join(TYPES)}")
    if not SEMVER.match(s.version):
        err('format', f"version '{s.version}' must look like 1.0.0")
    if s.status not in ('draft', 'approved', 'retired'):
        err('format', f"status '{s.status}' must be draft, approved or retired")
    if not s.owner:
        warn('format', 'no owner: every skill needs an accountable team')
    old = reg.get(s.name)
    if old is not None and old.type != s.type:
        err('format', f"'{s.name}' already exists as a {old.type} skill; a new version cannot change the type")

    # 2. links
    if s.extends:
        p = reg.get(s.extends)
        if p is None:
            err('links', f"extends '{s.extends}', which is not in the registry")
        elif p.type != s.type:
            err('links', f"extends '{s.extends}', a {p.type} skill; a {s.type} skill can only extend a {s.type} skill")
    resolved = None
    try:
        resolved = reg.resolve(s.name, s)
    except CycleError as e:
        err('links', str(e))
    except KeyError as e:
        err('links', f'cannot resolve: {e}')
    cyc = reg.find_cycle(s)
    if cyc:
        err('links', 'dependency cycle: ' + ' → '.join(cyc))
    if resolved:
        for u in resolved['uses']:
            if '{' in u:
                err('links', f"'{u}' is never filled in: set that parameter")
            elif u not in reg.skills and u != s.name:
                err('links', f"uses '{u}', which is not in the registry")
            elif u == s.name:
                err('links', 'a skill cannot use itself')
            elif reg.get(u) and reg.get(u).logic.get('abstract'):
                err('links', f"uses '{u}', an abstract parent that cannot run; use a skill that extends it")
            elif reg.get(u) and reg.get(u).status == 'retired':
                warn('links', f"uses '{u}', which is retired")
            elif reg.get(u) and reg.get(u).status == 'draft':
                warn('links', f"uses '{u}', which is still a draft")

    # 3. logic
    logic = resolved['logic'] if resolved else s.logic
    params = logic.get('params') or {}
    fields = known_fields()

    def check_vars(expr, where):
        bad_ops: list[str] = []
        _walk_ops(expr, bad_ops)
        for op in bad_ops:
            err('logic', f"{where}: unknown operator '{op}'")
        for v in variables(expr):
            head, _, rest = v.partition('.')
            field_name = rest.split('.')[0]
            if head == 'params':
                if field_name not in params:
                    err('logic', f"{where}: uses params.{field_name}, which is not set")
            elif head in fields:
                if field_name and field_name not in fields[head]:
                    warn('logic', f"{where}: '{v}' is not in the data vocabulary; it will read as empty")
    if s.type == 'technical':
        op = (logic.get('op') or {}).get('name')
        if op not in OPS:
            err('logic', f"technical skills must name one operation: {', '.join(OPS)}" + (f" (got '{op}')" if op else ''))
    elif s.type == 'rules':
        rules = logic.get('rules') or []
        if not any(not r.get('disabled') for r in rules):
            err('logic', 'a rules skill needs at least one active rule')
        ids = [r.get('id') for r in s.logic.get('rules') or []]
        for d in {i for i in ids if ids.count(i) > 1}:
            err('logic', f'rule id {d} appears more than once')
        for r in rules:
            if r.get('disabled'):
                continue
            rid = r.get('id') or '(no id)'
            if not r.get('id'):
                err('logic', 'every rule needs an id')
            if 'when' not in r:
                err('logic', f'{rid}: no condition (when)')
            else:
                check_vars(r['when'], rid)
            if r.get('outcome', 'flag') not in OUTCOMES:
                err('logic', f"{rid}: outcome must be one of {', '.join(sorted(OUTCOMES))}")
    elif s.type == 'policy':
        cons = logic.get('constraints') or []
        if not cons and not logic.get('required_phrases') and not logic.get('forbidden_phrases'):
            err('logic', 'a policy needs at least one constraint or wording rule')
        for c in cons:
            cid = c.get('id') or '(no id)'
            if 'must' not in c and 'must_not' not in c:
                err('logic', f'{cid}: needs must or must_not')
            for k in ('must', 'must_not'):
                if k in c:
                    check_vars(c[k], cid)
            if c.get('severity', 'block') not in ('block', 'warn'):
                err('logic', f'{cid}: severity must be block or warn')
    elif s.type == 'business':
        steps = logic.get('steps') or []
        if not steps:
            err('logic', 'a business skill needs steps (or must extend a parent that has them)')
        for i, st in enumerate(steps, 1):
            acts = [k for k in ('use', 'take', 'rank', 'set', 'compose', 'note') if k in st]
            if len(acts) != 1:
                err('logic', f'step {i}: needs exactly one of use, take, rank, set, compose or note')
            elif 'use' in st and resolved and st['use'] not in resolved['uses']:
                err('logic', f"step {i} uses '{st['use']}', which is not listed in metadata.uses")
            elif 'note' in st:
                warn('logic', f"step {i} is a manual step for a person: '{st['note']}'")
            elif 'compose' in st:
                for k in ('intro', 'line', 'outro'):
                    for ph in placeholders(st['compose'].get(k, '')):
                        if ph.split('.')[0] == 'params' and ph.split('.')[1] not in params:
                            err('logic', f"step {i}: uses {ph}, which is not set")

    # 4. contract
    contract = contract_check(reg, s, resolved) if resolved and s.type == 'business' and not resolved['abstract'] else []
    for c in contract:
        if not c['ok']:
            err('contract', c['message'])

    # 5. tests
    tests = run_tests(reg, s) if run_skill_tests and not errors else []
    for t in tests:
        if not t['ok']:
            err('tests', f"test '{t['name']}' failed: {t['detail']}")
    if not s.tests:
        warn('tests', 'no tests: add at least one example before approval')

    impact = reg.dependents(s.name) if old is not None else []
    return {'ok': not errors, 'errors': errors, 'warnings': warnings, 'tests': tests, 'contract': contract,
            'skill': s.summary(), 'resolved': resolved, 'is_update': old is not None, 'previous_version': old.version if old else None,
            'impact': impact}


def _io(reg: Registry, name: str, with_params: dict) -> tuple[list[str], list[str]]:
    r = reg.resolve(name)
    params = {**(r['logic'].get('params') or {}), **with_params}
    ins = [str(param_value(x, params)) for x in r['inputs']]
    outs = [str(param_value(x, params)) for x in r['outputs']]
    lg = r['logic']
    for k in ('into',):
        v = lg.get(k) or (lg.get('op') or {}).get('params', {}).get(k)
        if v:
            outs.append(str(param_value(v, params)))
    for u in r['uses']:  # implicit dependencies of non-business skills run first
        if reg.get(u) and reg.get(u).type != 'business' and r['type'] != 'business':
            outs += _io(reg, u, {})[1]
    return list(dict.fromkeys(i for i in ins if '{' not in i)), list(dict.fromkeys(o for o in outs if '{' not in o))


def contract_check(reg: Registry, s: Skill, resolved: dict) -> list[dict]:
    """Walk the steps in order and check that each one's inputs exist by then."""
    params = resolved['logic'].get('params') or {}
    have = set(BASE_KEYS) | {str(param_value(x, params)) for x in resolved['inputs']}
    out = []
    for i, st in enumerate(resolved['logic'].get('steps') or [], 1):
        if 'use' in st:
            name = st['use']
            if not reg.get(name):
                continue
            wp = {k: param_value(v, params) for k, v in (st.get('with') or {}).items()}
            try:
                ins, outs = _io(reg, name, wp)
            except (CycleError, KeyError) as e:
                out.append({'step': i, 'name': name, 'ok': False, 'message': f'step {i} ({name}): {e}'})
                continue
            missing = [x for x in ins if x not in have]
            out.append({'step': i, 'name': name, 'needs': ins, 'gives': outs, 'ok': not missing,
                        'message': f"step {i} ({name}) needs {', '.join(missing)}, which no earlier step produces" if missing else 'ok'})
            have |= set(outs)
        else:
            act = next((k for k in ('take', 'rank', 'set', 'compose', 'note') if k in st), None)
            if act is None:
                continue
            t = st[act] if isinstance(st[act], dict) else {}
            src = t.get('from') or t.get('over') or t.get('each')
            src = param_value(src, params) if src else None
            into = param_value(t.get('into'), params) if t.get('into') else (src if act in ('rank', 'set') else None)
            ok = not src or src in have
            out.append({'step': i, 'name': act, 'needs': [src] if src else [], 'gives': [into] if into else [], 'ok': ok,
                        'message': f"step {i} ({act}) reads '{src}', which no earlier step produces" if not ok else 'ok'})
            if into:
                have.add(into)
    return out
