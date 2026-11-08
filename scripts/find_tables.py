import re

with open(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

tables = re.findall(r'<table[^>]*id=["\']([^"\']+)["\']', text)
print('Tables with id:', tables)
all_tables = len(re.findall(r'<table', text))
print('Total <table> elements:', all_tables)

# Let's find classes or surrounding sections for all tables
matches = re.finditer(r'<table([^>]*)>', text)
for i, m in enumerate(matches):
    attrs = m.group(1)
    print(f'Table {i+1}: {attrs[:100]}...')
