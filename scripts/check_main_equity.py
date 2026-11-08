import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html", "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'mainEquityChart', text)]
for idx in matches[:5]:
    print(text[max(0, idx-100):idx+300])
    print("="*40)
