# Catálogo Secundario: Ejemplos Concretos de Estrategias y Bots Auditados en el Canal

> **Propósito de esta carpeta:** Tal como definimos, aquí se almacenan de forma separada los **ejemplos concretos de estrategias, setups virales auditados y plantillas por régimen** mostrados en los vídeos del canal `@Techain_Trading_Bots`. Sirven como banco de pruebas (*benchmark*) para nuestro motor de *backtesting*, manteniendo el conocimiento cuantitativo puro en `01_core_quant_knowledge/`.

---

## 1. Tabla Resumen de Bots y Estrategias Analizadas en Directo

| Código / Ficha | Estrategia / Bot | Activo y Timeframe | Estilo / Familia | Resultado de la Auditoría en el Canal | Enlace al Vídeo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| [BOT_01](file:///C:/Users/Sergio/.gemini/antigravity/scratch/techain-quant-lab/02_strategy_examples/fichas_bots/BOT_01_supply_demand_filtrada.md) | **Oferta y Demanda + Doble Filtro (Tendencia y Sesión)** | `XAUUSD` (H1) | Swing / Estructura | **PF 1.79**, DD histórico $23.98\%$, pero **Frágil en Monte Carlo** ($DD_{P95} > 35\%$) sin optimizar. | [Vídeo #001](https://www.youtube.com/watch?v=eTty1NzZI8A) |
| [BOT_02](file:///C:/Users/Sergio/.gemini/antigravity/scratch/techain-quant-lab/02_strategy_examples/fichas_bots/BOT_02_zscore_mean_reversion.md) | **Reversión a la Media por Z-Score (20 periodos)** | Multi-Activo (H1) | Reversión Estadística | Candidata didáctica: Entrada $Z < -2$, Salida $Z = 0$, Stop de emergencia $Z < -4$, Riesgo $1\%$. | [Vídeo #002](https://www.youtube.com/watch?v=q_gQDfAIqGY) |
| [BOT_03](file:///C:/Users/Sergio/.gemini/antigravity/scratch/techain-quant-lab/02_strategy_examples/fichas_bots/BOT_03_cesta_arbitraje_cointegracion.md) | **Arbitraje Estadístico / Cesta Multi-Divisa (*Water & Oil*)** | Cesta Forex (`M1` a `H4`) | Arbitraje / Cointegración | Opera divergencias ponderadas por volatilidad en 5 *timeframes*; se silencia en 2 de los 3 regímenes. | [Vídeo #003](https://www.youtube.com/watch?v=ihg7YdDExGU) |
| [BOT_04](file:///C:/Users/Sergio/.gemini/antigravity/scratch/techain-quant-lab/02_strategy_examples/fichas_bots/BOT_04_price_action_swings_objetivos.md) | **Acción del Precio 100% Objetiva (Swings + Ruptura)** | `XAUUSD` (H1) | Swing / Ruptura | **Retorno +105.8% (2020-2026)**, PF $1.87 \to 1.74$ tras fricción, WR $41.9\%$, alerta en $DD_{P95}$ ($39.8\%$). | [Vídeo #004](https://www.youtube.com/watch?v=fUfqEA1coQ0) |
| [BOT_05](file:///C:/Users/Sergio/.gemini/antigravity/scratch/techain-quant-lab/02_strategy_examples/fichas_bots/BOT_05_cruce_medias_puerta_adx.md) | **Cruce de Medias + Puerta de Régimen `ADX(14) > 25`** | `XAUUSD` (H1, 35.766 velas) | Tendencial Filtrado | Pasa de perder $-\$1.271$ (PF $0.60$, DD $102\%$) a ganar **+$27.236 (+272%)**, **PF 1.58**, DD $24.4\%$. | [Vídeo #006](https://www.youtube.com/watch?v=rAk0eqFnkp4) |
| [BOT_06](file:///C:/Users/Sergio/.gemini/antigravity/scratch/techain-quant-lab/02_strategy_examples/fichas_bots/BOT_06_supertrend_horizonte_optimo.md) | **Supertrend Cuantificado por Horizonte de Cierre** | `XAUUSD` (H1 / D1) | Seguimiento Volatilidad | En D1 con cierre por horizonte óptimo (68 barras) alcanza **75% de tasa de acierto** a favor de señal. | [Vídeo #011](https://www.youtube.com/watch?v=1x78Xf0w4Cw) |
| [BOT_07](file:///C:/Users/Sergio/.gemini/antigravity/scratch/techain-quant-lab/02_strategy_examples/fichas_bots/BOT_07_vwap_drift_pullback.md) | **VWAP Banda 3 + Filtro de Régimen (Reversivo Volátil)** | Índices / Forex | Intradía / Fondeo | Sin filtro de régimen fracasa (**PF 0.15**); solo funciona al restringir al estado *Reversivo Volátil*. | [Vídeo #018](https://www.youtube.com/watch?v=JVCoXEPVD9I) |
| [BOT_08](file:///C:/Users/Sergio/.gemini/antigravity/scratch/techain-quant-lab/02_strategy_examples/fichas_bots/BOT_08_smc_7_filtros_institucional.md) | **SMC Institucional con 7 Filtros Booleanos (OB + FVG + Sweep)** | Forex / Oro (H1 / M15) | Asimétrico Alto R:B | **PF 2.92**, Retorno **$+89\%$**, con un **Win Rate de solo 16.9%** pero **Ratio R:B medio de 14:1**. | [Vídeo #019](https://www.youtube.com/watch?v=AytFCULDyDM) |
| [BOT_09](file:///C:/Users/Sergio/.gemini/antigravity/scratch/techain-quant-lab/02_strategy_examples/fichas_bots/BOT_09_ineficiencia_oro_ruptura_diaria.md) | **Ineficiencia Estadística del Oro: Ruptura Máximo de Ayer (Sin Viernes)** | `XAUUSD` (H1 / D1) | Estacional / Breakout | Explota la ineficiencia de continuación alcista en `XAUUSD` excluyendo los viernes por exceso de ruido. | [Vídeo #020](https://www.youtube.com/watch?v=oVt83-odF3g) |
| [BOT_10](file:///C:/Users/Sergio/.gemini/antigravity/scratch/techain-quant-lab/02_strategy_examples/fichas_bots/BOT_10_viral_83wr_ema_macd_bb_rsi.md) | **Auditoría Estrategia Viral 83% WR (EMA 9/55/200 + MACD + BB + RSI)** | `EURUSD` | Reversión / Pullback | **DESMENTIDA:** Alcanza $91.2\%$ de Win Rate pero **Profit Factor 0.75** (pierde dinero por asimetría negativa). | [Vídeo #032](https://www.youtube.com/watch?v=YiC9gmo2A4Q) |

---

## 2. Las 7 Plantillas Canónicas por Régimen de Mercado (Vídeo #052)

En el Vídeo #052 (*Stop Losing Money: Use These 100 Trading Strategies Based on Market Regime*), documenta las **7 familias arquetípicas** diseñadas para cada uno de los 7 regímenes de mercado:

| Régimen de Mercado | Código en Catálogo | Arquitectura de la Estrategia |
| :--- | :--- | :--- |
| **1. Tendencia Alcista (`Bull Trend`)** | `BT_03` | **Donchian Channel Breakout + Retest:** Ruptura del canal superior de Donchian seguida de validación en el *pullback* con salida por múltiplo de ATR. |
| **2. Tendencia Bajista (`Bear Trend`)** | `BR_02` | **Pullback EMA(20) + Filtro RSI:** Entrada en corto cuando el precio retrocede a la media exponencial de 20 periodos en estructura bajista sin agotamiento extremo. |
| **3. Rango / Lateral (`Range`)** | `RG_02` | **Bandas de Bollinger + Choppiness Index:** Opera reversiones desde los extremos de las bandas únicamente cuando el *Choppiness Index* confirma ausencia de direccionalidad. |
| **4. Rupturas (`Breakout`)** | `BO_01` | **Bollinger Squeeze:** Detecta compresión de volatilidad y dispara a favor de la primera expansión con filtro de volumen/rango de vela $\ge 1.5\times \text{ATR}$. |
| **5. Alta Volatilidad (`High Volatility`)** | `HV_06` | **News Dodger / Protección:** Bloquea entradas estándar o exige confirmación tras barrido de liquidez con stops ampliados por ATR y lotaje reducido. |
| **6. Baja Volatilidad (`Low Volatility`)** | `LV_13` | **Scalping de Rango Estrecho con RSI:** Micro-reversiones en sesiones de baja amplitud (solo viable en cuentas con *spread* cero / ECN institucional). |
| **7. Momentum (`Momentum`)** | `MO_08` | **Squeeze + ADX Creciente + ROC:** Exige aceleración simultánea en tasa de cambio (`ROC`) y pendiente positiva en `ADX(14) > 25`. |

---

## 3. Ejemplos Reales de su Cartera Auditada de 32 Bots (Vídeo #028)

En el Vídeo #028 muestra ejemplos concretos que operan juntos dentro de su cuenta real auditada ($37.31\%$ CAGR en 60 meses, correlación media $\bar{\rho} = 0.16$):
* **`Helios Momentum` (`DAX` en `H1` — Bloque Convexo):** Seguidor de tendencia pura. *Win Rate* de solo el **$45\%$**, pero sus operaciones ganadoras superan ampliamente a las perdedoras.
* **`Lyra Scalper` (`EURUSD` en `M5` — Bloque Cóncavo):** Alta frecuencia / reversión corta. *Win Rate* del **$87.2\%$**, pero ratio de beneficio corto ($0.4R$ por operación). Aporta flujo de caja constante.
* **`Phoenix Scalper` (`SP500` — Bloque Cóncavo):** Detectado en la auditoría mensual con correlación $\rho = 0.52$ respecto a `Lyra Scalper` (candidato a reducción de peso por redundancia).
* **`Sigma MR` (`SP500` — Reversión a la Media):** Aprobado en la puerta de incubación tras **95 días en vivo** y **51 operaciones fuera de muestra** con un **Profit Factor de 2.60**.
