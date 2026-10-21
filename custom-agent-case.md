# Why the production advisory agent should be a custom agent, not a configuration of the firm's agent framework

## Bottom line

The firm's framework offers four things:
- a ReAct loop;
- tools, including custom ones;
- skills;
- MCP servers.

That is a good fit for open-ended assistants, where the model decides what to do next and the rules are simple enough to state in a prompt.

This agent is different in three ways:
- **It produces advice.** Its output is recommendations that an advisor reviews, adjusts and decides on before anything reaches a client. That human-in-the-loop step only works if every recommendation is consistent, explained rule by rule, and comes with the evidence the advisor needs to judge it.
- **The rules behind the advice are complex.** There are many interacting thresholds, look-through calculations, tax considerations, precedence between competing recommendations, and policy that differs by profile, state and point in time. Business teams change these rules often.
- **It sits between vendor data and existing tools.** Its inputs come from several vendor and internal sources that must be consistent within a run. Accepted advice has to flow into the firm's existing wealth tools through tracked handoffs.

In the framework, the model's loop decides the order of steps, the gates and which recommendations get made. Here those must be owned by code that we version, test and replay, and by rules that business teams own.

So the recommendation is: **build the agent's control layer custom, and run it on the firm's plumbing.**
- **Custom:**
  - the planner and skill runtime;
  - prerequisites and completion checks;
  - the policy snapshots;
  - the recommendation playbooks;
  - the analytics engine;
  - the vendor-data layer that maps feeds onto the rules' facts;
  - the handoff workflows into existing wealth tools;
  - the advisor review workspace.
- **From the firm:**
  - the LLM gateway;
  - identity and entitlements;
  - secrets;
  - logging and observability;
  - the deployment runtime;
  - the MCP registry.

We also publish our engine as MCP tools, so the framework's other agents can use it.

This is not a choice to build a bigger system. The heavy parts — the engine, policy and playbooks — have to exist either way. The real question is who controls the flow around them. In the proof of concept, the control part (agent loop plus workflow runtime) is about 1,700 lines.

## What we are building

The agent prepares advice for advisors in five areas:
- **Portfolio alignment.** Risk profile alignment, allocation gaps and where new cash should go, and goal-based recommendations, all with tax considerations.
- **Holdings and concentration.** Single stocks including look-through, sectors, single funds and below-investment-grade exposure.
- **Other analyses.** A portfolio deep dive, historical stress scenarios, and alternatives to recently downgraded stocks.
- **Meeting preparation.** The meeting brief draws on the other analyses.
- **Advisor workspace.** The advisor can ask through chat or work directly in a review workspace. Both use the same engine.

Three properties follow from that scope:
1. **Every output is a recommendation for an advisor to review.** The agent never acts on an account. The advisor sees each recommendation, the rule behind it, the figures and the alternatives, then accepts, changes or sets it aside. Recommendations are still subject to best-interest and suitability obligations, supervision, and books and records.
2. **Most of the value is deterministic analysis.** That covers look-through exposures, risk bands, allocation gaps, tax estimates, stress results and goal analysis. The model routes, explains and composes. It never produces a number.
3. **The rules are many, they interact, and they change on business timelines.** Thresholds, model portfolios, stress scenarios, tax assumptions and recommendation classes belong to business teams, not engineers.

## Ten reasons

### 1. The rules are too complex and interdependent to live in prompts

Even the POC's subset of the rules shows the problem.

**Thresholds measured in different ways:**
- A single stock counts as concentrated at 10% of the account, *including* what is held through funds.
- A sector is a concern at 40% of equity *or* 10 points over its benchmark, but only if it is also at least 15% of the account.
- A single fund is flagged at 25%, then put through a separate diversification test.
- The below-investment-grade limit depends on the client's risk profile (8% for Moderate), and illiquid funds are handled differently.
- Allocation drift is flagged at 3 points. Risk bands sit at the midpoints between neighboring profile models.

