import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """
echo "=== 1. COMMITS RECIENTES EN /root/AlgrokQuant ==="
cd /root/AlgrokQuant && git log --oneline -n 15 2>/dev/null || echo "No git repo or commits"

echo "=== 2. ESTADO GIT Y ARCHIVOS MODIFICADOS/NO TRACKEADOS EN /root/AlgrokQuant ==="
cd /root/AlgrokQuant && git status -s

echo "=== 3. ARCHIVOS MODIFICADOS EN LOS ÚLTIMOS 5 DÍAS EN /root/AlgrokQuant ==="
find /root/AlgrokQuant -maxdepth 4 -not -path '*/.*' -not -path './venv*' -mtime -5 -ls 2>/dev/null

echo "=== 4. ARCHIVOS RECIENTES EN /root/.openmausbot ==="
find /root/.openmausbot -maxdepth 3 -mtime -5 -ls 2>/dev/null | head -n 40
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='replace'))
print("ERR:", stderr.read().decode('utf-8', errors='replace'))
ssh.close()
