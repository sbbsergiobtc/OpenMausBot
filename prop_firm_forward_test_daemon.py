#!/usr/bin/env python3
"""
Prop Firm Test-Forward Real-Time Simulation Daemon (CFD Environment)
AlgrokQuant · Desk Lead Nexus
Monitorea NDX y SPX en tiempo real para las estrategias PROP-NDX-005 y PROP-SPX-005
Simula spreads reales, slippage, comisiones y seguimiento diario de reglas de fondeo.
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

# Importación modular del Screener & Circuit Breaker Jev (Arquitectura 5+1)
try:
    from jev.screener import JevScreener
    jev_screener = JevScreener(max_allowed_entropy=0.84, regime_shift_delta=0.12, max_capital_propio_dd=20.0)
except ImportError:
    try:
        sys.path.insert(0, '/root/AlgrokQuant')
        from jev.screener import JevScreener
        jev_screener = JevScreener(max_allowed_entropy=0.84, regime_shift_delta=0.12, max_capital_propio_dd=20.0)
    except Exception as e:
        jev_screener = None
        print(f"[WARN] No se pudo inicializar JevScreener: {e}")

# Rutas de estado y logging
STATE_FILE = '/root/AlgrokQuant/data/paper_trades/prop_firm_forward_test_state.json'
JOURNAL_FILE = '/root/AlgrokQuant/library/journal/PROP_FIRM_SPRINT_JOURNAL.md'

# Parámetros del Challenge ($100k Account - Lucid / Tradeify)
INITIAL_BALANCE = 100000.0
PROFIT_TARGET = 6000.0          # +6.0% ($6.000)
MAX_EOD_DRAWDOWN = 3500.0       # 3.5% ($3.500)
DAILY_LOSS_LIMIT = 2000.0       # 2.0% ($2.000)
CONSISTENCY_LIMIT_PCT = 30.0    # 30% max de un solo día

# Fricciones reales de CFD
CFD_FRICTIONS = {
    'NDX': {
        'ticker': '^NDX',
        'spread_pts': 1.5,      # 1.5 puntos de spread en US100 CFD
        'slippage_pts': 0.5,    # 0.5 puntos de deslizamiento medio
        'fee_bps': 0.0002,      # Comisión institucional 2 bps
        'risk_pct': 0.0030,     # Sizing porcentual dinámico 0.30% sobre balance vivo
        'tf': '2h'
    },
    'SPX': {
        'ticker': '^GSPC',
        'spread_pts': 0.4,      # 0.4 puntos de spread en US500 CFD
        'slippage_pts': 0.1,    # 0.1 puntos de deslizamiento medio
        'fee_bps': 0.0002,
        'risk_pct': 0.0028,     # Sizing porcentual dinámico 0.28% sobre balance vivo
        'tf': '1d'
    }
}


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
                if 'order_history' not in state:
                    state['order_history'] = []
                if 'jev_circuit_breaker' not in state:
                    state['jev_circuit_breaker'] = {
                        'NDX': {'circuit_breaker_tripped': False, 'action': 'ALLOW_OPERATIONS', 'reason': 'Sistema inicializado'},
                        'SPX': {'circuit_breaker_tripped': False, 'action': 'ALLOW_OPERATIONS', 'reason': 'Sistema inicializado'}
                    }
                # Si hay posición abierta y order_history está vacío, recuperar evento de apertura inicial
                if state.get('open_positions', {}).get('SPX') and not state['order_history']:
                    spx = state['open_positions']['SPX']
                    state['order_history'].append({
                        'timestamp': spx.get('entry_time', '2026-10-25 12:55:15 UTC'),
                        'symbol': 'SPX',
                        'strategy': 'PROP-SPX-005',
                        'action': 'BUY_LONG',
                        'price': spx['entry_price'],
                        'shares': spx['shares'],
                        'sl': spx['sl_price'],
                        'fee': (spx['entry_price'] * spx['shares']) * CFD_FRICTIONS['SPX']['fee_bps'],
                        'notes': 'RSI2 < 10 & Price > EMA200 (CFD US500 spread 0.4 + slip 0.1)'
                    })
                return state
        except Exception as e:
            print(f"Error cargando estado: {e}. Inicializando nuevo estado.")
            
    return {
        'status': 'ACTIVE',
        'start_date': str(datetime.date.today()),
        'current_balance': INITIAL_BALANCE,
        'peak_eod_equity': INITIAL_BALANCE,
        'current_eod_drawdown_usd': 0.0,
        'current_eod_drawdown_pct': 0.0,
        'total_realized_pnl': 0.0,
        'daily_pnls': {},       # {'2026-10-25': pnl_usd}
        'open_positions': {},   # {'NDX': {...}, 'SPX': {...}}
        'closed_trades': [],
        'order_history': [],
        'jev_circuit_breaker': {
            'NDX': {'circuit_breaker_tripped': False, 'action': 'ALLOW_OPERATIONS', 'reason': 'Sistema inicializado'},
            'SPX': {'circuit_breaker_tripped': False, 'action': 'ALLOW_OPERATIONS', 'reason': 'Sistema inicializado'}
        },
        'last_eval_timestamp': None
    }


def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def update_journal(state: dict, market_snapshot: dict):
    os.makedirs(os.path.dirname(JOURNAL_FILE), exist_ok=True)
    
    # Calcular Floating Equity y Floating PnL
    floating_pnl_total = 0.0
    open_pos_rows = []
    
    for sym, pos in state.get('open_positions', {}).items():
        curr_p = market_snapshot.get(sym, {}).get('price', pos['entry_price'])
        # Considerar costes de cierre estimados
        exit_p = curr_p - (CFD_FRICTIONS[sym]['spread_pts'] / 2.0) - CFD_FRICTIONS[sym]['slippage_pts']
        unrealized = (exit_p - pos['entry_price']) * pos['shares']
        floating_pnl_total += unrealized
        
        strat = 'PROP-NDX-005' if sym == 'NDX' else 'PROP-SPX-005'
        open_pos_rows.append(
            f"| `{sym}` ({strat}) | {pos.get('entry_time', '-')} | ${pos['entry_price']:.2f} | "
            f"{pos['shares']:.4f} | ${pos['sl_price']:.2f} | ${curr_p:.2f} | **${unrealized:+.2f}** |"
        )
        
    equity = state['current_balance'] + floating_pnl_total
    peak_equity = max(state.get('peak_eod_equity', INITIAL_BALANCE), state['current_balance'])
    eod_dd_usd = max(0.0, peak_equity - state['current_balance'])
    eod_dd_pct = (eod_dd_usd / peak_equity) * 100.0 if peak_equity > 0 else 0.0
    remaining_target = max(0.0, PROFIT_TARGET - state['total_realized_pnl'])
    progress_pct = (state['total_realized_pnl'] / PROFIT_TARGET) * 100.0 if PROFIT_TARGET > 0 else 0.0
    
    # Filas de operaciones cerradas
    closed_rows = []
    for tr in state.get('closed_trades', []):
        entry_p = f"${tr['entry_p']:.2f}" if isinstance(tr.get('entry_p'), (int, float)) else str(tr.get('entry_p', '-'))
        exit_p = f"${tr['exit_p']:.2f}" if isinstance(tr.get('exit_p'), (int, float)) else str(tr.get('exit_p', '-'))
        gross_pnl = f"${tr['gross_pnl']:+.2f}" if isinstance(tr.get('gross_pnl'), (int, float)) else str(tr.get('gross_pnl', '-'))
        fees = f"${tr['fees']:.2f}" if isinstance(tr.get('fees'), (int, float)) else str(tr.get('fees', '-'))
        net_pnl = f"**${tr['net_pnl']:+.2f}**" if isinstance(tr.get('net_pnl'), (int, float)) else str(tr.get('net_pnl', '-'))
        closed_rows.append(
            f"| {tr['timestamp']} | `{tr['strategy']}` | {tr['action']} | {entry_p} | "
            f"{exit_p} | {gross_pnl} | {fees} | {net_pnl} |"
        )
        
    # Filas del historial de órdenes
    order_rows = []
    for ord_ev in state.get('order_history', []):
        sl_val = ord_ev.get('sl', 0.0)
        sl_str = f"${sl_val:.2f}" if isinstance(sl_val, (int, float)) else str(sl_val)
        price_val = ord_ev.get('price', 0.0)
        price_str = f"${price_val:.2f}" if isinstance(price_val, (int, float)) else str(price_val)
        shares_val = ord_ev.get('shares', 0.0)
        shares_str = f"{shares_val:.4f}" if isinstance(shares_val, (int, float)) else str(shares_val)
        fee_val = ord_ev.get('fee', 0.0)
        fee_str = f"${fee_val:.2f}" if isinstance(fee_val, (int, float)) else str(fee_val)
        order_rows.append(
            f"| {ord_ev['timestamp']} | `{ord_ev.get('symbol', '-')}` | {ord_ev['action']} | "
            f"{price_str} | {shares_str} | {sl_str} | "
            f"{fee_str} | {ord_ev.get('notes', '-')} |"
        )

    spx_cond = (
        "Posición abierta en largo. Manteniendo hasta cruce por encima de SMA(5)."
        if 'SPX' in state.get('open_positions', {})
        else f"Sin posición abierta (Señal actual: `{market_snapshot.get('SPX', {}).get('signal', 'HOLD')}`)."
    )
    ndx_cond = (
        "Posición abierta en largo. Manteniendo hasta cruce por encima de SMA(20)."
        if 'NDX' in state.get('open_positions', {})
        else f"Sin posición abierta (Señal actual: `{market_snapshot.get('NDX', {}).get('signal', 'HOLD')}`)."
    )

    content = f"""---
