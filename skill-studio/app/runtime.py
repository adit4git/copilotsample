"""Run skills. Each of the four skill types has its own executor:

- technical: calls one operation from the safe library in ops.py
- rules:     evaluates rules (JSON-Logic) per item or once, and excludes, flags or blocks
- policy:    checks constraints and required wording; can remove items or block text
- business:  runs steps in order: sub-skills (`use`), plus take, rank, set and compose

A run records a trace: every skill and step, what it read and wrote, and its decisions.
"""
from __future__ import annotations
import copy
import time
from typing import Any
from .logic import evaluate, fmt, money
from .ops import OPS
from .registry import _PARAM, Registry, load_json
from .skillfile import Skill


class RunError(RuntimeError):
    pass


def param_value(v: Any, params: dict) -> Any:
    """'{params.x}' becomes the raw value of params.x (a list stays a list); anything else is returned as is."""
    if isinstance(v, str):
        m = _PARAM.match(v)
        if m:
            return params.get(m.group(1), v)
    return v


def make_context(client_id: str, asset_class: str | None = None, amount: float | None = None, client_over: dict | None = None) -> dict:
    clients = {c['id']: c for c in load_json('clients.json')['clients']}
    if client_id not in clients:
        raise KeyError(client_id)
    c = copy.deepcopy(clients[client_id])
    if client_over:
        c.update(client_over)
    req = dict(c.pop('request'))
    if asset_class:
        req['asset_class'] = asset_class
    if amount is not None:
        req['amount'] = float(amount)
    acs = load_json('asset_classes.json')
    if req['asset_class'] not in acs:
        raise KeyError(req['asset_class'])
    req['asset_class_label'] = acs[req['asset_class']]['label']
    return {'client': c, 'request': req}


