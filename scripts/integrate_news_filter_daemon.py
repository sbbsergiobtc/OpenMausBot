import re

file_path = r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\scripts\prop_firm_forward_test_daemon.py'

with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
    text = f.read()

# 1. Add import
target_import = """try:
    from jev.auto_deployer import evaluate_forward_test_incubation_guardian, dispatch_telegram_message"""

new_import = """try:
    from jev.news_risk_filter import check_news_blackout, get_macro_risk_status
except Exception as e:
    check_news_blackout = None
    get_macro_risk_status = None
    print(f"[WARN] NewsRiskFilter no inicializado: {e}")

try:
    from jev.auto_deployer import evaluate_forward_test_incubation_guardian, dispatch_telegram_message"""

if target_import in text:
    text = text.replace(target_import, new_import, 1)
    print("1. NewsRiskFilter import added")
else:
    print("1. Target import NOT found")

# 2. Add macro_risk_status to state in run_cycle
target_cycle_start = """    # 1. Sincronizar Balance Vivo con IC Markets MT5
    current_live_balance = sync_broker_state(state)"""

new_cycle_start = """    # 1. Sincronizar Balance Vivo con IC Markets MT5
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
            print(f"  [WARN] Error actualizando MacroRiskStatus: {me}")"""

if target_cycle_start in text:
    text = text.replace(target_cycle_start, new_cycle_start, 1)
    print("2. Macro risk status update added to run_cycle")
else:
    print("2. Target cycle start NOT found")

# 3. Add order execution interceptor (Rule 0)
target_rules = """            # 1. CANDADO DIRECCIONAL POR FIRMA (Firm-Scoped Anti-Hedging)"""

new_rules = """            # 0. CANDADO DE RIESGO MACRO (BLACKOUT NOTICIAS ±5 MINUTOS - DIRECTIVA SERGIO)
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

            # 1. CANDADO DIRECCIONAL POR FIRMA (Firm-Scoped Anti-Hedging)"""

if target_rules in text:
    text = text.replace(target_rules, new_rules, 1)
    print("3. Order execution news blackout interceptor added")
else:
    print("3. Target rules NOT found")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)

import py_compile
py_compile.compile(file_path)
print("Daemon script updated and compiled successfully!")
