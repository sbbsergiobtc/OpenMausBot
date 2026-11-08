#!/usr/bin/env python3
"""
Módulo de Gestión de Riesgo Macro: Filtro Activo de Noticias (Blackout ±5 Minutos)
AlgrokQuant · Desk Lead Nexus · Directiva Mandatoria de Sergio

Regla Operativa Estricta:
- Queda terminantemente PROHIBIDO abrir operaciones o mantener órdenes vivas
  5 minutos antes y 5 minutos después de un evento macroeconómico de alto impacto (High Impact).
- Aplica universalmente a cuentas de Prop Firm (evaluación y fondeada) y a Capital Propio.
- Activos monitoreados: USD para US500, USTEC, Cripto y EUR/USD; EUR para EUR/USD.
"""

import os
import json
import yaml
import time
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Tuple, Optional, Dict, List, Any

BASE_DIR = Path('/root/AlgrokQuant') if Path('/root/AlgrokQuant').exists() else Path(__file__).resolve().parent.parent
RULES_FILE = BASE_DIR / "config/risk_rules.yaml"
CALENDAR_CACHE = BASE_DIR / "data/economic_calendar.json"

# Mapeo de Activo a Monedas de Impacto Macro
# Divisas autorizadas para el Filtro de Riesgo Macro (Sergio Directiva: solo EUR, USD, GBP)
ALLOWED_CURRENCIES = {'EUR', 'USD', 'GBP'}

ASSET_CURRENCY_MAP = {
    'US500': ['USD'],
    'USTEC': ['USD'],
    'SPX': ['USD'],
    'NDX': ['USD'],
    'EURUSD': ['USD', 'EUR'],
    'EUR_USD': ['USD', 'EUR'],
    'GBPUSD': ['USD', 'GBP'],
    'GBP_USD': ['USD', 'GBP'],
    'BTC': ['USD'],
    'BTCUSDT': ['USD'],
    'ETH': ['USD'],
    'ETHUSDT': ['USD'],
    'SOL': ['USD'],
    'SOLUSDT': ['USD']
}

# Palabras clave de eventos de Nivel 1 Crítico
HIGH_IMPACT_KEYWORDS = [
    'FOMC', 'FED', 'RATE DECISION', 'INTEREST RATE',
    'CPI', 'CONSUMER PRICE INDEX', 'INFLATION',
    'NFP', 'NON-FARM', 'EMPLOYMENT', 'UNEMPLOYMENT RATE',
    'PPI', 'PCE', 'GDP', 'POWELL'
]

_MEM_CALENDAR_CACHE: List[Dict[str, Any]] = []
_LAST_FETCH_TIME: float = 0.0


