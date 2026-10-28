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
print(f'Total bots: {len(bots)}')
for b in bots:
    name = b.get('name')
    title = b.get('title')
    section = b.get('section')
    chief = b.get('chiefOfStaff')
    model = b.get('modelSelection', {}).get('model')
    print(f'- [{section}] {name} | {title} | Model: {model} | Chief: {chief}')
" """
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='replace'))
ssh.close()
