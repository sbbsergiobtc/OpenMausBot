import os, sys, paramiko

sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = '169.58.230.132'
VPS_USER = 'root'
VPS_PASS = '4722ADwTjGA'
REMOTE_BASE = '/root/AlgrokQuant'
LOCAL_BASE = r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot'

FILES_TO_UPLOAD = [
    ('jev/news_risk_filter.py', f'{REMOTE_BASE}/jev/news_risk_filter.py'),
    ('scripts/prop_firm_forward_test_daemon.py', f'{REMOTE_BASE}/scripts/prop_firm_forward_test_daemon.py'),
    ('dashboard/backend.py', f'{REMOTE_BASE}/dashboard/backend.py'),
    ('config/risk_rules.yaml', f'{REMOTE_BASE}/config/risk_rules.yaml')
]

print(f"Connecting to VPS {VPS_HOST} via SFTP...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS)
sftp = ssh.open_sftp()

for loc, rem in FILES_TO_UPLOAD:
    full_loc = os.path.join(LOCAL_BASE, loc)
    print(f"Uploading {full_loc} -> {rem}...")
    sftp.put(full_loc, rem)

sftp.close()
print("Upload complete. Restarting services on VPS...")

cmd = """
systemctl restart algrokquant-forward-test.service
systemctl restart algrokquant-dashboard.service
sleep 2
systemctl status algrokquant-forward-test.service --no-pager -l | head -n 8
systemctl status algrokquant-dashboard.service --no-pager -l | head -n 8
curl -s http://127.0.0.1:8080/api/macro_news_risk | head -c 200
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print("=== VPS OUTPUT ===")
print(stdout.read().decode('utf-8', errors='replace'))
err = stderr.read().decode('utf-8', errors='replace')
if err:
    print("=== ERRORS ===")
    print(err)

# Remote commit
git_cmd = """
cd /root/AlgrokQuant
git add jev/news_risk_filter.py scripts/prop_firm_forward_test_daemon.py dashboard/backend.py config/risk_rules.yaml
git commit -m 'feat(risk): implement active real-time Macro News Blackout filter (5-min window) in forward test daemon and API' || echo 'Clean'
git log -n 1 --oneline
"""
stdin, stdout, stderr = ssh.exec_command(git_cmd)
print("=== REMOTE COMMIT ===")
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
print("Deployment completed successfully!")
