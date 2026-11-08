import re
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot")
INDEX_PATH = BASE_DIR / "dashboard" / "templates" / "index.html"

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the 6 KPI cards grid
grid_start = content.find('<!-- ==================== 6 TARJETAS DE KPI INDEPENDIENTES (APPLE / LINEAR STYLE) ==================== -->')
grid_end = content.find('<!-- ==================== CUENTAS ACTIVAS: MODO CAPITAL PROPIO ==================== -->')

if grid_start == -1 or grid_end == -1:
    print("KPI grid markers not found!")
    exit(1)

new_kpi_grid = """<!-- ==================== 6 TARJETAS DE KPI INDEPENDIENTES (APPLE / LINEAR STYLE) ==================== -->
          <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3.5 sm:gap-4">
            
            <!-- KPI 1: Balance Total en Forward Test -->
            <div class="p-4 sm:p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs flex flex-col justify-between hover:border-[#D1D1D6] transition">
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-[11px] uppercase tracking-wider font-semibold text-[#6E6E73] truncate">Balance Total FT</span>
                  <div class="h-6 w-6 rounded-lg bg-[#EEF2FF] flex items-center justify-center text-[#3C45A5] shrink-0">
                    <i class="fa-solid fa-wallet text-[11px]"></i>
                  </div>
                </div>
                <div class="text-lg sm:text-2xl font-bold font-mono text-[#1D1D1F] tracking-tight" id="cockpit-kpi-total-balance">$1,998.09</div>
              </div>
              <div class="mt-3 pt-2.5 border-t border-[#F2F2F7] flex items-center justify-end text-[11px]">
                <span id="cockpit-kpi-total-subtext" class="badge-brand-indigo font-mono text-[10px] py-0.5 px-1.5">MT5 + DEX</span>
              </div>
            </div>

            <!-- KPI 2: PnL Realizado Total -->
            <div class="p-4 sm:p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs flex flex-col justify-between hover:border-[#D1D1D6] transition">
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-[11px] uppercase tracking-wider font-semibold text-[#6E6E73] truncate">PnL Realizado</span>
                  <div class="h-6 w-6 rounded-lg bg-[#F2F2F7] flex items-center justify-center text-[#1D1D1F] shrink-0">
                    <i class="fa-solid fa-scale-balanced text-[11px]"></i>
                  </div>
                </div>
                <div class="text-lg sm:text-2xl font-bold font-mono text-[#D70015] tracking-tight" id="cockpit-kpi-realized-pnl">-$1.91</div>
              </div>
              <div class="mt-3 pt-2.5 border-t border-[#F2F2F7] flex items-center justify-end text-[11px]">
                <span id="cockpit-kpi-realized-badge" class="badge-warning-risk font-mono text-[10px] py-0.5 px-1.5">-0.10%</span>
              </div>
            </div>

            <!-- KPI 3: PnL Flotante Total -->
            <div class="p-4 sm:p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs flex flex-col justify-between hover:border-[#D1D1D6] transition">
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-[11px] uppercase tracking-wider font-semibold text-[#6E6E73] truncate">PnL Flotante</span>
                  <div class="h-6 w-6 rounded-lg bg-[#FEF2F2] flex items-center justify-center text-[#D70015] shrink-0">
                    <i class="fa-solid fa-chart-line text-[11px]"></i>
                  </div>
                </div>
                <div class="text-lg sm:text-2xl font-bold font-mono text-[#D70015] tracking-tight" id="cockpit-kpi-floating-pnl">-$4.58</div>
              </div>
              <div class="mt-3 pt-2.5 border-t border-[#F2F2F7] flex items-center justify-end text-[11px]">
                <span id="cockpit-kpi-floating-badge" class="badge-neutral-soft font-mono text-[10px] py-0.5 px-1.5">-0.23%</span>
              </div>
            </div>

            <!-- KPI 4: Drawdown Cartera -->
            <div class="p-4 sm:p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs flex flex-col justify-between hover:border-[#D1D1D6] transition">
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-[11px] uppercase tracking-wider font-semibold text-[#6E6E73] truncate">Drawdown Cartera</span>
                  <div class="h-6 w-6 rounded-lg bg-[#FEF2F2] flex items-center justify-center text-[#D70015] shrink-0">
                    <i class="fa-solid fa-arrow-trend-down text-[11px]"></i>
                  </div>
                </div>
                <div class="text-lg sm:text-2xl font-bold font-mono text-[#D70015] tracking-tight" id="cockpit-kpi-drawdown">-0.23%</div>
              </div>
              <div class="mt-3 pt-2.5 border-t border-[#F2F2F7] flex items-center justify-end text-[11px]">
                <span class="text-[#D70015] font-mono font-semibold text-[11px]" id="cockpit-kpi-drawdown-limit">-5.00%</span>
              </div>
            </div>

            <!-- KPI 5: Margen Utilizado -->
            <div class="p-4 sm:p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs flex flex-col justify-between hover:border-[#D1D1D6] transition">
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-[11px] uppercase tracking-wider font-semibold text-[#6E6E73] truncate">Margen Utilizado</span>
                  <div class="h-6 w-6 rounded-lg bg-[#ECFDF5] flex items-center justify-center text-[#065F46] shrink-0">
                    <i class="fa-solid fa-gauge text-[11px]"></i>
                  </div>
                </div>
                <div class="text-lg sm:text-2xl font-bold font-mono text-[#1D1D1F] tracking-tight" id="cockpit-kpi-margin-used">0.85%</div>
              </div>
              <div class="mt-3 pt-2.5 border-t border-[#F2F2F7] flex items-center justify-end text-[11px]">
                <span id="cockpit-kpi-margin-badge" class="badge-success-live font-mono text-[10px] py-0.5 px-1.5">Seguro</span>
              </div>
            </div>

            <!-- KPI 6: Riesgo Flotante al SL (Suma de posiciones abiertas) -->
            <div class="p-4 sm:p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs flex flex-col justify-between hover:border-[#D1D1D6] transition">
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-[11px] uppercase tracking-wider font-semibold text-[#6E6E73] truncate">Riesgo Flotante (SL)</span>
                  <div class="h-6 w-6 rounded-lg bg-[#FEF2F2] flex items-center justify-center text-[#D70015] shrink-0">
                    <i class="fa-solid fa-crosshairs text-[11px]"></i>
                  </div>
                </div>
                <div class="text-lg sm:text-2xl font-bold font-mono text-[#D70015] tracking-tight" id="cockpit-kpi-open-risk">$0.00</div>
              </div>
              <div class="mt-3 pt-2.5 border-t border-[#F2F2F7] flex items-center justify-end text-[11px]">
                <span id="cockpit-kpi-open-risk-badge" class="badge-warning-risk font-mono text-[10px] py-0.5 px-1.5">0.00%</span>
              </div>
            </div>

          </div>

          """

