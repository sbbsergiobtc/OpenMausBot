import json
from datetime import datetime

with open('/root/.openmausbot/routines.json', 'r') as f:
    d = json.load(f)

print("Total runs in routines.json:", len(d.get('runs', [])))
recent_runs = d.get('runs', [])[-10:]
for r in recent_runs:
    started = r.get('startedAt') or r.get('createdAt')
    dt_str = datetime.fromtimestamp(started / 1000).strftime('%Y-%m-%d %H:%M:%S') if started else 'N/A'
    routine_id = r.get('routineId')
    status = r.get('status')
    error = r.get('error')
    print(f"Run {r.get('id')}: Routine={routine_id} | Date={dt_str} | Status={status} | Error={error}")
