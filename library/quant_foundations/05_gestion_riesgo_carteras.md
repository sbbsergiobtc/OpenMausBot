# 05. Gestión de Riesgo Adaptativa, Ingeniería de Carteras y Matemática de Fondeo

> **Fuente:** Extracción técnica del canal `@Techain_Trading_Bots` (Ignacio N. Ayago) — Vídeos #003, #005, #008, #014, #016, #018, #027, #028, #031, #051.
> **Enfoque:** Las 6 reglas de Gestión de Riesgo Adaptativa, el Criterio de Kelly Fraccional, la Fórmula de Varianza de Cartera de Hedge Funds, Correlación vs. Cointegración, el Demonio de Shannon (Rebalanceo $1/N$), la Estructura Macro Convexa/Cóncava y la Matemática de Supervivencia en *Prop Firms*.

---

## 1. Gestión de Riesgo Adaptativa en 3 Capas y 6 Reglas (Vídeo #027)

En el Vídeo #027 (*The Secret Behind Professional Trading Bots: Adaptive Risk Management*), Ignacio Ayago demuestra cómo una estrategia perdedora con lote fijo (*Drawdown* del $104\%$) pasa a tener un **Drawdown máximo de solo el $7\%$ y un Profit Factor de $1.41$** sin cambiar una sola línea de su señal de entrada, únicamente aplicando **Gestión de Riesgo Adaptativa por Régimen y Volatilidad**.

### Las 6 Reglas Institucionales de Dimensionamiento y Protección:
1. **Regla 1 — Riesgo Base Fraccional:**
   * Riesgo estándar por operación: **$0.5\%$ al $1.0\%$ del capital**.
   * **Techo absoluto innegociable:** **Jamás superar el $2.0\%$** en ningún escenario ni régimen.
2. **Regla 2 — Stop Loss Dinámico por Volatilidad (Jamás en Pips Fijos):**
   * Un *Stop Loss* fijo de 20 pips no significa lo mismo cuando el mercado está dormido que en medio de un dato de inflación (IPC/NFP).
   * Se utiliza siempre el **`ATR(14)`** con un **multiplicador base de $2.0\times$**:
     * **Rango válido:** Entre **$1.5 \times \text{ATR}(14)$** (para operativa intradía ajustada) y **$3.0 \times \text{ATR}(14)$** (para *Swing Trading*).
3. **Regla 3 — Tabla de Multiplicadores de Lotaje por Régimen de Mercado:**
   * Como la estrategia tiene una esperanza matemática distinta en cada uno de los 10 estados de mercado, el tamaño de posición se multiplica por un factor dinámico según el estado detectado en tiempo real:
     * **Régimen Favorable (ej. Tendencia Alcista/Bajista Limpia):** Multiplicador $1.0\times$ (o hasta $1.25\times$ dentro del techo de riesgo).
     * **Régimen Neutro / Transición:** Multiplicador reducido ($0.5\times$).
     * **Régimen Hostil (ej. Rango Volátil / Caos sin dirección):** Multiplicador de hibernación ($0.1\times$ —micro-lote mínimo $0.01$— o **$0.0\times$ autopausa total**).
4. **Regla 4 — Autopausa / *Circuit Breaker* con Reactivación Humana:**
   * Si se alcanza el umbral de pérdida diaria/semanal o de racha anómala, **el bot se detiene automáticamente**, pero **la decisión de reactivarlo es siempre humana tras auditar qué ocurrió**, nunca automática.
