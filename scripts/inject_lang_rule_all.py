import paramiko
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS_IP = "169.58.230.132"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "4722ADwTjGA"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_IP, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)

_, stdout, _ = ssh.exec_command('curl -s http://127.0.0.1:8799/api/bots')
data = json.loads(stdout.read().decode('utf-8'))
bots = data.get('bots', [])

lang_rule = "REGLA SUPREMA DE IDIOMA: Hablas, interactúas y razonas SIEMPRE en Español (España - es-ES), de forma clara, profesional y directa. Todas las comunicaciones, análisis, código documentado y notas de Obsidian se redactan estrictamente en Español (España)."

updated_count = 0
for b in bots:
    if b.get('section') == 'AlgrokQuant' and b.get('name') != 'Nexus':
        soul = b.get('soul', '')
        if "Español (España" not in soul:
            new_soul = f"{lang_rule}\n\n{soul}"
            bot_id = b['id']
            # Patch soul
            sftp = ssh.open_sftp()
            with sftp.file(f"/root/patch_{bot_id}.json", "w") as f:
                f.write(json.dumps({"soul": new_soul}))
            sftp.close()
            ssh.exec_command(f"curl -s -X PATCH http://127.0.0.1:8799/api/bots/{bot_id} -H 'Content-Type: application/json' -d @/root/patch_{bot_id}.json && rm /root/patch_{bot_id}.json")
            print(f"✅ Regla de Español (España) inyectada en {b.get('name')}")
            updated_count += 1
        else:
            print(f"✓ {b.get('name')} ya tiene la regla de Español (España).")

print(f"\nFinalizado. Bots actualizados: {updated_count}")
ssh.close()