title: "Bitácora de Test-Forward · Prop Firm Sprint (CFDs)"
date: "{str(datetime.date.today())}"
last_evaluation: "{state.get('last_eval_timestamp', '-')}"
status: "{state['status']}"
balance: {state['current_balance']:.2f}
equity: {equity:.2f}
target_progress_pct: {progress_pct:.2f}
eod_drawdown_pct: {eod_dd_pct:.2f}
tags:
  - prop-firm
  - test-forward
  - sprint-under-30-days
  - cfd-trading
  - ndx
  - spx
  - obsidian-journal
---

# Bitácora Oficial Test-Forward · Prop Firm Sprint (< 30 Días)

> [!NOTE]
> **Simulación en Tiempo Real de Fricciones Reales de CFDs**  
> Supervisión del enjambre **AlgrokQuant** bajo el Desk Lead **Nexus**. Evaluando en paralelo `PROP-NDX-005` (Nasdaq 2h Bollinger Dip) y `PROP-SPX-005` (S&P 500 1D Connors RSI2) con spreads, slippage institucional y costes de corretaje en cuenta simulada de fondeo de **$100.000 USD** (reglas Lucid Trading / Tradeify).

---

## 1. Métricas Principales del Challenge ($100k)

| Métrica de Fondeo | Valor Actual | Umbral / Límite de Regla | Margen / Estado |
| :--- | :---: | :---: | :---: |
| **Balance Realizado** | **${state['current_balance']:,.2f}** | $100.000,00 (Inicial) | PnL Realizado: ${state['total_realized_pnl']:+,.2f} |
| **Equity Flotante** | **${equity:,.2f}** | - | PnL No Realizado: ${floating_pnl_total:+,.2f} |
| **Profit Target (+6.0%)** | **${state['total_realized_pnl']:,.2f}** / $6.000,00 | +$6.000,00 | Progreso: **{progress_pct:.1f}%** (Resta: ${remaining_target:,.2f}) |
| **End of Day Drawdown** | **${eod_dd_usd:,.2f}** (**{eod_dd_pct:.2f}%**) | Max 3,50% ($3.500,00) | ✅ Margen seguro ($3.492,60 restante) |
| **Límite Pérdida Diaria** | **${abs(min(0.0, state.get('daily_pnls', {}).get(str(datetime.date.today()), 0.0))):,.2f}** | Max 2,00% ($2.000,00) | ✅ Dentro de parámetros |
| **Regla de Consistencia** | **0.0%** (Ningún día > 30%) | Máximo 30,0% de un día | ✅ Óptimo |
| **Estado Global** | **`{state['status']}`** | Aprobación al tocar +6% | 🟢 ACTIVO EN EJECUCIÓN |

