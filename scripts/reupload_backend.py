import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

sftp = ssh.open_sftp()
sftp.put(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py', '/root/AlgrokQuant/dashboard/backend.py')
sftp.close()

stdin, stdout, stderr = ssh.exec_command('systemctl restart algrokquant-dashboard && sleep 2 && curl -s "http://127.0.0.1:8080/api/analytics?filter=PROP-NDX-005"')
print(stdout.read().decode('utf-8')[:800])
ssh.close()
