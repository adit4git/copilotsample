---
name: score-candidates
description: Scores eligible candidates 0 to 100 with the CIO's weights for information ratio, fees, tracking error and style consistency. Use after a screen and before client fit.
metadata:
  type: technical
  version: 2.1.0
  owner: CIO Manager Research
  status: approved
  uses: []
  inputs: [eligible]
  outputs: [scored]
  tags: [scoring, selection]
---

# Score candidates with the CIO weights

Each field is scaled across the candidates being compared (lowest 0, highest 1), flipped where lower is better, then weighted. The weights belong to the CIO team; changing them is a new version of this skill, not a code change.

| Factor | Weight | Better |
|---|---|---|
| Information ratio | 35 | higher |
| Fee | 25 | lower |
| Style consistency | 25 | higher |
| Tracking error | 15 | lower |

## Logic

```yaml
op:
  name: weighted_score
  params:
    over: eligible
    into: scored
params:
  weights: {ir: 35, fee_bps: 25, style_consistency: 25, te: 15}
  better: {ir: high, fee_bps: low, style_consistency: high, te: low}
```

## Tests

```yaml
- name: The cheaper, higher-IR manager scores first
  context:
    eligible:
    - {name: Low cost high IR, ir: 0.6, fee_bps: 30, style_consistency: 0.9, te: 3.0}
    - {name: High cost low IR, ir: 0.3, fee_bps: 60, style_consistency: 0.8, te: 4.0}
  expect:
  - {path: scored.0.name, equals: Low cost high IR}
  - {path: scored.0.score, equals: 100.0}
```
