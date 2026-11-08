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
    ('dashboard/templates/index.html', f'{REMOTE_BASE}/dashboard/templates/index.html')
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
curl -s http://127.0.0.1:8080/ | grep -o 'cockpit-kpi-total-balance' | head -n 2
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')

print("=== VPS OUTPUT ===")
print(out)
if err:
    print("=== VPS ERRORS ===")
    print(err)

# Remote commit on VPS
git_cmd = """
cd /root/AlgrokQuant
git add dashboard/templates/index.html
git commit -m "feat(cockpit): redesign general cockpit with 6 independent KPIs and remove obsolete cards"
git status --short
"""
stdin, stdout, stderr = ssh.exec_command(git_cmd)
git_out = stdout.read().decode('utf-8', errors='replace')
print("=== VPS GIT OUTPUT ===")
print(git_out)

ssh.close()
print("Deployment and verification complete!")
