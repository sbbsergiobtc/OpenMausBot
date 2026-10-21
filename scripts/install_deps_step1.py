import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """
/root/AlgrokQuant/venv/bin/pip install --upgrade pip
/root/AlgrokQuant/venv/bin/pip install numpy pandas scipy pyyaml requests tabulate ccxt
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print("OUT:", stdout.read().decode('utf-8', errors='replace')[-500:])
print("ERR:", stderr.read().decode('utf-8', errors='replace'))
ssh.close()
