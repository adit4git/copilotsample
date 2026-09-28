"""build_data.py - builds every file in app/data/ from the tables in data/ and the strategy catalog.

Usage (from the kit folder):
    pdftotext -layout <strategy-catalog>.pdf catalog.txt
    python3 build_data.py <app_root> catalog.txt

Writes into <app_root>/app/data/: rule-store.json, households.json, fa-and-facts.json,
product-shelf.json, research-models.json, content-catalog.json. Each stage checks its own counts.
"""
import json, csv, re, sys, os
from pathlib import Path

# ======================= households + facts (from 5 CSV tables) =======================


def cell(v):
    if v == '': return None
    if v == 'True': return True
    if v == 'False': return False
    try:
        if '.' in v: return float(v)
        return int(v)
    except ValueError:
        return v

def reconstruct(table_dir='.'):
    rows = {}
    with open(f'{table_dir}/households_main.csv') as f:
        for r in csv.DictReader(f):
            hid = r['id']
            h = {
                'id': r['id'], 'name': r['name'], 'entity': r['entity'], 'segment': r['segment'],
                'advisor_id': r['advisor_id'],
                'aum': cell(r['aum']), 'rev': cell(r['rev']), 'since': cell(r['since']), 'risk': r['risk'], 'contact': r['contact'],
                'ytdReturn': cell(r['ytdReturn']), 'harvestable': cell(r['harvestable']), 'ytdRealizedGains': cell(r['ytdRealizedGains']),
                'target': {'equity':cell(r['target_equity']),'fixed':cell(r['target_fixed']),'alt':cell(r['target_alt']),'cash':cell(r['target_cash'])},
                'current': {'equity':cell(r['current_equity']),'fixed':cell(r['current_fixed']),'alt':cell(r['current_alt']),'cash':cell(r['current_cash'])},
                'concentration': [] if r['conc_label']=='' else [{'label':r['conc_label'],'pct':cell(r['conc_pct']),'threshold':cell(r['conc_threshold'])}],
                'cio': {'score':r['cio_score'],'view':r['cio_view'],'pub':r['cio_pub'],'diverge':r['cio_diverge']},
                'programs': {}, 'overlays': {},
                'notes': r['notes'],
            }
            if r['program']: h['program'] = r['program']
            h['nextMeeting'] = None if r['meet_type']=='' else {'inDays':cell(r['meet_days']),'type':r['meet_type'],'note':r['meet_note']}
            if r['current_model_id']: h['current_model_id'] = r['current_model_id']
            if r['current_implementation']: h['current_implementation'] = r['current_implementation']
            if r['tax_status']: h['tax_status'] = r['tax_status']
            if r['marginal_fed_rate']: h['marginal_fed_rate'] = cell(r['marginal_fed_rate'])
            if r['state']: h['state'] = r['state']
            if r['inc_amount']:
                h['incoming_capital'] = {'amount':cell(r['inc_amount']),'expected_date':r['inc_date'],'likelihood':r['inc_likelihood'],'source':r['inc_source'],'form':r['inc_form']}
            h['holdings'] = []
            rows[hid] = h

    with open(f'{table_dir}/holdings.csv') as f:
        for r in csv.DictReader(f):
            x = {'sym':r['sym'],'name':r['name'],'ac':r['ac'],'mv':cell(r['mv']),'cost':cell(r['cost'])}
            if r.get('type'): x['type'] = r['type']
            if r.get('lot_id'): x['lot_id'] = r['lot_id']
            rows[r['household_id']]['holdings'].append(x)

    with open(f'{table_dir}/enrollments.csv') as f:
        for r in csv.DictReader(f):
            rows[r['household_id']]['programs' if r['kind']=='program' else 'overlays'][r['offering_id']] = r['status']

    af = {}
    with open(f'{table_dir}/account_facts.csv') as f:
        reader = csv.DictReader(f)
        cols = [c for c in reader.fieldnames if c != 'household_id']
        for r in reader:
            d = {}
            for c in cols:
                v = r[c]
                if v == '': continue
                d[c] = None if v == '\x00NONE\x00' else (json.loads(v) if v.startswith('[') else cell(v))
            af[r['household_id']] = d

    oof = {}
    with open(f'{table_dir}/account_offering_facts.csv') as f:
        for r in csv.DictReader(f):
            v = r['value']
            v = None if v == '\x00NONE\x00' else cell(v)
            oof.setdefault(r['household_id'], {}).setdefault(r['offering_id'], {})[r['fact_key']] = v

    return rows, af, oof


KEY_ORDER = ['id','name','entity','segment','aum','rev','since','risk','contact','advisor_id','nextMeeting','ytdReturn','harvestable',
             'ytdRealizedGains','holdings','target','current','concentration','cio','programs','overlays','notes']
