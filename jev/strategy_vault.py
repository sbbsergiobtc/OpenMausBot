"""
Strategy Vault SQLite - Banco de Reserva Dinámico de Estrategias
AlgrokQuant · Jev Quantitative Engine & Enjambre Multi-Agente
Arquitectura: Relevo 100% Autónomo de Titulares y Suplentes (Fase 3)

REGLAS DE GOBERNANZA:
1. Conecta la salida del Screener diario de 100.000 combinaciones (08:00, 14:00, 20:00 CET).
2. Toda estrategia aprobada con DSR >= 0.85 se deposita automáticamente en el Banco de Reserva.
3. Si una titular entra en drawdown y se degrada a semáforo ROJO (Guardián Monte Carlo P95),
   se manda al banquillo (BENCH_INJURED) y se promueve automáticamente a la mejor suplente
   de la base de datos sin intervención manual.
"""

import os
import sys
import json
import time
import sqlite3
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

if Path('/root/AlgrokQuant').exists():
    BASE_DIR = Path('/root/AlgrokQuant')
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / 'data/strategy_vault.db'


def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    target_path = Path(db_path) if db_path else DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path), timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_vault(db_path: Optional[Path] = None) -> None:
    """Crea las tablas e índices del Strategy Vault si no existen."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS strategies (
        strategy_id TEXT PRIMARY KEY,
        asset TEXT NOT NULL,
        timeframe TEXT NOT NULL,
        desk_mode TEXT NOT NULL,
        family TEXT,
        macro_anchor TEXT,
        regime_gate TEXT,
        symbolic_trigger TEXT,
        params TEXT,
        status TEXT NOT NULL, -- 'ACTIVE_STARTER', 'BENCH_RESERVE', 'BENCH_INJURED', 'RETIRED'
        observed_sharpe REAL,
        dsr_prob REAL,
        mc_p95_dd REAL,
        mc_ruin_prob REAL,
        robust_kurtosis REAL,
        wr_cushion_pct REAL,
        profit_factor REAL,
        win_rate REAL,
        roi_pct REAL,
        cagr_pct REAL,
        traffic_light TEXT DEFAULT 'GREEN',
        incubation_trades INTEGER DEFAULT 0,
        current_drawdown REAL DEFAULT 0.0,
        replacement_for TEXT,
        bench_reason TEXT,
        created_at TEXT NOT NULL,
        last_status_change TEXT NOT NULL,
        meta_json TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS vault_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        event_type TEXT NOT NULL, -- 'DEPOSIT_RESERVE', 'PROMOTION_TO_STARTER', 'DEMOTION_TO_BENCH', 'STATUS_UPDATE'
        strategy_id TEXT NOT NULL,
        desk_mode TEXT NOT NULL,
        asset TEXT NOT NULL,
        old_status TEXT,
        new_status TEXT,
        details TEXT
    );
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_strat_status_desk ON strategies (status, desk_mode);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_strat_asset_dsr ON strategies (asset, dsr_prob);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_events_strat ON vault_events (strategy_id, timestamp);")

    conn.commit()
    conn.close()


def deposit_candidate(
    candidate: Dict[str, Any],
    audit_phase3: Optional[Dict[str, Any]] = None,
    skeptic_res: Optional[Dict[str, Any]] = None,
    status: str = 'BENCH_RESERVE',
    db_path: Optional[Path] = None
) -> bool:
    """
    Deposita una estrategia en el Banco de Reserva.
    Exige la condición mandatoria oficial: DSR >= 0.85.
    """
    init_vault(db_path)
    audit = audit_phase3 or {}
    skeptic = skeptic_res or {}

    cid = candidate.get("candidate_id") or candidate.get("strategy_id") or candidate.get("id")
    if not cid:
        return False

    dsr = float(audit.get("dsr_prob") or candidate.get("dsr_prob") or 0.0)
    # Filtro mandatorio: solo estrategias con DSR >= 0.85 ingresan al Banco de Reserva
    if dsr < 0.85 and status == 'BENCH_RESERVE':
        print(f"[VAULT REJECT] {cid} tiene DSR={dsr:.4f} < 0.85. No califica para Banco de Reserva.")
        return False

    asset = candidate.get("asset") or candidate.get("symbol", "UNKNOWN")
    tf = candidate.get("timeframe") or candidate.get("tf", "1h")
    mode = candidate.get("desk_mode") or candidate.get("branch", "CAPITAL_PROPIO")
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    sr = float(candidate.get("sharpe") or candidate.get("observed_sharpe") or 0.0)
    mc_dd = float(audit.get("mc_p95_dd") or candidate.get("mc_p95_dd") or candidate.get("max_dd") or 3.0)
    ruin = float(audit.get("mc_ruin_prob") or candidate.get("mc_ruin_prob") or 0.0)
    kurt = float(audit.get("robust_kurtosis", {}).get("robust_kurtosis") if isinstance(audit.get("robust_kurtosis"), dict) else (audit.get("robust_kurtosis") or candidate.get("robust_kurtosis") or 0.26))
    wr_cushion = float(audit.get("breakeven_cushion", {}).get("wr_cushion_pct") if isinstance(audit.get("breakeven_cushion"), dict) else (audit.get("wr_cushion_pct") or candidate.get("wr_cushion_pct") or 8.0))
    pf = float(candidate.get("profit_factor") or candidate.get("backtest_pf") or 2.0)
    wr = float(candidate.get("win_rate") or candidate.get("backtest_wr") or 65.0)
    roi = float(candidate.get("total_pnl_pct") or candidate.get("return_pct") or candidate.get("roi_total_pct") or 0.0)
    cagr = float(candidate.get("cagr_pct") or candidate.get("backtest_cagr_pct") or 0.0)

    params_json = json.dumps(candidate.get("params") or {
        "sl_atr_mult": candidate.get("sl_atr_mult"),
        "tp_atr_mult": candidate.get("tp_atr_mult"),
        "param1": candidate.get("param1"),
        "param2": candidate.get("param2"),
        "trigger_threshold": candidate.get("trigger_threshold")
    })

    meta_json = json.dumps({
        "audit": audit,
        "skeptic": skeptic,
        "deposited_by": "100k_Screener_Pipeline"
    })

    conn = get_db_connection(db_path)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO strategies (
        strategy_id, asset, timeframe, desk_mode, family, macro_anchor, regime_gate,
        symbolic_trigger, params, status, observed_sharpe, dsr_prob, mc_p95_dd,
        mc_ruin_prob, robust_kurtosis, wr_cushion_pct, profit_factor, win_rate,
        roi_pct, cagr_pct, traffic_light, incubation_trades, current_drawdown,
        replacement_for, bench_reason, created_at, last_status_change, meta_json
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'GREEN', 0, 0.0,
        NULL, NULL, ?, ?, ?
    )
    ON CONFLICT(strategy_id) DO UPDATE SET
        observed_sharpe=excluded.observed_sharpe,
        dsr_prob=excluded.dsr_prob,
        mc_p95_dd=excluded.mc_p95_dd,
        profit_factor=excluded.profit_factor,
        win_rate=excluded.win_rate,
        roi_pct=excluded.roi_pct,
        cagr_pct=excluded.cagr_pct,
        meta_json=excluded.meta_json,
        last_status_change=excluded.last_status_change;
    """, (
        cid, asset, tf, mode, candidate.get("family"), candidate.get("macro_anchor"),
        candidate.get("regime_gate", "ANY"), candidate.get("symbolic_trigger"),
        params_json, status, sr, dsr, mc_dd, ruin, kurt, wr_cushion, pf, wr,
        roi, cagr, now_str, now_str, meta_json
    ))

    # Registrar evento
    cur.execute("""
    INSERT INTO vault_events (
        timestamp, event_type, strategy_id, desk_mode, asset, old_status, new_status, details
    ) VALUES (?, 'DEPOSIT_RESERVE', ?, ?, ?, NULL, ?, ?);
    """, (
        now_str, cid, mode, asset, status,
        json.dumps({"dsr_prob": dsr, "profit_factor": pf, "mc_p95_dd": mc_dd})
    ))

    conn.commit()
    conn.close()
    return True


