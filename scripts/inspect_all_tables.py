import re

with open(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Find all tables with thead and tbody
table_pattern = re.compile(r'<table([^>]*)>(.*?)</table>', re.DOTALL)
tables = table_pattern.findall(text)

print(f"Total tables found: {len(tables)}")
for i, (attrs, content) in enumerate(tables):
    # find id in attrs
    id_m = re.search(r'id=["\']([^"\']+)["\']', attrs)
    table_id = id_m.group(1) if id_m else f"table-unnamed-{i+1}"
    
    # find tbody id
    tbody_m = re.search(r'<tbody[^>]*id=["\']([^"\']+)["\']', content)
    tbody_id = tbody_m.group(1) if tbody_m else "no-tbody-id"
    
    # count th
    ths = re.findall(r'<th([^>]*)>(.*?)</th>', content, re.DOTALL)
    th_texts = [re.sub(r'<[^>]+>', '', th[1]).strip() for th in ths]
    print(f"[{i+1}] Table ID: {table_id} | Tbody ID: {tbody_id} | Columns ({len(th_texts)}): {th_texts[:5]}")
