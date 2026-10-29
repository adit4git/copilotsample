'use strict';
/* Outside Accounts POC: upload -> extract -> review -> validate -> compare -> propose -> check, with a guided tour. */
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const money = (v, d = 0) => v == null ? '–' : (v < 0 ? '-' : '') + '$' + Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
const short = v => v == null ? '–' : Math.abs(v) >= 1e6 ? '$' + (v / 1e6).toFixed(2) + 'M' : Math.abs(v) >= 1e3 ? '$' + Math.round(v / 1e3).toLocaleString() + 'K' : money(v);
const pct = (v, d = 1) => v == null ? '–' : (v * 100).toFixed(d) + '%';
const STATUS = { approved: 'Approved', review: 'Under review', not_approved: 'Not approved', unrecognized: 'Not recognized', held_away: 'Held away', cash: 'Cash', excluded: 'Excluded' };
const ICON = { approved: '✓', review: '!', not_approved: '✕', unrecognized: '?', held_away: '⌂', cash: '$' };
const STEPS = [
  { id: 'collect', label: 'Collect statements' }, { id: 'review', label: 'Review extraction' }, { id: 'validate', label: 'Validate' },
  { id: 'compare', label: 'Inside vs outside' }, { id: 'proposals', label: 'Proposals' }, { id: 'document', label: 'Check & document' }, { id: 'workflow', label: 'Workflow' }];

const S = { households: [], samples: [], hh: null, sid: null, step: 'collect', consent: false, an: null, stmt: null, prop: 'B', vfilter: null, busy: false };

async function api(path, opts = {}) {
  const r = await fetch(path, { headers: opts.body && !(opts.body instanceof FormData) ? { 'content-type': 'application/json' } : {}, ...opts });
  if (!r.ok) { let m = r.statusText; try { m = (await r.json()).detail || m } catch (e) { } throw new Error(m) }
  return r.headers.get('content-type')?.includes('json') ? r.json() : r.text();
}
function toast(m) { const t = document.createElement('div'); t.className = 'toast'; t.textContent = m; document.body.append(t); setTimeout(() => t.remove(), 2600) }
const pill = st => `<span class="pill p-${st}">${ICON[st] || ''} ${STATUS[st] || st}</span>`;

async function boot() {
  try { const th = localStorage.getItem('oa-theme'); if (th) document.documentElement.dataset.theme = th } catch (e) { }
  [S.households, S.samples] = await Promise.all([api('/api/households'), api('/api/samples')]);
  $('#hh').innerHTML = S.households.map(h => `<option value="${h.id}">${esc(h.name)}${h.relationship === 'prospect' ? ' (prospect)' : ''}</option>`).join('');
  $('#hh').onchange = e => newSession(e.target.value);
  $('#themeBtn').onclick = () => { const d = document.documentElement; const dark = d.dataset.theme ? d.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; d.dataset.theme = dark ? 'light' : 'dark'; try { localStorage.setItem('oa-theme', d.dataset.theme) } catch (e) { } };
  $('#tourBtn').onclick = () => Tour.start();
  const q = new URLSearchParams(location.search);
  await newSession(q.get('hh') || 'henderson');
  if (q.get('samples')) await loadSamples(q.get('samples'));
  if (q.get('step')) go(q.get('step'));
  if (q.get('tour') === '1') Tour.start();
}

async function newSession(hid) {
  S.hh = hid; $('#hh').value = hid;
  const r = await api('/api/sessions', { method: 'POST', body: JSON.stringify({ household: hid }) });
  S.sid = r.id; S.an = null; S.stmt = null; S.consent = false; S.vfilter = null; S.prop = 'B';
  await refresh(); go('collect');
}
async function refresh() { S.an = await api(`/api/sessions/${S.sid}/analysis`); if (S.an.statements.length && !S.an.statements.find(s => s.id === S.stmt)) S.stmt = S.an.statements[0].id }
function go(step) { S.step = step; render(); window.scrollTo(0, 0) }

async function loadSamples(set) {
  S.consent = true; S.busy = true; render();
  try { await api(`/api/sessions/${S.sid}/samples/${set}`, { method: 'POST' }) } catch (e) { toast(e.message) }
  S.busy = false; await refresh(); render();
}
async function upload(files) {
  files = [...files];
  if (!S.consent) return toast('Record client consent first');
  if (files.length > 5) return toast('Upload up to 5 statements at a time');
  const fd = new FormData(); files.forEach(f => fd.append('files', f));
  S.busy = true; render();
  try { const r = await api(`/api/sessions/${S.sid}/statements`, { method: 'POST', body: fd }); r.errors.forEach(toast) } catch (e) { toast(e.message) }
  S.busy = false; await refresh(); render();
}
async function removeStmt(id) { await api(`/api/sessions/${S.sid}/statements/${id}`, { method: 'DELETE' }); await refresh(); render() }
async function override(body) { await api(`/api/sessions/${S.sid}/overrides`, { method: 'PUT', body: JSON.stringify(body) }); await refresh(); render() }
async function setBudget(v) { await api(`/api/sessions/${S.sid}/settings`, { method: 'PUT', body: JSON.stringify({ gain_budget: v }) }); await refresh(); render() }

/* ------------------------------------------------------------------ render */
function render() {
  const an = S.an, has = an && an.statements.length;
  const wf = an ? Object.fromEntries(an.workflow.map(w => [w.id, w])) : {};
  const doneMap = { collect: has, review: has && wf.confirm?.done, validate: has && wf.validate?.done, compare: has, proposals: has, document: false, workflow: false };
  $('#rail').innerHTML = STEPS.map((s, i) => `<button class="step ${S.step === s.id ? 'on' : ''} ${doneMap[s.id] ? 'done' : ''}" data-step="${s.id}" data-tour="rail-${s.id}" ${!has && i > 0 && i < 6 ? 'disabled style="opacity:.5"' : ''}><b>${doneMap[s.id] ? '✓' : i + 1}</b>${s.label}</button>`).join('')
    + `<div class="sep"></div><div class="note">Up to 5 statements per upload. PDF, scanned PDF, PNG/JPG, Excel or CSV.<br><br>Illustrative data; all outside institutions are fictional.</div>`;
  $$('#rail .step').forEach(b => b.onclick = () => { if (!b.disabled) go(b.dataset.step) });
  const view = { collect: vCollect, review: vReview, validate: vValidate, compare: vCompare, proposals: vProposals, document: vDocument, workflow: vWorkflow }[S.step];
  $('#main').innerHTML = view();
  bind();
}
const hhInfo = () => S.households.find(h => h.id === S.hh);

