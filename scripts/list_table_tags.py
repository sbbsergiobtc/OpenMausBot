import re

with open(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

table_pattern = re.compile(r'(<table[^>]*>)(.*?)(<tbody[^>]*id=["\']([^"\']+)["\'])', re.DOTALL)
for i, m in enumerate(table_pattern.finditer(text)):
    table_tag = m.group(1)
    tbody_id = m.group(4)
    print(f"Table {i+1}: {table_tag} -> tbody: {tbody_id}")
