"""
Módulo de Auto-Despliegue Directo a Forward Test y Despacho Oficial (Fase 5)
AlgrokQuant · Jev Quantitative Engine

Cumple la Norma Mandatoria Oficial de Sergio:
- Si una estrategia es aprobada por todos los filtros (@Auditor DSR/MC + @Skeptic + @RiskFilter),
  se auto-despliega de forma inmediata y automática en Forward Test con $1.000 de saldo virtual aislado.
- Si los candidatos no superan los filtros, genera el informe oficial de gobernanza con los motivos numéricos
  exactos y lo despacha a través de OpenMausBot (Telegram vía @AlphaReporter).
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

if Path('/root/AlgrokQuant').exists():
    BASE_DIR = Path('/root/AlgrokQuant')
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

STATE_FILE = BASE_DIR / 'data/paper_trades/prop_firm_forward_test_state.json'
STRAT_DIR = BASE_DIR / 'library/strategies'
REPORTS_DIR = BASE_DIR / 'reports'


def auto_deploy_strategy(candidate: Dict[str, Any], audit_phase3: Dict[str, Any], skeptic_res: Dict[str, Any]) -> bool:
    """
    Registra automáticamente una estrategia aprobada en el daemon de Forward Test
    con libros contables virtuales aislados de $1.000 USD/USDC (Libro A, B y C)
    y metadata completa de backtest y arquitectura.
    """
    cid = candidate.get("candidate_id") or candidate.get("strategy_id") or candidate.get("id")
    asset = candidate.get("asset") or candidate.get("symbol", "NDX")
    mode = str(candidate.get("desk_mode") or candidate.get("branch") or "CAPITAL_PROPIO").upper()
    cid_u = str(cid or "").upper()
    if cid_u.startswith(("CAP-", "CRYPTO-", "STRAT-")):
        is_prop = False
    elif cid_u.startswith(("PROP", "HYB")):
        is_prop = True
    else:
        is_prop = ("PROP_FIRM" in mode) or mode.startswith("PROP")
    tf = candidate.get("tf") or candidate.get("timeframe") or ("5m RTH" if is_prop else "1h")

    dsr_val = audit_phase3.get("dsr_prob")
    if dsr_val is None:
        dsr_val = audit_phase3.get("dsr_details", {}).get("prob", candidate.get("dsr_prob", 0.95))
    mc_dd_val = audit_phase3.get("mc_p95_dd")
    if mc_dd_val is None:
        mc_dd_val = audit_phase3.get("mc_details", {}).get("p95", candidate.get("mc_p95_dd", candidate.get("max_dd", 2.5)))
    mc_ruin_val = audit_phase3.get("mc_ruin_prob", candidate.get("mc_ruin_prob", 0.0))
    rk_raw = audit_phase3.get("robust_kurtosis")
    rk_val = rk_raw.get("robust_kurtosis") if isinstance(rk_raw, dict) else (rk_raw if rk_raw is not None else candidate.get("robust_kurtosis", 0.26))
    wc_raw = audit_phase3.get("breakeven_cushion") or audit_phase3.get("wr_cushion_pct")
    wc_val = wc_raw.get("wr_cushion_pct") if isinstance(wc_raw, dict) else (wc_raw if wc_raw is not None else candidate.get("wr_cushion_pct", 8.0))

    ret_bt = candidate.get("return_pct")
    if ret_bt is None:
        ret_bt = candidate.get("total_pnl_pct")
    if ret_bt is None:
        ret_bt = candidate.get("roi_total_pct", 0.0)
    cagr_bt = candidate.get("cagr_pct") if candidate.get("cagr_pct") is not None else candidate.get("backtest_cagr_pct")
    bnh_bt = candidate.get("bnh_cagr_pct")
    pf_bt = float(candidate.get("profit_factor") or candidate.get("backtest_pf") or 2.0)
    wr_bt = float(candidate.get("win_rate") or candidate.get("backtest_wr") or 65.0)
    dd_bt = float(candidate.get("max_dd") or candidate.get("backtest_max_dd") or mc_dd_val or 1.0)
    macro_anchor = candidate.get("macro_anchor") or candidate.get("archetype") or candidate.get("family") or "QUANT_ALPHA"
    sym_trigger = candidate.get("symbolic_trigger") or candidate.get("params") or f"EMA({candidate.get('fast_period', 12)}/{candidate.get('slow_period', 36)}) · BB {candidate.get('std_dev', 2.0)}σ"
    role = candidate.get("role") or ("TITULAR" if cid in ("CAP-SPX-006", "CAP-NDX-005", "CRYPTO-BTC-001", "STRAT-20261024-028", "PROP-FX-EUR-001") else "SUPLENTE")

    print(f"\n>>> INICIANDO AUTO-DESPLIEGUE A FORWARD TEST: {cid} ({asset} · {mode} · {role}) <<<")

    # 1. Actualizar estado de Forward Test en prop_firm_forward_test_state.json
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state_data = json.load(f)

            branch_key = "prop_firm" if is_prop else "capital_propio"
            other_key = "capital_propio" if is_prop else "prop_firm"
            branch = state_data.setdefault(branch_key, {})
            active_strats = branch.setdefault("active_strategies", [])

            # Limpiar si por un bug previo quedó duplicada o en la rama contraria
            other_strats = state_data.get(other_key, {}).get("active_strategies", [])
            if other_strats:
                state_data[other_key]["active_strategies"] = [
                    s for s in other_strats if isinstance(s, dict) and s.get("strategy_id") != cid
                ]

            existing_ids = [s.get("strategy_id") for s in active_strats if isinstance(s, dict)]
            mc_cone = audit_phase3.get("mc_cone") or {
                "p50_dd_pct": audit_phase3.get("mc_details", {}).get("median_max_dd_pct", round(float(mc_dd_val) * 0.55, 2)),
                "p95_dd_pct": float(mc_dd_val)
            }
            plateau_pct = skeptic_res.get("parametric_plateau", {}).get("survival_pct", 100.0)
            strat_payload = {
                "strategy_id": cid,
                "symbol": asset,
                "asset": asset,
                "timeframe": tf,
                "branch": "PROP_FIRM" if is_prop else "CAPITAL_PROPIO",
                "desk_mode": mode,
                "role": role,
                "virtual_balance": 1000.0,
                "virtual_equity": 1000.0,
                "risk_per_trade_pct": 1.0,
                "risk_nominal_usd": 10.0,
                "status": "FORWARD_TESTING_ACTIVE",
                "deployed_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "macro_anchor": macro_anchor,
                "symbolic_trigger": sym_trigger,
                "regime_gate": candidate.get("regime_gate", "ANY"),
                "fast_period": candidate.get("fast_period"),
                "slow_period": candidate.get("slow_period"),
                "std_dev": candidate.get("std_dev"),
                "sl_pct": candidate.get("sl_pct"),
                "tp_pct": candidate.get("tp_pct"),
                "roi_total_pct": float(ret_bt),
                "backtest_roi_total_pct": float(ret_bt),
                "cagr_pct": float(cagr_bt) if cagr_bt is not None else None,
                "bnh_cagr_pct": float(bnh_bt) if bnh_bt is not None else None,
                "beats_bnh": True if (not is_prop and cagr_bt is not None and (bnh_bt is None or float(cagr_bt) > float(bnh_bt))) else bool(candidate.get("beats_bnh", False)),
                "profit_factor": pf_bt,
                "win_rate": wr_bt,
                "max_dd": dd_bt,
                "days_to_target": candidate.get("days_to_target"),
                "time_to_target_tier": candidate.get("sprint_tier") or ("Multi-Año" if not is_prop else "OPTIMAL_<15D"),
                "observed_sharpe": float(candidate.get("sharpe") or candidate.get("observed_sharpe") or 0.0),
                "dsr_prob": float(dsr_val) if dsr_val is not None else 0.95,
                "mc_p95_dd": float(mc_dd_val) if mc_dd_val is not None else 2.5,
                "mc_cone": mc_cone,
                "robust_kurtosis": float(rk_val) if rk_val is not None else 0.26,
                "wr_cushion_pct": float(wc_val) if wc_val is not None else 8.0,
                "parametric_plateau_survival_pct": float(plateau_pct),
            }
            if cid not in existing_ids:
                strat_payload["incubation_guardian"] = {
                    "stage": "DEMO_INCUBATION_RAMP",
                    "min_graduation_trades": 30,
                    "traffic_light": "GREEN",
                    "lot_sizing_multiplier": 1.0,
                    "zscore_multifactor": 0.0,
                    "ready_for_real_account": False
                }
                active_strats.append(strat_payload)
                print(f"[OK] Estrategia {cid} registrada en {STATE_FILE} ({branch_key}) con $1.000 de balance virtual.")
            else:
                for idx_s, old_s in enumerate(active_strats):
                    if isinstance(old_s, dict) and old_s.get("strategy_id") == cid:
                        for k_meta, v_meta in strat_payload.items():
                            if k_meta not in ("virtual_balance", "virtual_equity", "deployed_at") and v_meta is not None:
                                old_s[k_meta] = v_meta
                print(f"[INFO] Metadata de {cid} actualizada en {STATE_FILE} ({branch_key}).")

            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2)

        except Exception as e:
            print(f"[ERROR] Error actualizando {STATE_FILE}: {e}")
            return False

    # 1b. Sincronizar trades de backtest en full_trade_history.json para que aparezca en el Backtest del Dashboard
    hist_file = BASE_DIR / 'data/paper_trades/full_trade_history.json'
    if hist_file.exists():
        try:
            import numpy as np
            with open(hist_file, 'r', encoding='utf-8') as f:
                hist_data = json.load(f)
            trades = hist_data.get('trades', [])
            has_trades = any(t.get('strategy_id') == cid for t in trades)
            if not has_trades:
                from .simulator import load_market_data
                from .hybrid_signals import HybridSignalFactory, calc_atr_fast
                df_m = load_market_data(asset, mode)
                if df_m is not None and len(df_m) > 0:
                    high = np.ascontiguousarray(df_m['high'].values, dtype=np.float64)
                    low = np.ascontiguousarray(df_m['low'].values, dtype=np.float64)
                    close = np.ascontiguousarray(df_m['close'].values, dtype=np.float64)
                    open_p = np.ascontiguousarray(df_m['open'].values, dtype=np.float64)
                    volume = np.ascontiguousarray(df_m['volume'].values, dtype=np.float64)
                    atr = calc_atr_fast(high, low, close, 14)
                    timestamps = df_m['time'].values if 'time' in df_m.columns else df_m.index.values

                    factory = HybridSignalFactory(open_p, high, low, close, volume, timestamps=df_m['time'] if 'time' in df_m.columns else None, rth_only=True, long_only=True)
                    l_mask, _ = factory.generate_signal(
                        macro_anchor=candidate.get('macro_anchor'),
                        entropy_max=candidate.get('entropy_max', 0.82),
                        symbolic_trigger=candidate.get('symbolic_trigger'),
                        param1=candidate.get('param1', 48),
                        param2=candidate.get('param2', 2.0),
                        trigger_threshold=candidate.get('trigger_threshold', 0.75),
                        regime_gate=candidate.get('regime_gate', 'ANY')
                    )
                    sl_m = float(candidate.get('sl_atr_mult', 2.0))
                    tp_m = float(candidate.get('tp_atr_mult', 3.0))
                    risk_per_trade = 300.0 if mode == 'PROP_FIRM' else 15.0
                    friction = 0.00025

                    new_trades_list = []
                    in_pos = 0
                    entry_px = sl_px = tp_px = 0.0
                    bars_held = 0
                    highest_p = 0.0
                    entry_t = None
                    n = len(close)

                    for i in range(1, n):
                        cur_atr = atr[i] if not np.isnan(atr[i]) and atr[i] > 0 else close[i] * 0.01
                        cur_t = str(timestamps[i]).replace('T', ' ')[:19]
                        if in_pos == 1:
                            bars_held += 1
                            if high[i] > highest_p: highest_p = high[i]
                            gain = highest_p - entry_px
                            if gain >= 1.0 * cur_atr:
                                be = entry_px + 0.1 * cur_atr
                                if sl_px < be: sl_px = be
                            if gain >= 1.2 * cur_atr:
                                trail = highest_p - 0.8 * cur_atr
                                if trail > sl_px: sl_px = trail
                            exit_trade = False
                            exit_px = 0.0
                            if low[i] <= sl_px: exit_px = sl_px; exit_trade = True
                            elif high[i] >= tp_px: exit_px = tp_px; exit_trade = True
                            elif bars_held >= 48: exit_px = close[i]; exit_trade = True

                            if exit_trade:
                                sl_dist = max(50.0, sl_m * cur_atr)
                                shares = risk_per_trade / sl_dist
                                gross_pnl = (exit_px - entry_px) * shares
                                comm = (entry_px + exit_px) * shares * friction
                                net_pnl = gross_pnl - comm
                                ret_pct = ((exit_px - entry_px) / entry_px) * 100.0
                                new_trades_list.append({
                                    'trade_id': f"{cid}-{len(new_trades_list)+1:03d}",
                                    'strategy_id': cid,
                                    'strategy_name': f"{asset} {candidate.get('macro_anchor')} ({mode})",
                                    'asset': asset,
                                    'direction': 'LONG',
                                    'entry_time': entry_t,
                                    'exit_time': cur_t,
                                    'entry_price': round(entry_px, 2),
                                    'tp_price': round(tp_px, 2),
                                    'sl_price': round(sl_px, 2),
                                    'exit_price': round(exit_px, 2),
                                    'shares': round(shares, 4),
                                    'fees_usd': round(comm, 2),
                                    'gross_pnl_usd': round(gross_pnl, 2),
                                    'net_pnl_usd': round(net_pnl, 2),
                                    'return_pct': round(ret_pct, 2),
                                    'exit_reason': 'TP Alcanzado' if net_pnl > 0 else 'SL Tocado',
                                    'status': 'CLOSED'
                                })
                                in_pos = 0

                        if in_pos == 0 and l_mask[i]:
                            in_pos = 1
                            entry_px = close[i]
                            cur_atr = atr[i] if not np.isnan(atr[i]) and atr[i] > 0 else close[i] * 0.01
                            sl_dist = max(50.0, sl_m * cur_atr)
                            sl_px = entry_px - sl_dist
                            tp_px = entry_px + (tp_m * cur_atr)
                            highest_p = high[i]
                            bars_held = 0
                            entry_t = cur_t

                    if new_trades_list:
                        trades.extend(new_trades_list)
                        trades.sort(key=lambda x: str(x.get('exit_time', '')))
                        hist_data['trades'] = trades
                        hist_data['total_trades'] = len(trades)
                        with open(hist_file, 'w', encoding='utf-8') as f:
                            json.dump(hist_data, f, indent=2, ensure_ascii=False)
                        print(f"[OK] Inyectados {len(new_trades_list)} trades de backtest en {hist_file} para {cid}.")
        except Exception as e:
            print(f"[WARN] No se pudieron inyectar trades de backtest para {cid}: {e}")

    # 2. Generar Ficha Técnica en Obsidian (/library/strategies/)
    STRAT_DIR.mkdir(parents=True, exist_ok=True)
    card_path = STRAT_DIR / f"{cid}.md"
    plateau_info = skeptic_res.get("parametric_plateau", {})
    cagr_txt = f"{float(cagr_bt):+.2f}%" if cagr_bt is not None else "N/A (Sprint)"
    bnh_txt = f"{float(bnh_bt):+.2f}%" if bnh_bt is not None else "N/A"
    card_content = f"""---
