#!/usr/bin/env python3
"""
Explorador de Mesetas Paramétricas (Parameter Plateau Grid) para STRAT-FAST-035 (BTC 1h)
AlgrokQuant · Desk Lead Nexus
Evalúa sobre el ciclo multianual de 5 años (2021-2026 Parquet) con fricciones reales (14 bps).
"""

import os
import sys
import itertools
import numpy as np
import pandas as pd
import vectorbt as vbt

# Importar Screener para validación
sys.path.insert(0, '/root/AlgrokQuant')
from jev.screener import JevScreener

DATA_PATH = "/root/AlgrokQuant/data/parquet_cache/BTC_USDT_1h_2021_2026.parquet"
FEE_RATE = 0.0005        # 5 bps taker fee
SLIPPAGE_RATE = 0.0002   # 2 bps slippage
COST_ROUND_TRIP = (FEE_RATE + SLIPPAGE_RATE) * 2.0

print("=" * 80)
print("EXPLORACIÓN MASIVA DE MESETAS PARAMÉTRICAS: STRAT-FAST-035 (BTC 1h)")
print("Ciclo Multianual de 5 Años (2021-2026) · Datos Parquet")
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

print(f"Datos cargados: {n} velas ({df.index[0]} a {df.index[-1]})")

# 2. Precomputar indicadores fijos (Vectorizado rápido)
log_ret = np.zeros(n)
log_ret[1:] = np.log(close[1:] / close[:-1])

# Entropía de Shannon (48 barras, 10 bins)
print("Precomputando Entropía de Shannon (48h)...")
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

# EMAs
s_close = pd.Series(close)
ema50 = s_close.ewm(span=50, adjust=False).mean().values
ema200 = s_close.ewm(span=200, adjust=False).mean().values
ema200_slope = np.zeros(n)
ema200_slope[5:] = (ema200[5:] - ema200[:-5]) / ema200[:-5]

# ATR(14)
tr = np.maximum(high - low, np.maximum(np.abs(high - np.roll(close, 1)), np.abs(low - np.roll(close, 1))))
tr[0] = high[0] - low[0]
atr14 = pd.Series(tr).ewm(alpha=1.0 / 14, adjust=False).mean().values

# CMF(20)
mfm = ((close - low) - (high - close)) / (high - low + 1e-9)
mfv = mfm * volume
sum_mfv = pd.Series(mfv).rolling(20).sum().values
sum_vol = pd.Series(volume).rolling(20).sum().values
cmf20 = sum_mfv / (sum_vol + 1e-9)

# RVOL(24)
vol_ma24 = pd.Series(volume).rolling(24).mean().values
rvol24 = volume / (vol_ma24 + 1e-9)

body_ratio = np.abs(close - open_) / (high - low + 1e-9)

# 3. Grid de Parámetros
# Parámetros a explorar:
# - Donchian Window: [20, 30, 48, 72]
# - H_norm Max: [0.72, 0.78, 0.84]
# - Modo: ['LONG_ONLY', 'LONG_SHORT']
# - SL ATR: [1.2, 1.8, 2.5]
# - TP ATR: [2.0, 3.5, 5.0, 0.0 (trailing)]

donchian_windows = [20, 30, 48, 72]
h_thresholds = [0.72, 0.78, 0.84]
modes = ['LONG_ONLY', 'LONG_SHORT']
sl_mults = [1.5, 2.0, 2.5]
tp_mults = [2.5, 4.0, 6.0]

param_combos = list(itertools.product(donchian_windows, h_thresholds, modes, sl_mults, tp_mults))
print(f"Total de combinaciones en el grid: {len(param_combos)}")

screener = JevScreener(max_capital_propio_dd=20.0, min_profit_factor=1.30)
results = []

# Precomputar Donchian Highs y Lows
hh_dict = {}
ll_dict = {}
for w in donchian_windows:
    hh_dict[w] = pd.Series(high).rolling(w).max().shift(1).values
    ll_dict[w] = pd.Series(low).rolling(w).min().shift(1).values

print("Ejecutando simulaciones VectorBT vectorizadas...")

