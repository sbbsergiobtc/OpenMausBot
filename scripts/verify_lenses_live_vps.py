import paramiko, json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """python3 -c "
import requests

for filt in ['PORT-NDX-SPX', 'PROP-NDX-005']:
    r_eval = requests.get(f'http://127.0.0.1:8080/api/analytics?filter={filt}&lens=EVALUATION').json()
    r_fund = requests.get(f'http://127.0.0.1:8080/api/analytics?filter={filt}&lens=FUNDED').json()

    print(f'=== FILTER {filt} ===')
    print('EVAL lens:', r_eval['kpis']['active_lens'], 'streaks target:', r_eval['streaks_analysis']['summary']['target_pass_pct'], 'passes:', r_eval['streaks_analysis']['summary']['challenges_passed'])
    print('FUND lens:', r_fund['kpis']['active_lens'], 'streaks target:', r_fund['streaks_analysis']['summary']['target_pass_pct'], 'passes:', r_fund['streaks_analysis']['summary']['challenges_passed'])
    print('EVAL pass_rate:', r_eval['kpis']['pass_rate_monte_carlo'])
    print('FUND payout_avail:', r_fund['kpis']['payout_available_usd'], 'monthly:', r_fund['kpis']['monthly_payout_projection_usd'])

# Check trade history
th_eval = requests.get('http://127.0.0.1:8080/api/trade_history?filter=PORT-NDX-SPX&lens=EVALUATION').json()
th_fund = requests.get('http://127.0.0.1:8080/api/trade_history?filter=PORT-NDX-SPX&lens=FUNDED').json()

t0_e = th_eval['trades'][0]
t0_f = th_fund['trades'][0]
print('Trade 0 EVAL lens:', t0_e.get('active_lens'), 'clamped:', t0_e.get('clamped'))
print('Trade 0 FUND lens:', t0_f.get('active_lens'), 'payout_usd:', t0_f.get('payout_usd'))
"
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print("STDOUT:\n", stdout.read().decode())
err = stderr.read().decode()
if err:
    print("STDERR:\n", err)
ssh.close()