class Runner:
    def __init__(self, reg: Registry, max_depth: int = 8):
        self.reg = reg
        self.max_depth = max_depth

    # ---------- entry point ----------
    def run(self, name: str, ctx: dict, skill: Skill | None = None) -> dict:
        self.trace: list[dict] = []
        self.ctx = ctx
        ctx.setdefault('policy_checks', [])
        self._done: set[str] = set()
        t0 = time.perf_counter()
        ok, err = True, None
        try:
            self.exec(name, depth=0, skill=skill)
        except (RunError, ValueError, KeyError) as e:
            ok, err = False, str(e)
        outputs = {k: v for k, v in ctx.items() if k not in ('client', 'request')}
        return {'ok': ok, 'error': err, 'trace': self.trace, 'context': outputs, 'client': ctx['client'], 'request': ctx['request'],
                'ms': round((time.perf_counter() - t0) * 1000, 1),
                'skills_run': len({e['skill'] for e in self.trace if e['kind'] == 'skill'})}

    # ---------- one skill ----------
    def exec(self, name: str, depth: int, with_params: dict | None = None, skill: Skill | None = None) -> None:
        if depth > self.max_depth:
            raise RunError(f'Too deep at {name}: check for a dependency loop')
        s = skill if skill is not None and skill.name == name else self.reg.get(name)
        if s is None:
            raise RunError(f'Skill not found: {name}')
        r = self.reg.resolve(name, s if skill is not None and skill.name == name else None)
        if r['abstract']:
            raise RunError(f'{name} is an abstract parent skill: run one of the skills that extend it')
        logic = r['logic']
        params = {**(logic.get('params') or {}), **(with_params or {})}
        ev = {'kind': 'skill', 'skill': name, 'type': s.type, 'version': s.version, 'status': s.status, 'title': s.title, 'depth': depth,
              'chain': r['chain'], 'params': with_params or {}, 'decisions': [], 'summary': '', 'reads': list(r['inputs']), 'writes': list(r['outputs'])}
        self.trace.append(ev)
        t0 = time.perf_counter()
        if s.type != 'business':
            for u in r['uses']:
                if u not in self._done:
                    self.exec(u, depth + 1)
        try:
            ev['summary'] = getattr(self, f'_{s.type}')(name, logic, params, depth, ev)
        except RunError:
            raise
        except (ValueError, KeyError, TypeError) as e:
            ev['error'] = str(e)
            raise RunError(f'{name}: {e}') from e
        finally:
            ev['ms'] = round((time.perf_counter() - t0) * 1000, 2)
        self._done.add(name)

    def _key(self, v: Any, params: dict) -> Any:
        return param_value(v, params)

    # ---------- technical ----------
    def _technical(self, name, logic, params, depth, ev):
        op = logic.get('op') or {}
        fn = OPS.get(op.get('name'))
        if fn is None:
            raise RunError(f"{name}: unknown operation '{op.get('name')}'")
        p = {**(op.get('params') or {}), **{k: v for k, v in params.items() if k not in ('weights', 'better')}}
        if 'weights' in params:
            p['weights'] = params['weights']
        if 'better' in params:
            p['better'] = params['better']
        p = {k: self._key(v, params) for k, v in p.items()}
        return fn[0](self.ctx, p)

    # ---------- rules ----------
    def _rules(self, name, logic, params, depth, ev):
        rules = [r for r in logic.get('rules') or [] if not r.get('disabled')]
        over = self._key(logic.get('over'), params)
        into = self._key(logic.get('into'), params) or (f'{over}_screened' if over else f'{name}_findings')
        if over:
            items = self.ctx.get(over)
            if not isinstance(items, list):
                raise RunError(f"{name}: needs '{over}' but it is not available yet")
            kept, counts = [], {}
            for it in items:
                it = copy.deepcopy(it)
                res = self.apply_rules(rules, it, params)
                for d in res['fired']:
                    ev['decisions'].append({'rule': d['id'], 'item': it.get('name'), 'outcome': d['outcome'], 'message': d['message'], 'from': d.get('from')})
                    counts[d['outcome']] = counts.get(d['outcome'], 0) + 1
                if res['outcome'] != 'exclude':
                    it.setdefault('flags', [])
                    it['flags'] += [{'rule': d['id'], 'message': d['message']} for d in res['fired'] if d['outcome'] == 'flag']
                    kept.append(it)
            self.ctx[into] = kept
            return f"{len(items)} in → {len(kept)} kept; {counts.get('exclude', 0)} excluded, {counts.get('flag', 0)} flagged"
        data = {**self.ctx, 'params': params}
        findings = []
        for r in rules:
            if evaluate(r['when'], data):
                f = {'rule': r['id'], 'outcome': r.get('outcome', 'flag'), 'message': fmt(r.get('message', r['id']), data), 'owner': r.get('owner', ''), 'from': r.get('from')}
                findings.append(f)
                ev['decisions'].append({'rule': r['id'], 'item': None, 'outcome': f['outcome'], 'message': f['message'], 'from': r.get('from')})
        self.ctx[into] = {'findings': findings, 'blocked': any(f['outcome'] == 'block' for f in findings)}
        return f"{len(findings)} of {len(rules)} rules fired" + ('; blocked' if self.ctx[into]['blocked'] else '')

    def apply_rules(self, rules: list, item: dict, params: dict) -> dict:
        data = {**self.ctx, 'item': item, 'params': params}
        fired, outcome = [], 'pass'
        for r in rules:
            if evaluate(r['when'], data):
                o = r.get('outcome', 'flag')
                fired.append({'id': r['id'], 'outcome': o, 'message': fmt(r.get('message', r['id']), data), 'from': r.get('from')})
                if o == 'exclude':
                    outcome = 'exclude'
                    break
                if o == 'flag' and outcome == 'pass':
                    outcome = 'flag'
        return {'outcome': outcome, 'fired': fired}

    # ---------- policy ----------
    def _policy(self, name, logic, params, depth, ev):
        cons = [c for c in logic.get('constraints') or [] if not c.get('disabled')]
        over = self._key(logic.get('over'), params)
        text_key = self._key(logic.get('text_key'), params)
        checks, removed, warned = [], 0, 0
        if over:
            items = self.ctx.get(over)
            if not isinstance(items, list):
                raise RunError(f"{name}: needs '{over}' but it is not available yet")
            kept = []
            for it in items:
                res = self.check_constraints([c for c in cons if c.get('scope', 'each') == 'each'], {**self.ctx, 'item': it, 'params': params})
                for v in res:
                    checks.append({**v, 'item': it.get('name')})
                    ev['decisions'].append({'rule': v['id'], 'item': it.get('name'), 'outcome': 'removed' if v['severity'] == 'block' else 'warning', 'message': v['message'], 'from': v.get('from')})
                if any(v['severity'] == 'block' for v in res):
                    removed += 1
                    continue
                if res:
                    warned += 1
                    it.setdefault('flags', [])
                    it['flags'] += [{'rule': v['id'], 'message': v['message']} for v in res]
                kept.append(it)
            self.ctx[over] = kept
        whole = [c for c in cons if not over or c.get('scope') == 'run']
        for v in self.check_constraints(whole, {**self.ctx, 'params': params}):
            checks.append({**v, 'item': None})
            ev['decisions'].append({'rule': v['id'], 'item': None, 'outcome': 'blocked' if v['severity'] == 'block' else 'warning', 'message': v['message'], 'from': v.get('from')})
        if text_key:
            text = str(self.ctx.get(text_key) or '')
            for v in self.check_text(logic, text, params):
                checks.append({**v, 'item': None})
                ev['decisions'].append({'rule': v['id'], 'item': None, 'outcome': 'blocked' if v['severity'] == 'block' else 'warning', 'message': v['message'], 'from': name})
        blocked = [c for c in checks if c['severity'] == 'block' and c['item'] is None]
        if blocked:
            self.ctx.setdefault('blocked', []).extend({'skill': name, 'rule': c['id'], 'message': c['message']} for c in blocked)
        n_checked = len(cons) + (len(logic.get('required_phrases') or []) + len(logic.get('forbidden_phrases') or []) if text_key else 0)
        self.ctx['policy_checks'].append({'skill': name, 'checked': n_checked, 'violations': checks})
        if not checks:
            return f'{n_checked} checks passed'
        bits = []
        if removed:
            bits.append(f'{removed} removed')
        if warned:
            bits.append(f'{warned} flagged')
        if blocked:
            bits.append(f'{len(blocked)} blocking')
        return f"{len(checks)} violation(s): " + ', '.join(bits or ['warnings'])

    def check_constraints(self, cons: list, data: dict) -> list[dict]:
        out = []
        for c in cons:
            bad = False
            if 'must' in c and not evaluate(c['must'], data):
                bad = True
            if 'must_not' in c and evaluate(c['must_not'], data):
                bad = True
            if bad:
                out.append({'id': c['id'], 'severity': c.get('severity', 'block'), 'message': fmt(c.get('message', c['id']), data), 'from': c.get('from')})
        return out

    def check_text(self, logic: dict, text: str, params: dict) -> list[dict]:
        low = text.lower()
        out = []
        for i, ph in enumerate(logic.get('required_phrases') or []):
            if ph.lower() not in low:
                out.append({'id': f'PHRASE-REQ-{i + 1}', 'severity': 'block', 'message': f'Missing required wording: "{ph}"'})
        for i, ph in enumerate(logic.get('forbidden_phrases') or []):
            if ph.lower() in low:
                out.append({'id': f'PHRASE-BAN-{i + 1}', 'severity': 'block', 'message': f'Uses wording that is not allowed: "{ph}"'})
        return out

    # ---------- business ----------
    def _business(self, name, logic, params, depth, ev):
        steps = logic.get('steps') or []
        n = 0
        for st in steps:
            n += 1
            if 'use' in st:
                with_p = {k: self._key(v, params) for k, v in (st.get('with') or {}).items()}
                self.exec(self._key(st['use'], params), depth + 1, with_p)
                continue
            sev = {'kind': 'step', 'skill': name, 'type': 'step', 'depth': depth + 1, 'decisions': []}
            t0 = time.perf_counter()
            if 'take' in st:
                t = st['take']
                src = self.ctx.get(self._key(t['from'], params)) or []
                top = int(self._key(t.get('top', params.get('top', 3)), params))
                self.ctx[self._key(t['into'], params)] = copy.deepcopy(src[:top])
                sev.update(step='take', summary=f"take the top {top} of {len(src)} from '{t['from']}' into '{t['into']}'")
            elif 'rank' in st:
                t = st['rank']
                src = list(self.ctx.get(self._key(t['over'], params)) or [])
                src.sort(key=lambda it: evaluate(t['by'], {**self.ctx, 'item': it, 'params': params}) or 0, reverse=t.get('desc', True))
                self.ctx[self._key(t.get('into', t['over']), params)] = src
                sev.update(step='rank', summary=f"rank {len(src)} by {t.get('label', 'value')} into '{t.get('into', t['over'])}'")
            elif 'set' in st:
                t = st['set']
                src = self.ctx.get(self._key(t['over'], params)) or []
                for it in src:
                    val = evaluate(t['value'], {**self.ctx, 'item': it, 'params': params})
                    it[t['field']] = round(val, 2) if isinstance(val, float) else val
                sev.update(step='set', summary=f"set '{t['field']}' on {len(src)} items ({t.get('label', '')})".replace(' ()', ''))
            elif 'compose' in st:
                t = st['compose']
                text = self.compose(t, params)
                self.ctx[t['into']] = text
                sev.update(step='compose', summary=f"write '{t['into']}' ({len(text.split())} words)")
            elif 'note' in st:
                sev.update(step='manual', summary=f"manual step for a person: {st['note']}")
                self.ctx.setdefault('manual_steps', []).append(st['note'])
            else:
                raise RunError(f'{name}: step {n} has no recognised action')
            sev['ms'] = round((time.perf_counter() - t0) * 1000, 2)
            self.trace.append(sev)
        outs = [o for o in (self.reg.resolve(name)['outputs'] if self.reg.get(name) else []) if o in self.ctx]
        return f"{n} steps; produced {', '.join(outs) or 'no outputs'}"

    def compose(self, t: dict, params: dict) -> str:
        data = {**self.ctx, 'params': params}
        parts = []
        if t.get('intro'):
            parts.append(fmt(t['intro'], data))
        if t.get('each'):
            for i, it in enumerate(self.ctx.get(t['each']) or []):
                line = fmt(t['line'], {**data, 'item': it, 'n': i + 1})
                if it.get('flags') and t.get('flag_line'):
                    line += fmt(t['flag_line'], {**data, 'item': it, 'flag_text': '; '.join(f['message'] for f in it['flags'])})
                parts.append(line)
            if not self.ctx.get(t['each']) and t.get('empty'):
                parts.append(fmt(t['empty'], data))
        for cond in t.get('when') or []:
            if evaluate(cond['if'], data):
                parts.append(fmt(cond['say'], data))
        if t.get('outro'):
            parts.append(fmt(t['outro'], data))
        return '\n\n'.join(p for p in parts if p.strip())


