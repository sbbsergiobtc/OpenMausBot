#!/usr/bin/env python3
"""
Entorno Gymnasium / MDP Basado en Eventos para Orquestación de los 10 Regímenes de Mercado
AlgrokQuant · Jev Quantitative Engine · Ignacio Ayago (Techain) RL Framework

Características Principales:
1. Taxonomía Canónica de 10 Regímenes Discretos (S0 a S9) × 3 Arquetipos × 2 Estados Guardián = 60 Estados.
2. Espacio de 5 Acciones Discretas: A = [0.00x, 0.50x, 0.75x, 1.00x, 1.25x].
3. Tope Dinámico del 40% de Consistencia en Prop Firm (Early TP Clamp):
   - Cuando se aplica sobre-apalancamiento (1.25x) o lote estándar (1.00x) en cuentas de fondeo,
     el sistema calcula el techo diario de beneficio permitido (40% del objetivo total del reto)
     y acorta automáticamente el Take Profit si el beneficio potencial excede dicho límite.
4. Función de Recompensa Dual Asimétrica:
   - CAPITAL_PROPIO: Maximiza el crecimiento compuesto (Sortino/CAGR diferencial).
   - PROP_FIRM: Penalización cuadrática severa sobre la proximidad al límite de EOD Drawdown (3.0% / 8.0%)
     y cumplimiento estricto de la regla del 40% de consistencia.
"""

from typing import Dict, List, Any, Tuple, Optional
import numpy as np

# ==============================================================================
# 1. TAXONOMÍA OFICIAL DE LOS 10 REGÍMENES CANÓNICOS (S0..S9) Y ARQUETIPOS
# ==============================================================================

REGIME_10_CATALOG: Dict[int, Dict[str, Any]] = {
    0: {
        "id": 0,
        "code": "S0_STRONG_CLEAN_BULL",
        "macro_regime": "TRENDING_BULLISH",
        "label": "Tendencia Alcista Fuerte Limpia",
        "favored_archetype": "TREND_FOLLOWING",
        "heuristic_mult": 1.25,
        "description": "ADX >= 25, +DI > -DI, Close >= EMA50 > EMA200, H_norm <= 0.78, Kurt_rob <= 3.20"
    },
    1: {
        "id": 1,
        "code": "S1_MODERATE_BULL_TREND",
        "macro_regime": "TRENDING_BULLISH",
        "label": "Tendencia Alcista Moderada",
        "favored_archetype": "TREND_FOLLOWING",
        "heuristic_mult": 1.00,
        "description": "20 <= ADX < 25 o Hurst >= 0.55, +DI >= -DI, Close >= EMA200"
    },
    2: {
        "id": 2,
        "code": "S2_BULL_VOLATILITY_CLIMAX",
        "macro_regime": "TRENDING_BULLISH",
        "label": "Clímax / Sobreextensión Alcista",
        "favored_archetype": "MEAN_REVERSION",
        "heuristic_mult": 0.50,
        "description": "+DI > -DI, Close > EMA50, pero ATR_Ratio > 1.50 o Kurt_rob > 3.20"
    },
    3: {
        "id": 3,
        "code": "S3_STRONG_CLEAN_BEAR",
        "macro_regime": "TRENDING_BEARISH",
        "label": "Tendencia Bajista Ordenada",
        "favored_archetype": "TREND_FOLLOWING",
        "heuristic_mult": 1.00,
        "description": "ADX >= 25, -DI > +DI, Close <= EMA50 < EMA200, H_norm <= 0.78, Kurt_rob <= 3.20"
    },
    4: {
        "id": 4,
        "code": "S4_MODERATE_BEAR_TREND",
        "macro_regime": "TRENDING_BEARISH",
        "label": "Tendencia Bajista Moderada",
        "favored_archetype": "TREND_FOLLOWING",
        "heuristic_mult": 0.75,
        "description": "20 <= ADX < 25, -DI > +DI, Close < EMA200, ATR_Ratio <= 1.50"
    },
    5: {
        "id": 5,
        "code": "S5_BEAR_PANIC_CAPITULATION",
        "macro_regime": "TRENDING_BEARISH",
        "label": "Capitulación / Pánico Bajista",
        "favored_archetype": "MEAN_REVERSION",
        "heuristic_mult": 0.50,
        "description": "-DI > +DI, Close < EMA50, ATR_Ratio > 1.50 (cascada con rebote en V)"
    },
    6: {
        "id": 6,
        "code": "S6_CLEAN_MEAN_REVERSION",
        "macro_regime": "RANGING_LATERAL",
        "label": "Rango Estacionario Limpio",
        "favored_archetype": "MEAN_REVERSION",
        "heuristic_mult": 1.00,
        "description": "ADX < 18.5, Hurst < 0.49, 0.75 <= ATR_Ratio <= 1.25, Kurt_rob <= 3.20"
    },
    7: {
        "id": 7,
        "code": "S7_COMPRESSION_SQUEEZE",
        "macro_regime": "RANGING_LATERAL",
        "label": "Compresión / Squeeze Volatilidad",
        "favored_archetype": "VOLATILITY_BREAKOUT",
        "heuristic_mult": 0.75,
        "description": "ADX < 20, ATR_Ratio < 0.75, H_norm <= 0.82 (acumulación pre-ruptura)"
    },
    8: {
        "id": 8,
        "code": "S8_CHOPPY_FAT_TAILS_RANGE",
        "macro_regime": "RANGING_LATERAL",
        "label": "Rango Sucio / Colas Pesadas",
        "favored_archetype": "MEAN_REVERSION",
        "heuristic_mult": 0.25,
        "description": "ADX < 21, Kurt_rob > 3.20 o 1.25 < ATR_Ratio <= 1.60 (zona de whipsaws)"
    },
    9: {
        "id": 9,
        "code": "S9_HIGH_ENTROPY_BLACKOUT",
        "macro_regime": "HIGH_ENTROPY_CHAOS",
        "label": "Caos / Ruido Blanco (Blackout)",
        "favored_archetype": "NONE",
        "heuristic_mult": 0.00,
        "description": "H_norm > 0.84 o Delta_H > 0.12 o ATR_Ratio > 2.20 -> Bloqueo 0.00x"
    },
}

