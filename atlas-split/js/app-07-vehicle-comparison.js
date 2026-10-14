/* ================= VIEW: VEHICLE COMPARISON WORKBENCH ================= */
async function openVehicleCompare(householdId, model=null, products=null, amount=null){
  state.view = 'vehicleCompare';
  state.compareTarget = {householdId, model: model||null, products: (products&&products.length)?products:null, amount: amount||null};
  await render();
  const main = document.querySelector('.main'); if(main) main.scrollTo({top:0});
}
const FLAG_LABELS = {hypothetical:'Not client-safe', basis:'Basis differs', minimum:'Below minimum', sleeves:'Different sleeve', noperf:'No published returns', nofee:'Fee in profile', pas:'PAS dual contract'};
function productChip(row){
  return `<span class="pchip" title="${esc(row.name)}"><b>${esc(row.ticker || row.vehicle.replace('_',' '))}</b><span class="pchip-n">${esc(row.name)}</span><button class="pchip-x" data-cmp-remove="${row.product_id}" aria-label="Remove ${esc(row.name)}">\u00d7</button></span>`;
}
function acMenuHtml(results){
  if(!results.length) return `<div class="ac-empty">No products match. Try a ticker (VOO), fund family (Vanguard), manager or asset class.</div>`;
  const inSel = new Set(state.compareCurrentIds||[]);
  return results.map(p=>`<button class="ac-item" data-cmp-add="${p.product_id}" ${inSel.has(p.product_id)?'disabled':''}>
    <span class="ac-t mono">${esc(p.ticker || (p.vehicle==='SMA'?'SMA':'DI'))}</span>
    <span class="ac-n">${esc(p.name)}<span class="ac-m">${esc(p.sleeve)} \u00b7 ${p.vehicle.replace('_',' ').toLowerCase()} \u00b7 ${p.fee_bps!=null?p.fee_bps+' bps':'fee in profile'}${p.tem_overlays&&p.tem_overlays.length?' \u00b7 TEM '+p.tem_overlays.join(''):''}${p.client_presentable?'':' \u00b7 not client-safe'}${inSel.has(p.product_id)?' \u00b7 already added':''}</span></span>
  </button>`).join('');
}
let acTimer = null;
function wireComparePicker(){
  const input = document.getElementById('cmpSearch'); const menu = document.getElementById('cmpMenu');
  if(!input || !menu) return;
  const run = async () => {
    const q = input.value.trim();
    if(!q){ menu.hidden = true; return; }
    try{
      const r = await api(`/api/products/search?q=${encodeURIComponent(q)}&limit=8`);
      if(input.value.trim() !== q) return;  // a newer keystroke superseded this request
      menu.innerHTML = acMenuHtml(r.results); menu.hidden = false;
    }catch(e){ menu.hidden = true; }
  };
  input.addEventListener('input', () => { clearTimeout(acTimer); acTimer = setTimeout(run, 140); });
  input.addEventListener('focus', () => { if(input.value.trim()) run(); });
  input.addEventListener('keydown', e => {
    if(e.key === 'Escape'){ menu.hidden = true; input.blur(); }
    if(e.key === 'Enter'){ e.preventDefault(); const first = menu.querySelector('.ac-item:not([disabled])'); if(first && !menu.hidden) first.click(); }
  });
  const amt = document.getElementById('cmpAmountApply');
  if(amt) amt.onclick = () => {
    const v = parseFloat(String(document.getElementById('cmpAmount').value).replace(/[$,\s]/g,''));
    if(v > 0){ const t = state.compareTarget; openVehicleCompare(t.householdId, t.model, state.compareCurrentIds, v); }
  };
}
function compareWithIds(ids){
  const t = state.compareTarget;
  if(!ids.length) return openVehicleCompare(t.householdId, t.model, null, t.amount);
  openVehicleCompare(t.householdId, null, ids, t.amount);
}
function contentFlagPill(flag){
  const map = { expired:['pill amber','Expired'], review:['pill amber','Needs review'], advisor_only:['pill','Advisor only'], required:['pill amber','Required'] };
  const [cls,label] = map[flag.severity] || ['pill', flag.severity];
  return `<span class="${cls}" title="${flag.message.replace(/"/g,'&quot;')}">${label}</span>`;
}
function contentRow(hit){
  const clickable = !!hit.pdf_url;
  return `<div class="row" ${clickable?`data-pdf-url="${hit.pdf_url}" data-pdf-title="${esc(hit.title)}"`:''} style="${clickable?'cursor:pointer':'cursor:default'};align-items:flex-start;gap:12px">
    <div style="flex-shrink:0;padding-top:2px">${I.chat}</div>
    <div style="min-width:0;flex:1">
      <div style="font-weight:600;font-size:13px">${esc(hit.title)}${hit.page?` <span class="mono" style="font-size:11px;color:var(--muted)">(p.${esc(String(hit.page))})</span>`:''}</div>
      <div class="sub" style="margin-top:3px;font-size:12px">${esc(hit.snippet).slice(0,180)}${hit.snippet.length>180?'\u2026':''}</div>
      ${hit.flags.length ? `<div style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap">${hit.flags.map(contentFlagPill).join('')}</div>` : ''}
      ${clickable ? `<div class="u" style="margin-top:7px;font-size:12px">Preview PDF (${hit.pages||'?'} pages) ${I.arrow}</div>` : ''}
    </div>
  </div>`;
}
function openPdfPreview(url, title){
  const existing = document.getElementById('pdfModalOverlay'); if(existing) existing.remove();
  const overlay = document.createElement('div');
  overlay.id = 'pdfModalOverlay';
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(15,18,24,.6);display:flex;align-items:center;justify-content:center;z-index:9999;padding:28px';
  overlay.innerHTML = `<div style="background:var(--paper);border-radius:var(--r-l);width:min(880px,100%);height:min(90vh,1000px);display:flex;flex-direction:column;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.35)">
    <div style="display:flex;align-items:center;gap:12px;padding:14px 18px;border-bottom:1px solid var(--line-2);flex-shrink:0">
      <div style="background:color-mix(in srgb, var(--brand) 12%, transparent);color:var(--brand);border-radius:var(--r-s);padding:6px 8px">${I.chat}</div>
      <div style="font-weight:600;font-size:14px;flex:1;min-width:0">${esc(title)}</div>
      <button class="btn sm" id="pdfModalClose">Close</button>
    </div>
    <iframe src="${url}" style="flex:1;border:none;width:100%;background:#525659"></iframe>
  </div>`;
  overlay.addEventListener('click', e => { if(e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
  document.getElementById('pdfModalClose').onclick = () => overlay.remove();
}
async function viewVehicleCompare(householdId, model, products, amount){
  const container = document.getElementById('view');
  container.innerHTML = '<div class="empty" style="padding:32px;text-align:center;color:var(--muted)">Comparing vehicles\u2026</div>';
  await ensureVerdicts(householdId);
  const c = byId(householdId);
  if(!c || c.advisor_id !== state.fa){ setView('book'); return; }
  const qs = new URLSearchParams();
  if(products && products.length) qs.set('products', products.join(','));
  else if(model) qs.set('model', model);
  if(amount) qs.set('amount', amount);
  let brief;
  try{ brief = await api(`/api/compare/${householdId}?${qs.toString()}`); }
  catch(e){ container.innerHTML = `<div class="empty" style="padding:32px;color:var(--red)">Could not build comparison: ${esc(e.message)}</div>`; return; }
  const cmp = brief.comparison;
  state.compareCurrentIds = cmp.implementations.map(r=>r.product_id);
  const vehicleRows = cmp.implementations.map(row => {
    const perf = row.performance;
    return `<tr>
      <td><b>${esc(row.ticker || row.vehicle.replace('_',' '))}</b><div class="sub" style="font-size:11.5px;max-width:280px">${esc(row.name)}</div></td>
      <td>${row.vehicle.replace('_',' ').toLowerCase()}<div class="sub" style="font-size:11px">${esc(row.sleeve)}</div></td>
      <td class="r mono">${row.fee_bps!=null?row.fee_bps+' bps<div class="sub" style="font-size:11px">'+fmt$(row.annual_fee_dollars)+'/yr</div>':'<span class="sub">per Strategy Profile</span>'}</td>
      <td class="r mono">${perf?(perf.returns['1y']*100).toFixed(1)+'% <span class="sub" style="font-size:11px">1y</span>':'<span class="sub">\u2014</span>'}</td>
      <td class="r mono">${perf?(perf.returns['3y']*100).toFixed(1)+'% <span class="sub" style="font-size:11px">3y ann.</span>':'<span class="sub">not published</span>'}</td>
      <td>${row.tlh_capable?'<span class="chip eligible dot">Yes</span>':'<span class="chip na">No</span>'}</td>
      <td>${row.flags.length ? row.flags.map(f=>`<span class="pill amber" title="${esc(f.message)}">${FLAG_LABELS[f.code]||'Review'}</span>`).join(' ') : '<span class="chip eligible dot">Clear</span>'}</td>
    </tr>`;
  }).join('');
  const bes = cmp.breakevens || [];
  const beCard = bes.length ? `<div class="card" style="margin-top:14px">
    <div class="ch"><h3>Fee premium vs. breakeven harvesting</h3><span class="r" style="font-size:12px;color:var(--muted)">vs. ${esc(bes[0].vs_product_name)}, the lowest-cost client-presentable ETF selected</span></div>
    <div class="cbp" style="padding:0">
      <table class="hh-tbl"><thead><tr><th>Tax-managed option</th><th class="r">Fee premium</th><th class="r">Breakeven harvest</th><th>Assessment</th></tr></thead><tbody>
      ${bes.map(b=>`<tr><td><b>${esc(b.product_name)}</b></td><td class="r mono">${b.fee_premium_bps} bps<div class="sub" style="font-size:11px">${fmt$(b.fee_premium_annual_dollars)}/yr</div></td>
        <td class="r mono">${(b.breakeven_harvest_needed_pct_of_assets*100).toFixed(2)}%<div class="sub" style="font-size:11px">${fmt$(b.breakeven_harvest_needed_annual_dollars)}/yr</div></td>
        <td style="font-size:12.5px;color:var(--fg-2)">${esc(b.assessment)}</td></tr>`).join('')}
      </tbody></table>
      <div class="sub" style="padding:10px 17px 13px;font-size:11.5px">Breakeven = fee premium \u00f7 23.8% blended rate. Typical first-year harvest range ${(bes[0].illustrative_typical_first_year_harvest_range_pct[0]*100).toFixed(1)}\u2013${(bes[0].illustrative_typical_first_year_harvest_range_pct[1]*100).toFixed(1)}% is illustrative, not a published figure.</div>
    </div>
  </div>` : `<div class="sub" style="margin-top:14px;padding:12px 14px;border:1px dashed var(--line);border-radius:var(--r-m);font-size:12.5px">Add a tax-managed option (SMA or direct indexing) and a client-presentable ETF to see the fee-premium breakeven.</div>`;
  const pickerCard = `<div class="card" style="margin-top:16px">
    <div class="ch"><h3>Vehicles in this comparison</h3><span class="r" style="font-size:12px;color:var(--muted)">${cmp.implementations.length} selected \u00b7 add any product from the shelf</span></div>
    <div class="cbp">
      <div class="pchips">${cmp.implementations.map(productChip).join('')}</div>
      <div class="cmp-controls">
        <div class="ac-wrap">
          <input id="cmpSearch" class="ac-input" type="text" autocomplete="off" placeholder="Add a product \u2014 ticker, fund, manager or asset class\u2026" aria-label="Search the product shelf">
          <div class="ac-menu" id="cmpMenu" hidden></div>
        </div>
        <label class="cmp-amt">Amount <input id="cmpAmount" type="text" value="${Math.round(cmp.amount).toLocaleString()}"></label>
        <button class="btn sm" id="cmpAmountApply">Recalculate</button>
        ${c.current_model_id && (products&&products.length) ? `<span class="u" data-compare="${c.id}:${c.current_model_id}" style="font-size:12px">Reset to ${esc(c.current_model_id.replace('_',' '))} ${I.arrow}</span>` : ''}
      </div>
    </div>
  </div>`;
  container.innerHTML = `
  <button class="backlink" data-client="${c.id}">${I.back} ${c.name}</button>
  <div class="cli-head reveal" style="margin-bottom:0">
    ${avatarEl(c)}
    <div style="min-width:200px">
      <div class="eyebrow" style="margin-bottom:4px">COMPARE VEHICLES</div>
      <div class="nm serif">${esc(cmp.model_label)}</div>
      <div class="sub" style="color:var(--muted)">${c.name}</div>
    </div>
    <div style="margin-left:auto;align-self:center;text-align:right">
      <div class="mono" style="font-size:20px;font-family:'Newsreader',serif">${fmtM(cmp.amount)}</div>
      <div class="sub">${c.incoming_capital && !amount ? 'incoming capital' : 'amount under consideration'}</div>
    </div>
  </div>
  ${pickerCard}
  <div class="card" style="margin-top:14px">
    <div class="ch"><h3>Implementation comparison</h3><span class="r" style="font-size:12px;color:var(--muted)">reference basis: ${esc(cmp.reference_basis||'')}, as of ${esc(cmp.reference_as_of||'')}</span></div>
    <div class="cbp" style="padding:0;overflow-x:auto">
      <table class="hh-tbl"><thead><tr><th>Product</th><th>Vehicle</th><th class="r">Fee</th><th class="r">Return</th><th class="r">Return</th><th>TLH</th><th>Flags</th></tr></thead>
      <tbody>${vehicleRows}</tbody></table>
    </div>
  </div>

  ${beCard}

  ${brief.switching_cost_note ? `<div style="margin-top:14px;padding:12px 14px;background:color-mix(in srgb, var(--blue) 8%, transparent);border-left:3px solid var(--blue);border-radius:6px;font-size:12.5px">${esc(brief.switching_cost_note)}${brief.switching_cost_basis?' '+esc(brief.switching_cost_basis):''} <span class="u" data-transition="${c.id}:${brief.switching_cost.offering}">View transition scenario ${I.arrow}</span></div>` : ''}

  <div class="card" style="margin-top:14px">
    <div class="ch"><h3>Client-approved content</h3><span class="r" style="font-size:12px;color:var(--muted)">${brief.client_content.length} document${brief.client_content.length===1?'':'s'}</span></div>
    <div class="cbp" style="padding:8px 17px">
      ${brief.content_gap
        ? `<div style="padding:12px;background:color-mix(in srgb, var(--amber) 10%, transparent);border-left:3px solid var(--amber);border-radius:6px;font-size:13px">${esc(brief.content_gap_message)}</div>`
        : brief.client_content.map(contentRow).join('')}
    </div>
  </div>

  ${brief.advisor_content.length ? `<div class="card" style="margin-top:14px">
    <div class="ch"><h3>Advisor-only context</h3><span class="r" style="font-size:12px;color:var(--muted)">not for client distribution</span></div>
    <div class="cbp" style="padding:8px 17px">${brief.advisor_content.map(contentRow).join('')}</div>
  </div>` : ''}

  <div style="margin-top:14px;font-size:11.5px;color:var(--muted);text-align:center;padding:14px">
    Content retrieval shown here uses catalog metadata and keyword matching over a seeded content set \u2014 a production deployment would call a real multimodal retrieval pipeline (e.g. Voyage embeddings for prose, ColPali for chart/table-heavy pages) over the full document corpus. Performance and fee figures are illustrative program data, not live pricing.
  </div>`;
  wireComparePicker();
}
