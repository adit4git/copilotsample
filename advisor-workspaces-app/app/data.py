"""Loads the illustrative data from app/data/*.json into one dictionary, DATA, and holds the per-request State.

All data is fictional. Files:
  market.json      asset classes, correlations, past events, sectors, disclosures, dates
  funds.json       fund shelf and stocks, with look-through
  households.json  six households with holdings and tax lots
  research.json    research rating changes (downgrades)
  cio.json         CIO tactical tilts, tolerance and views; return history
  program.json     fees, strategies, concentration flags and cash needs, pathway thresholds
  content.json     approved materials and objections
  events.json      curated news and events; firm intelligence catalog
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).parent / 'data'
DATA: dict = {}
for _f in sorted(DATA_DIR.glob('*.json')):
    DATA.update(json.loads(_f.read_text(encoding='utf-8')))


def HHS() -> list[dict]:
    """All households, in data order."""
    return list(DATA['households'].values())


def household(hid: str) -> dict:
    return DATA['households'][hid]


@dataclass
class State:
    """Everything the advisor has decided in the page. The API is stateless: the browser sends this with each request.

    disp      assessments and closures by item key: {status, set, reason, closed?: {outcome}}
    promo     firm-intelligence items added as opportunities: key "item:hid" -> {id, hid}
    choice    recorded choices by key; for households "hh:<id>" holds the chosen route id
    o2        proposal settings per household: {amount, turnover, sma, rev, ...}
    handed    households handed off to operations
    th        concentration alert threshold
    intel_run catalog items the advisor analyzed
    clips     number of talking points collected per household
    """
    disp: dict = field(default_factory=dict)
    promo: dict = field(default_factory=dict)
    choice: dict = field(default_factory=dict)
    o2: dict = field(default_factory=dict)
    handed: dict = field(default_factory=dict)
    th: float = 0.10
    intel_run: dict = field(default_factory=dict)
    clips: dict = field(default_factory=dict)
    _memo: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: dict | None) -> 'State':
        d = d or {}
        th = d.get('th')
        return cls(disp=dict(d.get('disp') or {}), promo=dict(d.get('promo') or {}), choice=dict(d.get('choice') or {}),
                   o2={k: dict(v) for k, v in (d.get('o2') or {}).items()}, handed=dict(d.get('handed') or {}),
                   th=DATA['concentration']['threshold'] if th is None else float(th), intel_run=dict(d.get('intel_run') or {}),
                   clips=dict(d.get('clips') or {}))

    def rev(self, hid: str) -> str:
        return (self.o2.get(hid) or {}).get('rev', 'draft')

    def memo(self, key, fn):
        if key not in self._memo:
            self._memo[key] = fn()
        return self._memo[key]