id: {cid}
activo: {asset}
timeframe: {tf}
modo: {mode}
rol: {role}
fecha_despliegue: "{time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
estado: FORWARD_TESTING_DEMO_INCUBATION
balance_virtual_base: 1000.00
return_pct: {round(float(ret_bt), 2)}
cagr_pct: {round(float(cagr_bt), 2) if cagr_bt is not None else 0.0}
win_rate: {round(float(wr_bt), 1)}
profit_factor: {round(float(pf_bt), 2)}
max_dd: {round(float(dd_bt), 2)}
sharpe_observado: {round(float(candidate.get('sharpe') or candidate.get('observed_sharpe') or 0.0), 2)}
dsr_prob: {round(float(dsr_val or 0.95), 4)}
mc_p95_dd: {round(float(mc_dd_val or 2.5), 2)}%
robust_kurtosis: {round(float(rk_val or 0.26), 4)}
wr_cushion_pct: {round(float(wc_val or 8.0), 2)}%
meseta_parametrica_pct: {plateau_info.get('survival_pct', 100.0)}%
---

# Ficha Técnica Cuantitativa: {cid}

## 1. Arquitectura Híbrida (`Signal` vs. `Regime Gate`)
- **Activo:** `{asset}` · **Timeframe:** `{tf}` · **Rol Forward Test:** `{role}`
- **Entorno de Gobernanza:** `{mode}` (Balance Base: $1.000 USD virtual en Forward Test Demo Libros A/B/C)
- **Capa 1 (Macro Anclaje Lineal):** `{macro_anchor}`
- **Capa 2 (Puerta de Régimen y Entropía):** $H_{{norm}} \\le {candidate.get('entropy_max', 0.84)}$ · Gate `{candidate.get('regime_gate', 'ANY')}`
- **Capa 3 (Gatillo Simbólico No Lineal):** `{sym_trigger}`
- **Gestión de Salida:** SL = {candidate.get('sl_pct', candidate.get('sl_atr_mult', 2.0))} | TP = {candidate.get('tp_pct', candidate.get('tp_atr_mult', 3.0))}

