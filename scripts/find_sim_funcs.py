import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\jev\simulator.py", "r", encoding="utf-8") as f:
    text = f.read()

import re
funcs = re.findall(r'def\s+([a-zA-Z0-9_]+)', text)
print("Functions in simulator.py:", funcs)
