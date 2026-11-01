"""Capa 3: Capa de Decisión de IA (Jev Decision Layer).

Analiza el MarketState estructurado (EMAs, SMA, Entropía de Shannon y Volatilidad)
y genera una decisión JSON tipada (AIDecision) adaptando el sesgo y la estrategia.
Incluye integración nativa con el SDK oficial de Google Gemini (Gemini Pro).
"""

from abc import ABC, abstractmethod
import json
import logging
import os
from typing import Dict, Any, Optional

from .models import MarketState, AIDecision, SignalDirection, EntropyRegime, StrategicBias
from .exceptions import AIDecisionError

logger = logging.getLogger("jev.decision_layer")


class BaseDecisionEngine(ABC):
    """Interfaz abstracta para el motor de decisión cuantitativa / IA."""

    @abstractmethod
    def evaluate(self, state: MarketState) -> AIDecision:
        """Emite una decisión estructurada basada en el estado de mercado."""
        pass


class PromptTemplateManager:
    """Gestiona los prompts de sistema y de usuario para el modelo de lenguaje de Jev."""

    @staticmethod
    def build_system_prompt() -> str:
        return (
            "Eres 'Jev', un motor analítico cuantitativo TypeSafe AI y estratega algorítmico de alta precisión.\n"
            "Tu propósito es evaluar el estado de mercado estructurado (EMAs, SMA, Volatilidad y ENTROPÍA DE SHANNON)\n"
            "para determinar el régimen de mercado, adaptar el sesgo y seleccionar la estrategia cuantitativa óptima.\n\n"
            "REGLAS CIENTÍFICAS BASADAS EN ENTROPÍA Y ESTRUCTURA DE MEDIAS:\n"
            "1. FILTRO DE ENTROPÍA DE SHANNON (H_norm):\n"
            "   - Si normalized_entropy > 0.84 (Régimen de Caos/Ruido Blanco): PROHIBIDO OPERAR. La señal DEBE ser 'NO_TRADE',\n"
            "     el sesgo 'CAPITAL_PRESERVATION' y la estrategia 'DEFENSIVE_CASH'. El mercado carece de persistencia.\n"
            "   - Si regime_shift_detected = true (Delta H > 0.12): Alerta de transición inminente. Mantener 'NO_TRADE'.\n"
            "   - Si normalized_entropy < 0.75: Existe persistencia y bajo ruido. Validar alineación con EMAs.\n"
            "2. ADAPTACIÓN DE ESTRATEGIA SEGÚN RÉGIMEN:\n"
            "   - Tendencia Fuerte (EMA 50 > EMA 200 + H_norm < 0.80): Adaptar a 'TREND_PULLBACK' (retroceso a EMA-20/valor) o 'TREND_BREAKOUT'.\n"
            "   - Rango Oscilatorio (EMA planas + ADX < 22 + Entropía moderada): Adaptar a 'MEAN_REVERSION_BANDS' o 'NO_TRADE'.\n"
            "3. FORMATO DE RESPUESTA: ÚNICAMENTE un objeto JSON estrictamente válido, sin markdown ni texto extra.\n\n"
            "ESQUEMA JSON OBLIGATORIO:\n"
            "{\n"
            '  "signal": "LONG" | "SHORT" | "NO_TRADE",\n'
            '  "confidence": 0.0 a 1.0,\n'
            '  "entry_type": "pullback" | "breakout" | "mean_reversion" | "none",\n'
            '  "adapted_strategy": "TREND_PULLBACK" | "TREND_BREAKOUT" | "MEAN_REVERSION_BANDS" | "DEFENSIVE_CASH",\n'
            '  "strategic_bias": "BULLISH_TREND" | "BEARISH_TREND" | "MEAN_REVERSION_RANGE" | "REGIME_TRANSITION_ALERT" | "CAPITAL_PRESERVATION",\n'
            '  "reason": "Explicación lógica confluente de Entropía, EMAs y Momento",\n'
            '  "invalidation": "Condición matemática o nivel que destruye la tesis",\n'
            '  "suggested_stop_loss": float o null,\n'
            '  "suggested_take_profit": float o null\n'
            "}"
        )

    @staticmethod
    def build_user_prompt(state: MarketState) -> str:
        context = state.to_ai_context()
        return (
            f"Analiza el siguiente estado de mercado estructurado (incluyendo Entropía de Shannon) y emite tu veredicto JSON:\n"
            f"{json.dumps(context, indent=2, ensure_ascii=False)}"
        )


