# BOT_07: VWAP Banda 3 + Filtro de Régimen (Reversivo Volátil)

* **Fuente:** [Vídeo #018 — This is how I backtested the VWAP Drift Pullback live, without code](https://www.youtube.com/watch?v=JVCoXEPVD9I)
* **Reglas de la Estrategia Original (Viral):**
  * Entrada cuando el precio rompe al alza la banda inferior de nivel 3 del `VWAP`.
* **Auditoría Cuantitativa:**
  * **Sin Filtro de Régimen:** Fracaso absoluto en *backtest* honesto (**Profit Factor `0.15`**, rentabilidad negativa a pesar de tener un *Win Rate* del `52.7%`).
  * **Corrección Cuantitativa:** Conectar a la salida del cruce del `VWAP` el **Nodo de Filtro de Régimen de 5 Estados**, habilitando las señales **únicamente en el estado `Reversivo Volátil`** y separando estrictamente el periodo *In-Sample* (2020–2024) del *Out-of-Sample* (2025–2026).