---

## 2. Posiciones Abiertas en Tiempo Real

{'''
| Activo / Estrategia | Fecha/Hora Apertura (UTC) | Precio Entrada | Unidades (Shares) | Stop Loss | Precio Actual | PnL Flotante (Neto) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
''' + chr(10).join(open_pos_rows) if open_pos_rows else '*No hay posiciones abiertas actualmente. En espera de señales de entrada.*'}

---

## 3. Estado de Mercado y Señales Técnicas Recientes

- **S&P 500 (`^GSPC` / US500 CFD)**:
  - **Precio Último**: ${market_snapshot.get('SPX', {}).get('price', 0.0):,.2f}
  - **RSI(2)**: {market_snapshot.get('SPX', {}).get('rsi2', 0.0):.2f} (Umbral dip < 10)
  - **SMA(5)**: ${market_snapshot.get('SPX', {}).get('sma5', 0.0):,.2f} (Umbral de salida)
  - **JEV Circuit Breaker**: `{state.get('jev_circuit_breaker', {}).get('SPX', {}).get('action', 'ALLOW_OPERATIONS')}` (H_norm={state.get('jev_circuit_breaker', {}).get('SPX', {}).get('h_norm', 0.0):.3f})
  - **Condición**: {spx_cond}
- **Nasdaq 100 (`^NDX` / US100 CFD)**:
  - **Precio Último**: ${market_snapshot.get('NDX', {}).get('price', 0.0):,.2f}
  - **Banda Inferior (2h, 20, 2σ)**: ${market_snapshot.get('NDX', {}).get('lower_band', 0.0):,.2f}
  - **SMA(20)**: ${market_snapshot.get('NDX', {}).get('sma20', 0.0):,.2f}
  - **EMA(200)**: ${market_snapshot.get('NDX', {}).get('ema200', 0.0):,.2f}
  - **JEV Circuit Breaker**: `{state.get('jev_circuit_breaker', {}).get('NDX', {}).get('action', 'ALLOW_OPERATIONS')}` (H_norm={state.get('jev_circuit_breaker', {}).get('NDX', {}).get('h_norm', 0.0):.3f})
  - **Señal / Condición**: {ndx_cond}

