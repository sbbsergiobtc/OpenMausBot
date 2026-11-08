with open(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = '@app.get("/api/ping")'
replacement = """try:
    from jev.news_risk_filter import get_macro_risk_status, check_news_blackout
except Exception as e:
    get_macro_risk_status = None
    check_news_blackout = None


@app.get("/api/macro_news_risk")
def get_macro_news_risk():
    if get_macro_risk_status is not None:
        return get_macro_risk_status()
    return {"policy_enabled": True, "active_blackout": None, "upcoming_events": []}


@app.get("/api/ping")"""

if target in text:
    text = text.replace(target, replacement, 1)
    with open(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("SUCCESS: /api/macro_news_risk added")
else:
    print("ERROR: Target not found")

import py_compile
py_compile.compile(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py')
print("Compiled successfully!")
