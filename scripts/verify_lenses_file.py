import paramiko

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
print("  Final Balance:", d_eval['kpis']['final_balance'])
print("  Net Profit:", d_eval['kpis']['net_profit'])
print("  Profit Factor:", d_eval['kpis']['profit_factor'])
print("  Max Drawdown:", d_eval['kpis']['max_drawdown'], "%")
print("  Best Day:", d_eval['best_single_day']['day'], "(", d_eval['best_single_day']['pnl'], ")")
print("  Streaks Count:", len(d_eval['streaks_analysis']['streaks']))

print("\\nFUNDED LENS:")
print("  Final Balance:", d_funded['kpis']['final_balance'])
print("  Net Profit:", d_funded['kpis']['net_profit'])
print("  Profit Factor:", d_funded['kpis']['profit_factor'])
print("  Max Drawdown:", d_funded['kpis']['max_drawdown'], "%")
print("  Best Day:", d_funded['best_single_day']['day'], "(", d_funded['best_single_day']['pnl'], ")")
print("  Streaks Count:", len(d_funded['streaks_analysis']['streaks']))
"""

sftp = ssh.open_sftp()
with sftp.open('/root/AlgrokQuant/scripts/test_lenses_http.py', 'w') as f:
    f.write(vps_test)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /root/AlgrokQuant/scripts/test_lenses_http.py')
print(stdout.read().decode('utf-8'))
err = stderr.read().decode('utf-8')
if err:
    print("ERR:", err)
ssh.close()