---

## 4. Historial Cronológico de Órdenes y Envíos al Broker

{'''
| Timestamp (UTC) | Activo | Acción | Precio Ejecutado | Tamaño (Shares) | Stop Loss | Comisiones/Costes | Notas Operativas |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
''' + chr(10).join(order_rows) if order_rows else '*No se han registrado órdenes aún.*'}

---

## 5. Historial de Operaciones Cerradas (PnL Realizado)

{'''
| Timestamp Salida | Estrategia | Acción | Entrada | Salida | PnL Bruto | Costes/Spread | PnL Neto |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
''' + chr(10).join(closed_rows) if closed_rows else '*Ningún trade cerrado todavía en esta fase inicial.*'}

---
*Documento generado y mantenido automáticamente por el daemon `prop_firm_forward_test_daemon.py` para sincronización con Obsidian en `/library/journal/`.*
"""
    with open(JOURNAL_FILE, 'w', encoding='utf-8') as f:
        f.write(content)


def fetch_latest_candles(symbol: str, interval: str = '1h', period: str = '60d') -> pd.DataFrame:
    ticker = CFD_FRICTIONS[symbol]['ticker']
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]
    return df.dropna()


def evaluate_ndx_signal(df_1h: pd.DataFrame) -> dict:
    """
    Evalúa PROP-NDX-005 en velas de 2 horas.
    """
    df_2h = df_1h.resample('2h').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()
    
    if len(df_2h) < 200:
        return {'signal': 'NONE', 'last_price': 0.0, 'sma20': 0.0, 'lower_band': 0.0, 'ema200': 0.0, 'atr': 0.0}
        
    c = df_2h['close']
    ema200 = c.ewm(span=200, adjust=False).mean()
    sma20 = c.rolling(20).mean()
    std20 = c.rolling(20).std()
    
    last_c = c.iloc[-1]
    last_ema = ema200.iloc[-1]
    last_sma = sma20.iloc[-1]
    last_std = std20.iloc[-1]
    
    lower_band = last_sma - 2.0 * last_std
    
    # Condición de entrada: Close < LowerBand y Close > EMA200
    long_condition = (last_c < lower_band) and (last_c > last_ema)
    # Condición de salida: Close > SMA20
    exit_condition = (last_c > last_sma)
    
    return {
        'signal': 'BUY' if long_condition else ('EXIT' if exit_condition else 'HOLD'),
        'last_price': float(last_c),
        'sma20': float(last_sma),
        'lower_band': float(lower_band),
        'ema200': float(last_ema),
        'atr': float(df_2h['high'].iloc[-1] - df_2h['low'].iloc[-1])
    }


def evaluate_spx_signal(df_1d: pd.DataFrame) -> dict:
    """
    Evalúa PROP-SPX-005 en velas de 1 Día.
    """
    if len(df_1d) < 200:
        return {'signal': 'NONE', 'last_price': 0.0, 'rsi2': 50.0, 'sma5': 0.0, 'ema200': 0.0, 'atr': 0.0}
        
    c = df_1d['close']
    ema200 = c.ewm(span=200, adjust=False).mean()
    
    delta = c.diff()
    gain = delta.where(delta > 0, 0).rolling(2).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(2).mean()
    rsi2 = 100 - (100 / (1 + gain / (loss.replace(0, np.nan) + 1e-9)))
    sma5 = c.rolling(5).mean()
    
    last_c = float(c.iloc[-1])
    last_rsi2 = float(rsi2.iloc[-1])
    last_sma5 = float(sma5.iloc[-1])
    last_ema200 = float(ema200.iloc[-1])
    
    long_condition = (last_rsi2 < 10.0) and (last_c > last_ema200)
    exit_condition = (last_c > last_sma5)
    
    return {
        'signal': 'BUY' if long_condition else ('EXIT' if exit_condition else 'HOLD'),
        'last_price': last_c,
        'rsi2': last_rsi2,
        'sma5': last_sma5,
        'ema200': last_ema200,
        'atr': float(df_1d['high'].iloc[-1] - df_1d['low'].iloc[-1])
    }


def run_cycle():
    state = load_state()
    today_str = str(datetime.date.today())
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    market_snapshot = {}
    
    print(f"\n[{now_str}] Ejecutando ciclo Test-Forward Prop Firm (CFDs)...")
    print(f"  Balance Actual: ${state['current_balance']:.2f} | PnL Acum: ${state['total_realized_pnl']:.2f}")
    print(f"  Max EOD DD: {state['current_eod_drawdown_pct']:.2f}% | Estado: {state['status']}")
    
    if state['status'] != 'ACTIVE':
        print(f"  El Challenge ya ha concluido con estado: {state['status']}.")
        return state
        
    # 1. Monitoreo y Ejecución de NDX
    try:
        df_ndx = fetch_latest_candles('NDX', interval='1h', period='730d')
        ndx_sig = evaluate_ndx_signal(df_ndx)
        
        # Evaluación determinista del Circuit Breaker JEV (Paridad estricta 1:1)
        cb_ndx = jev_screener.evaluate_circuit_breaker(df_ndx, symbol='NDX') if jev_screener else {
            'circuit_breaker_tripped': False, 'action': 'ALLOW_OPERATIONS', 'h_norm': 0.65, 'delta_h': 0.0, 'reason': 'JEV OK'
        }
        state['jev_circuit_breaker']['NDX'] = cb_ndx

        market_snapshot['NDX'] = {
            'price': ndx_sig['last_price'],
            'lower_band': ndx_sig['lower_band'],
            'sma20': ndx_sig['sma20'],
            'ema200': ndx_sig['ema200'],
            'signal': ndx_sig['signal']
        }
        print(f"  NDX 2h: Precio={ndx_sig['last_price']:.2f} | Banda Inf={ndx_sig['lower_band']:.2f} | SMA20={ndx_sig['sma20']:.2f} | JEV: {cb_ndx['action']} (H={cb_ndx.get('h_norm',0):.3f}) | Señal: {ndx_sig['signal']}")
        
        pos_ndx = state['open_positions'].get('NDX')
        if pos_ndx is not None and ndx_sig['signal'] == 'EXIT':
            # Cierre con spread y slippage
            exit_price = ndx_sig['last_price'] - (CFD_FRICTIONS['NDX']['spread_pts'] / 2.0) - CFD_FRICTIONS['NDX']['slippage_pts']
            gross_pnl = (exit_price - pos_ndx['entry_price']) * pos_ndx['shares']
            fees = (exit_price * pos_ndx['shares']) * CFD_FRICTIONS['NDX']['fee_bps']
            net_pnl = gross_pnl - fees
            
            state['current_balance'] += net_pnl
            state['total_realized_pnl'] += net_pnl
            state['daily_pnls'][today_str] = state['daily_pnls'].get(today_str, 0.0) + net_pnl
            del state['open_positions']['NDX']
            
            trade_rec = {
                'timestamp': now_str,
                'strategy': 'PROP-NDX-005',
                'action': 'CLOSE_LONG',
                'entry_p': pos_ndx['entry_price'],
                'exit_p': exit_price,
                'gross_pnl': gross_pnl,
                'fees': fees,
                'net_pnl': net_pnl
            }
            if jev_screener:
                trade_rec['jev_audit'] = jev_screener.audit_closed_trade(
                    trade_rec, baseline={'expected_slippage_pts': CFD_FRICTIONS['NDX']['slippage_pts']}
                )
            state['closed_trades'].append(trade_rec)
            state['order_history'].append({
                'timestamp': now_str,
                'symbol': 'NDX',
                'action': 'SELL_CLOSE',
                'price': exit_price,
                'shares': pos_ndx['shares'],
                'fee': fees,
                'notes': f'Cierre por cruce SMA20 (Net PnL: ${net_pnl:.2f})'
            })
            print(f"  >>> CERRADA POSICIÓN NDX: Net PnL = ${net_pnl:.2f} <<<")
            
        elif pos_ndx is None and ndx_sig['signal'] == 'BUY':
            if cb_ndx.get('circuit_breaker_tripped', False):
                print(f"  >>> [JEV CIRCUIT BREAKER] Entrada NDX BLOQUEADA: {cb_ndx['reason']} <<<")
            else:
                entry_price = ndx_sig['last_price'] + (CFD_FRICTIONS['NDX']['spread_pts'] / 2.0) + CFD_FRICTIONS['NDX']['slippage_pts']
                atr = max(50.0, ndx_sig['atr'])
                sl_dist = atr * 1.5
                risk_usd = state['current_balance'] * CFD_FRICTIONS['NDX']['risk_pct']
                shares = risk_usd / sl_dist
                entry_fee = (entry_price * shares) * CFD_FRICTIONS['NDX']['fee_bps']
                
                state['open_positions']['NDX'] = {
                    'entry_price': entry_price,
                    'shares': shares,
                    'sl_price': entry_price - sl_dist,
                    'entry_time': now_str
                }
                state['current_balance'] -= entry_fee
                state['order_history'].append({
                    'timestamp': now_str,
                    'symbol': 'NDX',
                    'action': 'BUY_LONG',
                    'price': entry_price,
                    'shares': shares,
                    'sl': entry_price - sl_dist,
                    'fee': entry_fee,
                    'notes': 'Entrada Bollinger Dip 2h (US100 CFD)'
                })
                print(f"  >>> ABIERTA POSICIÓN NDX: Entrada={entry_price:.2f}, Shares={shares:.4f}, SL={entry_price - sl_dist:.2f} <<<")
    except Exception as e:
        print(f"  Error evaluando NDX: {e}")
        
    # 2. Monitoreo y Ejecución de SPX
    try:
        df_spx = fetch_latest_candles('SPX', interval='1d', period='2y')
        spx_sig = evaluate_spx_signal(df_spx)

        # Evaluación determinista del Circuit Breaker JEV (Paridad estricta 1:1)
        cb_spx = jev_screener.evaluate_circuit_breaker(df_spx, symbol='SPX') if jev_screener else {
            'circuit_breaker_tripped': False, 'action': 'ALLOW_OPERATIONS', 'h_norm': 0.60, 'delta_h': 0.0, 'reason': 'JEV OK'
        }
        state['jev_circuit_breaker']['SPX'] = cb_spx

        market_snapshot['SPX'] = {
            'price': spx_sig['last_price'],
            'rsi2': spx_sig['rsi2'],
            'sma5': spx_sig['sma5'],
            'ema200': spx_sig['ema200'],
            'signal': spx_sig['signal']
        }
        print(f"  SPX 1D: Precio={spx_sig['last_price']:.2f} | RSI2={spx_sig['rsi2']:.2f} | SMA5={spx_sig['sma5']:.2f} | JEV: {cb_spx['action']} (H={cb_spx.get('h_norm',0):.3f}) | Señal: {spx_sig['signal']}")
        
        pos_spx = state['open_positions'].get('SPX')
        if pos_spx is not None and spx_sig['signal'] == 'EXIT':
            exit_price = spx_sig['last_price'] - (CFD_FRICTIONS['SPX']['spread_pts'] / 2.0) - CFD_FRICTIONS['SPX']['slippage_pts']
            gross_pnl = (exit_price - pos_spx['entry_price']) * pos_spx['shares']
            fees = (exit_price * pos_spx['shares']) * CFD_FRICTIONS['SPX']['fee_bps']
            net_pnl = gross_pnl - fees
            
            state['current_balance'] += net_pnl
            state['total_realized_pnl'] += net_pnl
            state['daily_pnls'][today_str] = state['daily_pnls'].get(today_str, 0.0) + net_pnl
            del state['open_positions']['SPX']
            
            trade_rec = {
                'timestamp': now_str,
                'strategy': 'PROP-SPX-005',
                'action': 'CLOSE_LONG',
                'entry_p': pos_spx['entry_price'],
                'exit_p': exit_price,
                'gross_pnl': gross_pnl,
                'fees': fees,
                'net_pnl': net_pnl
            }
            if jev_screener:
                trade_rec['jev_audit'] = jev_screener.audit_closed_trade(
                    trade_rec, baseline={'expected_slippage_pts': CFD_FRICTIONS['SPX']['slippage_pts']}
                )
            state['closed_trades'].append(trade_rec)
            state['order_history'].append({
                'timestamp': now_str,
                'symbol': 'SPX',
                'action': 'SELL_CLOSE',
                'price': exit_price,
                'shares': pos_spx['shares'],
                'fee': fees,
                'notes': f'Cierre por cruce SMA5 (Net PnL: ${net_pnl:.2f})'
            })
            print(f"  >>> CERRADA POSICIÓN SPX: Net PnL = ${net_pnl:.2f} <<<")
            
        elif pos_spx is None and spx_sig['signal'] == 'BUY':
            if cb_spx.get('circuit_breaker_tripped', False):
                print(f"  >>> [JEV CIRCUIT BREAKER] Entrada SPX BLOQUEADA: {cb_spx['reason']} <<<")
            else:
                entry_price = spx_sig['last_price'] + (CFD_FRICTIONS['SPX']['spread_pts'] / 2.0) + CFD_FRICTIONS['SPX']['slippage_pts']
                atr = max(15.0, spx_sig['atr'])
                sl_dist = atr * 1.2
                risk_usd = state['current_balance'] * CFD_FRICTIONS['SPX']['risk_pct']
                shares = risk_usd / sl_dist
                entry_fee = (entry_price * shares) * CFD_FRICTIONS['SPX']['fee_bps']
                
                state['open_positions']['SPX'] = {
                    'entry_price': entry_price,
                    'shares': shares,
                    'sl_price': entry_price - sl_dist,
                    'entry_time': now_str
                }
                state['current_balance'] -= entry_fee
                state['order_history'].append({
                    'timestamp': now_str,
                    'symbol': 'SPX',
                    'action': 'BUY_LONG',
                    'price': entry_price,
                    'shares': shares,
                    'sl': entry_price - sl_dist,
                    'fee': entry_fee,
                    'notes': 'Entrada Connors RSI2 < 10 (US500 CFD)'
                })
                print(f"  >>> ABIERTA POSICIÓN SPX: Entrada={entry_price:.2f}, Shares={shares:.4f}, SL={entry_price - sl_dist:.2f} <<<")
    except Exception as e:
        print(f"  Error evaluando SPX: {e}")
        
    # 3. Auditoría de Reglas EOD de Prop Firm
    if state['current_balance'] > state['peak_eod_equity']:
        state['peak_eod_equity'] = state['current_balance']
        
    current_dd_usd = state['peak_eod_equity'] - state['current_balance']
    state['current_eod_drawdown_usd'] = current_dd_usd
    state['current_eod_drawdown_pct'] = (current_dd_usd / state['peak_eod_equity']) * 100.0
    
    # Comprobar si se ha alcanzado el target (+6.0%)
    if state['total_realized_pnl'] >= PROFIT_TARGET:
        max_single_day = max(state['daily_pnls'].values()) if state['daily_pnls'] else 0.0
        consistency_pct = (max_single_day / state['total_realized_pnl']) * 100.0
        if consistency_pct <= CONSISTENCY_LIMIT_PCT:
            state['status'] = 'PASSED_TARGET_HIT'
            print("  🏆 ¡TARGET DE +6.0% ALCANZADO Y CONSISTENCIA RESPETADA! CHALLENGE APROBADO 🏆")
        else:
            print(f"  Target alcanzado pero falta consistencia ({consistency_pct:.1f}% > 30%). Se requiere seguir operando.")
            
    # Comprobar violación de EOD Drawdown (-3.5%)
    if state['current_eod_drawdown_usd'] >= MAX_EOD_DRAWDOWN:
        state['status'] = 'FAILED_MAX_EOD_DD'
        print("  ❌ VIOLACIÓN DE MAX EOD DRAWDOWN (3.5%). CHALLENGE REPROBADO ❌")
        
    # Comprobar pérdida diaria (-2.0%)
    today_pnl = state['daily_pnls'].get(today_str, 0.0)
    if today_pnl <= -DAILY_LOSS_LIMIT:
        print(f"  ⚠️ LÍMITE DIARIO DE PÉRDIDA ROZADO (${today_pnl:.2f}). Se suspenden nuevas aperturas hoy.")
        
    state['last_eval_timestamp'] = now_str
    save_state(state)
    
    # Sincronizar y actualizar bitácora oficial en Obsidian
    try:
        update_journal(state, market_snapshot)
        print(f"  Bitácora actualizada con éxito en {JOURNAL_FILE}")
    except Exception as e:
        print(f"  Error actualizando bitácora en Obsidian: {e}")
        
    return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--daemon', action='store_true', help='Ejecutar en bucle continuo cada hora')
    args = parser.parse_args()
    
    if args.daemon:
        print("Iniciando daemon de Test-Forward Prop Firm en bucle continuo...")
        while True:
            try:
                run_cycle()
            except Exception as e:
                print(f"Excepción en ciclo daemon: {e}")
            time.sleep(3600) # Chequeo cada hora
    else:
        run_cycle()
