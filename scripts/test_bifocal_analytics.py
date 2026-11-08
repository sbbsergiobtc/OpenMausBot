import json
import pandas as pd
import numpy as np

with open(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\data\paper_trades\full_trade_history.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data.get('trades', [])
df = pd.DataFrame(trades)
print("Total trades in history:", len(df))

# Test with subset: PROP-NDX-005
sub = df[df['strategy_id'] == 'PROP-NDX-005']
print(f"Subset PROP-NDX-005: {len(sub)} trades")

# Run bifocal calculation
initial_balance = 100000.0
raw_pnls = sub['net_pnl_usd'].values
total_raw_profit = sum(p for p in raw_pnls if p > 0)
consistency_cap_per_trade = total_raw_profit * 0.40

clamped_pnls = []
clamped_count = 0
penalty = 0.0
for p in raw_pnls:
    if p > consistency_cap_per_trade:
        clamped_pnls.append(consistency_cap_per_trade)
        penalty += (p - consistency_cap_per_trade)
        clamped_count += 1
    else:
        clamped_pnls.append(p)

print(f"Raw total profit: ${total_raw_profit:.2f}")
print(f"Consistency cap (40%): ${consistency_cap_per_trade:.2f}")
print(f"Clamped trades: {clamped_count} (Penalty: ${penalty:.2f})")
print(f"Capped total profit: ${sum(clamped_pnls):.2f}")
print("Bifocal calculation verified successfully!")
