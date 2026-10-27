# Skill registry export

19 skills. Each section below is one complete SKILL.md.



<!-- ===== concentration-facts/SKILL.md ===== -->

~~~~markdown
---
name: concentration-facts
description: Finds the client's largest single-company exposure, including look-through into funds, and every name above the guideline. Use before any concentration rule or review.
metadata:
  type: technical
  version: 1.0.0
  owner: Portfolio Analytics
  status: approved
  uses: []
  inputs: [client]
  outputs: [concentration]
  tags: [concentration, look-through]
---

# Concentration facts

Produces facts only: the largest name, its share of the account and the names above the threshold. Rules decide what those facts mean.

## Logic

```yaml
op:
  name: concentration_facts
  params:
    threshold: 0.10
    into: concentration
```

## Tests

```yaml
- name: Henderson's largest name is NVDA
  client_id: henderson
  expect:
  - {path: concentration.top_name, equals: NVDA}
  - {path: concentration.over_threshold, count: 2}
```
~~~~


<!-- ===== fee-comparison/SKILL.md ===== -->

~~~~markdown
---
name: fee-comparison
description: Works out each candidate's annual fee on the amount and compares it with the lower-cost index alternative for the asset class. Use before any shortlist is shown.
metadata:
  type: technical
  version: 1.0.0
  owner: Pricing
  status: approved
  uses: []
  inputs: [request, ranked]
  outputs: [alternative]
  tags: [fees, selection]
---

# Fee comparison with the lower-cost alternative

Adds the annual fee and the extra cost over the index alternative to every candidate, and records the alternative so it can always be shown to the client.

## Logic

```yaml
op:
  name: fee_comparison
  params:
    over: ranked
```

## Tests

```yaml
- name: Henderson's large cap value alternative is the index fund
  client_id: henderson
  context:
    ranked:
    - {name: Test SMA, fee_bps: 45}
  expect:
  - {path: alternative.name, equals: Core Value Index Fund}
  - {path: ranked.0.annual_fee, equals: 23085}
```
~~~~


<!-- ===== load-approved-list/SKILL.md ===== -->

~~~~markdown
---
name: load-approved-list
description: Loads the CIO approved list of managers and funds for one asset class, optionally limited to SMAs or funds. Use as the first step of any manager, SMA or fund selection.
metadata:
  type: technical
  version: 1.0.0
  owner: CIO Manager Research
  status: approved
  uses: []
  inputs: [request]
  outputs: [candidates]
  tags: [data, selection]
---

# Load the approved list

