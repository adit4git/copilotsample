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