function vCollect() {
  const h = hhInfo(), an = S.an;
  const sample = S.samples.find(x => x.household === S.hh);
  return `<div class="head"><div class="grow"><h1>Collect outside statements</h1><p>Bring in statements for accounts held at other institutions. The tool reads holdings, values and allocation, checks them against the firm's approved list, and builds proposals that cover inside and outside together.</p></div></div>
  <div class="grid2" style="grid-template-columns:minmax(0,5fr) minmax(0,7fr)">
    <div class="card stack" data-tour="household">
      <div><span class="pill p-plain">${h.relationship === 'prospect' ? 'Prospect' : 'Client'}</span></div>
      <h2>${esc(h.name)}</h2>
      <div class="meta"><div><span>Risk profile</span>${esc(h.profile)}</div><div><span>Held at the firm</span>${h.firm_total ? short(h.firm_total) : 'Nothing yet'}</div><div><span>Next meeting</span>${esc(h.meeting)}</div>
      <div><span>Gain budget</span>${money(an?.household.gain_budget)}</div></div>
      ${sample ? `<div class="consent" style="background:var(--accent-2);border-color:transparent"><div class="grow small"><b>Sample statements</b><br>${esc(sample.label)}: PDF, screenshot, Excel, phone photo, scanned PDF, CSV.</div><button class="btn primary sm" data-act="samples" data-set="${sample.id}" data-tour="load-samples">Load samples</button></div>` : ''}
    </div>
    <div class="card stack">
      <label class="consent" data-tour="consent"><input type="checkbox" id="consent" ${S.consent ? 'checked' : ''}> <span class="small"><b>Client consent recorded.</b> The client has agreed that we review these outside accounts. Account numbers are kept to the last 4 digits and uploaded files are deleted once they are read.</span></label>
      <div class="drop ${S.consent ? '' : 'disabled'}" id="drop" data-tour="drop">
        <div style="font-size:26px">⇪</div>
        <div><b>Drop up to 5 statements</b> or <label style="color:var(--accent);cursor:pointer;text-decoration:underline">browse<input type="file" id="file" multiple accept=".pdf,.png,.jpg,.jpeg,.webp,.tif,.tiff,.xlsx,.xlsm,.csv" hidden ${S.consent ? '' : 'disabled'}></label></div>
        <div class="small muted">Brokerage or bank PDFs, scanned PDFs, portal screenshots, phone photos, Excel or CSV exports. 15 MB each.</div>
        ${S.busy ? '<div class="small" style="margin-top:8px"><b>Reading statements…</b> OCR can take a few seconds per page.</div>' : ''}
      </div>
    </div>
  </div>
  <div style="margin-top:18px" class="row"><h2 class="grow">Statements (${an?.statements.length || 0})</h2>${an?.statements.length ? `<button class="btn primary" data-go="review">Review extraction →</button>` : ''}</div>
  <div class="stmts" style="margin-top:10px" data-tour="stmts">${an?.statements.length ? an.statements.map(stCard).join('') : '<div class="empty card">No statements yet.</div>'}</div>`;
}
function stCard(s) {
  const rec = s.reconciliation;
  const img = ['pdf-text', 'pdf-scan', 'image'].includes(s.kind) ? `style="background-image:url('/api/sessions/${S.sid}/statements/${s.id}/preview')"` : '';
  return `<div class="stmt"><div class="thumb" ${img}>${img ? '' : (s.kind === 'xlsx' ? '▦ Excel workbook' : '▤ CSV export')}</div><div class="body">
    <div class="t">${esc(s.institution || s.file)}</div><div class="small muted">${esc(s.account_type || '')}${s.account ? ' …' + esc(s.account) : ''} · ${esc(s.as_of || 'no date')}</div>
    <div class="row small"><span class="pill p-plain">${esc(s.method)}</span></div>
    <div class="row small"><b>${s.holdings.length}</b> rows · <b>${money(s.extracted_total)}</b><span class="grow"></span>${rec ? (rec.ok ? '<span class="ok">✓ reconciles</span>' : '<span class="bad">✕ off by ' + money(rec.diff) + '</span>') : '<span class="muted">no total</span>'}</div>
    <div class="row small"><span class="muted grow">${esc(s.file)}</span><button class="btn ghost sm" data-act="open" data-id="${s.id}">Open</button><button class="btn ghost sm" data-act="rm" data-id="${s.id}" title="Remove">✕</button></div>
  </div></div>`;
}

