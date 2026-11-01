"""
Módulo de Álgebra Simbólica Vectorizada para Minería de Alfas No Lineales
AlgrokQuant · Jev Quantitative Engine

Implementa operadores de series temporales (WorldQuant Formulaic Alphas)
y transformaciones de microestructura compiladas en Numba y NumPy.
Diseñado para evaluación masiva de alto rendimiento (< 50 ms en 100.000 barras).
"""

import numpy as np
import pandas as pd
from numba import njit, prange
from typing import Tuple, Union


# ==============================================================================
# OPERADORES BÁSICOS DE RETARDO Y DIFERENCIA
# ==============================================================================

@njit(fastmath=True)
def ts_delay(x: np.ndarray, d: int) -> np.ndarray:
    """Retardo temporal de d períodos: x[t-d]."""
    n = len(x)
    out = np.empty(n, dtype=np.float64)
    out[:d] = np.nan
    out[d:] = x[:-d]
    return out


@njit(fastmath=True)
def ts_delta(x: np.ndarray, d: int) -> np.ndarray:
    """Variación neta en d períodos: x[t] - x[t-d]."""
    n = len(x)
    out = np.empty(n, dtype=np.float64)
    out[:d] = np.nan
    out[d:] = x[d:] - x[:-d]
    return out


# ==============================================================================
# OPERADORES ESTADÍSTICOS Y DE MOMENTO
# ==============================================================================

@njit(fastmath=True)
def ts_std(x: np.ndarray, d: int) -> np.ndarray:
    """Desviación estándar móvil de d períodos."""
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    if d <= 1 or n < d:
        return out

    # Algoritmo de suma acumulada numéricamente estable
    for i in range(d - 1, n):
        w = x[i - d + 1 : i + 1]
        m = 0.0
        for val in w:
            m += val
        m /= d
        var = 0.0
        for val in w:
            diff = val - m
            var += diff * diff
        out[i] = np.sqrt(var / (d - 1))
    return out


@njit(fastmath=True)
def ts_zscore(x: np.ndarray, d: int) -> np.ndarray:
    """Z-Score normalizado móvil: (x[t] - mean(x, d)) / std(x, d)."""
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    if d <= 1 or n < d:
        return out

    for i in range(d - 1, n):
        w = x[i - d + 1 : i + 1]
        m = 0.0
        for val in w:
            m += val
        m /= d
        var = 0.0
        for val in w:
            diff = val - m
            var += diff * diff
        s = np.sqrt(var / (d - 1))
        if s > 1e-12:
            out[i] = (x[i] - m) / s
        else:
            out[i] = 0.0
    return out


@njit(fastmath=True)
def ts_decay_linear(x: np.ndarray, d: int) -> np.ndarray:
    """Media móvil ponderada linealmente con pesos decrecientes: [d, d-1, ..., 1]."""
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    if d <= 0 or n < d:
        return out

    w_sum = d * (d + 1) / 2.0
    weights = np.empty(d, dtype=np.float64)
    for k in range(d):
        weights[k] = (k + 1) / w_sum

    for i in range(d - 1, n):
        acc = 0.0
        for j in range(d):
            acc += x[i - d + 1 + j] * weights[j]
        out[i] = acc
    return out


# ==============================================================================
# OPERADORES DE RANGO PERCENTIL Y EXTREMOS
# ==============================================================================

@njit(fastmath=True)
def ts_rank(x: np.ndarray, d: int) -> np.ndarray:
    """
    Rango percentil móvil: posición relativa de x[t] en la ventana d normalizada [0.0, 1.0].
    Equivalente a scipy.stats.percentileofscore sobre ventana móvil.
    """
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    if d <= 1 or n < d:
        return out

    for i in range(d - 1, n):
        current = x[i]
        count_less = 0
        count_equal = 0
        for j in range(i - d + 1, i + 1):
            val = x[j]
            if val < current:
                count_less += 1
            elif val == current:
                count_equal += 1
        # Fórmula estándar percentil
        out[i] = (count_less + 0.5 * count_equal) / float(d)
    return out


@njit(fastmath=True)
def ts_argmax(x: np.ndarray, d: int) -> np.ndarray:
    """Índice relativo del valor máximo en la ventana d (distancia en barras desde la barra actual)."""
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    if d <= 0 or n < d:
        return out

    for i in range(d - 1, n):
        max_val = -1e30
        max_idx = 0
        for j in range(d):
            val = x[i - d + 1 + j]
            if val > max_val:
                max_val = val
                max_idx = j
        out[i] = float(d - 1 - max_idx)  # 0 si el máximo fue la barra actual
    return out


@njit(fastmath=True)
def ts_argmin(x: np.ndarray, d: int) -> np.ndarray:
    """Índice relativo del valor mínimo en la ventana d (distancia en barras desde la barra actual)."""
    n = len(x)
    out = np.full(n, np.nan, dtype=np.float64)
    if d <= 0 or n < d:
        return out

    for i in range(d - 1, n):
        min_val = 1e30
        min_idx = 0
        for j in range(d):
            val = x[i - d + 1 + j]
            if val < min_val:
                min_val = val
                min_idx = j
        out[i] = float(d - 1 - min_idx)
    return out


# ==============================================================================
# OPERADORES BIVARIADOS: CORRELACIÓN Y COVARIANZA
# ==============================================================================