**Conditions that change the advice:**
- Who directs the holding: a manager-run sleeve gets "discuss with the manager", while an advisor-directed holding gets a specific recommendation.
- Whether cost basis is on file.
- Whether the account is taxable.
- The client's tax bracket: muni alternatives are considered only at 32% and above.
- The annual gain budget: when a recommendation would exceed it, it is phased over several years.

**Precedence between recommendations:**
- When a holding qualifies for more than one recommendation, exactly one should apply. A taxable bond fund with a loss gets the muni alternative, not the loss harvest as well.
- Recommendations about the same stock under manager-run, advisor-directed and held-only-through-funds conditions must not overlap.

**Policy that varies:**
- State tax assumptions.
- New capital market assumptions in preview.
- A new stress scenario in pilot.

In a framework, these rules end up as skill text that the model interprets on each run. Nothing checks that "10% including look-through" was applied rather than "10% of direct holdings". Nothing ensures the precedence holds, and nothing shows that a rule change touched only what it was meant to.

In the custom agent:
- The engine computes every fact the rules refer to: about 70 named facts.
- The rules are evaluated in a defined order, with groups that guarantee one recommendation per holding.
- Each threshold is read from the policy version in force.
- In the POC, v3.1 expresses these as 19 rules in two playbooks, with tests for precedence and for rules that fail validation.

### 2. Human-in-the-loop needs structured, explained recommendations, not approvals of tool calls

- **In a ReAct framework:** human-in-the-loop usually means approving a tool call or reading a generated answer. That is the wrong level for advice. An advisor reviews *recommendations*, so each one needs:
  - a clear headline;
  - the rule and values that triggered it;
  - the figures (amounts, tax impact, phasing);
  - the alternatives considered;
  - the disclosures that apply.
- **In the custom agent:**
  - Every recommendation is a structured item with its rule, its "why" (the condition and the actual values), its evidence and alternatives, and whether it needs action.
  - The advisor works through those items in the workspace.
  - Because items are structured, the advisor's decision on each can be captured: accept, change, or set aside with a reason. That record feeds both supervision and rule improvement.
- **In the POC:** every card shows "Why: playbook rule … fired because …". A decisions panel lists every rule, what it checked and what it fired on.

### 3. The order of steps and the gates must be enforced, not suggested

- **In a ReAct framework:**
  - The model picks the next tool on each turn.
  - A skill is text the model reads and usually follows.
  - "Run the alignment before the meeting brief" or "don't present results until the historical-data disclosure is shown" are instructions, not guarantees.
- **In the custom agent:**
  - The runtime runs a skill's prerequisites before its main step, and skips them only when the skill's `skip_for` conditions are met.
  - It refuses to present a result until the completion checks pass.
  - A failed check is a recorded event, not a model mistake that went unnoticed.
- **In the POC:** `skills/*/skill.json` declares prerequisites, what each skill produces and its checks, and `workflows.py` enforces them. The run trace shows each check, for example "history disclosed".

We could retrofit this as a "gatekeeper" tool the model is told to call. But a model can skip a tool, so the gate is only as strong as the prompt.

### 4. Recommendations must be reproducible

- **In a ReAct framework:** which recommendations appear is decided inside the model's reasoning. Two advisors asking about the same household can get different findings. A review six months later, after the model or the loop has been upgraded, can't reproduce what the advisor saw.
- **In the custom agent:** the same household data and the same policy version always give the same recommendations, in the same order, with the same explanation. Only the narrative wording comes from the model, and the narrative never changes the substance.

That consistency is what lets advisors trust the tool, and what lets supervision review it.

### 5. Policy has to be versioned, pinned to each run and previewed safely

