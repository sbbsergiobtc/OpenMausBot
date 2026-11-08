"""
Fábrica Vectorizada de Señales Cuantitativas Híbridas
AlgrokQuant · Jev Quantitative Engine

Acopla en 3 capas deterministas:
Capa 1: Anclajes Macroeconómicos Lineales (VWAP, Donchian, Bollinger, EMAs)
Capa 2: Filtro de Régimen de Entropía de Shannon (H_norm <= threshold)
Capa 3: Gatillos No Lineales Simbólicos (ts_rank, ts_corr, ts_delta, OFI, ΔHist_norm)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

try:
    from numba import njit
except ImportError:
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from .symbolic_engine import (
    ts_delay,
    ts_delta,
    ts_std,
    ts_zscore,
    ts_decay_linear,
    ts_rank,
    ts_argmax,
    ts_argmin,
    ts_corr,
    calc_atr_fast,
    calc_diff_hist_norm,
    calc_order_flow_imbalance_proxy,
    calc_shannon_entropy_fast,
    calc_adx_fast,
    calc_atr_ratio_fast,
    calc_fvg_imbalance_fast,
    classify_7_regimes_fast
)


# ==============================================================================
# INDICADORES MACRO LINEALES ACELERADOS
# ==============================================================================

@njit(fastmath=True)
def calc_ema_fast(x: np.ndarray, period: int) -> np.ndarray:
    """EMA acelerada en Numba."""
    n = len(x)
    out = np.empty(n, dtype=np.float64)
    out[0] = x[0]
    alpha = 2.0 / (period + 1.0)
    for i in range(1, n):
        out[i] = alpha * x[i] + (1.0 - alpha) * out[i - 1]
    return out


@njit(fastmath=True)
def calc_bollinger_bands(close: np.ndarray, period: int = 20, num_std: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Bandas de Bollinger (Media, Superior, Inferior)."""
    n = len(close)
    mid = np.full(n, np.nan, dtype=np.float64)
    up = np.full(n, np.nan, dtype=np.float64)
    low = np.full(n, np.nan, dtype=np.float64)
    if period <= 1 or n < period:
        return mid, up, low

    for i in range(period - 1, n):
        w = close[i - period + 1 : i + 1]
        m = 0.0
        for val in w:
            m += val
        m /= period
        var = 0.0
        for val in w:
            diff = val - m
            var += diff * diff
        s = np.sqrt(var / (period - 1))
        mid[i] = m
        up[i] = m + num_std * s
        low[i] = m - num_std * s
    return mid, up, low


