with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html", "r", encoding="utf-8") as f:
    content = f.read()

print("File size:", len(content))
print("Has Motion CDN:", "cdn.jsdelivr.net/npm/motion@" in content)
print("Has AlgrokTableColumnReorderController:", "AlgrokTableColumnReorderController" in content)

# Check all 11 tables have id
ids = [
    'table-portfolio', 'table-trades', 'table-ft-active', 'table-ft-orders',
    'table-ft-trades', 'table-ql-matrix', 'table-orch-ab', 'table-tri-facet',
    'table-strategies', 'table-journal', 'table-accounts'
]
for tid in ids:
    found = f'id="{tid}"' in content
    print(f"Table ID '{tid}': {found}")
