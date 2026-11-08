import re

with open(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'(<tbody id="portfolio-table-tbody">)', text)
if m:
    pos = m.start()
    thead_snippet = text[max(0, pos-1200):pos]
    print(thead_snippet)
