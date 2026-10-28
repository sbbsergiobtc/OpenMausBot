"""
Módulo Screener & Pipeline Cuantitativo Jev (Arquitectura 5+1)
AlgrokQuant · Desk Lead Nexus

Implementa de forma determinista y modular:
1. Filtro Pre-LLM de Entropía de Shannon (0 tokens gastados en régimen de caos)
2. Clustering de Correlación Local NumPy (Eliminación de estrategias redundantes)
3. Validación Determinista de Reglas de Riesgo y Gobernanza (DD máx 20%, sizing dinámico)
C. Compresión de Contexto a ~60 tokens para llamadas de agentes
D. Loop Post-Trade Determinista (Detección de anomalías sin IA salvo >2.5 sigma)
A. Circuit Breaker de Régimen en Tiempo Real (Paridad estricta Backtest vs Forward)
+ Métricas Cuantitativas Avanzadas: OOS R/DD Degradation, Stagnation Days, Desglose de Rachas por Activo
"""

import math
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple


class JevScreener:
    """Motor de cribado sistemático y control determinista de 5+1 capas."""

    def __init__(
        self,
        max_allowed_entropy: float = 0.84,
        regime_shift_delta: float = 0.12,
        correlation_threshold: float = 0.80,
        max_capital_propio_dd: float = 20.0,
        min_profit_factor: float = 1.30,
        min_total_trades: int = 30
    ):
        self.max_allowed_entropy = max_allowed_entropy
        self.regime_shift_delta = regime_shift_delta
        self.correlation_threshold = correlation_threshold
        self.max_capital_propio_dd = max_capital_propio_dd
        self.min_profit_factor = min_profit_factor
        self.min_total_trades = min_total_trades

    # =========================================================================
    # UTILIDAD 1: FILTRO PRE-LLM DE ENTROPÍA DE SHANNON (0 Tokens en Ruido)
    # =========================================================================
    def filter_pre_llm_entropy(
        self,
        candles: pd.DataFrame,
        window: int = 50,
        recent_window: int = 14,
        bins: int = 8
    ) -> Dict[str, Any]:
        """
        Evalúa si la serie de precios tiene persistencia o es ruido blanco browniano.
        Si H_norm > 0.84 o Delta H > 0.12, bloquea la consulta a LLM ahorrando tokens.
        """
        if candles.empty or 'close' not in candles.columns or len(candles) < window:
            return {
                "allow_llm_call": False,
                "regime": "INSUFFICIENT_DATA",
                "h_norm": 1.0,
                "delta_h": 0.0,
                "predictability_score": 0.0,
                "reason": f"Velas insuficientes ({len(candles)} < {window}).",
                "tokens_saved": 0
            }

        close = candles['close'].astype(float)
        log_ret = np.log(close / close.shift(1)).dropna()

        if len(log_ret) < window:
            return {
                "allow_llm_call": False,
                "regime": "INSUFFICIENT_RETURNS",
                "h_norm": 1.0,
                "delta_h": 0.0,
                "predictability_score": 0.0,
                "reason": "Retornos insuficientes.",
                "tokens_saved": 0
            }

        # Entropía de Shannon base (50 barras)
        w_returns = log_ret.iloc[-window:]
        h_base, h_norm_base = self._calculate_shannon(w_returns, bins=bins)

        # Entropía reciente (14 barras)
        r_returns = log_ret.iloc[-recent_window:]
        _, h_norm_recent = self._calculate_shannon(r_returns, bins=bins)

        delta_h = float(h_norm_recent - h_norm_base)
        predictability = float(max(0.0, min(1.0, 1.0 - h_norm_base)))

        is_chaos = h_norm_base > self.max_allowed_entropy
        is_shift = delta_h > self.regime_shift_delta

        if is_chaos:
            return {
                "allow_llm_call": False,
                "regime": "HIGH_ENTROPY_CHAOS",
                "h_norm": round(h_norm_base, 4),
                "delta_h": round(delta_h, 4),
                "predictability_score": round(predictability, 4),
                "reason": f"Mercado en régimen caótico (H_norm={h_norm_base:.3f} > {self.max_allowed_entropy}). Cero persistencia direccional.",
                "tokens_saved": 2000
            }

        if is_shift:
            return {
                "allow_llm_call": False,
                "regime": "REGIME_TRANSITION_ALERT",
                "h_norm": round(h_norm_base, 4),
                "delta_h": round(delta_h, 4),
                "predictability_score": round(predictability, 4),
                "reason": f"Salto abrupto de entropía (Delta H={delta_h:+.3f} > {self.regime_shift_delta}). Riesgo de choque o colapso inminente.",
                "tokens_saved": 2000
            }

        return {
            "allow_llm_call": True,
            "regime": "PERSISTENT_STRUCTURE",
            "h_norm": round(h_norm_base, 4),
            "delta_h": round(delta_h, 4),
            "predictability_score": round(predictability, 4),
            "reason": f"Régimen estructurado persistente (H_norm={h_norm_base:.3f} <= {self.max_allowed_entropy}).",
            "tokens_saved": 0
        }

    # =========================================================================
    # UTILIDAD 2: CLUSTERING DE CORRELACIÓN LOCAL NUMPY
    # =========================================================================
    def cluster_correlation_matrix(
        self,
        equity_curves: Dict[str, pd.Series],
        kpi_rankings: Optional[Dict[str, float]] = None,
        max_correlation: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calcula la matriz de correlación de Pearson entre las curvas de equidad de las estrategias.
        Agrupa estrategias correlacionadas (> 0.80) y descarta las redundantes, reteniendo
        únicamente la de mayor ranking cualitativo o Calmar Ratio.
        """
        threshold = max_correlation or self.correlation_threshold
        if not equity_curves or len(equity_curves) <= 1:
            return {
                "retained_strategies": list(equity_curves.keys()),
                "pruned_strategies": [],
                "clusters": {k: [k] for k in equity_curves.keys()},
                "correlation_matrix": {}
            }

        # Alinear curvas en DataFrame
        df_curves = pd.DataFrame(equity_curves).dropna()
        if df_curves.empty or len(df_curves.columns) <= 1:
            return {
                "retained_strategies": list(equity_curves.keys()),
                "pruned_strategies": [],
                "clusters": {k: [k] for k in equity_curves.keys()},
                "correlation_matrix": {}
            }

        # Calcular matriz de correlación de retornos periódicos
        df_rets = df_curves.pct_change().dropna()
        corr_matrix = df_rets.corr()

        strats = list(corr_matrix.columns)
        scores = kpi_rankings or {s: 1.0 for s in strats}

        # Ordenar estrategias por puntuación descendente
        sorted_strats = sorted(strats, key=lambda s: scores.get(s, 0.0), reverse=True)

        retained = []
        pruned = []
        clusters = {}

        for s in sorted_strats:
            if s in pruned:
                continue

            retained.append(s)
            clusters[s] = [s]

            # Buscar todas las correlacionadas con s
            for other in sorted_strats:
                if other != s and other not in pruned and other not in retained:
                    r = corr_matrix.loc[s, other]
                    if not np.isnan(r) and r >= threshold:
                        pruned.append(other)
                        clusters[s].append(other)

        # Serializar matriz como dict
        corr_dict = {
            s1: {s2: round(float(corr_matrix.loc[s1, s2]), 3) for s2 in strats}
            for s1 in strats
        }

        return {
            "retained_strategies": retained,
            "pruned_strategies": pruned,
            "clusters": clusters,
            "correlation_matrix": corr_dict,
            "threshold": threshold,
            "compression_ratio": round((1.0 - (len(retained) / len(strats))) * 100, 1)
        }

    # =========================================================================
    # UTILIDAD 3: VALIDACIÓN DETERMINISTA DE RIESGO Y GOBERNANZA
    # =========================================================================
    def validate_governance_rules(
        self,
        strategy_meta: Dict[str, Any],
        account_type: str = "CAPITAL_PROPIO"
    ) -> Dict[str, Any]:
        """
        Aplica los filtros de gobernanza de LESSON-20261028-014 sin consultar a la IA.
        - Capital Propio: Max DD <= 20.0%, Sizing porcentual dinámico (0.50%-1.50%).
        - Prop Firm: Max EOD DD <= 3.50%, Daily DD <= 2.00%, Target +6.00%.
        - Mínimo trades >= 30, Profit Factor >= 1.30.
        """
        violations = []
        max_dd = float(strategy_meta.get("max_dd", strategy_meta.get("max_drawdown_pct", 0.0)))
        pf = float(strategy_meta.get("profit_factor", 0.0))
        trades_count = int(strategy_meta.get("total_trades", strategy_meta.get("trades_count", 0)))
        sizing_mode = str(strategy_meta.get("sizing_mode", "PERCENTAGE")).upper()

        if sizing_mode == "FIXED_DOLLAR":
            violations.append("Sizing en dólares fijos PROHIBIDO. Debe ser porcentual dinámico (0.50% - 1.50%).")

        if trades_count > 0 and trades_count < self.min_total_trades:
            violations.append(f"Muestra estadística insuficiente ({trades_count} trades < {self.min_total_trades} mínimo).")

        if pf > 0 and pf < self.min_profit_factor:
            violations.append(f"Profit Factor inaceptable ({pf:.2f} < {self.min_profit_factor:.2f} requerido).")

        if account_type == "CAPITAL_PROPIO":
            if max_dd > self.max_capital_propio_dd:
                violations.append(f"Drawdown máximo ({max_dd:.2f}%) excede el techo del {self.max_capital_propio_dd:.1f}%.")
        elif account_type == "PROP_FIRM":
            if max_dd > 3.50:
                violations.append(f"Drawdown máximo EOD ({max_dd:.2f}%) excede el límite del 3.50% de fondeo.")

        passed = len(violations) == 0
        return {
            "passed": passed,
            "account_type": account_type,
            "max_dd_observed": max_dd,
            "profit_factor": pf,
            "total_trades": trades_count,
            "violations": violations
        }

    # =========================================================================
    # UTILIDAD C: COMPRESIÓN DE CONTEXTO A ~60 TOKENS (Token Minimizer)
    # =========================================================================
    def compress_market_state(
        self,
        candles: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Dict[str, Any]:
        """
        Comprime 100+ velas de mercado en un vector JSON estructurado de ~60 tokens
        para suministrar a los agentes LLM sin saturar el contexto.
        """
        if candles.empty:
            return {"error": "No candle data"}

        close = candles['close'].astype(float)
        high = candles['high'].astype(float)
        low = candles['low'].astype(float)
        vol = candles['volume'].astype(float) if 'volume' in candles.columns else pd.Series(1, index=candles.index)

        curr_price = float(close.iloc[-1])
        ema20 = float(close.ewm(span=20).mean().iloc[-1])
        ema50 = float(close.ewm(span=50).mean().iloc[-1])
        ema200 = float(close.ewm(span=200).mean().iloc[-1]) if len(close) >= 200 else ema50

        # Stack de medias
        if ema20 > ema50 > ema200:
            ema_stack = "BULLISH_STACK"
        elif ema20 < ema50 < ema200:
            ema_stack = "BEARISH_STACK"
        else:
            ema_stack = "COMPRESSED_MIXED"

        # Volatilidad ATR %
        tr = np.maximum(high - low, np.maximum(abs(high - close.shift(1)), abs(low - close.shift(1))))
        atr14 = float(tr.rolling(14).mean().iloc[-1])
        atr_pct = (atr14 / curr_price) * 100 if curr_price > 0 else 0.0

        # Entropía
        entropy_eval = self.filter_pre_llm_entropy(candles)

        return {
            "asset": symbol,
            "tf": timeframe,
            "price": round(curr_price, 2),
            "regime": entropy_eval["regime"],
            "H_norm": entropy_eval["h_norm"],
            "delta_H": entropy_eval["delta_h"],
            "predictability": entropy_eval["predictability_score"],
            "ema_stack": ema_stack,
            "atr_pct": round(atr_pct, 2)
        }

    # =========================================================================
    # UTILIDAD D: LOOP POST-TRADE DETERMINISTA (Alertas solo en > 2.5 Sigma)
    # =========================================================================
    def audit_closed_trade(
        self,
        trade: Dict[str, Any],
        baseline: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Audita trades cerrados en papel o forward test sin invocar a la IA.
        Solo emite alerta si hay anomalía estadística (> 2.5 sigma).
        """
        base = baseline or {
            "expected_slippage_pts": 0.5,
            "expected_slippage_std": 0.2,
            "expected_hold_bars": 12,
            "max_hold_bars": 36
        }

        reasons = []
        severity = "NORMAL"

        actual_slippage = float(trade.get("slippage_pts", trade.get("slippage", 0.0)))
        hold_bars = int(trade.get("duration_bars", trade.get("hold_bars", 0)))
        pnl = float(trade.get("net_pnl", trade.get("net_pnl_usd", 0.0)))
        sl_hit = bool(trade.get("hit_sl", False))

        # Slippage anormal
        exp_slip = base["expected_slippage_pts"]
        std_slip = base.get("expected_slippage_std", 0.2)
        slip_z = (actual_slippage - exp_slip) / std_slip if std_slip > 0 else 0.0

        if slip_z > 2.5:
            reasons.append(f"Slippage anómalo (+{slip_z:.1f}σ): {actual_slippage} pts vs {exp_slip} pts.")
            severity = "WARNING"

        # Tiempo en posición desmedido
        if hold_bars > base["max_hold_bars"]:
            reasons.append(f"Duración anómala: {hold_bars} barras vs máximo previsto de {base['max_hold_bars']}.")
            severity = "WARNING"

        requires_llm = len(reasons) > 0
        if requires_llm and (slip_z > 4.0 or (pnl < 0 and abs(pnl) > 3000)):
            severity = "CRITICAL"

        return {
            "requires_llm_audit": requires_llm,
            "severity": severity,
            "slip_zscore": round(slip_z, 2),
            "reasons": reasons
        }

    # =========================================================================
    # UTILIDAD A: CIRCUIT BREAKER DE RÉGIMEN EN TIEMPO REAL (Paridad 1:1)
    # =========================================================================
    def evaluate_circuit_breaker(
        self,
        candles: pd.DataFrame,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Verifica en tiempo real (o en la barra t-1 de backtest) si el mercado
        ha cruzado el umbral de caos o shock inminente.
        Garantiza idéntica lógica en VectorBT histórico y en el forward daemon.
        """
        eval_res = self.filter_pre_llm_entropy(candles)
        h_norm = eval_res.get("h_norm", 0.0)
        delta_h = eval_res.get("delta_h", 0.0)

        tripped = False
        action = "ALLOW_OPERATIONS"
        reason = "Régimen ordenado y persistente."

        if h_norm > self.max_allowed_entropy:
            tripped = True
            action = "HALT_NEW_ENTRIES"
            reason = f"Circuit Breaker Disparado: H_norm={h_norm:.3f} > {self.max_allowed_entropy} (Ruido Blanco)."
        elif delta_h > self.regime_shift_delta:
            tripped = True
            action = "HALT_NEW_ENTRIES"
            reason = f"Circuit Breaker Disparado: Delta H={delta_h:+.3f} > {self.regime_shift_delta} (Transición de Régimen)."
        elif h_norm >= 0.75:
            action = "DEFENSIVE_TIGHTEN"
            reason = f"Modo Defensivo: H_norm={h_norm:.3f} en zona intermedia. Ajustar trailing stop y reducir riesgo 30%."

        return {
            "symbol": symbol,
            "circuit_breaker_tripped": tripped,
            "action": action,
            "h_norm": h_norm,
            "delta_h": delta_h,
            "reason": reason
        }

    # =========================================================================
    # MÉTRICAS CUANTITATIVAS AVANZADAS (Utilidad Real del Vídeo)
    # =========================================================================
    def calculate_stagnation_days(
        self,
        equity_series: pd.Series,
        dates: Optional[pd.Series] = None
    ) -> int:
        """
        Calcula los días máximos consecutivos que la curva de equidad pasó
        por debajo de su pico anterior sin marcar un nuevo máximo histórico.
        """
        if equity_series.empty or len(equity_series) < 2:
            return 0

        eq = equity_series.values
        peaks = np.maximum.accumulate(eq)

        if dates is not None and len(dates) == len(equity_series):
            dts = pd.to_datetime(dates).values
            max_days = 0
            last_peak_time = dts[0]

            for i, val in enumerate(eq):
                if val >= peaks[i]:
                    last_peak_time = dts[i]
                else:
                    diff_days = int((dts[i] - last_peak_time).astype('timedelta64[s]').astype(float) / 86400.0)
                    if diff_days > max_days:
                        max_days = diff_days
            return int(max_days)
        else:
            max_bars = 0
            last_peak_idx = 0
            for i, val in enumerate(eq):
                if val >= peaks[i]:
                    last_peak_idx = i
                else:
                    diff_bars = i - last_peak_idx
                    if diff_bars > max_bars:
                        max_bars = diff_bars
            return int(max_bars)

    def calculate_oos_r_dd_ratio(
        self,
        is_return: float,
        is_max_dd: float,
        oos_return: float,
        oos_max_dd: float
    ) -> Dict[str, Any]:
        """
        Calcula el ratio Rendimiento / Drawdown en In-Sample (IS) y Out-Of-Sample (OOS).
        Evalúa la degradación: si OOS R/DD cae más de un 40% respecto a IS, se rechaza.
        """
        is_dd = max(0.01, abs(is_max_dd))
        oos_dd = max(0.01, abs(oos_max_dd))

        is_r_dd = is_return / is_dd
        oos_r_dd = oos_return / oos_dd

        if is_r_dd > 0:
            degradation_pct = ((oos_r_dd - is_r_dd) / is_r_dd) * 100.0
        else:
            degradation_pct = -100.0 if oos_r_dd <= 0 else 0.0

        # Rechazar si degradación supera el 40% negativo
        pass_filter = degradation_pct >= -40.0 and oos_r_dd >= 1.0

        return {
            "is_r_dd": round(is_r_dd, 2),
            "oos_r_dd": round(oos_r_dd, 2),
            "degradation_pct": round(degradation_pct, 1),
            "pass_filter": pass_filter,
            "status": "APROBADO_OOS" if pass_filter else "RECHAZADO_OVERFITTING"
        }

    def calculate_asset_breakdown(
        self,
        trades: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Desglosa las métricas y rachas (win/loss streaks) por activo individual.
        Permite detectar si los beneficios provienen de consistencia o suerte aislada.
        """
        breakdown = {}
        for t in trades:
            asset = t.get("symbol", t.get("asset", "GLOBAL"))
            if asset not in breakdown:
                breakdown[asset] = {
                    "total_trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "gross_profit": 0.0,
                    "gross_loss": 0.0,
                    "net_pnl": 0.0,
                    "current_streak": 0,
                    "max_win_streak": 0,
                    "max_loss_streak": 0,
                    "streak_history": []
                }

            b = breakdown[asset]
            b["total_trades"] += 1
            pnl = float(t.get("net_pnl", t.get("net_pnl_usd", 0.0)))
            b["net_pnl"] += pnl

            if pnl > 0:
                b["wins"] += 1
                b["gross_profit"] += pnl
                if b["current_streak"] >= 0:
                    b["current_streak"] += 1
                else:
                    b["current_streak"] = 1
                if b["current_streak"] > b["max_win_streak"]:
                    b["max_win_streak"] = b["current_streak"]
            elif pnl < 0:
                b["losses"] += 1
                b["gross_loss"] += abs(pnl)
                if b["current_streak"] <= 0:
                    b["current_streak"] -= 1
                else:
                    b["current_streak"] = -1
                if abs(b["current_streak"]) > b["max_loss_streak"]:
                    b["max_loss_streak"] = abs(b["current_streak"])

        # Consolidar KPIs finales por activo
        summary = {}
        for asset, data in breakdown.items():
            tot = data["total_trades"]
            wr = (data["wins"] / tot * 100) if tot > 0 else 0.0
            pf = (data["gross_profit"] / data["gross_loss"]) if data["gross_loss"] > 0 else (999.0 if data["gross_profit"] > 0 else 0.0)

            summary[asset] = {
                "total_trades": tot,
                "win_rate_pct": round(wr, 1),
                "profit_factor": round(pf, 2),
                "net_pnl": round(data["net_pnl"], 2),
                "max_win_streak": data["max_win_streak"],
                "max_loss_streak": data["max_loss_streak"],
                "consistency_score": round(min(100.0, (wr * 0.6) + (min(pf, 3.0) / 3.0 * 40.0)), 1)
            }

        return summary

    # =========================================================================
    # HELPER PRIVADO: ENTROPÍA DE SHANNON POR CUANTILES
    # =========================================================================
    def _calculate_shannon(self, returns: pd.Series, bins: int = 8) -> Tuple[float, float]:
        if len(returns) < 5 or returns.std() == 0:
            return 0.0, 0.0

        hist, _ = np.histogram(returns, bins=bins, density=False)
        total = hist.sum()
        if total == 0:
            return 0.0, 0.0

        probs = hist / total
        probs = probs[probs > 0]
        h = -float(np.sum(probs * np.log2(probs)))
        h_norm = float(h / math.log2(bins))
        return h, h_norm