ARCHETYPE_MAP: Dict[int, str] = {
    0: "TREND_FOLLOWING",
    1: "MEAN_REVERSION",
    2: "VOLATILITY_BREAKOUT",
}

GUARDIAN_STATE_MAP: Dict[int, str] = {
    0: "GREEN_OPTIMAL",
    1: "AMBER_CAUTION",
}

ACTION_MULTIPLIERS: List[float] = [0.00, 0.50, 0.75, 1.00, 1.25]


def map_strategy_to_archetype_id(archetype_or_anchor: str) -> int:
    """Convierte el nombre del arquetipo o anclaje macro en su ID funcional (0, 1 o 2)."""
    s = (archetype_or_anchor or "").upper()
    if any(k in s for k in ["BOLLINGER", "VWAP", "RSI", "CONNORS", "MEAN", "REVERSION", "DIP", "CHANNEL", "ZSCORE"]):
        return 1  # MEAN_REVERSION
    if any(k in s for k in ["DONCHIAN", "ORB", "BREAKOUT", "BREAKDOWN", "SQUEEZE", "VOLATILITY", "FVG"]):
        return 2  # VOLATILITY_BREAKOUT
    return 0  # TREND_FOLLOWING (SUPERTREND, EMA_TREND, PULLBACK, MOMENTUM)


# ==============================================================================
# 2. REGLA DEL 40% DE CONSISTENCIA EN PROP FIRM (EARLY TAKE PROFIT CLAMP)
# ==============================================================================

