import urllib.request, json
d = json.loads(urllib.request.urlopen('http://127.0.0.1:8080/api/chart/STRAT-20261028-035').read().decode())
print("Total markers:", len(d['markers']))
for m in d['markers'][:6]:
    print(f"Shape: {m['shape']} | Color: {m['color']} | Text: {m['text']}")
