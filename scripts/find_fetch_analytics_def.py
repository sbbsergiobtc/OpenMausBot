import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html", "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'async function fetchAnalyticsData', text)]
for idx in matches:
    print("Found at:", idx)
    print(text[idx:idx+3500])
