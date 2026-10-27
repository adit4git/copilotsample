/* Skill Studio front end. Plain JavaScript, no build step. All data comes from the API. */
'use strict';

const S = { meta: null, skills: [], graph: null, detail: {}, view: 'registry', sel: null, sub: 'overview', q: '', ftype: 'all', fstatus: 'all',
  mapSel: null, run: { skill: 'manager-sma-selection', client: 'henderson', asset_class: null, amount: null, result: null, busy: false },
  create: { text: '', mode: 'offline', result: null, md: '', validation: null, busy: false, saved: null } };
const TYPES = ['business', 'rules', 'policy', 'technical'];
const TLABEL = { technical: 'Technical', business: 'Business', policy: 'Policy', rules: 'Rules-driven' };
const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const money = (x) => { x = Number(x || 0); const a = Math.abs(x); const s = a >= 1e6 ? `$${(a / 1e6).toFixed(2)}M` : a >= 1e3 ? `$${Math.round(a / 1e3)}K` : `$${Math.round(a)}`; return (x < 0 ? '-' : '') + s; };

async function api(path, opts = {}) {
  const r = await fetch(path, { headers: { 'content-type': 'application/json' }, ...opts, body: opts.body ? JSON.stringify(opts.body) : undefined });
  const ct = r.headers.get('content-type') || '';
  const data = ct.includes('json') ? await r.json() : await r.text();
  if (!r.ok) { const e = new Error((data && data.detail && (data.detail.message || data.detail)) || r.statusText); e.data = data; throw e; }
  return data;
}
function toast(msg) { const t = $('#toast'); t.textContent = msg; t.classList.add('show'); clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove('show'), 2600); }
const tb = (t) => `<span class="tb ${esc(t)}">${esc(TLABEL[t] || t)}</span>`;
const pill = (s) => `<span class="pill ${esc(s)}">${esc(s)}</span>`;
const skillChip = (n) => { const s = S.skills.find((x) => x.name === n); return `<a class="chip" href="#/registry/${esc(n)}"><span class="dot ${s ? s.type : ''}"></span>${esc(n)}</a>`; };

