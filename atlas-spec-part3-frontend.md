# Atlas Advisor Console — Rebuild Specification (Part 3 of 3): Frontend, UX & Testing

**This is Part 3 of a 3-part specification.** Part 1 covers architecture, design tokens, and backend logic; Part 2 is the raw reference data. This file covers everything about the frontend a person actually sees and clicks — the JavaScript application architecture, a list of real bugs found and fixed during development (read this before writing any new view — several of these are easy to reintroduce), the exact UX behavior of all 8 views, the complete `index.html` and `app.js` source, the testing/verification approach, and a final build-and-acceptance checklist.

The design tokens and CSS referenced throughout this file (`.card`, `.pill`, `.chip`, `.u`, `.go`, etc.) are defined in Part 1 §4 — this file assumes that stylesheet already exists and describes how the JavaScript uses it, rather than repeating it.

---


---

## 10. Frontend architecture (`app/static/app.js`)

### 10.1 Boot sequence

On script load, an IIFE at the bottom of the file: fetches `/api/meta` to populate the advisor switcher `<select>`, sets it to the default advisor (`dana`), calls `loadBook()` (fetches `/api/book?fa=dana`, stores the result in `state.book` and a `state.byId` index keyed by household id), paints the FA profile card and the "Rule engine ON" toggle in the topbar, then calls `render()` for the first time. Any failure in this sequence replaces the entire `#view` container with a plain error message — there's no partial/degraded boot state.

**This ordering matters for a specific reason documented below in §10.7**: anything that computes a value derived from `myBook()` (like a household count) must not be computed at module-parse time, only at actual render time, because `state.book` is empty until `loadBook()`'s `await` resolves.

### 10.2 Global state shape

```js
let state = { view:'today', client:null, fa:'dana', meta:null, book:[], byId:{}, verdicts:{}, composition:{} };
```

Plus several other module-level `let`s that are effectively part of application state but kept separate for historical/organizational reasons: `bookFilter` (Book of Business segment filter), `chatLog`/`sending` (chat), `themePref`. When a new stateful sub-view is added (as draft review and the transition workbench were), its own target — `state.draftTarget = {householdId, kind}`, `state.transitionTarget = {householdId, offering}` — is added directly onto the `state` object rather than as a new top-level `let`, since these are genuinely part of "what view are we looking at," unlike chat log or theme preference which are cross-cutting.