# ---------- skill tests ----------
BASE_ITEM = {'id': 't01', 'name': 'Test manager', 'vehicle': 'SMA', 'asset_class': 'LCV', 'status': 'Recommended', 'min_usd': 250000, 'fee_bps': 40,
             'te': 3.0, 'ir': 0.45, 'style_consistency': 0.9, 'tax_managed': True, 'accepting_new': True, 'track_years': 10, 'risk': 3,
             'esg_score': 60, 'top_holdings': {}, 'overlap_pct': 0.0, 'overlap_names': [], 'adds_to_concentration': False, 'score': 50}


def _assert(result: Any, a: dict) -> tuple[bool, str]:
    from .logic import get_path
    val = get_path(result, a['path']) if 'path' in a else result
    label = a.get('path', 'result')
    if 'equals' in a:
        return val == a['equals'], f"{label} = {val!r}, expected {a['equals']!r}"
    if 'count' in a:
        n = len(val or [])
        return n == a['count'], f'{label} has {n}, expected {a["count"]}'
    if 'min_count' in a:
        n = len(val or [])
        return n >= a['min_count'], f'{label} has {n}, expected at least {a["min_count"]}'
    if 'contains' in a:
        hay = val if isinstance(val, str) else [x.get('name') if isinstance(x, dict) else x for x in (val or [])]
        return a['contains'] in hay, f"{label} {'contains' if a['contains'] in hay else 'does not contain'} {a['contains']!r}"
    if 'not_contains' in a:
        hay = val if isinstance(val, str) else [x.get('name') if isinstance(x, dict) else x for x in (val or [])]
        return a['not_contains'] not in hay, f"{label} {'contains' if a['not_contains'] in hay else 'does not contain'} {a['not_contains']!r}"
    if 'gte' in a:
        return (val or 0) >= a['gte'], f'{label} = {val}, expected ≥ {a["gte"]}'
    if 'lte' in a:
        return (val or 0) <= a['lte'], f'{label} = {val}, expected ≤ {a["lte"]}'
    return False, f'unknown assertion {a}'


