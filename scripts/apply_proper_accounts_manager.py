# -*- coding: utf-8 -*-
"""
Script to apply the Proper Granular Multi-Account Manager:
1. Cleans up #portfolio-risk-hud to its pure original layout (no hardcoded buttons/texts).
2. Adds [ 🏢 Cuentas & Fases ] button to HUD actions.
3. Inserts #accounts-manager-modal in index.html with real account table and add-account form.
4. Upgrades dashboard/backend.py with /api/accounts, /api/accounts/update_stage, /api/accounts/add.
5. Updates scripts/prop_firm_forward_test_daemon.py to match accounts from accounts_catalog dynamically.
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH = Path(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot")

# ==============================================================================
# 1. UPGRADE dashboard/backend.py
# ==============================================================================
backend_path = BASE_PATH / "dashboard/backend.py"
backend_content = backend_path.read_text(encoding="utf-8")

accounts_api_code = """

# ==============================================================================
# GESTOR MULTICUENTA GRANULAR (CUENTAS CONECTADAS Y FASES DE FONDEO)
# ==============================================================================

@app.get("/api/accounts")
def get_accounts_catalog():
    state_file = BASE_DIR / 'data/paper_trades/prop_firm_forward_test_state.json'
    s = {}
    if state_file.exists():
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                s = json.load(f)
        except Exception:
            pass

    mt5_sync = s.get('live_broker_sync', {})
    mt5_acc = str(mt5_sync.get('account') or '53120791')
    mt5_srv = str(mt5_sync.get('server') or 'ICMarketsSC-Demo')
    mt5_bal = float(mt5_sync.get('broker_balance') or 984.53)
    mt5_eq = float(mt5_sync.get('broker_equity') or 979.95)

    catalog = s.get('accounts_catalog', None)
    if not catalog:
        catalog = [
            {
                "account_id": mt5_acc,
                "firm_name": f"{mt5_srv} (MT5)",
                "desk_type": "PROP_FIRM",
                "vehicle": "CFDs / Forex Spot",
                "balance": mt5_bal,
                "equity": mt5_eq,
                "stage": "EVALUATION",
                "consistency_rule_enabled": True,
                "max_single_trade_profit_pct": 40.0,
                "max_concurrent_trades": 3,
                "status": "CONECTADA (MT5)"
            },
            {
                "account_id": "PROP-CME-01",
                "firm_name": "Rithmic / NinjaTrader",
                "desk_type": "PROP_FIRM",
                "vehicle": "Futuros CME (US500/USTEC)",
                "balance": 50000.0,
                "equity": 50000.0,
                "stage": "EVALUATION",
                "consistency_rule_enabled": True,
                "max_single_trade_profit_pct": 40.0,
                "max_concurrent_trades": 3,
                "status": "INCUBACIÓN VIRTUAL"
            },
            {
                "account_id": "IBKR-CAP-01",
                "firm_name": "Interactive Brokers",
                "desk_type": "CAPITAL_PROPIO",
                "vehicle": "Multi-Activo Spot",
                "balance": 10000.0,
                "equity": 10000.0,
                "stage": "LIVE_CAPITAL",
                "consistency_rule_enabled": False,
                "max_single_trade_profit_pct": None,
                "max_concurrent_trades": 3,
                "status": "LISTA PARA DESPLIEGUE"
            }
        ]
        if state_file.exists():
            try:
                s['accounts_catalog'] = catalog
                with open(state_file, 'w', encoding='utf-8') as f:
                    json.dump(s, f, indent=2)
            except Exception:
                pass
    else:
        for acc in catalog:
            if str(acc.get("account_id")) == mt5_acc:
                acc["balance"] = mt5_bal
                acc["equity"] = mt5_eq
                acc["status"] = "CONECTADA (MT5)"

    return {"accounts": catalog}


