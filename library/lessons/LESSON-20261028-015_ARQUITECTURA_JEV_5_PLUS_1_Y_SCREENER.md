---
title: "LESSON-20261028-015: Arquitectura JEV 5+1, Screener Masivo y Separación de Linaje Cuantitativo"
date: "2026-10-28"
author: "Desk Lead Nexus & Auditor Cuantitativo"
status: "APROBADA Y DESPLEGADA EN PRODUCCIÓN"
tags:
  - jev-architecture
  - 5-plus-1-screener
  - shannon-entropy
  - parameter-plateau
  - correlation-clustering
  - context-compression
  - circuit-breaker
---

# Lección Magistral LESSON-20261028-015: Arquitectura JEV 5+1 y Screener Cuantitativo

## 1. Principio Rector
> **"La IA (Gemini Pro) decide a nivel de hipótesis y análisis cualitativo profundo; el Código (JEV Screener / VectorBT) controla y calcula de forma 100% determinista."**

Para evitar el sesgo de minería de datos (*Data Mining Bias / P-Hacking*) y proteger la cuota de tokens del plan Gemini Pro, ninguna estrategia se busca a ciegas ni se leen miles de velas crudas en el LLM.

---

## 2. Las Capas del Sistema (5+1)

1. **Capa 1: Filtro Pre-LLM de Entropía de Shannon ($H_{norm}$)**
   - Si $H_{norm} > 0.84$ (caos/ruido blanco browniano) o $\Delta H_{14} > 0.12$ (shock/transición), el sistema descarta la generación en ese activo.
   - **Gasto de tokens:** **0 tokens**. Se calcula en NumPy en microsegundos.

2. **Capa 2: Exploración Paramétrica Vectorizada (VectorBT Grid)**
   - Explora miles de combinaciones en arrays NumPy en segundos sobre datos Parquet de 10 años.
   - Exige **meseta paramétrica (*Parameter Plateau*)**: los parámetros vecinos no deben colapsar.

3. **Capa 3: Clustering de Correlación Local (NumPy Pearson)**
   - Calcula la matriz de correlación entre las curvas de equidad candidatas.
   - Descarta estrategias redundantes con correlación $> 0.80$, reteniendo únicamente la de mayor Calmar Ratio.

4. **Capa 4: Validación Determinista de Riesgo (Risk Engine)**
   - Techo inviolable de Drawdown: $\le 20.0\%$ en Capital Propio y $\le 3.50\%$ en Prop Firm.
   - Sizing obligatorio: 100% Porcentual Dinámico ($0.50\% - 1.50\%$ de equity vivo). Prohibidos importes fijos en dólares.
   - Estadísticos mínimos: $\ge 30$ trades y Profit Factor $\ge 1.30$.

5. **Capa 5: Compresión de Contexto a ~60 Tokens (Token Minimizer)**
   - Genera una radiografía matemática compacta para Gemini Pro en lugar de cientos de velas:
     `{"asset": "NDX", "price": 29650, "regime": "PERSISTENT", "H_norm": 0.54, "delta_H": 0.02, "ema_stack": "BULLISH", "atr_pct": 1.2}`.
   - Reduce el consumo de tokens en un **97.6%**.

6. **Capa +1: Circuit Breaker de Régimen en Vivo (Paridad 1:1)**
   - Ejecutado en cada barra $t-1$ tanto en el backtest histórico como en el forward test daemon.
   - Pausa aperturas si el mercado entra en caos o shock de volatilidad.

---

## 3. Separación de Linaje Cuantitativo (*Strategy Provenance*)

Toda estrategia catalogada en `/library/strategies/` y `/strategies/prop_firm/` queda categorizada en el Dashboard y la API:
* `source_type: "ROSTER_AGENT"`: Estrategias heurísticas estructuradas por los agentes del Roster (*Nexus, CoderQuant*) basadas en microestructura o literatura académica.
* `source_type: "HYBRID_VECTORBT"`: Estrategias originadas a partir de una tesis económica de *Ideator* y exploradas en meseta paramétrica masiva por VectorBT.

---

## 4. Métricas de Utilidad Real Incorporadas

* **OOS R/DD Ratio & Degradación:** $\frac{(R/DD)_{OOS} - (R/DD)_{IS}}{(R/DD)_{IS}} \times 100$. Rechazo inmediato si la degradación supera el 40%.
* **Días de Estancamiento (*Stagnation Days*):** Máximo de días naturales consecutivos que la estrategia permanece por debajo de su pico anterior.
* **Desglose de Rachas por Activo:** Estadísticos de rachas ganadoras/perdedoras y consistencia por símbolo individual.
