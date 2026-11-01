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
from .symbolic_engine import (
    ts_rank,
    ts_corr,
    calc_diff_hist_norm,
    calc_order_flow_imbalance_proxy,
    calc_shannon_entropy_fast
)
from .hybrid_signals import HybridSignalFactory, calc_atr_fast
from .simulator import load_market_data, simulate_signals_numba, extract_candidate_trade_pnls
from .metrics import calculate_deflated_sharpe_ratio, run_monte_carlo_bootstrap, audit_candidate_robustness
from .agent_protocol import compress_candidate_context, run_skeptic_destructive_stress
from .auto_deployer import auto_deploy_strategy, dispatch_governance_rejection_report

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
    "ts_rank",
    "ts_corr",
    "calc_diff_hist_norm",
    "calc_order_flow_imbalance_proxy",
    "calc_shannon_entropy_fast",
    "HybridSignalFactory",
    "calc_atr_fast",
    "calculate_deflated_sharpe_ratio",
    "run_monte_carlo_bootstrap",
    "audit_candidate_robustness",
    "compress_candidate_context",
    "run_skeptic_destructive_stress",
    "auto_deploy_strategy",
    "dispatch_governance_rejection_report",
]
