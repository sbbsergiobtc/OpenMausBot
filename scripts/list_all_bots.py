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

print(f"Total bots encontrados en el servidor: {len(bots)}\n")
for b in bots:
    name = b.get('name', 'Sin nombre')
    title = b.get('title', '')
    sec = b.get('section', 'General')
    chief = b.get('chiefOfStaff')
    model = b.get('modelSelection', {})
    inst = model.get('instanceId', 'default')
    mname = model.get('model', 'default')
    soul_len = len(b.get('soul', ''))
    cwd = b.get('cwd', 'default')
    print(f"• Nombre: {name} | Cargo: {title} | Equipo: {sec} | Chief: {chief}")
    print(f"  Modelo: {inst} / {mname}")
    print(f"  CWD: {cwd} | Soul length: {soul_len} caracteres")
    print("-" * 60)

ssh.close()
