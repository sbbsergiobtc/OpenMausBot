#!/usr/bin/env python3
"""
Institutional Multi-Branch Forward Test & Live MT5 Compounding Execution Daemon
AlgrokQuant · Desk Lead Nexus
Gobernanza Dual (LESSON-017) & Validacion Trifacetica (LESSON-018)

EXCLUSIVO PARA ACTIVOS TRADFI (BROKER IC MARKETS MT5):
  • RAMA CAPITAL PROPIO (INTERES COMPUESTO DINAMICO % SOBRE BALANCE VIVO):
      1. CAP-SPX-006: S&P 500 4h Bollinger Dip Reversion (US500, 1.50% riesgo)
      2. CAP-NDX-005: Nasdaq 100 2h Bollinger Dip Reversion (USTEC, 1.50% riesgo)
  • RAMA CUENTAS DE FONDEO (PROP FIRM FOREX):
      3. PROP-FX-EUR-001: EUR/USD 1h London-NY Session (EURUSD, 1.00% riesgo)

NOTA: Cualquier estrategia Cripto (ej. STRAT-FAST-035 BTC) se ejecuta EXCLUSIVAMENTE
en proveedores cripto nativos (Hyperliquid DEX L1 / Binance) y NUNCA en MT5.
"""

import os
import sys
import json
import time
import datetime
import argparse
import numpy as np
import pandas as pd
import yfinance as yf

sys.path.insert(0, '/root/AlgrokQuant')
from execution.mt5_client import MT5Client

try:
    from jev.screener import JevScreener
    jev_screener = JevScreener(max_allowed_entropy=0.84, regime_shift_delta=0.12, max_capital_propio_dd=20.0)
except Exception as e:
    jev_screener = None
    print(f"[WARN] JevScreener no inicializado: {e}")

try:
    from jev.regime_orchestrator import run_parallel_orchestrator_evaluation
except Exception as e:
    run_parallel_orchestrator_evaluation = None
    print(f"[WARN] RegimeOrchestrator no inicializado: {e}")

try:
    from jev.news_risk_filter import check_news_blackout, get_macro_risk_status
except Exception as e:
    check_news_blackout = None
    get_macro_risk_status = None
    print(f"[WARN] NewsRiskFilter no inicializado: {e}")

try:
    from jev.auto_deployer import evaluate_forward_test_incubation_guardian, dispatch_telegram_message
except Exception as e:
    evaluate_forward_test_incubation_guardian = None
    dispatch_telegram_message = None
    print(f"[WARN] IncubationGuardian no inicializado: {e}")

try:
    from jev.rl_regime_env import apply_prop_firm_consistency_tp_clamp
    from jev.rl_q_agent import (
        query_q_learning_lot_multiplier,
        check_intrasemanal_drift_trigger,
        train_and_save_dual_q_policies,
        record_online_trade_experience,
        record_libro_c_telemetry,
    )
except Exception as e:
    apply_prop_firm_consistency_tp_clamp = None
    query_q_learning_lot_multiplier = None
    check_intrasemanal_drift_trigger = None
    train_and_save_dual_q_policies = None
    record_online_trade_experience = None
    record_libro_c_telemetry = None
    print(f"[WARN] Double Q-Learning Orchestrator no inicializado: {e}")

STATE_FILE = '/root/AlgrokQuant/data/paper_trades/prop_firm_forward_test_state.json'
JOURNAL_FILE = '/root/AlgrokQuant/library/journal/PROP_FIRM_SPRINT_JOURNAL.md'

PORTFOLIO_CONFIG = {
    # RAMA 2: CAPITAL PROPIO TRADFI (COMPUESTO % SOBRE BALANCE VIVO IC MARKETS)
    'US500': {
        'id': 'CAP-SPX-006',
        'branch': 'CAPITAL_PROPIO',
        'ticker_yf': '^GSPC',
        'broker_symbol': 'US500',
        'risk_pct': 0.010,     # 1.00% de riesgo por operacion (Interes Compuesto)
        'spread_pts': 0.4,
        'tf': '4h'
    },
    'USTEC': {
        'id': 'CAP-NDX-005',
        'branch': 'CAPITAL_PROPIO',
        'ticker_yf': '^NDX',
        'broker_symbol': 'USTEC',
        'risk_pct': 0.010,     # 1.00% de riesgo por operacion (Interes Compuesto)
        'spread_pts': 1.5,
        'tf': '2h'
    },
    # RAMA 1: FOREX PROP FIRM
    'EURUSD': {
        'id': 'PROP-FX-EUR-001',
        'branch': 'PROP_FIRM',
        'ticker_yf': 'EURUSD=X',
        'broker_symbol': 'EURUSD',
        'risk_pct': 0.010,     # 1.00% de riesgo por operacion (Proteccion EOD DD)
        'spread_pts': 0.00008,
        'tf': '1h'
    }
}

