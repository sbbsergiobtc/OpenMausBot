"""Modelos de datos y estructuras fuertemente tipadas para el sistema Jev."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class SignalDirection(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NO_TRADE = "NO_TRADE"


class MarketRegime(str, Enum):
    TRENDING_BULLISH = "TRENDING_BULLISH"
    TRENDING_BEARISH = "TRENDING_BEARISH"
    RANGING_LOW_VOLATILITY = "RANGING_LOW_VOLATILITY"
    RANGING_HIGH_VOLATILITY = "RANGING_HIGH_VOLATILITY"
    REGIME_TRANSITION = "REGIME_TRANSITION"
    HIGH_ENTROPY_NOISE = "HIGH_ENTROPY_NOISE"
    UNKNOWN = "UNKNOWN"


class EntropyRegime(str, Enum):
    LOW_ENTROPY_STRUCTURED = "LOW_ENTROPY_STRUCTURED"       # < 0.72: Alto orden, tendencia persistente
    MEDIUM_ENTROPY_OSCILLATORY = "MEDIUM_ENTROPY_OSCILLATORY" # 0.72 - 0.84: Rango / reversión
    HIGH_ENTROPY_CHAOS = "HIGH_ENTROPY_CHAOS"                 # > 0.84: Ruido blanco, desorden puro


class StrategicBias(str, Enum):
    BULLISH_TREND = "BULLISH_TREND"
    BEARISH_TREND = "BEARISH_TREND"
    MEAN_REVERSION_RANGE = "MEAN_REVERSION_RANGE"
    REGIME_TRANSITION_ALERT = "REGIME_TRANSITION_ALERT"
    CAPITAL_PRESERVATION = "CAPITAL_PRESERVATION"


class AdaptiveStrategy(str, Enum):
    TREND_PULLBACK = "TREND_PULLBACK"
    TREND_BREAKOUT = "TREND_BREAKOUT"
    MEAN_REVERSION_BANDS = "MEAN_REVERSION_BANDS"
    DEFENSIVE_CASH = "DEFENSIVE_CASH"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_MARKET = "STOP_MARKET"


class ExecutionStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class Candle:
    """Representación inmutable de una vela de mercado OHLCV."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self):
        if self.high < self.low:
            raise ValueError(f"High ({self.high}) no puede ser inferior a Low ({self.low})")
        if self.volume < 0:
            raise ValueError(f"El volumen no puede ser negativo ({self.volume})")


@dataclass(frozen=True)
class ShannonEntropyMetrics:
    """Métricas cuantitativas de la Entropía de Shannon sobre la distribución de retornos."""
    shannon_entropy: float           # H(X) en bits
    normalized_entropy: float        # H_norm en rango [0.0, 1.0] (1.0 = máxima incertidumbre/ruido blanco)
    entropy_delta_14: float          # Tasa de cambio de entropía reciente (positivo = pérdida de orden)
    predictability_score: float      # 1.0 - normalized_entropy (orden estadístico del mercado)
    entropy_regime: EntropyRegime    # Clasificación categórica del nivel de información
    regime_shift_detected: bool      # Alerta de bifurcación o cambio brusco en la estructura


@dataclass(frozen=True)
class TechnicalIndicators:
    """Valores de indicadores técnicos normalizados para el estado de mercado."""
    sma_20: float
    ema_20: float
    ema_50: float
    ema_200: float
    rsi_14: float
    adx_14: float
    macd_line: float
    macd_signal: float
    macd_hist: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    atr_14: float
    obv: float
    volume_ratio_20: float
    entropy: ShannonEntropyMetrics


@dataclass(frozen=True)
class PriceStructure:
    """Niveles estructurales clave de soporte y resistencia."""
    recent_swing_high: float
    recent_swing_low: float
    distance_to_resistance_pct: float
    distance_to_support_pct: float


