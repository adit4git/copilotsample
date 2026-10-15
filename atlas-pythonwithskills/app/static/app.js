/* Atlas Advisor Console — client-side renderer for the Python port.
 * Fetches from /api/* (rule engine + household data lives in Python).
 * The HTML/CSS is a byte-faithful port of the original artifact; only
 * the data-loading paths are new.
 */
'use strict';

/* ================= ICONS (verbatim from original) ================= */
const I = {
  today:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0Z"/><path d="M12 7v5l3 2"/></svg>',
  book:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5V5.5Z"/><path d="M4 20.5A2.5 2.5 0 0 0 6.5 23H20"/><path d="M9 7h7M9 11h5"/></svg>',
  chat:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H8l-4 4V5a2 2 0 0 1 2-2h13a2 2 0 0 1 2 2v10Z"/><path d="M8 9h8M8 13h5"/></svg>',
  tax:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6h9M9 12h9M9 18h5"/><path d="M4.5 6h.01M4.5 12h.01M4.5 18h.01"/></svg>',
  cross:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m7 17 4-4 3 3 4-6"/><path d="M3 3v18h18"/></svg>',
  meet:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4.5" width="18" height="16" rx="2.5"/><path d="M8 3v3M16 3v3M3 10h18"/></svg>',
  drift:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9 2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>',
  cio:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19V5a2 2 0 0 1 2-2h9l5 5v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z"/><path d="M14 3v6h6M8 13h8M8 17h5"/></svg>',
  deep:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3M11 8v6M8 11h6"/></svg>',
  spark:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v3M12 18v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M3 12h3M18 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/></svg>',
  arrow:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
  back:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M11 6l-6 6 6 6"/></svg>',
  send:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7Z"/></svg>',
  sun:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2M12 20v2M4 12H2M22 12h-2M5 5l1.5 1.5M17.5 17.5 19 19M19 5l-1.5 1.5M6.5 17.5 5 19"/></svg>',
  moon:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/></svg>',
  bank:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10 12 4l9 6M5 10v9M19 10v9M9 10v9M15 10v9M3 21h18"/></svg>',
  trust:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 4 6v5c0 5 3.4 8 8 10 4.6-2 8-5 8-10V6l-8-3Z"/><path d="m9 12 2 2 4-4"/></svg>',
  alt:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m7 15 3-4 3 3 4-7"/></svg>',
  index:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>',
  lend:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v10M9.5 9a2.5 2 0 0 1 2.5-1.5c1.4 0 2.5.7 2.5 1.8 0 2.4-5 1.6-5 4 0 1.1 1.1 1.8 2.5 1.8A2.5 2 0 0 0 14.5 15"/></svg>',
  ins:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 4 6v5c0 5 3.4 8 8 10 4.6-2 8-5 8-10V6l-8-3Z"/></svg>',
  give:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.8 4.6a5.5 5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5 0 0 0 0-7.8Z"/></svg>',
  people:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5"/><path d="M16 5.2a3.2 3.2 0 0 1 0 5.6M21 20c0-2.6-1.4-4.4-3.5-5.1"/></svg>',
};

/* ================= HELPERS ================= */
const AV_COLORS = ['#0C5D51','#26548F','#6b4a9e','#9E5E12','#A2323E','#2f7d6b','#3a5a8c','#7a5aa0'];
function avColor(id){ let h=0; for(const c of id) h=(h*31+c.charCodeAt(0))>>>0; return AV_COLORS[h%AV_COLORS.length]; }
function initials(name){ return name.replace(/[^A-Za-z ]/g,'').split(' ').filter(Boolean).slice(0,2).map(w=>w[0]).join('').toUpperCase(); }
function avatarEl(c, cls=''){ return `<div class="avatar ${cls}" style="background:${avColor(c.id)}">${initials(c.name)}</div>`; }
function fmtM(n){ const a=Math.abs(n); if(a>=1e9) return '$'+(n/1e9).toFixed(2)+'B'; if(a>=1e6) return '$'+(n/1e6).toFixed(1)+'M'; if(a>=1e3) return '$'+Math.round(n/1e3)+'K'; return '$'+Math.round(n); }
function fmt$(n){ const s=n<0?'-':''; return s+'$'+Math.round(Math.abs(n)).toLocaleString('en-US'); }
function fmtSigned(n){ return (n>=0?'+':'−')+'$'+Math.round(Math.abs(n)).toLocaleString('en-US'); }
function pctOf(part,total){ return (part/total*100); }
function meetWhen(d){ return d===0?'Today':d===1?'Tomorrow':`In ${d} days`; }
const gl = h => h.cost==null ? 0 : h.mv - h.cost;
const clientGL = c => c.holdings.reduce((s,h)=>s+gl(h),0);
const clientHarvest = c => c.holdings.filter(h=>gl(h)<0).reduce((s,h)=>s+gl(h),0);
const TAX_RATE = 0.238;
const esc = s => String(s??'').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

async function api(path, opt){
  const r = await fetch(path, opt);
  if(!r.ok) throw new Error(await r.text());
  return r.json();
}

/* ================= STATE (client-side book cache) ================= */
let state = { view:'today', client:null, fa:'dana', meta:null, book:[], byId:{}, verdicts:{}, composition:{} };
let bookFilter = 'all';

function myBook(){ return state.book; }
function byId(id){ return state.byId[id]; }

async function loadBook(){
  state.book = await api(`/api/book?fa=${state.fa}`);
  state.byId = Object.fromEntries(state.book.map(c => [c.id, c]));
  state.verdicts = {};
  state.composition = {};
}

/* ================= NBA / METRIC HELPERS ================= */
function totalAUM(){ return myBook().reduce((s,c)=>s+c.aum,0); }
function totalRev(){ return myBook().reduce((s,c)=>s+c.rev,0); }
function totalHarvest(){ return myBook().reduce((s,c)=>s+Math.abs(clientHarvest(c)),0); }
function meetings(){ return myBook().filter(c=>c.nextMeeting).sort((a,b)=>a.nextMeeting.inDays-b.nextMeeting.inDays); }
function drifts(){ return myBook().filter(c=>(c.concentration||[]).length || Math.abs(c.current.cash-c.target.cash)>=12)
  .map(c=>{ const conc=(c.concentration||[])[0]; const breach = conc? conc.pct-conc.threshold : (c.current.cash-c.target.cash);
    const label = conc? conc.label : 'Cash drag'; const pct = conc? conc.pct : c.current.cash;
    return {c, label, pct, threshold: conc?conc.threshold:c.target.cash, breach};
  }).sort((a,b)=>b.breach-a.breach); }
function cioMisaligned(){ return myBook().filter(c=>c.cio.score!=='Low').sort((a,b)=>({High:3,Medium:2,Low:1}[b.cio.score]-{High:3,Medium:2,Low:1}[a.cio.score])); }
function topClients(){ return [...myBook()].sort((a,b)=>b.aum-a.aum).slice(0,4); }

async function ensureVerdicts(id){
  if(state.verdicts[id]) return state.verdicts[id];
  const rec = await api(`/api/household/${id}`);
  state.byId[id] = { ...state.byId[id], ...rec };
  state.verdicts[id] = rec.verdicts || {};
  return state.verdicts[id];
}
function vFor(id, off){ return (state.verdicts[id]||{})[off]; }

function crossSell(){ return myBook().flatMap(c=>programList(c).filter(p=>p.status==='eligible').map(p=>({c,p}))); }

/* ================= OFFERING LISTS ================= */
function offeringLabel(k){
  const meta = state.meta && state.meta.offerings; return (meta && meta[k]) || k;
}
function programList(c){
  const P=[
    ['privateBanking', I.bank], ['trustEstate', I.trust],
    ['alternatives', I.alt], ['directIndexing', I.index],
    ['lending', I.lend], ['insurance', I.ins]
  ];
  return P.map(([k,icon])=>({k, label: offeringLabel(k), icon, status:(c.programs||{})[k]}));
}
function overlayList(c){
  const O=[
    ['taxManagedSMA', I.tax],['qlhOverlay', I.tax],['dtlhOverlay', I.index],
    ['temSms', I.alt],['transition', I.alt],['dca', I.tax],['charitable', I.give]
  ];
  return O.map(([k,icon])=>({k, label: offeringLabel(k), icon,
    status:(c.overlays||{})[k]!==undefined?(c.overlays||{})[k]:null}));
}
function mgiOfferingList(c){
  const O=[['mgiTer', I.tax],['mgiQlh', I.tax],['mgiDtlh', I.index]];
  return O.map(([k,icon])=>({k, label: offeringLabel(k), icon, status:null}));
}

/* ================= VERDICT / STATUS RENDERING ================= */
function verdictPill(v){ if(!v) return '<span class="chip na">no rule</span>';
  const carve = v.scope_exclusions && v.scope_exclusions.length;
  if(v.verdict==='ELIGIBLE') return '<span class="chip eligible dot">Eligible'+(carve?'*':'')+'</span>';
  if(v.verdict==='CONDITIONAL') return '<span class="chip eligible dot">Conditional</span>';
  if(v.verdict==='NEEDS_REVIEW') return '<span class="pill amber">Needs review</span>';
  return '<span class="chip na">Ineligible</span>';
}
function verdictReason(v){ if(!v) return '';
  if(v.reasons && v.reasons.length) return v.reasons[0].message;
  if(v.scope_exclusions && v.scope_exclusions.length) return 'Carve-out: '+v.scope_exclusions[0].message;
  if(v.internal_only_reasons && v.internal_only_reasons.length) return '[FA-internal] '+v.internal_only_reasons[0].message;
  if(v.disclosures && v.disclosures.length) return v.disclosures[0].message;
  return '';
}
function statusChip(s){ return s==='enrolled'?'<span class="chip enrolled dot">Active</span>':s==='eligible'?'<span class="chip eligible dot">Eligible</span>':'<span class="chip na">N/A</span>'; }
function xinfoBtn(cid,off){ return `<button class="xinfo" data-explain data-client="${cid}" data-offering="${off}" title="Why this verdict?" aria-label="Explain verdict">i</button>`; }
function verdictCell(hh, off){ const v = vFor(hh.id, off); return verdictPill(v)+xinfoBtn(hh.id, off); }

