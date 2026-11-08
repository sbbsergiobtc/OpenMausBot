import re

with open(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

table_pattern = re.compile(r'(<table[^>]*>)(.*?)(</table>)', re.DOTALL)
for i, m in enumerate(table_pattern.finditer(text)):
    table_tag = m.group(1)
    table_content = m.group(2)
    tbody_m = re.search(r'<tbody[^>]*id=["\']([^"\']+)["\']', table_content)
    tbody_id = tbody_m.group(1) if tbody_m else f"no-tbody-{i+1}"
    thead_m = re.search(r'<thead[^>]*>(.*?)</thead>', table_content, re.DOTALL)
    has_thead = "YES" if thead_m else "NO"
    ths_count = len(re.findall(r'<th', thead_m.group(1))) if thead_m else 0
    print(f"Table {i+1}: {table_tag} | tbody: {tbody_id} | thead: {has_thead} ({ths_count} ths)")
