/* ================= Guided tour: how the flow works, on live screens =================
 * Each step sets the view (never records a decision), waits for the screen from the API, spotlights one element and explains it.
 * The advisor's view is saved on start and restored on exit. Esc exits; ← → move; Enter = next.
 */
const TOUR = [
  {view: {ws: 'queue', qv: 'hh'}, sel: null, title: 'How this tool works', body: 'It finds brokerage households where an advisory relationship could genuinely help, then takes you from the first signal to a reviewed proposal and a hand-off to operations. You decide at every stage; nothing is sent, enrolled or traded by the tool.'},
  {view: {ws: 'queue', qv: 'hh'}, sel: 'table.hq', title: '1 · Identify: brokerage opportunities in your book', body: 'One row per household: which household, why now, how much could move, by which route, and what to do next. Order is simple and stated under the table: a meeting, call date or client request first, then the amount movable now; accounts above 50% last.'},
  {view: {ws: 'queue', qv: 'hh'}, sel: 'tr.hrow .cues', title: 'Why it is near the top', body: 'Priority cues explain the order at a glance: meeting soon, a call date, a client request, a tax-basis blocker, a large movable amount. A rank is a prompt for review, not a suitability conclusion.'},
  {view: {ws: 'queue', qv: 'hh'}, sel: '.hfilt', title: 'Filter by what is needed', body: 'Needs discussion, waiting on a specialist or operations, ready to propose, or outcome recorded: so you can work the list by the next thing you can actually do.'},
  {view: {ws: 'queue', qv: 'hh'}, sel: 'tr.hrow td:nth-child(2)', title: 'Potentially movable now', body: 'Observed holdings that could move into an advisory account today. Anything held back (the liquidity reserve, bonds held to maturity, lots awaiting cost basis) is shown underneath, never added in.'},
  {view: {ws: 'queue', qv: 'hh'}, sel: 'tr.hrow td:nth-child(3)', title: 'A starting route, not a recommendation', body: 'The route most likely to fit, offered as a starting point for your review. Beside it, the main constraint and its owner: Operations for missing cost basis, Compliance for insider rules, a Specialist above the 50% limit.'},
  {view: {ws: 'queue', qv: 'hh'}, sel: 'tr.hrow td:nth-child(5)', title: 'One next step', body: 'Each household has a single next step that follows it through the flow, with the meeting date beside it. Recorded outcomes such as remain in brokerage show here instead.'},
  {view: {ws: 'queue', qv: 'hh'}, sel: '[data-mgmt]', title: 'Management view (internal)', body: 'Addressable assets by tax difficulty and firm revenue before and after sit here, off by default and labelled internal. They never appear on client-facing screens.'},
  {view: {ws: 'path', hid: 'henderson', hstep: 'assess'}, sel: '.hstep', title: 'Each household: four steps', body: 'Client case → Compare routes → Client proposal → Implementation handoff, matching the operating stages Analyze, Design, Propose and Implement. Ticks show progress.'},
  {view: {ws: 'path', hid: 'henderson', hstep: 'assess'}, sel: '.lead-amt', title: '2 · Analyze: how much, and what is in the way', body: 'One headline: potentially movable to advisory now. One line on what is held back and why, and the blocker with its owner, so you can answer “how much can I discuss moving, and what prevents the rest?” in seconds.'},
  {view: {ws: 'path', hid: 'henderson', hstep: 'assess'}, sel: '.tri', title: 'Moving the account is not trading the portfolio', body: 'Assets move into the account in kind at enrollment; repositioning happens over time; year-one alignment is an estimate for the phased route. None of these implies a trade has been approved.'},
  {view: {ws: 'path', hid: 'henderson', hstep: 'assess'}, sel: '.rows.vr', title: 'Every money figure says what it is', body: 'Each figure is tagged observed, estimate, modeled or needs validation. Returns are an illustrative scenario difference, not growth given up. Tax is planning level and flagged when cost basis is missing. The incremental fee is always shown.'},
  {view: {ws: 'path', hid: 'henderson', hstep: 'assess', open: 'a-rec'}, sel: '[data-dx="a-rec"]', title: 'Amounts that reconcile', body: 'Every holding sits in exactly one bucket: moves now, held for cost basis, kept in brokerage, or excluded. The bar adds back to the total identified. Bond calls and maturities are timing notes, never counted twice.'},
  {view: {ws: 'path', hid: 'henderson', hstep: 'assess'}, sel: '.assess .chips', title: 'Your decision', body: 'Pursue to compare routes, or record a legitimate outcome: remain in brokerage, monitor or refer to a specialist. A reason is needed before it closes, and other follow-ups for the household stay open.'},
  {view: {ws: 'path', hid: 'henderson', hstep: 'paths'}, sel: '.pcards2', title: '3 · Design: compare routes side by side', body: 'Each route shows why it fits, its two main trade-offs, account movement and portfolio trading separately, tax, the steady-state fee and who approves. Open feasibility checks are listed with owners; a screening match alone never makes a route actionable.'},
  {view: {ws: 'path', hid: 'henderson', hstep: 'paths'}, sel: '.pcard2 .sp', up: '.pcard2', title: 'A starting point for your review', body: 'One route is marked as a starting point, from the household’s situation. Choosing a route records a working choice for the proposal; it is not a suitability approval.'},
  {view: {ws: 'path', hid: 'henderson', hstep: 'paths'}, sel: '.pcard2.stay', title: 'Stay in brokerage, as a real option', body: 'Today’s cost, what the client would not get, the lower-cost advisory alternative and the reasons they might stay, with remain, monitor and refer one click away.'},
  {view: {ws: 'ws2', hid: 'henderson'}, sel: '#stage .sum', title: '4 · Propose: the client proposal', body: 'Value first, then what only a managed account can do, then cost and reasons to stay. Approved materials only; every draft is marked as needing advisor and compliance review.'},
  {view: {ws: 'path', hid: 'henderson', hstep: 'handoff'}, sel: '.feas.big', title: '5 · Implement: hand-off, never execution', body: 'Every item people must complete, with its owner. “Hand off to operations” unlocks only when all are done; operations enroll. The checklist here is a demonstration, not a system approval.'},
  {view: {ws: 'path', hid: 'henderson', hstep: 'assess'}, sel: '#side', side: true, title: 'Your task panel', body: 'Current task, owner, what is blocking, status and the one next action. The story draft, full stages and decision controls are tucked underneath.'},
  {view: {ws: 'path', hid: 'henderson', hstep: 'assess'}, sel: 'ul.sig', title: 'The analysis is still one click away', body: 'Allocation and performance, the concentrated position plan and research events open from here; the six-step worked example, plan by holding and sources are in the expandable sections.'},
  {view: {ws: 'queue', qv: 'hh'}, sel: '#top [data-checks]', title: 'Check the logic yourself', body: 'Runs the decision-engine checks in your browser: one eligibility rule, one cash figure, amounts that reconcile, no automatic execution. All data is illustrative and nothing is saved.'},
  {view: {ws: 'queue', qv: 'hh'}, sel: null, title: 'That is the flow', body: 'Your book → client case → compare routes → proposal → hand-off, with you deciding at every step. Start with the top household, or reopen this tour any time from “Tour”.', last: true},
];

