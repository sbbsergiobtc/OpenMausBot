from pathlib import Path
import re

with open("scripts/prop_firm_forward_test_daemon.py", "r", encoding="utf-8") as f:
    daemon_code = f.read()

# Look for strategy definitions or interval
matches = re.findall(r"'interval':\s*'([^']+)'", daemon_code)
print("Intervals found in daemon:", set(matches))

# Look for ticker_yf or strategy dicts
lines = daemon_code.split('\n')
for idx, l in enumerate(lines):
    if 'STRATEGIES_CONFIG' in l or 'ACTIVE_FORWARD_MODELS' in l or 'STRATEGIES =' in l or 'CONFIG =' in l:
        print(f"Line {idx+1}: {l}")
        for j in range(idx, min(len(lines), idx+50)):
            print(lines[j])
        break
