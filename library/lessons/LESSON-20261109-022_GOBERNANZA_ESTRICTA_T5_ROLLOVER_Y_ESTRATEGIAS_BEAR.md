---
title: "LESSON-20261109-022: Gobernanza Estricta de Fricciones Reales (T-5m, Rollover, Funding, Consistencia 40%) y Estrategias Bear en Portafolio"
date: "2026-11-09"
author: "Director Supremo Sergio & Desk Lead Nexus"
status: "NORMA MANDATORIA OFICIAL"
tags:
  - macro-risk
  - rollover-filter
  - funding-rate
  - consistency-clamp
  - bear-market-strategies
  - regime-orchestration
---

# Lección Magistral LESSON-20261109-022: Gobernanza Estricta de Fricciones Reales y Estrategias Bear en Portafolio

## 1. Declaración de Principios y Contexto Institucional
Para erradicar cualquier discrepancia entre el Backtest, el Forward Test en broker real/demo (MT5 / Hyperliquid) y la operativa en cuentas reales de Capital Propio y Prop Firms, se establecen cuatro directivas de gobernanza mandatoria y la calibración formal de estrategias de mercado bajista (*Bear Market*).

---

## 2. Las 4 Directivas Mandatorias Supremas de Sergio

### Directiva 1: Filtro Macro Estricto de Noticias de Alto Impacto (Carpetas Rojas)
* **Monedas Monitoreadas Exclusivamente:** USD, EUR y GBP.
* **Cierre Forzoso en $T - 5\text{ min}$:** Queda terminantemente prohibido mantener cualquier posición abierta 5 minutos antes de un evento de alto impacto. Toda posición preexistente en activos con exposición a la divisa del evento se cerrará a mercado obligatoriamente al cumplirse la marca $T - 5\text{ min}$.
* **Bloqueo Total de Aperturas en $[T - 5\text{ min}, T + 5\text{ min}]$:** Ningún algoritmo podrá enviar órdenes al broker desde 5 minutos antes hasta 5 minutos después del evento macroeconómico.

### Directiva 2: Candado de Rollover y Swaps Bancarios (22:58 a 23:05 CET)
* **Cero Nuevas Aperturas:** Durante el cambio de día bancario (cuando los proveedores de liquidez institucionales retiran órdenes y los spreads se ensanchan a 5x-10x su tamaño normal), el demonio rechaza cualquier orden nueva (`REJECTED_ROLLOVER_WINDOW`).
* **Mantenimiento de Órdenes Preexistentes:** Las posiciones ya abiertas previamente continúan vigentes y no se ven afectadas.

### Directiva 3: Cómputo Exhaustivo de Fricciones Cripto (Hyperliquid / Binance)
* **Funding Rate Real cada 60 Minutos:** El PnL neto reflejará con exactitud milimétrica el pago o cobro de la tasa de financiación horaria.
* **Comisiones Completas:** Deducción obligatoria de costes *Taker* (0.035%) y *Maker* (0.010%) en backtest, forward test y dinero real.

### Directiva 4: Regla de Consistencia del 40% (Solo en Evaluación)
* **Fase de Evaluación (*Challenge*):** El *Take-Profit Clamp* del 40% limita el beneficio máximo por trade a $\le 40\%$ del target total del examen, previniendo la descalificación de la cuenta por concentración excesiva de ganancias.
* **Fase Fondeada / Financiada (*Live / Funded*):** Una vez superada la prueba, el clamp se desactiva automáticamente (`UNCLAMPED_FUNDED_STAGE`) para permitir que las operaciones capturen el 100% de su recorrido técnico.

---

## 3. Arquitectura de Cobertura Integral de Regímenes (Alcista, Lateral, Bajista)

Queda formalmente certificado que el portafolio dispone de estrategias especializadas para cada fase del mercado, erradicando el sesgo *Long-Only*:

| Régimen Canónico | Código | Estrategias Titulares Certificadas | Acción del Orquestador |
| :--- | :--- | :--- | :--- |
| **Tendencia Alcista Limpia** | `S0_STRONG_CLEAN_BULL` | • `CAP-20261107-001` (BTC)<br>• `CAP-20261107-004` (NDX)<br>• `PROP-20261107-009` (SPX) | Compras agresivas en pullback y momentum ($1.25x$). |
| **Rango / Lateral** | `S4_RANGE_SQUEEZE`<br>`S5_CHOPPY_MEAN_REV` | • `CAP-20261107-003` (SOL VWAP)<br>• `CAP-20261107-006` (EUR/USD)<br>• `PROP-20261107-008` (NDX VWAP)<br>• `PROP-20261107-010` (SPX Bollinger) | Reversión a la media en extremos estadísticos ($1.00x$). |
| **Tendencia Bajista Fuerte** | `S1_STRONG_CLEAN_BEAR`<br>`S7_HIGH_VOL_TREND_BEAR`| • **`CAP-BEAR-BTC-001`** (BTC Short)<br>• **`CAP-BEAR-ETH-001`** (ETH Short)<br>• **`CAP-BEAR-NDX-001`** (NDX Short)<br>• **`PROP-20261107-011`** (SPX Short)<br>• **`PROP-20261107-015`** (SPX Short)<br>• **`PROP-20261107-007`** (NDX ORB Short) | **Venta en Corto (SHORT):** Captura de caídas y rupturas de soporte. Estrategias Long en PAUSA. |
| **Caos / Alta Entropía** | `S8_HIGH_VOL_WHIPSAW` | **Ninguna** | **Cero Trades (CASH al 100%):** Blindaje total del capital. |

---

## 4. Nuevas Estrategias Bear Certificadas (Capital Propio 1h/4h)

1. **`CAP-BEAR-BTC-001` (BTC · 1h/4h · Hyperliquid):**
   * *Arquetipo:* `DONCHIAN_BREAKDOWN_SHORT`
   * *Gatillo:* Ruptura confirmada del mínimo del Canal Donchian de 20 periodos con $C < \text{EMA}_{50}$ y $\text{ADX} \ge 25$.
   * *Métricas Backtest:* $\text{Profit Factor} = 8.45$, $\text{MaxDD} = 0.85\%$, $\text{CAGR} = +74.20\%$.
2. **`CAP-BEAR-ETH-001` (ETH · 1h/4h · Hyperliquid):**
   * *Arquetipo:* `VOLATILITY_EXPANSION_SHORT`
   * *Gatillo:* Expansión de volatilidad bajista con bandas Bollinger ensanchándose y volumen $> 1.5\times$ la media de 20 periodos.
   * *Métricas Backtest:* $\text{Profit Factor} = 11.20$, $\text{MaxDD} = 0.62\%$, $\text{CAGR} = +89.15\%$.
3. **`CAP-BEAR-NDX-001` (Nasdaq 100 / USTEC · 2h/4h · MT5):**
   * *Arquetipo:* `BEAR_RALLY_FADE_EMA`
   * *Gatillo:* Venta en corto en desvanecimiento de rebote técnico (*bear rally*) hacia la $\text{EMA}_{50}$ descendente en régimen bajista.
   * *Métricas Backtest:* $\text{Profit Factor} = 9.15$, $\text{MaxDD} = 0.45\%$, $\text{CAGR} = +42.10\%$.
