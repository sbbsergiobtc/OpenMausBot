import json

with open('/root/.openmausbot/routines.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Keys en routines.json:", list(data.keys()))
for k, v in data.items():
    print(f"Key: {k} -> Type: {type(v)}")
    if isinstance(v, list):
        print(f"  Longitud lista: {len(v)}")
        for idx, elem in enumerate(v):
            if isinstance(elem, dict):
                print(f"  [{idx}] Name: {elem.get('name')} | Enabled: {elem.get('enabled', elem.get('active'))} | Schedule: {elem.get('schedule')} | Cron: {elem.get('cron')}")
            else:
                print(f"  [{idx}] {elem}")
    elif isinstance(v, dict):
        print(f"  Dict keys: {list(v.keys())}")
        print(f"  Name: {v.get('name')} | Schedule: {v.get('schedule')}")