mt5 = MT5Client()


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
                if 'capital_propio' not in state:
                    state['capital_propio'] = {'open_positions': {}, 'closed_trades': []}
                if 'prop_firm' not in state:
                    state['prop_firm'] = {'open_positions': {}, 'closed_trades': []}
                if 'active_accounts' not in state:
                    state['active_accounts'] = {
                        'prop_firm': {
                            'account_id': 'PROP-50K-01',
                            'firm_name': 'LUCID_TRADING',
                            'stage': 'EVALUATION',
                            'consistency_rule_enabled': True,
                            'max_single_trade_profit_pct': 40.0,
                            'max_concurrent_trades': 3
                        },
                        'capital_propio': {
                            'account_id': 'CAP-PROPIO-01',
                            'firm_name': 'INTERACTIVE_BROKERS',
                            'stage': 'LIVE_CAPITAL',
                            'consistency_rule_enabled': False,
                            'max_single_trade_profit_pct': None,
                            'max_concurrent_trades': 3
                        }
                    }
                return state
        except Exception as e:
            print(f"Error cargando estado ({e}). Reinicializando...")

    return {
        'status': 'ACTIVE',
        'start_date': str(datetime.date.today()),
        'capital_propio': {
            'initial_balance': 1000.0,
            'current_balance': 1000.0,
            'open_positions': {},
            'closed_trades': []
        },
        'prop_firm': {
            'initial_balance': 100000.0,
            'current_balance': 100000.0,
            'open_positions': {},
            'closed_trades': []
        },
        'live_broker_sync': {
            'account': None,
            'broker_balance': 1000.0,
            'broker_equity': 1000.0,
            'last_sync': None
        },
        'order_history': [],
        'last_eval_timestamp': None
    }


def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def calculate_dynamic_lots(symbol_key: str, balance: float, entry_p: float, sl_p: float) -> float:
    cfg = PORTFOLIO_CONFIG[symbol_key]
    broker_sym = cfg['broker_symbol']
    risk_pct = cfg['risk_pct']

    sym_info = mt5.get_symbol_info(broker_sym).get('symbol', {})
    cs = float(sym_info.get('trade_contract_size', 1.0))
    vmin = float(sym_info.get('volume_min', 0.01))
    vmax = float(sym_info.get('volume_max', 100.0))
    vstep = float(sym_info.get('volume_step', 0.01))

    risk_usd = balance * risk_pct
    sl_dist = abs(entry_p - sl_p)
    if sl_dist <= 0:
        return vmin

    raw_lots = risk_usd / (sl_dist * cs)
    stepped_lots = round(raw_lots / vstep) * vstep
    final_lots = max(vmin, min(vmax, stepped_lots))
    return round(final_lots, 4)


def fetch_latest_candles(ticker: str, interval: str = '1h', period: str = '60d') -> pd.DataFrame:
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty:
            return df
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
        return df.dropna()
    except Exception as e:
        print(f"Error descargando {ticker}: {e}")
        return pd.DataFrame()


def evaluate_ndx_2h(df_1h: pd.DataFrame) -> dict:
    df_2h = df_1h.resample('2h').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna()
    if len(df_2h) < 50:
        return {'signal': 'HOLD', 'last_price': 0.0, 'sma': 0.0, 'atr': 0.0}
    c = df_2h['close']
    ema200 = c.ewm(span=200, adjust=False).mean()
    sma20 = c.rolling(20).mean()
    std20 = c.rolling(20).std()
    lower_bb = sma20 - 2.0 * std20

    last_c = float(c.iloc[-1])
    last_sma = float(sma20.iloc[-1])
    last_lower = float(lower_bb.iloc[-1])
    last_ema = float(ema200.iloc[-1])
    atr = float(df_2h['high'].iloc[-1] - df_2h['low'].iloc[-1])

    sig = 'BUY' if (last_c < last_lower and last_c > last_ema) else ('EXIT' if last_c > last_sma else 'HOLD')
    return {'signal': sig, 'last_price': last_c, 'sma': last_sma, 'lower': last_lower, 'atr': atr}


def evaluate_spx_4h(df_1h: pd.DataFrame) -> dict:
    df_4h = df_1h.resample('4h').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna()
    if len(df_4h) < 50:
        return {'signal': 'HOLD', 'last_price': 0.0, 'sma': 0.0, 'atr': 0.0}
    c = df_4h['close']
    ema200 = c.ewm(span=200, adjust=False).mean()
    sma20 = c.rolling(20).mean()
    std20 = c.rolling(20).std()
    lower_bb = sma20 - 1.2 * std20

    last_c = float(c.iloc[-1])
    last_sma = float(sma20.iloc[-1])
    last_lower = float(lower_bb.iloc[-1])
    last_ema = float(ema200.iloc[-1])
    atr = float(df_4h['high'].iloc[-1] - df_4h['low'].iloc[-1])

    sig = 'BUY' if (last_c < last_lower and last_c > last_ema) else ('EXIT' if last_c > last_sma else 'HOLD')
    return {'signal': sig, 'last_price': last_c, 'sma': last_sma, 'lower': last_lower, 'atr': atr}


