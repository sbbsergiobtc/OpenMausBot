import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

vps_script = """
import json, os, glob

# Check regime_orchestrator_state.json
path = '/root/AlgrokQuant/data/paper_trades/regime_orchestrator_state.json'
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    strats = data.get('strategies_ab_comparison', [])
    print(f"Total estrategias en Orchestrator State: {len(strats)}")
    rows = []
    for s in strats:
        ind = s.get('individual_book', {})
        sid = s.get('id', 'UNKNOWN')
        trades = ind.get('trades_count', 0)
        roi = ind.get('net_roi_pct', 0.0)
        asset = s.get('asset', '')
        state = s.get('orchestrator_state', '')
        desk = s.get('desk_mode', '')
        rows.append((trades, sid, asset, roi, state, desk))
    
    rows.sort(key=lambda x: x[0], reverse=True)
    print("\\n=== AUDITORÍA OFICIAL DE GRADUACIÓN MONTE CARLO (>=30 TRADES) ===")
    for trades, sid, asset, roi, state, desk in rows:
        pct = min(100, int((trades / 30) * 100))
        bars = '#' * (trades * 15 // 30) + '-' * max(0, 15 - (trades * 15 // 30))
        verdict = 'GRADUATED' if trades >= 30 else f'IN PROGRESS ({pct}%)'
        print(f"[{trades:2d}/30] [{bars}] {sid:<14} | {asset:<7} | ROI: {roi:+6.2f}% | Desk: {desk:<14} | Veredicto: {verdict}")

# Check telemetry files
t_files = glob.glob('/root/AlgrokQuant/data/paper_trades/strat_*_telemetry.json')
print(f"\\nTotal telemetry files activos: {len(t_files)}")
"""

sftp = ssh.open_sftp()
with sftp.open('/root/AlgrokQuant/scripts/audit_forward_trades.py', 'w') as f:
    f.write(vps_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /root/AlgrokQuant/scripts/audit_forward_trades.py')
print(stdout.read().decode('utf-8'))
ssh.close()
