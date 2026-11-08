import re
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot")
BACKEND_PATH = BASE_DIR / "dashboard" / "backend.py"

with open(BACKEND_PATH, "r", encoding="utf-8") as f:
    content = f.read()

target = '''@app.get("/api/telemetry")
def get_telemetry():
    pf_state_file = BASE_DIR / "data/paper_trades/prop_firm_forward_test_state.json"
    crypto_state_file = BASE_DIR / "data/paper_trades/account_state.json"
    
    live_broker = {}
    if pf_state_file.exists():
        try:
            with open(pf_state_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                live_broker = d.get("live_broker_sync", {})
        except Exception:
            pass

    crypto_state = {}
    if crypto_state_file.exists():
        try:
            with open(crypto_state_file, "r", encoding="utf-8") as f:
                crypto_state = json.load(f)
        except Exception:
            pass

        ic_bal = float(live_broker.get("broker_balance", 1001.52))
    ic_eq = float(live_broker.get("broker_equity", 1001.52))
    hl_bal = float(crypto_state.get("balance", 1000.66))
    hl_eq = float(crypto_state.get("equity", 1000.66))
    total_bal = round(ic_bal + hl_bal, 2)
    total_eq = round(ic_eq + hl_eq, 2)
    ic_pnl = round(ic_bal - 1000.0, 2)
    hl_pnl = float(crypto_state.get("realized_pnl", 0.66))
    total_pnl = round(ic_pnl + hl_pnl, 2)

    return {
        "status": "ONLINE",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_balance_usd": total_bal,
        "total_equity_usd": total_eq,
        "total_realized_pnl_usd": total_pnl,
        "mt5": {
            "status": "ONLINE" if live_broker.get("trade_allowed", True) else "OFFLINE",
            "account": live_broker.get("account", 53120791),
            "server": live_broker.get("server", "ICMarketsSC-Demo"),
            "balance": ic_bal,
            "equity": ic_eq,
            "realized_pnl": ic_pnl,
            "currency": "USD",
            "risk_mode": "1.5% Dinámico Compuesto",
            "monitored_assets": ["US500", "USTEC", "EURUSD"]
        },
        "hyperliquid": {
            "status": "ONLINE",
            "exchange": "Hyperliquid L1 Testnet (DEX)",
            "balance": hl_bal,
            "equity": hl_eq,
            "realized_pnl": hl_pnl,
            "currency": "USDC",
            "strategy": "STRAT-FAST-035 (BTC 1h)",
            "fees": "14 bps Taker + Funding 1h"
        },
        "daemon": {
            "status": "ACTIVE",
            "frequency": "Cada 1 hora",
            "active_assets": ["US500", "USTEC", "EURUSD", "BTC/USDT"]
        }
    }'''

replacement = '''@app.get("/api/telemetry")
def get_telemetry():
    pf_state_file = BASE_DIR / "data/paper_trades/prop_firm_forward_test_state.json"
    crypto_state_file = BASE_DIR / "data/paper_trades/account_state.json"
    
    live_broker = {}
    d = {}
    if pf_state_file.exists():
        try:
            with open(pf_state_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                live_broker = d.get("live_broker_sync", {})
        except Exception:
            pass

    crypto_state = {}
    if crypto_state_file.exists():
        try:
            with open(crypto_state_file, "r", encoding="utf-8") as f:
                crypto_state = json.load(f)
        except Exception:
            pass

    ic_bal = float(live_broker.get("broker_balance", 984.53))
    ic_eq = float(live_broker.get("broker_equity", 979.95))
    hl_bal = float(crypto_state.get("balance", 1013.56))
    hl_eq = float(crypto_state.get("equity", 1013.56))
    total_bal = round(ic_bal + hl_bal, 2)
    total_eq = round(ic_eq + hl_eq, 2)
    ic_pnl = round(ic_bal - 1000.0, 2)
    hl_pnl = float(crypto_state.get("realized_pnl", 13.56))
    total_pnl = round(ic_pnl + hl_pnl, 2)

    # Segregación granular de mesas: Capital Propio vs Prop Firm
    pf_data = d.get("prop_firm", {})
    pf_bal = float(pf_data.get("current_balance", 100002.01))
    pf_eq = float(pf_data.get("peak_eod_equity", pf_bal))
    pf_pnl = float(pf_data.get("total_realized_pnl", 2.01))
    pf_dd = float(pf_data.get("current_eod_dd_pct", 0.0))

    cp_bal = total_bal
    cp_eq = total_eq
    cp_pnl = total_pnl
    cp_float = round(cp_eq - cp_bal, 2)
    cp_dd = round(max(0.0, ((cp_bal - cp_eq) / cp_bal * 100) if cp_bal > 0 else 0.0), 2)

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
                "net_exposure": "LONG 100%" if abs(cp_float) > 0.1 else "FLAT (0.0%)",
                "net_subtext": "US500 / USTEC" if abs(cp_float) > 0.1 else "Sin posiciones",
                "badge_desk": "CAPITAL PROPIO",
                "sub_badge": "TradFi MT5 + DEX Crypto",
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
                "net_exposure": "FLAT (0.0%)",
                "net_subtext": "Futuros CME & CFDs",
                "badge_desk": "CUENTAS DE FONDEO",
                "sub_badge": "Challenge Prop Firm $100k",
                "sync_badge": "● CHALLENGE $100K ACTIVO",
                "risk_limit_label": "Límite EOD DD",
                "risk_limit_val": "-3.50%",
                "desc": "Supervisión de cuenta de fondeo evaluativa: Challenge de $100,000 USD (CME Globex + CFDs)."
            }
        },
        "mt5": {
            "status": "ONLINE" if live_broker.get("trade_allowed", True) else "OFFLINE",
            "account": live_broker.get("account", 53120791),
            "server": live_broker.get("server", "ICMarketsSC-Demo"),
            "balance": ic_bal,
            "equity": ic_eq,
            "realized_pnl": ic_pnl,
            "currency": "USD",
            "risk_mode": "1.5% Dinámico Compuesto",
            "monitored_assets": ["US500", "USTEC", "EURUSD"]
        },
        "hyperliquid": {
            "status": "ONLINE",
            "exchange": "Hyperliquid L1 Testnet (DEX)",
            "balance": hl_bal,
            "equity": hl_eq,
            "realized_pnl": hl_pnl,
            "currency": "USDC",
            "strategy": "STRAT-FAST-035 (BTC 1h)",
            "fees": "14 bps Taker + Funding 1h"
        },
        "daemon": {
            "status": "ACTIVE",
            "frequency": "Cada 1 hora",
            "active_assets": ["US500", "USTEC", "EURUSD", "BTC/USDT"]
        }
    }'''

content_norm = content.replace("\r\n", "\n")
target_norm = target.replace("\r\n", "\n")
if target_norm in content_norm:
    content_norm = content_norm.replace(target_norm, replacement.replace("\r\n", "\n"))
    with open(BACKEND_PATH, "w", encoding="utf-8") as f:
        f.write(content_norm)
    print("backend.py updated successfully!")
else:
    print("Target not found in backend.py!")
    exit(1)
