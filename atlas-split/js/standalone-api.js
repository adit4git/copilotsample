/* Atlas standalone file: an in-page stand-in for the FastAPI server.
   Every response below was captured from the real Atlas backend, except product
   search and vehicle comparison, which are line-by-line ports of the Python
   (services.py) so any search or product combination works. */
(function(){
  const g = typeof window !== 'undefined' ? window : globalThis;
  let D = null;
  /* Data: atlas-data.js next to this file holds one JSON part per line ({"part": ..., "data": {...}}), in any order. */
  function dataProblem(msg){
    const show = () => { const old = document.getElementById('atlasDataProblem'); if(old){ old.textContent += ' ' + msg; return; }
      const b = document.createElement('div'); b.id = 'atlasDataProblem'; b.setAttribute('role', 'alert');
      b.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:99999;padding:10px 16px;font:13px/1.5 system-ui,sans-serif;background:#fff4e5;color:#7a4b00;border-bottom:1px solid #f0c27a';
      b.textContent = 'Data problem: ' + msg; document.body.appendChild(b); };
    if(document.body) show(); else document.addEventListener('DOMContentLoaded', show);
  }
  function mergeParts(text){
    const out = {}, seen = [], dup = [], bad = [], parts = [];
    text.split('\n').forEach((line, i) => {
      line = line.trim(); if(!line) return;
      try { parts.push(JSON.parse(line)); } catch(e){ bad.push(i + 1); }
    });
    parts.sort((a, b) => a.part < b.part ? -1 : a.part > b.part ? 1 : 0);
    for(const p of parts){
      if(seen.includes(p.part)){ dup.push(p.part); continue; }     // pasted twice: the copy is ignored
      seen.push(p.part);
      for(const [k, v] of Object.entries(p.data)){
        if(Array.isArray(v)) out[k] = (out[k] || []).concat(v);
        else if(v && typeof v === 'object' && out[k] && typeof out[k] === 'object') Object.assign(out[k], v);
        else out[k] = v;
      }
    }
    if(out._rules){                                       // rule map: rule numbers back to rule IDs and text, field numbers back to names
      const R = out._rules, F = out._fields || {}, S = out._shapes || {}, T = out._texts || [], C = out._codes || {};
      delete out._rules; delete out._fields; delete out._shapes; delete out._texts; delete out._codes;
      const fix = x => {
        if(typeof x === 'string') return x[0] === '¶' ? T[+x.slice(1)] : x;    // "¶n": text stored once in the map
        if(Array.isArray(x) && typeof x[0] === 'string' && x[0][0] === '§'){     // a record written as ["§n", values...]
          const keys = S[x[0].slice(1)], o = {};
          for(let i = 0; i < keys.length; i++) o[keys[i]] = x[i + 1];
          x = o;
        }
        if(Array.isArray(x)){ for(let i = 0; i < x.length; i++) x[i] = fix(x[i]); return x; }
        if(!x || typeof x !== 'object') return x;
        for(const k in x){
          if(k === 'field' && typeof x[k] === 'number') x[k] = F[x[k]];
          else if(k === 'missing_fields' && Array.isArray(x[k])) x[k] = x[k].map(v => typeof v === 'number' ? F[v] : v);
          else x[k] = fix(x[k]);
        }
        if(Object.keys(x).some(k => /\|\d+$/.test(k))){              // "SYMBOL|2": strategy type / service code
          const o = {};
          for(const k in x){ const m = k.match(/^(.*)\|(\d+)$/); o[m ? m[1] + '|' + C[m[2]] : k] = x[k]; }
          x = o;
        }
        const r = typeof x.rule_id === 'number' && R[x.rule_id];
        if(!r) return x;
        const o = {};
        for(const k of r.shapes[x._r || 0]) o[k] = k === 'rule_id' ? r.rule_id : (k in x) ? x[k] : structuredClone(r.text[k]);
        return o;
      };
      fix(out);
    }
    const core = parts.find(p => p.part === 'core');
    const missing = core ? core.expects.filter(n => !seen.includes(n)) : ['core'];
    const msgs = [];
    if(bad.length) msgs.push(`${bad.length} line(s) in atlas-data.js aren't complete JSON (lines ${bad.join(', ')}): re-copy those parts`);
    if(missing.length) msgs.push('missing parts: ' + missing.join(', '));
    if(msgs.length) dataProblem(msgs.join('. ') + '.');
    return out;
  }
  const ready = (async () => {
    if(typeof g.ATLAS_DATA_TEXT === 'string'){
      D = mergeParts(g.ATLAS_DATA_TEXT);
      if(Array.isArray(g.ATLAS_PRODUCTS)) D.products = g.ATLAS_PRODUCTS;          // the product list from atlas-products.js
      else if(!Array.isArray(D.products) || !D.products.length){ D.products = []; dataProblem('atlas-products.js (the product list) was not found next to this HTML file.'); }
      return;
    }
    const el = typeof document !== 'undefined' && document.getElementById('atlas-data');
    if(!el){ dataProblem('atlas-data.js was not found next to this HTML file.'); return; }
    if(el.dataset.encoding === 'gzip-base64'){
      const bin = Uint8Array.from(atob(el.textContent.trim()), c => c.charCodeAt(0));
      const txt = await new Response(new Blob([bin]).stream().pipeThrough(new DecompressionStream('gzip'))).text();
      D = JSON.parse(txt);
    } else D = JSON.parse(el.textContent);
  })();
  g.__atlasSetData = d => { D = d; };

  /* ---------- ports of services.py ---------- */
  const feeBps = p => p.fees.manager_bps != null ? p.fees.manager_bps : (p.fees.expense_ratio_bps != null ? p.fees.expense_ratio_bps : null);
  const label = p => p.name || p.ticker || p.product_id;
  const pyIn = (sub, s) => s.indexOf(sub) !== -1;
  const byId = () => { if(!D._pid){ D._pid = {}; D.products.forEach(p => D._pid[p.product_id] = p); } return D._pid; };
  const cmp = (a, b) => a < b ? -1 : a > b ? 1 : 0;

  function searchProducts(query, o){
    o = o || {};
    const q = String(query || '').trim().toLowerCase();
    let veh = o.vehicle ? o.vehicle.toUpperCase() : null;
    const words = q.replace(/,/g, ' ').split(/\s+/).filter(Boolean);
    const VW = {sma:'SMA', smas:'SMA', etf:'ETF', etfs:'ETF', direct:'DIRECT_INDEXING', indexing:'DIRECT_INDEXING'};
    let content = words.filter(w => !(w in VW));
    if(!veh && words.length && !content.length) veh = VW[words[0]];
    if(content.length) content = words;
    const out = [];
    for(const p of D.products){
      if(veh && p.vehicle !== veh) continue;
      if(o.sleeve && !pyIn(o.sleeve.toLowerCase(), p.sleeve.toLowerCase())) continue;
      if(o.max_minimum != null && p.minimum > o.max_minimum) continue;
      const fee = feeBps(p);
      if(o.max_fee_bps != null && (fee == null || fee > o.max_fee_bps)) continue;
      if(o.tlh_capable != null && p.tlh_capable !== o.tlh_capable) continue;
      const ticker = (p.ticker || '').toLowerCase(), name = label(p).toLowerCase();
      const manager = (p.manager || '').toLowerCase(), family = (p.fund_family || '').toLowerCase();
      const sl = p.sleeve.toLowerCase(), bench = (p.benchmark || '').toLowerCase();
      const m = D.models[p.model_id]; const ml = m ? m.label.toLowerCase() : '';
      let score = content.length ? 0 : 1;
      for(const w of content){
        if(ticker && w === ticker) score += 100;
        else if(ticker && ticker.startsWith(w)) score += 60;
        else if(pyIn(w, name) || pyIn(w, manager) || pyIn(w, family)) score += 30;
        else if(pyIn(w, sl) || pyIn(w, bench) || pyIn(w, ml)) score += 15;
      }
      if(score === 0) continue;
      if(content.length > 1 && pyIn(q, name)) score += 50;
      out.push({product_id:p.product_id, name:label(p), ticker:p.ticker ?? null, vehicle:p.vehicle, sleeve:p.sleeve, model_id:p.model_id ?? null,
        model_label: m ? m.label : null, fee_bps:fee, minimum:p.minimum, tlh_capable:p.tlh_capable, client_presentable:p.client_presentable,
        score, tem_overlays:p.tem_overlays ?? null, asset_class:p.asset_class ?? null, premium_access:p.premium_access || false,
        source:p.source || 'Atlas illustrative shelf'});
    }
    out.sort((a, b) => (b.score - a.score) || ((a.fee_bps ?? 1e9) - (b.fee_bps ?? 1e9)) || cmp(a.name, b.name));
    return out;
  }

  const RATE = 0.238, RANGE = [0.015, 0.03];
  const r2 = x => Math.round(x * 100) / 100, r4 = x => Math.round(x * 10000) / 10000;
  function breakeven(amount, sma, etf){
    const prem = Math.max(0, sma - etf), dollars = amount * prem / 10000;
    const need = dollars ? dollars / RATE : 0, pct = amount ? need / amount : 0;
    const assessment = pct <= RANGE[0] ? 'Below the typical first-year harvesting range \u2014 the fee premium is likely easy to offset.'
      : pct <= RANGE[1] ? 'Within the typical first-year harvesting range \u2014 plausible but not guaranteed to fully offset the fee premium.'
      : 'Above the typical first-year harvesting range \u2014 the fee premium may not be fully offset by harvesting alone in year one.';
    return {fee_premium_bps:prem, fee_premium_annual_dollars:r2(dollars), breakeven_harvest_needed_annual_dollars:r2(need),
            breakeven_harvest_needed_pct_of_assets:r4(pct), illustrative_typical_first_year_harvest_range_pct:RANGE.slice(), assessment};
  }
  const money = n => '$' + Math.round(n).toLocaleString('en-US');
  function comparisonRows(products, amount){
    const withPerf = products.filter(p => p.performance);
    const ref = withPerf.find(p => p.vehicle === 'SMA') || withPerf[0] || null;
    const rb = ref ? ref.performance.basis : null, ra = ref ? ref.performance.as_of : null;
    const sleeves = [...new Set(products.map(p => p.sleeve))].sort();
    const rows = products.map(p => {
      const perf = p.performance || null, fee = feeBps(p);
      const mismatch = !!(perf && ref && (perf.basis !== rb || perf.as_of !== ra));
      const row = {product_id:p.product_id, name:label(p), vehicle:p.vehicle, sleeve:p.sleeve, ticker:p.ticker ?? null, model_id:p.model_id ?? null,
        fee_bps:fee, annual_fee_dollars: fee != null ? r2(amount * fee / 10000) : null, minimum:p.minimum, meets_minimum: amount >= p.minimum,
        tlh_capable:p.tlh_capable, customizable:p.customizable, tem_overlays:p.tem_overlays ?? null, premium_access:p.premium_access || false,
        performance:perf, performance_basis_matches_reference:!mismatch, client_presentable:p.client_presentable,
        source:p.source || 'Atlas illustrative shelf', flags:[]};
      if(perf && (perf.type === 'BACKTEST' || perf.type === 'HYPOTHETICAL')) row.flags.push({code:'hypothetical', severity:'required', message:'Hypothetical/backtested performance \u2014 must not be shown to the client under any framing.'});
      if(mismatch) row.flags.push({code:'basis', severity:'review', message:`Performance basis (${perf.basis}, as of ${perf.as_of}) differs from the reference (${rb}, as of ${ra}); not a like-for-like comparison as shown.`});
      if(!perf) row.flags.push({code:'noperf', severity:'review', message:'No performance is published in the Strategy Catalog; see the Strategy Profile. Compare fees, minimums and overlay eligibility only.'});
      if(fee == null) row.flags.push({code:'nofee', severity:'review', message:'The Style Manager Rate is set in the Strategy Profile and is not listed in the catalog.'});
      if(p.premium_access) row.flags.push({code:'pas', severity:'review', message:'Premium Access Strategy: dual contract with the PAS Manager; TEM Overlay Services and TET are not available.'});
      if(!row.meets_minimum) row.flags.push({code:'minimum', severity:'required', message:`Amount (${money(amount)}) is below this implementation's ${money(p.minimum)} minimum.`});
      if(sleeves.length > 1) row.flags.push({code:'sleeves', severity:'review', message:`Selection spans ${sleeves.length} different sleeves \u2014 fees are comparable, performance is not.`});
      return row;
    });
    const etfs = products.filter(p => (p.vehicle === 'ETF' || p.vehicle === 'ETF_MODEL') && p.client_presentable && feeBps(p) != null);
    let cheap = null; for(const p of etfs) if(!cheap || feeBps(p) < feeBps(cheap)) cheap = p;
    const bes = [];
    if(cheap) for(const p of products)
      if(p !== cheap && p.tlh_capable && p.client_presentable && feeBps(p) != null && feeBps(p) > feeBps(cheap))
        bes.push(Object.assign(breakeven(amount, feeBps(p), feeBps(cheap)), {product_id:p.product_id, product_name:label(p), vs_product_id:cheap.product_id, vs_product_name:label(cheap)}));
    const primary = bes.find(b => byId()[b.product_id].vehicle === 'SMA') || bes[0] || null;
    return {rows, reference_basis:rb, reference_as_of:ra, sleeves, breakevens:bes, primary_breakeven:primary};
  }
  function contentFlags(doc){
    const f = [];
    if(doc.audience == null) f.push({severity:'review', message:'Content audience is not set; cannot confirm this is client-safe.'});
    else if(doc.audience !== 'CLIENT_APPROVED') f.push({severity:'advisor_only', message:`Audience is ${doc.audience} \u2014 for advisor use only, not client-presentable.`});
    if(doc.expires && doc.expires < D.today) f.push({severity:'expired', message:`Approval expired ${doc.expires} \u2014 do not use until re-approved.`});
    if(!doc.compliance_ref) f.push({severity:'review', message:'No compliance approval reference on file.'});
    return f;
  }
  function contentSearch(query, modelId, topics, limit){
    const qt = new Set(query.split(/\s+/).filter(w => w.length > 2).map(w => w.toLowerCase()));
    const hits = [];
    for(const doc of D.content){
      if(modelId && !(doc.related_models || []).includes(modelId)) continue;
      if(topics && !topics.some(t => (doc.topics || []).includes(t))) continue;
      const hay = Object.assign({title: doc.title}, doc.page_snippets || {});
      let bp = null, bs = 0, bt = null;
      for(const [page, text] of Object.entries(hay)){
        const tt = new Set(text.split(/\s+/).filter(Boolean).map(w => w.toLowerCase().replace(/^[.,()]+|[.,()]+$/g, '')));
        let s = 0; qt.forEach(w => { if(tt.has(w)) s++; });
        if(s > bs){ bp = page; bs = s; bt = text; }
      }
      if(bs === 0 && !(modelId || topics)) continue;
      const fl = contentFlags(doc);
      hits.push({doc_id:doc.doc_id, title:doc.title, audience:doc.audience ?? null, page: bp !== 'title' ? bp : null, snippet: bt || doc.title,
        score:bs, flags:fl, pdf_url: doc.pdf_id ? `/static/content-pdfs/${doc.pdf_id}.pdf` : null, pages:doc.pages ?? null,
        client_safe: doc.audience === 'CLIENT_APPROVED' && !fl.some(x => x.severity === 'expired' || x.severity === 'review')});
    }
    hits.sort((a, b) => (b.score - a.score) || cmp(a.doc_id, b.doc_id));
    return hits.slice(0, limit);
  }
  function vehicleBrief(hid, modelId, amount, pids){
    const hh = D.hh[hid];
    if(amount == null) amount = hh.incoming_capital ? hh.incoming_capital.amount : hh.aum;
    let products, lbl;
    if(pids && pids.length){
      const P = byId(); const miss = pids.filter(x => !P[x]); if(miss.length) throw new Error('Unknown product(s): ' + miss.join(', '));
      products = [...new Set(pids)].map(x => P[x]);
      const mids = new Set(products.map(p => p.model_id ?? null));
      const only = mids.size === 1 ? [...mids][0] : undefined;
      if(only && D.models[only]){
        modelId = only;
        const full = new Set(D.models[only].implementations), sel = new Set(products.map(p => p.product_id));
        const same = full.size === sel.size && [...full].every(x => sel.has(x));
        lbl = D.models[only].label + (same ? '' : ' (custom selection)');
      } else { modelId = null; lbl = 'Custom comparison'; }
    } else {
      if(!modelId) modelId = hh.current_model_id || 'research_core';
      if(!D.models[modelId]) throw new Error('Unknown research model: ' + modelId);
      products = D.models[modelId].implementations.filter(x => byId()[x]).map(x => byId()[x]);
      lbl = D.models[modelId].label;
    }
    const body = comparisonRows(products, amount);
    const comparison = {household_id:hid, model_id:modelId, model_label:lbl, amount, reference_basis:body.reference_basis, reference_as_of:body.reference_as_of,
      sleeves:body.sleeves, implementations:body.rows, breakevens:body.breakevens, breakeven_tax_alpha:body.primary_breakeven};
    const related = [...new Set(body.rows.map(r => r.model_id).filter(Boolean))].sort();
    const query = `${lbl} ETF SMA fees performance tax management`, seen = new Set(), all = [];
    for(const mid of (related.length ? related : [null]))
      for(const h of contentSearch(query, mid, ['vehicle_comparison','performance','research_models','tax_management'], 12))
        if(!seen.has(h.doc_id)){ seen.add(h.doc_id); all.push(h); }
    all.sort((a, b) => (b.score - a.score) || cmp(a.doc_id, b.doc_id));
    const client = all.filter(h => h.client_safe), advisor = all.filter(h => !h.client_safe);
    let sw = null, basis = null;
    if(hh.current_implementation === 'SMA'){
      const v = new Set(body.rows.map(r => r.vehicle).filter(x => x !== 'SMA')); if(!v.size) v.add('DIRECT_INDEXING');
      const target = v.has('DIRECT_INDEXING') ? 'directIndexing' : (v.size === 1 && v.has('ETF') ? 'dtlhOverlay' : 'directIndexing');
      basis = target === 'dtlhOverlay' ? 'Modeled as an ETF-only conversion (single stocks sold into a broad-market ETF), the closest existing scenario to moving SMA assets into ETFs.'
        : v.has('DIRECT_INDEXING') ? 'Modeled as a transition into Direct Indexing (a direct-indexing product is in the selection).'
        : 'Modeled as a transition into Direct Indexing, the closest existing full-sleeve replacement scenario.';
      sw = (D.transition[hid] || {})[target] || null; if(!sw) basis = null;
    }
    return {household_id:hid, model_id:comparison.model_id, incoming_capital:hh.incoming_capital ?? null, comparison, client_content:client, advisor_content:advisor,
      content_gap: client.length === 0,
      content_gap_message: client.length === 0 ? `No client-approved content found for the ${lbl} comparison. Logging a content-gap ticket to content/marketing.` : null,
      switching_cost_note: sw ? 'Existing SMA assets are a separate decision from the incoming capital \u2014 see the linked transition scenario for the cost of moving assets already invested, if that is also being considered.' : null,
      switching_cost_basis: basis, switching_cost: sw};
  }
  g.AtlasMock = {searchProducts, vehicleBrief, ready: () => ready, data: () => D};

  /* ---------- routes ---------- */
  const drafts = {};
  const norm = s => String(s || '').trim().toLowerCase().replace(/\s+/g, ' ');
  const reply = (obj, status) => new Response(JSON.stringify(obj), {status: status || 200, headers: {'Content-Type':'application/json'}});
  const realFetch = g.fetch ? g.fetch.bind(g) : null;
  g.fetch = async function(input, opt){
    const raw = typeof input === 'string' ? input : input.url;
    if(!raw.startsWith('/api/')) return realFetch(input, opt);
    await ready;
    const url = new URL(raw, 'http://atlas.local'), path = url.pathname, q = url.searchParams, seg = path.split('/').filter(Boolean);
    const method = (opt && opt.method || 'GET').toUpperCase(), body = opt && opt.body ? JSON.parse(opt.body) : {};
    try{
      if(path === '/api/meta') return reply(D.meta);
      if(path === '/api/book') return reply(D.book[q.get('fa') || 'dana'] || []);
      if(seg[1] === 'household') return D.household[seg[2]] ? reply(D.household[seg[2]]) : reply({detail:'Household not found'}, 404);
      if(seg[1] === 'verdict'){ const h = D.household[seg[2]], v = (h && h.verdicts && h.verdicts[seg[3]]) || (D.verdict[seg[2]] || {})[seg[3]];
        return v ? reply(v) : reply({detail:'Not found'}, 404); }
      if(seg[1] === 'composition') return reply(D.composition[seg[2]]);
      if(seg[1] === 'conversion'){ const c = (D.conversion || {})[seg[2]]; return c ? reply(c) : reply({detail:'Not included in this file'}, 404); }
      if(seg[1] === 'transition'){ const t = (D.transition[seg[2]] || {})[q.get('offering')]; return t ? reply(t) : reply({detail:'Not found'}, 404); }
      if(path === '/api/products/sleeves') return reply(D.sleeves);
      if(path === '/api/products/search'){
        const num = k => q.get(k) != null && q.get(k) !== '' ? Number(q.get(k)) : null;
        const all = searchProducts(q.get('q') || '', {vehicle:q.get('vehicle') || null, sleeve:q.get('sleeve') || null, max_minimum:num('max_minimum'),
          max_fee_bps:num('max_fee_bps'), tlh_capable: q.get('tlh_capable') == null ? null : q.get('tlh_capable') === 'true'});
        return reply({query:q.get('q') || '', results: all.slice(0, Number(q.get('limit') || 10)), total: all.length});
      }
      if(seg[1] === 'compare'){
        const pids = (q.get('products') || '').split(',').filter(Boolean);
        return reply(vehicleBrief(seg[2], q.get('model') || null, q.get('amount') ? Number(q.get('amount')) : null, pids.length ? pids : null));
      }
      if(seg[1] === 'draft'){
        const key = seg[2] + ':' + (body.kind || q.get('kind') || 'meeting_prep');
        if(seg[3] === 'decision'){
          const rec = drafts[key]; if(!rec) return reply({detail:'No draft yet for this household/kind'}, 404);
          if(body.action === 'approve') rec.status = 'approved';
          else if(body.action === 'decline') rec.status = 'declined';
          else if(body.action === 'edit'){ rec.content = body.edited_content; rec.status = 'edited_approved'; }
          rec.decided_at = new Date().toISOString(); rec.decided_by = body.decided_by; return reply(rec);
        }
        if(method === 'POST'){
          drafts[key] = {household_id:seg[2], kind:body.kind || 'meeting_prep', content:D.draft[seg[2]] || 'No draft available for this household in the preview.',
                         status:'pending', mode:'local-grounded', created_at:new Date().toISOString(), decided_at:null, decided_by:null};
          return reply(drafts[key]);
        }
        return drafts[key] ? reply(drafts[key]) : reply({detail:'No draft yet for this household/kind'}, 404);
      }
      if(path === '/api/agent'){
        const hit = (D.agent[body.fa || 'dana'] || {})[norm(body.message)];
        if(hit) return reply(hit);
        return reply({mode:'preview', usage:null, steps:[],
          content:"This standalone file has no Atlas server behind it, so Ask Atlas answers the prepared requests: the suggested prompts, the guide\u2019s examples, \u201cAsk Atlas about this\u201d on each screen, and the tour.\n\nTry one of those, or press **Show me around** in the top bar.",
          actions:[{type:'navigate', workspace:'guide', household_id:null, offering_id:null, product_ids:null, model_id:null, auto_open:false, label:'See everything Atlas can do', amount:null, shelf_filters:null}]});
      }
      return reply({detail:'Not available in the preview'}, 404);
    }catch(e){ return reply({detail:String(e.message || e)}, 404); }
  };
})();
