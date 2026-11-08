with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('return {')
# find return within get_analytics
analytics_idx = text.find('def get_analytics')
ret_idx = text.find('return {', analytics_idx)
print(text[ret_idx:ret_idx+1200])
