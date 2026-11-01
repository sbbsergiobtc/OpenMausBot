#!/usr/bin/env python3
"""
Motor de Minado Matricial Masivo de Alfas Híbridos (Fase 2 - Numba Accelerated)
AlgrokQuant · Jev Quantitative Engine

Simulación vectorizada y compilada en Numba JIT (< 0.1 ms por backtest multianual).
Soporta Gobernanza Dual:
- CAPITAL_PROPIO: Todo el histórico multianual disponible (10 años 2016-2026 en Índices/Forex, histórico completo en Cripto).
- PROP_FIRM: Ventana del último año (12M reciente), EOD DD <= 3.0%, regla de consistencia 40%.
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
from numba import njit

sys.path.insert(0, '/root/AlgrokQuant')
base_dir = Path(__file__).resolve().parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from jev.hybrid_signals import (
    HybridSignalFactory,
    calc_atr_fast
)
from jev.simulator import (
    load_market_data,
    simulate_signals_numba
)


# ==============================================================================
# BARRIDO MATRICIAL POR LOTES
# ==============================================================================

def run_matrix_miner(
    asset: str = "NDX",
    desk_mode: str = "CAPITAL_PROPIO",
    max_candidates: int = 50000,
    top_n: int = 20
) -> List[Dict[str, Any]]:
    print(f"\n{'='*75}")
    print(f"ALGROKQUANT FAST MATRIX MINER · {asset} [{desk_mode}]")
    print(f"{'='*75}")

    df = load_market_data(asset, desk_mode=desk_mode)
    close = np.ascontiguousarray(df["close"].values, dtype=np.float64)
    high = np.ascontiguousarray(df["high"].values, dtype=np.float64)
    low = np.ascontiguousarray(df["low"].values, dtype=np.float64)
    open_p = np.ascontiguousarray(df["open"].values, dtype=np.float64)
    volume = np.ascontiguousarray(df["volume"].values, dtype=np.float64)
    atr = calc_atr_fast(high, low, close, 14)

    asset_u = asset.upper()
    if any(k in asset_u for k in ["BTC", "ETH", "SOL"]):
        friction = 0.0014  # 14 bps round-trip
    elif any(k in asset_u for k in ["NDX", "SPX", "US500", "USTEC"]):
        friction = 0.0006  # 6 bps round-trip
    else:
        friction = 0.0002  # ~1 pip FX

    t0 = time.perf_counter()
    factory = HybridSignalFactory(open_p, high, low, close, volume)
    t_pre = (time.perf_counter() - t0) * 1000.0
    print(f"Features precomputados en {t_pre:.2f} ms ({len(close)} barras)")

    dummy_mask = np.zeros(len(close), dtype=np.bool_)
    dummy_mask[10] = True
    _ = simulate_signals_numba(close, high, low, atr, dummy_mask, dummy_mask, 2.0, 3.0, 48, friction)

    macro_anchors = ["BOLLINGER_REVERSION", "DONCHIAN_BREAKOUT", "VWAP_VALUE_DISCOUNT", "EMA_TREND_PULLBACK"]
    entropy_thresholds = [0.72, 0.75, 0.78, 0.82]
    symbolic_triggers = ["VOL_CORR_ABSORPTION", "MACD_ACCELERATION", "OFI_PRESSURE", "LINEAR_DECAY_EXTREME"]
    param1_list = [14, 20, 30, 48]
    param2_list = [1.5, 2.0, 2.5]
    trigger_thresholds = [0.70, 0.75, 0.80, 0.85]
    sl_atr_mults = [1.5, 2.0, 2.5]
    tp_atr_mults = [2.0, 3.0, 4.0]

    max_dd_limit = 3.0 if desk_mode == "PROP_FIRM" else 20.0
    min_trades = 35 if desk_mode == "PROP_FIRM" else 50
    min_sharpe = 1.20

    candidates_evaluated = 0
    survivors = []

    print("Iniciando barrido combinatorio ultrarrápido...")
    t_start = time.perf_counter()

    for macro in macro_anchors:
        for ent in entropy_thresholds:
            for trig in symbolic_triggers:
                for p1 in param1_list:
                    for p2 in param2_list:
                        for tr_th in trigger_thresholds:
                            l_mask, s_mask = factory.generate_signal(
                                macro_anchor=macro,
                                entropy_max=ent,
                                symbolic_trigger=trig,
                                param1=p1,
                                param2=p2,
                                trigger_threshold=tr_th
                            )

                            if not np.any(l_mask) and not np.any(s_mask):
                                candidates_evaluated += len(sl_atr_mults) * len(tp_atr_mults)
                                continue

                            for sl_m in sl_atr_mults:
                                for tp_m in tp_atr_mults:
                                    candidates_evaluated += 1

                                    num_trades, total_pnl, win_rate, sharpe, max_dd = simulate_signals_numba(
                                        close, high, low, atr, l_mask, s_mask,
                                        float(sl_m), float(tp_m), 48, friction
                                    )

                                    if num_trades < min_trades:
                                        continue
                                    if total_pnl <= 0.0:
                                        continue
                                    if max_dd > max_dd_limit:
                                        continue
                                    if sharpe < min_sharpe:
                                        continue

                                    ret_pct = total_pnl / 1000.0 * 100.0
                                    model_id = f"HYB-{asset}-{macro[:3]}-{trig[:4]}-{p1}-{sl_m}-{tp_m}"
                                    survivors.append({
                                        "candidate_id": model_id,
                                        "asset": asset,
                                        "desk_mode": desk_mode,
                                        "macro_anchor": macro,
                                        "entropy_max": ent,
                                        "symbolic_trigger": trig,
                                        "param1": p1,
                                        "param2": p2,
                                        "trigger_threshold": tr_th,
                                        "sl_atr_mult": sl_m,
                                        "tp_atr_mult": tp_m,
                                        "trades": int(num_trades),
                                        "pnl": round(float(total_pnl), 2),
                                        "return_pct": round(float(ret_pct), 2),
                                        "win_rate": round(float(win_rate), 2),
                                        "sharpe": round(float(sharpe), 2),
                                        "max_dd": round(float(max_dd), 2)
                                    })

                                    if candidates_evaluated >= max_candidates:
                                        break
                                if candidates_evaluated >= max_candidates:
                                    break
                            if candidates_evaluated >= max_candidates:
                                break
                        if candidates_evaluated >= max_candidates:
                            break
                    if candidates_evaluated >= max_candidates:
                        break
                if candidates_evaluated >= max_candidates:
                    break
            if candidates_evaluated >= max_candidates:
                break
        if candidates_evaluated >= max_candidates:
            break

    elapsed_s = time.perf_counter() - t_start
    rate = candidates_evaluated / elapsed_s if elapsed_s > 0 else 0
    print(f"Evaluadas {candidates_evaluated} combinaciones en {elapsed_s:.2f} segundos ({rate:.0f} comb/seg)")
    print(f"Supervivientes que superan Fast-Kill: {len(survivors)}")

    survivors.sort(key=lambda x: (x["sharpe"], x["return_pct"]), reverse=True)
    top_candidates = survivors[:top_n]

    out_dir = Path("/root/AlgrokQuant/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"fast_matrix_{asset}_{desk_mode.lower()}_top.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "asset": asset,
            "desk_mode": desk_mode,
            "total_evaluated": candidates_evaluated,
            "survivors_count": len(survivors),
            "execution_time_sec": round(elapsed_s, 2),
            "top_candidates": top_candidates
        }, f, indent=2)

    print(f"Guardados {len(top_candidates)} finalistas en: {out_file}")

    print(f"\n--- TOP 5 FINALISTAS PARA AUDITORÍA ({asset} · {desk_mode}) ---")
    for idx, c in enumerate(top_candidates[:5]):
        print(f"#{idx+1} {c['candidate_id']} | Trades: {c['trades']} | Return: +{c['return_pct']}% | Sharpe: {c['sharpe']} | Max DD: {c['max_dd']}%")

    return top_candidates


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AlgrokQuant Fast Matrix Miner")
    parser.add_argument("--asset", type=str, default="NDX", help="Activo (NDX, SPX, EURUSD, BTC, ETH, SOL)")
    parser.add_argument("--mode", type=str, default="CAPITAL_PROPIO", choices=["CAPITAL_PROPIO", "PROP_FIRM"], help="Gobernanza dual")
    parser.add_argument("--max", type=int, default=50000, help="Límite de combinaciones a evaluar")
    args = parser.parse_args()

    run_matrix_miner(asset=args.asset, desk_mode=args.mode, max_candidates=args.max)
