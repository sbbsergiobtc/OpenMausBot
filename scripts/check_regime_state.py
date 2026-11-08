import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """
python3 -c "
import json
with open('/root/AlgrokQuant/data/paper_trades/regime_orchestrator_state.json', 'r') as f:
    st = json.load(f)
print('Keys in regime_orchestrator_state:', list(st.keys()))
strats = st.get('strategies_ab_comparison', [])
print('Total strategies in AB comparison:', len(strats))
for s in strats[:5]:
    ind = s.get('individual_book', {})
    print(f\"{s.get('id')} | {s.get('asset')} {s.get('timeframe')} | Trades: {ind.get('trades_count', 0)} | ROI: {ind.get('net_roi_pct')}% | State: {s.get('orchestrator_state')}\")
"
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8'))
ssh.close()
