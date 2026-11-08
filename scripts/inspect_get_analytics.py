with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('def get_analytics')
print(text[idx:idx+1500])
