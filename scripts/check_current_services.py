import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """
echo "=== SERVICIOS SYSTEMD ==="
systemctl is-active openmausbot traidinghub traidinghub-bot traidinghub-incubator

echo "=== PROCESOS PYTHON ACTIVOS ==="
ps aux | grep python3 | grep -v grep

echo "=== ÚLTIMOS LOGS DE OPENMAUSBOT ==="
journalctl -u openmausbot -n 15 --no-pager
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='replace'))
ssh.close()
