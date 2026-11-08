---
title: "Registro de Forward Test e Incubación Automatizada - AlgrokQuant"
date: "2026-11-08"
status: "VIGILANCIA 24/7 ACTIVA"
daemon: "algrokquant-forward-test.service"
monitored_strategies: 45
traffic_lights:
  green: 43
  amber: 2
  red: 0
graduated_count: 0
---

# Registro de Forward Test e Incubación en Tiempo Real (Snapshot 2026-11-08)

## 1. Estado General de la Flota en Incubación
El daemon `algrokquant-forward-test.service` ejecuta un bucle 24/7 con libro virtual aislado de \$1,000 USD/USDC por estrategia:
* **Estrategias en incubación continua:** 45 modelos auditados.
* **Semáforo del Guardián:**
  * **GREEN (43 modelos):** Operando con multiplicador $1.0x$ a $1.25x$. Desviación Z-Score $|Z| \le 1.5\sigma$ respecto al Cono Monte Carlo ($P_{05}\text{--}P_{95}$).
  * **AMBER (2 modelos):** Operando con multiplicador defensivo $0.50x$. Desviación $1.5\sigma < |Z| \le 2.0\sigma$.
  * **RED (0 modelos):** Ninguna estrategia pausada por rotura de cono.
* **Graduadas para Cuenta Real ($\ge 30$ trades):** 0 modelos (en fase de acumulación de trades iniciales).

---

## 2. Benchmark Fuera de Muestra (OOS Triple Book)
| Libro | Descripción | ROI Neto OOS | Max Drawdown EOD | Ratio Calmar | Clamps 40% TP |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Libro A** | Estrategias individuales sin filtro (100% autónomas) | $+85.17\%$ | $9.23\%$ | $9.23$ | 31 |
| **Libro B** | Portafolio Heurístico (Hurst, Shannon, Kaufman KER) | $+163.22\%$ | $7.68\%$ | $21.25$ | 25 |
| **Libro C** | **Double Q-Learning Tabular (10 Regímenes Canónicos)** | **$+191.28\%$** | **$7.79\%$** | **$24.55$** | **25** |

*Alfa Extra generado por Double Q-Learning vs. Heurístico:* **$+28.06\%$** neto.

---

## 3. Servicios y Daemons Activos
* `algrokquant-forward-test.service` (PID activo, bucle continuo multiactivo).
* `algrokquant-dashboard.service` (FastAPI Uvicorn en `:8080`, estado OK).
* `openmausbot.service` (Servicio core de mensajería y orquestación, estado OK).

---

## 4. Próximo Hito en Roadmap a Medio Plazo
* **Hito:** Opción 3 · Pasarela de Despliegue Real para Estrategias Graduadas (*Real Execution Bridge*).
* **Condición de Disparo:** Conteo $\ge 30$ trades en verde dentro del Cono Monte Carlo ($P_{05}\text{--}P_{95}$) con veredicto `GRADUATED_FOR_REAL_ACCOUNT`.
* **Especificación Completa:** Véase [`ROADMAP.md`](file:///C:/Users/Sergio/Documents/Antigravity/OpenMausBot/ROADMAP.md) y [`library/ROADMAP.md`](file:///C:/Users/Sergio/Documents/Antigravity/OpenMausBot/library/ROADMAP.md).

