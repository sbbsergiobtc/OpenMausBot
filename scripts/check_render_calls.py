with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html", "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'renderCockpitPortfolioTable', text)]
for idx in matches:
    print(text[max(0, idx-100):idx+200])
    print("="*40)
