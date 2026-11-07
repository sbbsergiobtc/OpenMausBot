---
title: "LESSON-20261107-016: Erradicación del Truncamiento Fijo y Adopción del Embudo Dinámico por Umbrales Objetivos"
date: "2026-11-07"
author: "Director Supremo Sergio & Desk Lead Nexus"
status: "NORMA MANDATORIA OFICIAL"
tags:
  - quantitative-methodology
  - truncation-bias
  - dynamic-funnel
  - threshold-filtering
  - correlation-clustering
  - zero-fixed-quota
---

# Lección Magistral LESSON-20261107-016: Embudo Cuantitativo Dinámico por Umbrales Objetivos

## 1. El Error Crítico del Truncamiento Arbitrario (Top 24 / Top 12)
Históricamente, el sistema arrastró la cota fija de "24 estrategias al día" debido a la programación de los cron jobs del Enjambre LLM (3 tandas de 8 estrategias). 

Desde el punto de vista cuantitativo e institucional, **este enfoque es un grave error de diseño (*Truncation Bias*)**:
1. **Pérdida de Alpha Real:** Si en una tirada de 100.000 combinaciones existen 80 estrategias que superan todos los filtros de robustez matemática, cortar artificialmente en 24 destruye 56 fuentes de alpha legítimas.
2. **Trampa del Pico Sobreoptimizado:** Las estrategias que ocupan las primeras 24 posiciones en métricas estáticas in-sample suelen ser aquellas con mayor sobreajuste al ruido histórico (*spurious spikes*). Las que habitan en los puestos 30 a 100 suelen ser más estables y tener mesetas paramétricas mucho más resilientes.
3. **Contaminación en Días Caóticos:** Si en un régimen de alta entropía el screener solo detecta 2 estrategias verdaderamente sólidas, forzar una cuota de 24 arrastra 22 estrategias mediocres al Forward Test solo para "rellenar el número".

---

## 2. Las 5 Etapas del Embudo Dinámico

Queda abolida cualquier cuota o límite artificial. El flujo de cribado se rige exclusivamente por **umbrales de eliminación en cascada**:

```
[100.000 Combinaciones en Paralelo]
                 │
                 ▼
[ETAPA 1: Screener Vectorizado Numérico]
  • Capital Propio (US500, US100, EURUSD, BTC, ETH, SOL · 15m/1h/4h):
    MaxDD ≤ 20.0%, Profit Factor ≥ 1.30, Sharpe ≥ 1.30, Trades ≥ 30.
  • Cuentas Fondeadas (ÚNICAMENTE US500 y US100 · 5m RTH 60D Sprint):
    MaxDD ≤ 3.50%, Profit Factor ≥ 1.40, Sharpe ≥ 1.50, Trades ≥ 30.
  ──> Supervivientes N1 (Variable: ej. 200 a 600 estrategias)
                 │
                 ▼
[ETAPA 2: Deduplicación por Clustering NumPy Pearson]
  • Matriz de correlación entre curvas de equidad.
  • Eliminación de redundancias con correlación ρ > 0.80.
  • Se retiene únicamente el líder ortogonal de cada familia.
  ──> Supervivientes N2 (Variable: ej. 25 a 50 familias únicas)
                 │
                 ▼
[ETAPA 3: Pre-Auditoría Destructiva Vectorizada (0 Tokens)]
  • Deflated Sharpe Ratio (DSR de López de Prado) con N=100.000 (p-valor ≥ 0.85).
  • 1.000 simulaciones Monte Carlo Bootstrap (P95 DD ≤ Límite, Ruina ≤ 1.0%).
  ──> Supervivientes N3 (Variable: ej. 10 a 25 estrategias indestructibles)
                 │
                 ▼
[ETAPA 4: Examen Destructivo del Enjambre (@Skeptic & @RiskFilter)]
  • Latencia forzada de 1 barra en señales + estrés de 2.0x comisiones de broker.
  • Profit Factor estresado ≥ 1.15 (Cap. Propio) o ≥ 1.25 (Fondeo).
  ──> Supervivientes N4 (Variable: ej. 4 a 18 estrategias certificadas)
                 │
                 ▼
[ETAPA 5: Auto-Despliegue Inmediato en Forward Test]
  • El 100% de las supervivientes de la Etapa 4 se auto-despliegan en el Daemon
    con $1.000 USD/USDC de libro contable virtual aislado.
```

---

## 3. Mandato Permanente
De ahora en adelante, todo script, rutina y agente de AlgrokQuant procesará **a todas las candidatas que superen los umbrales de cada etapa**, sin aplicar jamás un `[:24]`, `[:12]` ni truncamiento estático de ninguna clase.
