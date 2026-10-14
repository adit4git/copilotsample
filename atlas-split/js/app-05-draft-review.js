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
