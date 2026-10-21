import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """
ln -sf /root/AlgrokQuant/venv/bin/python3 /usr/local/bin/python3
ln -sf /root/AlgrokQuant/venv/bin/python /usr/local/bin/python
ln -sf /root/AlgrokQuant/venv/bin/pip /usr/local/bin/pip
ln -sf /root/AlgrokQuant/venv/bin/pip3 /usr/local/bin/pip3

python3 -c "import vectorbt, ccxt, pandas, hyperliquid, telegram; print('TODO EL STACK QUANT DISPONIBLE DIRECTAMENTE EN PYTHON3')"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='replace'))
print("ERR:", stderr.read().decode('utf-8', errors='replace'))
ssh.close()
