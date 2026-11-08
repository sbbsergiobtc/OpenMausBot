import re

with open(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

table_pattern = re.compile(r'(<table[^>]*>)(.*?)(</table>)', re.DOTALL)
for i, m in enumerate(table_pattern.finditer(text)):
    table_content = m.group(2)
    tbody_m = re.search(r'<tbody[^>]*id=["\']([^"\']+)["\']', table_content)
    tbody_id = tbody_m.group(1) if tbody_m else f"no-tbody-{i+1}"
    thead_m = re.search(r'<thead[^>]*>(.*?)</thead>', table_content, re.DOTALL)
    if thead_m:
        tr_count = len(re.findall(r'<tr', thead_m.group(1)))
        print(f"Table {i+1} ({tbody_id}): thead has {tr_count} <tr> rows")
    else:
        print(f"Table {i+1} ({tbody_id}): NO thead")
