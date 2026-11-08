# Protocolo de Gobernanza e Integración Cuantitativa (`AlgrokQuant` × `StratOS / Techain`)

> [!IMPORTANT]
> **Jerarquía Normativa Suprema (`AGENTS.md`):**
> Los 5 manuales cuantitativos de esta carpeta (`01` a `05`) enriquecen la memoria a largo plazo de los agentes (`@Ideator`, `@StratFinder`, `@CoderQuant`, `@Auditor`, `@Skeptic`, `@RiskFilter`). En caso de discrepancia entre un ejemplo de estos manuales y las leyes de gobernanza de `AlgrokQuant`, **prevalecen siempre e incondicionalmente las Reglas Supremas de `AlgrokQuant`**.

---

## 1. Reglas Supremas Inquebrantables en `AlgrokQuant`

1. **REGLA SUPREMA DE FONDEO (`[ Fondeo ]` — EOD Drawdown Exclusivo):**
   - **Queda terminantemente prohibido asumir o aplicar *Trailing Drawdown* intradía en cuentas de fondeo.**
   - Las fluctuaciones intradía de ganancias flotantes no realizadas (*floating equity peaks*) **nunca** desplazan el umbral de pérdida máxima.
   - Todo cálculo de supervivencia de `@Auditor` y `@RiskFilter` en modo `PROP_FIRM`, `PROP_FIRM_FUTURES` y `PROP_FIRM_CFD` se evalúa **exclusivamente sobre el Balance/Equity al Cierre Contable Diario (END OF DAY — EOD)**:
     - **Futuros CME (`US500`, `USTEC` 5m RTH):** Target $+6.0\%$, Max EOD Drawdown $\le 3.0\%$.
     - **CFDs/Forex (`US500`, `USTEC`, `EURUSD`):** Target $+8.0\%\text{--}10.0\%$, Max Daily Drawdown $\le 4.0\%$, Max Total EOD Drawdown $\le 8.0\%$.
2. **GOBERNANZA DE CAPITAL PROPIO (`[ Capital Propio ]`):**
   - Horizonte multianual completo ($10\text{ años}$ en TradFi, ciclo completo en Crypto).
   - **CAGR Anual $\ge 30.0\%$** y superación estricta del *Buy & Hold* ($\text{CAGR}_{\text{strat}} > \text{CAGR}_{\text{BnH}}$).
   - **Max Drawdown Continuo $\le 20.0\%$** (alerta preventiva en $-10.0\%$).
   - **Deflated Sharpe Ratio ($\text{DSR}$) $\ge 0.95$** y **Sharpe Observado $\ge 1.50$** (con alerta de inspección anti-*look-ahead* si $\text{Sharpe} > 3.50$).
3. **SEPARACIÓN ESTRICTA DE INFRAESTRUCTURA DE EJECUCIÓN:**
   - **TradFi (`US500`/`SPX`, `USTEC`/`NDX`, `EURUSD`):** Ejecución exclusiva en **IC Markets MT5** (`algrokquant-mt5.service`).
   - **Crypto (`BTC`, `ETH`, `SOL`):** Prohibido en MT5/CFDs; ejecución y backtesting exclusivos en **Hyperliquid L1 DEX / Binance** (`algrokquant-forward-test.service`).
4. **FLUJO DE AUTO-DESPLIEGUE A INCUBACIÓN DEMO (`Forward Test`) Y GRADUACIÓN A REAL:**
   - Toda estrategia que apruebe simultáneamente `@Auditor` (DSR + Monte Carlo 1.000 runs + Curtosis Robusta + Colchón $WR_{\text{BE}}$), `@Skeptic` (Latencia $+1\text{ barra}$ + Fricción $1.5\times$ + Meseta Paramétrica $\pm 10\%/\pm 20\% \ge 70\%$) y `@RiskFilter` se **auto-despliega inmediatamente en Forward Test (Demo)** con un libro virtual aislado de $\$1.000\text{ USD/USDC}$.
   - Durante el **Forward Test (Demo)**, el **Guardián de Incubación** monitoriza que la curva de capital permanezca dentro del **Cono de Monte Carlo ($P_5\text{--}P_{95}$)** y con **Z-Score Multifactorial $|Z| \le 1.5\sigma$** durante $30\text{--}100$ operaciones antes de autorizar su paso a **Cuenta Real / Challenge Real**.

---

## 2. Índice de Manuales Fundacionales (`library/quant_foundations/`)

- [`01_arquitectura_sistemas.md`](file:///C:/Users/Sergio/Documents/Antigravity/OpenMausBot/library/quant_foundations/01_arquitectura_sistemas.md): Arquitectura de 5 capas, desacoplamiento `Signal` vs. `Regime Gate`, clasificación de los 7 y 10 Regímenes Canónicos, Tier List de Indicadores (Tier S a Tier F) y booleanización de acción del precio sin *look-ahead bias*.
- [`02_estadistica_y_metricas.md`](file:///C:/Users/Sergio/Documents/Antigravity/OpenMausBot/library/quant_foundations/02_estadistica_y_metricas.md): Esperanza matemática con fricción real, Regla del Colchón sobre Breakeven Win Rate ($WR \ge WR_{\text{BE}} + 12\%$), calibración estadística de salidas mediante cuantiles $\text{SL} = P_{95}(\text{MAE}_{\text{winners}})$ y $\text{TP} = P_{75}(\text{MFE}_{\text{winners}})$, Curtosis Robusta por Percentiles y Guardián Z-Score Multifactorial.
- [`03_validacion_y_robustez.md`](file:///C:/Users/Sergio/Documents/Antigravity/OpenMausBot/library/quant_foundations/03_validacion_y_robustez.md): Embudo institucional de validación, Walk-Forward Analysis (retención OOS $\ge 50\%$ IS), Test de Meseta de Sensibilidad Paramétrica ($\pm 5\%, \pm 10\%, \pm 20\%$ con supervivencia $\ge 70\%$), Bootstrap Monte Carlo de 1.000 trayectorias y protocolo de graduación en Forward Test (Demo).
- [`04_ia_y_machine_learning.md`](file:///C:/Users/Sergio/Documents/Antigravity/OpenMausBot/library/quant_foundations/04_ia_y_machine_learning.md): Transpilación determinista frente a generación libre de código, taxonomía de 30 bloques de IA/ML (Clasificador de Régimen, Smart Router, Ensemble Voting 5 modelos, Confidence Gate, Q-Learning tabular y Self-Healer).
- [`05_gestion_riesgo_carteras.md`](file:///C:/Users/Sergio/Documents/Antigravity/OpenMausBot/library/quant_foundations/05_gestion_riesgo_carteras.md): Gestión de riesgo adaptativa de 3 capas, Tabla Multiplicadora de Lote por Régimen ($1.25\times$ a $0.00\times$), varianza de cartera y filtro de correlación ($\rho < 0.20$ óptimo, $\rho > 0.50$ redundante), arquitectura de los 3 Bloques Macro (Convexo, Cóncavo, Híbrido), Demonio de Shannon y Semáforo Quincenal de Mantenimiento.
