/* ================= COLLAPSIBLE SIDEBAR ================= */
const RAIL_KEY = 'atlas.rail.collapsed';
function setRailCollapsed(on, remember){
  document.getElementById('app').classList.toggle('rail-collapsed', on);
  const b = document.getElementById('railToggle');
  if(b){ const t = on ? 'Expand sidebar' : 'Collapse sidebar'; b.title = t + '  ['; b.setAttribute('aria-label', t); b.setAttribute('aria-expanded', String(!on)); }
  if(remember){ try{ localStorage.setItem(RAIL_KEY, on ? '1' : '0'); }catch(_){} }
}
function toggleRail(){ setRailCollapsed(!document.getElementById('app').classList.contains('rail-collapsed'), true); }
document.addEventListener('keydown', e => {   // "[" toggles the sidebar, except while typing
  if(e.key === '[' && !e.metaKey && !e.ctrlKey && !e.altKey && !/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) && !e.target.isContentEditable){ e.preventDefault(); toggleRail(); }
});
(function(){ let on = false; try{ on = localStorage.getItem(RAIL_KEY) === '1'; }catch(_){} setRailCollapsed(on, false); })();

/* ================= ROUTER ================= */
function setView(v, client=null){
  state.view = v; state.client = client;
  render();
  const view = document.getElementById('view'); if(view) view.scrollTop = 0;
  const main = document.querySelector('.main'); if(main) main.scrollTo({top:0});
}
async function render(){
  // Track which household the advisor is working on, so Ask Atlas can resolve
  // "this client" without the advisor retyping a name.
  if(state.view==='client' && state.client) state.focusHousehold = state.client;
  else if(state.view==='draftReview' && state.draftTarget) state.focusHousehold = state.draftTarget.householdId;
  else if(state.view==='transition' && state.transitionTarget) state.focusHousehold = state.transitionTarget.householdId;
  else if(state.view==='vehicleCompare' && state.compareTarget) state.focusHousehold = state.compareTarget.householdId;
  else if(state.view==='today' || state.view==='book') state.focusHousehold = null;
  if(state.view!=='chat') state.lastView = state.view;
  paintNav();
  const crumbs = {today:'Today', book:'Book of Business', chat:'Ask Atlas', tax:'Tax Overlay Desk', crosssell:'Cross-Sell Radar', shelf:'Product Shelf', guide:'Atlas Guide', client:'Book of Business', draftReview:'Book of Business', transition:'Book of Business', vehicleCompare:'Book of Business'};
  const cr = document.getElementById('crumb');
  if(state.view==='client') cr.innerHTML = `<span style="color:var(--muted)">Book of Business /</span> <b>${byId(state.client)?byId(state.client).name:''}</b>`;
  else if(state.view==='draftReview'){ const t=byId(state.draftTarget&&state.draftTarget.householdId); cr.innerHTML = `<span style="color:var(--muted)">Book of Business / ${t?t.name:''} /</span> <b>Draft</b>`; }
  else if(state.view==='transition'){ const t=byId(state.transitionTarget&&state.transitionTarget.householdId); cr.innerHTML = `<span style="color:var(--muted)">Book of Business / ${t?t.name:''} /</span> <b>Transition</b>`; }
  else if(state.view==='vehicleCompare'){ const t=byId(state.compareTarget&&state.compareTarget.householdId); cr.innerHTML = `<span style="color:var(--muted)">Book of Business / ${t?t.name:''} /</span> <b>Compare vehicles</b>`; }
  else cr.innerHTML = `<b>${crumbs[state.view]||'Today'}</b>`;
  const v = document.getElementById('view');
  if(state.view === 'today') v.innerHTML = viewToday();
  else if(state.view === 'book') v.innerHTML = viewBook();
  else if(state.view === 'chat'){ v.innerHTML = viewChat(); requestAnimationFrame(() => { scrollChat(); const ta = document.getElementById('chatInput'); if(ta) ta.focus(); }); }
  else if(state.view === 'tax') v.innerHTML = viewTax();
  else if(state.view === 'crosssell') v.innerHTML = viewCrossSell();
  else if(state.view === 'shelf') await viewShelf();
  else if(state.view === 'guide') v.innerHTML = viewGuide();
  else if(state.view === 'client'){ await viewClient(state.client); await loadConversion(state.client); }
  else if(state.view === 'draftReview') await viewDraftReview(state.draftTarget.householdId, state.draftTarget.kind);
  else if(state.view === 'transition') await viewTransition(state.transitionTarget.householdId, state.transitionTarget.offering);
  else if(state.view === 'vehicleCompare') await viewVehicleCompare(state.compareTarget.householdId, state.compareTarget.model, state.compareTarget.products, state.compareTarget.amount);
  decorateView();
}

async function switchFa(fa){
  state.fa = fa; state.client = null; state.view = 'today';
  await loadBook(); render(); paintFaProfile();
}

