import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html", "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'backtest', text, re.IGNORECASE)]
print(f"Total 'backtest' mentions: {len(matches)}")
# find section ids
sections = re.findall(r'<section[^>]*id=["\']([^"\']+)["\']|<div[^>]*id=["\']([^"\']*(?:backtest|report|strat)[^"\']*)["\']', text, re.IGNORECASE)
print("Sections/divs found:", sections[:15])