def get_best_reserve(
    asset: str,
    desk_mode: str,
    min_dsr: float = 0.85,
    db_path: Optional[Path] = None
) -> Optional[Dict[str, Any]]:
    """
    Busca la mejor suplente disponible en el Banco de Reserva.
    Prioriza:
    1. Coincidencia exacta de activo y mesa con DSR >= 0.85.
    2. Si no hay del mismo activo, mejor suplente de la misma mesa (ej. US100 por US500, o EURUSD por GBPUSD).
    Orden de selección: DSR DESC, Profit Factor DESC, MC P95 DD ASC.
    """
    init_vault(db_path)
    conn = get_db_connection(db_path)
    cur = conn.cursor()

    # 1. Búsqueda exacta de activo y mesa
    cur.execute("""
    SELECT * FROM strategies
    WHERE asset = ? AND desk_mode = ? AND status = 'BENCH_RESERVE' AND dsr_prob >= ?
    ORDER BY dsr_prob DESC, profit_factor DESC, mc_p95_dd ASC
    LIMIT 1;
    """, (asset, desk_mode, min_dsr))
    row = cur.fetchone()

    # 2. Búsqueda alternativa en la misma mesa si no hay del mismo activo
    if not row:
        cur.execute("""
        SELECT * FROM strategies
        WHERE desk_mode = ? AND status = 'BENCH_RESERVE' AND dsr_prob >= ?
        ORDER BY dsr_prob DESC, profit_factor DESC, mc_p95_dd ASC
        LIMIT 1;
        """, (desk_mode, min_dsr))
        row = cur.fetchone()

    conn.close()
    if row:
        return dict(row)
    return None


