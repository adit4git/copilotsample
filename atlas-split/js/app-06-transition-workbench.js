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
    stage_buy: {label:'STAGE BUY', color:'var(--brand)'},
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
        ${s.offering === 'dca' ? `
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:20px;margin-bottom:14px">
          <div><div style="font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;font-weight:600">DCA Cash to deploy</div><div class="mono" style="font-size:20px;font-family:'Newsreader',serif">${ts.dca_cash_amount?fmtM(ts.dca_cash_amount):'\u2014'}</div></div>
          <div><div style="font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;font-weight:600">Schedule</div><div class="mono" style="font-size:20px;font-family:'Newsreader',serif">${ts.dca_schedule_months?ts.dca_schedule_months+' mo \u00b7 '+(ts.dca_frequency||'monthly'):'\u2014'}</div></div>
          <div><div style="font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;font-weight:600">Per contribution</div><div class="mono" style="font-size:20px;font-family:'Newsreader',serif">${(ts.dca_cash_amount&&ts.dca_schedule&&ts.dca_schedule.length)?fmtM(ts.dca_cash_amount/ts.dca_schedule.length)+' \u00d7 '+ts.dca_schedule.length:'\u2014'}</div></div>
        </div>
        ${ts.dca_schedule && ts.dca_schedule.length ? `<table class="hh-tbl" style="margin-bottom:12px"><thead><tr><th>Contribution</th><th class="r">Amount invested</th><th class="r">Cumulative</th></tr></thead><tbody>${(()=>{let cum=0; return ts.dca_schedule.map(row=>{cum+=row.amount; return `<tr><td>${row.month}</td><td class="r mono">${fmt$(row.amount)}</td><td class="r mono">${fmt$(cum)}</td></tr>`;}).join('');})()}</tbody></table>` : ''}
        ` : `
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:20px;margin-bottom:14px">
          <div><div style="font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;font-weight:600">Reallocated</div><div class="mono" style="font-size:20px;font-family:'Newsreader',serif">${fmtM(ts.sells_total)}</div></div>
          <div><div style="font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;font-weight:600">Realized gain</div><div class="mono" style="font-size:20px;font-family:'Newsreader',serif;color:${ts.realized_gain>0?'var(--gain)':'var(--fg)'}">${ts.realized_gain?fmtM(ts.realized_gain):'\u2014'}</div></div>
          <div><div style="font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;font-weight:600">Offset by harvest</div><div class="mono" style="font-size:20px;font-family:'Newsreader',serif;color:${ts.harvest_offset>0?'var(--loss)':'var(--fg)'}">${ts.harvest_offset?'\u2212'+fmtM(ts.harvest_offset):'\u2014'}</div></div>
          <div><div style="font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;font-weight:600">Net taxable</div><div class="mono" style="font-size:20px;font-family:'Newsreader',serif">${ts.net_taxable_gain?fmtM(ts.net_taxable_gain):'\u2014'}</div></div>
          <div><div style="font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;font-weight:600">Est. ongoing tax alpha</div><div class="mono" style="font-size:20px;font-family:'Newsreader',serif;color:var(--gain)">${ts.estimated_ongoing_annual_tax_alpha?'+'+fmtM(ts.estimated_ongoing_annual_tax_alpha)+'/yr':'\u2014'}</div></div>
        </div>
        `}
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
