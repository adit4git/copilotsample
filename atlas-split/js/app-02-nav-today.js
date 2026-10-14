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
    const badge = item.badge ? `<span class="cnt">${item.badge()}</span>` : '';
    b.innerHTML = `${item.icon}<span>${item.label}</span>${badge}`;
  });
  const mt = document.getElementById('mtabbar');
  mt.innerHTML = NAVITEMS.map(n => `<button data-nav="${n.k}" class="${state.view===n.k||(n.k==='book'&&['client','draftReview','transition','vehicleCompare'].includes(state.view))?'on':''}">${n.icon}<span>${n.label.split(' ')[0]}</span></button>`).join('');
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
