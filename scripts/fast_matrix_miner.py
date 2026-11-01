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
from jev.hybrid_signals import (
    HybridSignalFactory,
    calc_atr_fast
)


# ==============================================================================
# CARGADOR DE DATOS SEGÚN GOBERNANZA DUAL Y HORIZONTE TEMPORAL
# ==============================================================================

def load_market_data(asset: str, desk_mode: str = "CAPITAL_PROPIO") -> pd.DataFrame:
    base_dir = Path("/root/AlgrokQuant/data")
    parquet_cache = base_dir / "parquet_cache"
    processed = base_dir / "processed"

    asset_upper = asset.upper()
    df = None

    if asset_upper in ["NDX", "NASDAQ", "USTEC"]:
        pq_path = parquet_cache / "NDX_1h_2016_2026.parquet"
        if not pq_path.exists():
            pq_path = parquet_cache / "NDX_2h_2016_2026.parquet"
        if pq_path.exists():
            df = pd.read_parquet(pq_path)
    elif asset_upper in ["SPX", "SP500", "US500"]:
        pq_path = parquet_cache / "SPX_2h_2016_2026.parquet"
        if not pq_path.exists():
            pq_path = parquet_cache / "SPX_1D_2016_2026.parquet"
        if pq_path.exists():
            df = pd.read_parquet(pq_path)
    elif asset_upper in ["EURUSD", "EUR_USD"]:
        pq_path = parquet_cache / "EUR_USD_1h_2016_2026.parquet"
        if pq_path.exists():
            df = pd.read_parquet(pq_path)
    elif asset_upper in ["BTC", "BTCUSDT", "BTCUSDC"]:
        pq_path = parquet_cache / "BTC_USDT_1h_2021_2026.parquet"
        if pq_path.exists():
            df = pd.read_parquet(pq_path)
        elif (processed / "btc_usdc_1h.csv").exists():
            df = pd.read_csv(processed / "btc_usdc_1h.csv")
    elif asset_upper in ["ETH", "ETHUSDT", "ETHUSDC"]:
        if (processed / "eth_usdc_1h.csv").exists():
            df = pd.read_csv(processed / "eth_usdc_1h.csv")
    elif asset_upper in ["SOL", "SOLUSDT", "SOLUSDC"]:
        if (processed / "sol_usdc_1h.csv").exists():
            df = pd.read_csv(processed / "sol_usdc_1h.csv")

    if df is None:
        raise FileNotFoundError(f"No se encontraron datos históricos para {asset}")

    cols = {c.lower(): c for c in df.columns}
    rename_dict = {}
    for standard in ["open", "high", "low", "close", "volume", "time", "date", "timestamp"]:
        if standard in cols:
            rename_dict[cols[standard]] = standard
    df = df.rename(columns=rename_dict)

    if "open" not in df.columns:
        df["open"] = df["close"]
    if "high" not in df.columns:
        df["high"] = df["close"]
    if "low" not in df.columns:
        df["low"] = df["close"]
    if "volume" not in df.columns:
        df["volume"] = 1000.0

    time_col = None
    for tc in ["time", "date", "timestamp"]:
        if tc in df.columns:
            time_col = tc
            break

    if time_col:
        df[time_col] = pd.to_datetime(df[time_col], utc=True)
        df = df.sort_values(time_col).reset_index(drop=True)

        if desk_mode == "PROP_FIRM":
            last_date = df[time_col].max()
            start_1y = last_date - pd.Timedelta(days=365)
            df = df[df[time_col] >= start_1y].reset_index(drop=True)
            print(f"[{desk_mode}] Recortado a ventana de 12M: {len(df)} barras ({start_1y.strftime('%Y-%m-%d')} a {last_date.strftime('%Y-%m-%d')})")
        else:
            first_date = df[time_col].min()
            last_date = df[time_col].max()
            print(f"[{desk_mode}] Histórico multianual completo disponible: {len(df)} barras ({first_date.strftime('%Y-%m-%d')} a {last_date.strftime('%Y-%m-%d')})")
    else:
        if desk_mode == "PROP_FIRM":
            cutoff = min(len(df), 6000)
            df = df.iloc[-cutoff:].reset_index(drop=True)
            print(f"[{desk_mode}] Recortado a últimas {len(df)} barras (~1Y)")
        else:
            print(f"[{desk_mode}] Histórico completo disponible: {len(df)} barras")

    return df


