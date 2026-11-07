# TAXONOMÍA FORMAL Y BLOQUES CONSTRUCTIVOS DE ESTRATEGIAS CUANTITATIVAS (100.000/CICLO · 300.000/DÍA)
**Mesa Cuantitativa Institucional AlgrokQuant · Jev Engine & Enjambre Multi-Agente**
**Frecuencia de Búsqueda:** 3 Ciclos Diarios (`08:00 CET`, `14:00 CET`, `20:00 CET`) × `100.000` combinaciones = **`300.000` Estrategias Evaluadas/Día**

---

## 1. Arquitectura de Generación Combinatoria Vectorizada (100.000 Combinaciones por Ciclo)
En cada uno de los 3 ciclos diarios, el motor vectorizado `JevScreener` explora **100.000 configuraciones paramétricas y estructurales** combinando 6 módulos ortogonales sin sesgo de anticipación (*zero lookahead bias*, señales evaluadas al cierre de la vela $t-1$ y ejecutadas en apertura $t$).

| Bloque Estructural | Función en la Estrategia | Herramientas, Indicadores y Osciladores | Rango de Parámetros Explorados |
| :--- | :--- | :--- | :--- |
| **1. Filtros de Tendencia y Estructura Macro** | Determina el sesgo direccional estructural y filtra operaciones contra-tendencia en regímenes direccionales. | • **EMA Stack** (Exponencial)<br>• **SMA Institucional**<br>• **Supertrend** (ATR-based)<br>• **KAMA** (Kaufman Adaptive MA)<br>• **Donchian Channel** (High/Low)<br>• **Ichimoku Cloud** (Tenkan/Kijun/Senkou)<br>• **Linear Regression Slope** ($\beta_1$) | • `EMA Fast`: $\{8, 9, 12, 13, 20, 21, 34, 50\}$<br>• `EMA Slow`: $\{50, 55, 89, 100, 144, 200\}$<br>• `Donchian N`: $\{10, 14, 20, 28, 40, 55, 89\}$<br>• `Supertrend`: Periodo $\{7, 10, 14, 20\}$, Mult $\{1.5, 2.0, 2.5, 3.0, 3.5\}$ |
| **2. Osciladores de Momentum y Reversión a la Media** | Identifica agotamiento estadístico (*mean-reversion*) o ignición de impulso (*momentum thrust*). | • **Wilder RSI** (Relative Strength Index)<br>• **Connors RSI** ($\text{CRSI}_{3,2,100}$)<br>• **Stochastic RSI** ($\%K, \%D$)<br>• **MACD Histogram** ($12, 26, 9$ y variantes)<br>• **CCI** (Commodity Channel Index)<br>• **Williams %R** & **ROC** (Rate of Change)<br>• **Z-Score Estadístico** ($\frac{P - \mu_N}{\sigma_N}$) | • `RSI Period`: $\{2, 3, 5, 7, 9, 14, 21\}$<br>• `Umbral Oversold`: $\{10, 15, 20, 25, 30, 35\}$<br>• `Umbral Overbought`: $\{65, 70, 75, 80, 85, 90\}$<br>• `Z-Score Lookback`: $\{15, 20, 30, 50, 100\}$, $|Z| \in \{1.5, 1.8, 2.0, 2.2, 2.5, 3.0\}$ |
| **3. Bandas de Volatilidad y Compresión** | Detecta compresión de volatilidad (*Squeeze*) previa a expansiones o extremos estadísticos de desviación. | • **Bollinger Bands** ($\mu \pm k\sigma$)<br>• **Keltner Channels** ($\text{EMA} \pm m \cdot \text{ATR}$)<br>• **TTM Squeeze** ($\text{BB dentro de KC}$)<br>• **ATR Ratio** ($\text{ATR}_{\text{corto}} / \text{ATR}_{\text{largo}}$)<br>• **Chaikin Volatility** & **Yang-Zhang $\sigma$** | • `BB Period`: $\{14, 20, 25, 30\}$, $\sigma \in \{1.5, 1.8, 2.0, 2.2, 2.5, 3.0\}$<br>• `KC Mult`: $\{1.0, 1.25, 1.5, 2.0, 2.5\}$<br>• `ATR Period`: $\{7, 10, 14, 20, 28\}$ |
| **4. Microestructura, Volumen y Flujo Institucional** | Confirma participación institucional real y ancla precios de equilibrio intradía (especialmente en RTH 5m). | • **VWAP Institucional** + Bandas $\pm 1\sigma, \pm 2\sigma, \pm 3\sigma$<br>• **Opening Range Breakout (ORB)** NY/London<br>• **Volume Spike** ($V_t > k \cdot \text{SMA}(V, 20)$)<br>• **OBV** (On-Balance Volume) & **MFI** (Money Flow Index)<br>• **CVD Proxy** (Cumulative Volume Delta) | • `ORB Window`: $\{5\text{m}, 15\text{m}, 30\text{m}, 60\text{m}\}$<br>• `Volume Mult` $k$: $\{1.2, 1.5, 1.8, 2.0, 2.5, 3.0\}$<br>• `VWAP Sigma`: $\{1.0, 1.5, 2.0, 2.5\}$<br>• `MFI Period`: $\{7, 10, 14, 20\}$ |
| **5. Filtros Cuantitativos de Régimen (Orquestador)** | Evita operar en ruido browniano de alta entropía y sincroniza la familia de estrategia con el estado del mercado. | • **Entropía de Shannon Normalizada** ($H_{\text{norm}}$)<br>• **Exponente de Hurst** ($H$ vía R/S Analysis)<br>• **Kaufman Efficiency Ratio** ($\text{KER}_{14}$)<br>• **Wilder ADX** ($14$) + Direccionalidad $+DI/-DI$<br>• **Filtro de Sesión Horaria** (RTH CME 09:30–16:00 ET) | • `H_norm Max`: $\{0.75, 0.78, 0.80, 0.82, 0.84\}$<br>• `Hurst Trend`: $H > \{0.52, 0.55, 0.58\}$<br>• `Hurst MeanRev`: $H < \{0.48, 0.45, 0.42\}$<br>• `ADX Umbral`: $\{18, 20, 22, 25, 30\}$ |
| **6. Gestión de Salidas, Sizing y Riesgo Dinámico** | Protege el capital, dimensiona por volatilidad y asegura asimetría matemática positiva. | • **Stop Loss Dinámico**: $k_{\text{SL}} \cdot \text{ATR}_{14}$ o estructura Swing<br>• **Take Profit Dinámico**: $k_{\text{TP}} \cdot \text{ATR}_{14}$ o retorno a $\mu/\text{VWAP}$<br>• **Trailing Stop**: Chandelier Exit / ATR Trailing<br>• **Time-Stop**: Cierre por agotamiento temporal ($N$ barras)<br>• **EOD Flat**: Cierre forzoso intradía (Prop Firm) | • `SL ATR Mult`: $\{0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0\}$<br>• `TP ATR Mult`: $\{1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0\}$<br>• `Time-Stop`: $\{6, 12, 24, 48, 72\}$ barras<br>• `Sizing`: **1.0% Equity** (Capital Propio) / **0.25%–0.50%** (Prop Firm) |