`state.verdicts` is a **cache**: `ensureVerdicts(id)` only fetches `/api/household/{id}` (which returns every offering's verdict in one call) if `state.verdicts[id]` isn't already populated — repeated visits to the same client deep-dive don't refetch.

### 10.3 Icon, formatting, and avatar conventions

- Every icon is an inline SVG string in the `I` object (`I.today`, `I.book`, `I.chat`, ... `I.people`), `viewBox="0 0 24 24"`, `stroke="currentColor"` so it inherits text color, no `fill`. **Icons rendered inside a `.u` or `.go` inline text link must be explicitly sized** — see the pitfall in §10.7; there is no automatic sizing for a bare inline SVG.
- `avColor(id)` hashes a household's id string to pick one of 8 fixed hex colors for its avatar background — deterministic per id, not random, so the same household always gets the same color across sessions.
- `initials(name)` strips non-letters, takes the first letter of up to the first 2 words, uppercases.
- `avatarEl(c, cls)` returns a `<div class="avatar ...">` with those two combined.
- `fmtM(n)` — compact magnitude formatting: `$1.23B` / `$4.5M` / `$12K` / `$340` depending on magnitude. Used for every AUM/value figure in tables and cards.
- `fmt$(n)` — full formatted dollar figure with thousands separators, no compaction (`$1,234,567`).
- `fmtSigned(n)` — like `fmt$` but always prefixed with `+` or `−` (real minus sign, not hyphen) — used for gain/loss figures.
- `meetWhen(days)` — `0→"Today"`, `1→"Tomorrow"`, else `"In N days"`.
- `gl(holding)` / `clientGL(c)` / `clientHarvest(c)` — **client-side duplicates** of the same-named Python functions in `services.py`/`data.py`. This duplication is intentional: the frontend needs these for optimistic/instant UI updates and sorting without a round trip, while the backend needs them for API responses; both must be kept in exact numeric agreement (same null-cost handling: a holding with `cost == null` contributes `0` to gain/loss, not `NaN` or an error).
- `esc(s)` — the one and only HTML-escaping helper; every piece of user-influenced or LLM-influenced text that gets interpolated into an `innerHTML` template string **must** go through `esc()` first, no exceptions, since there is no other XSS boundary in this app.

### 10.4 The `api(path, opt)` helper

A four-line wrapper around `fetch`: throws a plain `Error` (with the response body as the message) on any non-2xx response, otherwise returns the parsed JSON body. Every single network call in the frontend goes through this, so error handling at every call site is a uniform `try { await api(...) } catch(e) { /* show e.message */ }`.

### 10.5 Routing — no router library

`state.view` is a plain string; `setView(v, client=null)` sets `state.view` and `state.client`, then calls `render()`. `render()` is the single dispatcher:

```js
async function render(){
  paintNav();
  // ...breadcrumb logic keyed on state.view...
  const v = document.getElementById('view');
  if(state.view === 'today') v.innerHTML = viewToday();
  else if(state.view === 'book') v.innerHTML = viewBook();
  else if(state.view === 'chat'){ v.innerHTML = viewChat(); /* focus input */ }
  else if(state.view === 'tax') v.innerHTML = viewTax();
  else if(state.view === 'crosssell') v.innerHTML = viewCrossSell();
  else if(state.view === 'client') await viewClient(state.client);
  else if(state.view === 'draftReview') await viewDraftReview(state.draftTarget.householdId, state.draftTarget.kind);
  else if(state.view === 'transition') await viewTransition(state.transitionTarget.householdId, state.transitionTarget.offering);
}
```

Views that are pure synchronous string-builders (`viewToday`, `viewBook`, `viewChat`, `viewTax`, `viewCrossSell`) are called and their return value assigned directly to `innerHTML`. Views that need to fetch data first (`viewClient`, `viewDraftReview`, `viewTransition`) are `async` and write to `#view` themselves (first a loading placeholder, then the real content once the fetch resolves) rather than returning a string — this split exists because you cannot `await` inside a plain string-building expression, and a visible "loading…" state is required for any view that does a network round trip before it can render.

Two dedicated open-helpers exist for the two views that need a compound target (household + a sub-parameter) rather than just a single id:
```js
async function openDraft(householdId, kind='meeting_prep'){ state.view='draftReview'; state.draftTarget={householdId,kind}; await render(); /* scroll main to top */ }
async function openTransition(householdId, offering){ state.view='transition'; state.transitionTarget={householdId,offering}; await render(); /* scroll main to top */ }
```
Any new sub-view that needs more than one parameter to know what to show should follow this exact pattern: a dedicated `openX` function that sets both `state.view` and a `state.xTarget` object, rather than overloading `setView`'s signature further.

### 10.6 Event delegation — one global click handler, and **order matters**

There is exactly **one** `document.addEventListener('click', ...)` for the entire app (plus separate ones for `input`/`keydown`, which don't overlap in concern). Every interactive, non-native element (spans, divs styled as buttons, table rows) is made clickable by giving it a `data-*` attribute and matching it in this handler via `e.target.closest('[data-*]')` — **not** by attaching a per-element `onclick` at render time, except for the small number of view-local dynamic elements (draft/transition action buttons) that are re-rendered often enough that direct `element.onclick = ...` assignment right after building the DOM is more convenient; both patterns coexist in the codebase and that's fine, but the global delegated attributes are the backbone for anything that appears in more than one view.

**The check order in the handler is significant and must be preserved exactly:**

```js
document.addEventListener('click', e => {
  const ex = e.target.closest('[data-explain]'); if(ex){ ...; return; }
  const nav = e.target.closest('[data-nav]'); if(nav){ setView(nav.dataset.nav); return; }
  const dr = e.target.closest('[data-draft]'); if(dr){ ...; return; }
  const tr = e.target.closest('[data-transition]'); if(tr){ ...; return; }
  const cl = e.target.closest('[data-client]'); if(cl){ setView('client', cl.dataset.client); return; }
  const ask = e.target.closest('[data-ask]'); if(ask){ ...; return; }
  const send = e.target.closest('#sendBtn'); if(send){ ...; return; }
});
```

**Never put both `data-nav` and `data-client` on the same element.** `data-nav` is checked first and calls `setView(nav.dataset.nav)` with **no second argument**, so if an element also carries `data-client`, that value is silently ignored and `state.client` is reset to `null` — a real bug that shipped and was later fixed: a "back to client" link had `data-nav="client" data-client="${id}"`, and because `'client'` isn't itself a valid single-argument nav target (it always needs an id), the click landed on `viewClient(null)`, which failed and silently fell back to the Book of Business list instead of the intended household. **The fix, and the rule going forward: a link back to a specific household uses `data-client="{id}"` alone, never combined with `data-nav`.**

### 10.7 Known pitfalls — read before writing any new view

These are real bugs found and fixed during development. Each one represents a class of mistake that is easy to reintroduce if this app is rebuilt from a paraphrased description instead of from working code + these notes.

1. **Never invent a CSS class name and assume it's styled.** Early in development, an entire chat view was built using plausible-sounding class names (`chat-wrap`, `chat-hero`, `chat-intro`, `chat-starters`) that did not exist anywhere in the stylesheet. Nothing rendered — including one raw inline SVG icon that, with no CSS to constrain it, rendered at a huge, effectively-random intrinsic size, producing a giant broken-looking shape on screen. **Rule: before writing any new view's markup, grep the actual stylesheet for the exact class names you intend to use. If a class doesn't exist yet, either reuse an existing one or add a real CSS rule for it — never assume a plausible name is already styled.**

2. **Inline SVG icons need explicit `width`/`height` in CSS; there is no sane default.** A "Model transition ›" arrow icon, reused inside differently-sized flex/grid tiles across the eligibility grid, rendered anywhere from 73px to 144px square — wildly different per tile — because nothing constrained its size. The fix was a global rule: `.u svg, .go svg{ width:11px; height:11px; flex-shrink:0; vertical-align:-1px; }`. **Rule: any inline-icon-in-text pattern needs a corresponding `<container> svg{width;height;flex-shrink:0}` rule the first time it's introduced, not assumed to "just look like the other icons."**

3. **Every clickable, non-native element needs an explicit `cursor:pointer`.** A `<span>` made clickable purely through JS event delegation shows the default text cursor unless `cursor:pointer` is set explicitly — browsers do not infer clickability from a click listener on an ancestor. This was missed on the `.go` footer links and the `.u` inline links (`.u` had *no* base CSS rule at all originally, relying on ad hoc inline `style="cursor:pointer"` at only some call sites, which is why one instance — the hero's "Ask a question" — was completely unstyled). **Rule: define a real base rule (`.u{color:...;cursor:pointer;font-weight:600;}`) once, and every future usage of that class is correct for free — don't rely on remembering to add an inline style at each call site.**

4. **A markdown renderer written for one use case silently breaks when reused for richer content.** `mdToHtml()` was originally written only for short chat replies and supported bold text and lists but not `#`/`##`/`###` headers. When the same function was reused to render meeting-prep drafts and transition-workbench notes (which do use `##`/`###` section headers), the literal `## `/`### ` characters rendered as plain text instead of real headings. **Rule: when a markdown renderer is extended to a new content type, check the new content's actual markdown syntax against what the renderer supports — don't assume "it's markdown so it'll be fine."** (The fix added explicit heading-line detection before the list/paragraph checks, converting to real `<h2>`/`<h3>` tags, plus matching CSS: `.bubble h2` styled with the serif display font, `.bubble h3` as a small-caps section label — both are the pattern to reuse for any future rich-content view rather than inventing a new heading style.)

5. **Anything computed from asynchronously-loaded state must be computed lazily, not at module-parse time.** The chat view's welcome message originally read `` `I can see all ${myBook().length} households...` `` as part of a module-level `let chatLog = [...]` initializer — which runs at script-parse time, before the boot sequence's `await loadBook()` has resolved, so it always printed "0 households." **Rule: any string/value that depends on `state.book`/`state.byId` must be computed inside a function called at actual render time (or lazily on first access), never baked into a top-level variable initializer.**

6. **A visual-hierarchy request ("this should be bigger / same size as that") is about which CSS class an element uses, not about picking a bigger pixel value ad hoc.** When asked to promote a page's subtitle to the same visual weight as its main title, the correct fix was to give both elements the *same existing class* (`.nm.serif`, already used for household-name headers elsewhere) rather than inventing a new font-size. This keeps every "big serif header" in the app visually and semantically consistent — there is exactly one class for that role, and it's reused, not reinvented per screen.

7. **Every eligibility/gap/status list must render something even in the empty case.** The transition workbench's gap-analysis list always emits at least a `{"severity":"clear","message":"No structural blockers. Ready to initiate."}` row rather than an empty `<div>` when there's nothing to flag — an empty state that reads as "nothing to show" is indistinguishable from "this feature is broken" to an advisor scanning quickly; make the empty/clear case an explicit, positively-worded row instead.


---

## 11. View-by-view UX specification

The app shell (`index.html`) is: a fixed dark sidebar (logo mark, advisor switcher, nav items: Today / Book of Business / Ask Atlas, then a "PROGRAMS" section: Tax Overlay Desk / Cross-Sell Radar, then a footer with the current advisor's avatar/name/title), a topbar (page title on the left, a global search input with a `/` keyboard shortcut to focus it, a "Rule engine ON" status pill on the right), and a single `<main id="view">` content region that every view renders into. A `#crumb` breadcrumb sits just above `#view` and is rewritten by `render()` on every navigation.

### 11.1 Today (`viewToday`, default view on load)

A dark hero card (`.hero`) — always dark regardless of light/dark theme — containing: a serif "Good morning, {advisor's first name}." greeting, today's date + "· Book review", a one-paragraph plain-English brief with bolded figures (total AUM, household count, meetings needing prep within 5 days, count of households drifting on concentration/allocation, total harvestable-loss dollar figure, count of accounts with >$10K harvestable losses, count of unactioned cross-sell openings), a small "Atlas prioritized your book at 6:00 AM · Ask a question" line (the "Ask a question" text is a `.u` inline link to the chat view), and a 4-stat row (Total AUM / Annualized revenue / Meetings this week / Est. tax alpha available) — **each stat block uses `flex:1 1 140px` so the four of them spread evenly across the hero's full width**, they must never cluster on one side leaving visible dead space.

Below the hero: a "Next best actions" section header, then a 4-card grid (`.nba-grid`) of ranked action cards — Meeting prep, Concentration drift, CIO alignment, Top relationships (`nbaMeetings`, `nbaDrift`, `nbaCIO`, `nbaDeep` respectively). Each card shows its top few ranked rows and a footer line; the Meeting Prep card's footer has a "Draft with Atlas ›" link (`.go` class, arrow icon) which opens the **draft review workbench** (§11.7) for whichever household has the nearest upcoming meeting — not a generic chat redirect.

### 11.2 Book of Business (`viewBook`)

A segment filter row (`.filters .seg`, "All / Private Wealth / HNW / Institutional" or whatever segments are present in the book) followed by a full-width table of every household in the advisor's book: avatar, name + entity, segment, AUM, YTD return (colored green/red), next meeting (or "—"), and a row-level "harvestable" indicator. Clicking anywhere on a row (`data-client="{id}"`) opens that household's deep-dive.

### 11.3 Client deep-dive (`viewClient`, async)

The richest view. Header (`.cli-head`): avatar, household name (serif, `.nm`), a `.sub` line of entity/segment/client-since/risk-mandate, contact name, and AUM prominently right-aligned. Below that, a 4-up KPI row (YTD return, unrealized gain/loss, harvestable losses, annualized revenue), then a two-column layout: **Holdings & tax lots** (every position: symbol, name, asset class, market value, a proportional weight bar, gain/loss) alongside **Allocation vs. CIO target** (a bar per asset-class bucket comparing current % to target %, plus a drift callout pill if the household has a CIO alignment concern).

Below that: **"Next best actions for this household"** card header with a context-sensitive action button — **"Draft meeting prep"** (primary-styled, opens the draft workbench for *this* household) if the household has a scheduled meeting, otherwise a plain **"Ask Atlas"** button that opens the general chat.

Then two eligibility grid cards: **"Program eligibility"** (or the household's actual program family label) and **"Tax & overlay services"** (or, for an MGI-program household, **"Guided Investing (MGI) tax services"**). Each renders every applicable offering as a small tile (`.elig`): an icon, the offering label, a verdict chip with a small **"i" explain button** (`data-explain`) that opens a positioned popover (`showExplain`) showing the exact rule trace (message, source document/page/section, or an internal-review notice per §6.3's client-safe boundary) — and, **only when the verdict is ELIGIBLE and the offering is not already enrolled**, a small `"Model transition ›"` link (`.u`, `data-transition="{householdId}:{offeringKey}"`) that opens the **transition workbench** (§11.8) for that exact household+offering pair.

A composition panel (`compositionPanelHtml`) appears when the household holds 2+ offerings simultaneously, showing the composition-rule verdict for that specific combination (see §6.4).

### 11.4 Ask Atlas (`viewChat`)

A two-column layout: `.chatwrap` containing `.chat` (the conversation panel: header with a gradient "spark" icon mark and a live-dot "Grounded on your live book" subtitle, a scrolling `.stream` of `.msg.user`/`.msg.bot` bubbles, and a `.composer` with 6 suggestion chips shown only before the first user message plus an `.inputrow` textarea + send button) and a `.ctx-panel` sidebar (a "Top relationships" list of the 5 largest households by AUM, each clickable to their deep-dive, and a static "What Atlas can do" card).

The welcome message is computed lazily on first render of the view (never at module load — see pitfall #5) so it reports the correct household count. Sending a message posts to `/api/chat` with the last 8 turns of history; while waiting, a typing-indicator bubble (three animated dots) is shown and replaced in place once the response arrives — never appended as a separate bubble.

### 11.5 Tax Overlay Desk (`viewTax`)

A single ranked table across the whole book, sorted by harvestable-loss dollar magnitude descending: household, harvestable losses, estimated tax alpha, and an eligible-overlay-services-not-yet-enrolled count per household (using `I.people` for that column's icon).

### 11.6 Cross-Sell Radar (`viewCrossSell`)

A ranked, eligibility-screened list (see `cross_sell()` in services.py, §8.3) — every row is a real, currently-eligible-but-unenrolled offering for a real household, sorted by that household's revenue. Each row shows a short "why now" reason (`crossReason`) synthesized from the household's actual situation (e.g. referencing a real concentration flag or a real harvestable-loss figure when the offering being recommended is one that would address it).

### 11.7 Draft review — human-in-the-loop meeting prep (`viewDraftReview` / `renderDraftReview`, async)

Entered via `openDraft(householdId, kind)`. Layout: a `data-client="{id}"`-only backlink to the household's deep-dive (never combine with `data-nav`, per pitfall #6.6 in §10.6), then — **only when more than one household in the book has an upcoming meeting** — a `<select id="draftHouseholdSelect">` dropdown ("Drafting meeting prep for [Household · timing ▾]") listing every such household, letting the advisor switch which one's draft they're looking at without leaving the page; its `change` event re-calls `openDraft` for the newly selected household. Below that: a household header (avatar, "Meeting prep brief" title, "For {household}" subtitle, and a status pill — Awaiting your review / Approved / Declined / Edited & approved), a "Proposed draft" card rendering the markdown content (via `mdToHtml`, which must support `##`/`###` headers — pitfall #4), and an action bar that changes by state:

- **`pending`**: Approve (primary button) / Edit / Decline (styled with the red token inline, no dedicated `.btn.danger` class exists — don't invent one, just inline `style="color:var(--red);border-color:..."`) plus a small "FA sign-off required — nothing is sent automatically" note.
- **editing** (after clicking Edit): the rendered content is replaced by a plain `<textarea>` pre-filled with the raw markdown, with Save & approve / Cancel buttons.
- **decided** (`approved`/`declined`/`edited_approved`): a one-line status summary with the decision timestamp, plus a "Draft again" button that regenerates from scratch.

Every action calls `POST /api/draft/{id}/decision` and re-renders in place from the returned record — there is no client-side-only state mutation; the server's `DRAFT_STORE` record is always the source of truth for what's displayed.

### 11.8 Transition workbench (`viewTransition` / `renderTransition`, async)

Entered via `openTransition(householdId, offering)`, triggered from a "Model transition ›" link on an eligible-not-enrolled offering tile (§11.3). Layout, top to bottom:

1. Backlink to the household's deep-dive (`data-client` only, same rule as draft review).
2. Header: a small `.eyebrow` label reading "TRANSITION WORKBENCH", then **the offering's name as the primary large serif header** (`.nm.serif`) — not a generic "Transition workbench" title; the specific offering is the important piece of information, so it gets the visual weight — and **the household's name directly below it, in the same `.nm.serif` class and font size** (muted color to keep it visually secondary despite being the same size), plus a right-aligned pill showing "Already enrolled" / "Eligible · not yet enrolled" / the raw verdict string.
3. **Current state** card: position count + AUM in the header; a table of the household's top 6 holdings by market value (symbol, name, asset class, market value, weight %, unrealized G/L colored green/red); a concentration-flag callout banner if applicable.
4. **Gap analysis** card: every blocker/consideration from `_gap_analysis` as a row with a severity pill (Required / Recommended / Scope carve-out / Needs review / Clear) and a plain-English message — never an empty list (pitfall #7).
5. For a `trade_modelable` offering: a **Proposed trades** table (action badge — SELL red / STAGE SELL blue / HARVEST amber / BUY brand-teal / NOTE muted — symbol, name, value, realized G/L, plain-English rationale) followed by a **Target state** card: a 5-metric strip (Reallocated / Realized gain / Offset by harvest / Net taxable / Est. ongoing tax alpha), a residual-concentration callout if any concentration survives the transition, and a bulleted notes list (wash-sale/basis-reset caveats, etc.).
   For a `procedural` offering: a single **Onboarding steps** card with a numbered checklist instead of any trade table.
6. A closing disclaimer line: "Illustrative modeling for advisor review. Actual trade generation, tax impact, and eligibility subject to compliance sign-off and the strategy shelf at execution." — always present, since every trade proposal in this app is explicitly illustrative, not a real order.


---

## 12. Complete `app/static/index.html`

The entire HTML shell. Note the advisor-switcher `<select id="faSwitch">` is populated dynamically by the boot sequence in `app.js`, not hardcoded here.

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<title>Atlas — Advisor Console</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Public+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="/static/styles.css" />
</head>
<body>
<div id="app">
  <!-- SIDEBAR -->
  <aside class="rail">
    <div class="brand">
      <div class="mark" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2 3 7l9 5 9-5-9-5Z"/><path d="M3 12l9 5 9-5"/><path d="M3 17l9 5 9-5"/></svg>
      </div>
      <div>
        <div class="name">Atlas</div>
        <div class="sub">Meridian Private Wealth</div>
      </div>
    </div>
    <nav class="nav" id="nav">
      <div class="lbl">WORKSPACE</div>
      <button data-nav="today" class="on"></button>
      <button data-nav="book"></button>
      <button data-nav="chat"></button>
      <div class="lbl">PROGRAMS</div>
      <button data-nav="tax"></button>
      <button data-nav="crosssell"></button>
    </nav>
    <div class="foot">
      <div class="av" id="faAvatar">DW</div>
      <div style="min-width:0;flex:1">
        <div class="who" id="faWho">Dana Whitfield</div>
        <select id="faSwitch" title="Switch advisor / book of business" style="font:inherit;font-size:11.5px;font-weight:600;color:var(--muted);background:transparent;border:none;padding:0;margin-top:1px;cursor:pointer;max-width:100%"></select>
      </div>
      <button class="tog" id="themeToggle" title="Toggle theme" aria-label="Toggle theme"></button>
    </div>
  </aside>

  <!-- MAIN -->
  <main class="main" id="main">
    <div class="topbar">
      <div class="crumb" id="crumb"><b>Today</b></div>
      <div class="search">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
        <input id="globalSearch" placeholder="Search clients, holdings, programs…" />
        <span class="kbd">/</span>
      </div>
      <button id="engineToggle" title="Rule engine is active — verdicts derived from client facts + policy pack" aria-pressed="true" style="display:inline-flex;align-items:center;font:inherit;font-size:12px;font-weight:600;color:var(--fg);background:var(--paper);border:1px solid var(--line);border-radius:20px;padding:8px 13px;margin-left:10px;cursor:pointer;white-space:nowrap;flex:0 0 auto"></button>
    </div>
    <div class="content" id="view"></div>
  </main>
</div>

<!-- MOBILE TABS -->
<nav class="mtabbar" id="mtabbar"></nav>

<script src="/static/app.js"></script>
</body>
</html>
```

---

## 13. Complete `app/static/app.js`

The entire frontend application. Reproduce exactly — every function referenced in §10 and §11 is defined here in full.

```javascript
/* Atlas Advisor Console — client-side renderer for the Python port.
 * Fetches from /api/* (rule engine + household data lives in Python).
 * The HTML/CSS is a byte-faithful port of the original artifact; only
 * the data-loading paths are new.
 */
'use strict';

/* ================= ICONS (verbatim from original) ================= */
const I = {
  today:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0Z"/><path d="M12 7v5l3 2"/></svg>',
  book:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5V5.5Z"/><path d="M4 20.5A2.5 2.5 0 0 0 6.5 23H20"/><path d="M9 7h7M9 11h5"/></svg>',
  chat:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H8l-4 4V5a2 2 0 0 1 2-2h13a2 2 0 0 1 2 2v10Z"/><path d="M8 9h8M8 13h5"/></svg>',
  tax:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6h9M9 12h9M9 18h5"/><path d="M4.5 6h.01M4.5 12h.01M4.5 18h.01"/></svg>',
  cross:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m7 17 4-4 3 3 4-6"/><path d="M3 3v18h18"/></svg>',
  meet:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4.5" width="18" height="16" rx="2.5"/><path d="M8 3v3M16 3v3M3 10h18"/></svg>',
  drift:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9 2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>',
  cio:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19V5a2 2 0 0 1 2-2h9l5 5v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z"/><path d="M14 3v6h6M8 13h8M8 17h5"/></svg>',
  deep:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3M11 8v6M8 11h6"/></svg>',
  spark:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v3M12 18v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M3 12h3M18 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/></svg>',
  arrow:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
  back:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M11 6l-6 6 6 6"/></svg>',
  send:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7Z"/></svg>',
  sun:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2M12 20v2M4 12H2M22 12h-2M5 5l1.5 1.5M17.5 17.5 19 19M19 5l-1.5 1.5M6.5 17.5 5 19"/></svg>',
  moon:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/></svg>',
  bank:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10 12 4l9 6M5 10v9M19 10v9M9 10v9M15 10v9M3 21h18"/></svg>',
  trust:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 4 6v5c0 5 3.4 8 8 10 4.6-2 8-5 8-10V6l-8-3Z"/><path d="m9 12 2 2 4-4"/></svg>',
  alt:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m7 15 3-4 3 3 4-7"/></svg>',
  index:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>',
  lend:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v10M9.5 9a2.5 2 0 0 1 2.5-1.5c1.4 0 2.5.7 2.5 1.8 0 2.4-5 1.6-5 4 0 1.1 1.1 1.8 2.5 1.8A2.5 2 0 0 0 14.5 15"/></svg>',
  ins:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 4 6v5c0 5 3.4 8 8 10 4.6-2 8-5 8-10V6l-8-3Z"/></svg>',
  give:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.8 4.6a5.5 5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5 0 0 0 0-7.8Z"/></svg>',
  people:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5"/><path d="M16 5.2a3.2 3.2 0 0 1 0 5.6M21 20c0-2.6-1.4-4.4-3.5-5.1"/></svg>',
};

/* ================= HELPERS ================= */
const AV_COLORS = ['#0C5D51','#26548F','#6b4a9e','#9E5E12','#A2323E','#2f7d6b','#3a5a8c','#7a5aa0'];
function avColor(id){ let h=0; for(const c of id) h=(h*31+c.charCodeAt(0))>>>0; return AV_COLORS[h%AV_COLORS.length]; }
function initials(name){ return name.replace(/[^A-Za-z ]/g,'').split(' ').filter(Boolean).slice(0,2).map(w=>w[0]).join('').toUpperCase(); }
function avatarEl(c, cls=''){ return `<div class="avatar ${cls}" style="background:${avColor(c.id)}">${initials(c.name)}</div>`; }
function fmtM(n){ const a=Math.abs(n); if(a>=1e9) return '$'+(n/1e9).toFixed(2)+'B'; if(a>=1e6) return '$'+(n/1e6).toFixed(1)+'M'; if(a>=1e3) return '$'+Math.round(n/1e3)+'K'; return '$'+Math.round(n); }
function fmt$(n){ const s=n<0?'-':''; return s+'$'+Math.round(Math.abs(n)).toLocaleString('en-US'); }
function fmtSigned(n){ return (n>=0?'+':'−')+'$'+Math.round(Math.abs(n)).toLocaleString('en-US'); }
function pctOf(part,total){ return (part/total*100); }
function meetWhen(d){ return d===0?'Today':d===1?'Tomorrow':`In ${d} days`; }
const gl = h => h.cost==null ? 0 : h.mv - h.cost;
const clientGL = c => c.holdings.reduce((s,h)=>s+gl(h),0);
const clientHarvest = c => c.holdings.filter(h=>gl(h)<0).reduce((s,h)=>s+gl(h),0);
const TAX_RATE = 0.238;
const esc = s => String(s??'').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

async function api(path, opt){
  const r = await fetch(path, opt);
  if(!r.ok) throw new Error(await r.text());
  return r.json();
}

/* ================= STATE (client-side book cache) ================= */
let state = { view:'today', client:null, fa:'dana', meta:null, book:[], byId:{}, verdicts:{}, composition:{} };
let bookFilter = 'all';

function myBook(){ return state.book; }
function byId(id){ return state.byId[id]; }

async function loadBook(){
  state.book = await api(`/api/book?fa=${state.fa}`);
  state.byId = Object.fromEntries(state.book.map(c => [c.id, c]));
  state.verdicts = {};
  state.composition = {};
}

/* ================= NBA / METRIC HELPERS ================= */
function totalAUM(){ return myBook().reduce((s,c)=>s+c.aum,0); }
function totalRev(){ return myBook().reduce((s,c)=>s+c.rev,0); }
function totalHarvest(){ return myBook().reduce((s,c)=>s+Math.abs(clientHarvest(c)),0); }
function meetings(){ return myBook().filter(c=>c.nextMeeting).sort((a,b)=>a.nextMeeting.inDays-b.nextMeeting.inDays); }
function drifts(){ return myBook().filter(c=>(c.concentration||[]).length || Math.abs(c.current.cash-c.target.cash)>=12)
  .map(c=>{ const conc=(c.concentration||[])[0]; const breach = conc? conc.pct-conc.threshold : (c.current.cash-c.target.cash);
    const label = conc? conc.label : 'Cash drag'; const pct = conc? conc.pct : c.current.cash;
    return {c, label, pct, threshold: conc?conc.threshold:c.target.cash, breach};
  }).sort((a,b)=>b.breach-a.breach); }
function cioMisaligned(){ return myBook().filter(c=>c.cio.score!=='Low').sort((a,b)=>({High:3,Medium:2,Low:1}[b.cio.score]-{High:3,Medium:2,Low:1}[a.cio.score])); }
function topClients(){ return [...myBook()].sort((a,b)=>b.aum-a.aum).slice(0,4); }

async function ensureVerdicts(id){
  if(state.verdicts[id]) return state.verdicts[id];
  const rec = await api(`/api/household/${id}`);
  state.byId[id] = { ...state.byId[id], ...rec };
  state.verdicts[id] = rec.verdicts || {};
  return state.verdicts[id];
}
function vFor(id, off){ return (state.verdicts[id]||{})[off]; }

function crossSell(){ return myBook().flatMap(c=>programList(c).filter(p=>p.status==='eligible').map(p=>({c,p}))); }

/* ================= OFFERING LISTS ================= */
function offeringLabel(k){
  const meta = state.meta && state.meta.offerings; return (meta && meta[k]) || k;
}
function programList(c){
  const P=[
    ['privateBanking', I.bank], ['trustEstate', I.trust],
    ['alternatives', I.alt], ['directIndexing', I.index],
    ['lending', I.lend], ['insurance', I.ins]
  ];
  return P.map(([k,icon])=>({k, label: offeringLabel(k), icon, status:(c.programs||{})[k]}));
}
function overlayList(c){
  const O=[
    ['taxManagedSMA', I.tax],['qlhOverlay', I.tax],['dtlhOverlay', I.index],
    ['temSms', I.alt],['transition', I.alt],['charitable', I.give]
  ];
  return O.map(([k,icon])=>({k, label: offeringLabel(k), icon,
    status:(c.overlays||{})[k]!==undefined?(c.overlays||{})[k]:null}));
}
function mgiOfferingList(c){
  const O=[['mgiTer', I.tax],['mgiQlh', I.tax],['mgiDtlh', I.index]];
  return O.map(([k,icon])=>({k, label: offeringLabel(k), icon, status:null}));
}

/* ================= VERDICT / STATUS RENDERING ================= */
function verdictPill(v){ if(!v) return '<span class="chip na">no rule</span>';
  const carve = v.scope_exclusions && v.scope_exclusions.length;
  if(v.verdict==='ELIGIBLE') return '<span class="chip eligible dot">Eligible'+(carve?'*':'')+'</span>';
  if(v.verdict==='CONDITIONAL') return '<span class="chip eligible dot">Conditional</span>';
  if(v.verdict==='NEEDS_REVIEW') return '<span class="pill amber">Needs review</span>';
  return '<span class="chip na">Ineligible</span>';
}
function verdictReason(v){ if(!v) return '';
  if(v.reasons && v.reasons.length) return v.reasons[0].message;
  if(v.scope_exclusions && v.scope_exclusions.length) return 'Carve-out: '+v.scope_exclusions[0].message;
  if(v.internal_only_reasons && v.internal_only_reasons.length) return '[FA-internal] '+v.internal_only_reasons[0].message;
  if(v.disclosures && v.disclosures.length) return v.disclosures[0].message;
  return '';
}
function statusChip(s){ return s==='enrolled'?'<span class="chip enrolled dot">Active</span>':s==='eligible'?'<span class="chip eligible dot">Eligible</span>':'<span class="chip na">N/A</span>'; }
function xinfoBtn(cid,off){ return `<button class="xinfo" data-explain data-client="${cid}" data-offering="${off}" title="Why this verdict?" aria-label="Explain verdict">i</button>`; }
function verdictCell(hh, off){ const v = vFor(hh.id, off); return verdictPill(v)+xinfoBtn(hh.id, off); }

/* ================= EXPLAIN POPOVER ================= */
function fmtSrc(source_doc){ if(!source_doc) return null;
  if(typeof source_doc==='string') return source_doc;
  return source_doc.map(s=>s.document_id+(s.pdf_page?' p.'+s.pdf_page:'')).join(' · ');
}
function _fmtVal(x, field){ if(typeof x==='boolean') return x?'true':'false'; if(x==null) return '\u2014 (unknown)';
  if(typeof x==='number'){ const money=/value|cash|advisory|pledgeable/i.test(field||''); return (money?'$':'')+Math.round(x).toLocaleString('en-US')+(/pct|_pct/i.test(field||'')?'%':''); }
  return String(x);
}
function closeExplain(){ const h=document.getElementById('xpopHost'); if(h) h.remove(); }
function _positionPop(pop, anchor){ if(window.innerWidth<=640) return;
  const r=anchor.getBoundingClientRect(), pw=pop.offsetWidth, ph=pop.offsetHeight;
  let left=r.left, top=r.bottom+8;
  if(left+pw>window.innerWidth-10) left=window.innerWidth-pw-10; if(left<10) left=10;
  if(top+ph>window.innerHeight-10) top=Math.max(10, r.top-ph-8);
  pop.style.left=(left+window.scrollX)+'px'; pop.style.top=(top+window.scrollY)+'px';
}
async function showExplain(cid, off, anchor){
  closeExplain();
  const hh = byId(cid); if(!hh) return;
  let v;
  try{ v = await api(`/api/verdict/${cid}/${off}`); } catch(e){ return; }
  const label = v.label || offeringLabel(off);
  const opSym = {EQ:'=', NEQ:'\u2260', IN:'\u2208', CONTAINS:'includes', GTE:'\u2265'};
  const fld = s => s.replace(/^account\.|^client\.|^fa\.|^target_strategy\.|^strategy\.|^transition\.|^scope\.|^policy\./,'').replace(/_/g,' ');
  const val = (x, f) => Array.isArray(x)?(x.length>5?x.slice(0,4).join(', ')+', \u2026+'+(x.length-4)+' more':x.join(', ')):_fmtVal(x, f);
  let rows = '';
  (v.trace||[]).forEach(t => {
    (t.inputs||[]).forEach(l => {
      const passed = l.passed !== undefined ? l.passed : t.passed;
      rows += `<tr class="${passed===false?'bad':passed===null?'unk':''}">
        <td>${fld(l.field)}</td><td class="v">${val(l.actual, l.field)}</td>
        <td class="t">${opSym[l.op]||l.op} ${val(l.expected!==undefined?l.expected:l.value, l.field)}</td>
        <td class="p">${passed===true?'<span class="ok">\u2713</span>':passed===false?'<span class="no">\u2717</span>':'<span class="unk">?</span>'}</td>
      </tr>`;
    });
  });
  const realReasons = (v.reasons||[]).filter(r=>!r.missing_fields);
  const reason = realReasons.length?`<div class="xreason bad">${[...new Set(realReasons.map(r=>r.message))].join(' ')}</div>`:'';
  const missing = v.missing_fields && v.missing_fields.length ? `<div class="xreason unk">Unresolved \u2014 missing or invalid: ${v.missing_fields.map(fld).join(', ')}. Per policy, unknown facts route to review rather than a silent approval or rejection.</div>` : '';
  const carve = (v.scope_exclusions||[]).map(s=>`<div class="xnote">\u25D1 ${s.message}${s.excluded_ids?' ('+s.excluded_ids.join(', ')+')':''}</div>`).join('');
  const disc = (v.disclosures||[]).map(d=>`<div class="xnote">\u00A7 ${d.message}</div>`).join('');
  const realInternal = [...new Set((v.internal_only_reasons||[]).filter(r=>!r.missing_fields).map(r=>r.message))];
  const faint = realInternal.map(m=>`<div class="xnote fa">FA-internal \u00B7 ${m}</div>`).join('');
  let prereq = '';
  if(v.prerequisite && v.prerequisite.internal_only_reasons && v.prerequisite.internal_only_reasons.length){
    prereq = v.prerequisite.internal_only_reasons.map(r=>`<div class="xnote fa">Prerequisite (IAP enrollment) \u00B7 ${r.message}</div>`).join('');
  } else if(v.prerequisite && v.prerequisite.verdict==='INELIGIBLE'){
    prereq = `<div class="xnote">Prerequisite (IAP enrollment) is not met for this account \u2014 ${(v.prerequisite.reasons||[]).map(r=>r.message).join(' ')}</div>`;
  }
  const srcs = [...new Set((v.trace||[]).map(t=>fmtSrc(t.source_doc)).filter(Boolean))];
  const host = document.createElement('div'); host.className='xpop-back'; host.id='xpopHost';
  host.innerHTML = `<div class="xpop" role="dialog" aria-label="Eligibility explanation">
    <div class="xpop-h"><div class="xpop-t">${label}</div>${verdictPill(v)}</div>
    ${reason}${missing}
    <div class="xpop-sec">Inputs evaluated <span class="muted2">\u2014 derived fields the rules read</span></div>
    <div class="xtbl-wrap"><table class="xpop-tbl"><colgroup><col class="c1"><col class="c2"><col class="c3"><col class="c4"></colgroup><thead><tr><th>Derived field</th><th>Value</th><th>Test</th><th></th></tr></thead><tbody>${rows||'<tr><td colspan="4" class="muted2">No field predicates \u2014 this offering attaches only conditions/disclosures.</td></tr>'}</tbody></table></div>
    ${(carve||disc||faint||prereq)?`<div class="xpop-sec">Notes</div>${carve}${disc}${faint}${prereq}`:''}
    ${srcs.length?`<div class="xsrc">source: ${srcs.join(' \u00B7 ')}</div>`:''}
    <button class="xpop-x" aria-label="Close">\u00D7</button>
  </div>`;
  document.body.appendChild(host);
  _positionPop(host.querySelector('.xpop'), anchor);
  host.addEventListener('click', e => { if(e.target===host || e.target.closest('.xpop-x')) closeExplain(); });
}

/* ================= COMPOSITION PANEL ================= */
function compositionVerdictPill(cv){
  const map={CONFIRMED_ELIGIBLE:['chip eligible dot','Confirmed eligible'],ELIGIBLE_WITH_CARVEOUT:['chip eligible dot','Eligible, scoped'],
    CONDITIONAL:['chip eligible dot','Conditional'],NEEDS_REVIEW:['pill amber','Needs review'],CONFIRMED_INELIGIBLE:['chip na','Confirmed ineligible']};
  const [cls,label]=map[cv]||['chip na',cv]; return `<span class="${cls}">${label}</span>`;
}
async function compositionPanelHtml(c){
  const cacheKey = c.id + '|TET';
  let composition = state.composition[cacheKey];
  if(!composition){
    try { composition = await api(`/api/composition/${c.id}?offerings=transition,taxManagedSMA,qlhOverlay,dtlhOverlay`); }
    catch(e){ return ''; }
    state.composition[cacheKey] = composition;
  }
  const ids = ['transition','taxManagedSMA','qlhOverlay','dtlhOverlay'];
  const rows = ids.map(id => { const v=vFor(c.id, id); const label=offeringLabel(id);
    return `<div class="elig"><div class="eic" style="background:var(--brand-tint);color:var(--brand)">${I.tax}</div>
      <div style="min-width:0"><div class="en">${label}</div></div><div class="est">${verdictPill(v)}</div></div>`;
  }).join('');
  const notes = (composition.notes||[]).map(n=>`<div class="xnote" style="margin-top:6px">${n.offerings?('<b>'+n.offerings.join(' + ')+':</b> '):''}${n.message}</div>`).join('');
  return `<div class="card" style="margin-top:16px">
    <div class="ch"><h3>TET-family service composition</h3>${compositionVerdictPill(composition.verdict)}</div>
    <div class="cbp">
      <div class="es" style="margin-bottom:10px;color:var(--muted)">Considered together as a set (TET, TER, QLH, DTLH) \u2014 composition is evaluated separately from each service's own eligibility, and an unspecified pairing is never assumed compatible.</div>
      <div class="elig-grid">${rows}</div>
      ${notes}
    </div>
  </div>`;
}

/* ================= NAV / TITLE ================= */
const NAVITEMS = [
  {k:'today', label:'Today', icon:I.today, badge:()=>meetings().filter(m=>m.nextMeeting.inDays<=5).length},
  {k:'book', label:'Book of Business', icon:I.book, badge:()=>myBook().length},
  {k:'chat', label:'Ask Atlas', icon:I.chat},
  {k:'tax', label:'Tax Overlay Desk', icon:I.tax},
  {k:'crosssell', label:'Cross-Sell Radar', icon:I.cross, badge:()=>crossSell().length},
];

function paintNav(){
  const nav = document.getElementById('nav');
  nav.querySelectorAll('button[data-nav]').forEach(b => {
    const item = NAVITEMS.find(n => n.k === b.dataset.nav); if(!item) return;
    const on = state.view === b.dataset.nav || (b.dataset.nav === 'book' && (state.view === 'client' || state.view === 'draftReview' || state.view === 'transition'));
    b.className = on ? 'on' : '';
    const badge = item.badge ? `<span class="cnt">${item.badge()}</span>` : '';
    b.innerHTML = `${item.icon}<span>${item.label}</span>${badge}`;
  });
  const mt = document.getElementById('mtabbar');
  mt.innerHTML = NAVITEMS.map(n => `<button data-nav="${n.k}" class="${state.view===n.k||(n.k==='book'&&(state.view==='client'||state.view==='draftReview'||state.view==='transition'))?'on':''}">${n.icon}<span>${n.label.split(' ')[0]}</span></button>`).join('');
}

function paintFaProfile(){
  const fa = state.meta && state.meta.advisors && state.meta.advisors[state.fa]; if(!fa) return;
  const av = document.getElementById('faAvatar'), who = document.getElementById('faWho'), sw = document.getElementById('faSwitch');
  if(av) av.textContent = fa.initials || initials(fa.name);
  if(who) who.textContent = fa.name;
  if(sw) sw.value = fa.id;
}
function paintEngineToggle(){
  const b = document.getElementById('engineToggle'); if(!b) return;
  b.innerHTML = `<span style="width:8px;height:8px;border-radius:50%;background:var(--brand);display:inline-block;margin-right:7px"></span>Rule engine ON`;
  b.setAttribute('aria-pressed','true');
}

/* ================= VIEW: TODAY ================= */
function viewToday(){
  const meetSoon = meetings().filter(m => m.nextMeeting.inDays <= 5).length;
  const brief = `You're managing <b>${fmtM(totalAUM())}</b> across <b>${myBook().length} households</b>. Today: <b>${meetSoon}</b> meetings need prep, <b>${drifts().length}</b> households are drifting on concentration or allocation, <b>${fmtM(totalHarvest())}</b> in losses are harvestable across <b>${myBook().filter(c=>Math.abs(clientHarvest(c))>10000).length}</b> accounts, and <b>${crossSell().length}</b> cross-sell openings are unactioned.`;
  const fa = state.meta && state.meta.advisors && state.meta.advisors[state.fa];
  const firstName = fa ? fa.name.split(' ')[0] : 'there';
  return `
  <div class="hero reveal">
    <div class="greet serif">Good morning, ${firstName}.</div>
    <div class="date">${new Date().toLocaleDateString('en-US',{weekday:'long', month:'long', day:'numeric'})} \u00b7 Book review</div>
    <div class="brief">${brief}</div>
    <div class="agentline"><span class="live"></span> Atlas prioritized your book at 6:00 AM \u00b7 <span class="u" data-nav="chat">Ask a question</span></div>
    <div class="stats">
      <div class="stat"><div class="k serif">${fmtM(totalAUM())}</div><div class="l">Total AUM</div></div>
      <div class="stat"><div class="k serif">${fmtM(totalRev())}</div><div class="l">Annualized revenue</div></div>
      <div class="stat"><div class="k serif">${meetSoon}</div><div class="l">Meetings this week</div></div>
      <div class="stat"><div class="k serif">${fmtM(totalHarvest()*TAX_RATE)}</div><div class="l">Est. tax alpha available</div></div>
    </div>
  </div>

  <div class="sect-h"><h2>Next best actions</h2><span class="n">Ranked by revenue impact & urgency</span></div>
  <div class="nba-grid">
    ${nbaMeetings()}
    ${nbaDrift()}
    ${nbaCIO()}
    ${nbaDeep()}
  </div>`;
}

function nbaMeetings(){
  const m = meetings();
  const rows = m.slice(0,4).map(c => {
    const mt = c.nextMeeting;
    return `<button class="row" data-client="${c.id}">
      ${avatarEl(c)}
      <div class="lead"><div class="nm">${c.name}</div>
        <div class="meta">${mt.type} \u00b7 ${c.segment}</div></div>
      <div class="right"><div class="fig">${meetWhen(mt.inDays)}</div><div class="figsub">${fmtM(c.aum)}</div></div>
    </button>`;
  }).join('') || `<div class="empty" style="padding:16px 4px;color:var(--muted);font-size:12.5px">Nothing on the calendar for this book right now.</div>`;
  return `<section class="nba acc-meet reveal" style="animation-delay:.04s">
    <div class="head"><div class="ic">${I.meet}</div>
      <div><div class="t">Meeting prep</div><div class="d">Upcoming client meetings</div></div>
      <div class="badge">${m.length} scheduled</div></div>
    <div class="body">${rows}</div>
    <div class="foot">Atlas drafts a prep brief for each ${m.length?`<span class="go" data-draft="${m[0].id}:meeting_prep">Draft with Atlas ${I.arrow}</span>`:`<span class="go" data-nav="chat">Draft with Atlas ${I.arrow}</span>`}</div>
  </section>`;
}
function nbaDrift(){
  const d = drifts();
  const rows = d.slice(0,4).map(x => {
    const w = Math.min(100, x.pct); const tw = Math.min(100, x.threshold);
    return `<button class="row" data-client="${x.c.id}">
      ${avatarEl(x.c)}
      <div class="lead"><div class="nm">${x.c.name}</div>
        <div class="meta">${x.label}</div>
        <div class="bar" style="margin-top:7px;width:150px"><i style="width:${w}%;background:var(--amber)"></i><span class="mini-th" style="left:${tw}%"></span></div>
      </div>
      <div class="right"><div class="fig" style="color:var(--amber)">${x.pct.toFixed(0)}%</div><div class="figsub">limit ${x.threshold}%</div></div>
    </button>`;
  }).join('') || `<div class="empty" style="padding:16px 4px;color:var(--muted);font-size:12.5px">No concentration or allocation breaches in this book right now.</div>`;
  return `<section class="nba acc-drift reveal" style="animation-delay:.08s">
    <div class="head"><div class="ic">${I.drift}</div>
      <div><div class="t">Concentration drift</div><div class="d">Positions breaching policy limits</div></div>
      <div class="badge">${d.length} flags</div></div>
    <div class="body">${rows}</div>
    <div class="foot">Marker shows policy threshold ${d.length?`<span class="go" data-client="${d[0].c.id}">Review top breach ${I.arrow}</span>`:'<span style="color:var(--muted)">Nothing to review</span>'}</div>
  </section>`;
}
function nbaCIO(){
  const cm = cioMisaligned();
  const rows = cm.slice(0,4).map(c => {
    const sc = c.cio.score;
    const pill = sc==='High'?'red':sc==='Medium'?'amber':'teal';
    return `<button class="row" data-client="${c.id}">
      ${avatarEl(c)}
      <div class="lead"><div class="nm">${c.name}</div>
        <div class="meta" style="white-space:normal">${c.cio.view}</div></div>
      <div class="right"><span class="pill ${pill}">${sc} drift</span></div>
    </button>`;
  }).join('') || `<div class="empty" style="padding:16px 4px;color:var(--muted);font-size:12.5px">Every portfolio in this book is aligned with current CIO guidance.</div>`;
  return `<section class="nba acc-cio reveal" style="animation-delay:.12s">
    <div class="head"><div class="ic">${I.cio}</div>
      <div><div class="t">CIO alignment</div><div class="d">Portfolios vs. house views & publications</div></div>
      <div class="badge">${cm.length} to review</div></div>
    <div class="body">${rows}</div>
    <div class="foot">Linked to this week's CIO desk notes ${cm.length?`<span class="go" data-client="${cm[0].id}">Open alignment ${I.arrow}</span>`:'<span style="color:var(--muted)">Nothing to review</span>'}</div>
  </section>`;
}
function nbaDeep(){
  const tc = topClients();
  const rows = tc.map((c,i) => {
    const g = clientGL(c);
    return `<button class="row" data-client="${c.id}">
      <div style="width:22px;text-align:center;font-family:'Newsreader',serif;font-size:15px;color:var(--muted)">${i+1}</div>
      ${avatarEl(c)}
      <div class="lead"><div class="nm">${c.name}</div>
        <div class="meta">${c.risk} \u00b7 YTD ${c.ytdReturn>0?'+':''}${c.ytdReturn}%</div></div>
      <div class="right"><div class="fig">${fmtM(c.aum)}</div><div class="figsub ${g>=0?'pos':'neg'}">${g>=0?'+':'\u2212'}${fmtM(Math.abs(g))} unreal.</div></div>
    </button>`;
  }).join('') || `<div class="empty" style="padding:16px 4px;color:var(--muted);font-size:12.5px">No households in this book yet.</div>`;
  return `<section class="nba acc-deep reveal" style="animation-delay:.16s">
    <div class="head"><div class="ic">${I.deep}</div>
      <div><div class="t">Top-client deep dives</div><div class="d">Your largest relationships by AUM</div></div>
      <div class="badge">Top ${tc.length}</div></div>
    <div class="body">${rows}</div>
    <div class="foot">Full holdings, tax lots & eligibility ${tc.length?`<span class="go" data-client="${tc[0].id}">Deep dive ${I.arrow}</span>`:'<span style="color:var(--muted)">No clients yet</span>'}</div>
  </section>`;
}

/* ================= VIEW: BOOK ================= */
function viewBook(){
  const segs=['all','Private Wealth','HNW','Emerging HNW','Institutional'];
  const list = myBook().filter(c=>bookFilter==='all'||c.segment===bookFilter).sort((a,b)=>b.aum-a.aum);
  const rows = list.map(c=>{
    const elig = programList(c).filter(p=>p.status==='eligible').slice(0,3);
    const enr = programList(c).filter(p=>p.status==='enrolled').length;
    const g = clientGL(c);
    const chips = elig.map(p=>`<span class="chip eligible">${p.label}</span>`).join('')
      + (enr?`<span class="chip enrolled">${enr} active</span>`:'');
    return `<tr data-client="${c.id}">
      <td><div class="cellname">${avatarEl(c)}<div><div style="font-weight:600">${c.name}</div><div class="sub">${c.entity} \u00b7 since ${c.since}</div></div></div></td>
      <td><span class="chip">${c.segment}</span></td>
      <td class="num">${fmtM(c.aum)}</td>
      <td class="num">${fmt$(c.rev)}</td>
      <td class="num ${g>=0?'pos':'neg'}">${g>=0?'+':'\u2212'}${fmtM(Math.abs(g))}</td>
      <td><div class="chips-inline">${chips||'<span class="chip na">Fully penetrated</span>'}</div></td>
    </tr>`;
  }).join('');
  return `
  <div class="sect-h" style="margin-top:6px"><h2>Book of business</h2><span class="n">${list.length} households \u00b7 ${fmtM(list.reduce((s,c)=>s+c.aum,0))} AUM</span></div>
  <div class="filters">
    <div class="seg">${segs.map(s=>`<button data-seg="${s}" class="${bookFilter===s?'on':''}">${s==='all'?'All':s}</button>`).join('')}</div>
    <div style="margin-left:auto"></div>
    <button class="btn sm" data-nav="crosssell">${I.cross} Cross-sell radar</button>
  </div>
  <div class="tbl-wrap"><table>
    <thead><tr><th>Household</th><th>Segment</th><th class="num">AUM</th><th class="num">Ann. revenue</th><th class="num">Unrealized</th><th>Cross-sell eligibility</th></tr></thead>
    <tbody>${rows}</tbody>
  </table></div>`;
}

function viewCrossSell(){
  function oppValue(c,k){
    if(k==='alternatives') return c.aum*0.15*0.010;
    if(k==='directIndexing') return c.aum*0.20*0.004;
    if(k==='privateBanking') return c.aum*0.10*0.015;
    if(k==='lending') return c.aum*0.20*0.012;
    if(k==='trustEstate') return 15000;
    if(k==='insurance') return 12000;
    return 8000;
  }
  const rows = crossSell().map(({c,p})=>({c,p,opp:oppValue(c,p.k)}))
    .sort((a,b)=>b.opp-a.opp)
    .map(({c,p,opp})=>`<tr data-client="${c.id}">
      <td><div class="cellname">${avatarEl(c)}<div><div style="font-weight:600">${c.name}</div><div class="sub">${c.segment} \u00b7 ${fmtM(c.aum)}</div></div></div></td>
      <td><span class="chip eligible">${p.label}</span></td>
      <td style="color:var(--muted); font-size:12.5px; max-width:280px">${crossReason(c,p.k)}<div style="margin-top:6px">${verdictCell(c,p.k)}</div></td>
      <td class="num" style="font-weight:600">${fmt$(opp)}</td>
    </tr>`).join('');
  const totalOpp = crossSell().reduce((s,{c,p})=>s+oppValue(c,p.k),0);
  return `
  <div class="sect-h" style="margin-top:6px"><h2>Cross-sell radar</h2><span class="n">${crossSell().length} eligible openings \u00b7 ~${fmtM(totalOpp)} est. annual revenue</span></div>
  <div class="callout">${I.spark}<div class="t"><b>Atlas found ${crossSell().length} program-eligibility matches</b> your clients qualify for but aren't enrolled in \u2014 screened against suitability, segment, and current holdings. Ranked by estimated annualized revenue.</div></div>
  <div class="tbl-wrap"><table style="min-width:760px">
    <thead><tr><th>Household</th><th>Eligible program</th><th>Why it fits</th><th class="num">Est. ann. revenue</th></tr></thead>
    <tbody>${rows}</tbody>
  </table></div>`;
}
function crossReason(c,k){
  const cashPct=c.current.cash;
  const map={
    privateBanking: `Post-liquidity cash of ${fmtM(c.aum*cashPct/100)} \u2014 deposit & lending relationship fit.`,
    trustEstate: `Estate complexity + ${c.segment} tier; no plan on file.`,
    alternatives: `${c.risk} mandate with 0% alts vs ${c.target.alt}% target \u2014 sleeve capacity available.`,
    directIndexing: `Ongoing TLH + factor control; ${fmtM(c.aum*0.2)} of indexed equity convertible.`,
    lending: `Low-basis holdings support securities-based line without triggering gains.`,
    insurance: `Protection / annuity gap for ${c.risk.toLowerCase()} household.`,
  };
  return map[k]||'Qualifies on segment and suitability screen.';
}

function viewTax(){
  const ranked = myBook().map(c=>({c, loss:Math.abs(clientHarvest(c)), alpha:Math.abs(clientHarvest(c))*TAX_RATE, rg:c.ytdRealizedGains}))
    .filter(x=>x.loss>0).sort((a,b)=>b.alpha-a.alpha);
  const totalAlpha = ranked.reduce((s,x)=>s+x.alpha,0);
  const offsettable = myBook().filter(c=>c.ytdRealizedGains>0).reduce((s,c)=>s+c.ytdRealizedGains,0);
  const notEnrolled = myBook().filter(c=>(c.overlays||{}).taxManagedSMA!=='enrolled');
  const rows = ranked.map(({c,loss,alpha,rg})=>{
    const enr = (c.overlays||{}).taxManagedSMA==='enrolled';
    const wash = c.holdings.some(h=>gl(h)<0 && ['QQQ','VTI','VGT'].includes(h.sym)) && c.id==='reyes';
    const v = vFor(c.id, 'taxManagedSMA');
    const engineCell = v ? (verdictPill(v)+(v.scope_exclusions&&v.scope_exclusions.length?' <span class="pill amber" title="Not applied to fixed-income holdings">FI carve-out</span>':'')+xinfoBtn(c.id,'taxManagedSMA')) : (enr?'<span class="chip enrolled">Tax-Managed SMA</span>':'<span class="chip eligible">Overlay eligible</span>');
    return `<tr data-client="${c.id}">
      <td><div class="cellname">${avatarEl(c)}<div><div style="font-weight:600">${c.name}</div><div class="sub">${c.segment}</div></div></div></td>
      <td class="num neg">\u2212${fmt$(loss).slice(1)}</td>
      <td class="num">${rg>0?fmt$(rg):'\u2014'}</td>
      <td class="num" style="font-weight:600;color:var(--brand)">${fmt$(alpha)}</td>
      <td>${engineCell} ${wash?'<span class="pill amber" title="Wash-sale risk">wash-sale watch</span>':''}</td>
    </tr>`;
  }).join('');
  return `
  <div class="sect-h" style="margin-top:6px"><h2>Tax overlay desk</h2><span class="n">Harvesting, gain-offset & tax-managed enrollment</span></div>
  <div class="tax-hero">
    <div class="tk"><div class="l">${I.spark} Harvestable losses</div><div class="v">${fmtM(totalHarvest())}</div><div class="s">across ${ranked.length} households</div></div>
    <div class="tk"><div class="l">${I.tax} Est. tax alpha</div><div class="v" style="color:var(--brand)">${fmtM(totalAlpha)}</div><div class="s">@ ${(TAX_RATE*100).toFixed(1)}% blended LTCG+NIIT</div></div>
    <div class="tk"><div class="l">${I.cross} Gains to offset</div><div class="v">${fmtM(offsettable)}</div><div class="s">realized YTD in book</div></div>
    <div class="tk"><div class="l">${I.people} Overlay-eligible</div><div class="v">${notEnrolled.length}</div><div class="s">not yet on tax-managed SMA</div></div>
  </div>
  <div class="callout">${I.spark}<div class="t">${ranked.length?`<b>Priority:</b> ${ranked[0].c.name} carries <b>${fmtM(ranked[0].loss)}</b> of harvestable losses and isn't on a tax-managed overlay \u2014 an estimated <b>${fmtM(ranked[0].alpha)}</b> of tax alpha.`:`<b>No harvestable losses in this book right now.</b>`} Harvesting the book now could offset <b>${fmtM(offsettable)}</b> of gains already realized this year.</div></div>
  <div class="tbl-wrap"><table style="min-width:740px">
    <thead><tr><th>Household</th><th class="num">Harvestable loss</th><th class="num">YTD realized gains</th><th class="num">Est. tax alpha</th><th>Overlay status</th></tr></thead>
    <tbody>${rows}</tbody>
  </table></div>`;
}

function allocBar(cur,tgt,label,color){
  const w=Math.min(100,cur); const t=Math.min(100,tgt);
  return `<div class="alloc-row"><div class="al">${label}</div>
    <div class="track"><div class="bar" style="height:9px"><i style="width:${w}%;background:${color}"></i><span class="mini-th" style="left:${t}%"></span></div></div>
    <div class="av">${cur}% <span style="opacity:.6">/ ${tgt}% tgt</span></div></div>`;
}

async function viewClient(id){
  const container = document.getElementById('view');
  container.innerHTML = '<div class="empty" style="padding:32px;text-align:center;color:var(--muted)">Loading household\u2026</div>';
  await ensureVerdicts(id);
  const c = byId(id);
  if(!c || c.advisor_id !== state.fa){ setView('book'); return; }
  const g = clientGL(c); const harv = Math.abs(clientHarvest(c));
  const holdsSorted = [...c.holdings].sort((a,b) => b.mv - a.mv);
  const holdRows = holdsSorted.map(h => {
    const glv = gl(h); const w = pctOf(h.mv, c.aum);
    return `<div class="hold">
      <div class="sym">${h.sym}</div>
      <div class="hn"><div class="a">${h.name}</div><div class="b">${h.ac} \u00b7 ${fmtM(h.mv)}</div></div>
      <div class="w"><div class="p">${w.toFixed(1)}%</div><div class="bar"><i style="width:${Math.min(100,w*3.2)}%;background:${w>15?'var(--amber)':'var(--brand)'}"></i></div></div>
      <div class="gl ${glv>=0?'pos':'neg'}">${glv>=0?'+':'\u2212'}${fmtM(Math.abs(glv))}</div>
    </div>`;
  }).join('');

  const nbas = [];
  if(c.nextMeeting) nbas.push({col:'var(--blue)', t:`<b>${meetWhen(c.nextMeeting.inDays)}:</b> ${c.nextMeeting.type}. ${c.nextMeeting.note||''}`});
  if((c.concentration||[]).length) nbas.push({col:'var(--amber)', t:`<b>Concentration:</b> ${c.concentration[0].label} at ${c.concentration[0].pct}% vs ${c.concentration[0].threshold}% policy limit.`});
  if(c.cio.score !== 'Low') nbas.push({col:'var(--brand)', t:`<b>CIO view:</b> ${c.cio.view}. See ${c.cio.pub}.`});
  if(harv > 10000) nbas.push({col:'#6b4a9e', t:`<b>Tax:</b> ${fmtM(harv)} harvestable \u2014 est. ${fmtM(harv * TAX_RATE)} tax alpha${(c.overlays||{}).taxManagedSMA!=='enrolled'?'. Not on tax-managed overlay.':'.'}`});
  crossSell().filter(x=>x.c.id===c.id).slice(0,1).forEach(({p})=>nbas.push({col:'var(--red)', t:`<b>Cross-sell:</b> Eligible for ${p.label} \u2014 ${crossReason(c,p.k)}`}));

  const composition = (c.program||'IAP')!=='MGI' ? await compositionPanelHtml(c) : '';

  container.innerHTML = `
  <button class="backlink" data-nav="book">${I.back} Book of business</button>
  <div class="cli-head reveal">
    ${avatarEl(c)}
    <div style="min-width:200px">
      <div class="nm serif">${c.name}</div>
      <div class="sub">${c.entity} \u00b7 ${c.segment} \u00b7 Client since ${c.since} \u00b7 <span class="mono">${c.risk}</span></div>
      <div class="sub" style="margin-top:8px">${c.contact}</div>
    </div>
    <div class="aum"><div class="k serif">${fmtM(c.aum)}</div><div class="l">Assets under management</div></div>
  </div>

  <div class="kpis">
    <div class="kpi"><div class="l">YTD return</div><div class="v ${c.ytdReturn>=0?'pos':'neg'}">${c.ytdReturn>=0?'+':''}${c.ytdReturn}%</div></div>
    <div class="kpi"><div class="l">Unrealized gain/loss</div><div class="v ${g>=0?'pos':'neg'}">${g>=0?'+':'\u2212'}${fmtM(Math.abs(g))}</div></div>
    <div class="kpi"><div class="l">Harvestable losses</div><div class="v">${fmtM(harv)}</div></div>
    <div class="kpi"><div class="l">Ann. revenue</div><div class="v">${fmt$(c.rev)}</div></div>
  </div>

  <div class="grid2">
    <div class="card">
      <div class="ch"><h3>Holdings & tax lots</h3><span class="r mono" style="font-size:11px;color:var(--muted)">${c.holdings.length} positions</span></div>
      <div class="cb">${holdRows}</div>
    </div>
    <div class="card">
      <div class="ch"><h3>Allocation vs. CIO target</h3></div>
      <div class="cbp">
        ${allocBar(c.current.equity, c.target.equity, 'Equity', 'var(--brand)')}
        ${allocBar(c.current.fixed, c.target.fixed, 'Fixed inc.', 'var(--blue)')}
        ${allocBar(c.current.alt, c.target.alt, 'Alternatives', '#6b4a9e')}
        ${allocBar(c.current.cash, c.target.cash, 'Cash', 'var(--amber)')}
        <hr class="divider" style="margin:12px 0"/>
        <div style="display:flex;gap:9px;align-items:flex-start">
          <span class="pill ${c.cio.score==='High'?'red':c.cio.score==='Medium'?'amber':'teal'}">${c.cio.score} drift</span>
          <div style="font-size:12px;color:var(--fg-2);line-height:1.5">${c.cio.diverge}. <span style="color:var(--muted)">${c.cio.pub}</span></div>
        </div>
      </div>
    </div>
  </div>

  <div class="stack">
    <div class="card">
      <div class="ch"><h3>Next best actions for this household</h3>${c.nextMeeting ? `<button class="btn sm primary r" data-draft="${c.id}:meeting_prep">${I.chat} Draft meeting prep</button>` : `<button class="btn sm r" data-nav="chat">${I.chat} Ask Atlas</button>`}</div>
      <div class="cbp" style="display:flex;flex-direction:column;gap:9px">
        ${nbas.map(n=>`<div class="nba-mini"><div class="d" style="background:${n.col}"></div><div class="txt">${n.t}</div></div>`).join('')}
      </div>
    </div>

    <div class="grid2" style="margin-top:0">
      <div class="card">
        <div class="ch"><h3>Program eligibility \u00b7 cross-sell</h3></div>
        <div class="cbp"><div class="elig-grid">
          ${programList(c).map(p => { const v = vFor(c.id, p.k); const dim = v && v.verdict==='INELIGIBLE'; const rs = verdictReason(v); const canModel = v && v.verdict==='ELIGIBLE' && p.status!=='enrolled';
            return `<div class="elig">
            <div class="eic" style="background:${dim?'var(--inset)':'var(--brand-tint)'};color:${dim?'var(--muted)':'var(--brand)'}">${p.icon}</div>
            <div style="min-width:0"><div class="en">${p.label}</div>${rs?`<div class="es" title="${rs.replace(/"/g,'&quot;')}">${rs}</div>`:''}${canModel?`<div class="es" style="margin-top:6px"><span class="u" data-transition="${c.id}:${p.k}" style="font-size:12px">Model transition ${I.arrow}</span></div>`:''}</div>
            <div class="est">${verdictCell(c, p.k)}</div>
          </div>`;}).join('')}
        </div></div>
      </div>
      <div class="card">
        <div class="ch"><h3>${(c.program||'IAP')==='MGI'?'Guided Investing (MGI) tax services':'Tax & overlay services'}</h3></div>
        <div class="cbp"><div class="elig-grid">
          ${((c.program||'IAP')==='MGI'?mgiOfferingList(c):overlayList(c)).map(p => { const v = vFor(c.id, p.k); const dim = v && v.verdict==='INELIGIBLE'; const rs = verdictReason(v); const canModel = v && v.verdict==='ELIGIBLE' && p.status!=='enrolled';
            return `<div class="elig">
            <div class="eic" style="background:${dim?'var(--inset)':'var(--brand-tint)'};color:${dim?'var(--muted)':'var(--brand)'}">${p.icon}</div>
            <div style="min-width:0"><div class="en">${p.label}</div>${rs?`<div class="es" title="${rs.replace(/"/g,'&quot;')}">${rs}</div>`:''}${canModel?`<div class="es" style="margin-top:6px"><span class="u" data-transition="${c.id}:${p.k}" style="font-size:12px">Model transition ${I.arrow}</span></div>`:''}</div>
            <div class="est">${verdictCell(c, p.k)}</div>
          </div>`;}).join('')}
        </div></div>
      </div>
    </div>
    ${composition}
  </div>`;
}

/* ================= VIEW: CHAT (Ask Atlas) ================= */
const CHAT_SUGGESTS = [
  'Where is my biggest tax-loss harvesting opportunity?',
  'Prep me for my meeting with the Hendersons',
  'Which clients are eligible for direct indexing but not enrolled?',
  'Who is drifting on concentration limits?',
  'Which portfolios diverge most from the CIO view?',
  'Rank my top cross-sell opportunities by revenue',
];
let chatLog = [];
let sending = false;

function viewChat(){
  if(chatLog.length===0){
    chatLog.push({role:'bot', html:true, content:
      `<p>I'm <strong>Atlas</strong>, your book copilot. I can see all ${myBook().length} households in your book \u2014 holdings, tax lots, program eligibility, CIO alignment and meeting schedule.</p><p>Ask me anything, or try a prompt below.</p>`});
  }
  const stream = chatLog.map(renderMsg).join('');
  const ctxTop = [...myBook()].sort((a,b)=>b.aum-a.aum).slice(0,5);
  return `<div class="chatwrap">
    <div class="chat">
      <div class="ch-head"><div class="mk">${I.chat}</div>
        <div><div class="t">Ask Atlas</div><div class="s"><span class="live"></span> Grounded on your live book</div></div>
      </div>
      <div class="stream" id="stream">${stream}</div>
      <div class="composer">
        ${chatLog.some(m=>m.role==='user') ? '' : `<div class="suggests" id="suggests">${CHAT_SUGGESTS.map(s=>`<button data-ask="${s.replace(/"/g,'&quot;')}">${s}</button>`).join('')}</div>`}
        <div class="inputrow">
          <textarea id="chatInput" rows="1" placeholder="Ask about clients, holdings, tax, eligibility\u2026"></textarea>
          <button class="sendbtn" id="sendBtn" aria-label="Send" ${sending?'disabled':''}>${I.send}</button>
        </div>
      </div>
    </div>
    <aside class="ctx-panel">
      <div class="ctx-card"><h4>${I.people} Top relationships</h4>
        <div class="ctx-list">${ctxTop.map(c=>`<button data-client="${c.id}">${avatarEl(c)}<span style="min-width:0"><span style="display:block;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${c.name.split(' ')[0]} ${c.name.includes('Family')?'Family':c.name.split(' ')[1]||''}</span></span><span class="g">${fmtM(c.aum)}</span></button>`).join('')}</div>
      </div>
      <div class="ctx-card"><h4>${I.spark} What Atlas can do</h4>
        <div style="font-size:12.5px;color:var(--fg-2);line-height:1.65">
          Screen eligibility for cross-sell \u00b7 surface tax-harvesting opportunities \u00b7 draft meeting-prep briefs \u00b7 flag concentration & CIO drift \u00b7 summarize any household.
        </div>
      </div>
    </aside>
  </div>`;
}
function renderMsg(m){
  if(m.typing) return `<div class="msg bot" data-mid="${m.mid||''}"><div class="who">${I.chat}</div><div class="bubble"><span class="typing"><i></i><i></i><i></i></span></div></div>`;
  const body = m.html ? (m.content||'') : mdToHtml(m.content||'');
  const fa = state.meta && state.meta.advisors && state.meta.advisors[state.fa];
  const userInitials = fa ? (fa.initials || initials(fa.name)) : 'DW';
  return `<div class="msg ${m.role==='user'?'user':'bot'}"><div class="who">${m.role==='user'?userInitials:I.chat}</div><div class="bubble">${body}</div></div>`;
}
function mdToHtml(md){
  let s = esc(md);
  s = s.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/`(.+?)`/g,'<code>$1</code>');
  const lines = s.split(/\n/); let out=''; let inU=false, inO=false;
  for(let ln of lines){
    if(/^\s*###\s+/.test(ln)){ if(inU){out+='</ul>';inU=false;} if(inO){out+='</ol>';inO=false;} out+='<h3>'+ln.replace(/^\s*###\s+/,'')+'</h3>'; continue; }
    if(/^\s*##\s+/.test(ln)){ if(inU){out+='</ul>';inU=false;} if(inO){out+='</ol>';inO=false;} out+='<h2>'+ln.replace(/^\s*##\s+/,'')+'</h2>'; continue; }
    if(/^\s*[-*]\s+/.test(ln)){ if(!inU){out+='<ul>';inU=true;} out+='<li>'+ln.replace(/^\s*[-*]\s+/,'')+'</li>'; continue; }
    if(/^\s*\d+\.\s+/.test(ln)){ if(!inO){out+='<ol>';inO=true;} out+='<li>'+ln.replace(/^\s*\d+\.\s+/,'')+'</li>'; continue; }
    if(inU){out+='</ul>';inU=false;} if(inO){out+='</ol>';inO=false;}
    if(ln.trim()==='') continue;
    out+='<p>'+ln+'</p>';
  }
  if(inU) out+='</ul>'; if(inO) out+='</ol>';
  return out;
}
function scrollChat(){ const m=document.getElementById('main'); if(m) m.scrollTop=m.scrollHeight; }
function paintChat(){ document.getElementById('view').innerHTML = viewChat(); scrollChat(); const ta=document.getElementById('chatInput'); if(ta) ta.focus(); }
function resCard(items){
  return `<div class="rescard">${items.map(it=>`<div class="rc-row" data-client="${it.c.id}">${avatarEl(it.c)}<div style="min-width:0"><div class="nm">${it.c.name}</div><div class="mt">${it.sub||it.c.segment}</div></div><div class="vv">${it.right||''}</div></div>`).join('')}</div>`;
}
async function sendChat(text){
  text = (text||'').trim(); if(!text || sending) return;
  sending = true;
  const btn = document.getElementById('sendBtn'); if(btn) btn.disabled = true;
  chatLog.push({role:'user', content:text});
  const sg = document.getElementById('suggests'); if(sg) sg.remove();
  const mid = 'm'+Date.now();
  chatLog.push({role:'bot', typing:true, mid});
  paintChat(); scrollChat();
  try{
    const history = chatLog.filter(m=>!m.typing && (m.role==='user'||(m.role==='bot'&&!m.html)))
      .slice(-8).map(m=>({role:m.role==='user'?'user':'assistant', content:m.content||''}));
    const r = await api('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({fa:state.fa, message:text, history})});
    const i = chatLog.findIndex(m=>m.mid===mid);
    if(i>=0) chatLog[i] = {role:'bot', mid, content:r.content};
  }catch(e){
    const i = chatLog.findIndex(m=>m.mid===mid);
    if(i>=0) chatLog[i] = {role:'bot', mid, content:'Sorry \u2014 I hit an error reaching the model. Please try again.'};
  }finally{
    sending = false;
    const b = document.getElementById('sendBtn'); if(b) b.disabled = false;
    paintChat(); scrollChat();
  }
}

/* ================= VIEW: DRAFT REVIEW (human-in-the-loop) ================= */
const DRAFT_KIND_LABEL = {meeting_prep:'Meeting prep brief'};
function draftStatusPill(status){
  const map = {
    pending: ['pill amber', 'Awaiting your review'],
    approved: ['chip eligible dot', 'Approved'],
    declined: ['chip na', 'Declined'],
    edited_approved: ['chip eligible dot', 'Edited & approved'],
  };
  const [cls, label] = map[status] || ['chip na', status];
  return `<span class="${cls}">${label}</span>`;
}
async function openDraft(householdId, kind='meeting_prep'){
  state.view = 'draftReview'; state.draftTarget = {householdId, kind};
  render();
  const main = document.querySelector('.main'); if(main) main.scrollTo({top:0});
}
async function viewDraftReview(householdId, kind){
  const container = document.getElementById('view');
  container.innerHTML = '<div class="empty" style="padding:32px;text-align:center;color:var(--muted)">Atlas is drafting\u2026</div>';
  await ensureVerdicts(householdId);
  const c = byId(householdId);
  if(!c || c.advisor_id !== state.fa){ setView('book'); return; }
  let draft;
  try{
    draft = await api(`/api/draft/${householdId}`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({fa:state.fa, kind})});
  }catch(e){
    container.innerHTML = `<div class="empty" style="padding:32px;color:var(--red)">Could not generate draft: ${esc(e.message)}</div>`;
    return;
  }
  renderDraftReview(c, draft, kind, false);
}
function draftHouseholdToggle(activeId, kind){
  if(kind !== 'meeting_prep') return '';
  const m = meetings();
  if(m.length <= 1) return '';
  return `<div class="filters" style="margin-bottom:14px;align-items:center">
    <span style="font-size:12.5px;color:var(--muted)">Drafting meeting prep for</span>
    <select id="draftHouseholdSelect" style="font:inherit;font-size:13px;font-weight:600;color:var(--fg);background:var(--paper);border:1px solid var(--line);border-radius:9px;padding:7px 11px;box-shadow:var(--sh-1);cursor:pointer;max-width:360px">
      ${m.map(hh => `<option value="${hh.id}" ${hh.id===activeId?'selected':''}>${hh.name} \u00b7 ${meetWhen(hh.nextMeeting.inDays)}</option>`).join('')}
    </select>
  </div>`;
}
function renderDraftReview(c, draft, kind, editing){
  const container = document.getElementById('view');
  const kindLabel = DRAFT_KIND_LABEL[kind] || kind;
  const pending = draft.status === 'pending';
  container.innerHTML = `
  <button class="backlink" data-client="${c.id}">${I.back} ${c.name}</button>
  ${draftHouseholdToggle(c.id, kind)}
  <div class="cli-head reveal" style="margin-bottom:0">
    ${avatarEl(c)}
    <div style="min-width:200px">
      <div class="nm serif">${kindLabel}</div>
      <div class="sub">For ${c.name} \u00b7 drafted by Atlas \u00b7 human review required before it's used</div>
    </div>
    <div style="margin-left:auto;align-self:center">${draftStatusPill(draft.status)}</div>
  </div>

  <div class="card" style="margin-top:16px">
    <div class="ch"><h3>Proposed draft</h3><span class="r mono" style="font-size:11px;color:var(--muted)">${draft.mode==='model-drafted'?'grounded \u00b7 model-drafted':'grounded \u00b7 template'}</span></div>
    <div class="cbp">
      ${editing
        ? `<textarea id="draftEditArea" style="width:100%;min-height:380px;font:inherit;font-size:13.5px;line-height:1.6;border:1px solid var(--line);border-radius:var(--r-m);padding:14px;background:var(--paper-2);color:var(--fg);resize:vertical">${esc(draft.content)}</textarea>`
        : `<div class="bubble" style="max-width:none;background:transparent;border:none;padding:0">${mdToHtml(draft.content)}</div>`}
    </div>
  </div>

  <div class="card" style="margin-top:14px">
    <div class="cbp" style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
      ${editing ? `
        <button class="btn primary" id="draftSave">Save & approve</button>
        <button class="btn" id="draftCancelEdit">Cancel</button>
      ` : pending ? `
        <button class="btn primary" id="draftApprove">Approve</button>
        <button class="btn" id="draftEditBtn">Edit</button>
        <button class="btn" id="draftDecline" style="color:var(--red);border-color:color-mix(in srgb,var(--red) 40%,var(--line))">Decline</button>
        <span style="margin-left:auto;font-size:12px;color:var(--muted)">FA sign-off required \u2014 nothing is sent automatically.</span>
      ` : `
        <div style="font-size:13px;color:var(--fg-2)">${draft.status==='declined' ? 'Declined \u2014 no action taken.' : 'Ready to use.'}${draft.decided_at?(' Decided '+new Date(draft.decided_at).toLocaleString()+'.'):''}</div>
        <button class="btn" id="draftRegenerate" style="margin-left:auto">Draft again</button>
      `}
    </div>
  </div>`;

  const hhSelect = document.getElementById('draftHouseholdSelect');
  if(hhSelect) hhSelect.addEventListener('change', e => openDraft(e.target.value, kind));

  if(editing){
    document.getElementById('draftSave').onclick = async () => {
      const text = document.getElementById('draftEditArea').value;
      const updated = await api(`/api/draft/${c.id}/decision`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kind, action:'edit', edited_content:text, decided_by:state.fa})});
      renderDraftReview(c, updated, kind, false);
    };
    document.getElementById('draftCancelEdit').onclick = () => renderDraftReview(c, draft, kind, false);
  } else if(pending){
    document.getElementById('draftApprove').onclick = async () => {
      const updated = await api(`/api/draft/${c.id}/decision`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kind, action:'approve', decided_by:state.fa})});
      renderDraftReview(c, updated, kind, false);
    };
    document.getElementById('draftDecline').onclick = async () => {
      const updated = await api(`/api/draft/${c.id}/decision`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kind, action:'decline', decided_by:state.fa})});
      renderDraftReview(c, updated, kind, false);
    };
    document.getElementById('draftEditBtn').onclick = () => renderDraftReview(c, draft, kind, true);
  } else {
    document.getElementById('draftRegenerate').onclick = () => viewDraftReview(c.id, kind);
  }
}

/* ================= VIEW: TRANSITION WORKBENCH ================= */
async function openTransition(householdId, offering){
  state.view = 'transition'; state.transitionTarget = {householdId, offering};
  await render();
  const main = document.querySelector('.main'); if(main) main.scrollTo({top:0});
}
async function viewTransition(householdId, offering){
  const container = document.getElementById('view');
  container.innerHTML = '<div class="empty" style="padding:32px;text-align:center;color:var(--muted)">Modeling transition scenario\u2026</div>';
  await ensureVerdicts(householdId);
  const c = byId(householdId);
  if(!c || c.advisor_id !== state.fa){ setView('book'); return; }
  let s;
  try{ s = await api(`/api/transition/${householdId}?offering=${encodeURIComponent(offering)}`); }
  catch(e){ container.innerHTML = `<div class="empty" style="padding:32px;color:var(--red)">Could not model transition: ${esc(e.message)}</div>`; return; }
  renderTransition(c, s);
}
function transitionActionStyle(action){
  const map = {
    sell: {label:'SELL', color:'var(--red)'},
    stage_sell: {label:'STAGE SELL', color:'var(--blue)'},
    harvest: {label:'HARVEST', color:'var(--amber)'},
    buy: {label:'BUY', color:'var(--brand)'},
    note: {label:'NOTE', color:'var(--muted)'},
  };
  return map[action] || {label:action.toUpperCase(), color:'var(--fg-2)'};
}
function severityStyle(sev){
  const map = {
    required: {cls:'pill amber', label:'Required'},
    recommended: {cls:'pill blue', label:'Recommended'},
    scope_carveout: {cls:'pill', label:'Scope carve-out'},
    review: {cls:'pill amber', label:'Needs review'},
    clear: {cls:'chip eligible dot', label:'Clear'},
  };
  return map[sev] || {cls:'pill', label:sev};
}
function renderTransition(c, s){
  const container = document.getElementById('view');
  const cur = s.current_state;
  const enrolledPill = s.currently_enrolled
    ? `<span class="chip eligible dot">Already enrolled</span>`
    : (s.eligibility_verdict === 'ELIGIBLE' ? `<span class="chip eligible dot">Eligible \u00b7 not yet enrolled</span>`
      : `<span class="pill amber">${s.eligibility_verdict}</span>`);
  const topHoldings = `
    <table class="hh-tbl"><thead><tr><th>Symbol</th><th>Name</th><th>Asset class</th><th class="r">Mkt value</th><th class="r">Weight</th><th class="r">Unrealized G/L</th></tr></thead>
    <tbody>${cur.top_holdings.map(h => `<tr><td class="mono"><b>${h.sym}</b></td><td>${h.name}</td><td>${h.ac}</td><td class="r mono">${fmtM(h.mv)}</td><td class="r mono">${h.weight}%</td><td class="r mono" style="color:${h.gl==null?'var(--muted)':h.gl>=0?'var(--gain)':'var(--loss)'}">${h.gl==null?'\u2014':(h.gl>=0?'+':'')+fmtM(h.gl)}</td></tr>`).join('')}</tbody></table>`;
  const gapCard = `
    <div class="card" style="margin-top:14px">
      <div class="ch"><h3>Gap analysis</h3><span class="r" style="font-size:12px;color:var(--muted)">${s.gap_analysis.length} item${s.gap_analysis.length===1?'':'s'}</span></div>
      <div class="cbp">
        <div style="display:flex;flex-direction:column;gap:9px">
          ${s.gap_analysis.map(g => { const st = severityStyle(g.severity); return `<div style="display:flex;gap:11px;align-items:flex-start"><span class="${st.cls}" style="flex-shrink:0;min-width:110px;text-align:center">${st.label}</span><span style="font-size:13.5px;line-height:1.55;padding-top:2px">${esc(g.message)}</span></div>`; }).join('')}
        </div>
      </div>
    </div>`;
  let tradesOrSteps = '';
  if(s.kind === 'procedural'){
    tradesOrSteps = `
    <div class="card" style="margin-top:14px">
      <div class="ch"><h3>Onboarding steps</h3><span class="r" style="font-size:12px;color:var(--muted)">${s.steps.length} step${s.steps.length===1?'':'s'}</span></div>
      <div class="cbp">
        <ol style="margin:0;padding-left:22px;line-height:1.7;font-size:13.5px">${s.steps.map(step => `<li style="margin:6px 0">${esc(step)}</li>`).join('')}</ol>
      </div>
    </div>`;
  } else {
    const ts = s.target_state;
    tradesOrSteps = `
    <div class="card" style="margin-top:14px">
      <div class="ch"><h3>Proposed trades</h3><span class="r mono" style="font-size:11px;color:var(--muted)">${s.proposed_trades.length} action${s.proposed_trades.length===1?'':'s'}</span></div>
      <div class="cbp" style="padding:0">
        <table class="hh-tbl"><thead><tr><th>Action</th><th>Symbol</th><th>Name</th><th class="r">Value</th><th class="r">Realized G/L</th><th>Rationale</th></tr></thead>
        <tbody>${s.proposed_trades.map(t => { const st = transitionActionStyle(t.action); return `<tr><td><span class="mono" style="font-weight:700;font-size:11px;color:${st.color}">${st.label}</span></td><td class="mono"><b>${t.sym||'\u2014'}</b></td><td>${t.name||'\u2014'}</td><td class="r mono">${t.value?fmtM(t.value):'\u2014'}</td><td class="r mono" style="color:${t.gl==null?'var(--muted)':t.gl>=0?'var(--gain)':'var(--loss)'}">${t.gl==null?'\u2014':(t.gl>=0?'+':'')+fmtM(t.gl)}</td><td style="font-size:12.5px;color:var(--fg-2)">${esc(t.reason||'')}</td></tr>`; }).join('')}</tbody></table>
      </div>
    </div>
    <div class="card" style="margin-top:14px">
      <div class="ch"><h3>Target state</h3></div>
      <div class="cbp">
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:20px;margin-bottom:14px">
          <div><div style="font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;font-weight:600">Reallocated</div><div class="mono" style="font-size:20px;font-family:'Newsreader',serif">${fmtM(ts.sells_total)}</div></div>
          <div><div style="font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;font-weight:600">Realized gain</div><div class="mono" style="font-size:20px;font-family:'Newsreader',serif;color:${ts.realized_gain>0?'var(--gain)':'var(--fg)'}">${ts.realized_gain?fmtM(ts.realized_gain):'\u2014'}</div></div>
          <div><div style="font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;font-weight:600">Offset by harvest</div><div class="mono" style="font-size:20px;font-family:'Newsreader',serif;color:${ts.harvest_offset>0?'var(--loss)':'var(--fg)'}">${ts.harvest_offset?'\u2212'+fmtM(ts.harvest_offset):'\u2014'}</div></div>
          <div><div style="font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;font-weight:600">Net taxable</div><div class="mono" style="font-size:20px;font-family:'Newsreader',serif">${ts.net_taxable_gain?fmtM(ts.net_taxable_gain):'\u2014'}</div></div>
          <div><div style="font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;font-weight:600">Est. ongoing tax alpha</div><div class="mono" style="font-size:20px;font-family:'Newsreader',serif;color:var(--gain)">${ts.estimated_ongoing_annual_tax_alpha?'+'+fmtM(ts.estimated_ongoing_annual_tax_alpha)+'/yr':'\u2014'}</div></div>
        </div>
        ${ts.concentration_after && ts.concentration_after.length ? `<div style="margin-top:6px;padding:10px 12px;background:color-mix(in srgb, var(--amber) 8%, transparent);border-left:3px solid var(--amber);border-radius:6px;font-size:12.5px">Residual concentration: ${ts.concentration_after.map(c=>`${c.label} at ${c.pct}%`).join(', ')}</div>` : ''}
        ${ts.notes && ts.notes.length ? `<ul style="margin:12px 0 0;padding-left:20px;font-size:12.5px;color:var(--fg-2);line-height:1.6">${ts.notes.map(n=>`<li style="margin:4px 0">${esc(n)}</li>`).join('')}</ul>` : ''}
      </div>
    </div>`;
  }
  container.innerHTML = `
  <button class="backlink" data-client="${c.id}">${I.back} ${c.name}</button>
  <div class="cli-head reveal" style="margin-bottom:0">
    ${avatarEl(c)}
    <div style="min-width:200px">
      <div class="eyebrow" style="margin-bottom:4px">TRANSITION WORKBENCH</div>
      <div class="nm serif">${s.offering_label}</div>
      <div class="nm serif" style="color:var(--muted)">${c.name}</div>
    </div>
    <div style="margin-left:auto;align-self:center">${enrolledPill}</div>
  </div>

  <div class="card" style="margin-top:16px">
    <div class="ch"><h3>Current state</h3><span class="r mono" style="font-size:11px;color:var(--muted)">${cur.positions} position${cur.positions===1?'':'s'} \u00b7 ${fmtM(cur.aum)} AUM</span></div>
    <div class="cbp" style="padding:0">${topHoldings}</div>
    ${cur.concentration_flags && cur.concentration_flags.length ? `<div style="padding:0 17px 14px"><div style="padding:10px 12px;background:color-mix(in srgb, var(--amber) 8%, transparent);border-left:3px solid var(--amber);border-radius:6px;font-size:12.5px">Concentration flag: ${cur.concentration_flags.map(f=>`${f.label} at ${f.pct}% (limit ${f.threshold}%)`).join(', ')}</div></div>` : ''}
  </div>

  ${gapCard}
  ${tradesOrSteps}

  <div style="margin-top:14px;font-size:11.5px;color:var(--muted);text-align:center;padding:14px">
    Illustrative modeling for advisor review. Actual trade generation, tax impact, and eligibility subject to compliance sign-off and the strategy shelf at execution.
  </div>`;
}

/* ================= ROUTER ================= */
function setView(v, client=null){
  state.view = v; state.client = client;
  render();
  const view = document.getElementById('view'); if(view) view.scrollTop = 0;
  const main = document.querySelector('.main'); if(main) main.scrollTo({top:0});
}
async function render(){
  paintNav();
  const crumbs = {today:'Today', book:'Book of Business', chat:'Ask Atlas', tax:'Tax Overlay Desk', crosssell:'Cross-Sell Radar', client:'Book of Business', draftReview:'Book of Business', transition:'Book of Business'};
  const cr = document.getElementById('crumb');
  if(state.view==='client') cr.innerHTML = `<span style="color:var(--muted)">Book of Business /</span> <b>${byId(state.client)?byId(state.client).name:''}</b>`;
  else if(state.view==='draftReview'){ const t=byId(state.draftTarget&&state.draftTarget.householdId); cr.innerHTML = `<span style="color:var(--muted)">Book of Business / ${t?t.name:''} /</span> <b>Draft</b>`; }
  else if(state.view==='transition'){ const t=byId(state.transitionTarget&&state.transitionTarget.householdId); cr.innerHTML = `<span style="color:var(--muted)">Book of Business / ${t?t.name:''} /</span> <b>Transition</b>`; }
  else cr.innerHTML = `<b>${crumbs[state.view]||'Today'}</b>`;
  const v = document.getElementById('view');
  if(state.view === 'today') v.innerHTML = viewToday();
  else if(state.view === 'book') v.innerHTML = viewBook();
  else if(state.view === 'chat'){ v.innerHTML = viewChat(); requestAnimationFrame(() => { scrollChat(); const ta = document.getElementById('chatInput'); if(ta) ta.focus(); }); }
  else if(state.view === 'tax') v.innerHTML = viewTax();
  else if(state.view === 'crosssell') v.innerHTML = viewCrossSell();
  else if(state.view === 'client') await viewClient(state.client);
  else if(state.view === 'draftReview') await viewDraftReview(state.draftTarget.householdId, state.draftTarget.kind);
  else if(state.view === 'transition') await viewTransition(state.transitionTarget.householdId, state.transitionTarget.offering);
}

async function switchFa(fa){
  state.fa = fa; state.client = null; state.view = 'today';
  await loadBook(); render(); paintFaProfile();
}

/* ================= EVENTS ================= */
document.addEventListener('click', e => {
  const ex = e.target.closest('[data-explain]'); if(ex){ e.stopPropagation(); showExplain(ex.dataset.client, ex.dataset.offering, ex); return; }
  const nav = e.target.closest('[data-nav]'); if(nav){ setView(nav.dataset.nav); return; }
  const dr = e.target.closest('[data-draft]'); if(dr){ const [hid,kind] = dr.dataset.draft.split(':'); openDraft(hid, kind||'meeting_prep'); return; }
  const tr = e.target.closest('[data-transition]'); if(tr){ const [hid,off] = tr.dataset.transition.split(':'); openTransition(hid, off); return; }
  const cl = e.target.closest('[data-client]'); if(cl){ setView('client', cl.dataset.client); return; }
  const ask = e.target.closest('[data-ask]'); if(ask){ const q = ask.dataset.ask; if(state.view !== 'chat'){ setView('chat'); } setTimeout(() => { const ta = document.getElementById('chatInput'); if(ta){ ta.value = q; ta.style.height = 'auto'; ta.style.height = Math.min(120, ta.scrollHeight)+'px'; ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length); } }, 40); return; }
  const send = e.target.closest('#sendBtn'); if(send){ const ta = document.getElementById('chatInput'); if(ta){ const v = ta.value; ta.value = ''; ta.style.height = 'auto'; sendChat(v); } return; }
});
document.addEventListener('input', e => {
  if(e.target.id === 'chatInput'){ e.target.style.height = 'auto'; e.target.style.height = Math.min(120, e.target.scrollHeight)+'px'; }
});
document.addEventListener('keydown', e => {
  if(e.target.id === 'chatInput' && e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); const v = e.target.value; e.target.value = ''; e.target.style.height = 'auto'; sendChat(v); }
  if(e.key === '/' && !/input|textarea/i.test(document.activeElement.tagName)){ const s = document.getElementById('globalSearch'); if(s){ e.preventDefault(); s.focus(); } }
  if(e.key === 'Escape') closeExplain();
});
document.addEventListener('keydown', e => {
  if(e.target.id === 'globalSearch' && e.key === 'Enter'){
    const q = e.target.value.toLowerCase().trim(); if(!q) return;
    const hit = myBook().find(c => c.name.toLowerCase().includes(q) || c.contact.toLowerCase().includes(q) || c.holdings.some(h => h.sym.toLowerCase() === q));
    if(hit){ setView('client', hit.id); e.target.value = ''; }
    else { setView('chat'); setTimeout(() => sendChat(e.target.value), 30); e.target.value = ''; }
  }
});
window.addEventListener('scroll', () => closeExplain(), true);

/* theme */
function applyTheme(t){
  const root = document.documentElement;
  if(t) root.setAttribute('data-theme', t); else root.removeAttribute('data-theme');
  const cur = t || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  const tog = document.getElementById('themeToggle'); if(tog) tog.innerHTML = cur === 'dark' ? I.sun : I.moon;
}
let themePref = null;
try{ themePref = localStorage.getItem('atlas-theme'); } catch(e){}
applyTheme(themePref);
document.getElementById('themeToggle').addEventListener('click', () => {
  const isDark = (document.documentElement.getAttribute('data-theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')) === 'dark';
  themePref = isDark ? 'light' : 'dark'; applyTheme(themePref);
  try{ localStorage.setItem('atlas-theme', themePref); } catch(e){}
});

/* ================= BOOT ================= */
(async () => {
  try {
    state.meta = await api('/api/meta');
    document.getElementById('faSwitch').innerHTML = Object.values(state.meta.advisors).map(a =>
      `<option value="${a.id}">${esc(a.role || a.name)}</option>`).join('');
    document.getElementById('faSwitch').addEventListener('change', e => switchFa(e.target.value));
    document.getElementById('faSwitch').value = state.fa;
    await loadBook();
    paintFaProfile();
    paintEngineToggle();
    render();
  } catch(e) {
    document.getElementById('view').innerHTML = `<div class="empty" style="padding:32px;color:var(--red)">Failed to load: ${esc(e.message)}</div>`;
  }
})();
```

---

## 14. Testing and verification discipline

Two complementary layers were used throughout development; both should be reproduced.

### 14.1 Backend: `pytest` + FastAPI `TestClient`

`tests/test_api.py` hits the real FastAPI app in-process (no server needed) and asserts on response shape and specific known values from the seed data — e.g. `test_health` asserts the rule count is exactly 92; `test_book_isolated` asserts advisor `marcus` has exactly 6 households and every one of them has `advisor_id == 'marcus'` (book isolation between advisors is a real thing to guard against regressing); `test_composition` asserts a specific known-incompatible pair (`transition` + `dtlhOverlay` for household `henderson`) resolves to `CONFIRMED_INELIGIBLE`; `test_chat_grounded` asserts the local-fallback chat path actually mentions the household by name and reports `mode == 'local-grounded'` (proving the no-API-key path genuinely works, not just that *some* response came back). Complete file:

```python
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
def test_health():
 r=c.get('/api/health');assert r.status_code==200;assert r.json()['rules']==92
def test_book_isolated():
 d=c.get('/api/book?fa=marcus').json();assert len(d)==6;assert {x['advisor_id'] for x in d}=={'marcus'}
def test_household_payload():
 d=c.get('/api/household/henderson').json();assert d['id']=='henderson';assert d['program']=='IAP';assert 'transition' in d['verdicts']

def test_every_household_has_program_and_displayable_verdicts():
 for advisor in ('dana','marcus'):
  for row in c.get(f'/api/book?fa={advisor}').json():
   d=c.get(f'/api/household/{row["id"]}').json()
   expected=['taxManagedSMA','qlhOverlay','dtlhOverlay','transition','directIndexing','temSms','alternatives','privateBanking','lending','trustEstate','insurance','charitable'] if d['program']=='IAP' else ['mgiTer','mgiQlh','mgiDtlh']
   assert all(d['verdicts'].get(offering,{}).get('label') for offering in expected)
def test_composition(): assert c.get('/api/composition/henderson?offerings=transition,dtlhOverlay').json()['verdict']=='CONFIRMED_INELIGIBLE'
def test_chat_grounded():
 d=c.post('/api/chat',json={'fa':'dana','message':'Tell me about Henderson'}).json();assert 'Henderson' in d['content'];assert d['mode']=='local-grounded'
def test_unknown_fa(): assert c.get('/api/book?fa=missing').status_code==404
def test_static_app():
 r=c.get('/');assert r.status_code==200;assert 'Atlas' in r.text
```

`tests/test_engine.py` covers the rule kernel in isolation — three-valued AND/OR/NOT truth tables, unknown-field propagation, requirement-vs-condition-vs-disclosure effect handling, and composition-rule resolution. Reproduce equivalent unit coverage for every branch described in §6.3's effect table.

Run with: `python3 -m pytest tests/ -q` from the project root (with the venv active and `requirements.txt` installed).

### 14.2 Frontend: Playwright (Python, headless Chromium) — real-browser verification

No frontend unit-test framework is used; instead, every view and every interactive flow was verified by scripting a real headless browser against a running `uvicorn` instance, because this app's bugs are overwhelmingly the kind that only manifest in an actual rendered DOM (missing CSS classes, unconstrained SVG sizing, event-delegation ordering, lazy-vs-eager state computation) — none of which a pure-JS unit test would catch. The pattern used throughout:

```python
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width":1440,"height":900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.goto("http://127.0.0.1:9999/", wait_until="networkidle")
        await page.wait_for_timeout(800)
        # ... exercise the specific view/flow being changed, with real
        # locator-based clicks/fills, not innerHTML inspection ...
        # ... assert on rendered text, computed styles (getComputedStyle
        #     via page.locator(...).evaluate(...)), and bounding boxes
        #     (to catch exactly the unconstrained-icon-sizing class of bug) ...
        print("ERRORS:", errors if errors else "none")
        await browser.close()

asyncio.run(main())
```

Start the server on a scratch port before running any such script (`uvicorn app.main:app --host 127.0.0.1 --port 9999 --log-level warning &`), and always assert `ERRORS: none` (from a `pageerror` listener) in addition to whatever specific behavior is being checked — a silent JS exception mid-render is exactly the kind of failure that produces a half-rendered page with no console output visible to a casual look.

After any change, re-run the full sweep across every view (Today → Book → a client deep-dive → the explain popover → chat → the tax desk → cross-sell → draft review → transition workbench), not just the view that was directly touched — several of the real regressions caught during development were in a view *other* than the one being edited (e.g. a shared icon-sizing rule affecting both the transition workbench's new link and the pre-existing "Draft with Atlas" footer link).


---

## 15. Complete `tests/test_engine.py`

```python
import pytest
from app.data import RULE_STORE,BY_ID,derive_facts
from app.engine import evaluate_predicate,evaluate_offering,evaluate_composition,client_safe_view
from app.services import offering_result,composition_result

def test_pack_counts():
 assert len(RULE_STORE['offerings'])==16
 assert sum(len(x['rules']) for x in RULE_STORE['offerings'].values())==92
 assert len(RULE_STORE['composition_rules'])==4

def test_three_valued_logic():
 assert evaluate_predicate({'OR':[{'field':'missing','op':'EQ','value':True},True]}, {}) is True
 assert evaluate_predicate({'AND':[{'field':'missing','op':'EQ','value':True},False]}, {}) is False
 assert evaluate_predicate({'field':'missing','op':'EQ','value':True}, {}) is None
 assert evaluate_predicate({'field':'x','op':'EQ','value':True}, {'x':1}) is None

def test_henderson_tet_has_two_real_scope_exclusions():
 v=offering_result('henderson','transition')
 assert v['verdict']=='ELIGIBLE'
 ids={x for c in v['scope_exclusions'] for x in c['excluded_ids']}
 assert ids=={'LOT_HEND_GIFT_2011','AUSTIN-4.0-32'}

def test_sato_namespace_split():
 assert offering_result('sato','mgiQlh')['verdict']=='ELIGIBLE'
 assert offering_result('sato','mgiTer')['verdict']=='INELIGIBLE'
 wrong=offering_result('sato','taxManagedSMA')
 assert wrong['verdict']=='INELIGIBLE' and wrong['reasons'][0]['rule_id']=='PROGRAM_SCOPE'

def test_farkas_client_eligible_but_advisor_prerequisite_fails():
 v=offering_result('farkas','dtlhOverlay')
 assert v['verdict']=='ELIGIBLE'
 assert v['prerequisite']['verdict']=='INELIGIBLE'
 assert any(x['failure_class']=='FA_SCOPE' for x in v['prerequisite']['internal_only_reasons'])

def test_pas_blocks_iap_overlays():
 for x in ['taxManagedSMA','qlhOverlay','dtlhOverlay','transition']:
  assert offering_result('bianchi',x)['verdict']=='INELIGIBLE'

def test_duarte_tem_roster_fails(): assert offering_result('duarte','temSms')['verdict']=='INELIGIBLE'
def test_eshun_custom_managed_ter_is_eligible(): assert offering_result('eshun','taxManagedSMA')['verdict']=='ELIGIBLE'
def test_tet_dtlh_incompatible(): assert composition_result('henderson',['transition','dtlhOverlay'])['verdict']=='CONFIRMED_INELIGIBLE'
def test_tet_ter_scoped(): assert composition_result('henderson',['transition','taxManagedSMA'])['verdict']=='ELIGIBLE_WITH_CARVEOUT'
def test_unspecified_pair_requires_review(): assert composition_result('henderson',['qlhOverlay','dtlhOverlay'])['verdict']=='NEEDS_REVIEW'
def test_client_view_hides_internal_trace():
 v=offering_result('farkas','dtlhOverlay')['prerequisite']; safe=client_safe_view(v)
 assert 'trace' not in safe and 'internal_only_reasons' not in safe
 assert safe['generic_message']
```

## 16. Complete `requirements.txt`

```
fastapi>=0.115,<1
uvicorn[standard]>=0.30,<1
pydantic>=2.8,<3
pytest>=8,<9
httpx>=0.27,<1
```

## 17. Complete `pyproject.toml`

```toml
[project]
name = "atlas-advisor-console"
version = "1.0.0"
description = "FastAPI port of the Atlas advisor console and eligibility rule engine"
requires-python = ">=3.11"
dependencies = ["fastapi>=0.115,<1", "uvicorn[standard]>=0.30,<1", "pydantic>=2.8,<3"]
[project.optional-dependencies]
test = ["pytest>=8,<9", "httpx>=0.27,<1"]
[tool.pytest.ini_options]
testpaths = ["tests"]
```

## 18. Environment variables

| Variable | Purpose | Default if unset |
|---|---|---|
| `ATLAS_LLM_PROVIDER` | `"anthropic"` or `"openai"` — selects which live-LLM path chat/drafts attempt | unset → no live call attempted, local-grounded fallback used for everything |
| `ANTHROPIC_API_KEY` | required if provider is `anthropic` | unset → falls back |
| `OPENAI_API_KEY` | required if provider is `openai` | unset → falls back |
| `ATLAS_ANTHROPIC_MODEL` | model string for the Anthropic path | `claude-sonnet-4-6` |
| `ATLAS_OPENAI_MODEL` | model string for the OpenAI path | `gpt-5.4-mini` |
| `ATLAS_LLM_TIMEOUT` | seconds, HTTP timeout for the live-LLM call | `12` |

## 19. Build and run instructions

```bash
# from the project root, with a Python 3.11+ virtualenv active
pip install -r requirements.txt
python3 -m pytest tests/ -q          # 20 tests should pass
uvicorn app.main:app --reload        # serves on http://127.0.0.1:8000
```

No frontend build step exists or is needed — `app/static/{index.html,styles.css,app.js}` are served as-is by FastAPI's `StaticFiles` mount plus the `/` route. Editing any of the three static files and refreshing the browser (a hard refresh — `Cmd+Shift+R` / `Ctrl+Shift+R` — is often necessary since browsers cache static JS/CSS aggressively and `uvicorn --reload` only restarts the Python process, not the browser's cache) is sufficient to see changes; there is no webpack/vite/rollup step to run.

## 20. Final acceptance checklist for a rebuild

Before considering a rebuild complete, verify every one of these — each corresponds to a specific behavior documented above and, in several cases, to a real bug that was found and fixed during the original build:

- [ ] `python3 -m pytest tests/ -q` passes all 20 tests, including the exact rule count (92) and exact per-advisor household counts (11 for `dana`, 6 for `marcus`).
- [ ] The Today hero's 4 stat blocks span the full width of the card edge-to-edge on a wide viewport, never clustering to one side.
- [ ] Every offering tile on a client deep-dive that is `ELIGIBLE` and not yet enrolled shows a working "Model transition ›" link; every such link's arrow icon renders at a fixed small size (11×11px) regardless of which tile it's in.
- [ ] The "Draft with Atlas" and "Ask a question" inline links show a pointer cursor on hover.
- [ ] Opening Ask Atlas for the first time shows the correct live household count in the welcome message (not 0).
- [ ] A meeting-prep draft, once generated, can be Approved, Declined, or Edited-then-saved, and the status pill and action bar update correctly after each; the household-switcher dropdown (only shown when 2+ households have upcoming meetings) correctly regenerates the draft for whichever household is selected.
- [ ] The transition workbench correctly renders a trade table + target-state metrics for a trade-modelable offering (e.g. Direct Indexing) and a plain numbered onboarding checklist for a procedural offering (e.g. Private Banking) for the same household, with no shared/leftover UI between the two kinds.
- [ ] The transition workbench's header shows the offering name and the household name at the same font size and typographic level (both `.nm.serif`).
- [ ] Every backlink (draft review, transition workbench) returns to the originating household's deep-dive, never to the Book of Business list by mistake.
- [ ] With no `ATLAS_LLM_PROVIDER` set at all, chat and meeting-prep drafts still fully function via their local-grounded fallbacks — the app must never appear broken due to missing API keys.