/* ---------- tiny Markdown for skill prose ---------- */
function md(src) {
  const lines = String(src || '').split('\n'); let out = ''; let i = 0;
  const inline = (t) => esc(t).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>').replace(/\*([^*]+)\*/g, '<i>$1</i>');
  while (i < lines.length) {
    const l = lines[i];
    if (/^\s*\|/.test(l)) {
      const rows = []; while (i < lines.length && /^\s*\|/.test(lines[i])) rows.push(lines[i++]);
      const cells = (r) => r.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim());
      const body = rows.filter((r, k) => k !== 1 || !/^[\s|:-]+$/.test(r));
      out += '<table><thead><tr>' + cells(body[0]).map((c) => `<th>${inline(c)}</th>`).join('') + '</tr></thead><tbody>' + body.slice(1).map((r) => '<tr>' + cells(r).map((c) => `<td>${inline(c)}</td>`).join('') + '</tr>').join('') + '</tbody></table>';
      continue;
    }
    if (/^\s*[-*] /.test(l)) { let items = ''; while (i < lines.length && /^\s*[-*] /.test(lines[i])) items += `<li>${inline(lines[i++].replace(/^\s*[-*] /, ''))}</li>`; out += `<ul>${items}</ul>`; continue; }
    if (/^>\s?/.test(l)) { let q = ''; while (i < lines.length && /^>\s?/.test(lines[i])) q += lines[i++].replace(/^>\s?/, '') + ' '; out += `<blockquote>${inline(q)}</blockquote>`; continue; }
    if (/^#{1,4} /.test(l)) { out += `<h3>${inline(l.replace(/^#+ /, ''))}</h3>`; i++; continue; }
    if (!l.trim()) { i++; continue; }
    let p = ''; while (i < lines.length && lines[i].trim() && !/^(\s*[-*] |>|\s*\||#{1,4} )/.test(lines[i])) p += lines[i++] + ' ';
    out += `<p>${inline(p)}</p>`;
  }
  return `<div class="prose">${out}</div>`;
}

/* ---------- JSON-Logic in words ---------- */
function jl(e) {
  if (Array.isArray(e)) return '[' + e.map(jl).join(', ') + ']';
  if (e === null || typeof e !== 'object') return typeof e === 'string' ? `"${e}"` : String(e);
  const [op, a] = Object.entries(e)[0]; const args = Array.isArray(a) ? a : [a];
  const v = (x) => jl(x);
  switch (op) {
    case 'var': return String(Array.isArray(a) ? a[0] : a).replace(/^item\./, '');
    case 'and': return args.map(v).join(' and ');
    case 'or': return '(' + args.map(v).join(' or ') + ')';
    case '!': case 'not': return 'not ' + v(args[0]);
    case '!!': return v(args[0]) + ' is present';
    case 'in': return `${v(args[0])} in ${v(args[1])}`;
    case 'count': return `count of ${v(args[0])}`;
    case 'if': return `if ${v(args[0])} then ${v(args[1])} else ${v(args[2])}`;
    case '==': return `${v(args[0])} = ${v(args[1])}`;
    case '!=': return `${v(args[0])} ≠ ${v(args[1])}`;
    default: return args.length === 2 ? `${v(args[0])} ${op.replace('>=', '≥').replace('<=', '≤')} ${v(args[1])}` : `${op}(${args.map(v).join(', ')})`;
  }
}

/* ---------- data loading ---------- */
async function loadAll() {
  [S.meta, S.skills, S.graph] = await Promise.all([api('/api/meta'), api('/api/skills'), api('/api/graph')]);
  S.detail = {};
}
async function detail(name) { if (!S.detail[name]) S.detail[name] = await api(`/api/skills/${encodeURIComponent(name)}`); return S.detail[name]; }

/* ---------- routing ---------- */
function route() {
  const [, view = 'registry', arg] = location.hash.split('/');
  S.view = ['registry', 'map', 'run', 'create'].includes(view) ? view : 'registry';
  if (S.view === 'registry') S.sel = arg ? decodeURIComponent(arg) : (S.sel || 'manager-sma-selection');
  if (S.view === 'run' && arg) S.run.skill = decodeURIComponent(arg);
  document.querySelectorAll('.tabs a').forEach((a) => a.classList.toggle('on', a.dataset.view === S.view));
  paint();
}
async function paint() {
  const v = $('#view');
  try {
    if (S.view === 'registry') v.innerHTML = await viewRegistry();
    else if (S.view === 'map') { v.innerHTML = viewMap(); bindMap(); }
    else if (S.view === 'run') v.innerHTML = viewRun();
    else v.innerHTML = viewCreate();
  } catch (e) { v.innerHTML = `<div class="card pad"><div class="callout bad">${esc(e.message)}</div></div>`; }
}

/* ---------- registry ---------- */
function groupOf(s) { return s.capability ? 'Capabilities' : s.abstract ? 'Parent processes' : TLABEL[s.type]; }
async function viewRegistry() {
  const q = S.q.toLowerCase();
  const list = S.skills.filter((s) => (S.ftype === 'all' || s.type === S.ftype) && (S.fstatus === 'all' || s.status === S.fstatus)
    && (!q || (s.name + ' ' + s.description + ' ' + s.owner + ' ' + s.tags.join(' ')).toLowerCase().includes(q)));
  const order = ['Capabilities', 'Parent processes', 'Business', 'Rules-driven', 'Policy', 'Technical'];
  const groups = order.map((g) => [g, list.filter((s) => groupOf(s) === g)]).filter(([, l]) => l.length);
  const counts = Object.fromEntries(TYPES.map((t) => [t, S.skills.filter((s) => s.type === t).length]));
  const left = `<div class="card"><div class="filters">
      <input data-q placeholder="Search name, purpose, owner…" value="${esc(S.q)}" aria-label="Search skills">
      <div class="seg" role="group" aria-label="Type">${['all', ...TYPES].map((t) => `<button data-ftype="${t}" class="${S.ftype === t ? 'on' : ''}">${t === 'all' ? `All ${S.skills.length}` : `${TLABEL[t]} ${counts[t]}`}</button>`).join('')}</div>
      <div class="seg" role="group" aria-label="Status">${['all', 'approved', 'draft', 'retired'].map((t) => `<button data-fstatus="${t}" class="${S.fstatus === t ? 'on' : ''}">${t === 'all' ? 'Any status' : t}</button>`).join('')}</div>
    </div><div class="slist">${groups.map(([g, l]) => `<div class="sgroup kicker">${g} · ${l.length}</div>` + l.map((s) => `
      <button class="sitem ${S.sel === s.name ? 'on' : ''}" data-open="${esc(s.name)}"><b>${esc(s.title || s.name)}</b>
        <div class="meta">${tb(s.type)}<span>v${esc(s.version)}</span>${s.status !== 'approved' ? pill(s.status) : ''}${s.used_by ? `<span>used by ${s.used_by}</span>` : ''}</div></button>`).join('')).join('') || '<div class="empty">No skills match.</div>'}</div></div>`;
  let right = '<div class="card pad empty">Select a skill.</div>';
  if (S.sel && S.skills.some((s) => s.name === S.sel)) right = await skillDetail(await detail(S.sel));
  return `<h1>Skills registry</h1><p class="lede">Every skill is one SKILL.md file in the standard format. Skills come in four types, inherit from parents, and depend on each other to deliver a capability. Select one to see how it is built and who relies on it.</p><div class="split">${left}${right}</div>`;
}

function relRow(k, html) { return `<div class="k">${k}</div><div class="row">${html || '<span class="muted small">none</span>'}</div>`; }
async function skillDetail(d) {
  const imp = d.dependents; const caps = imp.filter((x) => x.capability);
  const chain = d.resolved.chain.slice(1);
  const runnable = !d.abstract;
  const head = `<div class="dhead"><div><div class="row">${tb(d.type)}${d.capability ? '<span class="pill cap">capability</span>' : ''}${d.abstract ? '<span class="pill abs">abstract parent</span>' : ''}${pill(d.status)}</div>
      <h1 style="margin-top:8px">${esc(d.title || d.name)}</h1><div class="dname">${esc(d.name)} · v${esc(d.version)}</div></div>
      <div class="row">${runnable ? `<a class="btn" href="#/run/${esc(d.name)}">Run</a>` : ''}${d.status === 'draft' ? `<button class="btn ghost" data-approve="${esc(d.name)}">Approve</button>` : ''}
      <button class="btn ghost" data-copy="${esc(d.name)}">Copy SKILL.md</button><a class="btn ghost" href="/api/skills/${esc(d.name)}/raw" download="${esc(d.name)}-SKILL.md">Download</a></div></div>
    <p class="lede" style="margin-top:10px">${esc(d.description)}</p>
    <div class="facts"><div class="fact"><div class="k">Owner</div><div class="v">${esc(d.owner || '—')}</div></div>
      <div class="fact"><div class="k">Reads</div><div class="v mono small">${esc(d.resolved.inputs.join(', ') || '—')}</div></div>
      <div class="fact"><div class="k">Produces</div><div class="v mono small">${esc(d.resolved.outputs.join(', ') || '—')}</div></div>
      <div class="fact"><div class="k">Tests</div><div class="v">${d.test_results.length ? `<span class="${d.test_results.every((t) => t.ok) ? 'ok' : 'bad'}">${d.test_results.filter((t) => t.ok).length} of ${d.test_results.length} pass</span>` : '<span class="warn">none</span>'}</div></div></div>
    <div class="rel">
      ${relRow('Inherits from', chain.map((c, i) => (i ? '<span class="muted">→</span>' : '') + skillChip(c)).join(' '))}
      ${relRow('Uses', d.resolved.uses.map(skillChip).join(''))}
      ${relRow('Used by', imp.filter((x) => x.depth === 1).map((x) => skillChip(x.name) + (x.kind === 'extends' ? '<span class="muted small">(extends)</span>' : '')).join(''))}
      <div class="k">Change impact</div><div class="small">${imp.length ? `Changing this skill reaches <b>${imp.length}</b> skill${imp.length > 1 ? 's' : ''}${caps.length ? `, including <b>${caps.length}</b> capabilit${caps.length > 1 ? 'ies' : 'y'}: ${caps.map((c) => esc(c.name)).join(', ')}` : ''}.` : 'Nothing depends on it yet.'}</div>
    </div>`;
  const tabs = [['overview', 'Overview'], ['logic', 'Logic'], ['tests', `Tests (${d.test_results.length})`], ['raw', 'SKILL.md'], ['history', `History (${d.history.length})`]];
  const sub = `<div class="subtabs" role="tablist">${tabs.map(([k, l]) => `<button data-sub="${k}" class="${S.sub === k ? 'on' : ''}" role="tab">${l}</button>`).join('')}</div><div class="panel">${subPanel(d)}</div>`;
  return `<div class="card pad">${head}${sub}</div>`;
}

function depTree(name, seen = new Set(), depth = 0) {
  const edges = S.graph.edges.filter((e) => e.from === name);
  if (!edges.length || depth > 7) return '';
  return '<ul>' + edges.map((e) => {
    const s = S.skills.find((x) => x.name === e.to); const loop = seen.has(e.to);
    return `<li>${e.kind === 'extends' ? '<span class="muted small">extends</span> ' : ''}<a class="chip" href="#/registry/${esc(e.to)}"><span class="dot ${s ? s.type : ''}"></span>${esc(e.to)}</a>${loop ? ' <span class="muted small">(shown above)</span>' : depTree(e.to, new Set([...seen, e.to]), depth + 1)}</li>`;
  }).join('') + '</ul>';
}

function subPanel(d) {
  if (S.sub === 'overview') {
    const tree = depTree(d.name, new Set([d.name]));
    return md(d.prose) + `<hr class="sep"><h3>What it needs to run</h3><p class="muted small" style="margin:4px 0 8px">Everything below is resolved before or while this skill runs. Dashed lines are inheritance.</p><div class="tree">${tree || '<span class="muted small">No dependencies: it runs on the request alone.</span>'}</div>`;
  }
  if (S.sub === 'logic') return logicPanel(d);
  if (S.sub === 'tests') return d.test_results.length ? d.test_results.map((t) => `<div class="tres"><span class="${t.ok ? 'ok' : 'bad'}">${t.skipped ? '–' : t.ok ? '✓' : '✗'}</span><div><b>${esc(t.name)}</b><div class="muted small">${esc(t.detail)}</div></div></div>`).join('') : '<div class="callout warn">No tests. A skill needs at least one passing test before it can be approved.</div>';
  if (S.sub === 'raw') return `<pre class="code">${esc(d.raw)}</pre>`;
  if (S.sub === 'history') return d.history.length ? `<table class="t"><thead><tr><th>Version</th><th>Status then</th><th></th></tr></thead><tbody>${d.history.map((h) => `<tr><td class="mono">${esc(h.version)}</td><td>${pill(h.status)}</td><td><a href="/api/skills/${esc(d.name)}/history/${esc(h.version)}" target="_blank" rel="noopener">View SKILL.md</a></td></tr>`).join('')}<tr><td class="mono">${esc(d.version)}</td><td>${pill(d.status)} <span class="muted small">current</span></td><td></td></tr></tbody></table>` : `<p class="muted">Only version ${esc(d.version)} so far. Saving a change keeps the previous version here.</p>`;
  return '';
}

function src(x, d) {
  if (x.disabled) return `<span class="inh">switched off by ${esc(x.disabled_by)}</span>`;
  if (x.overrides) return `<span class="inh ovr">overrides ${esc(x.overrides)}</span>`;
  return x.from === d.name ? '<span class="inh own">own</span>' : `<span class="inh">inherited from ${esc(x.from)}</span>`;
}
function paramsTable(p) {
  const rows = Object.entries(p || {}); if (!rows.length) return '';
  return `<h3 style="margin:16px 0 6px">Parameters</h3><table class="t"><tbody>${rows.map(([k, v]) => `<tr><td class="mono">${esc(k)}</td><td class="mono">${esc(typeof v === 'object' ? JSON.stringify(v) : v)}</td></tr>`).join('')}</tbody></table>`;
}
function logicPanel(d) {
  const L = d.resolved.logic; let html = '';
  if (d.type === 'rules') {
    html += `<p class="muted small">${L.over ? `Runs once per item in <code>${esc(L.over)}</code> and writes the survivors to <code>${esc(L.into)}</code>.` : `Runs once for the client and writes findings to <code>${esc(L.into)}</code>.`} Effective rules after inheritance:</p>
      <table class="t"><thead><tr><th>Rule</th><th>Outcome</th><th>When</th><th>Source</th></tr></thead><tbody>${(L.rules || []).map((r) => `<tr class="${r.disabled ? 'dis' : ''}"><td class="mono">${esc(r.id)}</td><td>${esc(r.outcome || '')}</td><td class="mono small">${esc(r.when ? jl(r.when) : '')}</td><td>${src(r, d)}</td></tr>`).join('')}</tbody></table>`;
  } else if (d.type === 'policy') {
    html += (L.constraints || []).length ? `<table class="t"><thead><tr><th>Check</th><th>Requirement</th><th>Applies to</th><th>If broken</th><th>Source</th></tr></thead><tbody>${(L.constraints || []).map((c) => `<tr><td class="mono">${esc(c.id)}</td><td class="mono small">${'must' in c ? 'must: ' + esc(jl(c.must)) : 'must not: ' + esc(jl(c.must_not))}</td><td>${c.scope === 'run' || !L.over ? 'the whole run' : 'each item in ' + esc(L.over)}</td><td>${c.severity === 'warn' ? '<span class="warn">warn</span>' : '<span class="bad">block</span>'}</td><td>${src(c, d)}</td></tr>`).join('')}</tbody></table>` : '';
    if (L.required_phrases || L.forbidden_phrases) html += `<h3 style="margin:16px 0 6px">Wording, checked in <code>${esc(L.text_key)}</code></h3><div class="row">${(L.required_phrases || []).map((p) => `<span class="chip">must include “${esc(p)}”</span>`).join('')}${(L.forbidden_phrases || []).map((p) => `<span class="chip">never “${esc(p)}”</span>`).join('')}</div>`;
  } else if (d.type === 'technical') {
    const op = L.op || {};
    html += `<div class="callout info">Calls the <b class="mono">${esc(op.name)}</b> operation: ${esc((S.meta.ops || {})[op.name] || '')}. Technical skills cannot carry their own code; they configure an operation from the reviewed library.</div>`;
    html += paramsTable({ ...(op.params || {}) });
    if (L.params && L.params.weights) {
      const w = L.params.weights; const tot = Object.values(w).reduce((a, b) => a + b, 0) || 1;
      html += `<h3 style="margin:16px 0 6px">Weights</h3><table class="t"><tbody>${Object.entries(w).map(([k, v]) => `<tr><td class="mono">${esc(k)}</td><td style="width:55%"><div style="height:8px;border-radius:4px;background:var(--tech);width:${(100 * v / tot).toFixed(0)}%" title="${v}"></div></td><td class="num">${v}</td><td class="small muted">${L.params.better && L.params.better[k] === 'low' ? 'lower is better' : 'higher is better'}</td></tr>`).join('')}</tbody></table>`;
    } else html += paramsTable(L.params);
  } else if (d.type === 'business') {
    const own = (S.skills.find((s) => s.name === d.name) || {});
    const inherited = !(d.logic.steps) && d.resolved.chain.length > 1;
    html += inherited ? `<div class="callout info">Steps are inherited from <b>${esc(d.resolved.chain[1])}</b>. This skill only sets the parameters below.</div>` : '';
    html += `<ol class="steps" style="margin-top:12px">${(L.steps || []).map((st) => {
      if (st.use) { const s = S.skills.find((x) => x.name === st.use) || {}; return `<li>${tb(s.type || '')}<a href="#/registry/${esc(st.use)}">${esc(st.use)}</a>${st.with ? `<span class="muted small mono">with ${esc(JSON.stringify(st.with))}</span>` : ''}</li>`; }
      if (st.take) return `<li><b>Take</b> the top ${esc(st.take.top)} of <code>${esc(st.take.from)}</code> into <code>${esc(st.take.into)}</code></li>`;
      if (st.rank) return `<li><b>Rank</b> <code>${esc(st.rank.over)}</code> by ${esc(st.rank.label || jl(st.rank.by))}</li>`;
      if (st.set) return `<li><b>Set</b> <code>${esc(st.set.field)}</code> on <code>${esc(st.set.over)}</code>: <span class="mono small">${esc(jl(st.set.value))}</span></li>`;
      if (st.compose) return `<li><b>Write</b> <code>${esc(st.compose.into)}</code> from the run's results</li>`;
      if (st.note) return `<li><b>Manual step</b> for a person: ${esc(st.note)}</li>`;
      return `<li>${esc(JSON.stringify(st))}</li>`;
    }).join('')}</ol>`;
    html += paramsTable(L.params);
    void own;
  }
  return html;
}

/* ---------- dependency map ---------- */
function layout() {
  const nodes = S.graph.nodes.map((n) => ({ ...n })); const by = Object.fromEntries(nodes.map((n) => [n.name, n]));
  const deps = (n) => S.graph.edges.filter((e) => e.from === n && by[e.to]).map((e) => e.to);
  const memo = {};
  const lvl = (n, seen = new Set()) => { if (n in memo) return memo[n]; if (seen.has(n)) return 0; seen.add(n); const d = deps(n); memo[n] = d.length ? 1 + Math.max(...d.map((x) => lvl(x, seen))) : 0; return memo[n]; };
  nodes.forEach((n) => { n.level = lvl(n.name); });
  const maxL = Math.max(...nodes.map((n) => n.level));
  const W = 184, H = 50, GX = 12, GY = 58, PER = 7, X0 = 128; let rows = [];
  for (let l = maxL; l >= 0; l--) { const r = nodes.filter((n) => n.level === l); for (let i = 0; i < r.length; i += PER) rows.push({ level: l, items: r.slice(i, i + PER) }); }
  const place = (row) => { const total = row.items.length * W + (row.items.length - 1) * GX; const x0 = Math.max(X0, (PER * (W + GX) - total) / 2 + X0); row.items.forEach((n, i) => { n.x = x0 + i * (W + GX); }); };
  rows.forEach(place);
  for (let pass = 0; pass < 4; pass++) rows.forEach((row, ri) => {
    const others = rows.filter((_, k) => k !== ri).flatMap((r) => r.items);
    const pos = Object.fromEntries(others.map((n) => [n.name, n.x ?? 0]));
    row.items.forEach((n) => { const ps = S.graph.edges.filter((e) => (e.to === n.name && e.from in pos) || (e.from === n.name && e.to in pos)).map((e) => pos[e.to === n.name ? e.from : e.to]); n.bc = ps.length ? ps.reduce((a, b) => a + b, 0) / ps.length : (n.x ?? 0); });
    row.items.sort((a, b) => a.bc - b.bc);
    const total = row.items.length * W + (row.items.length - 1) * GX; const x0 = Math.max(X0, (PER * (W + GX) - total) / 2 + X0);
    row.items.forEach((n, i) => { n.x = x0 + i * (W + GX); });
  });
  rows[0].items.forEach((n, i) => { if (n.x == null) n.x = X0 + i * (W + GX); });
  rows.forEach((row, ri) => row.items.forEach((n) => { n.y = 40 + ri * (H + GY); n.w = W; n.h = H; }));
  return { nodes, by, rows, W: X0 + PER * (W + GX) + 10, Hh: 40 + rows.length * (H + GY), maxL };
}
const LAYER_NAMES = (l, maxL) => l === 0 ? 'Foundations' : l === maxL ? 'Top level' : `Layer ${l}`;
function viewMap() {
  const L = layout(); S._layout = L;
  const sel = S.mapSel; const closure = new Set(); const impact = new Set();
  if (sel) {
    const walk = (n) => S.graph.edges.filter((e) => e.from === n).forEach((e) => { if (!closure.has(e.to)) { closure.add(e.to); walk(e.to); } }); walk(sel);
    const up = (n) => S.graph.edges.filter((e) => e.to === n).forEach((e) => { if (!impact.has(e.from)) { impact.add(e.from); up(e.from); } }); up(sel);
  }
  const edges = S.graph.edges.filter((e) => L.by[e.from] && L.by[e.to]).map((e) => {
    const a = L.by[e.from], b = L.by[e.to]; const x1 = a.x + a.w / 2, y1 = a.y + a.h, x2 = b.x + b.w / 2, y2 = b.y;
    const my = (y1 + y2) / 2; const cls = ['e', e.kind === 'extends' ? 'ext' : ''];
    if (sel) { if ((e.from === sel || closure.has(e.from)) && closure.has(e.to)) cls.push('hot'); else if ((impact.has(e.from)) && (e.to === sel || impact.has(e.to))) cls.push('hotimp'); else cls.push('dim'); }
    return `<path class="${cls.join(' ')}" d="M${x1},${y1} C${x1},${my} ${x2},${my} ${x2},${y2 - 4}" marker-end="url(#${e.kind === 'extends' ? 'tri' : 'arr'})"/>`;
  }).join('');
  const color = { technical: 'var(--tech)', business: 'var(--biz)', policy: 'var(--pol)', rules: 'var(--rul)' };
  const nodes = L.nodes.map((n) => {
    const st = !sel ? '' : n.name === sel ? 'sel' : closure.has(n.name) ? 'dep' : impact.has(n.name) ? 'imp' : 'dim';
    const label = n.name.length > 27 ? n.name.slice(0, 26) + '…' : n.name;
    return `<g class="node ${st}" data-node="${esc(n.name)}" tabindex="0" role="button" aria-label="${esc(n.name)}, ${esc(TLABEL[n.type])} skill"><title>${esc(n.name)} · ${esc(TLABEL[n.type])} · v${esc(n.version)}\n${esc(n.description)}</title>
      <rect class="box" x="${n.x}" y="${n.y}" width="${n.w}" height="${n.h}" rx="8"/><rect class="bar" x="${n.x}" y="${n.y}" width="5" height="${n.h}" rx="2" fill="${color[n.type]}"/>
      <text x="${n.x + 13}" y="${n.y + 20}">${esc(label)}</text><text class="sub" x="${n.x + 13}" y="${n.y + 37}">${esc(TLABEL[n.type])}${n.capability ? ' · capability' : n.abstract ? ' · parent' : ''}${n.status === 'draft' ? ' · draft' : ''}</text></g>`;
  }).join('');
  const seen = new Set(); const layers = L.rows.map((r) => { if (seen.has(r.level)) return ''; seen.add(r.level); return `<text class="layer" x="16" y="${r.items[0].y + 29}">${LAYER_NAMES(r.level, L.maxL)}</text>`; }).join('');
  const svg = `<svg class="map" viewBox="0 0 ${L.W} ${L.Hh}" width="100%" role="img" aria-label="Dependency map of ${L.nodes.length} skills">
    <defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="var(--line-2)"/></marker>
    <marker id="tri" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="var(--surface)" stroke="var(--ink-3)"/></marker></defs>${layers}${edges}${nodes}</svg>`;
  let info = '<p class="muted small">Select a skill to see everything it depends on (green) and everything that would be affected if it changed (red, dashed).</p>';
  if (sel) {
    const n = L.by[sel]; const caps = [...impact].filter((x) => L.by[x] && L.by[x].capability);
    info = `<div class="row" style="justify-content:space-between"><div class="row">${tb(n.type)}<b>${esc(sel)}</b><span class="muted small">v${esc(n.version)}</span></div><div class="row"><a class="btn ghost sm" href="#/registry/${esc(sel)}">Open in registry</a>${n.abstract ? '' : `<a class="btn sm" href="#/run/${esc(sel)}">Run</a>`}<button class="btn ghost sm" data-mapclear>Clear</button></div></div>
      <p class="small" style="margin:8px 0 0">${esc(n.description)}</p><p class="small" style="margin:8px 0 0"><b>${closure.size}</b> skills needed to deliver it · <b>${impact.size}</b> skills affected by a change${caps.length ? ` (capabilities: ${caps.map(esc).join(', ')})` : ''}.</p>`;
  }
  const legend = `<div class="legend">${TYPES.map((t) => `<span><span class="tb ${t}">${TLABEL[t]}</span></span>`).join('')}
    <span><svg width="44" height="10"><path d="M2,5 H36" stroke="var(--ink-3)" stroke-width="1.4"/><path d="M34,1 L42,5 L34,9 z" fill="var(--ink-3)"/></svg> uses</span>
    <span><svg width="44" height="10"><path d="M2,5 H34" stroke="var(--ink-3)" stroke-width="1.4" stroke-dasharray="5 4"/><path d="M34,1 L42,5 L34,9 z" fill="var(--surface)" stroke="var(--ink-3)"/></svg> extends (inherits)</span></div>`;
  return `<h1>Dependency map</h1><p class="lede">Capabilities at the top are delivered by the skills below them. Arrows point from a skill to what it relies on; dashed arrows are inheritance from a parent skill.</p>
    <div class="card pad stack">${legend}<div class="mapwrap">${svg}</div><div>${info}</div></div>`;
}
function bindMap() {
  document.querySelectorAll('[data-node]').forEach((g) => {
    const pick = () => { S.mapSel = S.mapSel === g.dataset.node ? null : g.dataset.node; paint(); };
    g.addEventListener('click', pick); g.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(); } });
  });
}

/* ---------- run ---------- */
function viewRun() {
  const R = S.run; const m = S.meta;
  const runnable = S.skills.filter((s) => !s.abstract);
  const caps = runnable.filter((s) => s.capability); const rest = runnable.filter((s) => !s.capability);
  const cl = m.clients.find((c) => c.id === R.client) || m.clients[0];
  const ac = R.asset_class || cl.request.asset_class; const amt = R.amount ?? cl.request.amount;
  const opt = (s) => `<option value="${esc(s.name)}" ${s.name === R.skill ? 'selected' : ''}>${esc(s.name)} (${esc(TLABEL[s.type])})</option>`;
  const form = `<div class="card pad"><div class="form">
    <div><label for="rs">Skill or capability</label><select id="rs" data-rk="skill"><optgroup label="Capabilities">${caps.map(opt).join('')}</optgroup><optgroup label="Other skills">${rest.map(opt).join('')}</optgroup></select></div>
    <div><label for="rc">Client</label><select id="rc" data-rk="client">${m.clients.map((c) => `<option value="${c.id}" ${c.id === R.client ? 'selected' : ''}>${esc(c.name)} · ${esc(c.profile)}</option>`).join('')}</select></div>
    <div><label for="ra">Asset class</label><select id="ra" data-rk="asset_class">${Object.entries(m.asset_classes).map(([k, v]) => `<option value="${k}" ${k === ac ? 'selected' : ''}>${esc(v)}</option>`).join('')}</select></div>
    <div><label for="rm">Amount to invest ($)</label><input id="rm" data-rk="amount" type="number" min="0" step="10000" value="${amt}"></div>
    <div><button class="btn" data-run ${R.busy ? 'disabled' : ''}>${R.busy ? 'Running…' : 'Run'}</button></div></div></div>`;
  return `<h1>Run a capability</h1><p class="lede">Runs a skill on an illustrative client and shows every skill that took part, in order, with each decision it made. Nothing is sent or traded.</p>${form}${R.result ? runResult(R.result) : ''}`;
}
function runResult(r) {
  const skills = r.trace.filter((e) => e.kind === 'skill');
  const uniq = [...new Map(skills.map((e) => [e.skill, e])).values()];
  const byType = TYPES.map((t) => [t, uniq.filter((e) => e.type === t).length]).filter(([, n]) => n);
  const dec = skills.flatMap((e) => e.decisions);
  const cnt = (o) => dec.filter((d) => o.includes(d.outcome)).length;
  const ctx = r.context; const blocked = ctx.blocked || [];
  const drafts = uniq.filter((e) => e.status === 'draft');
  const head = `<div class="card pad" style="margin-top:14px"><div class="sumbar">
      <div class="stat"><b class="${r.ok && !blocked.length ? 'ok' : 'bad'}">${r.ok ? (blocked.length ? 'Blocked' : 'Delivered') : 'Stopped'}</b><span>${esc(r.client.name)} · ${esc(r.request.asset_class_label)}</span></div>
      <div class="stat"><b>${uniq.length}</b><span>distinct skills took part</span></div>
      <div class="stat"><b>${r.trace.length}</b><span>skill runs and steps</span></div>
      <div class="stat"><b>${cnt(['exclude'])}</b><span>excluded by rules</span></div>
      <div class="stat"><b>${cnt(['removed', 'blocked'])}</b><span>stopped by policy</span></div>
      <div class="stat"><b>${cnt(['flag', 'warning', 'condition'])}</b><span>flags and warnings</span></div>
      <div class="stat"><b>${r.ms} ms</b><span>run time</span></div></div>
      <div class="row" style="margin-top:10px">${byType.map(([t, n]) => `<span class="tb ${t}">${n} ${TLABEL[t]}</span>`).join('')}${drafts.length ? `<span class="pill draft">uses draft: ${drafts.map((d) => esc(d.skill)).join(', ')}</span>` : ''}</div>
      ${r.ok ? '' : `<div class="callout bad" style="margin-top:10px">${esc(r.error)}</div>`}
      ${blocked.map((b) => `<div class="callout bad" style="margin-top:10px"><b>${esc(b.rule)}</b> (${esc(b.skill)}): ${esc(b.message)}</div>`).join('')}</div>`;
  const trace = r.trace.map((e) => {
    const pad = `style="padding-left:${e.depth * 20}px"`;
    if (e.kind === 'step') return `<div class="tr" ${pad}><div class="stepline">↳ ${esc(e.summary)}</div></div>`;
    return `<div class="tr" ${pad}><div class="h">${tb(e.type)}<a class="nm" href="#/registry/${esc(e.skill)}">${esc(e.skill)}</a><span class="muted small">v${esc(e.version)}</span>${e.status === 'draft' ? pill('draft') : ''}${e.chain.length > 1 ? `<span class="muted small">extends ${esc(e.chain[1])}</span>` : ''}${Object.keys(e.params || {}).length ? `<span class="muted small mono">${esc(JSON.stringify(e.params))}</span>` : ''}</div>
      <div class="sm">${esc(e.summary || e.error || '')}</div>${e.decisions.length ? `<ul class="dec">${e.decisions.map((d) => `<li class="${esc(d.outcome)}"><code>${esc(d.rule)}</code> ${esc(d.outcome)} · ${esc(d.message)}${d.from && d.from !== e.skill ? ` <code>from ${esc(d.from)}</code>` : ''}</li>`).join('')}</ul>` : ''}</div>`;
  }).join('');
  let out = '';
  if (Array.isArray(ctx.shortlist)) {
    out += `<h3>Shortlist</h3>${ctx.shortlist.length ? `<table class="t" style="margin-top:6px"><thead><tr><th>Candidate</th><th>Research</th><th class="num">Fit</th><th class="num">Fee</th><th class="num">A year</th></tr></thead><tbody>${ctx.shortlist.map((s) => `<tr><td><b>${esc(s.name)}</b><div class="muted small">${esc(s.vehicle)} · TE ${esc(s.te)}% · IR ${esc(s.ir)} · ${esc(s.track_years)} yrs</div>${(s.flags || []).map((f) => `<div class="flag">⚑ ${esc(f.message)}</div>`).join('')}</td><td>${esc(s.status)}</td><td class="num">${s.fit_score != null ? Math.round(s.fit_score) : '—'}</td><td class="num">${esc(s.fee_bps)} bp</td><td class="num">${s.annual_fee != null ? money(s.annual_fee) : '—'}</td></tr>`).join('')}</tbody></table>` : '<div class="callout warn">No candidate passed every screen and policy.</div>'}`;
    if (ctx.alternative) out += `<p class="small" style="margin:8px 0 0">Lower-cost alternative, always shown: <b>${esc(ctx.alternative.name)}</b>, ${esc(ctx.alternative.fee_bps)} bp (${money(ctx.alternative.annual_fee)} a year).</p>`;
  }
  for (const [k, label] of [['meeting_brief', 'Meeting brief'], ['position_summary', 'Position summary'], ['rationale', 'Rationale for the advisor']]) {
    if (typeof ctx[k] === 'string') out += `<h3 style="margin-top:16px">${label}</h3><div class="rationale" style="margin-top:6px">${esc(ctx[k])}</div>`;
  }
  if (ctx.concentration_findings && !ctx.shortlist && !ctx.position_summary) out += `<h3>Findings</h3>${ctx.concentration_findings.findings.map((f) => `<div class="tres"><span class="${f.outcome === 'block' ? 'bad' : 'warn'}">●</span><div><b>${esc(f.rule)}</b> ${esc(f.outcome)} · ${esc(f.message)}</div></div>`).join('') || '<p class="muted">No findings.</p>'}`;
  const scalar = Object.entries(ctx).filter(([k]) => !['shortlist', 'alternative', 'rationale', 'position_summary', 'meeting_brief', 'policy_checks', 'blocked', 'concentration_findings'].includes(k));
  if (!out && scalar.length) out += `<h3>Output</h3><pre class="code" style="margin-top:6px">${esc(JSON.stringify(Object.fromEntries(scalar), null, 1).slice(0, 4000))}</pre>`;
  const pc = ctx.policy_checks || [];
  if (pc.length) out += `<h3 style="margin-top:16px">Policy checks</h3>${pc.map((p) => `<div class="tres"><span class="${p.violations.length ? (p.violations.some((v) => v.severity === 'block') ? 'bad' : 'warn') : 'ok'}">${p.violations.length ? '!' : '✓'}</span><div><b>${esc(p.skill)}</b> <span class="muted small">${p.checked} checks</span>${p.violations.map((v) => `<div class="small">${esc(v.id)} · ${esc(v.message)}</div>`).join('')}</div></div>`).join('')}`;
  return head + `<div class="split2" style="margin-top:14px"><div class="card pad"><h2>How it was delivered</h2><p class="muted small" style="margin:4px 0 8px">Each skill in the order it ran. Indentation shows which skill called which.</p><div class="trace">${trace}</div></div><div class="card pad">${out || '<p class="muted">No output.</p>'}</div></div>`;
}

/* ---------- create ---------- */
const EXAMPLES = [
  ['Rules · child of a parent', 'Create a rules skill called esg-sma-screen that extends the SMA eligibility screen. Exclude any manager whose ESG score is below 50. Flag managers with tracking error above 4%. Owner: Sustainability Office.'],
  ['Policy · limits', 'A compliance policy: never shortlist a manager with fees above 55 bp, and always show the lower-cost index alternative. Owned by Compliance.'],
  ['Policy · wording', 'A policy for client letters: never use the words "guaranteed" or "beat the market". Always include "past performance".'],
  ['Technical · scoring', 'Technical skill to calculate a weighted score: information ratio 40% higher is better, fees 30% lower is better, ESG score 30%.'],
  ['Business · reuse a parent', 'A capability for growth SMAs that reuses the standard selection process with the SMA screen and the top 2 names.'],
  ['Business · compose skills', 'Business process called muni-ladder-selection: first load the approved list, then run the fund screen, then score candidates, then check client fit, then compare fees, then apply the approved list policy, then take the top 2, then write the selection rationale.'],
  ['Change an existing skill', 'Raise the SMA track record minimum to 5 years.'],
];
function viewCreate() {
  const C = S.create; const claude = S.meta.claude_available;
  const ask = `<div class="card pad"><h2>Describe the skill in plain English</h2><p class="muted small" style="margin:4px 0 10px">Say what it should do, what it builds on and who owns it. The generator reads one sentence at a time, maps your words to the data and to skills already in the registry, and shows how it read each sentence.</p>
    <textarea class="ask" data-ask placeholder="e.g. Create a rules skill that extends the SMA eligibility screen. Exclude any manager whose ESG score is below 50.">${esc(C.text)}</textarea>
    <div class="examples">${EXAMPLES.map(([k, t], i) => `<button data-ex="${i}" title="${esc(t)}"><b>${esc(k)}</b></button>`).join('')}</div>
    <div class="row" style="margin-top:12px;justify-content:space-between"><div class="mode" role="group" aria-label="Generator"><button data-mode="offline" class="${C.mode === 'offline' ? 'on' : ''}">Offline parser</button><button data-mode="claude" class="${C.mode === 'claude' ? 'on' : ''}" ${claude ? '' : 'disabled title="Set ANTHROPIC_API_KEY on the server to enable"'}>Claude</button></div>
    <button class="btn" data-generate ${C.busy ? 'disabled' : ''}>${C.busy ? 'Generating…' : 'Generate skill'}</button></div></div>`;
  if (!C.result) return `<h1>Create from English</h1><p class="lede">Write what you need; get a complete, tested SKILL.md back. Nothing is saved until you choose to.</p>${ask}`;
  const R = C.result;
  if (!R.ok) return `<h1>Create from English</h1><p class="lede">Write what you need; get a complete, tested SKILL.md back.</p>${ask}<div class="card pad" style="margin-top:14px"><div class="callout bad">${esc(R.error)}</div>${notesTable(R.notes || [])}${(R.warnings || []).map((w) => `<div class="callout warn" style="margin-top:8px">${esc(w)}</div>`).join('')}</div>`;
  const v = C.validation || R.validation;
  const layers = ['format', 'links', 'logic', 'contract', 'tests'].map((L) => {
    const errs = v.errors.filter((e) => e.layer === L); const warns = v.warnings.filter((e) => e.layer === L);
    const extra = L === 'tests' ? ` · ${v.tests.filter((t) => t.ok).length}/${v.tests.length} pass` : L === 'contract' && v.contract.length ? ` · ${v.contract.length} steps` : '';
    return `<div class="layer"><b>${L}</b><span class="st ${errs.length ? 'bad' : warns.length ? 'warn' : 'ok'}">${errs.length ? `✗ ${errs.length} error${errs.length > 1 ? 's' : ''}` : warns.length ? '! warnings' : '✓ ok'}</span><span class="muted">${extra}</span></div>`;
  }).join('');
  const msgs = [...v.errors.map((e) => `<div class="callout bad" style="margin-top:6px"><b>${esc(e.layer)}:</b> ${esc(e.message)}</div>`), ...v.warnings.map((e) => `<div class="callout warn" style="margin-top:6px"><b>${esc(e.layer)}:</b> ${esc(e.message)}</div>`), ...(R.warnings || []).map((w) => `<div class="callout warn" style="margin-top:6px">${esc(w)}</div>`)].join('');
  const isUpd = R.kind === 'update' || v.is_update;
  const impact = isUpd && v.impact && v.impact.length ? `<div class="callout info" style="margin-top:10px"><b>Impact if approved:</b> ${v.impact.length} skill${v.impact.length > 1 ? 's' : ''} rely on <b>${esc(v.skill.name)}</b>: ${v.impact.map((d) => esc(d.name)).join(', ')}. Their tests run against the new version once it is saved.</div>` : '';
  const saved = C.saved ? `<div class="callout ok" style="margin-top:10px">Saved <b>${esc(C.saved.name)}</b> v${esc(C.saved.version)} as ${esc(C.saved.status)}. <a href="#/registry/${esc(C.saved.name)}">Open in registry</a>${C.saved.abstract ? '' : ` · <a href="#/run/${esc(C.saved.name)}">Run it</a>`} · <a href="#/map" data-mapsel="${esc(C.saved.name)}">See it on the map</a></div>` : '';
  const left = `<div class="card pad stack"><div class="row" style="justify-content:space-between"><h2>${isUpd ? 'Change to' : 'New'} ${tb(v.skill ? v.skill.type : R.type)} <span class="mono" style="font-size:14px">${esc(v.skill ? v.skill.name : R.name)}</span></h2><span class="muted small">${R.mode === 'claude' ? 'drafted by Claude' : 'offline parser'}</span></div>
    <div><h3>How your request was read</h3>${notesTable(R.notes)}</div>
    <div><h3 style="margin-bottom:6px">Checks</h3><div class="layers">${layers}</div>${msgs}${impact}</div>
    ${v.contract && v.contract.length ? `<details><summary class="small">Data contract: what each step needs and gives</summary><table class="t small" style="margin-top:6px"><tbody>${v.contract.map((c) => `<tr><td>${c.step}</td><td class="mono">${esc(c.name)}</td><td class="mono">${esc((c.needs || []).join(', '))}</td><td class="mono">→ ${esc((c.gives || []).join(', '))}</td><td>${c.ok ? '<span class="ok">✓</span>' : '<span class="bad">✗</span>'}</td></tr>`).join('')}</tbody></table></details>` : ''}
    <div class="row"><button class="btn" data-save ${v.ok ? '' : 'disabled'}>${isUpd ? 'Save as new version (draft)' : 'Save as draft'}</button><button class="btn ghost" data-revalidate>Re-check my edits</button><button class="btn ghost" data-copytext>Copy SKILL.md</button></div>${saved}</div>`;
  const right = `<div class="card pad"><div class="row" style="justify-content:space-between"><h2>SKILL.md</h2><span class="muted small">Edit freely, then re-check</span></div><textarea class="editor" data-editor spellcheck="false" style="margin-top:8px" aria-label="SKILL.md editor">${esc(C.md)}</textarea></div>`;
  return `<h1>Create from English</h1><p class="lede">Write what you need; get a complete, tested SKILL.md back. Nothing is saved until you choose to.</p>${ask}<div class="split2" style="margin-top:14px">${left}${right}</div>`;
}
function notesTable(notes) {
  return `<table class="notes" style="margin-top:6px"><tbody>${notes.map((n) => `<tr><td class="${n.used ? 'ok' : 'warn'}">${n.used ? '✓' : '✗'}</td><td class="s">${esc(n.sentence)}</td><td>${esc(n.reading)}</td></tr>`).join('')}</tbody></table>`;
}

/* ---------- events ---------- */
document.addEventListener('click', async (ev) => {
  const t = ev.target.closest('button, a'); if (!t) return;
  const d = t.dataset;
  try {
    if (d.open) { location.hash = `#/registry/${d.open}`; return; }
    if (d.ftype) { S.ftype = d.ftype; paint(); return; }
    if (d.fstatus) { S.fstatus = d.fstatus; paint(); return; }
    if (d.sub) { S.sub = d.sub; paint(); return; }
    if (d.copy) { const raw = await api(`/api/skills/${d.copy}/raw`); await navigator.clipboard.writeText(raw).catch(() => {}); toast('SKILL.md copied'); return; }
    if (d.approve) { await api(`/api/skills/${d.approve}/approve`, { method: 'POST', body: {} }); await loadAll(); toast(`${d.approve} approved`); paint(); return; }
    if (d.mapclear !== undefined) { S.mapSel = null; paint(); return; }
    if (d.mapsel) { S.mapSel = d.mapsel; return; }
    if (d.run !== undefined) {
      const R = S.run; R.busy = true; paint();
      const cl = S.meta.clients.find((c) => c.id === R.client);
      try { R.result = await api('/api/run', { method: 'POST', body: { skill: R.skill, client: R.client, asset_class: R.asset_class || cl.request.asset_class, amount: R.amount ?? cl.request.amount } }); }
      finally { R.busy = false; } paint(); return;
    }
    if (d.ex) { S.create.text = EXAMPLES[+d.ex][1]; S.create.result = null; S.create.saved = null; paint(); return; }
    if (d.mode) { S.create.mode = d.mode; paint(); return; }
    if (d.generate !== undefined) {
      const C = S.create; C.text = $('[data-ask]').value; if (!C.text.trim()) { toast('Describe the skill first'); return; }
      C.busy = true; C.saved = null; paint();
      try { C.result = await api('/api/generate', { method: 'POST', body: { text: C.text, mode: C.mode } }); C.md = C.result.skill_md || ''; C.validation = C.result.validation || null; }
      finally { C.busy = false; } paint(); return;
    }
    if (d.revalidate !== undefined) { const C = S.create; C.md = $('[data-editor]').value; C.validation = await api('/api/validate', { method: 'POST', body: { text: C.md } }); C.saved = null; paint(); return; }
    if (d.copytext !== undefined) { await navigator.clipboard.writeText($('[data-editor]').value).catch(() => {}); toast('SKILL.md copied'); return; }
    if (d.save !== undefined) {
      const C = S.create; C.md = $('[data-editor]').value;
      const res = await api('/api/skills', { method: 'POST', body: { text: C.md } });
      C.saved = res.saved; C.validation = res.validation; await loadAll(); toast(`Saved ${res.saved.name} v${res.saved.version}`); paint(); return;
    }
    if (d.reset !== undefined) { await api('/api/reset', { method: 'POST' }); await loadAll(); S.create = { ...S.create, result: null, saved: null }; S.run.result = null; toast('Registry restored to the 19 seed skills'); paint(); return; }
    if (d.themeToggle !== undefined) {
      const cur = document.documentElement.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      document.documentElement.dataset.theme = cur === 'dark' ? 'light' : 'dark'; try { localStorage.setItem('ss-theme', document.documentElement.dataset.theme); } catch (e) { /* storage unavailable */ }
    }
  } catch (e) {
    const msg = e.data && e.data.detail && e.data.detail.validation ? `${e.message}: ${e.data.detail.validation.errors.map((x) => x.message).join('; ')}` : e.message;
    toast(msg); S.run.busy = false; S.create.busy = false;
  }
});
document.addEventListener('input', (ev) => {
  const t = ev.target;
  if (t.matches('[data-q]')) { S.q = t.value; clearTimeout(S._qt); S._qt = setTimeout(async () => { const pos = t.selectionStart; await paint(); const n = $('[data-q]'); if (n) { n.focus(); n.setSelectionRange(pos, pos); } }, 160); }
  if (t.matches('[data-ask]')) S.create.text = t.value;
  if (t.matches('[data-editor]')) S.create.md = t.value;
});
document.addEventListener('change', (ev) => {
  const t = ev.target; const k = t.dataset.rk; if (!k) return;
  const R = S.run;
  if (k === 'client') { R.client = t.value; R.asset_class = null; R.amount = null; R.result = null; paint(); return; }
  if (k === 'amount') R.amount = t.value === '' ? null : Number(t.value); else R[k] = t.value;
});
document.addEventListener('keydown', (ev) => { if (ev.target.matches('[data-ask]') && ev.key === 'Enter' && (ev.metaKey || ev.ctrlKey)) $('[data-generate]').click(); });
window.addEventListener('hashchange', route);
try { const th = localStorage.getItem('ss-theme'); if (th) document.documentElement.dataset.theme = th; } catch (e) { /* storage unavailable */ }
loadAll().then(route).catch((e) => { $('#view').innerHTML = `<div class="card pad"><div class="callout bad">Could not load the registry: ${esc(e.message)}</div></div>`; });