@njit(fastmath=True)
def calc_donchian_channel(high: np.ndarray, low: np.ndarray, period: int = 20) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Canal de Donchian (Superior, Inferior, Medio)."""
    n = len(high)
    up = np.full(n, np.nan, dtype=np.float64)
    dn = np.full(n, np.nan, dtype=np.float64)
    mid = np.full(n, np.nan, dtype=np.float64)
    if period <= 1 or n < period:
        return up, dn, mid

    for i in range(period - 1, n):
        max_v = -1e30
        min_v = 1e30
        for j in range(i - period + 1, i + 1):
            if high[j] > max_v:
                max_v = high[j]
            if low[j] < min_v:
                min_v = low[j]
        up[i] = max_v
        dn[i] = min_v
        mid[i] = 0.5 * (max_v + min_v)
    return up, dn, mid


@njit(fastmath=True)
def calc_rolling_vwap(close: np.ndarray, volume: np.ndarray, period: int = 48) -> np.ndarray:
    """Rolling VWAP sobre ventana móvil de barras."""
    n = len(close)
    vwap = np.full(n, np.nan, dtype=np.float64)
    if period <= 0 or n < period:
        return vwap

    for i in range(period - 1, n):
        pv_sum = 0.0
        v_sum = 0.0
        for j in range(i - period + 1, i + 1):
            v = volume[j]
            pv_sum += close[j] * v
            v_sum += v
        if v_sum > 1e-12:
            vwap[i] = pv_sum / v_sum
        else:
            vwap[i] = close[i]
    return vwap


@njit(fastmath=True)
def calc_supertrend_fast(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int = 10,
    multiplier: float = 3.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Supertrend ATR acelerado en Numba JIT (Tier S de Seguimiento Tendencial).
    Retorna (supertrend_line, trend_dir) donde trend_dir es +1 (Alcista) o -1 (Bajista).
    """
    n = len(close)
    atr = calc_atr_fast(high, low, close, period)
    st = np.empty(n, dtype=np.float64)
    direction = np.ones(n, dtype=np.int32)

    final_up = np.empty(n, dtype=np.float64)
    final_dn = np.empty(n, dtype=np.float64)

    hl2_0 = 0.5 * (high[0] + low[0])
    final_up[0] = hl2_0 + multiplier * atr[0]
    final_dn[0] = hl2_0 - multiplier * atr[0]
    st[0] = final_dn[0]

    for i in range(1, n):
        hl2 = 0.5 * (high[i] + low[i])
        basic_up = hl2 + multiplier * atr[i]
        basic_dn = hl2 - multiplier * atr[i]

        if basic_up < final_up[i - 1] or close[i - 1] > final_up[i - 1]:
            final_up[i] = basic_up
        else:
            final_up[i] = final_up[i - 1]

        if basic_dn > final_dn[i - 1] or close[i - 1] < final_dn[i - 1]:
            final_dn[i] = basic_dn
        else:
            final_dn[i] = final_dn[i - 1]

        prev_dir = direction[i - 1]
        if prev_dir == -1 and close[i] > final_up[i - 1]:
            direction[i] = 1
        elif prev_dir == 1 and close[i] < final_dn[i - 1]:
            direction[i] = -1
        else:
            direction[i] = prev_dir

        st[i] = final_dn[i] if direction[i] == 1 else final_up[i]

    return st, direction


# ==============================================================================
# FÁBRICA COMBINATORIA DE SEÑALES HÍBRIDAS
# ==============================================================================

