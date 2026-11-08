import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('/api/analytics')
print(text[idx:idx+2500])
