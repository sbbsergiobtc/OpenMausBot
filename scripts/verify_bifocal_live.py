import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """curl -s 'http://127.0.0.1:8080/api/analytics?filter=PROP-NDX-005'"""
stdin, stdout, stderr = ssh.exec_command(cmd)
res = stdout.read().decode('utf-8')
data = json.loads(res)

print("Account name:", data.get('account_name'))
print("Has bifocal_report:", 'bifocal_report' in data)
if 'bifocal_report' in data:
    bf = data['bifocal_report']
    ev = bf.get('evaluation_view', {})
    fv = bf.get('funded_view', {})
    print("=== LENTE DE EVALUACIÓN (RETO) ===")
    print("Pass Rate Monte Carlo:", ev.get('pass_rate_monte_carlo'), "%")
    print("Trades Clampeados (Tope 40%):", ev.get('clamped_trades_count'))
    print("Penalización por Consistencia: $", ev.get('consistency_penalty_usd'))
    print("Max Drawdown:", ev.get('max_drawdown_pct'), "%")
    print("=== LENTE FONDEADA (COSECHA) ===")
    print("Total Alpha Libre: $", fv.get('total_uncapped_alpha_usd'))
    print("Proyección Payout Mensual (80% split): $", fv.get('monthly_payout_projection_usd'))
    print("Meses Estimados:", fv.get('estimated_months'))

ssh.close()
