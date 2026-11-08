import re

INDEX_PATH = r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html"

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Insert Bifocal Selector HTML in tab-content-backtests
bifocal_html = """      <!-- Selector de Lente Cuantitativa Bifásica: Evaluación (Reto Prop Firm) vs Fondeada (Alpha & Retiros) -->
      <div class="rounded-xl p-3.5 border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div class="flex items-center space-x-3">
          <div class="h-8 w-8 rounded-lg bg-[#EEF2FF] flex items-center justify-center text-[#3C45A5]">
            <i class="fa-solid fa-code-compare text-sm"></i>
          </div>
          <div>
            <div class="text-xs font-bold text-[#1D1D1F] uppercase tracking-wider">Lente Cuantitativa Bifásica</div>
            <div class="text-[11px] text-[#6E6E73]">Alternar entre restricciones de Reto Prop Firm (40% Clamp & Monte Carlo) o Cosecha de Alpha en Fondeada</div>
          </div>
        </div>
        <!-- Segmented Control Apple -->
        <div class="segmented-control w-full sm:w-auto">
          <button id="btn-lens-eval" onclick="switchBifocalLens('EVALUATION')" class="segmented-pill active flex-1 sm:flex-initial">
            <i class="fa-solid fa-graduation-cap"></i> 1. Evaluación (40% Clamp & Pass Rate)
          </button>
          <button id="btn-lens-funded" onclick="switchBifocalLens('FUNDED')" class="segmented-pill flex-1 sm:flex-initial">
            <i class="fa-solid fa-gem"></i> 2. Fondeada (Full Alpha & Payouts)
          </button>
        </div>
      </div>

      <!-- Banner Dinámico de Métricas Bifásicas -->
      <div id="bifocal-metrics-hud" class="grid grid-cols-2 lg:grid-cols-4 gap-4 p-4 rounded-xl border border-[#E5E5EA] bg-[#FAFAFC] shadow-2xs">
        <div class="border-r border-[#E5E5EA] pr-3">
          <span class="text-[10px] uppercase font-bold text-[#6E6E73] tracking-wider block" id="bifocal-kpi1-label">Pass Rate Monte Carlo</span>
          <div class="flex items-baseline gap-2 mt-0.5">
            <span class="text-lg font-bold font-mono text-[#065F46]" id="bifocal-kpi1-val">78.4%</span>
            <span class="badge-success-live text-[10px]" id="bifocal-kpi1-badge">Verde (>=70%)</span>
          </div>
        </div>
        <div class="border-r border-[#E5E5EA] pr-3">
          <span class="text-[10px] uppercase font-bold text-[#6E6E73] tracking-wider block" id="bifocal-kpi2-label">Trades Clampeados (Tope 40%)</span>
          <div class="flex items-baseline gap-2 mt-0.5">
            <span class="text-lg font-bold font-mono text-[#1D1D1F]" id="bifocal-kpi2-val">0 Trades</span>
            <span class="text-[10px] text-[#86868B] font-mono" id="bifocal-kpi2-sub">$0.00 penalización</span>
          </div>
        </div>
        <div class="border-r border-[#E5E5EA] pr-3">
          <span class="text-[10px] uppercase font-bold text-[#6E6E73] tracking-wider block" id="bifocal-kpi3-label">Drawdown Máximo Reto</span>
          <div class="flex items-baseline gap-2 mt-0.5">
            <span class="text-lg font-bold font-mono text-[#D70015]" id="bifocal-kpi3-val">-2.10%</span>
            <span class="text-[10px] text-[#86868B] font-mono" id="bifocal-kpi3-sub">Límite: -4.0%</span>
          </div>
        </div>
        <div>
          <span class="text-[10px] uppercase font-bold text-[#6E6E73] tracking-wider block" id="bifocal-kpi4-label">Target / Retorno Capped</span>
          <div class="flex items-baseline gap-2 mt-0.5">
            <span class="text-lg font-bold font-mono text-[#3C45A5]" id="bifocal-kpi4-val">+$7,800.98</span>
            <span class="text-[10px] font-mono text-[#065F46] font-semibold" id="bifocal-kpi4-sub">Meta: $8,000 (97.5%)</span>
          </div>
        </div>
      </div>
"""