/* ================= EXPLAIN POPOVER ================= */
function fmtSrc(source_doc){ if(!source_doc) return null;
  if(typeof source_doc==='string') return source_doc;
  return source_doc.map(s=>s.document_id+(s.pdf_page?' p.'+s.pdf_page:'')).join(' · ');
}
function _fmtVal(x, field){ if(typeof x==='boolean') return x?'true':'false'; if(x==null) return '\u2014 (unknown)';
  if(typeof x==='number'){ const money=/value|cash|advisory|pledgeable/i.test(field||''); return (money?'$':'')+Math.round(x).toLocaleString('en-US')+(/pct|_pct/i.test(field||'')?'%':''); }
  return String(x);
}
function closeExplain(){ const h=document.getElementById('xpopHost'); if(h) h.remove(); }
function _positionPop(pop, anchor){ if(window.innerWidth<=640) return;
  const r=anchor.getBoundingClientRect(), pw=pop.offsetWidth, ph=pop.offsetHeight;
  let left=r.left, top=r.bottom+8;
  if(left+pw>window.innerWidth-10) left=window.innerWidth-pw-10; if(left<10) left=10;
  if(top+ph>window.innerHeight-10) top=Math.max(10, r.top-ph-8);
  pop.style.left=(left+window.scrollX)+'px'; pop.style.top=(top+window.scrollY)+'px';
}
async function showExplain(cid, off, anchor){
  closeExplain();
  const hh = byId(cid); if(!hh) return;
  let v;
  try{ v = await api(`/api/verdict/${cid}/${off}`); } catch(e){ return; }
  const label = v.label || offeringLabel(off);
  const opSym = {EQ:'=', NEQ:'\u2260', IN:'\u2208', CONTAINS:'includes', GTE:'\u2265'};
  const fld = s => s.replace(/^account\.|^client\.|^fa\.|^target_strategy\.|^strategy\.|^transition\.|^scope\.|^policy\./,'').replace(/_/g,' ');
  const val = (x, f) => Array.isArray(x)?(x.length>5?x.slice(0,4).join(', ')+', \u2026+'+(x.length-4)+' more':x.join(', ')):_fmtVal(x, f);
  let rows = '';
  (v.trace||[]).forEach(t => {
    (t.inputs||[]).forEach(l => {
      const passed = l.passed !== undefined ? l.passed : t.passed;
      rows += `<tr class="${passed===false?'bad':passed===null?'unk':''}">
        <td>${fld(l.field)}</td><td class="v">${val(l.actual, l.field)}</td>
        <td class="t">${opSym[l.op]||l.op} ${val(l.expected!==undefined?l.expected:l.value, l.field)}</td>
        <td class="p">${passed===true?'<span class="ok">\u2713</span>':passed===false?'<span class="no">\u2717</span>':'<span class="unk">?</span>'}</td>
      </tr>`;
    });
  });
  const realReasons = (v.reasons||[]).filter(r=>!r.missing_fields);
  const reason = realReasons.length?`<div class="xreason bad">${[...new Set(realReasons.map(r=>r.message))].join(' ')}</div>`:'';
  const missing = v.missing_fields && v.missing_fields.length ? `<div class="xreason unk">Unresolved \u2014 missing or invalid: ${v.missing_fields.map(fld).join(', ')}. Per policy, unknown facts route to review rather than a silent approval or rejection.</div>` : '';
  const carve = (v.scope_exclusions||[]).map(s=>`<div class="xnote">\u25D1 ${s.message}${s.excluded_ids?' ('+s.excluded_ids.join(', ')+')':''}</div>`).join('');
  const disc = (v.disclosures||[]).map(d=>`<div class="xnote">\u00A7 ${d.message}</div>`).join('');
  const realInternal = [...new Set((v.internal_only_reasons||[]).filter(r=>!r.missing_fields).map(r=>r.message))];
  const faint = realInternal.map(m=>`<div class="xnote fa">FA-internal \u00B7 ${m}</div>`).join('');
  let prereq = '';
  if(v.prerequisite && v.prerequisite.internal_only_reasons && v.prerequisite.internal_only_reasons.length){
    prereq = v.prerequisite.internal_only_reasons.map(r=>`<div class="xnote fa">Prerequisite (IAP enrollment) \u00B7 ${r.message}</div>`).join('');
  } else if(v.prerequisite && v.prerequisite.verdict==='INELIGIBLE'){
    prereq = `<div class="xnote">Prerequisite (IAP enrollment) is not met for this account \u2014 ${(v.prerequisite.reasons||[]).map(r=>r.message).join(' ')}</div>`;
  }
  const srcs = [...new Set((v.trace||[]).map(t=>fmtSrc(t.source_doc)).filter(Boolean))];
  const skn = (v.trace||[]).filter(t=>t.skills && t.skills.length).map(t=>`<div class="xnote">\u2726 <span class="mono">${esc(t.rule_id)}</span> comes from a team skill${skTag(t.skills)}${t.passed===false?' \u2014 not met':''}</div>`).join('');
  const host = document.createElement('div'); host.className='xpop-back'; host.id='xpopHost';
  host.innerHTML = `<div class="xpop" role="dialog" aria-label="Eligibility explanation">
    <div class="xpop-h"><div class="xpop-t">${label}</div>${verdictPill(v)}</div>
    ${reason}${missing}
    <div class="xpop-sec">Inputs evaluated <span class="muted2">\u2014 derived fields the rules read</span></div>
    <div class="xtbl-wrap"><table class="xpop-tbl"><colgroup><col class="c1"><col class="c2"><col class="c3"><col class="c4"></colgroup><thead><tr><th>Derived field</th><th>Value</th><th>Test</th><th></th></tr></thead><tbody>${rows||'<tr><td colspan="4" class="muted2">No field predicates \u2014 this offering attaches only conditions/disclosures.</td></tr>'}</tbody></table></div>
    ${(carve||disc||faint||prereq||skn)?`<div class="xpop-sec">Notes</div>${skn}${carve}${disc}${faint}${prereq}`:''}
    ${srcs.length?`<div class="xsrc">source: ${srcs.join(' \u00B7 ')}</div>`:''}
    <button class="xpop-x" aria-label="Close">\u00D7</button>
  </div>`;
  document.body.appendChild(host);
  _positionPop(host.querySelector('.xpop'), anchor);
  host.addEventListener('click', e => { if(e.target===host || e.target.closest('.xpop-x')) closeExplain(); });
}

/* ================= COMPOSITION PANEL ================= */
function compositionVerdictPill(cv){
  const map={CONFIRMED_ELIGIBLE:['chip eligible dot','Confirmed eligible'],ELIGIBLE_WITH_CARVEOUT:['chip eligible dot','Eligible, scoped'],
    CONDITIONAL:['chip eligible dot','Conditional'],NEEDS_REVIEW:['pill amber','Needs review'],CONFIRMED_INELIGIBLE:['chip na','Confirmed ineligible']};
  const [cls,label]=map[cv]||['chip na',cv]; return `<span class="${cls}">${label}</span>`;
}
async function compositionPanelHtml(c){
  const cacheKey = c.id + '|TET';
  let composition = state.composition[cacheKey];
  if(!composition){
    try { composition = await api(`/api/composition/${c.id}?offerings=transition,taxManagedSMA,qlhOverlay,dtlhOverlay`); }
    catch(e){ return ''; }
    state.composition[cacheKey] = composition;
  }
  const ids = ['transition','taxManagedSMA','qlhOverlay','dtlhOverlay'];
  const rows = ids.map(id => { const v=vFor(c.id, id); const label=offeringLabel(id);
    return `<div class="elig"><div class="eic" style="background:var(--brand-tint);color:var(--brand)">${I.tax}</div>
      <div style="min-width:0"><div class="en">${label}</div></div><div class="est">${verdictPill(v)}</div></div>`;
  }).join('');
  const notes = (composition.notes||[]).map(n=>`<div class="xnote" style="margin-top:6px">${n.offerings?('<b>'+n.offerings.join(' + ')+':</b> '):''}${n.message}</div>`).join('');
  return `<div class="card" style="margin-top:16px">
    <div class="ch"><h3>TET-family service composition</h3>${compositionVerdictPill(composition.verdict)}</div>
    <div class="cbp">
      <div class="es" style="margin-bottom:10px;color:var(--muted)">Considered together as a set (TET, TER, QLH, DTLH) \u2014 composition is evaluated separately from each service's own eligibility, and an unspecified pairing is never assumed compatible.</div>
      <div class="elig-grid">${rows}</div>
      ${notes}
    </div>
  </div>`;
}

/* ================= NAV / TITLE ================= */
const NAVITEMS = [
  {k:'today', label:'Today', icon:I.today, badge:()=>meetings().filter(m=>m.nextMeeting.inDays<=5).length},
  {k:'book', label:'Book of Business', icon:I.book, badge:()=>myBook().length},
  {k:'chat', label:'Ask Atlas', icon:I.chat},
  {k:'tax', label:'Tax Overlay Desk', icon:I.tax},
  {k:'crosssell', label:'Cross-Sell Radar', icon:I.cross, badge:()=>crossSell().length},
  {k:'shelf', label:'Product Shelf', icon:I.index},
  {k:'guide', label:'Atlas Guide', icon:I.spark},
];

