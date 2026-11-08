---
title: "Roadmap Cuantitativo Institucional - AlgrokQuant"
updated_at: "2026-11-08"
status: "ACTIVO Y VIGILADO"
author: "Director Supremo Sergio & Desk Lead Nexus"
tags:
  - roadmap
  - quantitative-desk
  - real-execution-bridge
  - double-q-learning
  - incubation-guardian
---

# Roadmap Cuantitativo Institucional · AlgrokQuant

Este documento formaliza la planificación estratégica, el estado de desarrollo y los hitos técnicos a corto y medio plazo para la flota de algoritmos cuantitativos y el orquestador de trading institucional.

---

## 1. Hitos Completados y Operativos (Producción VPS 169.58.230.132)

- [x] **Compendio Cuantitativo Ignacio Ayago / Techain (`task-339`):** 119 vídeos clasificados en 5 libros, compendio de 211k palabras cargado en NotebookLM (`bd74245e...`), sincronizador semanal en Windows y cron en VPS (`15 9,21 * * *`).
- [x] **Fundamentos Cuantitativos Numba JIT (`task-458`):** 5 bloques en `jev/` y `library/quant_foundations/` compilados con Numba 0.68.0 JIT (`SUPERTREND_FOLLOW`, `FVG_IMBALANCE`, `ZSCORE_EXTREME`, curtosis robusta, colchón sobre breakeven, meseta paramétrica).
- [x] **Screener Vectorizado Masivo 300k/día:** 4 `regime_gate` naturales, diagnóstico pasivo MAE/MFE sin sobreajuste y filtros de auditoría `@Auditor` y `@Skeptic` en cron (08:00, 14:00, 20:00 CET).
- [x] **Daemon 24/7 con Guardián de Incubación Monte Carlo:** Vigilancia continua con libro virtual de \$1.000 USD por estrategia, cono de fidelidad $P_{05}\text{--}P_{95}$, Z-score $|Z| \le 1.5\sigma$ y semáforos activos (43 GREEN, 2 AMBER, 0 RED).
- [x] **Orquestador Double Q-Learning Tabular:** 10 regímenes canónicos ($S_0 \dots S_9$), 3 arquetipos, 2 políticas independientes (`PROP_FIRM` vs. `CAPITAL_PROPIO`), Hard 40% Consistency Take-Profit Clamp para apuestas 1.25x en fondeo, memoria dual 80/20 y soft-update Polyak $\tau=0.25$.
- [x] **Despachador en Vivo & Buffer de Replay Online:** Integración lock-free en `scripts/prop_firm_forward_test_daemon.py`, telemetría de Libro C y watchdog de deriva con cooldown preventivo de 4 horas.
- [x] **Dashboard Web en Vivo (`:8080`):** Top HUD de activos, visualizador Triple Book (A vs. B vs. C), matriz $10 \times 3$, modal de explicabilidad causal (*Explainable RL*), simulador interactivo *"What-If"* y terminal en streaming de telemetría.

---

## 2. Hito Prioritario a Medio Plazo (En Espera por Graduación de Trades)

### 📌 Opción 3: Pasarela de Despliegue Real para Estrategias Graduadas (`Real Execution Bridge`)

> **Objetivo:** Construir el canal de transición automatizado y seguro desde la incubación virtual (paper trading) hacia cuentas con dinero real o pruebas de fondeo activas.

#### Contexto Operativo
Actualmente disponemos de **45 estrategias en incubación continua** con libro virtual aislado de \$1.000 USD/USDC cada una. Cuando el **Guardián de Incubación Monte Carlo** certifique que una estrategia alcanza **$\ge 30$ operaciones en forward test real**, manteniendo su curva de capital dentro del cono $P_{05}\text{--}P_{95}$, semáforo GREEN continuado y $|Z| \le 1.5\sigma$, emitirá el veredicto oficial:
$$\text{Verdict} = \mathbf{GRADUATED\_FOR\_REAL\_ACCOUNT}$$

#### Componentes de la Pasarela a Implementar:

1. **Bridges de Conexión Multi-Broker / Multi-Ecosistema:**
   * **IC Markets MetaTrader 5 (`algrokquant-mt5.service`):** Ejecución institucional TradFi para CFDs y Forex (`US500`, `USTEC`, `EURUSD`) vía Python MT5 IPC / ZeroMQ socket.
   * **TradeLocker Gateway:** REST API + WebSocket bridge de ejecución para cuentas de prop firms modernas de última generación.
   * **NinjaTrader / Rithmic Gateway:** Para operativas en Futuros CME Globex oficiales (Micro E-mini S&P 500 `MES`, Micro Nasdaq `MNQ`).
   * **Binance REST API / Hyperliquid L1 DEX:** Pasarela nativa con firmas criptográficas ed25519 para subyacentes Cripto (`BTC`, `ETH`, `SOL`).

2. **Flujo de Despliegue Seguro (Modo *Shadow / Staged Order*):**
   * **Generación en Sombra (*Staged Order*):** El bot no lanza órdenes a ciegas. Prepara la orden en memoria calculando el lote exacto según el capital de la cuenta real, el multiplicador Q-Learning $\pi^*(s)$ del régimen actual y el Hard 40% Consistency Clamp.
   * **Canal Dual de Confirmación Humana:**
     * **Confirmación por Telegram (`@AlphaReporter`):** Notificación en tiempo real con tarjeta detallada del trade (activo, lote, SL, TP ajustado) y botones interactivos inline `[ APROBAR Y DESPLEGAR ]` / `[ CANCELAR ]`.
     * **Confirmación por Dashboard (`:8080`):** Pestaña interactiva de *Staged Orders* con botón de despliegue con 1-click para el operador.

3. **Mecanismo de Reversión Preventiva (*De-graduation Fallback*):**
   * Si una estrategia en cuenta real sufre un drawdown superior al percentil 95 del cono Monte Carlo o su Z-score se degrada a $|Z| > 2.0\sigma$, el bridge cortará automáticamente las órdenes vivas, pausará la estrategia a $0.00x$ y devolverá el modelo a incubación demo.

---

## 3. Hito Secundario a Medio Plazo

- [ ] **Alimentación de Microestructura y Order Flow al Screener (CVD / Open Interest):** Ingesta de datos de Cumulative Volume Delta (CVD) e interés abierto de Coinglass y CME para enriquecer la discriminación de falsos breakouts en los regímenes $S_4$ (Compresión de Rango) y $S_7$ (Ruptura con Volatilidad).