def apply_prop_firm_consistency_tp_clamp(
    entry_price: float,
    sl_price: float,
    tp_price: float,
    direction: int,
    lot_multiplier: float,
    base_risk_pct: float = 1.00,
    target_challenge_pct: float = 6.00,
    today_realized_profit_pct: float = 0.00,
    consistency_cap_ratio: float = 0.40,
    safety_buffer: float = 0.95
) -> Dict[str, Any]:
    """
    Garantiza que ninguna operación o sesión diaria en Prop Firm supere el 40% del objetivo
    total de beneficio del reto (Regla de Consistencia).
    Si al usar 1.25x (o 1.00x) el Take Profit original generaría un beneficio que supera el
    margen de consistencia restante del día, acorta automáticamente el precio del Take Profit
    para cerrar antes la operación y asegurar el cobro sin violar jamás el 40%.
    """
    max_daily_consistency_pct = target_challenge_pct * consistency_cap_ratio * safety_buffer
    remaining_allowed_pct = max(0.0, max_daily_consistency_pct - max(0.0, today_realized_profit_pct))

    sl_dist = abs(entry_price - sl_price)
    tp_dist = abs(tp_price - entry_price)
    if sl_dist <= 1e-12 or lot_multiplier <= 0.0:
        return {
            "effective_lot_multiplier": 0.0,
            "clamped_tp_price": tp_price,
            "original_tp_price": tp_price,
            "expected_profit_pct": 0.0,
            "max_daily_consistency_pct": round(max_daily_consistency_pct, 3),
            "remaining_allowed_pct": round(remaining_allowed_pct, 3),
            "early_tp_clamped": False,
            "blocked_by_consistency": remaining_allowed_pct <= 0.05,
            "reason": "Sin margen de consistencia hoy o multiplicador 0.0x"
        }

    # Si ya se alcanzó el techo del 40% hoy, se bloquean nuevas entradas por el resto del día
    if remaining_allowed_pct <= 0.08:
        return {
            "effective_lot_multiplier": 0.0,
            "clamped_tp_price": tp_price,
            "original_tp_price": tp_price,
            "expected_profit_pct": 0.0,
            "max_daily_consistency_pct": round(max_daily_consistency_pct, 3),
            "remaining_allowed_pct": round(remaining_allowed_pct, 3),
            "early_tp_clamped": False,
            "blocked_by_consistency": True,
            "reason": f"Techo diario de consistencia (40% = +{max_daily_consistency_pct:.2f}%) alcanzado hoy"
        }

    rr_ratio = tp_dist / sl_dist
    effective_risk_pct = base_risk_pct * lot_multiplier
    unclamped_profit_pct = effective_risk_pct * rr_ratio

    if unclamped_profit_pct > remaining_allowed_pct:
        # Acortar el Take Profit (Early TP Clamp) para cerrar exactamente en el límite seguro del 40%
        clamped_rr = remaining_allowed_pct / max(1e-6, effective_risk_pct)
        new_tp_dist = sl_dist * clamped_rr
        clamped_tp = entry_price + (new_tp_dist if direction >= 0 else -new_tp_dist)
        return {
            "effective_lot_multiplier": lot_multiplier,
            "clamped_tp_price": round(float(clamped_tp), 5),
            "original_tp_price": round(float(tp_price), 5),
            "expected_profit_pct": round(float(remaining_allowed_pct), 3),
            "unclamped_profit_pct": round(float(unclamped_profit_pct), 3),
            "max_daily_consistency_pct": round(max_daily_consistency_pct, 3),
            "remaining_allowed_pct": round(remaining_allowed_pct, 3),
            "early_tp_clamped": True,
            "blocked_by_consistency": False,
            "reason": (
                f"Early TP Clamp activo ({lot_multiplier:.2f}x): TP acortado de {rr_ratio:.2f}R a {clamped_rr:.2f}R "
                f"para respetar consistencia <= 40% (+{remaining_allowed_pct:.2f}% máx hoy)"
            )
        }

    return {
        "effective_lot_multiplier": lot_multiplier,
        "clamped_tp_price": round(float(tp_price), 5),
        "original_tp_price": round(float(tp_price), 5),
        "expected_profit_pct": round(float(unclamped_profit_pct), 3),
        "unclamped_profit_pct": round(float(unclamped_profit_pct), 3),
        "max_daily_consistency_pct": round(max_daily_consistency_pct, 3),
        "remaining_allowed_pct": round(remaining_allowed_pct, 3),
        "early_tp_clamped": False,
        "blocked_by_consistency": False,
        "reason": f"TP dentro del límite del 40% de consistencia (+{unclamped_profit_pct:.2f}% <= +{remaining_allowed_pct:.2f}%)"
    }


# ==============================================================================
# 3. ENTORNO GYM BASADO EN EVENTOS (AlgrokRegimeGymEnv)
# ==============================================================================