function paintNav(){
  const nav = document.getElementById('nav');
  nav.querySelectorAll('button[data-nav]').forEach(b => {
    const item = NAVITEMS.find(n => n.k === b.dataset.nav); if(!item) return;
    const on = state.view === b.dataset.nav || (b.dataset.nav === 'book' && ['client','draftReview','transition','vehicleCompare'].includes(state.view));
    b.className = on ? 'on' : '';
    b.title = item.label;
    const bv = item.badge ? item.badge() : ''; const badge = (bv !== '' && bv != null) ? `<span class="cnt">${bv}</span>` : '';
    b.innerHTML = `${item.icon}<span>${item.label}</span>${badge}`;
  });
  const mt = document.getElementById('mtabbar');
  mt.innerHTML = NAVITEMS.filter(n => n.mobile !== false).map(n => `<button data-nav="${n.k}" class="${state.view===n.k||(n.k==='book'&&['client','draftReview','transition','vehicleCompare'].includes(state.view))?'on':''}">${n.icon}<span>${n.label.split(' ')[0]}</span></button>`).join('');
}

function paintFaProfile(){
  const fa = state.meta && state.meta.advisors && state.meta.advisors[state.fa]; if(!fa) return;
  const av = document.getElementById('faAvatar'), who = document.getElementById('faWho'), sw = document.getElementById('faSwitch');
  if(av) av.textContent = fa.initials || initials(fa.name);
  if(who) who.textContent = fa.name;
  if(sw) sw.value = fa.id;
}
function paintEngineToggle(){
  const b = document.getElementById('engineToggle'); if(!b) return;
  b.innerHTML = `<span style="width:8px;height:8px;border-radius:50%;background:var(--brand);display:inline-block;margin-right:7px"></span>Rule engine ON`;
  b.setAttribute('aria-pressed','true');
}

/* ================= VIEW: TODAY ================= */
function viewToday(){
  const meetSoon = meetings().filter(m => m.nextMeeting.inDays <= 5).length;
  const brief = `You're managing <b>${fmtM(totalAUM())}</b> across <b>${myBook().length} households</b>. Today: <b>${meetSoon}</b> meetings need prep, <b>${drifts().length}</b> households are drifting on concentration or allocation, <b>${fmtM(totalHarvest())}</b> in losses are harvestable across <b>${myBook().filter(c=>Math.abs(clientHarvest(c))>10000).length}</b> accounts, and <b>${crossSell().length}</b> cross-sell openings are unactioned.`;
  const fa = state.meta && state.meta.advisors && state.meta.advisors[state.fa];
  const firstName = fa ? fa.name.split(' ')[0] : 'there';
  return `
  <div class="hero reveal">
    <div class="greet serif">Good morning, ${firstName}.</div>
    <div class="date">${new Date().toLocaleDateString('en-US',{weekday:'long', month:'long', day:'numeric'})} \u00b7 Book review</div>
    <div class="brief">${brief}</div>
    <div class="agentline"><span class="live"></span> Atlas prioritized your book at 6:00 AM \u00b7 <span class="u" data-nav="chat">Ask a question</span></div>
    <div class="stats">
      <div class="stat"><div class="k serif">${fmtM(totalAUM())}</div><div class="l">Total AUM</div></div>
      <div class="stat"><div class="k serif">${fmtM(totalRev())}</div><div class="l">Annualized revenue</div></div>
      <div class="stat"><div class="k serif">${meetSoon}</div><div class="l">Meetings this week</div></div>
      <div class="stat"><div class="k serif">${fmtM(totalHarvest()*TAX_RATE)}</div><div class="l">Est. tax alpha available</div></div>
    </div>
  </div>

  <div class="sect-h"><h2>Next best actions</h2><span class="n">Ranked by revenue impact & urgency</span></div>
  <div class="nba-grid">
    ${nbaMeetings()}
    ${nbaDrift()}
    ${nbaCIO()}
    ${nbaDeep()}
  </div>`;
}

function nbaMeetings(){
  const m = meetings();
  const rows = m.slice(0,4).map(c => {
    const mt = c.nextMeeting;
    return `<button class="row" data-client="${c.id}">
      ${avatarEl(c)}
      <div class="lead"><div class="nm">${c.name}</div>
        <div class="meta">${mt.type} \u00b7 ${c.segment}</div></div>
      <div class="right"><div class="fig">${meetWhen(mt.inDays)}</div><div class="figsub">${fmtM(c.aum)}</div></div>
    </button>`;
  }).join('') || `<div class="empty" style="padding:16px 4px;color:var(--muted);font-size:12.5px">Nothing on the calendar for this book right now.</div>`;
  return `<section class="nba acc-meet reveal" style="animation-delay:.04s">
    <div class="head"><div class="ic">${I.meet}</div>
      <div><div class="t">Meeting prep</div><div class="d">Upcoming client meetings</div></div>
      <div class="badge">${m.length} scheduled</div></div>
    <div class="body">${rows}</div>
    <div class="foot">Atlas drafts a prep brief for each ${m.length?`<span class="go" data-draft="${m[0].id}:meeting_prep">Draft with Atlas ${I.arrow}</span>`:`<span class="go" data-nav="chat">Draft with Atlas ${I.arrow}</span>`}</div>
  </section>`;
}
function nbaDrift(){
  const d = drifts();
  const rows = d.slice(0,4).map(x => {
    const w = Math.min(100, x.pct); const tw = Math.min(100, x.threshold);
    return `<button class="row" data-client="${x.c.id}">
      ${avatarEl(x.c)}
      <div class="lead"><div class="nm">${x.c.name}</div>
        <div class="meta">${x.label}</div>
        <div class="bar" style="margin-top:7px;width:150px"><i style="width:${w}%;background:var(--amber)"></i><span class="mini-th" style="left:${tw}%"></span></div>
      </div>
      <div class="right"><div class="fig" style="color:var(--amber)">${x.pct.toFixed(0)}%</div><div class="figsub">limit ${x.threshold}%</div></div>
    </button>`;
  }).join('') || `<div class="empty" style="padding:16px 4px;color:var(--muted);font-size:12.5px">No concentration or allocation breaches in this book right now.</div>`;
  return `<section class="nba acc-drift reveal" style="animation-delay:.08s">
    <div class="head"><div class="ic">${I.drift}</div>
      <div><div class="t">Concentration drift</div><div class="d">Positions breaching policy limits</div></div>
      <div class="badge">${d.length} flags</div></div>
    <div class="body">${rows}</div>
    <div class="foot">Marker shows policy threshold ${d.length?`<span class="go" data-client="${d[0].c.id}">Review top breach ${I.arrow}</span>`:'<span style="color:var(--muted)">Nothing to review</span>'}</div>
  </section>`;
}
function nbaCIO(){
  const cm = cioMisaligned();
  const rows = cm.slice(0,4).map(c => {
    const sc = c.cio.score;
    const pill = sc==='High'?'red':sc==='Medium'?'amber':'teal';
    return `<button class="row" data-client="${c.id}">
      ${avatarEl(c)}
      <div class="lead"><div class="nm">${c.name}</div>
        <div class="meta" style="white-space:normal">${c.cio.view}</div></div>
      <div class="right"><span class="pill ${pill}">${sc} drift</span></div>
    </button>`;
  }).join('') || `<div class="empty" style="padding:16px 4px;color:var(--muted);font-size:12.5px">Every portfolio in this book is aligned with current CIO guidance.</div>`;
  return `<section class="nba acc-cio reveal" style="animation-delay:.12s">
    <div class="head"><div class="ic">${I.cio}</div>
      <div><div class="t">CIO alignment</div><div class="d">Portfolios vs. house views & publications</div></div>
      <div class="badge">${cm.length} to review</div></div>
    <div class="body">${rows}</div>
    <div class="foot">Linked to this week's CIO desk notes ${cm.length?`<span class="go" data-client="${cm[0].id}">Open alignment ${I.arrow}</span>`:'<span style="color:var(--muted)">Nothing to review</span>'}</div>
  </section>`;
}
function nbaDeep(){
  const tc = topClients();
  const rows = tc.map((c,i) => {
    const g = clientGL(c);
    return `<button class="row" data-client="${c.id}">
      <div style="width:22px;text-align:center;font-family:'Newsreader',serif;font-size:15px;color:var(--muted)">${i+1}</div>
      ${avatarEl(c)}
      <div class="lead"><div class="nm">${c.name}</div>
        <div class="meta">${c.risk} \u00b7 YTD ${c.ytdReturn>0?'+':''}${c.ytdReturn}%</div></div>
      <div class="right"><div class="fig">${fmtM(c.aum)}</div><div class="figsub ${g>=0?'pos':'neg'}">${g>=0?'+':'\u2212'}${fmtM(Math.abs(g))} unreal.</div></div>
    </button>`;
  }).join('') || `<div class="empty" style="padding:16px 4px;color:var(--muted);font-size:12.5px">No households in this book yet.</div>`;
  return `<section class="nba acc-deep reveal" style="animation-delay:.16s">
    <div class="head"><div class="ic">${I.deep}</div>
      <div><div class="t">Top-client deep dives</div><div class="d">Your largest relationships by AUM</div></div>
      <div class="badge">Top ${tc.length}</div></div>
    <div class="body">${rows}</div>
    <div class="foot">Full holdings, tax lots & eligibility ${tc.length?`<span class="go" data-client="${tc[0].id}">Deep dive ${I.arrow}</span>`:'<span style="color:var(--muted)">No clients yet</span>'}</div>
  </section>`;
}

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