def _parse_and_validate_response(raw_text: str, state: MarketState) -> AIDecision:
    """Limpia el texto, parsea JSON y valida estrictamente las claves requeridas."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as jde:
        raise AIDecisionError(f"El LLM devolvió un JSON inválido: {jde}. Raw text: {raw_text[:200]}")

    required_keys = ["signal", "confidence", "entry_type", "reason", "invalidation"]
    for key in required_keys:
        if key not in data:
            raise AIDecisionError(f"Falta el campo obligatorio '{key}' en la respuesta de la IA.")

    raw_signal = str(data["signal"]).upper().strip()
    try:
        signal_enum = SignalDirection(raw_signal)
    except ValueError:
        raise AIDecisionError(f"Valor de 'signal' no reconocido: '{raw_signal}'. Esperado: LONG, SHORT, NO_TRADE.")

    confidence = float(data["confidence"])
    if not (0.0 <= confidence <= 1.0):
        raise AIDecisionError(f"La confianza ({confidence}) debe estar en el rango [0.0, 1.0].")

    adapted_strategy = str(data.get("adapted_strategy") or state.recommended_strategy.value)
    strategic_bias = str(data.get("strategic_bias") or state.strategic_bias.value)

    return AIDecision(
        signal=signal_enum,
        confidence=confidence,
        entry_type=str(data["entry_type"]),
        adapted_strategy=adapted_strategy,
        strategic_bias=strategic_bias,
        reason=str(data["reason"]),
        invalidation=str(data["invalidation"]),
        suggested_stop_loss=float(data["suggested_stop_loss"]) if data.get("suggested_stop_loss") else None,
        suggested_take_profit=float(data["suggested_take_profit"]) if data.get("suggested_take_profit") else None,
    )


def _fallback_algorithmic_inference(state: MarketState) -> str:
    """Motor de inferencia determinista interno que simula el razonamiento analítico de Jev."""
    ind = state.indicators
    ent = ind.entropy
    price = state.current_price
    atr = ind.atr_14

    # 1. Filtro estricto de Entropía de Shannon
    if ent.entropy_regime == EntropyRegime.HIGH_ENTROPY_CHAOS or ent.normalized_entropy > 0.84:
        return json.dumps({
            "signal": "NO_TRADE",
            "confidence": 0.20,
            "entry_type": "none",
            "adapted_strategy": "DEFENSIVE_CASH",
            "strategic_bias": "CAPITAL_PRESERVATION",
            "reason": f"Entropía de Shannon extremadamente alta (H_norm={ent.normalized_entropy:.3f} > 0.84). El mercado está en ruido blanco caótico sin persistencia direccional.",
            "invalidation": "Reducción de H_norm < 0.75 y emergencia de estructura ordenada.",
            "suggested_stop_loss": None,
            "suggested_take_profit": None
        })

    # 2. Alerta de Transición de Régimen
    if ent.regime_shift_detected and ent.entropy_delta_14 > 0.12:
        return json.dumps({
            "signal": "NO_TRADE",
            "confidence": 0.30,
            "entry_type": "none",
            "adapted_strategy": "DEFENSIVE_CASH",
            "strategic_bias": "REGIME_TRANSITION_ALERT",
            "reason": f"Detección de transición de régimen: Delta de Entropía reciente={ent.entropy_delta_14:+.3f}. Posible colapso de tendencia o shock de información.",
            "invalidation": "Estabilización de entropía en ventana rodante.",
            "suggested_stop_loss": None,
            "suggested_take_profit": None
        })

    # 3. Pullback en Tendencia Alcista de Baja Entropía
    if state.strategic_bias == StrategicBias.BULLISH_TREND:
        is_pullback = abs(price - ind.ema_20) <= (1.2 * atr) or price <= ind.bb_middle
        if is_pullback and 38 <= ind.rsi_14 <= 62:
            sl = price - (1.1 * atr)
            tp = price + (2.5 * atr)
            return json.dumps({
                "signal": "LONG",
                "confidence": round(0.75 + (ent.predictability_score * 0.15), 2),
                "entry_type": "pullback",
                "adapted_strategy": "TREND_PULLBACK",
                "strategic_bias": "BULLISH_TREND",
                "reason": (
                    f"Confluencia cuantitativa: Baja entropía (H_norm={ent.normalized_entropy:.3f}, Predictabilidad={ent.predictability_score:.2f}) "
                    f"con precio en zona de valor EMA-20 ({ind.ema_20:.2f}) sobre EMA-50 ({ind.ema_50:.2f}) y EMA-200. RSI={ind.rsi_14:.1f} y ADX={ind.adx_14:.1f}."
                ),
                "invalidation": f"Cierre horario por debajo de {sl:.2f} (ruptura del swing low y pérdida de EMA-50).",
                "suggested_stop_loss": sl,
                "suggested_take_profit": tp
            })

    # 4. Pullback en Tendencia Bajista de Baja Entropía
    if state.strategic_bias == StrategicBias.BEARISH_TREND:
        is_pullback_short = abs(price - ind.ema_20) <= (1.2 * atr) or price >= ind.bb_middle
        if is_pullback_short and 38 <= ind.rsi_14 <= 62:
            sl = price + (1.1 * atr)
            tp = price - (2.5 * atr)
            return json.dumps({
                "signal": "SHORT",
                "confidence": round(0.75 + (ent.predictability_score * 0.15), 2),
                "entry_type": "pullback",
                "adapted_strategy": "TREND_PULLBACK",
                "strategic_bias": "BEARISH_TREND",
                "reason": (
                    f"Confluencia cuantitativa bajista: H_norm={ent.normalized_entropy:.3f} confirma orden en la tendencia. "
                    f"Rebote hacia resistencia dinámica EMA-20 ({ind.ema_20:.2f}) bajo EMA-50 ({ind.ema_50:.2f})."
                ),
                "invalidation": f"Cierre horario por encima de {sl:.2f}.",
                "suggested_stop_loss": sl,
                "suggested_take_profit": tp
            })

    # 5. Sin confluencia clara o Rango
    return json.dumps({
        "signal": "NO_TRADE",
        "confidence": 0.45,
        "entry_type": "none",
        "adapted_strategy": state.recommended_strategy.value,
        "strategic_bias": state.strategic_bias.value,
        "reason": f"Mercado en régimen {state.regime.value} con H_norm={ent.normalized_entropy:.3f}. No cumple criterios de asimetría favorable.",
        "invalidation": "Aparición de setup confluente.",
        "suggested_stop_loss": None,
        "suggested_take_profit": None
    })


class LLMStructuredDecisionEngine(BaseDecisionEngine):
    """Capa de Decisión TypeSafe AI genérica con callable inyectable."""

    def __init__(self, llm_callable=None):
        self.llm_callable = llm_callable

    def evaluate(self, state: MarketState) -> AIDecision:
        system_prompt = PromptTemplateManager.build_system_prompt()
        user_prompt = PromptTemplateManager.build_user_prompt(state)

        logger.info(
            "Jev Decision Layer analizando %s [%s] (Entropía H_norm=%.3f, Régimen=%s)...",
            state.symbol, state.timeframe, state.indicators.entropy.normalized_entropy, state.regime.value
        )

        try:
            if self.llm_callable is not None:
                raw_response = self.llm_callable(system_prompt, user_prompt)
            else:
                raw_response = _fallback_algorithmic_inference(state)

            decision = _parse_and_validate_response(raw_response, state)
            logger.info(
                "Decisión IA emitida: %s (confianza=%.2f, estrategia=%s, sesgo=%s) | Motivo: %s",
                decision.signal.value, decision.confidence, decision.adapted_strategy,
                decision.strategic_bias, decision.reason
            )
            return decision

        except Exception as e:
            logger.error("Fallo crítico en Jev Decision Layer: %s", e)
            raise AIDecisionError(f"Error procesando decisión de IA para {state.symbol}: {e}") from e


class GeminiDecisionEngine(BaseDecisionEngine):
    """
    Conector nativo con Google Gemini (Gemini Pro) usando el SDK oficial google-genai.
    Ejecuta inferencia con temperature=0.0, salida JSON estructurada y fallback
    algorítmico inmediato ante caídas de red, cuotas (429) o ausencia de credenciales.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-pro",
        temperature: float = 0.0,
        timeout_seconds: float = 5.0
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Cliente Gemini Pro inicializado exitosamente con modelo: %s", self.model_name)
            except Exception as e:
                logger.warning("No se pudo inicializar genai.Client: %s. Se utilizará fallback algorítmico.", e)
        else:
            logger.info("GEMINI_API_KEY no detectada. Operando con motor analítico TypeSafe interno de alta fidelidad.")

    def evaluate(self, state: MarketState) -> AIDecision:
        system_prompt = PromptTemplateManager.build_system_prompt()
        user_prompt = PromptTemplateManager.build_user_prompt(state)

        logger.info(
            "Gemini Pro Decision Layer evaluando %s [%s] (H_norm=%.3f, Régimen=%s)...",
            state.symbol, state.timeframe, state.indicators.entropy.normalized_entropy, state.regime.value
        )

        raw_response = None
        if self.client is not None:
            try:
                from google.genai import types
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=self.temperature,
                        response_mime_type="application/json"
                    )
                )
                if response and response.text:
                    raw_response = response.text
                    logger.info("Respuesta estructurada recibida de Gemini Pro API exitosamente.")
            except Exception as e:
                logger.warning(
                    "Excepción o timeout contactando con Gemini Pro API: %s. Activando fallback algorítmico de seguridad.",
                    e
                )

        if raw_response is None:
            raw_response = _fallback_algorithmic_inference(state)

        decision = _parse_and_validate_response(raw_response, state)
        logger.info(
            "Decisión Gemini Pro completada: %s (confianza=%.2f, estrategia=%s, sesgo=%s) | Motivo: %s",
            decision.signal.value, decision.confidence, decision.adapted_strategy,
            decision.strategic_bias, decision.reason
        )
        return decision
