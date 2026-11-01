#!/usr/bin/env python3
"""
Orquestador del Ciclo Cuantitativo de Alfas Híbridos (Fases 1 a 5 Completas)
AlgrokQuant · Jev Quantitative Engine

Pipeline Integral:
1. Fase 1: Fábrica de Señales Híbridas (Macro Lineal + Régimen Entropía + Gatillo Simbólico).
2. Fase 2: Minado Matricial Masivo en Numba (Fast-Kill trades >= 50, PnL > 0, Max DD).
3. Fase 3: Auditoría Matemática (Deflated Sharpe Ratio DSR de López de Prado + Monte Carlo 1.000 runs).
4. Fase 4: Auditoría Destructiva @Skeptic (Latencia 1 barra y fricción 1.5x) + Compresión de Contexto.
5. Fase 5: Auto-Deploy Inmediato a Forward Test ($1.000 virtual) y Despacho Telegram @AlphaReporter.
"""

import sys
import json
import time
import argparse
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))
if "/root/AlgrokQuant" not in sys.path:
    sys.path.insert(0, "/root/AlgrokQuant")

from scripts.fast_matrix_miner import run_matrix_miner
from jev.simulator import load_market_data, extract_candidate_trade_pnls
from jev.metrics import audit_candidate_robustness
from jev.agent_protocol import run_skeptic_destructive_stress, compress_candidate_context
from jev.auto_deployer import auto_deploy_strategy, dispatch_governance_rejection_report


def execute_hybrid_cycle(
    asset: str = "NDX",
    mode: str = "CAPITAL_PROPIO",
    max_combinations: int = 5000,
    top_n: int = 5
):
    print("\n" + "="*85)
    print(f"ALGROKQUANT HYBRID ALPHA CYCLE · {asset} [{mode}]")
    print(f"Horario: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print("="*85)

    # 1 & 2. Minado Matricial Rápido (Fases 1 y 2)
    top_candidates = run_matrix_miner(
        asset=asset,
        desk_mode=mode,
        max_candidates=max_combinations,
        top_n=top_n
    )

    if not top_candidates:
        print(f"[INFO] Cero candidatos superaron el filtro Fast-Kill en {asset} ({mode}).")
        return

    # 3. Auditoría Estadística de Robustez (Fase 3: DSR + Monte Carlo)
    df = load_market_data(asset, desk_mode=mode)
    approved_candidates = []
    audits_phase3 = []

    print("\n--- EJECUTANDO FASE 3: DEFLATED SHARPE RATIO & MONTE CARLO 1.000 RUNS ---")
    for cand in top_candidates:
        t_pnls = extract_candidate_trade_pnls(cand, df)
        audit_res = audit_candidate_robustness(
            candidate=cand,
            trade_pnls=t_pnls,
            n_trials_screened=max_combinations,
            desk_mode=mode
        )
        audits_phase3.append(audit_res)

        print(f"\nCandidato: {cand['candidate_id']}")
        print(f"  Sharpe: {cand['sharpe']} | DSR: {audit_res['dsr_prob']} ({audit_res['dsr_details']['verdict']})")
        print(f"  MC P95 DD: {audit_res['mc_p95_dd']}% | Ruina: {audit_res['mc_ruin_prob']}% ({audit_res['mc_details']['verdict']})")

        # 4. Auditoría Destructiva @Skeptic (Fase 4)
        if audit_res["overall_status"] == "APPROVED_PHASE_3":
            print("  -> Supera Fase 3. Ejecutando examen destructivo de @Skeptic...")
            skeptic_res = run_skeptic_destructive_stress(cand, df)
            print(f"  @Skeptic: {skeptic_res['verdict']}")

            if skeptic_res["skeptic_pass"]:
                print(f"  >>> CANDIDATO APROBADO UNÁNIMEMENTE: {cand['candidate_id']} <<<")
                approved_candidates.append((cand, audit_res, skeptic_res))
            else:
                print(f"  [RECHAZADO] Colapsó en la prueba de estrés de @Skeptic.")

    # 5. Auto-Despliegue a Forward Test o Informe de Rechazo (Fase 5)
    if approved_candidates:
        print(f"\n{'*'*85}")
        print(f"AUTO-DESPLEGANDO {len(approved_candidates)} ESTRATEGIAS APROBADAS A FORWARD TEST")
        print(f"{'*'*85}")
        for cand, a_res, s_res in approved_candidates:
            auto_deploy_strategy(cand, a_res, s_res)
    else:
        print(f"\n[GOBERNANZA] Ningún candidato superó el 100% de los filtros de robustez.")
        dispatch_governance_rejection_report(
            asset=asset,
            mode=mode,
            total_screened=max_combinations,
            top_candidates=top_candidates,
            audits=audits_phase3
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestador del Ciclo Cuantitativo de Alfas Híbridos")
    parser.add_argument("--asset", type=str, default="NDX", help="Activo a evaluar (NDX, EURUSD, BTC, etc.)")
    parser.add_argument("--mode", type=str, default="CAPITAL_PROPIO", choices=["CAPITAL_PROPIO", "PROP_FIRM"], help="Régimen de gobernanza")
    parser.add_argument("--max", type=int, default=5000, help="Número de combinaciones a evaluar en minado matricial")
    parser.add_argument("--top", type=int, default=5, help="Número de candidatos finalistas para auditoría")

    args = parser.parse_args()
    execute_hybrid_cycle(
        asset=args.asset,
        mode=args.mode,
        max_combinations=args.max,
        top_n=args.top
    )
