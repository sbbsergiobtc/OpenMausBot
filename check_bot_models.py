import json

with open('/root/.openmausbot/bots.json') as f:
    d = json.load(f)

items = d if isinstance(d, list) else d.get('bots', list(d.values()))
for b in items:
    if isinstance(b, dict):
        print(f"Bot: {b.get('name')} | Model: {b.get('model')} | Engine: {b.get('engine')} | Provider: {b.get('provider')}")
