---
title: "LESSON-20261108-019: Orquestador Double Q-Learning Tabular, 10 Regímenes Canónicos y Clamp de Consistencia del 40%"
date: "2026-11-08"
author: "Director Supremo Sergio & Desk Lead Nexus"
status: "NORMA MANDATORIA OFICIAL"
tags:
  - reinforcement-learning
  - double-q-learning
  - 10-market-regimes
  - prop-firm-consistency
  - incubation-guardian
  - polyak-soft-update
  - monte-carlo-cone
---

# Lección Magistral LESSON-20261108-019: Orquestación Double Q-Learning y Clamp de Consistencia del 40%

## 1. Contexto y Conflicto Cuantitativo Resuelto
El escalado de carteras cuantitativas enfrenta una contradicción fundamental entre dos paradigmas:
1. **Capital Propio Multi-Año:** Maximizar la tasa compuesta anual de retorno ($\text{CAGR} \ge 30\%$) tolerando drawdowns de hasta $20\%$ con horizonte ilimitado.
2. **Cuentas Fondeadas (Prop Firms):** Regla implacable de **Drawdown EOD diario estricto ($\le 3\% - 8\%$)** y **Regla de Consistencia del 40%** (ningún trade individual puede aportar más del 40% del profit total acumulado al superar el reto).

### La Solución: Dos Políticas de Decisión Separadas
Queda prohibido utilizar una función de recompensa unificada. El orquestador implementa **dos matrices $Q$ independientes**:
* `Q_prop_firm`: Penaliza asimétricamente el Drawdown EOD diario y premia el ratio Calmar a corto plazo.
* `Q_capital_propio`: Maximiza el Sharpe multianual, la captura de tendencia y el retorno compuesto.

---

## 2. Los 10 Regímenes Canónicos de Mercado ($S_0 \dots S_9$)

Compilados en Numba JIT en [`jev/symbolic_engine.py`](file:///C:/Users/Sergio/Documents/Antigravity/OpenMausBot/jev/symbolic_engine.py) y evaluados causalmente al cierre de vela:

| ID | Código de Régimen | Condición Cuantitativa Causal | Arquetipo Favorecido | Lote Base |
| :---: | :--- | :--- | :--- | :---: |
| **$S_0$** | `STRONG_CLEAN_BULL` | $\text{ADX} \ge 25, +DI > -DI, C \ge \text{EMA}_{50} > \text{EMA}_{200}, H_{norm} \le 0.78$ | Trend Following | $1.25x$ |
| **$S_1$** | `STRONG_CLEAN_BEAR` | $\text{ADX} \ge 25, -DI > +DI, C \le \text{EMA}_{50} < \text{EMA}_{200}, H_{norm} \le 0.78$ | Trend Following | $1.25x$ |
| **$S_2$** | `PARABOLIC_EXHAUSTION_BULL` | $C > \text{EMA}_{50} + 2.5\sigma, \text{RSI}_{14} \ge 75, \text{Kurt}_{rob} \ge 3.5$ | Mean Reversion | $0.50x$ |
| **$S_3$** | `PARABOLIC_EXHAUSTION_BEAR` | $C < \text{EMA}_{50} - 2.5\sigma, \text{RSI}_{14} \le 25, \text{Kurt}_{rob} \ge 3.5$ | Mean Reversion | $0.50x$ |
| **$S_4$** | `RANGE_SQUEEZE_COMPRESSION` | $\text{BBW} \le P_{20}(\text{BBW}_{100}), \text{ADX} < 18, \text{KER}_{14} < 0.25$ | Volatility Breakout (Armado) | $0.75x$ |
| **$S_5$** | `CHOPPY_MEAN_REVERSION` | $18 \le \text{ADX} < 25, H_{norm} > 0.85, 0.40 \le H \le 0.55$ | Mean Reversion puro | $1.00x$ |
| **$S_6$** | `HIGH_VOL_TREND_BULL` | $\text{ADX} \ge 25, \text{ATR}_{14} > P_{80}(\text{ATR}), +DI > -DI$ | Trend Following (Defensivo) | $0.75x$ |
| **$S_7$** | `HIGH_VOL_TREND_BEAR` | $\text{ADX} \ge 25, \text{ATR}_{14} > P_{80}(\text{ATR}), -DI > +DI$ | Trend Following (Defensivo) | $0.75x$ |
| **$S_8$** | `HIGH_VOL_WHIPSAW_CHAOS` | $\text{ATR}_{14} > P_{90}, H_{norm} > 0.92, \text{KER}_{14} < 0.15$ | **PAUSA TOTAL (Cero Trades)** | $0.00x$ |
| **$S_9$** | `DRIFT_LOW_VOL_TRANSITION` | $\text{ADX} < 15, \text{ATR}_{14} < P_{20}, \text{KER}_{14} \approx 0.30$ | Observación / Lote Mínimo | $0.50x$ |

---

## 3. Double Q-Learning Tabular Auditable ($Q_A, Q_B$)
Para erradicar el sesgo de sobrestimación (*Maximization Bias*) típico de Q-Learning clásico, se emplean dos estimadores desacoplados:
$$Q_A(s, a) \leftarrow Q_A(s, a) + \alpha \left[ R + \gamma Q_B(s', \arg\max_{a'} Q_A(s', a')) - Q_A(s, a) \right]$$

