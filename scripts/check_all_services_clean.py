import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

services = [
    'algrokquant-dashboard.service',
    'openmausbot.service',
    'algrokquant-forward-test.service',
    'algrokquant-mt5.service'
]

for s in services:
    stdin, stdout, stderr = ssh.exec_command(f'systemctl status {s} --no-pager -l | head -n 6')
    print(f"=== {s} ===")
    print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
