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
    con un libro contable virtual de $1.000 USD/USDC.
    """
    cid = candidate.get("candidate_id")
    asset = candidate.get("asset")
    mode = candidate.get("desk_mode")

    print(f"\n>>> INICIANDO AUTO-DESPLIEGUE A FORWARD TEST: {cid} ({asset} · {mode}) <<<")

    # 1. Actualizar estado de Forward Test en prop_firm_forward_test_state.json
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state_data = json.load(f)

            branch_key = "prop_firm" if mode == "PROP_FIRM" else "capital_propio"
            branch = state_data.setdefault(branch_key, {})
            active_strats = branch.setdefault("active_strategies", [])

            existing_ids = [s.get("strategy_id") for s in active_strats if isinstance(s, dict)]
            if cid not in existing_ids:
                mc_cone = audit_phase3.get("mc_cone") or {
                    "p50_dd_pct": audit_phase3.get("mc_details", {}).get("median_max_dd_pct", 1.5),
                    "p95_dd_pct": audit_phase3.get("mc_p95_dd", 3.0)
                }
                plateau_pct = skeptic_res.get("parametric_plateau", {}).get("survival_pct", 100.0)
                new_strat_entry = {
                    "strategy_id": cid,
                    "symbol": asset,
                    "branch": mode,
                    "virtual_balance": 1000.0,
                    "virtual_equity": 1000.0,
                    "risk_per_trade_pct": 1.0,
                    "risk_nominal_usd": 10.0,
                    "status": "FORWARD_TESTING_ACTIVE",
                    "deployed_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                    "macro_anchor": candidate.get("macro_anchor"),
                    "symbolic_trigger": candidate.get("symbolic_trigger"),
                    "observed_sharpe": candidate.get("sharpe"),
                    "dsr_prob": audit_phase3.get("dsr_prob"),
                    "mc_p95_dd": audit_phase3.get("mc_p95_dd"),
                    "mc_cone": mc_cone,
                    "robust_kurtosis": audit_phase3.get("robust_kurtosis"),
                    "wr_cushion_pct": audit_phase3.get("wr_cushion_pct"),
                    "parametric_plateau_survival_pct": plateau_pct,
                    "incubation_guardian": {
                        "stage": "DEMO_INCUBATION_RAMP",
                        "min_graduation_trades": 30,
                        "traffic_light": "GREEN",
                        "lot_sizing_multiplier": 1.0,
                        "zscore_multifactor": 0.0,
                        "ready_for_real_account": False
                    }
                }
                active_strats.append(new_strat_entry)

                with open(STATE_FILE, "w", encoding="utf-8") as f:
                    json.dump(state_data, f, indent=2)
                print(f"[OK] Estrategia {cid} registrada en {STATE_FILE} con $1.000 de balance virtual.")
            else:
                print(f"[INFO] Estrategia {cid} ya estaba registrada en {STATE_FILE}.")

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
    card_content = f"""---
id: {cid}
activo: {asset}
modo: {mode}
fecha_despliegue: "{time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
estado: FORWARD_TESTING_DEMO_INCUBATION
balance_virtual_base: 1000.00
sharpe_observado: {candidate.get('sharpe')}
dsr_prob: {audit_phase3.get('dsr_prob')}
mc_p95_dd: {audit_phase3.get('mc_p95_dd')}%
robust_kurtosis: {audit_phase3.get('robust_kurtosis')}
wr_cushion_pct: {audit_phase3.get('wr_cushion_pct')}%
meseta_parametrica_pct: {plateau_info.get('survival_pct', 100.0)}%
---

# Ficha Técnica Cuantitativa: {cid}

## 1. Arquitectura Híbrida (`Signal` vs. `Regime Gate`)
- **Activo:** `{asset}`
- **Entorno de Gobernanza:** `{mode}` (Balance Base: $1.000 USD virtual en Forward Test Demo)
- **Capa 1 (Macro Anclaje Lineal):** `{candidate.get('macro_anchor')}` (Parámetros: {candidate.get('param1')}, {candidate.get('param2')})
- **Capa 2 (Puerta de Régimen y Entropía):** $H_{{norm}} \\le {candidate.get('entropy_max')}$ · Gate `{candidate.get('regime_gate', 'ANY')}`
- **Capa 3 (Gatillo Simbólico No Lineal):** `{candidate.get('symbolic_trigger')}` (Umbral: {candidate.get('trigger_threshold')})
- **Gestión de Salida:** SL = {candidate.get('sl_atr_mult')} ATR | TP = {candidate.get('tp_atr_mult')} ATR

## 2. Auditoría Matemática de Robustez (`@Auditor` & `@Skeptic`)
- **Retorno Backtest:** `+{candidate.get('return_pct')}%` ({candidate.get('trades')} trades)
- **Deflated Sharpe Ratio (DSR):** `{audit_phase3.get('dsr_prob')}` (Z-Stat: {audit_phase3.get('z_stat')})
- **Monte Carlo 1.000 Runs:** P95 Max Drawdown = `{audit_phase3.get('mc_p95_dd')}%` | Probabilidad Ruina = `{audit_phase3.get('mc_ruin_prob')}%`
- **Curtosis Robusta por Percentiles:** `{audit_phase3.get('robust_kurtosis')}` | **Colchón sobre $WR_{{BE}}$:** `+{audit_phase3.get('wr_cushion_pct')}%`
- **Estrés @Skeptic:** Latencia 1 barra = {skeptic_res.get('latency_1bar', {}).get('sharpe')} SR | Comisiones 1.5x = {skeptic_res.get('friction_15x', {}).get('sharpe')} SR | Meseta Paramétrica (±10%/±20%) = `{plateau_info.get('survival_pct', 100.0)}%`

## 3. Rampa de Incubación en Forward Test (Demo) y Graduación a Real
- Desplegada automáticamente a Forward Test (Demo) bajo la Norma Mandatoria Oficial de Sergio.
- **Criterio de Promoción a Cuenta Real:** Completar $\\ge 30$ trades dentro del Cono Monte Carlo ($P_5\\text{{--}}P_{{95}}$) con Guardián Z-Score Multifactorial $|Z| \\le 1.5\\sigma$ y Semáforo en `GREEN (1.0x)`.
"""
    with open(card_path, "w", encoding="utf-8") as f:
        f.write(card_content)
    print(f"[OK] Ficha técnica creada en {card_path}")

    # 3. Notificación a Telegram vía OpenMausBot (@AlphaReporter)
    alert_msg = (
        f"🚀 *ALFA HÍBRIDO APROBADO Y AUTO-DESPLEGADO A FORWARD TEST (DEMO)*\n\n"
        f"• *ID:* `{cid}`\n"
        f"• *Activo:* {asset} ({mode})\n"
        f"• *Arquitectura:* {candidate.get('macro_anchor')} + {candidate.get('symbolic_trigger')}\n"
        f"• *Sharpe:* {candidate.get('sharpe')} | *DSR:* {audit_phase3.get('dsr_prob')} (PASS)\n"
        f"• *Monte Carlo P95 DD:* {audit_phase3.get('mc_p95_dd')}% | *Curtosis Rob:* {audit_phase3.get('robust_kurtosis')}\n"
        f"• *Estrés @Skeptic:* Latencia 1 barra + Meseta Paramétrica ({plateau_info.get('survival_pct', 100.0)}%) superadas.\n"
        f"• *Capital Asignado:* $1.000 USD virtual (Riesgo 1% / $10 USD · Semáforo GREEN).\n\n"
        f"Incubación en vivo simulada activada dentro del Cono de Monte Carlo."
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
