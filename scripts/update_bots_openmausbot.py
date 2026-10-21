import sys
import paramiko
import json

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """python3 -c "
import json

with open('/root/.openmausbot/bots.json', 'r', encoding='utf-8') as f:
    bots = json.load(f)

for b in bots:
    soul = b.get('soul', '')
    # Reemplazar cualquier referencia remanente a tokens del plan o grok
    soul = soul.replace('no agotar los tokens del plan.', 'operativa optimizada y continua en OpenMausBot (motor Gemini 3.8 Flash High sin coste ni límites de tokens de X/Grok).')
    soul = soul.replace('no agotar los tokens del plan Premium de X.', 'operativa optimizada y continua en OpenMausBot (motor Gemini 3.8 Flash High sin coste ni límites de tokens de X/Grok).')
    if b.get('name') == 'Nexus':
        if 'OpenMausBot' not in soul:
            soul = soul.replace(
                'Tu misión es construir y dirigir un enjambre ligero de agentes de inteligencia artificial para generar',
                'Tu misión es construir y dirigir un enjambre ligero de agentes de inteligencia artificial en OpenMausBot (motor Gemini 3.8 Flash High) para generar'
            )
    b['soul'] = soul

with open('/root/.openmausbot/bots.json', 'w', encoding='utf-8') as f:
    json.dump(bots, f, indent=2, ensure_ascii=False)

print('bots.json actualizado correctamente con OpenMausBot.')
" """
stdin, stdout, stderr = ssh.exec_command(cmd)
print("OUT:", stdout.read().decode('utf-8', errors='replace'))
print("ERR:", stderr.read().decode('utf-8', errors='replace'))
ssh.close()