def households_list(rows):
    out = []
    for h in rows.values():
        ordered = {k: h[k] for k in KEY_ORDER}
        ordered.update({k: v for k, v in h.items() if k not in ordered})
        out.append(ordered)
    return out

# ======================= rule store (from 2 CSV tables) =======================



PACK_ID = 'atlas.tax-services.2026-09-20'
STATUS = 'POC_DRAFT_NOT_APPROVED_POLICY'

def build(offerings_csv='rule_store_offerings.csv', composition_csv='rule_store_composition.csv'):
    offerings = {}
    with open(offerings_csv, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['offering_id'] not in offerings:
                off = {'label': r['offering_label'], 'program_scope': json.loads(r['program_scope'])}
                if r['coverage_note']: off['coverage_note'] = r['coverage_note']
                off['rules'] = []
                offerings[r['offering_id']] = off
            off = offerings[r['offering_id']]
            rule = {
                'rule_id': r['rule_id'], 'effect': r['effect'],
                'predicate': json.loads(r['predicate_json']),
                'failure_class': r['failure_class'],
            }
            if r['routing']: rule['routing'] = r['routing']
            if r['scope_key']: rule['scope_key'] = r['scope_key']
            rule['message'] = r['message']
            rule['source_doc'] = json.loads(r['source_doc_json'])
            rule['compile_source'] = {'kind': r['compile_kind'], 'review_status': r['review_status']}
            off['rules'].append(rule)
    composition_rules = []
    with open(composition_csv, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            c = {'rule_id': r['rule_id'], 'relation': r['relation'], 'offerings': json.loads(r['offerings_json'])}
            if r['scope']: c['scope'] = r['scope']
            c['message'] = r['message']
            c['source_doc'] = json.loads(r['source_doc_json'])
            c['compile_source'] = {'kind': r['compile_kind'], 'review_status': r['review_status']}
            composition_rules.append(c)
    return {'pack_id': PACK_ID, 'status': STATUS, 'offerings': offerings, 'composition_rules': composition_rules}


# ======================= product shelf (illustrative CSV + catalog text) =======================


def unflat(row):
    out = {}
    for k, v in row.items():
        if v == '': continue
        cur = out; parts = k.split('.')
        for p in parts[:-1]: cur = cur.setdefault(p, {})
        cur[parts[-1]] = json.loads(v)
    return out
TOC = "Large Cap Core|Large Cap Growth|Large Cap Value|Mid Cap Core|Mid Cap Growth|Mid Cap Value|Small Cap Core|Small Cap Growth|Small Cap Value|SMID Cap Core|SMID Cap Growth|SMID Cap Value|All Cap Core|All Cap Growth|All Cap Value|Global Core|Global Growth|Global Value|International Core|International Growth|International Value|Emerging Markets|Sector: Global Real Estate|Sector: Health|Sector: Infrastructure|Sector: Real Estate|Sector: Technology|Sector: Thematic|Multi-Style|Convertibles|Intermediate Duration|Intermediate Duration Core-Plus|Short/Limited Duration|Ultra Short|US Government Intermediate|US Government Short|Inflation Protected|Investment Grade Corporate|Corporate Ladders|High Yield Taxable|Multi-Style Fixed Income|Preferreds|Other Fixed Income|Muni National Long|Muni National Intermediate|Muni National Short|Laddered Muni|High Yield Muni|Commodities|Multi-Style Alternative Investments|Multi-Asset|Global Multi-Asset|LDI".split('|')
norm = lambda s: re.sub(r'[\s\-:]+', ' ', s).strip().lower()
BY = {norm(t): t for t in TOC}
BY.update({'emerging markets equity':'Emerging Markets','multi style equity':'Multi-Style','convertibles eq':'Convertibles','us govt intermediate':'US Government Intermediate','us govt short':'US Government Short'})
ROW = re.compile(r'^(?P<name>\S.*?\S)\s{2,}\$(?P<min>[\d,]+)\s{2,}(?P<tem>[DQT,]+|--)\s{2,}(?P<er>[\d.]+%|--)\s{2,}(?P<fsa>Yes|No|--)\s{2,}(?P<dm>DM/PAS|DM|PAS|--)\s*$')
DI_KEYS = ['APERIO','PARAMETRIC','ACTIVE INDEX ADVISORS','CANVAS TAX','TAX ADVANTGED','TAX ADVANTAGED','TAX-ADVANTAGED','CUSTOM HARVEST','DIRECT INDEX','VANGUARD S&P U.S. DIVIDEND','TACS']
FI = {'Convertibles','Intermediate Duration','Intermediate Duration Core-Plus','Short/Limited Duration','Ultra Short','US Government Intermediate','US Government Short','Inflation Protected','Investment Grade Corporate','Corporate Ladders','High Yield Taxable','Multi-Style Fixed Income','Preferreds','Other Fixed Income','Muni National Long','Muni National Intermediate','Muni National Short','Laddered Muni','High Yield Muni','LDI'}
def catalog(path):
    out, section = [], None
    for ln in open(path, encoding='utf-8').read().split('\n'):
        s = ln.strip()
        if norm(s) in BY: section = BY[norm(s)]; continue
        if s.startswith('$') or not s or section is None: continue
        m = ROW.match(s)
        if not m: continue
        d = m.groupdict(); name = d['name']; codes = [] if d['tem']=='--' else d['tem'].split(',')
        er = None if d['er']=='--' else round(float(d['er'].rstrip('%'))*100, 1)
        pas = 'PAS' in d['dm']; dm = d['dm'] in ('DM','DM/PAS')
        if dm and any(k in name for k in DI_KEYS): veh = 'DIRECT_INDEXING'
        elif er is not None: veh = 'ETF_MODEL' if ('ETF' in name and 'MF' not in name) else 'FUND_MODEL'
        else: veh = 'SMA'
        out.append({'product_id': ('CAT-' + re.sub(r'[^A-Z0-9]+','-',name).strip('-'))[:80], 'vehicle': veh, 'model_id': None, 'sleeve': section,
            'asset_class': 'Fixed Income' if section in FI else ('Multi-Asset' if section in ('Multi-Asset','Global Multi-Asset') else ('Alternatives' if section in ('Commodities','Multi-Style Alternative Investments') else 'Equity')),
            'benchmark': '', 'name': name.title().replace('Etf','ETF').replace('Sma','SMA').replace('Cio ','CIO ').replace('Mf/','MF/').replace('(Pas)','(PAS)'), 'ticker': None,
            'fees': {'manager_bps': None, 'expense_ratio_bps': er, 'program_fee_applies': True,
                     'fee_note': 'Weighted fund expense ratio per catalog' if er is not None else 'Style Manager Rate set per Strategy Profile (not listed in catalog)'},
            'minimum': int(d['min'].replace(',','')), 'program_scope': ['IAP'], 'tem_overlays': codes,
            'tlh_capable': bool(set(codes) & {'Q','D'}) or veh == 'DIRECT_INDEXING', 'customizable': veh in ('SMA','DIRECT_INDEXING'),
            'in_kind_accepted': True, 'discretionary_manager': dm, 'premium_access': pas, 'fsa_eligible': d['fsa']=='Yes',
            'performance': None, 'client_presentable': True, 'source': 'MLIAP Strategy Catalog, June 2026'})
    seen = {}
    for p in out:
        if p['product_id'] in seen: seen[p['product_id']] += 1; p['product_id'] = f"{p['product_id']}-{seen[p['product_id']]}"
        else: seen[p['product_id']] = 1
    return out


def main(root, catalog_txt):
    here = Path(__file__).resolve().parent / 'data'
    out = Path(root) / 'app' / 'data'; out.mkdir(parents=True, exist_ok=True)
    w = lambda name, obj: json.dump(obj, open(out / name, 'w', encoding='utf-8'), indent=2)

    rs = build(str(here / 'rule_store_offerings.csv'), str(here / 'rule_store_composition.csv'))
    n = sum(len(o['rules']) for o in rs['offerings'].values())
    assert (len(rs['offerings']), n, len(rs['composition_rules'])) == (17, 112, 16), 'rule store counts wrong'
    w('rule-store.json', rs); print('rule-store.json      17 offerings, 112 rules, 16 composition rules')

    rows, af, oof = reconstruct(str(here))
    hh = households_list(rows); assert len(hh) == 25, 'expected 25 households'
    w('households.json', hh); print(f'households.json      {len(hh)} households, {sum(len(h["holdings"]) for h in hh)} holdings')

    cfg = json.load(open(here / 'fa_core.json', encoding='utf-8'))
    full = {'fa_profiles': cfg['fa_profiles'], 'account_facts': af, 'account_offering_facts': oof,
            'offering_minimums': cfg['offering_minimums'], 'requires_qualified_advisor': cfg['requires_qualified_advisor']}
    w('fa-and-facts.json', full); print('fa-and-facts.json    advisors, facts, minimums')

    illus = [unflat(r) for r in csv.DictReader(open(here / 'illustrative_products.csv', newline='', encoding='utf-8'))]
    cat = catalog(catalog_txt)
    assert len(cat) == 1097, f'catalog parse found {len(cat)} products, expected 1097 - different PDF edition?'
    w('product-shelf.json', illus + cat); print(f'product-shelf.json   {len(illus)} illustrative + {len(cat)} catalog')

    for n in ('research-models', 'content-catalog'):
        w(n + '.json', json.load(open(here / (n + '.json'), encoding='utf-8'))); print(f'{n}.json')

if __name__ == '__main__':
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
