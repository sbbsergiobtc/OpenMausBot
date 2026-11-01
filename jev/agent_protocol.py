"""
Protocolo de Compresión de Contexto y Auditoría Destructiva de Agentes (Fase 4)
AlgrokQuant · Jev Quantitative Engine

1. Compresión de Contexto: Transforma los resultados de Fase 3 en JSON ultracompacto (~150 tokens/candidato).
2. Examen Destructivo @Skeptic:
   - Inyección forzada de latencia de ejecución (retardo de 1 barra en señales).
   - Estrés severo de fricción y slippage (1.5x y 2.0x comisiones).
3. Validación de Gobernanza @RiskFilter:
   - Sizing 1.0% ($10 USD) sobre balance virtual aislado de $1.000.
   - Verificación de límites de Drawdown según Gobernanza Dual.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np

base_dir = Path(__file__).resolve().parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))
if "/root/AlgrokQuant" not in sys.path:
    sys.path.insert(0, "/root/AlgrokQuant")

from jev.hybrid_signals import HybridSignalFactory, calc_atr_fast
from jev.metrics import calculate_deflated_sharpe_ratio, run_monte_carlo_bootstrap
from jev.simulator import simulate_signals_numba, load_market_data


def compress_candidate_context(cand_audit: Dict[str, Any]) -> str:
    """
    Comprime los datos clave de un candidato auditado a un JSON compacto de ~150 tokens,
    diseñado para alimentar a los agentes LLM sin inflar el consumo de tokens.
    """
    cid = cand_audit.get("candidate_id", "HYB-UNKNOWN")
    dsr = cand_audit.get("dsr_details", {})
    mc = cand_audit.get("mc_details", {})
    
    compact_payload = {
        "id": cid,
        "asset": cand_audit.get("asset"),
        "mode": cand_audit.get("desk_mode"),
        "metrics": {
            "sr_obs": cand_audit.get("observed_sharpe"),
            "dsr_prob": cand_audit.get("dsr_prob"),
            "z_stat": cand_audit.get("z_stat"),
            "mc_p95_dd": cand_audit.get("mc_p95_dd"),
            "mc_ruin_prob": cand_audit.get("mc_ruin_prob")
        },
        "status": cand_audit.get("overall_status")
    }
    return json.dumps(compact_payload, separators=(',', ':'))


def run_skeptic_destructive_stress(
    candidate: Dict[str, Any],
    df
) -> Dict[str, Any]:
    """
    Prueba Destructiva de @Skeptic:
    1. Latencia forzada: Retardo de 1 barra en la entrada (evalúa look-ahead bias y velocidad irrealista).
    2. Estrés de comisiones: Fricción multiplicada por 1.5x y 2.0x.
    """
    close = np.ascontiguousarray(df["close"].values, dtype=np.float64)
    high = np.ascontiguousarray(df["high"].values, dtype=np.float64)
    low = np.ascontiguousarray(df["low"].values, dtype=np.float64)
    open_p = np.ascontiguousarray(df["open"].values, dtype=np.float64)
    volume = np.ascontiguousarray(df["volume"].values, dtype=np.float64)
    atr = calc_atr_fast(high, low, close, 14)

    timestamps = df["time"] if "time" in df.columns else None
    is_equity_index = any(k in candidate["asset"].upper() for k in ["NDX", "SPX", "US500", "USTEC", "NASDAQ"])

    factory = HybridSignalFactory(
        open_p, high, low, close, volume,
        timestamps=timestamps,
        rth_only=is_equity_index,
        long_only=is_equity_index
    )
    l_mask, s_mask = factory.generate_signal(
        macro_anchor=candidate["macro_anchor"],
        entropy_max=candidate["entropy_max"],
        symbolic_trigger=candidate["symbolic_trigger"],
        param1=candidate["param1"],
        param2=candidate["param2"],
        trigger_threshold=candidate["trigger_threshold"]
    )

    base_friction = 0.0006 if any(k in candidate["asset"].upper() for k in ["NDX", "SPX"]) else 0.0014
    sl_m = float(candidate["sl_atr_mult"])
    tp_m = float(candidate["tp_atr_mult"])
    desk_mode = candidate.get("desk_mode", "CAPITAL_PROPIO")
    risk_pct = 0.005 if desk_mode == "PROP_FIRM" else 0.01

    # Test 1: Latencia forzada de 1 barra
    l_delayed = np.zeros_like(l_mask)
    s_delayed = np.zeros_like(s_mask)
    l_delayed[1:] = l_mask[:-1]
    s_delayed[1:] = s_mask[:-1]

    trades_del, pnl_del, wr_del, sr_del, dd_del = simulate_signals_numba(
        close, high, low, atr, l_delayed, s_delayed, sl_m, tp_m, 48, base_friction, risk_pct, 1.2, 0.8
    )

    # Test 2: Estrés de Fricción 1.5x
    trades_f15, pnl_f15, wr_f15, sr_f15, dd_f15 = simulate_signals_numba(
        close, high, low, atr, l_mask, s_mask, sl_m, tp_m, 48, base_friction * 1.5, risk_pct, 1.2, 0.8
    )

    # Test 3: Estrés de Fricción 2.0x
    trades_f20, pnl_f20, wr_f20, sr_f20, dd_f20 = simulate_signals_numba(
        close, high, low, atr, l_mask, s_mask, sl_m, tp_m, 48, base_friction * 2.0, risk_pct, 1.2, 0.8
    )

    # Criterios de Aprobación de @Skeptic:
    # 1. PnL positivo tras 1 barra de retardo.
    # 2. Sharpe con latencia >= 1.0.
    # 3. PnL positivo con comisiones 1.5x.
    pass_latency = (pnl_del > 0.0) and (sr_del >= 1.0)
    pass_friction = (pnl_f15 > 0.0)
    skeptic_pass = pass_latency and pass_friction

    verdict_desc = "PASS (Resiste latencia y fricción severa)" if skeptic_pass else "FAIL (Colapsa ante retardo o comisiones 1.5x)"

    return {
        "candidate_id": candidate.get("candidate_id"),
        "latency_1bar": {
            "pnl": round(float(pnl_del), 2),
            "sharpe": round(float(sr_del), 2),
            "max_dd": round(float(dd_del), 2),
            "passed": pass_latency
        },
        "friction_15x": {
            "pnl": round(float(pnl_f15), 2),
            "sharpe": round(float(sr_f15), 2),
            "passed": (pnl_f15 > 0.0)
        },
        "friction_20x": {
            "pnl": round(float(pnl_f20), 2),
            "sharpe": round(float(sr_f20), 2)
        },
        "skeptic_pass": skeptic_pass,
        "verdict": verdict_desc
    }
