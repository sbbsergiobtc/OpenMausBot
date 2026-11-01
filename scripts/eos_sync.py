import sys
import paramiko
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

vps_script = """import pathlib, os, json
from datetime import datetime, timezone

now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

# 1. Eliminar scripts temporales en scripts/
scripts_to_remove = [
    'cat_phase3.py', 'check_078_079.py', 'check_cards.py', 'check_forward_count.py',
    'check_reports.py', 'check_switch_desk.py', 'check_top_prop.py', 'deep_audit_discarded.py',
    'deploy_recovered_strategies.py', 'e2e_check.py', 'find_audit_scripts.py', 'inspect_audits.py',
    'patch_backend_remote.py', 'patch_html_remote.py', 'read_cards_detail.py',
    'retest_all_prop_candidates.py', 'retest_prop_candidates.py', 'update_grid_cards.py',
    'vps_check_8080.py'
]
scripts_dir = pathlib.Path('/root/AlgrokQuant/scripts')
for s in scripts_to_remove:
    p = scripts_dir / s
    if p.exists():
        p.unlink()
        print(f"Removed temp script: {s}")

# 2. Crear LESSON-20261101-020
lesson_content = f\"\"\"# LESSON-20261101-020: Calibración Dual de Robustez en Monte Carlo, Regla Suprema EOD Drawdown y Auto-Deploy

**Fecha:** 1 de Noviembre de 2026  
**Autor:** Sergio & Desk Lead Nexus (AlgrokQuant)  
**Gobernanza:** LESSON-017 / LESSON-018 / Norma Mandatoria Oficial  

---

### 1. Regla Suprema de Fondeo: Exclusivamente End of Day Drawdown (EOD)
- **Prohibición de Trailing Drawdown:** Queda estrictamente prohibido asumir, mencionar o calcular drawdown intra-trade o trailing intradía continuo.
- Sergio **ÚNICAMENTE** opera cuentas bajo **END OF DAY DRAWDOWN (EOD)** calculado al cierre oficial de sesión.
- Ninguna fluctuación intra-trade mueve la marca de agua del drawdown de la cuenta.

### 2. Calibración de Monte Carlo en Cuentas de Fondeo (IC >= 70%)
- Exigir un 100% de tasa de pase (cero fallos) en simulaciones de Monte Carlo ante barreras asimétricas (4% pérdida vs 8% objetivo) es una **falacia probabilística y causa sobreajuste letal**.
- La robustez en prop firms se calibra exigiendo una **tasa de pase empírica en Monte Carlo >= 70%** (3 de cada 4 cuentas simuladas aprueban el challenge).
- Con un payout medio de 4x a 8x el coste de la evaluación, un 70%-75% de pase garantiza una **esperanza matemática (EV) masivamente positiva**.

### 3. Segmentación por Vehículo Operativo
- **Cuentas de Futuros (CME / Topstep / Apex / Tradovate):** Drawdown máximo estricto de **3.0% a 4.0% END OF DAY (EOD)**.
- **Cuentas de CFDs / Forex (FTMO, The Funded Trader, IC Markets Prop):** Drawdown máximo de **8.0%**.
- **Cuentas de Capital Propio:** Se mantienen **sin cambios** (preservación estricta de capital: Max DD continuo <= 20.0%, alerta -10.0%, Sharpe >= 1.50, Retorno Anualizado >= 30.0%, probabilidad de ruina del 0.0%).

### 4. Auto-Deploy Oficial con Balance Base de $1.000 USD
- Toda estrategia aprobada por los 6 agentes (@StratFinder, @Ideator, @CoderQuant, @Auditor, @Skeptic y @RiskFilter) se añade directamente a Forward Test en vivo con libro contable virtual de **$1.000 USD/USDC**.
- Se han desplegado y activado 6 estrategias híbridas formales en el Cockpit Forward Test con fichas técnicas completas en `/library/strategies/`.
\"\"\"

lesson_file = pathlib.Path('/root/AlgrokQuant/library/lessons/LESSON-20261101-020_CALIBRACION_DUAL_ROBUSTEZ_EOD_Y_AUTO_DEPLOY.md')
lesson_file.write_text(lesson_content, encoding='utf-8')
print("Created LESSON-20261101-020 successfully.")

# 3. Actualizar library/journal/PROP_FIRM_SPRINT_JOURNAL.md
journal_file = pathlib.Path('/root/AlgrokQuant/library/journal/PROP_FIRM_SPRINT_JOURNAL.md')
journal_entry = f\"\"\"

---

## [2026-11-01 22:10 UTC] Cierre de Sesión Oficial: Optimización Pipeline, Regla EOD y Despliegue Híbrido

### 1. Directivas Consolidadas
- **Regla Suprema EOD:** Cuentas de fondeo operan exclusivamente bajo End of Day Drawdown (EOD). Trailing drawdown prohibido.
- **Calibración Dual Monte Carlo:** Tasa de pase >= 70% en Monte Carlo para cuentas de fondeo (Futuros 3-4% EOD DD, CFDs 8% EOD DD). Capital propio sin cambios.
- **Auto-Deploy Activo:** 6 estrategias híbridas formales auto-desplegadas con balance base de $1.000 USD virtuales c/u.

### 2. Roster de Estrategias Híbridas en Forward Test (Cockpit Activo)
1. `HYB-NDX-BOL-LINE-48-2.5-3.0` (Futuros CME · 4% EOD DD · Sharpe 7.25 · $1.000 USD)
2. `HYB-NDX-BOL-LINE-48-2.5-4.0` (Futuros CME · 4% EOD DD · Sharpe 7.25 · $1.000 USD)
3. `HYB-NDX-BOL-LINE-48-2.5-2.0` (Futuros CME · 4% EOD DD · Sharpe 7.24 · $1.000 USD)
4. `HYB-NDX-BOL-OFI-48-2.5-2.0-CFD` (CFDs FTMO/IC · 8% EOD DD · Sharpe 1.71 · $1.000 USD)
5. `HYB-NDX-BOL-LINE-48-2.0-3.0` (Futuros + CFDs · SL 2.0 · Sharpe 7.40 · $1.000 USD)
6. `HYB-NDX-BOL-LINE-48-2.0-4.0` (Futuros + CFDs · SL 2.0 · Sharpe 7.40 · $1.000 USD)

### 3. Estado de Servicios y Telemetría
- `algrokquant-forward-test.service`: ACTIVO (Running)
- `algrokquant-dashboard.service`: ACTIVO (Running en puerto 8080)
- `openmausbot.service`: ACTIVO (Running)
\"\"\"
with open(journal_file, "a", encoding="utf-8") as f:
    f.write(journal_entry)
print("Updated PROP_FIRM_SPRINT_JOURNAL.md.")

# 4. Actualizar library/00_INDICE_OBSIDIAN.md si existe
indice_file = pathlib.Path('/root/AlgrokQuant/library/00_INDICE_OBSIDIAN.md')
if indice_file.exists():
    txt = indice_file.read_text(encoding='utf-8')
    if 'LESSON-20261101-020' not in txt:
        txt += "\\n- [[LESSON-20261101-020_CALIBRACION_DUAL_ROBUSTEZ_EOD_Y_AUTO_DEPLOY|LESSON-020: Calibración Dual Monte Carlo EOD y Auto-Deploy]]\\n"
        indice_file.write_text(txt, encoding='utf-8')
        print("Updated 00_INDICE_OBSIDIAN.md.")
"""

sftp = ssh.open_sftp()
with sftp.file('/root/AlgrokQuant/scripts/end_of_session_sync.py', 'w') as f:
    f.write(vps_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /root/AlgrokQuant/scripts/end_of_session_sync.py && rm -f /root/AlgrokQuant/scripts/end_of_session_sync.py')
print(stdout.read().decode('utf-8', errors='replace'))
print('STDERR:', stderr.read().decode('utf-8', errors='replace'))
ssh.close()
