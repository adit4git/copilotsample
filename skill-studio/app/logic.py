"""A small, safe JSON-Logic evaluator and a text formatter.

Rules, policy constraints and computed fields are written as JSON-Logic, for example
{"<": [{"var": "item.track_years"}, 3]}. Nothing here executes arbitrary code.
"""
from __future__ import annotations
import re
from typing import Any

MISSING = object()


def get_path(data: Any, path: str, default: Any = None) -> Any:
    """Read a dotted path such as 'item.top_holdings.NVDA' from nested dicts."""
    if path in ('', None):
        return data
    cur = data
    for part in str(path).split('.'):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return default
    return cur


def _num(x: Any) -> float:
    if isinstance(x, bool):
        return float(x)
    if x is None:
        return 0.0
    return float(x)


def _truthy(x: Any) -> bool:
    if isinstance(x, (list, dict, str)):
        return len(x) > 0
    return bool(x)


OPS = {'==', '!=', '>', '>=', '<', '<=', 'and', 'or', '!', '!!', 'not', 'in', 'contains', 'var', 'missing',
       '+', '-', '*', '/', 'min', 'max', 'if', 'count', 'abs'}


def evaluate(rule: Any, data: Any) -> Any:
    """Evaluate a JSON-Logic expression against data."""
    if isinstance(rule, list):
        return [evaluate(r, data) for r in rule]
    if not isinstance(rule, dict) or len(rule) != 1:
        return rule
    op, args = next(iter(rule.items()))
    if op not in OPS:
        raise ValueError(f'Unknown operator: {op}')
    if op == 'var':
        if isinstance(args, list):
            path, default = (args + [None])[:2]
        else:
            path, default = args, None
        return get_path(data, path, default)
    if not isinstance(args, list):
        args = [args]
    if op == 'and':
        out = True
        for a in args:
            out = evaluate(a, data)
            if not _truthy(out):
                return out
        return out
    if op == 'or':
        out = False
        for a in args:
            out = evaluate(a, data)
            if _truthy(out):
                return out
        return out
    if op == 'if':
        for i in range(0, len(args) - 1, 2):
            if _truthy(evaluate(args[i], data)):
                return evaluate(args[i + 1], data)
        return evaluate(args[-1], data) if len(args) % 2 else None
    v = [evaluate(a, data) for a in args]
    if op in ('!', 'not'):
        return not _truthy(v[0])
    if op == '!!':
        return _truthy(v[0])
    if op == '==':
        return v[0] == v[1]
    if op == '!=':
        return v[0] != v[1]
    if op in ('>', '>=', '<', '<='):
        if v[0] is None or v[1] is None:
            return False
        a, b = _num(v[0]), _num(v[1])
        return {'>': a > b, '>=': a >= b, '<': a < b, '<=': a <= b}[op]
    if op == 'in':
        return v[1] is not None and v[0] in v[1]
    if op == 'contains':
        return v[0] is not None and v[1] in v[0]
    if op == 'missing':
        return [p for p in v if get_path(data, p, MISSING) is MISSING]
    if op == 'count':
        return len(v[0] or [])
    if op == 'abs':
        return abs(_num(v[0]))
    if op == '+':
        return sum(_num(x) for x in v)
    if op == '*':
        out = 1.0
        for x in v:
            out *= _num(x)
        return out
    if op == '-':
        return -_num(v[0]) if len(v) == 1 else _num(v[0]) - _num(v[1])
    if op == '/':
        return _num(v[0]) / _num(v[1]) if _num(v[1]) else 0.0
    if op == 'min':
        return min(_num(x) for x in v)
    if op == 'max':
        return max(_num(x) for x in v)
    raise ValueError(op)


def variables(rule: Any) -> set[str]:
    """Every variable path a JSON-Logic expression reads."""
    out: set[str] = set()
    if isinstance(rule, list):
        for r in rule:
            out |= variables(r)
    elif isinstance(rule, dict):
        for op, args in rule.items():
            if op == 'var':
                p = args[0] if isinstance(args, list) else args
                if p:
                    out.add(str(p))
            else:
                out |= variables(args)
    return out


def money(x: Any) -> str:
    x = _num(x)
    a = abs(x)
    s = f'${a / 1e6:.2f}M' if a >= 1e6 else (f'${a / 1e3:.0f}K' if a >= 1e3 else f'${a:,.0f}')
    return ('-' if x < 0 else '') + s


_FIELD = re.compile(r'\{([a-zA-Z_][\w.]*)(?::([^{}]+))?\}')


def fmt(template: str, data: Any) -> str:
    """Fill {path} or {path:spec} placeholders. Specs: money, pct (fraction → %), pct1, bp, or any Python format spec."""
    def rep(m: re.Match) -> str:
        val = get_path(data, m.group(1), None)
        spec = m.group(2)
        if val is None:
            return '—'
        if spec == 'money':
            return money(val)
        if spec == 'pct':
            return f'{_num(val) * 100:.0f}%'
        if spec == 'pct1':
            return f'{_num(val) * 100:.1f}%'
        if spec == 'count':
            return str(len(val)) if isinstance(val, (list, tuple, dict)) else '0'
        if spec == 'list':
            return ', '.join(str(x) for x in val) if isinstance(val, (list, tuple)) else str(val)
        if spec:
            try:
                return format(val, spec)
            except (ValueError, TypeError):
                return str(val)
        if isinstance(val, float):
            return f'{val:g}'
        if isinstance(val, (list, tuple)):
            return ', '.join(str(x) for x in val)
        return str(val)
    return _FIELD.sub(rep, template)


def placeholders(template: str) -> set[str]:
    return {m.group(1) for m in _FIELD.finditer(template or '')}
