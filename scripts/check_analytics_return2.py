with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py", "r", encoding="utf-8") as f:
    text = f.read()

analytics_idx = text.find('def get_analytics')
ret2_idx = text.rfind('return {', analytics_idx, analytics_idx + 6000)
print(text[ret2_idx:ret2_idx+1500])
