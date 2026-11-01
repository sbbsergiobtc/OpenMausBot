"""Capa 5: Ejecución y Bucle de Mejora (Execution & Feedback Loop).

Envío de órdenes autorizadas al broker (Paper/Live) e integración del bucle continuo:
TRADE -> MEASURE -> ANALYZE -> IMPROVE.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
import json
import logging
import uuid

from .models import OrderIntent, ExecutionReport, ExecutionStatus, SignalDirection
from .exceptions import ExecutionError

logger = logging.getLogger("jev.execution")


class ValidationPhase(str, Enum):
    BACKTESTING = "BACKTESTING"
    OUT_OF_SAMPLE = "OUT_OF_SAMPLE"
    PAPER_TRADING = "PAPER_TRADING"
    LIVE_SMALL = "LIVE_SMALL"


class BaseExecutionHandler(ABC):
    """Interfaz abstracta para el manejador de ejecución de órdenes."""

    @abstractmethod
    def execute_order(self, intent: OrderIntent) -> ExecutionReport:
        """Enruta y ejecuta la orden autorizada."""
        pass


class PaperExecutionHandler(BaseExecutionHandler):
    """Ejecutor de Paper Trading de alta fidelidad con simulación de fricciones reales."""

    def __init__(
        self,
        base_fee_pct: float = 0.0005,       # 0.05% comisión taker
        simulated_slippage_pct: float = 0.0002, # 0.02% slippage medio
        trades_log_file: Optional[str] = None
    ):
        self.base_fee_pct = base_fee_pct
        self.simulated_slippage_pct = simulated_slippage_pct
        self.trades_log_file = Path(trades_log_file) if trades_log_file else None
        if self.trades_log_file:
            self.trades_log_file.parent.mkdir(parents=True, exist_ok=True)

    def execute_order(self, intent: OrderIntent) -> ExecutionReport:
        try:
            logger.info(
                "Enrutando orden PAPER: %s %s (Qty: %.4f @ ~%.2f | SL: %.2f | TP: %s)",
                intent.direction.value, intent.symbol, intent.quantity,
                intent.entry_price, intent.stop_loss, intent.take_profit
            )

            # Simulación de deslizamiento (desfavorable al trader)
            slippage_mult = (1.0 + self.simulated_slippage_pct) if intent.direction == SignalDirection.LONG else (1.0 - self.simulated_slippage_pct)
            filled_price = intent.entry_price * slippage_mult
            slippage_amount = abs(filled_price - intent.entry_price)

            trade_notional = filled_price * intent.quantity
            fee_paid = trade_notional * self.base_fee_pct

            order_id = f"HL-PAPER-{uuid.uuid4().hex[:8].upper()}"

            report = ExecutionReport(
                order_id=order_id,
                symbol=intent.symbol,
                status=ExecutionStatus.FILLED,
                filled_price=round(filled_price, 2),
                filled_quantity=intent.quantity,
                fee_paid=round(fee_paid, 4),
                slippage=round(slippage_amount, 4),
                execution_time=datetime.utcnow(),
                raw_exchange_response={
                    "exchange": "Hyperliquid Paper L1",
                    "order_id": order_id,
                    "type": intent.order_type.value,
                    "side": "BUY" if intent.direction == SignalDirection.LONG else "SELL",
                    "leverage": intent.leverage,
                    "simulated": True
                }
            )

            self._log_trade_journal(intent, report)
            logger.info("✅ Orden %s EJECUTADA con éxito @ %.2f (Comisión: $%.4f)", order_id, filled_price, fee_paid)
            return report

        except Exception as e:
            logger.error("Error crítico ejecutando orden para %s: %s", intent.symbol, e)
            raise ExecutionError(f"Fallo en la capa de ejecución para {intent.symbol}: {e}") from e

    def _log_trade_journal(self, intent: OrderIntent, report: ExecutionReport) -> None:
        """Registra la operación en el libro diario de operaciones para retroalimentación."""
        if not self.trades_log_file:
            return

        record = {
            "timestamp": report.execution_time.isoformat(),
            "order_id": report.order_id,
            "symbol": report.symbol,
            "direction": intent.direction.value,
            "filled_price": report.filled_price,
            "quantity": report.filled_quantity,
            "notional_usdc": round(report.filled_price * report.filled_quantity, 2),
            "stop_loss": intent.stop_loss,
            "take_profit": intent.take_profit,
            "fee_paid": report.fee_paid,
            "slippage": report.slippage,
            "leverage": intent.leverage
        }

        with open(self.trades_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


class ContinuousImprovementLoop:
    """Implementa el bucle de optimización sistemática: TRADE -> MEASURE -> ANALYZE -> IMPROVE."""

    def __init__(self, current_phase: ValidationPhase = ValidationPhase.PAPER_TRADING):
        self.current_phase = current_phase
        self.metrics_history: List[Dict] = []

    def log_trade_metric(self, pnl: float, r_multiple: float, duration_hours: float, regime: str) -> None:
        """Registra la métrica post-trade para el análisis de sesgos y rendimiento."""
        self.metrics_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "pnl": pnl,
            "r_multiple": r_multiple,
            "duration_hours": duration_hours,
            "market_regime": regime
        })

    def analyze_performance(self) -> Dict[str, float]:
        """Calcula métricas clave para decidir si el sistema puede avanzar de fase."""
        if not self.metrics_history:
            return {"total_trades": 0}

        pnls = [m["pnl"] for m in self.metrics_history]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]

        win_rate = (len(wins) / len(pnls)) * 100 if pnls else 0.0
        profit_factor = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else (999.0 if wins else 0.0)

        return {
            "total_trades": len(pnls),
            "win_rate_pct": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "net_pnl": round(sum(pnls), 2)
        }

    def evaluate_phase_promotion(self) -> bool:
        """Verifica si el sistema cumple los criterios cuantitativos para pasar a la siguiente fase."""
        perf = self.analyze_performance()
        if self.current_phase == ValidationPhase.PAPER_TRADING:
            # Requisito para pasar a Live Small: Mínimo 30 trades en paper, PF >= 1.30, Net PnL > 0
            if perf["total_trades"] >= 30 and perf["profit_factor"] >= 1.30 and perf["net_pnl"] > 0:
                logger.info("Promoción aprobada de PAPER_TRADING a LIVE_SMALL")
                return True
        return False
