import re

with open(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

tbodies = re.findall(r'<tbody[^>]*id=["\']([^"\']+)["\']', text)
print('tbodies with id:', tbodies)
