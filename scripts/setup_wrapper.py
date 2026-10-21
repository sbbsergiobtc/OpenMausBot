import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """
rm -f /usr/local/bin/python3 /usr/local/bin/python /usr/local/bin/pip /usr/local/bin/pip3

cat << 'EOF' > /usr/local/bin/python3
#!/bin/bash
exec /root/AlgrokQuant/venv/bin/python3 "$@"
EOF
chmod +x /usr/local/bin/python3

cat << 'EOF' > /usr/local/bin/python
#!/bin/bash
exec /root/AlgrokQuant/venv/bin/python3 "$@"
EOF
chmod +x /usr/local/bin/python

cat << 'EOF' > /usr/local/bin/pip
#!/bin/bash
exec /root/AlgrokQuant/venv/bin/pip "$@"
EOF
chmod +x /usr/local/bin/pip

cat << 'EOF' > /usr/local/bin/pip3
#!/bin/bash
exec /root/AlgrokQuant/venv/bin/pip "$@"
EOF
chmod +x /usr/local/bin/pip3

python3 -c "import vectorbt, ccxt, pandas, hyperliquid, telegram; print('SUCCESS: FULL QUANT STACK DISPONIBLE GLOBALMENTE')"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print("OUT:", stdout.read().decode('utf-8', errors='replace'))
print("ERR:", stderr.read().decode('utf-8', errors='replace'))
ssh.close()
