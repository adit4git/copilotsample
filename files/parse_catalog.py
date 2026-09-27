import json, re, sys
lines = open(sys.argv[1] if len(sys.argv)>1 else 'catalog.txt', encoding='utf-8').read().split('\n')
toc = "Large Cap Core|Large Cap Growth|Large Cap Value|Mid Cap Core|Mid Cap Growth|Mid Cap Value|Small Cap Core|Small Cap Growth|Small Cap Value|SMID Cap Core|SMID Cap Growth|SMID Cap Value|All Cap Core|All Cap Growth|All Cap Value|Global Core|Global Growth|Global Value|International Core|International Growth|International Value|Emerging Markets|Sector: Global Real Estate|Sector: Health|Sector: Infrastructure|Sector: Real Estate|Sector: Technology|Sector: Thematic|Multi-Style|Convertibles|Intermediate Duration|Intermediate Duration Core-Plus|Short/Limited Duration|Ultra Short|US Government Intermediate|US Government Short|Inflation Protected|Investment Grade Corporate|Corporate Ladders|High Yield Taxable|Multi-Style Fixed Income|Preferreds|Other Fixed Income|Muni National Long|Muni National Intermediate|Muni National Short|Laddered Muni|High Yield Muni|Commodities|Multi-Style Alternative Investments|Multi-Asset|Global Multi-Asset|LDI".split('|')
norm = lambda s: re.sub(r'[\s\-:]+',' ',s).strip().lower()
by_norm = {norm(t): t for t in toc}
ALIASES = {'emerging markets equity':'Emerging Markets','multi style equity':'Multi-Style','convertibles eq':'Convertibles','us govt intermediate':'US Government Intermediate','us govt short':'US Government Short'}
by_norm.update(ALIASES)
row = re.compile(r'^(?P<name>\S.*?\S)\s{2,}\$(?P<min>[\d,]+)\s{2,}(?P<tem>[DQT,]+|--)\s{2,}(?P<er>[\d.]+%|--)\s{2,}(?P<fsa>Yes|No|--)\s{2,}(?P<dm>DM/PAS|DM|PAS|--)\s*$')
TEM_SMS_KEYS = ['APERIO','PARAMETRIC','ACTIVE INDEX ADVISORS','CANVAS TAX','TAX ADVANTAGED','CUSTOM HARVEST','DIRECT INDEX','VANGUARD S&P U.S. DIVIDEND']
FI = {'Convertibles','Intermediate Duration','Intermediate Duration Core-Plus','Short/Limited Duration','Ultra Short','US Government Intermediate','US Government Short','Inflation Protected','Investment Grade Corporate','Corporate Ladders','High Yield Taxable','Multi-Style Fixed Income','Preferreds','Other Fixed Income','Muni National Long','Muni National Intermediate','Muni National Short','Laddered Muni','High Yield Muni','LDI'}
section, out = None, []
for ln in lines:
    s = ln.strip()
    if norm(s) in by_norm: section = by_norm[norm(s)]; continue
    if s.startswith('$') or not s or section is None: continue
    m = row.match(s)
    if not m: continue
    d = m.groupdict(); name = d['name']; codes = [] if d['tem']=='--' else d['tem'].split(',')
    er = None if d['er']=='--' else round(float(d['er'].rstrip('%'))*100,1)
    pas='PAS' in d['dm']; dm=d['dm'] in ('DM','DM/PAS')
    vehicle = 'DIRECT_INDEXING' if (dm and any(k in name for k in TEM_SMS_KEYS)) else ('ETF_MODEL' if er is not None and 'ETF' in name and 'MF' not in name else ('FUND_MODEL' if er is not None else 'SMA'))
    out.append({'name':name,'sleeve':section,'minimum':int(d['min'].replace(',','')),'tem_overlays':codes,'expense_ratio_bps':er,'vehicle':vehicle,'premium_access':pas,'fsa_eligible':d['fsa']=='Yes'})
json.dump(out, open('product-shelf-catalog.json','w'), indent=1)
print('parsed', len(out), 'products')