def load_news_policy() -> Dict[str, Any]:
    """Carga la configuración de la ventana de blackout desde config/risk_rules.yaml."""
    default_policy = {
        'allow_news_trading': False,
        'blackout_window_minutes_before': 5,
        'blackout_window_minutes_after': 5,
        'high_impact_events': HIGH_IMPACT_KEYWORDS
    }
    if not RULES_FILE.exists():
        return default_policy
    try:
        with open(RULES_FILE, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
            return cfg.get('news_trading_policy', default_policy)
    except Exception as e:
        print(f"[WARN] Error leyendo {RULES_FILE}: {e}")
        return default_policy


def fetch_and_cache_economic_calendar(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    Descarga el calendario económico semanal de Forex Factory y lo cachea localmente.
    Usa caché en memoria y archivo por 1 hora para evitar latencias de red en cada evaluación.
    """
    global _MEM_CALENDAR_CACHE, _LAST_FETCH_TIME
    now_t = time.time()

    if not force_refresh and _MEM_CALENDAR_CACHE and (now_t - _LAST_FETCH_TIME < 3600):
        return _MEM_CALENDAR_CACHE

    # Si el archivo en disco existe y tiene menos de 1 hora
    if not force_refresh and CALENDAR_CACHE.exists():
        try:
            mtime = os.path.getmtime(CALENDAR_CACHE)
            if now_t - mtime < 3600:
                with open(CALENDAR_CACHE, 'r', encoding='utf-8') as f:
                    _MEM_CALENDAR_CACHE = json.load(f)
                    _LAST_FETCH_TIME = now_t
                    return _MEM_CALENDAR_CACHE
        except Exception:
            pass

    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    headers = {"User-Agent": "AlgrokQuant-MacroRisk/2.0"}
    
    events: List[Dict[str, Any]] = []
    try:
        resp = requests.get(url, headers=headers, timeout=4)
        if resp.status_code == 200:
            events = resp.json()
            CALENDAR_CACHE.parent.mkdir(parents=True, exist_ok=True)
            with open(CALENDAR_CACHE, 'w', encoding='utf-8') as f:
                json.dump(events, f, indent=2)
            _MEM_CALENDAR_CACHE = events
            _LAST_FETCH_TIME = now_t
            return events
    except Exception as e:
        print(f"[INFO] No se pudo refrescar calendario online ({e}). Usando caché local...")

    if CALENDAR_CACHE.exists():
        try:
            with open(CALENDAR_CACHE, 'r', encoding='utf-8') as f:
                _MEM_CALENDAR_CACHE = json.load(f)
                _LAST_FETCH_TIME = now_t
                return _MEM_CALENDAR_CACHE
        except Exception as e:
            print(f"[WARN] Error leyendo caché de calendario: {e}")

    return _MEM_CALENDAR_CACHE or []


def parse_event_datetime(date_str: str) -> Optional[datetime]:
    """Parsea el timestamp ISO del evento a UTC."""
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def is_high_impact_event(event: Dict[str, Any]) -> bool:
    """
    Directiva Forex Factory de Sergio:
    Solo son de alto impacto las noticias con CARPETA ROJA (impact == 'High')
    y los días festivos / Bank Holidays (impact == 'Holiday' o 'bank holiday' en título).
    """
    impact = str(event.get('impact', '')).strip()
    title = str(event.get('title', '')).strip().lower()

    if impact == 'High':
        return True
    if impact == 'Holiday' or 'bank holiday' in title or 'holiday' in title:
        return True
    return False

def check_news_blackout(symbol: str, target_time_utc: Optional[datetime] = None) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    INTERCEPTOR DE EJECUCIÓN (Regla Directa de Sergio):
    Comprueba si el símbolo solicitado se encuentra actualmente dentro de la ventana de Blackout
    (5 minutos antes o 5 minutos después de una noticia de alto impacto).

    Retorna:
      - (True, motivo, evento) si la orden DEBE SER BLOQUEADA.
      - (False, None, None) si el mercado está limpio y la orden PUEDE EJECUTARSE.
    """
    now = target_time_utc or datetime.now(timezone.utc)
    policy = load_news_policy()
    
    if policy.get('allow_news_trading', False):
        return False, None, None

    win_before = float(policy.get('blackout_window_minutes_before', 5))
    win_after = float(policy.get('blackout_window_minutes_after', 5))

    clean_sym = symbol.upper().replace('/', '').replace('_', '')
    relevant_currencies = ASSET_CURRENCY_MAP.get(clean_sym, ['USD'])

    events = fetch_and_cache_economic_calendar()
    if not events:
        return False, None, None

    for ev in events:
        ev_country = str(ev.get('country', '')).upper()
        if ev_country not in relevant_currencies:
            continue

        if not is_high_impact_event(ev):
            continue

        ev_dt = parse_event_datetime(ev.get('date', ''))
        if not ev_dt:
            continue

        # diff_minutes > 0: El evento ocurrirá en el futuro próximo
        # diff_minutes < 0: El evento ocurrió en el pasado reciente
        diff_minutes = (ev_dt - now).total_seconds() / 60.0

        # Ventana de Blackout: Entre -win_after (-5m) y +win_before (+5m)
        if -win_after <= diff_minutes <= win_before:
            phase = "FALTAN" if diff_minutes >= 0 else "PASARON"
            reason = (
                f"BLACKOUT NOTICIA ±5 MIN: {ev.get('title')} ({ev_country}) programado para {ev.get('date')}. "
                f"Estado: {phase} {abs(diff_minutes):.1f} min (Límite: ±{win_before:.0f}m)"
            )
            return True, reason, ev

    return False, None, None


def get_macro_risk_status() -> Dict[str, Any]:
    """Devuelve un resumen de estado de riesgo macro para el Dashboard y Telemetría (Filtrado estricto a EUR, USD, GBP)."""
    policy = load_news_policy()
    events = fetch_and_cache_economic_calendar()
    now = datetime.now(timezone.utc)

    upcoming_high_impact = []
    active_blackout = None

    for ev in events:
        country = str(ev.get('country', '')).strip().upper()
        # Directiva Sergio: mostrar solo eventos de EUR, USD, GBP
        if country not in ALLOWED_CURRENCIES:
            continue
        if not is_high_impact_event(ev):
            continue
        ev_dt = parse_event_datetime(ev.get('date', ''))
        if not ev_dt:
            continue

        diff_min = (ev_dt - now).total_seconds() / 60.0
        if -120.0 <= diff_min <= 10080.0:
            item = {
                'currency': country,
                'country': country,
                'title': ev.get('title'),
                'impact': ev.get('impact', 'High'),
                'datetime_utc': ev_dt.isoformat(),
                'minutes_away': round(diff_min, 1),
                'in_blackout': (-5.0 <= diff_min <= 5.0),
                'url': 'https://www.forexfactory.com/calendar'
            }
            upcoming_high_impact.append(item)
            if item['in_blackout'] and active_blackout is None:
                active_blackout = item

    # Ordenar eventos cronológicamente
    upcoming_high_impact.sort(key=lambda x: x['minutes_away'])

    return {
        'policy_enabled': not policy.get('allow_news_trading', False),
        'blackout_window_minutes_before': policy.get('blackout_window_minutes_before', 5),
        'blackout_window_minutes_after': policy.get('blackout_window_minutes_after', 5),
        'active_blackout': active_blackout,
        'upcoming_events_count': len(upcoming_high_impact),
        'upcoming_events': upcoming_high_impact
    }


if __name__ == "__main__":
    print("=== TEST NEWS RISK FILTER ===")
    status = get_macro_risk_status()
    print(f"Policy Enabled: {status['policy_enabled']}")
    print(f"Próximos eventos de alto impacto detectados: {status['upcoming_events_count']}")
    for ev in status['upcoming_events'][:5]:
        print(f" - [{ev['country']}] {ev['title']} en {ev['minutes_away']} min (Blackout: {ev['in_blackout']})")

    now_test = datetime.now(timezone.utc)
    is_blocked, reason, _ = check_news_blackout("US500", now_test)
    print(f"\nChequeo US500 ahora: Bloqueado={is_blocked} | Motivo={reason}")
