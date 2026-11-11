---
title: "Registro de Forward Test e Incubación Automatizada - AlgrokQuant"
date: "2026-11-11"
status: "VIGILANCIA 24/7 ACTIVA · TRIPLE LIBRO A/B/C"
daemon: "algrokquant-forward-test.service"
prop_firm_strategies: 32
capital_propio_strategies: 23
total_active_strategies: 55
graduated_count: 0
---

# Registro de Forward Test e Incubación en Tiempo Real (Snapshot 2026-11-11)

## 1. Estado General de la Flota y Triple Libro (A / B / C)
Al cierre de la sesión (`2026-11-11 02:42 CET`), todas las estrategias aprobadas (`55` totales sin truncamiento, segregadas por mesa y rol `TITULAR VIVO` / `SHADOW $1K`) operan conectadas en tiempo real sobre [`regime_orchestrator.py`](file:///C:/Users/Sergio/Documents/Antigravity/OpenMausBot/jev/regime_orchestrator.py) y [`backend.py`](file:///C:/Users/Sergio/Documents/Antigravity/OpenMausBot/dashboard/backend.py):

| Rama / Desglose | Estrategias Activas | Titulares Bróker | Suplentes Shadow ($1K) | Ejemplos en Vivo Verificados |
| :--- | :---: | :---: | :---: | :--- |
| **Capital Propio (`CAPITAL_PROPIO`)** | **23** | 4 (`CAP-SPX-006`, `CAP-NDX-005`, `CRYPTO-BTC-001`, `STRAT-20261024-028`) | 19 (`CAP-20261107-*`) | `CAP-SPX-006`: A `+0.15%` / C `+0.08%` · `CRYPTO-BTC-001`: A `+2.04%` · `STRAT-20261024-028`: `+3.64%` |
| **Fondeo Prop Firm (`PROP_FIRM_*`)** | **32** | 1 (`PROP-FX-EUR-001`) | 31 (`PROP-20261107-*`, `HYB-*`, etc.) | `PROP-FX-EUR-001`: A `+0.45%` / B `+0.45%` / C `+0.22%` (`2` trades cerrados reales) |
| **Consolidado Portfolio Virtual** | **55** | 5 | 50 | **Libro A:** `$54,952.58 (-0.09%)` · **Libro B:** `$55,026.44 (+0.05%)` · **Libro C:** `$55,023.64 (+0.04%)` · **15 whipsaws evitados** |

---

## 2. Catálogos y Vistas Verificadas (`HTTP 200 OK`)
* `/api/forward_state`: `23` Capital Propio + `32` Prop Firm (`0` fugas `PROP` en Capital Propio).
* `/api/regime_orchestrator`: `55` estrategias comparadas (`ab_portfolio_summary` + Libros A/B/C activos).
* `/api/strategies`: `55` · `/api/backtest_strategies`: `9` starters y `48` reserves · `/api/strategies/tri_facet`: `57` · `/api/chart_strategies`: `58`.

---

## 3. Próximo Paso en Roadmap
* Implementar cuenta demo dedicada de **$500,000 IC Markets MT5 (modo Hedging)** + aislamiento Cripto para medir *fills*, *spreads* y *slippage* reales en Libro A por cada estrategia individual (ver [`ROADMAP.md`](file:///C:/Users/Sergio/Documents/Antigravity/OpenMausBot/library/ROADMAP.md)).
