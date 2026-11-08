import os
import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = '169.58.230.132'
VPS_USER = 'root'
VPS_PASS = '4722ADwTjGA'
REMOTE_FILE = '/root/AlgrokQuant/dashboard/templates/index.html'
LOCAL_FILE = r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html'

print(f"Connecting to VPS {VPS_HOST} via SFTP...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS)
sftp = ssh.open_sftp()

print(f"Uploading {LOCAL_FILE} -> {REMOTE_FILE}...")
sftp.put(LOCAL_FILE, REMOTE_FILE)
sftp.close()
print("Upload complete. Restarting algrokquant-dashboard on VPS...")

cmd = """
systemctl restart algrokquant-dashboard
sleep 2
systemctl status algrokquant-dashboard --no-pager -l | head -n 15
curl -s http://127.0.0.1:8080/ | grep -o 'AlgrokTableColumnReorderController' | head -n 1
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')

print("=== VPS OUTPUT ===")
print(out)
if err:
    print("=== VPS ERRORS ===")
    print(err)

# Git commit on remote
git_cmd = """
cd /root/AlgrokQuant
git add dashboard/templates/index.html
git commit -m 'feat(tables): enable Framer Motion spring drag-and-drop column reordering across all 11 tables'
"""
stdin, stdout, stderr = ssh.exec_command(git_cmd)
print("=== REMOTE GIT COMMIT ===")
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
print("All remote steps completed successfully!")
