/* ================= Atlas Advisor Workspaces: browser app =================
 * Every figure, finding and rule comes from the Python API (POST /api/view). This file only keeps what the advisor
 * did in this page (decisions, choices, drafts) and lays out the screens. Nothing is saved, sent, enrolled or traded.
 */
const $ = s => document.querySelector(s);
const esc = CH.esc;
function money(n, d){ if(n == null || isNaN(n)) return '—'; const s = n < 0 ? '−' : ''; n = Math.abs(n); return s + (n >= 1e6 ? '$' + (n / 1e6).toFixed(d ?? 2) + 'M' : n >= 1e4 ? '$' + Math.round(n / 1e3) + 'K' : '$' + Math.round(n).toLocaleString('en-US')); }
const pct = (x, d = 0) => x == null || isNaN(x) ? '—' : (x < 0 ? '−' : '') + Math.abs(x * 100).toFixed(d) + '%';
const spct = (x, d = 1) => (x >= 0 ? '+' : '−') + Math.abs(x * 100).toFixed(d) + '%';
const ppt = (x, d = 1) => (x >= 0 ? '+' : '−') + Math.abs(x * 100).toFixed(d) + ' pts';
let META = null, V = null;
const cls = k => (META.classes[k] || META.sectors[k] || k);
const short = k => cls(k).replace('U.S. ', 'US ').replace('International Developed Equity', 'International developed').replace('Emerging Markets Equity', 'Emerging markets').replace('U.S. Corporates (IG)', 'IG corporates');
const lc = t => t.toLowerCase().replace(/\bus\b/g, 'US').replace(/\big\b/g, 'IG');

/* ---------- what the advisor did, kept in this page only ---------- */
const S = {ws: 'queue', hid: 'henderson', hstep: 'assess', qv: 'hh', hf: 'all', mgmt: false, about: false, open: new Set(), popp: null,
  o1: {scope: 'brokerage', basis: 'tactical', lvl: 'L1', period: '3Y'}, o2: {}, o3: {}, th: 0.10, o4: {view: 'book', filter: 'all', ft: 'all', fb: 'all', q: '', sel: null, hh: null, all: false},
  ev: 'n1', pos: null, disp: {}, choice: {}, promo: {}, handed: {}, done: {}, intelRun: {}, watch: new Set(), story: {}};
let uid = 1;
const clips = hid => (S.story[hid] = S.story[hid] || []);
function addClip(ws, title, text, extra = {}){ const c = clips(S.hid), i = c.findIndex(x => x.key && x.key === extra.key), clip = {id: uid++, ws, title, text, ...extra}; if(i >= 0) c[i] = clip; else c.push(clip); if(S.o2[S.hid]) S.o2[S.hid].tp = null; toast(`Added to ${(V.side.hh.name || '').split(' ')[0]}'s talking points`); }
function toast(m){ const t = $('#toast'); t.textContent = m; t.classList.add('on'); clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove('on'), 1900); }

/* ---------- one request per paint ---------- */
let seq = 0;
function request(){
  return {route: {ws: S.ws, hid: S.hid, hstep: S.hstep, qv: S.qv, o1: S.o1, o2: S.o2, o3: S.o3, o4: S.o4, o4hh: S.o4.hh, ev: S.ev, pos: S.pos, popp: S.popp},
    state: {disp: S.disp, promo: S.promo, choice: S.choice, handed: S.handed, th: S.th, intel_run: S.intelRun, clips_list: S.story, watch: [...S.watch]}};
}
async function paint(o = {}){
  const my = ++seq; let r;
  try { r = await fetch('/api/view', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(request())}); }
  catch(err){ toast('The server is not reachable'); return; }
  if(!r.ok){ toast('Request failed: ' + r.status); return; }
  const v = await r.json(); if(my !== seq) return;
  V = v; const rt = v.route;
  if(rt.hid) S.hid = rt.hid; if(rt.pos) S.pos = rt.pos;
  const sd = v.stage.data;
  if(v.stage.ws === 'ws2' && sd) S.o2[sd.hh.id] = sd.o2;
  if(v.stage.ws === 'ws3' && sd && !sd.empty) S.o3[sd.pos] = sd.o3;
  if(v.stage.ws === 'ws4' && !v.stage.firm && sd) S.o4.hh = sd.sel;
  const sc = window.scrollY; render(); if(o.top) window.scrollTo({top: 0}); else window.scrollTo(0, sc);
  document.dispatchEvent(new Event('painted'));
}
function render(){ paintTop(); $('#journey').innerHTML = entries(); $('#stage').innerHTML = stage(); paintSide(); const ta = document.querySelector('textarea[data-tp2]'); if(ta){ ta.style.height = 'auto'; ta.style.height = ta.scrollHeight + 6 + 'px'; } }
function stage(){ const s = V.stage; return s.ws === 'queue' ? (S.qv === 'opp' ? WORKFLOW() : QUEUE()) : s.ws === 'path' ? PATH() : s.ws === 'ws1' ? WS1() : s.ws === 'ws2' ? WS2() : s.ws === 'ws3' ? WS3() : s.firm ? FIRM() : WS4(); }

/* ---------- shared pieces ---------- */
const ABOUT = {
  ws1: 'Compares each brokerage portfolio with the CIO strategic and tactical target for the client\'s risk profile, uses performance attribution to show which allocation and manager decisions drove under- or outperformance, sizes the gap in points and dollars, and shows what it costs in expected return and risk.',
  ws2: 'Equips the advisor to tell the client a clear, balanced story about whether the advisory program is the better structure for them, covering value, pricing for value and the fiduciary model, using only approved content.',
  ws3: 'Helps advisors reduce single-company risk at a pace set by the client\'s tax position. Accounts more than 50% in a single security are excluded from the addressable universe.',
  ws4: 'Aligns market news, CIO views and research to a client\'s portfolio: which holdings and allocations are affected, what the CIO and research say, and what it means for the client.',
  path: 'Turns each opportunity into a dollar figure, a set of options and a specific, advisor-approved path into the advisory program: trigger, size, value, options, transition plan and client story.',
  queue: 'A book-level opportunity scanner: approved screens across the advisor\'s households (allocation gap, embedded gains and loss harvesting, individual bonds, excess cash, high-cost funds, concentrated stock, news and research, trading economics). Each household\'s opportunities feed one advisory pathway, with the lower-cost alternative and staying in brokerage always shown.'};
const WSL = {queue: 'My book', ws1: 'Allocation and performance', ws2: 'Client story and proposal', ws3: 'Concentrated position', ws4: 'Market and research', path: 'Advisory pathway'};
const MT = {obs: 'observed', est: 'estimate', mod: 'modeled', val: 'needs validation'};
const mt = k => `<span class="mt mt-${k}">${MT[k]}</span>`;
const LIC = {ready: '✓', pending: '…', blocked: '✕'};
const CUEI = {meet: '◷', date: '◷', ask: '✉', basis: '!', amt: '$'};
const DOT = {review: 'look', ready: 'ok', specialist: 'nav', blocked: 'act', monitor: 'none', none: 'none', stay: 'none', defer: 'none', unsuitable: 'none', respond: 'look'};
const STATUS = k => META.status[k] || [k, 'neutral', k];
const pill = st => { const [l, t] = STATUS(st); return `<span class="pill ${t === 'info' ? 'neutral info' : t}">${esc(l)}</span>`; };
const heat = (v, bad, good) => { if(v == null || isNaN(v)) return 'var(--inset)'; const t = Math.max(0, Math.min(1, (v - bad) / (good - bad))); return t >= 0.5 ? `rgba(11,122,75,${(0.08 + 0.3 * (t - 0.5) * 2).toFixed(2)})` : `rgba(162,50,62,${(0.08 + 0.3 * (0.5 - t) * 2).toFixed(2)})`; };
function head(t, sub){ return `<div class="stage-h"><h1 class="serif">${esc(t)}</h1><p class="uc">${esc(sub)} <button class="link" data-about style="font-size:12px">About this workspace</button></p>${S.about ? `<p class="uc about">${esc(ABOUT[S.ws])}</p>` : ''}</div>`; }
function dx(id, title, sub, body){ return `<details class="dx" data-dx="${id}" ${S.open.has(id) ? 'open' : ''}><summary><span class="dx-t">${esc(title)}</span><span class="sub">${esc(sub || '')}</span></summary><div class="dx-b">${body}</div></details>`; }
function card(o){
  return `<div class="sum"><div class="sum-h"><span class="k">${esc(o.title)}</span><button class="link wf-link" data-wf>Workflow, readiness and owners in the Decision panel</button></div>
    ${o.controls ? `<div class="assum ctrls"><span class="k">Based on</span>${o.controls}${o.baseline === false ? '<span class="tw-warn" style="font-size:12px">Differs from the queue baseline (brokerage · CIO tactical · 3-year)</span>' : ''}</div>` : o.assumptions ? `<div class="assum"><span class="k">Based on</span> ${esc(o.assumptions)}</div>` : ''}
    <h2 class="serif finding">${esc(o.finding)}</h2>${o.why ? `<p class="why-t">${esc(o.why)}</p>` : ''}
    ${(o.gates || []).length ? `<div class="gates">${o.gates.map(([t, x]) => `<div class="gate ${t}"><b>${t === 'bad' ? 'Blocker' : 'Condition'}:</b> ${esc(x)}</div>`).join('')}</div>` : ''}
    <div class="ev3">${o.evidence.map((e, i) => `<div><span class="k">${i ? '' : 'Evidence'}</span>${esc(e || '—')}</div>`).join('')}</div>
    <div class="sum-grid">${(o.trade || []).length ? `<div><div class="k">Trade-offs</div><div class="rows">${o.trade.map(([l, v, t]) => `<div><span>${esc(l)}</span><span class="${t === 'warn' ? 'tw-warn' : t === 'good' ? 'up' : ''}">${esc(v)}</span></div>`).join('')}</div></div>` : ''}
      <div><div class="k">Choices <span class="sub" style="text-transform:none;letter-spacing:0;font-weight:400">pick one to record it and open what supports it</span></div><div class="chips" style="margin-top:6px">${o.choices.map(([n, tag]) => { const on = S.choice[o.key] === n, blk = tag === 'blocked';
        return `<button type="button" class="choice ${tag === 'recommended' ? 'rec' : blk ? 'blk' : ''}" data-choice="${esc(o.key)}|${esc(n)}" aria-pressed="${on}" ${blk ? `disabled title="${esc('Not available: ' + ((o.elig && o.elig.reason) || 'not eligible for the program'))}"` : `title="${esc(choiceAct(n, S.ws).hint)}"`}>${on ? '✓ ' : ''}${esc(n)}${tag ? `<em>${esc(tag)}</em>` : ''}</button>`; }).join('')}</div></div></div>
    <div class="next"><span class="k">Next step</span><div>${esc(o.next)}</div></div>${pathStrip(o.strip)}</div>`;
}
function pathStrip(sp){ if(!sp) return ''; const cut = t => t.length > 96 ? t.slice(0, 94).replace(/[ ,;:]+[^ ]*$/, '') + '…' : t;
  return `<div class="pstrip"><div class="pstrip-h"><span class="k">Advisory pathway</span><span class="sub">${esc(sp.kind)} · ${esc(sp.pathway)}</span><button class="link" data-popen="${esc(sp.key)}">Open the full pathway</button></div>
    <div class="steps6 sm">${sp.steps.map(x => `<div class="s6 ${x.n === 6 ? 'last' : ''}"><div class="s6h"><span>${x.n}</span>${esc(x.k)}</div><p>${esc(cut(x.v))}</p></div>`).join('')}</div></div>`; }
/* what picking a choice does: record it, set the matching assessment, and open what supports it */
function choiceAct(n, ws){
  const N = n.toLowerCase(), a = (disp, extra, hint) => ({disp, ...extra, hint});
  if(/^stay in brokerage/.test(N)) return a('stay', {}, 'Records "Stay in brokerage"; add a reason in the Decision panel to close it');
  if(/^monitor/.test(N)) return a('monitor', {}, 'Records "Monitor" and moves it to Monitor or deferred');
  if(/^specialist review/.test(N)) return a('specialist', {}, 'Records "Specialist review"');
  if(/^no action/.test(N)) return a(null, {close: 'No action needed after review'}, 'Closes the item: no action needed');
  if(/^review alternatives/.test(N)) return a('review', {open: 'w1-strat'}, 'Records "Review needed" and opens Strategies that fit');
  if(/^rebalance in brokerage/.test(N)) return a('review', {open: 'w1-drift'}, 'Records "Review needed" and opens the allocation bands');
  if(/^advisory/.test(N)) return ws === 'ws2' ? a('ready', {open: 'w2-svc'}, 'Records "Ready for client discussion" and opens the service comparison') : a('ready', {go: 'ws2'}, 'Records "Ready for client discussion" and opens the value story');
  if(/direct indexing and sma/.test(N)) return a('ready', {open: 'w2-svc'}, 'Records "Ready for client discussion" and opens the service comparison');
  if(/^index-only/.test(N)) return a('ready', {open: 'w2-fee'}, 'Records "Ready for client discussion" and opens the fee model');
  if(/review the concentrated position/.test(N)) return a('review', {go: 'ws3'}, 'Records "Review needed" and opens the position plan');
  if(/reassess the allocation/.test(N)) return a('review', {go: 'ws1'}, 'Records "Review needed" and opens the allocation review');
  if(/contact the client/.test(N)) return a('ready', {}, 'Records "Ready for client discussion"');
  if(/request a manager review/.test(N)) return a('review', {}, 'Records "Review needed" for the manager request');
  if(ws === 'ws3') return a('review', {open: 'w3-sol'}, 'Records "Review needed" and opens Solutions and actionability');
  return a(null, {}, 'Records the chosen path');
}

