import json
data = open('/tmp/work/cio/data.json').read()
html = open('/tmp/work/cio/template.html').read().replace('/*DATA*/null', data)
open('/tmp/work/cio/cio-gap-views.html', 'w').write(html)
print(len(html))
