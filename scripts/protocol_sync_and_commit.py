import os, sys, paramiko

sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = '169.58.230.132'
VPS_USER = 'root'
VPS_PASS = '4722ADwTjGA'
REMOTE_BASE = '/root/AlgrokQuant'
LOCAL_BASE = r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot'

print("1. Connecting to VPS via SFTP to sync LESSON-020...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS)
sftp = ssh.open_sftp()

lesson_local = os.path.join(LOCAL_BASE, 'library/lessons/LESSON-20261108-020_LENTE_CUANTITATIVA_BIFASICA_Y_BLACKOUT_NOTICIAS.md')
lesson_remote = f'{REMOTE_BASE}/library/lessons/LESSON-20261108-020_LENTE_CUANTITATIVA_BIFASICA_Y_BLACKOUT_NOTICIAS.md'

sftp.put(lesson_local, lesson_remote)
print(f"Uploaded: {lesson_remote}")
sftp.close()

print("2. Committing all modified files on VPS...")
cmd_git = """
cd /root/AlgrokQuant
git add library/ reports/ jev/ config/ dashboard/
git commit -m 'feat(quant): session wrap - Bifocal Quantitative Lens, 5-min news blackout, and LESSON-020' || echo 'No new changes to commit'
git log -n 2 --oneline
"""
stdin, stdout, stderr = ssh.exec_command(cmd_git)
print("=== VPS GIT LOG ===")
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
print("VPS Sync & Commit done.")
