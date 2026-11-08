import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

vps_script = """
import urllib.request, json

url = 'http://127.0.0.1:8080/api/analytics?filter=CAP-SPX-006'
req = urllib.request.urlopen(url)
data = json.loads(req.read())
print("Keys in response:", list(data.keys()))
print("Account name:", data.get('account_name'))
if 'bifocal_report' in data:
    bf = data['bifocal_report']
    print("Bifocal keys:", list(bf.keys()))
    ev = bf.get('evaluation_view', {})
    print("Monte Carlo Pass Rate:", ev.get('pass_rate_monte_carlo'), "%")
    fv = bf.get('funded_view', {})
    print("Monthly Payout:", fv.get('monthly_payout_projection_usd'), "USD")
else:
    print("bifocal_report NOT found in response!")
"""

sftp = ssh.open_sftp()
with sftp.open('/root/AlgrokQuant/scripts/test_analytics_endpoint.py', 'w') as f:
    f.write(vps_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /root/AlgrokQuant/scripts/test_analytics_endpoint.py')
print(stdout.read().decode('utf-8'))
ssh.close()
