import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """python3 -c "
import requests, time

endpoints = [
    '/api/telemetry',
    '/api/forward_state',
    '/api/summary',
    '/api/analytics?filter=PORT-NDX-SPX',
    '/api/trade_history?filter=PORT-NDX-SPX',
    '/api/regime_orchestrator'
]

for ep in endpoints:
    times = []
    for _ in range(5):
        t0 = time.perf_counter()
        r = requests.get('http://127.0.0.1:8080' + ep)
        times.append((time.perf_counter() - t0) * 1000)
    avg_ms = sum(times) / len(times)
    min_ms = min(times)
    max_ms = max(times)
    print(f'{ep:40s} -> Avg: {avg_ms:6.2f} ms | Min: {min_ms:6.2f} ms | Max: {max_ms:6.2f} ms')
"
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print("=== VPS INTERNAL ENDPOINT BENCHMARK ===")
print(stdout.read().decode('utf-8', errors='replace'))
err = stderr.read().decode('utf-8', errors='replace')
if err:
    print("=== ERRORS ===")
    print(err)

ssh.close()