/* ---------- top bar ---------- */
function paintTop(){
  const hn = V.side.hh.name, crumbs = S.ws !== 'queue' && S.ws !== 'ws4' ? `<span class="sep">›</span><button class="crumb" data-phh="${S.hid}">${esc(hn)}</button><span class="sep">›</span><span class="crumb on">${esc(S.ws === 'path' ? (META.hsteps.find(x => x[0] === S.hstep) || META.hsteps[0])[1] : META.viewl[S.ws])}</span>` : '';
  $('#top').innerHTML = `<div class="brand"><div class="mark"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2 3 7l9 5 9-5-9-5Z"/><path d="M3 12l9 5 9-5"/><path d="M3 17l9 5 9-5"/></svg></div><div><b>Advisor workspaces</b><span>Atlas · prototype v6.2</span></div></div>
    <nav class="crumbs" aria-label="Where you are"><button class="crumb ${S.ws === 'queue' ? 'on' : ''}" data-go="queue"><span class="n">${V.top.open}</span>My book</button>${crumbs}</nav><button class="mr ${S.ws === 'ws4' ? 'on' : ''}" data-go="ws4">Market and research</button>
    <span class="grow"></span><span class="facts"><span>Illustrative data as of ${META.as_of.positions}</span></span><button class="tourbtn" data-tour="start" title="A guided tour of how the flow works">Tour</button><button class="proto" data-checks title="Decisions, drafts and approvals are kept in this page only; nothing is saved. Click to run the rule-engine checks.">Prototype · checks</button>`;
}

/* ---------- left list ---------- */
function entries(){
  const E = V.entries, e = (on, attrs, st, t, v) => `<button class="step" ${attrs} aria-current="${on}"><i class="dot ${DOT[st] || st || 'none'}"></i><span class="t">${esc(t)}</span><span class="v">${v}</span></button>`;
  if(E.kind === 'households') return `<div class="grp k">Households by actionability</div>` + E.rows.map(x => e(S.ws === 'path' && x.hid === S.hid, `data-phh="${x.hid}"`, x.ex ? 'nav' : x.life !== 'open' ? 'none' : 'look', x.name, x.ex ? 'Not eligible now' : `${money(x.now)} now · ${esc(META.pshort[x.path] || '')}`)).join('');
  if(E.kind === 'groups') return `<div class="grp k">Group</div>${[['all', 'All open', 'none'], ['action', 'Needs action', 'review'], ['specialist', 'Specialist or not eligible', 'specialist'], ['monitor', 'Monitor or deferred', 'monitor'], ['done', 'Closed', 'none']].map(([k, l, st]) => e((S.qf || 'all') === k, `data-qf="${k}"`, st, l, `${E.counts[k]}`)).join('')}
      <div class="grp k">Source</div><div class="chips" style="padding:4px 14px 10px">${[['all', 'All'], ['ws1', 'Allocation'], ['ws3', 'Concentration'], ['ws4', 'Events'], ['ws2', 'Value']].map(([k, l]) => `<button class="chip" data-qws="${k}" aria-pressed="${(S.qws || 'all') === k}">${l}</button>`).join('')}</div>`;
  if(E.kind === 'hhlist') return `<div class="grp k">Households</div>` + E.rows.map(r => e(r.hid === S.hid, `data-hh="${r.hid}"`, (S.disp[(S.ws === 'ws1' ? 'ws1:' : 'ws2:') + r.hid] || {}).status || r.status, r.name, esc(STATUS(r.status)[0]) + ' · ' + esc(r.ev))).join('');
  if(E.kind === 'positions') return `<div class="grp k">Positions above ${pct(E.th)}</div>` + (E.rows.length ? E.rows.map(p => e(p.key === S.pos, `data-pos="${p.key}"`, p.excl ? 'specialist' : p.insider ? 'review' : 'ready', `${p.sym} · ${p.hname}`, `${pct(p.share, 1)} of the account${p.excl ? ' · above program limit' : p.insider ? ' · insider' : ''}`)).join('') : '<p class="lh">None above this threshold.</p>');
  if(E.kind === 'firm') return `<div class="grp k">Type</div><div class="chips" style="padding:4px 14px 8px">${[['all', 'All'], ['market', 'Market'], ['cio', 'CIO'], ['research', 'Research']].map(([k, l]) => `<button class="chip" data-ift="${k}" aria-pressed="${S.o4.ft === k}">${l} <span class="sub">${E.types[k]}</span></button>`).join('')}</div>
      <div class="grp k">Book impact</div>${[['all', 'All', 'none'], ['match', 'Affects my book', 'review'], ['none', 'No identified impact', 'none'], ['pending', 'Not yet evaluated', 'none'], ['unknown', 'Insufficient data', 'none'], ['na', 'Superseded', 'none'], ['watch', 'Watchlist', 'none']].map(([k, l, st]) => e(S.o4.fb === k, `data-ifb="${k}"`, st, l, `${E.book[k]}`)).join('')}
      <p class="lh sub" style="padding:8px 14px;margin:0">"No identified impact" is limited by holdings coverage, fund look-through and the matching rules on file; it does not mean no possible relevance.</p>`;
  return `<div class="grp k">Events</div><div class="chips" style="padding:4px 14px 8px">${[['all', 'All sample events'], ['market', 'Market'], ['cio', 'CIO'], ['research', 'Research'], ['client', 'Client']].map(([k, l]) => `<button class="chip" data-evf="${k}" aria-pressed="${S.o4.filter === k}">${l}</button>`).join('')}</div><p class="lh sub" style="padding:0 14px 6px;margin:0">A curated sample of ${E.n} events, matched to your households. For everything published, use Firm intelligence.</p>` +
    E.rows.map(n => e(n.id === S.ev, `data-ev="${n.id}"`, n.material ? 'review' : 'none', n.headline, `${n.date} · <span class="src src-${n.type}">${esc(n.source)}</span> · ${n.material ? n.material + ' material' : 'monitor only'}`)).join('');
}

/* ---------- landing: brokerage opportunities in your book ---------- */
function QUEUE(){
  const L = V.stage.landing, H0 = L.rows, H = H0.filter(x => S.hf === 'all' || x.filt === S.hf), F = [['all', 'All'], ['discuss', 'Needs discussion'], ['waiting', 'Waiting on specialist or operations'], ['propose', 'Ready to propose'], ['done', 'Outcome recorded']];
  const toggle = `<p class="tourhint">New to this tool? <button class="link" data-tour="start">Take the guided tour</button> (about 2 minutes).</p><div class="qbar"><div class="seg qview">${[['hh', 'Households'], ['opp', 'All opportunities (workflow)']].map(([k, l]) => `<button data-qv="${k}" aria-pressed="${S.qv === k}">${l}</button>`).join('')}</div><button class="link" data-mgmt>${S.mgmt ? 'Hide' : 'Show'} management view (internal)</button></div>
    <div class="chips hfilt">${F.map(([k, l]) => `<button class="chip" data-hf="${k}" aria-pressed="${S.hf === k}">${l} <span class="sub">${k === 'all' ? H0.length : H0.filter(x => x.filt === k).length}</span></button>`).join('')}</div>`;
  const row = x => { const out = x.life.state !== 'open';
    return `<tr class="hrow ${x.ex ? 'ex' : ''}"><td><div class="hn1"><b>${esc(x.name)}</b></div>
        <div class="cues">${x.cues.map(([k, l]) => `<span class="cue cue-${k}"><i>${CUEI[k]}</i>${esc(l)}</span>`).join('')}</div>
        <div class="why1"><span class="k2i">Why now</span> ${esc(x.why)}</div>
        ${x.others.length ? `<details class="others"><summary>${x.others.length} other signal${x.others.length === 1 ? '' : 's'}</summary><ul>${x.others.map(o => `<li><span class="uct">${esc(o.kind)}</span> ${esc(o.why)} <button class="link" data-open="${esc(o.key)}">detail</button></li>`).join('')}</ul></details>` : ''}</td>
      <td>${x.ex ? '<b>—</b><div class="sub">Not eligible now</div>' : `<b class="amt">${money(x.now)}</b> ${mt('obs')}<div class="sub">${x.held ? `held back ${money(x.held)}` : 'nothing held back'}</div>`}</td>
      <td>${x.path ? `<b>${esc(META.pshort[x.path])}</b><div class="sub">starting point for review</div>` : '—'}</td>
      <td>${esc(x.blk.t)}<div><span class="own">${esc(x.blk.owner)}</span></div></td>
      <td>${out ? `<span class="pill neutral">${esc(x.life.label)}</span><div class="sub">${esc(x.life.note || '')}</div>` : `<button class="btn sm" data-hstep="${x.next[1]}" data-hid="${x.hid}">${esc(x.next[0])}</button><div class="sub">${esc(x.meeting.type)} in ${x.meeting.inDays} day${x.meeting.inDays === 1 ? '' : 's'}</div>`}</td></tr>`; };
  return head('Brokerage opportunities in your book', 'Which household, why now, how much could move, by which route, and what to do next.') + toggle + (S.mgmt ? bookView(L) : '') +
    `<div class="sec"><div class="tw"><table class="tbl hq"><colgroup><col style="width:37%"><col style="width:15%"><col style="width:16%"><col style="width:16%"><col style="width:16%"></colgroup>
      <thead><tr><th>Household · why now</th><th>Potentially movable now</th><th>Starting route</th><th>Constraint · owner</th><th>Next</th></tr></thead><tbody>${H.map(row).join('') || '<tr><td colspan="5" class="sub">No households in this filter.</td></tr>'}</tbody></table></div>
      <p class="disc"><b>Order:</b> households with a meeting, call date or client request coming up first, then by the amount potentially movable now; accounts above the 50% limit last. A rank is a prompt for review, not a suitability conclusion. Amounts are observed holdings; the canonical investable cash excludes the CIO cash target, the liquidity reserve and next year's needs.</p></div>`;
}
function bookView(L){
  const B = L.book, segs = [['low', 'Low'], ['medium', 'Medium'], ['hard', 'Hard']], mx = Math.max(1, ...segs.map(([k]) => B.seg[k]));
  return `<div class="sec"><div class="panel book"><div class="sec-h"><span class="k">Book view <span class="proto-tag">internal · not client-facing</span></span><span class="sub">${L.nhh} households · positions as of ${L.as_of}</span></div>
    <div class="bk-grid"><div><div class="k2">Addressable brokerage assets</div><div class="big">${money(B.scope)}</div><div class="sub">of ${money(B.brk)} in brokerage; ${money(B.excl)} excluded (above the 50% limit, or not transferable)</div></div>
      <div><div class="k2">By tax difficulty</div>${segs.map(([k, l]) => `<div class="segbar"><span>${l}</span><i style="width:${Math.round(B.seg[k] / mx * 100)}%"></i><b>${money(B.seg[k])}</b></div>`).join('')}<div class="sub">${esc(L.segnote)}</div></div>
      <div><div class="k2">Firm value on the addressable assets</div><div class="big">~${Math.round(B.bpsNow)} bp → ~${Math.round(B.bpsAdv)} bp</div><div class="sub">${money(B.revNow)} a year today (commissions at current trading) → ${money(B.revAdv)} in the advisory program. The lower-cost alternative is shown alongside every proposal.</div></div></div></div></div>`;
}
function WORKFLOW(){
  const all = V.stage.workflow.rows, open = all.filter(o => o.grp !== 'done'), src = o => (S.qws || 'all') === 'all' || o.ws === S.qws, qf = S.qf || 'all';
  const toggle = `<div class="seg qview">${[['hh', 'By household: the advisory pathway'], ['opp', 'By opportunity: workflow']].map(([k, l]) => `<button data-qv="${k}" aria-pressed="${S.qv === k}">${l}</button>`).join('')}</div>`;
  const G = [['action', 'Needs action'], ['specialist', 'Specialist or not eligible'], ['monitor', 'Monitor or deferred'], ['done', 'Closed']].filter(([k]) => qf === 'all' ? k !== 'done' : qf === k);
  const row = o => { const st = o.disp ? o.disp.status : o.status, L = o.life, n = o.ws === 'ws4' ? 1 : 0;
    return `<tr class="click ${o.disp ? 'done' : ''}" data-open="${esc(o.key)}" tabindex="0"><td><b>${esc(o.hname)}</b> · ${esc(o.type)}<div class="sub"><span class="uct">${esc(o.kind)}</span> ${o.flow && o.flow !== 'na' ? `<span class="flow">${esc(META.flow[o.flow])}</span>` : ''}</div><div class="sub pw">→ ${esc(o.pathway || '')}</div>${o.rel.length > n ? `<details class="reld"><summary>${o.rel.length - n} related</summary>${o.rel.slice(n).map(x => `<span class="rel">${esc(x)}</span>`).join('')}</details>` : ''}${o.ws === 'ws4' && o.rel[0] ? `<span class="rel">${esc(o.rel[0])}</span>` : ''}</td>
    <td>${esc(o.impact)}</td><td>${esc(o.next)}<div><span class="act-pill ${o.act[1]} xs">${esc(o.act[0])}</span></div></td><td><span class="pill ${L.state === 'closed' ? 'neutral' : STATUS(st)[1] === 'info' ? 'neutral info' : STATUS(st)[1]}">${esc(STATUS(st)[2])}</span><div class="sub wf ${L.need ? 'need' : ''}">${o.disp && o.disp.set ? 'Advisor · ' : 'Suggested · '}${esc(L.label)}${L.note && L.state !== 'open' ? ': ' + esc(L.note) : L.need ? ' · ' + esc(L.note) : ''}</div></td></tr>`; };
  return head('My book', 'Households ranked by advisory potential: each household\'s opportunities feed one advisory pathway.') + toggle +
  `<p class="lede"><b>${open.filter(o => o.grp === 'action').length}</b> need action, <b>${open.filter(o => o.grp === 'specialist').length}</b> go to a specialist or are not eligible, <b>${open.filter(o => o.grp === 'monitor').length}</b> to monitor, across <b>${new Set(open.map(o => o.hid)).size}</b> households.</p>
  <div class="sec"><div class="tw"><table class="tbl q"><thead><tr><th>Client · opportunity · advisory pathway</th><th>Material impact</th><th>Next action</th><th>Status</th></tr></thead>
    ${G.map(([k, l]) => { const rows = all.filter(o => o.grp === k && src(o)); return `<tbody><tr class="qgrp"><td colspan="4">${esc(l)} <span class="sub">${rows.length}</span></td></tr>${rows.map(row).join('') || '<tr><td colspan="4" class="sub">Nothing here.</td></tr>'}</tbody>`; }).join('')}</table></div>
    <p class="disc">Uses the baseline settings (brokerage accounts, CIO tactical target, 3-year performance). Ranking weighs status, materiality and concentration; related events sit under the position they concern. An advisor assessment does not remove open work: a row leaves the active groups only when it is closed with an outcome, closed as stay or not suitable with a reason, deferred with a reason, or set to monitor. <b>Prototype:</b> assessments and closures are kept in this page only.</p></div>`;
}

