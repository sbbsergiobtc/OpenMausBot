import re
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot")
BACKEND_PATH = BASE_DIR / "dashboard" / "backend.py"

with open(BACKEND_PATH, "r", encoding="utf-8") as f:
    content = f.read()

target = '''    # Segregación granular de mesas: Capital Propio vs Prop Firm
    pf_data = d.get("prop_firm", {})
    pf_bal = float(pf_data.get("current_balance", 100002.01))
    pf_eq = float(pf_data.get("peak_eod_equity", pf_bal))
    pf_pnl = float(pf_data.get("total_realized_pnl", 2.01))
    pf_dd = float(pf_data.get("current_eod_dd_pct", 0.0))

    # Cálculo del Riesgo Flotante al SL (Suma de risk_usd de posiciones abiertas)
    pf_open_positions = pf_data.get("open_positions", {})
    pf_open_risk = 0.0
    for pos_key, pos_val in pf_open_positions.items():
        if isinstance(pos_val, dict):
            pf_open_risk += float(pos_val.get("risk_usd", 0.0))
    pf_open_risk = round(pf_open_risk, 2)
    pf_open_risk_pct = round((pf_open_risk / pf_bal * 100), 2) if pf_bal > 0 else 0.0

    cp_bal = total_bal
    cp_eq = total_eq
    cp_pnl = total_pnl
    cp_float = round(cp_eq - cp_bal, 2)
    cp_dd = round(max(0.0, ((cp_bal - cp_eq) / cp_bal * 100) if cp_bal > 0 else 0.0), 2)

    cp_open_positions = d.get("capital_propio", {}).get("open_positions", {})
    cp_open_risk = 0.0
    for pos_key, pos_val in cp_open_positions.items():
        if isinstance(pos_val, dict):
            cp_open_risk += float(pos_val.get("risk_usd", 0.0))
    if cp_open_risk == 0.0 and abs(ic_eq - ic_bal) > 0.1:
        cp_open_risk = round(abs(ic_eq - ic_bal) * 2.0, 2)
    cp_open_risk = round(cp_open_risk, 2)
    cp_open_risk_pct = round((cp_open_risk / cp_bal * 100), 2) if cp_bal > 0 else 0.0

    return {
        "status": "ONLINE",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_balance_usd": total_bal,
        "total_equity_usd": total_eq,
        "total_realized_pnl_usd": total_pnl,
        "desks": {
            "CAPITAL_PROPIO": {
                "total_balance_usd": cp_bal,
                "total_equity_usd": cp_eq,
                "total_realized_pnl_usd": cp_pnl,
                "total_floating_pnl_usd": cp_float,
                "drawdown_pct": -cp_dd if cp_dd > 0 else 0.0,
                "margin_used_pct": 0.85 if abs(cp_float) > 0.1 else 0.0,
                "open_sl_risk_usd": cp_open_risk,
                "open_sl_risk_pct": cp_open_risk_pct,
                "badge_desk": "CAPITAL PROPIO",
                "sub_badge": "MT5 + DEX",
                "sync_badge": "● 2 CUENTAS SYNC",
                "risk_limit_label": "Límite Máx DD",
                "risk_limit_val": "-5.00%",
                "desc": "Supervisión consolidada de capital propio: IC Markets MT5 ($1,000) y Hyperliquid DEX (1,000 USDC)."
            },
            "PROP_FIRM": {
                "total_balance_usd": pf_bal,
                "total_equity_usd": pf_eq,
                "total_realized_pnl_usd": pf_pnl,
                "total_floating_pnl_usd": 0.0,
                "drawdown_pct": -pf_dd if pf_dd > 0 else 0.0,
                "margin_used_pct": 0.0,
                "open_sl_risk_usd": pf_open_risk,
                "open_sl_risk_pct": pf_open_risk_pct,
                "badge_desk": "CUENTAS DE FONDEO",
                "sub_badge": "Challenge $100k",
                "sync_badge": "● CHALLENGE $100K ACTIVO",
                "risk_limit_label": "Límite EOD DD",
                "risk_limit_val": "-3.50%",
                "desc": "Supervisión de cuenta de fondeo evaluativa: Challenge de $100,000 USD (CME Globex + CFDs)."
            }
        },'''

