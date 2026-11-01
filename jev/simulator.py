"""
Motor Vectorizado de Simulación y Carga de Datos Históricos
AlgrokQuant · Jev Quantitative Engine

Contiene los métodos deterministas de ejecución ultrarrápida compilados en Numba:
- load_market_data: Carga y recorta según Gobernanza Dual (10Y Capital Propio vs 1Y Prop Firm).
- simulate_signals_numba: Simulación JIT compilada (< 0.1 ms por ciclo de 75.000 barras).
- extract_candidate_trade_pnls: Reconstrucción de retornos trade a trade para DSR y Monte Carlo.
"""

import sys
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import numpy as np
import pandas as pd
from numba import njit

from .hybrid_signals import HybridSignalFactory, calc_atr_fast


# ==============================================================================
# CARGADOR DE DATOS SEGÚN GOBERNANZA DUAL Y HORIZONTE TEMPORAL
# ==============================================================================

def load_market_data(asset: str, desk_mode: str = "CAPITAL_PROPIO") -> pd.DataFrame:
    """
    Carga datos de mercado respetando la Gobernanza Dual:
    - CAPITAL_PROPIO: Histórico completo disponible multianual (10 años 2016-2026 en Índices CME / Forex).
    - PROP_FIRM: Ventana recortada estrictamente al último año (12M reciente).
    """
    if Path("/root/AlgrokQuant").exists():
        base_dir = Path("/root/AlgrokQuant/data")
    else:
        base_dir = Path(__file__).resolve().parent.parent / "data"

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

    if isinstance(df.index, pd.DatetimeIndex):
        df["time"] = df.index
        df = df.reset_index(drop=True)

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
    round_trip_friction: float,
    risk_per_trade_pct: float = 0.01,
    trailing_trigger_atr: float = 1.2,
    trailing_dist_atr: float = 0.8
) -> Tuple[int, float, float, float, float]:
    n = len(close)
    in_pos = 0  # 1 = Long, -1 = Short, 0 = Flat
    entry_px = 0.0
    sl_px = 0.0
    tp_px = 0.0
    bars_held = 0
    pos_units = 0.0
    highest_p = 0.0
    lowest_p = 0.0

    running_eq = 1000.0
    peak_eq = 1000.0
    max_dd_pct = 0.0
    num_trades = 0
    wins = 0

    sum_ret = 0.0
    sum_sq_ret = 0.0

    for i in range(1, n):
        cur_atr = atr[i] if not np.isnan(atr[i]) and atr[i] > 0 else close[i] * 0.01

        if in_pos == 1:
            bars_held += 1
            if high[i] > highest_p:
                highest_p = high[i]

            # GESTIÓN DINÁMICA: Break-Even y Trailing ATR
            gain = highest_p - entry_px
            if gain >= 1.0 * cur_atr:
                be_level = entry_px + 0.1 * cur_atr
                if sl_px < be_level:
                    sl_px = be_level

            if trailing_trigger_atr > 0.0 and gain >= trailing_trigger_atr * cur_atr:
                trail_level = highest_p - trailing_dist_atr * cur_atr
                if trail_level > sl_px:
                    sl_px = trail_level

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
                gross_pnl = (exit_px - entry_px) * pos_units
                notional = entry_px * pos_units
                comm = notional * round_trip_friction
                trade_pnl = gross_pnl - comm
                trade_ret = trade_pnl / running_eq
                running_eq += trade_pnl

                if trade_pnl > 0.0:
                    wins += 1
                sum_ret += trade_ret
                sum_sq_ret += trade_ret * trade_ret
                in_pos = 0
                pos_units = 0.0

        elif in_pos == -1:
            bars_held += 1
            if low[i] < lowest_p:
                lowest_p = low[i]

            drop = entry_px - lowest_p
            if drop >= 1.0 * cur_atr:
                be_level = entry_px - 0.1 * cur_atr
                if sl_px > be_level:
                    sl_px = be_level

            if trailing_trigger_atr > 0.0 and drop >= trailing_trigger_atr * cur_atr:
                trail_level = lowest_p + trailing_dist_atr * cur_atr
                if trail_level < sl_px:
                    sl_px = trail_level

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
                gross_pnl = (entry_px - exit_px) * pos_units
                notional = entry_px * pos_units
                comm = notional * round_trip_friction
                trade_pnl = gross_pnl - comm
                trade_ret = trade_pnl / running_eq
                running_eq += trade_pnl

                if trade_pnl > 0.0:
                    wins += 1
                sum_ret += trade_ret
                sum_sq_ret += trade_ret * trade_ret
                in_pos = 0
                pos_units = 0.0

        if in_pos == 0:
            if entries_long[i]:
                in_pos = 1
                entry_px = close[i]
                sl_dist = max(1e-6, sl_atr_mult * cur_atr)
                sl_px = entry_px - sl_dist
                tp_px = entry_px + tp_atr_mult * cur_atr
                risk_cash = running_eq * risk_per_trade_pct
                pos_units = risk_cash / sl_dist
                highest_p = high[i]
                bars_held = 0
            elif entries_short[i]:
                in_pos = -1
                entry_px = close[i]
                sl_dist = max(1e-6, sl_atr_mult * cur_atr)
                sl_px = entry_px + sl_dist
                tp_px = entry_px - tp_atr_mult * cur_atr
                risk_cash = running_eq * risk_per_trade_pct
                pos_units = risk_cash / sl_dist
                lowest_p = low[i]
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


