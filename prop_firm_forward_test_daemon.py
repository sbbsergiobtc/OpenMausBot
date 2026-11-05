#!/usr/bin/env python3
"""
Institutional Multi-Branch Forward Test & Live MT5 Compounding Execution Daemon
AlgrokQuant · Desk Lead Nexus
Gobernanza Dual (LESSON-017) & Validacion Trifacetica (LESSON-018)

EXCLUSIVO PARA ACTIVOS TRADFI (BROKER IC MARKETS MT5):
  • RAMA CAPITAL PROPIO (INTERES COMPUESTO DINAMICO % SOBRE BALANCE VIVO):
      1. CAP-SPX-006: S&P 500 4h Bollinger Dip Reversion (US500, 1.50% riesgo)
      2. CAP-NDX-005: Nasdaq 100 2h Bollinger Dip Reversion (USTEC, 1.50% riesgo)
  • RAMA CUENTAS DE FONDEO (PROP FIRM FOREX):
      3. PROP-FX-EUR-001: EUR/USD 1h London-NY Session (EURUSD, 1.00% riesgo)

NOTA: Cualquier estrategia Cripto (ej. STRAT-FAST-035 BTC) se ejecuta EXCLUSIVAMENTE
en proveedores cripto nativos (Hyperliquid DEX L1 / Binance) y NUNCA en MT5.
"""

import os
import sys
import json
import time
import datetime
import argparse
import numpy as np
import pandas as pd
import yfinance as yf

sys.path.insert(0, '/root/AlgrokQuant')
from execution.mt5_client import MT5Client

try:
    from jev.screener import JevScreener
    jev_screener = JevScreener(max_allowed_entropy=0.84, regime_shift_delta=0.12, max_capital_propio_dd=20.0)
except Exception as e:
    jev_screener = None
    print(f"[WARN] JevScreener no inicializado: {e}")

STATE_FILE = '/root/AlgrokQuant/data/paper_trades/prop_firm_forward_test_state.json'
JOURNAL_FILE = '/root/AlgrokQuant/library/journal/PROP_FIRM_SPRINT_JOURNAL.md'

PORTFOLIO_CONFIG = {
    # RAMA 2: CAPITAL PROPIO TRADFI (COMPUESTO % SOBRE BALANCE VIVO IC MARKETS)
    'US500': {
        'id': 'CAP-SPX-006',
        'branch': 'CAPITAL_PROPIO',
        'ticker_yf': '^GSPC',
        'broker_symbol': 'US500',
        'risk_pct': 0.015,     # 1.50% de riesgo por operacion (Interes Compuesto)
        'spread_pts': 0.4,
        'tf': '4h'
    },
    'USTEC': {
        'id': 'CAP-NDX-005',
        'branch': 'CAPITAL_PROPIO',
        'ticker_yf': '^NDX',
        'broker_symbol': 'USTEC',
        'risk_pct': 0.015,     # 1.50% de riesgo por operacion (Interes Compuesto)
        'spread_pts': 1.5,
        'tf': '2h'
    },
    # RAMA 1: FOREX PROP FIRM
    'EURUSD': {
        'id': 'PROP-FX-EUR-001',
        'branch': 'PROP_FIRM',
        'ticker_yf': 'EURUSD=X',
        'broker_symbol': 'EURUSD',
        'risk_pct': 0.010,     # 1.00% de riesgo por operacion (Proteccion EOD DD)
        'spread_pts': 0.00008,
        'tf': '1h'
    }
}

mt5 = MT5Client()


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
                if 'capital_propio' not in state:
                    state['capital_propio'] = {'open_positions': {}, 'closed_trades': []}
                if 'prop_firm' not in state:
                    state['prop_firm'] = {'open_positions': {}, 'closed_trades': []}
                return state
        except Exception as e:
            print(f"Error cargando estado ({e}). Reinicializando...")

    return {
        'status': 'ACTIVE',
        'start_date': str(datetime.date.today()),
        'capital_propio': {
            'initial_balance': 1000.0,
            'current_balance': 1000.0,
            'open_positions': {},
            'closed_trades': []
        },
        'prop_firm': {
            'initial_balance': 100000.0,
            'current_balance': 100000.0,
            'open_positions': {},
            'closed_trades': []
        },
        'live_broker_sync': {
            'account': None,
            'broker_balance': 1000.0,
            'broker_equity': 1000.0,
            'last_sync': None
        },
        'order_history': [],
        'last_eval_timestamp': None
    }