- **In a ReAct framework:** configuration is usually global and live. Changing a threshold, a model portfolio or a scenario changes the advice for everyone at once, and a framework rarely answers "what would this change do?"
- **In the custom agent:**
  - Policy lives in versioned snapshots built from packs.
  - Each run is pinned to one snapshot.
  - A preview pack (for example "add a 2025 tariff stress scenario") can be turned on for one session.
  - "What it changes" lists every household and result that would differ before the pack is released. In the demo, the tariff scenario produces 22 differences.
- **In the POC:** `policy/` holds 11 packs plus `releases.json`. `policy.py` builds the snapshots, and `policy_impact.py` produces the diff.

### 6. Business teams own recommendation classes, with validation, not prompts

- **In a ReAct framework:** the no-code route to a new kind of recommendation is to edit a prompt or a skill's text. Nothing checks that it refers to real data, and nothing stops it changing other recommendations by accident.
- **In the custom agent:**
  - A new class is a JSON rule.
  - It is checked against the catalog of about 70 facts, a fixed set of seven actions and the policy snapshot in force.
  - Unsafe expressions and unknown fields are rejected, and the other rules keep running.
  - Rules move from draft to active to retired, and the playbook names its owner and version.
- **In the POC:** three classes were added as JSON only:
  - review a recently downgraded stock;
  - consider a municipal bond alternative;
  - consider harvesting a loss.

  The tests prove that a class can be added, rejected, drafted or re-prioritized without code.

So the framework's no-code promise is delivered here with guarantees a prompt cannot give.

### 7. Behaviour must be tested in CI and pinned against platform changes

- **In a ReAct framework:**
  - Flows built in a visual tool are hard to diff, code-review or unit test.
  - The platform team upgrades the model, the loop or the skill-selection logic on its own schedule.
  - Each upgrade can silently change which skill is chosen or what is recommended.
- **In the custom agent:**
  - Every rule and calculation has a test.
  - Skill selection is measured against tuning and held-out request sets.
  - Model and prompt changes ship only when those pass.
- **In the POC:**
  - 134 automated tests.
  - A routing evaluation: 75 of 82 requests pick exactly the right skills.
  - The honest held-out score is 11 of 18, and 3 of 8 for the newest skills. That gap is exactly why the evaluation has to sit in our pipeline, gating our releases.

### 8. Supervision needs a complete record, and the product is a review workspace

**The record.** Each run should record:
- the request;
- the skill chosen and why;
- the policy snapshot;
- the analyses run and their inputs;
- the rules that fired and their values;
- the checks and disclosures;
- the recommendations presented;
- the advisor's decision on each.

All of it must be in one record that can be kept and replayed. Framework logs show model and tool calls. They do not know what a rule, a policy version, a disclosure check or an advisor's decision is.

**The workspace.** Advisors review advice in screens built for the job:
- alignment and allocation gaps;
- look-through sector charts;
- stress results;
- downgrade alternatives;
- a Skills & Policy page where business owners read playbooks and preview policy.

Chat is one way in, and it calls the same engine. A framework typically supplies a chat panel. Embedding this workspace means building it custom anyway, then wiring it to an agent we don't control.

**Cost and resilience.** Routine requests run deterministically with no model call: the POC's local planner handles them. The model is used where it adds value — understanding the request, choosing a skill when patterns don't settle it, and writing the narrative. That keeps cost and latency down, and core analysis keeps working through a model or gateway outage.

### 9. Vendor data has to be normalized, consistent within a run, and used within its licence

The advice depends on data from several vendors and internal systems:
- fund holdings for look-through;
- fund research, ratings and analyst reports;
- equity research ratings and downgrades;
- index and benchmark weights;
- market data and history for stress scenarios;
- capital market assumptions;
- cost basis and tax lots;
- client profiles and goals.

Each source has its own schema, identifiers, refresh schedule and licence terms.

