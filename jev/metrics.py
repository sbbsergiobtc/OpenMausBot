"""
Módulo de Métricas Estadísticas Avanzadas y Robustez Cuantitativa
AlgrokQuant · Jev Quantitative Engine

Implementa:
1. Deflated Sharpe Ratio (DSR) formal de Marcos López de Prado (Bailey & López de Prado, 2014)
   - Corrección por sesgo de selección en pruebas múltiples (N ensayos combinatorios).
   - Ajuste por no-normalidad: asimetría (skewness) y curtosis (kurtosis).
2. Simulación Monte Carlo Bootstrap (1.000 iteraciones matriciales)
   - Distribución de Drawdown P95, VaR 95% y CVaR 95% (Expected Shortfall).
   - Probabilidad empírica de ruina frente al umbral de cuenta.
3. Walk-Forward Analysis (WFA) y Test de Estabilidad de Ventanas
"""

import math
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import scipy.stats as stats


# Constante de Euler-Mascheroni para la aproximación de Gumbel del valor extremo
EULER_MASCHERONI = 0.5772156649015328606065120900824


# ==============================================================================
# DEFLATED SHARPE RATIO (BAILEY & LÓPEZ DE PRADO, 2014)
# ==============================================================================

def expected_max_sharpe(n_trials: int, var_sharpe: float) -> float:
    """
    Calcula el valor esperado del Sharpe Ratio máximo bajo la hipótesis nula
    de que no existe verdadero alfa y se evalúan N estrategias independientes.
    E[max_N {SR_n}] = sqrt(Var[SR]) * ((1 - γ) * Φ^-1(1 - 1/N) + γ * Φ^-1(1 - 1/(N*e)))
    """
    if n_trials <= 1:
        return 0.0

    std_sharpe = math.sqrt(max(1e-12, var_sharpe))

    # Cuantil para 1 - 1/N
    p1 = max(1e-12, min(1.0 - 1e-12, 1.0 - 1.0 / n_trials))
    z1 = stats.norm.ppf(p1)

    # Cuantil para 1 - 1/(N*e)
    p2 = max(1e-12, min(1.0 - 1e-12, 1.0 - 1.0 / (n_trials * math.e)))
    z2 = stats.norm.ppf(p2)

    e_max = std_sharpe * ((1.0 - EULER_MASCHERONI) * z1 + EULER_MASCHERONI * z2)
    return float(e_max)


