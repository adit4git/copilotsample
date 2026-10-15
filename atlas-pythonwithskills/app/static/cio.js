/* ================= CIO MODEL FIT workspace =================
 * Self-contained add-on, loaded after app.js (and tem.js). Adds a "CIO Model Fit" nav item and view:
 * brokerage accounts (Bridgewater NJ market, over $50K) side by side with the CIO strategic model each
 * should map to. All figures come from /api/cio-fit (2026 CMA math in app/cio.py); no AI.
 */
(function(){
  if(typeof render !== 'function' || typeof NAVITEMS === 'undefined') return;
  const CIOS = {data:null, fa:null, sel:null};
  const pct = (x, d=1) => x == null ? '—' : (x * 100).toFixed(d) + '%';
  const pts = (x, d=1) => x == null ? '—' : ((x >= 0 ? '+' : '−') + Math.abs(x * 100).toFixed(d));
  const num = (x, d=2) => x == null ? '—' : x.toFixed(d);
  const sgn = (x, d=2) => x == null ? '—' : ((x >= 0 ? '+' : '−') + Math.abs(x).toFixed(d));
  const money = n => (typeof fmtM === 'function' ? fmtM(n) : '$' + Math.round(n).toLocaleString('en-US'));
  const dshort = iso => { const d = new Date(iso + 'T00:00:00'); return `${d.getMonth() + 1}/${d.getDate()}/${d.getFullYear()}`; };
  const first = n => n.split(' ')[0];

  async function load(){
    if(CIOS.data && CIOS.fa === state.fa) return CIOS.data;
    CIOS.data = await api(`/api/cio-fit?fa=${state.fa}`); CIOS.fa = state.fa;
    if(!CIOS.data.accounts.some(a => a.household_id === CIOS.sel)) CIOS.sel = CIOS.data.accounts[0] ? CIOS.data.accounts[0].household_id : null;
    return CIOS.data;
  }

  /* ---------- chart: expected risk vs return, today's holdings -> CIO model ---------- */
  const cmaLabel = () => (CIOS.data && CIOS.data.as_of && CIOS.data.as_of.cma) || '2026';
  function scatter(accts){
    if(!accts.length) return '';
    const W = 640, H = 300, P = {l:52, r:24, t:18, b:40};
    const xs = accts.flatMap(a => [a.current.volatility, a.model_stats.volatility]), ys = accts.flatMap(a => [a.current.expected_return, a.model_stats.expected_return]);
    const x0 = 0, x1 = Math.ceil(Math.max(...xs) * 100 / 2) * 2 / 100 + 0.02;
    const y0 = Math.floor(Math.min(...ys) * 100 - 0.5) / 100, y1 = Math.ceil(Math.max(...ys) * 100 + 0.5) / 100;
    const X = v => P.l + (v - x0) / (x1 - x0) * (W - P.l - P.r), Y = v => P.t + (y1 - v) / (y1 - y0) * (H - P.t - P.b);
    const xt = []; for(let v = 0; v <= x1 + 1e-9; v += 0.04) xt.push(v);
    const yt = []; for(let v = Math.ceil(y0 * 200) / 200; v <= y1 + 1e-9; v += 0.005) yt.push(v);
    // Place each name beside its "today" point, then nudge any label that would overlap one already placed.
    const placed = [], lab = {};
    accts.forEach(a => {
      const cx = X(a.current.volatility), cy = Y(a.current.expected_return), w = first(a.name).length * 7.2 + 4;
      const right = cx <= W - 140; let x = right ? cx + 10 : cx - 10 - w, y = cy + 4;
      const hit = () => placed.some(b => x < b.x + b.w && b.x < x + w && Math.abs(b.y - y) < 15);
      for(const dy of [0, 16, -16, 30, -30]){ y = cy + 4 + dy; if(!hit()) break; }
      placed.push({x, y, w}); lab[a.household_id] = {x, y};
    });
    const marks = accts.map(a => {
      const cx = X(a.current.volatility), cy = Y(a.current.expected_return), mx = X(a.model_stats.volatility), my = Y(a.model_stats.expected_return);
      const on = a.household_id === CIOS.sel;
      const tip = `${a.name}\nToday's holdings: ${pct(a.current.expected_return)} return, ${pct(a.current.volatility)} risk, Sharpe ${num(a.current.sharpe)}\n${a.model.label}: ${pct(a.model_stats.expected_return)} return, ${pct(a.model_stats.volatility)} risk, Sharpe ${num(a.model_stats.sharpe)}`;
      const L = lab[a.household_id];
      return `<g class="cio-pt${on ? ' on' : ''}" data-cio-acct="${a.household_id}" tabindex="0" role="button" aria-label="${esc(tip.replace(/\n/g, '. '))}"><title>${esc(tip)}</title>
        <line class="cio-link" x1="${cx}" y1="${cy}" x2="${mx}" y2="${my}"/>
        <rect class="cio-mod-mk" x="${mx - 6}" y="${my - 6}" width="12" height="12" rx="2"/>
        <circle class="cio-cur-mk" cx="${cx}" cy="${cy}" r="6.5"/>
        <circle class="cio-hit" cx="${cx}" cy="${cy}" r="16"/><circle class="cio-hit" cx="${mx}" cy="${my}" r="14"/>
        <text class="cio-lbl" x="${L.x}" y="${L.y}">${esc(first(a.name))}</text></g>`;
    }).join('');
    return `<svg class="cio-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="Expected risk and return of each account's holdings and its CIO model">
      ${yt.map(v => `<line class="cio-grid" x1="${P.l}" x2="${W - P.r}" y1="${Y(v)}" y2="${Y(v)}"/><text class="cio-ax" x="${P.l - 8}" y="${Y(v) + 4}" text-anchor="end">${(v * 100).toFixed(1)}%</text>`).join('')}
      ${xt.map(v => `<text class="cio-ax" x="${X(v)}" y="${H - P.b + 18}" text-anchor="middle">${Math.round(v * 100)}%</text>`).join('')}
      <line class="cio-axis" x1="${P.l}" x2="${W - P.r}" y1="${H - P.b}" y2="${H - P.b}"/>
      <text class="cio-ax t" x="${(P.l + W - P.r) / 2}" y="${H - 4}" text-anchor="middle">Expected risk (volatility, ${esc(cmaLabel())} CMA)</text>
      <text class="cio-ax t" x="14" y="${(P.t + H - P.b) / 2}" text-anchor="middle" transform="rotate(-90 14 ${(P.t + H - P.b) / 2})">Expected return</text>
      ${marks}</svg>
      <div class="cio-legend"><span><i class="cio-k cur"></i>Today’s holdings</span><span><i class="cio-k mod"></i>Matched CIO model</span><span class="sub">The line joins an account to its model. Click a point for the detail.</span></div>`;
  }

  /* ---------- table: one row per account ---------- */
  function table(accts){
    return `<div class="cio-scroll"><table class="cio-tbl">
      <thead><tr><th rowspan="2">Account</th><th rowspan="2">Profile → CIO model</th><th colspan="3" class="grp">Actual (ex post)</th><th colspan="3" class="grp">Expected: today’s holdings</th><th colspan="3" class="grp">Expected: CIO model</th><th rowspan="2" class="r">Sharpe gap</th><th rowspan="2" class="r">Coverage</th><th rowspan="2" class="r">Muni proxy</th><th rowspan="2">Flags</th></tr>
      <tr><th class="r">1y / 3y</th><th class="r">Std dev</th><th class="r">Sharpe</th><th class="r">Return</th><th class="r">Risk</th><th class="r">Sharpe</th><th class="r">Return</th><th class="r">Risk</th><th class="r">Sharpe</th></tr></thead>
      <tbody>${accts.map(a => { const p = a.performance, rev = a.flags.filter(f => f.severity === 'review').length;
        return `<tr class="${a.household_id === CIOS.sel ? 'on' : ''}" data-cio-acct="${a.household_id}" tabindex="0">
        <td><b>${esc(a.name)}</b><div class="sub">${esc(a.account_no)} · ${esc(a.account_type)} · ${esc(a.fa || '')}</div></td>
        <td>${esc(a.setup.profile)}${a.setup.desc_matches === false ? ' <span class="cio-warn" title="allocation_profile_desc reads differently">≠ desc</span>' : ''}<div class="sub">${esc(a.setup.tier_label)}${a.setup.tier_defaulted ? ' (defaulted)' : ''}</div></td>
        <td class="r mono">${pct(p.return_1y)} / ${pct(p.return_3y)}</td><td class="r mono">${pct(p.std_dev)}</td><td class="r mono">${num(p.sharpe)}</td>
        <td class="r mono">${pct(a.current.expected_return)}</td><td class="r mono">${pct(a.current.volatility)}</td><td class="r mono">${num(a.current.sharpe)}</td>
        <td class="r mono">${pct(a.model_stats.expected_return)}</td><td class="r mono">${pct(a.model_stats.volatility)}</td><td class="r mono">${num(a.model_stats.sharpe)}</td>
        <td class="r mono b">${sgn(a.gap.sharpe)}</td>
        <td class="r mono">${a.coverage.pct < 0.9 ? `<span class="cio-warn">${pct(a.coverage.pct, 0)}</span>` : pct(a.coverage.pct, 0)}</td>
        <td class="r mono">${a.muni_proxy_share ? pct(a.muni_proxy_share, 0) : '—'}</td>
        <td>${rev ? `<span class="cio-flag review">${rev} to review</span>` : ''}${a.flags.length - rev ? ` <span class="cio-flag info">${a.flags.length - rev} note${a.flags.length - rev > 1 ? 's' : ''}</span>` : ''}</td></tr>`; }).join('')}</tbody></table></div>`;
  }

  /* ---------- detail for the selected account ---------- */
  function allocChart(a){
    const m = Math.max(...a.allocation.flatMap(r => [r.current, r.model])) || 1;
    let group = '';
    return `<div class="cio-alloc">${a.allocation.map(r => {
      const head = r.group !== group ? `<div class="cio-ag">${esc(group = r.group)}</div>` : '';
      return head + `<div class="cio-ar" title="${esc(r.label)}: today ${pct(r.current)}, model ${pct(r.model)}, difference ${pts(r.diff)} points">
        <span class="cio-an">${esc(r.label)}</span>
        <span class="cio-bars"><b class="cur" style="width:${r.current / m * 100}%"></b><b class="mod" style="width:${r.model / m * 100}%"></b></span>
        <span class="cio-av mono">${pct(r.current)} <span class="sub">/ ${pct(r.model)}</span></span>
        <span class="cio-ad mono">${pts(r.diff)}</span></div>`; }).join('')}
      <div class="cio-legend"><span><i class="cio-k cur"></i>Today’s holdings (classified value)</span><span><i class="cio-k mod"></i>${esc(a.model.label)}</span><span class="sub">Last column: difference in percentage points.</span></div></div>`;
  }
  function detail(a){
    if(!a) return '';
    const s = a.setup, p = a.performance;
    const step = (k, v, extra='') => `<div class="cio-step"><div class="l">${k}</div><div class="v">${v}</div>${extra}</div>`;
    const setup = `<div class="cio-chain">${step('Risk tolerance', esc(s.risk_tolerance))}${step('Time horizon', esc(s.time_horizon))}<span class="cio-arrow">\u2192</span>${step('Investor profile (2-factor grid)', `<b>${esc(s.profile)}</b>`)}
        <div class="cio-side">allocation_profile_desc: ${s.allocation_profile_desc ? `\u201c${esc(s.allocation_profile_desc)}\u201d ${s.desc_matches ? '<span class="cio-ok">matches</span>' : `<span class="cio-warn">reads as ${esc(s.desc_profile)}</span>`}` : '<span class="cio-warn">blank</span>'}<div class="sub">shown for comparison; its source isn\u2019t confirmed</div></div></div>
      <div class="cio-chain">${step('Liquidity needs', s.liquidity_needs ? esc(s.liquidity_needs) : '<span class="cio-warn">blank</span>')}<span class="cio-arrow">\u2192</span>${step('Liquidity tier', `<b>${esc(s.tier_label)}</b>`)}${s.tier_defaulted ? '<div class="cio-side"><span class="cio-warn">defaulted</span><div class="sub">blank liquidity needs default to Tier 0</div></div>' : ''}</div>
      <div class="cio-chain"><span class="cio-arrow">\u21b3</span>${step('CIO strategic model (profile \u00d7 tier)', `<b>${esc(a.model.label)}</b>`)}</div>`;
    const row = (k, cur, mod, diff, act) => `<tr><td>${k}</td><td class="r mono">${cur}</td><td class="r mono">${mod}</td><td class="r mono b">${diff}</td><td class="r mono">${act}</td></tr>`;
    const metrics = `<table class="cio-tbl small"><thead><tr><th></th><th class="r">Today’s holdings<div class="sub">expected, ${esc(cmaLabel())} CMA</div></th><th class="r">CIO model<div class="sub">expected, ${esc(cmaLabel())} CMA</div></th><th class="r">Difference</th><th class="r">Actual<div class="sub">${esc(p.source)}</div></th></tr></thead><tbody>
      ${row('Return', pct(a.current.expected_return), pct(a.model_stats.expected_return), pts(a.gap.expected_return) + ' pts', `${pct(p.return_1y)} 1y · ${pct(p.return_3y)} 3y`)}
      ${row('Risk (volatility)', pct(a.current.volatility), pct(a.model_stats.volatility), pts(a.gap.volatility) + ' pts', `${pct(p.std_dev)} <span class="sub">${esc(p.std_basis)}</span>`)}
      ${row('Sharpe ratio', num(a.current.sharpe), num(a.model_stats.sharpe), sgn(a.gap.sharpe), num(p.sharpe))}
      ${row('Tracking error vs model', pct(a.gap.tracking_error), '—', '', '—')}</tbody></table>`;
    const cov = a.coverage;
    const hold = `<table class="cio-tbl small"><thead><tr><th>Holding</th><th class="r">Value</th><th>How it is classified</th><th>CMA asset class</th></tr></thead><tbody>${a.holdings.map(h => `<tr class="${h.method === 'UNCLASSIFIED' || h.method === 'MARGIN_DEBIT' ? 'dim' : ''}">
      <td><b class="mono">${esc(h.sym)}</b><div class="sub">${esc(h.name)}</div></td><td class="r mono">${money(h.mv)}</td>
      <td class="sub">${esc(h.method_text)}${h.why ? ` <span class="cio-warn">${esc(h.why)}</span>` : ''}</td>
      <td>${Object.keys(h.classes).map(k => esc((CIOS.data.cma.classes.find(c => c.id === k) || {}).label || k)).join(', ') || '—'}</td></tr>`).join('')}</tbody></table>
      <div class="cio-note">Classified ${money(cov.covered_mv)} of ${money(cov.total_mv)} (${pct(cov.pct, 0)})${cov.margin_debit ? ` · margin debit ${money(cov.margin_debit)} reported separately` : ''}${cov.margin_credit ? ` · margin credit ${money(cov.margin_credit)} counted as cash` : ''}. Classifications from the ${dshort(CIOS.data.as_of.classifications)} snapshot; positions as of ${dshort(CIOS.data.as_of.positions)}.</div>`;
    const flags = a.flags.length ? `<ul class="cio-flags">${a.flags.map(f => `<li class="${f.severity}"><span class="cio-flag ${f.severity}">${f.severity === 'review' ? 'Review' : 'Note'}</span> ${esc(f.text)}</li>`).join('')}</ul>` : '';
    return `<div class="card cio-card" id="cioDetail"><div class="ch"><h3>${esc(a.name)} · ${esc(a.account_no)}</h3><span class="r sub">${esc(a.account_type)} · ${esc(a.fa || '')} · ${esc(a.market)}</span></div>
      <div class="cbp"><p class="cio-headline">${esc(a.headline)}</p>
        <h4 class="cio-h4">How the account maps to a CIO model</h4>${setup}
        <h4 class="cio-h4">Expected outcome vs the model, and actual performance</h4>${metrics}
        <p class="cio-note">Expected figures come from the same CMA returns, volatilities and correlations for both columns, so they compare like for like. Actual figures are realized history and aren’t comparable to expected ones.</p>
        ${flags ? `<h4 class="cio-h4">Worth checking</h4>${flags}` : ''}
        <h4 class="cio-h4">Allocation by CMA asset class: today vs the model</h4>${allocChart(a)}
        <h4 class="cio-h4">How each holding rolls up</h4>${hold}
        <div class="cio-actions"><button class="btn sm" data-client="${a.household_id}">Open client page</button><span class="u" data-ask="Compare ${esc(first(a.name))}'s account with its CIO model">Ask Atlas about ${esc(first(a.name))} ${typeof I !== 'undefined' ? I.arrow : ''}</span></div>
      </div></div>`;
  }

  async function view(){
    const v = document.getElementById('view');
    v.innerHTML = '<div class="empty" style="padding:32px;text-align:center;color:var(--muted)">Loading the CIO model comparison…</div>';
    let d; try{ d = await load(); }catch(e){ v.innerHTML = `<div class="empty" style="padding:32px;color:var(--red)">Couldn’t load the CIO model comparison: ${esc(e.message)}</div>`; return; }
    const accts = d.accounts, sel = accts.find(a => a.household_id === CIOS.sel);
    const g = d.cio_guidance;
    v.innerHTML = `<div class="cio">
      <div class="cli-head reveal" style="margin-bottom:12px"><div style="min-width:220px"><div class="eyebrow" style="margin-bottom:4px">CIO MODEL FIT</div>
        <div class="nm serif">Accounts against their CIO model</div>
        <div class="sub">${esc(d.scope.description)}. Expected outcome of what each client holds today vs the CIO strategic model for that client.</div></div>
        <div class="cio-meta"><span><b>${accts.length}</b> accounts</span><span>CIO targets ${dshort(g.targets_dated)} · ${esc(g.orientation)}, ${esc(g.tax_sensitivity.toLowerCase())} tax sensitivity</span><span>${esc(d.as_of.cma)} CMA · positions ${dshort(d.as_of.positions)}</span></div></div>
      ${accts.length ? `
      <div class="card cio-card"><div class="ch"><h3>Expected risk and return: today’s holdings vs the CIO model</h3></div><div class="cbp">${scatter(accts)}</div></div>
      <div class="card cio-card"><div class="ch"><h3>One row per account</h3><span class="r sub">sorted by Sharpe gap, widest first · click a row</span></div><div class="cbp">${table(accts)}</div></div>
      ${detail(sel)}` : `<div class="card"><div class="cbp">No brokerage accounts in this advisor’s book meet the filter (${esc(d.scope.description)}).</div></div>`}
      <details class="card cio-card cio-jc"><summary><b>How accounts are matched, and the judgment calls behind the numbers</b></summary><div class="cbp">
        <ul>${d.judgment_calls.map(j => `<li><b>${esc(j.title)}:</b> ${esc(j.text)}</li>`).join('')}<li><b>CIO guidance used:</b> ${esc(g.orientation)}, ${esc(g.tax_sensitivity)} Tax Sensitivity, strategic targets dated ${dshort(g.targets_dated)}. ${esc(g.note)}</li></ul>
        <p class="cio-note">${esc(d.note)} ${esc(d.cma.note)} Risk-free rate: the CMA cash return, ${pct(d.cma.risk_free)}.</p></div></details>
    </div>`;
  }

  /* ---------- hooks into the app ---------- */
  if(!NAVITEMS.some(n => n.k === 'ciofit')){
    const i = NAVITEMS.findIndex(n => n.k === 'tax');
    NAVITEMS.splice(i + 1, 0, {k:'ciofit', label:'CIO Model Fit', icon:(typeof I !== 'undefined' && I.cio) || ''});
    const tb = document.querySelector('#nav button[data-nav="tax"]');
    if(tb && !document.querySelector('#nav button[data-nav="ciofit"]')){ const b = document.createElement('button'); b.dataset.nav = 'ciofit'; tb.insertAdjacentElement('afterend', b); }
  }
  const _render = render;
  render = async function(){
    if(state.view !== 'ciofit') return _render.apply(this, arguments);
    state.focusHousehold = CIOS.sel || null; state.lastView = 'ciofit';
    paintNav();
    const cr = document.getElementById('crumb'); if(cr) cr.innerHTML = '<b>CIO Model Fit</b>';
    await view();
    if(typeof decorateView === 'function') decorateView();
  };
  if(typeof HOWTO !== 'undefined') HOWTO.ciofit = [
    ['Shows', 'Each brokerage account in the Bridgewater, NJ market over $50K next to the CIO strategic model it should map to.'],
    ['Calculated by', 'Expected return, risk and Sharpe from the 2026 CMA, for today’s holdings and for the model; actual figures from the performance system. No AI.'],
    ['Read it as', 'Coverage and flags tell you how far to trust a row. Click a row for the allocation gap, the roll-up and the judgment calls.']];
  if(typeof askPrompt === 'function'){
    const _ask = askPrompt;
    askPrompt = function(){
      if(state.view === 'ciofit'){ const a = CIOS.data && CIOS.data.accounts.find(x => x.household_id === CIOS.sel);
        return a ? `Compare ${first(a.name)}'s account with its CIO model` : 'Show the CIO model fit for my brokerage accounts'; }
      return _ask.apply(this, arguments);
    };
  }
  const _run = runAgentAction;
  runAgentAction = async function(a, q){
    if(a && a.workspace === 'cio_fit'){
      state.fromChat = {q: q || a.__q || '', view: 'ciofit'};
      if(a.household_id) CIOS.sel = a.household_id;
      await setView('ciofit');
      if(a.household_id) scrollToAnchor('cioDetail');
      return;
    }
    return _run.apply(this, arguments);
  };
  const pick = id => { CIOS.sel = id; state.focusHousehold = id; view().then(() => { if(typeof decorateView === 'function') decorateView(); scrollToAnchor('cioDetail'); }); };
  document.addEventListener('click', e => {
    if(state.view !== 'ciofit') return;
    const r = e.target.closest('[data-cio-acct]'); if(r){ e.stopPropagation(); pick(r.dataset.cioAcct); }
  }, true);
  document.addEventListener('keydown', e => {
    if(state.view !== 'ciofit' || (e.key !== 'Enter' && e.key !== ' ')) return;
    const r = e.target.closest && e.target.closest('[data-cio-acct]'); if(r){ e.preventDefault(); pick(r.dataset.cioAcct); }
  });
  if(typeof switchFa === 'function'){ const _sw = switchFa; switchFa = async function(){ CIOS.data = null; return _sw.apply(this, arguments); }; }

  /* ---------- Today dashboard: households on the "CIO alignment" tile open their CIO Model Fit row ---------- */
  const inScope = id => !!(CIOS.data && CIOS.data.accounts.some(a => a.household_id === id));
  if(typeof nbaCIO === 'function'){
    const _nb = nbaCIO;
    nbaCIO = function(){
      let html = _nb.apply(this, arguments);
      if(!CIOS.data) return html;
      return html.replace(/<button class="row" data-client="([^"]+)">([\s\S]*?)<\/button>/g, (m, id, inner) => !inScope(id) ? m
        : `<button class="row" data-cio-open="${id}" title="Open in CIO Model Fit">${inner.replace('<div class="right">', '<div class="right"><span class="cio-tag">vs CIO model</span>')}</button>`);
    };
  }
  const openFit = id => { CIOS.sel = id; state.fromChat = null; setView('ciofit'); scrollToAnchor('cioDetail'); };
  document.addEventListener('click', e => {
    const b = e.target.closest('[data-cio-open]'); if(b){ e.stopPropagation(); openFit(b.dataset.cioOpen); }
  }, true);
  // Load the comparison in the background so the tile knows which households are in it.
  const warm = async () => { try{ await load(); if(state.view === 'today') render(); }catch(e){} };
  warm();
  if(typeof switchFa === 'function'){ const _sw2 = switchFa; switchFa = async function(){ const r = await _sw2.apply(this, arguments); warm(); return r; }; }

  if(typeof TOOL_LABELS !== 'undefined') TOOL_LABELS.cio_model_fit = 'Compared accounts with their CIO models';
  if(typeof CHAT_GROUPS !== 'undefined' && !CHAT_GROUPS.some(g => g[0] === 'CIO model fit'))
    CHAT_GROUPS.splice(2, 0, ['CIO model fit', [['Show the CIO model fit for my brokerage accounts', 'CIO Model Fit'], ["Compare Montgomery's account with its CIO model", 'CIO Model Fit']]]);
  if(typeof CAPS !== 'undefined' && !CAPS.some(c => c.t === 'CIO model fit'))
    CAPS.splice(2, 0, {t:'CIO model fit', what:'Brokerage accounts next to the CIO strategic model each should map to: setup, actual performance, today’s allocation by CMA asset class, and expected return, risk and Sharpe of both.',
      ex:['Show the CIO model fit for my brokerage accounts', "Compare Montgomery's account with its CIO model"], opens:'CIO Model Fit',
      uses:'2026 CMA returns, volatilities and correlations; CIO strategic targets dated 1/7/2026; classification snapshot 8/28 and positions 8/31',
      limits:'Illustrative data. Unclassified holdings are left out (coverage shown); munis and EM debt are proxied; single stocks are priced as their asset class.'});
  if(typeof TOUR !== 'undefined' && !TOUR.some(s => s.view === 'ciofit')){
    const i = TOUR.findIndex(s => s.view === 'shelf');
    TOUR.splice(i >= 0 ? i : TOUR.length - 1, 0, {title:'Brokerage accounts against their CIO model', prompt:'Show the CIO model fit for my brokerage accounts', view:'ciofit',
      fallback: () => setView('ciofit'),
      text:'For each brokerage account, Atlas derives the investor profile and liquidity tier, picks the CIO strategic model, and compares the expected outcome of today’s holdings with that model, using the same 2026 capital market assumptions for both.',
      look:['The chart: each account’s holdings (circle) joined to its model (square)', 'Coverage: Fairbanks is only 62% classified, so read that row with care', 'Click a row: the allocation gap by asset class and how each holding rolls up']});
    const n = TOUR.filter(s => s.prompt).length, words = ['zero','one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen'];
    if(TOUR[0] && TOUR[0].text) TOUR[0].text = TOUR[0].text.replace(/runs \w+ real requests/, `runs ${words[n] || n} real requests`);
  }
  window.AtlasCio = {state: CIOS};
})();