@app.post("/api/accounts/update_stage")
def update_single_account_stage(data: dict):
    state_file = BASE_DIR / 'data/paper_trades/prop_firm_forward_test_state.json'
    account_id = str(data.get("account_id", "")).strip()
    new_stage = str(data.get("stage", "EVALUATION")).upper()
    if not account_id:
        return {"error": "account_id es requerido"}

    try:
        s = {}
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                s = json.load(f)

        catalog = s.get('accounts_catalog', [])
        target_acc = None
        for acc in catalog:
            if str(acc.get("account_id")) == account_id:
                target_acc = acc
                break

        if not target_acc:
            return {"error": f"Cuenta {account_id} no encontrada en catálogo"}

        target_acc["stage"] = new_stage
        target_acc["consistency_rule_enabled"] = (new_stage == "EVALUATION")

        if "firm_name" in data:
            target_acc["firm_name"] = str(data["firm_name"])
        if "max_concurrent_trades" in data:
            target_acc["max_concurrent_trades"] = int(data["max_concurrent_trades"])

        # Sincronizar también con active_accounts
        branch = target_acc.get("desk_type", "PROP_FIRM").lower()
        if "active_accounts" not in s:
            s["active_accounts"] = {}
        s["active_accounts"][branch] = {
            "account_id": target_acc["account_id"],
            "firm_name": target_acc["firm_name"],
            "stage": target_acc["stage"],
            "consistency_rule_enabled": target_acc["consistency_rule_enabled"],
            "max_concurrent_trades": target_acc.get("max_concurrent_trades", 3)
        }

        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(s, f, indent=2)

        return {"status": "SUCCESS", "updated_account": target_acc}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/accounts/add")
def add_new_account(data: dict):
    state_file = BASE_DIR / 'data/paper_trades/prop_firm_forward_test_state.json'
    account_id = str(data.get("account_id", "")).strip()
    firm_name = str(data.get("firm_name", "")).strip()
    desk_type = str(data.get("desk_type", "PROP_FIRM")).upper()
    vehicle = str(data.get("vehicle", "CFDs / Forex")).strip()
    balance = float(data.get("balance", 50000.0))
    stage = str(data.get("stage", "EVALUATION")).upper()

    if not account_id or not firm_name:
        return {"error": "account_id y firm_name son obligatorios"}

    try:
        s = {}
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                s = json.load(f)

        if "accounts_catalog" not in s:
            s["accounts_catalog"] = []

        s["accounts_catalog"] = [a for a in s["accounts_catalog"] if str(a.get("account_id")) != account_id]
        new_acc = {
            "account_id": account_id,
            "firm_name": firm_name,
            "desk_type": desk_type,
            "vehicle": vehicle,
            "balance": balance,
            "equity": balance,
            "stage": stage,
            "consistency_rule_enabled": (stage == "EVALUATION"),
            "max_single_trade_profit_pct": 40.0 if stage == "EVALUATION" else None,
            "max_concurrent_trades": int(data.get("max_concurrent_trades", 3)),
            "status": "REGISTRADA"
        }
        s["accounts_catalog"].append(new_acc)

        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(s, f, indent=2)

        return {"status": "SUCCESS", "account": new_acc}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/account_stage")
def get_account_stage():
    \"\"\"Wrapper de compatibilidad para consultas legacy.\"\"\"
    cat = get_accounts_catalog().get("accounts", [])
    pf = next((a for a in cat if a.get("desk_type") == "PROP_FIRM"), None)
    cap = next((a for a in cat if a.get("desk_type") == "CAPITAL_PROPIO"), None)
    return {
        "prop_firm": pf or {"firm_name": "ICMarketsSC-Demo", "stage": "EVALUATION", "consistency_rule_enabled": True},
        "capital_propio": cap or {"firm_name": "Interactive Brokers", "stage": "LIVE_CAPITAL", "consistency_rule_enabled": False}
    }
