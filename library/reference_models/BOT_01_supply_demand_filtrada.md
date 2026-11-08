# BOT_01: Oferta y Demanda con Doble Filtro (Tendencia + Ventana Londres/NY)

* **Fuente:** [Vídeo #001 — I Turned the 79% Win Rate Supply and Demand Strategy Into a Bot](https://www.youtube.com/watch?v=eTty1NzZI8A)
* **Activo de Prueba:** `XAUUSD` (Oro) | **Timeframe:** `H1` (6 años de histórico)
* **Reglas de Entrada:**
  1. Detección objetiva de zona de Oferta/Demanda tras vela de desplazamiento + brecha de valor (FVG) + ruptura de estructura (BOS).
  2. **Filtro 1 (Tendencia Estructural):** Solo comprar en zona de demanda si la cadena de *swings* es alcista (máximos y mínimos crecientes); solo vender en oferta si la estructura es bajista.
  3. **Filtro 2 (Ventana Horaria):** Habilitado únicamente en sesiones de alta liquidez (**Londres y Nueva York**).
* **Resultado de Auditoría Cuantitativa:**
  * **Profit Factor:** `1.79` (Consistente ante fricción por ser estilo *Swing*).
  * **Max Drawdown Histórico:** `23.98%`.
  * **Veredicto Monte Carlo:** **Frágil** (`Drawdown P95 > 35%`), requiere ajuste de riesgo o filtro de volatilidad antes de pasar a Demo.