def extract_candidate_trade_pnls(
    candidate: dict,
    df: pd.DataFrame,
    risk_per_trade_pct: Optional[float] = None
) -> np.ndarray:
    """Reconstruye el array de PnLs individuales de cada trade del candidato con sizing proporcional."""
    close = np.ascontiguousarray(df["close"].values, dtype=np.float64)
    high = np.ascontiguousarray(df["high"].values, dtype=np.float64)
    low = np.ascontiguousarray(df["low"].values, dtype=np.float64)
    open_p = np.ascontiguousarray(df["open"].values, dtype=np.float64)
    volume = np.ascontiguousarray(df["volume"].values, dtype=np.float64)
    atr = calc_atr_fast(high, low, close, 14)

    timestamps = df["time"] if "time" in df.columns else None
    is_equity_index = any(k in candidate["asset"].upper() for k in ["NDX", "SPX", "US500", "USTEC", "NASDAQ"])

    factory = HybridSignalFactory(
        open_p, high, low, close, volume,
        timestamps=timestamps,
        rth_only=is_equity_index,
        long_only=is_equity_index
    )
    l_mask, s_mask = factory.generate_signal(
        macro_anchor=candidate["macro_anchor"],
        entropy_max=candidate["entropy_max"],
        symbolic_trigger=candidate["symbolic_trigger"],
        param1=candidate["param1"],
        param2=candidate["param2"],
        trigger_threshold=candidate["trigger_threshold"]
    )

    friction = 0.0006 if any(k in candidate["asset"].upper() for k in ["NDX", "SPX"]) else 0.0014
    sl_m = float(candidate["sl_atr_mult"])
    tp_m = float(candidate["tp_atr_mult"])
    max_h = 48

    if risk_per_trade_pct is None:
        desk_mode = candidate.get("desk_mode", "CAPITAL_PROPIO")
        risk_pct = 0.005 if desk_mode == "PROP_FIRM" else 0.01
    else:
        risk_pct = float(risk_per_trade_pct)

    n = len(close)
    in_pos = 0
    entry_px = 0.0
    sl_px = 0.0
    tp_px = 0.0
    bars_held = 0
    pos_units = 0.0
    highest_p = 0.0
    lowest_p = 0.0
    trade_pnls = []
    running_eq = 1000.0

    for i in range(1, n):
        cur_atr = atr[i] if not np.isnan(atr[i]) and atr[i] > 0 else close[i] * 0.01

        if in_pos == 1:
            bars_held += 1
            if high[i] > highest_p:
                highest_p = high[i]
            gain = highest_p - entry_px
            if gain >= 1.0 * cur_atr:
                be = entry_px + 0.1 * cur_atr
                if sl_px < be:
                    sl_px = be
            if gain >= 1.2 * cur_atr:
                trail = highest_p - 0.8 * cur_atr
                if trail > sl_px:
                    sl_px = trail

            exit_trade = False
            exit_px = 0.0
            if low[i] <= sl_px:
                exit_px = sl_px
                exit_trade = True
            elif high[i] >= tp_px:
                exit_px = tp_px
                exit_trade = True
            elif bars_held >= max_h:
                exit_px = close[i]
                exit_trade = True

            if exit_trade:
                gross_pnl = (exit_px - entry_px) * pos_units
                notional = entry_px * pos_units
                comm = notional * friction
                pnl = gross_pnl - comm
                running_eq += pnl
                trade_pnls.append(pnl)
                in_pos = 0
                pos_units = 0.0

        elif in_pos == -1:
            bars_held += 1
            if low[i] < lowest_p:
                lowest_p = low[i]
            drop = entry_px - lowest_p
            if drop >= 1.0 * cur_atr:
                be = entry_px - 0.1 * cur_atr
                if sl_px > be:
                    sl_px = be
            if drop >= 1.2 * cur_atr:
                trail = lowest_p + 0.8 * cur_atr
                if trail < sl_px:
                    sl_px = trail

            exit_trade = False
            exit_px = 0.0
            if high[i] >= sl_px:
                exit_px = sl_px
                exit_trade = True
            elif low[i] <= tp_px:
                exit_px = tp_px
                exit_trade = True
            elif bars_held >= max_h:
                exit_px = close[i]
                exit_trade = True

            if exit_trade:
                gross_pnl = (entry_px - exit_px) * pos_units
                notional = entry_px * pos_units
                comm = notional * friction
                pnl = gross_pnl - comm
                running_eq += pnl
                trade_pnls.append(pnl)
                in_pos = 0
                pos_units = 0.0

        if in_pos == 0:
            if l_mask[i]:
                in_pos = 1
                entry_px = close[i]
                sl_dist = max(1e-6, sl_m * cur_atr)
                sl_px = entry_px - sl_dist
                tp_px = entry_px + tp_m * cur_atr
                risk_cash = running_eq * risk_pct
                pos_units = risk_cash / sl_dist
                highest_p = high[i]
                bars_held = 0
            elif s_mask[i]:
                in_pos = -1
                entry_px = close[i]
                sl_dist = max(1e-6, sl_m * cur_atr)
                sl_px = entry_px + sl_dist
                tp_px = entry_px - tp_m * cur_atr
                risk_cash = running_eq * risk_pct
                pos_units = risk_cash / sl_dist
                lowest_p = low[i]
                bars_held = 0

    return np.array(trade_pnls, dtype=np.float64)
