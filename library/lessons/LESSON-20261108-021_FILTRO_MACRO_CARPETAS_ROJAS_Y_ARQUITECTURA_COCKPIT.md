# Lección Aprendida: Filtro Macro Forex Factory (Carpetas Rojas), Cierre Preventivo y Arquitectura del Cockpit
**ID:** `LESSON-20261108-021`  
**Fecha:** 2026-11-08  
**Autor:** Sergio & AlgrokQuant Fleet  
**Área:** Gestión de Riesgo Institucional, Ejecución de Órdenes & UX/UI Cockpit  

---

## 1. Contexto y Problema Detectado

Durante la operación y supervisión de las 45 estrategias en Forward Test (25 en Capital Propio y 20 en Prop Firm), se identificaron varias desviaciones críticas entre la política de riesgo cuantitativo y su reflejo visual/operativo:
1. **Falsos Positivos en Calendario Económico:** La coincidencia genérica por palabras clave (`FOMC`, `CPI`, `SPEECH`) catalogaba eventos menores de impacto bajo/medio (carpetas amarillas/naranjas en Forex Factory) como noticias de alto impacto, saturando el filtro y bloqueando operativa innecesariamente.
2. **Posiciones Abiertas Previas a Noticias:** No bastaba con rechazar órdenes nuevas durante el blackout ($\pm 5$ min); era mandatorio liquidar posiciones vivas en MT5 o DEX DEX 5 minutos antes de la publicación para evitar deslizamientos salvajes.
3. **Persistencia Multi-Dispositivo de Tablas:** El orden personalizado de columnas en tablas drag-and-drop se perdía al cambiar de dispositivo o navegador porque solo se guardaba en el `localStorage` local.
4. **Rebote de Notificaciones Leídas:** Al pulsar *"Limpiar"*, las alertas volvían a aparecer en el siguiente ciclo de polling de 30 segundos porque el servidor no guardaba el estado de vaciado.

---

## 2. Reglas Mandatorias Institucionales Implementadas

### A. Criterio de Alto Impacto Forex Factory
* **Regla:** Solo se consideran eventos de alto impacto aquellos catalogados formalmente con **Carpeta Roja** (`impact == 'High'`) y los días de **Bank Holiday** (`impact == 'Holiday'` o mención explícita a festivo bancario).
* **Filtro de Divisas Exclusivo:** Únicamente se vigilan eventos en `USD`, `EUR` y `GBP`. Divisas externas (`CNY`, `AUD`, `CAD`, etc.) quedan fuera del interceptor macro.
* **Código de Colores Estricto:** `USD` en Verde institucional, `EUR` en Rojo de alerta, `GBP` en Azul corporativo.
* **Manejo de Festivos:** Para Bank Holidays, la columna de hora se rotula como `"Festivo"` en gris y la cuenta atrás se mantiene vacía, preservando la anchura fija (`w-28 min-w-[112px]`).

### B. Liquidación Forzosa 5 Minutos Antes de la Noticia
* En el daemon de forward test ([`scripts/prop_firm_forward_test_daemon.py`](file:///root/AlgrokQuant/scripts/prop_firm_forward_test_daemon.py)), al detectar que el activo entra en la ventana de 5 minutos previos a una noticia de alto impacto de su divisa, se emite una orden de cierre inmediato a mercado (`mt5.close_position(ticket)` o cierre en DEX) y se clasifica bajo motivo `MACRO_NEWS_BLACKOUT`.

### C. Persistencia Centralizada de Preferencias
* Endpoints [`/api/table_column_preferences`](file:///root/AlgrokQuant/dashboard/backend.py) y [`/api/notifications/clear`](file:///root/AlgrokQuant/dashboard/backend.py) garantizan que las configuraciones de usuario (orden de columnas arrastradas y bandeja de notificaciones limpias) se persistan en el servidor y sincronicen entre cualquier dispositivo.

### D. Jerarquía Visual Cockpit (Apple/Linear)
* Todos los iconos de los KPIs se unifican en color negro puro (`#1D1D1F`) sobre contenedor neutro suave (`#F2F2F7`).
* Botones de control operativo alineados estrictamente a la derecha en dos filas independientes (`Cuentas & Fases` y `PAUSA PREVENTIVA`).

---

## 3. Estado Operativo para la Siguiente Sesión
* **Filtro Macro:** 7 eventos reales catalogados para la semana actual (Core CPI, CPI, French Bank Holiday, US Bank Holiday, UK GDP, Core PPI, PPI). Lunes 09/11 libre de bloqueos.
* **Servicios Activos:** `algrokquant-dashboard`, `algrokquant-forward-test`, `algrokquant-mt5` y `openmausbot` monitorizados 24/7 en systemd.
