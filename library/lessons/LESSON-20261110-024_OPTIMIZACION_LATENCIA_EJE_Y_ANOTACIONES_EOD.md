# LESSON-20261110-024: Eliminación de Lag UI, Coherencia Bifásica/Modalidad y Anotaciones Dinámicas de Eje Y

**Fecha:** 2026-11-10T22:50:00+01:00  
**Autor:** Enjambre Cuantitativo AlgrokQuant  
**Aprobado por:** Director Supremo Sergio  
**Categoría:** Arquitectura Frontend/Backend · UX Institucional · Rendimiento Tiempo Real  

---

## 1. Hallazgos Críticos de la Auditoría Full-Stack

Durante la auditoría integral del dashboard en las modalidades **Capital Propio** y **Fondeo (Evaluación / Fondeada)** se identificaron tres familias de problemas:

1. **Incoherencia contextual por ausencia de filtro de Desk (`PROP_FIRM` vs `CAPITAL_PROPIO`)**:
   - El selector bifásico (`currentBifocalLens`) conservaba su valor `'EVALUATION'` aunque el usuario conmutase al desk de **Capital Propio**. Esto provocaba que tanto el gráfico principal de equidad (`Target Reto (+8%)`, `Límite EOD (-4%)`, tooltip `Payout Retirable (80%)`), como el bloque de *Desglose de Rachas* (*Aprobaciones de Fondeo* / *Pases Challenge +8%*) y la tabla de operaciones (*Consistencia 40%* / `PASS` / `40% CLAMP`) mostrasen reglas exclusivas de Prop Firm sobre cuentas propias.
   - **Regla arquitectónica**: Toda etiqueta, umbral horizontal, cálculo de tooltip o badge ligado a reglas de reto (`40% Clamp`, `Límite EOD -4%`, `Target +8%`, `Pases Challenge`) debe depender explícitamente de `deskMode === 'PROP_FIRM'`, nunca únicamente de `currentBifocalLens`.

2. **Recorte de anotaciones horizontales en ApexCharts cuando el umbral queda fuera del rango de precios**:
   - Cuando la curva de balance de un reto de Fondeo no desciende por debajo del balance inicial (`$100,000`), el autoescalado de ApexCharts fija `yaxis.min ≈ $100,000`, recortando la línea roja de `Límite EOD (-4% / $96,000)` por debajo del área visible.
   - **Regla arquitectónica**: Al añadir `annotations.yaxis` críticas (como `Límite EOD -4%` o `Target Reto +8%`), `yaxis.min` y `yaxis.max` deben calcularse explícitamente incluyendo dichos umbrales más un margen (`~8%` del rango) para garantizar visibilidad constante.

3. **Cuellos de botella de latencia en Frontend y Backend**:
   - En `dashboard/backend.py`, llamar a `pd.to_datetime(...).tz_convert('Europe/Madrid')` por cada operación duplicaba la latencia de `/api/trade_history`. Sustituirlo por `zoneinfo.ZoneInfo('Europe/Madrid')` + parser rápido redujo `/api/trade_history?filter=ALL_PROP` de `1.034s` a `0.247s` (>4x más rápido).
   - En `dashboard/templates/index.html`, eliminar llamadas huérfanas (`fetchLiveState`), cancelar peticiones obsoletas (`AbortController`), paralelizar con `Promise.all`, desactivar animaciones pesadas de ApexCharts y pausar/segmentar el polling según la pestaña visible eliminó los bloqueos de interacción en botones.

4. **Consistencia en `POST /api/account_stage` e Iconografía**:
   - Sincronizada la actualización de `max_single_trade_profit_pct` (`40.0` vs `None`) conservando el estado vivo `'CONECTADA (MT5)'`.
   - Estandarizados los iconos de tarjetas KPI en negro (`#1D1D1F`) arriba a la izquierda y completada la limpieza a tema claro en Forward Test y curvas de rachas.
