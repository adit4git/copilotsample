/* Team skills: the catalog of policy packs and playbooks that business and product teams own,
   a switch for each, a measured before/after of what it changes in this advisor's book,
   and a "Shaped by team skills" strip on every workspace an active skill changes. */
(function(){
  const SK = {list: [], labels: {}, open: {}, impact: {}, busy: null, filter: 'all', loaded: false};
  const ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>';
  const VIEW_WS = {client: ['eligibility', 'conversion', 'tem'], transition: ['eligibility', 'transition'], ciofit: ['cio_fit'], tax: ['tax_desk', 'tem'],
                   draftReview: ['meeting_prep_draft'], crosssell: ['cross_sell'], today: ['today']};
  const WS_FILTERS = [['all', 'All'], ['eligibility', 'Eligibility'], ['conversion', 'Conversion map'], ['tem', 'Tax personalization'], ['cio_fit', 'CIO Model Fit'],
                      ['meeting_prep_draft', 'Meeting prep'], ['ask_atlas', 'Ask Atlas']];
  const byId = id => SK.list.find(s => s.id === id);
  const on = () => SK.list.filter(s => s.enabled);
  const faName = () => { const p = state.meta && state.meta.advisors && state.meta.advisors[state.fa]; return p ? p.name.split(' ')[0] : 'this advisor'; };

  async function load(){
    const r = await api('/api/skills');
    SK.list = r.skills; SK.labels = r.labels || {}; SK.loaded = true;
    window.AtlasSkills.list = SK.list;
    return r;
  }

  /* ---------- tiny markdown for SKILL.md: ## headings, - lists, **bold**, paragraphs ---------- */
  function md(text){
    const inline = s => esc(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/`([^`]+)`/g, '<code>$1</code>');
    let html = '', list = 0;
    const close = () => { while(list > 0){ html += '</ul>'; list--; } };
    for(const raw of text.split('\n')){
      const line = raw.replace(/\s+$/, '');
      if(/^# /.test(line)) continue;
      const h = line.match(/^##\s+(.*)/); if(h){ close(); html += `<h3>${inline(h[1])}</h3>`; continue; }
      const li = line.match(/^(\s*)- (.*)/);
      if(li){ const depth = li[1].length >= 2 ? 2 : 1; while(list < depth){ html += '<ul>'; list++; } while(list > depth){ html += '</ul>'; list--; } html += `<li>${inline(li[2])}</li>`; continue; }
      close(); if(line.trim()) html += `<p>${inline(line)}</p>`;
    }
    close(); return html;
  }

  function impactHtml(s){
    const r = SK.impact[s.id];
    if(r === 'loading') return `<div class="sk-panel"><p class="lede">Running ${esc(faName())}’s book with and without this skill…</p></div>`;
    if(!r) return '';
    const L = w => SK.labels[w] || w;
    const n = r.changes.length;
    const lede = n ? `Measured on ${esc(faName())}’s book: running Atlas without this skill and with it changes <b>${n}</b> thing${n === 1 ? '' : 's'}. ${s.enabled ? 'It is on now.' : 'It is off now; turn it on to make these changes live.'}`
                   : `Measured on ${esc(faName())}’s book: nothing changes for these clients${s.enabled ? '' : ' (it may still change other books)'}.`;
    const rows = r.changes.slice(0, 80).map((c, i) => `<tr><td class="ws">${esc(L(c.workspace))}</td><td>${esc(c.subject)}</td><td>${esc(c.what)}</td>
        <td><span class="b">${esc(String(c.before))}</span></td><td><span class="a">${esc(String(c.after))}</span></td>
        <td>${c.open ? `<button data-sk-open="${s.id}|${i}">Open →</button>` : ''}</td></tr>`).join('');
    return `<div class="sk-panel"><h4>What it changes</h4><p class="lede">${lede}</p>
      ${n ? `<div class="sk-imp-sum">${Object.entries(r.by_workspace).map(([w, k]) => `<span>${esc(L(w))}: ${k}</span>`).join('')}</div>
      <div class="sk-tbl-wrap"><table class="sk-tbl"><thead><tr><th>Workspace</th><th>Client or request</th><th>What</th><th>Without the skill</th><th>With it</th><th></th></tr></thead><tbody>${rows}</tbody></table></div>
      ${n > 80 ? `<p class="lede" style="margin-top:8px">Showing 80 of ${n}.</p>` : ''}` : ''}
      ${s.try && s.try.length ? `<div class="sk-try">${s.try.map((t, i) => `<button data-sk-try="${s.id}|${i}">${esc(t.label)} →</button>`).join('')}</div>` : ''}</div>`;
  }

  function readHtml(s){
    if(SK.open[s.id] !== 'read') return '';
    const P = (s.patches || []).map(p => `<div><span class="op">${esc(p.op)}</span> ${esc(p.target)}: ${esc(p.path)}${p.why ? ` <span style="color:var(--muted)"># ${esc(p.why)}</span>` : ''}</div>`).join('');
    return `<div class="sk-panel"><div class="sk-md"><div class="file">skills/${esc(s.id)}/SKILL.md · owner: ${esc(s.owner)}</div>${md(s.markdown)}</div>
      ${P ? `<h4 style="margin-top:12px">policy.json: ${s.patches.length} change${s.patches.length === 1 ? '' : 's'} to the data</h4><div class="sk-patches">${P}</div>` : ''}</div>`;
  }

  function card(s){
    const st = /approved/i.test(s.status) ? 'sk-st ok' : 'sk-st';
    return `<div class="sk-card${s.enabled ? ' on' : ''}" id="sk-${s.id}">
      <div class="sk-row"><div style="min-width:0">
          <div class="sk-title">${esc(s.title)}</div>
          <div class="sk-sum">${esc(s.summary)}</div>
          <div class="sk-tags">${s.workspace_labels.map(w => `<span class="sk-tag">${esc(w)}</span>`).join('')}<span class="sk-kind">${esc(s.kind)}</span><span class="${st}">${esc(s.status)}</span><span class="sk-ver">v${esc(s.version)}</span></div>
          ${s.errors && s.errors.length ? `<div class="sk-err">Not applied: ${s.errors.map(esc).join('; ')}</div>` : ''}
        </div>
        <div class="sk-side">
          <button class="sk-switch" role="switch" aria-checked="${s.enabled}" data-sk-toggle="${s.id}" ${SK.busy === s.id ? 'disabled' : ''} aria-label="${s.enabled ? 'Turn off' : 'Turn on'} ${esc(s.title)}"><span>${s.enabled ? 'On' : 'Off'}</span><span class="t"></span></button>
          <div class="sk-links"><button data-sk-impact="${s.id}">${SK.impact[s.id] && SK.impact[s.id] !== 'loading' ? 'Hide changes' : 'What it changes'}</button><button data-sk-read="${s.id}">${SK.open[s.id] === 'read' ? 'Hide skill' : 'Read the skill'}</button></div>
        </div></div>
      ${impactHtml(s)}${readHtml(s)}</div>`;
  }

  function paint(){
    const v = document.getElementById('view'); if(!v || state.view !== 'skills') return;
    const teams = [...new Set(SK.list.map(s => s.team))];
    const shown = SK.list.filter(s => SK.filter === 'all' || s.workspaces.includes(SK.filter));
    const count = w => SK.list.filter(s => w === 'all' || s.workspaces.includes(w)).length;
    const groups = [...new Set(shown.map(s => s.team))].map(t => `<div class="sk-team">${esc(t)}</div>${shown.filter(s => s.team === t).map(card).join('')}`).join('');
    v.innerHTML = `<div class="sk">
      <div class="sk-head"><div><div class="eyebrow" style="margin-bottom:4px">TEAM SKILLS</div>
          <div class="nm">Policy and playbooks, owned by the teams that write them</div>
          <div class="sub">Each skill is a short file a business or product team owns. Turn one on and every workspace that reads that policy changes at once: verdicts, conversion maps, tax lots, CIO numbers, drafts and Ask Atlas. Nothing in the code changes, and turning it off puts everything back.</div></div>
        <div class="sk-meta"><span><b>${on().length}</b> of ${SK.list.length} on · ${teams.length} teams</span><button class="btn sm" data-sk-reset ${on().length ? '' : 'disabled'}>Turn all off</button></div></div>
      <div class="sk-how">
        <div><b><span class="n">1</span>A team writes the skill</b><code>SKILL.md</code> says who owns it, what it changes and why, in plain English. An optional <code>policy.json</code> holds the exact rule, threshold or template.</div>
        <div><b><span class="n">2</span>Atlas applies it</b>The rule engine, conversion map, tax personalization, CIO Model Fit, drafts and Ask Atlas all read the same policy. A skill changes that policy, not the code.</div>
        <div><b><span class="n">3</span>Every answer shows it</b>Verdicts, map cells and notes name the skill and team behind them. “What it changes” runs this book with and without the skill.</div></div>
      <div class="sk-filters" role="group" aria-label="Filter by workspace">${WS_FILTERS.map(([k, l]) => `<button data-sk-filter="${k}" class="${SK.filter === k ? 'on' : ''}">${esc(l)}<span class="c">${count(k)}</span></button>`).join('')}</div>
      ${groups || '<div class="sk-empty">No skills shape this workspace yet.</div>'}
    </div>`;
  }

  async function view(){
    const v = document.getElementById('view');
    if(!SK.loaded) v.innerHTML = '<div class="empty" style="padding:32px;text-align:center;color:var(--muted)">Loading team skills…</div>';
    try{ await load(); }catch(e){ v.innerHTML = `<div class="empty" style="padding:32px;color:var(--red)">Couldn’t load team skills: ${esc(e.message)}</div>`; return; }
    paint();
  }

  async function measure(id){
    SK.impact[id] = 'loading'; paint();
    try{ SK.impact[id] = await api(`/api/skills/${id}/impact?fa=${state.fa}`); }catch(e){ delete SK.impact[id]; }
    paint();
  }

  // After a skill changes the policy, anything the page cached from the old policy is stale.
  async function invalidate(){
    try{ await loadBook(); }catch(e){}
    if(typeof CONV !== 'undefined') CONV = null;
    if(window.AtlasCio && window.AtlasCio.state) window.AtlasCio.state.data = null;
    if(window.AtlasTem && window.AtlasTem.state){ window.AtlasTem.state.data = null; window.AtlasTem.state.id = null; }
  }

  async function toggle(id){
    const s = byId(id); if(!s || SK.busy) return;
    SK.busy = id; paint();
    try{
      const r = await api(`/api/skills/${id}`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({enabled: !s.enabled})});
      SK.list = r.skills; window.AtlasSkills.list = SK.list;
      await invalidate();
    }finally{ SK.busy = null; }
    paintNav(); paint();
    measure(id);
  }

  async function go(t){
    if(!t) return;
    if(t.workspace === 'ask'){ state.fromChat = null; setView('chat'); setTimeout(() => sendChat(t.q), 60); return; }
    if(t.workspace === 'tax_desk'){ state.fromChat = null; return setView('tax'); }
    await runAgentAction({workspace: t.workspace, household_id: t.household_id || null, offering_id: t.offering_id || null, auto_open: true}, '');
    state.fromChat = null;
  }

  /* ---------- strip on workspaces an active skill shapes ---------- */
  function strip(){
    const v = document.getElementById('view'); if(!v || !SK.loaded) return;
    const ws = VIEW_WS[state.view]; if(!ws) return;
    const act = on().filter(s => s.workspaces.some(w => ws.includes(w)));
    if(!act.length || v.querySelector('.sk-strip')) return;
    v.insertAdjacentHTML('afterbegin', `<div class="sk-strip" role="note"><span class="sk-ico">${ICON}</span><span>Shaped by team skills:</span>
      ${act.map(s => `<span><b>${esc(s.title)}</b> · ${esc(s.team)}</span>`).join('<span class="sep">|</span>')}<button data-nav="skills">Manage skills →</button></div>`);
  }

  /* ---------- hooks into the app ---------- */
  window.AtlasSkills = {list: [], state: SK, load,
    // "Shaped by" tag for anything carrying skill ids or skill objects
    tag(items){
      const ids = (items || []).map(x => typeof x === 'string' ? x : x.id);
      return ids.map(id => { const s = (SK.list || []).find(x => x.id === id) || (items || []).find(x => x.id === id) || {title: id, team: ''};
        return `<span class="sk-by" title="From the ${esc(s.team)} skill “${esc(s.title)}”">${esc(s.team || 'Team skill')} skill</span>`; }).join('');
    }};
  if(!NAVITEMS.some(n => n.k === 'skills')){
    NAVITEMS.push({k:'skills', label:'Team Skills', icon: ICON, badge: () => on().length || '', mobile: false});
    const gb = document.querySelector('#nav button[data-nav="guide"]');
    if(gb && !document.querySelector('#nav button[data-nav="skills"]')){ const b = document.createElement('button'); b.dataset.nav = 'skills'; gb.insertAdjacentElement('afterend', b); }
  }
  const _render = render;
  render = async function(){
    if(state.view !== 'skills'){ const r = await _render.apply(this, arguments); strip(); return r; }
    state.focusHousehold = null; state.lastView = 'skills';
    paintNav();
    const cr = document.getElementById('crumb'); if(cr) cr.innerHTML = '<b>Team Skills</b>';
    await view();
    if(typeof decorateView === 'function') decorateView();
  };
  if(typeof HOWTO !== 'undefined') HOWTO.skills = [
    ['Shows', 'The skills business and product teams provide: rule packs, thresholds, playbooks, draft standards and phrasing, each with its owner and version.'],
    ['Changes', 'Turning one on changes the policy every workspace reads. The rule engine, conversion map, tax personalization, CIO Model Fit, drafts and Ask Atlas pick it up at once.'],
    ['Read it as', '“What it changes” runs this book without and with the skill and lists every difference. Open any row to see it in place.']];
  const _run = runAgentAction;
  runAgentAction = async function(a, q){
    if(a && a.workspace === 'skills'){ state.fromChat = {q: q || a.__q || '', view: 'skills'}; return setView('skills'); }
    return _run.apply(this, arguments);
  };
  document.addEventListener('click', e => {
    const t = e.target.closest('[data-sk-toggle]'); if(t){ e.stopPropagation(); toggle(t.dataset.skToggle); return; }
    const im = e.target.closest('[data-sk-impact]'); if(im){ const id = im.dataset.skImpact; if(SK.impact[id] && SK.impact[id] !== 'loading'){ delete SK.impact[id]; paint(); } else measure(id); return; }
    const rd = e.target.closest('[data-sk-read]'); if(rd){ const id = rd.dataset.skRead; SK.open[id] = SK.open[id] === 'read' ? null : 'read'; paint(); return; }
    const f = e.target.closest('[data-sk-filter]'); if(f){ SK.filter = f.dataset.skFilter; paint(); return; }
    const tr = e.target.closest('[data-sk-try]'); if(tr){ const [id, i] = tr.dataset.skTry.split('|'); go(byId(id).try[+i]); return; }
    const op = e.target.closest('[data-sk-open]'); if(op){ const [id, i] = op.dataset.skOpen.split('|'); const c = SK.impact[id].changes[+i]; go(c.open); return; }
    const rs = e.target.closest('[data-sk-reset]'); if(rs){
      (async () => { const r = await api('/api/skills/reset', {method:'POST'}); SK.list = r.skills; window.AtlasSkills.list = SK.list; SK.impact = {}; await invalidate(); paintNav(); paint(); })();
    }
  }, true);

  if(typeof TOOL_LABELS !== 'undefined'){ TOOL_LABELS.team_skill = 'Applied a team skill'; TOOL_LABELS.list_skills = 'Checked the team skills'; }
  if(typeof CAPS !== 'undefined' && !CAPS.some(c => c.t === 'Team skills'))
    CAPS.push({t:'Team skills', what:'Rule packs, thresholds, playbooks and draft standards that business and product teams own. Each one changes how the workspaces behave, with its owner named on every answer it shapes.',
      ex:['Which team skills are on?'], opens:'Team Skills',
      uses:'skills/ folder: one SKILL.md per skill, plus an optional policy.json of exact changes',
      limits:'Illustrative skills. A skill changes data and instructions only; it cannot add new calculations.'});
  if(typeof TOUR !== 'undefined' && !TOUR.some(s => s.view === 'skills')){
    const i = TOUR.findIndex(s => s.view === 'guide');
    TOUR.splice(i >= 0 ? i : TOUR.length - 1, 0, {title:'Skills from business and product teams', prompt:'Which team skills are on?', view:'skills',
      fallback: () => setView('skills'),
      text:'Rules, thresholds and playbooks come from the teams that own them: Product and Compliance, Tax Services, Wealth Planning, Manager Research, the CIO office, Risk, Field Enablement. Each is a short file. Turning one on changes every workspace that reads that policy.',
      look:['Turn on “Conversion playbook: managed first”: the table lists what changes in this book', 'Open Montgomery: the conversion map now suggests Custom Managed and says why', 'Add the New Jersey tax skill: Montgomery no longer fits the tax budget']});
    const n = TOUR.filter(s => s.prompt).length, words = ['zero','one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen'];
    if(TOUR[0] && TOUR[0].text) TOUR[0].text = TOUR[0].text.replace(/runs \w+ real requests/, `runs ${words[n] || n} real requests`);
  }
  if(typeof switchFa === 'function'){ const _sw = switchFa; switchFa = async function(){ SK.impact = {}; return _sw.apply(this, arguments); }; }
  load().then(() => { paintNav(); if(VIEW_WS[state.view]) strip(); }).catch(() => {});
})();
