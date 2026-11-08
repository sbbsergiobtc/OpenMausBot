# BOT_03: Cesta de Arbitraje Estadístico y Cointegración Forex (Water & Oil)

* **Fuente:** [Vídeo #003 — Forex Arbitrage: The Live Trading Dashboard You Need to See](https://www.youtube.com/watch?v=ihg7YdDExGU)
* **Activos:** Cesta multi-divisa (Pares mayores y cruces AUD/NZD/EUR/CHF/USD) | **Timeframes:** Ponderación simultánea en `M1`, `M5`, `M15`, `H1` y `H4`.
* **Lógica Cuantitativa:**
  1. Mide fuerza relativa y divergencia de cada divisa **normalizada por su propia volatilidad (ATR)** (nunca en pips brutos).
  2. Distingue entre **Correlación** (parecido temporal) y **Cointegración** (residuo estacionario tipo goma elástica).
  3. **Filtro de Régimen de Cesta:** Se silencia en 2 de los 3 estados (Tendencia Desbocada y Mezcla ruidosa) y solo opera en estado de **Reversión limpia**, fuera de ventanas de Bancos Centrales (RBA, RBNZ, FED, BCE).
  4. **Filtro de Peaje Real:** Verifica que la expectativa de convergencia supere ampliamente el coste combinado de *Spread* de entrada/salida, comisión y *Swap* de todas las patas.
