# LESSON-20261108-020: Lente Cuantitativa Bifásica Reactiva y Blackout Macro de 5 Minutos

**Fecha:** 2026-11-08  
**Autor:** Antigravity Pairing Assistant & Sergio  
**Área:** Arquitectura Cuantitativa, Frontend Reactivo, Gobernanza de Riesgo y Prop Firms  
**Estado:** IMPLEMENTADO, VERIFICADO Y DESPLEGADO EN PRODUCCIÓN  

---

## 1. Contexto y Problema Detectado

Durante la auditoría visual y cuantitativa en el Dashboard de AlgrokQuant, se detectaron dos necesidades operativas y de visualización críticas:
1. **Blackout de Noticias de Alto Impacto:** Se requería formalizar la directiva operativa estricta de **no abrir operaciones ni mantener exposición activa 5 minutos antes y 5 minutos después** de noticias macroeconómicas de nivel 1 (FOMC, CPI, NFP, PPI, Decisión de Tipos).
2. **Inercia Visual en la Lente Bifásica de Backtests:** Al alternar entre el botón de *Lente Evaluación* y *Lente Fondeada*, los números y gráficos permanecían idénticos. Esto ocurría porque:
   - En el backend, las carteras cuantitativas no tenían trades individuales que excedieran el 40% del profit acumulado total, por lo que el clamp bruto no alteraba la serie matemática si no se aplicaba una parametrización específica de fase.
   - En el frontend, el gráfico de equidad mantenía anotaciones estáticas fijas (+6%) y la función de cambio de lente no sincronizaba los endpoints de analítica e historial ni actualizaba las tarjetas de KPI subordinadas.

---

## 2. Solución Arquitectónica Implementada

### A. Gobernanza de Riesgo: Ventana de Blackout ±5 Minutos
En `config/risk_rules.yaml`:
```yaml
news_filter:
  enabled: true
  blackout_window_minutes_before: 5
  blackout_window_minutes_after: 5
  high_impact_events:
    - "FOMC"
    - "CPI"
    - "NFP"
    - "PPI"
    - "INTEREST_RATE_DECISION"
```
Aplica tanto para el libro de cuentas de evaluación/fondeo como para capital propio.

### B. Desacoplamiento Cuantitativo Bifásico Full-Stack
Se dividió matemáticamente y visualmente el comportamiento de ambas perspectivas:

| Componente | Lente Evaluación (Prop Firm Challenge) | Lente Fondeada & Capital Propio |
| :--- | :--- | :--- |
| **Objetivo Principal** | Superar el Reto de Fase (+8.0% / $8,000 en 100k) | Cosecha de Alpha Libre y Retiros Periódicos |
| **Drawdown Límite** | Límite EOD Trailing DD -4.0% ($96,000) | Drawdown Real Libre (sin riesgo de rescisión de cuenta) |
| **Gráfico Equity** | Verde Esmeralda (`#10b981`) con líneas de Target (+8%) y EOD DD (-4%) | Índigo (`#6366f1`) con Buffer Capital Base ($100k) e Hitos de Retiro ($110k) |
| **Rachas (Picos y Valles)** | Target de tramo al 8.0%. Chips: `🏆 +8% RETO PASSED` / `🛡️ DD EOD SEGURO` | Target de tramo al 5.0%. Chips: `💎 CICLO PAYOUT` / `🛡️ BUFFER PRESERVADO` |
| **KPIs HUD** | Pass Rate Monte Carlo (78-98%), Trades Clampeados, Reto Superado | Expectativa Retiro Mensual ($), Split 80% Trader ($), Buffer Libre |
| **Historial Trades** | Columna con badges `PASS OK (<40%)` o `40% CLAMP` | Columna con badges `80% PAYOUT: +$XXX` retirable |

### C. Transición Fluida
Se integró el barrido de animación Framer Motion (`triggerMotionSweep`) al alternar entre pestañas, garantizando que el usuario perciba de inmediato el refresco y la transición reactiva de los datos.

---

## 3. Regla Nemotécnica para Sesiones Futuras
> *En sistemas cuantitativos para Prop Firms, la curva de balance no es solo una serie de precios: es una función condicionada por el marco de evaluación. Nunca evalúes una racha de examen con las mismas métricas con las que mides la cosecha de retiros.*