function vReview() {
  const an = S.an; const s = an.statements.find(x => x.id === S.stmt) || an.statements[0];
  const checks = an.statement_checks[s.id];
  const img = ['pdf-text', 'pdf-scan', 'image'].includes(s.kind);
  const keyOf = h => `${s.id}:${h.row}`;
  return `<div class="head"><div class="grow"><h1>Review extraction</h1><p>Each statement next to what was read from it. Rows the reader is less sure of are highlighted; edit any value and the change is logged with the original.</p></div></div>
  <div class="tabs" data-tour="stmt-tabs">${an.statements.map(x => `<button class="${x.id === s.id ? 'on' : ''}" data-stmt="${x.id}">${esc(x.institution || x.file)}${x.needs_review ? ' •' : ''}</button>`).join('')}</div>
  <div class="split">
    <div class="stack" style="min-width:0">${pageStrip(s)}
    <div class="preview" data-tour="preview">${img ? `<img alt="Statement page" src="/api/sessions/${S.sid}/statements/${s.id}/preview/${curPreview(s)}">` : `<pre>${esc((s.kind === 'xlsx' ? 'Excel cells read directly (no OCR)\n\n' : 'CSV cells read directly (no OCR)\n\n') + (S.an.statements.find(x => x.id === s.id).holdings.map(h => [h.sym || '', h.desc, h.qty ?? '', h.price ?? '', h.value].join('  |  ')).join('\n')))}</pre>`}</div>${chartsCard(s)}</div>
    <div class="stack">
      <div class="card" data-tour="meta"><div class="meta">
        <div><span>Institution</span>${esc(s.institution || '–')}</div><div><span>Owner</span>${esc(s.owner || '–')}</div><div><span>Account</span>${esc(s.account_type || '–')}${s.account ? ' …' + esc(s.account) : ''}</div>
        <div><span>As of</span>${esc(s.as_of || '–')}</div><div><span>Statement total</span>${money(s.stated_total, 2)}</div><div><span>Read by</span>${esc(s.method)}</div></div>
        <div class="checks" style="margin-top:12px" data-tour="checks">${checks.map(c => `<div class="chk"><b class="${c.ok ? 'ok' : c.ok === false ? 'warn' : 'muted'}">${c.ok ? '✓' : c.ok === false ? '!' : '–'}</b><span>${esc(c.text)}</span></div>`).join('')}
        ${s.surrender ? `<div class="chk"><b class="warn">!</b><span>${esc(s.surrender)}</span></div>` : ''}${(s.notes || []).map(n => `<div class="chk"><b class="muted">i</b><span>${esc(n)}</span></div>`).join('')}${s.warnings.map(w => `<div class="chk"><b class="warn">!</b><span>${esc(w)}</span></div>`).join('')}</div>
      </div>
      <div class="tw" data-tour="rows"><table><thead><tr><th>Symbol</th><th>Description</th><th class="num">Quantity</th><th class="num">Price</th><th class="num">Value</th><th class="num">Cost basis</th><th>Read</th><th></th></tr></thead><tbody>
        ${s.holdings.map(h => { const ov = an.overrides[keyOf(h)]; return `<tr class="${h.review || h.flags.length ? 'flag' : ''}"><td class="mono">${esc(ov?.sym ?? h.sym ?? '–')}</td><td>${esc(ov?.desc ?? h.desc)}${h.detail ? `<span class="sub">${esc(h.detail)}</span>` : ''}${s.pages > 1 && h.page ? `<span class="sub">Page ${h.page}${h.section ? ' · ' + esc(h.section) : ''}</span>` : ''}${h.flags.map(f => `<span class="sub warn">${esc(f)}</span>`).join('')}${ov ? '<span class="sub ok">Edited by the advisor</span>' : ''}${ov?.exclude ? '<span class="sub bad">Excluded</span>' : ''}</td>
          <td class="num">${h.qty == null ? '–' : (+h.qty).toLocaleString()}</td><td class="num">${h.price == null ? '–' : money(h.price, 2)}</td><td class="num">${money(ov?.value ?? h.value, 2)}</td><td class="num">${h.cost == null ? '–' : money(ov?.cost ?? h.cost, 0)}</td>
          <td class="small"><span class="conf ${h.confidence < .85 ? 'lo' : ''}"><i style="width:${Math.round(h.confidence * 100)}%"></i></span>${Math.round(h.confidence * 100)}%</td><td><button class="btn ghost sm" data-act="edit" data-key="${keyOf(h)}">Edit</button></td></tr>` }).join('')}
      </tbody></table></div>
      ${s.allocation.length ? `<div class="card"><h3>Allocation as printed on the statement${s.allocation[0].source && s.allocation[0].source.startsWith('chart') ? ' (read from the ' + esc(s.allocation[0].source) + ')' : ''}</h3><div class="row small">${s.allocation.map(a => `<span class="pill p-plain">${esc(a.label)} ${a.pct}%</span>`).join('')}</div><p class="small muted" style="margin-top:6px">Kept for cross-checking. The household view uses the holdings, mapped to the firm's asset classes.</p></div>` : ''}
      <div class="row"><span class="grow"></span><button class="btn primary" data-go="validate">Validate against the approved list →</button></div>
    </div>
  </div>`;
}

const PTYPE = { summary: 'Summary', chart: 'Chart', holdings: 'Holdings', activity: 'Activity', disclosure: 'Disclosures', other: 'Other' };
function curPreview(s) { const k = (S.pv || {})[s.id]; return k && (s.previews || []).includes(k) ? k : 'page-1' }
function pageStrip(s) {
  const pm = s.page_map || []; if (pm.length < 2) return '';
  const cur = curPreview(s), counts = {}; pm.forEach(p => counts[p.type] = (counts[p.type] || 0) + 1);
  return `<div class="card pagemap" data-tour="pagemap"><div class="row small"><b class="grow">${pm.length} pages</b>${Object.entries(counts).map(([t, n]) => `<span class="pt pt-${t}">${PTYPE[t]} ${n}</span>`).join('')}</div>
  <div class="pages">${pm.map(p => { const k = 'page-' + p.page, has = (s.previews || []).includes(k); return `<button class="pg pt-${p.type} ${cur === k ? 'on' : ''}" ${has ? `data-pv="${s.id}|${k}"` : 'disabled'} title="Page ${p.page}: ${PTYPE[p.type]} (${esc(p.why)})${p.rows ? ', ' + p.rows + ' rows read' : ''}${has ? '' : '. Not kept for preview'}">${p.page}</button>` }).join('')}</div>
  <p class="small muted" style="margin-top:6px">Every page is classed before reading. Only summary, chart and holdings pages are read for holdings; activity, fee tables and disclosures are skipped. Select a page to view it.</p></div>`
}
function chartsCard(s) {
  const cs = s.charts || []; if (!cs.length) return '';
  const chk = (S.an.statement_checks[s.id] || []).find(c => c.id === 'chart');
  return `<div class="card" data-tour="charts"><h3>Allocation read from charts</h3>${cs.map(c => {
    const det = c.type === 'pie' && chk && chk.detail ? Object.fromEntries(chk.detail.map(d => [d.label, d.holdings])) : null;
    return `<div class="chart-item"><div class="row small"><b class="grow">${esc(c.title || (c.type === 'pie' ? 'Pie chart' : 'Bar chart'))} · page ${c.page}</b><span class="pill p-plain">${c.type === 'pie' ? 'Pie' : 'Bar'} · ${c.method === 'vector' ? 'measured from the drawing' : c.method.startsWith('raster') ? 'measured from the image' : esc(c.method)}</span>
    <button class="btn sm" data-pv="${s.id}|${c.asset || 'page-' + c.page}">Show</button></div>
    <table><thead><tr><th>${c.type === 'pie' ? 'Slice' : 'Bar'}</th><th class="num">Chart</th>${det ? '<th class="num">From holdings</th>' : ''}</tr></thead><tbody>${c.values.map(v => `<tr><td>${v.color ? `<i class="sw" style="background:${v.color}"></i>` : ''}${esc(v.label)}</td><td class="num">${v.pct.toFixed(1)}%</td>${det ? `<td class="num">${det[v.label] != null ? det[v.label].toFixed(1) + '%' : '–'}</td>` : ''}</tr>`).join('')}</tbody></table>
    <p class="small muted">${esc(c.note)}. Confidence ${Math.round(c.confidence * 100)}%.${c.type === 'pie' && chk ? ' ' + esc(chk.text) + '.' : ''}</p></div>` }).join('')}</div>`
}
function vValidate() {
  const an = S.an; const pos = an.positions;
  const groups = ['approved', 'review', 'not_approved', 'unrecognized', 'held_away', 'cash'];
  const bs = an.comparison.by_status;
  const rows = S.vfilter ? pos.filter(p => p.status === S.vfilter) : pos;
  const cls = c => Object.entries(c).sort((a, b) => b[1] - a[1]).map(([k, w]) => `${an.classes[k].label}${w < .999 ? ' ' + Math.round(w * 100) + '%' : ''}`).join(', ');
  return `<div class="head"><div class="grow"><h1>Validate against the firm's approved list</h1><p>Every row is matched by symbol, by name, or by a category rule. The account type then decides whether it can move: employer plans, annuities and private securities stay where they are.</p></div></div>
  <div class="tiles" data-tour="status-tiles">${groups.map(g => `<div class="tile ${S.vfilter === g ? 'sel' : ''}"><button data-filter="${g}"><div class="k">${pill(g)}</div><div class="v">${bs[g]?.count || 0}</div><div class="s">${short(bs[g]?.value || 0)}</div></button></div>`).join('')}</div>
  <div class="row small" style="margin:12px 0 8px"><span class="muted grow">${S.vfilter ? `Showing ${STATUS[S.vfilter]} only. <a href="#" data-filter="">Show all</a>` : 'Select a tile to filter.'}</span><span class="muted">Approved list as of ${esc('1 Oct 2026')}</span></div>
  <div class="tw" data-tour="validate-table"><table><thead><tr><th>Statement</th><th>Security</th><th class="num">Value</th><th>Status</th><th>Why</th><th>Asset classes</th><th></th></tr></thead><tbody>
  ${rows.map(p => `<tr data-row="${p.key}"><td class="small">${esc(p.statement)}<span class="sub">${esc(p.institution)}</span></td><td><span class="mono">${esc(p.sym || '')}</span> ${esc(p.name)}${p.match && p.match !== p.sym ? `<span class="sub">Matched to ${esc(p.match)}</span>` : ''}</td>
    <td class="num">${money(p.mv)}</td><td>${pill(p.status)}${p.view && !['Covered'].includes(p.view) ? `<span class="sub">Research: ${esc(p.view)}</span>` : ''}</td><td class="small">${esc(p.reason)}${p.fill && ['not_approved', 'review'].includes(p.status) ? `<span class="sub">Approved alternative: <b>${esc(p.fill)}</b></span>` : ''}</td>
    <td class="small">${esc(cls(p.classes))}<span class="sub">from ${esc(p.class_source)}</span></td><td>${['unrecognized', 'not_approved', 'review'].includes(p.status) || an.overrides[p.key] ? `<button class="btn sm" data-act="resolve" data-key="${p.key}">${p.status === 'unrecognized' ? 'Resolve' : 'Change'}</button>` : ''}</td></tr>`).join('')}
  </tbody></table></div>
  <div class="row" style="margin-top:12px"><span class="grow"></span><button class="btn primary" data-go="compare">Compare inside and outside →</button></div>`;
}

function vCompare() {
  const an = S.an, c = an.comparison, m = an.now, h = an.household;
  const maxAbs = Math.max(.05, ...c.rows.map(r => Math.abs(r.gap)));
  const stance = s => s ? `<span class="pill ${s === 'Overweight' ? 'p-approved' : s === 'Underweight' ? 'p-not_approved' : 'p-plain'}">${s === 'Overweight' ? '▲' : s === 'Underweight' ? '▼' : '●'} ${s}</span>` : '';
  const worst = an.scenarios.map(s => [s, m.stress[s.id]]).sort((a, b) => a[1] - b[1])[0];
  return `<div class="head"><div class="grow"><h1>Inside vs outside, against the target</h1><p>Firm and outside holdings together, by asset class, next to the ${esc(h.model_name)} target and the CIO view. Everything on this page is calculated.</p></div></div>
  <div class="tiles" data-tour="cmp-tiles">
    <div class="tile"><div class="k">Held at the firm</div><div class="v">${short(c.inside_total)}</div><div class="s">${an.inside_count} positions</div></div>
    <div class="tile"><div class="k">Outside (from statements)</div><div class="v">${short(c.outside_total)}</div><div class="s">${an.statements.length} statements</div></div>
    <div class="tile"><div class="k">Stays held away</div><div class="v">${short(c.held_away)}</div><div class="s">plans, annuity, private</div></div>
    <div class="tile"><div class="k">Household risk</div><div class="v ${m.in_band ? '' : 'bad'}">${pct(m.vol)}</div><div class="s">band ${pct(h.band[0])}–${pct(h.band[1])}</div></div>
    <div class="tile"><div class="k">Tracking error vs target</div><div class="v">${pct(m.te)}</div><div class="s">Sharpe ${m.sharpe.toFixed(2)}</div></div>
    <div class="tile"><div class="k">Worst historical event</div><div class="v">${pct(worst[1])}</div><div class="s">${esc(worst[0].label)}</div></div>
  </div>
  <div class="card" style="margin-top:14px" data-tour="alloc"><div class="row"><h2 class="grow">Asset classes</h2><div class="legend"><span><i style="background:var(--firm)"></i>Firm</span><span><i style="background:var(--out)"></i>Outside</span><span>Gap bar: household minus target</span></div></div>
  <div class="tw" style="margin-top:10px;border:0"><table><thead><tr><th>Asset class</th><th>Firm + outside</th><th class="num">Firm</th><th class="num">Outside</th><th class="num">Household</th><th class="num">Target</th><th>Gap</th><th>CIO</th><th>Vs view</th></tr></thead><tbody>
  ${c.rows.map(r => { const tot = r.inside + r.outside, w = Math.min(50, Math.abs(r.gap) / maxAbs * 50); return `<tr><td>${esc(r.label)}<span class="sub">${esc(r.group)}</span></td>
    <td><div class="stackbar" title="Firm ${short(r.inside)}, outside ${short(r.outside)}">${tot ? `<i style="width:${r.inside / tot * 100}%;background:var(--firm)"></i><i style="width:${r.outside / tot * 100}%;background:var(--out)"></i>` : ''}</div></td>
    <td class="num">${short(r.inside)}</td><td class="num">${short(r.outside)}</td><td class="num">${pct(r.weight)}</td><td class="num">${pct(r.target)}</td>
    <td><div class="gapbar" title="${(r.gap * 100).toFixed(1)} pts"><span class="mid"></span><i style="${r.gap >= 0 ? `left:50%;width:${w}%` : `left:${50 - w}%;width:${w}%`};background:${Math.abs(r.gap) > .02 ? (r.gap > 0 ? 'var(--ink-2)' : 'var(--info)') : 'var(--ink-3)'}"></i></div><span class="sub">${r.gap >= 0 ? '+' : ''}${(r.gap * 100).toFixed(1)} pts</span></td>
    <td>${stance(r.cio)}</td><td class="small">${esc(r.stance_fit)}</td></tr>` }).join('')}
  </tbody></table></div><p class="small muted" style="margin-top:6px">CIO view as of ${esc(an.cio.as_of)}: ${esc(an.cio.headline)} Published house view, not generated.</p></div>
  <div class="grid3" style="margin-top:14px">
    <div class="card" data-tour="conc"><h3>Single names across all accounts</h3>${c.concentration.length ? `<table><thead><tr><th>Name</th><th class="num">Firm only</th><th class="num">Household</th></tr></thead><tbody>${c.concentration.map(x => `<tr><td class="mono">${esc(x.name)}${x.outside_direct ? `<span class="sub">${short(x.outside_direct)} held outside</span>` : ''}</td><td class="num">${an.comparison.inside_total ? pct(x.inside_weight) : '–'}</td><td class="num ${x.over_limit ? 'bad' : ''}">${pct(x.household_weight)}${x.over_limit ? ' ✕' : ''}</td></tr>`).join('')}</tbody></table><p class="small muted" style="margin-top:6px">Direct shares plus look-through of fund top holdings. Limit ${pct(h.limits.single_stock, 0)}.</p>` : '<p class="muted small">No single name near the limit.</p>'}</div>
    <div class="card"><h3>Fund costs outside</h3>${c.fees.length ? `<table><thead><tr><th>Fund</th><th class="num">Cost</th><th>Approved alternative</th><th class="num">Saving / yr</th></tr></thead><tbody>${c.fees.map(f => `<tr><td class="mono">${esc(f.sym)}</td><td class="num">${f.bps} bp</td><td class="mono">${esc(f.alt)} <span class="muted">${f.alt_bps} bp</span></td><td class="num">${money(f.saving)}</td></tr>`).join('')}</tbody></table>` : '<p class="muted small">No outside fund costs more than 10 bp above its approved alternative.</p>'}${m.fee_unknown ? `<p class="small muted" style="margin-top:6px">Costs not on the statements for ${short(m.fee_unknown)} (plan funds without a fee disclosure, annuity subaccounts, private holdings): request fee schedules.</p>` : ''}</div>
    <div class="card"><h3>Overlap and cash</h3><p class="small">Held both at the firm and outside: ${c.overlap.length ? c.overlap.map(x => `<span class="pill p-plain mono">${esc(x)}</span>`).join(' ') : '<span class="muted">none</span>'}</p><p class="small" style="margin-top:8px">Cash and cash equivalents outside: <b>${short(c.outside_cash)}</b>. The CIO is ${esc(an.cio.groups.cash.stance.toLowerCase())} on cash: ${esc(an.cio.groups.cash.note)}</p></div>
  </div>
  <div class="row" style="margin-top:12px"><span class="grow"></span><button class="btn primary" data-go="proposals">Build proposals →</button></div>`;
}

function vProposals() {
  const an = S.an, P = an.proposals, now = an.now, h = an.household;
  const sel = P.find(p => p.id === S.prop);
  const worst = m => Math.min(...Object.values(m.stress));
  const fails = p => p.checks.filter(c => !c.ok && !c.warn).length, warns = p => p.checks.filter(c => !c.ok && c.warn).length;
  const rowsM = [['Expected risk', m => pct(m.vol)], ['Tracking error vs target', m => pct(m.te)], ['Expected return', m => pct(m.er)], ['Sharpe', m => m.sharpe.toFixed(2)], ['Worst historical event', m => pct(worst(m))], ['Fund expenses / yr', m => money(m.fees)], ['Income / yr', m => short(m.income)]];
  const groupsOrder = ['Transfer in kind', 'Transfer as cash', 'Transfer and invest', 'Sell', 'Trim', 'Buy', 'Pending review', 'Stays outside'];
  const gkey = a => groupsOrder.find(g => a.action.startsWith(g)) || a.action;
  const acts = {}; sel.actions.forEach(a => (acts[gkey(a)] = acts[gkey(a)] || []).push(a));
  return `<div class="head"><div class="grow"><h1>Proposals</h1><p>Three ways to bring the outside accounts together with what is held at the firm. Firm guidance is applied to every proposal: approved securities only, new money tilted to the CIO view, the single-name and high-yield limits, and the client's gain budget.</p></div>
    <label class="row small" data-tour="budget">Gain budget <input type="number" id="budget" step="5000" min="0" value="${Math.round(h.gain_budget)}" style="width:130px"><button class="btn sm" data-act="budget">Apply</button></label></div>
  <div class="props" data-tour="props">${P.map(p => `<div class="prop ${p.id === S.prop ? 'on' : ''}" data-prop="${p.id}"><div class="row"><span class="pill p-plain">${p.id}</span><h3 class="grow">${esc(p.name)}</h3></div><p class="small muted">${esc(p.idea)}</p>
    <div class="kv"><span>Moves to the firm</span><span>${short(p.moved)}</span><span>Sold</span><span>${short(p.sold)}</span><span>Net realized gain</span><span>${money(p.net_gain)}</span><span>Estimated tax</span><span>${money(p.tax)}</span><span>Risk</span><span>${pct(p.metrics.vol)}</span><span>Tracking error</span><span>${pct(p.metrics.te)}</span></div>
    <div class="small">${fails(p) ? `<span class="bad">✕ ${fails(p)} check${fails(p) > 1 ? 's' : ''} failed</span>` : '<span class="ok">✓ blocking checks pass</span>'}${warns(p) ? ` · <span class="warn">! ${warns(p)} to note</span>` : ''}</div></div>`).join('')}</div>
  <div class="card" style="margin-top:14px" data-tour="prop-compare"><h3>Side by side</h3><div class="tw" style="border:0"><table><thead><tr><th></th><th class="num">Now</th>${P.map(p => `<th class="num">${p.id}. ${esc(p.name)}</th>`).join('')}</tr></thead><tbody>
    ${rowsM.map(([k, f]) => `<tr><td>${k}</td><td class="num">${f(now)}</td>${P.map(p => `<td class="num">${f(p.metrics)}</td>`).join('')}</tr>`).join('')}
    <tr><td>Estimated tax</td><td class="num">–</td>${P.map(p => `<td class="num">${money(p.tax)}</td>`).join('')}</tr>
    ${sel.checks.map((c, i) => `<tr><td>${esc(c.label)}</td><td class="num muted">–</td>${P.map(p => { const k = p.checks[i]; return `<td class="num ${k.ok ? 'ok' : k.warn ? 'warn' : 'bad'}" title="${esc(k.text)}">${k.ok ? '✓' : k.warn ? '!' : '✕'}</td>` }).join('')}</tr>`).join('')}
  </tbody></table></div><p class="small muted">Risk band ${pct(h.band[0])} to ${pct(h.band[1])}. Hover a check mark for the detail. Tax assumes long-term rates where the statement shows no holding period.</p></div>
  <div class="card" style="margin-top:14px" data-tour="actions"><div class="row"><h2 class="grow">${sel.id}. ${esc(sel.name)}: what happens to each position</h2><button class="btn sm" data-go="document">Check & document →</button></div>
  ${groupsOrder.filter(g => acts[g]).map(g => `<h3 style="margin:14px 0 6px">${g} <span class="muted">(${acts[g].length} · ${short(acts[g].reduce((a, x) => a + x.value, 0))})</span></h3><div class="tw"><table><tbody>${acts[g].map(a => `<tr><td style="width:34%"><span class="mono">${esc(a.sym || '')}</span> ${esc(a.name)}<span class="sub">${esc(a.from)}${a.dest ? ' → ' + esc(a.dest) : ''}</span></td><td class="num" style="width:110px">${money(a.value)}</td><td class="small">${esc(a.action !== g ? a.action + ': ' : '')}${esc(a.why)}</td></tr>`).join('')}</tbody></table></div>`).join('')}</div>`;
}

function vDocument() {
  const an = S.an, p = an.proposals.find(x => x.id === S.prop);
  return `<div class="head"><div class="grow"><h1>Check and document</h1><p>Proposal ${p.id}, ${esc(p.name)}. Failed checks block submission; warnings need an advisor note.</p></div><a class="btn" href="/api/sessions/${S.sid}/summary.md" download="outside-accounts-review.md" data-tour="download">⤓ Review record (.md)</a></div>
  <div class="grid2">
    <div class="card" data-tour="policy"><h2>Policy checks</h2><div class="checks">${p.checks.map(c => `<div class="chk"><b class="${c.ok ? 'ok' : c.warn ? 'warn' : 'bad'}">${c.ok ? '✓' : c.warn ? '!' : '✕'}</b><span><b>${esc(c.label)}</b><br><span class="muted small">${esc(c.text)}</span></span></div>`).join('')}</div></div>
    <div class="card stack" data-tour="talk"><div class="row"><h2 class="grow">Client talking points</h2><span class="pill p-ai">✦ AI-drafted in production</span></div>
      <div class="ai"><ul>${an.talking_points.map(t => `<li contenteditable="true">${esc(t)}</li>`).join('')}</ul></div>
      <p class="small muted">Drafted here from templates over the calculated figures. In production a language model writes these from the same figures; numbers come from the engine and are checked before display, and the advisor edits before use.</p></div>
  </div>
  <div class="grid2" style="margin-top:14px">
    <div class="card"><h2>Costs and constraints to disclose</h2><ul class="small" style="margin:0;padding-left:18px">
      <li>Estimated tax on sales: <b>${money(p.tax)}</b> (net realized gain ${money(p.net_gain)}; losses harvested ${money(p.realized_loss)}).</li>
      ${an.statements.filter(s => s.surrender).map(s => `<li>${esc(s.institution)}: ${esc(s.surrender)}. The contract is not touched in any proposal.</li>`).join('')}
      <li>Employer plan assets stay in the plan while the client is employed; consider them in the household allocation only.</li>
      <li>Transfers in kind are requested from the other institution; sales happen only after the assets arrive.</li></ul></div>
    <div class="card"><h2>Audit trail</h2><div class="small" style="max-height:220px;overflow:auto">${an.log.slice().reverse().map(l => `<div>· ${esc(l.event)} ${esc(l.statement || l.row || '')} ${esc(l.file || '')} ${l.rows != null ? l.rows + ' rows' : ''} ${l.change ? esc(JSON.stringify(l.change)) : ''} ${l.value != null ? money(l.value) : ''}</div>`).join('') || '<span class="muted">Nothing yet.</span>'}</div></div>
  </div>
  <p class="small muted" style="margin-top:14px">${esc(an.disclosures.tax)}</p>`;
}

function vWorkflow() {
  const an = S.an;
  return `<div class="head"><div class="grow"><h1>Recommended workflow for inside vs outside reviews</h1><p>Eight stages from consent to implementation, with the control that makes each one safe. Status reflects this household's review.</p></div></div>
  <div class="flow" data-tour="flow">${an.workflow.map(w => `<div class="st ${w.done ? 'done' : ''}"><h3>${esc(w.label)}</h3><p>${esc(w.what)}</p><div class="ctl"><b>Control:</b> ${esc(w.controls)}</div><div class="stat ${w.done ? 'ok' : 'warn'}">${esc(w.status)}</div></div>`).join('')}</div>
  <div class="grid2" style="margin-top:14px">
    <div class="card"><h2>Who does what</h2><table><tbody>
      <tr><td><b>Advisor</b></td><td class="small">Gets consent, uploads, confirms flagged rows, picks a proposal, edits talking points.</td></tr>
      <tr><td><b>Engine</b></td><td class="small">Extraction, validation, all figures, proposals and checks. Deterministic and repeatable.</td></tr>
      <tr><td><b>Language model</b></td><td class="small">Optional second reader for hard statements (every number must appear on the page) and draft narrative. Never sets a status or a figure.</td></tr>
      <tr><td><b>Supervision</b></td><td class="small">Approves exceptions to the approved list and any failed check that goes ahead.</td></tr>
      <tr><td><b>Operations</b></td><td class="small">Transfer requests, settlement, then trades.</td></tr></tbody></table></div>
    <div class="card"><h2>When to use which proposal</h2><ul class="small" style="margin:0;padding-left:18px">
      <li><b>A. Transfer what is approved</b>: first meeting, client not ready to sell, or most outside holdings already approved.</li>
      <li><b>B. Consolidate and align</b>: client wants one plan now and accepts the tax inside the gain budget.</li>
      <li><b>C. Tax-aware phased move</b>: large embedded gains; move tax-free now, revisit the rest each year or at events (CD maturity, end of surrender period, job change).</li></ul>
      <p class="small muted" style="margin-top:8px">Held-away accounts stay in the household view and are re-checked when the next statement arrives.</p></div>
  </div>`;
}

/* ------------------------------------------------------------------ events */
function bind() {
  $$('[data-go]').forEach(b => b.onclick = () => go(b.dataset.go));
  $$('[data-stmt]').forEach(b => b.onclick = () => { S.stmt = b.dataset.stmt; render() });
  $$('[data-pv]').forEach(b => b.onclick = () => { const [id, k] = b.dataset.pv.split('|'); S.pv = { ...(S.pv || {}), [id]: k }; render(); $('[data-tour=pagemap]')?.scrollIntoView({ block: 'start' }); scrollBy(0, -70) });
  $$('[data-prop]').forEach(b => b.onclick = () => { S.prop = b.dataset.prop; render() });
  $$('[data-filter]').forEach(b => b.onclick = e => { e.preventDefault(); S.vfilter = b.dataset.filter && S.vfilter !== b.dataset.filter ? b.dataset.filter : null; render() });
  $$('[data-act]').forEach(b => b.onclick = () => {
    const a = b.dataset.act;
    if (a === 'samples') loadSamples(b.dataset.set);
    if (a === 'rm') removeStmt(b.dataset.id);
    if (a === 'open') { S.stmt = b.dataset.id; go('review') }
    if (a === 'edit') editDialog(b.dataset.key);
    if (a === 'resolve') resolveDialog(b.dataset.key);
    if (a === 'budget') setBudget(+$('#budget').value);
  });
  const c = $('#consent'); if (c) c.onchange = () => { S.consent = c.checked; render() };
  const f = $('#file'); if (f) f.onchange = () => upload(f.files);
  const d = $('#drop');
  if (d) {
    d.ondragover = e => { e.preventDefault(); if (S.consent) d.classList.add('over') };
    d.ondragleave = () => d.classList.remove('over');
    d.ondrop = e => { e.preventDefault(); d.classList.remove('over'); upload(e.dataTransfer.files) };
  }
}
function dialog(html, onSave) {
  const sc = document.createElement('div'); sc.className = 'scrim'; sc.innerHTML = `<div class="dlg">${html}<div class="row"><span class="grow"></span><button class="btn" data-x>Cancel</button><button class="btn primary" data-save>Save</button></div></div>`;
  document.body.append(sc);
  sc.onclick = e => { if (e.target === sc || e.target.dataset.x !== undefined) sc.remove() };
  $('[data-save]', sc).onclick = async () => { await onSave(sc); sc.remove() };
  return sc;
}
function editDialog(key) {
  const [sid, row] = key.split(':'); const s = S.an.statements.find(x => x.id === sid); const h = s.holdings.find(x => String(x.row) === row); const ov = S.an.overrides[key] || {};
  const f = (k, lab, v, t = 'text') => `<label>${lab}<input type="${t}" name="${k}" value="${esc(ov[k] ?? v ?? '')}" step="any"></label>`;
  dialog(`<h2>Edit row</h2><p class="small muted">Read from ${esc(s.file)}: <span class="mono">${esc(h.source)}</span></p><div class="fields">${f('sym', 'Symbol', h.sym)}${f('desc', 'Description', h.desc)}${f('qty', 'Quantity', h.qty, 'number')}${f('price', 'Price', h.price, 'number')}${f('value', 'Market value', h.value, 'number')}${f('cost', 'Cost basis', h.cost, 'number')}</div>
    <label class="row small"><input type="checkbox" name="exclude" ${ov.exclude ? 'checked' : ''}> Exclude this row (not a holding)</label>`, async sc => {
    const body = { key }; $$('input', sc).forEach(i => { if (i.type === 'checkbox') { if (i.checked) body.exclude = true } else if (i.value !== '' && String(i.value) !== String(h[i.name] ?? '')) body[i.name] = i.type === 'number' ? +i.value : i.value });
    await override(body); toast('Row updated and logged');
  });
}
function resolveDialog(key) {
  const p = S.an.positions.find(x => x.key === key); const cls = Object.entries(S.an.classes);
  const main = Object.entries(p.classes).sort((a, b) => b[1] - a[1])[0]?.[0];
  dialog(`<h2>${esc(p.sym || '')} ${esc(p.name)}</h2><p class="small">${esc(p.reason)}</p><div class="fields">
    <label>Treat as<select name="status"><option value="not_approved" ${p.status === 'not_approved' ? 'selected' : ''}>Not approved: replace with an approved fund</option><option value="approved">Approved by exception (needs supervision sign-off)</option><option value="held_away">Leave held away</option></select></label>
    <label>Main asset class<select name="cls">${cls.map(([k, c]) => `<option value="${k}" ${k === main ? 'selected' : ''}>${esc(c.label)}</option>`).join('')}</select></label></div>
    <label class="fields" style="grid-template-columns:1fr"><label>Note for the record<input type="text" name="note" placeholder="e.g. Thematic quantum computing ETF; confirmed with the client"></label></label>`, async sc => {
    const st = $('[name=status]', sc).value, c = $('[name=cls]', sc).value, note = $('[name=note]', sc).value;
    await override({ key, status: st, classes: { [c]: 1 }, note: note || null }); toast('Resolved and logged');
  });
}

/* ------------------------------------------------------------------ guided tour */
const Tour = {
  i: 0, steps: [
    { t: 'Outside accounts, start to finish', b: 'This tour runs the whole flow on sample statements for a client household: five statements in five formats, read, checked against the approved list, compared with what is held at the firm, and turned into three proposals.', run: async () => { if (S.hh !== 'henderson') await newSession('henderson'); go('collect') } },
    { sel: '[data-tour=household]', t: 'Start from the household', b: 'Pick the client or prospect. The household brings its risk profile, target allocation, firm holdings and gain budget; every later step uses them.' },
    { sel: '[data-tour=consent]', t: 'Consent first', b: 'Uploads stay locked until client consent is recorded. Account numbers are kept to the last 4 digits and uploaded files are deleted once read.' },
    { sel: '[data-tour=drop]', t: 'Up to 5 statements at a time', b: 'PDF statements, scanned PDFs, portal screenshots, phone photos, Excel and CSV exports. Text PDFs use the text layer; images and scans go through OCR; spreadsheets are read cell by cell.' },
    { sel: '[data-tour=stmts]', t: 'Five formats, read in seconds', b: 'We loaded the samples: a brokerage PDF, a 401(k) screenshot, an Excel export, a photo of a bank statement and a scanned annuity summary. Each card shows the rows found and whether they add up to the statement total.', run: async () => { if (!S.an.statements.length) await loadSamples('henderson'); go('collect') } },
    { sel: '[data-tour=preview]', t: 'Statement and extraction side by side', b: 'The phone photo is slightly rotated and noisy. The reader straightens it, reads it, and finds the institution, owner, last 4 digits, date and total.', run: () => { S.stmt = 'H4'; go('review') } },
    { sel: '[data-tour=checks]', t: 'Checks on every statement', b: 'Rows reconcile to the printed total; the statement is recent; the owner matches the household; confidence is high. Anything doubtful is highlighted so the advisor confirms it before it is used.' },
    { sel: '[data-tour=rows]', t: 'Edit anything, with a record', b: 'Every value can be corrected or a row excluded. The change is logged with the original, and every figure downstream recalculates.', run: () => { S.stmt = 'H1'; go('review') } },
    { sel: '[data-tour=status-tiles]', t: 'Validated against the approved list', b: 'Each row is matched by symbol, by name, or by a category rule (municipal bonds, CDs, money market, private placements). Then the account type decides what can move.', run: () => { S.vfilter = null; go('validate') } },
    { sel: '[data-tour=validate-table]', t: 'Why each row landed where it did', b: 'QZLGX and TRVLX are not approved, so each is mapped to the approved fund for its asset class. ARKK and BAL-C are approved but rated Not recommended. The 401(k) funds and annuity subaccounts stay held away.', run: () => { S.vfilter = null; go('validate') } },
    { sel: '[data-tour=alloc]', t: 'Inside and outside together', b: 'Firm and outside holdings by asset class against the target, with the CIO stance and whether the household is with or against the view.', run: () => go('compare') },
    { sel: '[data-tour=conc]', t: 'What only shows up across accounts', b: 'NVDA and MSFT are held at the firm and outside. Looking through funds as well, NVDA is about a fifth of the household, twice the single-name limit.' },
    { sel: '[data-tour=props]', t: 'Three proposals with firm guidance applied', b: 'A moves approved positions with no tax. B replaces what is not approved, trims single names and invests toward the target with the CIO tilt, within the gain budget. C moves only what costs no tax, including harvesting the ARKK loss.', run: () => { S.prop = 'B'; go('proposals') } },
    { sel: '[data-tour=prop-compare]', t: 'Side by side, with checks', b: 'Risk, tracking error, return, worst historical event, fees, income and tax, plus every policy check per proposal.' },
    { sel: '[data-tour=actions]', t: 'Position by position', b: 'For the selected proposal: what transfers in kind, what is sold after transfer and why, what is bought with the CIO stance behind it, and what stays outside.' },
    { sel: '[data-tour=budget]', t: 'Change the gain budget', b: 'Agree a different gain budget with the client and every proposal recalculates: trims grow or shrink, and the checks update.' },
    { sel: '[data-tour=talk]', t: 'Checks, talking points and the record', b: 'Policy checks for the chosen proposal, draft talking points (marked as AI-drafted in production), and a downloadable review record for the file.', run: () => go('document') },
    { sel: '[data-tour=flow]', t: 'The recommended workflow', b: 'Eight stages from consent to implementation, each with the control that makes it safe, and live status for this review.', run: () => go('workflow') },
    { sel: '[data-tour=pagemap]', t: 'Long statements: every page classed first', b: 'A 28-page consolidated statement: summary, two chart pages, holdings across five pages, activity, fee tables and 16 pages of disclosures. Only the summary, chart and holdings pages are read for holdings; the other 20 are skipped, so transactions and fee tables never become holdings.', run: async () => { await newSession('kaplan'); await loadSamples('kaplan'); S.stmt = 'C1'; go('review') } },
    { sel: '[data-tour=charts]', t: 'Allocation that is only in a chart', b: 'The asset allocation on page 2 is only a pie chart and the sector mix on page 3 only a bar chart. Bars are measured from the drawing; pie slices from their area, with the legend read by OCR. The pie is then checked against the same split computed from the holdings.' },
    { sel: '[data-tour=meta]', t: 'Tables that span pages', b: 'The holdings table carries over page breaks, including a page with no repeated column header. Section subtotals are checked against their rows, and bond descriptions that wrap onto a second line stay with their row.' },
    { sel: '[data-tour=household]', t: 'Try the prospect next', b: 'Switch to the Rivera Household (prospect): a CSV export, a robo-adviser screenshot where OCR misreads VTI, and an IRA with a security nobody recognizes. Resolve it on Validate, then raise the gain budget on Proposals and watch the checks pass.', run: async () => { await newSession('rivera'); await loadSamples('rivera'); go('collect') } },
  ],
  start() { this.i = 0; document.body.style.paddingBottom = '70vh'; this.show() },
  stop(end) { $$('.tour-hole,.tour-card,.tour-block').forEach(e => e.remove()); if (end !== false) document.body.style.paddingBottom = '' },
  async show(noRun) {
    this.stop(false);
    const s = this.steps[this.i];
    if (s.run && !noRun) await s.run();
    await new Promise(r => setTimeout(r, 60));
    const el = s.sel ? $(s.sel) : null;
    const block = document.createElement('div'); block.className = 'tour-block'; document.body.append(block);
    const card = document.createElement('div'); card.className = 'tour-card';
    card.innerHTML = `<div class="tour-dots">${this.i + 1} of ${this.steps.length}</div><h3>${esc(s.t)}</h3><p>${esc(s.b)}</p><div class="row"><button class="btn ghost sm" data-t="end">End tour</button><span class="grow"></span>${this.i ? '<button class="btn sm" data-t="back">Back</button>' : ''}<button class="btn primary sm" data-t="next">${this.i === this.steps.length - 1 ? 'Finish' : 'Next'}</button></div>`;
    document.body.append(card);
    if (el) {
      const tall = el.getBoundingClientRect().height > innerHeight * .6;
      el.scrollIntoView({ block: tall ? 'start' : 'center' }); if (tall) scrollBy(0, -70);
      await new Promise(r => setTimeout(r, 80));
      const r = el.getBoundingClientRect(), hole = document.createElement('div'); hole.className = 'tour-hole';
      Object.assign(hole.style, { left: r.left - 6 + 'px', top: r.top - 6 + 'px', width: r.width + 12 + 'px', height: Math.min(r.height, innerHeight - 20) + 12 + 'px' });
      document.body.append(hole);
      const cw = card.offsetWidth, ch = card.offsetHeight;
      let top = r.bottom + 14, left = Math.min(Math.max(16, r.left), innerWidth - cw - 16);
      if (top + ch > innerHeight - 10) top = r.top - ch - 14;
      if (top < 10 || tall) { top = Math.max(10, innerHeight - ch - 16); left = innerWidth - cw - 16 }
      top = Math.max(10, Math.min(top, innerHeight - ch - 10));
      Object.assign(card.style, { top: top + 'px', left: left + 'px' });
    } else {
      block.style.background = 'rgba(10,15,12,.55)';
      Object.assign(card.style, { top: '50%', left: '50%', transform: 'translate(-50%,-50%)' });
    }
    card.onclick = e => { const t = e.target.dataset.t; if (t === 'end') this.stop(); if (t === 'back') { this.i--; this.show() } if (t === 'next') { if (this.i === this.steps.length - 1) this.stop(); else { this.i++; this.show() } } };
  }
};
addEventListener('keydown', e => { if (!$('.tour-card')) return; if (e.key === 'Escape') Tour.stop(); if (e.key === 'ArrowRight') $('.tour-card [data-t=next]')?.click(); if (e.key === 'ArrowLeft') $('.tour-card [data-t=back]')?.click() });
addEventListener('resize', () => { if ($('.tour-card')) Tour.show(true) });
boot();
