import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """
python3 -c "
import json
with open('/root/AlgrokQuant/data/paper_trades/prop_firm_forward_test_state.json', 'r') as f:
    st = json.load(f)

strats = st.get('strategies', {})
print('Total strategies tracked:', len(strats))
rows = []
for sid, s in strats.items():
    tr_count = s.get('trades_count', len(s.get('trade_history', [])))
    pnl = s.get('cumulative_pnl', s.get('current_equity', 1000) - 1000)
    sem = s.get('semaphore', 'GREEN')
    cone = s.get('fidelity_cone', 'IN_BOUNDS')
    z_score = s.get('z_score', 0.0)
    rows.append((tr_count, sid, pnl, sem, cone, z_score))

rows.sort(key=lambda x: x[0], reverse=True)
print('\\n=== RANKING DE GRADUACIÓN MONTE CARLO (HACIA >=30 TRADES) ===')
for tr, sid, pnl, sem, cone, z in rows[:20]:
    progress_bar = '#' * (tr * 15 // 30) + '-' * (15 - (tr * 15 // 30))
    print(f'[{tr:2d}/30] [{progress_bar}] {sid:<14} | PnL: ${pnl:+7.2f} | Semáforo: {sem:<5} | Cono: {cone:<10} | Z: {z:+.2f}σ')
"
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8'))
ssh.close()