replacement = '''    # Segregación granular de mesas: Capital Propio vs Prop Firm
    pf_data = d.get("prop_firm", {})
    num_pf_strats = len(pf_data.get("active_strategies", [])) or 20
    pf_initial_bal = num_pf_strats * 100000.0  # 20 estrategias x $100k Challenge = $2,000,000 USD
    pf_pnl = float(pf_data.get("total_realized_pnl", 2.01))
    pf_bal = round(pf_initial_bal + pf_pnl, 2)  # $2,000,002.01 USD
    pf_eq = pf_bal
    pf_dd = float(pf_data.get("current_eod_dd_pct", 0.0))

    # Cálculo del Riesgo Flotante al SL en Fondeo
    pf_open_positions = pf_data.get("open_positions", {})
    pf_open_risk = 0.0
    for pos_key, pos_val in pf_open_positions.items():
        if isinstance(pos_val, dict):
            pf_open_risk += float(pos_val.get("risk_usd", 0.0))
    pf_open_risk = round(pf_open_risk, 2)
    pf_open_risk_pct = round((pf_open_risk / pf_bal * 100), 4) if pf_bal > 0 else 0.0

    # Capital Propio: 25 estrategias x $1,000 = $25,000 USD base
    cp_data = d.get("capital_propio", {})
    num_cp_strats = len(cp_data.get("active_strategies", [])) or 25
    cp_initial_bal = num_cp_strats * 1000.0  # 25 estrategias x $1k = $25,000 USD
    cp_pnl = total_pnl  # -$1.91 USD
    cp_bal = round(cp_initial_bal + cp_pnl, 2)  # $24,998.09 USD
    cp_float = round(total_eq - total_bal, 2)  # -$4.58 USD
    cp_eq = round(cp_bal + cp_float, 2)  # $24,993.51 USD
    cp_dd = round(max(0.0, ((cp_bal - cp_eq) / cp_bal * 100) if cp_bal > 0 else 0.0), 2)

    cp_open_positions = cp_data.get("open_positions", {})
    cp_open_risk = 0.0
    for pos_key, pos_val in cp_open_positions.items():
        if isinstance(pos_val, dict):
            cp_open_risk += float(pos_val.get("risk_usd", 0.0))
    if cp_open_risk == 0.0 and abs(ic_eq - ic_bal) > 0.1:
        cp_open_risk = round(abs(ic_eq - ic_bal) * 2.0, 2)
    cp_open_risk = round(cp_open_risk, 2)
    cp_open_risk_pct = round((cp_open_risk / cp_bal * 100), 2) if cp_bal > 0 else 0.0

    return {
        "status": "ONLINE",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_balance_usd": total_bal,
        "total_equity_usd": total_eq,
        "total_realized_pnl_usd": total_pnl,
        "desks": {
            "CAPITAL_PROPIO": {
                "total_balance_usd": cp_bal,
                "total_equity_usd": cp_eq,
                "total_realized_pnl_usd": cp_pnl,
                "total_floating_pnl_usd": cp_float,
                "drawdown_pct": -cp_dd if cp_dd > 0 else 0.0,
                "margin_used_pct": 0.85 if abs(cp_float) > 0.1 else 0.0,
                "open_sl_risk_usd": cp_open_risk,
                "open_sl_risk_pct": cp_open_risk_pct,
                "badge_desk": "CAPITAL PROPIO",
                "sub_badge": f"{num_cp_strats} Cuentas x $1k",
                "sync_badge": f"● {num_cp_strats} CUENTAS FT",
                "risk_limit_label": "Límite Máx DD",
                "risk_limit_val": "-5.00%",
                "desc": f"Supervisión consolidada de capital propio en Forward Test: {num_cp_strats} estrategias ($25,000 inicial) en MT5 y Hyperliquid DEX."
            },
            "PROP_FIRM": {
                "total_balance_usd": pf_bal,
                "total_equity_usd": pf_eq,
                "total_realized_pnl_usd": pf_pnl,
                "total_floating_pnl_usd": 0.0,
                "drawdown_pct": -pf_dd if pf_dd > 0 else 0.0,
                "margin_used_pct": 0.0,
                "open_sl_risk_usd": pf_open_risk,
                "open_sl_risk_pct": pf_open_risk_pct,
                "badge_desk": "CUENTAS DE FONDEO",
                "sub_badge": f"{num_pf_strats} Cuentas x $100k",
                "sync_badge": f"● {num_pf_strats} CHALLENGES FT",
                "risk_limit_label": "Límite EOD DD",
                "risk_limit_val": "-3.50%",
                "desc": f"Supervisión consolidada de cuentas de fondeo en Forward Test: {num_pf_strats} challenges de $100k ($2,000,000 inicial) en CME Globex y CFDs."
            }
        },'''

content_norm = content.replace("\r\n", "\n")
target_norm = target.replace("\r\n", "\n")
if target_norm in content_norm:
    content_norm = content_norm.replace(target_norm, replacement.replace("\r\n", "\n"))
    with open(BACKEND_PATH, "w", encoding="utf-8") as f:
        f.write(content_norm)
    print("backend.py updated successfully with aggregate multi-account balances!")
else:
    print("Target string not found in backend.py!")
    exit(1)
