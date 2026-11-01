"""Capa 4: Motor de Riesgo Determinista (Deterministic Risk Engine).

Filtro inquebrantable de seguridad en código algorítmico puro.
La IA propone; el código valida, recalcula el sizing exacto, aplica filtros de entropía o rechaza.
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime

from .models import (
    MarketState,
    AIDecision,
    RiskApproval,
    SignalDirection,
    OrderIntent,
    OrderType,
    EntropyRegime
)
from .exceptions import RiskValidationError, KillSwitchTriggeredError

logger = logging.getLogger("jev.risk_engine")


class DeterministicRiskEngine:
    """Motor de gestión de riesgo determinista sin sesgo probabilístico."""

    def __init__(
        self,
        account_capital: float = 1000.0,
        risk_per_trade_pct: float = 0.01,         # 1.0% de riesgo base por trade ($10 USDC)
        max_daily_loss_pct: float = 0.03,         # 3.0% de pérdida diaria ($30 USDC)
        max_portfolio_exposure_pct: float = 1.5,  # 150% de apalancamiento efectivo máximo total
        min_sl_distance_pct: float = 0.005,       # Mínimo 0.5% de distancia de SL
        max_sl_distance_pct: float = 0.040,       # Máximo 4.0% de distancia de SL
        max_allowed_entropy: float = 0.84,        # Límite máximo de Entropía de Shannon (0.84 = umbral de ruido blanco)
        max_active_positions: int = 2,
        max_consecutive_losses: int = 4,
        roundtrip_fee_pct: float = 0.0014         # 0.14% de comisiones + slippage buffer
    ):
        self.account_capital = account_capital
        self.risk_per_trade_pct = risk_per_trade_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_portfolio_exposure_pct = max_portfolio_exposure_pct
        self.min_sl_distance_pct = min_sl_distance_pct
        self.max_sl_distance_pct = max_sl_distance_pct
        self.max_allowed_entropy = max_allowed_entropy
        self.max_active_positions = max_active_positions
        self.max_consecutive_losses = max_consecutive_losses
        self.roundtrip_fee_pct = roundtrip_fee_pct

        # Estado del motor de riesgo
        self.current_daily_loss: float = 0.0
        self.active_positions: Dict[str, Dict] = {}
        self.consecutive_losses: int = 0
        self.kill_switch_active: bool = False
        self.kill_switch_reason: Optional[str] = None

    def trigger_kill_switch(self, reason: str) -> None:
        """Activa el Kill Switch de emergencia cerrando nuevas admisiones."""
        self.kill_switch_active = True
        self.kill_switch_reason = reason
        logger.critical("🚨 KILL SWITCH ACTIVADO: %s", reason)

    def reset_kill_switch(self) -> None:
        """Restablece manualmente el Kill Switch."""
        self.kill_switch_active = False
        self.kill_switch_reason = None
        logger.info("Kill switch restablecido por el operador.")

    def evaluate_intent(self, state: MarketState, decision: AIDecision) -> RiskApproval:
        """Valida deterministamente la propuesta de la IA y computa el dimensionamiento exacto."""
        logger.info("Risk Engine auditando propuesta IA para %s (%s)", state.symbol, decision.signal.value)

        # 1. Verificación del Kill Switch de Emergencia
        if self.kill_switch_active:
            reason = f"Kill Switch ACTIVO ({self.kill_switch_reason}). Se bloquea toda orden."
            logger.warning("Orden rechazada: %s", reason)
            return self._build_rejection(reason)

        # 2. Filtrado de Señales Nulas
        if decision.signal == SignalDirection.NO_TRADE:
            return self._build_rejection("La IA determinó NO_TRADE. Ninguna acción requerida.")

        # 3. FILTRO DETERMINISTA DE ENTROPÍA DE SHANNON (Hurdle de Información)
        ent = state.indicators.entropy
        if ent.normalized_entropy > self.max_allowed_entropy:
            reason = (
                f"Filtro de Entropía RECHAZADO: H_norm={ent.normalized_entropy:.3f} > {self.max_allowed_entropy:.2f}. "
                "Mercado en régimen de caos/ruido blanco. Prohibida la entrada determinista."
            )
            logger.warning("Orden rechazada por Risk Engine: %s", reason)
            return self._build_rejection(reason)

        if ent.regime_shift_detected and ent.entropy_delta_14 > 0.12:
            reason = f"Alerta de transición de régimen (Delta H={ent.entropy_delta_14:+.3f}). Posible falso rompimiento."
            logger.warning("Orden rechazada por Risk Engine: %s", reason)
            return self._build_rejection(reason)

        # 4. Verificación de Confianza Mínima de IA
        min_confidence = 0.70
        if decision.confidence < min_confidence:
            reason = f"Confianza de IA insuficiente ({decision.confidence:.2f} < {min_confidence:.2f})."
            logger.info("Orden rechazada: %s", reason)
            return self._build_rejection(reason)

        # 5. Verificación de Pérdida Diaria Máxima
        allowed_daily_loss = self.account_capital * self.max_daily_loss_pct
        if self.current_daily_loss >= allowed_daily_loss:
            self.trigger_kill_switch(f"Límite de pérdida diaria alcanzado ({self.current_daily_loss:.2f} >= {allowed_daily_loss:.2f} USDC)")
            return self._build_rejection("Límite de pérdida diaria alcanzado.")

        # 6. Verificación de Rachas de Pérdidas Consecutivas
        if self.consecutive_losses >= self.max_consecutive_losses:
            reason = f"Demasiadas pérdidas consecutivas ({self.consecutive_losses}). Periodo de enfriamiento activado."
            logger.warning("Orden rechazada: %s", reason)
            return self._build_rejection(reason)

        # 7. Concurrencia de Posiciones y Exposición de Cartera
        if len(self.active_positions) >= self.max_active_positions:
            reason = f"Máximo de posiciones activas alcanzado ({len(self.active_positions)}/{self.max_active_positions})."
            logger.info("Orden rechazada: %s", reason)
            return self._build_rejection(reason)

        if state.symbol in self.active_positions:
            reason = f"Ya existe una posición activa en {state.symbol}. Prohibido promediar."
            logger.info("Orden rechazada: %s", reason)
            return self._build_rejection(reason)

        # 8. Validación y Ajuste Determinista del Stop Loss
        entry_price = state.current_price
        atr = state.indicators.atr_14

        if decision.suggested_stop_loss is not None:
            raw_sl = decision.suggested_stop_loss
        else:
            raw_sl = entry_price - (1.2 * atr) if decision.signal == SignalDirection.LONG else entry_price + (1.2 * atr)

        if decision.signal == SignalDirection.LONG and raw_sl >= entry_price:
            reason = f"Incoherencia geométrica: Stop Loss ({raw_sl:.2f}) >= Precio de entrada ({entry_price:.2f}) en LONG."
            logger.error("Orden rechazada: %s", reason)
            return self._build_rejection(reason)

        if decision.signal == SignalDirection.SHORT and raw_sl <= entry_price:
            reason = f"Incoherencia geométrica: Stop Loss ({raw_sl:.2f}) <= Precio de entrada ({entry_price:.2f}) en SHORT."
            logger.error("Orden rechazada: %s", reason)
            return self._build_rejection(reason)

        sl_distance_pct = abs(entry_price - raw_sl) / entry_price

        if sl_distance_pct < self.min_sl_distance_pct:
            reason = f"Stop Loss demasiado estrecho ({sl_distance_pct*100:.2f}% < {self.min_sl_distance_pct*100:.2f}%). Riesgo de ruido."
            logger.warning("Orden rechazada: %s", reason)
            return self._build_rejection(reason)

        if sl_distance_pct > self.max_sl_distance_pct:
            reason = f"Stop Loss excesivamente amplio ({sl_distance_pct*100:.2f}% > {self.max_sl_distance_pct*100:.2f}%). Ineficiente."
            logger.warning("Orden rechazada: %s", reason)
            return self._build_rejection(reason)

        # 9. Cálculo Estricto de Tamaño de Posición (Fixed Fractional Risk con Modulador de Entropía)
        base_risk_cash = self.account_capital * self.risk_per_trade_pct

        # Si la entropía está en zona moderada (0.75 - 0.84), se reduce el riesgo al 70% como modulador prudencial
        if ent.normalized_entropy >= 0.75:
            risk_cash = base_risk_cash * 0.70
            logger.info("Modulador de Entropía activo: riesgo ajustado a 70%% ($%.2f USDC) debido a H_norm=%.3f", risk_cash, ent.normalized_entropy)
        else:
            risk_cash = base_risk_cash

        effective_loss_pct = sl_distance_pct + self.roundtrip_fee_pct
        notional_size_usdc = risk_cash / effective_loss_pct

        # Limitar apalancamiento máximo permitido (ej. 1.5x de cuenta)
        max_allowed_notional_per_trade = self.account_capital * 1.5
        if notional_size_usdc > max_allowed_notional_per_trade:
            logger.debug(
                "Nocional calculado (%.2f USDC) supera el tope por activo. Acotando a %.2f USDC.",
                notional_size_usdc, max_allowed_notional_per_trade
            )
            notional_size_usdc = max_allowed_notional_per_trade

        quantity = notional_size_usdc / entry_price
        leverage = notional_size_usdc / self.account_capital

        # 10. Validación del Take Profit (Asimetría R:R obligatoria >= 1.8:1)
        raw_tp = decision.suggested_take_profit
        if raw_tp is not None:
            tp_distance_pct = abs(raw_tp - entry_price) / entry_price
            rr_ratio = tp_distance_pct / sl_distance_pct
            if rr_ratio < 1.8:
                logger.warning("Take profit sugerido ofrece R:R < 1.8 (%.2f). Ajustando a 2.0x R:R.", rr_ratio)
                raw_tp = entry_price + (2.0 * abs(entry_price - raw_sl)) if decision.signal == SignalDirection.LONG else entry_price - (2.0 * abs(entry_price - raw_sl))
        else:
            raw_tp = entry_price + (2.0 * abs(entry_price - raw_sl)) if decision.signal == SignalDirection.LONG else entry_price - (2.0 * abs(entry_price - raw_sl))

        logger.info(
            "✅ PROPUESTA APROBADA por Risk Engine: Símbolo=%s, Qty=%.4f (%.2f USDC, apalancamiento=%.2fx, Riesgo=$%.2f, H_norm=%.3f)",
            state.symbol, quantity, notional_size_usdc, leverage, risk_cash, ent.normalized_entropy
        )

        return RiskApproval(
            approved=True,
            reason="Aprobado: Cumple con restricciones de entropía, sizing determinista y límites de cartera.",
            adjusted_position_size=round(quantity, 6),
            calculated_risk_amount=round(risk_cash, 2),
            validated_stop_loss=round(raw_sl, 2),
            validated_take_profit=round(raw_tp, 2) if raw_tp else None,
            leverage=round(leverage, 2),
            max_slippage_pct=0.0005,
            entropy_filter_passed=True
        )

    def create_authorized_order(self, state: MarketState, decision: AIDecision, approval: RiskApproval) -> OrderIntent:
        """Crea la orden formal de compra/venta tras la aprobación determinista."""
        if not approval.approved:
            raise RiskValidationError(f"Intento de ordenar una propuesta rechazada: {approval.reason}")

        return OrderIntent(
            symbol=state.symbol,
            direction=decision.signal,
            order_type=OrderType.MARKET,
            entry_price=state.current_price,
            quantity=approval.adjusted_position_size,
            stop_loss=approval.validated_stop_loss,
            take_profit=approval.validated_take_profit,
            leverage=approval.leverage
        )

    def _build_rejection(self, reason: str) -> RiskApproval:
        return RiskApproval(
            approved=False,
            reason=reason,
            adjusted_position_size=0.0,
            calculated_risk_amount=0.0,
            validated_stop_loss=0.0,
            validated_take_profit=None,
            leverage=1.0,
            max_slippage_pct=0.0,
            entropy_filter_passed=False
        )
