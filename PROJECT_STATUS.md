# 🤖 OpenMausBot & AlgrokQuant — Estado del Proyecto & Registro de Sesión

**Última Actualización:** 2026-10-21 17:30 UTC  
**Estado General:** Plataforma **OpenMausBot** y enjambre **AlgrokQuant** en producción y operativa continua en el servidor VPS de Contabo (`169.58.230.132`). Todos los archivos, dependencias, estrategias, diario de operaciones y configuraciones han sido analizados, consolidados y persistidos tanto en Git local como en Git remoto del VPS con copias de seguridad de seguridad activas.

---

## 📌 1. Resumen Ejecutivo de la Auditoría y Persistencia

1. **Persistencia y Control de Versiones Dual (Local + VPS):**
   - **Workspace Local (`OpenMausBot/`):**
     - Rama: `algrokquant-fleet` limpia y al día.
     - Commit: `f19e79fac` (*feat(algrokquant): consolidar arquitectura, bots, spec definitiva y scripts de administracion VPS*).
     - Añadidos `.gitignore` para grabaciones y cachés, especificación completa [`docs/ALGROKQUANT_SPEC.md`](docs/ALGROKQUANT_SPEC.md) y conjunto de scripts de administración en `scripts/`.
   - **Servidor VPS (`/root/AlgrokQuant/`):**
     - Repositorio Git inicializado y persistido con éxito (Commit `fd3fb60`: *177 archivos consolidados*).
     - Copias de seguridad automáticas de OpenMausBot generadas:
       - `/root/.openmausbot/bots.json.backup_20261021_172906`
       - `/root/.openmausbot/sessions.json.backup_20261021_172906`

2. **Infraestructura y Servicios en el VPS (`169.58.230.132`):**
   - **4 Servicios Systemd Activos al 100%:**
     - `openmausbot.service` (`active (running)`) — Orquestador de agentes y proxy TLS Caddy (`https://169.58.230.132.sslip.io`).
     - `traidinghub.service` (`active (running)`) — Dashboard central en puerto 8501.
     - `traidinghub-bot.service` (`active (running)`) — Bot interactivo de Telegram del Hub.
     - `traidinghub-incubator.service` (`active (running)`) — Minería y backtesting 24/7.
   - **Recursos del Sistema:**
     - RAM: 2.3 GiB usados de 7.8 GiB (5.4 GiB disponibles, uso muy holgado).
     - Swap: 4.0 GiB configurados en `/swapfile` (768 KiB usados).
     - Disco NVMe: 17 GB usados de 96 GB (79 GB libres, 18% ocupación).

3. **Pila de Dependencias Cuantitativas Global:**
   - Wrappers activos en `/usr/local/bin/python3`, `/usr/local/bin/python`, `/usr/local/bin/pip`.
   - Verificado: `vectorbt 1.2.0`, `numba 0.68.0`, `ccxt 4.5.89`, `pandas 3.0.6`, `scipy 1.18.1`, `hyperliquid-python-sdk 0.24.0`, `python-telegram-bot 22.8`, `pyyaml`.

4. **Ecosistema AlgrokQuant Desplegado en el VPS (`/root/AlgrokQuant/`):**
   - **Estrategias Codificadas y Backtesteadas (16 estrategias):**
     - `strat_001` a `strat_016` implementadas con VectorBT en `strategies/fast/`.
     - Estrategia insignia activa para paper: `strat_010_eth_btc_pairs_vbt.py` y ejecutor en vivo `strategies/live_paper/strat_010_pairs_paper_runner.py`.
   - **Motor de Decisiones JEV:**
     - Arquitectura modular implementada en `/root/AlgrokQuant/jev/`: `market_data.py`, `feature_engine.py`, `models.py`, `decision_layer.py`, `risk_engine.py`, `execution_layer.py`, `orchestrator.py`.
   - **Biblioteca Obsidian (`/root/AlgrokQuant/library/`):**
     - `00_INDICE_OBSIDIAN.md` y `00_MANIFIESTO_Y_ESPECIFICACION.md`.
     - Plantillas operativas en `templates/`: `Strategy_Card.md`, `Trade_Journal.md`, `Lesson.md`.
     - Fichas técnicas de ideas en `ideas/` (009 a 017).
     - Auditorías estadísticas en `audit/` (Auditor, Risk y Skeptic para Strat 010 y 014).
     - Lecciones aprendidas en `lessons/` (001 a 004: fricción de comisiones, asimetría de mean reversion, whipsaws).
     - Informes y rendimiento en `performance/`.
   - **Telemetría y Paper Trading:**
     - Estado de cuenta y registros en `data/paper_trades/account_state.json` y `trades_history.json`.
     - Datos históricos procesados en `data/processed/` (BTC, ETH, SOL en 15m y 1h).

---

## 🌐 2. Resumen de Estado del Enjambre (OpenMausBot)

| Agente | Rol | Modelo | Estado |
| :--- | :--- | :--- | :--- |
| **Nexus** | Desk Lead & Chief of Staff | `gemini-3.8-flash-high` | **Online / Activo** |
| **Ideator** | Generador de Alfas | `gemini-3.8-flash-high` | **Online / Activo** |
| **CoderQuant** | Desarrollador Quant | `gemini-3.8-flash-high` | **Online / Activo** |
| **Auditor** | Auditor de Robustez | `gemini-3.8-flash-high` | **Online / Activo** |
| **RiskFilter** | Gestor de Riesgo y Sizing | `gemini-3.8-flash-high` | **Online / Activo** |
| **Skeptic** | Destructor de Sesgos | `gemini-3.8-flash-high` | **Online / Activo** |
| **ExecCrypto** | Ejecutor Paper Hyperliquid | `gemini-3.8-flash-high` | **Online / Activo** |

---

## 🛠️ 3. Comandos Rápidos de Verificación

```powershell
# En PC (PowerShell): Estado Git local
git status

# Generar enlace de emparejamiento para móvil o nuevo PC:
python scripts/pair_vps.py
```

```bash
# En el VPS (SSH):
cd /root/AlgrokQuant && git status
systemctl is-active openmausbot traidinghub traidinghub-bot traidinghub-incubator
python3 -c "import vectorbt, ccxt, pandas; print('Stack OK')"
```