5. **Regla 5 — El Criterio de Kelly y el Techo de $\frac{1}{4}$ de Kelly (Vídeos #027 y #031):**
   * La fórmula matemática de Kelly para maximizar el crecimiento geométrico es:
     $$f^* = W - \frac{1 - W}{R}$$
   * **El Peligro del *Full Kelly*:** Con un buen sistema ($W = 55\%$, $R = 1.5$), el Kelly completo sugiere arriesgar $\approx 25\%$ del capital por operación, lo cual es un suicidio financiero ante cualquier racha normal de 4 pérdidas o error de estimación muestral.
   * **Regla Cuantitativa:** Si se activa dimensionamiento por Kelly, **jamás superar un cuarto ($\frac{1}{4}$) del Kelly teórico**, y **siempre acotado por debajo del $2.0\%$ absoluto**.
6. **Regla 6 — Dimensionamiento por Cola Izquierda (`CVaR` / Percentil 1 — Vídeos #014 y #063):**
   * En lugar de dimensionar la posición pensando en la pérdida media, se utiliza el **CVaR (*Conditional Value at Risk*)** o el **Percentil 1 ($P_1$)** de la distribución de pérdidas para garantizar que **3 días consecutivos de pérdida extrema de cola no inhabiliten la cuenta**.

---

## 2. Ingeniería de Carteras Multi-Bot (La Matemática de los *Hedge Funds*)

### A. La Fórmula de Varianza de una Cartera de Bots (Vídeo #016)
El riesgo total ($\sigma_p^2$) de una cuenta donde operan $N$ bots simultáneamente se descompone en dos bloques matemáticos:

$$\sigma_p^2 = \underbrace{\sum_{i=1}^{N} w_i^2 \sigma_i^2}_{\text{Bloque 1: Riesgo Propio}} + \underbrace{\sum_{i=1}^{N}\sum_{j \neq i}^{N} w_i w_j \sigma_i \sigma_j \rho_{ij}}_{\text{Bloque 2: Riesgo Cruzado (Correlación)}}$$

* **La Revelación Matemática:**
  * El **Bloque 1** (riesgo individual de cada bot) apenas se puede comprimir sin bajar el retorno.
  * Pero el **Bloque 2** está multiplicado íntegramente por el coeficiente de correlación $\rho_{ij}$ entre cada par de bots:
    * Si tienes 4 bots con $\rho = 1.0$ ("clones disfrazados"), la volatilidad y el *Drawdown* de la cartera es idéntico al de un solo bot. Has multiplicado tu trabajo por 4 para tener cero protección.
    * Si consigues que $\rho_{ij} \approx 0$ (o ligeramente negativa, ej. $\rho = -0.15$ como demuestra en el Vídeo #008, o $\bar{\rho} = 0.16$ en su cartera real de 32 bots del Vídeo #028), **el Bloque 2 casi desaparece**: el $95\%$ del riesgo vive aislado dentro de cada bot y el *Drawdown* conjunto se desploma a una fracción.

### B. Umbrales Numéricos de Correlación entre Bots (Vídeos #003, #016, #028)
* **Correlación ideal de cartera ($\bar{\rho}$):** Entre **$-0.20$ y $+0.20$** (en su cartera auditada de 32 bots que rindió un $37.31\%$ anualizado durante 60 meses frente al $11.90\%$ del S&P 500, la correlación media es de **$0.16$**).
* **Alerta de Par Redundante ("Gemelos Ocultos"):** Cuando dos bots —aunque operen en mercados distintos, ej. un *scalper* en `EURUSD` y otro en `SP500` (Vídeo #028)— presentan una **correlación $\rho > 0.50$** (y especialmente crítica si **$\rho > 0.70$**), están asumiendo el mismo riesgo el mismo día. Uno de los dos debe ceder peso o ser reemplazado.
* **Diferencia entre Correlación y Cointegración (Vídeo #003):**
  * **Correlación** mide si dos activos se mueven parecido hoy; dos activos pueden tener $\rho = 0.80$ y aun así divergir durante meses sin volver a juntarse.
  * **Cointegración** mide si el diferencial (*spread/residuo*) entre ambos es estacionario ("una goma elástica que vuelve a su media"). Además, **la correlación es dinámica**: en tardes de pánico o decisiones de Bancos Centrales, correlaciones históricas de $0.80$ se rompen abruptamente.

---

## 3. Arquitectura Macro de un Portfolio Profesional: Los 3 Bloques (Vídeo #028)

Para lograr una descorrelación real, una cartera no se construye juntando 10 bots del mismo estilo, sino combinando **4 clases de activos** (Cripto, Índices, Metales, Divisas) y **3 bloques estructurales opuestos**:

| Bloque de Cartera | Estilo de Bots | Perfil de Retorno (*Payoff*) | Función dentro del Portfolio |
| :--- | :--- | :--- | :--- |
| **1. Bloque Convexo** | Seguimiento de Tendencia y *Momentum* (ej. `DAX H1`, `XAUUSD H1`). | *"Pescadores de atún"*: Bajo *Win Rate* ($35\% - 45\%$), alto ratio $R:B$. Pasan semanas planos y capturan movimientos explosivos. | Generan los grandes saltos de capital y **protegen la cartera durante crisis y choques geopolíticos**. |
| **2. Bloque Cóncavo** | Reversión a la Media (`Z-Score`, RSI en rango, *Grid* dinámico con ATR). | *"La panadería del barrio"*: Alto *Win Rate* ($70\% - 87\%$), beneficio pequeño y constante por operación ($0.4R - 0.8R$). | Aportan **flujo de caja diario/semanal estable** mientras los mercados están en rango y los tendenciales sufren. |
| **3. Bloque Híbrido / Rotación** | Rupturas de volatilidad (*Breakout*), estacionalidad e intradía filtrado. | Equilibrado ($W \approx 50\% - 60\%$, $R \approx 1.5 - 2.0$). | Suaviza la transición entre regímenes laterales y tendenciales. |

> **Paradoja de la Cartera (Vídeo #016):** A menudo, añadir un bot con menor retorno absoluto (ej. en `EURUSD` o `BTC`) a tus dos bots estrella (`XAUUSD` y `SP500`) reduce ligeramente la rentabilidad bruta anual, pero **corta a la mitad el Drawdown y el CVaR**, permitiendo operar la cartera con mayor tranquilidad o mayor apalancamiento seguro.

---

## 4. El Secreto del Rebalanceo Sistemático y el Demonio de Shannon (Vídeo #008)

> *"La diversificación te da la volatilidad descorrelacionada; el rebalanceo es lo que la convierte en crecimiento compuesto en tu cuenta"* (Vídeo #008).

En el Vídeo #008 (*Why Your Bots Fail: The Secret to Systematic Rebalancing*), demuestra con pruebas fuera de muestra dos hallazgos fundamentales de ingeniería de carteras:
1. **La Prima de Rebalanceo (*Shannon's Demon*):** Si dejas tus bots en "parcelas fijas" aisladas sin mover capital entre ellos, pierdes la prima de rebalanceo. Al reasignar periódicamente el capital entre bots descorrelacionados ($\rho \le 0$), cosechas una prima matemática adicional de crecimiento compuesto.
2. **Por qué el reparto equiponderado ($1/N$) con rebalanceo suele vencer al "Reparto Óptimo" fuera de muestra:**
   * Cuando un optimizador prueba miles de combinaciones de pesos ($w_1, w_2, \dots, w_n$) sobre el histórico, sobreajusta los pesos al pasado (*estabilidad cero fuera de muestra*).
   * **Regla de Decisión (Vídeo #008):** Si el reparto optimizado no supera la prueba de estabilidad fuera de muestra, **aplica asignación equiponderada ($1/N$) con rebalanceo periódico**, que en las pruebas *Out-of-Sample* batió al "óptimo histórico" en más de $+1.5\%$ anual con menor fragilidad.

---

## 5. Protocolo Operativo de Mantenimiento de Cartera (El Calendario del Quant — Vídeo #028)

Un gestor cuantitativo dedica entre **15 y 30 minutos por semana** a su cartera siguiendo una cadencia estricta y **jamás apaga o modifica parámetros en caliente por una racha de 3 días**:

* **Cada Domingo (Semanal):**
  * Cargar el calendario de noticias macroeconómicas de alto impacto de la semana entrante en el filtro horario (*News Dodger*).
  * **Prohibido mirar la rentabilidad de la semana para tomar decisiones emocionales.**
* **Cada 15 Días (Quincenal — Sistema de Semáforos contra *Baseline*):**
  * Comparar las métricas rodantes de cada bot contra la línea base (*Baseline*) de su *backtest*:
    * **Semáforo Verde:** Dentro de los parámetros normales $\implies 100\%$ de su *sizing* asignado.
    * **Semáforo Amarillo (Desviación moderada):** Reducir automáticamente su *sizing* al **$50\%$**.
    * **Semáforo Rojo (Ruptura de bandas de Monte Carlo / `Z-Score` de anomalía):** Pausa del bot y envío a auditoría.
* **Primer Domingo de cada Mes (Mensual):**
  * Comparar cada bot con su *backtest* y cono de Monte Carlo.
  * **Rebalancear los bloques macro** si sus pesos se han desviado en **más de 10 puntos porcentuales**.
  * Revisar la matriz de correlaciones cruzadas.
* **Enero (Anual):**
  * Reestructuración anual del portfolio: retiro de pares redundantes ($\rho > 0.50$) y ascenso de nuevos bots que hayan completado los **6 meses / +50–100 operaciones de incubación en Demo**.

---

## 6. La Matemática Exacta para Superar Empresas de Fondeo (*Prop Firms* — Vídeos #005, #018, #051)

Ignacio Ayago advierte con crudeza sobre el modelo de negocio *B-Book* de muchas empresas de fondeo (que viven de las tarifas de exámenes suspendidos e imponen límites de *Drawdown* diario del 3 %–5 % y total del 8 %–10 %, llegando incluso a congelar cuentas si detectan operativas tóxicas — Vídeo #051).

Sin embargo, si se decide operar *challenges* de fondeo, explica que **la pregunta matemática cambia por completo** (Vídeos #005 y #018):

1. **Cuenta Propia vs. Challenge de Fondeo:**
   * En **cuenta propia**, la pregunta es: *¿Tiene esta estrategia esperanza matemática positiva a largo plazo?*
   * En un **challenge de fondeo**, la pregunta es un problema de **barrera de absorción estocástica**: ***¿Qué probabilidad tiene esta curva de tocar el $+10\%$ (objetivo) antes de tocar el $-5\%$ diario o $-10\%$ total (eliminación)?***
2. **Por qué la Varianza importa más que la Esperanza Matemática en un Fondeo (Vídeo #005):**
   * Dadas 3 estrategias con **exactamente la misma esperanza matemática positiva**:
     * **Estrategia A (Alto *Win Rate* $\ge 60\%$, baja varianza, curva suave):** Pasa el *challenge* en el **$77\%$ de las simulaciones**.
     * **Estrategia B (Equilibrada):** Pasa el **$58\%$ de las simulaciones**.
     * **Estrategia C (Bajo *Win Rate*, pocas ganadoras gigantes, alta varianza):** Solo pasa el **$46\%$ de las simulaciones** (porque una racha normal de pérdidas al inicio te expulsa por límite de *Drawdown* antes de que llegue el *home run*).
3. **La Regla Contraintuitiva del Riesgo en Fondeos (Vídeo #005):**
   * Arriesgar un $2\%$ por operación en un fondeo garantiza casi matemáticamente tocar el límite de pérdida diaria/máxima durante una racha adversa normal.
   * **Bajar el riesgo por operación al $0.25\% - 0.50\%$** multiplica drásticamente la probabilidad de supervivencia y superación del reto, aunque tarde más días en completarse.
4. **Los 3 Filtros Numéricos para un Bot de Fondeo (Vídeo #018):**
   * **Filtro 1:** Tasa de acierto consistente ($\ge 60\%$ si se busca baja varianza) sobre cientos de operaciones, o control estricto de racha máxima perdedora.
   * **Filtro 2:** Calibrar el lotaje dividiendo el límite de *Drawdown* permitido del *challenge* (con margen de seguridad) entre el **Drawdown en el Percentil 95 de Monte Carlo** del bot.
   * **Filtro 3:** Integrar los límites de la prueba (*Drawdown diario máximo*, *Drawdown total*, *Objetivo de beneficio*) como **nodos cortafuegos dentro del propio código del EA** (*Challenge Architect* — Vídeo #015) para que el bot cierre y bloquee la operativa del día antes de acercarse a la falta eliminatoria.
