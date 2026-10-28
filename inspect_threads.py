import sqlite3

conn = sqlite3.connect("/root/.openmausbot/messages.db")
c = conn.cursor()
rows = c.execute("SELECT text FROM messages WHERE thread_id = '24c63d68-25ea-48df-a739-aa83a4061d05' AND text LIKE '%A la atención de Sergio%'").fetchall()
for r in rows:
    print(r[0])
