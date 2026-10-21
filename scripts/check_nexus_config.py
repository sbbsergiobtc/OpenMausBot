import sys
import paramiko
import json

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """python3 -c "
import json
with open('/root/.openmausbot/bots.json') as f:
    bots = json.load(f)
for b in bots:
    if b.get('name') == 'Nexus':
        print(json.dumps({k: v for k, v in b.items() if k != 'soul'}, indent=2))
" """
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='replace'))
ssh.close()
