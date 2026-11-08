with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html", "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = re.findall(r'<table[^>]*>', text)
for i, m in enumerate(matches):
    print(f"{i+1}: {m}")
