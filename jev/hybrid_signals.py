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
from numba import njit
from typing import Dict, Any, Tuple

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
    calc_shannon_entropy_fast
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


# ==============================================================================
# FÁBRICA COMBINATORIA DE SEÑALES HÍBRIDAS
# ==============================================================================

class HybridSignalFactory:
    """
    Genera matrices de señales booleanas para VectorBT combinando:
    1. Anclas Lineales: VWAP, Bollinger, Donchian, Trend EMA.
    2. Entropía de Shannon (filtro de no-caos).
    3. Gatillos No Lineales Simbólicos.
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
        trigger_threshold: float = 0.80
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Genera máscaras booleanas (entries_long, entries_short).
        """
        # 1. Filtro de Régimen de Entropía
        regime_mask = (self.h_norm <= entropy_max) & ~np.isnan(self.h_norm)

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
