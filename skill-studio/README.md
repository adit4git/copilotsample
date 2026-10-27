# Skill Studio: proof of concept

A small, working demonstration of **skills as building blocks**:

- **Four types of skill**, each with its own executor:
  - **technical**: calculations;
  - **business**: processes;
  - **policy**: compliance controls;
  - **rules-driven**: screens.
- **Parent and child skills.**
  - A child inherits its parent's rules or steps.
  - It can add, override or switch off a rule.
  - A whole process can be defined once and reused by setting parameters.
- **Dependencies that deliver a capability.** "Manager and SMA selection" is one request delivered by 13 skills of all four types. "Advisor meeting prep" is a capability made of capabilities.
- **A lightweight registry UI.** Browse skills, see the dependency map and change impact, run a capability with a full trace, and **write a new skill in plain English**. You get back a complete SKILL.md that has already been checked and tested.

The worked example is the CIO's manager and SMA selection process. All managers, clients and figures are fictional, nothing is sent or traded, and the registry is a folder of plain files.

## Run it (about 2 minutes)

```bash
cd skill-studio
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000. Python 3.11 or later. The only outside request is Google Fonts; the page works without it.

**Optional: Claude as the generator.** Set `ANTHROPIC_API_KEY` before starting the server to enable the **Claude** switch on the Create screen. `SKILL_STUDIO_MODEL` picks the model. Claude's draft goes through exactly the same checks as the offline parser's, and if the call fails the app falls back to the offline parser and says so.

## Test it

```bash
python -m pytest -q          # 43 tests, including 5 browser tests if Playwright is installed
pip install playwright && playwright install chromium   # optional: enables tests/test_ui_browser.py
```

## A five-minute demo

1. **Registry → Manager and SMA selection.** It's a business skill and a capability.
   - It *inherits* every step from the abstract parent `investment-selection-process` and only sets three parameters.
   - **Uses** lists the skills it depends on; **Change impact** shows who relies on it.
2. **Registry → SMA eligibility screen → Logic.**
   - Each rule says where it comes from: *own*, *inherited from base-eligibility-screen*, or *overrides* (BASE-03).
   - The fund screen *switches off* BASE-03 instead.
3. **Dependency map.** Click `client-fit-assessment`:
   - green: the 3 skills it needs;
   - red dashed: the 4 skills a change would affect, 3 of them capabilities.
4. **Run a capability → Henderson → Run.** The trace shows each skill in order:
   - the rules exclude three managers;
   - an inherited rule flags a Watch-list manager;
   - the approved-list policy removes it;
   - the disclosure policy checks the rationale.

   Switch the client:
   - **Okonkwo** (tax-exempt): the tax rule no longer fires, but the suitability policy removes Fernhill instead.
   - **Kaplan**: both growth managers carry a warning that they add to the AAPL position.
5. **Create from English → "Rules · child of a parent" → Generate.**
   - Read the sentence-by-sentence interpretation, the five checks and the generated tests.
   - **Save as draft**. It's now in the registry and on the map.
6. **Create from English**, type: *A capability for value SMAs called esg-value-sma-selection that reuses the standard selection process with the ESG SMA screen and the top 3 names.* Generate, save, then **Run** it. Kestrel Point (ESG 48) is now excluded by your new rule.
7. **"Change an existing skill"** (*Raise the SMA track record minimum to 5 years*).
   - This produces version 1.3.0 of the existing skill as a draft and lists the 2 skills it affects.
   - The previous version stays under **History**.
   - Approving `manager-sma-selection` is refused until the changed dependency is approved.

## The skill file

Each skill is a folder with one `SKILL.md` in the standard Agent Skills layout, so the same files can be loaded as skills by Claude.

- **Frontmatter** holds `name` and `description`, plus registry details under `metadata`: type, version, owner, status, `extends`, `uses`, inputs and outputs.
- **The body** is prose for people and for Claude.
- **`## Logic`** is one YAML block the runtime executes.
- **`## Tests`** holds examples that must pass before a skill can be approved.

| Type | Logic block holds | Executor does |
|---|---|---|
| Technical | `op`: one operation from the reviewed library (`app/ops.py`) plus parameters | Calls the operation. Skills never carry their own code, so a generated skill is safe to run |
| Rules-driven | `rules`: id, `when` (JSON-Logic), outcome (exclude, flag, condition, block), message | Applies the rules per item or once per client, and records every decision with its rule id |
| Policy | `constraints` (`must` / `must_not`, severity block or warn) and required or banned wording | Removes items, warns, or blocks the run; checks text such as a rationale |
| Business | `steps`: `use` a skill (with parameters), `take`, `rank`, `set`, `compose`, or a manual `note` | Runs the steps in order and calls sub-skills |

