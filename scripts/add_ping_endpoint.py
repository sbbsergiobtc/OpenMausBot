with open(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = '@app.get("/api/summary")'
replacement = """@app.get("/api/ping")
def get_ping():
    return {"status": "ok", "timestamp_utc": datetime.now(timezone.utc).isoformat()}


@app.get("/api/summary")"""

if target in text:
    text = text.replace(target, replacement, 1)
    with open(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("SUCCESS: /api/ping added to backend.py")
else:
    print("ERROR: Target not found")

import py_compile
py_compile.compile(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py')
print("Syntax compiled successfully")
