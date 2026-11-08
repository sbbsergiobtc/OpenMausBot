import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """python3 -c "
import requests, json

for filt in ['PORT-NDX-SPX', 'PROP-NDX-005', 'ALL']:
    r1 = requests.get(f'http://127.0.0.1:8080/api/analytics?filter={filt}&lens=EVALUATION').json()
    r2 = requests.get(f'http://127.0.0.1:8080/api/analytics?filter={filt}&lens=FUNDED').json()
    p1 = r1.get('kpis', {}).get('net_profit')
    p2 = r2.get('kpis', {}).get('net_profit')
    print(f'Filter {filt}: EVAL net_profit={p1} vs FUNDED net_profit={p2}')
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print("STDOUT:\n", stdout.read().decode())
print("STDERR:\n", stderr.read().decode())
ssh.close()