/* ================= EVENTS ================= */
document.addEventListener('click', e => {
  if(e.target.closest('#railToggle')){ toggleRail(); return; }
  if(e.target.closest('#tourBtn,[data-tour-start]')){ startTour(); return; }
  const convC = e.target.closest('[data-conv-cell]'); if(convC && CONV){ CONV.cell = CONV.cell === convC.dataset.convCell ? null : convC.dataset.convCell; CONV.strategy = convC.dataset.convCell.split('|')[1]; paintConversion(); return; }
  const convS = e.target.closest('[data-conv-strategy]'); if(convS && CONV){ CONV.strategy = convS.dataset.convStrategy; CONV.cell = null; paintConversion(); return; }
  const tn = e.target.closest('[data-tour]'); if(tn){ const k = tn.dataset.tour; if(k==='next') tourNext(); else if(k==='back') tourBack(); else endTour(); return; }
  const hd = e.target.closest('[data-howto-dismiss]'); if(hd){ dismissHowto(hd.dataset.howtoDismiss); return; }
  if(e.target.closest('[data-howto-reset]')){ try{ localStorage.removeItem(HOWTO_KEY); }catch(_){} render(); return; }
  if(e.target.closest('[data-nav],[data-client],[data-transition],[data-compare],[data-draft]')) state.fromChat = null;
  const ex = e.target.closest('[data-explain]'); if(ex){ e.stopPropagation(); showExplain(ex.dataset.client, ex.dataset.offering, ex); return; }
  const nav = e.target.closest('[data-nav]'); if(nav){ setView(nav.dataset.nav); return; }
  const dr = e.target.closest('[data-draft]'); if(dr){ const [hid,kind] = dr.dataset.draft.split(':'); openDraft(hid, kind||'meeting_prep'); return; }
  const tr = e.target.closest('[data-transition]'); if(tr){ const [hid,off] = tr.dataset.transition.split(':'); openTransition(hid, off); return; }
  const aa = e.target.closest('[data-agent-action]'); if(aa){ runAgentAction(AGENT_ACTIONS[aa.dataset.agentAction]); return; }
  const cc = e.target.closest('[data-clear-context]'); if(cc){ state.focusHousehold = null; paintChat(); return; }
  const ca = e.target.closest('[data-cmp-add]'); if(ca){ compareWithIds([...(state.compareCurrentIds||[]), ca.dataset.cmpAdd]); return; }
  const cr = e.target.closest('[data-cmp-remove]'); if(cr){ compareWithIds((state.compareCurrentIds||[]).filter(x=>x!==cr.dataset.cmpRemove)); return; }
  if(!e.target.closest('.ac-wrap')){ const m = document.getElementById('cmpMenu'); if(m) m.hidden = true; }
  const vc = e.target.closest('[data-compare]'); if(vc){ const [hid,model] = vc.dataset.compare.split(':'); openVehicleCompare(hid, model||null); return; }
  const pdf = e.target.closest('[data-pdf-url]'); if(pdf){ openPdfPreview(pdf.dataset.pdfUrl, pdf.dataset.pdfTitle); return; }
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


/* Factsheet PDFs, when embedded in this file, open from memory; without them "Preview PDF" says the factsheet isn't included. */
const ATLAS_PDFS = {};
(function(){
  const original = openPdfPreview, urls = {};
  openPdfPreview = function(url, title){
    const b64 = ATLAS_PDFS[url];
    if(!b64) return original('data:text/html;charset=utf-8,' + encodeURIComponent('<body style="margin:0;display:flex;align-items:center;justify-content:center;height:100vh;background:#f4f5f7;color:#3a3f47;font:14px/1.5 system-ui,sans-serif"><p style="max-width:420px;text-align:center;padding:24px">This factsheet isn\u2019t included in this copy of Atlas. The research match and its excerpt above come from the factsheet text.</p></body>'), title);
    if(!urls[url]) urls[url] = URL.createObjectURL(new Blob([Uint8Array.from(atob(b64), c => c.charCodeAt(0))], {type:'application/pdf'}));
    return original(urls[url], title);
  };
})();
/* Full details are included for the clients used in the tour, the prompts and the conversion map.
   Everyone is still listed in the book; opening anyone else shows a short note. */
const ATLAS_SCOPE = new Set(["brennan", "castellano", "fairbanks", "ferreira", "harlow", "henderson", "kaplan", "lindqvist", "montgomery", "okonkwo", "okoye"]);
function outOfScope(id){
  const c = byId(id), names = [...ATLAS_SCOPE].map(x => (byId(x) || {}).name).filter(Boolean);
  document.getElementById('view').innerHTML = `<div class="card" style="margin-top:8px"><div class="cbp" style="padding:28px">
    <h3 style="margin:0 0 8px">${esc(c ? c.name : 'This client')} isn\u2019t included in this file</h3>
    <p style="margin:0 0 14px;color:var(--fg-2);line-height:1.55;max-width:70ch">This standalone file carries full details only for the clients used in the guided tour, the suggested prompts and the conversion map: ${esc(names.join(', '))}. Everyone is still listed in the Book of Business. The full Atlas app has every client.</p>
    <span style="display:inline-flex;gap:8px;flex-wrap:wrap"><button class="btn sm" data-nav="book">Back to Book of Business</button><button class="btn sm primary" data-tour-start>Show me around</button></span></div></div>`;
}
(function(){
  const guard = (fn) => async function(id){ if(!ATLAS_SCOPE.has(id)) return outOfScope(id); return fn.apply(this, arguments); };
  viewClient = guard(viewClient); viewTransition = guard(viewTransition);
  viewVehicleCompare = guard(viewVehicleCompare); viewDraftReview = guard(viewDraftReview);
})();
