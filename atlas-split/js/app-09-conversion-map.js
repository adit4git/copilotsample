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
  CONV = {data: m, strategy: (CONV && CONV.data.household_id === id && CONV.strategy) || m.most_held_as_is, cell: null};
  paintConversion();
}
function convSrc(docs){ return (docs || []).map(d => `IAP Brochure p.${d.pdf_page} \u2014 ${esc(d.section)}`).join('<br>'); }
function paintConversion(){
  const slot = document.getElementById('convSlot'); if(!slot || !CONV) return;
  const m = CONV.data, S = Object.fromEntries(m.strategies.map(s => [s.strategy, s])), sel = S[CONV.strategy];
  const head = `With a <b>${esc(sel.label)}</b>: ${fmtM(sel.hold_mv)} comes over as-is`
    + (sel.exchange_mv ? `, ${fmtM(sel.exchange_mv)} is exchanged into an eligible share class` : '')
    + (sel.sell_mv ? `, ${fmtM(sel.sell_mv)} is sold on entry (about ${fmtM(sel.realized_gain)} of gains, ~${fmtM(sel.est_tax)} tax at ${Math.round(m.tax_rate*1000)/10}%${sel.tet_stageable_gain ? `; TET can stage ${fmtM(sel.tet_stageable_gain)}` : ''})` : '')
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
      ${c.notes.map(n => `<p class="conv-note"><span class="mono">${esc(n.rule_id)}</span> ${esc(n.message)}</p>`).join('')}
      ${c.realized_gain ? `<p class="conv-note">Realized gain if sold: <b>${fmt$(c.realized_gain)}</b> (~${fmt$(Math.round(c.realized_gain*m.tax_rate))} tax, illustrative).</p>` : ''}
      <div class="conv-src"><span class="mono">${esc(c.rule_id || 'no rule')}</span>${c.assumption ? ' \u00b7 <b>illustrative assumption</b>' : ''}<br>${convSrc(c.source_doc)}</div>`;
  }
  slot.innerHTML = `<div class="card conv" style="margin-bottom:14px">
    <div class="ch"><h3 id="conversion">Brokerage \u2192 advisory conversion map</h3><span class="r" style="font-size:12px;color:var(--muted)">${fmt$(m.total_mv)} brokerage account \u00b7 rule-based</span></div>
    <div class="cbp">
      <p class="conv-headline">${head}</p>
      <div class="conv-gates">${gates}</div>
      <div class="conv-legend">${Object.values(CONV_OUTCOME).map(o => `<span class="conv-cell static ${o.cls}">${o.label}</span>`).join('')}<span class="sub">TET = sale the Tax Efficient Transition Service can stage \u00b7 * = illustrative assumption \u00b7 click a column to compare strategy types</span></div>
      <div style="overflow-x:auto"><table class="conv-tbl"><thead><tr><th>Holding</th><th class="r">Value</th>${th}</tr></thead><tbody>${rows}</tbody>
        <tfoot>${foot('Comes over without a sale', s => fmtM(s.hold_mv + s.exchange_mv))}${foot('Sold on entry', s => s.sell_mv ? fmtM(s.sell_mv) : '\u2014')}${foot('Gains realized', s => s.realized_gain ? fmtM(s.realized_gain) : '\u2014')}${foot('Stays in brokerage', s => s.move_out_mv ? fmtM(s.move_out_mv) : '\u2014')}</tfoot></table></div>
      <div class="conv-detail" id="convDetail">${detail}</div>
      <ul class="conv-notes">${m.notes.map(n => `<li>${esc(n.message)} <span class="sub">(IAP Brochure p.${n.source_doc[0].pdf_page})</span></li>`).join('')}</ul>
    </div></div>`;
}
