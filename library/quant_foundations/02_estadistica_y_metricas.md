# 02. Estadística Cuantitativa y Métricas de Optimización

> **Fuente:** Extracción técnica del canal `@Techain_Trading_Bots` (Ignacio N. Ayago).
> **Enfoque:** Esperanza matemática, falacia del *Win Rate*, optimización quirúrgica mediante distribuciones **MAE / MFE**, **Curtosis Robusta** por percentiles, **Z-Score** y métricas institucionales de auditoría.

---

## 1. La Esperanza Matemática ($E$) y la Falacia del *Win Rate*

Uno de los axiomas más repetidos en el canal (Vídeos #001, #005, #019, #021, #026, #032) es que **"El Win Rate es el envoltorio comercial; la Esperanza Matemática es el producto que viene dentro"**.

### A. Fórmula de la Esperanza Matemática (Expectancy)
$$E = (W \times \overline{G}) - ((1 - W) \times \overline{P}) - C_{\text{fricción}}$$

Donde:
* $W$: Probabilidad de acierto (*Win Rate*, entre $0$ y $1$).
* $\overline{G}$: Ganancia media de las operaciones positivas.
* $\overline{P}$: Pérdida media de las operaciones negativas (en valor absoluto).
* $C_{\text{fricción}}$: Coste medio por operación (*Spread* + Comisión + *Slippage* + *Swap*).

> **Regla Innegociable:** *"Si el Edge solo existe sin costes de fricción, es que el Edge no existe"* (Vídeo #001).

### B. El *Win Rate* de Equilibrio (*Breakeven Win Rate*) y la Regla del Colchón
Dado un ratio de pago (*Payoff Ratio* o *Risk:Reward* efectivo $R = \frac{\overline{G}}{\overline{P}}$), el porcentaje de acierto mínimo para no perder dinero antes de costes es:

$$W_{\text{equilibrio}} = \frac{1}{1 + R}$$

* Con $R = 1:1 \implies W_{\text{equilibrio}} = 50.0\%$
* Con $R = 1:2 \implies W_{\text{equilibrio}} = 33.3\%$
* Con $R = 1:3 \implies W_{\text{equilibrio}} = 25.0\%$
* Con $R = 1:14$ (ej. bot SMC asimétrico del Vídeo #019) $\implies$ Es altamente rentable con solo un **$16.9\%$ de *Win Rate*** (*Profit Factor* de $2.92$).
* A la inversa, en el Vídeo #032 audita una estrategia viral con un **$91.2\%$ de *Win Rate*** que **quiebra la cuenta** (*Profit Factor* $0.75$) porque sus pocas pérdidas son catastróficas frente a ganancias diminutas.

> **Filtro del Equilibrio con Colchón (Vídeo #032):**
> Para aprobar un sistema, su *Win Rate* real **después de costes** debe superar al $W_{\text{equilibrio}}$ en **al menos 12 a 15 puntos porcentuales** (o mantener un *Profit Factor* neto $\ge 1.30$).

---

## 2. Optimización Quirúrgica con MAE y MFE (Vídeo #012)

El resultado final de una operación (*Profit/Loss*) solo cuenta el final de la historia, pero oculta el recorrido intra-operación. Ignacio Ayago dedica una metodología específica al uso de **MAE** y **MFE** para calibrar paradas y objetivos con datos en lugar de intuición:

### Definiciones:
* **MAE (*Maximum Adverse Excursion* — Excursión Adversa Máxima):** El punto de mayor pérdida flotante ("el calor máximo") que soportó la operación mientras estuvo abierta antes de cerrarse.
* **MFE (*Maximum Favorable Excursion* — Excursión Favorable Máxima):** El punto de mayor beneficio flotante que llegó a alcanzar la operación antes de cerrarse.

### Diagnóstico Rápido mediante el Cociente $\frac{\text{MFE}}{\text{MAE}}$:
* Permite separar si el problema de un bot perdedor está en **la entrada** o en **la salida**:
  * Si las operaciones entran y casi nunca generan MFE antes de irse directo al Stop Loss $\implies$ **La señal de entrada no tiene ventaja (*Edge* nulo)**.
  * Si las operaciones alcanzan sistemáticamente un MFE alto pero terminan cerrando en pérdida o *breakeven* $\implies$ **La entrada es buena, pero el mecanismo de salida/*Take Profit* está mal calibrado**.

### Regla de los Percentiles para Colocar *Stop Loss* y *Take Profit* (Vídeo #012):
En lugar de optimizar el *Stop Loss* a fuerza bruta (lo que causa *overfitting*), se toma la distribución de MAE de **todas las operaciones ganadoras históricas** y la distribución de MFE:

| Parámetro | Regla Estadística por Percentiles | Matiz por Estilo (Swing vs. Scalping) |
| :--- | :--- | :--- |
| **Stop Loss Óptimo** | **Percentil 95 de la distribución de MAE** de las operaciones ganadoras (cubre el 95 % de las excursiones adversas que luego se recuperaron). | En *Swing Trading* o cuentas con límite estricto de Drawdown, mantener el **P95**. En *Scalping* puro, bajar al **P80 – P85** para cortar rápido anomalías. |
| **Take Profit Óptimo** | **Percentil 75 de la distribución de MFE** (asegura capturar el grueso del movimiento recurrente sin dejar el dinero en la mesa esperando el extremo del P95). | Combinar con cierre parcial o *Trailing Stop* por ATR a partir del P50-P60 del MFE. |

> **Nota sobre MetaTrader 5 (*Custom Max*):** Al optimizar en MT5, no se debe optimizar por "Beneficio Bruto máximo", sino por criterio personalizado (*Custom Max*) que pondere la calidad de la distribución MAE/MFE y estabilidad de la curva.

---

## 3. Curtosis (*Kurtosis*) y Control de Colas Gruesas (*Fat Tails* — Vídeo #014)

La desviación típica ($\sigma$) mide el "día normal" de un mercado o de un bot, pero **es ciega ante los cisnes negros y eventos extremos**. Dos bots pueden tener exactamente la misma media de ganancia y la misma desviación típica, pero uno tiene pérdidas suaves y el otro esconde una bomba de tiempo ("perfil asegurador": gana poquito 95 días y pierde media cuenta en 1 día).

### A. Por qué falla la Curtosis Clásica ($\mu_4 / \sigma^4$)
* Un único *outlier* extremo eleva a la cuarta potencia la desviación y distorsiona toda la métrica (como cuando entra un multimillonario en un bar y dispara el "sueldo medio" de todos los presentes).

### B. Fórmula de la Curtosis Robusta Basada en Percentiles (Vídeo #014)
Para evitar la distorsión de un único *outlier*, se mide el cociente entre la **anchura de las colas** y la **anchura del cuerpo central** de la distribución de retornos:

$$K_{\text{robusta}} = \frac{P_{97.5} - P_{2.5}}{P_{75} - P_{25}}$$

* **Umbral de Alerta Estructural:** En una distribución normal estándar (Gaussiana), este cociente ronda $\approx 2.90$. Un cociente **muy por encima de $2.90$** con asimetría negativa (*negative skew*) confirma **colas gruesas estructurales en el lado de las pérdidas**.

### C. Protocolo Anti-Crash de 5 Pasos basado en Curtosis:
1. **Exigir muestra mínima:** Con menos de $50$ operaciones no se puede evaluar la cola de una distribución.
2. **Auditar el perfil asegurador:** Si el bot gana micro-operaciones con *Win Rate* altísimo y tiene cola izquierda larga ($K_{\text{robusta}} \gg 2.9$), congelar lotaje.
3. **Usar la Curtosis del activo como diagnóstico de régimen** (nunca como señal de entrada): cuando las colas del mercado se ensanchan abruptamente, reducir exposición.
4. **Dimensionar el lote usando el Percentil 1 ($P_1$) de las pérdidas del bot, jamás usando la pérdida media:**
   * **Regla de Supervivencia:** Una cuenta (ej. $\$5.000$) debe poder sufrir **3 días/eventos consecutivos de cola ($P_1$)** y seguir completamente operativa sin violar límites de *Drawdown*.

---

## 4. El `Z-Score`: Estadística de Reversión y Guardián de Anomalías

El **Z-Score** aparece en dos dimensiones críticas dentro de la arquitectura de Techain (Vídeos #002, #003, #014, #067, #081):

### A. Como Motor de Reversión a la Media y Arbitraje Estadístico (Cestas / Pares)
$$Z = \frac{X - \mu_N}{\sigma_N}$$
* Mide a cuántas desviaciones estándar se encuentra el precio actual (o el diferencial/*spread* entre dos activos cointegrados) respecto a su media móvil de periodo $N$ (ej. $N = 20$).
* **Reglas operativas típicas (Vídeo #002 y #003):**
  * **Entrada:** Cuando $|Z| > 2.0$ (ej. $Z < -2.0$ para largos en un activo o residuo cointegrado).
  * **Salida natural:** Regreso al equilibrio ($Z = 0$).
  * **Cierre de emergencia (*Kill-Switch* de Régimen):** Si $|Z| \ge 4.0$ (ej. $Z < -4.0$). **Lección clave:** *"Un Z-Score de 4 no es 'más señal de rebote'; significa que el par se ha roto o ha cambiado de régimen macroeconómico (ej. divergencia de bancos centrales), y ahí no promedias: cierras y te apartas"*.

### B. Como "Guardián de Anomalía Multifactor" en Vivo (Vídeo #014)
* Vigila en tiempo real las métricas operativas del bot (duración de rachas perdedoras, tamaño de pérdidas, *slippage* y volatilidad) comparándolas en términos de `Z-Score` contra su distribución histórica de *backtest*. Si el comportamiento en vivo se desvía más allá del umbral estadístico (ej. $>2.5\sigma\text{--}3\sigma$), el guardián pausa el bot automáticamente.

---

## 5. Tabla Maestra de KPIs y Listones de Evaluación Cuantitativa

Recopilación de los umbrales numéricos exactos utilizados por Ignacio Ayago en el *Backtest Runner* y *Quant Lab* (Vídeos #001, #002, #004, #007, #023, #027, #036):

| Métrica | Nivel Pobre / Descarte | Nivel Aceptable / Mejorable | Nivel Sólido / Institucional | Observaciones Técnicas |
| :--- | :--- | :--- | :--- | :--- |
| **N.º de Operaciones ($N$)** | $< 30$ (Invalidez estadística) | $100 - 199$ | **$\ge 200 - 300$ trades** | En ventanas *Out-of-Sample* cortas, mínimo absoluto de $20\text{--}30$ trades. |
| **Profit Factor (PF)** | $< 1.00$ (Perdedor) | $1.00 - 1.29$ (Frágil ante fricción) | **$1.30 - 2.50$** | Un PF $> 3.0\text{--}4.0$ con muchas operaciones suele esconder *overfitting* o falta de costes. |
| **Sharpe Ratio (OOS)** | $< 0.50$ (Descarte directo) | $0.50 - 1.00$ | **$1.00 - 2.99$** | **Filtro sorpresa (Vídeo #023):** Si el Sharpe *Out-of-Sample* supera **$> 3.0$**, se descarta o audita por sospecha de *bug* / *look-ahead bias*. |
| **Max Drawdown (Histórico)** | $> 35\%$ | $20\% - 35\%$ | **$< 15\% - 20\%$** | Medir siempre el **Drawdown de Equity (flotante)**, no solo el de Balance al cierre. |
| **Drawdown Monte Carlo (P95)** | $> 35\%$ (Sello *Frágil*) | $15\% - 35\%$ (Sello *Neutral*) | **$< 15\%$ (Sello *Sólido*)** | Calculado sobre 1.000 permutaciones con capital de ruina fijado al 50 % del depósito. |
| **Probabilidad de Ruina (MC)** | $> 5.0\%$ | $1.0\% - 5.0\%$ | **$< 1.0\%$ (ideal $0.0\%$)** | Probabilidad de que el *Equity* caiga un 50 % en las 1.000 vidas alternativas de Monte Carlo. |
