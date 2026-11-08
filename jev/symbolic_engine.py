"""
Módulo de Álgebra Simbólica Vectorizada para Minería de Alfas No Lineales
AlgrokQuant · Jev Quantitative Engine

Implementa operadores de series temporales (WorldQuant Formulaic Alphas)
y transformaciones de microestructura compiladas en Numba y NumPy.
Diseñado para evaluación masiva de alto rendimiento (< 50 ms en 100.000 barras).
"""

import numpy as np
import pandas as pd
from typing import Tuple, Union

try:
    from numba import njit, prange
except ImportError:
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    prange = range


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


# ==============================================================================
# PRIMITIVAS AVANZADAS DE RÉGIMEN Y MICROESTRUCTURA (INTEGRACIÓN STRATOS/TECHAIN)
# ==============================================================================

@njit(fastmath=True)
def calc_adx_fast(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int = 14
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Wilder's ADX(14), +DI y -DI 100% causales compilados en Numba JIT.
    Indicador Tier S de Puerta de Régimen (ADX > 25 Tendencia Fuerte, ADX < 20 Rango/Compresión).
    """
    n = len(close)
    adx = np.full(n, 20.0, dtype=np.float64)
    plus_di = np.full(n, 20.0, dtype=np.float64)
    minus_di = np.full(n, 20.0, dtype=np.float64)
    if n <= period:
        return adx, plus_di, minus_di

    alpha = 1.0 / float(period)
    tr_s = max(1e-8, high[0] - low[0])
    pdm_s = 0.0
    mdm_s = 0.0
    dx_s = 20.0

    for i in range(1, n):
        up_move = high[i] - high[i - 1]
        dn_move = low[i - 1] - low[i]

        pdm = up_move if (up_move > dn_move and up_move > 0.0) else 0.0
        mdm = dn_move if (dn_move > up_move and dn_move > 0.0) else 0.0

        hl = high[i] - low[i]
        hc = abs(high[i] - close[i - 1])
        lc = abs(low[i] - close[i - 1])
        tr = max(hl, max(hc, lc))

        tr_s = alpha * tr + (1.0 - alpha) * tr_s
        pdm_s = alpha * pdm + (1.0 - alpha) * pdm_s
        mdm_s = alpha * mdm + (1.0 - alpha) * mdm_s

        denom_tr = max(1e-9, tr_s)
        pdi = 100.0 * (pdm_s / denom_tr)
        mdi = 100.0 * (mdm_s / denom_tr)
        plus_di[i] = pdi
        minus_di[i] = mdi

        sum_di = pdi + mdi
        dx = 100.0 * abs(pdi - mdi) / sum_di if sum_di > 1e-9 else 0.0
        dx_s = alpha * dx + (1.0 - alpha) * dx_s
        adx[i] = dx_s

    return adx, plus_di, minus_di


@njit(fastmath=True)
def calc_atr_ratio_fast(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    fast_period: int = 14,
    slow_period: int = 100
) -> np.ndarray:
    """
    Ratio de Volatilidad Relativa: ATR(fast) / ATR(slow).
    - < 0.75: Compresión / Squeeze de volatilidad pre-ruptura.
    - 0.75 a 1.35: Volatilidad normal operativa.
    - > 1.50: Expansión / Shock de volatilidad.
    """
    atr_f = calc_atr_fast(high, low, close, fast_period)
    atr_s = calc_atr_fast(high, low, close, slow_period)
    n = len(close)
    out = np.ones(n, dtype=np.float64)
    for i in range(n):
        if atr_s[i] > 1e-12:
            out[i] = atr_f[i] / atr_s[i]
    return out


@njit(fastmath=True)
def calc_fvg_imbalance_fast(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    atr: np.ndarray,
    min_atr_mult: float = 0.40
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detector Booleano Vectorizado de Fair Value Gap (Ineficiencia de 3 velas cerradas i-2, i-1, i)
    100% libre de look-ahead bias (evaluado estrictamente al cierre de la barra i).
    - bull_fvg[i]: low[i] - high[i-2] >= min_atr_mult * atr[i] y vela central alcista.
    - bear_fvg[i]: low[i-2] - high[i] >= min_atr_mult * atr[i] y vela central bajista.
    """
    n = len(close)
    bull_fvg = np.zeros(n, dtype=np.bool_)
    bear_fvg = np.zeros(n, dtype=np.bool_)
    if n < 3:
        return bull_fvg, bear_fvg

    for i in range(2, n):
        cur_atr = atr[i] if (not np.isnan(atr[i]) and atr[i] > 1e-12) else close[i] * 0.005
        thresh = min_atr_mult * cur_atr
        gap_up = low[i] - high[i - 2]
        gap_dn = low[i - 2] - high[i]
        if gap_up >= thresh and close[i - 1] > close[i - 2]:
            bull_fvg[i] = True
        if gap_dn >= thresh and close[i - 1] < close[i - 2]:
            bear_fvg[i] = True

    return bull_fvg, bear_fvg


@njit(fastmath=True)
def classify_7_regimes_fast(
    close: np.ndarray,
    ema_200: np.ndarray,
    h_norm: np.ndarray,
    adx: np.ndarray,
    plus_di: np.ndarray,
    minus_di: np.ndarray,
    atr_ratio: np.ndarray
) -> np.ndarray:
    """
    Clasificador Determinista de los 7 Regímenes Canónicos de Mercado (0 a 6) en cada barra t:
    0 = STRONG_BULL          (ADX >= 25, +DI > -DI, Close >= EMA200)
    1 = STRONG_BEAR          (ADX >= 25, -DI > +DI, Close < EMA200)
    2 = WEAK_TREND           (20 <= ADX < 25 y H_norm <= 0.82)
    3 = RANGING_MEAN_REV     (ADX < 20, 0.75 <= ATR_Ratio <= 1.35, H_norm <= 0.80)
    4 = VOLATILITY_SQUEEZE   (ADX < 20, ATR_Ratio < 0.75)
    5 = VOLATILITY_EXPANSION (ATR_Ratio > 1.50 y H_norm <= 0.84)
    6 = HIGH_ENTROPY_SHOCK   (H_norm > 0.84 o ATR_Ratio > 2.20 -> Bloqueo Operativo)
    """
    n = len(close)
    regimes = np.full(n, 3, dtype=np.int32)
    for i in range(n):
        hn = h_norm[i] if not np.isnan(h_norm[i]) else 0.70
        ar = atr_ratio[i] if not np.isnan(atr_ratio[i]) else 1.0
        ax = adx[i]
        pdi = plus_di[i]
        mdi = minus_di[i]

        if hn > 0.84 or ar > 2.20:
            regimes[i] = 6  # HIGH_ENTROPY_SHOCK
        elif ar > 1.50:
            regimes[i] = 5  # VOLATILITY_EXPANSION
        elif ax >= 25.0:
            if pdi >= mdi and close[i] >= ema_200[i] * 0.995:
                regimes[i] = 0  # STRONG_BULL
            elif mdi > pdi and close[i] <= ema_200[i] * 1.005:
                regimes[i] = 1  # STRONG_BEAR
            else:
                regimes[i] = 2  # WEAK_TREND
        elif ax >= 20.0:
            regimes[i] = 2  # WEAK_TREND
        elif ar < 0.75:
            regimes[i] = 4  # VOLATILITY_SQUEEZE
        else:
            regimes[i] = 3  # RANGING_MEAN_REV

    return regimes


@njit(fastmath=True)
def classify_10_regimes_fast(
    close: np.ndarray,
    ema_50: np.ndarray,
    ema_200: np.ndarray,
    h_norm: np.ndarray,
    adx: np.ndarray,
    plus_di: np.ndarray,
    minus_di: np.ndarray,
    atr_ratio: np.ndarray,
    hurst: np.ndarray,
    robust_kurt: np.ndarray
) -> np.ndarray:
    """
    Clasificador Determinista de los 10 Regímenes Canónicos de Mercado (S0 a S9) en cada barra t (100% causal):
    0 = S0_STRONG_CLEAN_BULL       (ADX >= 25, +DI > -DI, Close >= EMA50 >= EMA200, H_norm <= 0.78, Kurt_rob <= 3.20)
    1 = S1_MODERATE_BULL_TREND     ((20 <= ADX < 25 o Hurst >= 0.55), +DI >= -DI, Close >= EMA200, ATR_Ratio <= 1.50)
    2 = S2_BULL_VOLATILITY_CLIMAX  (+DI > -DI, Close > EMA50, pero ATR_Ratio > 1.50 o Kurt_rob > 3.20)
    3 = S3_STRONG_CLEAN_BEAR       (ADX >= 25, -DI > +DI, Close <= EMA50 < EMA200, H_norm <= 0.78, Kurt_rob <= 3.20)
    4 = S4_MODERATE_BEAR_TREND     ((20 <= ADX < 25 o Hurst >= 0.55), -DI > +DI, Close < EMA200, ATR_Ratio <= 1.50)
    5 = S5_BEAR_PANIC_CAPITULATION (-DI > +DI, Close < EMA50, ATR_Ratio > 1.50 o Kurt_rob > 3.20)
    6 = S6_CLEAN_MEAN_REVERSION    (ADX < 18, Hurst < 0.48, 0.75 <= ATR_Ratio <= 1.25, Kurt_rob <= 3.20)
    7 = S7_COMPRESSION_SQUEEZE     (ADX < 20, ATR_Ratio < 0.75, H_norm <= 0.80)
    8 = S8_CHOPPY_FAT_TAILS_RANGE  (Rango lateral sucio con Kurt_rob > 3.20 o 1.25 < ATR_Ratio <= 1.60)
    9 = S9_HIGH_ENTROPY_BLACKOUT   (H_norm > 0.84 o Delta_H > 0.12 o ATR_Ratio > 2.20 -> Bloqueo Operativo 0.00x)
    """
    n = len(close)
    regimes = np.full(n, 6, dtype=np.int32)
    for i in range(n):
        hn = h_norm[i] if not np.isnan(h_norm[i]) else 0.68
        prev_hn = h_norm[i - 14] if (i >= 14 and not np.isnan(h_norm[i - 14])) else hn
        delta_h = abs(hn - prev_hn)
        ar = atr_ratio[i] if not np.isnan(atr_ratio[i]) else 1.0
        ax = adx[i] if not np.isnan(adx[i]) else 20.0
        pdi = plus_di[i] if not np.isnan(plus_di[i]) else 20.0
        mdi = minus_di[i] if not np.isnan(minus_di[i]) else 20.0
        hu = hurst[i] if not np.isnan(hurst[i]) else 0.50
        rk = robust_kurt[i] if not np.isnan(robust_kurt[i]) else 2.80
        c = close[i]
        e50 = ema_50[i] if not np.isnan(ema_50[i]) else c
        e200 = ema_200[i] if not np.isnan(ema_200[i]) else c

        if hn > 0.84 or delta_h > 0.12 or ar > 2.20:
            regimes[i] = 9  # S9_HIGH_ENTROPY_BLACKOUT
        elif (ax >= 20.0 or hu >= 0.53) and pdi >= mdi and c >= e200 * 0.998:
            if ar > 1.50 or rk > 3.20:
                regimes[i] = 2  # S2_BULL_VOLATILITY_CLIMAX
            elif ax >= 25.0 and c >= e50 and e50 >= e200 and hn <= 0.78:
                regimes[i] = 0  # S0_STRONG_CLEAN_BULL
            else:
                regimes[i] = 1  # S1_MODERATE_BULL_TREND
        elif (ax >= 20.0 or hu >= 0.53) and mdi > pdi and c <= e200 * 1.002:
            if ar > 1.50 or rk > 3.20:
                regimes[i] = 5  # S5_BEAR_PANIC_CAPITULATION
            elif ax >= 25.0 and c <= e50 and e50 < e200 and hn <= 0.78:
                regimes[i] = 3  # S3_STRONG_CLEAN_BEAR
            else:
                regimes[i] = 4  # S4_MODERATE_BEAR_TREND
        else:
            if ar < 0.75 and hn <= 0.82:
                regimes[i] = 7  # S7_COMPRESSION_SQUEEZE
            elif rk > 3.20 or ar > 1.25:
                regimes[i] = 8  # S8_CHOPPY_FAT_TAILS_RANGE
            elif ax < 18.5 and hu < 0.49:
                regimes[i] = 6  # S6_CLEAN_MEAN_REVERSION
            else:
                regimes[i] = 6  # S6_CLEAN_MEAN_REVERSION (Default Lateral Limpio)

    return regimes