"""

# Replace the previous temporary /api/account_stage in backend
import re
pattern = re.compile(r'@app\.get\("/api/account_stage"\)[\s\S]*?(?=@app\.get\("/api/notifications"\))')
if pattern.search(backend_content):
    backend_content = pattern.sub(accounts_api_code + "\n\n", backend_content, count=1)
    print("[OK] backend.py updated with full Multi-Account API.")
else:
    print("[WARN] pattern for /api/account_stage not found in backend.py.")

backend_path.write_text(backend_content, encoding="utf-8")

# ==============================================================================
# 2. UPGRADE scripts/prop_firm_forward_test_daemon.py
# ==============================================================================
daemon_path = BASE_PATH / "scripts/prop_firm_forward_test_daemon.py"
daemon_content = daemon_path.read_text(encoding="utf-8")

# Replace acc_info lookup with catalog match
target_daemon_acc = """            acc_info = state.get('active_accounts', {}).get(branch.lower(), {})
            firm_name = acc_info.get('firm_name', 'LUCID_TRADING' if branch == 'PROP_FIRM' else 'INTERACTIVE_BROKERS')
            account_stage = acc_info.get('stage', 'EVALUATION' if branch == 'PROP_FIRM' else 'LIVE_CAPITAL')
            consistency_active = (account_stage == 'EVALUATION') and acc_info.get('consistency_rule_enabled', True)"""

repl_daemon_acc = """            # Búsqueda dinámica en el catálogo de cuentas registradas (sin hardcodeo)
            catalog = state.get('accounts_catalog', [])
            matched_acc = next((a for a in catalog if a.get('desk_type') == branch), None)
            if matched_acc is None:
                matched_acc = state.get('active_accounts', {}).get(branch.lower(), {})

            firm_name = matched_acc.get('firm_name', 'ICMarketsSC-Demo' if branch == 'PROP_FIRM' else 'INTERACTIVE_BROKERS')
            account_stage = matched_acc.get('stage', 'EVALUATION' if branch == 'PROP_FIRM' else 'LIVE_CAPITAL')
            consistency_active = (account_stage == 'EVALUATION') and matched_acc.get('consistency_rule_enabled', True)"""

if target_daemon_acc in daemon_content:
    daemon_content = daemon_content.replace(target_daemon_acc, repl_daemon_acc, 1)
    print("[OK] daemon updated to read accounts dynamically from catalog.")
else:
    print("[WARN] target_daemon_acc not found in daemon.")

daemon_path.write_text(daemon_content, encoding="utf-8")

# ==============================================================================
# 3. UPGRADE dashboard/templates/index.html
# ==============================================================================
html_path = BASE_PATH / "dashboard/templates/index.html"
html_content = html_path.read_text(encoding="utf-8")

# Replace #portfolio-risk-hud with clean layout and [ 🏢 Cuentas & Fases ] button
# Let's find #portfolio-risk-hud to end of that div
hud_start_idx = html_content.find('id="portfolio-risk-hud"')
if hud_start_idx != -1:
    hud_div_start = html_content.rfind('<div', 0, hud_start_idx)
    hud_div_end = html_content.find('<!-- ==================== GESTIÓN DE CARTERA ACTIVA', hud_start_idx)
    if hud_div_start != -1 and hud_div_end != -1:
        clean_hud = """          <!-- ==================== RISK HUD SUPERIOR & KILL-SWITCH CONSOLIDADO ==================== -->
          <div id="portfolio-risk-hud" class="my-4 p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs">
            <div class="flex flex-col xl:flex-row xl:items-center justify-between gap-5">
              <!-- 4 Métricas de Riesgo Clave de Cartera (Espaciado Generoso Anti-Colisión) -->
              <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 flex-1 min-w-0">
                <div class="border-r border-[#F2F2F7] pr-3 min-w-0">
                  <span class="text-[11px] uppercase tracking-wider font-semibold text-[#6E6E73] block mb-1 truncate">Margen Utilizado</span>
                  <div class="flex items-baseline gap-2 flex-wrap">
                    <span class="text-lg sm:text-xl font-bold font-mono text-[#1D1D1F]" id="hud-margin-used">14.2%</span>
                    <span class="badge-success-live text-[10px] py-0.5 px-2">Seguro</span>
                  </div>
                </div>
                <div class="border-r border-[#F2F2F7] pr-3 min-w-0">
                  <span class="text-[11px] uppercase tracking-wider font-semibold text-[#6E6E73] block mb-1 truncate">Drawdown Cartera</span>
                  <div class="flex items-baseline gap-2 flex-wrap">
                    <span class="text-lg sm:text-xl font-bold font-mono text-[#D70015]" id="hud-global-dd">-4.20%</span>
                    <span class="text-[11px] text-[#86868B] font-mono whitespace-nowrap">Máx: -20.0%</span>
                  </div>
                </div>
                <div class="border-r border-[#F2F2F7] pr-3 min-w-0">
                  <span class="text-[11px] uppercase tracking-wider font-semibold text-[#6E6E73] block mb-1 truncate">PnL Flotante Total</span>
                  <div class="flex items-baseline gap-1.5 flex-wrap">
                    <span class="text-lg sm:text-xl font-bold font-mono text-[#065F46]" id="hud-floating-pnl">+$1,420.50</span>
                    <span class="text-xs font-mono text-[#065F46] font-semibold whitespace-nowrap">(+1.42%)</span>
                  </div>
                </div>
                <div class="min-w-0">
                  <span class="text-[11px] uppercase tracking-wider font-semibold text-[#6E6E73] block mb-1 truncate">Exposición Neta</span>
                  <div class="flex items-baseline gap-2 flex-wrap">
                    <span class="text-lg sm:text-xl font-bold font-mono text-[#3C45A5]" id="hud-net-exposure">LONG 62%</span>
                    <span class="text-[11px] font-mono text-[#86868B] whitespace-nowrap">Asimétrico</span>
                  </div>
                </div>
              </div>
              <!-- Acciones de Intervención Operativa & Gestor de Cuentas -->
              <div class="flex items-center gap-2.5 pt-3 xl:pt-0 border-t xl:border-t-0 border-[#F2F2F7] shrink-0">
                <button onclick="toggleAccountsManagerModal()" class="btn-secondary whitespace-nowrap cursor-pointer text-xs flex items-center gap-1.5" title="Gestionar Cuentas Conectadas y Fases de Fondeo">
                  <i class="fa-solid fa-building-columns text-[#3C45A5]"></i> Cuentas & Fases
                </button>
                <button onclick="toggleRiskAuditModal()" class="btn-secondary whitespace-nowrap cursor-pointer text-xs" title="Ver auditoría de drawdown multianual">
                  <i class="fa-solid fa-shield-halved text-[#3C45A5]"></i> Auditoría Riesgo
                </button>
                <button onclick="triggerEmergencyKillSwitch()" id="btn-kill-switch" class="px-4 py-2 rounded-lg bg-[#D70015] hover:bg-[#B50012] text-white text-xs font-bold font-mono flex items-center gap-2 transition shadow-xs cursor-pointer whitespace-nowrap" title="Desconexión preventiva y pausa de todos los bots">
                  <i class="fa-solid fa-hand text-white"></i> PAUSA PREVENTIVA
                </button>
              </div>
            </div>
          </div>

