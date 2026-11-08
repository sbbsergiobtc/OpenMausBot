import os
import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = '169.58.230.132'
VPS_USER = 'root'
VPS_PASS = '4722ADwTjGA'
REMOTE_DIR = '/root/AlgrokQuant'
LOCAL_BASE = r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot'

FILES_TO_UPLOAD = [
    ('dashboard/backend.py', f'{REMOTE_DIR}/dashboard/backend.py'),
    ('dashboard/templates/index.html', f'{REMOTE_DIR}/dashboard/templates/index.html'),
    ('scripts/prop_firm_forward_test_daemon.py', f'{REMOTE_DIR}/scripts/prop_firm_forward_test_daemon.py')
]

print(f"Connecting to VPS {VPS_HOST}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS)
sftp = ssh.open_sftp()

for local_rel, remote_path in FILES_TO_UPLOAD:
    local_path = os.path.join(LOCAL_BASE, local_rel)
    print(f"Uploading {local_rel} -> {remote_path}...")
    sftp.put(local_path, remote_path)

sftp.close()
print("Upload complete. Restarting services on VPS...")

cmd = """
systemctl restart algrokquant-dashboard
systemctl restart algrokquant-forward-test
sleep 2
systemctl status algrokquant-dashboard --no-pager -l
systemctl status algrokquant-forward-test --no-pager -l
curl -s http://127.0.0.1:8080/api/accounts | head -n 30
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')

print("=== VPS OUTPUT ===")
print(out)
if err:
    print("=== VPS ERRORS ===")
    print(err)

ssh.close()
