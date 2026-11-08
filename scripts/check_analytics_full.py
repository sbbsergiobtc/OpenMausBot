with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py", "r", encoding="utf-8") as f:
    text = f.read()

analytics_idx = text.find('def get_analytics')
next_func_idx = text.find('def ', analytics_idx + 20)
print(text[analytics_idx:next_func_idx])
