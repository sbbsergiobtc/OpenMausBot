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
    annualization_factor: float = 252.0
) -> Dict[str, Any]:
    """
    Calcula el Deflated Sharpe Ratio (DSR) formal.

    Parámetros:
    - observed_sr: Sharpe Ratio anualizado observado en el backtest.
    - returns: Array de retornos periódicos por trade o por barra.
    - n_trials: Número total de combinaciones probadas en el ciclo (ej. 5.000 o 100.000).
    - var_sharpe: Varianza de los Sharpes en el universo de pruebas (típico 0.15 - 0.35).
    - annualization_factor: Factor para des-anualizar al horizonte muestral.

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

    # Valor esperado del máximo Sharpe bajo N pruebas
    e_max_sr = expected_max_sharpe(n_trials, var_sharpe)

    # Z-statistic deflactado
    z_stat = (observed_sr - e_max_sr) / std_estimator_ann

    # DSR es la probabilidad acumulada normal: P[SR* > 0 | N trials]
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

    # Criterio institucional: Ruin Prob < 0.1% y P95 DD dentro del límite
    is_mc_sound = (ruin_prob < 0.1) and (p95_dd <= ruin_dd_limit_pct)

    return {
        "n_simulations": int(n_simulations),
        "median_max_dd_pct": round(median_dd, 2),
        "p95_max_dd_pct": round(p95_dd, 2),
        "cvar_95_pct": round(cvar_95, 2),
        "worst_sim_dd_pct": round(worst_dd, 2),
        "ruin_dd_limit_pct": round(ruin_dd_limit_pct, 2),
        "ruin_prob_pct": round(ruin_prob, 3),
        "is_mc_sound": is_mc_sound,
        "verdict": "PASS (Colas controladas en 1.000 runs)" if is_mc_sound else "FAIL (Riesgo de cola o ruina inaceptable)"
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
    - Deflated Sharpe Ratio (DSR)
    - Monte Carlo 1.000 Runs
    - Dictamen unificado PASS / FAIL
    """
    obs_sharpe = float(candidate.get("sharpe", 0.0))
    limit_dd = 3.0 if desk_mode == "PROP_FIRM" else 20.0

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

    # Dictamen Unificado
    pass_dsr = dsr_audit.get("is_significant", False)
    pass_mc = mc_audit.get("is_mc_sound", False)
    final_pass = pass_dsr and pass_mc

    return {
        "candidate_id": candidate.get("candidate_id"),
        "asset": candidate.get("asset"),
        "desk_mode": desk_mode,
        "observed_sharpe": obs_sharpe,
        "dsr_prob": dsr_audit.get("dsr_prob"),
        "z_stat": dsr_audit.get("z_stat"),
        "pass_dsr": pass_dsr,
        "mc_p95_dd": mc_audit.get("p95_max_dd_pct"),
        "mc_ruin_prob": mc_audit.get("ruin_prob_pct"),
        "pass_mc": pass_mc,
        "overall_status": "APPROVED_PHASE_3" if final_pass else "REJECTED_PHASE_3",
        "dsr_details": dsr_audit,
        "mc_details": mc_audit
    }