def demote_starter_to_bench(
    strategy_id: str,
    reason: str,
    db_path: Optional[Path] = None
) -> bool:
    """Manda una estrategia titular al banquillo por drawdown / semáforo ROJO."""
    init_vault(db_path)
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    cur.execute("SELECT desk_mode, asset, status FROM strategies WHERE strategy_id = ?;", (strategy_id,))
    row = cur.fetchone()
    old_status = row['status'] if row else 'ACTIVE_STARTER'
    desk_mode = row['desk_mode'] if row else 'UNKNOWN'
    asset = row['asset'] if row else 'UNKNOWN'

    cur.execute("""
    UPDATE strategies
    SET status = 'BENCH_INJURED',
        traffic_light = 'RED',
        bench_reason = ?,
        last_status_change = ?
    WHERE strategy_id = ?;
    """, (reason, now_str, strategy_id))

    cur.execute("""
    INSERT INTO vault_events (
        timestamp, event_type, strategy_id, desk_mode, asset, old_status, new_status, details
    ) VALUES (?, 'DEMOTION_TO_BENCH', ?, ?, ?, ?, 'BENCH_INJURED', ?);
    """, (now_str, strategy_id, desk_mode, asset, old_status, json.dumps({"reason": reason})))

    conn.commit()
    conn.close()
    return True


def promote_reserve_to_starter(
    reserve_id: str,
    replacing_id: Optional[str] = None,
    db_path: Optional[Path] = None
) -> bool:
    """Promueve una estrategia del Banco de Reserva a Titular en juego."""
    init_vault(db_path)
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    cur.execute("SELECT desk_mode, asset, status FROM strategies WHERE strategy_id = ?;", (reserve_id,))
    row = cur.fetchone()
    old_status = row['status'] if row else 'BENCH_RESERVE'
    desk_mode = row['desk_mode'] if row else 'UNKNOWN'
    asset = row['asset'] if row else 'UNKNOWN'

    cur.execute("""
    UPDATE strategies
    SET status = 'ACTIVE_STARTER',
        traffic_light = 'GREEN',
        replacement_for = ?,
        bench_reason = NULL,
        last_status_change = ?
    WHERE strategy_id = ?;
    """, (replacing_id, now_str, reserve_id))

    cur.execute("""
    INSERT INTO vault_events (
        timestamp, event_type, strategy_id, desk_mode, asset, old_status, new_status, details
    ) VALUES (?, 'PROMOTION_TO_STARTER', ?, ?, ?, ?, 'ACTIVE_STARTER', ?);
    """, (now_str, reserve_id, desk_mode, asset, old_status, json.dumps({"replacing_id": replacing_id})))

    conn.commit()
    conn.close()
    return True


