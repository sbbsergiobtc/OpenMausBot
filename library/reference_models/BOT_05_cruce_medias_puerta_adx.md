# BOT_05: Cruce de Medias + Puerta de Régimen ADX(14) > 25

* **Fuente:** [Vídeo #006 — 35,766 Gold Candles: The Backtest That Separates Winning From Blowing Up](https://www.youtube.com/watch?v=rAk0eqFnkp4)
* **Activo de Prueba:** `XAUUSD` (Oro) | **Timeframe:** `H1` (31 Ago 2020 – 7 Sep 2026, 35.766 velas)
* **Arquitectura:**
  * **Motor de Señal:** Cruce simple de medias móviles.
  * **Puerta de Régimen (`AND`):** Nodo `ADX(14) > 25` conectado como puerta de permiso antes de la orden.
* **Comparativa Directa (Efecto Aislado del Filtro de Régimen):**
  * **Sin Puerta ADX:** Beneficio Neto `-$1.271` | Profit Factor `0.60` | Win Rate `24.1%` | Expectancia `-$118.06/trade` | Max DD `102.71%`.
  * **Con Puerta `ADX(14) > 25`:** Beneficio Neto **`+$27.236` (`+272.36%`)** | Profit Factor **`1.58`** | Win Rate **`45.8%`** | Expectancia **`+$121.05/trade`** | Max DD **`24.41%`**.