/* ================= VIEW: CHAT (Ask Atlas) ================= */
const CHAT_GROUPS = [
  ['Check eligibility', [['Is Okoye eligible for DTLH?','Eligibility screen'], ['What is Kaplan eligible for?','Eligibility screen']]],
  ['Convert to advisory', [["Open Montgomery's advisory conversion map",'Conversion map'], ["Open Brennan's advisory conversion map",'Conversion map']]],
  ['Model a transition', [['Model a tax efficient transition for Montgomery','Transition workbench'], ['Model a direct indexing transition for Henderson','Transition workbench']]],
  ['Compare vehicles', [["Compare vehicles for Henderson's $5M incoming capital",'Vehicle comparison'], ['Compare VOO, QQQ and the SMA for Henderson','Vehicle comparison']]],
  ['Phase in cash (DCA)', [['Model a DCA schedule for Harlow','DCA schedule'], ['Is Ferreira eligible for DCA?','Eligibility screen']]],
  ['Find opportunities', [['Where are my biggest tax-loss harvesting opportunities?','Tax Overlay Desk'], ['Show me cross-sell opportunities','Cross-Sell Radar']]],
  ['Prepare and explore', [['Prep me for my meeting with Kaplan','Meeting-prep draft'], ['Open the product shelf with SMAs with a minimum of 100K','Product Shelf']]],
];
function chatSuggestGroups(){
  const c = state.focusHousehold && byId(state.focusHousehold);
  if(!c) return CHAT_GROUPS;
  const first = c.name.split(' ')[0], items = [];
  if(c.incoming_capital) items.push([`Compare vehicles for ${first}'s ${fmtM(c.incoming_capital.amount)} incoming capital`, 'Vehicle comparison']);
  if(c.nextMeeting) items.push([`Prep me for my meeting with ${first}`, 'Meeting-prep draft']);
  if(c.concentration && c.concentration.length) items.push([`Model a tax efficient transition for ${first}`, 'Transition workbench']);
  items.push([`What is ${first} eligible for?`, 'Eligibility screen']);
  return [[`For ${c.name}`, items.slice(0, 3)]].concat(CHAT_GROUPS);
}
function suggestsBlock(){
  return `<div class="sg-wrap" id="suggests"><div class="sg-grid">${chatSuggestGroups().map(([g, items]) => `<div class="sg-group"><h5>${esc(g)}</h5>${items.map(([q, d]) => `<button class="sg-item" data-ask="${esc(q)}">${esc(q)}<span class="sg-dest">\u2192 ${esc(d)}</span></button>`).join('')}</div>`).join('')}</div>
    <div class="sg-foot"><button class="btn sm primary" data-tour-start>${I.spark} Show me around</button><span class="u" data-nav="guide">Everything Atlas can do ${I.arrow}</span></div></div>`;
}
let chatLog = [];
let sending = false;
let agentMode = null;
const AGENT_ACTIONS = {};

