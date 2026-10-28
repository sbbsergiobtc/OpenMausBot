import json

with open('/root/.openmausbot/routines.json') as f:
    d = json.load(f)

for r in d['routines']:
    print("ID:", r.get('id'))
    print("Name:", r.get('name'))
    print("Actor/Bot:", r.get('actorId'), r.get('botId'), r.get('target'))
    print("Schedule:", r.get('schedule'))
    print("-" * 50)