content = content[:grid_start] + new_kpi_grid + content[grid_end:]
print("KPI grid HTML updated: removed bottom-left text and replaced Net Exposure with Riesgo Flotante (SL)!")

# Update updateCockpitKPIs in JavaScript
js_old = """      // 5. Margen Utilizado
      const kpiMargin = document.getElementById('cockpit-kpi-margin-used');
      if (kpiMargin) kpiMargin.innerText = Number(marginVal).toFixed(2) + '%';

      // 6. Exposición Neta
      const kpiExp = document.getElementById('cockpit-kpi-net-exposure');
      const kpiExpSub = document.getElementById('cockpit-kpi-net-subtext');
      if (kpiExp) kpiExp.innerText = expVal;
      if (kpiExpSub) kpiExpSub.innerText = expSub;
    }"""

js_new = """      // 5. Margen Utilizado
      const kpiMargin = document.getElementById('cockpit-kpi-margin-used');
      if (kpiMargin) kpiMargin.innerText = Number(marginVal).toFixed(2) + '%';

      // 6. Riesgo Flotante al SL (Suma del valor en riesgo de posiciones vivas)
      const kpiRisk = document.getElementById('cockpit-kpi-open-risk');
      const kpiRiskBadge = document.getElementById('cockpit-kpi-open-risk-badge');
      const riskVal = deskData ? Number(deskData.open_sl_risk_usd || 0.0) : 0.0;
      const riskPct = deskData ? Number(deskData.open_sl_risk_pct || 0.0) : 0.0;

      if (kpiRisk) {
        kpiRisk.innerText = '$' + riskVal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        kpiRisk.className = `text-lg sm:text-2xl font-bold font-mono tracking-tight ${riskVal > 0 ? 'text-[#D70015]' : 'text-[#1D1D1F]'}`;
      }
      if (kpiRiskBadge) {
        kpiRiskBadge.innerText = riskPct.toFixed(2) + '%';
        kpiRiskBadge.className = `font-mono text-[10px] py-0.5 px-1.5 ${riskVal > 0 ? 'badge-warning-risk' : 'badge-neutral-soft'}`;
      }
    }"""

content_norm = content.replace("\r\n", "\n")
js_old_norm = js_old.replace("\r\n", "\n")
js_new_norm = js_new.replace("\r\n", "\n")

if js_old_norm in content_norm:
    content_norm = content_norm.replace(js_old_norm, js_new_norm)
    content = content_norm
    print("JavaScript updateCockpitKPIs successfully patched with open SL risk!")
else:
    print("js_old_norm not found in content!")
    exit(1)

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated index.html completely!")
