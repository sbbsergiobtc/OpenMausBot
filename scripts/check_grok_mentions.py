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
    name = b.get('name')
    soul = b.get('soul', '')
    has_grok = 'grok' in soul.lower() or 'premium' in soul.lower()
    print(f'Bot {name}: contains grok/premium={has_grok}')
    if has_grok:
        lines = [line for line in soul.splitlines() if 'grok' in line.lower() or 'premium' in line.lower() or 'x' in line.lower()]
        for l in lines:
            print('  ->', l)
" """
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='replace'))
ssh.close()
