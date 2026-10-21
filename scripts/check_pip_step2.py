import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """
ps aux | grep pip | grep -v grep
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print("Pip processes:", stdout.read().decode('utf-8', errors='replace'))
ssh.close()
