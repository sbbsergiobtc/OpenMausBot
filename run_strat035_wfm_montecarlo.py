#!/usr/bin/env python3
"""
Validación Rigurosa Walk-Forward (WFM) y Test de Estrés Monte Carlo para STRAT-FAST-035 (BTC 1h)
Configuración: D30 / H72 / LONG ONLY / SL 2.0x ATR / TP 4.0x ATR
Gobernanza: LESSON-20261028-014 y Arquitectura JevScreener 5+1
"""

import os
import sys
import numpy as np
import pandas as pd
import vectorbt as vbt

sys.path.insert(0, '/root/AlgrokQuant')
from jev.screener import JevScreener

DATA_PATH = "/root/AlgrokQuant/data/parquet_cache/BTC_USDT_1h_2021_2026.parquet"
FEE_RATE = 0.0005        # 5 bps taker fee
SLIPPAGE_RATE = 0.0002   # 2 bps slippage

print("=" * 80)
print("VALIDACIÓN RIGUROSA INSTITUCIONAL: STRAT-FAST-035 (BTC/USDC 1h)")
print("1. Walk-Forward Analysis (IS: 2021-2024 vs OOS: 2024-2026)")
print("2. Test de Estrés Monte Carlo (1.000 iteraciones + Shock de Slippage 3x)")
print("=" * 80)

# 1. Cargar datos
df = pd.read_parquet(DATA_PATH)
if not isinstance(df.index, pd.DatetimeIndex):
    df.index = pd.to_datetime(df.index, utc=True)
df.sort_index(inplace=True)

close = df["close"].values.astype(float)
high = df["high"].values.astype(float)
low = df["low"].values.astype(float)
open_ = df["open"].values.astype(float)
volume = df["volume"].values.astype(float)
n = len(close)

# 2. Indicadores
log_ret = np.zeros(n)
log_ret[1:] = np.log(close[1:] / close[:-1])

window_ent = 48
bins = 10
max_ent = np.log2(bins)
h_norm = np.zeros(n)
for i in range(window_ent, n):
    w = log_ret[i - window_ent + 1 : i + 1]
    counts, _ = np.histogram(w, bins=bins)
    probs = counts / float(window_ent)
    probs = probs[probs > 0]
    h_norm[i] = -np.sum(probs * np.log2(probs)) / max_ent

s_close = pd.Series(close)
ema50 = s_close.ewm(span=50, adjust=False).mean().values
ema200 = s_close.ewm(span=200, adjust=False).mean().values
ema200_slope = np.zeros(n)
ema200_slope[5:] = (ema200[5:] - ema200[:-5]) / ema200[:-5]

tr = np.maximum(high - low, np.maximum(np.abs(high - np.roll(close, 1)), np.abs(low - np.roll(close, 1))))
tr[0] = high[0] - low[0]
atr14 = pd.Series(tr).ewm(alpha=1.0 / 14, adjust=False).mean().values

mfm = ((close - low) - (high - close)) / (high - low + 1e-9)
mfv = mfm * volume
sum_mfv = pd.Series(mfv).rolling(20).sum().values
sum_vol = pd.Series(volume).rolling(20).sum().values
cmf20 = sum_mfv / (sum_vol + 1e-9)

vol_ma24 = pd.Series(volume).rolling(24).mean().values
rvol24 = volume / (vol_ma24 + 1e-9)
body_ratio = np.abs(close - open_) / (high - low + 1e-9)

# Donchian 30
hh30 = pd.Series(high).rolling(30).max().shift(1).values

# Señales de entrada Long
long_entries = (
    (h_norm < 0.72) &
    (ema50 > ema200) &
    (close > ema50) &
    (ema200_slope > 0) &
    (cmf20 > 0.05) &
    (rvol24 >= 1.20) &
    (close > open_) &
    (body_ratio >= 0.50) &
    (close > hh30)
)
entries = np.roll(long_entries, 1)
entries[0] = False

# Stops: SL 2.0x ATR, TP 4.0x ATR
sl_stop = float(np.nanmedian((2.0 * atr14) / close))
tp_stop = float(np.nanmedian((4.0 * atr14) / close))

# ==============================================================================
# FASE 1: WALK-FORWARD ANALYSIS (In-Sample vs Out-of-Sample)
# ==============================================================================
# División temporal:
# IS: 2021-10-01 a 2024-09-30 (3 años / 36 meses)
# OOS: 2024-10-01 a 2026-10-21 (2 años / 24 meses)
split_date = pd.Timestamp("2024-10-01", tz="UTC")
is_mask = df.index < split_date
oos_mask = df.index >= split_date

print(f"\nDivisión Walk-Forward:")
print(f"  • In-Sample (IS):     {df.index[0].strftime('%Y-%m-%d')} a {split_date.strftime('%Y-%m-%d')} ({is_mask.sum()} horas)")
print(f"  • Out-of-Sample (OOS): {split_date.strftime('%Y-%m-%d')} a {df.index[-1].strftime('%Y-%m-%d')} ({oos_mask.sum()} horas)")

# Simulación In-Sample
pf_is = vbt.Portfolio.from_signals(
    close=pd.Series(close[is_mask], index=df.index[is_mask]),
    entries=entries[is_mask],
    sl_stop=sl_stop,
    tp_stop=tp_stop,
    init_cash=1000.0,
    fees=FEE_RATE + SLIPPAGE_RATE,
    freq='1h'
)
ret_is = float(pf_is.total_return() * 100.0)
dd_is = float(pf_is.max_drawdown() * 100.0)
pf_is_val = float(pf_is.trades.profit_factor())
trades_is = int(pf_is.trades.count())
wr_is = float(pf_is.trades.win_rate() * 100.0)

