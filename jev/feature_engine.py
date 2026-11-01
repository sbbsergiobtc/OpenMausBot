"""Capa 2: Motor de Características (Feature Engine).

Transforma los datos de velas en bruto en un estado de mercado estructurado (MarketState),
integrando indicadores clásicos (SMA/EMA) junto con la Entropía de Shannon para la
detección de orden vs ruido y transiciones de régimen.
"""

from typing import List, Optional, Tuple
import logging
import math
import numpy as np
import pandas as pd

from .models import (
    Candle,
    MarketState,
    TechnicalIndicators,
    PriceStructure,
    MarketRegime,
    ShannonEntropyMetrics,
    EntropyRegime,
    StrategicBias,
    AdaptiveStrategy
)
from .exceptions import FeatureExtractionError

logger = logging.getLogger("jev.feature_engine")


class FeatureEngine:
    """Motor de cálculo de indicadores técnicos, entropía de información y régimen adaptativo."""

    def __init__(
        self,
        bb_period: int = 20,
        bb_std: float = 2.0,
        entropy_window: int = 50,
        entropy_bins: int = 8
    ):
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.entropy_window = entropy_window
        self.entropy_bins = entropy_bins

    def compute_market_state(
        self,
        symbol: str,
        timeframe: str,
        candles: List[Candle],
        macro_notes: Optional[str] = None
    ) -> MarketState:
        """Procesa una secuencia de velas OHLCV y construye el MarketState estructurado."""
        if len(candles) < 55:
            raise FeatureExtractionError(
                f"Se requieren al menos 55 velas para calcular EMA-50 y Entropía (recibidas: {len(candles)})."
            )

        try:
            df = pd.DataFrame([
                {
                    "timestamp": c.timestamp,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume
                }
                for c in candles
            ])

            close = df["close"]
            high = df["high"]
            low = df["low"]
            volume = df["volume"]

            # 1. Medias Móviles y Tendencia
            sma_20 = float(close.rolling(window=20).mean().iloc[-1])
            ema_20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
            ema_50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
            
            # EMA 200 (si hay suficientes velas, sino fallback a ema disponible o ponderada)
            if len(close) >= 200:
                ema_200 = float(close.ewm(span=200, adjust=False).mean().iloc[-1])
            else:
                ema_200 = float(close.ewm(span=len(close), adjust=False).mean().iloc[-1])

            # 2. RSI (14)
            delta = close.diff()
            gain = (delta.where(delta > 0, 0.0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
            rs = gain / (loss.replace(0, np.nan))
            rsi_series = 100 - (100 / (1 + rs))
            rsi_14 = float(rsi_series.fillna(50.0).iloc[-1])

            # 3. MACD (12, 26, 9)
            ema_12 = close.ewm(span=12, adjust=False).mean()
            ema_26 = close.ewm(span=26, adjust=False).mean()
            macd_line_series = ema_12 - ema_26
            macd_signal_series = macd_line_series.ewm(span=9, adjust=False).mean()
            macd_hist_series = macd_line_series - macd_signal_series

            macd_line = float(macd_line_series.iloc[-1])
            macd_signal = float(macd_signal_series.iloc[-1])
            macd_hist = float(macd_hist_series.iloc[-1])

            # 4. Bandas de Bollinger (20, 2.0)
            rolling_mean_20 = close.rolling(window=self.bb_period).mean()
            rolling_std_20 = close.rolling(window=self.bb_period).std()
            bb_middle = float(rolling_mean_20.iloc[-1])
            bb_upper = float((rolling_mean_20 + (rolling_std_20 * self.bb_std)).iloc[-1])
            bb_lower = float((rolling_mean_20 - (rolling_std_20 * self.bb_std)).iloc[-1])

            # 5. ATR (14)
            tr1 = high - low
            tr2 = (high - close.shift(1)).abs()
            tr3 = (low - close.shift(1)).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr_14 = float(tr.rolling(window=14).mean().iloc[-1])

            # 6. ADX (14)
            up_move = high - high.shift(1)
            down_move = low.shift(1) - low
            plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
            minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
            
            tr_smooth = tr.rolling(window=14).mean()
            plus_di = 100 * (pd.Series(plus_dm).rolling(window=14).mean() / tr_smooth.replace(0, np.nan))
            minus_di = 100 * (pd.Series(minus_dm).rolling(window=14).mean() / tr_smooth.replace(0, np.nan))
            dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)).fillna(0)
            adx_14 = float(dx.rolling(window=14).mean().fillna(20.0).iloc[-1])

            # 7. Volumen & OBV
            vol_sma_20 = volume.rolling(window=20).mean().iloc[-1]
            volume_ratio_20 = float(volume.iloc[-1] / vol_sma_20) if vol_sma_20 > 0 else 1.0

            obv_direction = np.sign(close.diff().fillna(0))
            obv_series = (obv_direction * volume).cumsum()
            obv = float(obv_series.iloc[-1])

            # 8. CÁLCULO DE ENTROPÍA DE SHANNON (Distribución de Retornos Logarítmicos)
            entropy_metrics = self._calculate_shannon_entropy(close)

            indicators = TechnicalIndicators(
                sma_20=sma_20,
                ema_20=ema_20,
                ema_50=ema_50,
                ema_200=ema_200,
                rsi_14=rsi_14,
                adx_14=adx_14,
                macd_line=macd_line,
                macd_signal=macd_signal,
                macd_hist=macd_hist,
                bb_upper=bb_upper,
                bb_middle=bb_middle,
                bb_lower=bb_lower,
                atr_14=atr_14,
                obv=obv,
                volume_ratio_20=volume_ratio_20,
                entropy=entropy_metrics
            )

            # 9. Estructura de Precios (Swings y Distancias)
            current_price = float(close.iloc[-1])
            recent_highs = high.tail(24)
            recent_lows = low.tail(24)
            swing_high = float(recent_highs.max())
            swing_low = float(recent_lows.min())

            dist_res_pct = ((swing_high - current_price) / current_price) * 100.0
            dist_sup_pct = ((current_price - swing_low) / current_price) * 100.0

            structure = PriceStructure(
                recent_swing_high=swing_high,
                recent_swing_low=swing_low,
                distance_to_resistance_pct=dist_res_pct,
                distance_to_support_pct=dist_sup_pct,
            )

            # 10. Detección Integral de Régimen, Sesgo Estratégico y Adaptación
            regime, bias, recommended_strat = self._determine_market_regime_and_bias(
                current_price=current_price,
                ind=indicators,
                ent=entropy_metrics
            )

            logger.debug(
                "MarketState generado para %s [%s]: Precio=%.2f, Régimen=%s, Sesgo=%s, H_norm=%.3f, ADX=%.1f",
                symbol, timeframe, current_price, regime.value, bias.value, entropy_metrics.normalized_entropy, indicators.adx_14
            )

            return MarketState(
                symbol=symbol,
                timeframe=timeframe,
                current_price=current_price,
                regime=regime,
                strategic_bias=bias,
                recommended_strategy=recommended_strat,
                indicators=indicators,
                structure=structure,
                raw_candles_count=len(candles),
                macro_notes=macro_notes
            )

        except Exception as e:
            raise FeatureExtractionError(f"Error extrayendo características de {symbol}: {e}") from e

    def _calculate_shannon_entropy(self, close_series: pd.Series) -> ShannonEntropyMetrics:
        """
        Calcula la Entropía de Shannon de los retornos logarítmicos:
        H(X) = - sum(p_i * log2(p_i))
        H_norm = H(X) / log2(k) donde k es el número de particiones/bins.
        """
        log_returns = np.log(close_series / close_series.shift(1)).dropna()

        if len(log_returns) < self.entropy_window:
            window_returns = log_returns
        else:
            window_returns = log_returns.tail(self.entropy_window)

        # 1. Entropía ventana benchmark (últimas 50 barras)
        h_bench, h_norm_bench = self._compute_binned_entropy(window_returns, bins=self.entropy_bins)

        # 2. Entropía ventana corta / reciente (últimas 14 barras)
        recent_returns = log_returns.tail(14)
        _, h_norm_recent = self._compute_binned_entropy(recent_returns, bins=self.entropy_bins)

        # Delta de entropía: un aumento fuerte de entropía reciente (> +0.10) indica transición hacia desorden/ruido
        entropy_delta = float(h_norm_recent - h_norm_bench)
        regime_shift_detected = abs(entropy_delta) >= 0.12

        # Clasificación del régimen entrópico
        if h_norm_bench < 0.72:
            entropy_regime = EntropyRegime.LOW_ENTROPY_STRUCTURED
        elif h_norm_bench <= 0.84:
            entropy_regime = EntropyRegime.MEDIUM_ENTROPY_OSCILLATORY
        else:
            entropy_regime = EntropyRegime.HIGH_ENTROPY_CHAOS

        predictability_score = float(max(0.0, min(1.0, 1.0 - h_norm_bench)))

        return ShannonEntropyMetrics(
            shannon_entropy=round(float(h_bench), 4),
            normalized_entropy=round(float(h_norm_bench), 4),
            entropy_delta_14=round(entropy_delta, 4),
            predictability_score=round(predictability_score, 4),
            entropy_regime=entropy_regime,
            regime_shift_detected=regime_shift_detected
        )

    def _compute_binned_entropy(self, returns: pd.Series, bins: int = 8) -> Tuple[float, float]:
        """Calcula H(X) y H_norm discretizando los retornos en k cuantiles/bins equiprobables a priori."""
        if len(returns) < 5 or returns.std() == 0:
            return 0.0, 0.0

        counts, _ = np.histogram(returns, bins=bins)
        total = np.sum(counts)
        if total == 0:
            return 0.0, 0.0

        probabilities = counts / total
        # H(X) = -sum(p * log2(p)) para p > 0
        entropy = -np.sum([p * np.log2(p) for p in probabilities if p > 0])
        max_entropy = np.log2(bins)
        normalized_entropy = float(entropy / max_entropy) if max_entropy > 0 else 0.0

        return float(entropy), float(min(1.0, normalized_entropy))

    def _determine_market_regime_and_bias(
        self,
        current_price: float,
        ind: TechnicalIndicators,
        ent: ShannonEntropyMetrics
    ) -> Tuple[MarketRegime, StrategicBias, AdaptiveStrategy]:
        """
        Detección confluente de Régimen y Adaptación Dinámica:
        Combina la estructura geométrica de EMAs (20/50/200) y ADX con la Entropía de Shannon.
        """
        # 1. Filtro de Caos / Ruido Blanco Puro (Entropía Extrema)
        # Si la entropía supera 0.85, el mercado es ruido puro (Browniano). Cualquier tendencia aparente es un espejismo.
        if ent.entropy_regime == EntropyRegime.HIGH_ENTROPY_CHAOS:
            return (
                MarketRegime.HIGH_ENTROPY_NOISE,
                StrategicBias.CAPITAL_PRESERVATION,
                AdaptiveStrategy.DEFENSIVE_CASH
            )

        # 2. Alerta de Transición de Régimen (Bifurcación / Shock de Información)
        if ent.regime_shift_detected and ent.entropy_delta_14 > 0.12:
            return (
                MarketRegime.REGIME_TRANSITION,
                StrategicBias.REGIME_TRANSITION_ALERT,
                AdaptiveStrategy.DEFENSIVE_CASH
            )

        # 3. Tendencia con Bajo Nivel de Ruido (Estructura Ordenada y Persistente)
        is_trending_adx = ind.adx_14 >= 24.0
        is_structured = ent.normalized_entropy < 0.80

        if is_trending_adx and is_structured:
            # Estructura Alcista: Precio > EMA-50 > EMA-200
            if current_price > ind.ema_50 and ind.ema_50 > ind.ema_200:
                # Si el precio retrocede cerca de EMA-20: Adaptar a Pullback
                is_pullback = abs(current_price - ind.ema_20) <= (1.2 * ind.atr_14)
                strat = AdaptiveStrategy.TREND_PULLBACK if is_pullback else AdaptiveStrategy.TREND_BREAKOUT
                return (
                    MarketRegime.TRENDING_BULLISH,
                    StrategicBias.BULLISH_TREND,
                    strat
                )
            # Estructura Bajista: Precio < EMA-50 < EMA-200
            elif current_price < ind.ema_50 and ind.ema_50 < ind.ema_200:
                is_pullback = abs(current_price - ind.ema_20) <= (1.2 * ind.atr_14)
                strat = AdaptiveStrategy.TREND_PULLBACK if is_pullback else AdaptiveStrategy.TREND_BREAKOUT
                return (
                    MarketRegime.TRENDING_BEARISH,
                    StrategicBias.BEARISH_TREND,
                    strat
                )

        # 4. Rango Oscilatorio (Entropía Moderada + ADX < 24)
        bb_width_pct = ((ind.bb_upper - ind.bb_lower) / ind.bb_middle) * 100.0 if ind.bb_middle > 0 else 0
        if bb_width_pct > 5.0:
            regime = MarketRegime.RANGING_HIGH_VOLATILITY
        else:
            regime = MarketRegime.RANGING_LOW_VOLATILITY

        return (
            regime,
            StrategicBias.MEAN_REVERSION_RANGE,
            AdaptiveStrategy.MEAN_REVERSION_BANDS
        )