const T = {i: 0, saved: null};
function tourSave(){ return JSON.stringify({ws: S.ws, hid: S.hid, hstep: S.hstep, qv: S.qv, mgmt: S.mgmt, hf: S.hf, about: S.about, open: [...S.open]}); }
async function tourRestore(j){ const o = JSON.parse(j); Object.assign(S, {ws: o.ws, hid: o.hid, hstep: o.hstep, qv: o.qv, mgmt: o.mgmt, hf: o.hf || 'all', about: o.about}); S.open = new Set(o.open); $('#side').classList.remove('open'); await paint(); }
function tourStart(){ T.saved = tourSave(); T.i = 0; tourShow(); }
window.tourStart = tourStart;
async function tourEnd(){ const el = document.getElementById('tour'); if(el) el.remove(); document.removeEventListener('keydown', tourKey, true); window.removeEventListener('resize', tourPlace); window.removeEventListener('scroll', tourPlace, true); const s = T.saved; T.saved = null; if(s) await tourRestore(s); }
function tourKey(e){ if(e.key === 'Escape'){ e.preventDefault(); tourEnd(); } else if(e.key === 'ArrowRight' || e.key === 'Enter'){ e.preventDefault(); tourGo(1); } else if(e.key === 'ArrowLeft'){ e.preventDefault(); tourGo(-1); } }
function tourGo(d){ const n = T.i + d; if(n < 0) return; if(n >= TOUR.length) return tourEnd(); T.i = n; tourShow(); }
async function tourShow(){
  const st = TOUR[T.i], v = st.view; S.about = false;
  Object.assign(S, v.qv ? {qv: v.qv} : {}, v.hid ? {hid: v.hid} : {}, v.hstep ? {hstep: v.hstep} : {}, {ws: v.ws}); S.mgmt = false; S.hf = 'all'; if(v.open) S.open.add(v.open);
  const mobile = window.innerWidth < 900;
  if(st.side && mobile) $('#side').classList.add('open'); else $('#side').classList.remove('open');
  await paint();
  let el = document.getElementById('tour'); if(!el){ el = document.createElement('div'); el.id = 'tour'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true'); el.setAttribute('aria-labelledby', 'tour-t'); document.body.appendChild(el);
    document.addEventListener('keydown', tourKey, true); window.addEventListener('resize', tourPlace); window.addEventListener('scroll', tourPlace, true); }
  el.innerHTML = `<div class="tour-hole"></div><div class="tour-card" aria-live="polite"><div class="tour-k">Guided tour · ${T.i + 1} of ${TOUR.length}</div><h3 id="tour-t">${esc(st.title)}</h3><p>${esc(st.body)}</p>
    <div class="tour-dots">${TOUR.map((_, i) => `<i class="${i === T.i ? 'on' : i < T.i ? 'done' : ''}"></i>`).join('')}</div>
    <div class="tour-b"><button class="btn sm" data-tour="end">Exit tour</button><span class="grow"></span>${T.i ? '<button class="btn sm" data-tour="back">Back</button>' : ''}<button class="btn primary sm" data-tour="next">${st.last ? 'Finish' : T.i ? 'Next' : 'Start the tour'}</button></div></div>`;
  const t = st.sel && document.querySelector(st.sel); T.target = t ? (st.up ? t.closest(st.up) || t : t) : null;
  if(T.target) T.target.scrollIntoView({block: 'center', behavior: 'instant'}); else window.scrollTo({top: 0});
  requestAnimationFrame(tourPlace); el.querySelector('[data-tour="next"]').focus({preventScroll: true});
}
function tourPlace(){
  const el = document.getElementById('tour'); if(!el) return; const hole = el.querySelector('.tour-hole'), card = el.querySelector('.tour-card'), t = T.target, pad = 8, vw = window.innerWidth, vh = window.innerHeight;
  if(!t){ hole.style.cssText = `left:${vw / 2}px;top:${vh / 2}px;width:0;height:0`; card.classList.add('center'); card.style.left = ''; card.style.top = ''; return; }
  card.classList.remove('center'); const r = t.getBoundingClientRect(), x = Math.max(4, r.left - pad), y = Math.max(4, r.top - pad), w = Math.min(vw - 8, r.width + 2 * pad), h = Math.min(vh - 8, r.height + 2 * pad);
  hole.style.cssText = `left:${x}px;top:${y}px;width:${w}px;height:${h}px`;
  const cw = Math.min(380, vw - 24), ch = card.offsetHeight; card.style.width = cw + 'px';
  let cx = Math.min(Math.max(12, r.left), vw - cw - 12), cy = y + h + 12;
  const st = TOUR[T.i];
  if(vw > 700 && (r.height > vh * 0.55 || st.side)){ cy = vh - ch - 20; cx = st.side ? Math.max(12, r.left - cw - 20) : vw - cw - 20; card.style.left = cx + 'px'; card.style.top = cy + 'px'; return; }
  if(cy + ch > vh - 12){ cy = y - ch - 12; if(cy < 12){ cy = Math.max(12, vh - ch - 12); if(r.right + cw + 24 < vw){ cx = r.right + 16; cy = Math.min(Math.max(12, r.top), vh - ch - 12); } else if(r.left - cw - 24 > 0){ cx = r.left - cw - 16; cy = Math.min(Math.max(12, r.top), vh - ch - 12); } } }
  card.style.left = cx + 'px'; card.style.top = cy + 'px';
}
document.addEventListener('click', e => { const b = e.target.closest('[data-tour]'); if(b){ e.stopPropagation(); e.preventDefault(); const a = b.dataset.tour; if(a === 'start') tourStart(); else if(a === 'next') tourGo(1); else if(a === 'back') tourGo(-1); else tourEnd(); return; }
  if(document.getElementById('tour') && !e.target.closest('.tour-card')){ e.stopPropagation(); e.preventDefault(); } }, true);