**Inheritance (`extends`)** merges the parent's logic:

- rules and constraints merge by id (same id overrides, `disable: true` switches off);
- parameters merge;
- steps are inherited unless the child defines its own.

`{params.x}` placeholders are filled only after the whole chain is merged, so a child's parameters can change what the parent's steps call.

**Dependencies (`uses`)** are what a skill needs. The registry answers two questions:

- what a skill needs, transitively (`closure`);
- who is affected by changing it (`dependents`).

## Checks before saving (`app/validate.py`)

1. **Format:** name, description (with when-to-use guidance), type, version, owner.
2. **Links:**
   - parents exist and have the same type;
   - dependencies exist;
   - there are no cycles;
   - no abstract or retired skills are used.
3. **Logic:** fits the type; known operations and operators; data fields exist in the vocabulary.
4. **Contract:** for business skills, every step has the data it needs from earlier steps. For example, removing "compare fees" from a process fails because the approved-list policy needs `alternative`.
5. **Tests:** the skill's own examples run and pass.

**Approval** needs zero errors, at least one passing test, and approved dependencies. **Retiring** is refused while another skill still uses the skill.

## How English becomes a skill (`app/generator.py`)

The offline parser is deliberately transparent:

- **Type.** It decides the type from explicit words ("rules skill", "policy", "business process") or from the dominant wording.
- **Sentences.** It reads one sentence at a time, maps words to the data vocabulary (`app/data/fields.json`) and to skills already in the registry, and turns comparisons into JSON-Logic.
- **Unread sentences.** Every sentence it can't use is shown as *not used*, with the reason. It never guesses.
- **Tests.** It writes tests for each rule: a boundary case that must trigger and a typical case that must pass.
- **Change requests.** Requests to change a skill ("raise … to 5 years", "change the fee weight to 30") edit that skill's parameters and produce a new draft version, with impact.

It understands a fixed vocabulary, which is the point of a proof of concept. Claude mode handles freer wording, and the checks are the same either way.

## What is where

| Path | What it does |
|---|---|
| `seed/` | The 19 starting skills: 5 technical, 4 rules-driven, 3 policy, 7 business |
| `registry/` | The working registry, created from `seed/` on first run. **Reset demo** restores it. `SKILL_REGISTRY` points elsewhere |
| `app/skillfile.py` | Read and write SKILL.md |
| `app/registry.py` | Load, inheritance, dependency graph, impact, versions and history |
| `app/runtime.py` | The four executors, run traces, and the skill test runner |
| `app/ops.py` | The library of operations technical skills may call |
| `app/logic.py` | Safe JSON-Logic evaluator and text templates |
| `app/validate.py` | The five layers of checks |
| `app/generator.py` | English to SKILL.md (offline parser; optional Claude) |
| `app/main.py` | FastAPI routes; interactive docs at `/docs` |
| `app/static/` | The UI: `index.html`, `styles.css`, `app.js` |
| `app/data/` | Illustrative managers, clients, asset classes and the field vocabulary |
| `tests/` | 43 tests |

## API

| Method and path | Does |
|---|---|
| `GET /api/skills` · `GET /api/skills/{name}` | List; full detail with the resolved logic, dependencies, dependents, history and test results |
| `GET /api/skills/{name}/raw` | The SKILL.md text |
| `GET /api/graph` | Nodes and edges (`uses`, `extends`) |
| `POST /api/run` | `{skill, client, asset_class?, amount?}` → trace and outputs |
| `POST /api/generate` | `{text, mode: offline or claude}` → SKILL.md, interpretation notes, checks |
| `POST /api/validate` | `{text}` → the five layers of checks |
| `POST /api/skills` | Save SKILL.md text. A new version keeps the previous one in `history/` |
| `POST /api/skills/{name}/approve` · `/retire` | Change status, with the guards above |
| `GET /api/export` | Every SKILL.md in one plain-text Markdown file |
| `POST /api/reset` | Restore the seed skills |

## Boundaries

- It is a proof of concept. There are no users, roles or sign-off records: approval is one button, and the history is files.
- Technical skills can only call the operations in `app/ops.py`. Adding a new kind of calculation is a code change that people review.
- Business skills compose text from templates. In a production version Claude would draft that prose, and the disclosure policy would check it exactly as it does here.