# Simulación Out-of-Sample
pf_oos = vbt.Portfolio.from_signals(
    close=pd.Series(close[oos_mask], index=df.index[oos_mask]),
    entries=entries[oos_mask],
    sl_stop=sl_stop,
    tp_stop=tp_stop,
    init_cash=1000.0,
    fees=FEE_RATE + SLIPPAGE_RATE,
    freq='1h'
)
ret_oos = float(pf_oos.total_return() * 100.0)
dd_oos = float(pf_oos.max_drawdown() * 100.0)
pf_oos_val = float(pf_oos.trades.profit_factor())
trades_oos = int(pf_oos.trades.count())
wr_oos = float(pf_oos.trades.win_rate() * 100.0)

screener = JevScreener()
oos_eval = screener.calculate_oos_r_dd_ratio(is_return=ret_is, is_max_dd=dd_is, oos_return=ret_oos, oos_max_dd=dd_oos)

print("\n" + "-" * 70)
print("RESULTADOS WALK-FORWARD:")
print(f"  • In-Sample (IS 3A):    Retorno: {ret_is:+6.2f}% | Max DD: {dd_is:5.2f}% | PF: {pf_is_val:4.2f} | WR: {wr_is:4.1f}% | Trades: {trades_is}")
print(f"  • Out-of-Sample (OOS 2A): Retorno: {ret_oos:+6.2f}% | Max DD: {dd_oos:5.2f}% | PF: {pf_oos_val:4.2f} | WR: {wr_oos:4.1f}% | Trades: {trades_oos}")
print(f"  • Ratio R/DD In-Sample:     {oos_eval['is_r_dd']:.2f}")
print(f"  • Ratio R/DD Out-of-Sample: {oos_eval['oos_r_dd']:.2f}")
print(f"  • Degradación OOS:          {oos_eval['degradation_pct']:+.1f}% (Límite máximo permitido: -40.0%)")
print(f"  • Veredicto Walk-Forward:   {'✅ APROBADO OOS (Sin Sobreajuste)' if oos_eval['pass_filter'] else '❌ RECHAZADO'}")
print("-" * 70)

# ==============================================================================
# FASE 2: TEST DE ESTRÉS MONTE CARLO (Simulación de Resampling & Shock de Fricción)
# ==============================================================================
print("\nEjecutando Test de Estrés Monte Carlo (1.000 caminos simulados)...")

# Portfolio completo 5 años
pf_full = vbt.Portfolio.from_signals(
    close=pd.Series(close, index=df.index),
    entries=entries,
    sl_stop=sl_stop,
    tp_stop=tp_stop,
    init_cash=1000.0,
    fees=FEE_RATE + SLIPPAGE_RATE,
    freq='1h'
)

trade_returns = pf_full.trades.records_readable['Return'].values
num_trades = len(trade_returns)
print(f"Universo total de operaciones para remuestreo: {num_trades} trades")

np.random.seed(42)
simulations = 1000
mc_final_returns = []
mc_max_drawdowns = []

# Shock de fricción: agregar 4 bps de slippage adverso extra a cada trade
extra_slippage_drag = 0.0004

for s in range(simulations):
    # Remuestreo con reemplazo (Bootstrapping)
    sampled_returns = np.random.choice(trade_returns, size=num_trades, replace=True) - extra_slippage_drag
    equity_curve = np.cumprod(1 + sampled_returns)
    peak = np.maximum.accumulate(equity_curve)
    dd_curve = (equity_curve - peak) / peak
    
    mc_final_returns.append((equity_curve[-1] - 1.0) * 100.0)
    mc_max_drawdowns.append(abs(np.min(dd_curve)) * 100.0)

mc_final_returns = np.array(mc_final_returns)
mc_max_drawdowns = np.array(mc_max_drawdowns)

p95_dd = np.percentile(mc_max_drawdowns, 95)
p99_dd = np.percentile(mc_max_drawdowns, 99)
median_ret = np.median(mc_final_returns)
prob_ruin = np.mean(mc_max_drawdowns > 20.0) * 100.0

print("-" * 70)
print("RESULTADOS TEST DE ESTRÉS MONTE CARLO:")
print(f"  • Retorno Mediano Simulado (con Fricción 3x): {median_ret:+6.2f}%")
print(f"  • Drawdown Máximo Esperado (Percentil 95):    {p95_dd:5.2f}% (Techo Gobernanza: 20.0%)")
print(f"  • Drawdown Máximo Extremo  (Percentil 99):    {p99_dd:5.2f}%")
print(f"  • Probabilidad de Ruina (DD > 20.0%):        {prob_ruin:4.2f}%")
print(f"  • Veredicto Monte Carlo:                     {'✅ ROBUSTEZ APROBADA' if p95_dd <= 20.0 else '❌ EXCESO DE RIESGO'}")
print("=" * 80)

# Resumen Final de Aprobación
passes_all = oos_eval['pass_filter'] and p95_dd <= 20.0
print(f"\nDICTAMEN FINAL COMITÉ DE AUDITORÍA: {'🏆 ESTRATEGIA STRAT-035 APROBADA PARA CATÁLOGO Y FORWARD TEST' if passes_all else 'RECHAZADA'}")
