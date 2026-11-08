import paramiko
import os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

sftp = ssh.open_sftp()
local_dir = r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\data\paper_trades'
remote_dir = '/root/AlgrokQuant/data/paper_trades'

files_to_sync = ['full_trade_history.json', 'prop_firm_forward_test_state.json', 'regime_orchestrator_state.json']
for f in files_to_sync:
    rem = f"{remote_dir}/{f}"
    loc = os.path.join(local_dir, f)
    print(f"Downloading {rem} -> {loc}...")
    sftp.get(rem, loc)

sftp.close()
ssh.close()
print("Data sync complete!")
