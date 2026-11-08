import json

with open('data/paper_trades/prop_firm_forward_test_state.json', 'r', encoding='utf-8') as f:
    state = json.load(f)

for branch in ['capital_propio', 'prop_firm']:
    strats = state.get(branch, {}).get('active_strategies', [])
    print(f"=== {branch.upper()} (Total: {len(strats)}) ===")
    for s in strats:
        strat_id = s.get('strategy_id')
        sym = s.get('symbol')
        tf = s.get('timeframe') or s.get('interval') or s.get('tf')
        name = s.get('name') or s.get('description') or ''
        print(f"  [{strat_id}] {sym} | TF: {tf} | {name}")