target_horizon_comment = "<!-- Selector de Horizonte Temporal: Segmented Control Apple -->"
if "Lente Cuantitativa Bifásica" not in html:
    html = html.replace(target_horizon_comment, bifocal_html + "\n      " + target_horizon_comment, 1)
    print("[OK] Bifocal HTML injected in tab-content-backtests")
else:
    print("[INFO] Bifocal HTML already present")

# 2. Add JS functions switchBifocalLens and renderBifocalUI
bifocal_js = """
    // =========================================================================
    // CONTROLADOR DE LENTE CUANTITATIVA BIFÁSICA (EVALUACIÓN vs FONDEADA)
    // =========================================================================
    let currentBifocalLens = 'EVALUATION';

    function switchBifocalLens(lens) {
      currentBifocalLens = lens;
      const bEval = document.getElementById('btn-lens-eval');
      const bFunded = document.getElementById('btn-lens-funded');

      if (bEval && bFunded) {
        if (lens === 'EVALUATION') {
          bEval.className = 'segmented-pill active flex-1 sm:flex-initial';
          bFunded.className = 'segmented-pill flex-1 sm:flex-initial';
        } else {
          bEval.className = 'segmented-pill flex-1 sm:flex-initial';
          bFunded.className = 'segmented-pill active flex-1 sm:flex-initial';
        }
      }
      renderBifocalUI();
    }

    function renderBifocalUI() {
      if (!currentAnalyticsData) return;
      const bf = currentAnalyticsData.bifocal_report;

      const kpi1Label = document.getElementById('bifocal-kpi1-label');
      const kpi1Val = document.getElementById('bifocal-kpi1-val');
      const kpi1Badge = document.getElementById('bifocal-kpi1-badge');

      const kpi2Label = document.getElementById('bifocal-kpi2-label');
      const kpi2Val = document.getElementById('bifocal-kpi2-val');
      const kpi2Sub = document.getElementById('bifocal-kpi2-sub');

      const kpi3Label = document.getElementById('bifocal-kpi3-label');
      const kpi3Val = document.getElementById('bifocal-kpi3-val');
      const kpi3Sub = document.getElementById('bifocal-kpi3-sub');

      const kpi4Label = document.getElementById('bifocal-kpi4-label');
      const kpi4Val = document.getElementById('bifocal-kpi4-val');
      const kpi4Sub = document.getElementById('bifocal-kpi4-sub');

      if (currentBifocalLens === 'EVALUATION') {
        const ev = bf ? bf.evaluation_view : null;
        const passRate = ev ? ev.pass_rate_monte_carlo : 78.4;
        const clampedCount = ev ? ev.clamped_trades_count : 0;
        const penalty = ev ? ev.consistency_penalty_usd : 0.0;
        const maxDd = ev ? ev.max_drawdown_pct : (currentAnalyticsData.kpis ? currentAnalyticsData.kpis.max_drawdown : 2.1);
        const netProfit = ev ? ev.net_profit_usd : (currentAnalyticsData.kpis ? currentAnalyticsData.kpis.net_profit : 7800.98);

        if (kpi1Label) kpi1Label.innerText = 'Pass Rate Monte Carlo';
        if (kpi1Val) { kpi1Val.innerText = `${passRate}%`; kpi1Val.className = 'text-lg font-bold font-mono text-[#065F46]'; }
        if (kpi1Badge) { kpi1Badge.innerText = passRate >= 70 ? 'Verde (>=70%)' : 'Ámbar'; kpi1Badge.className = passRate >= 70 ? 'badge-success-live text-[10px]' : 'badge-warning-risk text-[10px]'; }

        if (kpi2Label) kpi2Label.innerText = 'Trades Clampeados (Tope 40%)';
        if (kpi2Val) kpi2Val.innerText = `${clampedCount} Trades`;
        if (kpi2Sub) kpi2Sub.innerText = `$${penalty.toFixed(2)} penalización`;

        if (kpi3Label) kpi3Label.innerText = 'Drawdown Máximo Reto';
        if (kpi3Val) { kpi3Val.innerText = `-${maxDd.toFixed(2)}%`; kpi3Val.className = 'text-lg font-bold font-mono text-[#D70015]'; }
        if (kpi3Sub) kpi3Sub.innerText = 'Límite EOD: -4.0%';

        if (kpi4Label) kpi4Label.innerText = 'Target / Retorno Capped';
        if (kpi4Val) { kpi4Val.innerText = `+$${netProfit.toLocaleString('en-US', {minimumFractionDigits: 2})}`; kpi4Val.className = 'text-lg font-bold font-mono text-[#3C45A5]'; }
        if (kpi4Sub) kpi4Sub.innerText = 'Meta Reto: $8,000 (+8%)';

        if (ev && ev.curve && ev.curve.length > 0) {
          renderMainEquityChart(ev.curve);
        } else if (currentAnalyticsData.balance_curve) {
          renderMainEquityChart(currentAnalyticsData.balance_curve);
        }
      } else {
        const fv = bf ? bf.funded_view : null;
        const totalAlpha = fv ? fv.total_uncapped_alpha_usd : (currentAnalyticsData.kpis ? currentAnalyticsData.kpis.net_profit : 10054.45);
        const payout = fv ? fv.monthly_payout_projection_usd : 670.30;
        const maxDd = fv ? fv.max_drawdown_pct : (currentAnalyticsData.kpis ? currentAnalyticsData.kpis.max_drawdown : 2.1);
        const pf = currentAnalyticsData.kpis ? currentAnalyticsData.kpis.profit_factor : 2.18;
        const sharpe = currentAnalyticsData.kpis ? currentAnalyticsData.kpis.sharpe_ratio : 1.94;

        if (kpi1Label) kpi1Label.innerText = 'Beneficio Total sin Topes';
        if (kpi1Val) { kpi1Val.innerText = `+$${totalAlpha.toLocaleString('en-US', {minimumFractionDigits: 2})}`; kpi1Val.className = 'text-lg font-bold font-mono text-[#065F46]'; }
        if (kpi1Badge) { kpi1Badge.innerText = 'Full Alpha'; kpi1Badge.className = 'badge-brand-indigo text-[10px]'; }

        if (kpi2Label) kpi2Label.innerText = 'Expectativa Retiro Mensual';
        if (kpi2Val) kpi2Val.innerText = `$${payout.toLocaleString('en-US', {minimumFractionDigits: 2})} / mes`;
        if (kpi2Sub) kpi2Sub.innerText = 'Profit Split: 80% Trader';

        if (kpi3Label) kpi3Label.innerText = 'Profit Factor / Sharpe';
        if (kpi3Val) { kpi3Val.innerText = `PF ${pf} · S ${sharpe}`; kpi3Val.className = 'text-lg font-bold font-mono text-[#181A20]'; }
        if (kpi3Sub) kpi3Sub.innerText = 'Métricas Reales sin Clamp';

        if (kpi4Label) kpi4Label.innerText = 'Drawdown Libre de Cartera';
        if (kpi4Val) { kpi4Val.innerText = `-${maxDd.toFixed(2)}%`; kpi4Val.className = 'text-lg font-bold font-mono text-[#D70015]'; }
        if (kpi4Sub) kpi4Sub.innerText = 'Sin riesgo de fallo de reto';

        if (fv && fv.curve && fv.curve.length > 0) {
          renderMainEquityChart(fv.curve);
        } else if (currentAnalyticsData.balance_curve) {
          renderMainEquityChart(currentAnalyticsData.balance_curve);
        }
      }
    }
"""

if "CONTROLADOR DE LENTE CUANTITATIVA BIFÁSICA" not in html:
    # Insert right before renderMainEquityChart
    html = html.replace("function renderMainEquityChart(", bifocal_js + "\n    function renderMainEquityChart(", 1)
    print("[OK] Bifocal JS controller inserted before renderMainEquityChart")
else:
    print("[INFO] Bifocal JS controller already present")

# Also hook renderBifocalUI into fetchAnalyticsData when data arrives
fetch_hook_target = "currentAnalyticsData = data;\n      updateAnalyticsUI(data);"
fetch_hook_replacement = "currentAnalyticsData = data;\n      updateAnalyticsUI(data);\n      if (typeof renderBifocalUI === 'function') renderBifocalUI();"
if fetch_hook_target in html and "renderBifocalUI();" not in html:
    html = html.replace(fetch_hook_target, fetch_hook_replacement, 1)
    print("[OK] Hooked renderBifocalUI into fetchAnalyticsData")

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("[SUCCESS] index.html updated with Bifocal Backtest UI!")
