import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

services = [
    'algrokquant-dashboard.service',
    'openmausbot.service',
    'strat_028_paper_runner.service',
    'prop_firm_forward_test.service'
]

print("=== SYSTEMD SERVICES STATUS ===")
for s in services:
    stdin, stdout, stderr = ssh.exec_command(f'systemctl is-active {s}')
    status = stdout.read().decode().strip()
    stdin, stdout, stderr = ssh.exec_command(f'systemctl show -p MainPID,SubState,ActiveEnterTimestamp {s}')
    details = stdout.read().decode().strip().replace('\n', ' | ')
    print(f"[{status.upper()}] {s}: {details}")

# Also check any other running custom service
stdin, stdout, stderr = ssh.exec_command("systemctl list-unit-files | grep -iE 'algrok|openmaus|strat|prop'")
print("\n=== SYSTEMD DEFINED UNITS ===")
print(stdout.read().decode().strip())

ssh.close()
