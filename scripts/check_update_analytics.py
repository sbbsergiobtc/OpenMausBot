import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('function updateAnalyticsUI(')
print(text[idx:idx+3000])