/* ---------- household flow ---------- */
function hstepper(hh, H, handed){
  const at = S.ws === 'ws2' ? 'proposal' : S.hstep, reach = {assess: 0, specialist: 0, outcome: 0, paths: 1, proposal: 2, handoff: 3}[H.step];
  return `<div class="hstep" role="navigation" aria-label="Household steps">${META.hsteps.map(([k, l], i) => { const done = i < reach || (k === 'handoff' && handed);
    return `<button class="hs ${at === k ? 'on' : ''} ${done ? 'done' : ''}" data-hstep="${k}" data-hid="${hh.id}"><span class="hn">${done ? '✓' : i + 1}</span>${l}</button>`; }).join('<span class="hsep"></span>')}</div>`;
}
function PATH(){
  const s = V.stage, d = s.data, hh = d.hh, step = s.step;
  return head(hh.name, `${hh.profile} · ${money(hh.brokerage)} brokerage · ${hh.meeting.type.toLowerCase()} in ${hh.meeting.inDays} day${hh.meeting.inDays === 1 ? '' : 's'}`) + hstepper(hh, s.hstate, d.handed) + (step === 'paths' ? PATHS(d) : step === 'handoff' ? HANDOFF(d) : ASSESS(d));
}
function waterfall(K){
  const segs = [['move', K.move, 'var(--brand)'], ['gated', K.gated, 'var(--warn)'], ['kept', K.kept, 'var(--c-other)'], ['excluded', K.excluded, 'var(--bad)']].filter(x => x[1] > 0), tot = K.total || 1;
  return `<div class="wf"><div class="wfbar">${segs.map(([k, v, c]) => `<i style="width:${(v / tot * 100).toFixed(2)}%;background:${c}" title="${esc(K.labels[k] + ': ' + money(v))}"></i>`).join('')}</div>
    <div class="wfleg">${segs.map(([k, v, c]) => `<span><i style="background:${c}"></i>${esc(K.labels[k])} <b>${money(v)}</b></span>`).join('')}<span class="sub">= ${money(K.total)} identified ${Math.abs(K.move + K.gated + K.kept + K.excluded - K.total) < 1 ? '✓' : '≠'}</span></div></div>`;
}
const RL = {inkind: 'Move in kind', swap: 'Replace high-cost class', transfer: 'Tax-efficient transition (sell within the gain budget)', harvest: 'Sell and harvest the loss', instep: 'Invest in steps', basis: 'Hold until basis is found', stay: 'Stays outside the program', reserve: 'Kept as liquidity reserve'};
function planTable(p){
  return dx('a-plan', 'Transition plan by holding', `≈${Math.round(p.pct * 100)}% aligned in year one on the phased path · tax ≈ ${money(p.taxNet)} (planning)`, `<div class="tw"><table class="tbl"><thead><tr><th>Holding</th><th>Route</th><th class="r">Value</th><th class="r">Gain or loss</th><th>Why</th></tr></thead><tbody>${p.rows.map(x => `<tr><td><span class="ticker">${esc(x.sym)}</span></td><td>${esc(RL[x.route])}</td><td class="r">${money(x.mv)}</td><td class="r ${x.gain < 0 ? 'down' : ''}">${x.route === 'basis' ? 'basis missing' : money(x.gain)}</td><td class="sub">${esc(x.why)}</td></tr>`).join('')}</tbody></table></div><p class="disc">Planning estimates on today's prices; not a validated trade plan or an instruction.</p>`);
}
function ASSESS(d){
  const hh = d.hh, A = d.A, e = d.elig, H = d.H, prim = d.prim, decided = H.d && H.d.set, needR = H.L.need;
  const dec = [['ready', 'Pursue: compare routes'], ['stay', 'Remain in brokerage'], ['monitor', 'Monitor'], ['specialist', 'Refer to specialist']].filter(([k]) => !(e.state === 'ineligible' && k === 'ready'));
  const heldTxt = A.held.length ? A.held.map(x => `${money(x.amt)} ${x.sym === 'CASH' || x.sym === 'MMF' ? '' : x.sym + ' '}${x.why}`).join(' · ') : 'nothing held back';
  const sel = d.ops.find(x => x.key === S.popp) || d.ops.find(x => prim && x.key === prim.key) || d.ops[0];
  return `<div class="sec"><div class="sum assess"><div class="sum-h"><span class="k">Client case</span><span>${e.state === 'ineligible' ? '<span class="pill bad">Not eligible for the program</span>' : `<span class="act-pill ${d.eligLabel[1]}">${esc(d.eligLabel[0])}</span>`}</span></div>
      <div class="k" style="margin-top:6px">Why now</div><h2 class="serif finding">${esc(prim ? prim.why : 'Nothing material found')}${d.cat.length ? `; ${esc(d.cat.join('; '))}` : ''}.</h2>
      <div class="lead-amt"><div><div class="l">Potentially movable to advisory now ${mt('obs')}</div><div class="v">${A.ex ? '—' : money(A.now)}</div><div class="sub">${A.ex ? esc(e.reason) : `Held back: ${esc(heldTxt)}`}</div></div>
        <div class="lead-blk"><div class="l">What stands in the way</div><div>${esc(d.blk.t)} <span class="own">${esc(d.blk.owner)}</span></div>${A.reserveMissing ? '<div class="need-t">Liquidity reserve not on file: confirm before sizing cash.</div>' : ''}${A.needsLater ? `<div class="sub">${money(A.needsLater)} of cash needs after 2027 are not reserved; review with the client.</div>` : ''}</div></div>
      ${A.ex ? '' : `<div class="tri">${[['Moves into the account at enrollment', money(A.now), 'in kind; no trade implied', 'obs'], ['Repositioned over time', money(A.repositionOverTime), 'on the phased route, within the gain budget', 'mod'], ['Estimated target alignment, year one', `≈${Math.round(A.alignY1 * 100)}%`, 'phased route; rebalancing now reaches ≈100%', 'mod']].map(([l, v, sb, k]) => `<div><div class="l">${l} ${mt(k)}</div><div class="v2">${v}</div><div class="sub">${sb}</div></div>`).join('')}</div>`}
      <div class="k" style="margin-top:12px">Client value and cost, by measure</div><div class="rows vr">${d.valueRows.map(([l, k, v, t]) => `<div><span>${esc(l)} ${mt(k)}</span><span class="${t === 'warn' ? 'tw-warn' : ''}">${esc(v)}</span></div>`).join('')}</div>
      <div class="k" style="margin-top:12px">Your decision <span class="proto-tag">prototype: kept in this page only</span></div>
      <div class="chips" style="margin-top:6px">${dec.map(([k, l]) => `<button class="choice ${k === 'ready' ? 'rec' : ''}" data-hdec="${k}" data-hid="${hh.id}" aria-pressed="${!!(H.d && H.d.status === k)}">${H.d && H.d.status === k ? '✓ ' : ''}${esc(l)}</button>`).join('')}</div>
      ${needR ? `<div class="disp" style="margin-top:6px"><select data-hreason="${hh.id}" class="need" aria-label="Reason"><option value="">Reason (needed to close)…</option>${META.reasons.map(r => `<option>${esc(r)}</option>`).join('')}</select></div><p class="need-t">A reason is needed before this is recorded as closed; until then it stays open.</p>` : ''}
      ${decided && H.L.state !== 'open' ? `<p class="sub" style="margin:6px 0 0">Recorded: ${esc(H.L.label)}${H.L.note ? ' · ' + esc(H.L.note) : ''}. Follow-up work elsewhere stays open until it is closed separately.</p>` : ''}
    </div></div>
    ${d.others.length ? `<div class="sec"><div class="panel"><div class="sec-h"><span class="k">Other signals for this household</span><span class="sub">they feed the same transition</span></div><ul class="sig">${d.others.map(o => `<li><span class="uct">${esc(o.kind)}</span> ${esc(o.why)} <button class="link" data-open="${esc(o.key)}">Open the analysis</button></li>`).join('')}</ul></div></div>` : ''}
    <div class="sec">${dx('a-rec', 'How the amounts reconcile', 'every holding in exactly one bucket', `${waterfall(d.buckets)}<div class="tw" style="margin-top:8px"><table class="tbl"><thead><tr><th>Holding</th><th>Bucket</th><th class="r">Value</th><th>Route</th><th>Timing note</th></tr></thead><tbody>${d.buckets.rows.map(r => `<tr><td><span class="ticker">${esc(r.sym)}</span></td><td>${esc(r.label)}</td><td class="r">${money(r.mv)}</td><td class="sub">${esc(META.routes[r.route] ? META.routes[r.route][0] : r.route)}</td><td class="sub">${esc(r.overlay || '')}</td></tr>`).join('')}</tbody></table></div><p class="disc">Timing notes (bond calls, maturities) describe when proceeds could be reinvested; they are not added to any total.</p>`)}
      ${sel ? dx('a-six', 'How it was found: trigger to client story', 'the six-step worked example', `<div class="chips" style="margin-bottom:6px">${d.ops.map(x => `<button class="chip" data-popp="${esc(x.key)}" aria-pressed="${x.key === sel.key}">${esc(x.kind)}</button>`).join('')}</div><div class="steps6">${sel.steps.map(x => `<div class="s6 ${x.n === 6 ? 'last' : ''}"><div class="s6h"><span>${x.n}</span>${esc(x.k)}</div><p>${esc(x.v)}</p></div>`).join('')}</div>`) : ''}
      ${planTable(d.plan)}
      ${dx('a-ev', 'Evidence and sources', 'data dates and lineage', `<ul class="pre"><li>Positions as of ${d.evidence.positions} (observed)</li><li>Returns as of ${d.evidence.returns}</li><li>CIO views updated ${d.evidence.cio}</li><li>Research as of ${d.evidence.research}</li><li>Look-through as of ${d.evidence.look_through}</li><li>Screen thresholds: ${esc(d.evidence.note)}</li><li>All data illustrative</li></ul><p class="sub">Meeting note: ${esc(hh.meeting.note)}</p>`)}</div>`;
}
function PATHS(d){
  const hh = d.hh, H = d.H, R = d.remain;
  const card2 = p => { const on = H.path === p.id;
    return `<div class="pcard2 ${on ? 'on' : ''}">${p.suggested ? '<div class="sp">Starting point for advisor review</div>' : ''}<div class="pc-h"><b>${esc(p.name)}</b></div>
      <p class="pwhy"><b>Why this route:</b> ${esc(p.why || p.rationale)}</p><ul class="tdo">${(p.trade || []).map(t => `<li>${esc(t)}</li>`).join('')}</ul>
      <div class="rows">${[['Account', p.account || p.amount, 'obs'], ['Trading', p.trading || p.timing, 'mod'], ['Tax', p.tax, d.noBasis ? 'val' : 'est'], ['Cost', p.cost, 'est'], ['Approves', p.approver, '']].map(([l, x, k]) => `<div><span>${l}${k ? ' ' + mt(k) : ''}</span><span>${esc(x)}</span></div>`).join('')}</div>
      <div class="k" style="margin-top:8px">Still to check before it is actionable</div><ul class="feas">${p.feas.map(f => `<li class="${f.ok ? 'ok' : ''}"><span>${f.ok ? '✓' : '…'}</span><span>${esc(f.t)} <span class="own">${esc(f.owner)}</span></span></li>`).join('')}</ul>
      <button class="btn sm" data-hpath="${p.id}" data-hid="${hh.id}" style="margin-top:auto" aria-pressed="${on}">${on ? '✓ Working choice' : 'Make this the working choice'}</button></div>`; };
  const stayCard = `<div class="pcard2 stay ${H.d && ['stay', 'monitor'].includes(H.d.status) ? 'on' : ''}"><div class="pc-h"><b>Stay in brokerage</b></div><p class="pwhy"><b>Why this route:</b> the client keeps today's structure and cost.</p>
      <ul class="tdo"><li>No program fee: about ${money(R.cost)} a year today</li><li>No ongoing advice, rebalancing or tax management</li></ul>
      <div class="rows"><div><span>Account ${mt('obs')}</span><span>Nothing moves</span></div><div><span>Tax</span><span>None triggered</span></div><div><span>Alternative</span><span>Lower-cost ${esc(R.lc.name)}: ${money(R.lc.total)} (${Math.round(R.lc.bps)} bp)</span></div></div>
      ${d.stayR.length ? `<div class="k" style="margin-top:8px">Reasons the client might stay</div><ul class="tdo">${d.stayR.slice(0, 3).map(x => `<li>${esc(x)}</li>`).join('')}</ul>` : ''}
      <div class="chips" style="margin-top:auto">${[['stay', 'Remain in brokerage'], ['monitor', 'Monitor'], ['specialist', 'Refer to specialist']].map(([k, l]) => `<button class="choice" data-hdec="${k}" data-hid="${hh.id}" aria-pressed="${!!(H.d && H.d.status === k)}">${esc(l)}</button>`).join('')}</div></div>`;
  return `<div class="sec"><p class="sub" style="margin:0 0 8px">Account movement and portfolio trading are shown separately. Choosing a route records a <b>working choice</b> for the proposal; it is not a suitability approval.</p><div class="pcards2 n${d.paths.length + 1}">${d.paths.map(card2).join('')}${stayCard}</div></div>
    <div class="sec">${dx('p-all', 'Show all alternatives', `${d.options.length} strategies from the approved universe, plus the lower-cost alternative`, `<div class="tw"><table class="tbl"><thead><tr><th>Strategy</th><th>Kind</th><th>Why it fits</th><th class="r">Minimum</th></tr></thead><tbody>${d.options.map(x => `<tr><td><b>${esc(x.name)}</b></td><td>${esc(x.kind)}</td><td class="sub">${esc(x.why.join('; '))}</td><td class="r">${money(x.min)}</td></tr>`).join('')}<tr><td><b>${esc(R.lc.name)}</b> <span class="pill neutral">lower-cost alternative</span></td><td>Program</td><td class="sub">${esc(R.lc.note || '')}</td><td class="r">—</td></tr></tbody></table></div>`)}
      ${planTable(d.plan)}</div>
    <div class="sec pf-bar"><button class="btn" data-hstep="proposal" data-hid="${hh.id}" ${H.path ? '' : 'disabled title="Make a route the working choice first"'}>Next: prepare the client proposal</button></div>`;
}
function HANDOFF(d){
  const hh = d.hh, done = S.done[hh.id] = S.done[hh.id] || {}, all = d.items.every(i => i.auto || done[i.id]), handed = d.handed, ex = d.ex;
  return `<div class="sec"><div class="panel"><div class="sec-h"><span class="k">Before anything moves</span><span class="sub">people complete each item; the tool never enrolls or trades</span></div>
      <ul class="feas big">${d.items.map(i => { const ok = i.auto || done[i.id]; return `<li class="${ok ? 'ok' : ''}"><label><input type="checkbox" ${ok ? 'checked' : ''} ${i.auto ? 'disabled' : ''} data-hdone="${i.id}" data-hid="${hh.id}"> ${esc(i.t)}</label> <span class="own">${esc(i.owner)}</span>${i.auto ? '<span class="sub"> · from the workflow</span>' : ''}</li>`; }).join('')}</ul>
      ${ex ? '<p class="need-t">Not eligible for the program: the handoff applies only to a specialist plan.</p>' : ''}
      <div class="pf-bar" style="margin-top:8px"><button class="btn primary" data-handoff="${hh.id}" ${all && !handed && !ex ? '' : 'disabled'}>${handed ? '✓ Handed off to operations' : 'Hand off to operations'}</button><span class="sub">${handed ? 'Operations enroll and move the assets; nothing is executed by this tool (prototype: kept in this page only).' : all ? 'Ready to hand off for operations to enroll.' : 'Complete every item first. Prepared for review is not approved.'}</span></div></div></div>
    <div class="sec"><div class="panel"><div class="sec-h"><span class="k">Handoff package</span><span class="sub">${d.path ? 'path: ' + esc(META.pshort[d.path] || d.path) : 'no path chosen yet'}</span></div>
      <div class="rows"><div><span>Enroll now</span><span>${money(d.now)}</span></div><div><span>Later, when gated</span><span>${d.later.map(x => `${money(x.amt)}: ${x.gate}`).join('; ') || 'none'}</span></div><div><span>Kept in brokerage</span><span>${money(d.kept)}</span></div></div>
      ${d.steps.length ? `<div class="k" style="margin-top:10px">Invest in steps</div><div class="tw"><table class="tbl"><tbody><tr>${d.steps.map(s => `<td><div class="sub">${s.m}</div><b>${money(s.amt)}</b></td>`).join('')}</tr></tbody></table></div>` : ''}</div></div>
    <div class="sec">${planTable(d.plan)}</div>`;
}

