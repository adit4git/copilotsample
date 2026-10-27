"""Turn a plain-English request into a SKILL.md.

Two modes:
- offline (default): a transparent parser. It reads one sentence at a time, maps words to the
  data vocabulary (fields.json) and to skills already in the registry, and reports how it read
  every sentence, including the ones it could not use. Same input, same output.
- claude (when ANTHROPIC_API_KEY is set): Claude drafts the SKILL.md from the same vocabulary
  and catalog. The result goes through exactly the same validation.

It also understands change requests for an existing skill ("raise the SMA track record minimum
to 5 years"): it edits that skill's parameters and returns a new version.
"""
from __future__ import annotations
import copy
import json
import os
import re
from typing import Any
from .logic import evaluate
from .ops import OPS
from .registry import Registry, load_json
from .runtime import BASE_ITEM, make_context
from .skillfile import TYPE_LABEL, Skill, parse, render, ydump

NUMWORDS = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10}
STOP = set('a an the to of for and or with that which who any all each every is are be on in by as at from it its this these those '
           'skill skills create make build write new please should would can will we i me my our their than then when if not no '
           'rule rules policy technical business process called named owner owned'.split())

EXPLICIT_TYPE = re.compile(r'\b(business|technical|policy|compliance|rules?)(?:[- ](?:driven|based))?\s+(?:skill|process|control)\b', re.I)
TYPE_PATTERNS = [
    ('rules', r'\brules?[- ]?(?:driven|based)?\s+skill\b|\bscreen(?:ing)?\s+skill\b|\ba (?:new )?screen\b'),
    ('policy', r'\bpolicy\b|\bcompliance\s+(?:rule|control)\b'),
    ('technical', r'\btechnical\s+skill\b|\bcalculation\b|\bcalculate\b|\bcompute\b|\bweighted score\b'),
    ('business', r'\bbusiness\s+(?:skill|process)\b|\bcapability\b|\bworkflow\b|\bprocess\b'),
]
TYPE_WORDS = {
    'policy': r'\bnever\b|\bmust\b|\balways\b|\bnot allowed\b|\bprohibit|\bdisclos|\bwording\b|\bcompliance\b',
    'rules': r'\bexclude\b|\bflag\b|\bscreen\b|\bremove\b|\breject\b|\babove\b|\bbelow\b|\bthreshold\b|\bfewer than\b|\bless than\b',
    'technical': r'\bcalculat|\bcompute|\bscore\b|\bweight|\bmeasure|\bload\b|\boverlap\b',
    'business': r'\bfirst\b|\bthen\b|\bfinally\b|\bsteps?\b|\bshortlist\b|\bprepare\b',
}
CMP = [  # (pattern, operator, words for the message)
    (r'\b(?:fewer than|less than|lower than|below|under|beneath|shorter than)\b', '<', 'below'),
    (r'\b(?:more than|greater than|higher than|above|over|exceeds?|exceeding|longer than)\b', '>', 'above'),
    (r'\b(?:at least|minimum of|no less than|or more)\b', '>=', 'at least'),
    (r'\b(?:at most|maximum of|no more than|or less|up to)\b', '<=', 'at most'),
]
NEG_EX = r'\b(?:not|isn\'t|aren\'t|without|lacks?|non)\b'


def stem(w: str) -> str:
    w = w.lower().strip(".,;:'\"()")
    if len(w) > 3 and w.endswith('s') and not w.endswith('ss'):
        w = w[:-1]
    return w[:5]


def tokens(text: str) -> list[str]:
    return [stem(t) for t in re.findall(r'[A-Za-z][A-Za-z0-9/&-]*', text.replace('-', ' ')) if t.lower() not in STOP]


def slug(text: str, limit: int = 5) -> str:
    words = [w.lower() for w in re.findall(r'[A-Za-z0-9]+', text) if w.lower() not in STOP]
    return '-'.join(words[:limit]) or 'new-skill'


def split_sentences(text: str) -> list[str]:
    text = re.sub(r'\s+', ' ', text.strip())
    parts = re.split(r'(?<=[.;!?])\s+(?=[A-Z0-9"\'])|;\s*|\n+', text)
    out = []
    for p in parts:  # "never X, and always Y" is two rules
        out += re.split(r',?\s+(?:and|but)\s+(?=(?:always|never|must|do not|don\'t|exclude|flag|remove|reject|block|warn)\b)', p, flags=re.I)
    return [p.strip(' .') for p in out if p.strip(' .')]


