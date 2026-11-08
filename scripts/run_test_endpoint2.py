import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

stdin, stdout, stderr = ssh.exec_command('python3 /root/AlgrokQuant/scripts/test_analytics_endpoint.py')
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("STDOUT:", out)
print("STDERR:", err)
ssh.close()