---

## 2. Distribución de las 100.000 Combinaciones por Ciclo entre las 3 Mesas Operativas

Cada ciclo de **100.000 estrategias** se reparte en una matriz estructurada según vehículo y horizonte:

1. **Mesa 1 · Capital Propio Multi-Año (`40.000` combinaciones/ciclo = `120.000`/día):**
   - **Activos:** `BTC`, `ETH`, `SOL` (Crypto multi-año nativo) y `SPX`, `NDX`, `EUR_USD` (TradFi 10 Años).
   - **Timeframes:** `15m`, `1h`, `4h`.
   - **Familias exploradas:** *Trend-Following Breakout* (Donchian + EMA + ADX), *Volatility Squeeze Expansion* (BB/KC + KAMA + Volume Spike), *Multi-Day Pullback Continuation* (EMA 50/200 + RSI2/CRSIDip), y *Statistical Mean-Reversion* (Z-Score + Bollinger + Hurst $< 0.48$).
   - **Requisitos Mandatorios:** $\text{CAGR Anual} \ge 30.0\%$, **Superar Buy & Hold Anual ($\text{CAGR} > \text{BnH}$)**, $\text{MaxDD} \le 20.0\%$, Sizing dinámico **1.0% del equity por trade**.

2. **Mesa 2 · Cuentas de Fondeo Futuros CME Globex (`30.000` combinaciones/ciclo = `90.000`/día):**
   - **Activos y Sesión:** Exclusivamente `US500` (ES/MES) y `US100` (NQ/MNQ) en `5m` RTH (`09:30–16:00 ET`), 100% Flat al cierre diario.
   - **Familias exploradas:** *NY Opening Range Breakout (ORB 15m/30m)*, *VWAP Institutional Trend Pullback*, *Extreme Statistical Reversion to VWAP* ($\pm 2.5\sigma$ + RSI), *RTH Microstructure Momentum Thrust*.
   - **Requisitos Mandatorios:** Profit Target **$6.0\%$**, Max Trailing EOD Drawdown **$\le 3.0\%$**, Time-to-Target **$< 30$ días naturales** (Prioridad **Tier Oro $< 15$ días naturales**).

3. **Mesa 3 · Cuentas de Fondeo CFDs (`30.000` combinaciones/ciclo = `90.000`/día):**
   - **Activos y Sesión:** Exclusivamente `US500` y `US100` en `5m` RTH (`09:30–16:00 ET`), 100% Flat antes del rollover.
   - **Familias exploradas:** *High-Asymmetry Intraday Breakout*, *VWAP + Keltner Volatility Ignition*, *Intraday Exhaustion Fade* con filtro estricto de spread/slippage estresado ($\times 1.5$).
   - **Requisitos Mandatorios:** Profit Target **$8.0\% - 10.0\%$**, Max Drawdown Diario **$\le 4.0\%$**, Max Drawdown Total **$\le 8.0\%$**, Time-to-Target **$< 30$ días naturales** (Prioridad **Tier Oro $< 15$ días naturales**).