function chatContext(){
  const id = state.focusHousehold;
  return (id && byId(id)) ? {household_id:id, view:state.lastView||'client'} : null;
}
function viewChat(){
  if(chatLog.length===0){
    chatLog.push({role:'bot', html:true, content:
      `<p>I'm <strong>Atlas</strong>, your advisor copilot across all ${myBook().length} households in your book. I can screen eligibility, model tax-aware transitions, compare ETFs, SMAs and direct indexing from the full product shelf, surface cross-sell and harvesting opportunities, and draft meeting prep \u2014 then open the right workspace for you.</p><p>Ask in your own words, or pick a request below. New here? <span class="u" data-tour-start>Take the 4-minute tour</span> or open the <span class="u" data-nav="guide">Atlas guide</span>.</p>`});
  }
  const stream = chatLog.map(renderMsg).join('');
  const ctxTop = [...myBook()].sort((a,b)=>b.aum-a.aum).slice(0,5);
  const ctx = chatContext();
  const modeLabel = !agentMode ? 'Grounded on your live book'
    : agentMode.startsWith('live:') ? `Live agent \u00b7 ${esc(agentMode.slice(5))}` : 'Grounded planner \u00b7 no live model';
  return `<div class="chatwrap">
    <div class="chat">
      <div class="ch-head"><div class="mk">${I.chat}</div>
        <div><div class="t">Ask Atlas</div><div class="s"><span class="live"></span> ${modeLabel}</div></div>
      </div>
      ${ctx ? `<div class="ctx-bar">${I.people}<span>Working on <b>${esc(byId(ctx.household_id).name)}</b> \u2014 \u201cthis client\u201d refers to them</span><button class="ctx-x" data-clear-context aria-label="Clear client context">\u00d7</button></div>` : ''}
      <div class="stream" id="stream">${stream}${chatLog.some(m=>m.role==='user') ? '' : suggestsBlock()}</div>
      <div class="composer">
        <div class="inputrow">
          <textarea id="chatInput" rows="1" placeholder="Ask about any client, product, eligibility, transition or opportunity\u2026"></textarea>
          <button class="sendbtn" id="sendBtn" aria-label="Send" ${sending?'disabled':''}>${I.send}</button>
        </div>
      </div>
    </div>
    <aside class="ctx-panel">
      <div class="ctx-card"><h4>${I.people} Top relationships</h4>
        <div class="ctx-list">${ctxTop.map(c=>`<button data-client="${c.id}">${avatarEl(c)}<span style="min-width:0"><span style="display:block;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${c.name.split(' ')[0]} ${c.name.includes('Family')?'Family':c.name.split(' ')[1]||''}</span></span><span class="g">${fmtM(c.aum)}</span></button>`).join('')}</div>
      </div>
      <div class="ctx-card"><h4>${I.spark} Workspaces Atlas can open</h4><div style="margin:-2px 0 8px"><span class="u" data-nav="guide" style="font-size:12.5px">Open the Atlas guide ${I.arrow}</span></div>
        <div style="font-size:12.5px;color:var(--fg-2);line-height:1.65">
          Client profile \u00b7 eligibility screen \u00b7 transition workbench \u00b7 vehicle comparison \u00b7 Cross-Sell Radar \u00b7 Tax Overlay Desk \u00b7 meeting-prep draft review. Every figure comes from the rule engine and product shelf, never from the model.
        </div>
      </div>
    </aside>
  </div>`;
}
function renderMsg(m){
  if(m.role==='nav') return `<div class="nav-note">${I.arrow}<span>${esc(m.label)}</span></div>`;
  if(m.typing) return `<div class="msg bot" data-mid="${m.mid||''}"><div class="who">${I.chat}</div><div class="bubble"><span class="typing"><i></i><i></i><i></i></span></div></div>`;
  const body = m.html ? (m.content||'') : mdToHtml(m.content||'');
  const fa = state.meta && state.meta.advisors && state.meta.advisors[state.fa];
  const userInitials = fa ? (fa.initials || initials(fa.name)) : 'DW';
  let extra = '';
  if(m.steps && m.steps.length){
    extra += `<details class="trace"><summary>How Atlas worked this out \u00b7 ${m.steps.length} step${m.steps.length===1?'':'s'}</summary><ol>${m.steps.map(s=>`<li><b>${esc(TOOL_LABELS[s.tool]||s.tool)}</b> \u2014 ${esc(s.summary)}</li>`).join('')}</ol></details>`;
  }
  if(m.actions && m.actions.length){
    extra += `<div class="agent-actions">${m.actions.map((a,i)=>{ const key=(m.mid||'m')+'-'+i; AGENT_ACTIONS[key]=Object.assign(a,{__q:m.q});
      return `<button class="btn sm${i===0?' primary':''}" data-agent-action="${key}">${esc(a.label)} ${I.arrow}</button>`; }).join('')}</div>`;
  }
  return `<div class="msg ${m.role==='user'?'user':'bot'}"><div class="who">${m.role==='user'?userInitials:I.chat}</div><div class="bubble">${body}${extra}</div></div>`;
}
const WS_VIEW = {client:'client', eligibility:'client', transition:'transition', vehicle_compare:'vehicleCompare', cross_sell:'crosssell',
  product_shelf:'shelf', tax_desk:'tax', meeting_prep_draft:'draftReview', book:'book', today:'today', guide:'guide', conversion:'client'};
async function runAgentAction(a, q){
  if(!a) return;
  state.fromChat = {q: q || a.__q || '', view: WS_VIEW[a.workspace]};
  switch(a.workspace){
    case 'client': return setView('client', a.household_id);
    case 'eligibility': setView('client', a.household_id); return scrollToAnchor('eligibility');
    case 'transition': return openTransition(a.household_id, a.offering_id);
    case 'vehicle_compare': return openVehicleCompare(a.household_id, a.model_id, a.product_ids, a.amount);
    case 'cross_sell': return setView('crosssell');
    case 'product_shelf': state.shelfFilters = Object.assign({q:'', vehicle:'', sleeve:'', max_minimum:'', tlh:''}, Object.fromEntries(Object.entries(a.shelf_filters||{}).filter(([k,v])=>v!==null&&v!==undefined))); return setView('shelf');
    case 'tax_desk': return setView('tax');
    case 'meeting_prep_draft': return openDraft(a.household_id, 'meeting_prep');
    case 'book': return setView('book');
    case 'today': return setView('today');
    case 'guide': return setView('guide');
    case 'conversion': setView('client', a.household_id); return scrollToAnchor('conversion');
  }
}
function scrollToAnchor(id, tries=0){
  const el = document.getElementById(id);
  if(el){ el.scrollIntoView({behavior:'smooth', block:'start'}); return; }
  if(tries < 30) setTimeout(()=>scrollToAnchor(id, tries+1), 100);
}
function mdTableRow(ln){ return ln.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(c=>c.trim()); }
function mdToHtml(md){
  let s = esc(md);
  s = s.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/`(.+?)`/g,'<code>$1</code>');
  // Models sometimes separate table rows with blank lines; drop a blank line
  // that sits between two table rows so the table isn't split apart.
  const raw = s.split(/\n/), lines = [];
  raw.forEach((ln, i) => {
    if(ln.trim()===''){
      const prev = lines.length ? lines[lines.length-1] : '';
      const next = raw.slice(i+1).find(x => x.trim() !== '') || '';
      if(prev.trim().startsWith('|') && next.trim().startsWith('|')) return;
    }
    lines.push(ln);
  });
  let out=''; let inU=false, inO=false;
  for(let i=0; i<lines.length; i++){
    const ln = lines[i];
    // GitHub-style table: header row, a |---| separator row, then body rows.
    if(ln.trim().startsWith('|') && i+1 < lines.length && /^\s*\|?\s*:?-{2,}/.test(lines[i+1])){
      if(inU){out+='</ul>';inU=false;} if(inO){out+='</ol>';inO=false;}
      const head = mdTableRow(ln); let body = []; i += 2;
      while(i < lines.length && lines[i].trim().startsWith('|')){ body.push(mdTableRow(lines[i])); i++; }
      i--;
      out += `<div class="md-table"><table><thead><tr>${head.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${body.map(r=>`<tr>${r.map(c=>`<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
      continue;
    }
    if(/^\s*###\s+/.test(ln)){ if(inU){out+='</ul>';inU=false;} if(inO){out+='</ol>';inO=false;} out+='<h3>'+ln.replace(/^\s*###\s+/,'')+'</h3>'; continue; }
    if(/^\s*##\s+/.test(ln)){ if(inU){out+='</ul>';inU=false;} if(inO){out+='</ol>';inO=false;} out+='<h2>'+ln.replace(/^\s*##\s+/,'')+'</h2>'; continue; }
    if(/^\s*[-*]\s+/.test(ln)){ if(!inU){out+='<ul>';inU=true;} out+='<li>'+ln.replace(/^\s*[-*]\s+/,'')+'</li>'; continue; }
    if(/^\s*\d+\.\s+/.test(ln)){ if(!inO){out+='<ol>';inO=true;} out+='<li>'+ln.replace(/^\s*\d+\.\s+/,'')+'</li>'; continue; }
    if(inU){out+='</ul>';inU=false;} if(inO){out+='</ol>';inO=false;}
    if(ln.trim()==='') continue;
    out+='<p>'+ln+'</p>';
  }
  if(inU) out+='</ul>'; if(inO) out+='</ol>';
  return out;
}
function scrollChat(){ const m=document.getElementById('main'); if(m) m.scrollTop=m.scrollHeight; }
function paintChat(){ document.getElementById('view').innerHTML = viewChat(); scrollChat(); const ta=document.getElementById('chatInput'); if(ta) ta.focus(); }
function resCard(items){
  return `<div class="rescard">${items.map(it=>`<div class="rc-row" data-client="${it.c.id}">${avatarEl(it.c)}<div style="min-width:0"><div class="nm">${it.c.name}</div><div class="mt">${it.sub||it.c.segment}</div></div><div class="vv">${it.right||''}</div></div>`).join('')}</div>`;
}
async function sendChat(text){
  text = (text||'').trim(); if(!text || sending) return;
  sending = true;
  const btn = document.getElementById('sendBtn'); if(btn) btn.disabled = true;
  chatLog.push({role:'user', content:text});
  const sg = document.getElementById('suggests'); if(sg) sg.remove();
  const mid = 'm'+Date.now();
  chatLog.push({role:'bot', typing:true, mid});
  paintChat(); scrollChat();
  let autoAction = null;
  try{
    const history = chatLog.filter(m=>!m.typing && (m.role==='user'||(m.role==='bot'&&!m.html)))
      .slice(-9, -1).map(m=>({role:m.role==='user'?'user':'assistant', content:m.content||''}));
    const r = await api('/api/agent', {method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({fa:state.fa, message:text, history, context:chatContext()})});
    agentMode = r.mode;
    const i = chatLog.findIndex(m=>m.mid===mid);
    if(i>=0) chatLog[i] = {role:'bot', mid, q:text, content:r.content, steps:r.steps, actions:r.actions, mode:r.mode};
    autoAction = (r.actions||[]).find(a=>a.auto_open) || null;
  }catch(e){
    const i = chatLog.findIndex(m=>m.mid===mid);
    if(i>=0) chatLog[i] = {role:'bot', mid, content:'Sorry \u2014 I hit an error answering that. Please try again.'};
  }finally{
    sending = false;
    const b = document.getElementById('sendBtn'); if(b) b.disabled = false;
    paintChat(); scrollChat();
    // Only navigate automatically when the advisor explicitly asked to open
    // something; otherwise the action stays a button they choose to click.
    if(autoAction){
      const hh = autoAction.household_id && byId(autoAction.household_id);
      chatLog.push({role:'nav', label:'Opening ' + autoAction.label.replace(/^Open\s+/i,'').replace(/^the\s+/i,'') + (hh ? ' \u00b7 ' + hh.name : '') + '\u2026'});
      paintChat(); scrollChat();
      await new Promise(r => setTimeout(r, 1100));
      if(state.view==='chat') await runAgentAction(autoAction, text);
    }
  }
}

/* ================= VIEW: DRAFT REVIEW (human-in-the-loop) ================= */
const DRAFT_KIND_LABEL = {meeting_prep:'Meeting prep brief'};
function draftStatusPill(status){
  const map = {
    pending: ['pill amber', 'Awaiting your review'],
    approved: ['chip eligible dot', 'Approved'],
    declined: ['chip na', 'Declined'],
    edited_approved: ['chip eligible dot', 'Edited & approved'],
  };
  const [cls, label] = map[status] || ['chip na', status];
  return `<span class="${cls}">${label}</span>`;
}
async function openDraft(householdId, kind='meeting_prep'){
  state.view = 'draftReview'; state.draftTarget = {householdId, kind};
  render();
  const main = document.querySelector('.main'); if(main) main.scrollTo({top:0});
}
async function viewDraftReview(householdId, kind){
  const container = document.getElementById('view');
  container.innerHTML = '<div class="empty" style="padding:32px;text-align:center;color:var(--muted)">Atlas is drafting\u2026</div>';
  await ensureVerdicts(householdId);
  const c = byId(householdId);
  if(!c || c.advisor_id !== state.fa){ setView('book'); return; }
  let draft;
  try{
    draft = await api(`/api/draft/${householdId}`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({fa:state.fa, kind})});
  }catch(e){
    container.innerHTML = `<div class="empty" style="padding:32px;color:var(--red)">Could not generate draft: ${esc(e.message)}</div>`;
    return;
  }
  renderDraftReview(c, draft, kind, false);
}
function draftHouseholdToggle(activeId, kind){
  if(kind !== 'meeting_prep') return '';
  const m = meetings();
  if(m.length <= 1) return '';
  return `<div class="filters" style="margin-bottom:14px;align-items:center">
    <span style="font-size:12.5px;color:var(--muted)">Drafting meeting prep for</span>
    <select id="draftHouseholdSelect" style="font:inherit;font-size:13px;font-weight:600;color:var(--fg);background:var(--paper);border:1px solid var(--line);border-radius:9px;padding:7px 11px;box-shadow:var(--sh-1);cursor:pointer;max-width:360px">
      ${m.map(hh => `<option value="${hh.id}" ${hh.id===activeId?'selected':''}>${hh.name} \u00b7 ${meetWhen(hh.nextMeeting.inDays)}</option>`).join('')}
    </select>
  </div>`;
}
function renderDraftReview(c, draft, kind, editing){
  const container = document.getElementById('view');
  const kindLabel = DRAFT_KIND_LABEL[kind] || kind;
  const pending = draft.status === 'pending';
  container.innerHTML = `
  <button class="backlink" data-client="${c.id}">${I.back} ${c.name}</button>
  ${draftHouseholdToggle(c.id, kind)}
  <div class="cli-head reveal" style="margin-bottom:0">
    ${avatarEl(c)}
    <div style="min-width:200px">
      <div class="nm serif">${kindLabel}</div>
      <div class="sub">For ${c.name} \u00b7 drafted by Atlas \u00b7 human review required before it's used</div>
    </div>
    <div style="margin-left:auto;align-self:center">${draftStatusPill(draft.status)}</div>
  </div>

  <div class="card" style="margin-top:16px">
    <div class="ch"><h3>Proposed draft</h3><span class="r mono" style="font-size:11px;color:var(--muted)">${draft.mode==='model-drafted'?'grounded \u00b7 model-drafted':'grounded \u00b7 template'}</span></div>
    <div class="cbp">
      ${editing
        ? `<textarea id="draftEditArea" style="width:100%;min-height:380px;font:inherit;font-size:13.5px;line-height:1.6;border:1px solid var(--line);border-radius:var(--r-m);padding:14px;background:var(--paper-2);color:var(--fg);resize:vertical">${esc(draft.content)}</textarea>`
        : `<div class="bubble" style="max-width:none;background:transparent;border:none;padding:0">${mdToHtml(draft.content)}</div>`}
    </div>
  </div>

  <div class="card" style="margin-top:14px">
    <div class="cbp" style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
      ${editing ? `
        <button class="btn primary" id="draftSave">Save & approve</button>
        <button class="btn" id="draftCancelEdit">Cancel</button>
      ` : pending ? `
        <button class="btn primary" id="draftApprove">Approve</button>
        <button class="btn" id="draftEditBtn">Edit</button>
        <button class="btn" id="draftDecline" style="color:var(--red);border-color:color-mix(in srgb,var(--red) 40%,var(--line))">Decline</button>
        <span style="margin-left:auto;font-size:12px;color:var(--muted)">FA sign-off required \u2014 nothing is sent automatically.</span>
      ` : `
        <div style="font-size:13px;color:var(--fg-2)">${draft.status==='declined' ? 'Declined \u2014 no action taken.' : 'Ready to use.'}${draft.decided_at?(' Decided '+new Date(draft.decided_at).toLocaleString()+'.'):''}</div>
        <button class="btn" id="draftRegenerate" style="margin-left:auto">Draft again</button>
      `}
    </div>
  </div>`;

  const hhSelect = document.getElementById('draftHouseholdSelect');
  if(hhSelect) hhSelect.addEventListener('change', e => openDraft(e.target.value, kind));

  if(editing){
    document.getElementById('draftSave').onclick = async () => {
      const text = document.getElementById('draftEditArea').value;
      const updated = await api(`/api/draft/${c.id}/decision`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kind, action:'edit', edited_content:text, decided_by:state.fa})});
      renderDraftReview(c, updated, kind, false);
    };
    document.getElementById('draftCancelEdit').onclick = () => renderDraftReview(c, draft, kind, false);
  } else if(pending){
    document.getElementById('draftApprove').onclick = async () => {
      const updated = await api(`/api/draft/${c.id}/decision`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kind, action:'approve', decided_by:state.fa})});
      renderDraftReview(c, updated, kind, false);
    };
    document.getElementById('draftDecline').onclick = async () => {
      const updated = await api(`/api/draft/${c.id}/decision`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({kind, action:'decline', decided_by:state.fa})});
      renderDraftReview(c, updated, kind, false);
    };
    document.getElementById('draftEditBtn').onclick = () => renderDraftReview(c, draft, kind, true);
  } else {
    document.getElementById('draftRegenerate').onclick = () => viewDraftReview(c.id, kind);
  }
}

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
      <td style="font-size:12.5px">${p.model_label ? esc(p.model_label) : (p.source&&p.source.startsWith('MLIAP') ? '<span class="sub">MLIAP catalog</span>' : '<span class="sub">off-model</span>')}</td>
      <td>${p.client_presentable?'<span class="chip eligible dot">Presentable</span>':'<span class="pill amber">Not client-safe</span>'}</td>
    </tr>`).join('')}</tbody></table>`
    : `<div class="empty" style="padding:28px;text-align:center;color:var(--muted)">No products match these filters.</div>`;
  box.querySelectorAll('.shelf-pick').forEach(cb => cb.onchange = () => {
    cb.checked ? sel.add(cb.dataset.pid) : sel.delete(cb.dataset.pid);
    document.getElementById('shelfCount').textContent = countText();
  });
}

