import os
import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = '169.58.230.132'
VPS_USER = 'root'
VPS_PASS = '4722ADwTjGA'
REMOTE_BASE = '/root/AlgrokQuant'
LOCAL_BASE = r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot'

FILES_TO_UPLOAD = [
    ('dashboard/backend.py', f'{REMOTE_BASE}/dashboard/backend.py'),
    ('dashboard/templates/index.html', f'{REMOTE_BASE}/dashboard/templates/index.html'),
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
print("Upload complete. Restarting algrokquant-dashboard on VPS...")

cmd = """
systemctl restart algrokquant-dashboard
sleep 2
systemctl status algrokquant-dashboard --no-pager -l | head -n 12
curl -s 'http://127.0.0.1:8080/api/analytics?filter=PROP-NDX-005' | grep -o '\"bifocal_report\":{[^}]*' | head -n 1
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')

print("=== VPS OUTPUT ===")
print(out)
if err:
    print("=== VPS ERRORS ===")
    print(err)

# Remote commit
git_cmd = """
cd /root/AlgrokQuant
git add dashboard/backend.py dashboard/templates/index.html config/risk_rules.yaml
git commit -m 'feat(backtest): add Bifocal Quantitative Lens (Evaluation vs Funded) and 5-min news trading blackout'
"""
stdin, stdout, stderr = ssh.exec_command(git_cmd)
print("=== REMOTE COMMIT ===")
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
print("Deployment completed successfully!")
