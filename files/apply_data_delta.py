"""Apply atlas-data-delta.json to the standalone Atlas data.

Either straight into the HTML (reads the embedded data, applies the delta, writes it back):
    python3 apply_data_delta.py atlas-data-delta.json atlas-tour-standalone-scoped.html
or to a plain-JSON copy of the data:
    python3 apply_data_delta.py atlas-data-delta.json atlas-standalone-data.json

Each delta names the data version it was built against ("base"); apply deltas in order. The script checks a
fingerprint (SHA-256) before and after, so it stops instead of writing a wrong result.
"""
import sys, json, gzip, base64, re, hashlib

delta_file, target = sys.argv[1], sys.argv[2]
delta = json.load(open(delta_file, encoding='utf-8'))
canon = lambda d: json.dumps(d, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
sha = lambda d: hashlib.sha256(canon(d).encode()).hexdigest()

is_html = target.lower().endswith(('.html', '.htm'))
PAT = re.compile(r'(<script type="text/plain" id="atlas-data" data-encoding="gzip-base64">)([^<]*)(</script>)')
if is_html:
    html = open(target, encoding='utf-8').read()
    m = PAT.findall(html)
    if len(m) != 1: sys.exit('could not find exactly one atlas-data block in the HTML')
    data = json.loads(gzip.decompress(base64.b64decode(m[0][1].strip())).decode('utf-8'))
else:
    data = json.load(open(target, encoding='utf-8'))

def norm(x):
    if isinstance(x, float):
        x = round(x, 6); return int(x) if x.is_integer() else x
    if isinstance(x, list): return [norm(v) for v in x]
    if isinstance(x, dict): return {k: norm(v) for k, v in x.items()}
    return x
data = norm(data)
now = sha(data)
if now == delta['result_sha256']: sys.exit('already up to date: nothing to do')
if now != delta['base_sha256']:
    sys.exit(f"this data is not the {delta.get('base', 'conversion-map')} version this delta was built against; apply the earlier delta first, or embed the full atlas-standalone-data.json instead")

def rep(x):
    if isinstance(x, str):
        for a, b in delta.get('replace_text', []): x = x.replace(a, b)
        return x
    if isinstance(x, list): return [rep(v) for v in x]
    if isinstance(x, dict): return {rep(k): rep(v) for k, v in x.items()}
    return x
data = rep(data)
for s in delta['set']:
    node = data
    for k in s['path'][:-1]: node = node[k] if isinstance(node, list) else node.setdefault(k, {})
    last = s['path'][-1]
    if isinstance(node, list) and last == len(node): node.append(s['value'])
    else: node[last] = s['value']
for p in delta.get('remove', []):
    node = data
    for k in p[:-1]: node = node[k]
    if isinstance(node, list): del node[p[-1]]
    else: node.pop(p[-1], None)

if sha(data) != delta['result_sha256']: sys.exit('result does not match the expected fingerprint; nothing was written')
if is_html:
    blob = base64.b64encode(gzip.compress(json.dumps(data, separators=(',', ':')).encode(), 9)).decode()
    open(target, 'w', encoding='utf-8').write(PAT.sub(lambda m: m.group(1) + blob + m.group(3), html))
else:
    open(target, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
print(f"applied {len(delta['set'])} changes and {len(delta.get('remove', []))} removals to {target}; fingerprint matches")