/* ================= BROKERAGE-TO-ADVISORY CONVERSION MAP ================= */
const CONV_OUTCOME = {
  HOLD: {label:'Held as-is', short:'Held', cls:'o-hold'}, SELL: {label:'Sold on entry', short:'Sold', cls:'o-sell'}, EXCHANGE: {label:'Share-class exchange', short:'Exchanged', cls:'o-exch'},
  MOVE_OUT: {label:'Stays in brokerage', short:'Stays out', cls:'o-out'}, REVIEW: {label:'Confirm', short:'Confirm', cls:'o-review'},
};
let CONV = null;
async function loadConversion(id){
  const slot = document.getElementById('convSlot'); if(!slot) return;
  let m; try{ m = await api(`/api/conversion/${id}?fa=${state.fa}`); }catch(e){ return; }
  if(!m.applicable){ slot.innerHTML = ''; return; }
  CONV = {data: m, strategy: (CONV && CONV.data.household_id === id && CONV.data.recommended === m.recommended && CONV.strategy) || m.recommended || m.most_held_as_is, cell: null};
  paintConversion();
}
function skTag(items){ return (items && items.length && window.AtlasSkills) ? ' ' + window.AtlasSkills.tag(items) : ''; }
function convSrc(docs){ return (docs || []).map(d => `IAP Brochure p.${d.pdf_page} \u2014 ${esc(d.section)}`).join('<br>'); }
function paintConversion(){
  const slot = document.getElementById('convSlot'); if(!slot || !CONV) return;
  const m = CONV.data, S = Object.fromEntries(m.strategies.map(s => [s.strategy, s])), sel = S[CONV.strategy];
  const head = `With a <b>${esc(sel.label)}</b>: ${fmtM(sel.hold_mv)} comes over as-is`
    + (sel.exchange_mv ? `, ${fmtM(sel.exchange_mv)} is exchanged into an eligible share class` : '')
    + (sel.sell_mv ? `, ${fmtM(sel.sell_mv)} is sold on entry (about ${fmtM(sel.realized_gain)} of gains, ~${fmtM(sel.est_tax)} tax at ${+(m.tax_rate*100).toFixed(2)}%${skTag((m.policy_skills||{}).tax_rate)}${sel.tet_stageable_gain ? `; TET can stage ${fmtM(sel.tet_stageable_gain)}` : ''})` : '')
    + (sel.move_out_mv ? `, ${fmtM(sel.move_out_mv)} stays in brokerage` : '')
    + (sel.review_mv ? `, ${fmtM(sel.review_mv)} needs confirming` : '') + '.';
  const gates = sel.gates.map(g => `<span class="conv-gate${g.blocking?' blocking':''}" title="${esc(g.rule_id)}">${g.blocking?'\u26d4':'\u2460'} ${esc(g.message)}</span>`).join('');
  const th = m.strategies.map(s => `<th class="conv-th${s.strategy===CONV.strategy?' sel':''}${s.available?'':' na'}" data-conv-strategy="${s.strategy}" title="${esc(s.authority)}">${esc(s.short)}${s.available?'':' <span class="sub">(not qualified)</span>'}</th>`).join('');
  const rows = m.holdings.map(h => `<tr><td><b class="mono">${esc(h.sym)}</b><div class="sub" style="font-size:11.5px">${esc(h.name)}</div><span class="conv-kind">${esc(h.kind_label)}${h.concentrated?' \u00b7 concentrated':''}</span></td>
      <td class="r mono">${fmtM(h.mv)}<div class="sub" style="font-size:11px">${h.weight}%</div></td>
      ${m.strategies.map(s => { const c = m.cells[`${h.sym}|${s.strategy}`], o = CONV_OUTCOME[c.outcome] || CONV_OUTCOME.REVIEW;
        const on = CONV.cell === `${h.sym}|${s.strategy}`;
        return `<td class="${s.strategy===CONV.strategy?'sel':''}"><button class="conv-cell ${o.cls}${on?' on':''}" data-conv-cell="${esc(h.sym)}|${s.strategy}" title="${o.label}">${o.short}${c.tet_stageable?'<span class="conv-tet">TET</span>':''}${c.assumption?'<span class="conv-asm">*</span>':''}</button></td>`; }).join('')}</tr>`).join('');
  const foot = (lbl, f) => `<tr class="conv-sum"><td colspan="2">${lbl}</td>${m.strategies.map(s => `<td class="r mono${s.strategy===CONV.strategy?' sel':''}">${f(s)}</td>`).join('')}</tr>`;
  let detail = `<div class="sub">Click any cell to see the rule behind it.</div>`;
  if(CONV.cell){
    const [sym, st] = CONV.cell.split('|'), c = m.cells[CONV.cell], h = m.holdings.find(x => x.sym === sym), o = CONV_OUTCOME[c.outcome] || CONV_OUTCOME.REVIEW;
    detail = `<div class="conv-dh"><b>${esc(h.name)}</b> under <b>${esc(S[st].label)}</b> <span class="conv-cell ${o.cls} static">${o.label}</span></div>
      <p>${esc(c.message)}</p>
      ${c.notes.map(n => `<p class="conv-note"><span class="mono">${esc(n.rule_id)}</span> ${esc(n.message)}${skTag(n.skills)}</p>`).join('')}
      ${c.realized_gain ? `<p class="conv-note">Realized gain if sold: <b>${fmt$(c.realized_gain)}</b> (~${fmt$(Math.round(c.realized_gain*m.tax_rate))} tax, illustrative).</p>` : ''}
      <div class="conv-src"><span class="mono">${esc(c.rule_id || 'no rule')}</span>${c.assumption ? ' \u00b7 <b>illustrative assumption</b>' : ''}${skTag(c.skills)}<br>${convSrc(c.source_doc)}</div>`;
  }
  slot.innerHTML = `<div class="card conv" style="margin-bottom:14px">
    <div class="ch"><h3 id="conversion">Brokerage \u2192 advisory conversion map</h3><span class="r" style="font-size:12px;color:var(--muted)">${fmt$(m.total_mv)} brokerage account \u00b7 rule-based</span></div>
    <div class="cbp">
      ${m.recommended ? `<p class="conv-rec">Atlas suggests starting from <b>${esc(S[m.recommended].label)}</b>: ${esc(m.recommend_reason)}${skTag((m.policy_skills||{}).recommend)}</p>` : ''}
      <p class="conv-headline">${head}</p>
      <div class="conv-gates">${gates}</div>
      <div class="conv-legend">${Object.values(CONV_OUTCOME).map(o => `<span class="conv-cell static ${o.cls}">${o.label}</span>`).join('')}<span class="sub">TET = sale the Tax Efficient Transition Service can stage \u00b7 * = illustrative assumption \u00b7 click a column to compare strategy types</span></div>
      <div style="overflow-x:auto"><table class="conv-tbl"><thead><tr><th>Holding</th><th class="r">Value</th>${th}</tr></thead><tbody>${rows}</tbody>
        <tfoot>${foot('Comes over without a sale', s => fmtM(s.hold_mv + s.exchange_mv))}${foot('Sold on entry', s => s.sell_mv ? fmtM(s.sell_mv) : '\u2014')}${foot('Gains realized', s => s.realized_gain ? fmtM(s.realized_gain) : '\u2014')}${foot('Stays in brokerage', s => s.move_out_mv ? fmtM(s.move_out_mv) : '\u2014')}</tfoot></table></div>
      <div class="conv-detail" id="convDetail">${detail}</div>
      <ul class="conv-notes">${m.notes.map(n => `<li>${esc(n.message)} <span class="sub">(IAP Brochure p.${n.source_doc[0].pdf_page})</span>${n.rule_id === 'CONV.note.high_cash' ? skTag((m.policy_skills||{}).high_cash) : skTag(n.skills)}</li>`).join('')}</ul>
    </div></div>`;
}

/* ================= ONBOARDING: guide, how-to panels, ask button, tour ================= */
const TOOL_LABELS = {
  search_households:'Looked up clients', get_household:'Read the client snapshot', check_eligibility:'Checked eligibility with the rule engine',
  find_cross_sell:'Screened cross-sell opportunities', rank_book:'Ranked your book', model_transition:'Modeled the transition',
  search_products:'Searched the product shelf', compare_vehicles:'Compared vehicles', search_content:'Searched approved content',
  open_workspace:'Prepared the workspace', advisory_conversion:'Mapped the brokerage-to-advisory conversion',
};

