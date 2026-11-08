import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

vps_script = """
import json

with open('/root/AlgrokQuant/data/paper_trades/regime_orchestrator_state.json', 'r') as f:
    d = json.load(f)

strats = d.get('strategies_ab', [])
print(f"Total strategies_ab: {len(strats)}")
for s in strats:
    sid = s.get('strategy_id') or s.get('id')
    desk = s.get('desk_mode')
    orch_state = s.get('orchestrator_state')
    asset = s.get('asset')
    tf = s.get('timeframe')
    ind = s.get('individual_book', {})
    orch = s.get('orchestrated_book', {})
    print(f"{sid:<16} | {asset} {tf} | Desk: {desk:<14} | State: {orch_state} | Ind Trades: {ind.get('trades_count', 0)} PnL: ${ind.get('net_pnl_usd', 0):.2f}")
"""

sftp = ssh.open_sftp()
with sftp.open('/root/AlgrokQuant/scripts/inspect_strategies_ab.py', 'w') as f:
    f.write(vps_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /root/AlgrokQuant/scripts/inspect_strategies_ab.py')
print(stdout.read().decode('utf-8'))
ssh.close()
