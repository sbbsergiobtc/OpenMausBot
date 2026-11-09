# LESSON-20261109-023: Infraestructura TradFi Triple Cuenta MT5 y Banco de Reserva Dinámico (Strategy Vault SQLite)

**Fecha:** 2026-11-09T02:20:00+01:00  
**Autor:** Desk Lead Nexus & Enjambre Cuantitativo AlgrokQuant  
**Aprobado por:** Director Supremo Sergio  
**Categoría:** Infraestructura de Ejecución · Gestión de Cartera Multicuenta · Robustez Estadística  

---

## 1. Contexto y Objetivos Superados

En esta sesión se completaron e integraron en producción dos fases críticas de la arquitectura cuantitativa de AlgrokQuant:

1. **Fase 2 (Infraestructura TradFi Triple Cuenta MT5)**:
   - Superación del modelo monousuario para soportar simultáneamente tres cuentas de trading segregadas bajo el broker IC Markets Demo SC.
   - Configuración de sizing diferenciado por balance real y régimen regulatorio (ESMA vs. Prop Firm).
   - Enrutamiento dinámico por cuenta en el microservicio headless MT5 sin colisiones ni consumo excesivo de memoria RAM.

2. **Fase 3 (El "Banco de Reserva Dinámico" - Strategy Vault SQLite)**:
   - Creación de una base de datos local SQLite (`data/strategy_vault.db`) para gestionar el ciclo de vida de las estrategias.
   - Conexión directa con el Screener masivo de 100.000 combinaciones (08:00, 14:00 y 20:00 CET).
   - Automatización al 100% del relevo de estrategias: si una titular entra en drawdown y se degrada a semáforo **ROJO** (ruptura de cono Monte Carlo $P_{95}$), el sistema la envía al banquillo y promueve automáticamente a la mejor suplente de la base de datos ($DSR \ge 0.85$) sin requerir intervención manual.

---

## 2. Mapa de Cuentas y Desks Operativos

| # | Desk / Entorno | Login MT5 | Servidor Broker | Balance Vivo | Apalancamiento | Activos Oficiales | Regla Consistencia |
| :-: | :--- | :---: | :---: | :---: | :---: | :--- | :---: |
| **1** | **Capital Propio (Retail)** | **`53138338`** | `ICMarketsSC-Demo` | **$1,000.00 USD** | **1:30** | `US500` (4h), `USTEC` (2h) | **Desactivada** (Compuesto puro) |
| **2** | **Fondeo Prop Firm CFDs** | **`53138341`** | `ICMarketsSC-Demo` | **$50,000.00 USD** | **1:100** | `EURUSD` (1h), CFDs TradFi | **Activada** (Clamp 40% TP) |
| **3** | **Fondeo Futuros CME** | **`53138343`** | `ICMarketsSC-Demo` | **$50,000.00 USD** | **1:100** | Futuros CME (`NQ`, `ES`, `GC`) | **Activada** (Clamp 40% TP) |
| **4** | **Cripto Nativa L1** | `0x009D...` | `Hyperliquid Testnet` | **$1,036.42 USDC** | Cross Margin | `SOL-PERP`, `BTC-PERP` | **Desactivada** (Fricción horaria) |

---

## 3. Principios de Arquitectura del Strategy Vault SQLite

### A. Condición de Admisión Incondicional: $DSR \ge 0.85$
El Screener masivo descarta el curve-fitting mediante el cálculo del **Deflated Sharpe Ratio (DSR)** considerando las 100.000 combinaciones probadas.
- Sólo aquellas estrategias que obtienen $DSR \ge 0.85$ tras el examen destructivo `@Skeptic` son admitidas en `strategy_vault.db` con estado `BENCH_RESERVE`.

### B. Ciclo de Vida y Estados Cuantitativos:
- **`ACTIVE_STARTER`**: Estrategia titular operando activamente en el daemon.
- **`BENCH_RESERVE`**: Estrategia suplente certificada ($DSR \ge 0.85$) lista para entrar al campo.
- **`BENCH_INJURED`**: Estrategia retirada al banquillo tras degradación a semáforo ROJO (ruptura de cono Monte Carlo $P_{95}$ o anomalía $Z > 2.0\sigma$).
- **`RETIRED`**: Estrategia archivada definitivamente.

### C. Algoritmo de Relevo Autónomo:
Ante semáforo ROJO en una titular, el daemon ejecuta:
1. `demote_starter_to_bench(strat_id, reason)` -> pasa a `BENCH_INJURED`.
2. `get_best_reserve(asset, desk_mode, min_dsr=0.85)` -> selecciona la suplente óptima:
   $$\max(DSR) \quad \text{con } DSR \ge 0.85, \quad \max(\text{Profit Factor}), \quad \min(\text{Max DD}_{P95})$$
3. `promote_reserve_to_starter(new_id, replacing_id=strat_id)` -> pasa a `ACTIVE_STARTER`.
4. Actualización en caliente de `PORTFOLIO_CONFIG` y envío de alerta detallada a Telegram (`@AlphaReporter`).

---

## 4. Estado de Verificación en Producción (VPS 169.58.230.132)

- **`algrokquant-mt5`**: Servicio activo en puerto 8001 con caché en memoria (TTL 120s) y soporte triple cuenta.
- **`algrokquant-forward-test`**: Daemon activo 24/7 sincronizando balance y evaluando cono Monte Carlo.
- **`algrokquant-dashboard`**: Backend FastAPI activo en puerto 8080 exponiendo `/api/forward_state` y `/api/strategy_vault`.
- **`openmausbot`**: Gateway de mensajería y alertas Telegram activo en puerto 8799.
- **`data/strategy_vault.db`**: Inicializado y poblado con 4 titulares y 7 suplentes con $DSR \ge 0.85$.
