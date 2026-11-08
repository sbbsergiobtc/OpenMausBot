# BOT_10: Auditoría de Estrategia Viral "83% Win Rate" (EMA 9/55/200 + MACD + Bollinger + RSI)

* **Fuente:** [Vídeo #032 — I Turned the Viral 83% Win Rate Trading Strategy Into a Bot (and Tested It)](https://www.youtube.com/watch?v=YiC9gmo2A4Q)
* **Activo de Prueba:** `EURUSD`
* **Reglas del Vídeo Viral:**
  * **Tendencia:** Para cortos, `EMA(9) < EMA(55) < EMA(200)` (inverso para largos).
  * **Gatillo:** Precio toca banda de Bollinger(20) contra tendencia + giro en pico del histograma MACD + filtro `RSI < 59` (cortos) / `RSI > 41` (largos).
  * **Riesgo:** Stop Loss entre `0.8%` y `0.9%` del precio; Take Profit muy corto.
* **Veredicto del Backtest Realista (con Spread Variable, Comisión y Slippage):**
  * **Win Rate Real:** **`91.2%`** (incluso superior al prometido).
  * **Profit Factor:** **`0.75` (PERDEDORA)**. Por cada dólar que pierde en su $8.8\%$ de fallos, solo recupera $0.75$ en su $91.2\%$ de aciertos.
  * **Resultado de Cuenta:** Cae de `10.000 €` a `~6.000 €` con rachas de 4 meses en pérdidas. Ejemplo de manual de por qué el *Win Rate* sin esperanza matemática positiva ni *Filter Cushion* (12–15 puntos sobre el *win rate* de equilibrio) es marketing engañoso.
