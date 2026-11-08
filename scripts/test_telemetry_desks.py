from pathlib import Path
import json

BASE_DIR = Path(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot")
pf_state_file = BASE_DIR / "data/paper_trades/prop_firm_forward_test_state.json"

with open(pf_state_file, "r", encoding="utf-8") as f:
    d = json.load(f)

live_broker = d.get("live_broker_sync", {})
ic_bal = float(live_broker.get("broker_balance", 984.53))
ic_eq = float(live_broker.get("broker_equity", 979.95))
ic_pnl = round(ic_bal - 1000.0, 2)

hl_bal = 1013.56
hl_eq = 1013.56
hl_pnl = 13.56

pf_data = d.get("prop_firm", {})
pf_bal = float(pf_data.get("current_balance", 100002.01))
pf_eq = float(pf_data.get("peak_eod_equity", pf_bal))
pf_pnl = float(pf_data.get("total_realized_pnl", 2.01))
pf_dd = float(pf_data.get("current_eod_dd_pct", 0.0))

cp_bal = round(ic_bal + hl_bal, 2)
cp_eq = round(ic_eq + hl_eq, 2)
cp_pnl = round(ic_pnl + hl_pnl, 2)
cp_float = round(cp_eq - cp_bal, 2)
cp_dd = round(max(0.0, ((cp_bal - cp_eq) / cp_bal * 100) if cp_bal > 0 else 0.0), 2)

print("CAPITAL PROPIO:", {
    "total_balance_usd": cp_bal,
    "total_equity_usd": cp_eq,
    "total_realized_pnl_usd": cp_pnl,
    "total_floating_pnl_usd": cp_float,
    "drawdown_pct": -cp_dd if cp_dd > 0 else 0.0,
    "margin_used_pct": 0.85 if abs(cp_float) > 0.1 else 0.0,
    "net_exposure": "LONG 100%" if abs(cp_float) > 0.1 else "FLAT (0.0%)",
})

print("PROP FIRM:", {
    "total_balance_usd": pf_bal,
    "total_equity_usd": pf_eq,
    "total_realized_pnl_usd": pf_pnl,
    "total_floating_pnl_usd": 0.0,
    "drawdown_pct": -pf_dd if pf_dd > 0 else 0.0,
    "margin_used_pct": 0.0,
    "net_exposure": "FLAT (0.0%)",
})
