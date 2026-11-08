with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('/api/trade_history')
print(text[idx:idx+1500])
