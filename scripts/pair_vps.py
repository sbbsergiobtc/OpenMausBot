import paramiko
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

_, stdout, _ = ssh.exec_command('openmausbot pair --public-url https://169.58.230.132.sslip.io')
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
