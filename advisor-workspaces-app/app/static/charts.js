/* ================= Small SVG chart kit (no library, works offline) =================
 * donut / sunburst (part-to-whole with drill), treemap (holdings), gauge (risk against its band), waterfall (why a figure
 * changes), dumbbell rows (today → proposal against a target tick), ring (progress toward an objective).
 * Colors are roles from the stylesheet (--c1..--c8 categorical, fixed order; --c-other for the folded tail). Every chart has a
 * hover tooltip (data-tip) and its numbers are also shown as text next to it.
 */
const CH = {
  esc: s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c])),
  arc(cx, cy, r0, r1, a0, a1){
    const p = (r, a) => [cx + r * Math.sin(a), cy - r * Math.cos(a)], big = a1 - a0 > Math.PI ? 1 : 0;
    if(a1 - a0 >= 2 * Math.PI - 1e-6) a1 = a0 + 2 * Math.PI - 1e-4;
    const [x0, y0] = p(r1, a0), [x1, y1] = p(r1, a1), [x2, y2] = p(r0, a1), [x3, y3] = p(r0, a0);
    return `M${x0},${y0}A${r1},${r1} 0 ${big} 1 ${x1},${y1}L${x2},${y2}A${r0},${r0} 0 ${big} 0 ${x3},${y3}Z`;
  },
  /* segs: [{id, label, value, color, tip, drill}] ; ring of one level */
  ctr(cx, cy, rHole, big, sub, base){
    const fs = Math.min(base, rHole * 1.5 / (Math.max(3, String(big || '').length) * 0.56)), ss = Math.max(9, Math.min(12, fs * 0.55));
    return (big ? `<text x="${cx}" y="${cy + (sub ? -fs * 0.08 : fs * 0.35)}" text-anchor="middle" class="c-big" style="font-size:${fs.toFixed(1)}px">${CH.esc(big)}</text>` : '') +
      (sub ? `<text x="${cx}" y="${cy + fs * 0.35 + ss + 2}" text-anchor="middle" class="c-sub" style="font-size:${ss.toFixed(1)}px">${CH.esc(sub)}</text>` : '');
  },
  donut(segs, o = {}){
    const S = o.size || 220, cx = S / 2, cy = S / 2, r1 = S / 2 - 4, r0 = r1 * (o.hole ?? 0.62), tot = segs.reduce((s, x) => s + Math.max(0, x.value), 0) || 1;
    let a = 0; const gap = segs.length > 1 ? 0.012 : 0;
    const paths = segs.filter(x => x.value > 0).map(x => { const da = x.value / tot * 2 * Math.PI, d = CH.arc(cx, cy, r0, r1, a + gap / 2, a + da - gap / 2); a += da;
      return `<path d="${d}" fill="${x.color}" ${x.drill ? `data-drill="${CH.esc(x.drill)}" class="hit"` : ''} data-tip="${CH.esc(x.tip || `${x.label}: ${(x.value / tot * 100).toFixed(1)}%`)}" ${x.dim ? 'opacity=".28"' : ''}></path>`; }).join('');
    return `<svg class="chart" viewBox="0 0 ${S} ${S}" width="${S}" height="${S}" role="img" aria-label="${CH.esc(o.label || 'Donut chart')}">${paths}
      ${CH.ctr(cx, cy, r0, o.center, o.sub, 24)}</svg>`;
  },
  /* two rings: inner = parents, outer = children (each child has parent id) */
  sunburst(inner, outer, o = {}){
    const S = o.size || 260, cx = S / 2, cy = S / 2, R = S / 2 - 4, rA0 = R * 0.34, rA1 = R * 0.62, rB0 = R * 0.64, rB1 = R;
    const tot = inner.reduce((s, x) => s + x.value, 0) || 1; let a = 0, out = '';
    for(const p of inner){ if(p.value <= 0) continue; const da = p.value / tot * 2 * Math.PI, a0 = a;
      out += `<path d="${CH.arc(cx, cy, rA0, rA1, a0 + 0.006, a0 + da - 0.006)}" fill="${p.color}" class="hit" data-drill="${CH.esc(p.drill || p.id)}" data-tip="${CH.esc(p.tip)}"></path>`;
      let b = a0; for(const c of outer.filter(c => c.parent === p.id && c.value > 0)){ const db = c.value / tot * 2 * Math.PI;
        out += `<path d="${CH.arc(cx, cy, rB0, rB1, b + 0.004, b + db - 0.004)}" fill="${c.color}" class="hit" data-drill="${CH.esc(c.drill || c.id)}" data-tip="${CH.esc(c.tip)}"></path>`; b += db; }
      a += da; }
    return `<svg class="chart" viewBox="0 0 ${S} ${S}" width="${S}" height="${S}" role="img" aria-label="${CH.esc(o.label || 'Sunburst')}">${out}
      ${CH.ctr(cx, cy, rA0, o.center, o.sub, 22)}</svg>`;
  },
  /* squarified treemap: items [{id, label, value, color, tip, sub}] */
  treemap(items, o = {}){
    const W = o.w || 560, H = o.h || 260, list = items.filter(x => x.value > 0).sort((a, b) => b.value - a.value), tot = list.reduce((s, x) => s + x.value, 0) || 1;
    const rects = []; let x = 0, y = 0, w = W, h = H, rest = list.map(i => ({...i, area: i.value / tot * W * H}));
    const worst = (row, len) => { const s = row.reduce((a, r) => a + r.area, 0), mx = Math.max(...row.map(r => r.area)), mn = Math.min(...row.map(r => r.area)); return Math.max(len * len * mx / (s * s), s * s / (len * len * mn)); };
    while(rest.length){
      const len = Math.min(w, h); let row = [rest[0]], i = 1;
      while(i < rest.length && worst(row.concat(rest[i]), len) <= worst(row, len)){ row.push(rest[i]); i++; }
      const s = row.reduce((a, r) => a + r.area, 0);
      if(w >= h){ const cw = s / h; let yy = y; for(const r of row){ const rh = r.area / cw; rects.push({...r, x, y: yy, w: cw, h: rh}); yy += rh; } x += cw; w -= cw; }
      else { const rh = s / w; let xx = x; for(const r of row){ const rw = r.area / rh; rects.push({...r, x: xx, y, w: rw, h: rh}); xx += rw; } y += rh; h -= rh; }
      rest = rest.slice(row.length);
    }
    return `<svg class="chart tm" viewBox="0 0 ${W} ${H}" width="100%" preserveAspectRatio="none" style="max-width:${W}px;aspect-ratio:${W}/${H}" role="img" aria-label="${CH.esc(o.label || 'Treemap')}">${rects.map(r => {
      const big = r.w > 70 && r.h > 34;
      return `<g class="hit ${r.hl ? 'hl' : ''}" ${r.drill ? `data-drill="${CH.esc(r.drill)}"` : ''} data-tip="${CH.esc(r.tip)}"><rect x="${r.x + 1}" y="${r.y + 1}" width="${Math.max(0, r.w - 2)}" height="${Math.max(0, r.h - 2)}" rx="4" fill="${r.color}" ${r.dim ? 'opacity=".35"' : ''}></rect>
        ${big ? `<text x="${r.x + 8}" y="${r.y + 18}" class="t-l">${CH.esc(r.label)}</text><text x="${r.x + 8}" y="${r.y + 33}" class="t-s">${CH.esc(r.sub || '')}</text>` : (r.w > 34 && r.h > 16 ? `<text x="${r.x + 5}" y="${r.y + 13}" class="t-s">${CH.esc(r.label)}</text>` : '')}</g>`; }).join('')}</svg>`;
  },
  /* semicircle gauge: band [lo, hi], markers today/proposal, domain [min,max] */
  gauge(o){
    const W = o.w || 260, H = W * 0.6, cx = W / 2, cy = W / 2 - 4, R = W / 2 - 14, r0 = R - 16, min = o.min, max = o.max;
    const ang = v => -Math.PI / 2 + Math.max(0, Math.min(1, (v - min) / (max - min))) * Math.PI;
    const mk = (v, cls, lab, up) => { const a = ang(v), x1 = cx + (r0 - 6) * Math.sin(a), y1 = cy - (r0 - 6) * Math.cos(a), x2 = cx + (R + 6) * Math.sin(a), y2 = cy - (R + 6) * Math.cos(a);
      return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="${cls}"></line>`; };
    return `<svg class="chart" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="${CH.esc(o.label || 'Gauge')}">
      <path d="${CH.arc(cx, cy, r0, R, -Math.PI / 2, Math.PI / 2)}" class="g-rail"></path>
      <path d="${CH.arc(cx, cy, r0, R, ang(o.lo), ang(o.hi))}" class="g-band" data-tip="${CH.esc(o.bandTip || '')}"></path>
      ${mk(o.today, 'g-today')}${o.after != null ? mk(o.after, 'g-after') : ''}
      <text x="${cx}" y="${cy - 14}" text-anchor="middle" class="c-big">${CH.esc(o.big)}</text><text x="${cx}" y="${cy + 4}" text-anchor="middle" class="c-sub">${CH.esc(o.sub || '')}</text>
      <text x="${cx - R}" y="${cy + 18}" class="c-ax">${CH.esc(o.minLab || '')}</text><text x="${cx + R}" y="${cy + 18}" text-anchor="end" class="c-ax">${CH.esc(o.maxLab || '')}</text></svg>`;
  },
  /* ring toward a goal: frac 0..1 today and after */
  ring(o){
    const S = o.size || 150, cx = S / 2, cy = S / 2, R = S / 2 - 6, r0 = R - 12, f = v => Math.max(0, Math.min(1, v)) * 2 * Math.PI;
    return `<svg class="chart" viewBox="0 0 ${S} ${S}" width="${S}" height="${S}" role="img" aria-label="${CH.esc(o.label || '')}">
      <path d="${CH.arc(cx, cy, r0, R, 0, 2 * Math.PI)}" class="g-rail"></path>
      ${o.today > 0 ? `<path d="${CH.arc(cx, cy, r0, R, 0, f(o.today))}" class="r-today"></path>` : ''}
      ${o.after != null ? `<path d="${CH.arc(cx, cy, r0 - 15, r0 - 5, 0, f(o.after))}" class="r-after"></path>` : ''}
      <text x="${cx}" y="${cy + 2}" text-anchor="middle" class="c-big">${CH.esc(o.big)}</text><text x="${cx}" y="${cy + 20}" text-anchor="middle" class="c-sub">${CH.esc(o.sub || '')}</text></svg>`;
  },
  /* waterfall: steps [{label, delta, tip}] from start to end; fmt formats a value */
  waterfall(o){
    const steps = o.steps, W = o.w || 320, rowH = 26, H = (steps.length + 2) * rowH + 8, L = 118, Rw = W - L - 56;
    let v = o.start; const vals = [o.start]; for(const s of steps){ v += s.delta; vals.push(v); }
    const lo = Math.min(...vals, o.lo ?? Infinity), hi = Math.max(...vals, o.hi ?? -Infinity), pad = (hi - lo) * 0.08 || Math.abs(hi) * 0.05 || 1, a = lo - pad, b = hi + pad, X = t => L + (t - a) / (b - a) * Rw;
    let y = 4, cur = o.start, out = '';
    const bar = (x0, x1, cls, tip) => `<rect x="${Math.min(x0, x1)}" y="${y + 6}" width="${Math.max(2, Math.abs(x1 - x0))}" height="${rowH - 12}" rx="3" class="${cls}" data-tip="${CH.esc(tip)}"></rect>`;
    out += `<text x="0" y="${y + 17}" class="w-l">${CH.esc(o.startLab)}</text>${bar(X(a), X(o.start), 'w-total', o.startLab + ': ' + o.fmt(o.start))}<text x="${W}" y="${y + 17}" text-anchor="end" class="w-v">${o.fmt(o.start)}</text>`; y += rowH;
    for(const s of steps){ const n = cur + s.delta;
      out += `<text x="0" y="${y + 17}" class="w-l">${CH.esc(s.label.length > 19 ? s.label.slice(0, 18) + '…' : s.label)}</text>${bar(X(cur), X(n), s.delta >= 0 ? (o.upGood ? 'w-good' : 'w-bad') : (o.upGood ? 'w-bad' : 'w-good'), s.tip || s.label)}<text x="${W}" y="${y + 17}" text-anchor="end" class="w-v">${o.dfmt(s.delta)}</text>`;
      cur = n; y += rowH; }
    out += `<text x="0" y="${y + 17}" class="w-l b">${CH.esc(o.endLab)}</text>${bar(X(a), X(cur), 'w-total end', o.endLab + ': ' + o.fmt(cur))}<text x="${W}" y="${y + 17}" text-anchor="end" class="w-v b">${o.fmt(cur)}</text>`;
    const bands = o.band ? `<rect x="${X(o.band[0])}" y="0" width="${Math.max(0, X(o.band[1]) - X(o.band[0]))}" height="${H}" class="w-band"></rect>` : '';
    return `<svg class="chart" viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px" role="img" aria-label="${CH.esc(o.label || 'Waterfall')}">${bands}${out}</svg>`;
  },
  /* dumbbell rows: [{label, a, b, t, tipA, tipB}] on a shared 0..max scale */
  dumbbell(rows, o = {}){
    const W = o.w || 520, rowH = 30, H = rows.length * rowH + 22, L = o.left || 150, R = 70, max = o.max || Math.max(...rows.flatMap(r => [r.a, r.b ?? r.a, r.t ?? 0])) * 1.08 || 1, min = o.min ?? 0;
    const X = v => L + (v - min) / (max - min) * (W - L - R);
    const ticks = [min, (min + max) / 2, max];
    return `<svg class="chart" viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px" role="img" aria-label="${CH.esc(o.label || '')}">
      ${ticks.map(t => `<line x1="${X(t)}" x2="${X(t)}" y1="0" y2="${H - 18}" class="grid"></line><text x="${X(t)}" y="${H - 4}" text-anchor="middle" class="c-ax">${CH.esc(o.fmt ? o.fmt(t) : t)}</text>`).join('')}
      ${rows.map((r, i) => { const y = i * rowH + 15; return `<text x="0" y="${y + 4}" class="w-l">${CH.esc(r.label)}</text>
        ${r.t != null ? `<line x1="${X(r.t)}" x2="${X(r.t)}" y1="${y - 9}" y2="${y + 9}" class="d-target" data-tip="${CH.esc(r.tipT || '')}"></line>` : ''}
        ${r.b != null && Math.abs(r.b - r.a) > 1e-9 ? `<line x1="${X(r.a)}" x2="${X(r.b)}" y1="${y}" y2="${y}" class="d-link"></line>` : ''}
        <circle cx="${X(r.a)}" cy="${y}" r="5.5" class="d-a" data-tip="${CH.esc(r.tipA || '')}"></circle>${r.b != null ? `<circle cx="${X(r.b)}" cy="${y}" r="5.5" class="d-b" data-tip="${CH.esc(r.tipB || '')}"></circle>` : ''}
        <text x="${W}" y="${y + 4}" text-anchor="end" class="w-v">${CH.esc(r.val || '')}</text>`; }).join('')}</svg>`;
  },
};
/* one tooltip for every chart */
(function(){
  const tip = document.createElement('div'); tip.id = 'tip'; tip.setAttribute('role', 'tooltip'); document.addEventListener('DOMContentLoaded', () => document.body.appendChild(tip));
  document.addEventListener('mousemove', e => { const t = e.target.closest && e.target.closest('[data-tip]'); if(!t || !t.dataset.tip){ tip.style.opacity = 0; return; }
    tip.textContent = t.dataset.tip; tip.style.opacity = 1; const x = Math.min(e.clientX + 14, innerWidth - tip.offsetWidth - 8), y = Math.min(e.clientY + 14, innerHeight - tip.offsetHeight - 8); tip.style.left = x + 'px'; tip.style.top = y + 'px'; });
})();