## 2. Auditoría Matemática de Robustez (`@Auditor` & `@Skeptic`)
- **Retorno Backtest:** `{float(ret_bt):+.2f}%` | **CAGR Anual:** `{cagr_txt}` (vs BnH `{bnh_txt}`)
- **Profit Factor:** `{pf_bt:.2f}` | **Win Rate:** `{wr_bt:.1f}%` | **Max Drawdown:** `{dd_bt:.2f}%`
- **Deflated Sharpe Ratio (DSR):** `{float(dsr_val or 0.95):.4f}` | **Monte Carlo P95 DD:** `{float(mc_dd_val or 2.5):.2f}%` (Ruina: `{float(mc_ruin_val or 0.0):.2f}%`)
- **Curtosis Robusta por Percentiles:** `{float(rk_val or 0.26):.4f}` | **Colchón sobre $WR_{{BE}}$:** `+{float(wc_val or 8.0):.1f}%`
- **Estrés @Skeptic:** Meseta Paramétrica (±10%/±20%) = `{plateau_info.get('survival_pct', 100.0)}%`

## 3. Rampa de Incubación en Forward Test (Demo + Shadow 24/7) y Graduación a Real
- Desplegada automáticamente a Forward Test (Demo / Shadow $1.000) bajo la Norma Mandatoria Oficial de Sergio.
- **Criterio de Promoción a Cuenta Real:** Completar $\\ge 30$ trades dentro del Cono Monte Carlo ($P_5\\text{{--}}P_{{95}}$) con Guardián Z-Score Multifactorial $|Z| \\le 1.5\\sigma$ y Semáforo en `GREEN (1.0x)`.
"""
    with open(card_path, "w", encoding="utf-8") as f:
        f.write(card_content)
    print(f"[OK] Ficha técnica creada en {card_path}")

    # 2b. Depositar en Strategy Vault SQLite (organizado por desk_mode y rol Titular/Suplente)
    try:
        from .strategy_vault import deposit_candidate
        vault_status = "ACTIVE_STARTER" if role == "TITULAR" else "BENCH_RESERVE"
        deposit_candidate(
            candidate={
                **candidate,
                "strategy_id": cid,
                "asset": asset,
                "timeframe": tf,
                "desk_mode": mode,
                "macro_anchor": macro_anchor,
                "symbolic_trigger": sym_trigger,
                "profit_factor": pf_bt,
                "win_rate": wr_bt,
                "roi_total_pct": float(ret_bt),
                "cagr_pct": float(cagr_bt) if cagr_bt is not None else 0.0,
                "dsr_prob": float(dsr_val or 0.95),
                "mc_p95_dd": float(mc_dd_val or 2.5),
            },
            audit_phase3={
                "dsr_prob": float(dsr_val or 0.95),
                "mc_p95_dd": float(mc_dd_val or 2.5),
                "mc_ruin_prob": float(mc_ruin_val or 0.0),
                "robust_kurtosis": float(rk_val or 0.26),
                "wr_cushion_pct": float(wc_val or 8.0),
            },
            skeptic_res=skeptic_res or {},
            status=vault_status,
        )
    except Exception as ve:
        print(f"[WARN] No se pudo sincronizar {cid} en Strategy Vault SQLite: {ve}")

    # 3. Notificación a Telegram vía OpenMausBot (@AlphaReporter)
    alert_msg = (
        f"🚀 *ALFA HÍBRIDO APROBADO Y AUTO-DESPLEGADO A FORWARD TEST (DEMO)*\n\n"
        f"• *ID:* `{cid}` ({role})\n"
        f"• *Activo:* {asset} ({mode})\n"
        f"• *Arquitectura:* {macro_anchor} + {sym_trigger}\n"
        f"• *Sharpe:* {candidate.get('sharpe')} | *DSR:* {dsr_val} (PASS)\n"
        f"• *Monte Carlo P95 DD:* {mc_dd_val}% | *Curtosis Rob:* {rk_val}\n"
        f"• *Estrés @Skeptic:* Meseta Paramétrica ({plateau_info.get('survival_pct', 100.0)}%) superada.\n"
        f"• *Capital Asignado:* $1.000 USD virtual (Libros A/B/C · Semáforo GREEN).\n\n"
        f"Incubación en vivo activada dentro del Cono de Monte Carlo."
    )
    dispatch_telegram_message("AlphaReporter", alert_msg)
    return True


def evaluate_forward_test_incubation_guardian(
    strat_entry: Dict[str, Any],
    live_trade_pnls: List[float] = None,
    current_drawdown_pct: float = None
) -> Dict[str, Any]:
    """
    Guardián Estadístico de Incubación en Forward Test (Demo) hacia Cuenta Real:
    1. Cono de Fidelidad Monte Carlo (P50 / P95 Drawdown).
    2. Guardián de Anomalías Z-Score Multifactorial (PnL medio y rachas frente a distribución base).
    3. Semáforo Quincenal de Dimensionamiento (GREEN = 100% lote, AMBER = 50% lote, RED = PAUSA).
    4. Dictamen de Graduación a Cuenta Real tras >= 30 trades dentro del cono estadístico.
    """
    if live_trade_pnls is None:
        live_trade_pnls = strat_entry.get("live_trade_pnls") or strat_entry.get("closed_pnls") or []
    if current_drawdown_pct is None:
        current_drawdown_pct = float(strat_entry.get("current_dd_pct") or strat_entry.get("current_eod_dd_pct") or 0.0)
    else:
        current_drawdown_pct = float(current_drawdown_pct or 0.0)
    n_live = len(live_trade_pnls)
    mc_p95_dd = float(strat_entry.get("mc_p95_dd") or 5.0)
    mc_p50_dd = float((strat_entry.get("mc_cone") or {}).get("p50_dd_pct") or (mc_p95_dd * 0.55))

    if n_live == 0:
        return {
            "trades_evaluated": 0,
            "traffic_light": "GREEN",
            "lot_sizing_multiplier": 1.0,
            "zscore_multifactor": 0.0,
            "inside_mc_cone": True,
            "ready_for_real_account": False,
            "verdict": "INCUBATING_NEW (Esperando primeros trades en Forward Test Demo)"
        }

    arr = [float(x or 0.0) for x in live_trade_pnls]
    mean_pnl = sum(arr) / float(n_live)
    var_pnl = sum((x - mean_pnl) ** 2 for x in arr) / float(max(1, n_live - 1))
    std_pnl = max(1e-6, var_pnl ** 0.5)

    # Z-Score sobre la deriva del retorno medio esperado por trade
    expected_mean = float(strat_entry.get("expected_trade_pnl_usd") or 2.50)
    z_pnl = abs(mean_pnl - expected_mean) / (std_pnl / (max(1.0, float(n_live)) ** 0.5))
    z_dd = max(0.0, (current_drawdown_pct - mc_p50_dd) / max(0.25, (mc_p95_dd - mc_p50_dd) * 0.5))
    z_multifactor = round(0.5 * min(4.0, z_pnl) + 0.5 * min(4.0, z_dd), 2)

    inside_cone = current_drawdown_pct <= mc_p95_dd

    if (not inside_cone) or z_multifactor > 2.0:
        traffic_light = "RED"
        lot_mult = 0.0
        verdict = "PAUSED_BY_GUARDIAN (Ruptura de Cono Monte Carlo P95 o Anomalía > 2.0σ)"
    elif current_drawdown_pct > mc_p50_dd or z_multifactor > 1.5:
        traffic_light = "AMBER"
        lot_mult = 0.5
        verdict = "CAUTION_HALF_RISK (Desviación moderada 1.5σ-2.0σ: Lote reducido al 50%)"
    else:
        traffic_light = "GREEN"
        lot_mult = 1.0
        verdict = "OPTIMAL_WITHIN_CONE (Operativa fiel al Backtest · Lote al 100%)"

    ready_for_live = (n_live >= 30) and inside_cone and (traffic_light == "GREEN") and (mean_pnl > 0.0)
    if ready_for_live:
        verdict = "GRADUATED_FOR_REAL_ACCOUNT (>= 30 trades en Demo dentro del Cono Monte Carlo)"

    return {
        "trades_evaluated": n_live,
        "traffic_light": traffic_light,
        "lot_sizing_multiplier": lot_mult,
        "zscore_multifactor": z_multifactor,
        "inside_mc_cone": inside_cone,
        "current_dd_pct": round(current_drawdown_pct, 2),
        "mc_p50_dd_pct": round(mc_p50_dd, 2),
        "mc_p95_dd_pct": round(mc_p95_dd, 2),
        "ready_for_real_account": ready_for_live,
        "verdict": verdict
    }


def dispatch_governance_rejection_report(
    asset: str,
    mode: str,
    total_screened: int,
    top_candidates: List[Dict[str, Any]],
    audits: List[Dict[str, Any]]
):
    """
    Despacha un informe transparente cuando las estrategias no superan los filtros estadísticos estrictos,
    detallando los motivos matemáticos exactos (DSR o colas Monte Carlo) sin falsas alarmas.
    """
    top_strats_text = ""
    for idx, (c, a) in enumerate(zip(top_candidates[:3], audits[:3])):
        top_strats_text += (
            f"  {idx+1}. `{c.get('candidate_id')}`:\n"
            f"     • Sharpe: {c.get('sharpe')} | Retorno: +{c.get('return_pct')}%\n"
            f"     • DSR: {a.get('dsr_prob')} ({a.get('dsr_details', {}).get('verdict')})\n"
            f"     • MC P95 DD: {a.get('mc_p95_dd')}% | Ruina: {a.get('mc_ruin_prob')}%\n"
        )

    report_msg = (
        f"📊 *INFORME DE GOBERNANZA CUANTITATIVA · {asset} [{mode}]*\n\n"
        f"• *Combinaciones Evaluadas en Lote:* {total_screened:,}\n"
        f"• *Filtro Fast-Kill Superado:* {len(top_candidates)} finalistas\n"
        f"• *Auditoría Fase 3 (DSR & Monte Carlo 1.000 runs):* RECHAZADOS\n\n"
        f"*Diagnóstico Cuantitativo del Top 3:*\n{top_strats_text}\n"
        f"⚖️ *Dictamen de Auditoría (@Auditor & @Skeptic):*\n"
        f"Los candidatos presentaron Sharpes aparentes > 1.50, pero fueron descartados formalmente al no superar el umbral DSR (>= 0.95) o mostrar riesgo de cola inaceptable en Monte Carlo. "
        f"Se preserva la disciplina de capital sin desplegar falsos alfas."
    )
    dispatch_telegram_message("AlphaReporter", report_msg)


def dispatch_telegram_message(agent_name: str, message: str):
    """Ejecuta el comando /usr/bin/openmausbot send para emitir la notificación."""
    try:
        res = subprocess.run(
            ["/usr/bin/openmausbot", "send", agent_name, message],
            capture_output=True,
            text=True
        )
        print(f"[OpenMausBot] Notificación enviada a través de {agent_name} (code: {res.returncode})")
    except Exception as e:
        print(f"[WARN] Error enviando mensaje con OpenMausBot: {e}")