/* ---------- allocation and performance ---------- */
function WS1(){
  const d = V.stage.data, o = S.o1, g = d.gap, a = d.attr, b = d.hh.band, tol = d.tol, c = d.card;
  const fmt = v => pct(v, 0), rows = o.lvl === 'L1' ? g.groups.map(r => ({label: r.label, a: r.w, t: r.t, lo: r.t - tol.group, hi: r.t + tol.group, out: r.out, val: `${ppt(r.g, 0)} · ${money(r.usd, 1)}`}))
    : g.rows.map(r => ({label: short(r.k), a: r.w, t: r.t, lo: r.t - tol.class, hi: r.t + tol.class, out: r.out, val: `${ppt(r.g, 0)} · ${money(r.usd, 1)}`}));
  const outRows = (o.lvl === 'L1' ? g.groups : g.rows).filter(r => r.out), lo = Math.min(b.low, g.st.vol, g.stT.vol) - 0.02, hi = Math.max(b.high, g.st.vol, g.stT.vol) + 0.02;
  const rsum = {}; for(const r of d.routing) rsum[r.route] = (rsum[r.route] || 0) + r.mv; const instep = rsum.instep || 0, months = ['Nov 2026', 'Dec 2026', 'Jan 2027', 'Feb 2027', 'Mar 2027', 'Apr 2027'];
  const ex = c.elig.state === 'ineligible', R = d.routes;
  return head('Allocation and performance', 'Brokerage portfolio against the CIO target: what needs attention, why, and the choices.') +
  `<div class="sec">${card({...c, strip: d.strip, controls: `<div class="seg sm">${[['brokerage', 'Brokerage accounts'], ['all', 'Whole household']].map(([k, l]) => `<button data-o1="scope=${k}" aria-pressed="${o.scope === k}">${l}</button>`).join('')}</div><div class="seg sm">${[['strategic', 'CIO strategic'], ['tactical', 'CIO tactical']].map(([k, l]) => `<button data-o1="basis=${k}" aria-pressed="${o.basis === k}">${l}</button>`).join('')}</div><div class="seg sm">${['1Y', '3Y'].map(p => `<button data-o1="period=${p}" aria-pressed="${o.period === p}">${p === '1Y' ? '1 year' : '3 years'}</button>`).join('')}</div>`})}</div>
  <div class="sec">
  ${dx('w1-drift', 'Why flagged: allocation against the CIO bands', `${g.out} classes and ${g.outG} groups outside tolerance`, `
    <div class="sec-h"><span class="sub">Settings come from the summary above: ${esc(c.assumptions)}</span>
      <div class="seg"><button data-o1="lvl=L1" aria-pressed="${o.lvl === 'L1'}">L1 groups</button><button data-o1="lvl=L2" aria-pressed="${o.lvl === 'L2'}">L2 classes</button></div></div>
    <div class="grid2"><div class="panel">${CH.bands(rows, {w: 360, left: o.lvl === 'L1' ? 92 : 136, fmt, label: 'Allocation against tolerance bands'})}
        <div class="legend"><span><i class="ring"></i>inside band</span><span><i style="background:var(--warn);border-radius:50%"></i>outside band</span><span><i class="tick"></i>CIO target</span><span><i style="background:rgba(11,122,75,.18)"></i>tolerance</span></div></div>
      <div class="panel">${CH.gauge({w: 280, min: lo, max: hi, lo: b.low, hi: b.high, today: g.st.vol, after: g.stT.vol, big: pct(g.st.vol, 1), sub: `${pct(g.stT.vol, 1)} at the CIO target`, minLab: pct(lo, 0), maxLab: pct(hi, 0), bandTip: `${d.hh.profile} band`})}
        <div class="legend"><span><i style="background:rgba(11,122,75,.35)"></i>profile band</span><span><i style="background:var(--fg)"></i>today</span><span><i style="background:var(--brand)"></i>CIO target</span></div>
        <p class="sub" style="margin-top:8px">Amber marks a difference from the house model. Red is reserved for a breach of the client's risk profile, blockers and missing data.</p></div></div>
    ${outRows.length ? `<div class="tw" style="margin-top:10px"><table class="tbl"><thead><tr><th>${o.lvl === 'L1' ? 'Group' : 'Asset class'}</th><th class="r">Today</th><th class="r">CIO target</th><th class="r">Band</th><th class="r">Gap</th><th class="r">Dollars</th></tr></thead><tbody>
      ${outRows.map(r => `<tr><td>${esc(o.lvl === 'L1' ? r.label : short(r.k))}</td><td class="r">${pct(r.w, 1)}</td><td class="r">${pct(r.t, 1)}</td><td class="r">${pct(Math.max(0, r.t - (o.lvl === 'L1' ? tol.group : tol.class)), 0)}–${pct(r.t + (o.lvl === 'L1' ? tol.group : tol.class), 0)}</td><td class="r"><b>${ppt(r.g, 1)}</b></td><td class="r">${money(r.usd)}</td></tr>`).join('')}</tbody></table></div>` : ''}`)}
  ${dx('w1-attr', 'Performance attribution', `${o.period === '3Y' ? '3 years' : '1 year'}: ${spct(a.active)} vs the CIO allocation`, `
    <div class="sec-h"><span class="sub">Period from the summary above: ${o.period === '1Y' ? '1 year' : '3 years, annualized'}</span></div>
    <div class="split"><div style="min-width:300px">${CH.waterfall({steps: [{label: 'Allocation', delta: a.alloc, tip: 'Weights different from the CIO allocation'}, {label: 'Selection', delta: a.sel, tip: 'Funds and stocks beating or trailing their class benchmark'}, {label: 'Interaction', delta: a.inter, tip: 'Combined effect'}], start: a.RB, startLab: 'CIO allocation', endLab: 'This portfolio', fmt: v => pct(v, 1), dfmt: x => ppt(x), upGood: true, w: 330, label: 'Attribution'})}</div>
      <div class="tw"><table class="tbl"><thead><tr><th>Asset class</th><th class="r">Weight vs CIO</th><th class="r">Allocation (pts)</th><th class="r">Selection (pts)</th></tr></thead><tbody>
        ${a.rows.filter(r => Math.abs(r.alloc) + Math.abs(r.sel) > 0.0003).sort((x, y) => (x.alloc + x.sel) - (y.alloc + y.sel)).map(r => `<tr><td>${esc(short(r.k))}</td><td class="r">${ppt(r.wp - r.wb, 0)}</td><td class="r" style="background:${heat(r.alloc, -0.006, 0.006)}">${(r.alloc >= 0 ? '+' : '−') + Math.abs(r.alloc * 100).toFixed(2)}</td><td class="r" style="background:${heat(r.sel, -0.006, 0.006)}">${(r.sel >= 0 ? '+' : '−') + Math.abs(r.sel * 100).toFixed(2)}</td></tr>`).join('')}</tbody></table></div></div>
    ${a.det.length ? `<p class="sub" style="margin:10px 0 4px"><b>Detractors against their benchmark:</b></p><div class="chips">${a.det.slice(0, 6).map(x => `<span class="chip" style="cursor:default" data-tip="${esc(`${x.name}: ${pct(x.r, 1)} vs ${pct(x.bm, 1)} benchmark${x.cost ? ' · costs ' + x.cost + ' bp' : ''}`)}">${esc(x.sym)} ${ppt(x.ex, 1)}</span>`).join('')}</div>` : ''}
    <p class="disc">${esc(d.perfNote)} Returns as of ${d.perfAsOf}. Past performance does not guarantee future results.</p>`)}
  ${dx('w1-strat', 'Strategies that fit', d.strat.map(s => s.name).slice(0, 2).join(', '), `<div class="cmp-cards">${d.strat.map(s => `<div class="pcard"><div class="sec-h" style="margin:0"><h3 style="font-size:14px">${esc(s.name)}</h3>${s.blocked ? '<span class="act-pill bad">not eligible</span>' : `<span class="pill ${s.score >= 0.6 ? 'good' : 'neutral'}">fit ${Math.round(s.score * 100)}</span>`}</div><p class="sub" style="margin:0">${esc(s.desc)}</p><div class="rows"><div><span>Type · minimum</span><span>${esc(s.kind)} · ${money(s.min)}</span></div><div><span>Manager fee</span><span>${s.fee_bps} bp</span></div></div><ul class="why-l">${s.why.map(w => `<li>${esc(w)}</li>`).join('')}</ul></div>`).join('')}</div><p class="disc">Fit reflects gaps, detractors and tax needs; product eligibility and suitability are confirmed before any proposal.</p>`)}
  ${dx('w1-move', 'Tax and implementation: how it would move', ex ? 'transition not available' : `planning estimate · ${Object.keys(rsum).length} routes`, `${ex ? `<div class="gate bad">Not eligible for the program: ${esc(c.elig.reason)}. The routing below is shown for reference only.</div>` : '<p class="sub" style="margin-top:0">Planning estimate, not a validated trade plan.</p>'}
    <div class="split"><div>${CH.donut(Object.entries(rsum).map(([k, v]) => ({id: k, label: R[k][0], value: v, color: R[k][1], tip: `${R[k][0]}: ${money(v)}`})), {size: 170, center: money(d.routing.reduce((s, r) => s + r.mv, 0), 1), sub: 'brokerage', label: 'Routing'})}</div>
      <div class="tw"><table class="tbl"><thead><tr><th>Holding</th><th>Route</th><th class="r">Value</th><th class="r">Gain</th></tr></thead><tbody>${d.routing.map(r => `<tr><td><span class="ticker">${esc(r.sym)}</span> <span class="nm" style="display:inline">${esc(r.name)}</span></td><td><i class="sw" style="background:${R[r.route][1]}"></i><span data-tip="${esc(r.why)}">${R[r.route][0]}</span></td><td class="r">${money(r.mv)}</td><td class="r">${r.route === 'basis' ? '<span class="down">part missing</span>' : money(r.gain)}</td></tr>`).join('')}</tbody></table></div></div>
    ${instep ? `<p class="sub" style="margin:10px 0 0"><b>Invest in steps:</b> ${months.map(m => `${m} ${money(instep / 6)}`).join(' · ')}</p>` : ''}`)}
  </div>
  <div class="sec"><div class="pf-bar"><button class="btn" data-clip="ws1">Add to talking points</button><span class="sub">Carries the finding, its evidence and the trade-offs.</span></div></div>`;
}

