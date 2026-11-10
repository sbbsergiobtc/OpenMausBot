---
title: "Registro de Forward Test e Incubación Automatizada - AlgrokQuant"
date: "2026-11-10"
status: "VIGILANCIA 24/7 ACTIVA"
daemon: "algrokquant-forward-test.service"
prop_firm_strategies: 20
capital_propio_strategies: 28
total_active_strategies: 48
prop_traffic_lights:
  green: 20
  amber: 0
  red: 0
graduated_count: 0
---

# Registro de Forward Test e Incubación en Tiempo Real (Snapshot 2026-11-10)

## 1. Estado General de la Flota en Tiempo Real
El daemon `algrokquant-forward-test.service` y el entorno de ejecución multiactivo mantienen la supervisión continua sobre **48 estrategias activas**:

| Desk / Entorno | Cuenta(s) Activa(s) | Balance Vivo | Estrategias Activas | Semáforo Guardián | Graduadas |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Fondeo Prop Firm** | `53138341` (CFDs \$50k) + `53138343` (Futuros \$50k) | **$100,000.00 USD** | 20 | 20 GREEN · 0 AMBER · 0 RED | 0 |
| **Capital Propio (TradFi)** | MT5 Demo Retail (`53138338`) | **$1,000.00 USD** | *(incl. en Capital Propio)* | Activo | 0 |
| **Capital Propio (Crypto)** | Hyperliquid Testnet (`STRAT-20261024-028`) | **$1,036.42 USDC** | **+$36.42 USDC** (14 trades) | Activo | 0 |
| **Total Capital Propio** | TradFi + Hyperliquid Testnet | **$2,036.42 USD** | 28 | Operativa continua | 0 |

* **Trades cerrados registrados en Prop Firm Forward Test:** 2 (`PROP-FX-EUR-001` sobre `EURUSD`).
* **Guardia EOD Prop Firm:** Peak EOD Equity `$100,004.47`, drawdown EOD actual `0.0%`.

---

## 2. Servicios `systemd` Verificados
* `algrokquant-forward-test.service`: **active** (desde `2026-11-10 06:12:00 CET`).
* `algrokquant-dashboard.service`: **active** (reiniciado tras despliegue final a las `22:33:05 CET`, HTTP 200 en `:8080`).
* `openmausbot.service`: **active**.
* `algrokquant-mt5.service`: **active**.

---

## 3. Referencias Relacionadas
* [`LESSON-20261110-024_OPTIMIZACION_LATENCIA_EJE_Y_ANOTACIONES_EOD.md`](file:///C:/Users/Sergio/Documents/Antigravity/OpenMausBot/library/lessons/LESSON-20261110-024_OPTIMIZACION_LATENCIA_EJE_Y_ANOTACIONES_EOD.md)
* [`FORWARD_TEST_SNAPSHOT_20261108.md`](file:///C:/Users/Sergio/Documents/Antigravity/OpenMausBot/library/forward_test_records/FORWARD_TEST_SNAPSHOT_20261108.md)