/* ---- "How this workspace works" panels (dismissible, remembered in this browser) ---- */
const HOWTO_KEY = 'atlas.howto.dismissed';
const HOWTO = {
  client: [['Shows','Holdings, allocation against target, next best actions, and an eligibility verdict for every offering.'],
           ['Calculated by','The rule engine. Click any verdict to see the rules behind it. No AI on this page.'],
           ['Next step','Use \u201cModel transition\u201d on an offering, or \u201cCompare vehicles\u201d for new money.']],
  transition: [['Shows','What it takes to move this client into the offering: gaps, proposed trades, gains and tax.'],
               ['Calculated by','Rules from the term sheets, applied to the client\u2019s holdings and cost basis. No AI.'],
               ['Read it as','Fix \u201crequired\u201d gaps first. Trades are proposals for review, not orders.']],
  dca: [['Shows','Whether the client can use dollar cost averaging, and the contribution schedule.'],
        ['Calculated by','The DCA term sheet: $3,000 minimum, 6-month maximum, cash-only funding. No AI.'],
        ['Next step','Funding must arrive within 60 days of enrolling; the first contribution within 2 weeks.']],
  vehicleCompare: [['Shows','The same money in different vehicles: annual fee, returns, flags and breakeven harvesting.'],
                   ['Calculated by','Shelf data and a fixed formula (fee difference \u00f7 23.8% tax rate). No AI.'],
                   ['Try','Add any product with the search box, remove chips, or change the amount and press Recalculate.']],
  shelf: [['Shows','All 1,157 products with minimums, fees and tax-overlay eligibility codes.'],
          ['Codes','D = dynamic tax-loss harvesting, Q = quarterly loss harvesting, T = tax-efficient rebalancing.'],
          ['Next step','Tick products, pick a client, and press Compare selected.']],
  tax: [['Shows','Households ranked by harvestable losses and illustrative tax value.'],
        ['Calculated by','Holdings and cost basis. No AI.'],
        ['Next step','Open a client to check which tax overlays they qualify for.']],
  crosssell: [['Shows','Offerings each client is eligible for but not yet enrolled in.'],
              ['Calculated by','Rule engine verdicts. No AI.'],
              ['Next step','Open a client to see the reasons and model the transition.']],
  draftReview: [['Shows','A meeting brief drafted for you.'],
                ['Written by','The AI, or a template when no AI is connected. Facts come from the household data.'],
                ['Your call','Approve, edit or decline. Nothing reaches the client without you.']],
};
function howtoDismissed(){ try{ return JSON.parse(localStorage.getItem(HOWTO_KEY) || '[]'); }catch(_){ return []; } }
function dismissHowto(k){
  try{ localStorage.setItem(HOWTO_KEY, JSON.stringify([...new Set(howtoDismissed().concat(k))])); }catch(_){}
  const el = document.querySelector(`.howto[data-howto="${k}"]`); if(el) el.remove();
}
function howtoKey(){
  if(state.view === 'transition' && state.transitionTarget && state.transitionTarget.offering === 'dca') return 'dca';
  return HOWTO[state.view] ? state.view : null;
}

/* ---- "Ask Atlas about this": a question about what's on screen ---- */
function askPrompt(){
  const name = id => (byId(id) || {}).name || 'this client';
  switch(state.view){
    case 'client': return `What is ${name(state.client)} eligible for, and what should I do next?`;
    case 'transition': { const t = state.transitionTarget || {};
      return t.offering === 'dca' ? `Explain this DCA schedule for ${name(t.householdId)}`
                                  : `Explain the gaps and trades in this ${offeringLabel(t.offering)} transition for ${name(t.householdId)}`; }
    case 'vehicleCompare': return `Explain this vehicle comparison and the breakeven for ${name((state.compareTarget || {}).householdId)}`;
    case 'shelf': return 'Find SMAs with a minimum of 100K';
    case 'tax': return 'Where are my biggest tax-loss harvesting opportunities?';
    case 'crosssell': return 'Show me cross-sell opportunities';
    case 'draftReview': return `What should I cover in the meeting with ${name((state.draftTarget || {}).householdId)}?`;
    case 'today': return 'What meetings do I have this week?';
    case 'book': return 'Who is breaching concentration limits?';
  }
  return null;
}

/* ---- applied after every render ---- */
function decorateView(){
  document.body.classList.toggle('touring', !!tourState);
  const v = document.getElementById('view'); if(!v || state.view === 'chat') return;
  let top = '';
  if(state.fromChat && state.fromChat.view === state.view){
    top += `<div class="from-chat">${I.chat}<span>Opened from Ask Atlas${state.fromChat.q ? ` \u2014 you asked \u201c${esc(state.fromChat.q)}\u201d` : ''}</span><button class="btn sm" data-nav="chat">Back to conversation</button></div>`;
  }
  const hk = howtoKey();
  if(hk && !howtoDismissed().includes(hk)){
    top += `<div class="howto" data-howto="${hk}"><div class="howto-h"><b>How this workspace works</b><button class="howto-x" data-howto-dismiss="${hk}">Got it</button></div>
      <dl>${HOWTO[hk].map(([k, val]) => `<dt>${esc(k)}</dt><dd>${esc(val)}</dd>`).join('')}</dl></div>`;
  }
  if(top) v.insertAdjacentHTML('afterbegin', top);
  const q = askPrompt();
  if(q) v.insertAdjacentHTML('beforeend', `<button class="ask-fab" data-ask="${esc(q)}">${I.chat} Ask Atlas about this</button>`);
}

/* ---- Atlas guide ---- */
const CAPS = [
  {t:'Eligibility and reasons', what:'A verdict for any of 17 offerings, with the reasons and the rule behind each.',
   ex:['Is Okoye eligible for DTLH?','What is Kaplan eligible for?'], opens:'Client page \u203a Program eligibility',
   uses:'Rule engine: 112 rules from the term sheets and program brochure, applied to client account facts',
   limits:'Missing client data shows as Needs review, never as eligible or ineligible.'},
  {t:'Brokerage-to-advisory conversion', what:'For a brokerage account not yet in the program: every holding against the six program strategy types, decided by brochure rules.',
   ex:["Open Montgomery's advisory conversion map","Open Fairbanks's advisory conversion map"], opens:'Client page \u203a Conversion map',
   uses:'Conversion rules from the program brochure (pp. 4\u201342), plus the TET and DCA rules',
   limits:'Assumes funds are on the program\u2019s approved list; the Excluded Asset example is an illustrative assumption.'},
  {t:'Transitions', what:'Gaps, proposed trades, realized gains and tax for moving a client into an offering.',
   ex:['Model a tax efficient transition for Montgomery','Model a direct indexing transition for Henderson'], opens:'Transition workbench',
   uses:'Holdings and cost basis; elections such as the TET annual gain budget',
   limits:'Proposals for review, not orders. Tax shown at an illustrative 23.8% rate.'},
  {t:'Phasing cash in (DCA)', what:'Checks dollar cost averaging eligibility and builds the contribution schedule.',
   ex:['Model a DCA schedule for Harlow','Is Ferreira eligible for DCA?'], opens:'Transition workbench (DCA)',
   uses:'DCA term sheet: $3,000 minimum, 6-month maximum, cash-only funding',
   limits:'The schedule can\u2019t change once set; uninvested cash still pays the advisory fee.'},
  {t:'Vehicle comparison', what:'ETF vs. SMA vs. direct indexing for new money: fees, flags and breakeven harvesting.',
   ex:["Compare vehicles for Henderson's $5M incoming capital",'Compare VOO, QQQ and the SMA for Henderson'], opens:'Vehicle comparison',
   uses:'Product shelf fees and returns; client-approved content',
   limits:'Each row assumes the full amount in that one vehicle; catalog products have no published returns.'},
  {t:'Product shelf', what:'Search and filter 1,157 products, then compare any of them for a client.',
   ex:['Open the product shelf with SMAs with a minimum of 100K','Find dividend ETFs'], opens:'Product Shelf',
   uses:'Strategy catalog (1,097 products) plus the research-model shelf',
   limits:'The catalog lists no Style Manager fees; those are in each Strategy Profile.'},
  {t:'Tax-loss harvesting', what:'Ranks your book by harvestable losses and shows what each overlay would do.',
   ex:['Where are my biggest tax-loss harvesting opportunities?'], opens:'Tax Overlay Desk',
   uses:'Holdings and cost basis; QLH 5% lot threshold; TER and DTLH rules',
   limits:'Illustrative tax value; wash sales across other accounts are not checked.'},
  {t:'Cross-sell', what:'Offerings each client is eligible for but not yet enrolled in.',
   ex:['Show me cross-sell opportunities','Any cross-sell for Okonkwo?'], opens:'Cross-Sell Radar',
   uses:'Rule engine verdicts across your book', limits:'Screens eligibility only; suitability is the advisor\u2019s call.'},
  {t:'Meeting prep', what:'Drafts a meeting brief for you to approve, edit or decline.',
   ex:['Prep me for my meeting with Kaplan'], opens:'Meeting-prep draft review',
   uses:'Household data; AI-written text, or a template when no AI is connected', limits:'Nothing is sent to a client; you review every draft.'},
  {t:'Your book at a glance', what:'Meetings, concentration breaches, house-view drift and largest relationships.',
   ex:['What meetings do I have this week?','Who is breaching concentration limits?'], opens:'Answered in chat; Today and Book of Business',
   uses:'Household data and the CIO house view', limits:'Covers your own book only.'},
];
function viewGuide(){
  const steps = [['1','Ask','Type a request or pick one below. Name a client, or open their page first and say \u201cthis client\u201d.'],
                 ['2','Atlas works it out','It checks eligibility rules, product data and holdings. \u201cHow Atlas worked this out\u201d lists each step.'],
                 ['3','It opens the workspace','Requests to compare, model, draft or open something go straight there. \u201cBack to conversation\u201d returns you.']];
  return `<div class="cli-head reveal" style="margin-bottom:0">
    <div style="min-width:220px"><div class="eyebrow" style="margin-bottom:4px">ATLAS GUIDE</div><div class="nm serif">What Atlas can do</div>
      <div class="sub" style="color:var(--muted)">Ask in plain words. Atlas checks the rules and your clients\u2019 data, answers, and opens the workspace that does the work.</div></div>
    <div style="margin-left:auto;align-self:center;display:flex;gap:8px;flex-wrap:wrap"><button class="btn primary" data-tour-start>${I.spark} Take the 4-minute tour</button><button class="btn" data-nav="chat">${I.chat} Open Ask Atlas</button></div>
  </div>
  <div class="how-steps">${steps.map(([n, t, d]) => `<div class="how-step"><span class="how-n">${n}</span><div><b>${t}</b><p>${d}</p></div></div>`).join('')}</div>
  <div class="ai-boundary">${I.spark}<div><b>Where the AI is used, and where it isn\u2019t.</b> The AI decides which checks to run and writes the wording. Every eligibility verdict, number, fee and trade comes from the rule engine and your data. With no AI connected, Atlas still handles the requests below.</div></div>
  <h3 class="guide-h">Capabilities</h3>
  <div class="cap-grid">${CAPS.map(c => `<div class="cap-card"><h4>${esc(c.t)}</h4><p class="cap-what">${esc(c.what)}</p>
    <div class="cap-ex">${c.ex.map(q => `<button class="chip-ask" data-ask="${esc(q)}">${esc(q)}</button>`).join('')}</div>
    <dl class="cap-meta"><dt>Opens</dt><dd>${esc(c.opens)}</dd><dt>Uses</dt><dd>${esc(c.uses)}</dd><dt>Limits</dt><dd>${esc(c.limits)}</dd></dl></div>`).join('')}</div>
  <div class="guide-foot">Every workspace has an <b>Ask Atlas about this</b> button and a short <b>How this workspace works</b> panel. <span class="u" data-howto-reset>Show those panels again</span></div>`;
}

