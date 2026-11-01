"""Paquete modular Jev: Arquitectura Cuantitativa de 5 Capas.
La IA decide (probabilística) y el código controla (determinista).
"""

from .models import (
    Candle,
    TechnicalIndicators,
    ShannonEntropyMetrics,
    EntropyRegime,
    StrategicBias,
    AdaptiveStrategy,
    PriceStructure,
    MarketState,
    MarketRegime,
    SignalDirection,
    AIDecision,
    RiskApproval,
    OrderIntent,
    ExecutionReport,
    ExecutionStatus,
    OrderType
)
from .exceptions import (
    JevError,
    DataIngestionError,
    FeatureExtractionError,
    AIDecisionError,
    RiskValidationError,
    KillSwitchTriggeredError,
    ExecutionError
)
from .market_data import BaseMarketDataIngestion, CSVMarketDataIngestion, SimulatedRealtimeDataIngestion
from .feature_engine import FeatureEngine
from .decision_layer import BaseDecisionEngine, LLMStructuredDecisionEngine, GeminiDecisionEngine, PromptTemplateManager
from .risk_engine import DeterministicRiskEngine
from .execution_layer import BaseExecutionHandler, PaperExecutionHandler, ContinuousImprovementLoop, ValidationPhase
from .orchestrator import JevTradingSystem
from .screener import JevScreener

__all__ = [
    "Candle",
    "TechnicalIndicators",
    "ShannonEntropyMetrics",
    "EntropyRegime",
    "StrategicBias",
    "AdaptiveStrategy",
    "PriceStructure",
    "MarketState",
    "MarketRegime",
    "SignalDirection",
    "AIDecision",
    "RiskApproval",
    "OrderIntent",
    "ExecutionReport",
    "ExecutionStatus",
    "OrderType",
    "JevError",
    "DataIngestionError",
    "FeatureExtractionError",
    "AIDecisionError",
    "RiskValidationError",
    "KillSwitchTriggeredError",
    "ExecutionError",
    "BaseMarketDataIngestion",
    "CSVMarketDataIngestion",
    "SimulatedRealtimeDataIngestion",
    "FeatureEngine",
    "BaseDecisionEngine",
    "LLMStructuredDecisionEngine",
    "GeminiDecisionEngine",
    "PromptTemplateManager",
    "DeterministicRiskEngine",
    "BaseExecutionHandler",
    "PaperExecutionHandler",
    "ContinuousImprovementLoop",
    "ValidationPhase",
    "JevTradingSystem",
    "JevScreener",
]