class Generator:
    def __init__(self, reg: Registry):
        self.reg = reg
        self.vocab = load_json('fields.json')

    # ---------- matching ----------
    def match_skill(self, phrase: str, want_type: str | None = None, threshold: float = 0.6) -> tuple[str | None, float]:
        ptoks = set(tokens(phrase))
        hint = None
        low = phrase.lower()
        if re.search(r'\b(load|get|fetch|pull)\b', low):
            hint = 'technical'
        elif re.search(r'\b(check|apply|policy|complian|control)', low):
            hint = 'policy'
        elif re.search(r'\bscreen', low):
            hint = 'rules'
        elif re.search(r'\b(write|explain|draft|summar)', low):
            hint = 'business'
        best, best_score = None, 0.0
        for n, s in self.reg.skills.items():
            ntoks = [stem(t) for t in n.split('-')]
            if not ntoks:
                continue
            score = sum(1 for t in ntoks if t in ptoks) / len(ntoks)
            if score == 0:
                continue
            ttoks = set(tokens(s.title))
            score += 0.1 * len(ttoks & ptoks) / max(1, len(ttoks))
            if hint and s.type == hint:
                score += 0.3
            if want_type and s.type != want_type:
                score -= 0.5
            if s.logic.get('abstract'):
                score -= 0.2
            if score > best_score:
                best, best_score = n, score
        return (best, round(best_score, 2)) if best_score >= threshold else (None, round(best_score, 2))

    def find_field(self, sentence: str) -> tuple[str, str, dict] | None:
        """Longest synonym match: returns (scope, field, meta)."""
        low = sentence.lower()
        for scope in ('item', 'concentration', 'client', 'request'):
            best = None
            for f, meta in self.vocab[scope].items():
                for syn in meta['syn']:
                    if re.search(r'(?<![a-z])' + re.escape(syn) + r'(?![a-z])', low):
                        if best is None or len(syn) > best[3]:
                            best = (scope, f, meta, len(syn))
            if best:
                return best[:3]
        return None

    @staticmethod
    def parse_value(sentence: str, unit: str) -> tuple[Any, str] | None:
        low = sentence.lower()
        for w, n in NUMWORDS.items():
            low = re.sub(rf'\b{w}\b', str(n), low)
        if unit == 'usd':
            m = re.search(r'\$?\s*(\d+(?:\.\d+)?)\s*(m|mm|million|k|thousand|bn|billion)?\b', low)
            if not m:
                return None
            v = float(m.group(1)) * {'m': 1e6, 'mm': 1e6, 'million': 1e6, 'k': 1e3, 'thousand': 1e3, 'bn': 1e9, 'billion': 1e9}.get(m.group(2) or '', 1)
            return v, f'${v:,.0f}'
        m = re.search(r'(\d+(?:\.\d+)?)\s*(%|percent|bp|bps|basis points?|years?)?', low)
        if not m:
            return None
        x, u = float(m.group(1)), (m.group(2) or '')
        if unit == 'bp':
            v = x * 100 if u in ('%', 'percent') else x
            return (int(v) if v == int(v) else v), f'{v:g} bp'
        if unit == 'fraction':
            v = x / 100 if (u in ('%', 'percent') or x > 1) else x
            return round(v, 4), f'{v * 100:g}%'
        if unit == 'pct_number':
            return x, f'{x:g}%'
        if unit == 'years':
            return (int(x) if x == int(x) else x), f'{x:g} years'
        return (int(x) if x == int(x) else x), f'{x:g}'

    def condition(self, sentence: str) -> tuple[dict, str, dict] | None:
        """One condition from one sentence: (json-logic, readable text, info)."""
        hit = self.find_field(sentence)
        if not hit:
            return None
        scope, f, meta = hit
        var = {'var': f'{scope}.{f}'}
        low = sentence.lower()
        unit = meta['unit']
        if unit == 'bool':
            neg = any(re.search(NEG_EX + r'[^.]{0,25}?' + re.escape(sy), low) for sy in meta['syn']) or ('closed' in low and f == 'accepting_new')
            return ({'!': var} if neg else var), f"{meta['label']} is {'no' if neg else 'yes'}", {'field': f, 'scope': scope, 'value': not neg, 'unit': unit}
        if unit == 'text':
            vals = meta.get('values') or []
            for v in vals:
                if re.search(rf'\b{v.lower()}\b', low):
                    neg = bool(re.search(NEG_EX, low)) and not re.search(r'\b(never|must not|do not|don\'t|cannot)\b', low)
                    return ({'!=' if neg else '==': [var, v]}), f"{meta['label']} {'is not' if neg else 'is'} {v}", {'field': f, 'scope': scope, 'value': v, 'unit': unit, 'op': '!=' if neg else '=='}
            return None
        op, words = None, ''
        for pat, o, w in CMP:
            if re.search(pat, low):
                op, words = o, w
                break
        val = self.parse_value(sentence, unit)
        if op is None or val is None:
            return None
        return {op: [var, val[0]]}, f"{meta['label']} {words} {val[1]}", {'field': f, 'scope': scope, 'value': val[0], 'unit': unit, 'op': op, 'shown': val[1]}

    def client_condition(self, sentence: str) -> tuple[dict, str] | None:
        low = sentence.lower()
        if re.search(r'\btax[- ]exempt\b|\bnon[- ]taxable\b', low):
            return {'!': {'var': 'client.taxable'}}, 'the client is tax-exempt'
        if re.search(r'\btaxable (?:client|account|household)s?\b|\bclient is taxable\b', low):
            if re.search(r'\b(large|big|significant) (?:embedded |unrealized )?gains\b', low):
                return {'and': [{'var': 'client.taxable'}, {'var': 'client.large_embedded_gains'}]}, 'the client is taxable with large embedded gains'
            return {'var': 'client.taxable'}, 'the client is taxable'
        return None

    def owner(self, text: str) -> str:
        m = re.search(r'(?:owner(?:\s+is)?|owned by|maintained by)\s*:?\s*(?:the\s+)?([A-Za-z][\w&/ -]*?)(?:\s+team)?(?:[.;,]|$)', text, re.I)
        return m.group(1).strip().title() if m and m.group(1).islower() else (m.group(1).strip() if m else '')

    def explicit_name(self, text: str) -> str | None:
        m = re.search(r'\b(?:called|named)\s+["\']?([A-Za-z0-9][A-Za-z0-9 -]*?)["\']?(?=[,.;:]|\s+(?:that|which|to|for|and|with|it|extends?|based)\b|$)', text)
        return slug(m.group(1), 8) if m else None

    def extends(self, text: str, want_type: str | None) -> tuple[str | None, str | None]:
        m = re.search(r'\b(?:extends?|extending|based on|inherits? from|inheriting from|a variant of|a version of|child of|builds? on)\s+(?:the\s+)?([a-z0-9][a-z0-9 /-]*?)(?=[,.;]|\s+(?:and|with|that|to|but|so|which|for)\b|$)', text, re.I)
        if not m:
            return None, None
        name, score = self.match_skill(m.group(1), want_type, 0.5)
        return name, m.group(1)

    def detect_type(self, text: str) -> tuple[str, str]:
        low = text.lower()
        m = EXPLICIT_TYPE.search(low)
        if m:
            w = m.group(1).lower()
            t = {'compliance': 'policy', 'rule': 'rules'}.get(w, w)
            return t, f'the request says "{m.group(0)}"'
        for t, pat in TYPE_PATTERNS:
            if re.search(pat, low):
                return t, f'the request says "{re.search(pat, low).group(0)}"'
        scores = {t: len(re.findall(p, low)) for t, p in TYPE_WORDS.items()}
        t = max(scores, key=lambda k: scores[k])
        if scores[t] == 0:
            return 'business', 'no type words found; defaulting to a business skill'
        return t, f'most of its wording is {t} wording ({scores[t]} cues)'

    # ---------- entry point ----------
    def generate(self, text: str, mode: str = 'offline') -> dict:
        text = text.strip()
        if not text:
            return {'ok': False, 'error': 'Describe the skill in a sentence or two.'}
        if mode == 'claude':
            res = self.with_claude(text)
            if res.get('ok'):
                return res
            fallback = self.generate(text, 'offline')
            fallback['notes'].insert(0, {'sentence': '(Claude mode)', 'reading': f"Claude was not used: {res.get('error')}. Fell back to the offline parser.", 'used': False})
            return fallback
        upd = self.update_request(text)
        if upd:
            return upd
        t, why = self.detect_type(text)
        notes = [{'sentence': '(whole request)', 'reading': f'{TYPE_LABEL[t]} skill, because {why}', 'used': True}]
        return getattr(self, f'_gen_{t}')(text, notes)

    # ---------- common assembly ----------
    def _finish(self, s: Skill, text: str, notes: list, warnings: list, extra_sections: dict | None = None) -> dict:
        base = s.name
        n = 2
        while s.name in self.reg.skills:
            s.name = f'{base}-{n}'
            n += 1
        if s.name != base:
            warnings.append(f"'{base}' already exists, so this is saved as '{s.name}'. To change the existing skill, say \"update {base} …\".")
        acr = {'esg', 'sma', 'smas', 'cio', 'etf', 'etfs', 'ir', 'te', 'us'}
        words = [w.upper() if w in acr else w for w in s.name.split('-')]
        if words and words[0].islower():
            words[0] = words[0].capitalize()
        s.title = s.title or ' '.join(words)
        bullets = '\n'.join(f"- {x['reading']}" for x in notes if x['used'] and not x['reading'].startswith(('skill type', '(')))
        s.prose = (f'{s.prose}\n\n' if s.prose else '') + f'Written from this request:\n\n> {text}\n\nHow the request was read:\n\n{bullets}'
        md = render(s, extra_sections)
        return {'ok': True, 'mode': 'offline', 'skill_md': md, 'name': s.name, 'type': s.type, 'notes': notes, 'warnings': warnings}

    def _desc(self, kind: str, text: str, use: str) -> str:
        first = split_sentences(text)[0]
        first = re.sub(r'^(?:please\s+)?(?:create|make|build|write|add)\s+(?:a|an)\s+(?:new\s+)?', '', first, flags=re.I)
        first = first[0].upper() + first[1:] if first else kind
        d = f'{first.rstrip(".")}. {use}'
        return d[:1000]

    # ---------- rules ----------
    def _gen_rules(self, text: str, notes: list) -> dict:
        warnings: list[str] = []
        parent, said = self.extends(text, 'rules')
        if said and not parent:
            warnings.append(f"Could not find a rules skill matching \"{said}\"; it will not inherit anything.")
        rules, tests = [], []
        for sent in split_sentences(text):
            low = sent.lower()
            if (EXPLICIT_TYPE.search(low) or re.search(r'\b(?:called|named|owner|owned by|extends?|based on|inherits?)\b', low)) and not re.search(r'\b(exclude|flag|remove|reject|drop|warn|block)\b', low):
                notes.append({'sentence': sent, 'reading': 'skill type, name, owner or parent (see metadata)', 'used': True})
                continue
            outcome = 'exclude' if re.search(r'\b(exclude|remove|reject|drop|screen out|rule out|eliminate)\b', low) else \
                'flag' if re.search(r'\b(flag|warn|highlight|mark|note)\b', low) else \
                'block' if re.search(r'\b(block|stop|refer)\b', low) else None
            cond = self.condition(sent)
            if not outcome or not cond:
                notes.append({'sentence': sent, 'reading': 'not used: ' + ('no action word (exclude, flag, block)' if not outcome else
                                                                            'no known field with a comparison, e.g. "fee above 60 bp"'), 'used': False})
                if outcome and not cond:
                    warnings.append(f'"{sent}" has an action but no field the data has. Known fields: ' + ', '.join(m['label'] for m in self.vocab['item'].values()))
                continue
            expr, readable, info = cond
            cc = self.client_condition(sent)
            if cc:
                expr = {'and': [cc[0], expr]}
                readable = f'{cc[1]} and {readable}'
            rid = f'R{len(rules) + 1:02d}'
            fld = info['field']
            shown = '{item.' + fld + (':money' if info['unit'] == 'usd' else (':pct' if info['unit'] == 'fraction' else '')) + '}'
            if info['scope'] == 'item':
                msg = f"{{item.name}}: {self.vocab['item'][fld]['label']} {shown}" + (f" is {info['op'].replace('<=', 'at most').replace('>=', 'at least').replace('<', 'below').replace('>', 'above')} {info.get('shown', '')}" if info['unit'] not in ('bool', 'text') else f' ({readable})')
            else:
                msg = readable[0].upper() + readable[1:]
            rules.append({'id': rid, 'when': expr, 'outcome': outcome, 'message': msg})
            notes.append({'sentence': sent, 'reading': f'{rid}: {outcome} when {readable}', 'used': True})
            if info['scope'] == 'item':
                tests.extend(self._rule_tests(rid, expr, outcome, info, cc))
            if info['field'] in ('overlap_pct', 'score'):
                warnings.append(f"{rid} reads '{fld}', which is only set after {self.vocab['item'][fld].get('computed_by')} runs; place this screen after it.")
            if info['scope'] == 'item' and fld not in BASE_ITEM:
                warnings.append(f"{rid} reads '{fld}', which the approved-list data does not hold")
        if not rules:
            return {'ok': False, 'error': 'No rule could be read. Try: "Exclude managers with fees above 60 bp" or "Flag managers with a track record under 5 years".',
                    'notes': notes, 'warnings': warnings}
        labels = [self.vocab['item'][f]['label'] for f in (self._first_field(r['when']) for r in rules) if f in self.vocab['item']]
        name = self.explicit_name(text) or (slug(' '.join(dict.fromkeys(labels[:2])), 3) + '-screen' if labels else 'new-screen')
        prefix = ''.join(w[0] for w in name.split('-') if w).upper()[:4] or 'R'
        ren = {r['id']: f"{prefix}-{i + 1:02d}" for i, r in enumerate(rules)}
        for r in rules:
            r['id'] = ren[r['id']]
        for t in tests:
            t['expect']['rule'] = ren[t['expect']['rule']]
            t['name'] = t['name'].replace(next(k for k in ren if t['name'].startswith(k + ' ')), t['expect']['rule'], 1)
        for n in notes:
            for k, v in ren.items():
                if n['reading'].startswith(k + ':'):
                    n['reading'] = v + n['reading'][len(k):]
        s = Skill(name=name, description='', type='rules', owner=self.owner(text), status='draft', extends=parent,
                  inputs=[] if parent else ['{params.over}', 'request'], outputs=[] if parent else ['{params.into}'], tags=['screen', 'generated'])
        s.logic = {} if parent else {'over': '{params.over}', 'into': '{params.into}', 'params': {'over': 'candidates', 'into': 'eligible'}}
        s.logic['rules'] = rules
        if parent:
            notes.append({'sentence': '(inheritance)', 'reading': f"extends {parent}: inherits its {len(self.reg.resolve(parent)['logic'].get('rules') or [])} rules and adds {len(rules)}", 'used': True})
        acts = [n['reading'].split(': ', 1)[1] for n in notes if n['used'] and re.match(r'^[A-Z]+-\d\d: ', n['reading'])]
        acts = [a.replace('exclude when ', 'excludes candidates when ').replace('flag when ', 'flags candidates when ').replace('block when ', 'blocks when ').replace('condition when ', 'raises a condition when ') for a in acts]
        s.description = (f"Screen that {'; '.join(acts)}" + (f', on top of every {parent} rule' if parent else '') + '. Use as a screen before scoring candidates.')[:1000]
        base_ok = self._base_passes(s)
        s.tests = ([{'name': 'A typical eligible manager passes', 'item': {}, 'expect': {'outcome': 'pass'}}] if base_ok else []) + tests
        return self._finish(s, text, notes, warnings)

    @staticmethod
    def _first_field(expr) -> str | None:
        from .logic import variables
        for v in sorted(variables(expr)):
            if v.startswith('item.'):
                return v.split('.')[1]
        return None

    def _base_passes(self, s: Skill) -> bool:
        try:
            r = self.reg.resolve(s.name, s)
        except Exception:  # noqa: BLE001
            return False
        ctx = make_context('henderson')
        data = {**ctx, 'item': BASE_ITEM, 'params': r['logic'].get('params') or {}}
        return not any(evaluate(x['when'], data) for x in r['logic'].get('rules') or [] if not x.get('disabled'))

    def _rule_tests(self, rid, expr, outcome, info, cc) -> list[dict]:
        f, op, v, unit = info['field'], info.get('op'), info['value'], info['unit']
        if unit == 'bool':
            bad = {f: v}
        elif unit == 'text':
            bad = {f: v if op == '==' else ('Neutral' if v != 'Neutral' else 'Watch')}
        else:
            step = {'bp': 10, 'years': 1, 'usd': 100000, 'fraction': 0.05, 'pct_number': 1}.get(unit, 1)
            if unit == 'number' and abs(v) < 2:
                step = 0.1
            bad_v = v - step if op in ('<', '<=') else v + step
            bad = {f: round(bad_v, 4) if isinstance(bad_v, float) else bad_v}
        t = {'name': f'{rid} {outcome}s when {f} is {list(bad.values())[0]}', 'item': bad, 'expect': {'outcome': outcome, 'rule': rid}}
        if cc:
            t['client_id'] = 'henderson' if 'taxable' in json.dumps(cc[0]) and '!' not in json.dumps(cc[0]) else 'okonkwo'
        return [t]

    # ---------- policy ----------
    def _gen_policy(self, text: str, notes: list) -> dict:
        warnings: list[str] = []
        cons, req, ban, tests = [], [], [], []
        over = None
        for sent in split_sentences(text):
            low = sent.lower()
            quoted = re.findall(r'["“]([^"”]+)["”]', sent)
            if (EXPLICIT_TYPE.search(low) or re.search(r'\b(?:called|named|owner|owned by)\b', low)) and not re.search(r'\b(never|must|always|do not|don\'t|cannot)\b', low):
                notes.append({'sentence': sent, 'reading': 'skill type, name or owner (see metadata)', 'used': True})
                continue
            if quoted and re.search(r'\b(include|mention|contain|say|state|disclose)\b', low) and not re.search(r'\b(never|not|don\'t)\b', low):
                req += quoted
                notes.append({'sentence': sent, 'reading': 'required wording: ' + ', '.join(f'"{q}"' for q in quoted), 'used': True})
                continue
            if quoted and re.search(r'\b(never|not|don\'t|avoid|ban|prohibit)\b', low):
                ban += quoted
                notes.append({'sentence': sent, 'reading': 'wording not allowed: ' + ', '.join(f'"{q}"' for q in quoted), 'used': True})
                continue
            if re.search(r'\b(?:index|lower[- ]cost|cheaper)\b.*\balternative\b', low):
                cid = f'POL-{len(cons) + 1:02d}'
                cons.append({'id': cid, 'scope': 'run', 'must': {'!!': {'var': 'alternative'}}, 'severity': 'block', 'message': 'The lower-cost alternative must be shown'})
                notes.append({'sentence': sent, 'reading': f'{cid}: block the run unless the lower-cost alternative is present', 'used': True})
                continue
            neg = bool(re.search(r'\b(never|must not|do not|don\'t|cannot|can\'t|not allowed|prohibit|no)\b', low))
            sev = 'warn' if re.search(r'\b(warn|flag|caution)\b', low) else 'block'
            cond = self.condition(sent)
            if not cond:
                notes.append({'sentence': sent, 'reading': 'not used: no field with a measurable condition (e.g. "never shortlist a manager with fees above 80 bp")', 'used': False})
                if re.search(r'\b(must|always|never)\b', low):
                    warnings.append(f'"{sent}" reads like a policy but has nothing measurable; it was left out. A person must check it, or restate it with a field and a number.')
                continue
            expr, readable, info = cond
            cc = self.client_condition(sent)
            if cc:
                expr = {'and': [cc[0], expr]}
                readable = f'{cc[1]} and {readable}'
            cid = f'POL-{len(cons) + 1:02d}'
            positive = re.search(r'\b(must|always|require|only)\b', low) and not neg
            key = 'must' if positive else 'must_not'
            label = self.vocab[info['scope']][info['field']]['label']
            msg = ('{item.name}: ' if info['scope'] == 'item' else '') + (f'{label} must be {readable.split(label, 1)[-1].strip()}' if positive else f'not allowed: {readable}')
            cons.append({'id': cid, key: expr, 'severity': sev, 'message': msg})
            notes.append({'sentence': sent, 'reading': f"{cid}: {'require' if positive else 'never allow'} {readable} ({'removes the item' if sev == 'block' else 'warning only'})", 'used': True})
            if info['scope'] == 'item':
                over = 'ranked'
                bad = self._violating_item(info, positive)
                if bad is not None:
                    tests.append({'name': f'{cid} catches {list(bad.values())[0]}', 'item': bad, 'expect': {'ok': False, 'violation': cid}})
        if not cons and not req and not ban:
            return {'ok': False, 'error': 'No policy could be read. Try: "Never shortlist a manager with fees above 80 bp" or "Always include \\"not a recommendation\\"".',
                    'notes': notes, 'warnings': warnings}
        flds = [self._first_field(c.get('must', c.get('must_not'))) for c in cons if 'scope' not in c]
        lbls = [self.vocab['item'][f]['label'] for f in flds if f in self.vocab['item']]
        auto = (slug(' '.join(dict.fromkeys(lbls[:2])), 3) + '-policy') if lbls else ('wording-policy' if (req or ban) and not cons else 'alternative-shown-policy' if cons else 'new-policy')
        s = Skill(name=self.explicit_name(text) or auto, description='', type='policy',
                  owner=self.owner(text) or 'Compliance', status='draft', tags=['compliance', 'generated'])
        logic: dict = {}
        if over:
            logic['over'] = '{params.over}'
            logic['params'] = {'over': over}
            s.inputs = ['{params.over}']
        if req or ban:
            logic['text_key'] = '{params.text_key}'
            logic.setdefault('params', {})['text_key'] = 'rationale'
            s.inputs.append('{params.text_key}')
            if req:
                logic['required_phrases'] = req
            if ban:
                logic['forbidden_phrases'] = ban
                tests.append({'name': 'Banned wording is caught', 'text': ' '.join(req + [ban[0]]), 'expect': {'ok': False, 'violation': 'PHRASE-BAN-1'}})
            if req:
                tests.append({'name': 'Text with the required wording passes', 'text': ' '.join(req), 'expect': {'ok': True}})
        if cons:
            logic['constraints'] = cons
        s.outputs = ['policy_checks']
        s.logic = logic
        if over and not any(c.get('scope') == 'run' for c in cons):
            tests.insert(0, {'name': 'A typical manager is compliant', 'item': {}, 'expect': {'ok': True}})
        s.tests = tests
        acts = [n['reading'].split(': ', 1)[1] if re.match(r'^POL-\d\d: ', n['reading']) else n['reading'] for n in notes if n['used'] and not n['reading'].startswith(('skill type', '(')) and 'skill, because' not in n['reading']]
        s.description = ('Policy: ' + '; '.join(acts) + '. Use before results are shown to an advisor or client.')[:1000]
        return self._finish(s, text, notes, warnings)

    def _violating_item(self, info: dict, positive: bool) -> dict | None:
        f, op, v, unit = info['field'], info.get('op'), info['value'], info['unit']
        if unit == 'bool':
            return {f: (not v) if positive else v}
        if unit == 'text':
            other = 'Neutral' if v != 'Neutral' else 'Watch'
            return {f: (other if positive else v)} if info.get('op', '==') == '==' else {f: (v if positive else other)}
        step = {'bp': 10, 'years': 1, 'usd': 100000, 'fraction': 0.05, 'pct_number': 1}.get(unit, 1 if abs(v) >= 2 else 0.1)
        inside = v + step if op in ('>', '>=') else v - step
        outside = v - step if op in ('>', '>=') else v + step
        val = outside if positive else inside
        return {f: round(val, 4) if isinstance(val, float) else val}

    # ---------- technical ----------
    def _gen_technical(self, text: str, notes: list) -> dict:
        warnings: list[str] = []
        low = text.lower()
        if re.search(r'\bweight|\bscore\b', low):
            weights, better = {}, {}
            for m in re.finditer(r'([a-z][a-z /-]*?)\s*(?:at|:|=|weight(?:ed)? of)?\s*(\d+(?:\.\d+)?)\s*(?:%|percent|points?)?(?:\s*\(?\s*(higher|lower)(?: is better)?\)?)?', low):
                phrase, w = m.group(1), float(m.group(2))
                hit = None
                for f, meta in self.vocab['item'].items():
                    for syn in sorted(meta['syn'], key=len, reverse=True):
                        if re.search(r'(?<![a-z])' + re.escape(syn) + r'(?![a-z])', phrase.split(',')[-1].split(' and ')[-1]):
                            hit = f
                            break
                    if hit:
                        break
                if not hit or meta.get('unit') in ('text', 'bool'):
                    continue
                weights[hit] = int(w) if w == int(w) else w
                after = low[m.end():m.end() + 25]
                dirn = m.group(3) or (re.search(r'^\W*(higher|lower)', after).group(1) if re.search(r'^\W*(higher|lower)', after) else None)
                better[hit] = 'low' if (dirn == 'lower' or (dirn is None and hit in ('fee_bps', 'te', 'risk', 'overlap_pct'))) else 'high'
                notes.append({'sentence': m.group(0).strip(), 'reading': f"weight {weights[hit]} on {self.vocab['item'][hit]['label']}, {'lower' if better[hit] == 'low' else 'higher'} is better", 'used': True})
            if not weights:
                return {'ok': False, 'error': 'Name the factors and weights, e.g. "information ratio 40%, fees 30% (lower is better), ESG score 30%".', 'notes': notes, 'warnings': warnings}
            if sum(weights.values()) != 100:
                warnings.append(f'The weights add up to {sum(weights.values()):g}, not 100; they are used in proportion.')
            s = Skill(name=self.explicit_name(text) or slug(' '.join(self.vocab['item'][k]['label'] for k in list(weights)[:2]), 4) + '-score', description='', type='technical',
                      owner=self.owner(text) or 'CIO Manager Research', status='draft', inputs=['eligible'], outputs=['scored'], tags=['scoring', 'generated'])
            s.logic = {'op': {'name': 'weighted_score', 'params': {'over': 'eligible', 'into': 'scored'}}, 'params': {'weights': weights, 'better': better}}
            sample = [{k: v for k, v in m.items() if k in ('name', *weights)} for m in load_json('managers.json')['managers'] if m['asset_class'] == 'LCV' and m['vehicle'] == 'SMA'][:3]
            s.tests = [{'name': 'Scores the sample managers 0-100 and sorts them', 'context': {'eligible': sample},
                        'expect': [{'path': 'scored', 'count': len(sample)}, {'path': 'scored.0.score', 'gte': 0}]}]
            s.description = ('Scores candidates 0 to 100 with weights: ' + ', '.join(f"{self.vocab['item'][k]['label']} {v}" for k, v in weights.items())
                             + '. Use as the scoring step in a selection process, in place of score-candidates.')
            notes.append({'sentence': '(operation)', 'reading': 'uses the weighted_score operation from the safe library', 'used': True})
            return self._finish(s, text, notes, warnings)
        for op, (fn, label, ins, outs) in OPS.items():
            key = op.split('_')[0]
            if key in low or label.lower().split()[0] in low:
                s = Skill(name=self.explicit_name(text) or slug(text, 4), description='', type='technical', owner=self.owner(text), status='draft',
                          inputs=list(ins), outputs=list(outs), tags=['generated'])
                s.logic = {'op': {'name': op, 'params': {}}}
                s.description = self._desc(label, text, 'Use as a calculation step inside a business process.')
                notes.append({'sentence': '(operation)', 'reading': f'uses the {op} operation: {label.lower()}', 'used': True})
                return self._finish(s, text, notes, warnings)
        return {'ok': False, 'error': 'Technical skills call one operation from the safe library: ' + '; '.join(f'{k} ({v[1].lower()})' for k, v in OPS.items())
                + '. Describe which one you need, or a weighted score with factors and weights.', 'notes': notes, 'warnings': warnings}

    # ---------- business ----------
    def _gen_business(self, text: str, notes: list) -> dict:
        warnings: list[str] = []
        low = text.lower()
        top = re.search(r'\btop\s+(\d+|' + '|'.join(NUMWORDS) + r')\b', low)
        top_n = int(NUMWORDS.get(top.group(1), top.group(1))) if top else None
        if re.search(r'\b(?:standard|cio|same|usual)\s+(?:selection\s+)?process\b|\bselection process\b', low):
            screen = None
            for m in re.finditer(r'([a-z/ -]+?)\s+screen', low):
                screen, _ = self.match_skill(m.group(0), 'rules', 0.5)
                if screen:
                    break
            vehicles = [v for v, pat in (('SMA', r'\bsmas?\b|separately managed'), ('Fund', r'\bfunds?\b|\betfs?\b')) if re.search(pat, low)]
            params = {}
            if screen:
                params['screen'] = screen
                notes.append({'sentence': '(screen)', 'reading': f'screen: {screen}', 'used': True})
            else:
                warnings.append('No screen named; the parent default (base-eligibility-screen) applies.')
            if vehicles:
                params['vehicles'] = vehicles
                notes.append({'sentence': '(vehicles)', 'reading': 'vehicles: ' + ', '.join(vehicles), 'used': True})
            if top_n:
                params['top'] = top_n
                notes.append({'sentence': '(shortlist size)', 'reading': f'shortlist of {top_n}', 'used': True})
            acw = {'LCV': 'value', 'LCG': 'growth', 'SMID': 'small-mid', 'INTL': 'international', 'MUNI': 'muni'}.get(self._asset_class(low) or '', '')
            auto = '-'.join(x for x in (acw, '-'.join(v.lower() for v in vehicles) or 'investment', 'selection') if x)
            s = Skill(name=self.explicit_name(text) or auto, description='', type='business', owner=self.owner(text) or 'CIO Manager Research',
                      status='draft', extends='investment-selection-process', uses=[screen] if screen else [], tags=['capability', 'selection', 'generated'])
            s.logic = {'params': params}
            notes.insert(1, {'sentence': '(inheritance)', 'reading': 'extends investment-selection-process: inherits its 9 steps and changes only parameters', 'used': True})
            s.tests = [{'name': 'Runs for Henderson and returns a compliant rationale', 'client_id': 'henderson', 'request': {'asset_class': self._asset_class(low) or 'LCV'},
                        'expect': [{'path': 'rationale', 'contains': 'not a recommendation'}]}]
            s.description = (f"Shortlists {', '.join(vehicles) or 'investment'} candidates with the standard CIO selection process"
                             + (f', the {screen} screen' if screen else '') + (f' and the top {top_n}' if top_n else '') + '. Use when an advisor needs candidates for a proposal.')
            return self._finish(s, text, notes, warnings)
        steps, uses = [], []
        body = re.sub(r'^.*?\b(?:first|steps?:|:)\s*', '', text, count=1, flags=re.I) if re.search(r'\bfirst\b|:', text, re.I) else text
        pieces = [p.strip(' .') for p in re.split(r',?\s*\b(?:then|next|after that|finally|and then|followed by)\b\s*|;|\.\s+|\n|→|->', body, flags=re.I) if p and p.strip(' .')]
        for p in pieces:
            pl = p.lower()
            if re.search(r'\b(?:called|named|owner|owned by)\b', pl) and len(pieces) > 1:
                continue
            m = re.search(r'\btop\s+(\d+|' + '|'.join(NUMWORDS) + r')\b', pl)
            if m:
                n = int(NUMWORDS.get(m.group(1), m.group(1)))
                steps.append({'take': {'from': 'ranked', 'top': n, 'into': 'shortlist'}})
                notes.append({'sentence': p, 'reading': f'take the top {n} into the shortlist', 'used': True})
                continue
            name, score = self.match_skill(p)
            if name:
                steps.append({'use': name})
                if name not in uses:
                    uses.append(name)
                notes.append({'sentence': p, 'reading': f'use {name} ({self.reg.get(name).type}), match {score:.2f}', 'used': True})
            else:
                steps.append({'note': p})
                notes.append({'sentence': p, 'reading': 'no matching skill: kept as a manual step for a person', 'used': False})
                warnings.append(f'No skill matches "{p}". It is kept as a manual step; create a skill for it and replace the step.')
        if not any('use' in st for st in steps):
            return {'ok': False, 'error': 'No step matched a skill in the registry. Describe the steps with skill names, e.g. "first load the approved list, then run the fund screen, then score candidates, then take the top 2".',
                    'notes': notes, 'warnings': warnings}
        if any(x in uses for x in ('write-selection-rationale', 'concentrated-position-review')) is False and 'disclosure-policy' not in uses:
            warnings.append('Nothing in this process checks wording; consider adding the disclosure policy before text reaches a client.')
        s = Skill(name=self.explicit_name(text) or slug(text.split('.')[0], 4), description='', type='business', owner=self.owner(text) or 'Advice Methodology',
                  status='draft', uses=uses, inputs=['client', 'request'], tags=(['capability'] if re.search(r'\bcapabilit', low) else []) + ['generated'])
        outs = []
        for st in steps:
            if 'use' in st:
                outs += [o for o in self.reg.resolve(st['use'])['outputs'] if '{' not in o and o != 'policy_checks']
            if 'take' in st:
                outs.append('shortlist')
        s.outputs = list(dict.fromkeys(outs))[-3:]
        s.logic = {'steps': steps}
        s.tests = [{'name': 'Runs end to end for Henderson', 'client_id': 'henderson', 'request': {'asset_class': self._asset_class(low) or 'LCV'},
                    'expect': [{'path': s.outputs[-1], 'min_count': 1}] if s.outputs else []}]
        s.description = ('Process: ' + ' → '.join(st.get('use') or (f"top {st['take']['top']}" if 'take' in st else 'manual step') for st in steps)
                         + '. Use when an advisor needs this done end to end.')[:1000]
        return self._finish(s, text, notes, warnings)

    @staticmethod
    def _asset_class(low: str) -> str | None:
        for ac, pat in (('MUNI', r'\bmuni'), ('LCG', r'\bgrowth\b'), ('LCV', r'\bvalue\b'), ('SMID', r'\bsmall|\bmid'), ('INTL', r'\binternational\b|\bnon-us\b')):
            if re.search(pat, low):
                return ac
        return None

    # ---------- change requests ----------
    PARAM_SYN = {'min_track_years': ['track record', 'track'], 'max_expense_bps': ['expense', 'fee cap', 'fee', 'cost'], 'single_stock_limit': ['single stock', 'single-company', 'single company', 'concentration guideline'],
                 'program_gate': ['program limit', 'program gate', 'eligibility gate'], 'min_multiple': ['times the minimum', 'multiple of the minimum', 'multiple'],
                 'top': ['top', 'shortlist size', 'names', 'candidates'], 'overlap_penalty': ['overlap penalty'], 'concentration_penalty': ['concentration penalty'],
                 'threshold': ['threshold', 'guideline']}

    def update_request(self, text: str) -> dict | None:
        low = text.lower()
        if not re.match(r'\s*(?:please\s+)?(update|change|raise|lower|increase|decrease|reduce|set|tighten|loosen|cut|bump)\b', low):
            return None
        val_m = re.search(r'\bto\s+\$?(\d+(?:\.\d+)?)\s*(%|percent|bp|bps|years?)?', low) or re.search(r'(\d+(?:\.\d+)?)\s*(%|percent|bp|bps|years?)', low)
        cands = []
        for n, s in self.reg.skills.items():
            params = s.logic.get('params') or {}
            for p in params:
                syns = self.PARAM_SYN.get(p, [p.replace('_', ' ')])
                if any(re.search(r'(?<![a-z])' + re.escape(x) + r'(?![a-z])', low) for x in syns):
                    name_score = sum(1 for t in n.split('-') if stem(t) in set(tokens(text))) / len(n.split('-'))
                    cands.append((name_score, n, p))
            for f, w in (params.get('weights') or {}).items():
                if re.search(r'\bweight', low) and any(re.search(r'(?<![a-z])' + re.escape(x) + r'(?![a-z])', low) for x in self.vocab['item'][f]['syn']):
                    cands.append((sum(1 for t in n.split('-') if stem(t) in set(tokens(text))) / len(n.split('-')) + 0.5, n, f'weights.{f}'))
        if not cands or not val_m:
            return None
        cands.sort(key=lambda c: -c[0])
        _, name, pkey = cands[0]
        s = self.reg.get(name)
        x, unit = float(val_m.group(1)), (val_m.group(2) or '')
        old_params = copy.deepcopy(s.logic.get('params') or {})
        if pkey.startswith('weights.'):
            f = pkey.split('.', 1)[1]
            old = old_params['weights'][f]
            new = int(x) if x == int(x) else x
            s2 = parse(s.raw)
            s2.logic['params']['weights'][f] = new
        else:
            old = old_params[pkey]
            if isinstance(old, float) and old < 1 and (unit in ('%', 'percent') or x > 1):
                new = round(x / 100, 4)
            else:
                new = int(x) if x == int(x) else x
            s2 = parse(s.raw)
            s2.logic.setdefault('params', {})[pkey] = new
        from .registry import _bump
        s2.version = _bump(s.version)
        s2.status = 'draft'
        md = _replace_logic(s.raw, s2.logic, s2.version)
        dep = self.reg.dependents(name)
        notes = [{'sentence': text, 'reading': f'change request for {name}: {pkey} {old} → {new}', 'used': True},
                 {'sentence': '(version)', 'reading': f'{s.version} → {s2.version}, status draft until approved', 'used': True},
                 {'sentence': '(impact)', 'reading': f"{len(dep)} skills depend on it: " + ', '.join(d['name'] for d in dep[:8]), 'used': True}]
        return {'ok': True, 'mode': 'offline', 'kind': 'update', 'skill_md': md, 'name': name, 'type': s.type, 'notes': notes, 'warnings': [],
                'change': {'param': pkey, 'old': old, 'new': new}}

    # ---------- Claude ----------
    def with_claude(self, text: str) -> dict:
        key = os.environ.get('ANTHROPIC_API_KEY')
        if not key:
            return {'ok': False, 'error': 'ANTHROPIC_API_KEY is not set'}
        import httpx
        catalog = '\n'.join(f'- {n} ({s.type}): {s.description}' for n, s in self.reg.skills.items())
        examples = '\n\n'.join(self.reg.get(n).raw for n in ('sma-eligibility-screen', 'approved-list-policy', 'score-candidates', 'fund-selection') if self.reg.get(n))
        system = ('You write SKILL.md files for a skill registry. Reply with one SKILL.md and nothing else. Follow the format of the examples exactly: '
                  'frontmatter with name, description and metadata (type, version 1.0.0, owner, status draft, extends, uses, inputs, outputs, tags); '
                  'a title and short prose; a "## Logic" section with one fenced yaml block; a "## Tests" section with one fenced yaml list. '
                  f'Technical skills may only use these operations: {", ".join(OPS)}. Conditions are JSON-Logic. '
                  f'Data fields: {json.dumps({k: list(v) for k, v in self.vocab.items()})}.\n\nRegistry:\n{catalog}\n\nExamples:\n\n{examples}')
        try:
            r = httpx.post('https://api.anthropic.com/v1/messages', timeout=60,
                           headers={'x-api-key': key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'},
                           json={'model': os.environ.get('SKILL_STUDIO_MODEL', 'claude-sonnet-5-5'), 'max_tokens': 4000, 'system': system,
                                 'messages': [{'role': 'user', 'content': text}]})
            r.raise_for_status()
            out = ''.join(b.get('text', '') for b in r.json().get('content', []))
        except Exception as e:  # noqa: BLE001
            return {'ok': False, 'error': f'the request failed ({e.__class__.__name__})'}
        out = re.sub(r'^```(?:markdown|md)?\s*\n|\n```\s*$', '', out.strip())
        try:
            s = parse(out)
        except Exception as e:  # noqa: BLE001
            return {'ok': False, 'error': f'Claude returned text that is not a SKILL.md ({e})'}
        return {'ok': True, 'mode': 'claude', 'skill_md': out, 'name': s.name, 'type': s.type,
                'notes': [{'sentence': '(Claude mode)', 'reading': 'drafted by Claude from the registry catalog, data vocabulary and examples', 'used': True}], 'warnings': []}


def _replace_logic(raw: str, logic: dict, version: str) -> str:
    """Swap the Logic block and the version in an existing SKILL.md, keeping its prose and tests."""
    from .registry import _set_meta
    raw = _set_meta(raw, version=version, status='draft')
    return re.sub(r'(## Logic\s*\n\s*```ya?ml\s*\n)(.*?)(\n```)', lambda m: m.group(1) + ydump(logic) + m.group(3), raw, count=1, flags=re.S)