def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def calculate_dynamic_lots(symbol_key: str, balance: float, entry_p: float, sl_p: float) -> float:
    cfg = PORTFOLIO_CONFIG[symbol_key]
    broker_sym = cfg['broker_symbol']
    risk_pct = cfg['risk_pct']

    sym_info = mt5.get_symbol_info(broker_sym).get('symbol', {})
    cs = float(sym_info.get('trade_contract_size', 1.0))
    vmin = float(sym_info.get('volume_min', 0.01))
    vmax = float(sym_info.get('volume_max', 100.0))
    vstep = float(sym_info.get('volume_step', 0.01))

    risk_usd = balance * risk_pct
    sl_dist = abs(entry_p - sl_p)
    if sl_dist <= 0:
        return vmin

    raw_lots = risk_usd / (sl_dist * cs)
    stepped_lots = round(raw_lots / vstep) * vstep
    final_lots = max(vmin, min(vmax, stepped_lots))
    return round(final_lots, 4)


def fetch_latest_candles(ticker: str, interval: str = '1h', period: str = '60d') -> pd.DataFrame:
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty:
            return df
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
        return df.dropna()
    except Exception as e:
        print(f"Error descargando {ticker}: {e}")
        return pd.DataFrame()


def evaluate_ndx_2h(df_1h: pd.DataFrame) -> dict:
    df_2h = df_1h.resample('2h').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna()
    if len(df_2h) < 50:
        return {'signal': 'HOLD', 'last_price': 0.0, 'sma': 0.0, 'atr': 0.0}
    c = df_2h['close']
    ema200 = c.ewm(span=200, adjust=False).mean()
    sma20 = c.rolling(20).mean()
    std20 = c.rolling(20).std()
    lower_bb = sma20 - 2.0 * std20

    last_c = float(c.iloc[-1])
    last_sma = float(sma20.iloc[-1])
    last_lower = float(lower_bb.iloc[-1])
    last_ema = float(ema200.iloc[-1])
    atr = float(df_2h['high'].iloc[-1] - df_2h['low'].iloc[-1])

    sig = 'BUY' if (last_c < last_lower and last_c > last_ema) else ('EXIT' if last_c > last_sma else 'HOLD')
    return {'signal': sig, 'last_price': last_c, 'sma': last_sma, 'lower': last_lower, 'atr': atr}


def evaluate_spx_4h(df_1h: pd.DataFrame) -> dict:
    df_4h = df_1h.resample('4h').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna()
    if len(df_4h) < 50:
        return {'signal': 'HOLD', 'last_price': 0.0, 'sma': 0.0, 'atr': 0.0}
    c = df_4h['close']
    ema200 = c.ewm(span=200, adjust=False).mean()
    sma20 = c.rolling(20).mean()
    std20 = c.rolling(20).std()
    lower_bb = sma20 - 1.2 * std20

    last_c = float(c.iloc[-1])
    last_sma = float(sma20.iloc[-1])
    last_lower = float(lower_bb.iloc[-1])
    last_ema = float(ema200.iloc[-1])
    atr = float(df_4h['high'].iloc[-1] - df_4h['low'].iloc[-1])

    sig = 'BUY' if (last_c < last_lower and last_c > last_ema) else ('EXIT' if last_c > last_sma else 'HOLD')
    return {'signal': sig, 'last_price': last_c, 'sma': last_sma, 'lower': last_lower, 'atr': atr}


def evaluate_eur_1h(df_1h: pd.DataFrame) -> dict:
    if len(df_1h) < 100:
        return {'signal': 'HOLD', 'last_price': 0.0, 'sma': 0.0, 'atr': 0.0}
    c = df_1h['close']
    hour = df_1h.index[-1].hour
    is_session = 7 <= hour <= 17
    sma24 = c.rolling(24).mean()
    std24 = c.rolling(24).std()
    lower_bb = sma24 - 2.0 * std24
    delta = c.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi14 = 100 - (100 / (1 + gain / (loss.replace(0, np.nan) + 1e-9)))

    last_c = float(c.iloc[-1])
    last_sma = float(sma24.iloc[-1])
    last_lower = float(lower_bb.iloc[-1])
    last_rsi = float(rsi14.iloc[-1])
    atr = float(df_1h['high'].iloc[-1] - df_1h['low'].iloc[-1])

    sig = 'BUY' if (is_session and last_c < last_lower and last_rsi < 35) else ('EXIT' if last_c > last_sma else 'HOLD')
    return {'signal': sig, 'last_price': last_c, 'sma': last_sma, 'lower': last_lower, 'atr': atr}


