import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')

with open('docs/ALGROKQUANT_SPEC.md', 'r', encoding='utf-8') as f:
    content = f.read()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

sftp = ssh.open_sftp()
try:
    sftp.mkdir('/root/AlgrokQuant/docs')
except:
    pass

with sftp.file('/root/AlgrokQuant/docs/ALGROKQUANT_SPEC.md', 'w') as f:
    f.write(content)

with sftp.file('/root/AlgrokQuant/library/00_MANIFIESTO_Y_ESPECIFICACION.md', 'w') as f:
    f.write(content)

with sftp.file('/root/AlgrokQuant/README.md', 'w') as f:
    f.write(content)

sftp.close()

stdin, stdout, stderr = ssh.exec_command('ls -la /root/AlgrokQuant/docs/ /root/AlgrokQuant/library/ /root/AlgrokQuant/README.md')
print(stdout.read().decode('utf-8', errors='replace'))
ssh.close()
