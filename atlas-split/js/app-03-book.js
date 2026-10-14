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

  ${c.incoming_capital ? `<div class="card" style="margin-bottom:16px">
    <div class="cbp" style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">
      <div style="background:color-mix(in srgb, var(--brand) 12%, transparent);color:var(--brand);border-radius:var(--r-m);padding:8px 10px;flex-shrink:0">${I.give}</div>
      <div style="flex:1 1 260px">
        <div style="font-weight:600;font-size:13.5px">${fmtM(c.incoming_capital.amount)} incoming \u00b7 ${c.incoming_capital.likelihood} likelihood \u00b7 expected ${c.incoming_capital.expected_date}</div>
        <div class="sub" style="margin-top:2px">${c.incoming_capital.source}, ${c.incoming_capital.form}${c.current_model_id?` \u00b7 currently on ${c.current_model_id.replace('_',' ')} (${c.current_implementation})`:''}</div>
      </div>
      ${c.current_model_id ? `<span class="u" data-compare="${c.id}:${c.current_model_id}">Compare vehicles ${I.arrow}</span>` : ''}
    </div>
  </div>` : ''}

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
      <div class="ch"><h3>Next best actions for this household</h3><span class="r" style="display:flex;gap:8px;flex-wrap:wrap">${c.nextMeeting ? `<button class="btn sm primary" data-draft="${c.id}:meeting_prep">${I.chat} Draft meeting prep</button>` : ''}<button class="btn sm" data-compare="${c.id}:${c.current_model_id||''}">Compare vehicles</button><button class="btn sm" data-nav="chat">${I.chat} Ask Atlas about ${esc(c.name.split(' ')[0])}</button></span></div>
      <div class="cbp" style="display:flex;flex-direction:column;gap:9px">
        ${nbas.map(n=>`<div class="nba-mini"><div class="d" style="background:${n.col}"></div><div class="txt">${n.t}</div></div>`).join('')}
      </div>
    </div>

    <div id="convSlot"></div>
    <div class="grid2" style="margin-top:0">
      <div class="card">
        <div class="ch"><h3 id="eligibility">Program eligibility \u00b7 cross-sell</h3></div>
        <div class="cbp"><div class="elig-grid">
          ${programList(c).map(p => { const v = vFor(c.id, p.k); const dim = v && v.verdict==='INELIGIBLE'; const rs = verdictReason(v); const canModel = v && (v.verdict==='ELIGIBLE' || v.verdict==='NEEDS_REVIEW') && p.status!=='enrolled';
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
          ${((c.program||'IAP')==='MGI'?mgiOfferingList(c):overlayList(c)).map(p => { const v = vFor(c.id, p.k); const dim = v && v.verdict==='INELIGIBLE'; const rs = verdictReason(v); const canModel = v && (v.verdict==='ELIGIBLE' || v.verdict==='NEEDS_REVIEW') && p.status!=='enrolled';
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
