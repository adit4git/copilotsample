"""Put plain-JSON data into the standalone Atlas HTML (gzip + base64, as the page expects).
Usage: python3 embed_data.py atlas-standalone-data.json atlas-tour-standalone-scoped.html
"""
import sys, json, gzip, base64, re
data_file, html_file = sys.argv[1], sys.argv[2]
data = json.load(open(data_file, encoding='utf-8'))                      # fails loudly if the JSON is damaged
blob = base64.b64encode(gzip.compress(json.dumps(data, separators=(',', ':')).encode(), 9)).decode()
html = open(html_file, encoding='utf-8').read()
pat = re.compile(r'(<script type="text/plain" id="atlas-data" data-encoding="gzip-base64">)[^<]*(</script>)')
if len(pat.findall(html)) != 1: sys.exit('could not find exactly one atlas-data block in the HTML')
open(html_file, 'w', encoding='utf-8').write(pat.sub(lambda m: m.group(1) + blob + m.group(2), html))
print('embedded', len(json.dumps(data)), 'bytes of JSON into', html_file)