def run_tests(reg: Registry, s: Skill) -> list[dict]:
    """Run the examples in a skill's Tests block. Rules and policy tests check one item or one text;
    technical and business tests run the skill on a sample client and check the outputs."""
    out = []
    try:
        r = reg.resolve(s.name, s)
    except Exception as e:  # noqa: BLE001
        return [{'name': 'resolve', 'ok': False, 'detail': str(e)}]
    if r['abstract']:
        return [{'name': t.get('name', f'test {i + 1}'), 'ok': True, 'detail': 'abstract parent: tested through the skills that extend it', 'skipped': True}
                for i, t in enumerate(s.tests)]
    logic = r['logic']
    params = logic.get('params') or {}
    for i, t in enumerate(s.tests):
        name = t.get('name', f'test {i + 1}')
        try:
            ctx = make_context(t.get('client_id', 'henderson'), (t.get('request') or {}).get('asset_class'), (t.get('request') or {}).get('amount'), t.get('client'))
            if t.get('concentration'):
                ctx['concentration'] = t['concentration']
            if t.get('context'):
                ctx.update(copy.deepcopy(t['context']))
            run = Runner(reg)
            run.ctx = ctx
            ctx.setdefault('policy_checks', [])
            expect = t.get('expect') or {}
            if s.type == 'rules' and 'item' in t:
                item = {**BASE_ITEM, **t['item']}
                res = run.apply_rules([x for x in logic.get('rules') or [] if not x.get('disabled')], item, params)
                ok = res['outcome'] == expect.get('outcome', res['outcome'])
                fired = [f['id'] for f in res['fired']]
                if 'rule' in expect:
                    ok = ok and expect['rule'] in fired
                detail = f"{res['outcome']}" + (f" by {', '.join(fired)}" if fired else '')
            elif s.type == 'rules':
                run.trace, run._done = [], set()
                run._rules(s.name, logic, params, 0, {'decisions': []})
                into = logic.get('into') or f'{s.name}_findings'
                found = [f['rule'] for f in ctx[into]['findings']]
                outs = {f['outcome'] for f in ctx[into]['findings']}
                ok = True
                if 'rule' in expect:
                    ok = expect['rule'] in found
                if 'outcome' in expect:
                    ok = ok and (expect['outcome'] in outs if expect['outcome'] != 'pass' else not found)
                detail = ', '.join(found) or 'no rules fired'
            elif s.type == 'policy' and ('item' in t or 'text' in t):
                if 'item' in t:
                    item = {**BASE_ITEM, **t['item']}
                    v = run.check_constraints([c for c in logic.get('constraints') or [] if not c.get('disabled') and c.get('scope', 'each') == 'each'],
                                              {**ctx, 'item': item, 'params': params})
                else:
                    v = run.check_text(logic, t['text'], params)
                ids = [x['id'] for x in v]
                ok = (not v) == expect.get('ok', not v)
                if 'violation' in expect:
                    ok = ok and expect['violation'] in ids
                detail = 'compliant' if not v else 'violates ' + ', '.join(ids)
            else:
                res = Runner(reg).run(s.name, ctx, skill=s)
                if not res['ok']:
                    ok, detail = False, res['error']
                else:
                    checks = [_assert(res['context'], a) for a in (expect if isinstance(expect, list) else [expect]) if a]
                    ok = all(c[0] for c in checks)
                    detail = '; '.join(c[1] for c in checks) or 'ran without errors'
            out.append({'name': name, 'ok': bool(ok), 'detail': detail})
        except Exception as e:  # noqa: BLE001
            out.append({'name': name, 'ok': False, 'detail': f'error: {e}'})
    return out
