import re

with open(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's inspect where marked.min.js and apexcharts are loaded in <head>
m = re.search(r'(<!-- ApexCharts.*?-->.*?)(</head>)', text, re.DOTALL)
if m:
    print("Found head scripts area:")
    print(m.group(1)[:300])