def execute_autonomous_relay(
    injured_strat_id: str,
    reason: str,
    asset: str,
    desk_mode: str,
    db_path: Optional[Path] = None
) -> Optional[Dict[str, Any]]:
    """
    Ejecuta el relevo automático 100% autónomo:
    1. Degrada la titular lesionada a BENCH_INJURED.
    2. Localiza la mejor suplente con DSR >= 0.85 en SQLite.
    3. Promueve la suplente a ACTIVE_STARTER.
    4. Registra los eventos y retorna la ficha completa del relevo.
    """
    init_vault(db_path)

    # 1. Mandar al banquillo
    demote_starter_to_bench(injured_strat_id, reason, db_path=db_path)

    # 2. Buscar suplente calificada
    best_reserve = get_best_reserve(asset, desk_mode, min_dsr=0.85, db_path=db_path)
    if not best_reserve:
        print(f"[RELEVO VAULT] No se encontró suplente calificada con DSR >= 0.85 para {asset} ({desk_mode}).")
        return None

    new_id = best_reserve['strategy_id']

    # 3. Promover a titular
    promote_reserve_to_starter(new_id, replacing_id=injured_strat_id, db_path=db_path)

    relay_summary = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "demoted_strategy_id": injured_strat_id,
        "demotion_reason": reason,
        "promoted_strategy_id": new_id,
        "asset": asset,
        "desk_mode": desk_mode,
        "promoted_strategy": best_reserve
    }
    return relay_summary


