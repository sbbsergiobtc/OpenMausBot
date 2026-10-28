import sqlite3, json

conn = sqlite3.connect('/root/.openmausbot/messages.db')
c = conn.cursor()
c.execute("SELECT id, at, role, kind, text, json FROM messages WHERE thread_id='153b98ad-fac8-4aab-a12d-bc3f3eb4e305' ORDER BY rowid DESC LIMIT 5")
rows = c.fetchall()
for r in reversed(rows):
    print("=" * 60)
    print("ID:", r[0], "Role:", r[2], "Kind:", r[3])
    if r[4]:
        print("Text:", r[4][:200])
    if r[5]:
        try:
            parsed = json.loads(r[5])
            print("JSON summary:", list(parsed.keys()) if isinstance(parsed, dict) else type(parsed))
            if isinstance(parsed, dict) and 'tool' in parsed:
                print("Tool call:", parsed.get('tool'), parsed.get('args'))
            elif isinstance(parsed, dict) and 'command' in parsed:
                print("Command:", parsed.get('command')[:150])
            elif isinstance(parsed, dict) and 'output' in parsed:
                print("Output:", str(parsed.get('output'))[:200])
            elif isinstance(parsed, dict) and 'text' in parsed:
                print("Parsed text:", parsed.get('text')[:200])
            else:
                print("JSON preview:", str(parsed)[:250])
        except:
            print("Raw json:", str(r[5])[:200])
