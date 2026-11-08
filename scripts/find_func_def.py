with open(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'renderCockpitPortfolioTable', text)]
print("Matches found at indices:", matches)
for idx in matches:
    print("--- Match snippet ---")
    print(text[idx:idx+300])