def sync_broker_state(state: dict) -> float:
    live_balance = 1000.0
    if not mt5.is_healthy():
        print("  [MT5] Puente no responde en 127.0.0.1:8001.")
        return live_balance
    try:
        acc = mt5.get_health()
        live_balance = float(acc.get('balance', 1000.0))
        state['live_broker_sync'] = {
            'account': acc.get('login'),
            'server': acc.get('server'),
            'broker_balance': live_balance,
            'broker_equity': float(acc.get('equity', live_balance)),
            'currency': acc.get('currency'),
            'trade_allowed': acc.get('trade_allowed'),
            'last_sync': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        print(f"  [MT5 SYNC] Cuenta {acc.get('login')} | Balance Vivo: ${live_balance:,.2f} USD (Interes Compuesto TradFi)")
    except Exception as e:
        print(f"  [MT5] Error sincronizando cuenta: {e}")
    return live_balance


def run_cycle():
    state = load_state()
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    print(f"\n[{now_str}] Ciclo Multiactivo TradFi: Capital Propio (% Compuesto) & Prop Firms...")

    # 1. Sincronizar Balance Vivo con IC Markets MT5
    current_live_balance = sync_broker_state(state)

    evaluators = {
        'US500':  (evaluate_spx_4h, '1h', '730d'),
        'USTEC':  (evaluate_ndx_2h, '1h', '730d'),
        'EURUSD': (evaluate_eur_1h, '1h', '60d')
    }

    market_snapshot = {}

    for sym, (eval_fn, interval, period) in evaluators.items():
        cfg = PORTFOLIO_CONFIG[sym]
        strat_id = cfg['id']
        branch = cfg['branch']
        broker_sym = cfg['broker_symbol']

        df = fetch_latest_candles(cfg['ticker_yf'], interval=interval, period=period)
        if df.empty:
            continue

        sig_data = eval_fn(df)
        market_snapshot[sym] = sig_data
        sig = sig_data['signal']
        price = sig_data['last_price']
        atr = max(sig_data.get('atr', price * 0.01), price * 0.005)

        print(f"  [{branch}] {sym} ({strat_id}): Precio={price:.4f} | Señal={sig}")

        pos_container = state['capital_propio']['open_positions'] if branch == 'CAPITAL_PROPIO' else state['prop_firm']['open_positions']
        pos = pos_container.get(sym)

        # A) Cierre de Posicion
        if pos is not None and sig == 'EXIT':
            ticket = pos.get('live_ticket')
            if ticket and mt5.is_healthy():
                print(f"  [MT5] Cerrando en broker posicion viva Ticket {ticket} ({broker_sym})...")
                mt5.close_position(ticket=ticket)

            del pos_container[sym]
            print(f"  >>> CERRADA POSICION EN {sym} ({strat_id}) <<<")

        # B) Apertura de Posicion con INTERES COMPUESTO DINAMICO
        elif pos is None and sig == 'BUY':
            entry_p = price + (cfg['spread_pts'] / 2.0)
            sl_dist = atr * 1.5
            sl_price = entry_p - sl_dist
            tp_price = entry_p + (atr * 2.5)

            dynamic_lots = calculate_dynamic_lots(sym, current_live_balance, entry_p, sl_price)
            risk_usd = current_live_balance * cfg['risk_pct']

            print(f"  [COMPUESTO %] Balance: ${current_live_balance:,.2f} | Riesgo: {cfg['risk_pct']*100:.1f}% (${risk_usd:.2f}) -> {dynamic_lots} lotes en {broker_sym}")

            ticket = None
            if mt5.is_healthy():
                live_res = mt5.open_order(
                    symbol=broker_sym,
                    order_type='BUY',
                    volume=dynamic_lots,
                    sl=sl_price,
                    tp=tp_price,
                    comment=f"{strat_id} %Comp"
                )
                print(f"  [MT5 ORDER RESULT] {live_res}")
                ticket = live_res.get('order') or live_res.get('deal')

            pos_container[sym] = {
                'strategy_id': strat_id,
                'branch': branch,
                'entry_price': entry_p,
                'dynamic_lots': dynamic_lots,
                'risk_usd': risk_usd,
                'sl_price': sl_price,
                'tp_price': tp_price,
                'entry_time': now_str,
                'live_ticket': ticket
            }
            state['order_history'].append({
                'timestamp': now_str,
                'symbol': sym,
                'strategy': strat_id,
                'branch': branch,
                'action': 'BUY_LONG',
                'lots': dynamic_lots,
                'price': entry_p,
                'sl': sl_price,
                'live_ticket': ticket,
                'notes': f"Sizing Dinamico {cfg['risk_pct']*100:.1f}% sobre ${current_live_balance:,.2f}"
            })
            print(f"  >>> NUEVA POSICION {branch}: {sym} {dynamic_lots} lotes | SL={sl_price:.4f} | Ticket={ticket} <<<")

    state['last_eval_timestamp'] = now_str
    save_state(state)
    update_obsidian_journal(state, market_snapshot)
    return state


def update_obsidian_journal(state: dict, market_snapshot: dict):
    os.makedirs(os.path.dirname(JOURNAL_FILE), exist_ok=True)
    today = str(datetime.date.today())
    sync = state.get('live_broker_sync', {})

    open_cap = state.get('capital_propio', {}).get('open_positions', {})
    open_prop = state.get('prop_firm', {}).get('open_positions', {})

    rows = []
    for s, p in open_cap.items():
        curr_p = market_snapshot.get(s, {}).get('last_price', p['entry_price'])
        rows.append(f"| **CAPITAL PROPIO (TradFi)** | {s} ({p['strategy_id']}) | {p['entry_time']} | {p['dynamic_lots']} lotes | ${p['risk_usd']:.2f} | {p['entry_price']:.2f} | {p['sl_price']:.2f} | {curr_p:.2f} | Ticket: `{p.get('live_ticket', '-')}` |")

    for s, p in open_prop.items():
        curr_p = market_snapshot.get(s, {}).get('last_price', p['entry_price'])
        rows.append(f"| **PROP FIRM (Forex)** | {s} ({p['strategy_id']}) | {p['entry_time']} | {p['dynamic_lots']} lotes | ${p['risk_usd']:.2f} | {p['entry_price']:.2f} | {p['sl_price']:.2f} | {curr_p:.2f} | Ticket: `{p.get('live_ticket', '-')}` |")

    table_text = "\n".join(rows) if rows else "*Sin posiciones abiertas en este momento. Sistema en monitorizacion activa.*"

    content = f"""---
title: "Bitacora Oficial · Capital Propio & Fondeo TradFi (Interes Compuesto MT5)"
date: "{today}"
last_evaluation: "{state.get('last_eval_timestamp')}"
status: "{state.get('status')}"
broker_account: "{sync.get('account', '-')}"
broker_server: "{sync.get('server', '-')}"
broker_balance: {sync.get('broker_balance', 0.0)}
broker_equity: {sync.get('broker_equity', 0.0)}
compounding_mode: "DYNAMIC_PERCENTAGE_RISK"
tags:
  - capital-propio-tradfi
  - prop-firm
  - interes-compuesto
  - mt5-live
  - tri-facet
---

# Bitacora Oficial · Capital Propio & Fondeo TradFi (Interes Compuesto MT5)

> [!NOTE]
> **Separacion Estricta de Ecosistemas de Ejecucion:**
> - **Activos TradFi (Indices y Forex):** Se gestionan exclusivamente en broker institucional **IC Markets MT5**.
> - **Activos Cripto:** Se gestionan exclusivamente en **Hyperliquid L1 DEX / Binance** (NUNCA en broker tradicional).

---

## 1. Cartera TradFi Activa y Estado de la Cuenta MT5

| Rama / Activo | Estrategia Oficial | Riesgo % | TF | Broker Ticker | Modo Sizing |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Capital Propio (Indices)** | **`CAP-SPX-006`** | **1.50%** | 4h | `US500` | Interes Compuesto Dinamico |
| **Capital Propio (Indices)** | **`CAP-NDX-005`** | **1.50%** | 2h | `USTEC` | Interes Compuesto Dinamico |
| **Fondeo (Forex)** | **`PROP-FX-EUR-001`** | **1.00%** | 1h | `EURUSD` | Proteccion EOD Drawdown |

| Metrica de Cuenta | Valor en Vivo | Observaciones |
| :--- | :---: | :---: |
| **Cuenta MT5** | **`{sync.get('account')}`** en **`{sync.get('server')}`** | IC Markets Demo SC (1:30) |
| **Balance Vivo** | **${sync.get('broker_balance', 0.0):,.2f} {sync.get('currency', 'USD')}** | Base para el calculo del proximo lote |
| **Equity Flotante** | **${sync.get('broker_equity', 0.0):,.2f} {sync.get('currency', 'USD')}** | Margen libre en MT5 |
| **Ultima Evaluacion** | `{state.get('last_eval_timestamp', '-')}` | Bucle horario continuo 24/7 |

---

## 2. Posiciones Vivas y Ordenes de Mercado

| Rama | Activo / Estrategia | Fecha Apertura | Lotaje Dinamico | Riesgo \$ | Entrada | Stop Loss | Actual | Ticket MT5 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
{table_text}

---
*Mantenido de forma autonoma por `algrokquant-forward-test.service` en `/library/journal/`.*
"""
    with open(JOURNAL_FILE, 'w', encoding='utf-8') as f:
        f.write(content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--daemon', action='store_true', help='Bucle continuo cada hora')
    args = parser.parse_args()

    if args.daemon:
        print("[AlgrokQuant Compounding Daemon] Iniciando bucle 24/7...")
        while True:
            try:
                run_cycle()
            except Exception as e:
                print(f"[ERROR] Excepcion en ciclo: {e}")
            time.sleep(3600)
    else:
        run_cycle()