class HybridSignalFactory:
    """
    Genera matrices de señales booleanas para VectorBT combinando:
    1. Anclas Lineales: VWAP, Bollinger, Donchian, Trend EMA, Supertrend.
    2. Puerta de Régimen: Entropía de Shannon + Clasificador de 7 Regímenes Canónicos (ADX/ATR Ratio).
    3. Gatillos No Lineales Simbólicos (incluyendo FVG Imbalance y Z-Score Extreme sin look-ahead).
    """

    def __init__(
        self,
        open_p: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        volume: np.ndarray,
        timestamps: Any = None,
        rth_only: bool = True,
        long_only: bool = True
    ):
        self.open = np.ascontiguousarray(open_p, dtype=np.float64)
        self.high = np.ascontiguousarray(high, dtype=np.float64)
        self.low = np.ascontiguousarray(low, dtype=np.float64)
        self.close = np.ascontiguousarray(close, dtype=np.float64)
        self.volume = np.ascontiguousarray(volume, dtype=np.float64)
        self.n = len(self.close)
        self.rth_only = rth_only
        self.long_only = long_only

        # Precomputación de Primitivas para Reutilización
        self.delta_p = ts_delta(self.close, 1)
        self.rvol_20 = self.volume / (ts_decay_linear(self.volume, 20) + 1e-12)
        self.atr_14 = calc_atr_fast(self.high, self.low, self.close, 14)
        self.h_norm = calc_shannon_entropy_fast(self.close, window=48, bins=10)
        self.ofi = calc_order_flow_imbalance_proxy(self.open, self.high, self.low, self.close, self.volume)
        self.diff_hist_norm = calc_diff_hist_norm(self.close, self.high, self.low, 12, 26, 9, 14)
        self.ema_200 = calc_ema_fast(self.close, 200)

        # Primitivas de Puerta de Régimen e Ineficiencia (Techain/StratOS Tier S)
        self.adx_14, self.plus_di_14, self.minus_di_14 = calc_adx_fast(self.high, self.low, self.close, 14)
        self.atr_ratio = calc_atr_ratio_fast(self.high, self.low, self.close, 14, 100)
        self.regime_7 = classify_7_regimes_fast(
            self.close, self.ema_200, self.h_norm,
            self.adx_14, self.plus_di_14, self.minus_di_14, self.atr_ratio
        )
        self.bull_fvg, self.bear_fvg = calc_fvg_imbalance_fast(
            self.high, self.low, self.close, self.atr_14, 0.40
        )

        # Filtro de Sesión Operativa RTH (14:00 a 20:00 UTC)
        if timestamps is not None:
            if hasattr(timestamps, "hour"):
                hours = timestamps.hour
            elif hasattr(timestamps, "dt"):
                hours = timestamps.dt.hour.values
            else:
                try:
                    dt_s = pd.to_datetime(timestamps, utc=True)
                    hours = dt_s.hour if hasattr(dt_s, "hour") else dt_s.dt.hour.values
                except Exception:
                    hours = np.full(self.n, 15, dtype=np.int32)
            self.rth_mask = (hours >= 14) & (hours <= 20)
        else:
            self.rth_mask = np.ones(self.n, dtype=np.bool_)

    def generate_signal(
        self,
        macro_anchor: str = "BOLLINGER_REVERSION",
        entropy_max: float = 0.78,
        symbolic_trigger: str = "VOL_CORR_ABSORPTION",
        param1: int = 20,
        param2: float = 2.0,
        trigger_threshold: float = 0.80,
        regime_gate: str = "ANY"
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Genera máscaras booleanas (entries_long, entries_short).
        Soporta separación estricta Signal vs. Regime Gate (Entropía + 7 Regímenes ADX/ATR).
        """
        # 1. Filtro de Régimen (Entropía de Shannon + Puerta Canónica de 7 Regímenes)
        regime_mask = (self.h_norm <= entropy_max) & ~np.isnan(self.h_norm) & (self.regime_7 != 6)

        if regime_gate == "TREND_ONLY":
            # Requiere ADX(14) >= 25 (Regímenes 0: Strong Bull, 1: Strong Bear o 5: Volatility Expansion)
            regime_mask = regime_mask & ((self.adx_14 >= 25.0) | (self.regime_7 == 5))
        elif regime_gate == "MEAN_REV_ONLY":
            # Requiere ADX(14) < 22 y volatilidad acotada (Régimen 3: Ranging Mean Reversion)
            regime_mask = regime_mask & (self.adx_14 < 22.0) & (self.atr_ratio <= 1.35)
        elif regime_gate == "SQUEEZE_BREAKOUT":
            # Compresión previa seguida de expansión (Regímenes 4 o 5)
            regime_mask = regime_mask & ((self.regime_7 == 4) | (self.regime_7 == 5) | (self.adx_14 >= 22.0))

        # 2. Capa Macroeconómica Lineal
        long_macro = np.zeros(self.n, dtype=np.bool_)
        short_macro = np.zeros(self.n, dtype=np.bool_)

        if macro_anchor == "BOLLINGER_REVERSION":
            _, bb_up, bb_low = calc_bollinger_bands(self.close, period=param1, num_std=param2)
            long_macro = (self.close <= bb_low)
            short_macro = (self.close >= bb_up)

        elif macro_anchor == "DONCHIAN_BREAKOUT":
            dc_up, dc_dn, _ = calc_donchian_channel(self.high, self.low, period=param1)
            prev_up = ts_delay(dc_up, 1)
            prev_dn = ts_delay(dc_dn, 1)
            long_macro = (self.high >= prev_up)
            short_macro = (self.low <= prev_dn)

        elif macro_anchor == "VWAP_VALUE_DISCOUNT":
            vwap = calc_rolling_vwap(self.close, self.volume, period=param1)
            dist_pct = (self.close - vwap) / (vwap + 1e-12) * 100.0
            # param2 representa el umbral porcentual de descuento (ej. 1.5%)
            long_macro = (dist_pct <= -param2)
            short_macro = (dist_pct >= param2)

        elif macro_anchor == "EMA_TREND_PULLBACK":
            ema_trend = calc_ema_fast(self.close, period=param1)
            dist_atr = (self.close - ema_trend) / (self.atr_14 + 1e-12)
            # Pullback moderado hacia la EMA dentro de tendencia
            long_macro = (self.close > ema_trend) & (dist_atr <= param2)
            short_macro = (self.close < ema_trend) & (dist_atr >= -param2)

        elif macro_anchor == "SUPERTREND_FOLLOW":
            st_line, st_dir = calc_supertrend_fast(self.high, self.low, self.close, period=max(5, int(param1)), multiplier=float(param2))
            # Confirmación con puerta ADX >= 20 para evitar whipsaws en lateral
            long_macro = (st_dir == 1) & (self.close > st_line) & (self.adx_14 >= 20.0)
            short_macro = (st_dir == -1) & (self.close < st_line) & (self.adx_14 >= 20.0)

        # 3. Capa Simbólica No Lineal (Gatillo de Microestructura)
        long_trigger = np.zeros(self.n, dtype=np.bool_)
        short_trigger = np.zeros(self.n, dtype=np.bool_)

        if symbolic_trigger == "VOL_CORR_ABSORPTION":
            # ts_rank(ts_corr(delta_p, rvol, 10), 5)
            # Divergencia: mucho volumen con escasa variación de precio o reversión
            corr = ts_corr(self.delta_p, self.rvol_20, 10)
            ranked_corr = ts_rank(corr, 5)
            long_trigger = (ranked_corr >= trigger_threshold)
            short_trigger = (ranked_corr <= (1.0 - trigger_threshold))

        elif symbolic_trigger == "MACD_ACCELERATION":
            # Segunda derivada normalizada por volatilidad
            long_trigger = (self.diff_hist_norm >= trigger_threshold)
            short_trigger = (self.diff_hist_norm <= -trigger_threshold)

        elif symbolic_trigger == "OFI_PRESSURE":
            # Order Flow Imbalance normalizado con Z-score móvil
            z_ofi = ts_zscore(self.ofi, 20)
            long_trigger = (z_ofi >= trigger_threshold)
            short_trigger = (z_ofi <= -trigger_threshold)

        elif symbolic_trigger == "LINEAR_DECAY_EXTREME":
            # ts_decay_linear de la variación porcentual en rango percentil
            decay_dp = ts_decay_linear(self.delta_p, 10)
            rnk = ts_rank(decay_dp, 20)
            long_trigger = (rnk <= (1.0 - trigger_threshold))  # Agotamiento de caída
            short_trigger = (rnk >= trigger_threshold)         # Agotamiento de subida

        elif symbolic_trigger == "FVG_IMBALANCE":
            # Ineficiencia de 3 velas cerradas confirmada con volumen relativo > trigger_threshold
            long_trigger = self.bull_fvg & (self.rvol_20 >= max(0.8, trigger_threshold))
            short_trigger = self.bear_fvg & (self.rvol_20 >= max(0.8, trigger_threshold))

        elif symbolic_trigger == "ZSCORE_EXTREME":
            # Reversión estadística pura por Z-Score (|Z| >= trigger_threshold * 2.5)
            z_p = ts_zscore(self.close, 20)
            z_thresh = max(1.5, trigger_threshold * 2.5)
            long_trigger = (z_p <= -z_thresh)
            short_trigger = (z_p >= z_thresh)

        # 4. Señal Final Compuesta (Intersección Booleana)
        entries_long = long_macro & long_trigger & regime_mask
        entries_short = short_macro & short_trigger & regime_mask

        # 5. Filtro de Sesión Operativa (RTH)
        if self.rth_only:
            entries_long = entries_long & self.rth_mask
            entries_short = entries_short & self.rth_mask

        # 6. Filtro Direccional Asimétrico (Sesgo Estructural Institucional)
        entries_long = entries_long & (self.close >= self.ema_200 * 0.99)
        if self.long_only:
            entries_short = np.zeros_like(entries_short)
        else:
            entries_short = entries_short & (self.close < self.ema_200 * 0.98)

        # Limpiar NaNs iniciales
        entries_long[np.isnan(self.close)] = False
        entries_short[np.isnan(self.close)] = False

        return entries_long, entries_short