/* ---------- workspace charts: tolerance bands, line with a target, decision tree ---------- */
Object.assign(CH, {
  /* dumbbell rows with a tolerance band per row: rows [{label, a, t, lo, hi, val, out}] */
  bands(rows, o = {}){
    const W = o.w || 520, rowH = 30, H = rows.length * rowH + 22, L = o.left || 140, R = 84, max = o.max || Math.max(...rows.flatMap(r => [r.a, r.hi ?? r.t])) * 1.08 || 1, min = 0;
    const X = v => L + (v - min) / (max - min) * (W - L - R), ticks = [0, max / 2, max];
    return `<svg class="chart" viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px" role="img" aria-label="${CH.esc(o.label || '')}">
      ${ticks.map(t => `<line x1="${X(t)}" x2="${X(t)}" y1="0" y2="${H - 18}" class="grid"></line><text x="${X(t)}" y="${H - 4}" text-anchor="middle" class="c-ax">${CH.esc(o.fmt ? o.fmt(t) : t)}</text>`).join('')}
      ${rows.map((r, i) => { const y = i * rowH + 15, lo = Math.max(0, r.lo); return `<text x="0" y="${y + 4}" class="w-l">${CH.esc(r.label)}</text>
        <rect x="${X(lo)}" y="${y - 8}" width="${Math.max(2, X(r.hi) - X(lo))}" height="16" rx="4" class="b-band" data-tip="${CH.esc(`tolerance ${o.fmt(lo)}–${o.fmt(r.hi)}`)}"></rect>
        <line x1="${X(r.t)}" x2="${X(r.t)}" y1="${y - 9}" y2="${y + 9}" class="d-target" data-tip="${CH.esc('CIO target ' + o.fmt(r.t))}"></line>
        <line x1="${X(r.t)}" x2="${X(r.a)}" y1="${y}" y2="${y}" class="d-link"></line>
        <circle cx="${X(r.a)}" cy="${y}" r="6" class="${r.out ? 'b-out' : 'b-in'}" data-tip="${CH.esc(`today ${o.fmt(r.a)}${r.out ? ' · outside the band' : ''}`)}"></circle>
        <text x="${W}" y="${y + 4}" text-anchor="end" class="w-v">${CH.esc(r.val || '')}</text>`; }).join('')}</svg>`;
  },
  /* simple line over years with a threshold: pts [{x, y, tip}] */
  line(pts, o = {}){
    const W = o.w || 520, H = o.h || 200, L = 44, B = 26, T = 10, Rr = 12, xs = pts.map(p => p.x), maxY = Math.max(o.th || 0, ...pts.map(p => p.y)) * 1.12 || 1;
    const X = i => L + (pts.length > 1 ? i / (pts.length - 1) : 0.5) * (W - L - Rr), Y = v => T + (1 - v / maxY) * (H - T - B);
    const path = pts.map((p, i) => `${i ? 'L' : 'M'}${X(i)},${Y(p.y)}`).join(''), area = path + `L${X(pts.length - 1)},${Y(0)}L${X(0)},${Y(0)}Z`;
    const ticks = [0, maxY / 2, maxY];
    return `<svg class="chart" viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px" role="img" aria-label="${CH.esc(o.label || '')}">
      ${ticks.map(t => `<line x1="${L}" x2="${W - Rr}" y1="${Y(t)}" y2="${Y(t)}" class="grid"></line><text x="${L - 6}" y="${Y(t) + 3}" text-anchor="end" class="c-ax">${CH.esc(o.fmt(t))}</text>`).join('')}
      ${o.th != null ? `<line x1="${L}" x2="${W - Rr}" y1="${Y(o.th)}" y2="${Y(o.th)}" class="l-th"></line><text x="${W - Rr}" y="${Y(o.th) - 5}" text-anchor="end" class="c-ax">${CH.esc(o.thLab || '')}</text>` : ''}
      <path d="${area}" class="l-area"></path><path d="${path}" class="l-line"></path>
      ${pts.map((p, i) => `<circle cx="${X(i)}" cy="${Y(p.y)}" r="4.5" class="l-pt" data-tip="${CH.esc(p.tip || '')}"></circle><text x="${X(i)}" y="${H - 8}" text-anchor="middle" class="c-ax">${CH.esc(p.x)}</text>`).join('')}</svg>`;
  },
  /* decision path: steps [{q, a, yes, out}] then result; yes branch shows its outcome to the side */
  tree(steps, result, o = {}){
    const W = o.w || 640, rowH = 58, H = steps.length * rowH + 82, nx = 16, nw = 300, ox = 360, ow = W - ox - 8;
    const cut = (t, n) => t.length > n ? t.slice(0, n - 1) + '\u2026' : t;
    const wrap2 = (t, n) => { if(t.length <= n) return [t]; let i = t.lastIndexOf(' ', n); if(i < 20) i = n; return [t.slice(0, i), cut(t.slice(i).trim(), n)]; };
    let out = '';
    steps.forEach((s, i) => { const y = 8 + i * rowH, on = s.yes;
      out += `<rect x="${nx}" y="${y}" width="${nw}" height="40" rx="8" class="t-q ${on ? 'on' : ''}"></rect><text x="${nx + 12}" y="${y + 17}" class="t-qt">${CH.esc(s.q)}</text><text x="${nx + 12}" y="${y + 32}" class="t-qa">${CH.esc(cut(s.a, 46))}</text>`;
      if(i < steps.length - 1 || true) out += `<line x1="${nx + 24}" x2="${nx + 24}" y1="${y + 40}" y2="${y + rowH}" class="t-ln"></line>`;
      out += `<line x1="${nx + nw}" x2="${ox}" y1="${y + 20}" y2="${y + 20}" class="t-ln ${on ? 'on' : ''}"></line><rect x="${ox}" y="${y + 4}" width="${ow}" height="32" rx="8" class="t-o ${on ? 'on' : ''}"></rect><text x="${ox + 10}" y="${y + 24}" class="t-ot ${on ? 'on' : ''}">${CH.esc(cut(s.out, 46))}</text>`; });
    const y = 8 + steps.length * rowH;
    const rl = wrap2(result, 92);
    out += `<rect x="${nx}" y="${y}" width="${W - nx - 8}" height="${rl.length > 1 ? 62 : 44}" rx="10" class="t-r"></rect><text x="${nx + 14}" y="${y + 18}" class="t-rk">RECOMMENDED PATH</text>${rl.map((t, i) => `<text x="${nx + 14}" y="${y + 35 + i * 17}" class="t-rt">${CH.esc(t)}</text>`).join('')}`;
    return `<svg class="chart" viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px" role="img" aria-label="Decision tree">${out}</svg>`;
  },
});
