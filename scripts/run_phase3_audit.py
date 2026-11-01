#!/usr/bin/env python3
"""
Ejecutor de Auditoría Estadística Fase 3 (DSR + Monte Carlo 1.000 Runs)
AlgrokQuant · Jev Quantitative Engine

Toma los mejores finalistas de Fase 2 (fast_matrix_miner), reconstruye
su serie de retornos trade a trade y aplica:
1. Deflated Sharpe Ratio (DSR) de López de Prado penalizando por N pruebas.
2. Monte Carlo Bootstrap (1.000 simulaciones).
3. Dictamen oficial de robustez matemática para pasar al enjambre.
"""

import sys
import json
import time
from pathlib import Path
import numpy as np

sys.path.insert(0, '/root/AlgrokQuant')
base_dir = Path(__file__).resolve().parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from jev.metrics import audit_candidate_robustness
from jev.hybrid_signals import HybridSignalFactory, calc_atr_fast
from jev.simulator import load_market_data, extract_candidate_trade_pnls


def run_phase3_audit_on_report(report_json_path: Path):
    if not report_json_path.exists():
        print(f"No existe el archivo {report_json_path}")
        return

    with open(report_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    asset = data["asset"]
    mode = data["desk_mode"]
    total_screened = data.get("total_evaluated", 5000)
    top_candidates = data.get("top_candidates", [])

    print(f"\n{'='*75}")
    print(f"AUDITORÍA ESTADÍSTICA FASE 3 · {asset} [{mode}]")
    print(f"Total combinaciones previas evaluadas: {total_screened}")
    print(f"{'='*75}")

    df = load_market_data(asset, desk_mode=mode)
    audited_results = []

    for idx, cand in enumerate(top_candidates[:5]):
        t_pnls = extract_candidate_trade_pnls(cand, df)
        print(f"\nAuditando #{idx+1} {cand['candidate_id']} ({len(t_pnls)} trades)...")

        audit_res = audit_candidate_robustness(
            candidate=cand,
            trade_pnls=t_pnls,
            n_trials_screened=total_screened,
            desk_mode=mode
        )

        audited_results.append(audit_res)

        print(f"  Observed Sharpe: {audit_res['observed_sharpe']}")
        print(f"  DSR Probabilidad: {audit_res['dsr_prob']} | Z-Stat: {audit_res['z_stat']} -> {audit_res['dsr_details']['verdict']}")
        print(f"  Monte Carlo P95 DD: {audit_res['mc_p95_dd']}% | Ruin Prob: {audit_res['mc_ruin_prob']}% -> {audit_res['mc_details']['verdict']}")
        print(f"  >>> DICTAMEN OFICIAL: {audit_res['overall_status']} <<<")

    # Guardar resultados auditados
    out_file = report_json_path.parent / f"phase3_audit_{asset}_{mode.lower()}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "asset": asset,
            "desk_mode": mode,
            "n_trials": total_screened,
            "audited_candidates": audited_results
        }, f, indent=2)

    print(f"\nResultados guardados en: {out_file}")


if __name__ == "__main__":
    rep_dir = Path("/root/AlgrokQuant/reports")
    run_phase3_audit_on_report(rep_dir / "fast_matrix_NDX_capital_propio_top.json")
    run_phase3_audit_on_report(rep_dir / "fast_matrix_NDX_prop_firm_top.json")