def evaluate_eur_1h(df_1h: pd.DataFrame) -> dict:
    if len(df_1h) < 100:
        return {'signal': 'HOLD', 'last_price': 0.0, 'sma': 0.0, 'atr': 0.0}
    c = df_1h['close']
    hour = df_1h.index[-1].hour
    is_session = 7 <= hour <= 17
    sma24 = c.rolling(24).mean()
    std24 = c.rolling(24).std()
    lower_bb = sma24 - 2.0 * std24
    delta = c.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi14 = 100 - (100 / (1 + gain / (loss.replace(0, np.nan) + 1e-9)))

    last_c = float(c.iloc[-1])
    last_sma = float(sma24.iloc[-1])
    last_lower = float(lower_bb.iloc[-1])
    last_rsi = float(rsi14.iloc[-1])
    atr = float(df_1h['high'].iloc[-1] - df_1h['low'].iloc[-1])

    sig = 'BUY' if (is_session and last_c < last_lower and last_rsi < 35) else ('EXIT' if last_c > last_sma else 'HOLD')
    return {'signal': sig, 'last_price': last_c, 'sma': last_sma, 'lower': last_lower, 'atr': atr}


def sync_broker_state(state: dict) -> float:
    live_balance = 1000.0
    if not mt5.is_healthy():
        print("  [MT5] Puente no responde en 127.0.0.1:8001.")
        return live_balance
    try:
        acc = mt5.get_health()
        live_balance = float(acc.get('balance', 1000.0))
        state['live_broker_sync'] = {
            'account': acc.get('login'),
            'server': acc.get('server'),
            'broker_balance': live_balance,
            'broker_equity': float(acc.get('equity', live_balance)),
            'currency': acc.get('currency'),
            'trade_allowed': acc.get('trade_allowed'),
            'last_sync': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        print(f"  [MT5 SYNC] Cuenta {acc.get('login')} | Balance Vivo: ${live_balance:,.2f} USD (Interes Compuesto TradFi)")
    except Exception as e:
        print(f"  [MT5] Error sincronizando cuenta: {e}")
    return live_balance


def run_cycle():
    state = load_state()
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    print(f"\n[{now_str}] Ciclo Multiactivo TradFi: Capital Propio (% Compuesto) & Prop Firms...")

    # 1. Sincronizar Balance Vivo con IC Markets MT5
    current_live_balance = sync_broker_state(state)

    # 1a. Estado de Riesgo Macro y Calendario Económico (Regla Blackout ±5 min)
    if get_macro_risk_status is not None:
        try:
            m_status = get_macro_risk_status()
            state['macro_risk_status'] = m_status
            if m_status.get('active_blackout'):
                ab = m_status['active_blackout']
                print(f"  [ALERTA MACRO] BLACKOUT ACTIVO: {ab['title']} ({ab['country']}) a las {ab['datetime_utc']}")
        except Exception as me:
            print(f"  [WARN] Error actualizando MacroRiskStatus: {me}")

    # 1b. Actualizar Orquestador Paralelo A/B (10 Sub-estados y multiplicadores de lotaje 1.25x..0.00x)
    if run_parallel_orchestrator_evaluation is not None:
        try:
            orch_res = run_parallel_orchestrator_evaluation()
            summary_obj = orch_res.get('summary', orch_res.get('ab_portfolio_summary', {}))
            val_add = summary_obj.get('orchestrator_value_add', {})
            state['regime_orchestrator_summary'] = summary_obj
            state['market_regimes'] = orch_res.get('regimes_by_asset', {})
            extra_roi = val_add.get('extra_roi_pct', summary_obj.get('orchestrator_alpha_roi_pct', 0.0))
            whipsaws = val_add.get('whipsaws_filtered', summary_obj.get('total_whipsaws_avoided', 0))
            print(f"  [ORQUESTADOR PARALELO A/B] Alfa Neto: +{extra_roi}% | Whipsaws Evitados: {whipsaws}")
        except Exception as e:
            print(f"  [WARN] Error ejecutando Orquestador Paralelo A/B: {e}")

    # 1c. Evaluar Guardián de Incubación Forward Test (Cono Monte Carlo P05/P50/P95 + Semáforo GREEN/AMBER/RED)
    guardian_mult_by_id = {}
    guardian_light_by_id = {}
    if evaluate_forward_test_incubation_guardian is not None:
        for branch_key in ['prop_firm', 'capital_propio']:
            branch_obj = state.get(branch_key, {})
            active_strats = branch_obj.get('active_strategies', [])
            closed_all = branch_obj.get('closed_trades', [])
            for strat in active_strats:
                try:
                    sid = strat.get('strategy_id', 'UNKNOWN')
                    prev_ready = bool(strat.get('incubation_guardian', {}).get('ready_for_real_account', False))
                    strat_pnls = strat.get('live_trade_pnls') or [
                        float(t.get('pnl_usd') or t.get('pnl') or 0.0)
                        for t in closed_all
                        if isinstance(t, dict) and t.get('strategy_id') == sid
                    ]
                    curr_dd = float(strat.get('current_dd_pct') or branch_obj.get('current_eod_dd_pct') or 0.0)
                    g_res = evaluate_forward_test_incubation_guardian(strat, strat_pnls, curr_dd)
                    strat['incubation_guardian'] = g_res
                    guardian_mult_by_id[sid] = float(g_res.get('lot_sizing_multiplier', 1.0))
                    guardian_light_by_id[sid] = str(g_res.get('traffic_light', 'GREEN'))
                    if g_res.get('ready_for_real_account') and not prev_ready and dispatch_telegram_message is not None:
                        dispatch_telegram_message(
                            "AlphaReporter",
                            f"🟢 <b>ESTRATEGIA LISTA PARA CUENTA REAL</b>\n\n"
                            f"• <b>ID:</b> <code>{sid}</code> ({strat.get('asset', '')} {strat.get('timeframe', '')})\n"
                            f"• <b>Estado Guardián:</b> {g_res.get('traffic_light')} (Trades OOS: {g_res.get('trades_evaluated')})\n"
                            f"• <b>Diagnóstico:</b> {g_res.get('verdict')}"
                        )
                except Exception as ge:
                    print(f"  [WARN] Error evaluando IncubationGuardian para {strat.get('strategy_id')}: {ge}")

    # 1d. Gatillo Intra-Semanal por Deriva (Drift Trigger) para Recalibración Double Q-Learning
    if check_intrasemanal_drift_trigger is not None and train_and_save_dual_q_policies is not None:
        try:
            drift_info = check_intrasemanal_drift_trigger(state, state.get('market_regimes', {}))
            state['q_learning_drift_status'] = drift_info
            if drift_info.get('drift_triggered'):
                state['last_drift_retrain_time'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                print(f"  [Q-LEARNING DRIFT TRIGGER] {drift_info.get('reason')} -> Re-entrenando políticas 80/20 + Polyak...")
                retrain_res = train_and_save_dual_q_policies(trigger_reason="INTRASEMANAL_DRIFT_TRIGGER")
                if dispatch_telegram_message is not None:
                    dispatch_telegram_message(
                        "AlphaReporter",
                        f"⚠️ <b>RE-ENTRENAMIENTO Q-LEARNING POR DERIVA (DRIFT TRIGGER)</b>\n\n"
                        f"• <b>Causa:</b> {drift_info.get('reason')}\n"
                        f"• <b>Amortiguación:</b> Polyak τ = 0.25 (80% Estructural / 20% Memoria Reciente)\n"
                        f"• <b>Políticas Actualizadas:</b> PROP_FIRM & CAPITAL_PROPIO"
                    )
        except Exception as de:
            print(f"  [WARN] Error en check_intrasemanal_drift_trigger: {de}")

    evaluators = {
        'US500':  (evaluate_spx_4h, '1h', '730d'),
        'USTEC':  (evaluate_ndx_2h, '1h', '730d'),
        'EURUSD': (evaluate_eur_1h, '1h', '60d')
    }

    market_snapshot = {}

    for sym, (eval_fn, interval, period) in evaluators.items():
        cfg = PORTFOLIO_CONFIG[sym]
        strat_id = cfg['id']
        branch = cfg['branch']
        broker_sym = cfg['broker_symbol']

        df = fetch_latest_candles(cfg['ticker_yf'], interval=interval, period=period)
        if df.empty:
            continue

        sig_data = eval_fn(df)
        market_snapshot[sym] = sig_data
        sig = sig_data['signal']
        price = sig_data['last_price']
        atr = max(sig_data.get('atr', price * 0.01), price * 0.005)

        print(f"  [{branch}] {sym} ({strat_id}): Precio={price:.4f} | Señal={sig}")

        pos_container = state['capital_propio']['open_positions'] if branch == 'CAPITAL_PROPIO' else state['prop_firm']['open_positions']
        pos = pos_container.get(sym)

        # A) Cierre de Posicion: por señal cuantitativa o por REGLA OBLIGATORIA MACRO (cerrar 5 min antes de noticias)
        is_news_exit = False
        if pos is not None and check_news_blackout is not None:
            is_blackout, blackout_reason, ev_data = check_news_blackout(sym)
            if is_blackout:
                is_news_exit = True
                print(f"  [CIERRE PREVENTIVO NOTICIAS MACRO] Posicion abierta en {sym} ({strat_id}) DEBE CERRARSE 5 MIN ANTES: {blackout_reason}")

        if pos is not None and (sig == 'EXIT' or is_news_exit):
            ticket = pos.get('live_ticket')
            if ticket and mt5.is_healthy():
                print(f"  [MT5] Cerrando en broker posicion viva Ticket {ticket} ({broker_sym})...")
                mt5.close_position(ticket=ticket)

            # Cálculo de PnL Realizado y R-Múltiplo para Replay Memory
            exit_p = price - (cfg['spread_pts'] / 2.0)
            entry_p = float(pos.get('entry_price', price))
            lots = float(pos.get('dynamic_lots', 0.01))
            risk_usd = float(pos.get('risk_usd', 10.0))
            sl_price = float(pos.get('sl_price', entry_p - atr * 1.5))
            sl_dist = max(1e-6, abs(entry_p - sl_price))

            pnl_pts = (exit_p - entry_p)
            r_mult = pnl_pts / sl_dist
            realized_pnl = r_mult * risk_usd
            clamped = bool(pos.get('consistency_clamped', False))
            q_meta = pos.get('q_decision', {})

            closed_rec = {
                'strategy_id': strat_id,
                'symbol': sym,
                'branch': branch,
                'entry_time': pos.get('entry_time'),
                'exit_time': now_str,
                'entry_price': entry_p,
                'exit_price': exit_p,
                'lots': lots,
                'risk_usd': round(risk_usd, 2),
                'pnl_usd': round(realized_pnl, 2),
                'r_multiple': round(r_mult, 2),
                'consistency_clamped': clamped,
                'q_decision': q_meta
            }

            b_key = 'capital_propio' if branch == 'CAPITAL_PROPIO' else 'prop_firm'
            state[b_key].setdefault('closed_trades', []).append(closed_rec)

            # Inyectar experiencia en el Buffer Online de Aprendizaje por Refuerzo
            if record_online_trade_experience is not None:
                record_online_trade_experience(
                    desk_mode=branch,
                    regime_id_10=int(q_meta.get('regime_id_10', 6)),
                    archetype_or_anchor=strat_id,
                    guardian_traffic_light=str(q_meta.get('guardian_state', 'GREEN')),
                    action_multiplier=float(q_meta.get('q_lot_multiplier', 1.0)),
                    pnl_usd=realized_pnl,
                    r_multiple=r_mult,
                    consistency_clamped=clamped,
                    symbol=sym,
                    strategy_id=strat_id,
                )

            # Telemetría en Vivo de Libro C
            if record_libro_c_telemetry is not None:
                record_libro_c_telemetry(
                    event_type="TRADE_CLOSED",
                    desk_mode=branch,
                    symbol=sym,
                    strategy_id=strat_id,
                    regime_id_10=int(q_meta.get('regime_id_10', 6)),
                    archetype_or_anchor=strat_id,
                    guardian_traffic_light=str(q_meta.get('guardian_state', 'GREEN')),
                    action_multiplier=float(q_meta.get('q_lot_multiplier', 1.0)),
                    q_value=float(q_meta.get('q_value', 0.0)),
                    details={
                        'entry_price': entry_p,
                        'exit_price': exit_p,
                        'pnl_usd': round(realized_pnl, 2),
                        'r_multiple': round(r_mult, 2),
                        'consistency_clamped': clamped
                    }
                )

            del pos_container[sym]
            print(f"  >>> CERRADA POSICION EN {sym} ({strat_id}) | Realized PnL: ${realized_pnl:+.2f} ({r_mult:+.2f}R) <<<")

        # B) Apertura de Posicion con INTERES COMPUESTO + DOUBLE Q-LEARNING (10 ESTADOS) + TOPE 40% CONSISTENCIA
        elif pos is None and sig == 'BUY':
            regime_asset_map = {'US500': 'SPX', 'USTEC': 'NDX', 'EURUSD': 'EUR_USD'}
            reg_info = state.get('market_regimes', {}).get(regime_asset_map.get(sym, sym), {})
            regime_id_10 = int(reg_info.get('regime_id_10', 6))
            sub_regime_10 = reg_info.get('sub_regime_10', 'S6_CLEAN_MEAN_REVERSION')
            guard_light = guardian_light_by_id.get(strat_id, 'GREEN')
            guard_lot_mult = float(guardian_mult_by_id.get(strat_id, 1.0))

            q_dec = {}
            if query_q_learning_lot_multiplier is not None:
                q_dec = query_q_learning_lot_multiplier(branch, regime_id_10, strat_id, guard_light)
                q_mult = float(q_dec.get('q_lot_multiplier', reg_info.get('lot_multiplier', 1.0)))
                effective_mult = round(min(q_mult, guard_lot_mult if guard_light != 'GREEN' else 1.25), 4)
            else:
                regime_lot_mult = float(reg_info.get('lot_multiplier', 1.0))
                effective_mult = round(regime_lot_mult * guard_lot_mult, 4)

            if effective_mult <= 0.0:
                print(f"  [BLOQUEO Q-LEARNING/GUARDIAN] {sym} ({strat_id}) bloqueado: SubRegimen={sub_regime_10} (effective_mult={effective_mult}x, guard={guard_light})")
                if record_libro_c_telemetry is not None:
                    record_libro_c_telemetry(
                        event_type="TRADE_BLOCKED_BY_Q",
                        desk_mode=branch,
                        symbol=sym,
                        strategy_id=strat_id,
                        regime_id_10=regime_id_10,
                        archetype_or_anchor=strat_id,
                        guardian_traffic_light=guard_light,
                        action_multiplier=0.0,
                        q_value=float(q_dec.get('q_value', 0.0)),
                        details={'reason': f"Whipsaw Evitado en {sub_regime_10}", 'guard': guard_light}
                    )
                continue

            # ==============================================================
            # REGLAS DE GESTION DE CARTERA INSTITUCIONAL (BLOQUE 2)
            # ==============================================================
            # Búsqueda dinámica en el catálogo de cuentas registradas (sin hardcodeo)
            catalog = state.get('accounts_catalog', [])
            matched_acc = next((a for a in catalog if a.get('desk_type') == branch), None)
            if matched_acc is None:
                matched_acc = state.get('active_accounts', {}).get(branch.lower(), {})

            firm_name = matched_acc.get('firm_name', 'ICMarketsSC-Demo' if branch == 'PROP_FIRM' else 'INTERACTIVE_BROKERS')
            account_stage = matched_acc.get('stage', 'EVALUATION' if branch == 'PROP_FIRM' else 'LIVE_CAPITAL')
            consistency_active = (account_stage == 'EVALUATION') and matched_acc.get('consistency_rule_enabled', True)

            # 0. CANDADO DE RIESGO MACRO (BLACKOUT NOTICIAS ±5 MINUTOS - DIRECTIVA SERGIO)
            if check_news_blackout is not None:
                is_blackout, blackout_reason, ev_data = check_news_blackout(sym)
                if is_blackout:
                    print(f"  [BLOQUEO NOTICIAS MACRO ±5 MIN] {sym} ({strat_id}): {blackout_reason}")
                    if record_libro_c_telemetry is not None:
                        record_libro_c_telemetry(
                            event_type="REJECTED_NEWS_BLACKOUT",
                            desk_mode=branch,
                            symbol=sym,
                            strategy_id=strat_id,
                            regime_id_10=regime_id_10,
                            archetype_or_anchor=strat_id,
                            guardian_traffic_light=guard_light,
                            action_multiplier=0.0,
                            q_value=float(q_dec.get('q_value', 0.0)),
                            details={'reason': blackout_reason, 'event': ev_data.get('title'), 'date': ev_data.get('date')}
                        )
                    continue

            # 1. CANDADO DIRECCIONAL POR FIRMA (Firm-Scoped Anti-Hedging)
            # Solo bloquea si existe posición contraria en el MISMO ACTIVO dentro de la MISMA FIRMA
            has_opposite_firm_trade = False
            for open_sym, open_pos in pos_container.items():
                if open_sym == sym and open_pos.get('firm_name', firm_name) == firm_name:
                    open_action = str(open_pos.get('action', 'BUY')).upper()
                    if ('SELL' in open_action and sig == 'BUY') or ('BUY' in open_action and sig == 'SELL'):
                        has_opposite_firm_trade = True
                        break

            if has_opposite_firm_trade:
                print(f"  [BLOQUEO ANTI-HEDGING MISMA FIRMA] {sym} ({strat_id}): Posicion contraria activa en {firm_name}")
                if record_libro_c_telemetry is not None:
                    record_libro_c_telemetry(
                        event_type="REJECTED_SAME_FIRM_HEDGING",
                        desk_mode=branch,
                        symbol=sym,
                        strategy_id=strat_id,
                        regime_id_10=regime_id_10,
                        archetype_or_anchor=strat_id,
                        guardian_traffic_light=guard_light,
                        action_multiplier=0.0,
                        q_value=float(q_dec.get('q_value', 0.0)),
                        details={'reason': f"Anti-Hedging Rule: posicion opuesta en {firm_name}", 'firm': firm_name}
                    )
                continue

            # 2. LÍMITE DE CONCURRENCIA DE CARTERA (Max 3 trades simultáneos por cuenta)
            max_concurrent = int(acc_info.get('max_concurrent_trades', 3))
            if len(pos_container) >= max_concurrent:
                print(f"  [BLOQUEO CONCURRENCIA CARTERA] {sym} ({strat_id}): Limite de {max_concurrent} trades simultaneos alcanzado en {branch}")
                if record_libro_c_telemetry is not None:
                    record_libro_c_telemetry(
                        event_type="TRADE_BLOCKED_PORTFOLIO_CAP",
                        desk_mode=branch,
                        symbol=sym,
                        strategy_id=strat_id,
                        regime_id_10=regime_id_10,
                        archetype_or_anchor=strat_id,
                        guardian_traffic_light=guard_light,
                        action_multiplier=0.0,
                        q_value=float(q_dec.get('q_value', 0.0)),
                        details={'reason': f"Cap de concurrencia alcanzado ({max_concurrent} trades)", 'max_cap': max_concurrent}
                    )
                continue

            entry_p = price + (cfg['spread_pts'] / 2.0)
            sl_dist = atr * 1.5
            sl_price = entry_p - sl_dist
            tp_price = entry_p + (atr * 2.5)

            # 3. SELECTOR DE FASE DE CUENTA (Consistencia activa en EVALUATION, libre en FUNDED/LIVE)
            consistency_note = "UNCLAMPED_FUNDED_STAGE" if not consistency_active else "N/A_CAP_PROPIO"
            is_early_clamped = False
            if branch == 'PROP_FIRM' and consistency_active and apply_prop_firm_consistency_tp_clamp is not None:
                today_realized_pct = float(state.get('prop_firm', {}).get('today_realized_profit_pct', 0.0))
                clamp_res = apply_prop_firm_consistency_tp_clamp(
                    entry_price=entry_p,
                    sl_price=sl_price,
                    tp_price=tp_price,
                    direction=1,
                    lot_multiplier=effective_mult,
                    base_risk_pct=cfg['risk_pct'] * 100.0,
                    target_challenge_pct=6.00,
                    today_realized_profit_pct=today_realized_pct,
                )
                if clamp_res.get('blocked_by_consistency'):
                    print(f"  [BLOQUEO CONSISTENCIA 40%] {sym} ({strat_id}): {clamp_res.get('reason')}")
                    if record_libro_c_telemetry is not None:
                        record_libro_c_telemetry(
                            event_type="TRADE_BLOCKED_BY_CONSISTENCY_40",
                            desk_mode=branch,
                            symbol=sym,
                            strategy_id=strat_id,
                            regime_id_10=regime_id_10,
                            archetype_or_anchor=strat_id,
                            guardian_traffic_light=guard_light,
                            action_multiplier=effective_mult,
                            q_value=float(q_dec.get('q_value', 0.0)),
                            details={'reason': clamp_res.get('reason')}
                        )
                    continue
                tp_price = float(clamp_res.get('clamped_tp_price', tp_price))
                consistency_note = clamp_res.get('reason', 'OK_40PCT')
                is_early_clamped = bool(clamp_res.get('early_tp_clamped', False))
                if is_early_clamped:
                    print(f"  [EARLY TP CLAMP 40%] {sym} ({strat_id}): {consistency_note}")
                    if record_libro_c_telemetry is not None:
                        record_libro_c_telemetry(
                            event_type="EARLY_TP_CLAMPED",
                            desk_mode=branch,
                            symbol=sym,
                            strategy_id=strat_id,
                            regime_id_10=regime_id_10,
                            archetype_or_anchor=strat_id,
                            guardian_traffic_light=guard_light,
                            action_multiplier=effective_mult,
                            q_value=float(q_dec.get('q_value', 0.0)),
                            details={'reason': consistency_note, 'clamped_tp': tp_price}
                        )

            effective_balance = current_live_balance * effective_mult
            dynamic_lots = calculate_dynamic_lots(sym, effective_balance, entry_p, sl_price)
            risk_usd = effective_balance * cfg['risk_pct']

            print(f"  [Q-LEARNING %] Balance: ${current_live_balance:,.2f} | Régimen ({sub_regime_10}): {effective_mult:.2f}x | Riesgo: ${risk_usd:.2f} -> {dynamic_lots} lotes en {broker_sym} | TP={tp_price:.4f}")

            ticket = None
            if mt5.is_healthy():
                live_res = mt5.open_order(
                    symbol=broker_sym,
                    order_type='BUY',
                    volume=dynamic_lots,
                    sl=sl_price,
                    tp=tp_price,
                    comment=f"{strat_id} %Comp"
                )
                print(f"  [MT5 ORDER RESULT] {live_res}")
                ticket = live_res.get('order') or live_res.get('deal')

            pos_container[sym] = {
                'strategy_id': strat_id,
                'branch': branch,
                'firm_name': firm_name,
                'account_stage': account_stage,
                'action': sig,
                'entry_price': entry_p,
                'dynamic_lots': dynamic_lots,
                'risk_usd': risk_usd,
                'sl_price': sl_price,
                'tp_price': tp_price,
                'entry_time': now_str,
                'live_ticket': ticket,
                'consistency_clamped': is_early_clamped,
                'q_decision': q_dec
            }
            state['order_history'].append({
                'timestamp': now_str,
                'symbol': sym,
                'strategy': strat_id,
                'branch': branch,
                'action': 'BUY_LONG',
                'lots': dynamic_lots,
                'price': entry_p,
                'sl': sl_price,
                'live_ticket': ticket,
                'notes': f"Sizing Q-Learning {effective_mult:.2f}x sobre ${current_live_balance:,.2f} ({sub_regime_10})"
            })
            print(f"  >>> NUEVA POSICION {branch}: {sym} {dynamic_lots} lotes | SL={sl_price:.4f} | Ticket={ticket} <<<")

            if record_libro_c_telemetry is not None:
                record_libro_c_telemetry(
                    event_type="TRADE_OPENED",
                    desk_mode=branch,
                    symbol=sym,
                    strategy_id=strat_id,
                    regime_id_10=regime_id_10,
                    archetype_or_anchor=strat_id,
                    guardian_traffic_light=guard_light,
                    action_multiplier=effective_mult,
                    q_value=float(q_dec.get('q_value', 0.0)),
                    details={
                        'sub_regime_10': sub_regime_10,
                        'lots': dynamic_lots,
                        'risk_usd': round(risk_usd, 2),
                        'entry_price': entry_p,
                        'sl_price': sl_price,
                        'tp_price': tp_price,
                        'consistency_clamped': is_early_clamped,
                        'consistency_note': consistency_note
                    }
                )

    state['last_eval_timestamp'] = now_str
    save_state(state)
    update_obsidian_journal(state, market_snapshot)
    return state


def update_obsidian_journal(state: dict, market_snapshot: dict):
    os.makedirs(os.path.dirname(JOURNAL_FILE), exist_ok=True)
    today = str(datetime.date.today())
    sync = state.get('live_broker_sync', {})

    open_cap = state.get('capital_propio', {}).get('open_positions', {})
    open_prop = state.get('prop_firm', {}).get('open_positions', {})

    rows = []
    for s, p in open_cap.items():
        curr_p = market_snapshot.get(s, {}).get('last_price', p['entry_price'])
        rows.append(f"| **CAPITAL PROPIO (TradFi)** | {s} ({p['strategy_id']}) | {p['entry_time']} | {p['dynamic_lots']} lotes | ${p['risk_usd']:.2f} | {p['entry_price']:.2f} | {p['sl_price']:.2f} | {curr_p:.2f} | Ticket: `{p.get('live_ticket', '-')}` |")

    for s, p in open_prop.items():
        curr_p = market_snapshot.get(s, {}).get('last_price', p['entry_price'])
        rows.append(f"| **PROP FIRM (Forex)** | {s} ({p['strategy_id']}) | {p['entry_time']} | {p['dynamic_lots']} lotes | ${p['risk_usd']:.2f} | {p['entry_price']:.2f} | {p['sl_price']:.2f} | {curr_p:.2f} | Ticket: `{p.get('live_ticket', '-')}` |")

    table_text = "\n".join(rows) if rows else "*Sin posiciones abiertas en este momento. Sistema en monitorizacion activa.*"

    content = rf"""---
title: "Bitacora Oficial · Capital Propio & Fondeo TradFi (Interes Compuesto MT5)"
date: "{today}"
last_evaluation: "{state.get('last_eval_timestamp')}"
status: "{state.get('status')}"
broker_account: "{sync.get('account', '-')}"
broker_server: "{sync.get('server', '-')}"
broker_balance: {sync.get('broker_balance', 0.0)}
broker_equity: {sync.get('broker_equity', 0.0)}
compounding_mode: "DYNAMIC_PERCENTAGE_RISK"
tags:
  - capital-propio-tradfi
  - prop-firm
  - interes-compuesto
  - mt5-live
  - tri-facet
---

# Bitacora Oficial · Capital Propio & Fondeo TradFi (Interes Compuesto MT5)

> [!NOTE]
> **Separacion Estricta de Ecosistemas de Ejecucion:**
> - **Activos TradFi (Indices y Forex):** Se gestionan exclusivamente en broker institucional **IC Markets MT5**.
> - **Activos Cripto:** Se gestionan exclusivamente en **Hyperliquid L1 DEX / Binance** (NUNCA en broker tradicional).

---

## 1. Cartera TradFi Activa y Estado de la Cuenta MT5

| Rama / Activo | Estrategia Oficial | Riesgo % | TF | Broker Ticker | Modo Sizing |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Capital Propio (Indices)** | **`CAP-SPX-006`** | **1.50%** | 4h | `US500` | Interes Compuesto Dinamico |
| **Capital Propio (Indices)** | **`CAP-NDX-005`** | **1.50%** | 2h | `USTEC` | Interes Compuesto Dinamico |
| **Fondeo (Forex)** | **`PROP-FX-EUR-001`** | **1.00%** | 1h | `EURUSD` | Proteccion EOD Drawdown |

| Metrica de Cuenta | Valor en Vivo | Observaciones |
| :--- | :---: | :---: |
| **Cuenta MT5** | **`{sync.get('account')}`** en **`{sync.get('server')}`** | IC Markets Demo SC (1:30) |
| **Balance Vivo** | **${sync.get('broker_balance', 0.0):,.2f} {sync.get('currency', 'USD')}** | Base para el calculo del proximo lote |
| **Equity Flotante** | **${sync.get('broker_equity', 0.0):,.2f} {sync.get('currency', 'USD')}** | Margen libre en MT5 |
| **Ultima Evaluacion** | `{state.get('last_eval_timestamp', '-')}` | Bucle horario continuo 24/7 |

---

## 2. Posiciones Vivas y Ordenes de Mercado

| Rama | Activo / Estrategia | Fecha Apertura | Lotaje Dinamico | Riesgo \$ | Entrada | Stop Loss | Actual | Ticket MT5 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
{table_text}

---
*Mantenido de forma autonoma por `algrokquant-forward-test.service` en `/library/journal/`.*
"""
    with open(JOURNAL_FILE, 'w', encoding='utf-8') as f:
        f.write(content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--daemon', action='store_true', help='Bucle continuo cada hora')
    args = parser.parse_args()

    if args.daemon:
        print("[AlgrokQuant Compounding Daemon] Iniciando bucle 24/7...")
        while True:
            try:
                run_cycle()
            except Exception as e:
                print(f"[ERROR] Excepcion en ciclo: {e}")
            time.sleep(3600)
    else:
        run_cycle()