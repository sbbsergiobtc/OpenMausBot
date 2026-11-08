# BOT_02: Reversión a la Media Estadística con Z-Score (20 Periodos)

* **Fuente:** [Vídeo #002 — Testing my live trading bot: Did it pass the test?](https://www.youtube.com/watch?v=q_gQDfAIqGY)
* **Activo de Prueba:** Multi-Activo | **Timeframe:** `H1`
* **Fórmula Base:**
  $$Z = \frac{\text{Close} - \text{SMA}(\text{Close}, 20)}{\text{StdDev}(\text{Close}, 20)}$$
* **Reglas Operativas:**
  * **Entrada Larga:** $Z < -2.0$ (desviación estadística extrema inferior).
  * **Salida Normal (Take Profit):** Regreso a la media ($Z \ge 0.0$).
  * **Salida de Emergencia (Stop Loss de Ruptura de Régimen):** $Z < -4.0$.
  * **Gestión Monetaria:** Tamaño de lote dinámico para arriesgar el `1.0%` de la cuenta si salta el cierre de emergencia.
