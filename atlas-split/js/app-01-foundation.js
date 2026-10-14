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
  const host = document.createElement('div'); host.className='xpop-back'; host.id='xpopHost';
  host.innerHTML = `<div class="xpop" role="dialog" aria-label="Eligibility explanation">
    <div class="xpop-h"><div class="xpop-t">${label}</div>${verdictPill(v)}</div>
    ${reason}${missing}
    <div class="xpop-sec">Inputs evaluated <span class="muted2">\u2014 derived fields the rules read</span></div>
    <div class="xtbl-wrap"><table class="xpop-tbl"><colgroup><col class="c1"><col class="c2"><col class="c3"><col class="c4"></colgroup><thead><tr><th>Derived field</th><th>Value</th><th>Test</th><th></th></tr></thead><tbody>${rows||'<tr><td colspan="4" class="muted2">No field predicates \u2014 this offering attaches only conditions/disclosures.</td></tr>'}</tbody></table></div>
    ${(carve||disc||faint||prereq)?`<div class="xpop-sec">Notes</div>${carve}${disc}${faint}${prereq}`:''}
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
