import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """
echo "=== DIFF EN risk_rules.yaml ==="
cd /root/AlgrokQuant && git diff config/risk_rules.yaml

echo "=== DIFF EN tracks.yaml ==="
cd /root/AlgrokQuant && git diff config/tracks.yaml

echo "=== RECIENTES COMMITS EN DETALLE ==="
cd /root/AlgrokQuant && git log --stat -n 6
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='replace'))
ssh.close()
