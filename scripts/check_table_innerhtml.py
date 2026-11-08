with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html", "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = re.findall(r'(\.innerHTML\s*=\s*[^;]+table[^;]*;)', text, re.IGNORECASE)
print("Matches setting table innerHTML:", len(matches))
for m in matches[:10]:
    print("Match:", m)