### Espacio de Estados y Acciones
* **Estados ($60$ discretos):** $10 \text{ Regímenes} \times 3 \text{ Arquetipos} \times 2 \text{ Estados Guardián (GREEN / AMBER)}$.
* **Acciones ($5$ discretas):** $\mathcal{A} = \{0.00x, 0.50x, 0.75x, 1.00x, 1.25x\}$.

---

## 4. Hard 40% Consistency Take-Profit Clamp
En retos de fondeo, si el agente asigna $1.25x$ (apuesta agresiva en régimen ideal $S_0$ o $S_1$), existe el riesgo de que una operación ganadora descomunal genere más del $40\%$ del target total de la cuenta, invalidando la evaluación de la firma.

### Algoritmo de Corte Previo
$$\text{MaxAllowedProfitPerTrade} = 0.40 \times \text{ProfitTarget}_{\text{PropFirm}}$$
$$\Delta P_{\text{clamp}} = \frac{\text{MaxAllowedProfitPerTrade}}{\text{Lots} \times \text{TickValue}}$$
$$\text{TakeProfit}_{\text{efectivo}} = \min\left(\text{TakeProfit}_{\text{técnico}}, \text{EntryPrice} + \Delta P_{\text{clamp}}\right)$$
*En el benchmark OOS sobre 440 eventos, este mecanismo intervino exitosamente en **25 operaciones**, salvando las cuentas de ser descalificadas por exceso de concentración de beneficios.*

---

## 5. El Guardián de Incubación Monte Carlo
Antes de que una estrategia pase a producción real con capital:
1. **Periodo de Incubación Paper:** Mínimo 30 operaciones reales ejecutadas por el daemon.
2. **Cono de Fidelidad Monte Carlo ($P_{05}\text{--}P_{95}$):** La curva de equidad en forward test debe mantenerse estrictamente dentro de la envolvente simulada en backtest.
3. **Guardián Z-Score ($|Z| \le 1.5\sigma$):** Desviaciones mayores a $1.5\sigma$ degradan la estrategia a semáforo **AMBER** ($0.5x$ lote). Desviaciones mayores a $2.0\sigma$ degradan a **RED** (Pausa $0.0x$).
4. **Graduación:** Únicamente estrategias con $\ge 30$ trades, semáforo GREEN continuado y DSR significativo reciben el estado `GRADUATED_FOR_REAL_ACCOUNT`.

---

## 6. Política de Re-entrenamiento y Amortiguación
* **Doble Memoria (80/20):** $80\%$ peso a la base multianual estructural y $20\%$ a la ventana reciente (60D) + trades vivos del daemon.
* **Actualización Suave Polyak ($\tau = 0.25$):** $Q \leftarrow \tau Q_{\text{nuevo}} + (1-\tau) Q_{\text{antiguo}}$, garantizando que el orquestador nunca oscile drásticamente por una mala racha transitoria.
* **Frecuencia:** Crontab semanal los Domingos a las 22:00 UTC, más **Gatillo por Deriva (Drift Trigger)** si el Sharpe OOS rodante diverge $> 1.5\sigma$.