- **In a ReAct framework:** each source becomes an MCP server or tool that the model calls when it decides to. That gives access, but none of the following:
  - **Consistency:** one run can mix fund holdings from one date with prices from another, and nothing records which.
  - **Mapping:** identifiers such as tickers, CUSIPs, ISINs and vendor fund ids have to be mapped to one security master. Look-through also needs sector and asset-class mappings so that holdings from different vendors add up.
  - **Gaps and staleness:** for example, a fund whose holdings are a quarter old, or a missing cost basis. The rules need to see these as facts ("cost basis missing on part of the position; that part is excluded"), not as gaps the model papers over.
  - **Licensing:** vendor content often comes with display, attribution and redistribution terms. These depend on who is viewing and where the content appears, for example an advisor screen versus a client-facing brief.
  - **Changing vendors:** with the model reading vendor fields directly, replacing one research vendor means rewriting skills and prompts.
- **In the custom agent:**
  - A data layer maps each vendor feed onto the fact catalog the rules use. Rules say `position.rating` or `position.diversified`, never a vendor's field name, so changing vendors means changing one adapter, not the rules.
  - Each run is pinned to a data as-of time and records which source and date it used for each fact.
  - Gaps and staleness are facts the rules can test.
  - Licence rules control what appears where, and attribution is added automatically.
- **In the POC:** this is the main gap between demo and production. The POC uses illustrative research, fund holdings and ratings behind the same fact catalog the playbooks use. The data requirements document lists each entity, field and source.

### 10. Accepted advice has to flow into the firm's existing wealth tools

After review, the advisor completes the work in the firm's existing tools, not in the agent. Typical next steps:
- turn an accepted allocation recommendation into a proposal or investment policy update in the proposal tool;
- send an accepted portfolio change to the portfolio management or rebalancing tool, where the advisor completes it under that tool's own controls;
- update goals or the plan in the financial planning tool;
- create CRM tasks, notes and follow-ups, and attach the meeting brief;
- send items that need sign-off (for example, a concentrated-position plan) to the supervision or approval queue;
- start forms or service requests.

- **In a ReAct framework:** these become tools the model may call at the end of a conversation. That falls short in several ways:
  - **Lifetime:** the workflow outlives the conversation. A proposal is drafted today, approved tomorrow and discussed next week.
  - **State:** the agent needs to know whether each recommendation was accepted, changed, handed off, approved or completed.
  - **Mapping:** each target tool has its own data model and validation rules.
  - **Safety:** a handoff must happen exactly once, even if a step is retried.
  - **Control:** handoffs must happen only after the advisor's explicit decision, never because the model chose to call a tool.
- **In the custom agent:**
  - Each accepted recommendation becomes a structured handoff: a prefilled payload, or a deep link into the target tool for that household. The advisor completes it there.
  - A small workflow engine tracks each recommendation's status across tools, retries safely, and receives status updates back from the target tools.
  - The loop is closed: the next review knows what was proposed, accepted, approved and done, and does not raise the same recommendation again.
  - The advisor-decision record from reason 2 becomes the start of an auditable chain from recommendation to completed action.
- **In the POC:** recommendations already carry the structured detail a handoff needs: subject, amounts, rule, alternatives and disclosures. The meeting brief already combines results from several skills. Handoff adapters and status tracking are the next step.

These integrations are where most of the long-term value and effort will be. They are also where a generic loop is weakest, because they need durable state and exactly-once handoffs, under the advisor's control.

## What "retrofitting" would actually look like

To make the framework meet the requirements above, we would have to:
- put the engine, rules, policy snapshots, gates and checks into custom tools or MCP servers;
- put a vendor-data layer behind them for mapping, as-of consistency and licensing;
- add a workflow engine for handoffs to the wealth tools;
- build the review workspace separately;
- add our own record store and evaluation pipeline.

What would the framework still contribute? The loop, which is the one thing we cannot hand to the model. Then we would spend effort forcing that loop to behave: prompts that insist on step order, checks after the fact, and two places to look when advice comes out wrong. That gives us all the cost of the custom build plus the constraints of the framework.

## What we take from the firm rather than rebuild