def list_vault_strategies(
    status: Optional[str] = None,
    desk_mode: Optional[str] = None,
    limit: int = 100,
    db_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """Retorna las estrategias registradas en el Vault con filtros opcionales."""
    init_vault(db_path)
    conn = get_db_connection(db_path)
    cur = conn.cursor()

    query = "SELECT * FROM strategies WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if desk_mode:
        query += " AND desk_mode = ?"
        params.append(desk_mode)
    query += " ORDER BY dsr_prob DESC, profit_factor DESC LIMIT ?;"
    params.append(limit)

    cur.execute(query, tuple(params))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_vault_summary(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Resumen estadístico de titulares, banco de reserva y relevos recientes."""
    init_vault(db_path)
    conn = get_db_connection(db_path)
    cur = conn.cursor()

    cur.execute("SELECT status, count(*) as cnt FROM strategies GROUP BY status;")
    status_counts = {r['status']: r['cnt'] for r in cur.fetchall()}

    cur.execute("SELECT * FROM strategies WHERE status = 'ACTIVE_STARTER' ORDER BY dsr_prob DESC;")
    starters = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM strategies WHERE status = 'BENCH_RESERVE' AND dsr_prob >= 0.85 ORDER BY dsr_prob DESC, profit_factor DESC;")
    reserves = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM strategies WHERE status = 'BENCH_INJURED' ORDER BY last_status_change DESC;")
    injured = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM vault_events ORDER BY event_id DESC LIMIT 15;")
    events = [dict(r) for r in cur.fetchall()]

    conn.close()

    return {
        "status": "ok",
        "counts": {
            "starters": status_counts.get("ACTIVE_STARTER", 0),
            "bench_reserves": status_counts.get("BENCH_RESERVE", 0),
            "bench_injured": status_counts.get("BENCH_INJURED", 0),
            "retired": status_counts.get("RETIRED", 0),
            "total_strategies": sum(status_counts.values())
        },
        "starters": starters,
        "bench_reserves": reserves,
        "injured_bench": injured,
        "recent_events": events,
        "last_checked": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    }


def seed_vault_initial_data(db_path: Optional[Path] = None) -> int:
    """
    Puebla el Strategy Vault con las estrategias certificadas del sistema:
    - Titulares oficiales activas en MT5 (US500, USTEC, EURUSD, SOL).
    - Suplentes certificadas de alto DSR (>= 0.85) de los sprints de investigación.
    """
    init_vault(db_path)

    initial_strats = [
        # TITULARES OFICIALES
        {
            "id": "CAP-SPX-006",
            "asset": "US500",
            "timeframe": "4h",
            "desk_mode": "CAPITAL_PROPIO",
            "family": "Bollinger Dip Reversion",
            "macro_anchor": "S&P 500 Dip Mean Reversion",
            "regime_gate": "ANY",
            "symbolic_trigger": "Close < LowerBB(20, 1.2) & Close > EMA(200)",
            "sharpe": 2.65,
            "dsr_prob": 0.9850,
            "mc_p95_dd": 2.85,
            "profit_factor": 2.45,
            "win_rate": 68.5,
            "status": "ACTIVE_STARTER"
        },
        {
            "id": "CAP-NDX-005",
            "asset": "USTEC",
            "timeframe": "2h",
            "desk_mode": "CAPITAL_PROPIO",
            "family": "Bollinger Dip Reversion",
            "macro_anchor": "Nasdaq 100 Dip Mean Reversion",
            "regime_gate": "ANY",
            "symbolic_trigger": "Close < LowerBB(20, 1.2) & Close > EMA(200)",
            "sharpe": 2.75,
            "dsr_prob": 0.9910,
            "mc_p95_dd": 3.10,
            "profit_factor": 2.60,
            "win_rate": 70.0,
            "status": "ACTIVE_STARTER"
        },
        {
            "id": "PROP-FX-EUR-001",
            "asset": "EURUSD",
            "timeframe": "1h",
            "desk_mode": "PROP_FIRM",
            "family": "Session Mean Reversion",
            "macro_anchor": "EURUSD London-NY Session",
            "regime_gate": "ANY",
            "symbolic_trigger": "Session(7-17) & Close < LowerBB(24, 2.0) & RSI(14) < 35",
            "sharpe": 2.40,
            "dsr_prob": 0.9620,
            "mc_p95_dd": 2.20,
            "profit_factor": 2.30,
            "win_rate": 66.0,
            "status": "ACTIVE_STARTER"
        },
        {
            "id": "STRAT-20261024-028",
            "asset": "SOL",
            "timeframe": "5m",
            "desk_mode": "CAPITAL_PROPIO",
            "family": "VWAP Trend Following",
            "macro_anchor": "SOL VWAP Breakout Native",
            "regime_gate": "TRENDING_BULLISH",
            "symbolic_trigger": "Close > VWAP & Volume > SMA(Volume, 20)",
            "sharpe": 2.50,
            "dsr_prob": 0.9700,
            "mc_p95_dd": 3.40,
            "profit_factor": 2.35,
            "win_rate": 64.0,
            "status": "ACTIVE_STARTER"
        },
        # BANCO DE RESERVA (SUPLENTES DE ÉLITE CON DSR >= 0.85)
        {
            "id": "RES-SPX-007-REV",
            "asset": "US500",
            "timeframe": "1h",
            "desk_mode": "CAPITAL_PROPIO",
            "family": "Keltner Exhaustion",
            "macro_anchor": "S&P 500 Keltner Channel Dip",
            "regime_gate": "TRENDING_BULLISH",
            "symbolic_trigger": "Close < LowerKeltner(20, 1.5) & RSI(14) < 30",
            "sharpe": 2.45,
            "dsr_prob": 0.9550,
            "mc_p95_dd": 2.95,
            "profit_factor": 2.35,
            "win_rate": 67.0,
            "status": "BENCH_RESERVE"
        },
        {
            "id": "RES-NDX-008-REV",
            "asset": "USTEC",
            "timeframe": "1h",
            "desk_mode": "CAPITAL_PROPIO",
            "family": "VWAP Pullback",
            "macro_anchor": "Nasdaq 100 VWAP Institutional",
            "regime_gate": "TRENDING_BULLISH",
            "symbolic_trigger": "Close crosses above VWAP & ADX(14) > 25",
            "sharpe": 2.60,
            "dsr_prob": 0.9820,
            "mc_p95_dd": 3.05,
            "profit_factor": 2.50,
            "win_rate": 69.0,
            "status": "BENCH_RESERVE"
        },
        {
            "id": "RES-EUR-002-LON",
            "asset": "EURUSD",
            "timeframe": "15m",
            "desk_mode": "PROP_FIRM",
            "family": "London Breakout",
            "macro_anchor": "EURUSD London Open Range Breakout",
            "regime_gate": "HIGH_VOLATILITY",
            "symbolic_trigger": "Hour == 8 & High > RangeMax(07:00, 08:00)",
            "sharpe": 2.35,
            "dsr_prob": 0.9480,
            "mc_p95_dd": 2.15,
            "profit_factor": 2.25,
            "win_rate": 65.5,
            "status": "BENCH_RESERVE"
        },
        {
            "id": "RES-FUT-NQ-001",
            "asset": "NQ",
            "timeframe": "5m",
            "desk_mode": "PROP_FIRM",
            "family": "CME Futures RTH Sprint",
            "macro_anchor": "E-mini Nasdaq 100 Futures 5m RTH",
            "regime_gate": "RTH_OPENING_DRIVE",
            "symbolic_trigger": "VolumeProfile POC Rejection & Delta > 0",
            "sharpe": 2.70,
            "dsr_prob": 0.9880,
            "mc_p95_dd": 2.40,
            "profit_factor": 2.65,
            "win_rate": 71.0,
            "status": "BENCH_RESERVE"
        },
        {
            "id": "RES-FUT-ES-001",
            "asset": "ES",
            "timeframe": "5m",
            "desk_mode": "PROP_FIRM",
            "family": "CME Futures RTH Sprint",
            "macro_anchor": "E-mini S&P 500 Futures 5m RTH",
            "regime_gate": "RTH_OPENING_DRIVE",
            "symbolic_trigger": "Close > VWAP & CumulativeDelta > 1500",
            "sharpe": 2.65,
            "dsr_prob": 0.9810,
            "mc_p95_dd": 2.25,
            "profit_factor": 2.55,
            "win_rate": 70.0,
            "status": "BENCH_RESERVE"
        },
        {
            "id": "RES-CRYPTO-BTC-001",
            "asset": "BTC",
            "timeframe": "1h",
            "desk_mode": "CAPITAL_PROPIO",
            "family": "Funding Rate Mean Reversion",
            "macro_anchor": "BTC Hourly Funding Rate Arbitrage",
            "regime_gate": "TRENDING_BEARISH",
            "symbolic_trigger": "HourlyFunding < -0.01% & RSI(14) < 30",
            "sharpe": 2.40,
            "dsr_prob": 0.9520,
            "mc_p95_dd": 4.10,
            "profit_factor": 2.30,
            "win_rate": 66.0,
            "status": "BENCH_RESERVE"
        },
        {
            "id": "RES-CRYPTO-ETH-001",
            "asset": "ETH",
            "timeframe": "1h",
            "desk_mode": "CAPITAL_PROPIO",
            "family": "Donchian Trend Following",
            "macro_anchor": "ETH Donchian Breakout 1h",
            "regime_gate": "TRENDING_BULLISH",
            "symbolic_trigger": "Close > UpperDonchian(20) & Volume > SMA(Volume, 20)",
            "sharpe": 2.30,
            "dsr_prob": 0.9410,
            "mc_p95_dd": 4.50,
            "profit_factor": 2.20,
            "win_rate": 63.5,
            "status": "BENCH_RESERVE"
        }
    ]

    inserted = 0
    for s in initial_strats:
        res = deposit_candidate(
            candidate=s,
            audit_phase3={"dsr_prob": s["dsr_prob"], "mc_p95_dd": s["mc_p95_dd"]},
            status=s["status"],
            db_path=db_path
        )
        if res:
            inserted += 1

    return inserted


if __name__ == '__main__':
    print("Inicializando Strategy Vault SQLite...")
    init_vault()
    seeded = seed_vault_initial_data()
    print(f"Strategy Vault inicializado y poblado con {seeded} estrategias.")
    summary = get_vault_summary()
    print(f"Titulares: {summary['counts']['starters']} | Banco de Reserva (DSR >= 0.85): {summary['counts']['bench_reserves']}")