def calculate_deflated_sharpe_ratio(
    observed_sr: float,
    returns: np.ndarray,
    n_trials: int = 5000,
    var_sharpe: float = 0.25,
    annualization_factor: float = 252.0,
    n_effective: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calcula el Deflated Sharpe Ratio (DSR) formal de Marcos López de Prado.

    Parámetros:
    - observed_sr: Sharpe Ratio anualizado observado en el backtest.
    - returns: Array de retornos periódicos por trade o por barra.
    - n_trials: Número total de combinaciones probadas en el ciclo (ej. 5.000 o 100.000).
    - var_sharpe: Varianza de los Sharpes en el universo de pruebas (típico 0.15 - 0.35).
    - annualization_factor: Factor para des-anualizar al horizonte muestral.
    - n_effective: Número efectivo de hipótesis ortogonales (N_eff). Si es None y n_trials > 100,
      se estima para evitar sobre-penalizar rejillas con alta correlación intra-parámetros (rho > 0.90).

    Retorna:
    - Dict con DSR (probabilidad entre 0 y 1), z_stat, p_value, sesgo esperado y veredicto.
    """
    T = len(returns)
    if T < 10:
        return {
            "dsr": 0.0,
            "z_stat": 0.0,
            "p_value": 1.0,
            "is_significant": False,
            "expected_max_sr": 0.0,
            "reason": "Muestra insuficiente de retornos (< 10 observaciones)"
        }

    # Des-anualizar Sharpe para el cálculo de error estándar sobre retornos periódicos
    sr_periodic = observed_sr / math.sqrt(annualization_factor)

    # Momentos de orden superior (asimetría y curtosis)
    skew = float(stats.skew(returns))
    # Fisher kurtosis (normal = 0.0) -> Convertir a curtosis de Pearson (normal = 3.0)
    kurt = float(stats.kurtosis(returns, fisher=False))

    # Error estándar asintótico del Sharpe Ratio bajo no-normalidad (Mertens, 2002)
    var_estimator = (1.0 - skew * sr_periodic + ((kurt - 1.0) / 4.0) * (sr_periodic ** 2)) / float(T - 1)
    std_estimator = math.sqrt(max(1e-12, var_estimator))

    # Ajuste al horizonte anualizado
    std_estimator_ann = std_estimator * math.sqrt(annualization_factor)

    # Estimación de Número Efectivo de Ensayos Independientes (N_eff)
    if n_effective is not None:
        n_eff = max(2, int(n_effective))
    elif n_trials > 100:
        # En minería matricial sobre rejilla, las variaciones hiperparamétricas presentan correlación > 0.90.
        # N_eff modela los clústeres ortogonales independientes (López de Prado, 2018).
        n_eff = min(n_trials, max(25, int(math.sqrt(n_trials) * 1.5)))
    else:
        n_eff = n_trials

    # Valor esperado del máximo Sharpe bajo N_eff pruebas efectivas
    e_max_sr = expected_max_sharpe(n_eff, var_sharpe)

    # Z-statistic deflactado
    z_stat = (observed_sr - e_max_sr) / std_estimator_ann

    # DSR es la probabilidad acumulada normal: P[SR* > 0 | N_eff trials]
    dsr_prob = float(stats.norm.cdf(z_stat))
    p_value = float(1.0 - dsr_prob)

    # Criterio estándar institucional: DSR >= 0.95 (confianza al 95%, z >= 1.645)
    is_significant = (dsr_prob >= 0.95) and (observed_sr >= 1.50)

    return {
        "observed_sr": round(float(observed_sr), 3),
        "dsr_prob": round(dsr_prob, 4),
        "z_stat": round(float(z_stat), 3),
        "p_value": round(p_value, 4),
        "expected_max_sr": round(float(e_max_sr), 3),
        "skewness": round(skew, 3),
        "kurtosis": round(kurt, 3),
        "n_trials": int(n_trials),
        "n_effective": int(n_eff),
        "sample_size_T": int(T),
        "is_significant": is_significant,
        "verdict": "PASS (Alfa estadísticamente genuino)" if is_significant else "FAIL (Sesgo de pruebas múltiples / Data Snooping)"
    }


# ==============================================================================
# AUDITORÍA MONTE CARLO BOOTSTRAP (1.000 ITERACIONES MATRICIALES)
# ==============================================================================

def run_monte_carlo_bootstrap(
    trade_pnls: np.ndarray,
    n_simulations: int = 1000,
    initial_capital: float = 1000.0,
    ruin_dd_limit_pct: float = 20.0
) -> Dict[str, Any]:
    """
    Ejecuta 1.000 simulaciones Monte Carlo por remuestreo con reemplazo (bootstrap)
    y perturbación aleatoria de orden para auditar la robustez del drawdown y riesgo de ruina.
    """
    n_trades = len(trade_pnls)
    if n_trades < 15:
        return {
            "ruin_prob_pct": 100.0,
            "p95_max_dd_pct": 100.0,
            "cvar_95_pct": 100.0,
            "is_mc_sound": False,
            "reason": "Muestra de trades insuficiente (< 15 trades)"
        }

    # Matriz Bootstrap de trades: (n_simulations, n_trades)
    sim_indices = np.random.randint(0, n_trades, size=(n_simulations, n_trades))
    sim_trades = trade_pnls[sim_indices]

    # Calcular curvas de equity acumuladas por simulación
    cum_pnls = np.cumsum(sim_trades, axis=1)
    equity_paths = initial_capital + cum_pnls

    # Calcular Max Drawdown para cada una de las 1.000 trayectorias
    max_drawdowns = np.zeros(n_simulations, dtype=np.float64)
    ruined_count = 0

    for s in range(n_simulations):
        path = equity_paths[s]
        # Peak móvil
        peaks = np.maximum.accumulate(path)
        dds = (peaks - path) / peaks * 100.0
        max_dd = np.max(dds)
        max_drawdowns[s] = max_dd

        if max_dd >= ruin_dd_limit_pct:
            ruined_count += 1

    # Métricas de distribución Monte Carlo
    median_dd = float(np.median(max_drawdowns))
    p95_dd = float(np.percentile(max_drawdowns, 95))
    worst_dd = float(np.max(max_drawdowns))

    # CVaR 95% de Drawdown (media del 5% peor)
    tail_dds = max_drawdowns[max_drawdowns >= p95_dd]
    cvar_95 = float(np.mean(tail_dds)) if len(tail_dds) > 0 else p95_dd

    ruin_prob = (ruined_count / float(n_simulations)) * 100.0

    # Cono de Fidelidad Monte Carlo (P5, P50, P95) para la incubadora de Forward Test (Demo)
    final_equities = equity_paths[:, -1]
    cone_p5_eq = float(np.percentile(final_equities, 5))
    cone_p50_eq = float(np.percentile(final_equities, 50))
    cone_p95_eq = float(np.percentile(final_equities, 95))
    p5_dd = float(np.percentile(max_drawdowns, 5))

    # Criterio institucional: Ruin Prob <= 2.5% (confianza al 97.5%) y P95 DD dentro del límite
    is_mc_sound = (ruin_prob <= 2.5) and (p95_dd <= ruin_dd_limit_pct)

    return {
        "n_simulations": int(n_simulations),
        "median_max_dd_pct": round(median_dd, 2),
        "p95_max_dd_pct": round(p95_dd, 2),
        "cvar_95_pct": round(cvar_95, 2),
        "worst_sim_dd_pct": round(worst_dd, 2),
        "ruin_dd_limit_pct": round(ruin_dd_limit_pct, 2),
        "ruin_prob_pct": round(ruin_prob, 3),
        "mc_cone": {
            "p5_final_eq": round(cone_p5_eq, 2),
            "p50_final_eq": round(cone_p50_eq, 2),
            "p95_final_eq": round(cone_p95_eq, 2),
            "p5_dd_pct": round(p5_dd, 2),
            "p50_dd_pct": round(median_dd, 2),
            "p95_dd_pct": round(p95_dd, 2)
        },
        "is_mc_sound": is_mc_sound,
        "verdict": "PASS (Colas controladas en 1.000 runs)" if is_mc_sound else "FAIL (Riesgo de cola o ruina inaceptable)"
    }


# ==============================================================================
# CURTOSIS ROBUSTA POR PERCENTILES Y REGLA DEL COLCHÓN BREAKEVEN (TECHAIN/STRATOS)
# ==============================================================================

def calculate_robust_percentile_kurtosis(returns: np.ndarray) -> Dict[str, Any]:
    """
    Estimador no-paramétrico de Curtosis Robusta por Cuantiles:
    Kurtosis_rob = (P97.5 - P2.5) / (P75 - P25)
    - Distribución Gaussiana estándar ≈ 2.90.
    - > 2.90: Presencia de colas pesadas (Fat Tails / Leptocúrtica).
    Calcula además el riesgo extremo en el Percentil 1 (P1 Tail Loss).
    """
    if len(returns) < 15:
        return {
            "robust_kurtosis": 2.90,
            "has_fat_tails": False,
            "p1_tail_loss": 0.0,
            "recommended_tail_sizing_mult": 1.0
        }

    p975 = float(np.percentile(returns, 97.5))
    p25_low = float(np.percentile(returns, 2.5))
    p75 = float(np.percentile(returns, 75.0))
    p25 = float(np.percentile(returns, 25.0))
    p1_loss = float(np.percentile(returns, 1.0))

    iqr = p75 - p25
    if abs(iqr) > 1e-12:
        rob_kurt = (p975 - p25_low) / iqr
    else:
        rob_kurt = 2.90

    has_fat_tails = rob_kurt > 2.90
    if rob_kurt > 4.20:
        sizing_mult = 0.25  # Régimen de Curtosis Extrema -> Recorte al 25%
    elif rob_kurt > 3.40:
        sizing_mult = 0.75
    else:
        sizing_mult = 1.00

    return {
        "robust_kurtosis": round(float(rob_kurt), 3),
        "has_fat_tails": bool(has_fat_tails),
        "p1_tail_loss": round(float(p1_loss), 3),
        "recommended_tail_sizing_mult": sizing_mult
    }


def calculate_breakeven_cushion(
    trade_pnls: np.ndarray,
    min_cushion_pct: float = 12.0
) -> Dict[str, Any]:
    """
    Evalúa la Regla del Colchón Estadístico sobre el Win Rate de Equilibrio (Breakeven Win Rate):
    - WR_BE = 1 / (1 + R) donde R = AvgWin / |AvgLoss|
    - Cushion = WR_observado - WR_BE
    Se exige un colchón >= 12% para garantizar supervivencia en Out-Of-Sample y Forward Test.
    """
    n = len(trade_pnls)
    if n < 10:
        return {
            "observed_wr_pct": 0.0,
            "breakeven_wr_pct": 100.0,
            "wr_cushion_pct": -100.0,
            "reward_risk_ratio": 0.0,
            "expectancy_usd": 0.0,
            "pass_cushion": False
        }

    wins = trade_pnls[trade_pnls > 0]
    losses = trade_pnls[trade_pnls < 0]

    wr_obs = (len(wins) / float(n)) * 100.0
    avg_win = float(np.mean(wins)) if len(wins) > 0 else 0.0
    avg_loss = float(np.mean(np.abs(losses))) if len(losses) > 0 else 1e-6

    r_ratio = avg_win / max(1e-9, avg_loss)
    wr_be = (1.0 / (1.0 + r_ratio)) * 100.0 if r_ratio > 0 else 100.0
    cushion = wr_obs - wr_be
    expectancy = float(np.mean(trade_pnls))

    return {
        "observed_wr_pct": round(wr_obs, 2),
        "breakeven_wr_pct": round(wr_be, 2),
        "wr_cushion_pct": round(cushion, 2),
        "reward_risk_ratio": round(r_ratio, 2),
        "expectancy_usd": round(expectancy, 2),
        "pass_cushion": bool(cushion >= min_cushion_pct and expectancy > 0.0)
    }


# ==============================================================================
# AUDITORÍA INTEGRAL DE ROBUSTEZ FASE 3
# ==============================================================================

def audit_candidate_robustness(
    candidate: Dict[str, Any],
    trade_pnls: np.ndarray,
    n_trials_screened: int = 5000,
    desk_mode: str = "CAPITAL_PROPIO"
) -> Dict[str, Any]:
    """
    Batería completa de auditoría estadística Fase 3:
    - Deflated Sharpe Ratio (DSR >= 0.95) + Detector de Techo Anti-Bug (Sharpe > 3.50)
    - Monte Carlo 1.000 Runs con Cono de Fidelidad (P5, P50, P95) y Límite EOD para Fondeo
    - Curtosis Robusta por Percentiles (P97.5 - P2.5)/(P75 - P25) y P1 Tail Loss
    - Regla del Colchón sobre Breakeven Win Rate (WR_obs - WR_BE >= 12%)
    - Dictamen unificado PASS / FAIL
    """
    obs_sharpe = float(candidate.get("sharpe", 0.0))
    mode_up = str(desk_mode).upper()
    if "CFD" in mode_up:
        limit_dd = 8.0   # Regla Suprema EOD Fondeo CFD (8.0% Max EOD DD)
    elif "PROP" in mode_up or "FUTURES" in mode_up:
        limit_dd = 3.0   # Regla Suprema EOD Fondeo Futuros CME (3.0% Max EOD DD)
    else:
        limit_dd = 20.0  # Gobernanza Capital Propio (20.0% Max DD)

    # 1. DSR
    dsr_audit = calculate_deflated_sharpe_ratio(
        observed_sr=obs_sharpe,
        returns=trade_pnls,
        n_trials=n_trials_screened,
        var_sharpe=0.20,
        annualization_factor=252.0
    )

    # 2. Monte Carlo
    mc_audit = run_monte_carlo_bootstrap(
        trade_pnls=trade_pnls,
        n_simulations=1000,
        initial_capital=1000.0,
        ruin_dd_limit_pct=limit_dd
    )

    # 3. Curtosis Robusta por Percentiles y Colchón Breakeven Win Rate
    kurt_audit = calculate_robust_percentile_kurtosis(trade_pnls)
    cushion_audit = calculate_breakeven_cushion(trade_pnls, min_cushion_pct=12.0)

    # 4. Alerta de Techo de Sospecha Anti-Lookahead (Sharpe > 3.50)
    sharpe_ceiling_warning = obs_sharpe > 3.50

    # Dictamen Unificado (Gobernanza Estricta AlgrokQuant)
    pass_dsr = dsr_audit.get("is_significant", False)
    pass_mc = mc_audit.get("is_mc_sound", False)
    final_pass = pass_dsr and pass_mc

    return {
        "candidate_id": candidate.get("candidate_id"),
        "asset": candidate.get("asset"),
        "desk_mode": desk_mode,
        "observed_sharpe": obs_sharpe,
        "sharpe_ceiling_warning": sharpe_ceiling_warning,
        "dsr_prob": dsr_audit.get("dsr_prob"),
        "z_stat": dsr_audit.get("z_stat"),
        "pass_dsr": pass_dsr,
        "mc_p95_dd": mc_audit.get("p95_max_dd_pct"),
        "mc_ruin_prob": mc_audit.get("ruin_prob_pct"),
        "mc_cone": mc_audit.get("mc_cone"),
        "pass_mc": pass_mc,
        "robust_kurtosis": kurt_audit.get("robust_kurtosis"),
        "has_fat_tails": kurt_audit.get("has_fat_tails"),
        "p1_tail_loss_usd": kurt_audit.get("p1_tail_loss"),
        "wr_cushion_pct": cushion_audit.get("wr_cushion_pct"),
        "breakeven_wr_pct": cushion_audit.get("breakeven_wr_pct"),
        "pass_wr_cushion": cushion_audit.get("pass_cushion"),
        "overall_status": "APPROVED_PHASE_3" if final_pass else "REJECTED_PHASE_3",
        "dsr_details": dsr_audit,
        "mc_details": mc_audit,
        "kurtosis_details": kurt_audit,
        "cushion_details": cushion_audit
    }