/* ---- Guided tour: every step sends a real request through Ask Atlas ---- */
const sleep = ms => new Promise(r => setTimeout(r, ms));
const TOUR = [
  {title:'Welcome to Atlas', go: () => setView('today'),
   text:'Atlas is an advisor console with an AI chat on top. You ask in plain words; Atlas checks the rule engine and your clients\u2019 data, answers, and opens the workspace that does the work. This tour runs nine real requests through the chat.',
   look:['Each step types a request into Ask Atlas', 'Watch for the \u201cOpening\u2026\u201d note and the \u201cOpened from Ask Atlas\u201d banner']},
  {title:'Brokerage to advisory: what happens to each holding', prompt:"Open Montgomery's advisory conversion map", view:'client', anchor:'conversion',
   fallback: () => setView('client', 'montgomery'),
   text:'Montgomery\u2019s $3.25M brokerage account isn\u2019t in the advisory program yet. The map shows each holding against all six program strategy types: what comes over as-is, what is sold or exchanged, and what has to stay in brokerage. Every cell comes from a brochure rule.',
   look:['Personalized and Defined strategies keep the stocks; a Managed Strategy sells them, and TET can stage the gains', 'The Class A fund is exchanged into an eligible share class', 'Click any cell to see the rule and brochure page; click a column to compare strategy types']},
  {title:'If he picks a Managed Strategy: staging the gains', prompt:'Model a tax efficient transition for Montgomery', view:'transition',
   fallback: () => openTransition('montgomery', 'transition'),
   text:'A Managed Strategy would sell the Costco position and the other stocks on entry. Atlas models a Tax Efficient Transition that spreads those gains over several years against his annual budget.',
   look:['The first gap: advisory program enrollment is required first', 'Sales staged year by year against a $50K annual gain budget']},
  {title:'$5M of new money: which vehicle?', prompt:"Compare vehicles for Henderson's $5M incoming capital", view:'vehicleCompare',
   fallback: () => openVehicleCompare('henderson', 'research_growth', null, 5000000),
   text:'Henderson expects $5M from a business sale. Atlas compares the SMA, ETFs and direct indexing for the full amount.',
   look:['The annual fee in dollars for each vehicle', 'Breakeven: how much loss harvesting pays for a higher fee', 'Client-approved factsheets you can preview']},
  {title:'Phasing cash in with dollar cost averaging', prompt:'Model a DCA schedule for Harlow', view:'transition',
   fallback: () => openTransition('harlow', 'dca'),
   text:'Harlow has $600K in cash and is nervous about investing it all at once. Atlas checks DCA eligibility and builds the schedule.',
   look:['Six monthly contributions of $100K', 'Uninvested DCA cash still pays the advisory fee']},
  {title:'Catching a DCA request the rules don\u2019t allow', prompt:'Is Ferreira eligible for DCA? Open her eligibility screen', view:'client', anchor:'eligibility',
   fallback: () => setView('client', 'ferreira'),
   text:'Ferreira wants a 12-month schedule funded from a money market fund. Both break the DCA term sheet, and Atlas says why before anything is set up.',
   look:['DCA ineligible, with two reasons: the 6-month maximum and cash-only funding']},
  {title:'Eligibility that comes from the product catalog', prompt:'Is Okoye eligible for DTLH? Open his eligibility screen', view:'client', anchor:'eligibility',
   fallback: () => setView('client', 'okoye'),
   text:'Okoye\u2019s ClearBridge SMA is coded for QLH and TER in the strategy catalog, but not for DTLH.',
   look:['DTLH ineligible: only CIO ETF strategies qualify', 'TER and QLH eligible on the same account']},
  {title:'Rules about the client, not only the product', prompt:'Is Lindqvist eligible for QLH? Open her eligibility screen', view:'client', anchor:'eligibility',
   fallback: () => setView('client', 'lindqvist'),
   text:'Lindqvist\u2019s strategy qualifies for every tax overlay, but she now lives in Sweden. Tax overlays are available to U.S. residents only.',
   look:['Every tax overlay ineligible for one reason: residency']},
  {title:'Services that interact', prompt:'Is Castellano eligible for direct indexing? Open his eligibility screen', view:'client', anchor:'eligibility',
   fallback: () => setView('client', 'castellano'),
   text:'Castellano has QLH and DTLH on a Custom Managed account and is asking about direct indexing.',
   look:['Direct indexing ineligible: not available inside a Custom Managed Strategy', 'Combination note: DTLH supersedes QLH on CIO ETF models']},
  {title:'The full product shelf', prompt:'Open the product shelf with SMAs with a minimum of 100K', view:'shelf',
   fallback: () => { state.shelfFilters = {q:'', vehicle:'SMA', sleeve:'', max_minimum:'100000', tlh:''}; setView('shelf'); },
   text:'1,157 products, including 1,097 from the strategy catalog, filtered by Atlas to SMAs with minimums up to $100K.',
   look:['Filters already applied from your request', 'Tick products, pick a client, and compare them']},
  {title:'Where to go from here', go: () => setView('guide'),
   text:'This guide lists everything Atlas can do, with example requests you can click. On any screen, \u201cAsk Atlas about this\u201d starts a question about what you\u2019re looking at, and each workspace has a short \u201cHow this workspace works\u201d panel.',
   look:['Click any example to try it', 'Restart the tour from \u201cShow me around\u201d in the top bar']},
];
let tourState = null;
function startTour(){ tourGo(0); }
function endTour(){ tourState = null; paintTour(); document.body.classList.remove('touring'); }
function tourNext(){ if(tourState && !tourState.busy){ if(tourState.i < TOUR.length - 1) tourGo(tourState.i + 1); else endTour(); } }
function tourBack(){ if(tourState && !tourState.busy && tourState.i > 0) tourGo(tourState.i - 1); }
async function tourGo(i){
  const s = TOUR[i];
  tourState = {i, busy: true}; document.body.classList.add('touring'); paintTour();
  try{
    if(s.prompt){
      if(state.view !== 'chat') setView('chat');
      await sleep(400);
      await sendChat(s.prompt);
      await sleep(300);
      if(state.view === 'chat' && s.fallback){ state.fromChat = {q: s.prompt, view: s.view}; await s.fallback(); }
    } else if(s.go){ await s.go(); }
    await sleep(700);
    if(s.anchor) scrollToAnchor(s.anchor);
  } finally {
    if(tourState && tourState.i === i){ tourState.busy = false; paintTour(); }
  }
}
function paintTour(){
  let p = document.getElementById('tourPanel');
  if(!tourState){ if(p) p.remove(); return; }
  if(!p){ p = document.createElement('div'); p.id = 'tourPanel'; p.setAttribute('role', 'dialog'); p.setAttribute('aria-label', 'Guided tour'); document.body.appendChild(p); }
  const s = TOUR[tourState.i], n = TOUR.length, last = tourState.i === n - 1, busy = tourState.busy;
  p.innerHTML = `<div class="tour-top"><span>Guided tour \u00b7 ${tourState.i + 1} of ${n}</span><button class="tour-x" data-tour="exit" aria-label="Exit tour">\u00d7</button></div>
    <div class="tour-bar"><i style="width:${Math.round((tourState.i + 1) / n * 100)}%"></i></div>
    <h4>${esc(s.title)}</h4><p>${esc(s.text)}</p>
    ${s.prompt ? `<div class="tour-prompt">${I.chat}<span>\u201c${esc(s.prompt)}\u201d</span></div>` : ''}
    ${s.look && s.look.length ? `<div class="tour-look"><b>Look for</b><ul>${s.look.map(x => `<li>${esc(x)}</li>`).join('')}</ul></div>` : ''}
    <div class="tour-foot">${busy ? '<span class="tour-busy"><span class="typing"><i></i><i></i><i></i></span> Atlas is working\u2026</span>' : '<span></span>'}
      <span class="tour-btns"><button class="btn sm" data-tour="back" ${tourState.i === 0 || busy ? 'disabled' : ''}>Back</button>
      <button class="btn sm primary" data-tour="next" ${busy ? 'disabled' : ''}>${last ? 'Finish' : 'Next'}${last ? '' : ' ' + I.arrow}</button></span></div>`;
}

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
