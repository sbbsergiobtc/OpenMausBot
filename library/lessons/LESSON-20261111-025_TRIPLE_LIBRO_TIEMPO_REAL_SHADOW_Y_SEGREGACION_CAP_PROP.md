---
id: LESSON-20261111-025
title: "Triple Libro A/B/C en Tiempo Real, Shadow $1K, Colisión de Subcadena PROP/PROPIO y Nitidez FLIP"
date: "2026-11-11"
category: "architecture-governance"
severity: "CRITICAL"
tags:
  - regime-orchestrator
  - triple-book
  - q-learning
  - dashboard-ui
  - shadow-forward-test
---

# Lección 025 · Pipeline Triple Libro en Tiempo Real, Tracking Shadow $1K y Blindaje UI

## 1. Colisión Semántica `'CAPITAL_PROPIO'` vs `'PROP'`
* **Hallazgo:** En [`formatDeskBadgeHtml`](file:///C:/Users/Sergio/Documents/Antigravity/OpenMausBot/dashboard/templates/index.html#L7395) y en los filtros de backend, comprobaciones como `'PROP' in desk_mode` o `dm.includes('PROP')` devolvían `True` sobre **`CAPITAL_PROPIO`** porque la palabra `PROPIO` contiene `PROP`. Además, `auto_deployer.py` comparaba `mode == "PROP_FIRM"`, enviando estrategias `PROP_FIRM_FUTURES` y `PROP_FIRM_CFD` al bloque `capital_propio`.
* **Regla Permanente:** Toda clasificación por mesa debe comprobar primero el prefijo de ID (`CAP-`, `CRYPTO-`, `STRAT-` -> `CAPITAL_PROPIO`; `PROP-`, `HYB-` -> `PROP_FIRM`) y en modo de mesa exigir `'PROP_FIRM' in dm` o `dm.startswith('PROP')`, nunca la subcadena suelta `'PROP'`.

## 2. Desconexión de Claves (`strategies_ab` vs. `strategies_ab_comparison`) y Libros Sintéticos
* **Hallazgo:** [`regime_orchestrator.py`](file:///C:/Users/Sergio/Documents/Antigravity/OpenMausBot/jev/regime_orchestrator.py) publicaba `strategies_ab` con fórmulas sintéticas fijas (`base_edge_pct = 2.45 + ...`), mientras que Cockpit, Forward Test y Orquestador leían `strategies_ab_comparison`, provocando valores congelados en `+0.00%` / `$1000.00`.
* **Solución Implementada:** Se eliminaron las fórmulas sintéticas. Ahora `run_parallel_orchestrator_evaluation()` evalúa velas reales actualizadas (`^GSPC`, `^NDX`, `EURUSD=X`, Binance `BTC`/`ETH`/`SOL`) + ejecuciones MT5/Hyperliquid en paralelo sobre **Libro A (Individual)**, **Libro B (Orquestado)** y **Libro C (Double Q-Learning RL)**, sincronizando todas las vistas (`/api/forward_state`, `/api/regime_orchestrator`, `/api/strategies`, `/api/backtest_strategies`, `/api/strategies/tri_facet`, `/api/chart_strategies`).

## 3. Visibilidad Total de Suplentes (`SHADOW $1K`) vs. Riesgo Titular Acotado
* **Problema Detectado por Dirección (Sergio):** Solo las estrategias Titulares envían órdenes al bróker para no superar el límite de riesgo de cuenta, lo que impedía ver el rendimiento real vivo de las estrategias Suplentes y nuevas aprobadas por el Screener 100k.
* **Arquitectura Adoptada:** Todas las estrategias aprobadas (`55` totales: `23` Capital Propio + `32` Fondeo) corren en seguimiento paralelo en tiempo real con libros virtuales aislados de `$1,000` (`TITULAR VIVO` en bróker vs. `SHADOW $1K` barra a barra), preparando la pasarela de la próxima sesión hacia una cuenta demo dedicada de **$500,000 IC Markets MT5 (Hedging)** para medir *slippage* y *spread* físico en Libro A.

## 4. Nitidez GPU al Redimensionar Tarjetas (`will-change` + `Motion.scale`)
* **Hallazgo:** Combinar `will-change: transform;` permanente en `.algrok-kpi-card` con `Motion.animate(..., { scale: ... })` y `playFlipShift` cuando una tarjeta cambiaba de 2 columnas a 1 columna (`algrok-grid-stacked`) forzaba a Chromium a reescalar una textura GPU rasterizada en lugar de volver a dibujar texto nítido 1:1.
* **Solución:** Retirar `will-change: transform;` permanente, omitir `FLIP`/`scale` cuando varía el ancho de columna, limpiar `transform` / `--motion-scale` al soltar y compactar badges internos en `forward-card*-kpis`.
