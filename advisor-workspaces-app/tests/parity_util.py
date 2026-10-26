"""Helpers to compare Python rule results with the fixture captured from the reference page (tests/fixtures/parity.json)."""
import json
import math
from pathlib import Path

FIXTURE = json.loads((Path(__file__).parent / 'fixtures' / 'parity.json').read_text())


def ser(x, top=True):
    """Serialise like the fixture: households as '@hh:id', holdings as '@h:sym', drop None-valued keys."""
    if isinstance(x, dict):
        if 'holdings' in x and 'id' in x and 'model_w' in x:
            return '@hh:' + x['id']
        if not top and 'lots' in x and 'sym' in x and 'mv' in x:
            return '@h:' + x['sym']
        return {k: ser(v, False) for k, v in x.items() if v is not None and not k.startswith('_')}
    if isinstance(x, (list, tuple)):
        return [ser(v, False) for v in x]
    if isinstance(x, float) and not math.isfinite(x):
        return str(x)
    return x


def diff(a, b, path='', out=None, tol=1e-7):
    """Differences between fixture value a and Python value b. Fixture keys must match; extra Python keys are ignored."""
    out = [] if out is None else out
    if isinstance(a, dict):
        if not isinstance(b, dict):
            out.append(f'{path}: expected object, got {type(b).__name__}'); return out
        for k, v in a.items():
            if k not in b:
                if v in (None, False) or v == []:
                    continue
                out.append(f'{path}.{k}: missing'); continue
            diff(v, b[k], f'{path}.{k}', out, tol)
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            out.append(f'{path}: list length {len(a)} vs {len(b) if isinstance(b, list) else type(b).__name__}'); return out
        for i, (x, y) in enumerate(zip(a, b)):
            diff(x, y, f'{path}[{i}]', out, tol)
    elif isinstance(a, bool) or isinstance(b, bool):
        if bool(a) != bool(b):
            out.append(f'{path}: {a!r} vs {b!r}')
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if (a != b) if tol == 0 else not math.isclose(a, b, rel_tol=tol, abs_tol=1e-6):
            out.append(f'{path}: {a!r} vs {b!r}')
    elif a != b:
        out.append(f'{path}: {a!r} vs {b!r}')
    return out
