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
                    "mc_p95_dd": audit_phase3.get("mc_p95_dd")
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

    # 2. Generar Ficha Técnica en Obsidian (/library/strategies/)
    STRAT_DIR.mkdir(parents=True, exist_ok=True)
    card_path = STRAT_DIR / f"{cid}.md"
    card_content = f"""---
id: {cid}
activo: {asset}
modo: {mode}
fecha_despliegue: "{time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
estado: FORWARD_TESTING
balance_virtual_base: 1000.00
sharpe_observado: {candidate.get('sharpe')}
dsr_prob: {audit_phase3.get('dsr_prob')}
mc_p95_dd: {audit_phase3.get('mc_p95_dd')}%
---

# Ficha Técnica Cuantitativa: {cid}

## 1. Arquitectura Híbrida
- **Activo:** `{asset}`
- **Entorno de Gobernanza:** `{mode}` (Balance Base: $1.000 USD virtual)
- **Capa 1 (Macro Anclaje Lineal):** `{candidate.get('macro_anchor')}` (Parámetros: {candidate.get('param1')}, {candidate.get('param2')})
- **Capa 2 (Régimen de Entropía):** $H_{{norm}} \\le {candidate.get('entropy_max')}$
- **Capa 3 (Gatillo Simbólico No Lineal):** `{candidate.get('symbolic_trigger')}` (Umbral: {candidate.get('trigger_threshold')})
- **Gestión de Salida:** SL = {candidate.get('sl_atr_mult')} ATR | TP = {candidate.get('tp_atr_mult')} ATR

## 2. Auditoría Matemática de Robustez
- **Retorno Backtest:** `+{candidate.get('return_pct')}%` ({candidate.get('trades')} trades)
- **Deflated Sharpe Ratio (DSR):** `{audit_phase3.get('dsr_prob')}` (Z-Stat: {audit_phase3.get('z_stat')})
- **Monte Carlo 1.000 Runs:** P95 Max Drawdown = `{audit_phase3.get('mc_p95_dd')}%` | Probabilidad Ruina = `{audit_phase3.get('mc_ruin_prob')}%`
- **Estrés @Skeptic:** Latencia 1 barra = {skeptic_res.get('latency_1bar', {}).get('sharpe')} SR | Comisiones 1.5x = {skeptic_res.get('friction_15x', {}).get('sharpe')} SR

## 3. Estado Operativo
- Desplegada de forma inmediata a Forward Test en vivo bajo la Norma Mandatoria Oficial de Sergio.
"""
    with open(card_path, "w", encoding="utf-8") as f:
        f.write(card_content)
    print(f"[OK] Ficha técnica creada en {card_path}")

    # 3. Notificación a Telegram vía OpenMausBot (@AlphaReporter)
    alert_msg = (
        f"🚀 *ALFA HÍBRIDO APROBADO Y AUTO-DESPLEGADO A FORWARD TEST*\n\n"
        f"• *ID:* `{cid}`\n"
        f"• *Activo:* {asset} ({mode})\n"
        f"• *Arquitectura:* {candidate.get('macro_anchor')} + {candidate.get('symbolic_trigger')}\n"
        f"• *Sharpe:* {candidate.get('sharpe')} | *DSR:* {audit_phase3.get('dsr_prob')} (PASS)\n"
        f"• *Monte Carlo P95 DD:* {audit_phase3.get('mc_p95_dd')}%\n"
        f"• *Estrés @Skeptic:* Latencia 1 barra superada con éxito.\n"
        f"• *Capital Asignado:* $1.000 USD virtual (Riesgo 1% / $10 USD).\n\n"
        f"Operativa en vivo simulada activada en el dashboard."
    )
    dispatch_telegram_message("AlphaReporter", alert_msg)
    return True


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
