import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """
python3 -c "
import urllib.request, json
res = urllib.request.urlopen('http://127.0.0.1:8080/api/analytics?filter=PROP-NDX-005')
d = json.loads(res.read())
print('Full keys:', list(d.keys()))
print('Account name:', d.get('account_name'))
"
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8'))
ssh.close()