Reads the approved list (managers and funds the CIO's research team covers) and keeps the rows for the asset class in the request. A caller can narrow the vehicles, for example to SMAs only.

This is a technical skill: it names one operation from the safe operations library and gives it parameters. It does not judge anything; screens and policies do that.

## Logic

```yaml
op:
  name: load_dataset
  params:
    dataset: managers
    where: {"and": [{"==": [{"var": "item.asset_class"}, {"var": "request.asset_class"}]}, {"in": [{"var": "item.vehicle"}, {"var": "params.vehicles"}]}]}
    into: candidates
params:
  vehicles: [SMA, Fund]
```

## Tests

```yaml
- name: Large cap value returns SMAs and funds
  client_id: henderson
  request: {asset_class: LCV}
  expect:
  - {path: candidates, count: 10}
- name: Growth list includes the closed manager (screens remove it later)
  client_id: kaplan
  expect:
  - {path: candidates, contains: Larkspur Growth SMA}
```
~~~~


<!-- ===== lookthrough-overlap/SKILL.md ===== -->

~~~~markdown
---
name: lookthrough-overlap
description: Measures how much of each candidate's top holdings the client already owns and whether it adds to the client's concentrated stock. Use inside client-fit checks.
metadata:
  type: technical
  version: 1.0.0
  owner: Portfolio Analytics
  status: approved
  uses: []
  inputs: [client, '{params.over}', concentration]
  outputs: []
  tags: [look-through, client-fit]
---

# Look-through overlap with the client's holdings

Adds three fields to every candidate: the names it shares with the client (above 1% of the account), the share of the candidate's top holdings those names represent, and whether it holds the client's largest single name.

## Logic

```yaml
op:
  name: lookthrough_overlap
  params:
    over: '{params.over}'
    min_client_weight: 0.01
params:
  over: scored
```

## Tests

```yaml
- name: A manager holding NVDA adds to Henderson's concentration
  client_id: henderson
  context:
    concentration: {top_name: NVDA, top_share: 0.229}
    scored:
    - {name: Growth SMA, top_holdings: {NVDA: 0.09, MSFT: 0.08, KO: 0.02}}
  expect:
  - {path: scored.0.adds_to_concentration, equals: true}
  - {path: scored.0.overlap_pct, equals: 0.17}
```
~~~~


<!-- ===== score-candidates/SKILL.md ===== -->

~~~~markdown
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
~~~~


<!-- ===== advisor-meeting-prep/SKILL.md ===== -->

~~~~markdown
---
name: advisor-meeting-prep
description: Prepares an advisor's meeting brief by composing two capabilities - the concentrated position review and the manager and SMA selection - into one checked document. Use before a client review meeting.
metadata:
  type: business
  version: 1.0.0
  owner: Advice Methodology
  status: draft
  uses: [concentrated-position-review, manager-sma-selection, disclosure-policy]
  inputs: [client, request]
  outputs: [position_summary, shortlist, rationale, meeting_brief]
  tags: [capability, meeting]
---

# Advisor meeting preparation

A capability made of capabilities. It shows the deepest dependency chain in the registry: meeting prep → manager selection → selection process → client fit → concentration rules → concentration facts.

It is still a **draft**, to show the approval workflow: drafts can run here but are marked in every trace.

## Logic

```yaml
steps:
- use: concentrated-position-review
- use: manager-sma-selection
- compose:
    into: meeting_brief
    intro: 'Meeting brief: {client.name} - {client.next_meeting}. Prepared for advisor review; illustrative figures, not a recommendation.'
    when:
    - if: {"var": "position_summary"}
      say: '1. Concentration. {position_summary}'
    - if: {"var": "rationale"}
      say: '2. Manager candidates. {rationale}'
    - if: {"var": "manual_steps"}
      say: 'Manual steps outstanding: {manual_steps:list}.'
    outro: 'Checks run: {policy_checks:count} policy checks. Suitability remains the advisor''s determination.'
- use: disclosure-policy
  with: {text_key: meeting_brief}
```

## Tests

```yaml
- name: Henderson brief has both sections
  client_id: henderson
  expect:
  - {path: meeting_brief, contains: 1. Concentration.}
  - {path: meeting_brief, contains: 2. Manager candidates.}
```
~~~~


<!-- ===== client-fit-assessment/SKILL.md ===== -->

~~~~markdown
---
name: client-fit-assessment
description: Adjusts candidate scores for this client - overlap with what the client already owns and whether a candidate adds to the concentrated stock - then ranks them. A sub-skill used by every selection capability.
metadata:
  type: business
  version: 1.2.0
  owner: Advice Methodology
  status: approved
  uses: [concentration-facts, concentration-rules, lookthrough-overlap]
  inputs: [client, scored]
  outputs: [concentration, concentration_findings, ranked]
  tags: [sub-skill, client-fit]
---

# Client fit

A sub-skill: it is not useful alone, but every selection capability needs it. It combines two technical skills and one rules skill, then applies the fit adjustment:

fit score = score − overlap × 100 − 10 if the candidate holds the client's largest name.

## Logic

```yaml
params:
  overlap_penalty: 100
  concentration_penalty: 10
steps:
- use: concentration-facts
- use: concentration-rules
- use: lookthrough-overlap
  with: {over: scored}
- set:
    over: scored
    field: fit_score
    label: score less overlap and concentration penalties
    value: {"-": [{"-": [{"var": "item.score"}, {"*": [{"var": "item.overlap_pct"}, {"var": "params.overlap_penalty"}]}]}, {"if": [{"var": "item.adds_to_concentration"}, {"var": "params.concentration_penalty"}, 0]}]}
- rank: {over: scored, by: {"var": "item.fit_score"}, into: ranked, label: fit score}
```

## Tests

```yaml
- name: Kaplan's AAPL exposure lowers a growth manager that holds AAPL
  client_id: kaplan
  context:
    scored:
    - {name: Holds AAPL, score: 80, top_holdings: {AAPL: 0.07}}
    - {name: No overlap, score: 75, top_holdings: {KO: 0.01}}
  expect:
  - {path: ranked.0.name, equals: No overlap}
```
~~~~


<!-- ===== concentrated-position-review/SKILL.md ===== -->

~~~~markdown
---
name: concentrated-position-review
description: Reviews the client's single-company concentration against the guideline and the program limit and lists the options for advisor review. Use before a meeting or proposal when a name is above 10%.
metadata:
  type: business
  version: 1.0.0
  owner: Advice Methodology
  status: approved
  uses: [concentration-facts, concentration-rules, disclosure-policy]
  inputs: [client]
  outputs: [concentration, concentration_findings, position_summary]
  tags: [capability, concentration]
---

# Concentrated position review

A second capability that reuses skills from the selection process: the same concentration facts, the same concentration rules and the same disclosure policy, pointed at different text.

## Logic

```yaml
steps:
- use: concentration-facts
- use: concentration-rules
- compose:
    into: position_summary
    intro: 'Concentration review for {client.name}: the largest single-company exposure is {concentration.top_name} at {concentration.top_share:pct1} of the account (guideline {concentration.threshold:pct}).'
    when:
    - if: {"var": "concentration_findings.blocked"}
      say: Above the program limit. Refer to the concentrated-stock specialist before any program proposal.
    - if: {"and": [{">": [{"var": "concentration.top_share"}, {"var": "concentration.threshold"}]}, {"!": {"var": "concentration_findings.blocked"}}]}
      say: 'Options for advisor review: gift low-basis lots, a tax-managed SMA transition, direct indexing with the stock excluded, or a staged sale within the {client.gain_budget:money} gain budget.'
    - if: {">": [{"count": {"var": "concentration.over_threshold"}}, 1]}
      say: 'Also above the guideline: {concentration.over_threshold:list}.'
    - if: {"<=": [{"var": "concentration.top_share"}, {"var": "concentration.threshold"}]}
      say: No single company is above the guideline; no concentration action is needed.
    outro: Illustrative planning view for the advisor; not a recommendation.
- use: disclosure-policy
  with: {text_key: position_summary}
```

## Tests

```yaml
- name: Henderson gets options and the second name
  client_id: henderson
  expect:
  - {path: position_summary, contains: Options for advisor review}
  - {path: position_summary, contains: 'MSFT'}
- name: Okonkwo needs no action
  client_id: okonkwo
  expect:
  - {path: position_summary, contains: no concentration action}
```
~~~~


<!-- ===== fund-selection/SKILL.md ===== -->

~~~~markdown
---
name: fund-selection
description: Shortlists mutual funds and ETFs for a client and asset class with the same CIO selection process, using the fund screen. Use when an advisor wants fund candidates or a lower-cost implementation.
metadata:
  type: business
  version: 1.0.0
  owner: CIO Manager Research
  status: approved
  extends: investment-selection-process
  uses: [fund-eligibility-screen]
  inputs: [client, request]
  outputs: [shortlist, alternative, rationale]
  tags: [capability, selection, fund]
---

# Fund selection

The second capability built on the same parent process. Only the screen, the vehicle and the number of names differ. Every other skill is reused unchanged.

## Logic

```yaml
params:
  screen: fund-eligibility-screen
  vehicles: [Fund]
  top: 2
```

## Tests

```yaml
- name: Henderson large cap value funds - the 62 bp fund is excluded
  client_id: henderson
  expect:
  - {path: shortlist, count: 2}
  - {path: shortlist, not_contains: Active Value Fund, institutional class}
```
~~~~


<!-- ===== investment-selection-process/SKILL.md ===== -->

~~~~markdown
---
name: investment-selection-process
description: The CIO's standard selection process as an abstract parent - load the approved list, screen, score, check client fit, compare fees, apply suitability and approved-list policies, shortlist and explain. Extend it for a specific vehicle by naming the screen.
metadata:
  type: business
  version: 2.0.0
  owner: CIO Manager Research
  status: approved
  uses: [load-approved-list, '{params.screen}', score-candidates, client-fit-assessment, fee-comparison, suitability-policy, approved-list-policy, write-selection-rationale]
  inputs: [client, request]
  outputs: [shortlist, alternative, rationale]
  tags: [process, parent]
---

# Investment selection process (parent)

This skill is **abstract**: it defines the process once and cannot run on its own. Each child names its screen and vehicles, and inherits every step, so a change to the process (say, a new policy step) reaches every selection capability at once.

The order matters: policies run on the ranked list *before* the shortlist is taken, so a removed name is replaced by the next one rather than leaving a gap.

## Logic

```yaml
abstract: true
params:
  screen: base-eligibility-screen
  vehicles: [SMA, Fund]
  top: 3
steps:
- use: load-approved-list
  with: {vehicles: '{params.vehicles}'}
- use: '{params.screen}'
- use: score-candidates
- use: client-fit-assessment
- use: fee-comparison
- use: suitability-policy
- use: approved-list-policy
- take: {from: ranked, top: '{params.top}', into: shortlist}
- use: write-selection-rationale
```

## Tests

```yaml
- name: Abstract; tested through manager-sma-selection and fund-selection
```
~~~~


<!-- ===== manager-sma-selection/SKILL.md ===== -->

~~~~markdown
---
name: manager-sma-selection
description: Shortlists SMA managers for a client and asset class using the CIO selection process, the SMA screen, client fit, fee comparison and compliance policies, and drafts the rationale. Use when an advisor needs SMA candidates for a proposal.
metadata:
  type: business
  version: 1.4.0
  owner: CIO Manager Research
  status: approved
  extends: investment-selection-process
  uses: [sma-eligibility-screen]
  inputs: [client, request]
  outputs: [shortlist, alternative, rationale]
  tags: [capability, selection, sma]
---

# Manager and SMA selection

A capability: one request ("SMA candidates for this client in this asset class") delivered by eleven skills of all four types working together.

It adds almost nothing of its own. It extends the parent process and sets three parameters: the SMA screen, SMAs only, and three names.

## Logic

```yaml
params:
  screen: sma-eligibility-screen
  vehicles: [SMA]
  top: 3
```

## Tests

```yaml
- name: Henderson large cap value - three names, none on Watch, none failing the screens
  client_id: henderson
  expect:
  - {path: shortlist, count: 3}
  - {path: shortlist, not_contains: Ashgrove Value Equity SMA}
  - {path: shortlist, not_contains: Fernhill Deep Value SMA}
  - {path: shortlist, not_contains: Alder Peak Value Select SMA}
  - {path: rationale, contains: not a recommendation}
- name: Okonkwo (tax-exempt, Moderate) - Fernhill passes the tax rule but fails suitability
  client_id: okonkwo
  expect:
  - {path: shortlist, not_contains: Fernhill Deep Value SMA}
  - {path: shortlist, count: 3}
```
~~~~


<!-- ===== write-selection-rationale/SKILL.md ===== -->

~~~~markdown
---
name: write-selection-rationale
description: Writes the advisor-facing rationale for a shortlist - why each candidate fits, fees against the lower-cost alternative, flags and disclosures - and checks it against the disclosure policy. A sub-skill used by every selection capability.
metadata:
  type: business
  version: 1.1.0
  owner: Advice Methodology
  status: approved
  uses: [disclosure-policy]
  inputs: [client, request, shortlist, alternative]
  outputs: [rationale]
  tags: [sub-skill, writing]
---

# Write the selection rationale

Composes plain-language text from the run's results, never from memory, then hands it to the disclosure policy. In a production version this is where Claude would draft richer prose; the policy check would stay exactly the same.

## Logic

```yaml
steps:
- compose:
    into: rationale
    intro: 'Shortlist for {client.name} ({client.profile} profile): {request.amount:money} in {request.asset_class_label}. These are illustrative candidates for advisor review, not a recommendation to the client.'
    each: shortlist
    line: '{n}. {item.name} ({item.vehicle}, research {item.status}): fit score {item.fit_score:.0f}. Fee {item.fee_bps} bp, about {item.annual_fee:money} a year, {item.extra_vs_index:money} more than the index alternative. Tracking error {item.te}%, information ratio {item.ir}, {item.track_years}-year track record.'
    flag_line: ' Note: {flag_text}.'
    empty: No candidate passed the screens and policies. Consider the lower-cost alternative or widen the search.
    when:
    - if: {"var": "concentration_findings.findings.0"}
      say: 'Concentration: {concentration.top_name} is {concentration.top_share:pct1} of the account. Candidates that hold it would add to that exposure.'
    outro: 'Lower-cost alternative, always shown: {alternative.name} at {alternative.fee_bps} bp (about {alternative.annual_fee:money} a year). Figures are illustrative; suitability and the final choice remain the advisor''s decision.'
- use: disclosure-policy
  with: {text_key: rationale}
```

## Tests

```yaml
- name: Writes a compliant rationale with an empty shortlist
  client_id: henderson
  context:
    shortlist: []
    alternative: {name: Core Value Index Fund, fee_bps: 4, annual_fee: 2052}
  expect:
  - {path: rationale, contains: No candidate passed}
  - {path: blocked, count: 0}
```
~~~~


<!-- ===== approved-list-policy/SKILL.md ===== -->

~~~~markdown
---
name: approved-list-policy
description: Compliance policy for any shortlist - no Watch or Terminated names, the lower-cost alternative is always shown, and a warning when a candidate adds to the client's concentrated stock. Use before a shortlist leaves the advisor's desk.
metadata:
  type: policy
  version: 2.0.0
  owner: Compliance
  status: approved
  uses: []
  inputs: ['{params.over}', alternative]
  outputs: [policy_checks]
  tags: [compliance, selection]
---

# Approved-list policy

A policy is a control, independent of the screens. The base screen only *flags* Watch-list names; this policy is what keeps them off a shortlist. If a screen is later changed or a new screen forgets a rule, the policy still holds.

- **AP-01 (blocks):** never shortlist a Watch or Terminated name.
- **AP-02 (blocks the run):** the lower-cost alternative must be present.
- **AP-03 (warns):** say so when a candidate holds the client's largest single name.

## Logic

```yaml
over: '{params.over}'
params:
  over: ranked
constraints:
- id: AP-01
  must_not: {"in": [{"var": "item.status"}, ["Watch", "Terminated"]]}
  severity: block
  message: '{item.name} is on the {item.status} list and cannot be shortlisted'
- id: AP-02
  scope: run
  must: {"!!": {"var": "alternative"}}
  severity: block
  message: The lower-cost alternative must be shown with any shortlist
- id: AP-03
  must_not: {"var": "item.adds_to_concentration"}
  severity: warn
  message: '{item.name} holds {concentration.top_name}, which would add to the client''s concentrated position'
```

## Tests

```yaml
- name: A Watch-list manager violates AP-01
  item: {status: Watch}
  expect: {ok: false, violation: AP-01}
- name: Adding to the concentrated name violates AP-03
  item: {adds_to_concentration: true}
  expect: {ok: false, violation: AP-03}
- name: A recommended manager is compliant
  item: {}
  expect: {ok: true}
```
~~~~


<!-- ===== disclosure-policy/SKILL.md ===== -->

~~~~markdown
---
name: disclosure-policy
description: Checks client-facing or advisor-facing text for the required disclosures and for wording that is never allowed (guarantees, promises to outperform). Use on any generated text before it is shown.
metadata:
  type: policy
  version: 1.1.0
  owner: Compliance
  status: approved
  uses: []
  inputs: ['{params.text_key}']
  outputs: [policy_checks]
  tags: [compliance, wording]
---

# Disclosure policy

Works on whatever text the caller names (`text_key`), so the same policy checks a selection rationale, a position summary or a meeting brief. That is reuse through parameters rather than copies.

## Logic

```yaml
text_key: '{params.text_key}'
params:
  text_key: rationale
required_phrases: [illustrative, not a recommendation, advisor]
forbidden_phrases: [guarantee, will outperform, risk-free]
```

## Tests

```yaml
- name: Compliant text passes
  text: Illustrative candidates for advisor review, not a recommendation.
  expect: {ok: true}
- name: A guarantee is not allowed
  text: Illustrative, for the advisor, not a recommendation. We guarantee returns.
  expect: {ok: false, violation: PHRASE-BAN-1}
- name: Missing disclosure is caught
  text: Here are the best managers.
  expect: {ok: false, violation: PHRASE-REQ-1}
```
~~~~


<!-- ===== suitability-policy/SKILL.md ===== -->

~~~~markdown
---
name: suitability-policy
description: Suitability policy - a candidate's risk level must not exceed the client's risk profile, and nothing is proposed while a concentration block stands. Use in every selection and proposal.
metadata:
  type: policy
  version: 1.0.0
  owner: Compliance
  status: approved
  uses: []
  inputs: [client, '{params.over}']
  outputs: [policy_checks]
  tags: [compliance, suitability]
---

# Suitability policy

Applies the client's risk profile to every candidate. Suitability itself remains the advisor's determination; this policy removes candidates that could never be suitable.

## Logic

```yaml
over: '{params.over}'
params:
  over: ranked
constraints:
- id: SUIT-01
  must: {"<=": [{"var": "item.risk"}, {"var": "client.risk_max"}]}
  severity: block
  message: '{item.name}: risk level {item.risk} is above the client''s {client.profile} profile (at most {client.risk_max})'
- id: SUIT-02
  scope: run
  must_not: {"var": "concentration_findings.blocked"}
  severity: block
  message: A concentration block stands; refer to a specialist before proposing
```

## Tests

```yaml
- name: Risk 4 is too high for a Moderate client
  item: {risk: 4}
  expect: {ok: false, violation: SUIT-01}
- name: Risk 3 is suitable for a Moderate client
  item: {risk: 3}
  expect: {ok: true}
```
~~~~


<!-- ===== base-eligibility-screen/SKILL.md ===== -->

~~~~markdown
---
name: base-eligibility-screen
description: The firm-wide eligibility screen every manager or fund must pass. Excludes terminated and closed strategies and minimums above the amount, and flags Watch-list names. Use directly, or extend it for a vehicle-specific screen.
metadata:
  type: rules
  version: 1.3.0
  owner: Investment Policy
  status: approved
  uses: []
  inputs: ['{params.over}', request]
  outputs: ['{params.into}']
  tags: [screen, parent]
---

# Base eligibility screen

The parent screen. Vehicle-specific screens extend it: they inherit these rules, can add their own, override one by giving the same id, or switch one off with `disable: true`.

An excluded candidate leaves the list with the rule that removed it. A flagged candidate stays, carrying the flag to later steps, so a policy can make the final call.

## Logic

```yaml
over: '{params.over}'
into: '{params.into}'
params:
  over: candidates
  into: eligible
rules:
- id: BASE-01
  when: {"==": [{"var": "item.status"}, "Terminated"]}
  outcome: exclude
  message: '{item.name}: terminated by research'
- id: BASE-02
  when: {"!": {"var": "item.accepting_new"}}
  outcome: exclude
  message: '{item.name}: closed to new accounts'
- id: BASE-03
  when: {">": [{"var": "item.min_usd"}, {"var": "request.amount"}]}
  outcome: exclude
  message: '{item.name}: minimum {item.min_usd:money} is above the amount {request.amount:money}'
- id: BASE-04
  when: {"==": [{"var": "item.status"}, "Watch"]}
  outcome: flag
  message: '{item.name} is on the research Watch list'
```

## Tests

```yaml
- name: Terminated is excluded
  item: {status: Terminated}
  expect: {outcome: exclude, rule: BASE-01}
- name: Watch is flagged, not excluded
  item: {status: Watch}
  expect: {outcome: flag, rule: BASE-04}
- name: Closed is excluded
  item: {accepting_new: false}
  expect: {outcome: exclude, rule: BASE-02}
- name: A recommended open manager passes
  item: {}
  expect: {outcome: pass}
```
~~~~


<!-- ===== concentration-rules/SKILL.md ===== -->

~~~~markdown
---
name: concentration-rules
description: Applies the single-company guideline (10%) and the program eligibility gate (50%) to the client's concentration facts. Use in any client-fit check or concentrated-position review.
metadata:
  type: rules
  version: 1.1.0
  owner: Investment Policy
  status: approved
  uses: [concentration-facts]
  inputs: [concentration]
  outputs: [concentration_findings]
  tags: [concentration]
---

# Concentration rules

Runs once for the client, not per candidate. It depends on **concentration-facts**; if those facts are not in the run yet, the runtime runs that skill first.

- A *condition* needs an advisor discussion.
- A *block* stops a program proposal and routes to a specialist.

## Logic

```yaml
into: concentration_findings
params:
  single_stock_limit: 0.10
  program_gate: 0.50
rules:
- id: CONC-01
  when: {">": [{"var": "concentration.top_share"}, {"var": "params.single_stock_limit"}]}
  outcome: condition
  owner: Advisor
  message: '{concentration.top_name} is {concentration.top_share:pct1} of the account, above the {params.single_stock_limit:pct} single-company guideline'
- id: CONC-02
  when: {">": [{"var": "concentration.top_share"}, {"var": "params.program_gate"}]}
  outcome: block
  owner: Specialist
  message: '{concentration.top_name} is above the {params.program_gate:pct} program limit: refer to a specialist'
- id: CONC-03
  when: {">": [{"count": {"var": "concentration.over_threshold"}}, 1]}
  outcome: flag
  owner: Advisor
  message: 'More than one name is above the guideline: {concentration.over_threshold:list}'
```

## Tests

```yaml
- name: Henderson has two names above the guideline
  client_id: henderson
  context:
    concentration: {top_name: NVDA, top_share: 0.229, over_threshold: [NVDA, MSFT]}
  expect: {rule: CONC-03}
- name: Above 50% blocks
  context:
    concentration: {top_name: COST, top_share: 0.583, over_threshold: [COST]}
  expect: {outcome: block, rule: CONC-02}
- name: A diversified client triggers nothing
  context:
    concentration: {top_name: MSFT, top_share: 0.04, over_threshold: []}
  expect: {outcome: pass}
```
~~~~


<!-- ===== fund-eligibility-screen/SKILL.md ===== -->

~~~~markdown
---
name: fund-eligibility-screen
description: Eligibility screen for mutual funds and ETFs. Extends the base screen with a fee cap and switches off the account-minimum rule. Use when shortlisting funds.
metadata:
  type: rules
  version: 1.0.0
  owner: Investment Policy
  status: approved
  extends: base-eligibility-screen
  uses: []
  inputs: []
  outputs: []
  tags: [screen, fund]
---

# Fund eligibility screen

Inherits the base rules, adds a fee cap, and **disables BASE-03**: funds have no account minimum.

## Logic

```yaml
params:
  max_expense_bps: 50
rules:
- id: BASE-03
  disable: true
- id: FUND-01
  when: {"!=": [{"var": "item.vehicle"}, "Fund"]}
  outcome: exclude
  message: '{item.name}: not a fund'
- id: FUND-02
  when: {">": [{"var": "item.fee_bps"}, {"var": "params.max_expense_bps"}]}
  outcome: exclude
  message: '{item.name}: costs {item.fee_bps} bp, above the {params.max_expense_bps} bp cap'
```

## Tests

```yaml
- name: Expensive fund is excluded
  item: {vehicle: Fund, fee_bps: 62}
  expect: {outcome: exclude, rule: FUND-02}
- name: A fund with a high minimum is not excluded (rule switched off)
  item: {vehicle: Fund, min_usd: 99000000, fee_bps: 5}
  expect: {outcome: pass}
```
~~~~


<!-- ===== sma-eligibility-screen/SKILL.md ===== -->

~~~~markdown
---
name: sma-eligibility-screen
description: Eligibility screen for separately managed accounts. Extends the base screen with SMA-only rules for track record and tax management, and a stricter minimum. Use when shortlisting SMA managers.
metadata:
  type: rules
  version: 1.2.0
  owner: Investment Policy
  status: approved
  extends: base-eligibility-screen
  uses: []
  inputs: []
  outputs: []
  tags: [screen, sma]
---

# SMA eligibility screen

Inherits every base rule, then:

- adds SMA-01 to SMA-03;
- **overrides BASE-03**: an SMA needs at least twice its minimum so the manager can build the full portfolio and harvest losses.

## Logic

```yaml
params:
  min_track_years: 3
  min_multiple: 2
rules:
- id: BASE-03
  when: {">": [{"*": [{"var": "item.min_usd"}, {"var": "params.min_multiple"}]}, {"var": "request.amount"}]}
  outcome: exclude
  message: '{item.name}: needs at least {params.min_multiple}× its {item.min_usd:money} minimum to build the full portfolio'
- id: SMA-01
  when: {"!=": [{"var": "item.vehicle"}, "SMA"]}
  outcome: exclude
  message: '{item.name}: not a separately managed account'
- id: SMA-02
  when: {"<": [{"var": "item.track_years"}, {"var": "params.min_track_years"}]}
  outcome: exclude
  message: '{item.name}: {item.track_years}-year track record, under {params.min_track_years} years'
- id: SMA-03
  when: {"and": [{"var": "client.taxable"}, {"var": "client.large_embedded_gains"}, {"!": {"var": "item.tax_managed"}}]}
  outcome: exclude
  message: '{item.name}: not tax-managed, and the client has large embedded gains to move in kind'
```

## Tests

```yaml
- name: Short track record is excluded
  item: {track_years: 2}
  expect: {outcome: exclude, rule: SMA-02}
- name: Not tax-managed is excluded for a taxable client with large gains
  item: {tax_managed: false}
  expect: {outcome: exclude, rule: SMA-03}
- name: Not tax-managed is fine for a tax-exempt client
  client_id: okonkwo
  item: {tax_managed: false}
  expect: {outcome: pass}
- name: The inherited Watch flag still applies
  item: {status: Watch}
  expect: {outcome: flag, rule: BASE-04}
- name: The overridden minimum rule needs twice the minimum
  item: {min_usd: 3000000}
  expect: {outcome: exclude, rule: BASE-03}
```
~~~~
