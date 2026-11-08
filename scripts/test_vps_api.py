import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """
curl -s -X POST http://127.0.0.1:8080/api/accounts/update_stage \
     -H "Content-Type: application/json" \
     -d '{"account_id": "53120791", "stage": "FUNDED"}'
echo ""
curl -s http://127.0.0.1:8080/api/accounts
echo ""
curl -s -X POST http://127.0.0.1:8080/api/accounts/update_stage \
     -H "Content-Type: application/json" \
     -d '{"account_id": "53120791", "stage": "EVALUATION"}'
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8'))
ssh.close()
