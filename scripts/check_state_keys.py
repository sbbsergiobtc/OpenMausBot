import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """
python3 -c "
import json
with open('/root/AlgrokQuant/data/paper_trades/prop_firm_forward_test_state.json', 'r') as f:
    st = json.load(f)
print('Keys in state:', list(st.keys()))
for k in st.keys():
    v = st[k]
    if isinstance(v, list):
        print(f'{k}: list of {len(v)} items')
    elif isinstance(v, dict):
        print(f'{k}: dict with {len(v)} keys -> {list(v.keys())[:5]}')
    else:
        print(f'{k}: {v}')
"
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8'))
ssh.close()
