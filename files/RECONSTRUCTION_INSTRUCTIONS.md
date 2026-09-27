# Reconstructing Atlas from your Part 1/2/3 baseline — final instructions

You have the app as it existed when `atlas-spec-part1-architecturev2.md`, `-part2-data.md`, and `-part3-frontend.md` were written: **92 rules, 16 offerings, 17 households**, no `dca` offering, no `agent.py`, no strategy catalog. Everything below brings that exact baseline forward to the current state. Do these in order — later steps assume earlier ones are done.

Every file referenced here was verified by actually reconstructing it and diffing byte-for-byte against the real running app before being handed to you — not assumed correct from the generation logic alone. Three real bugs were caught and fixed doing that (booleans round-tripping as strings, an explicit-`null` field being indistinguishable from an absent field, and a `failure_class`/`routing`/`scope_key`/`coverage_note` set of fields the first pass missed entirely). If you rebuild any of this yourself using a different method, verify it the same way: load both JSON files in Python and check `a == b`, not just that they look similar.

---

## Step 0 — Confirm your source PDFs match

`parse_catalog.py` (Step 4) depends on the *exact* section-header wording in `ml-investment-advisory-program-strategy-catalog.pdf`. An earlier pass of this same parser silently mis-filed rows under the wrong sleeve because the PDF's body text didn't match its own table of contents in five places (e.g. body says "Multi-Style Equity", TOC says "Multi-Style"). The parser already has those five aliases built in — but if your copy of the catalog is a different edition, re-verify by running the parser and checking that every one of its ~52 sections has at least one product (a section with zero rows usually means a header-text mismatch, not an empty section).

---

## Step 1 — CSS (already resolved, no file needed)

Append this to the end of your existing `app/static/styles.css` — it's the exact, verified 51-line delta, already confirmed zero lines removed or changed from your baseline:

```css
/* ============ AGENT: CONTEXT, TRACE, ACTIONS ============ */
.ctx-bar{ display:flex; align-items:center; gap:8px; padding:8px 17px; font-size:12.5px; color:var(--fg-2); background:color-mix(in srgb,var(--brand) 7%,transparent); border-bottom:1px solid var(--line-2);}
.ctx-bar svg{ width:14px; height:14px; color:var(--brand); flex-shrink:0;}
.ctx-bar span{ flex:1; min-width:0;}
.ctx-x{ width:22px; height:22px; border-radius:var(--r-s); color:var(--muted); font-size:15px; line-height:1; cursor:pointer;}
.ctx-x:hover{ background:var(--paper-2); color:var(--fg);}
.trace{ margin-top:10px; font-size:12px; color:var(--muted);}
.trace summary{ cursor:pointer; font-weight:600; list-style-position:inside;}
.trace ol{ margin:6px 0 0; padding-left:20px;}
.trace li{ margin:3px 0;}
.trace .mono{ color:var(--fg-2); font-size:11.5px;}
.agent-actions{ display:flex; flex-wrap:wrap; gap:8px; margin-top:12px;}
.agent-actions .btn svg{ width:12px; height:12px;}

/* ============ VEHICLE PICKER / AUTOCOMPLETE ============ */
.pchips{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px;}
.pchip{ display:inline-flex; align-items:center; gap:7px; max-width:100%; padding:5px 6px 5px 10px; border:1px solid var(--line); border-radius:999px; background:var(--paper-2); font-size:12.5px;}
.pchip b{ font-family:"IBM Plex Mono",monospace; font-size:12px;}
.pchip-n{ color:var(--muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:230px;}
.pchip-x{ width:20px; height:20px; border-radius:999px; color:var(--muted); font-size:14px; line-height:1; cursor:pointer; flex-shrink:0;}
.pchip-x:hover{ background:color-mix(in srgb,var(--red) 12%,transparent); color:var(--red);}
.cmp-controls{ display:flex; flex-wrap:wrap; align-items:center; gap:10px;}
.ac-wrap{ position:relative; flex:1 1 320px; min-width:240px;}
.ac-input, .cmp-amt input{ width:100%; font:inherit; font-size:13px; color:var(--fg); background:var(--paper); border:1px solid var(--line); border-radius:var(--r-m); padding:8px 11px; box-shadow:var(--sh-1); outline:none;}
.ac-input:focus, .cmp-amt input:focus{ border-color:var(--brand);}
.cmp-amt{ display:inline-flex; align-items:center; gap:8px; font-size:12.5px; color:var(--muted);}
.cmp-amt input{ width:130px; font-family:"IBM Plex Mono",monospace;}
.ac-menu{ position:absolute; z-index:50; top:calc(100% + 4px); left:0; right:0; max-height:320px; overflow-y:auto; background:var(--paper); border:1px solid var(--line); border-radius:var(--r-m); box-shadow:0 12px 32px rgba(0,0,0,.14); padding:4px;}
.ac-item{ display:flex; align-items:flex-start; gap:10px; width:100%; text-align:left; padding:8px 9px; border-radius:var(--r-s); cursor:pointer;}
.ac-item:hover:not([disabled]){ background:var(--paper-2);}
.ac-item[disabled]{ opacity:.5; cursor:default;}
.ac-t{ min-width:46px; font-weight:600; font-size:12px; color:var(--brand); padding-top:1px;}
.ac-n{ display:flex; flex-direction:column; font-size:13px; font-weight:600; min-width:0;}
.ac-m{ font-size:11.5px; font-weight:400; color:var(--muted); margin-top:1px;}
.ac-empty{ padding:10px; font-size:12.5px; color:var(--muted);}

/* ============ PRODUCT SHELF ============ */
.shelf-filters{ display:flex; flex-wrap:wrap; align-items:center; gap:10px;}
.shelf-sel{ font:inherit; font-size:13px; color:var(--fg); background:var(--paper); border:1px solid var(--line); border-radius:var(--r-m); padding:8px 10px; box-shadow:var(--sh-1); cursor:pointer;}
.shelf-chk{ display:inline-flex; align-items:center; gap:7px; font-size:12.5px; color:var(--fg-2); cursor:pointer;}
.shelf-compare{ display:flex; gap:8px; align-items:center; flex-wrap:wrap;}
.shelf-pick{ cursor:pointer; width:15px; height:15px; accent-color:var(--brand);}

/* ============ CHAT MARKDOWN TABLES ============ */
.bubble .md-table{ overflow-x:auto; margin:8px 0; border:1px solid var(--line-2); border-radius:var(--r-m); background:var(--paper);}
.bubble .md-table table{ border-collapse:collapse; width:100%; font-size:12.5px;}
.bubble .md-table th{ text-align:left; font-weight:600; color:var(--muted); font-size:11.5px; background:var(--paper-2);}
.bubble .md-table th, .bubble .md-table td{ padding:7px 10px; border-bottom:1px solid var(--line-2); vertical-align:top;}
.bubble .md-table tr:last-child td{ border-bottom:none;}
```

