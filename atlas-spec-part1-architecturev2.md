# Atlas Advisor Console — Rebuild Specification (Part 1 of 3): Architecture, Design & Backend Logic

**This is Part 1 of a 3-part specification.** Together, the three parts contain everything needed to recreate the Atlas Advisor Console exactly as it exists today, with no gaps:

- **Part 1 (this file)** — what the app is, the complete design system (CSS), the data *schema* (field-by-field meaning, but not the raw data itself), the rule-evaluation engine, and the two backend logic files (`services.py`, `main.py`).
- **Part 2** — the complete raw reference data: `households.json`, `fa-and-facts.json`, and the 92-rule `rule-store.json`, referenced by schema in Part 1 §5.
- **Part 3** — frontend architecture, a list of known pitfalls/bugs to avoid reintroducing, the view-by-view UX specification, the complete `index.html` and `app.js`, the testing approach, and a final build/acceptance checklist.

Read all three before starting a rebuild — Part 1 explains *why* things are structured as they are, Part 2 is pure reference data to copy verbatim, Part 3 covers everything a person actually clicks on.

## 1. What this application is

Atlas is a **single-advisor-seat, institutional private-wealth advisor console** — explicitly *not* a retail/consumer investing app. It is the working tool a senior wealth advisor ("Dana Whitfield" or "Marcus Chen" in the seed data) uses at a fictional firm, "Meridian Private Wealth," to:

- See a prioritized "Today" briefing of the book of business (meetings, tax-loss harvesting, concentration drift, cross-sell).
- Browse a **Book of Business**: a table of every household relationship the advisor manages.
- Open a **client deep-dive** for any household: holdings, tax lots, allocation vs. CIO house-view target, and a full **eligibility screen** against every program/overlay/service offering the firm has, each with a machine-readable verdict (ELIGIBLE / INELIGIBLE / NEEDS_REVIEW) and a click-through explanation ("why?") popover showing the exact rule trace.
- Ask a grounded chat assistant ("Ask Atlas") questions about the book, with a live-model call (Anthropic or OpenAI) that gracefully falls back to a deterministic, fully-grounded local answer generator if no API key is configured — the feature must never simply not work.
- Generate a **human-in-the-loop (HITL) meeting-prep draft** for any household with an upcoming meeting, review it, and Approve / Decline / Edit it before it's ever used — nothing is sent or acted on automatically.
- Open a **transition scenario workbench** for any eligible-but-not-yet-enrolled program or tax overlay: a concrete, grounded proposal of what selling/buying/harvesting would be required to transition that specific household into that specific offering, with a full accounting of realized gain, harvest offset, net taxable event, and ongoing estimated tax alpha — or, for offerings that are procedural rather than trade-based (Private Banking, Trust & Estate, Alternatives, etc.), a concrete onboarding checklist instead.
- Work a **Tax Overlay Desk** (ranked harvesting opportunities across the whole book) and a **Cross-Sell Radar** (ranked, eligibility-screened upsell opportunities).

The defining design discipline of this app is: **every number, every eligibility verdict, every draft, every trade proposal is grounded in real, structured household data — nothing is invented by the UI or the LLM.** Where an LLM is used (chat, meeting-prep drafts), it is given the household's real data as context and instructed never to invent facts; a fully deterministic local fallback exists for every LLM-backed feature so the app is 100% functional with zero API keys configured.

## 2. Tech stack

- **Backend:** Python 3.11+, FastAPI, Pydantic v2, served by Uvicorn. No database — all reference data (households, rule store, advisor profiles) is loaded from JSON files on disk at import time into in-memory Python structures. Two small pieces of *mutable* state exist purely in-memory for the session: `DRAFT_STORE` (meeting-prep draft HITL state) and nothing else persists across a server restart — this is a deliberate prototype simplification, called out explicitly in the code.
- **Frontend:** a single-page app with **zero build step** — one plain `<script>`-tag JavaScript file (`app.js`), one CSS file (`styles.css`), one HTML shell (`index.html`). No React, no bundler, no npm dependency at runtime. All rendering is done by building HTML strings and assigning `innerHTML`. Client-side routing is a hand-rolled `state.view` switch, not a router library. This is a deliberate choice: the whole frontend is legible in one pass and has no tooling dependency.
- **HTTP:** the frontend calls a same-origin JSON REST API under `/api/*`; FastAPI also mounts the frontend's static folder at `/static` and serves `index.html` at `/`.
- **Testing:** `pytest` + FastAPI's `TestClient` for the backend (endpoint-level tests); Playwright (Python, Chromium headless) was used throughout development for real-browser verification of every view and interaction. Both are described in full later in this document so the same verification discipline can be reapplied.

## 3. Project file structure

```
atlas-python-app/
├── app/
│   ├── main.py              # FastAPI app: all HTTP endpoints
│   ├── services.py          # business logic: eligibility helpers, NBA ranking,
│   │                        #   chat grounding, draft generation, transition scenarios
│   ├── engine.py            # the 3-valued rule-evaluation kernel
│   ├── data.py               # loads JSON data files into in-memory structures at import time
│   ├── data/
│   │   ├── rule-store.json         # 16 offerings, ~92 rules, 4 composition rules
│   │   ├── households.json         # 17 households across 2 advisors (11 for the seat used in this app: Dana)
│   │   └── fa-and-facts.json       # advisor profiles + misc reference facts
│   └── static/
│       ├── index.html        # the entire HTML shell (sidebar, topbar, one <main id="view">)
│       ├── styles.css        # the entire design system — every visual rule in the app
│       └── app.js            # the entire frontend application logic
├── tests/
│   ├── test_api.py           # FastAPI TestClient endpoint tests
│   └── test_engine.py        # rule-engine unit tests
├── requirements.txt
├── pyproject.toml
└── README.md
```

There is intentionally no `models/`, `routers/`, `components/` subdivision — the app is small enough that one file per genuine responsibility (data loading, rule evaluation, business logic, HTTP surface, one HTML file, one CSS file, one JS file) is the right amount of structure. Do not over-decompose when rebuilding.


---

## 4. Design system

This is an institutional, editorial-feeling design — closer to a serious financial publication than a typical SaaS dashboard. Key choices that must be preserved:

- **Serif for identity, sans for UI.** Household names, the "Good morning" hero greeting, and card titles that name a specific entity use **Newsreader** (a serif). Everything else — labels, buttons, table headers, body copy — uses **Public Sans**. Numbers and tickers use **IBM Plex Mono**. This three-typeface split is load-bearing for the "institutional" feel; do not consolidate to one font.
- **The sidebar and the Today hero card are *always* dark**, in both light and dark theme. Everything else (cards, tables, the main canvas) follows the active light/dark theme. This asymmetry is deliberate — the dark rail anchors the UI the way a private-bank lobby's dark wood paneling does, regardless of the "theme" of the working area.
- **Amber, red, and blue are reserved exclusively as signal colors** — amber for "needs attention / drift," red for sell/decline/loss, blue for a staged/neutral action. Never use them decoratively. The brand teal (`--brand`) is the only color used for primary actions and positive/eligible states.
- **Radii scale in three fixed steps** (`--r-s` 6px, `--r-m` 10px, `--r-l` 14px) — small controls, standard cards/inputs, and large hero/container surfaces, respectively. Don't introduce arbitrary radius values.
- Every one of the CSS custom properties below is used *by name* throughout the JS (both in class-based rules and in a good number of deliberate inline `style="color:var(--brand)"` usages for one-off elements that don't warrant a new class). When rebuilding, define every token exactly as below before writing any component CSS, since the component rules assume they exist.

### 4.1 Complete `app/static/styles.css`

Reproduce this file **exactly**, byte for byte. Nothing in it is accidental — including rules that look redundant (e.g. both a `.u` base rule and inline `style` overrides in some call sites; both are intentional, see §9.9 "Known pitfalls" for why).

```css
/* ============ TOKENS ============ */
:root{
  color-scheme: light dark;
  --canvas:#E9EBEF; --paper:#FFFFFF; --paper-2:#F4F6F8; --inset:#EEF1F4;
  --fg:#161B24; --fg-2:#3F4856; --muted:#6B7482;
  --line:#DBE0E6; --line-2:#E7EAEF;
  --surface-ink:#11151D; --surface-ink-2:#1A2030; --on-ink:#EDEFF3; --on-ink-2:#98A2B2; --on-ink-line:#262E3C;
  --brand:#0C5D51; --brand-2:#0A4A41; --brand-tint:#E1EEEB; --brand-ink:#06382F; --on-brand:#F4FBF9;
  --amber:#9E5E12; --amber-tint:#F5EBDA;
  --red:#A2323E; --red-tint:#F4E2E4;
  --blue:#26548F; --blue-tint:#E4ECF6;
  --gain:#0B7A4B; --loss:#B23A3A;
  --focus:#1f8f7c;
  --r-s:6px; --r-m:10px; --r-l:14px;
  --sh-1:0 1px 2px rgba(20,26,38,.05), 0 1px 1px rgba(20,26,38,.04);
  --sh-2:0 8px 28px -12px rgba(20,26,38,.22);
  --pad: env(safe-area-inset-top,0px);
  --padb: env(safe-area-inset-bottom,0px);
}
:root:not([data-theme="light"]){
  @media (prefers-color-scheme: dark){
    --canvas:#0B0E13; --paper:#141922; --paper-2:#1A202B; --inset:#10151D;
    --fg:#E6E9EF; --fg-2:#B6BDC9; --muted:#818A98;
    --line:#242C39; --line-2:#1E2531;
    --surface-ink:#090C11; --surface-ink-2:#141A24; --on-ink:#E6E9EF; --on-ink-2:#8B94A3; --on-ink-line:#212A38;
    --brand:#3FB7A0; --brand-2:#2F9C88; --brand-tint:#10302A; --brand-ink:#8FE6D5; --on-brand:#04140F;
    --amber:#D79A46; --amber-tint:#2A2214;
    --red:#DE7076; --red-tint:#2C171A;
    --blue:#6FA0DA; --blue-tint:#14202F;
    --gain:#40C48D; --loss:#E0736F;
    --focus:#3FB7A0;
    --sh-1:0 1px 2px rgba(0,0,0,.35);
    --sh-2:0 14px 40px -14px rgba(0,0,0,.6);
  }
}
:root[data-theme="dark"]{
  --canvas:#0B0E13; --paper:#141922; --paper-2:#1A202B; --inset:#10151D;
  --fg:#E6E9EF; --fg-2:#B6BDC9; --muted:#818A98;
  --line:#242C39; --line-2:#1E2531;
  --surface-ink:#090C11; --surface-ink-2:#141A24; --on-ink:#E6E9EF; --on-ink-2:#8B94A3; --on-ink-line:#212A38;
  --brand:#3FB7A0; --brand-2:#2F9C88; --brand-tint:#10302A; --brand-ink:#8FE6D5; --on-brand:#04140F;
  --amber:#D79A46; --amber-tint:#2A2214;
  --red:#DE7076; --red-tint:#2C171A;
  --blue:#6FA0DA; --blue-tint:#14202F;
  --gain:#40C48D; --loss:#E0736F;
  --focus:#3FB7A0;
  --sh-1:0 1px 2px rgba(0,0,0,.35);
  --sh-2:0 14px 40px -14px rgba(0,0,0,.6);
}

*{box-sizing:border-box}
html{ -webkit-text-size-adjust:100%; scroll-padding-top: var(--pad); height:100%;}
body{
  margin:0; height:100%; background:var(--canvas); color:var(--fg);
  font-family:"Public Sans", system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  font-size:14px; line-height:1.5; -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
}
h1,h2,h3,h4{margin:0; font-weight:600;}
.serif{font-family:"Newsreader", Georgia, serif; font-weight:500; letter-spacing:-.01em;}
.mono{font-family:"IBM Plex Mono", ui-monospace, monospace;}
button{font:inherit; color:inherit; cursor:pointer; background:none; border:none;}
a{color:inherit}
::selection{background:var(--brand); color:var(--on-brand)}
.tnum{font-variant-numeric:tabular-nums}
:focus-visible{outline:2px solid var(--focus); outline-offset:2px; border-radius:4px}
@media (prefers-reduced-motion: reduce){ *{animation:none !important; transition:none !important} }

/* ============ APP SHELL ============ */
#app{ display:grid; grid-template-columns:248px 1fr; height:100%; min-height:100%; }
/* Sidebar */
.rail{
  background:var(--surface-ink); color:var(--on-ink); display:flex; flex-direction:column;
  border-right:1px solid var(--on-ink-line);
  padding-top: var(--pad); padding-bottom: var(--padb);
}
.brand{ display:flex; align-items:center; gap:11px; padding:20px 20px 18px; }
.brand .mark{ width:30px; height:30px; border-radius:8px; background:linear-gradient(150deg,var(--brand),var(--brand-2)); display:grid; place-items:center; color:var(--on-brand); flex:0 0 auto; box-shadow: inset 0 0 0 1px rgba(255,255,255,.12);}
.brand .mark svg{width:17px;height:17px}
.brand .name{ font-family:"Newsreader",serif; font-size:19px; line-height:1; letter-spacing:-.01em; }
.brand .sub{ font-size:10.5px; letter-spacing:.14em; text-transform:uppercase; color:var(--on-ink-2); margin-top:3px; }
.nav{ padding:6px 12px; display:flex; flex-direction:column; gap:2px; }
.nav .lbl{ font-size:10.5px; letter-spacing:.13em; color:var(--on-ink-2); padding:14px 10px 6px; }
.nav button{
  display:flex; align-items:center; gap:11px; width:100%; text-align:left; padding:9px 10px; border-radius:8px;
  color:var(--on-ink-2); font-size:13.5px; font-weight:500; transition:background .12s, color .12s;
}
.nav button svg{width:18px;height:18px; opacity:.9}
.nav button .cnt{ margin-left:auto; font-size:11px; font-weight:600; background:rgba(255,255,255,.08); color:var(--on-ink); padding:1px 7px; border-radius:20px; min-width:20px; text-align:center;}
.nav button:hover{ background:rgba(255,255,255,.05); color:var(--on-ink); }
.nav button.on{ background:rgba(255,255,255,.09); color:var(--on-ink); }
.nav button.on .cnt{ background:var(--brand); color:var(--on-brand);}
.rail .foot{ margin-top:auto; padding:14px 16px calc(14px + var(--padb)); border-top:1px solid var(--on-ink-line); display:flex; align-items:center; gap:10px;}
.rail .foot .av{ width:32px;height:32px;border-radius:50%; background:#3a4658; color:var(--on-ink); display:grid;place-items:center; font-weight:600; font-size:12.5px; flex:0 0 auto;}
.rail .foot .who{font-size:12.5px; font-weight:600; color:var(--on-ink)}
.rail .foot .role{font-size:11px; color:var(--on-ink-2)}
.rail .foot .tog{ margin-left:auto; color:var(--on-ink-2); padding:6px; border-radius:8px;}
.rail .foot .tog:hover{ background:rgba(255,255,255,.06); color:var(--on-ink)}

/* Main column */
.main{ min-width:0; overflow:auto; display:flex; flex-direction:column; height:100%;}
.topbar{
  position:sticky; top:0; z-index:20; background:color-mix(in srgb, var(--canvas) 86%, transparent);
  backdrop-filter:saturate(1.4) blur(10px); border-bottom:1px solid var(--line);
  padding: calc(12px + var(--pad)) 26px 12px; display:flex; align-items:center; gap:18px;
}
.topbar .crumb{ font-size:12.5px; color:var(--muted);}
.topbar .crumb b{ color:var(--fg); font-weight:600;}
.search{ margin-left:auto; position:relative; width:min(340px, 40vw);}
.search input{
  width:100%; background:var(--paper); border:1px solid var(--line); border-radius:9px; padding:8px 12px 8px 34px;
  color:var(--fg); font-size:13px; box-shadow:var(--sh-1);
}
.search input::placeholder{color:var(--muted)}
.search svg{ position:absolute; left:10px; top:50%; transform:translateY(-50%); width:16px;height:16px; color:var(--muted)}
.kbd{ position:absolute; right:9px; top:50%; transform:translateY(-50%); font-size:10.5px; color:var(--muted); border:1px solid var(--line); border-radius:5px; padding:1px 5px;}
.content{ padding:26px 26px calc(40px + var(--padb)); max-width:1220px; width:100%; margin:0 auto; }

/* ============ PRIMITIVES ============ */
.panel{ background:var(--paper); border:1px solid var(--line); border-radius:var(--r-l); box-shadow:var(--sh-1); }
.eyebrow{ font-size:11px; letter-spacing:.11em; color:var(--muted); font-weight:600; }
.chip{ display:inline-flex; align-items:center; gap:5px; font-size:11.5px; font-weight:600; padding:2px 8px; border-radius:20px; border:1px solid var(--line); color:var(--fg-2); background:var(--paper-2); white-space:nowrap;}
.chip.enrolled{ background:var(--brand-tint); color:var(--brand-ink); border-color:transparent;}
.chip.eligible{ background:transparent; color:var(--brand); border-color:color-mix(in srgb,var(--brand) 45%, var(--line));}
.chip.na{ opacity:.5;}
.chip.dot::before{content:""; width:6px;height:6px;border-radius:50%; background:currentColor; display:inline-block}
.pill{ display:inline-flex;align-items:center;gap:6px; font-size:11px; font-weight:700; letter-spacing:.02em; padding:3px 9px; border-radius:6px;}
.pill.amber{background:var(--amber-tint); color:var(--amber)}
.pill.red{background:var(--red-tint); color:var(--red)}
.pill.blue{background:var(--blue-tint); color:var(--blue)}
.pill.teal{background:var(--brand-tint); color:var(--brand-ink)}
.pos{color:var(--gain)} .neg{color:var(--loss)}
.btn{ display:inline-flex; align-items:center; gap:7px; font-size:13px; font-weight:600; padding:8px 13px; border-radius:9px; border:1px solid var(--line); background:var(--paper); color:var(--fg); box-shadow:var(--sh-1); transition:.12s;}
.btn:hover{ border-color:color-mix(in srgb,var(--fg) 22%,var(--line)); }
.btn.primary{ background:var(--brand); color:var(--on-brand); border-color:transparent;}
.btn.primary:hover{ background:var(--brand-2);}
.btn.sm{ padding:5px 10px; font-size:12px;}
.btn svg{width:15px;height:15px}
.divider{height:1px;background:var(--line-2); border:none; margin:0;}

/* ============ TODAY / HERO ============ */
.hero{ background:var(--surface-ink); color:var(--on-ink); border-radius:var(--r-l); padding:26px 28px; position:relative; overflow:hidden; border:1px solid var(--on-ink-line);}
.hero::after{ content:""; position:absolute; inset:0; background:
  radial-gradient(120% 140% at 100% 0%, color-mix(in srgb,var(--brand) 30%, transparent) 0%, transparent 46%);
  pointer-events:none;}
.hero .greet{ font-family:"Newsreader",serif; font-size:clamp(26px,4.4vw,38px); line-height:1.04; letter-spacing:-.02em; }
.hero .date{ color:var(--on-ink-2); font-size:12.5px; margin-top:8px; letter-spacing:.02em;}
.hero .brief{ position:relative; margin-top:20px; max-width:62ch; font-size:15px; line-height:1.6; color:#D9DEE7;}
.hero .brief b{ color:#fff; font-weight:600;}
.hero .brief .u{ text-decoration:underline; text-decoration-color:var(--brand); text-underline-offset:3px; text-decoration-thickness:2px; color:#fff; cursor:pointer;}
.hero .stats{ position:relative; display:flex; flex-wrap:wrap; gap:28px; margin-top:22px; padding-top:20px; border-top:1px solid var(--on-ink-line);}
.hero .stat{ flex:1 1 140px; min-width:140px;}
.hero .stat .k{ font-family:"Newsreader",serif; font-size:26px; line-height:1;}
.hero .stat .l{ color:var(--on-ink-2); font-size:11.5px; margin-top:6px; letter-spacing:.03em;}
.hero .agentline{ position:relative; display:inline-flex; align-items:center; gap:8px; margin-top:20px; font-size:12px; color:var(--on-ink-2);}
.hero .agentline .live{ width:7px;height:7px;border-radius:50%; background:var(--brand); box-shadow:0 0 0 0 var(--brand); animation:pulse 2.4s infinite;}
@keyframes pulse{0%{box-shadow:0 0 0 0 color-mix(in srgb,var(--brand) 60%,transparent)}70%{box-shadow:0 0 0 7px transparent}100%{box-shadow:0 0 0 0 transparent}}

.sect-h{ display:flex; align-items:baseline; gap:12px; margin:30px 2px 14px;}
.sect-h h2{ font-family:"Newsreader",serif; font-size:22px; font-weight:500; letter-spacing:-.01em;}
.sect-h .n{ font-size:12px; color:var(--muted);}
.sect-h .more{ margin-left:auto; font-size:12.5px; font-weight:600; color:var(--brand); display:inline-flex; align-items:center; gap:4px;}

/* NBA grid */
.nba-grid{ display:grid; grid-template-columns:1fr 1fr; gap:16px;}
.nba{ background:var(--paper); border:1px solid var(--line); border-radius:var(--r-l); overflow:hidden; box-shadow:var(--sh-1); display:flex; flex-direction:column;}
.nba > .head{ display:flex; align-items:center; gap:11px; padding:15px 17px 13px; border-bottom:1px solid var(--line-2); position:relative;}
.nba > .head::before{ content:""; position:absolute; left:0; top:12px; bottom:12px; width:3px; border-radius:0 3px 3px 0; background:var(--accent);}
.nba .ic{ width:30px;height:30px; border-radius:8px; display:grid; place-items:center; background:var(--accent-tint); color:var(--accent);}
.nba .ic svg{width:17px;height:17px}
.nba .head .t{ font-size:14px; font-weight:600;}
.nba .head .d{ font-size:11.5px; color:var(--muted);}
.nba .head .badge{ margin-left:auto; font-size:11px; font-weight:700; color:var(--accent); background:var(--accent-tint); padding:3px 9px; border-radius:20px;}
.nba .body{ padding:6px 8px 10px; display:flex; flex-direction:column;}
.row{ display:flex; align-items:center; gap:12px; padding:10px 10px; border-radius:10px; transition:background .12s; cursor:pointer; text-align:left; width:100%;}
.row:hover{ background:var(--paper-2);}
.row .lead{ min-width:0; flex:1;}
.row .nm{ font-size:13.5px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.row .meta{ font-size:12px; color:var(--muted); margin-top:2px; display:flex; gap:8px; align-items:center;}
.row .right{ text-align:right; flex:0 0 auto;}
.row .fig{ font-size:13px; font-weight:600; font-variant-numeric:tabular-nums;}
.row .figsub{ font-size:11px; color:var(--muted);}
.avatar{ width:34px;height:34px; border-radius:9px; display:grid; place-items:center; font-weight:600; font-size:12.5px; flex:0 0 auto; color:#fff; font-family:"Newsreader",serif;}
.nba .foot{ margin-top:auto; padding:10px 15px 13px; border-top:1px solid var(--line-2); display:flex; align-items:center; gap:10px; font-size:12px; color:var(--muted);}
.nba .foot .go{ margin-left:auto; color:var(--accent); font-weight:600; display:inline-flex; align-items:center; gap:4px; cursor:pointer;}
.u{ color:var(--brand); cursor:pointer; font-weight:600;}
.u svg, .go svg{ width:11px; height:11px; flex-shrink:0; vertical-align:-1px;}
.acc-meet{ --accent:var(--blue); --accent-tint:var(--blue-tint);}
.acc-drift{ --accent:var(--amber); --accent-tint:var(--amber-tint);}
.acc-cio{ --accent:var(--brand); --accent-tint:var(--brand-tint);}
.acc-deep{ --accent:#6b4a9e; --accent-tint:color-mix(in srgb,#6b4a9e 12%, var(--paper));}
:root[data-theme="dark"] .acc-deep, :root:not([data-theme="light"]) .acc-deep{ --accent:#a98fe0;}

.bar{ height:5px; border-radius:3px; background:var(--inset); overflow:hidden; position:relative;}
.bar > i{ position:absolute; left:0;top:0;bottom:0; border-radius:3px; display:block;}
.mini-th{ position:absolute; top:-2px; bottom:-2px; width:2px; background:var(--fg); opacity:.55;}

/* ============ TABLES ============ */
.tbl-wrap{ overflow-x:auto; border-radius:var(--r-l); border:1px solid var(--line); background:var(--paper); box-shadow:var(--sh-1);}
table{ width:100%; border-collapse:collapse; font-size:13px; min-width:720px;}
thead th{ text-align:left; font-size:11px; letter-spacing:.04em; color:var(--muted); font-weight:600; padding:12px 14px; border-bottom:1px solid var(--line); position:sticky; top:0; background:var(--paper); white-space:nowrap;}
th.num, td.num{ text-align:right; font-variant-numeric:tabular-nums;}
tbody td{ padding:12px 14px; border-bottom:1px solid var(--line-2); vertical-align:middle;}
tbody tr{ cursor:pointer; transition:background .12s;}
tbody tr:hover{ background:var(--paper-2);}
tbody tr:last-child td{ border-bottom:none;}
.cellname{ display:flex; align-items:center; gap:11px;}
.cellname .avatar{ width:30px;height:30px; border-radius:8px; font-size:11.5px;}
.cellname .sub{ font-size:11.5px; color:var(--muted);}
.chips-inline{ display:flex; gap:5px; flex-wrap:wrap;}

.filters{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin-bottom:14px;}
.seg{ display:inline-flex; background:var(--paper); border:1px solid var(--line); border-radius:9px; padding:3px; box-shadow:var(--sh-1);}
.seg button{ padding:6px 12px; font-size:12.5px; font-weight:600; color:var(--muted); border-radius:6px;}
.seg button.on{ background:var(--brand); color:var(--on-brand);}

/* ============ CHAT ============ */
.chatwrap{ display:grid; grid-template-columns: 1fr 288px; gap:18px; align-items:start;}
.chat{ background:var(--paper); border:1px solid var(--line); border-radius:var(--r-l); box-shadow:var(--sh-1); display:flex; flex-direction:column; min-height:420px;}
.chat .ch-head{ display:flex; align-items:center; gap:11px; padding:14px 18px; border-bottom:1px solid var(--line-2);}
.chat .ch-head .mk{ width:30px;height:30px;border-radius:8px; background:linear-gradient(150deg,var(--brand),var(--brand-2)); display:grid;place-items:center; color:var(--on-brand);}
.chat .ch-head .mk svg{width:16px;height:16px}
.chat .ch-head .t{ font-weight:600; font-size:14px;}
.chat .ch-head .s{ font-size:11.5px; color:var(--muted); display:flex; align-items:center; gap:6px;}
.chat .ch-head .s .live{ width:6px;height:6px;border-radius:50%; background:var(--gain);}
.stream{ padding:20px 18px; display:flex; flex-direction:column; gap:16px; min-height:120px;}
.msg{ display:flex; gap:11px; max-width:100%;}
.msg .who{ width:28px;height:28px;border-radius:8px; flex:0 0 auto; display:grid;place-items:center; font-size:11px; font-weight:700;}
.msg.user{ flex-direction:row-reverse;}
.msg.user .who{ background:#38465a; color:#fff;}
.msg.bot .who{ background:linear-gradient(150deg,var(--brand),var(--brand-2)); color:var(--on-brand);}
.bubble{ padding:11px 14px; border-radius:13px; font-size:13.5px; line-height:1.55; max-width:min(78%, 640px);}
.msg.user .bubble{ background:var(--brand); color:var(--on-brand); border-bottom-right-radius:5px;}
.msg.bot .bubble{ background:var(--paper-2); border:1px solid var(--line-2); border-bottom-left-radius:5px;}
.bubble h2{ font-family:"Newsreader",serif; font-size:19px; font-weight:500; letter-spacing:-.01em; margin:0 0 10px; color:var(--fg);}
.bubble h3{ font-size:12.5px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); margin:18px 0 8px; }
.bubble h3:first-child{ margin-top:0; }
.bubble p{margin:0 0 8px} .bubble p:last-child{margin:0}
.bubble ul,.bubble ol{margin:6px 0; padding-left:20px} .bubble li{margin:3px 0}
.bubble strong{font-weight:700}
.bubble code{font-family:"IBM Plex Mono",monospace; font-size:12px; background:var(--inset); padding:1px 5px; border-radius:5px;}
.bubble .rescard{ margin:9px 0 2px; border:1px solid var(--line); border-radius:11px; overflow:hidden; background:var(--paper);}
.bubble .rescard .rc-row{ display:flex; align-items:center; gap:10px; padding:9px 12px; border-bottom:1px solid var(--line-2);}
.bubble .rescard .rc-row:last-child{border-bottom:none}
.bubble .rescard .rc-row:hover{background:var(--paper-2); cursor:pointer}
.bubble .rescard .nm{font-weight:600; font-size:13px}
.bubble .rescard .mt{font-size:11.5px; color:var(--muted)}
.bubble .rescard .vv{margin-left:auto; text-align:right; font-weight:600; font-size:13px; font-variant-numeric:tabular-nums}
.typing{display:inline-flex; gap:4px; align-items:center; padding:4px 0}
.typing i{width:6px;height:6px;border-radius:50%; background:var(--muted); animation:blink 1.2s infinite both}
.typing i:nth-child(2){animation-delay:.2s} .typing i:nth-child(3){animation-delay:.4s}
@keyframes blink{0%,80%,100%{opacity:.25}40%{opacity:1}}
.composer{ position:sticky; bottom:0; z-index:5; background:var(--paper); border-top:1px solid var(--line-2); border-radius:0 0 var(--r-l) var(--r-l); padding:12px 14px calc(12px + var(--padb)); }
.suggests{ display:flex; gap:7px; flex-wrap:wrap; margin-bottom:10px;}
.suggests button{ font-size:12px; font-weight:500; color:var(--fg-2); border:1px solid var(--line); background:var(--paper-2); padding:6px 11px; border-radius:20px; transition:.12s;}
.suggests button:hover{ border-color:var(--brand); color:var(--brand);}
.inputrow{ display:flex; gap:10px; align-items:flex-end; background:var(--paper-2); border:1px solid var(--line); border-radius:12px; padding:8px 8px 8px 14px;}
.inputrow textarea{ flex:1; border:none; background:none; resize:none; color:var(--fg); font:inherit; font-size:13.5px; max-height:120px; padding:5px 0; outline:none;}
.inputrow textarea::placeholder{color:var(--muted)}
.sendbtn{ width:38px;height:38px; border-radius:10px; background:var(--brand); color:var(--on-brand); display:grid; place-items:center; flex:0 0 auto; transition:.12s;}
.sendbtn:hover{background:var(--brand-2)} .sendbtn:disabled{opacity:.4; cursor:default}
.sendbtn svg{width:17px;height:17px}
.ctx-panel{ position:sticky; top:84px; display:flex; flex-direction:column; gap:14px;}
.ctx-card{ background:var(--paper); border:1px solid var(--line); border-radius:var(--r-l); padding:15px 16px; box-shadow:var(--sh-1);}
.ctx-card h4{ font-size:12.5px; display:flex; align-items:center; gap:7px; margin-bottom:10px;}
.ctx-card h4 svg{width:15px;height:15px; color:var(--muted)}
.ctx-list{display:flex; flex-direction:column; gap:1px}
.ctx-list button{ display:flex; align-items:center; gap:9px; padding:7px 8px; border-radius:8px; width:100%; text-align:left; font-size:12.5px; transition:background .12s;}
.ctx-list button:hover{background:var(--paper-2)}
.ctx-list .avatar{width:26px;height:26px;border-radius:7px;font-size:10.5px}
.ctx-list .g{margin-left:auto; font-size:11.5px; font-weight:600; font-variant-numeric:tabular-nums; color:var(--muted)}

/* ============ CLIENT PROFILE ============ */
.backlink{ display:inline-flex; align-items:center; gap:6px; font-size:12.5px; font-weight:600; color:var(--muted); margin-bottom:14px;}
.backlink:hover{color:var(--fg)}
.cli-head{ display:flex; gap:18px; align-items:flex-start; flex-wrap:wrap;}
.cli-head .avatar{ width:60px;height:60px; border-radius:14px; font-size:22px;}
.cli-head .nm{ font-family:"Newsreader",serif; font-size:30px; line-height:1.05; letter-spacing:-.01em;}
.cli-head .sub{ color:var(--muted); font-size:13px; margin-top:5px; display:flex; gap:10px; flex-wrap:wrap; align-items:center;}
.cli-head .aum{ margin-left:auto; text-align:right;}
.cli-head .aum .k{ font-family:"Newsreader",serif; font-size:30px; line-height:1;}
.cli-head .aum .l{ font-size:11.5px; color:var(--muted); margin-top:4px;}
.kpis{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-top:20px;}
.kpi{ background:var(--paper); border:1px solid var(--line); border-radius:var(--r-m); padding:13px 15px; box-shadow:var(--sh-1);}
.kpi .l{ font-size:11.5px; color:var(--muted);}
.kpi .v{ font-size:19px; font-weight:600; margin-top:5px; font-variant-numeric:tabular-nums; font-family:"Newsreader",serif;}
.grid2{ display:grid; grid-template-columns:1.4fr 1fr; gap:16px; margin-top:16px; align-items:start;}
.card{ background:var(--paper); border:1px solid var(--line); border-radius:var(--r-l); box-shadow:var(--sh-1);}
.card .ch{ padding:14px 17px; border-bottom:1px solid var(--line-2); display:flex; align-items:center; gap:10px;}
.card .ch h3{ font-size:14px;}
.card .ch .r{ margin-left:auto;}
.card .cb{ padding:8px 8px;}
.card .cbp{ padding:16px 17px;}
.hold{ display:flex; align-items:center; gap:12px; padding:9px 10px; border-radius:9px;}
.hold:hover{background:var(--paper-2)}
.hold .sym{ font-family:"IBM Plex Mono",monospace; font-size:12px; font-weight:500; width:52px; color:var(--fg-2);}
.hold .hn{ flex:1; min-width:0;}
.hold .hn .a{font-size:13px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis}
.hold .hn .b{font-size:11.5px; color:var(--muted)}
.hold .w{ width:88px;}
.hold .w .p{font-size:12px; text-align:right; font-variant-numeric:tabular-nums; margin-bottom:3px;}
.hold .gl{ width:96px; text-align:right; font-variant-numeric:tabular-nums; font-size:12.5px; font-weight:600;}
.alloc-row{ display:flex; align-items:center; gap:12px; padding:8px 4px;}
.alloc-row .al{ width:78px; font-size:12.5px; color:var(--fg-2);}
.alloc-row .track{ flex:1;}
.alloc-row .av{ width:120px; text-align:right; font-size:12px; color:var(--muted); font-variant-numeric:tabular-nums;}
.stack{display:flex; flex-direction:column; gap:16px; margin-top:16px}
.elig-grid{ display:grid; grid-template-columns:1fr 1fr; gap:8px; }
.elig{ display:flex; align-items:center; gap:9px; padding:10px 11px; border:1px solid var(--line); border-radius:10px; background:var(--paper);}
.elig .eic{width:28px;height:28px;border-radius:7px; display:grid;place-items:center; flex:0 0 auto}
.elig .en{font-size:12.5px; font-weight:600}
.elig .es{font-size:11px; color:var(--muted)}
.elig .est{margin-left:auto}
.nba-mini{ display:flex; gap:10px; padding:11px 12px; border-radius:11px; border:1px solid var(--line); align-items:flex-start;}
.nba-mini .d{ width:8px;height:8px;border-radius:50%; margin-top:5px; flex:0 0 auto;}
.nba-mini .txt{font-size:12.5px; line-height:1.5}
.nba-mini .txt b{font-weight:600}

/* ============ TAX ============ */
.tax-hero{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px;}
.tax-hero .tk{ background:var(--paper); border:1px solid var(--line); border-radius:var(--r-l); padding:16px 17px; box-shadow:var(--sh-1); position:relative; overflow:hidden;}
.tax-hero .tk .l{ font-size:12px; color:var(--muted); display:flex; align-items:center; gap:7px;}
.tax-hero .tk .v{ font-family:"Newsreader",serif; font-size:29px; margin-top:9px; line-height:1;}
.tax-hero .tk .s{ font-size:11.5px; color:var(--muted); margin-top:7px;}
.callout{ display:flex; gap:12px; padding:13px 15px; border-radius:12px; background:var(--brand-tint); border:1px solid color-mix(in srgb,var(--brand) 25%, transparent); margin:16px 0;}
.callout svg{width:18px;height:18px;color:var(--brand); flex:0 0 auto; margin-top:1px}
.callout .t{font-size:13px; line-height:1.55; color:var(--brand-ink)}
.callout .t b{font-weight:700}

/* ============ MOBILE ============ */
.mtabbar{ display:none;}
@media (max-width: 940px){
  #app{ grid-template-columns:1fr;}
  .rail{ display:none;}
  .main{ padding-bottom:70px;}
  .content{padding:18px 15px 90px;}
  .topbar{padding:calc(12px + var(--pad)) 15px 12px;}
  .search{display:none;}
  .nba-grid{grid-template-columns:1fr;}
  .chatwrap{grid-template-columns:1fr;}
  .ctx-panel{display:none;}
  .chat{min-height:0;}
  .grid2{grid-template-columns:1fr;}
  .kpis{grid-template-columns:1fr 1fr;}
  .tax-hero{grid-template-columns:1fr 1fr;}
  .cli-head .aum{margin-left:0; width:100%; text-align:left; margin-top:8px;}
  .mtabbar{
    display:flex; position:fixed; bottom:0; left:0; right:0; z-index:40;
    background:var(--surface-ink); border-top:1px solid var(--on-ink-line);
    padding:8px 6px calc(8px + var(--padb)); justify-content:space-around;
  }
  .mtabbar button{ display:flex; flex-direction:column; align-items:center; gap:3px; color:var(--on-ink-2); font-size:10px; font-weight:600; padding:4px 10px; border-radius:9px;}
  .mtabbar button svg{width:20px;height:20px}
  .mtabbar button.on{color:var(--on-ink)}
  .hero .greet{font-size:26px}
}
@media (max-width:520px){
  .elig-grid{grid-template-columns:1fr} .kpis{grid-template-columns:1fr 1fr} .tax-hero{grid-template-columns:1fr}
}
.reveal{ opacity:0; transform:translateY(8px); animation:rise .5s cubic-bezier(.2,.7,.2,1) forwards;}
@keyframes rise{to{opacity:1; transform:none}}
.xinfo{display:inline-flex;align-items:center;justify-content:center;width:16px;height:16px;border-radius:50%;border:1px solid var(--line-2);background:var(--paper);color:var(--muted);font-size:10px;font-weight:700;font-style:italic;font-family:Georgia,'Times New Roman',serif;cursor:pointer;vertical-align:middle;margin-left:5px;line-height:1;padding:0}
.xinfo:hover{color:var(--brand);border-color:var(--brand)}
.xpop-back{position:fixed;inset:0;z-index:200;background:transparent}
.xpop{box-sizing:border-box;position:absolute;width:min(420px,94vw);background:var(--paper);border:1px solid var(--line);border-radius:13px;box-shadow:0 16px 48px rgba(15,23,32,.32);padding:14px 15px 15px;color:var(--fg)}
.xpop-x{position:absolute;top:9px;right:11px;border:none;background:none;color:var(--muted);font-size:19px;line-height:1;cursor:pointer;padding:0}
.xpop-h{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:0 18px 9px 0}
.xpop-t{font-weight:700;font-size:13.5px}
.xreason{font-size:12px;padding:7px 9px;border-radius:8px;margin-bottom:9px;background:var(--inset)}
.xreason.bad{color:#b4322a;background:color-mix(in srgb,#b4322a 9%,var(--paper))}
.xreason.unk{color:#8a6d1f;background:color-mix(in srgb,var(--amber) 14%,var(--paper))}
.xpop-sec{font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:11px 0 6px}
.muted2{text-transform:none;letter-spacing:0;font-weight:400}
.xtbl-wrap{max-width:100%;overflow-x:auto}
.xpop-tbl{width:100%;min-width:340px;border-collapse:collapse;font-size:11.5px;table-layout:fixed}
.xpop-tbl col.c1{width:29%}.xpop-tbl col.c2{width:29%}.xpop-tbl col.c3{width:32%}.xpop-tbl col.c4{width:10%}
.xpop-tbl th,.xpop-tbl td{box-sizing:border-box}
.xpop-tbl th{text-align:left;font-weight:600;color:var(--muted);border-bottom:1px solid var(--line);padding:2px 6px 5px}
.xpop-tbl td{padding:5px 6px;border-bottom:1px solid var(--line-2);vertical-align:top;overflow-wrap:anywhere;word-break:break-word}
.xpop-tbl td.v{font-family:'IBM Plex Mono',ui-monospace,monospace;font-size:11px}
.xpop-tbl td.t{color:var(--muted)}
.xpop-tbl td.p{text-align:right}
.xpop-tbl tr.bad td.v{color:#b4322a;font-weight:600}
.xpop-tbl tr.unk td.v{color:#8a6d1f;font-weight:600}
.xpop-tbl .ok{color:var(--brand);font-weight:700}
.xpop-tbl .no{color:#b4322a;font-weight:700}
.xpop-tbl .unk{color:#8a6d1f;font-weight:700}
.xnote{font-size:11.5px;color:var(--fg);padding:6px 9px;border-radius:7px;background:var(--inset);margin-top:5px;line-height:1.45}
.xnote.fa{background:color-mix(in srgb,var(--amber) 13%,var(--paper))}
.xsrc{margin-top:11px;font-size:10px;color:var(--muted);font-family:'IBM Plex Mono',ui-monospace,monospace;word-break:break-word}
@media(max-width:640px){ .xpop-back{background:rgba(10,15,20,.30)} .xpop{position:fixed !important;left:8px !important;right:8px !important;bottom:8px !important;top:auto !important;width:auto !important} }
```

---

## 5. Data model

All reference data lives in three JSON files under `app/data/`, loaded once at import time by `app/data.py` into plain Python `list`/`dict` structures — no ORM, no schema validation beyond what Pydantic does at the API boundary. This section documents the shape of every field before the raw files are embedded, because several fields have non-obvious semantics that a model regenerating similar data must get right.

### 5.1 `households.json` — shape

A flat JSON **list** of household objects (17 total, spanning 2 advisors — the app's default seat, `dana`, manages 11 of them; `marcus` manages the other 6). Each household object has these top-level fields:

| Field | Type | Notes |
|---|---|---|
| `id` | string | lowercase slug, e.g. `"henderson"` — used as the URL/path identifier everywhere |
| `name` | string | display name, e.g. `"Henderson Family Trust"` |
| `entity` | string | legal entity type, e.g. `"Revocable Trust"`, `"LLC"`, `"Individual"` |
| `segment` | string | book segment, e.g. `"Private Wealth"`, `"HNW"`, `"Institutional"` |
| `aum` | number | assets under management, in raw dollars (not millions) |
| `rev` | number | annualized advisory revenue, in raw dollars |
| `since` | number | year client relationship began |
| `risk` | string | risk mandate label, e.g. `"Moderate Growth"` |
| `contact` | string | primary contact name(s) |
| `advisor_id` | string | `"dana"` or `"marcus"` — which advisor's book this household belongs to |
| `nextMeeting` | object or `null` | `{"type": str, "inDays": int, "note": str}` — `null` if nothing scheduled |
| `ytdReturn` | number | percent, e.g. `11.4` |
| `harvestable` | number | **not directly used by most code** — superseded by computing this live from holdings; kept for compatibility |
| `ytdRealizedGains` | number | raw dollars, realized so far this year |
| `holdings` | list of objects | see §5.2 below — the actual position-level data everything else derives from |
| `target` | object | CIO house-view target allocation, e.g. `{"equity":55,"fixedIncome":30,"alternatives":10,"cash":5}` (percentages) |
| `current` | object | same shape as `target` — the household's actual current allocation |
| `concentration` | list of objects | zero or more `{"label": str, "pct": number, "threshold": number}` — policy-limit breaches, e.g. a single stock over its concentration limit |
| `cio` | object | `{"score": "Low"|"Moderate"|"High", "view": str, "pub": str, "diverge": str}` — CIO house-view alignment/drift narrative |
| `programs` | object | map of IAP program-offering keys → status string (`"enrolled"` or absent/other) |
| `overlays` | object | map of overlay-offering keys → status string, same convention as `programs` |
| `notes` | string | free-text advisor notes on file |

### 5.2 `holdings[]` — shape

Each entry in a household's `holdings` list:

| Field | Type | Notes |
|---|---|---|
| `sym` | string | ticker or identifier. Individual municipal bonds use a synthetic CUSIP-like id, e.g. `"AUSTIN-4.0-32"` (issuer-coupon-maturity) rather than a real ticker — this convention is how the code (`_is_single_stock`) distinguishes an individual bond from an ETF without needing a `type` field lookup in every case |
| `name` | string | display name |
| `ac` | string | asset class bucket: `"US Equity"`, `"Intl Equity"`, `"Fixed Income"`, `"Municipal"`, `"Cash"` |
| `mv` | number | market value, raw dollars |
| `cost` | number or `null` | cost basis, raw dollars — `null` means unresolved/unknown basis (this matters: TET transition scope explicitly excludes lots with unknown basis, see §7) |
| `type` | string (optional) | only set to `"BOND"` on individual (non-ETF) fixed-income/municipal positions; used to detect "individual fixed income" for TET scope carve-outs |
| `lot_id` | string (optional) | present on some positions with unresolved basis, used in gap-analysis messaging |

### 5.3 `fa-and-facts.json` — shape

A single JSON object with these top-level keys:

- `fa_profiles`: map of advisor id (`"dana"`, `"marcus"`) → `{"name": str, "title": str, "initials": str, ...}`
- `account_facts`: per-household boolean/enum facts used directly by rule predicates (e.g. `account.iap_agreement_executed`)
- `account_offering_facts`: per-household, per-offering override facts (e.g. an explicit `offering_profile_verified` override)
- `offering_minimums`: map of offering key → minimum AUM required (e.g. `{"taxManagedSMA": 250000, "dtlhOverlay": 500000, ...}`)
- `requires_qualified_advisor`: list of offering keys that require the assigned advisor to hold a specific qualification flag

### 5.4 `rule-store.json` — shape

The eligibility rule pack. Top level://
```json
{"pack_id": "...", "status": "...", "offerings": {...}, "composition_rules": [...]}
```

`offerings` is a map of **16 offering keys** → offering definition:

```json
{
  "<offeringKey>": {
    "label": "Human-readable name",
    "program_scope": ["IAP"] | ["MGI"] | ["IAP","MGI"],
    "rules": [
      {
        "rule_id": "string, dotted namespace e.g. 'IAP.agreement'",
        "effect": "REQUIREMENT" | "ELIGIBILITY_GATE" | ...,
        "predicate": {"field": "dotted.path", "op": "EQ"|"NEQ"|"GTE"|"LTE"|..., "value": <any>},
        "failure_class": "CLIENT_ELIGIBILITY" | "ACCOUNT_STRUCTURE" | "ADVISOR_QUALIFICATION" | "FA_SCOPE" | ...,
        "message": "advisor-facing explanation shown in the ⓘ popover",
        "source_doc": [{"document_id": str, "pdf_page": int, "section": str}],
        "compile_source": {"kind": str, "review_status": str}
      }
    ]
  }
}
```

`composition_rules` is a list of 4 objects describing constraints that apply when *combinations* of offerings are held simultaneously (e.g. you cannot layer two competing tax overlays on the same sleeve) — evaluated separately from single-offering eligibility, only over the specific set of offerings a UI screen asks about (see §7.3).

The 16 offering keys, for reference, split into three functional groups used throughout the frontend and the transition-workbench logic:

- **IAP programs** (`IAP_OFFERINGS`): `iapEnrollment`, `taxManagedSMA`, `qlhOverlay`, `dtlhOverlay`, `directIndexing`, `temSms`, `transition` (= Tax Efficient Transition, "TET"), `alternatives`, `privateBanking`, `trustEstate`, `lending`, `insurance`, `charitable`
- **MGI programs** (`MGI_OFFERINGS`): `mgiTer`, `mgiQlh`, `mgiDtlh`
- Every household has a `program` field (`"IAP"` or `"MGI"`) that determines which of the two offering lists applies to it.


---

## 6. The rule-evaluation engine (`app/engine.py`)

This is the most important piece of business logic in the app and the part most likely to be subtly wrong if reimplemented from a paraphrase instead of the exact code. Read this section carefully, then reproduce the code in §6.6 verbatim.

### 6.1 Core principle: three-valued logic, fail-closed

Every predicate evaluates to one of **three** values, never just two:

- `True` — the condition is known to hold
- `False` — the condition is known **not** to hold
- `None` (Python `None`, representing "unknown") — the fact needed to evaluate this condition is missing, null, or explicitly marked `"UNKNOWN"` in the data

This is a deliberate design discipline: **an unset fact is never treated as `False`.** A boolean fact that hasn't been populated for a given household must not silently read as "does not meet requirement" — it must read as "cannot be determined," which elevates the verdict to `NEEDS_REVIEW`, never to `INELIGIBLE` and never to `ELIGIBLE`. This is why `_unknown()` checks for the sentinel `UNKNOWN` object, `None`, *and* the literal string `"UNKNOWN"` — data authors sometimes encode "not yet known" as a literal string in the JSON, and the engine must treat that the same as a truly missing key.

**The system fails closed, never open.** If the engine cannot prove eligibility, the household does not get an ELIGIBLE verdict by default — it gets NEEDS_REVIEW, forcing a human to look at it. The only way to reach ELIGIBLE is for every applicable REQUIREMENT rule to evaluate cleanly to `True`.

### 6.2 Predicate language

A predicate is either a literal boolean, or an object with exactly one of:
- `{"field": "dotted.path", "op": "EQ"|"NEQ"|"IN"|"CONTAINS"|"GTE", "value": <expected>}` — a leaf comparison. `field` is looked up in the facts dict by dotted-path traversal (`_get`); if any segment of the path is missing, the result is the `UNKNOWN` sentinel, which `evaluate_predicate` turns into `None`.
- `{"AND": [predicate, ...]}` — **three-valued AND**: `False` if any child is `False` (short-circuits to false even if others are unknown — a known failure is still a failure regardless of what else is unknown); else `None` if any child is `None`; else `True`.
- `{"OR": [predicate, ...]}` — the dual: `True` if any child is `True`; else `None` if any child is `None`; else `False`.
- `{"NOT": predicate}` — `None` stays `None`; otherwise inverts.

Note the asymmetry that matters: `AND` treats a single known-`False` child as decisive even in the presence of unknowns (you don't need to resolve every unknown once you already know the whole thing fails), but otherwise infects with unknown. Reproduce this exact truth table — it is not the same as either "optimistic" or "pessimistic" three-valued logic in every corner case, it's specifically: false dominates, then unknown, then true.

Comparison operators:
- `EQ`/`NEQ`: only comparable if `actual` and `expected` are the **same Python type** (deliberately strict — comparing a string to a bool must not silently coerce); otherwise `None`.
- `IN`: `actual` must be a string and `expected` a list.
- `CONTAINS`: `actual` must be a list and `expected` is checked for membership in it.
- `GTE`: both operands must be `int`/`float`, else `None`.

### 6.3 Rule effects

Each rule in an offering's `rules` list has an `effect` that determines what happens when its predicate evaluates:

| Effect | On predicate `True` | On predicate `False` | On predicate `None` (unknown) |
|---|---|---|---|
| `REQUIREMENT` | nothing (satisfied) | verdict elevated to `INELIGIBLE` (or `NEEDS_REVIEW` if `failure_class` is `MANAGER_ADJUDICATION` — a human-adjudicated gate never auto-fails) | verdict elevated to `NEEDS_REVIEW`; field added to `missing_fields` |
| `NEEDS_REVIEW` | verdict elevated to `NEEDS_REVIEW` (this effect *flags* a condition that always needs a human look when true — e.g. "large single-stock concentration exists") | nothing | verdict elevated to `NEEDS_REVIEW` |
| `CONDITION` | nothing | verdict elevated to `CONDITIONAL` | verdict elevated to `NEEDS_REVIEW` |
| `DISCLOSURE` | added to `disclosures` list (informational, never changes verdict) | nothing | verdict elevated to `NEEDS_REVIEW` (still — an unresolved disclosure predicate needs review too) |
| `SCOPE_CARVEOUT` | this rule identifies an asset-level carve-out (certain positions are excluded from the offering's scope, e.g. bonds with no cost basis excluded from a tax-transition's scope). The rule's `scope_key` field names a fact path holding the list of excluded ids; if that list isn't resolvable, the verdict is elevated to `NEEDS_REVIEW` | nothing | verdict elevated to `NEEDS_REVIEW` |

Verdict elevation only ever moves in one direction, ranked `ELIGIBLE(0) < CONDITIONAL(1) < NEEDS_REVIEW(2) < INELIGIBLE(3)` — `elevate()` is a no-op if the new verdict outranks the current one already lower in severity; a household starts at `ELIGIBLE` and can only get worse as rules fire, never better.

Every rule's `failure_class` determines whether its reason goes into the **client-safe** `reasons` list or the **internal-only** `internal_only_reasons` list — `CLIENT_ELIGIBILITY` failures are shown to the client-facing surface (`client_safe_view`); anything else (`ACCOUNT_STRUCTURE`, `ADVISOR_QUALIFICATION`, `FA_SCOPE`, `MANAGER_ADJUDICATION`, etc.) is advisor/manager-only and must never leak to a client-safe serializer. This is a real compliance boundary, not a cosmetic one — reproduce `client_safe_view()` exactly, including that it also strips out any reason carrying a `missing_fields` marker (those are internal "we don't know" markers, not client-presentable explanations) and instead surfaces a generic `"Additional internal review or service arrangements are needed."` message when `internal_only_reasons` is non-empty.

### 6.4 Program-scope gate and composition rules

Before any rule runs, `evaluate_offering` checks whether the offering's `program_scope` includes the household's `program` (`"IAP"` or `"MGI"`) — if not, it's an immediate `INELIGIBLE` with a synthetic `PROGRAM_SCOPE` reason, no further rules evaluated.

`evaluate_composition(offering_ids, ...)` is a **separate** evaluation, only run when a UI screen explicitly asks about a *specific combination* of offerings (never automatically for every pair a household happens to hold). It:
1. Evaluates each offering individually first (composition can never make an individually-ineligible offering eligible).
2. For every *pairwise* combination of the given offerings (excluding `iapEnrollment`, which is the base enrollment, not a program that composes with anything), looks up matching composition rules by exact offering-pair match.
3. An unmatched pair (no composition rule found for that exact pair) is **not** assumed compatible — it elevates to `NEEDS_REVIEW` with an `UNRESOLVED` note, because compatibility must be established by an actual source document, not inferred.
4. `INCOMPATIBLE_WITH` relation → `CONFIRMED_INELIGIBLE`. `SCOPE_CARVEOUT_WITHIN_COMPOSITION` → `ELIGIBLE_WITH_CARVEOUT`.

Composition verdicts use their own separate rank order (`CONFIRMED_ELIGIBLE < ELIGIBLE_WITH_CARVEOUT < CONDITIONAL < NEEDS_REVIEW < CONFIRMED_INELIGIBLE`) — do not conflate this with the single-offering verdict rank.

### 6.5 Design rationale and worked examples

This subsection explains *why* the engine is shaped the way §6.1–6.4 describe, and proves each key design decision against real households rather than asserting it abstractly. It synthesizes the original design rationale written before the Python port existed — that document's core worked examples still hold exactly against the current app (verified directly against the running code while writing this) and are worth preserving here rather than being lost to an earlier-stage planning document.

**The problem this engine replaced.** Atlas originally stored eligibility as a verdict someone typed by hand — `programs: {directIndexing:'eligible', privateBanking:'enrolled', ...}`. `'eligible'` as a bare string is an assertion with no derivation, no reason, and no way to replay "why." When policy changes — a minimum moves, a tax rule tightens — every household record has to be re-typed by hand, and nothing can answer *why* a specific household is eligible for a specific offering, or *what* would need to change to make it eligible. Worse, the cross-sell radar and tax desk read these strings directly, so one wrong hand-typed string silently produces a wrong recommendation with no trace back to a cause. This is the exact anti-pattern the whole rule-store/kernel/derive-layer split exists to remove: **eligibility must be computed, sourced, and versioned — never stored as a bare status.**

**Why an unmatched composition pair elevates to `NEEDS_REVIEW` instead of assuming compatibility.** Composition only ever runs over a *specific, caller-supplied set* of offerings under consideration — never "all offerings this household happens to hold" — precisely because compatibility between two offerings is a real-world fact that has to come from an actual source document, not be inferred from the absence of a conflict rule. Silence in the rule pack is evidence of an unresolved question, not evidence of safety.

**Worked example — Henderson's TET scope carve-outs are backed by real holdings, not asserted flags.** `henderson`'s Tax Efficient Transition (TET) verdict shows two scope carve-outs, and both are computed live from the actual `holdings` array (per §7.1's discipline that scope facts are never taken from a static override):
- A legacy gift lot of NVDA carrying `"lot_id": "LOT_HEND_GIFT_2011"` and `"cost": null` — the missing cost basis is what triggers `scope.has_tet_missing_basis`.
- A genuine individual municipal bond, `"sym": "AUSTIN-4.0-32"`, explicitly tagged `"type": "BOND"` — which is what triggers `scope.has_individual_fixed_income`. Note that Henderson's *other* municipal holding, `MUB`, is a fund (no `type: "BOND"` tag) and correctly does **not** trigger this carve-out — the distinction between an individual bond and a bond fund is load-bearing, not cosmetic, and is exactly why `_is_single_stock`-style classification in the transition workbench (§8.6) checks the same `type` field rather than just the asset-class bucket.

Both lot ids shown in the household deep-dive's explain-popover are real identifiers pulled from real data, not synthesized display strings — this matters because the whole point of a scope carve-out is that an advisor can go look up the exact lot being excluded.

**Worked example — a rule that can't be sourced to a real document gets re-homed, not deleted.** Two demo households, `bianchi` and `duarte`, were originally built to demonstrate rule ids that an independent policy-pack review determined were never actually sourced to a real clause. Rather than delete these cases (and lose the demonstration), they were re-homed onto rules that *are* genuinely sourced:
- `bianchi` now demonstrates `account.has_pas_strategy == true` — a real, sourced rule ("TEM overlays are unavailable for accounts invested in a PAS Style Manager Strategy") that blocks TER, QLH, DTLH, and TET simultaneously for the same underlying reason.
- `duarte` now demonstrates `temSms`'s roster check failing outright (`target_strategy.in_approved_temSms_roster: false`) — a clean, singular INELIGIBLE, deliberately distinct in *cause* from Bianchi's PAS-based block, even though both end up INELIGIBLE.

The lesson generalizes beyond these two households: **a demo case built to exercise a specific rule must be re-pointed at a real rule if the original one is later found not to be genuinely sourced — never left pointing at a rule that no longer represents real policy, and never simply deleted just because it's inconvenient to fix.**

**Worked example — FA qualification is contextual to the strategy being considered, not a fixed property of the advisor or the account.** The real mechanism is a single predicate on `iapEnrollment`: `strategy.requires_qualified_advisor == false` **OR** `fa.qualified_for_selected_strategy == true`. Both facts vary by *which offering is currently being evaluated* — `derive_facts` takes the offering id being evaluated, not just the household, specifically because of this. This is provable directly: `farkas` (one of Marcus's households) shows **DTLH itself as `ELIGIBLE`** — every client-level fact passes — while a separate `prerequisite` object attached to that same verdict shows the household's `iapEnrollment` prerequisite as `INELIGIBLE`, with an internal-only (`FA_SCOPE`, never client-facing) reason reading *"Qualification is required for designated strategy types/products; obtain the qualification policy."* This is deliberately **not folded into DTLH's own trace** — it's surfaced as a separate `prerequisite` field on the verdict object (see `offering_result` in `services.py`, §8.1) — because conflating "is the client eligible for this offering" with "is the assigned advisor licensed to sell it" would make the client-eligibility trace lie about what it actually checked. An advisor reading Farkas's DTLH popover sees two separate, correctly-labeled facts: the client qualifies; the advisor currently assigned does not.

**Worked example — namespace isolation between IAP and MGI is a hard gate, not a convention.** `sato` is the one household on `program: "MGI"` (every other household in the book is `"IAP"`). Evaluating `sato` against `mgiQlh` returns `ELIGIBLE`; evaluating the *same household* against `mgiTer` and `mgiDtlh` returns `INELIGIBLE` on their own individual merits (not a program-scope block — Sato genuinely fails those two on the facts) — proving that the namespace split doesn't just block cross-program evaluation, it also lets two offerings in the *same* program produce genuinely different verdicts for genuinely different reasons on the same account. Conversely, evaluating any IAP household against an `MGI`-scoped offering (or vice versa) is rejected immediately with a synthetic `PROGRAM_SCOPE` reason before a single rule runs — this is the `program_scope` gate described in §6.4.

**Worked example — composition's "worst outcome always wins" rule, proven on the sharpest available case.** `henderson` is independently `ELIGIBLE` for TER and also independently eligible for TET — on their own, TET+TER and TET+QLH each resolve to `ELIGIBLE_WITH_CARVEOUT` (both are scope carve-outs, not blocks). Yet the composition panel's *overall* verdict for the set `{transition, taxManagedSMA, qlhOverlay, dtlhOverlay}` on Henderson is `CONFIRMED_INELIGIBLE` — because the TET+DTLH pair is a hard `INCOMPATIBLE_WITH` relation, and composition takes the single worst pairwise outcome across the *entire* requested set, never an average or a majority. One incompatible pair poisons the whole combination, regardless of how many other pairs in the same set are fine or merely carved-out.

**Two real bugs surfaced while originally wiring this in — both about nested-vs-flat key access, both worth remembering as a class of mistake.** First: a `SCOPE_CARVEOUT` rule's `scope_key` lookup was originally written as flat-key indexing (`facts[scope_key]`) against what is actually a *nested* facts object — this silently returned "not found" for every single scope check until it was caught by direct testing and fixed to use the same nested dotted-path resolver (`_get`, §6.2) that every other predicate in the engine already used. Second: a `fa.qualified_for_selected_strategy` fact was initially written as a flat top-level key instead of properly nested under `fa: {...}` — which would have made the kernel's path-based lookup treat it as permanently missing (`UNKNOWN`), silently routing every affected verdict to `NEEDS_REVIEW` rather than the correct eligible/ineligible answer, with no error raised anywhere to reveal the mistake. **The general lesson: in a system where every predicate is a dotted-path lookup into a nested dict, a fact written at the wrong nesting depth doesn't crash — it just silently reads as unknown, which fails closed (§6.1) but can mask a real bug behind a plausible-looking `NEEDS_REVIEW` verdict for a long time if not directly tested against a known-correct expected verdict.** When adding any new derived fact, always test it by asserting the specific expected verdict for a specific household, not just that the code runs without throwing.


### 6.6 Complete `app/engine.py`

```python
from __future__ import annotations
from copy import deepcopy
from itertools import combinations
from typing import Any

UNKNOWN = object()
_RANK = {'ELIGIBLE':0,'CONDITIONAL':1,'NEEDS_REVIEW':2,'INELIGIBLE':3}
_CRANK = {'CONFIRMED_ELIGIBLE':0,'ELIGIBLE_WITH_CARVEOUT':1,'CONDITIONAL':2,'NEEDS_REVIEW':3,'CONFIRMED_INELIGIBLE':4}

def _get(facts: dict[str, Any], field: str) -> Any:
    if field in facts: return facts[field]
    cur: Any = facts
    for part in field.split('.'):
        if not isinstance(cur, dict) or part not in cur: return UNKNOWN
        cur = cur[part]
    return cur

def _unknown(value: Any) -> bool:
    return value is UNKNOWN or value is None or value == 'UNKNOWN'

def evaluate_predicate(predicate: Any, facts: dict[str, Any]) -> bool | None:
    if type(predicate) is bool: return predicate
    if not isinstance(predicate, dict): raise ValueError('Predicate must be boolean or object')
    if 'AND' in predicate:
        values=[evaluate_predicate(x,facts) for x in predicate['AND']]
        return False if False in values else None if None in values else True
    if 'OR' in predicate:
        values=[evaluate_predicate(x,facts) for x in predicate['OR']]
        return True if True in values else None if None in values else False
    if 'NOT' in predicate:
        value=evaluate_predicate(predicate['NOT'],facts)
        return None if value is None else not value
    actual=_get(facts,predicate['field']); expected=predicate.get('value'); op=predicate['op']
    if _unknown(actual): return None
    if op in {'EQ','NEQ'}:
        if type(actual) is not type(expected): return None
        result=actual==expected
        return result if op=='EQ' else not result
    if op=='IN': return expected is not None and type(actual) is str and isinstance(expected,list) and actual in expected
    if op=='CONTAINS': return actual is not None and isinstance(actual,list) and expected in actual
    if op=='GTE': return actual>=expected if type(actual) in {int,float} and type(expected) in {int,float} else None
    raise ValueError(f'Unsupported operator: {op}')

def _leaves(predicate: Any, facts: dict[str, Any]) -> list[dict[str,Any]]:
    if type(predicate) is bool: return []
    if 'field' in predicate:
        value=_get(facts,predicate['field'])
        return [{'field':predicate['field'],'op':predicate['op'],'expected':predicate.get('value'),'actual':None if value is UNKNOWN else value}]
    leaves=[]
    for value in predicate.values():
        for node in value if isinstance(value,list) else [value]: leaves.extend(_leaves(node,facts))
    return leaves

def evaluate_offering(offering_id: str, facts: dict[str,Any], store: dict[str,Any], program: str) -> dict[str,Any]:
    offering=store['offerings'].get(offering_id)
    if not offering: raise KeyError(f'Unknown offering {offering_id}')
    result={'offering_id':offering_id,'label':offering['label'],'verdict':'ELIGIBLE','reasons':[],'internal_only_reasons':[],'disclosures':[],'scope_exclusions':[],'missing_fields':[],'trace':[],'rule_pack_id':store['pack_id']}
    if program not in offering['program_scope']:
        result['verdict']='INELIGIBLE'; result['reasons'].append({'rule_id':'PROGRAM_SCOPE','message':f'{offering["label"]} is unavailable in the {program} program.','failure_class':'CLIENT_ELIGIBILITY'}); return result
    def elevate(verdict: str):
        if _RANK[verdict]>_RANK[result['verdict']]: result['verdict']=verdict
    for rule in offering['rules']:
        value=evaluate_predicate(rule['predicate'],facts); leaves=_leaves(rule['predicate'],facts)
        result['trace'].append({'rule_id':rule['rule_id'],'effect':rule['effect'],'passed':value,'source_doc':rule['source_doc'],'inputs':leaves})
        reason={'rule_id':rule['rule_id'],'message':rule['message'],'source_doc':rule['source_doc'],'failure_class':rule['failure_class']}
        destination=result['reasons'] if rule['failure_class']=='CLIENT_ELIGIBILITY' else result['internal_only_reasons']
        if value is None:
            missing=sorted({x['field'] for x in leaves if _unknown(_get(facts,x['field']))})
            elevate('NEEDS_REVIEW'); result['missing_fields'].extend(missing)
            destination.append({**reason,'message':'Required input is missing or invalid; eligibility is unresolved.','missing_fields':missing}); continue
        effect=rule['effect']
        if effect=='REQUIREMENT' and not value:
            elevate('NEEDS_REVIEW' if rule['failure_class']=='MANAGER_ADJUDICATION' else 'INELIGIBLE'); destination.append(reason)
        elif effect=='NEEDS_REVIEW' and value: elevate('NEEDS_REVIEW'); destination.append(reason)
        elif effect=='CONDITION' and not value: elevate('CONDITIONAL'); destination.append(reason)
        elif effect=='DISCLOSURE' and value: result['disclosures'].append(reason)
        elif effect=='SCOPE_CARVEOUT' and value:
            ids=_get(facts,rule.get('scope_key',''))
            ids=None if ids is UNKNOWN else ids
            result['scope_exclusions'].append({**reason,'scope_key':rule.get('scope_key'),'excluded_ids':ids if isinstance(ids,list) else None})
            if not isinstance(ids,list) or not ids:
                elevate('NEEDS_REVIEW'); result['missing_fields'].append(rule.get('scope_key')); destination.append({**reason,'message':'A scope exclusion is known but its affected asset identifiers are unresolved.'})
    result['missing_fields']=sorted({x for x in result['missing_fields'] if x})
    return result

def evaluate_composition(offering_ids: list[str], facts_by_offering: dict[str,dict[str,Any]], store: dict[str,Any], program: str) -> dict[str,Any]:
    ids=list(dict.fromkeys(offering_ids)); verdicts={i:evaluate_offering(i,facts_by_offering[i],store,program) for i in ids}
    result={'verdict':'CONFIRMED_ELIGIBLE','notes':[],'offerings':ids,'offering_verdicts':verdicts}
    def elevate(verdict: str):
        if _CRANK[verdict]>_CRANK[result['verdict']]: result['verdict']=verdict
    if not ids: elevate('NEEDS_REVIEW')
    for v in verdicts.values():
        elevate('CONFIRMED_INELIGIBLE' if v['verdict']=='INELIGIBLE' else v['verdict'] if v['verdict']!='ELIGIBLE' else 'ELIGIBLE_WITH_CARVEOUT' if v['scope_exclusions'] else 'CONFIRMED_ELIGIBLE')
    for a,b in combinations([x for x in ids if x!='iapEnrollment'],2):
        matches=[r for r in store['composition_rules'] if {a,b}==set(r['offerings'])]
        if not matches:
            elevate('NEEDS_REVIEW');result['notes'].append({'offerings':[a,b],'relation':'UNRESOLVED','message':'Composition is not established by supplied sources; obtain offering-specific terms.'});continue
        for rule in matches:
            result['notes'].append(deepcopy(rule))
            if rule['relation']=='INCOMPATIBLE_WITH': elevate('CONFIRMED_INELIGIBLE')
            elif rule['relation']=='SCOPE_CARVEOUT_WITHIN_COMPOSITION': elevate('ELIGIBLE_WITH_CARVEOUT')
    return result

def client_safe_view(verdict: dict[str,Any]) -> dict[str,Any]:
    return {'offering_id':verdict['offering_id'],'label':verdict['label'],'verdict':verdict['verdict'],'reasons':[{'message':x['message'],'source_doc':x.get('source_doc',[])} for x in verdict['reasons'] if not x.get('missing_fields')],'generic_message':'Additional internal review or service arrangements are needed.' if verdict['internal_only_reasons'] else None,'disclosures':[x['message'] for x in verdict['disclosures']],'scope_notes':[x['message'] for x in verdict['scope_exclusions']]}
```

---

## 7. Data loading and fact derivation (`app/data.py`)

This module loads the three JSON files once at import time and exposes them as module-level constants (`RULE_STORE`, `BOOK_ALL`, `FA_PROFILES`, `BY_ID`, `IAP_OFFERINGS`, `MGI_OFFERINGS`, etc.) — every other module imports from here rather than re-reading JSON.

### 7.1 `derive_facts(household, offering_id)` — the critical function

This is the bridge between raw household/holdings data and the flat `facts` dict the rule engine's predicates read by dotted path (§6.2). **This function must never let an asserted override in `account_offering_facts` contradict what the actual holdings array shows.** Concretely:

- `scope.has_tet_missing_basis` and `scope.tet_missing_basis_ids` are **computed live** from `holdings` (`x.get('cost') is None`), never taken from a static override — because the whole point of this scope-carveout rule is to catch positions with unresolved basis, and that must reflect the real data, not a cached assertion.
- `scope.has_individual_fixed_income` / `scope.individual_fixed_income_ids` are likewise computed live from holdings where asset class is Fixed Income/Municipal *and* `type == 'BOND'` (the individual-bond marker), never from an override.
- `account.has_low_basis_position` **can** be overridden per-account via `ACCOUNT_FACTS`, but falls back to a real computation over holdings (a position representing >10% of the account with cost basis under 50% of market value) if no override is set.
- `account.offering_profile_requirements_met` defaults to a real AUM-vs-minimum comparison (`household['aum'] >= OFFERING_MINIMUMS.get(offering_id, 250_000)`) and is only overridden per-account-per-offering when `ACCOUNT_OFFERING_FACTS` explicitly says so.
- Every fact that has no explicit account-level or offering-level override defaults to `None` (unknown) rather than `False` — e.g. `account.pas_manager_contract_executed` is hardcoded `None` because no seed data currently establishes it either way, and per §6.1 that must never silently read as "not executed."

`client_gl(household)` sums `mv - cost` over every holding with a known cost basis (unrealized gain/loss); `client_harvest(household)` sums only the *negative* `mv - cost` values (i.e. total harvestable losses, always ≤ 0). `my_book(fa)` returns a deep copy of every household belonging to the given advisor id — deep-copied specifically so that nothing downstream can accidentally mutate the shared in-memory `BOOK_ALL` list.

### 7.2 Complete `app/data.py`

```python
from __future__ import annotations
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

DATA_DIR=Path(__file__).parent/'data'
RULE_STORE=json.loads((DATA_DIR/'rule-store.json').read_text())
CONFIG=json.loads((DATA_DIR/'fa-and-facts.json').read_text())
BOOK_ALL=json.loads((DATA_DIR/'households.json').read_text())
FA_PROFILES=CONFIG['fa_profiles']; ACCOUNT_FACTS=CONFIG['account_facts']; ACCOUNT_OFFERING_FACTS=CONFIG['account_offering_facts']
OFFERING_MINIMUMS=CONFIG['offering_minimums']; REQUIRES_QUALIFIED_ADVISOR=set(CONFIG['requires_qualified_advisor'])
IAP_OFFERINGS=[x for x,o in RULE_STORE['offerings'].items() if 'IAP' in o['program_scope']]
MGI_OFFERINGS=[x for x,o in RULE_STORE['offerings'].items() if 'MGI' in o['program_scope']]
ALL_OFFERINGS=list(RULE_STORE['offerings'])
BY_ID={x['id']:x for x in BOOK_ALL}

def derive_facts(household: dict[str,Any], offering_id: str) -> dict[str,Any]:
    holdings=household.get('holdings',[]); total=sum(x['mv'] for x in holdings)
    is_cash=lambda x:x.get('ac')=='Cash' or x.get('sym')=='CASH'
    is_fi=lambda x:x.get('ac') in {'Fixed Income','Municipal'}
    cash=sum(x['mv'] for x in holdings if is_cash(x)); marketable=sum(x['mv'] for x in holdings if not is_cash(x))
    a=ACCOUNT_FACTS.get(household['id'],{}); o=ACCOUNT_OFFERING_FACTS.get(household['id'],{}).get(offering_id,{})
    def override(key,fallback=None): return o[key] if key in o else fallback
    fi_lots=[x for x in holdings if is_fi(x) and x.get('type')=='BOND']; missing=[x for x in holdings if x.get('cost') is None]
    fa=FA_PROFILES.get(household['advisor_id'],FA_PROFILES['dana'])
    facts={
      'account_id':household['id'],'program':household.get('program','IAP'),
      'account.tax_status':a.get('tax_status','TAXABLE'),'account.segment':household['segment'],'account.advisory_value':household['aum'],
      'account.cash_value':cash,'account.pledgeable_marketable_value':marketable,
      'account.alt_capacity_pct':max(0,household.get('target',{}).get('alt',0)-household.get('current',{}).get('alt',0)),
      'account.has_low_basis_position':a.get('has_low_basis_position',any(x.get('cost') is not None and x['mv']>0 and x['cost']/x['mv']<.5 and x['mv']>total*.1 for x in holdings)),
      'account.protection_gap':a.get('protection_gap',False),'account.program_enrollment':a.get('program_enrollment'),
      'account.iap_agreement_executed':True,'account.iap_account_type_eligible':True,'account.separate_account_per_program_strategy':True,'account.selected_strategy_requirements_met':True,
      'account.has_pas_strategy':a.get('has_pas_strategy',False),'account.pas_manager_contract_executed':None,
      'account.is_domestic':a.get('residency_country','US')=='US',
      'account.in_universe_TER':a.get('in_universe_TER'),'account.in_universe_QLH':a.get('in_universe_QLH'),'account.in_universe_DTLH':a.get('in_universe_DTLH'),'account.in_universe_TET':a.get('in_universe_TET'),
      'account.offering_profile_requirements_met':override('account.offering_profile_requirements_met',household['aum']>=OFFERING_MINIMUMS.get(offering_id,250_000)),
      'account.goal_type':a.get('goal_type'),'account.is_retirement':a.get('is_retirement'),'account.available_tem_services':a.get('available_tem_services'),
      'client.residency_country':a.get('residency_country','US'),'client.qualified_purchaser':a.get('qualified_purchaser',household['aum']>=5_000_000),
      'fa.qualified_for_offering':fa['qualified_for_offering'],'fa.qualified_for_selected_strategy':offering_id in fa['qualified_for_offering'],
      'strategy.requires_qualified_advisor':offering_id in REQUIRES_QUALIFIED_ADVISOR,
      'policy.offering_profile_verified':override('policy.offering_profile_verified',True),
      'target_strategy.is_direct_indexing':False,
      'target_strategy.in_approved_directIndexing_roster':override('target_strategy.in_approved_directIndexing_roster'),
      'target_strategy.in_approved_temSms_roster':override('target_strategy.in_approved_temSms_roster'),
      'target_strategy.restrictions_awaiting_manager_acceptance':override('target_strategy.restrictions_awaiting_manager_acceptance'),
      'target_strategy.is_eligible_cio_etf_strategy':a.get('is_eligible_cio_etf_strategy'),
      'transition.strategy_minimum_met':override('transition.strategy_minimum_met'),'transition.budget_minimum_met':override('transition.budget_minimum_met'),'transition.long_term_budget_selected':override('transition.long_term_budget_selected'),
      'scope.has_overlay_ineligible_investments':override('scope.has_overlay_ineligible_investments',False),'scope.overlay_ineligible_investment_ids':[],
      'scope.has_tet_missing_basis':bool(missing),'scope.tet_missing_basis_ids':[x.get('lot_id') or x['sym'] for x in missing],
      'scope.has_individual_fixed_income':bool(fi_lots),'scope.individual_fixed_income_ids':[x.get('lot_id') or x['sym'] for x in fi_lots],
      'scope.has_tma_income_cash':False,'scope.tma_income_cash_ids':[],'scope.has_inaccurate_cost_basis':False,
    }
    return facts

def client_gl(household): return sum(x['mv']-x['cost'] for x in household['holdings'] if x.get('cost') is not None)
def client_harvest(household): return sum(min(0,x['mv']-x['cost']) for x in household['holdings'] if x.get('cost') is not None)
def my_book(fa): return [deepcopy(x) for x in BOOK_ALL if x['advisor_id']==fa]
```

---

## 8. Business logic layer (`app/services.py`)

This module sits between the raw data/rule-engine layer and the HTTP API. It has grown to cover five distinct subsystems as the app was built out; each is explained before the complete file is embedded.

### 8.1 Household and offering helpers

- `household_or_404(household_id)` — looks up in `BY_ID`, raises `KeyError` (caught and converted to HTTP 404 at the API layer) if not found.
- `offering_result(household_id, offering_id)` — calls `derive_facts` then `evaluate_offering`; this is the single choke point every eligibility-consuming feature (client deep-dive, cross-sell, transition workbench) goes through.
- `all_verdicts(household_id)` — evaluates every offering in the household's applicable program list (`IAP_OFFERINGS` or `MGI_OFFERINGS` based on the household's `program` field) and returns a dict keyed by offering id. This is what powers the client deep-dive's full eligibility grid.
- `composition_result(household_id, ids)` — thin wrapper calling `evaluate_composition` with facts for each requested offering.
- `enrich(household)` — computes and attaches `clientGL`, `clientHarvest` (via `client_gl`/`client_harvest`), and `taxAlpha` (an illustrative dollar figure — harvestable losses × a flat illustrative rate — used throughout the UI as "estimated tax alpha available"). Every place that needs these derived numbers calls `enrich()` rather than recomputing them inline.
- `_effective_eligible(result)` — a small helper: a verdict counts as "effectively eligible" for cross-sell/ranking purposes if it's `ELIGIBLE` outright, or `NEEDS_REVIEW` with zero *client-facing* reasons (i.e. the only open items are internal/manager-side, not something blocking the client) — this nuance matters because a raw `verdict == 'ELIGIBLE'` check alone would undercount households that are functionally ready but have a purely internal loose end.

### 8.2 Next-best-action (NBA) ranking — `nba(kind, fa)`

Powers the "Today" hero's four ranked action cards. `kind` is one of `'meetings'`, `'drift'`, `'cio'`, `'deep'`:
- `'meetings'` — every household in the advisor's book with a non-null `nextMeeting`, sorted ascending by `inDays` (soonest first).
- `'drift'` — every household with at least one `concentration` flag, sorted descending by the flag's `pct` (worst breach first). Each result carries a `drift` key with the household's *first* concentration flag attached for display.
- `'cio'` — every household whose `cio.score` is `'Moderate'` or `'High'` (i.e. has meaningful house-view drift), sorted with `'High'` first.
- `'deep'` — the top-N households by `aum` descending (used for the chat sidebar's "Top relationships" list and similar "biggest relationships" surfaces).

### 8.3 Tax desk and cross-sell ranking

- `tax_desk(fa)` — every household in the book, enriched, sorted descending by `taxAlpha`. Straightforward ranked list — no eligibility filtering, since harvesting opportunity is a portfolio fact, not a program-eligibility fact.
- `cross_sell(fa)` — the more interesting one: for every household, for every offering in its applicable program list *except* `iapEnrollment` (base enrollment isn't a cross-sell), evaluate eligibility; keep it only if `_effective_eligible(result)` is true **and** the offering is not already in that household's `programs`/`overlays` enrolled map. Returns a flat, sorted-by-household-revenue list of `{household, offering_id, label, ...}` opportunities. This is deliberately an *eligibility-screened* opportunity list, not a raw "hasn't bought X yet" list — an ineligible household is never surfaced as a cross-sell target no matter how much revenue it might generate.

### 8.4 Chat grounding — `book_context(fa)` and `local_answer(fa, message)`

`book_context(fa)` builds a plain-text, multi-paragraph summary of the *entire* book (every household's AUM, YTD return, meeting status, harvest opportunity, concentration flags, CIO drift) — this is what gets passed as context to a live LLM call for the "Ask Atlas" chat feature (the actual LLM call itself, `_live_chat`, lives in `main.py` since it's an async HTTP-calling concern, not pure business logic).

`local_answer(fa, message)` is the **fully deterministic fallback** used when no LLM key is configured or the live call fails — chat must never simply not work. It does simple keyword matching against the incoming message:
- If the message seems to name a specific household (by id, by a >3-character word from its name, or by contact name), answer with that household's AUM/risk/YTD/unrealized-P&L and next-meeting note.
- Otherwise, match on keyword groups: harvest/tax-loss → top 3 by tax alpha; meeting/week/upcoming → the meetings NBA list; eligible/cross-sell/opportunity → top 5 cross-sell opportunities; concentration/drift/breach/overweight → the drift NBA list; cio/house view/align → the CIO NBA list; top/largest/biggest → the deep NBA list.
- If nothing matches, return a fixed sentence describing what Atlas can do.

This local-answer function is exactly why the chat feature is described as "must always work" — it's a real, if simple, grounded answer generator with zero external dependencies.

### 8.5 Draft review (human-in-the-loop) — meeting-prep drafts

This subsystem exists so an advisor can generate a per-household meeting-prep brief, then **Approve / Decline / Edit** it before it's ever used — nothing is sent or acted on automatically.

- `DRAFT_STORE: dict[str, dict]` — **in-memory only**. Keyed by `f"{household_id}:{kind}"` (currently only `kind == 'meeting_prep'` is implemented). This is explicitly a prototype limitation: a real deployment needs this in a database, keyed by advisor + household, with a full approve/decline/edit history rather than a single mutable record overwritten on each new draft. The code comments this limitation directly above the store's definition — preserve that comment.
- `household_draft_context(household_id)` — builds a **richer, single-household** plain-text context than `book_context` (which is built for ranking across the whole book): full holdings list (top 12), next meeting detail, concentration/policy detail, CIO detail, and a list of eligible-but-unenrolled programs specific to this one household. This is what's handed to the LLM when generating a live draft.
- `local_meeting_prep_draft(household_id)` — the deterministic fallback, structured as markdown with these exact section headers, in this order: `## Meeting prep — <household name>`, `### What prompted this meeting`, `### Portfolio snapshot`, `### Concentration & risk`, `### CIO alignment`, `### Suggested talking points` (3–5 numbered points, built from whatever of: the meeting note, a concentration flag, harvestable losses over $10k, and CIO drift are actually present for that household — never invented), `### Eligible next steps` (the household's real eligible-but-unenrolled offerings, or an explicit "none flagged" line if there are none).
- `generate_draft_local(household_id, kind)` — dispatches to the above for `kind == 'meeting_prep'`; any other kind currently returns a plain "not yet supported" string (the mechanism is deliberately extensible to other draft kinds later, but only meeting-prep is implemented today).

The live-LLM path (`_live_draft`, prompting either Anthropic or OpenAI with a persona instructing it to use *only* the supplied context and follow the same exact section-header structure) lives in `main.py` — see §9.

### 8.6 Transition scenario workbench

The largest and most recently added subsystem. Given a household and an offering it is eligible for but not yet enrolled in, produce either a concrete trade proposal (for offerings that actually restructure a portfolio) or a concrete onboarding checklist (for offerings that are relationship/paperwork-based).

**Kind classification:**
```python
TRADE_MODELABLE = {'directIndexing','taxManagedSMA','qlhOverlay','dtlhOverlay','temSms','transition','mgiTer','mgiQlh','mgiDtlh'}
PROCEDURAL_OFFERINGS = {'alternatives','privateBanking','trustEstate','lending','insurance','charitable','iapEnrollment'}
```
An offering's `kind` in the API response is `'procedural'` if it's in `PROCEDURAL_OFFERINGS` **or** simply not in `TRADE_MODELABLE` (i.e. `TRADE_MODELABLE` is checked first, and anything not explicitly trade-modelable defaults to procedural — this means a future 17th offering not yet classified falls safely to the checklist path rather than attempting to model trades against a shape it doesn't understand).

**ETF-vs-single-stock detection** (`_is_single_stock`, `_KNOWN_ETFS`): this app has no real security master, so ETF-ness is determined by a hardcoded set of ~23 well-known ETF tickers (VTI, VOO, ITOT, SCHB, SPY, IVV, VXUS, IEFA, VEA, EFA, IEMG, VWO, AGG, BND, MUB, TIP, LQD, HYG, SHY, GLD, VNQ, SCHF, IWM) plus exclusion of cash and bond-type positions. **This is explicitly called out in the code comment as illustrative** — a real deployment resolves this from a security master, not a hardcoded list. Preserve that comment; do not "fix" it by trying to build a more sophisticated classifier, since the illustrative-ness is the intended, disclosed behavior.

**Trade-generation algorithm, per offering — these genuinely differ and must not be collapsed into one generic "propose trades" function:**

| Offering(s) | Algorithm |
|---|---|
| `directIndexing`, `temSms`, `mgiDtlh` | **Full sleeve replacement.** Sell every US/Intl equity holding (concentration-flagged single stocks get a "trim concentration" reason, others get a generic "reallocate into sleeve" reason), harvest any other position already sitting at a loss >$1,000, then buy one placeholder line: `SMA*` — labeled explicitly as `"(~200 lines, illustrative universe)"` since a real direct-indexing basket has hundreds of individual lines this demo cannot enumerate |
| `taxManagedSMA`, `qlhOverlay`, `mgiTer`, `mgiQlh` | **Overlay on existing sleeve — minimal transition.** No sells at all; just a one-time harvest scan across existing positions at a loss >$1,000. If there's nothing to harvest, emit a single `note`-action row saying so explicitly rather than an empty table |
| `dtlhOverlay` | **ETF-only conversion.** Sell every single-stock position (DTLH requires an ETF-only portfolio), buy one consolidated `ITOT` line sized to the proceeds as the replacement broad-market exposure, then harvest any *already-ETF* position sitting at a loss |
| `transition` (TET) | **Staged tax-aware transition.** For every equity position with a known cost basis and embedded gain over $25,000, emit a `stage_sell` (not an immediate `sell` — TET paces sells against a budget over time, it doesn't sell everything on day one), then harvest any loss position to offset the staged gains |

**Gap analysis** (`_gap_analysis`) surfaces, in priority order: any `NEEDS_REVIEW`-level reasons from the eligibility engine itself (both client-facing and internal — this screen is advisor-facing, so both are shown, unlike the client-safe serializer); for DTLH specifically, a `required`-severity gap naming exactly which non-ETF positions block it; for DI/TEM, a `required` gap for any concentration flag plus a `recommended` gap suggesting a cash buffer if current cash allocation is under 2%; for TET, `scope_carveout`-severity gaps for missing-basis lots and individual fixed income (mirroring the engine's own scope-carveout rules). If no gaps are found at all, emit a single `clear`-severity "No structural blockers. Ready to initiate." row — the gap list is never empty.

**Target state** (`_target_state`) computes: `sells_total`/`buys_total` (straight sums over the trade list), `realized_gain` (sum of positive G/L across sell/stage_sell rows), `harvest_offset` (sum of the *magnitude* of negative G/L across harvest rows), `net_taxable_gain` = `max(0, realized_gain - harvest_offset)` (never negative — you can't have a negative taxable event, excess losses just carry forward unmentioned at this level of detail), and `estimated_ongoing_annual_tax_alpha` — the household's flat `taxAlpha` figure scaled by a **per-offering factor** reflecting how much of the theoretical alpha that specific overlay actually captures in steady state: DTLH 0.9, DI 0.85, QLH 0.7, TEM 0.7, mgiDtlh 0.75, mgiQlh 0.55, TER-family (`taxManagedSMA`) 0.6, mgiTer 0.5, TET (`transition`) 0 (TET is a one-time transition event, not an ongoing overlay, so it has no ongoing alpha figure). `notes` is a list of plain-English caveats assembled conditionally: a basis-reset/wash-sale note for DI/TEM, a "harvested losses carry forward" note for the overlay-only offerings, a TET-specific pacing note, and — whenever `net_taxable_gain > 0` — an explicit illustrative-tax-dollar-estimate line at a flat 23.8% blended rate.

**Procedural steps** (`_procedural_steps`) is a hardcoded, offering-specific checklist (KYC/suitability confirmation first on every list, then 3–4 offering-specific onboarding steps) for each of the seven procedural offerings, with a generic 3-step fallback for anything else.

### 8.7 Complete `app/services.py`

```python
from __future__ import annotations
from typing import Any
from .data import *
from .engine import evaluate_offering,evaluate_composition

PROGRAM_LISTS={'IAP':IAP_OFFERINGS,'MGI':MGI_OFFERINGS}

def household_or_404(household_id:str):
    if household_id not in BY_ID: raise KeyError(household_id)
    return BY_ID[household_id]

def offering_result(household_id:str, offering_id:str):
    hh=household_or_404(household_id); facts=derive_facts(hh,offering_id)
    result=evaluate_offering(offering_id,facts,RULE_STORE,hh.get('program','IAP'))
    if hh.get('program','IAP')=='IAP' and offering_id!='iapEnrollment':
        pre=evaluate_offering('iapEnrollment',derive_facts(hh,offering_id),RULE_STORE,'IAP')
        result['prerequisite']=pre
    return result

def all_verdicts(household_id:str):
    hh=household_or_404(household_id)
    return {i:offering_result(household_id,i) for i in PROGRAM_LISTS[hh.get('program','IAP')] if i!='iapEnrollment'}

def composition_result(household_id:str, ids:list[str]):
    hh=household_or_404(household_id)
    facts={i:derive_facts(hh,i) for i in ids}
    return evaluate_composition(ids,facts,RULE_STORE,hh.get('program','IAP'))

def enrich(hh):
    row={**hh,'clientGL':client_gl(hh),'clientHarvest':client_harvest(hh),'taxAlpha':abs(client_harvest(hh))*.238}
    return row

def nba(kind:str,fa:str):
    book=[enrich(x) for x in my_book(fa)]
    if kind=='meetings': return sorted([x for x in book if x.get('nextMeeting')],key=lambda x:x['nextMeeting']['inDays'])[:4]
    if kind=='drift':
        rows=[]
        for x in book:
            if x['concentration']: rows.append({**x,'drift':x['concentration'][0]})
            elif abs(x['current']['cash']-x['target']['cash'])>=12: rows.append({**x,'drift':{'label':'Cash allocation','pct':x['current']['cash'],'threshold':x['target']['cash']}})
        return sorted(rows,key=lambda x:x['drift']['pct']-x['drift']['threshold'],reverse=True)[:4]
    if kind=='cio': return sorted([x for x in book if x['cio']['score']!='Low'],key=lambda x:{'High':0,'Medium':1}.get(x['cio']['score'],2))[:4]
    if kind=='deep': return sorted(book,key=lambda x:x['aum'],reverse=True)[:4]
    raise ValueError(kind)

def tax_desk(fa:str):
    rows=[]
    for hh in my_book(fa):
        row=enrich(hh); ids=['taxManagedSMA','qlhOverlay','dtlhOverlay'] if hh.get('program','IAP')=='IAP' else MGI_OFFERINGS
        row['verdicts']={i:offering_result(hh['id'],i) for i in ids}; rows.append(row)
    return sorted(rows,key=lambda x:x['taxAlpha'],reverse=True)

def _effective_eligible(result):
    return result['verdict']=='ELIGIBLE' and (not result.get('prerequisite') or result['prerequisite']['verdict']=='ELIGIBLE')

def cross_sell(fa:str):
    rows=[]
    for hh in my_book(fa):
        if hh.get('program','IAP')!='IAP': continue
        enrolled={k for k,v in {**hh.get('programs',{}),**hh.get('overlays',{})}.items() if v=='enrolled'}
        for off in ['privateBanking','trustEstate','alternatives','directIndexing','lending','insurance','charitable','taxManagedSMA','qlhOverlay','dtlhOverlay','transition','temSms']:
            r=offering_result(hh['id'],off)
            if _effective_eligible(r) and off not in enrolled:
                values={'alternatives':hh['aum']*.15*.01,'directIndexing':hh['aum']*.2*.004,'privateBanking':hh['aum']*.1*.015,'lending':hh['aum']*.2*.012,'trustEstate':15000,'insurance':12000,'charitable':10000,'taxManagedSMA':hh['aum']*.003,'qlhOverlay':hh['aum']*.0025,'dtlhOverlay':hh['aum']*.003,'transition':hh['aum']*.002,'temSms':hh['aum']*.003}
                rows.append({'household_id':hh['id'],'name':hh['name'],'offering_id':off,'label':r['label'],'estimated_value':round(values.get(off,0)),'reason':(r['reasons'][0]['message'] if r['reasons'] else 'All evaluated eligibility requirements are satisfied.'),'verdict':r['verdict']})
    return sorted(rows,key=lambda x:x['estimated_value'],reverse=True)

def book_context(fa:str):
    lines=[]
    for x in my_book(fa):
        e=enrich(x); meeting=x['nextMeeting']; concentration=x['concentration'][0]['label'] if x['concentration'] else 'none'
        lines.append(f"{x['name']} | {x['segment']} | AUM ${x['aum']:,.0f} | YTD {x['ytdReturn']}% | unrealized ${e['clientGL']:,.0f} | harvestable ${abs(e['clientHarvest']):,.0f} | meeting {meeting['inDays'] if meeting else 'none'} | concentration {concentration} | CIO {x['cio']['score']} | {x['notes']}")
    return '\n'.join(lines)

def local_answer(fa:str,message:str):
    q=message.lower(); book=my_book(fa)
    target=next((x for x in book if x['id'] in q or any(w.lower() in q for w in x['name'].split() if len(w)>3) or x['contact'].lower() in q),None)
    if target:
        e=enrich(target); meeting=target['nextMeeting']; return f"{target['name']} has ${target['aum']/1e6:.1f}M AUM, {target['risk']} risk, {target['ytdReturn']:.1f}% YTD return, and ${e['clientGL']/1e6:.2f}M unrealized P&L. " + (f"Next meeting is in {meeting['inDays']} days: {meeting['note']}" if meeting else target['notes'])
    if any(k in q for k in ['harvest','tax loss','losses','tlh']):
        rows=sorted([enrich(x) for x in book],key=lambda x:x['taxAlpha'],reverse=True)[:3];return 'Top current tax-loss opportunities: '+', '.join(f"{x['name']} (${abs(x['clientHarvest']):,.0f} losses; illustrative tax value ${x['taxAlpha']:,.0f})" for x in rows)+'.'
    if any(k in q for k in ['meeting','week','upcoming']):
        rows=nba('meetings',fa); return 'Upcoming meetings: '+(', '.join(f"{x['name']} in {x['nextMeeting']['inDays']} days" for x in rows) if rows else 'none scheduled')+'.'
    if any(k in q for k in ['eligible','cross-sell','opportunity']):
        rows=cross_sell(fa)[:5];return 'Highest reviewed opportunities: '+(', '.join(f"{x['name']} — {x['label']}" for x in rows) if rows else 'none with a clean eligible verdict')+'.'
    if any(k in q for k in ['concentration','drift','breach','overweight']):
        rows=nba('drift',fa);return 'Priority drift cases: '+(', '.join(f"{x['name']} — {x['drift']['label']} {x['drift']['pct']}% vs {x['drift']['threshold']}% limit" for x in rows) if rows else 'none')+'.'
    if any(k in q for k in ['cio','house view','align','publication']):
        rows=nba('cio',fa);return 'CIO alignment follow-ups: '+(', '.join(f"{x['name']} — {x['cio']['view']}" for x in rows) if rows else 'none')+'.'
    if any(k in q for k in ['top','largest','biggest']): return 'Largest relationships: '+', '.join(f"{x['name']} (${x['aum']/1e6:.1f}M)" for x in nba('deep',fa))+'.'
    return 'I can rank tax-loss opportunities, prepare a client meeting, show upcoming meetings, identify concentration drift, summarize CIO misalignment, or list reviewed cross-sell opportunities.'

# ---- Draft review (human-in-the-loop) ----
# In-memory only: a real deployment would persist this per-household/kind draft
# and its approve/decline/edit history in a database, keyed by advisor + household.
DRAFT_STORE: dict[str, dict] = {}

def draft_key(household_id: str, kind: str) -> str:
    return f"{household_id}:{kind}"

def household_draft_context(household_id: str) -> str:
    """Rich, single-household context for drafting — deliberately more detailed
    than book_context(), which is built for ranking across an entire book."""
    hh = household_or_404(household_id); e = enrich(hh)
    meeting = hh.get('nextMeeting')
    concentration = hh['concentration'][0] if hh.get('concentration') else None
    enrolled = {**hh.get('programs', {}), **hh.get('overlays', {})}
    elig_lines = []
    for off in PROGRAM_LISTS.get(hh.get('program', 'IAP'), []):
        if off == 'iapEnrollment': continue
        try:
            r = offering_result(household_id, off)
            if _effective_eligible(r) and enrolled.get(off) != 'enrolled':
                elig_lines.append(f"  - {r['label']}: eligible, not yet enrolled")
        except Exception:
            pass
    holdings_lines = '\n'.join(
        f"  - {h['sym']} ({h['name']}): {h['ac']}, ${h['mv']:,.0f}" for h in hh['holdings'][:12]
    )
    return f"""HOUSEHOLD: {hh['name']}
Entity: {hh['entity']} | Segment: {hh['segment']} | Client since: {hh['since']} | Risk mandate: {hh['risk']}
Primary contact(s): {hh['contact']}
AUM: ${hh['aum']:,.0f} | Annual revenue: ${hh['rev']:,.0f} | YTD return: {hh['ytdReturn']}%
Unrealized gain/loss: ${e['clientGL']:,.0f} | Harvestable losses: ${abs(e['clientHarvest']):,.0f} (~${e['taxAlpha']:,.0f} illustrative tax alpha)
Next meeting: {(str(meeting['inDays']) + ' days from now — ' + meeting['type'] + '. Advisor note: ' + (meeting.get('note') or 'none')) if meeting else 'None currently scheduled'}
Concentration/policy: {(concentration['label'] + ' at ' + str(concentration['pct']) + '% vs a ' + str(concentration['threshold']) + '% policy limit') if concentration else 'No policy breaches flagged'}
CIO alignment: {hh['cio']['score']} drift — "{hh['cio']['view']}" ({hh['cio']['pub']}). {hh['cio']['diverge']}.
Holdings (showing {min(12,len(hh['holdings']))} of {len(hh['holdings'])}):
{holdings_lines}
Eligible but unenrolled programs/services:
{chr(10).join(elig_lines) if elig_lines else '  - none currently flagged'}
Advisor notes on file: {hh.get('notes','') or 'none'}
"""

def local_meeting_prep_draft(household_id: str) -> str:
    """Deterministic, fully-grounded fallback used when no LLM key is configured
    or the live call fails — the draft feature must always work."""
    hh = household_or_404(household_id); e = enrich(hh)
    meeting = hh.get('nextMeeting')
    concentration = hh['concentration'][0] if hh.get('concentration') else None
    lines = [f"## Meeting prep — {hh['name']}"]
    if meeting:
        lines.append(f"**{meeting['type']}** · in {meeting['inDays']} days · {hh['segment']} · ${hh['aum']:,.0f} AUM\n")
    else:
        lines.append(f"{hh['segment']} · ${hh['aum']:,.0f} AUM — no meeting currently scheduled.\n")
    lines.append("### What prompted this meeting\n" + (meeting.get('note') if meeting and meeting.get('note') else "Standing scheduled review; no specific trigger on file.") + "\n")
    lines.append(f"### Portfolio snapshot\n- YTD return: {hh['ytdReturn']}%\n- Unrealized gain/loss: ${e['clientGL']:,.0f}\n- Harvestable losses: ${abs(e['clientHarvest']):,.0f} (~${e['taxAlpha']:,.0f} illustrative tax alpha)\n")
    lines.append("### Concentration & risk\n" + (f"{concentration['label']} at {concentration['pct']}% vs a {concentration['threshold']}% policy limit — worth raising directly." if concentration else "No policy breaches flagged this cycle.") + "\n")
    lines.append(f"### CIO alignment\n{hh['cio']['score']} drift. \"{hh['cio']['view']}\" {hh['cio']['diverge']}.\n")
    talking = []
    if meeting and meeting.get('note'): talking.append(meeting['note'])
    if concentration: talking.append(f"Discuss trimming {concentration['label']} toward the {concentration['threshold']}% policy target.")
    if abs(e['clientHarvest']) > 10000: talking.append(f"Flag ${abs(e['clientHarvest']):,.0f} of harvestable losses (~${e['taxAlpha']:,.0f} illustrative tax alpha) ahead of year-end.")
    if hh['cio']['score'] != 'Low': talking.append(f"Walk through the CIO's current view: {hh['cio']['view']}")
    if not talking: talking.append("Confirm goals and risk tolerance are still current; no urgent flags this cycle.")
    lines.append("### Suggested talking points\n" + '\n'.join(f"{i+1}. {t}" for i, t in enumerate(talking[:5])) + "\n")
    enrolled = {**hh.get('programs', {}), **hh.get('overlays', {})}
    elig = []
    for off in PROGRAM_LISTS.get(hh.get('program', 'IAP'), []):
        if off == 'iapEnrollment': continue
        try:
            r = offering_result(household_id, off)
            if _effective_eligible(r) and enrolled.get(off) != 'enrolled':
                elig.append(r['label'])
        except Exception:
            pass
    lines.append("### Eligible next steps\n" + ('\n'.join(f"- {x}" for x in elig) if elig else "- No unenrolled eligible programs flagged this cycle."))
    return '\n'.join(lines)

def generate_draft_local(household_id: str, kind: str) -> str:
    if kind == 'meeting_prep':
        return local_meeting_prep_draft(household_id)
    return f"Draft generation for '{kind}' is not yet supported."

# ---- Transition scenario workbench ----
# Some offerings model a real portfolio transition (trades to execute); others
# are procedural onboardings (paperwork, meetings, funding). Both kinds share
# the same top-level shape so the frontend can render them consistently.
TRADE_MODELABLE = {'directIndexing','taxManagedSMA','qlhOverlay','dtlhOverlay','temSms','transition','mgiTer','mgiQlh','mgiDtlh'}
PROCEDURAL_OFFERINGS = {'alternatives','privateBanking','trustEstate','lending','insurance','charitable','iapEnrollment'}
# Illustrative ETF tickers used in this demo book. A real deployment would
# resolve this from a security master, not a hard-coded list.
_KNOWN_ETFS = {'VTI','VOO','ITOT','SCHB','SPY','IVV','VXUS','IEFA','VEA','EFA','IEMG','VWO','AGG','BND','MUB','TIP','LQD','HYG','SHY','GLD','VNQ','SCHF','IWM'}

def _is_single_stock(h: dict) -> bool:
    if h.get('type') == 'BOND': return False
    if h['ac'] == 'Cash': return False
    if h['ac'] == 'Municipal' and h.get('type') == 'BOND': return False
    if h['sym'] in ('CASH',): return False
    if h['sym'] in _KNOWN_ETFS: return False
    if h['ac'] == 'Fixed Income' and h['sym'] in _KNOWN_ETFS: return False
    # Individual bonds have specific ID-style tickers or type BOND
    if any(sep in h['sym'] for sep in ('-',)): return False
    return h['ac'] in ('US Equity','Intl Equity')

def _label_for_offering(offering: str) -> str:
    for _, o in RULE_STORE['offerings'].items():
        pass
    # RULE_STORE['offerings'][key]['label']
    return RULE_STORE['offerings'].get(offering, {}).get('label', offering)

def _current_state(hh, e):
    top = sorted(hh['holdings'], key=lambda h: -h['mv'])[:6]
    return {
        'aum': hh['aum'],
        'positions': len(hh['holdings']),
        'allocation': hh['current'],
        'target_allocation': hh['target'],
        'top_holdings': [{'sym': h['sym'], 'name': h['name'], 'ac': h['ac'], 'mv': h['mv'],
                          'weight': round(h['mv']/hh['aum']*100, 1),
                          'gl': (h['mv']-h['cost']) if h['cost'] is not None else None} for h in top],
        'concentration_flags': hh.get('concentration', []),
        'cash_pct': hh['current'].get('cash', 0),
        'ytd_realized_gains': hh.get('ytdRealizedGains', 0),
        'harvestable_losses': abs(e['clientHarvest']),
    }

def _gap_analysis(hh, e, offering, verdict):
    gaps = []
    if verdict and verdict.get('verdict') == 'NEEDS_REVIEW':
        for r in verdict.get('reasons', []) + verdict.get('internal_only_reasons', []):
            if not r.get('missing_fields'):
                gaps.append({'severity':'review','message': r.get('message','')})
        for f in verdict.get('missing_fields', []):
            gaps.append({'severity':'review','message':f'Resolve unknown field: {f.replace("_"," ")}'})
    if offering == 'dtlhOverlay':
        non_etfs = [h for h in hh['holdings'] if _is_single_stock(h)]
        if non_etfs:
            gaps.append({'severity':'required',
                'message': f'Portfolio must be ETF-only for DTLH. {len(non_etfs)} non-ETF position(s) to swap: '+', '.join(h['sym'] for h in non_etfs[:5])})
    if offering in ('directIndexing','temSms'):
        conc = hh.get('concentration', [])
        if conc:
            gaps.append({'severity':'required',
                'message': f"Concentrated positions need trimming: {conc[0]['label']} at {conc[0]['pct']}% (policy limit {conc[0]['threshold']}%)."})
        if hh['current'].get('cash', 0) < 2:
            gaps.append({'severity':'recommended',
                'message':'Modest cash reserve helps stage the initial buy without forced timing.'})
    if offering == 'transition':
        missing_basis = [h for h in hh['holdings'] if h.get('cost') is None]
        indiv_fi = [h for h in hh['holdings'] if h.get('type') == 'BOND']
        if missing_basis:
            gaps.append({'severity':'scope_carveout',
                'message':f'{len(missing_basis)} lot(s) with unresolved cost basis excluded from TET scope: '+', '.join(h.get('lot_id',h['sym']) for h in missing_basis)+'.'})
        if indiv_fi:
            gaps.append({'severity':'scope_carveout',
                'message':f'{len(indiv_fi)} individual fixed-income position(s) excluded from TET scope: '+', '.join(h['sym'] for h in indiv_fi)+'.'})
    if not gaps:
        gaps.append({'severity':'clear','message':'No structural blockers. Ready to initiate.'})
    return gaps

def _propose_trades(hh, e, offering):
    trades = []
    holdings = hh['holdings']
    if offering in ('directIndexing','temSms','mgiDtlh'):
        # Replace equity sleeve with a broad SMA basket
        equity = [h for h in holdings if h['ac'] in ('US Equity','Intl Equity')]
        proceeds = 0
        for h in sorted(equity, key=lambda x: -x['mv']):
            weight = h['mv']/hh['aum']*100
            gl = (h['mv']-h['cost']) if h['cost'] is not None else None
            reason = (f'Trim concentration ({weight:.1f}% \u2192 basket weight).'
                if _is_single_stock(h) and weight > 5
                else 'Reallocate into direct-indexed broad-market sleeve.')
            trades.append({'action':'sell','sym':h['sym'],'name':h['name'],'value':h['mv'],'gl':gl,'reason':reason})
            proceeds += h['mv']
        # Harvest losses at onboarding to offset gains
        for h in holdings:
            if h.get('cost') is not None and (h['mv']-h['cost']) < -1000 and h not in equity:
                trades.append({'action':'harvest','sym':h['sym'],'name':h['name'],'value':h['mv'],
                    'gl':h['mv']-h['cost'],
                    'reason':f'Harvest ${abs(h["mv"]-h["cost"]):,.0f} of losses at onboarding; carry forward.'})
        if proceeds > 0:
            label = 'Direct-indexed broad-market SMA sleeve' if offering=='directIndexing' else 'Style-manager SMA sleeve'
            trades.append({'action':'buy','sym':'SMA*','name':f'{label} (~200 lines, illustrative universe)',
                'value':proceeds,'gl':None,'reason':'Basis reset at trade date. Overlay begins next business day.'})
    elif offering in ('taxManagedSMA','qlhOverlay','mgiTer','mgiQlh'):
        # Overlay on existing holdings: minimal transition, one-time harvest scan
        for h in holdings:
            if h.get('cost') is not None and (h['mv']-h['cost']) < -1000:
                trades.append({'action':'harvest','sym':h['sym'],'name':h['name'],'value':h['mv'],
                    'gl':h['mv']-h['cost'],
                    'reason':f'Onboarding harvest: realize ${abs(h["mv"]-h["cost"]):,.0f}, carry loss forward.'})
        if not trades:
            trades.append({'action':'note','sym':'','name':'No trades required at onboarding',
                'value':0,'gl':None,'reason':'Existing sleeve stays in place; overlay begins with next dividend/rebalance event.'})
    elif offering == 'dtlhOverlay':
        # Swap non-ETFs to ETF equivalents, then harvest
        for h in holdings:
            if _is_single_stock(h):
                gl = (h['mv']-h['cost']) if h['cost'] is not None else None
                trades.append({'action':'sell','sym':h['sym'],'name':h['name'],'value':h['mv'],'gl':gl,
                    'reason':'DTLH requires ETF-only positions.'})
                # Suggest a broad-market ETF as the replacement sleeve rather than a per-stock swap
        non_etf_mv = sum(h['mv'] for h in holdings if _is_single_stock(h))
        if non_etf_mv > 0:
            trades.append({'action':'buy','sym':'ITOT','name':'US broad-market ETF (equivalent exposure)',
                'value':non_etf_mv,'gl':None,'reason':'Preserves equity exposure while enabling DTLH.'})
        # Harvest on ETF losses
        for h in holdings:
            if not _is_single_stock(h) and h.get('cost') is not None and (h['mv']-h['cost']) < -1000:
                trades.append({'action':'harvest','sym':h['sym'],'name':h['name'],'value':h['mv'],
                    'gl':h['mv']-h['cost'],'reason':'Initial daily-cadence DTLH harvest at onboarding.'})
    elif offering == 'transition':
        # TET: staged tax-aware transition of gain positions
        for h in holdings:
            if h.get('cost') is None or h.get('type') == 'BOND': continue
            gl = h['mv']-h['cost']
            if gl > 25000:
                trades.append({'action':'stage_sell','sym':h['sym'],'name':h['name'],'value':h['mv'],'gl':gl,
                    'reason':f'Stage LT-gain sell across TET budget window (~${gl:,.0f} embedded gain).'})
        for h in holdings:
            if h.get('cost') is not None and (h['mv']-h['cost']) < -1000:
                trades.append({'action':'harvest','sym':h['sym'],'name':h['name'],'value':h['mv'],
                    'gl':h['mv']-h['cost'],
                    'reason':f'Realize ${abs(h["mv"]-h["cost"]):,.0f} of losses to offset staged gains.'})
    return trades

def _target_state(hh, e, offering, trades):
    sells = sum(t['value'] for t in trades if t['action'] in ('sell','stage_sell'))
    buys = sum(t['value'] for t in trades if t['action'] == 'buy')
    realized_gain = sum(t.get('gl') or 0 for t in trades if t['action'] in ('sell','stage_sell') and (t.get('gl') or 0) > 0)
    harvest_offset = sum(-(t.get('gl') or 0) for t in trades if t['action'] == 'harvest' and (t.get('gl') or 0) < 0)
    net_taxable = max(0, realized_gain - harvest_offset)
    ongoing_alpha = {
        'taxManagedSMA': e['taxAlpha']*0.6,
        'qlhOverlay': e['taxAlpha']*0.7,
        'dtlhOverlay': e['taxAlpha']*0.9,
        'directIndexing': e['taxAlpha']*0.85,
        'temSms': e['taxAlpha']*0.7,
        'transition': 0,
        'mgiTer': e['taxAlpha']*0.5,
        'mgiQlh': e['taxAlpha']*0.55,
        'mgiDtlh': e['taxAlpha']*0.75,
    }.get(offering, 0)
    # Simulated post-allocation: unchanged for overlays; equity sleeve reshaped for SMA/DI
    post_alloc = dict(hh['current'])
    if offering in ('directIndexing','temSms','dtlhOverlay') and any(_is_single_stock(h) for h in hh['holdings']):
        # Concentration cleared but overall allocation preserved
        pass
    conc_after = [] if offering in ('directIndexing','temSms') else hh.get('concentration', [])
    notes = []
    if offering in ('directIndexing','temSms'):
        notes.append('Basis resets at trade date across the reallocated sleeve; wash-sale windows apply for 30 days on any replacement ETF held elsewhere.')
    if offering in ('qlhOverlay','taxManagedSMA','dtlhOverlay'):
        notes.append('Overlay is applied to the existing sleeve; harvested losses carry forward.')
    if offering == 'transition':
        notes.append('Realized gain paced against the elected TET budget over the horizon; unsold lots stay in current strategy.')
    if net_taxable > 0:
        notes.append(f'Estimated net taxable event: ~${net_taxable:,.0f} of long-term gain (post-offset). Illustrative at {int(0.238*100)}% blended rate: ~${net_taxable*0.238:,.0f}.')
    return {
        'allocation_after': post_alloc,
        'concentration_after': conc_after,
        'realized_gain': realized_gain,
        'harvest_offset': harvest_offset,
        'net_taxable_gain': net_taxable,
        'estimated_ongoing_annual_tax_alpha': int(ongoing_alpha),
        'sells_total': sells, 'buys_total': buys,
        'notes': notes,
    }

def _procedural_steps(hh, offering):
    common_kyc = 'Confirm KYC and suitability profile is current (last review within 12 months).'
    steps_by_offering = {
        'privateBanking': [common_kyc,
            'Introduce client to the Private Banking relationship manager.',
            f'Set up deposit and cash-management relationship sized to the household\'s cash position (~${hh["aum"]*hh["current"].get("cash",0)/100:,.0f}).',
            'Complete Private Banking application and beneficiary designation.',
            'Coordinate initial funding: transfer or direct-deposit new payroll/distributions.',
        ],
        'trustEstate': [common_kyc,
            'Schedule intake with the Trust & Estate specialist.',
            'Review existing will, powers of attorney, and beneficiary designations.',
            'Model gift/estate scenarios against the household\'s AUM and family structure.',
            'Draft or update trust documents; coordinate with outside counsel where applicable.',
        ],
        'alternatives': [common_kyc,
            'Confirm accredited/qualified purchaser status and liquidity budget.',
            'Model the sleeve size against the household\'s target-alt allocation and target risk profile.',
            'Present specific offerings on the approved shelf; capture subscription paperwork.',
            'Coordinate custody and capital-call cash management.',
        ],
        'lending': [common_kyc,
            'Confirm pledgeable collateral and desired credit purpose.',
            'Underwrite a securities-based line sized to advance rates on eligible holdings.',
            'Complete pledge agreement; document intended draw schedule.',
            'Confirm interest-rate/margin covenants with the client in writing.',
        ],
        'insurance': [common_kyc,
            'Review protection gap: life, disability, LTC, umbrella liability.',
            'Underwrite proposed coverage; obtain quotes and medical/financial requirements.',
            'Compare against household\'s existing coverage and beneficiary structure.',
            'Bind policies and integrate premium funding into the cash-management plan.',
        ],
        'charitable': [common_kyc,
            'Confirm charitable intent and preferred vehicle (DAF, private foundation, CRT).',
            'Identify low-basis positions that are attractive for in-kind gifting (see harvestable-losses and gain lots).',
            'Draft gift acceptance / operating documents; coordinate custodian.',
            'Schedule initial funding and set annual grant cadence.',
        ],
        'iapEnrollment': [
            'Review and countersign the current IAP wrap-fee agreement.',
            'Confirm the target strategy and its minimums, program-scope constraints, and fee schedule.',
            'Complete the strategy-specific selection form; confirm advisor qualification for the chosen strategy.',
        ],
    }
    return steps_by_offering.get(offering, [
        common_kyc,
        f'Confirm eligibility and required documents for {_label_for_offering(offering)}.',
        'Complete application, custody setup, and initial funding.',
    ])

def transition_scenario(household_id: str, offering: str):
    if offering not in RULE_STORE['offerings']:
        raise KeyError(f'Unknown offering: {offering}')
    hh = household_or_404(household_id); e = enrich(hh)
    label = _label_for_offering(offering)
    verdict = None
    try: verdict = offering_result(household_id, offering)
    except Exception: pass
    enrolled_map = {**hh.get('programs',{}), **hh.get('overlays',{})}
    is_enrolled = enrolled_map.get(offering) == 'enrolled'
    current = _current_state(hh, e)
    gaps = _gap_analysis(hh, e, offering, verdict)
    procedural = offering in PROCEDURAL_OFFERINGS or offering not in TRADE_MODELABLE
    result = {
        'household_id': household_id, 'offering': offering, 'offering_label': label,
        'kind': 'procedural' if procedural else 'trade_modelable',
        'currently_enrolled': is_enrolled,
        'eligibility_verdict': (verdict or {}).get('verdict', 'UNKNOWN'),
        'current_state': current,
        'gap_analysis': gaps,
    }
    if procedural:
        result['steps'] = _procedural_steps(hh, offering)
    else:
        trades = _propose_trades(hh, e, offering)
        result['proposed_trades'] = trades
        result['target_state'] = _target_state(hh, e, offering, trades)
    return result
```

---

## 9. HTTP API (`app/main.py`)

FastAPI app, no auth layer (single-seat prototype). Every endpoint that takes a household id wraps the `KeyError` from `household_or_404`/`offering_result`/etc. into an HTTP 404 — this pattern (`try: ... except KeyError as e: raise HTTPException(404, str(e))`) is used consistently and should be preserved for every new household-scoped endpoint added later.

### 9.1 Endpoint reference

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | serves `index.html` |
| GET | `/reference` | serves a static `reference.html` (a leftover/reference file, not part of the main app flow) |
| GET | `/api/health` | `{status, pack_id, offerings, rules}` — rule-pack sanity check |
| GET | `/api/meta` | `{advisors, offerings, pack_id, policy_status}` — advisor profiles + offering label map, used to populate the FA switcher and any offering-label lookups |
| GET | `/api/book?fa=dana` | full household list for one advisor (deep copy, so client-side mutation can't corrupt server state) |
| GET | `/api/household/{id}` | one household's full record **plus** `verdicts` — every offering's eligibility result, computed on the fly |
| GET | `/api/verdict/{id}/{offering_id}` | single-offering eligibility result |
| GET | `/api/composition/{id}?offerings=a,b,c` | composition-rule result over a specific comma-separated set of offerings |
| GET | `/api/nba/{kind}?fa=dana` | `kind` ∈ `meetings\|drift\|cio\|deep` — one of the four Today-page ranked lists |
| GET | `/api/tax-desk?fa=dana` | full book ranked by tax-alpha opportunity |
| GET | `/api/cross-sell?fa=dana` | eligibility-screened cross-sell opportunity list |
| POST | `/api/chat` | body `{fa, message, history}` → `{content, mode, context_households}`. `mode` is `"anthropic"`, `"openai"`, or `"local-grounded"` — the frontend doesn't need to branch on this, but it's useful for debugging/observability |
| POST | `/api/draft/{id}` | body `{fa, kind}` → generates (or regenerates) a draft, always returns a full draft record with `status:"pending"` |
| GET | `/api/draft/{id}?kind=meeting_prep` | fetch the current draft record for a household/kind; 404 if none has been generated yet |
| POST | `/api/draft/{id}/decision` | body `{kind, action, edited_content?, decided_by}` → `action` ∈ `approve\|decline\|edit`; `edit` requires `edited_content` (422 if missing) and sets status to `edited_approved` with the content replaced |
| GET | `/api/transition/{id}?offering=directIndexing` | the full transition-scenario payload (§8.6) |

### 9.2 Live-LLM calling pattern — reproduce exactly for both chat and drafts

Both `_live_chat` (for `/api/chat`) and `_live_draft` (for `/api/draft/{id}`) follow the **identical** pattern, and any future LLM-backed feature added to this app should follow it too:

1. Read `ATLAS_LLM_PROVIDER` env var (`"anthropic"` or `"openai"`, case-insensitive lowercase comparison; anything else, including unset, means "no live provider configured").
2. Build a `persona` system-prompt string that explicitly instructs the model to use *only* the supplied context and never invent facts.
3. Build the grounding `context` string from the appropriate service-layer function (`book_context` for chat, `household_draft_context` for drafts).
4. Make the actual HTTP call with `httpx.AsyncClient`, a configurable timeout (`ATLAS_LLM_TIMEOUT` env var, default 12s), to `https://api.anthropic.com/v1/messages` or `https://api.openai.com/v1/responses` depending on provider — model name itself is also env-configurable (`ATLAS_ANTHROPIC_MODEL`/`ATLAS_OPENAI_MODEL`) with a sensible default.
5. If no provider is configured, or the provider's required API key env var (`ANTHROPIC_API_KEY`/`OPENAI_API_KEY`) isn't set, the function returns `(None, None)` / `None` without making any network call at all.
6. **The calling endpoint always wraps the live call in `try/except Exception: pass`** and falls through to the deterministic local generator (`local_answer`/`generate_draft_local`) on *any* failure — timeout, network error, non-2xx response, malformed response shape, anything. This is the single most important behavioral contract in the app: **an LLM-backed feature must never surface an error to the advisor; it must silently degrade to a grounded local answer.**

### 9.3 Complete `app/main.py`

```python
from pathlib import Path
import os
from datetime import datetime,timezone
import httpx
from typing import Literal
from fastapi import FastAPI,HTTPException,Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from .data import RULE_STORE,FA_PROFILES,BY_ID,my_book
from .services import *

app=FastAPI(title='Atlas Advisor Console',version='1.0.0')
STATIC=Path(__file__).parent/'static'
app.mount('/static',StaticFiles(directory=STATIC),name='static')

def valid_fa(fa):
    if fa not in FA_PROFILES: raise HTTPException(404,'Advisor not found')
    return fa
@app.get('/')
def index(): return FileResponse(STATIC/'index.html')
@app.get('/reference')
def reference(): return FileResponse(STATIC/'reference.html')
@app.get('/api/health')
def health(): return {'status':'ok','pack_id':RULE_STORE['pack_id'],'offerings':len(RULE_STORE['offerings']),'rules':sum(len(o['rules']) for o in RULE_STORE['offerings'].values())}
@app.get('/api/meta')
def meta(): return {'advisors':FA_PROFILES,'offerings':{k:v['label'] for k,v in RULE_STORE['offerings'].items()},'pack_id':RULE_STORE['pack_id'],'policy_status':RULE_STORE['status']}
@app.get('/api/book')
def book(fa:str='dana'): return my_book(valid_fa(fa))
@app.get('/api/household/{household_id}')
def household(household_id:str):
    try:
        record=household_or_404(household_id)
        return {**record,'program':record.get('program','IAP'),'verdicts':all_verdicts(household_id)}
    except KeyError:raise HTTPException(404,'Household not found')
@app.get('/api/verdict/{household_id}/{offering_id}')
def verdict(household_id:str,offering_id:str):
    try:return offering_result(household_id,offering_id)
    except KeyError as e:raise HTTPException(404,str(e))
@app.get('/api/composition/{household_id}')
def composition(household_id:str,offerings:str=Query(...)):
    try:return composition_result(household_id,[x for x in offerings.split(',') if x])
    except KeyError as e:raise HTTPException(404,str(e))
@app.get('/api/nba/{kind}')
def nba_endpoint(kind:Literal['meetings','drift','cio','deep'],fa:str='dana'): return nba(kind,valid_fa(fa))
@app.get('/api/tax-desk')
def tax_endpoint(fa:str='dana'): return tax_desk(valid_fa(fa))
@app.get('/api/cross-sell')
def cross_endpoint(fa:str='dana'): return cross_sell(valid_fa(fa))
class ChatRequest(BaseModel):
    fa:str='dana';message:str=Field(min_length=1,max_length=4000);history:list[dict]=[]
async def _live_chat(req: ChatRequest):
    provider=os.getenv('ATLAS_LLM_PROVIDER','').lower()
    fa=FA_PROFILES[req.fa]
    persona=f"You are Atlas, an advisor-facing book copilot for {fa['name']}. Use only the supplied book context. Never invent clients, holdings, figures, eligibility or policy. Distinguish eligible, ineligible and needs-review outcomes."
    context=book_context(req.fa)
    timeout=float(os.getenv('ATLAS_LLM_TIMEOUT','12'))
    async with httpx.AsyncClient(timeout=timeout) as client:
        if provider=='anthropic' and os.getenv('ANTHROPIC_API_KEY'):
            r=await client.post('https://api.anthropic.com/v1/messages',headers={'x-api-key':os.environ['ANTHROPIC_API_KEY'],'anthropic-version':'2023-06-01','content-type':'application/json'},json={'model':os.getenv('ATLAS_ANTHROPIC_MODEL','claude-sonnet-4-6'),'max_tokens':700,'system':persona+'\n\nBOOK DATA:\n'+context,'messages':[{'role':'user','content':req.message}]});r.raise_for_status();return r.json()['content'][0]['text'],'anthropic'
        if provider=='openai' and os.getenv('OPENAI_API_KEY'):
            r=await client.post('https://api.openai.com/v1/responses',headers={'Authorization':'Bearer '+os.environ['OPENAI_API_KEY'],'content-type':'application/json'},json={'model':os.getenv('ATLAS_OPENAI_MODEL','gpt-5.4-mini'),'instructions':persona,'input':'BOOK DATA:\n'+context+'\n\nQUESTION:\n'+req.message});r.raise_for_status();d=r.json();return d.get('output_text') or ''.join(x.get('text','') for o in d.get('output',[]) for x in o.get('content',[])),'openai'
    return None,None

@app.post('/api/chat')
async def chat(req:ChatRequest):
    valid_fa(req.fa)
    try:
        content,mode=await _live_chat(req)
        if content:return {'content':content,'mode':mode,'context_households':len(my_book(req.fa))}
    except Exception:
        pass
    return {'content':local_answer(req.fa,req.message),'mode':'local-grounded','context_households':len(my_book(req.fa))}

class DraftRequest(BaseModel):
    fa:str='dana';kind:Literal['meeting_prep']='meeting_prep'
class DraftDecisionRequest(BaseModel):
    kind:Literal['meeting_prep']='meeting_prep'
    action:Literal['approve','decline','edit']
    edited_content:str|None=None
    decided_by:str='dana'

async def _live_draft(household_id:str,kind:str,fa:str)->str|None:
    if kind!='meeting_prep':return None
    provider=os.getenv('ATLAS_LLM_PROVIDER','').lower()
    fa_p=FA_PROFILES[fa]
    persona=(f"You are Atlas, drafting a meeting-prep brief for {fa_p['name']} ahead of a specific client meeting. "
        f"Use ONLY the household data supplied below. Never invent facts, holdings, figures, or eligibility. "
        f"Write in markdown with exactly these section headers, in this order: "
        f"'### What prompted this meeting', '### Portfolio snapshot', '### Concentration & risk', "
        f"'### CIO alignment', '### Suggested talking points' (3 to 5 numbered points), '### Eligible next steps'. "
        f"Start with a single '## Meeting prep — <household name>' title line. Be specific, cite real numbers, keep it concise.")
    context=household_draft_context(household_id)
    timeout=float(os.getenv('ATLAS_LLM_TIMEOUT','12'))
    async with httpx.AsyncClient(timeout=timeout) as client:
        if provider=='anthropic' and os.getenv('ANTHROPIC_API_KEY'):
            r=await client.post('https://api.anthropic.com/v1/messages',headers={'x-api-key':os.environ['ANTHROPIC_API_KEY'],'anthropic-version':'2023-06-01','content-type':'application/json'},json={'model':os.getenv('ATLAS_ANTHROPIC_MODEL','claude-sonnet-4-6'),'max_tokens':900,'system':persona,'messages':[{'role':'user','content':context}]});r.raise_for_status();return r.json()['content'][0]['text']
        if provider=='openai' and os.getenv('OPENAI_API_KEY'):
            r=await client.post('https://api.openai.com/v1/responses',headers={'Authorization':'Bearer '+os.environ['OPENAI_API_KEY'],'content-type':'application/json'},json={'model':os.getenv('ATLAS_OPENAI_MODEL','gpt-5.4-mini'),'instructions':persona,'input':context});r.raise_for_status();d=r.json();return d.get('output_text') or ''.join(x.get('text','') for o in d.get('output',[]) for x in o.get('content',[]))
    return None

@app.post('/api/draft/{household_id}')
async def create_draft(household_id:str,req:DraftRequest):
    try:household_or_404(household_id)
    except KeyError:raise HTTPException(404,'Household not found')
    valid_fa(req.fa)
    content=None
    try:content=await _live_draft(household_id,req.kind,req.fa)
    except Exception:content=None
    mode='model-drafted' if content else 'local-grounded'
    if not content:content=generate_draft_local(household_id,req.kind)
    record={'household_id':household_id,'kind':req.kind,'content':content,'status':'pending','mode':mode,
        'created_at':datetime.now(timezone.utc).isoformat(),'decided_at':None,'decided_by':None}
    DRAFT_STORE[draft_key(household_id,req.kind)]=record
    return record

@app.get('/api/draft/{household_id}')
def get_draft(household_id:str,kind:str='meeting_prep'):
    key=draft_key(household_id,kind)
    if key not in DRAFT_STORE:raise HTTPException(404,'No draft yet for this household/kind')
    return DRAFT_STORE[key]

@app.post('/api/draft/{household_id}/decision')
def decide_draft(household_id:str,req:DraftDecisionRequest):
    key=draft_key(household_id,req.kind)
    if key not in DRAFT_STORE:raise HTTPException(404,'No draft yet for this household/kind')
    rec=DRAFT_STORE[key]
    if req.action=='approve':rec['status']='approved'
    elif req.action=='decline':rec['status']='declined'
    elif req.action=='edit':
        if not req.edited_content:raise HTTPException(422,'edited_content required for edit action')
        rec['content']=req.edited_content;rec['status']='edited_approved'
    rec['decided_at']=datetime.now(timezone.utc).isoformat();rec['decided_by']=req.decided_by
    return rec

@app.get('/api/transition/{household_id}')
def transition(household_id:str,offering:str=Query(...)):
    try: return transition_scenario(household_id,offering)
    except KeyError as ke: raise HTTPException(404,str(ke))
```
