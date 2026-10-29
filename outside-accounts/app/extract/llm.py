"""Optional second reader: an LLM structures the statement text, and every number it returns is checked against the source.

Off by default. Turned on with OUTSIDE_LLM=1 and ANTHROPIC_API_KEY. The deterministic parser always runs first; the model
is used for rows the parser could not read or flagged, and its output is accepted only when each number appears in
the statement text (so it can re-arrange what is on the page but cannot invent figures).
"""
from __future__ import annotations

import json
import os
import re
import urllib.request

MODEL = os.environ.get('OUTSIDE_LLM_MODEL', 'claude-sonnet-5-5')
PROMPT = """You read brokerage, bank, retirement-plan and annuity statements.
From the statement text below, return JSON only, in this shape:
{"holdings":[{"sym":string|null,"desc":string,"qty":number|null,"price":number|null,"value":number,"cost":number|null}],
 "allocation":[{"label":string,"pct":number}]}
Rules: copy numbers exactly as printed (no rounding, no arithmetic); leave a field null when it is not printed;
skip totals and subtotals; never guess a ticker.

Statement text:
"""


def enabled() -> bool:
    return os.environ.get('OUTSIDE_LLM') == '1' and bool(os.environ.get('ANTHROPIC_API_KEY'))


def call_model(text: str) -> str:
    body = json.dumps({'model': MODEL, 'max_tokens': 2000, 'messages': [{'role': 'user', 'content': PROMPT + text[:20000]}]}).encode()
    req = urllib.request.Request('https://api.anthropic.com/v1/messages', data=body, headers={
        'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.loads(r.read())
    return ''.join(b.get('text', '') for b in out.get('content', []))


def numbers_in(text: str) -> set[float]:
    found = set()
    for t in re.findall(r'\d[\d,]*(?:\.\d+)?', text):
        try:
            found.add(round(float(t.replace(',', '')), 2))
        except ValueError:
            pass
    return found


def grounded(rows: list[dict], text: str) -> tuple[list[dict], list[str]]:
    """Keep only rows whose every number is printed in the statement."""
    ok, dropped = [], []
    nums = numbers_in(text)
    for r in rows:
        vals = [r.get(k) for k in ('qty', 'price', 'value', 'cost') if r.get(k) is not None]
        if r.get('value') is None or any(round(float(v), 2) not in nums for v in vals):
            dropped.append(r.get('desc') or r.get('sym') or '?')
        else:
            ok.append(r)
    return ok, dropped


def refine(statement: dict, caller=call_model) -> dict:
    """Ask the model to read the statement text; merge grounded rows the parser missed."""
    raw = caller(statement['text'])
    m = re.search(r'\{.*\}', raw, re.S)
    data = json.loads(m.group(0)) if m else {'holdings': []}
    rows, dropped = grounded(data.get('holdings', []), statement['text'])
    have = {(h['sym'] or h['desc'] or '').lower() for h in statement['holdings']}
    added = 0
    for r in rows:
        key = (r.get('sym') or r.get('desc') or '').lower()
        if key and key not in have:
            statement['holdings'].append({'row': len(statement['holdings']) + 1, 'sym': r.get('sym'), 'desc': r.get('desc') or r.get('sym'), 'cls_hint': None,
                                          'qty': r.get('qty'), 'price': r.get('price'), 'value': float(r['value']), 'cost': r.get('cost'), 'pct': None,
                                          'confidence': 0.8, 'review': True, 'flags': ['Read by the language model; every number matched the statement text'],
                                          'source': 'llm'})
            added += 1
    if dropped:
        statement['warnings'].append(f'Language model rows dropped because a number was not on the statement: {", ".join(dropped)}')
    statement['method'] += f' + language model ({added} row(s) added)'
    statement['extracted_total'] = round(sum(h['value'] for h in statement['holdings']), 2)
    return statement


CHART_PROMPT = """This image is a chart from an investment statement. Return JSON only:
{"type": "pie" | "bar", "values": [{"label": string, "pct": number}]}
Use the legend or axis labels exactly as printed. Percentages must add up to 100 for a pie."""


def call_vision(png: bytes) -> str:
    import base64
    body = json.dumps({'model': MODEL, 'max_tokens': 800, 'messages': [{'role': 'user', 'content': [
        {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': base64.b64encode(png).decode()}},
        {'type': 'text', 'text': CHART_PROMPT}]}]}).encode()
    req = urllib.request.Request('https://api.anthropic.com/v1/messages', data=body, headers={
        'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.loads(r.read())
    return ''.join(b.get('text', '') for b in out.get('content', []))


def check_chart(chart: dict, png: bytes, caller=call_vision) -> dict:
    """Second reading of a chart the measurement was unsure about (unlabelled slices, odd shapes).

    The model's labels are used only when its numbers agree with the measured ones (within 3 points each) and add up
    to 100 for a pie; otherwise the measured values stand and the disagreement is noted for the advisor."""
    raw = caller(png)
    m = re.search(r'\{.*\}', raw, re.S)
    got = json.loads(m.group(0)).get('values', []) if m else []
    chart = json.loads(json.dumps(chart))
    total = sum(float(v.get('pct', 0)) for v in got)
    if not got or (chart['type'] == 'pie' and abs(total - 100) > 1.5):
        chart['note'] += '; language model reading rejected (does not add up to 100)'
        return chart
    measured = sorted(chart['values'], key=lambda v: -v['pct'])
    model = sorted(got, key=lambda v: -float(v['pct']))
    if len(measured) == len(model) and all(abs(a['pct'] - float(b['pct'])) <= 3 for a, b in zip(measured, model)):
        for a, b in zip(measured, model):
            if a['label'].startswith(('Slice', 'Bar')):
                a['label'] = str(b['label'])
        chart['values'] = measured
        chart['method'] += ' + language model labels'
        chart['confidence'] = max(chart['confidence'], 0.8)
        chart['note'] += '; labels confirmed by the language model, values measured'
    else:
        chart['note'] += '; language model reading disagrees with the measurement by more than 3 points: check by eye'
    return chart