---

## Step 2 — Household and fact data

Files: `households_main.csv`, `holdings.csv`, `enrollments.csv`, `account_facts.csv`, `account_offering_facts.csv`, `reconstruct.py`.

```bash
python3 reconstruct.py
```
This prints three `True`/`False` lines confirming each section matches the real app exactly. It writes `/tmp/rebuilt_households.json` for a final look, but you'll actually want its output copied to `app/data/households.json`, and the `af`/`oof` dicts it builds merged into `app/data/fa-and-facts.json` under `account_facts` and `account_offering_facts` respectively (the script prints them; adapt the bottom few lines to write them out directly if you'd rather not do it by hand — it's a two-line change).

This resolves your "only got the first household" problem: all **25** households (your original 17 plus 8 new ones — Montgomery, Thornbury, Kestrel, Harlow, Lindqvist, Castellano, Okoye, Ferreira) are in these tables.

---

## Step 3 — Rule store

Files: `rule_store_offerings.csv`, `rule_store_composition.csv`, `expand_rule_store.py`.

```bash
python3 expand_rule_store.py
```
Prints `17 offerings, 112 rules, 16 composition rules` and writes `rule-store.json` — copy it to `app/data/rule-store.json`. This is your existing 92 rules plus 20 new ones (the `dca` offering's 13 rules, U.S.-residency and Custom-Managed-Strategy exclusions on the TEM offerings) and 12 new composition rules.

---

## Step 4 — Strategy catalog → product shelf

File: `parse_catalog.py`.

```bash
pdftotext -layout ml-investment-advisory-program-strategy-catalog.pdf catalog.txt
python3 parse_catalog.py catalog.txt
```
Writes `product-shelf-catalog.json` — **1,097 real products** (579 SMAs, 332 fund models, 94 Direct Indexing strategies, 92 ETF models), each with its real minimum and TEM-overlay eligibility code. Your app's `product-shelf.json` should be this list plus the ~60 illustrative products (real ETFs + fictional SMA managers) already in your baseline — append rather than replace.

`research-models.json` and `content-catalog.json` (the vehicle-comparison model links and CIO document catalog) aren't reconstructable from any source document — they're hand-authored. If you need them, ask and I'll ship them directly; they're small (13 KB combined).

---

## Step 5 — Python backend

Five files: `data.py.patch`, `services.py.patch`, `main.py.patch`, `index.html.patch`, and `agent_NEW_FILE.py`. `engine.py` needs **no patch at all** — it's byte-identical to your baseline; the rule-evaluation kernel was never touched.

```bash
patch app/data.py < data.py.patch
patch app/services.py < services.py.patch
patch app/main.py < main.py.patch
patch app/static/index.html < index.html.patch
cp agent_NEW_FILE.py app/agent.py
```
Every patch here was applied to your exact baseline and diffed byte-for-byte against the real current file before being sent to you — confirmed identical, not just "should work."

---

## Step 6 — Frontend

File: `app.js.patch`.

```bash
patch app/static/app.js < app.js.patch
```
Same verification as Step 5 — applied and confirmed byte-identical against the real file.

---

## Step 7 — Verify

```bash
pip install -r requirements.txt
python3 -m pytest tests/ -q          # expect: 38 passed
uvicorn app.main:app --reload
curl localhost:8000/api/health       # expect: {"status":"ok","pack_id":"atlas.merrill.tax-services.2026-09-20","offerings":17,"rules":112}
```
If the rule/offering counts don't match, Steps 2–4 didn't complete cleanly — re-run their round-trip checks before touching the Python.

---

## What still can't be reconstructed and must be sent directly if you need it

- `research-models.json`, `content-catalog.json` — hand-authored, 13 KB, mentioned in Step 4.
- The 3 generated PDF client factsheets under `app/static/content-pdfs/` — these are rendered output (charts + tables), not source-derivable; ~55 KB total if needed.
- `README.md`, `Dockerfile`, `railway.json`, `.dockerignore` — deployment config, not app logic; ask if you want these.