@njit(fastmath=True)
def ts_corr(x: np.ndarray, y: np.ndarray, d: int) -> np.ndarray:
    """
    Correlación de Pearson móvil entre series x e y sobre d períodos.
    Retorna valores acotados estrictamente entre [-1.0, 1.0].
    """
    n = min(len(x), len(y))
    out = np.full(n, np.nan, dtype=np.float64)
    if d <= 1 or n < d:
        return out

    for i in range(d - 1, n):
        mx = 0.0
        my = 0.0
        for j in range(i - d + 1, i + 1):
            mx += x[j]
            my += y[j]
        mx /= d
        my /= d

        cov = 0.0
        var_x = 0.0
        var_y = 0.0
        for j in range(i - d + 1, i + 1):
            dx = x[j] - mx
            dy = y[j] - my
            cov += dx * dy
            var_x += dx * dx
            var_y += dy * dy

        denom = np.sqrt(var_x * var_y)
        if denom > 1e-12:
            rho = cov / denom
            if rho > 1.0:
                rho = 1.0
            elif rho < -1.0:
                rho = -1.0
            out[i] = rho
        else:
            out[i] = 0.0
    return out


# ==============================================================================
# OPERADORES DE MICROESTRUCTURA Y SEGUNDA DERIVADA CUANTITATIVA
# ==============================================================================

@njit(fastmath=True)
def calc_atr_fast(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """Average True Range acelerado en Numba."""
    n = len(close)
    tr = np.empty(n, dtype=np.float64)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i - 1])
        lc = abs(low[i] - close[i - 1])
        tr[i] = max(hl, max(hc, lc))

    alpha = 1.0 / period
    atr = np.empty(n, dtype=np.float64)
    atr[0] = tr[0]
    for i in range(1, n):
        atr[i] = alpha * tr[i] + (1.0 - alpha) * atr[i - 1]
    return atr


@njit(fastmath=True)
def calc_diff_hist_norm(
    close: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    atr_period: int = 14
) -> np.ndarray:
    """
    Aceleración de Segundo Orden del MACD Normalizada por Volatilidad:
    ΔHist_norm = (Histogram_t - Histogram_{t-1}) / ATR_t
    Elimina la multicolinealidad lineal y el retardo del cruce, midiendo la segunda derivada.
    """
    n = len(close)
    a_fast = 2.0 / (fast_period + 1.0)
    a_slow = 2.0 / (slow_period + 1.0)
    a_sig = 2.0 / (signal_period + 1.0)

    ema_f = np.empty(n, dtype=np.float64)
    ema_s = np.empty(n, dtype=np.float64)
    ema_f[0] = close[0]
    ema_s[0] = close[0]

    for i in range(1, n):
        ema_f[i] = a_fast * close[i] + (1.0 - a_fast) * ema_f[i - 1]
        ema_s[i] = a_slow * close[i] + (1.0 - a_slow) * ema_s[i - 1]

    macd_line = ema_f - ema_s
    signal_line = np.empty(n, dtype=np.float64)
    signal_line[0] = macd_line[0]
    for i in range(1, n):
        signal_line[i] = a_sig * macd_line[i] + (1.0 - a_sig) * signal_line[i - 1]

    hist = macd_line - signal_line
    atr = calc_atr_fast(high, low, close, atr_period)

    diff_norm = np.full(n, np.nan, dtype=np.float64)
    for i in range(1, n):
        denom = atr[i]
        if denom > 1e-12:
            diff_norm[i] = (hist[i] - hist[i - 1]) / denom
        else:
            diff_norm[i] = 0.0
    return diff_norm


@njit(fastmath=True)
def calc_order_flow_imbalance_proxy(
    open_p: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    volume: np.ndarray
) -> np.ndarray:
    """
    Proxy no lineal de Order Flow Imbalance (OFI) basado en microestructura de vela:
    Mide la presión direccional neta de volumen en relación con la dispersión intraintérvalo.
    """
    n = len(close)
    ofi = np.empty(n, dtype=np.float64)
    for i in range(n):
        rng = high[i] - low[i]
        if rng > 1e-12:
            ofi[i] = volume[i] * ((close[i] - open_p[i]) / rng)
        else:
            ofi[i] = 0.0
    return ofi


@njit(fastmath=True)
def calc_shannon_entropy_fast(close: np.ndarray, window: int = 48, bins: int = 10) -> np.ndarray:
    """
    Entropía de Shannon Normalizada sobre retornos logarítmicos [0.0, 1.0].
    H_norm <= 0.75: Estructura no aleatoria detectable.
    H_norm > 0.84: Régimen de ruido browniano caótico puro.
    """
    n = len(close)
    h_norm = np.full(n, np.nan, dtype=np.float64)
    if n <= window:
        return h_norm

    log_rets = np.zeros(n, dtype=np.float64)
    for i in range(1, n):
        prev = close[i - 1]
        if prev > 1e-12:
            log_rets[i] = np.log(close[i] / prev)

    max_ent = np.log2(float(bins))
    counts = np.zeros(bins, dtype=np.float64)

    for i in range(window, n):
        # Encontrar min y max de la ventana para bins equidistantes
        w_min = 1e30
        w_max = -1e30
        for j in range(i - window + 1, i + 1):
            val = log_rets[j]
            if val < w_min:
                w_min = val
            if val > w_max:
                w_max = val

        diff = w_max - w_min
        if diff < 1e-12:
            h_norm[i] = 0.0
            continue

        for b in range(bins):
            counts[b] = 0.0

        for j in range(i - window + 1, i + 1):
            val = log_rets[j]
            bin_idx = int((val - w_min) / diff * bins)
            if bin_idx >= bins:
                bin_idx = bins - 1
            counts[bin_idx] += 1.0

        ent = 0.0
        inv_w = 1.0 / window
        for b in range(bins):
            c = counts[b]
            if c > 0:
                p = c * inv_w
                ent -= p * np.log2(p)

        h_norm[i] = ent / max_ent

    return h_norm
