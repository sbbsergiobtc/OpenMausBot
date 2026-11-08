# BOT_08: Smart Money Concepts (SMC) Institucional con 7 Filtros Booleanos

* **Fuente:** [Vídeo #019 — The Secret to Turning Any SMC Setup into a Profitable Trading Bot](https://www.youtube.com/watch?v=AytFCULDyDM) y [Vídeo #035](https://www.youtube.com/watch?v=WnXfqXff7aY)
* **Los 7 Filtros Programables Obligatorios:**
  1. **Liquidez Relevante:** Barrido del máximo/mínimo de al menos las últimas **20 velas** (o `EQH/EQL`).
  2. **Barrido Limpio:** Cierre de vuelta dentro del nivel o permanencia $\le 3$ velas al otro lado.
  3. **Desplazamiento Violento:** Vela de ruptura con rango $\ge 1.5 \times \text{ATR}(14)$ y cuerpo $\ge 70\%$ del rango total.
  4. **Ruptura de Estructura (BOS/MSS):** Cierre confirmado más allá del último *swing* validado.
  5. **Filtro de Tamaño de FVG y OB:** El *Fair Value Gap* debe estar pegado al *Order Block* con anchura mínima respecto al ATR; descartar OBs microscópicos ($<5$ pips en M5) o gigantes ($>50$ puntos).
  6. **Zona Virgen:** El *Order Block* no puede haber sido tocado/mitigado previamente.
  7. **Ventana Horaria:** Solo sesiones principales (Londres / Nueva York).
* **Resultado de Auditoría:**
  * Reduce el ruido a solo las operaciones de alta asimetría: **Profit Factor `2.92`**, Retorno **`+89.28%` (`+$8.928`)**, con un **Win Rate de solo el `16.9%`** compensado por un **Ratio R:B medio de `14:1`**.
