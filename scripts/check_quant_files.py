import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """
echo "=== risk_rules.yaml ==="
cat /root/AlgrokQuant/config/risk_rules.yaml 2>/dev/null
echo "=== tracks.yaml ==="
cat /root/AlgrokQuant/config/tracks.yaml 2>/dev/null
echo "=== telegram.env ==="
cat /root/AlgrokQuant/config/telegram.env 2>/dev/null
echo "=== library/README.md ==="
cat /root/AlgrokQuant/library/README.md 2>/dev/null
echo "=== Python env / dependencies ==="
python3 --version
python3 -c "import vectorbt" 2>&1
python3 -c "import ccxt" 2>&1
python3 -c "import pandas" 2>&1
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='replace'))
ssh.close()
