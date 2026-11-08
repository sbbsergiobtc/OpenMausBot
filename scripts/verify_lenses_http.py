import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

vps_test = """
import urllib.request, json

url_eval = 'http://127.0.0.1:8080/api/analytics?filter=PORT-NDX-SPX&lens=EVALUATION'
url_funded = 'http://127.0.0.1:8080/api/analytics?filter=PORT-NDX-SPX&lens=FUNDED'

d_eval = json.loads(urllib.request.urlopen(url_eval).read())
d_funded = json.loads(urllib.request.urlopen(url_funded).read())

print("=== PORT-NDX-SPX ANALYTICS TEST ===")
print("EVALUATION LENS:")
print(f"  Final Balance: ${d_eval['kpis']['final_balance']:,.2f}")
print(f"  Net Profit: +${d_eval['kpis']['net_profit']:,.2f}")
print(f"  Profit Factor: {d_eval['kpis']['profit_factor']}")
print(f"  Max Drawdown: {d_eval['kpis']['max_drawdown']}%")
print(f"  Best Day: {d_eval['best_single_day']['day']} (+${d_eval['best_single_day']['pnl']:,.2f})")
print(f"  Streaks Count: {len(d_eval['streaks_analysis']['streaks'])}")

print("\\nFUNDED LENS:")
print(f"  Final Balance: ${d_funded['kpis']['final_balance']:,.2f}")
print(f"  Net Profit: +${d_funded['kpis']['net_profit']:,.2f}")
print(f"  Profit Factor: {d_funded['kpis']['profit_factor']}")
print(f"  Max Drawdown: {d_funded['kpis']['max_drawdown']}%")
print(f"  Best Day: {d_funded['best_single_day']['day']} (+${d_funded['best_single_day']['pnl']:,.2f})")
print(f"  Streaks Count: {len(d_funded['streaks_analysis']['streaks'])}")
"""

stdin, stdout, stderr = ssh.exec_command(f"python3 -c \"{vps_test}\"")
print(stdout.read().decode('utf-8'))
err = stderr.read().decode('utf-8')
if err:
    print("ERR:", err)
ssh.close()
