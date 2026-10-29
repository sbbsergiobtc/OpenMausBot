# Bitácora Oficial de Sesión · 2026-10-29

**Fecha:** 29 de Octubre de 2026  
**Responsables:** Sergio & Nexus (Desk Lead Cuantitativo)  
**Ecosistema:** AlgrokQuant Fleet & OpenMausBot  
**Entorno VPS:** Ubuntu 24.04 LTS (`169.58.230.132`)  
**Estado General:** OPERATIVO · SERVICIOS ACTIVOS · SINCRONIZACIÓN CERTIFICADA  

---

## 1. Hitos Operativos y Decisiones de Gobernanza

### A. Separación Estricta de Ecosistemas de Ejecución
* **Activos TradFi (Índices y Forex):**
  * `US500` (S&P 500) y `USTEC` (Nasdaq 100) en cuenta de **Capital Propio**.
  * `EURUSD` en cuenta de **Fondeo**.
  * Ejecución exclusiva en **IC Markets MT5** (cuenta demo demo institucional `53120791`, servidor `ICMarketsSC-Demo`).
* **Activos Cripto:**
  * `BTC/USDT`, `ETH/USDT`, `SOL/USDT`.
  * Ejecución y backtesting **únicamente** en proveedores cripto: **Hyperliquid L1 DEX / Binance** (NUNCA en broker tradicional/MT5 ni CFDs).

### B. Gestión Monetaria e Interés Compuesto
* Superación del modelo de lotaje fijo: cada operación en cuenta de capital propio calcula su tamaño de posición en **porcentaje de riesgo por trade (1.50% en índices, 1.00% en EURUSD)** sobre el balance flotante actualizado para aprovechar el interés compuesto dinámico.

### C. Gobernanza Cuantitativa Trifacética (LESSON-018)
* Todo modelo cuantitativo se valida en 3 capas obligatorias:
  1. **Capa 1 (Teórico Python):** VectorBT / Numba sobre datos Parquet.
  2. **Capa 2 (Simulado Broker):** Microestructura de IC Markets (spreads reales, lotes mínimos y comisiones).
  3. **Capa 3 (Real en Vivo):** Forward test en directo con ejecución de mercado.

---

## 2. Correcciones de Sistema y Frontend

### A. Diagnóstico y Resolución del Bloqueo del Menú Lateral
* **Problema:** Al hacer clic en cualquier pestaña del menú lateral (Contraste Tri-Faceta, Forward Tests, Backtests, etc.), la interfaz no cambiaba de pantalla y quedaba congelada.
* **Causa Raíz:** Se detectó una doble declaración de variable en el script de cliente:
  ```javascript
  let allTriFacetData = {}; // Declarado en línea 3102 y repetido en línea 3842
  ```
  Esto generaba un `Uncaught SyntaxError: Identifier 'allTriFacetData' has already been declared`, abortando el motor de JavaScript y evitando que la función `switchTab()` fuera registrada.
* **Solución:** Se depuró y unificó la lógica del script. Se validaron todos los bloques de script con `node --check` obteniendo un resultado de cero errores sintácticos.

### B. Eliminación de Badges en el Menú Lateral
* A petición expresa del usuario, se eliminaron todos los badges flotantes (`sidebar-badge`) de los botones del menú lateral (`1.1k Tr`, `En Vivo`, `3 Capas`, `Nexus`, `PRO`).
* El menú lateral presenta ahora una estética limpia, homogénea y minimalista.

### C. Verificación de Integridad de Backtests
* Se certificó que no se eliminó ningún backtest. El repositorio de operaciones históricas ([`full_trade_history.json`](file:///root/AlgrokQuant/data/paper_trades/full_trade_history.json)) mantiene sus **1.127 trades** intactos:
  * **Net Profit:** `+$22,453.47 USD`
  * **Win Rate:** `67.7%`
  * **Profit Factor:** `2.11`
  * **Sharpe Ratio:** `8.85`
  * **Max Drawdown:** `1.6%`

---

## 3. Telemetría y Estado de Cuentas Sincronizadas

| Cuenta / Broker | Entorno | Balance Vivo | Equity | Estado |
| :--- | :---: | :---: | :---: | :---: |
| **IC Markets MT5 (`53120791`)** | TradFi (Índices & FX) | **$999.51 USD** | **$999.51 USD** | Activo (Wine/Headless) |
| **Hyperliquid L1 DEX** | Cripto (Perpetuos) | **1,000.66 USDC** | **1,000.66 USDC** | Activo (API WebSocket) |
| **Consolidado Forward Test** | **Total Cartera** | **$2,000.17 USD** | **$2,000.17 USD** | Sincronizado en tiempo real |

---

## 4. Estado de los Servicios en el VPS (`169.58.230.132`)

* **`algrokquant-dashboard.service`**: `active (running)` — Puerto 8080 (HTTP 200).
* **`algrokquant-forward-test.service`**: `active (running)` — Demonio autónomo de evaluación horaria.
* **`algrokquant-mt5.service`**: `active (running)` — Bridge de MetaTrader 5 en Wine con conexión en vivo al servidor `ICMarketsSC-Demo`.

---

## 5. Perfeccionamiento de UI y Encabezado de Cuentas Activas

### A. Condicionalidad del Encabezado de Cartera Activa
* El encabezado superior con el grid de tarjetas de cuentas/estrategias activas (`#active-portfolio-section`: CAP-SPX-006, CAP-NDX-005, CRYPTO-BTC-001, PROP-FX-EUR-001, etc.) aparecía de forma persistente en todas las pestañas de la plataforma.
* Se configuró para que **únicamente se muestre en `Cockpit General` (`dashboard`) y en `Forward Tests (En Vivo)` (`forward`)**.
* En cualquier otra pestaña (Backtests, Contraste Tri-Faceta, Enjambre, VectorBT Lab, TradingView, Catálogo, Reglas de Riesgo, Bitácora), se oculta automáticamente de forma limpia sin solapamientos.

### B. Corrección y Acabado de Tarjetas de Forward Test
* Las dos sub-tarjetas inferiores de estado operativo en Forward Test (Cuenta Demo IC Markets SC y Hyperliquid Testnet) mantenían un contenedor gris oscuro heredado (`bg-slate-900/60`) con texto ilegible.
* Se unificaron con la paleta Warm Minimalist:
  * Contenedores con fondo marfil cálido (`#FAF7F2`) y bordes nítidos (`#E6E2D8`).
  * Badges contrastados para posición flotante (`#EAE5DC` con texto `#181A20` y `#EEF2FF` con `#3730A3`).
  * Indicadores de estado activo en verde esmeralda institucional (`#065F46`) e indigo corporativo (`#5865F2`).
  * Sincronización estática en HTML y dinámica en tiempo real mediante `fetchForwardState()`.

---

## 6. Control de Versiones Git

* **VPS (`/root/AlgrokQuant`):**
  * `06ffcce`: *feat(ui): restrict active portfolio header to cockpit and forward tabs, and finish warm styling of forward test account cards*
  * Working tree: 100% limpio.
* **Local (`OpenMausBot`):**
  * Rama activa: `algrokquant-fleet`.
  * `daf0c924a`: *feat(ui): restrict active portfolio header to cockpit and forward tabs, and finish warm styling of forward test account cards*
