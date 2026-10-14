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