@dataclass(frozen=True)
class MarketState:
    """Estado estructurado completo que se entrega a la Capa de Decisión de IA."""
    symbol: str
    timeframe: str
    current_price: float
    regime: MarketRegime
    strategic_bias: StrategicBias
    recommended_strategy: AdaptiveStrategy
    indicators: TechnicalIndicators
    structure: PriceStructure
    raw_candles_count: int
    macro_notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_ai_context(self) -> Dict[str, Any]:
        """Convierte el estado de mercado a un diccionario limpio y descriptivo para el prompt del LLM."""
        ind = self.indicators
        ent = ind.entropy
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "current_price": self.current_price,
            "market_regime": self.regime.value,
            "strategic_bias": self.strategic_bias.value,
            "recommended_strategy": self.recommended_strategy.value,
            "shannon_entropy_engine": {
                "normalized_entropy": round(ent.normalized_entropy, 3),
                "predictability_score": round(ent.predictability_score, 3),
                "entropy_delta_14": round(ent.entropy_delta_14, 4),
                "entropy_regime": ent.entropy_regime.value,
                "regime_shift_detected": ent.regime_shift_detected,
                "entropy_interpretation": (
                    "High Disorder / Pure Noise (Inhibit directional betting)" if ent.normalized_entropy > 0.84
                    else "Structured / Low Noise (High statistical persistence)" if ent.normalized_entropy < 0.72
                    else "Oscillatory / Moderate Noise"
                )
            },
            "trend_and_structure": {
                "ema_20": round(ind.ema_20, 2),
                "ema_50": round(ind.ema_50, 2),
                "ema_200": round(ind.ema_200, 2),
                "sma_20": round(ind.sma_20, 2),
                "price_vs_ema200": "ABOVE" if self.current_price > ind.ema_200 else "BELOW",
                "ema50_vs_ema200": "GOLDEN_STRUCTURE" if ind.ema_50 > ind.ema_200 else "DEATH_STRUCTURE"
            },
            "momentum_and_volatility": {
                "rsi_14": round(ind.rsi_14, 2),
                "adx_14": round(ind.adx_14, 2),
                "macd_histogram": round(ind.macd_hist, 4),
                "atr_14": round(ind.atr_14, 4),
                "bb_upper": round(ind.bb_upper, 4),
                "bb_lower": round(ind.bb_lower, 4),
                "volume_ratio_20": round(ind.volume_ratio_20, 2)
            },
            "price_structure": {
                "swing_high": self.structure.recent_swing_high,
                "swing_low": self.structure.recent_swing_low,
                "dist_to_resistance_pct": round(self.structure.distance_to_resistance_pct, 2),
                "dist_to_support_pct": round(self.structure.distance_to_support_pct, 2)
            },
            "context_notes": self.macro_notes or "No high-impact macro news flagged."
        }


@dataclass(frozen=True)
class AIDecision:
    """Salida estricta esperada de la Capa de Decisión de IA (Jev)."""
    signal: SignalDirection
    confidence: float
    entry_type: str
    adapted_strategy: str
    strategic_bias: str
    reason: str
    invalidation: str
    suggested_stop_loss: Optional[float] = None
    suggested_take_profit: Optional[float] = None


@dataclass(frozen=True)
class RiskApproval:
    """Dictamen determinista emitido por el Risk Engine."""
    approved: bool
    reason: str
    adjusted_position_size: float
    calculated_risk_amount: float
    validated_stop_loss: float
    validated_take_profit: Optional[float]
    leverage: float
    max_slippage_pct: float
    entropy_filter_passed: bool


@dataclass(frozen=True)
class OrderIntent:
    """Intención de orden autorizada lista para el módulo de ejecución."""
    symbol: str
    direction: SignalDirection
    order_type: OrderType
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: Optional[float]
    leverage: float
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class ExecutionReport:
    """Informe de ejecución y auditoría generado tras interactuar con el broker/simulador."""
    order_id: str
    symbol: str
    status: ExecutionStatus
    filled_price: float
    filled_quantity: float
    fee_paid: float
    slippage: float
    execution_time: datetime
    raw_exchange_response: Dict[str, Any]
