"""Orquestador Principal del Sistema de Trading Jev.

Coordina secuencialmente las 5 capas de la arquitectura:
1. Market Data -> 2. Feature Engine -> 3. Jev Decision -> 4. Risk Engine -> 5. Execution.
"""

from typing import Optional, Dict, Any
import logging

from .models import MarketState, AIDecision, RiskApproval, ExecutionReport
from .exceptions import (
    JevError,
    DataIngestionError,
    FeatureExtractionError,
    AIDecisionError,
    RiskValidationError,
    ExecutionError
)
from .market_data import BaseMarketDataIngestion
from .feature_engine import FeatureEngine
from .decision_layer import BaseDecisionEngine
from .risk_engine import DeterministicRiskEngine
from .execution_layer import BaseExecutionHandler, ContinuousImprovementLoop, ValidationPhase

logger = logging.getLogger("jev.orchestrator")


class JevTradingSystem:
    """Sistema modular de trading algorítmico guiado por IA con control de riesgo determinista."""

    def __init__(
        self,
        market_data: BaseMarketDataIngestion,
        feature_engine: FeatureEngine,
        decision_layer: BaseDecisionEngine,
        risk_engine: DeterministicRiskEngine,
        execution_handler: BaseExecutionHandler,
        improvement_loop: Optional[ContinuousImprovementLoop] = None
    ):
        self.market_data = market_data
        self.feature_engine = feature_engine
        self.decision_layer = decision_layer
        self.risk_engine = risk_engine
        self.execution_handler = execution_handler
        self.improvement_loop = improvement_loop or ContinuousImprovementLoop(ValidationPhase.PAPER_TRADING)

    def process_symbol(
        self,
        symbol: str,
        timeframe: str,
        limit_candles: int = 250,
        macro_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ejecuta una iteración completa del pipeline de 5 capas para un activo determinado."""
        logger.info("================================================================================")
        logger.info("Iniciando ciclo Jev para %s en timeframe %s", symbol, timeframe)
        logger.info("================================================================================")

        pipeline_result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "status": "COMPLETED",
            "market_state": None,
            "ai_decision": None,
            "risk_approval": None,
            "execution_report": None,
            "error": None
        }

        try:
            # -----------------------------------------------------------------
            # CAPA 1: Recopilación de Datos de Mercado
            # -----------------------------------------------------------------
            logger.info("[Capa 1/5] Ingestando datos de mercado...")
            candles = self.market_data.fetch_recent_candles(symbol, timeframe, limit=limit_candles)
            logger.info("Datos ingeridos con éxito: %d velas disponibles.", len(candles))

            # -----------------------------------------------------------------
            # CAPA 2: Motor de Características (Feature Engine)
            # -----------------------------------------------------------------
            logger.info("[Capa 2/5] Extrayendo características y estado estructurado...")
            market_state = self.feature_engine.compute_market_state(
                symbol=symbol,
                timeframe=timeframe,
                candles=candles,
                macro_notes=macro_notes
            )
            pipeline_result["market_state"] = market_state
            logger.info(
                "Estado computado: Precio=%.2f | Régimen=%s | ADX=%.1f | RSI=%.1f",
                market_state.current_price,
                market_state.regime.value,
                market_state.indicators.adx_14,
                market_state.indicators.rsi_14
            )

            # -----------------------------------------------------------------
            # CAPA 3: Capa de Decisión de IA (Jev Decision Layer)
            # -----------------------------------------------------------------
            logger.info("[Capa 3/5] Consultando razonamiento a Jev Decision Layer...")
            ai_decision = self.decision_layer.evaluate(market_state)
            pipeline_result["ai_decision"] = ai_decision
            logger.info(
                "Propuesta de IA: Señal=%s, Confianza=%.2f, Tipo=%s | Motivo: %s",
                ai_decision.signal.value,
                ai_decision.confidence,
                ai_decision.entry_type,
                ai_decision.reason
            )

            # -----------------------------------------------------------------
            # CAPA 4: Motor de Riesgo Determinista (Risk Engine)
            # -----------------------------------------------------------------
            logger.info("[Capa 4/5] Auditando propuesta con el Motor de Riesgo Determinista...")
            risk_approval = self.risk_engine.evaluate_intent(market_state, ai_decision)
            pipeline_result["risk_approval"] = risk_approval

            if not risk_approval.approved:
                logger.warning("Propuesta RECHAZADA por Motor de Riesgo: %s", risk_approval.reason)
                return pipeline_result

            # Crear orden autorizada inmutable
            order_intent = self.risk_engine.create_authorized_order(
                state=market_state,
                decision=ai_decision,
                approval=risk_approval
            )

            # -----------------------------------------------------------------
            # CAPA 5: Ejecución y Bucle de Mejora
            # -----------------------------------------------------------------
            logger.info("[Capa 5/5] Enrutando orden autorizada a la Capa de Ejecución...")
            execution_report = self.execution_handler.execute_order(order_intent)
            pipeline_result["execution_report"] = execution_report
            logger.info("Ciclo Jev completado con éxito para %s. Orden: %s", symbol, execution_report.order_id)

            return pipeline_result

        except (DataIngestionError, FeatureExtractionError, AIDecisionError, RiskValidationError, ExecutionError) as jev_err:
            logger.error("Error operativo en Jev: %s", jev_err)
            pipeline_result["status"] = "FAILED"
            pipeline_result["error"] = str(jev_err)
            return pipeline_result
        except Exception as unhandled_err:
            logger.critical("Excepción no controlada en JevTradingSystem: %s", unhandled_err, exc_info=True)
            pipeline_result["status"] = "CRITICAL_ERROR"
            pipeline_result["error"] = str(unhandled_err)
            return pipeline_result
