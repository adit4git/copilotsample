/* ================= VIEW: PRODUCT SHELF ================= */
function shelfFilters(){ return state.shelfFilters || (state.shelfFilters = {q:'', vehicle:'', sleeve:'', max_minimum:'', tlh:''}); }
let shelfSleeves = null, shelfTimer = null;
async function viewShelf(){
  const v = document.getElementById('view');
  if(!shelfSleeves){ try{ shelfSleeves = (await api('/api/products/sleeves')).sleeves; }catch(e){ shelfSleeves = []; } }
  const f = shelfFilters();
  state.shelfSelected = state.shelfSelected || new Set();
  const focus = state.focusHousehold && byId(state.focusHousehold) ? state.focusHousehold : '';
  const opt = (val, label, cur) => `<option value="${val}" ${String(cur)===String(val)?'selected':''}>${label}</option>`;
  v.innerHTML = `
  <div class="cli-head reveal" style="margin-bottom:0">
    <div style="min-width:200px">
      <div class="eyebrow" style="margin-bottom:4px">PRODUCT SHELF</div>
      <div class="nm serif">Every ETF, SMA and direct-indexing product</div>
      <div class="sub" style="color:var(--muted)">Filter the shelf, select products, and compare them for any client.</div>
    </div>
  </div>
  <div class="card" style="margin-top:16px">
    <div class="cbp shelf-filters">
      <div class="ac-wrap" style="flex:2 1 260px"><input id="shelfQ" class="ac-input" type="text" autocomplete="off" placeholder="Ticker, fund, manager or asset class\u2026" value="${esc(f.q||'')}"></div>
      <select id="shelfVehicle" class="shelf-sel">${opt('', 'All vehicles', f.vehicle)}${opt('ETF','ETFs',f.vehicle)}${opt('SMA','SMAs',f.vehicle)}${opt('DIRECT_INDEXING','Direct indexing / TEM SMS',f.vehicle)}${opt('ETF_MODEL','ETF models',f.vehicle)}${opt('FUND_MODEL','Fund models',f.vehicle)}</select>
      <select id="shelfSleeve" class="shelf-sel">${opt('', 'All sleeves', f.sleeve)}${shelfSleeves.map(s=>opt(s, s, f.sleeve)).join('')}</select>
      <select id="shelfMin" class="shelf-sel">${opt('', 'Any minimum', f.max_minimum)}${opt('0','No minimum',f.max_minimum)}${opt('100000','Up to $100K',f.max_minimum)}${opt('250000','Up to $250K',f.max_minimum)}</select>
      <label class="shelf-chk"><input id="shelfTlh" type="checkbox" ${f.tlh?'checked':''}> Tax-loss harvesting only</label>
    </div>
  </div>
  <div class="card" style="margin-top:14px">
    <div class="ch"><h3 id="shelfCount">Loading\u2026</h3>
      <span class="r shelf-compare">
        <select id="shelfHH" class="shelf-sel"><option value="">Compare for client\u2026</option>${myBook().map(c=>`<option value="${c.id}" ${c.id===focus?'selected':''}>${esc(c.name)}</option>`).join('')}</select>
        <button class="btn sm primary" id="shelfCompareBtn">Compare selected</button>
      </span>
    </div>
    <div class="cbp" style="padding:0;overflow-x:auto" id="shelfTable"></div>
  </div>`;
  const reload = () => loadShelfRows();
  document.getElementById('shelfQ').addEventListener('input', e => { f.q = e.target.value; clearTimeout(shelfTimer); shelfTimer = setTimeout(reload, 160); });
  document.getElementById('shelfVehicle').onchange = e => { f.vehicle = e.target.value; reload(); };
  document.getElementById('shelfSleeve').onchange = e => { f.sleeve = e.target.value; reload(); };
  document.getElementById('shelfMin').onchange = e => { f.max_minimum = e.target.value; reload(); };
  document.getElementById('shelfTlh').onchange = e => { f.tlh = e.target.checked ? 'true' : ''; reload(); };
  document.getElementById('shelfCompareBtn').onclick = () => {
    const hid = document.getElementById('shelfHH').value; const ids = [...state.shelfSelected];
    if(!hid){ document.getElementById('shelfHH').focus(); return; }
    if(!ids.length) return;
    openVehicleCompare(hid, null, ids);
  };
  await loadShelfRows();
}
async function loadShelfRows(){
  const f = shelfFilters(); const qs = new URLSearchParams({limit:'300'});
  if(f.q) qs.set('q', f.q); if(f.vehicle) qs.set('vehicle', f.vehicle); if(f.sleeve) qs.set('sleeve', f.sleeve);
  if(f.max_minimum !== '' && f.max_minimum !== undefined) qs.set('max_minimum', f.max_minimum); if(f.tlh) qs.set('tlh_capable', 'true');
  let rows = [], total = 0;
  try{ const res = await api(`/api/products/search?${qs.toString()}`); rows = res.results; total = res.total ?? rows.length; }catch(e){ rows = []; }
  const countText = () => `${total>rows.length?`Showing ${rows.length} of ${total} products \u2014 refine the filters to see the rest`:`${rows.length} product${rows.length===1?'':'s'}`}${sel.size?` \u00b7 ${sel.size} selected`:''}`;
  const sel = state.shelfSelected;
  const box = document.getElementById('shelfTable'); if(!box) return;
  document.getElementById('shelfCount').textContent = countText();
  box.innerHTML = rows.length ? `<table class="hh-tbl"><thead><tr><th></th><th>Product</th><th>Vehicle</th><th>Sleeve</th><th class="r">Fee</th><th class="r">Minimum</th><th>TLH</th><th>TEM overlays</th><th>Source</th><th>Client use</th></tr></thead><tbody>
    ${rows.map(p=>`<tr>
      <td><input type="checkbox" class="shelf-pick" data-pid="${p.product_id}" ${sel.has(p.product_id)?'checked':''} aria-label="Select ${esc(p.name)}"></td>
      <td><b>${esc(p.ticker || (p.vehicle==='SMA'?'SMA':'DI'))}</b><div class="sub" style="font-size:11.5px;max-width:300px">${esc(p.name)}</div></td>
      <td>${p.vehicle.replace('_',' ').toLowerCase()}</td>
      <td style="font-size:12.5px">${esc(p.sleeve)}</td>
      <td class="r mono" style="white-space:nowrap">${p.fee_bps!=null?p.fee_bps+' bps':'<span class="sub">in profile</span>'}</td>
      <td class="r mono" style="white-space:nowrap">${p.minimum ? fmtM(p.minimum) : '\u2014'}</td>
      <td>${p.tlh_capable?'<span class="chip eligible dot">Yes</span>':'<span class="chip na">No</span>'}</td>
      <td class="mono" style="font-size:12px">${p.tem_overlays&&p.tem_overlays.length?p.tem_overlays.join(', '):'<span class="sub">\u2014</span>'}</td>
      <td style="font-size:12.5px">${p.model_label ? esc(p.model_label) : (p.source&&/IAP Strategy Catalog/.test(p.source) ? '<span class="sub">IAP catalog</span>' : '<span class="sub">off-model</span>')}</td>
      <td>${p.client_presentable?'<span class="chip eligible dot">Presentable</span>':'<span class="pill amber">Not client-safe</span>'}</td>
    </tr>`).join('')}</tbody></table>`
    : `<div class="empty" style="padding:28px;text-align:center;color:var(--muted)">No products match these filters.</div>`;
  box.querySelectorAll('.shelf-pick').forEach(cb => cb.onchange = () => {
    cb.checked ? sel.add(cb.dataset.pid) : sel.delete(cb.dataset.pid);
    document.getElementById('shelfCount').textContent = countText();
  });
}