class AlgrokRegimeGymEnv:
    """
    Entorno de Aprendizaje por Refuerzo compatible con la convención OpenAI Gymnasium:
      - observation_space: 60 estados discretos (10 regímenes × 3 arquetipos × 2 estados guardián)
      - action_space: 5 acciones discretas [0.00x, 0.50x, 0.75x, 1.00x, 1.25x]
      - Avanza evento por evento (cada vez que una estrategia solicita abrir un trade).
      - Contabiliza el EOD Drawdown real al cierre de cada día y aplica el Early TP Clamp del 40% en Prop Firm.
    """

    def __init__(self, trade_events: List[Dict[str, Any]], desk_mode: str = "PROP_FIRM"):
        self.trade_events = trade_events
        self.desk_mode = desk_mode.upper()
        self.is_prop = "PROP_FIRM" in self.desk_mode or self.desk_mode.startswith("PROP_")
        self.n_states = 60  # 10 * 3 * 2
        self.n_actions = len(ACTION_MULTIPLIERS)

        # Parámetros de riesgo según mesa
        self.max_eod_dd_limit_pct = 3.00 if self.is_prop else 20.00
        self.target_challenge_pct = 6.00 if self.is_prop else 30.00
        self.base_risk_pct = 0.65 if self.is_prop else 1.00

        self.idx = 0
        self.equity = 100.0
        self.eod_peak_equity = 100.0
        self.current_eod_dd_pct = 0.0
        self.max_eod_dd_pct = 0.0
        self.today_realized_pct = 0.0
        self.current_day_id = -1

    @staticmethod
    def encode_state(regime_id: int, archetype_id: int, guardian_id: int) -> int:
        r = max(0, min(9, int(regime_id)))
        a = max(0, min(2, int(archetype_id)))
        g = max(0, min(1, int(guardian_id)))
        return r * 6 + a * 2 + g

    @staticmethod
    def decode_state(state_idx: int) -> Tuple[int, int, int]:
        r = state_idx // 6
        rem = state_idx % 6
        a = rem // 2
        g = rem % 2
        return r, a, g

    def reset(self) -> int:
        self.idx = 0
        self.equity = 100.0
        self.eod_peak_equity = 100.0
        self.current_eod_dd_pct = 0.0
        self.max_eod_dd_pct = 0.0
        self.today_realized_pct = 0.0
        self.current_day_id = -1
        if not self.trade_events:
            return 0
        ev = self.trade_events[0]
        return self.encode_state(ev["regime_id"], ev["archetype_id"], ev["guardian_id"])

    def step(self, action_idx: int) -> Tuple[int, float, bool, Dict[str, Any]]:
        if self.idx >= len(self.trade_events):
            return 0, 0.0, True, {}

        ev = self.trade_events[self.idx]
        mult = ACTION_MULTIPLIERS[max(0, min(self.n_actions - 1, int(action_idx)))]

        # Cambio de día natural -> Actualización de EOD High-Water Mark (Regla Suprema EOD DD)
        day_id = int(ev.get("day_id", self.idx // 3))
        if day_id != self.current_day_id:
            if self.current_day_id != -1:
                if self.equity > self.eod_peak_equity:
                    self.eod_peak_equity = self.equity
                self.current_eod_dd_pct = max(0.0, ((self.eod_peak_equity - self.equity) / self.eod_peak_equity) * 100.0)
                if self.current_eod_dd_pct > self.max_eod_dd_pct:
                    self.max_eod_dd_pct = self.current_eod_dd_pct
            self.current_day_id = day_id
            self.today_realized_pct = 0.0

        raw_r_multiple = float(ev["r_multiple"])  # Retorno en unidades de riesgo R (ej. +2.2R o -1.0R)
        trade_pct = raw_r_multiple * self.base_risk_pct * mult
        early_clamped = False

        # En Prop Firm: aplicar Regla del 40% de Consistencia (Early TP Clamp si mult = 1.25x o 1.00x supera el tope)
        if self.is_prop and mult > 0.0:
            max_day_pct = self.target_challenge_pct * 0.40 * 0.95  # 2.28% en reto del 6%
            rem_pct = max(0.0, max_day_pct - max(0.0, self.today_realized_pct))
            if rem_pct <= 0.05:
                trade_pct = 0.0
                mult = 0.0
            elif trade_pct > rem_pct:
                trade_pct = rem_pct
                early_clamped = True

        self.equity *= (1.0 + trade_pct / 100.0)
        self.today_realized_pct += trade_pct

        # Calcular EOD Drawdown provisional
        provisional_dd = max(0.0, ((self.eod_peak_equity - self.equity) / self.eod_peak_equity) * 100.0)
        memory_weight = float(ev.get("memory_weight", 1.0))

        # Función de Recompensa Asimétrica
        if self.is_prop:
            # Penalización cuadrática fuerte si el EOD DD se acerca al límite de 3.0%
            dd_warn = 1.35
            eod_penalty = 3.50 * max(0.0, provisional_dd - dd_warn) ** 2
            var_penalty = 0.35 * max(0.0, -trade_pct) ** 2
            consistency_bonus = 0.15 if early_clamped else 0.0
            reward = (trade_pct - var_penalty - eod_penalty + consistency_bonus) * memory_weight
        else:
            # Capital Propio: Crecimiento compuesto Sortino (penaliza solo volatilidad bajista)
            downside_sq = 0.25 * max(0.0, -trade_pct) ** 2
            eod_penalty = 0.40 * max(0.0, provisional_dd - 8.0) ** 2
            reward = (trade_pct - downside_sq - eod_penalty) * memory_weight

        self.idx += 1
        done = self.idx >= len(self.trade_events)
        next_state = (
            self.encode_state(
                self.trade_events[self.idx]["regime_id"],
                self.trade_events[self.idx]["archetype_id"],
                self.trade_events[self.idx]["guardian_id"],
            )
            if not done
            else 0
        )

        info = {
            "trade_pct": round(trade_pct, 4),
            "effective_mult": mult,
            "early_tp_clamped": early_clamped,
            "eod_dd_pct": round(provisional_dd, 3),
        }
        return next_state, float(reward), done, info
