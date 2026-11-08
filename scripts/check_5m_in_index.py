with open("dashboard/templates/index.html", "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'5m|1m|15m|1h|2h|4h|table-ft-active', text)]
print("Matches in index.html:", len(matches))

# Let's inspect where table-ft-active is populated in index.html
pos = text.find('table-ft-active')
print("table-ft-active at:", pos)
if pos != -1:
    print(text[pos-200:pos+1500])
