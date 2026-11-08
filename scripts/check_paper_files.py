import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """
python3 -c "
import json, os
files = os.listdir('/root/AlgrokQuant/data/paper_trades/')
print('Files in data/paper_trades/:', files)
with open('/root/AlgrokQuant/data/paper_trades/prop_firm_forward_test_state.json', 'r') as f:
    st = json.load(f)
c16 = st.get('certified_16_strategies', [])
print('\\nSample from certified_16_strategies (first 3):')
for item in c16[:3]:
    print(item.get('id'), '|', item.get('asset'), '|', item.get('orchestrator_state'), '| Individual:', item.get('individual_book'))
"
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8'))
ssh.close()
