import re

with open(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.finditer(r'<table([^>]*)>', text)
for i, m in enumerate(matches):
    start = max(0, m.start() - 200)
    end = min(len(text), m.end() + 200)
    snippet = text[start:end]
    # find closest id or heading before table
    pre = text[max(0, m.start()-500):m.start()]
    h_match = re.findall(r'<h[1-6][^>]*>([^<]+)</h[1-6]>', pre)
    id_match = re.findall(r'id=["\']([^"\']+)["\']', pre)
    heading = h_match[-1] if h_match else 'No heading'
    closest_id = id_match[-1] if id_match else 'No id'
    print(f"Table {i+1} | Nearest ID: {closest_id} | Heading: {heading}")