| Firm capability | How the custom agent uses it |
|---|---|
| LLM gateway | Every model call goes through it, with the firm's approved models, content filters, rate limits and usage accounting. There is no direct model access. |
| Identity and entitlements | The advisor's identity and book entitlements decide which households a run can see. |
| Secrets, network and data access | Standard services and approved connectors for portfolio, cost basis, research and CRM data. |
| Enterprise data and vendor feeds | The firm's security master, the vendor feeds it already licenses, and its data platform. Our adapters map these onto the fact catalog; we don't add separate vendor contracts. |
| Existing wealth tools and their APIs | The proposal, portfolio management, planning, CRM and supervision tools, and their APIs or deep links. The agent hands off to them and does not replace them. |
| Workflow or event services | If the firm has a standard workflow or event service, handoff status runs on it. |
| Logging and observability | Our run record is written to the firm's log and monitoring stack, in its standard format. |
| Runtime and deployment | Standard container platform, CI/CD, security scanning and change management. |
| MCP registry | We **consume** firm MCP servers (CRM, research, market data). We **publish** our analyses as MCP tools so other firm agents can call them. Examples: `portfolio_alignment`, `holdings_review`, `stress_test`. |
| Framework skills | Our skills keep a plain SKILL.md, so the framework can list and read them. The enforcement stays in our runtime. |

The custom part is the control layer and the advice logic. Everything generic is the firm's.

## Costs of going custom, and how to contain them

| Risk | Mitigation |
|---|---|
| A team has to own and run it | Keep the harness thin; the POC's control layer is about 1,700 lines. Most of the code is advice logic that would exist in any design. |
| It drifts from firm standards | Use the firm's gateway, identity, logging and runtime from day one, and pass the same architecture and security reviews. |
| Duplicated effort across teams | Publish the analyses and the playbook runtime as MCP tools, so other agents reuse them instead of rebuilding. |
| Key-person risk | Rules live in documented JSON, behaviour is covered by tests and evaluations, and `PLAYBOOKS.md` documents the format. |
| Vendor and tool integrations take longer than expected | Build them behind fixed interfaces (the fact catalog for data, handoff adapters for tools). Start with deep links and prefilled payloads before full API integration, and add tools one at a time. |
| The framework gains these features later | Revisit using the test below. Because the advice logic sits behind MCP, moving the control layer later would not mean rewriting it. |

## A fair test: when the framework would be enough

We would put the agent on the framework if it can do all of the following without custom code in its loop:
1. Evaluate a large, interdependent rule set deterministically, with defined precedence. The rules must be owned by business teams, validated before use, and explained per rule.
2. Present recommendations as structured items for advisor review, and capture the advisor's decision on each.
3. Enforce skill prerequisites and block results until named checks (including disclosures) pass.
4. Pin each run to a versioned policy snapshot, preview a change for one session, and report its impact before release.
5. Run unit tests and held-out routing evaluations in our CI, and pin model and loop versions until they pass.
6. Produce one replayable record per run: skill, policy version, analyses, rules fired and values, checks, recommendations, advisor decisions.
7. Serve a custom review workspace that calls the same engine as the chat, and run routine requests without a model call.
8. Pin each run to a data as-of time across vendor sources. Map vendor fields to stable facts so that changing a vendor doesn't touch the rules, and apply licence rules to what is shown where.
9. Run durable workflows that hand accepted recommendations to the firm's wealth tools only after the advisor's decision, exactly once. Track status back from those tools across days.

If the answer to any of these is no, the agent belongs in custom code running on the firm's plumbing. Today the answer to most of them is typically no.

## Recommendation

1. Build the production agent as a custom service with its own planner, skill runtime, rule playbooks, policy snapshots, vendor-data layer, handoff workflows and advisor review workspace.
2. Run it on the firm's LLM gateway, identity, logging and container platform.
3. Publish its analyses as MCP tools for the rest of the firm.
4. Review the decision every year against the nine-point test above.