for idx, (dw, h_thresh, mode, sl_m, tp_m) in enumerate(param_combos):
    hh = hh_dict[dw]
    ll = ll_dict[dw]

    # Condición Long
    long_entries = (
        (h_norm < h_thresh) &
        (ema50 > ema200) &
        (close > ema50) &
        (ema200_slope > 0) &
        (cmf20 > 0.05) &
        (rvol24 >= 1.20) &
        (close > open_) &
        (body_ratio >= 0.50) &
        (close > hh)
    )

    if mode == 'LONG_SHORT':
        short_entries = (
            (h_norm < h_thresh) &
            (ema50 < ema200) &
            (close < ema50) &
            (ema200_slope < 0) &
            (cmf20 < -0.05) &
            (rvol24 >= 1.30) &
            (close < open_) &
            (body_ratio >= 0.50) &
            (close < ll)
        )
    else:
        short_entries = np.zeros(n, dtype=bool)

    # Causalidad t -> entrada t+1
    entries = np.roll(long_entries, 1)
    entries[0] = False
    short_en = np.roll(short_entries, 1)
    short_en[0] = False

    # Backtest con VectorBT
    # Calculamos stops basados en ATR promedio
    sl_stop = (sl_m * atr14) / close
    tp_stop = (tp_m * atr14) / close
    avg_sl = float(np.nanmedian(sl_stop))
    avg_tp = float(np.nanmedian(tp_stop))

    try:
        pf = vbt.Portfolio.from_signals(
            close=pd.Series(close, index=df.index),
            entries=entries,
            short_entries=short_en,
            sl_stop=avg_sl,
            tp_stop=avg_tp,
            init_cash=1000.0,
            fees=FEE_RATE + SLIPPAGE_RATE,
            freq='1h'
        )

        tot_return = float(pf.total_return() * 100.0)
        max_dd = float(pf.max_drawdown() * 100.0)
        trades_count = int(pf.trades.count())
        win_rate = float(pf.trades.win_rate() * 100.0) if trades_count > 0 else 0.0
        profit_factor = float(pf.trades.profit_factor()) if trades_count > 0 else 0.0
        calmar = tot_return / max(0.01, max_dd)

        # Stagnation days
        eq_curve = pf.value()
        stag_days = screener.calculate_stagnation_days(eq_curve, dates=pd.Series(eq_curve.index))

        results.append({
            "combo_id": f"D{dw}_H{int(h_thresh*100)}_{mode[:4]}_SL{sl_m}_TP{tp_m}",
            "dw": dw,
            "h_thresh": h_thresh,
            "mode": mode,
            "sl_mult": sl_m,
            "tp_mult": tp_m,
            "tot_return_pct": round(tot_return, 2),
            "ann_cagr_pct": round(((1.0 + tot_return/100.0)**(1.0/5.0) - 1.0)*100.0, 2) if tot_return > -100 else -100,
            "max_dd_pct": round(max_dd, 2),
            "calmar": round(calmar, 2),
            "profit_factor": round(profit_factor, 2),
            "win_rate_pct": round(win_rate, 1),
            "trades": trades_count,
            "stagnation_days": stag_days,
            "passes_governance": max_dd <= 20.0 and profit_factor >= 1.30 and trades_count >= 30 and tot_return > 0
        })
    except Exception as e:
        continue

df_res = pd.DataFrame(results)
print(f"\nSimulaciones completadas: {len(df_res)}")

# Ordenar por Calmar Ratio
df_sorted = df_res.sort_values(by="calmar", ascending=False)

print("\n" + "=" * 95)
print("TOP 10 COMBINACIONES EN EL GRID (Ordenadas por Calmar Ratio):")
print("=" * 95)
print(f"{'Combo ID':<26} | {'Modo':<10} | {'Retorno 5A':<11} | {'CAGR/A':<8} | {'Max DD':<8} | {'Calmar':<7} | {'PF':<5} | {'WR%':<6} | {'Trades':<6} | {'Stag':<5} | {'Gobernanza'}")
print("-" * 115)

for _, r in df_sorted.head(10).iterrows():
    gov_badge = "✅ APROBADA" if r['passes_governance'] else "❌ RECHAZADA"
    print(f"{r['combo_id']:<26} | {r['mode']:<10} | {r['tot_return_pct']:+10.2f}% | {r['ann_cagr_pct']:+7.2f}% | {r['max_dd_pct']:7.2f}% | {r['calmar']:7.2f} | {r['profit_factor']:5.2f} | {r['win_rate_pct']:5.1f}% | {r['trades']:6d} | {r['stagnation_days']:4d}d | {gov_badge}")

# Análisis de Meseta (Robustness Plateau)
print("\n" + "=" * 95)
print("ANÁLISIS DE SENSIBILIDAD POR FACTOR (Evaluación de Meseta):")
print("=" * 95)

# 1. Long Only vs Long Short
print("\n1. Impacto del Modo Operativo:")
print(df_res.groupby('mode')[['tot_return_pct', 'max_dd_pct', 'profit_factor', 'calmar']].mean().round(2))

# 2. Ventana Donchian
print("\n2. Sensibilidad a la Ventana Donchian:")
print(df_res.groupby('dw')[['tot_return_pct', 'max_dd_pct', 'profit_factor', 'calmar']].mean().round(2))

# 3. Umbral de Entropía
print("\n3. Sensibilidad al Umbral de Entropía de Shannon:")
print(df_res.groupby('h_thresh')[['tot_return_pct', 'max_dd_pct', 'profit_factor', 'calmar']].mean().round(2))

# Guardar resultados consolidados
output_csv = "/root/AlgrokQuant/reports/strat_035_plateau_exploration.csv"
df_sorted.to_csv(output_csv, index=False)
print(f"\nResultados completos exportados a: {output_csv}")