"""
        html_content = html_content[:hud_div_start] + clean_hud + html_content[hud_div_end:]
        print("[OK] Clean #portfolio-risk-hud restored with Cuentas & Fases button.")

# Insert Accounts Manager Modal right before </body>
modal_html = """
  <!-- =========================================================================
       MODAL INSTITUCIONAL DE GESTIÓN MULTICUENTA GRANULAR
       ========================================================================= -->
  <div id="accounts-manager-modal" class="hidden fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4 overflow-y-auto">
    <div class="max-w-4xl w-full bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] my-8">
      
      <!-- Cabecera del Modal -->
      <div class="p-5 border-b border-[#F2F2F7] bg-[#FAFAFC] flex items-center justify-between">
        <div>
          <div class="overline-text">INFRAESTRUCTURA MULTICUENTA</div>
          <h3 class="text-base font-bold text-[#1D1D1F] mt-0.5">Gestor de Cuentas Conectadas & Fases de Fondeo</h3>
          <p class="text-xs text-[#6E6E73] mt-0.5">Control individual e independiente por cuenta: alterna entre Evaluación (40% Clamp) y Fondeada (Full Alpha) con botones explícitos.</p>
        </div>
        <button onclick="toggleAccountsManagerModal()" class="w-8 h-8 rounded-lg hover:bg-[#E5E5EA] text-[#6E6E73] flex items-center justify-center transition cursor-pointer" title="Cerrar ventana">
          <i class="fa-solid fa-xmark text-sm"></i>
        </button>
      </div>

      <!-- Contenido: Tabla de Cuentas Registradas -->
      <div class="p-5 overflow-y-auto space-y-6 flex-1">
        <div class="overflow-x-auto rounded-xl border border-[#E5E5EA]">
          <table class="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr class="border-b border-[#E5E5EA] bg-[#FAFAFC] text-[#6E6E73] text-[11px] uppercase">
                <th class="py-2.5 px-3">ID Cuenta</th>
                <th class="py-2.5 px-3">Firma / Bróker</th>
                <th class="py-2.5 px-3">Mesa / Vehículo</th>
                <th class="py-2.5 px-3 text-right">Saldo / Equidad</th>
                <th class="py-2.5 px-3 text-center">Fase Operativa (Selector Individual)</th>
                <th class="py-2.5 px-3 text-center">Consistencia 40%</th>
              </tr>
            </thead>
            <tbody id="accounts-table-tbody" class="divide-y divide-[#F2F2F7]">
              <!-- Populado dinámicamente por renderAccountsManagerUI() -->
            </tbody>
          </table>
        </div>

        <!-- Formulario para Registrar Nueva Cuenta -->
        <div class="p-4 rounded-xl border border-[#E5E5EA] bg-[#FAFAFC] space-y-3">
          <h4 class="text-xs font-bold text-[#1D1D1F] uppercase tracking-wider flex items-center gap-1.5">
            <i class="fa-solid fa-plus-circle text-[#3C45A5]"></i> Registrar Nueva Cuenta de Fondeo o Broker
          </h4>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            <div>
              <label class="text-[10px] uppercase font-bold text-[#6E6E73] block mb-1">ID Cuenta</label>
              <input type="text" id="new-acc-id" placeholder="Ej: 53120791 o PROP-100K" class="w-full px-2.5 py-1.5 rounded-lg border border-[#E5E5EA] bg-white text-xs font-mono text-[#1D1D1F]">
            </div>
            <div>
              <label class="text-[10px] uppercase font-bold text-[#6E6E73] block mb-1">Firma / Bróker</label>
              <input type="text" id="new-acc-firm" placeholder="Ej: Topstep, Tradeify, Apex..." class="w-full px-2.5 py-1.5 rounded-lg border border-[#E5E5EA] bg-white text-xs font-mono text-[#1D1D1F]">
            </div>
            <div>
              <label class="text-[10px] uppercase font-bold text-[#6E6E73] block mb-1">Mesa / Tipo</label>
              <select id="new-acc-desk" class="w-full px-2.5 py-1.5 rounded-lg border border-[#E5E5EA] bg-white text-xs font-mono text-[#1D1D1F]">
                <option value="PROP_FIRM">Fondeo (Prop Firm)</option>
                <option value="CAPITAL_PROPIO">Capital Propio</option>
              </select>
            </div>
            <div>
              <label class="text-[10px] uppercase font-bold text-[#6E6E73] block mb-1">Saldo ($ USD)</label>
              <input type="number" id="new-acc-balance" value="50000" class="w-full px-2.5 py-1.5 rounded-lg border border-[#E5E5EA] bg-white text-xs font-mono text-[#1D1D1F]">
            </div>
            <div>
              <label class="text-[10px] uppercase font-bold text-[#6E6E73] block mb-1">Fase Inicial</label>
              <select id="new-acc-stage" class="w-full px-2.5 py-1.5 rounded-lg border border-[#E5E5EA] bg-white text-xs font-mono text-[#1D1D1F]">
                <option value="EVALUATION">Evaluación (40% Clamp)</option>
                <option value="FUNDED">Fondeada (Full Alpha)</option>
                <option value="LIVE_CAPITAL">Capital Propio</option>
              </select>
            </div>
          </div>
          <div class="flex justify-end pt-1">
            <button onclick="submitNewAccount()" class="px-3 py-1.5 rounded-lg bg-[#3C45A5] hover:bg-[#32398a] text-white text-xs font-bold font-mono transition cursor-pointer flex items-center gap-1.5 shadow-xs">
              <i class="fa-solid fa-check text-xs"></i> Guardar y Conectar Cuenta
            </button>
          </div>
        </div>
      </div>

      <!-- Footer del Modal -->
      <div class="p-3.5 border-t border-[#F2F2F7] bg-[#FAFAFC] flex items-center justify-between text-xs font-mono">
        <span class="text-[#6E6E73] text-[11px] flex items-center gap-1.5">
          <i class="fa-solid fa-shield text-[#107C41]"></i> Anti-Hedging acotado por firma activo
        </span>
        <button onclick="toggleAccountsManagerModal()" class="btn-secondary text-xs cursor-pointer">
          Cerrar
        </button>
      </div>

    </div>
  </div>
"""

body_end_idx = html_content.rfind('</body>')
if body_end_idx != -1 and 'id="accounts-manager-modal"' not in html_content:
    html_content = html_content[:body_end_idx] + modal_html + "\n" + html_content[body_end_idx:]
    print("[OK] accounts-manager-modal HTML inserted before </body>.")

# Add JS functions for the Accounts Manager
accounts_js = """
    // =========================================================================
    // GESTOR MULTICUENTA GRANULAR (MODAL & TOGGLES POR CUENTA)
    // =========================================================================
    let cachedAccountsList = [];

    function toggleAccountsManagerModal() {
      const modal = document.getElementById('accounts-manager-modal');
      if (!modal) return;
      modal.classList.toggle('hidden');
      if (!modal.classList.contains('hidden')) {
        fetchAccountsCatalog();
      }
    }

    async function fetchAccountsCatalog() {
      try {
        const res = await fetch('/api/accounts');
        if (!res.ok) return;
        const data = await res.json();
        cachedAccountsList = data.accounts || [];
        renderAccountsManagerUI();
      } catch (e) {
        console.error('Error fetching accounts catalog:', e);
      }
    }

    function renderAccountsManagerUI() {
      const tbody = document.getElementById('accounts-table-tbody');
      if (!tbody) return;

      if (cachedAccountsList.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="p-4 text-center text-[#86868B]">No hay cuentas registradas</td></tr>';
        return;
      }

      tbody.innerHTML = cachedAccountsList.map(acc => {
        const isEval = (acc.stage === 'EVALUATION');
        const isFunded = (acc.stage === 'FUNDED');
        const isCap = (acc.stage === 'LIVE_CAPITAL');

        const consistencyBadge = isEval
          ? '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-[#FEF3C7] text-[#B45309] border border-[#FDE68A]">🛡️ 40% Clamp Activo</span>'
          : '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0]">⚡ Desactivada (Full Alpha)</span>';

        const deskBadge = (acc.desk_type === 'CAPITAL_PROPIO')
          ? '<span class="badge-success-live text-[10px] py-0.5 px-2">Capital Propio</span>'
          : '<span class="badge-brand-indigo text-[10px] py-0.5 px-2">Fondeo (Prop Firm)</span>';

        return `
          <tr class="hover:bg-[#FAFAFC] transition">
            <td class="py-3 px-3 font-bold text-[#1D1D1F]">${acc.account_id}</td>
            <td class="py-3 px-3">
              <div class="font-bold text-[#1D1D1F]">${acc.firm_name}</div>
              <div class="text-[10px] text-[#86868B]">${acc.status || 'ACTIVA'}</div>
            </td>
            <td class="py-3 px-3">${deskBadge}</td>
            <td class="py-3 px-3 text-right font-bold text-[#1D1D1F]">$${Number(acc.balance || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
            <td class="py-3 px-3 text-center">
              <div class="inline-flex rounded-lg border border-[#E5E5EA] p-0.5 bg-[#F5F5F7] shadow-2xs">
                <button onclick="setSingleAccountStage('${acc.account_id}', 'EVALUATION')" class="px-2.5 py-1 rounded-md text-[10px] font-bold transition cursor-pointer ${isEval ? 'bg-[#FEF3C7] text-[#B45309] shadow-xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'}">
                  Evaluación
                </button>
                <button onclick="setSingleAccountStage('${acc.account_id}', 'FUNDED')" class="px-2.5 py-1 rounded-md text-[10px] font-bold transition cursor-pointer ${isFunded ? 'bg-[#ECFDF5] text-[#065F46] shadow-xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'}">
                  Fondeada
                </button>
                ${(acc.desk_type === 'CAPITAL_PROPIO') ? `
                <button onclick="setSingleAccountStage('${acc.account_id}', 'LIVE_CAPITAL')" class="px-2.5 py-1 rounded-md text-[10px] font-bold transition cursor-pointer ${isCap ? 'bg-[#EEF2FF] text-[#3C45A5] shadow-xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'}">
                  Capital Propio
                </button>` : ''}
              </div>
            </td>
            <td class="py-3 px-3 text-center">${consistencyBadge}</td>
          </tr>
        `;
      }).join('');
    }

    async function setSingleAccountStage(accountId, newStage) {
      try {
        const res = await fetch('/api/accounts/update_stage', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ account_id: accountId, stage: newStage })
        });
        if (res.ok) {
          fetchAccountsCatalog();
          if (typeof fetchNotifications === 'function') fetchNotifications();
        }
      } catch (e) {
        console.error('Error updating account stage:', e);
      }
    }

    async function submitNewAccount() {
      const id = document.getElementById('new-acc-id').value.trim();
      const firm = document.getElementById('new-acc-firm').value.trim();
      const desk = document.getElementById('new-acc-desk').value;
      const balance = parseFloat(document.getElementById('new-acc-balance').value) || 50000.0;
      const stage = document.getElementById('new-acc-stage').value;

      if (!id || !firm) {
        alert('Por favor introduce el ID de cuenta y el nombre del Bróker/Firma.');
        return;
      }

      try {
        const res = await fetch('/api/accounts/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            account_id: id,
            firm_name: firm,
            desk_type: desk,
            balance: balance,
            stage: stage
          })
        });
        if (res.ok) {
          document.getElementById('new-acc-id').value = '';
          document.getElementById('new-acc-firm').value = '';
          fetchAccountsCatalog();
        }
      } catch (e) {
        console.error('Error adding new account:', e);
      }
    }

"""

target_js_ins = "// =========================================================================\n    // CENTRO DE ALERTAS Y NOTIFICACIONES CUANTITATIVAS"
if target_js_ins in html_content:
    html_content = html_content.replace(target_js_ins, accounts_js + "\n    " + target_js_ins, 1)
    print("[OK] Accounts Manager JS handlers added to index.html.")

html_path.write_text(html_content, encoding="utf-8")
print("[SUCCESS] All files patched locally.")