/* ---------- client story and proposal ---------- */
function WS2(){
  const d = V.stage.data, hh = d.hh, o = d.o2, c = d.costs, v = d.v, V2 = v.val, cl = d.clips, wn = d.whyNow, sma = c.opt.find(x => x.id === 'sma');
  const blocked = v.status === 'blocked', steps = hstepper(hh, V.stage.hstate, V.side.H.step === 'handoff' && false);
  return head('Client story and proposal', 'What an advisory relationship could add for this client, what it costs, and the alternatives, using approved content only.') + hstepper(hh, V.stage.hstate, !!S.handed[hh.id]) +
  `<div class="sec">${card({...d.card, strip: d.strip})}</div>
  ${blocked ? '' : `<div class="sec"><div class="panel"><div class="sec-h"><span class="k">Only in a managed account</span><span class="sub">not available in a brokerage account · applied to ${esc(hh.name)}'s holdings</span></div>
    <div class="mgd">${v.mgd.map(m => `<div class="mg"><span class="mtag">Managed accounts only</span><b>${esc(m.t)}</b><p>${esc(m.d)}</p></div>`).join('')}</div></div></div>`}
  ${blocked ? '' : `<div class="sec"><div class="panel"><div class="sec-h"><span class="k">The value case</span><span class="sub">illustrative; suitability is the advisor's determination</span></div>
    <div class="tradeoff">
      <div><div class="k">What the client would gain</div><ul class="gain">
        <li><b>A fiduciary relationship</b> with ongoing monitoring and rebalancing to the CIO allocation${V2.er > 0 ? `: expected return ${ppt(V2.erPts, 2)} a year before costs (≈ ${money(V2.er)})` : ''}.</li>
        ${['drift', 'none'].includes(v.kind) ? '' : `<li><b>${esc(v.plan[0].toUpperCase() + v.plan.slice(1))}.</b></li>`}
        <li><b>Tax management built in</b>: ${v.mgd.length} managed-account capabilities above${V2.lossNow > 1000 ? `, plus ${money(V2.lossNow)} of losses harvested in the move` : ''}.</li>
        <li><b>More investment choices</b>: ${d.nStrategies} strategies, including models, SMA managers and direct indexing${v.fits.length ? `; the best fits here are ${esc(v.fits.join(', '))}` : ''}.</li>
        <li><b>Trading included</b>: no commissions (about ${money(V2.comm)} a year today).</li></ul></div>
      <div><div class="k">What it costs</div><p><b>${money(v.prog.total)} a year</b> in the program (${Math.round(v.prog.bps)} bp, tiered), against ${money(v.stay.total)} today: <b>${V2.inc >= 0 ? '+' : '−'}${money(Math.abs(V2.inc))}</b>.</p>
        <p>Quantified value ≈ <b>${money(V2.quant)} a year</b>; estimated net <b class="${V2.net >= 0 ? 'up' : 'tw-warn'}">${V2.net >= 0 ? '+' : '−'}${money(Math.abs(V2.net))}</b>.</p>
        <p class="sub">Not counted: ongoing advice and planning, the risk reduction from the plan, and the one-time tax items.</p></div>
      ${v.stayR.length ? `<div class="stayr"><div class="k">Points to weigh openly</div><ul>${v.stayR.map(x => `<li>${esc(x)}</li>`).join('')}</ul></div>` : ''}</div>
    <p class="disc">Illustrative fees, capital market assumptions and harvesting assumptions; not a guarantee of results. Advisor compensation differs between options. Staying in brokerage remains a legitimate choice.</p></div></div>`}
  <div class="sec">
  ${dx('w2-svc', 'Service-level comparison', 'four options side by side', `<div class="tw"><table class="tbl svc"><thead><tr><th></th><th>Stay in brokerage</th><th>Advisory: CIO model</th><th>With SMA managers</th><th>Index-only</th></tr></thead><tbody>${d.svc.map(r => `<tr><td><b>${esc(r[0])}</b></td>${r.slice(1).map(x => `<td>${esc(x)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`)}
  ${dx('w2-why', '1 · Why now', `${wn.filter(w => o.auto[w.key]).length} of ${wn.length} selected · ${cl.length} talking point${cl.length === 1 ? '' : 's'}`, `<div class="clips">${wn.map(w => `<label class="clip"><input type="checkbox" data-auto="${w.key}" ${o.auto[w.key] ? 'checked' : ''}><span><b>${esc(w.title)}</b><span class="sub" style="display:block">${esc(w.text)}</span><span class="prov">${esc(w.src)}</span></span></label>`).join('')}
      ${cl.map(w => `<div class="clip in"><span class="src src-${w.ws}">${esc(WSL[w.ws] || '')}</span><span><b>${esc(w.title)}</b><span class="sub" style="display:block">${esc(w.text)}</span></span></div>`).join('')}</div>`)}
  ${dx('w2-fee', '2 · Fee model', `program ${money(v.prog.total)} vs brokerage ${money(v.stay.total)} a year`, `
    <div class="adjust"><div class="ctl"><label for="amt">Assets moving</label><input id="amt" type="number" step="50000" value="${o.amount}" data-o2n="amount"></div>
      <div class="ctl"><label>Brokerage trading a year <span class="val">${pct(o.turnover)}</span></label><input type="range" min="0" max="0.5" step="0.01" value="${o.turnover}" data-o2r="turnover"></div>
      <div class="ctl"><label>Equity run by SMA managers <span class="val">${pct(o.sma)}</span></label><input type="range" min="0" max="1" step="0.05" value="${o.sma}" data-o2r="sma"></div></div>
    <div class="cmp-cards" style="margin-top:12px">${c.opt.map(x => `<div class="pcard"><h3 style="font-size:14px">${esc(x.name)}</h3>
      <div class="mini">${CH.donut(x.parts.filter(p => p[1] > 0).map((p, i) => ({id: p[0], label: p[0], value: p[1], color: `var(--c${[1, 2, 5, 7][i]})`, tip: `${p[0]}: ${money(p[1])}`})), {size: 88, center: Math.round(x.bps) + ' bp', label: x.name + ' cost'})}<div><div style="font-size:18px;font-weight:700">${money(x.total)}</div><div class="sub">a year</div></div></div>
      <div class="rows">${x.parts.map(p => `<div><span>${esc(p[0])}</span><span>${money(p[1])}</span></div>`).join('')}<div><span>Net of costs</span><span>${pct(x.net, 2)}</span></div></div></div>`).join('')}</div>
    <div class="tw" style="margin-top:10px"><table class="tbl"><thead><tr><th>Program fee tier</th><th class="r">Rate</th><th class="r">Assets</th><th class="r">Fee</th></tr></thead><tbody>${c.pf.parts.map(p => `<tr><td>${money(p.from)}${p.to ? '–' + money(p.to) : ' and above'}</td><td class="r">${(p.rate * 100).toFixed(2)}%</td><td class="r">${money(p.slab)}</td><td class="r">${money(p.fee)}</td></tr>`).join('')}</tbody></table></div>
    <p class="disc">${esc(d.feeNotes.join(' '))}</p>`)}
  ${dx('w2-obj', '3 · Client considerations', `${d.objs.filter(x => o.obj[x.id]).length} objections prepared`, d.objs.map(x => `<label class="clip"><input type="checkbox" data-obj="${x.id}" ${o.obj[x.id] ? 'checked' : ''}><span><b>${esc(x.q)}</b><span class="sub" style="display:block">${esc(x.a)}</span><span class="appr">Approved response · ${esc(x.contentTitle)}</span></span></label>`).join('') + d.objOut.map(x => `<div class="clip off"><span>✕</span><span><b>${esc(x.q)}</b><span class="sub" style="display:block">Not offered for this client: the approved answer says the move lowers risk, but expected volatility does not fall here (${pct(v.stay.vol, 1)} → ${pct(v.prog.vol, 1)}).</span></span></div>`).join(''))}
  ${dx('w2-prep', '4 · Advisor preparation: materials and draft', `${d.lib.filter(x => o.content[x.id]).length} approved items · draft v${o.ver} · ${({draft: 'not reviewed', advisor: 'advisor reviewed', compliance: 'submitted for compliance'})[o.rev]}`, `
    <div class="k" style="margin-bottom:6px">Approved materials</div>${d.lib.map(x => `<label class="clip"><input type="checkbox" data-con="${x.id}" ${o.content[x.id] ? 'checked' : ''} ${x.audience === 'advisor' ? 'disabled' : ''}><span><b>${esc(x.title)}</b> <span class="pill neutral">${esc(x.kind)}</span>${x.audience === 'advisor' ? ' <span class="pill warn">advisor only</span>' : ''}<span class="sub" style="display:block">${esc(x.summary)}</span><span class="appr">Approved ${x.approved} · expires <span class="${x.soon ? 'down' : ''}">${x.expires}</span></span></span></label>`).join('')}
    <div class="draft-h"><span><b>Client story draft</b> <span class="pill warn">Generated draft · requires advisor and compliance review</span></span><span class="sub">Version ${o.ver} · prototype: not saved</span>
      <select data-rev aria-label="Review status">${[['draft', 'Draft'], ['advisor', 'Advisor reviewed'], ['compliance', 'Submitted for compliance']].map(([k, l]) => `<option value="${k}" ${o.rev === k ? 'selected' : ''}>${l}</option>`).join('')}</select></div>
    <div class="sum-doc"><textarea data-tp2 aria-label="Client story draft">${esc(d.story)}</textarea>
    <div class="pf-bar" style="margin-top:6px"><button class="btn sm" data-regen2>Rebuild draft</button><button class="btn sm" data-copy2>Copy</button></div>
    <div class="adjust" style="margin-top:10px"><div class="ctl" style="flex:1"><label for="note">Advisor note (not pre-approved; marked as such)</label><input id="note" type="text" style="width:100%" value="${esc(o.note)}" data-o2t="note"></div></div>
    <div class="provl"><div class="k">Sources in this draft</div><ul>${wn.filter(w => o.auto[w.key]).map(w => `<li>${esc(w.title)}: ${esc(w.src)}</li>`).join('')}${cl.map(w => `<li>${esc(w.title)}: talking point from ${esc(WSL[w.ws] || '')}</li>`).join('')}${d.objs.filter(x => o.obj[x.id]).map(x => `<li>Approved response: ${esc(x.q)}</li>`).join('')}${d.lib.filter(x => o.content[x.id]).map(x => `<li>Approved material: ${esc(x.title)} (approved ${x.approved})</li>`).join('')}</ul></div>
    <p class="disc">Approved materials explain the program; they do not establish that this recommendation is suitable for this client. Suitability is the advisor's determination.</p></div>`)}
  </div>`;
}

/* ---------- concentrated position ---------- */
function thCtl(t){ return `<div class="sec"><div class="adjust thr"><div class="ctl"><label>Alert threshold (analytical) <span class="val">${pct(t.th)}</span></label><input type="range" min="0.05" max="0.3" step="0.01" value="${t.th}" data-th></div>
  <div class="ctl" style="min-width:220px"><span class="lab">Program eligibility gate (fixed)</span><span><b>${pct(t.exclude_over)}</b> in one security <span class="sub">excluded from the program; measured on direct holdings plus look-through into funds</span></span></div>
  <span class="sub">The alert threshold finds positions to review (requirements: ${pct(t.threshold)}; earlier material: ${pct(t.deck)}). The 50% gate is a business rule and cannot be changed here. This list shows positions held directly, where tax lots can be planned; a concentration held only through funds is still caught by the gate and flagged in the allocation review.</span></div></div>`; }
function WS3(){
  const d = V.stage.data;
  if(d.empty) return head('Concentrated position', 'No positions above the alert threshold.') + thCtl(d.thCtl);
  const o = d.o3, plan = d.plan, sym = d.sym, R = d.risk;
  return head('Concentrated position', 'Single-company risk reduced at a pace set by the client\'s tax position.') + thCtl(d.thCtl) +
  `<div class="sec">${card({...d.card, strip: d.strip})}</div>
  <div class="sec"><div class="panel"><div class="sec-h"><span class="k">Available path</span><span class="sub">answers come from the client file; change them here</span></div>
      ${CH.tree(d.tree.steps, d.tree.result, {w: 700})}
      <div class="chips" style="margin-top:8px"><button class="chip" data-ans="gift" aria-pressed="${o.ans.gift}">Gifting intent</button><button class="chip" data-ans="cash" aria-pressed="${o.ans.cash}">Cash needs</button><button class="chip" data-ans="keep" aria-pressed="${o.ans.keep}">Keep the upside</button></div></div></div>
  <div class="sec">
  ${dx('w3-risk', 'Risk before and after', `planning scenario year one vs illustrative full trim`, `<div class="tw"><table class="tbl"><thead><tr><th></th><th class="r">Today</th><th class="r">Planning scenario: year one</th><th class="r">Illustrative full trim to ${pct(o.target, 1)}</th></tr></thead><tbody>
      <tr><td>${esc(sym)} share of the account</td><td class="r">${pct(R.m0.share, 1)}</td><td class="r">${pct(R.mY.share, 1)}</td><td class="r">${pct(R.mF.share, 1)}</td></tr>
      <tr><td>Portfolio volatility</td><td class="r">${pct(R.m0.vol, 1)}</td><td class="r">${pct(R.mY.vol, 1)}</td><td class="r">${pct(R.mF.vol, 1)}</td></tr>
      <tr><td>Worst past event (${esc(R.worst)})</td><td class="r">${pct(R.m0.stress)}</td><td class="r">${pct(R.mY.stress)}</td><td class="r">${pct(R.mF.stress)}</td></tr>
      <tr><td>Sold · estimated tax</td><td class="r">—</td><td class="r">${money(R.y1)} · ${money(R.y1tax)}</td><td class="r">${money(R.full)} · ${money(R.fullTax)}</td></tr></tbody></table></div>
    <p class="sub">The planning-scenario column follows the gain budget, gifting, cash needs and trading rules; the full trim shows the end point if everything were sold at once, which the gain budget would not allow. Neither is a validated trade plan.</p>`)}
  ${dx('w3-lots', 'Tax lots', `${d.lots.length} lot${d.lots.length === 1 ? '' : 's'}${d.noBasis ? ' · basis missing' : ''}`, `<div class="tw"><table class="tbl"><thead><tr><th>Lot</th><th>Acquired</th><th>Term</th><th class="r">Value</th><th class="r">Cost</th><th class="r">Basis / value</th><th class="r">Gain</th><th class="r">Tax if sold</th><th></th></tr></thead><tbody>
      ${d.lots.map(l => { const bp = l.cost == null ? null : l.cost / l.mv, gn = l.cost == null ? null : l.mv - l.cost; return `<tr><td>${esc(l.id)}</td><td>${esc(l.acquired || '—')}</td><td>${esc(l.term)}</td><td class="r">${money(l.mv)}</td><td class="r">${l.cost == null ? '<span class="down">missing</span>' : money(l.cost)}</td><td class="r" style="background:${heat(bp, 0, 1)}">${bp == null ? '—' : pct(bp)}</td><td class="r">${gn == null ? '—' : money(gn)}</td><td class="r">${gn == null ? '—' : money(gn * (l.term === 'ST' ? d.rates.st : d.rates.lt))}</td><td>${bp == null ? '<span class="pill bad">blocker: find basis</span>' : bp < 0.3 ? '<span class="pill neutral">gift candidate</span>' : ''}</td></tr>`; }).join('')}</tbody></table></div>`)}
  ${dx('w3-plan', 'Multi-year sale plan', plan.reach ? `reaches ${pct(o.target, 1)} in ${plan.reach}` : `above ${pct(o.target, 1)} after ${o.years} years`, `
    <div class="adjust"><div class="ctl"><label>Target share <span class="val">${pct(o.target, 1)}</span></label><input type="range" min="0.05" max="${Math.max(0.06, Math.min(0.5, d.share)).toFixed(3)}" step="0.005" value="${o.target}" data-o3r="target"></div>
      <div class="ctl"><label for="gb">Gains allowed a year</label><input id="gb" type="number" step="10000" value="${Math.round(o.budget || 0)}" data-o3n="budget"></div>
      ${o.ans.gift ? `<div class="ctl"><label for="gf">Gift a year (lowest basis)</label><input id="gf" type="number" step="50000" value="${o.gift}" data-o3n="gift"></div>` : ''}
      ${o.ans.cash ? `<div class="ctl" style="flex-basis:100%"><span class="lab">Cash needed from the position</span><div class="chips">${[2026, 2027, 2028, 2029, 2030, 2031].slice(0, o.years).map(y => `<label class="yr">${y} <input type="number" step="10000" value="${o.needs[y] || 0}" data-need="${y}"></label>`).join('')}</div></div>` : ''}</div>
    <div style="margin-top:10px">${CH.line(plan.years.map(r => ({x: String(r.y), y: r.share, tip: `${r.y}: ${pct(r.share, 1)} after selling ${money(r.sold)}${r.gifted ? ', gifting ' + money(r.gifted) : ''}`})), {w: 680, h: 200, th: o.target, thLab: 'target ' + pct(o.target, 1), fmt: v => pct(v, 0), label: 'Share by year'})}
      <div class="tw"><table class="tbl"><thead><tr><th>Year</th><th class="r">Sold</th><th class="r">Gifted</th><th class="r">Gain</th><th class="r">Tax</th><th class="r">Cash need</th><th class="r">Share after</th></tr></thead><tbody>${plan.years.map(r => `<tr><td>${r.y}</td><td class="r">${money(r.sold)}</td><td class="r">${r.gifted ? money(r.gifted) : ''}</td><td class="r ${r.overBudget ? 'down' : ''}">${money(r.gain)}${r.overBudget ? ' *' : ''}</td><td class="r">${money(r.tax)}</td><td class="r">${r.need ? money(r.need) : ''}</td><td class="r"><b>${pct(r.share, 1)}</b></td></tr>`).join('')}</tbody></table>
      ${plan.years.some(r => r.overBudget) ? '<p class="sub">* over the yearly gain budget because of the cash need</p>' : ''}</div></div>
    <p class="disc">A simulation, not an executable order: prices held constant; trades follow lot order and any trading windows. ${esc(d.taxNote)}</p>`)}
  ${dx('w3-sol', 'Solutions and actionability', d.sols.filter(s => s.at !== 'bad').length + ' available', `<div class="tw"><table class="tbl"><thead><tr><th>Solution</th><th>Actionability</th><th>Effect on concentration</th><th>Horizon</th><th class="r">Fit</th></tr></thead><tbody>
      ${d.sols.map(s => `<tr><td><b>${esc(s.name)}</b><div class="sub">${esc(s.desc)}</div></td><td><span class="act-pill ${s.at}">${esc(s.al)}</span></td><td>${esc(s.why)}</td><td>${esc(s.horizon)}</td><td class="r">${Math.round(s.fit * 100)}</td></tr>`).join('')}</tbody></table></div>`)}
  </div>
  <div class="sec"><div class="pf-bar"><button class="btn" data-clip="ws3">Add to talking points</button></div></div>`;
}

/* ---------- market and research ---------- */
const evTabs = () => `<div class="sec"><div class="seg evtabs" role="tablist">${[['book', 'My book impact', 'events matched to your households'], ['firm', 'Firm intelligence', 'everything you are entitled to read']].map(([k, l, d]) => `<button role="tab" data-o4view="${k}" aria-pressed="${S.o4.view === k}"><b>${l}</b><span>${d}</span></button>`).join('')}</div></div>`;
function WS4(){
  const d = V.stage.data, ev = d.ev, view = d.view, dg = d.dg;
  const row = (r, i) => `<tr class="click ${r.hid === d.sel ? 'sel' : ''}" data-drill="hh:${r.hid}" tabindex="0"><td>${i + 1}. <b>${esc(r.name)}</b></td><td>${esc(r.size)}</td><td>${pill(r.status)}</td></tr>`;
  const det = d.detail;
  const detail = !det ? '' : det.kind === 'view' ? `<div class="tw"><table class="tbl"><thead><tr><th>Asset class</th><th>New view</th><th class="r">Today vs tactical target</th><th class="r">Dollars</th><th></th></tr></thead><tbody>${det.rows.map(x => `<tr><td>${esc(short(x.k))}</td><td>${x.dir > 0 ? 'Overweight' : 'Underweight'}</td><td class="r">${ppt(x.g, 1)}</td><td class="r">${money(x.usd)}</td><td>${x.against ? '<span class="pill warn">against the view</span>' : '<span class="pill good">in line</span>'}</td></tr>`).join('')}</tbody></table></div>`
    : det.kind === 'client' ? `<p>${esc(ev.summary)}</p>` : !det.rows.length ? '<p class="sub">No holdings move.</p>'
    : `<div class="tw"><table class="tbl"><thead><tr><th>Holding</th><th>How</th><th class="r">Value</th><th class="r">Estimated move</th><th class="r">Dollars (est.)</th><th class="r">Of the account</th></tr></thead><tbody>${det.rows.map(x => `<tr><td><span class="ticker">${esc(x.sym)}</span> <span class="nm" style="display:inline">${esc(x.name)}</span></td><td>${esc(x.via.join(', '))}</td><td class="r">${money(x.mv)}</td><td class="r">${spct(x.r, 2)}</td><td class="r">${money(x.usd)}</td><td class="r">${spct(x.usd / det.tot, 2)}</td></tr>`).join('')}</tbody></table></div><p class="disc">Estimated from the event's price moves applied to today's holdings, looking through funds; not a realized gain or loss.</p>`;
  return head('Market and research', 'Which clients an event materially affects, how sure we are, and what merits action.') + evTabs() +
  `<div class="sec"><div class="panel soft"><div class="sec-h" style="margin:0"><span><span class="src src-${ev.type}">${esc(d.typeL)}</span> <span class="sub">${ev.date}</span></span></div><h2 class="serif" style="margin:6px 0 4px;font-size:22px">${esc(ev.headline)}</h2><p style="margin:0">${esc(ev.summary)}</p></div></div>
  ${d.card ? `<div class="sec">${card({...d.card, strip: d.strip})}</div>` : ''}
  <div class="sec"><div class="panel"><div class="sec-h"><span class="k">Affected households</span><span class="sub">${d.ranked.length} material · ${d.rest.length} monitor or no action</span></div>
    ${d.ranked.length ? `<table class="tbl"><tbody>${d.ranked.map(row).join('')}</tbody></table>` : '<p class="sub">No household is materially affected.</p>'}
    ${d.rest.length ? `<details class="dx inline" ${S.o4.all ? 'open' : ''} data-o4all><summary><span class="dx-t">Monitor or no action (${d.rest.length})</span></summary><table class="tbl"><tbody>${d.rest.map((r, i) => row(r, d.ranked.length + i)).join('')}</tbody></table></details>` : ''}
    ${d.book.length ? `<p class="sub">Across the book: ${d.book.map(esc).join(', ')} (not in this list).</p>` : ''}
    <p class="disc">Material means an estimated move of at least 0.5% of the account, a direct holding of a downgraded stock, or an asset class at least 5 points against a new CIO view. Smaller effects are listed as monitor or no action.</p></div></div>
  <div class="sec">
  ${det ? dx('w4-path', 'How it reaches the portfolio', det.kind === 'market' ? 'estimated, by holding' : 'exposure', detail) : ''}
  ${dx('w4-view', 'House view and research', [view && 'CIO ' + view.date, dg && 'Research ' + dg.change.date].filter(Boolean).join(' · '), `
    ${view ? `<div class="doc"><div class="dk">CIO view · ${esc(view.kind === 'class' ? 'asset class' : 'sector')} · ${view.date}</div><b>${esc(cls(view.key))}: ${esc(view.view)}</b>${view.was !== view.view ? ` <span class="sub">(was ${esc(view.was)})</span>` : ''}<div>${esc(view.why)}</div></div>` : ''}
    ${dg ? `<div class="doc"><div class="dk">Research · ${dg.change.date}</div><b>${esc(dg.sym)}: ${esc(dg.change.from)} → ${esc(dg.change.to)}</b><div>${esc(dg.change.why)}</div><div class="sub">Similar companies rated Buy: ${dg.buy.join(', ')}</div></div>` : ''}
    <p style="margin:8px 0 0;font-size:13px">${esc(ev.house)}</p><p class="disc">Sources: ${esc(d.typeL)} (${ev.date})${view ? `; CIO view (${view.date})` : ''}${dg ? `; research (${dg.change.date})` : ''}. ${esc(d.researchNote)}</p>`)}
  ${d.card ? dx('w4-story', 'Client story draft', 'what happened, house view, what it means, what to do', `<div class="why"><p><b>What happened.</b> ${esc(ev.summary)}</p><p><b>The house view.</b> ${esc(ev.house)}</p><p><b>For you.</b> ${esc(d.card.why)}</p><p><b>What to do.</b> ${esc(d.selMaterial ? ev.todo : 'No change needed; we will keep watching.')}</p></div>
    <div class="pf-bar" style="margin-top:10px"><button class="btn" data-clip="ws4">Add to talking points</button>${ev.route ? `<button class="btn" data-go="${ev.route}">${ev.route === 'ws1' ? 'Open the allocation review' : ev.route === 'ws3' ? 'Open the concentrated position' : 'Open the value story'}</button>` : ''}</div>`) : ''}
  </div>`;
}
const ST4 = {matched: ['Material match', 'warn'], monitor: ['Monitor', 'neutral'], none: ['No identified impact', 'neutral'], unknown: ['Not evaluated: insufficient data', 'neutral info'], na: ['Superseded', 'neutral']};
function FIRM(){
  const d = V.stage.data, typeL = {market: 'Market news (third party)', cio: 'Firm CIO view', research: 'Firm research'};
  const icard = it => { const b = it.book, sup = it.rule === 'superseded', run = it.run, res = it.res;
    return `<div class="icard ${S.o4.sel === it.id ? 'sel' : ''} ${sup ? 'sup' : ''}" id="ic-${it.id}"><div class="ih"><span class="src src-${it.type}">${esc(typeL[it.type])}</span><span class="sub">${it.date}</span>${sup ? '<span class="pill neutral">Superseded</span>' : ''}${S.watch.has(it.id) ? '<span class="pill neutral">On watchlist</span>' : ''}<span class="grow"></span><span class="bk ${b.k}">${esc(b.label)}</span></div>
      <h3 class="serif">${esc(it.headline)}</h3><p>${esc(it.abstract)}</p>${it.stance ? `<div class="stance"><span class="k">House stance</span> ${esc(it.stance)}</div>` : ''}
      ${sup ? `<div class="gate warn sm">${esc(it.superseded_by)}. Use the current view; this version cannot be analyzed or shared.</div>` : ''}
      <div class="meta"><span>Source: ${esc(it.source)}, ${it.date} · ${esc(it.version)}</span><span>Status: ${esc(it.status)}</span><span>Client use: ${it.client_use && !sup ? 'approved' + (it.expires ? ' until ' + it.expires : '') : it.type === 'market' ? 'third-party news, summarize in your own words' : 'internal only'}</span><span>Entitlement: ${esc(it.entitled)}</span></div>
      <div class="pf-bar acts"><button class="btn sm ${run ? '' : 'primary'}" data-ianalyze="${it.id}" ${sup ? 'disabled' : ''}>${run ? 'Hide results' : it.everRun ? 'Show book matches' : 'Analyze against my book'}</button>
        <button class="btn sm" data-iwatch="${it.id}">${S.watch.has(it.id) ? 'Remove from watchlist' : 'Add to watchlist'}</button>
        <button class="btn sm" data-isave="${it.id}" ${it.client_use && !sup ? '' : 'disabled title="Not approved for client use"'}>Save for ${esc(d.first)}'s meeting</button>
        <button class="btn sm" disabled title="Source documents are not available in this prototype">Open approved source · not in prototype</button></div>
      ${run ? `<div class="ires"><div class="sec-h" style="margin:8px 0 4px"><span class="k">Against my book</span><span class="sub">${res.filter(x => x.r.state === 'matched').length} material · ${res.filter(x => x.r.state === 'monitor').length} monitor · ${res.filter(x => x.r.state === 'none').length} no identified impact · ${res.filter(x => x.r.state === 'unknown').length} not evaluated · run against positions as of ${d.positions}</span></div>
        <div class="tw"><table class="tbl"><tbody>${res.map(x => { const key = it.id + ':' + x.hid;
          return `<tr class="${x.hid === S.hid ? 'sel' : ''}"><td><button class="link" data-hh="${x.hid}"><b>${esc(x.name)}</b></button></td><td><span class="pill ${ST4[x.r.state][1]}">${esc(ST4[x.r.state][0])}</span></td><td>${esc(x.r.size)}<div class="sub">${esc(x.r.why)}</div></td>
            <td>${x.r.state !== 'matched' ? '' : it.auto ? `<button class="btn sm" data-bookev="${it.id}:${x.hid}">Open in My book impact</button>` : x.promoted ? '<span class="sub">Added to opportunities ✓</span>' : `<button class="btn sm" data-promo="${key}">Add to opportunities</button><div><span class="act-pill ${x.elig[1]} xs">${esc(x.elig[0])}</span></div>`}</td></tr>`; }).join('')}</tbody></table></div>
        <p class="disc">Only a material match can become an opportunity, and only when the advisor adds it; its eligibility comes from the same rule as everywhere else. "No identified impact" is limited by holdings coverage, look-through and matching rules; "not evaluated" means the data needed is missing.</p></div>` : ''}</div>`; };
  return head('Market and research', 'Which clients an event materially affects, how sure we are, and what merits action.') + evTabs() +
    `<div class="sec"><div class="panel soft firm-h"><p style="margin:0">Everything you are entitled to read, whether or not it touches your households: <b>${d.n}</b> items in this sample catalog, as of ${d.as_of}. Reading or publishing an item never adds work; the opportunity count changes only when you add a material match.</p>
      <input class="isearch" type="search" placeholder="Search titles, tickers, themes…" value="${esc(S.o4.q)}" data-isearch aria-label="Search firm intelligence"></div></div>
    <div class="sec">${d.cards.length ? d.cards.map(icard).join('') : '<p class="sub">Nothing matches these filters.</p>'}</div>`;
}

/* ---------- task panel ---------- */
function paintSide(){
  const s = V.side, hh = s.hh, open = $('#side').classList.contains('open'), key = s.decision.key, disp = s.disp, L = s.life, st = s.stages, cur = s.cur;
  const inPage = S.ws === 'path' && S.hstep === 'handoff';
  $('#side').innerHTML = `<div class="sh"><button class="mob btn sm" data-sidetoggle style="float:right">${open ? 'Close ▾' : 'Open ▴'}</button><div class="k">Current task</div><div class="pname"><b style="font-size:15px">${esc(hh.name)}</b></div>
      <p class="sub" style="margin:4px 0 0">${esc(cur >= 0 ? st[cur].stage + ': ' + st[cur].note : 'All stages complete')}</p>
      <button class="btn ${inPage ? '' : 'primary'} nextbtn" data-hstep="${s.H.next[1]}" data-hid="${hh.id}">${esc(s.H.next[0])}</button></div>
    <div class="sb">
      <div class="rail-b"><div class="kv"><span>Owner</span><b>${esc(s.blk.owner === 'Advisor' ? 'You (advisor)' : 'You, then ' + s.blk.owner)}</b></div>
        <div class="kv"><span>Blocking</span><b>${esc(s.blk.t)}</b></div>
        <div class="kv"><span>Status</span><b>${esc(s.elig[0])} · ${esc(st[4].note.replace(/:.*/, ''))}</b></div>
        <div class="stg">${st.map((x, i) => `<span class="sd ${x.state} ${i === cur ? 'cur' : ''}" title="${esc(x.stage + ': ' + x.note)}">${esc(x.stage)}</span>`).join('')}</div></div>
      <details class="dx inline"><summary><span class="dx-t">Story draft</span> <span class="sub">prepared for review, not approved</span></summary><p class="story">${esc(s.story)}</p><p class="sub" style="margin:2px 0 0">Talking points collected: ${s.clips}</p></details>
      <details class="dx inline"><summary><span class="dx-t">Stages, decisions and owners</span></summary><div class="ladder full stages">${st.map(x => `<div class="lstep ${x.state}"><span class="ic">${LIC[x.state]}</span><div><b>${esc(x.stage)}</b><div class="sub">${esc(x.note)}</div><div class="hd"><em>You decide:</em> ${esc(x.decide)}</div><div class="hd hctl"><em>Control:</em> ${esc(x.control)}</div></div></div>`).join('')}</div>
        <div class="k" style="margin-top:8px">All blockers</div><ul class="pre">${s.blockers.map(b => `<li>${esc(b.t)} <span class="own">${esc(b.owner)}</span></li>`).join('')}</ul></details>
      ${key ? `<details class="dx inline" id="wf" ${disp || S.ws !== 'path' ? 'open' : ''}><summary><span class="dx-t">Record a decision</span> <span class="sub">${esc(L.label)}${L.note ? ' · ' + esc(L.note) : ''}</span></summary>
        <div class="wf-b"><div class="wf-row"><span class="wf-state ${L.state}">${esc(L.label)}</span><span class="sub">${disp && disp.set ? 'set by advisor' : 'suggested'}: ${esc(STATUS((disp || {}).status || s.decision.status || 'review')[0])}</span></div>
        ${L.state === 'closed' && disp && disp.closed ? '' : `<div class="disp"><select data-disp aria-label="Advisor assessment"><option value="">${disp && disp.set ? 'Back to suggested' : 'Set the assessment…'}</option>${META.dispositions.map(k => `<option value="${k}" ${disp && disp.status === k ? 'selected' : ''}>${esc(STATUS(k)[0])}</option>`).join('')}</select>
          ${disp && ['stay', 'defer', 'unsuitable', 'monitor'].includes(disp.status) ? `<select data-reason aria-label="Reason" class="${L.need ? 'need' : ''}"><option value="">Reason…</option>${META.reasons.map(r => `<option ${disp.reason === r ? 'selected' : ''}>${esc(r)}</option>`).join('')}</select>` : ''}</div>${L.need ? `<p class="need-t">${esc(L.note)}; until then it stays open.</p>` : ''}`}
        ${L.state === 'closed' ? '<button class="btn sm" data-reopen>Reopen</button>' : `<div class="disp"><select data-close aria-label="Close with an outcome"><option value="">Close with an outcome…</option>${META.close_outcomes.map(x => `<option>${esc(x)}</option>`).join('')}</select></div>`}
        <p class="sub" style="margin:4px 0 0">An assessment alone keeps work open; closing is separate. Prototype: kept in this page only, not a CRM or audit record.</p></div></details>` : ''}
    </div>`;
}

/* ---------- checks dialog (rule-engine checks run on the server) ---------- */
async function showChecks(){
  const el = document.getElementById('checks') || document.body.appendChild(Object.assign(document.createElement('div'), {id: 'checks', className: 'checks'}));
  el.innerHTML = '<div class="checks-b" role="dialog" aria-label="Prototype checks"><p class="sub">Running the checks…</p></div>'; el.hidden = false;
  const r = await (await fetch('/api/checks')).json(), areas = [...new Set(r.checks.map(x => x.area))];
  el.innerHTML = `<div class="checks-b" role="dialog" aria-label="Prototype checks"><div class="sec-h"><span class="k">Prototype checks</span><button class="btn sm" data-closechecks>Close</button></div>
    <p class="sub" style="margin:4px 0 10px"><b class="${r.passed === r.total ? 'up' : 'tw-warn'}">${r.passed} of ${r.total} passed</b>, run against the rule engine at ${new Date().toLocaleTimeString()}. Nothing on screen is changed. All data is illustrative; nothing is saved.</p>
    ${areas.map(a => `<div class="k" style="margin-top:8px">${esc(a)}</div><ul class="ck">${r.checks.filter(x => x.area === a).map(x => `<li class="${x.pass ? 'ok' : 'no'}"><span>${x.pass ? '✓' : '✕'}</span><div>${esc(x.name)}${x.info ? `<div class="sub">${esc(x.info)}</div>` : ''}</div></li>`).join('')}</ul>`).join('')}
    <p class="disc">Covers: one eligibility rule including look-through; readiness wording; assessment vs workflow; claim wording; attribution arithmetic; amounts that reconcile; routes with owners; event labels; firm intelligence never creating work by itself.</p></div>`;
}

/* ---------- events ---------- */
function decisionKey(){ return V.side.decision.key; }
function go(ws, o = {}){ S.ws = ws; S.about = false; Object.assign(S, o); paint({top: true}); }
document.addEventListener('toggle', e => { const t = e.target; if(t.dataset && t.dataset.dx){ t.open ? S.open.add(t.dataset.dx) : S.open.delete(t.dataset.dx); const ta = t.querySelector('textarea[data-tp2]'); if(ta){ ta.style.height = 'auto'; ta.style.height = ta.scrollHeight + 6 + 'px'; } } if(t.dataset && t.dataset.o4all != null) S.o4.all = t.open; }, true);
document.addEventListener('click', e => {
  const c = s => e.target.closest(s); let el;
  if(document.getElementById('tour')) return;
  if(el = c('[data-checks]')){ showChecks(); return; }
  if(el = c('[data-closechecks]') || e.target.id === 'checks'){ document.getElementById('checks').hidden = true; return; }
  if(el = c('[data-hstep]')){ const st = el.dataset.hstep; if(el.dataset.hid) S.hid = el.dataset.hid; if(st === 'proposal') go('ws2'); else go('path', {hstep: st}); return; }
  if(el = c('[data-hdec]')){ const hid = el.dataset.hid, k = 'hh:' + hid, v = el.dataset.hdec; S.hid = hid;
    if(S.disp[k] && S.disp[k].status === v){ delete S.disp[k]; toast('Decision cleared'); }
    else { S.disp[k] = {status: v, set: true, reason: '', ws: 'path', at: new Date().toISOString()}; toast(v === 'ready' ? 'Pursuing: compare the paths' : `Recorded: ${STATUS(v)[0]}`); }
    if(v === 'ready' && S.disp[k]){ go('path', {hstep: 'paths'}); return; } paint(); return; }
  if(el = c('[data-hpath]')){ const k = 'hh:' + el.dataset.hid; S.choice[k] = el.dataset.hpath; if(!S.disp[k] || !['ready', 'review'].includes(S.disp[k].status)) S.disp[k] = {status: 'ready', set: true, reason: '', ws: 'path', at: new Date().toISOString()}; toast(`Path chosen: ${META.pshort[el.dataset.hpath]}`); paint(); return; }
  if(el = c('[data-handoff]')){ S.handed[el.dataset.handoff] = true; toast('Handed off to operations (prototype)'); paint(); return; }
  if(el = c('[data-mgmt]')){ S.mgmt = !S.mgmt; render(); return; }
  if(el = c('[data-hf]')){ S.hf = el.dataset.hf; render(); return; }
  if(el = c('[data-qv]')){ S.qv = el.dataset.qv; paint(); return; }
  if(el = c('[data-go]')){ const ws = el.dataset.go; go(ws, ws === 'ws3' ? {pos: null} : {}); return; }
  if(el = c('[data-open]')){ const k = el.dataset.open, p = k.split(':');
    if(p[0] === 'ws1' || p[0] === 'ws2'){ go(p[0], {hid: p[1]}); return; }
    if(p[0] === 'ws3'){ go('ws3', {hid: p[1], pos: p[1] + ':' + p[2]}); return; }
    if(p[0] === 'ws4'){ S.o4.view = 'book'; S.o4.hh = p[2]; go('ws4', {hid: p[2], ev: p[1]}); return; }
    if(p[0] === 'ws4f'){ S.o4 = {...S.o4, view: 'firm', sel: p[1], ft: 'all', fb: 'all', q: ''}; S.intelRun[p[1]] = true; go('ws4', {hid: p[2]}); return; }
    go('path', {hid: p[1], hstep: 'assess', popp: k}); return; }
  if(el = c('[data-about]')){ S.about = !S.about; render(); return; }
  if(el = c('[data-phh]')){ go('path', {hid: el.dataset.phh, popp: null}); return; }
  if(el = c('[data-popen]')){ const k = el.dataset.popen, p = k.split(':'); go('path', {hid: p[0] === 'ws4' ? p[2] : p[1], hstep: 'assess', popp: k}); S.open.add('a-six'); return; }
  if(el = c('[data-popp]')){ S.popp = el.dataset.popp; render(); return; }
  if(el = c('[data-qf]')){ S.qf = el.dataset.qf; render(); return; }
  if(el = c('[data-qws]')){ S.qws = el.dataset.qws; render(); return; }
  if(el = c('[data-hh]')){ S.hid = el.dataset.hh; paint(); return; }
  if(el = c('[data-pos]')){ S.pos = el.dataset.pos; S.hid = S.pos.split(':')[0]; paint(); return; }
  if(el = c('[data-ev]')){ S.ev = el.dataset.ev; S.o4.hh = null; paint(); return; }
  if(el = c('[data-o4view]')){ S.o4.view = el.dataset.o4view; paint(); return; }
  if(el = c('[data-ift]')){ S.o4.ft = el.dataset.ift; paint(); return; }
  if(el = c('[data-ifb]')){ S.o4.fb = el.dataset.ifb; paint(); return; }
  if(el = c('[data-evf]')){ S.o4.filter = el.dataset.evf; paint(); return; }
  if(el = c('[data-ianalyze]')){ const id = el.dataset.ianalyze, it = V.stage.data.cards.find(x => x.id === id); if(it && it.run) S.o4.sel = null; else { S.intelRun[id] = true; S.o4.sel = id; } paint(); return; }
  if(el = c('[data-iwatch]')){ const id = el.dataset.iwatch; S.watch.has(id) ? S.watch.delete(id) : S.watch.add(id); toast(S.watch.has(id) ? 'Added to watchlist (prototype: this page only)' : 'Removed from watchlist'); paint(); return; }
  if(el = c('[data-isave]')){ const it = V.stage.data.cards.find(x => x.id === el.dataset.isave); addClip('ws4', it.headline, `${it.abstract}${it.stance ? ' House stance: ' + it.stance + '.' : ''} (Source: ${it.source}, ${it.date}; from Firm intelligence.)`, {key: 'intel:' + it.id}); paint(); return; }
  if(el = c('[data-promo]')){ const [id, hid] = el.dataset.promo.split(':'); S.promo[el.dataset.promo] = {id, hid, at: new Date().toISOString()}; toast(`Added to opportunities: ${META.households.find(h => h.id === hid).name}`); paint(); return; }
  if(el = c('[data-bookev]')){ const [id, hid] = el.dataset.bookev.split(':'); S.o4.view = 'book'; S.o4.filter = 'all'; S.o4.hh = hid; go('ws4', {ev: id, hid}); return; }
  if(el = c('[data-drill^="hh:"]')){ S.o4.hh = el.dataset.drill.slice(3); S.hid = S.o4.hh; paint(); return; }
  if(el = c('[data-o1]')){ const [k, v] = el.dataset.o1.split('='); S.o1[k] = v; paint(); return; }
  if(el = c('[data-ans]')){ const o = S.o3[S.pos], k = el.dataset.ans; o.ans[k] = !o.ans[k]; if(k === 'gift' && o.ans.gift && !o.gift) o.gift = 250000; paint(); return; }
  if(el = c('[data-clip]')){ const [t, x, extra] = V.stage.data.clip; addClip(el.dataset.clip, t, x, extra); paint(); return; }
  if(el = c('[data-choice]')){ const [key, n] = el.dataset.choice.split('|'), A = choiceAct(n, S.ws);
    if(S.choice[key] === n){ delete S.choice[key]; toast('Choice cleared'); paint(); return; }
    S.choice[key] = n; const prev = S.disp[key] || {};
    if(A.close) S.disp[key] = {...prev, status: prev.status || 'monitor', set: true, reason: prev.reason || '', at: new Date().toISOString(), closed: {outcome: A.close, at: new Date().toISOString()}};
    else if(A.disp) S.disp[key] = {status: A.disp, set: true, reason: A.disp === prev.status ? prev.reason || '' : '', ws: S.ws, at: new Date().toISOString()};
    toast(`Chosen: ${n}${A.close ? ' · closed' : A.disp ? ' · assessment: ' + STATUS(A.disp)[0] : ''}`);
    if(A.open) S.open.add(A.open);
    if(A.go){ go(A.go, A.go === 'ws3' ? {pos: null} : {}); return; }
    paint().then(() => { if(A.open){ const d = document.querySelector(`[data-dx="${A.open}"]`); if(d) d.scrollIntoView({behavior: 'smooth', block: 'start'}); } }); return; }
  if(el = c('[data-reopen]')){ const k = decisionKey(), x = S.disp[k]; if(x){ delete x.closed; if(META.reason_needed.includes(x.status)) x.reason = ''; if(!x.set) delete S.disp[k]; } toast('Reopened'); paint(); return; }
  if(el = c('[data-wf]')){ const sd = $('#side'); if(getComputedStyle(sd.querySelector('[data-sidetoggle]')).display !== 'none'){ sd.classList.add('open'); paintSide(); } const w = $('#wf'); if(w) w.scrollIntoView({block: 'nearest', behavior: 'smooth'}); return; }
  if(el = c('[data-regen2]')){ const o = S.o2[S.hid]; o.tp = null; o.ver++; o.rev = 'draft'; paint(); return; }
  if(el = c('[data-copy2]')){ const ta = $('textarea[data-tp2]'); try{ navigator.clipboard.writeText(ta.value).then(() => toast('Copied'), () => { ta.select(); document.execCommand('copy'); toast('Copied'); }); }catch(_){ ta.select(); document.execCommand('copy'); toast('Copied'); } return; }
  if(el = c('[data-sidetoggle]')){ $('#side').classList.toggle('open'); paintSide(); return; }
});
document.addEventListener('change', e => {
  const t = e.target, o2 = () => S.o2[S.hid];
  if(t.dataset.hreason){ const k = 'hh:' + t.dataset.hreason; if(S.disp[k]) S.disp[k].reason = t.value; paint(); return; }
  if(t.dataset.hdone){ const m = S.done[t.dataset.hid] = S.done[t.dataset.hid] || {}; m[t.dataset.hdone] = t.checked; render(); return; }
  if(t.dataset.disp != null){ const k = decisionKey(); if(t.value) S.disp[k] = {status: t.value, set: true, reason: (S.disp[k] || {}).reason || '', ws: S.ws, at: new Date().toISOString()}; else delete S.disp[k]; toast(t.value ? `Assessment recorded: ${STATUS(t.value)[0]}` : 'Back to the suggested assessment'); paint(); return; }
  if(t.dataset.close != null){ const k = decisionKey(); if(!t.value) return; const x = S.disp[k] || (S.disp[k] = {status: V.side.decision.status, set: false, reason: '', ws: S.ws, at: new Date().toISOString()}); x.closed = {outcome: t.value, at: new Date().toISOString()}; toast(`Closed: ${t.value}`); paint(); return; }
  if(t.dataset.reason != null){ const k = decisionKey(); if(S.disp[k]) S.disp[k].reason = t.value; paint(); return; }
  if(t.dataset.rev != null){ o2().rev = t.value; paint(); return; }
  if(t.dataset.auto){ o2().auto[t.dataset.auto] = t.checked; o2().tp = null; paint(); return; }
  if(t.dataset.obj){ o2().obj[t.dataset.obj] = t.checked; o2().tp = null; paint(); return; }
  if(t.dataset.con){ o2().content[t.dataset.con] = t.checked; o2().tp = null; paint(); return; }
  if(t.dataset.o2n){ o2()[t.dataset.o2n] = Math.max(0, +t.value || 0); o2().tp = null; paint(); return; }
  if(t.dataset.o2t){ o2()[t.dataset.o2t] = t.value; o2().tp = null; paint(); return; }
  if(t.dataset.o3n){ S.o3[S.pos][t.dataset.o3n] = Math.max(0, +t.value || 0); paint(); return; }
  if(t.dataset.need){ S.o3[S.pos].needs[t.dataset.need] = Math.max(0, +t.value || 0); paint(); return; }
});
let deb; const later = f => { clearTimeout(deb); deb = setTimeout(f, 160); };
document.addEventListener('input', e => {
  const t = e.target, lab = t.parentElement && t.parentElement.querySelector('.val');
  if(t.dataset.o2r){ S.o2[S.hid][t.dataset.o2r] = +t.value; S.o2[S.hid].tp = null; if(lab) lab.textContent = pct(+t.value); later(paint); return; }
  if(t.dataset.o3r){ S.o3[S.pos][t.dataset.o3r] = +t.value; if(lab) lab.textContent = pct(+t.value, 1); later(paint); return; }
  if(t.dataset.th != null){ S.th = +t.value; if(lab) lab.textContent = pct(+t.value); later(paint); return; }
  if(t.dataset.isearch != null){ S.o4.q = t.value; later(() => paint().then(() => { const i = document.querySelector('[data-isearch]'); if(i){ i.focus(); i.setSelectionRange(i.value.length, i.value.length); } })); return; }
  if(t.dataset.tp2 != null){ S.o2[S.hid].tp = t.value; t.style.height = 'auto'; t.style.height = t.scrollHeight + 6 + 'px'; return; }
});
document.addEventListener('keydown', e => { if((e.key === 'Enter' || e.key === ' ') && e.target.dataset && (e.target.dataset.drill || e.target.dataset.open) && !document.getElementById('tour')){ e.preventDefault(); e.target.click(); } });

/* ---------- start ---------- */
(async () => { META = await (await fetch('/api/meta')).json(); S.th = META.threshold; await paint(); if(/[#&]tour\b/.test(location.hash)) setTimeout(() => window.tourStart && tourStart(), 300); })();
