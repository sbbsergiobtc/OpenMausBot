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

try:
    from numba import njit
except ImportError:
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

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
    risk_per_trade_pct: Optional[float] = None,
    apply_consistency_clamp: bool = False,
    target_challenge_pct: float = 6.0
) -> np.ndarray:
    """Reconstruye el array de PnLs individuales de cada trade del candidato con sizing proporcional.
    Soporta apply_consistency_clamp=True para simular el modo de evaluación con regla del 40%."""
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
        trigger_threshold=candidate["trigger_threshold"],
        regime_gate=candidate.get("regime_gate", "ANY")
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
                if apply_consistency_clamp and pnl > 0:
                    max_allowed_profit = 1000.0 * (target_challenge_pct / 100.0) * 0.40 * 0.95
                    if pnl > max_allowed_profit:
                        pnl = max_allowed_profit
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
                if apply_consistency_clamp and pnl > 0:
                    max_allowed_profit = 1000.0 * (target_challenge_pct / 100.0) * 0.40 * 0.95
                    if pnl > max_allowed_profit:
                        pnl = max_allowed_profit
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


def extract_candidate_trade_diagnostics(
    candidate: dict,
    df: pd.DataFrame,
    risk_per_trade_pct: Optional[float] = None,
    dual_lens: bool = True
) -> Dict[str, Any]:
    """
    Reconstruye las métricas microestructurales trade a trade del candidato:
    1. Vectores MAE (Maximum Adverse Excursion) y MFE (Maximum Favorable Excursion) en unidades de ATR.
    2. Calibración estadística óptima de salidas (Techain/StratOS):
       - SL sugerido = P95(MAE de trades ganadores)
       - TP sugerido = P75(MFE de trades ganadores)
    3. Cálculo de Drawdown END OF DAY (EOD) estricto (Regla Suprema de Fondeo: sin Trailing intradía),
       evaluando el High-Water Mark exclusivamente al cierre contable de cada día natural.
    """
    close = np.ascontiguousarray(df["close"].values, dtype=np.float64)
    high = np.ascontiguousarray(df["high"].values, dtype=np.float64)
    low = np.ascontiguousarray(df["low"].values, dtype=np.float64)
    open_p = np.ascontiguousarray(df["open"].values, dtype=np.float64)
    volume = np.ascontiguousarray(df["volume"].values, dtype=np.float64)
    atr = calc_atr_fast(high, low, close, 14)

    timestamps = df["time"] if "time" in df.columns else None
    if timestamps is not None:
        dt_series = pd.to_datetime(timestamps, utc=True)
        day_ids = (dt_series.values.astype("datetime64[D]").astype(np.int64))
    else:
        # Fallback: cada 24 barras = 1 día contable EOD
        day_ids = (np.arange(len(close)) // 24).astype(np.int64)

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
        trigger_threshold=candidate["trigger_threshold"],
        regime_gate=candidate.get("regime_gate", "ANY")
    )

    friction = 0.0006 if any(k in candidate["asset"].upper() for k in ["NDX", "SPX", "US500", "USTEC"]) else 0.0014
    sl_m = float(candidate["sl_atr_mult"])
    tp_m = float(candidate["tp_atr_mult"])
    max_h = 48

    if risk_per_trade_pct is None:
        desk_mode = str(candidate.get("desk_mode", "CAPITAL_PROPIO")).upper()
        risk_pct = 0.005 if "PROP" in desk_mode else 0.01
    else:
        risk_pct = float(risk_per_trade_pct)

    n = len(close)
    in_pos = 0
    entry_px = 0.0
    entry_atr = 1.0
    sl_px = 0.0
    tp_px = 0.0
    bars_held = 0
    pos_units = 0.0
    highest_p = 0.0
    lowest_p = 0.0

    trade_pnls: List[float] = []
    trade_mae_atr: List[float] = []
    trade_mfe_atr: List[float] = []
    winner_mae_atr: List[float] = []
    winner_mfe_atr: List[float] = []

    # Segmentación MAE/MFE Condicionada por Régimen Canónico (Ignacio Ayago / Techain)
    entry_regime_7 = 0
    trending_winner_mae_atr: List[float] = []
    trending_winner_mfe_atr: List[float] = []
    choppy_winner_mae_atr: List[float] = []
    choppy_winner_mfe_atr: List[float] = []

    running_eq = 1000.0
    continuous_peak_eq = 1000.0
    continuous_max_dd_pct = 0.0

    # Contabilidad estricta END OF DAY (EOD) para Fondeo (Regla Suprema AGENTS.md)
    eod_peak_balance = 1000.0
    eod_max_dd_pct = 0.0
    eod_daily_max_loss_pct = 0.0
    prev_eod_balance = 1000.0

    for i in range(1, n):
        cur_atr = atr[i] if not np.isnan(atr[i]) and atr[i] > 0 else close[i] * 0.01

        if in_pos == 1:
            bars_held += 1
            if high[i] > highest_p:
                highest_p = high[i]
            if low[i] < lowest_p:
                lowest_p = low[i]

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

                mae_val = max(0.0, (entry_px - lowest_p) / max(1e-9, entry_atr))
                mfe_val = max(0.0, (highest_p - entry_px) / max(1e-9, entry_atr))
                trade_mae_atr.append(mae_val)
                trade_mfe_atr.append(mfe_val)
                if pnl > 0:
                    winner_mae_atr.append(mae_val)
                    winner_mfe_atr.append(mfe_val)
                    if entry_regime_7 in (0, 1, 3, 4):  # Tendencias S0/S1/S3/S4
                        trending_winner_mae_atr.append(mae_val)
                        trending_winner_mfe_atr.append(mfe_val)
                    elif entry_regime_7 in (2, 5, 6, 7, 8):  # Rango / Choppy S2/S5/S6/S7/S8
                        choppy_winner_mae_atr.append(mae_val)
                        choppy_winner_mfe_atr.append(mfe_val)

                in_pos = 0
                pos_units = 0.0

        elif in_pos == -1:
            bars_held += 1
            if low[i] < lowest_p:
                lowest_p = low[i]
            if high[i] > highest_p:
                highest_p = high[i]

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

                mae_val = max(0.0, (highest_p - entry_px) / max(1e-9, entry_atr))
                mfe_val = max(0.0, (entry_px - lowest_p) / max(1e-9, entry_atr))
                trade_mae_atr.append(mae_val)
                trade_mfe_atr.append(mfe_val)
                if pnl > 0:
                    winner_mae_atr.append(mae_val)
                    winner_mfe_atr.append(mfe_val)
                    if entry_regime_7 in (0, 1, 3, 4):  # Tendencias S0/S1/S3/S4
                        trending_winner_mae_atr.append(mae_val)
                        trending_winner_mfe_atr.append(mfe_val)
                    elif entry_regime_7 in (2, 5, 6, 7, 8):  # Rango / Choppy S2/S5/S6/S7/S8
                        choppy_winner_mae_atr.append(mae_val)
                        choppy_winner_mfe_atr.append(mfe_val)

                in_pos = 0
                pos_units = 0.0

        if in_pos == 0:
            if l_mask[i]:
                in_pos = 1
                entry_px = close[i]
                entry_atr = cur_atr
                entry_regime_7 = int(factory.regime_7[i]) if hasattr(factory, "regime_7") else 0
                sl_dist = max(1e-6, sl_m * cur_atr)
                sl_px = entry_px - sl_dist
                tp_px = entry_px + tp_m * cur_atr
                risk_cash = running_eq * risk_pct
                pos_units = risk_cash / sl_dist
                highest_p = high[i]
                lowest_p = low[i]
                bars_held = 0
            elif s_mask[i]:
                in_pos = -1
                entry_px = close[i]
                entry_atr = cur_atr
                entry_regime_7 = int(factory.regime_7[i]) if hasattr(factory, "regime_7") else 0
                sl_dist = max(1e-6, sl_m * cur_atr)
                sl_px = entry_px + sl_dist
                tp_px = entry_px - tp_m * cur_atr
                risk_cash = running_eq * risk_pct
                pos_units = risk_cash / sl_dist
                highest_p = high[i]
                lowest_p = low[i]
                bars_held = 0

        # Drawdown continuo sobre trades cerrados (Capital Propio)
        if running_eq > continuous_peak_eq:
            continuous_peak_eq = running_eq
        c_dd = (continuous_peak_eq - running_eq) / continuous_peak_eq * 100.0
        if c_dd > continuous_max_dd_pct:
            continuous_max_dd_pct = c_dd

        # Contabilidad EOD estricta al cambio de día (Regla Suprema Fondeo)
        if day_ids[i] != day_ids[i - 1] or i == n - 1:
            eod_balance = running_eq
            if prev_eod_balance > 0:
                daily_loss_pct = max(0.0, (prev_eod_balance - eod_balance) / prev_eod_balance * 100.0)
                if daily_loss_pct > eod_daily_max_loss_pct:
                    eod_daily_max_loss_pct = daily_loss_pct
            if eod_balance > eod_peak_balance:
                eod_peak_balance = eod_balance
            eod_dd = (eod_peak_balance - eod_balance) / eod_peak_balance * 100.0
            if eod_dd > eod_max_dd_pct:
                eod_max_dd_pct = eod_dd
            prev_eod_balance = eod_balance

    pnls_arr = np.array(trade_pnls, dtype=np.float64)
    wins_arr = pnls_arr[pnls_arr > 0]
    loss_arr = pnls_arr[pnls_arr < 0]

    win_rate_pct = float(len(wins_arr) / len(pnls_arr) * 100.0) if len(pnls_arr) > 0 else 0.0
    avg_win = float(np.mean(wins_arr)) if len(wins_arr) > 0 else 0.0
    avg_loss = float(np.mean(np.abs(loss_arr))) if len(loss_arr) > 0 else 0.0
    rr_ratio = (avg_win / avg_loss) if avg_loss > 1e-9 else 0.0

    opt_sl_atr = float(np.percentile(winner_mae_atr, 95)) if len(winner_mae_atr) >= 5 else sl_m
    opt_tp_atr = float(np.percentile(winner_mfe_atr, 75)) if len(winner_mfe_atr) >= 5 else tp_m

    # Calibración Dinámica de MAE/MFE Condicionada por Régimen Canónico (1.2):
    # En S0/S1/S3/S4 (Tendencias Fuertes): TP = P85(MFE) para dejar correr beneficios (Fat-Tail Capture)
    # En S5/S6/S8 (Choppy Mean Reversion): TP = P60(MFE) y SL = P90(MAE) para cortes rápidos
    trending_tp_atr = float(np.percentile(trending_winner_mfe_atr, 85)) if len(trending_winner_mfe_atr) >= 4 else round(opt_tp_atr * 1.25, 2)
    trending_sl_atr = float(np.percentile(trending_winner_mae_atr, 95)) if len(trending_winner_mae_atr) >= 4 else opt_sl_atr

    choppy_tp_atr = float(np.percentile(choppy_winner_mfe_atr, 60)) if len(choppy_winner_mfe_atr) >= 4 else round(opt_tp_atr * 0.75, 2)
    choppy_sl_atr = float(np.percentile(choppy_winner_mae_atr, 90)) if len(choppy_winner_mae_atr) >= 4 else round(opt_sl_atr * 0.85, 2)

    # -------------------------------------------------------------
    # GENERADOR DE REPORTES BIFÁSICOS (EVALUACIÓN vs. FUNDED)
    # -------------------------------------------------------------
    # 1. Lente Evaluación (Challenge Mode con Hard Clamp 40% de consistencia):
    target_challenge_pct = 6.0 if "FUTURES" in str(candidate.get("desk_mode", "")).upper() else 8.0
    consistency_cap_ratio = 0.40
    safety_buffer = 0.95
    max_single_trade_usd = 1000.0 * (target_challenge_pct / 100.0) * consistency_cap_ratio * safety_buffer

    eval_trade_pnls = []
    eval_clamped_count = 0
    for p in trade_pnls:
        if p > max_single_trade_usd:
            eval_trade_pnls.append(max_single_trade_usd)
            eval_clamped_count += 1
        else:
            eval_trade_pnls.append(p)

    eval_pnls_arr = np.array(eval_trade_pnls, dtype=np.float64)
    eval_net_pnl = float(np.sum(eval_pnls_arr)) if len(eval_pnls_arr) > 0 else 0.0
    eval_roi_pct = round((eval_net_pnl / 1000.0) * 100.0, 2)

    # Simulación Monte Carlo (1000 caminos) de tasa de pase en < 15 días:
    eval_pass_rate_pct = 0.0
    if len(eval_pnls_arr) >= 10:
        trades_per_window = min(len(eval_pnls_arr), 15)
        sim_paths = 1000
        passes = 0
        target_cash = 1000.0 * (target_challenge_pct / 100.0)
        max_loss_cash = 1000.0 * 0.04  # 4% max loss
        for _ in range(sim_paths):
            sampled = np.random.choice(eval_pnls_arr, size=trades_per_window, replace=True)
            cumsum = np.cumsum(sampled)
            hit_target = np.any(cumsum >= target_cash)
            hit_fail = np.any(cumsum <= -max_loss_cash)
            if hit_target and not hit_fail:
                passes += 1
            elif hit_target and hit_fail:
                idx_target = int(np.argmax(cumsum >= target_cash))
                idx_fail = int(np.argmax(cumsum <= -max_loss_cash))
                if idx_target < idx_fail:
                    passes += 1
        eval_pass_rate_pct = round((passes / sim_paths) * 100.0, 1)

    eval_lens = {
        "lens_name": "EVALUATION_CHALLENGE_VIEW",
        "consistency_clamp_active": True,
        "consistency_cap_usd": round(max_single_trade_usd, 2),
        "clamped_trades_count": eval_clamped_count,
        "net_pnl_usd": round(eval_net_pnl, 2),
        "net_roi_pct": eval_roi_pct,
        "eod_max_dd_pct": round(float(eod_max_dd_pct), 2),
        "mc_pass_rate_pct": eval_pass_rate_pct,
        "verdict": "QUALIFIED_FOR_EVALUATION" if (eval_pass_rate_pct >= 70.0 and eod_max_dd_pct <= 3.5) else "NEEDS_TUNING",
        "description": "Evalúa el reto de fondeo con Hard Clamp 40% de consistencia y tasa de pase Monte Carlo >= 70%."
    }

    # 2. Lente Funded / Live (Harvest Mode sin consistencia):
    funded_pnls_arr = pnls_arr
    funded_net_pnl = float(np.sum(funded_pnls_arr)) if len(funded_pnls_arr) > 0 else 0.0
    funded_roi_pct = round((funded_net_pnl / 1000.0) * 100.0, 2)
    calmar_ratio = round(funded_roi_pct / max(0.1, float(eod_max_dd_pct)), 2)
    est_monthly_payout = round((funded_roi_pct / 100.0) * 50000.0 * 0.40, 2)

    funded_lens = {
        "lens_name": "FUNDED_HARVEST_VIEW",
        "consistency_clamp_active": False,
        "clamped_trades_count": 0,
        "net_pnl_usd": round(funded_net_pnl, 2),
        "net_roi_pct": funded_roi_pct,
        "eod_max_dd_pct": round(float(eod_max_dd_pct), 2),
        "calmar_ratio": calmar_ratio,
        "expected_monthly_payout_usd_50k": est_monthly_payout,
        "verdict": "GRADUATED_FOR_PAYOUTS" if (calmar_ratio >= 2.5 and funded_roi_pct > 15.0) else "ACCEPTABLE",
        "description": "Evalúa la cuenta fondeada real dejando correr los beneficios sin límite de consistencia."
    }

    return {
        "trade_pnls": pnls_arr,
        "trade_mae_atr": np.array(trade_mae_atr, dtype=np.float64),
        "trade_mfe_atr": np.array(trade_mfe_atr, dtype=np.float64),
        "winners_mae_p95_atr": round(opt_sl_atr, 2),
        "winners_mfe_p75_atr": round(opt_tp_atr, 2),
        "eod_max_dd_pct": round(float(eod_max_dd_pct), 2),
        "eod_daily_max_loss_pct": round(float(eod_daily_max_loss_pct), 2),
        "continuous_max_dd_pct": round(float(continuous_max_dd_pct), 2),
        "win_rate_pct": round(win_rate_pct, 2),
        "avg_win_usd": round(avg_win, 2),
        "avg_loss_usd": round(avg_loss, 2),
        "reward_risk_ratio": round(rr_ratio, 2),
        "regime_conditioned_exits": {
            "trending_s0_s1": {
                "tp_atr": round(trending_tp_atr, 2),
                "sl_atr": round(trending_sl_atr, 2),
                "mfe_percentile": 85,
                "mae_percentile": 95,
                "description": "Fat-Tail Capture en tendencias limpias"
            },
            "choppy_s5_s6": {
                "tp_atr": round(choppy_tp_atr, 2),
                "sl_atr": round(choppy_sl_atr, 2),
                "mfe_percentile": 60,
                "mae_percentile": 90,
                "description": "Cortes rápidos en rango/reversión"
            },
            "baseline_global": {
                "tp_atr": round(opt_tp_atr, 2),
                "sl_atr": round(opt_sl_atr, 2),
                "mfe_percentile": 75,
                "mae_percentile": 95,
                "description": "Percentiles globales de referencia"
            }
        },
        "dual_lens_report": {
            "evaluation_lens": eval_lens,
            "funded_lens": funded_lens
        }
    }

