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
from jev.metrics import audit_candidate_robustness
from jev.hybrid_signals import HybridSignalFactory, calc_atr_fast
from scripts.fast_matrix_miner import load_market_data


def extract_candidate_trade_pnls(candidate: dict, df) -> np.ndarray:
    """Reconstruye el array de PnLs individuales de cada trade del candidato."""
    close = np.ascontiguousarray(df["close"].values, dtype=np.float64)
    high = np.ascontiguousarray(df["high"].values, dtype=np.float64)
    low = np.ascontiguousarray(df["low"].values, dtype=np.float64)
    open_p = np.ascontiguousarray(df["open"].values, dtype=np.float64)
    volume = np.ascontiguousarray(df["volume"].values, dtype=np.float64)
    atr = calc_atr_fast(high, low, close, 14)

    factory = HybridSignalFactory(open_p, high, low, close, volume)
    l_mask, s_mask = factory.generate_signal(
        macro_anchor=candidate["macro_anchor"],
        entropy_max=candidate["entropy_max"],
        symbolic_trigger=candidate["symbolic_trigger"],
        param1=candidate["param1"],
        param2=candidate["param2"],
        trigger_threshold=candidate["trigger_threshold"]
    )

    friction = 0.0006 if any(k in candidate["asset"].upper() for k in ["NDX", "SPX"]) else 0.0014
    sl_m = float(candidate["sl_atr_mult"])
    tp_m = float(candidate["tp_atr_mult"])
    max_h = 48

    # Reconstruir lista de trades individual
    n = len(close)
    in_pos = 0
    entry_px = 0.0
    sl_px = 0.0
    tp_px = 0.0
    bars_held = 0
    trade_pnls = []
    running_eq = 1000.0

    for i in range(1, n):
        if in_pos == 1:
            bars_held += 1
            exit_trade = False
            exit_px = 0.0
            if low[i] <= sl_px:
                exit_px = sl_px
                exit_trade = True
            elif high[i] >= tp_px:
                exit_px = tp_px
                exit_trade = True
            elif bars_held >= max_h:
                exit_px = close[i]
                exit_trade = True

            if exit_trade:
                net_ret = (exit_px - entry_px) / entry_px - friction
                pnl = running_eq * net_ret
                running_eq += pnl
                trade_pnls.append(pnl)
                in_pos = 0

        elif in_pos == -1:
            bars_held += 1
            exit_trade = False
            exit_px = 0.0
            if high[i] >= sl_px:
                exit_px = sl_px
                exit_trade = True
            elif low[i] <= tp_px:
                exit_px = tp_px
                exit_trade = True
            elif bars_held >= max_h:
                exit_px = close[i]
                exit_trade = True

            if exit_trade:
                net_ret = (entry_px - exit_px) / entry_px - friction
                pnl = running_eq * net_ret
                running_eq += pnl
                trade_pnls.append(pnl)
                in_pos = 0

        if in_pos == 0:
            if l_mask[i]:
                in_pos = 1
                entry_px = close[i]
                cur_atr = atr[i] if not np.isnan(atr[i]) else close[i] * 0.01
                sl_px = entry_px - sl_m * cur_atr
                tp_px = entry_px + tp_m * cur_atr
                bars_held = 0
            elif s_mask[i]:
                in_pos = -1
                entry_px = close[i]
                cur_atr = atr[i] if not np.isnan(atr[i]) else close[i] * 0.01
                sl_px = entry_px + sl_m * cur_atr
                tp_px = entry_px - tp_m * cur_atr
                bars_held = 0

    return np.array(trade_pnls, dtype=np.float64)


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
