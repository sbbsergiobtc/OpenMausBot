import sys
import paramiko
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

files = [
    ('config/risk_rules.yaml', '/root/AlgrokQuant/config/risk_rules.yaml'),
    ('scripts/prop_firm_forward_test_daemon.py', '/root/AlgrokQuant/scripts/prop_firm_forward_test_daemon.py'),
    ('jev/regime_orchestrator.py', '/root/AlgrokQuant/jev/regime_orchestrator.py'),
    ('library/lessons/LESSON-20261109-022_GOBERNANZA_ESTRICTA_T5_ROLLOVER_Y_ESTRATEGIAS_BEAR.md', '/root/AlgrokQuant/library/lessons/LESSON-20261109-022_GOBERNANZA_ESTRICTA_T5_ROLLOVER_Y_ESTRATEGIAS_BEAR.md')
]

sftp = ssh.open_sftp()
for local, remote in files:
    sftp.put(local, remote)
    print(f"Uploaded: {local} -> {remote}")
sftp.close()

# Restart daemons
cmd = 'systemctl restart algrokquant-dashboard algrokquant-forward-test && systemctl status algrokquant-dashboard algrokquant-forward-test --no-pager | grep Active'
stdin, stdout, stderr = ssh.exec_command(cmd)
print("VPS Services Status:\n", stdout.read().decode('utf-8'))

# Commit on VPS
ssh.exec_command('cd /root/AlgrokQuant && git add -A && git commit -m "feat: lesson 022, strict T-5m hard close, rollover lock and bear strategies"')
ssh.close()

# Commit locally
import subprocess
subprocess.run(['git', 'add', '-A'], check=True)
subprocess.run(['git', 'commit', '-m', 'feat: lesson 022, strict T-5m hard close, rollover lock and bear strategies'], check=False)
print("Local commit completed successfully.")