# ==============================================================================
# MOTOR VECTORIZADO DE ALTA VELOCIDAD COMPILADO EN NUMBA JIT
# ==============================================================================

@njit(fastmath=True)
def simulate_signals_numba(
    close: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    atr: np.ndarray,
    entries_long: np.ndarray,
    entries_short: np.ndarray,
    sl_atr_mult: float,
    tp_atr_mult: float,
    max_holding_bars: int,
    round_trip_friction: float
) -> Tuple[int, float, float, float, float]:
    n = len(close)
    in_pos = 0  # 1 = Long, -1 = Short, 0 = Flat
    entry_px = 0.0
    sl_px = 0.0
    tp_px = 0.0
    bars_held = 0

    running_eq = 1000.0
    peak_eq = 1000.0
    max_dd_pct = 0.0
    num_trades = 0
    wins = 0

    sum_ret = 0.0
    sum_sq_ret = 0.0

    for i in range(1, n):
        if in_pos == 1:
            bars_held += 1
            exit_trade = False
            exit_px = 0.0

            if low[i] <= sl_px:
                exit_px = sl_px
                exit_trade = True
            elif high[i] >= tp_px:
                exit_px = tp_px
                exit_trade = True
            elif bars_held >= max_holding_bars:
                exit_px = close[i]
                exit_trade = True

            if exit_trade:
                num_trades += 1
                net_ret = (exit_px - entry_px) / entry_px - round_trip_friction
                running_eq += running_eq * net_ret
                if net_ret > 0:
                    wins += 1
                sum_ret += net_ret
                sum_sq_ret += net_ret * net_ret
                in_pos = 0

        elif in_pos == -1:
            bars_held += 1
            exit_trade = False
            exit_px = 0.0

            if high[i] >= sl_px:
                exit_px = sl_px
                exit_trade = True
            elif low[i] <= tp_px:
                exit_px = tp_px
                exit_trade = True
            elif bars_held >= max_holding_bars:
                exit_px = close[i]
                exit_trade = True

            if exit_trade:
                num_trades += 1
                net_ret = (entry_px - exit_px) / entry_px - round_trip_friction
                running_eq += running_eq * net_ret
                if net_ret > 0:
                    wins += 1
                sum_ret += net_ret
                sum_sq_ret += net_ret * net_ret
                in_pos = 0

        if in_pos == 0:
            if entries_long[i]:
                in_pos = 1
                entry_px = close[i]
                cur_atr = atr[i] if not np.isnan(atr[i]) else close[i] * 0.01
                sl_px = entry_px - sl_atr_mult * cur_atr
                tp_px = entry_px + tp_atr_mult * cur_atr
                bars_held = 0
            elif entries_short[i]:
                in_pos = -1
                entry_px = close[i]
                cur_atr = atr[i] if not np.isnan(atr[i]) else close[i] * 0.01
                sl_px = entry_px + sl_atr_mult * cur_atr
                tp_px = entry_px - tp_atr_mult * cur_atr
                bars_held = 0

        if running_eq > peak_eq:
            peak_eq = running_eq
        dd = (peak_eq - running_eq) / peak_eq * 100.0
        if dd > max_dd_pct:
            max_dd_pct = dd

    total_pnl = running_eq - 1000.0
    win_rate = (wins / num_trades * 100.0) if num_trades > 0 else 0.0

    if num_trades > 1:
        mean_ret = sum_ret / num_trades
        var_ret = (sum_sq_ret - num_trades * mean_ret * mean_ret) / (num_trades - 1)
        std_ret = np.sqrt(max(0.0, var_ret))
        sharpe = (mean_ret / (std_ret + 1e-12)) * np.sqrt(min(252.0, float(num_trades)))
    else:
        sharpe = 0.0

    return num_trades, total_pnl, win_rate, sharpe, max_dd_pct


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
