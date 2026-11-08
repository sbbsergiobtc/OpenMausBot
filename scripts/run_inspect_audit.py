import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

vps_script = """
import json, glob

with open('/root/AlgrokQuant/data/paper_trades/regime_orchestrator_state.json', 'r') as f:
    d = json.load(f)
print("Keys in regime_orchestrator_state:", list(d.keys()))

t_files = glob.glob('/root/AlgrokQuant/data/paper_trades/strat_*_telemetry.json')
print(f"Reading {len(t_files)} telemetry files:")
for f in sorted(t_files):
    with open(f, 'r') as fp:
        tdata = json.load(fp)
    sid = tdata.get('strategy_id', f)
    trades = tdata.get('trades_count', len(tdata.get('trade_history', [])))
    pnl = tdata.get('cumulative_pnl', 0.0)
    sem = tdata.get('semaphore', 'GREEN')
    print(f"Strategy: {sid:<16} | Trades: {trades} | PnL: ${pnl:.2f} | Sem: {sem}")

# Check full_trade_history.json
with open('/root/AlgrokQuant/data/paper_trades/full_trade_history.json', 'r') as f:
    fth = json.load(f)
all_trades = fth.get('trades', [])
print(f"\\nTotal trades in full_trade_history.json: {len(all_trades)}")
from collections import Counter
counts = Counter(t.get('strategy_id') for t in all_trades)
print("Top strategies by trade count in history:")
for sid, count in counts.most_common(15):
    print(f"  {sid}: {count} trades")
"""

sftp = ssh.open_sftp()
with sftp.open('/root/AlgrokQuant/scripts/inspect_full_audit.py', 'w') as f:
    f.write(vps_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /root/AlgrokQuant/scripts/inspect_full_audit.py')
print(stdout.read().decode('utf-8'))
ssh.close()
