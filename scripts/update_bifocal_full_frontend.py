import re

path = r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html'

with open(path, 'r', encoding='utf-8', errors='replace') as f:
    text = f.read()

# 1. Update HTML IDs if not present
# kpi-dd-label, kpi-dd-sub
if 'id="kpi-dd-label"' not in text:
    old_dd = """          <!-- Max Drawdown EOD -->
          <div class="rounded-xl p-4 border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs flex flex-col justify-between min-w-0">
            <div class="text-[11px] text-[#6E6E73] flex items-center justify-between font-medium">
              <span>Max Drawdown</span>
              <i class="fa-solid fa-shield-halved text-[#D70015] text-xs"></i>
            </div>
            <div class="text-lg xl:text-xl font-bold font-mono text-[#065F46] mt-1.5 truncate" id="kpi-dd">0.85%</div>
            <div class="text-[11px] text-[#6E6E73] mt-1 font-mono">Lmite Fondeo: 3.50%</div>
          </div>"""
    new_dd = """          <!-- Max Drawdown EOD -->
          <div class="rounded-xl p-4 border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs flex flex-col justify-between min-w-0">
            <div class="text-[11px] text-[#6E6E73] flex items-center justify-between font-medium">
              <span id="kpi-dd-label">Max Drawdown EOD</span>
              <i class="fa-solid fa-shield-halved text-[#D70015] text-xs"></i>
            </div>
            <div class="text-lg xl:text-xl font-bold font-mono text-[#065F46] mt-1.5 truncate" id="kpi-dd">0.85%</div>
            <div class="text-[11px] text-[#6E6E73] mt-1 font-mono" id="kpi-dd-sub">Límite Fondeo: -4.00%</div>
          </div>"""
    # Regex fallback if encoding of 'Lmite' differs
    text = re.sub(
        r'<!-- Max Drawdown EOD -->\s*<div class="rounded-xl p-4[^>]*>.*?<span>Max Drawdown</span>.*?<div class="[^"]*" id="kpi-dd">.*?</div>\s*<div class="text-\[11px\] text-\[#6E6E73\] mt-1 font-mono">.*?</div>\s*</div>',
        new_dd,
        text,
        flags=re.DOTALL
    )
    print("1. kpi-dd IDs added")
else:
    print("1. kpi-dd IDs already present")

# streak-kpi-passes-label, streak-kpi-worstdowndd-label
if 'id="streak-kpi-passes-label"' not in text:
    text = re.sub(
        r'<div class="text-\[10px\] text-\[#86868B\] uppercase font-mono tracking-wider">Pases Challenge \(\+6%\)</div>',
        r'<div class="text-[10px] text-[#86868B] uppercase font-mono tracking-wider" id="streak-kpi-passes-label">Pases Challenge (+8%)</div>',
        text
    )
    text = re.sub(
        r'<div class="text-\[10px\] text-\[#86868B\] uppercase font-mono tracking-wider">Peor Valle Post-Pico</div>',
        r'<div class="text-[10px] text-[#86868B] uppercase font-mono tracking-wider" id="streak-kpi-worstdowndd-label">Peor Drawdown EOD</div>',
        text
    )
    print("2. streak-kpi labels IDs added")
else:
    print("2. streak-kpi labels IDs already present")

# table th id
if 'id="th-trades-profit"' not in text:
    text = re.sub(
        r'<th class="py-2.5 px-3 text-right">Beneficio Neto</th>',
        r'<th id="th-trades-profit" class="py-2.5 px-3 text-right">Beneficio Neto</th>',
        text,
        count=1
    )
    print("3. th-trades-profit ID added")
else:
    print("3. th-trades-profit ID already present")

# 4. Update switchBifocalLens and renderBifocalUI
old_switch_and_render = """    let currentBifocalLens = 'EVALUATION';

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

      // Re-consultar analíticas e historial completos con la lente seleccionada
      if (typeof fetchAnalyticsData === 'function') {
        fetchAnalyticsData(currentAccountFilter);
      }
      if (typeof fetchTradeHistory === 'function') {
        fetchTradeHistory(currentAccountFilter);
      }
    }

    function renderBifocalUI() {"""

new_switch_and_render = """    let currentBifocalLens = 'EVALUATION';

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

      // Disparar animación suave de transición en el contenedor
      const backtestPane = document.getElementById('tab-content-backtests') || document.getElementById('tab-content-dashboard');
      if (typeof triggerMotionSweep === 'function') {
        triggerMotionSweep(backtestPane);
      }

      // Re-consultar analíticas e historial completos con la lente seleccionada
      if (typeof fetchAnalyticsData === 'function') {
        fetchAnalyticsData(currentAccountFilter);
      }
      if (typeof fetchTradesData === 'function') {
        fetchTradesData(currentAccountFilter);
      }
    }

    function renderBifocalUI() {"""

if old_switch_and_render in text:
    text = text.replace(old_switch_and_render, new_switch_and_render, 1)
    print("4. switchBifocalLens updated successfully")
else:
    print("4. switchBifocalLens pattern NOT found directly, trying regex")
    text = re.sub(
        r'let currentBifocalLens = [^;]+;.*?function switchBifocalLens\(lens\)\s*\{.*?\}\s*function renderBifocalUI\(\)\s*\{',
        new_switch_and_render,
        text,
        flags=re.DOTALL
    )

# 5. Update renderMainEquityChart
chart_func_regex = r'function renderMainEquityChart\(curveData\)\s*\{.*?\n    \}\n\n    // Renderizar Gr[aá]fico de Rendimiento por D[ií]a'
new_chart_func = """function renderMainEquityChart(curveData) {
      if (!curveData || curveData.length === 0) return;
      // Formatear eje X en español DD/MM/AAAA (autoajustable por ApexCharts)
      const categories = curveData.map(d => formatSpanishDate(d.timestamp));
      const balances = curveData.map(d => d.balance);
      const isEval = currentBifocalLens === 'EVALUATION';
      const initBal = Number(curveData[0].balance) || 100000;
      const targetVal = initBal * 1.08;
      const eodDdLimitVal = initBal * 0.96;

      let annotationsConfig = {};
      if (isEval) {
        annotationsConfig = {
          yaxis: [
            {
              y: targetVal,
              borderColor: '#10b981',
              strokeDashArray: 4,
              label: {
                borderColor: '#10b981',
                style: { color: '#ffffff', background: '#059669', fontSize: '10px', fontWeight: 'bold' },
                text: `Target Reto Superado (+8% / $${targetVal.toLocaleString('es-ES', {minimumFractionDigits: 0})})`
              }
            },
            {
              y: eodDdLimitVal,
              borderColor: '#ef4444',
              strokeDashArray: 4,
              label: {
                borderColor: '#ef4444',
                style: { color: '#ffffff', background: '#dc2626', fontSize: '10px', fontWeight: 'bold' },
                text: `Límite EOD Drawdown (-4% / $${eodDdLimitVal.toLocaleString('es-ES', {minimumFractionDigits: 0})})`
              }
            }
          ]
        };
      } else {
        annotationsConfig = {
          yaxis: [
            {
              y: initBal * 1.10,
              borderColor: '#6366f1',
              strokeDashArray: 4,
              label: {
                borderColor: '#6366f1',
                style: { color: '#ffffff', background: '#4f46e5', fontSize: '10px', fontWeight: 'bold' },
                text: `Hito Cosecha Retiro #1 ($${(initBal * 1.10).toLocaleString('es-ES', {minimumFractionDigits: 0})})`
              }
            },
            {
              y: initBal,
              borderColor: '#64748b',
              strokeDashArray: 2,
              label: {
                borderColor: '#64748b',
                style: { color: '#ffffff', background: '#334155', fontSize: '10px', fontWeight: 'bold' },
                text: `Buffer Capital Base ($${initBal.toLocaleString('es-ES', {minimumFractionDigits: 0})})`
              }
            }
          ]
        };
      }

      const options = {
        chart: {
          type: 'area',
          height: 320,
          toolbar: { show: true },
          background: 'transparent',
          fontFamily: 'JetBrains Mono, monospace',
          animations: {
            enabled: true,
            easing: 'easeinout',
            speed: 950,
            animateGradually: {
              enabled: true,
              delay: 140
            },
            dynamicAnimation: {
              enabled: true,
              speed: 400
            }
          }
        },
        theme: { mode: 'dark' },
        stroke: { curve: 'smooth', width: 2.2 },
        colors: isEval ? ['#10b981'] : ['#6366f1'],
        fill: {
          type: 'gradient',
          gradient: {
            shadeIntensity: 1,
            opacityFrom: 0.42,
            opacityTo: 0.03,
            stops: [0, 95, 100]
          }
        },
        dataLabels: { enabled: false },
        series: [{
          name: isEval ? 'Balance Reto Evaluación ($)' : 'Balance Cartera Fondeada ($)',
          data: balances
        }],
        xaxis: {
          categories: categories,
          tickAmount: Math.min(10, categories.length),
          labels: { 
            style: { colors: '#94a3b8', fontSize: '10px', fontFamily: 'monospace' },
            rotate: -35,
            rotateAlways: false
          },
          axisBorder: { show: false }
        },
        yaxis: {
          labels: {
            formatter: (val) => '$' + Number(val).toLocaleString('es-ES', {minimumFractionDigits: 0}),
            style: { colors: '#94a3b8', fontSize: '11px', fontFamily: 'monospace' }
          }
        },
        grid: {
          borderColor: '#1e293b',
          strokeDashArray: 3
        },
        annotations: annotationsConfig,
        tooltip: {
          theme: 'dark',
          custom: function({series, seriesIndex, dataPointIndex, w}) {
            const d = curveData[dataPointIndex];
            const dateStr = formatSpanishDateTime(d.timestamp);
            const val = series[seriesIndex][dataPointIndex];
            const bal = '$' + Number(val).toLocaleString('es-ES', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' USD';
            const pnlFromStart = Number(val) - initBal;
            const sign = pnlFromStart >= 0 ? '+' : '';
            const pnlStr = sign + '$' + pnlFromStart.toLocaleString('es-ES', {minimumFractionDigits: 2}) + ' USD';
            
            let extraHtml = '';
            if (isEval) {
              const distToTarget = targetVal - Number(val);
              const targetStatus = distToTarget <= 0 
                ? '<span class="text-emerald-400 font-bold">🏆 ¡Reto Superado!</span>'
                : `<span class="text-slate-300">Faltan: $${distToTarget.toLocaleString('es-ES', {minimumFractionDigits: 2})}</span>`;
              extraHtml = `
                <div class="text-[11px] border-t border-slate-700/60 pt-1 mt-1 text-slate-400 flex justify-between gap-2">
                  <span>Meta Reto (+8%):</span>
                  ${targetStatus}
                </div>
              `;
            } else {
              const payoutAvailable = pnlFromStart > 0 ? (pnlFromStart * 0.80).toLocaleString('es-ES', {minimumFractionDigits: 2}) : '0.00';
              extraHtml = `
                <div class="text-[11px] border-t border-slate-700/60 pt-1 mt-1 text-slate-400 flex justify-between gap-2">
                  <span>Payout Retirable (80%):</span>
                  <span class="text-indigo-300 font-bold font-mono">+$${payoutAvailable} USD</span>
                </div>
              `;
            }

            return `
              <div class="p-2.5 bg-slate-900 border border-slate-700 rounded-lg shadow-xl font-mono text-xs">
                <div class="text-slate-400 text-[11px] flex items-center gap-1.5 mb-1">
                  <i class="fa-regular fa-calendar text-cyan-400"></i> ${dateStr}
                </div>
                <div class="text-white font-bold flex items-center justify-between gap-3">
                  <span class="text-slate-400">Balance:</span>
                  <span class="text-cyan-300 font-mono text-sm">${bal}</span>
                </div>
                <div class="text-slate-300 text-[11px] flex items-center justify-between gap-3 mt-0.5">
                  <span class="text-slate-400">PnL Acumulado:</span>
                  <span class="${pnlFromStart >= 0 ? 'text-emerald-400' : 'text-rose-400'} font-bold">${pnlStr}</span>
                </div>
                ${extraHtml}
              </div>
            `;
          }
        }
      };

      if (mainEquityChart) mainEquityChart.destroy();
      mainEquityChart = new ApexCharts(document.querySelector("#main-equity-chart"), options);
      mainEquityChart.render();
    }

    // Renderizar Gráfico de Rendimiento por Día"""

text = re.sub(chart_func_regex, new_chart_func, text, flags=re.DOTALL)
print("5. renderMainEquityChart updated")

# 6. Update fetchAnalyticsData
fetch_analytics_regex = r'// Cargar An[aá]lisis y M[eé]tricas desde /api/analytics\s*async function fetchAnalyticsData\(filter\)\s*\{.*?\n    \}\n\n    // Cargar Historial de Operaciones'
new_fetch_analytics = """// Cargar Análisis y Métricas desde /api/analytics
    async function fetchAnalyticsData(filter) {
      let data = null;
      try {
        const res = await fetch(`/api/analytics?filter=${encodeURIComponent(filter)}&lens=${encodeURIComponent(currentBifocalLens)}`);
        if (res.ok) {
          data = await res.json();
        }
      } catch (err) {
        console.warn('Backend offline, utilizando modelo cuantitativo por defecto:', err);
      }

      if (!data) return;

      currentAnalyticsData = data;
      renderBifocalUI();

      // 1. Actualizar KPIs Principales según la Lente Activa
      const kpis = data.kpis;
      const isEval = currentBifocalLens === 'EVALUATION';

      if (document.getElementById('kpi-balance')) document.getElementById('kpi-balance').innerText = '$' + kpis.final_balance.toLocaleString(undefined, {minimumFractionDigits: 2});
      if (document.getElementById('kpi-init-bal')) document.getElementById('kpi-init-bal').innerText = '$' + kpis.initial_balance.toLocaleString(undefined, {minimumFractionDigits: 0});
      if (document.getElementById('kpi-net-profit')) document.getElementById('kpi-net-profit').innerText = (kpis.net_profit >= 0 ? '+' : '') + '$' + kpis.net_profit.toLocaleString(undefined, {minimumFractionDigits: 2});
      if (document.getElementById('kpi-pf')) document.getElementById('kpi-pf').innerText = kpis.profit_factor;
      if (document.getElementById('kpi-wr')) document.getElementById('kpi-wr').innerText = kpis.win_rate + '%';
      if (document.getElementById('kpi-trades-count')) document.getElementById('kpi-trades-count').innerText = `${kpis.win_count}W / ${kpis.loss_count}L (${kpis.total_trades} total)`;
      if (document.getElementById('kpi-dd')) document.getElementById('kpi-dd').innerText = kpis.max_drawdown.toFixed(2) + '%';
      if (document.getElementById('kpi-sharpe')) document.getElementById('kpi-sharpe').innerText = kpis.sharpe_ratio;
      if (document.getElementById('kpi-return')) document.getElementById('kpi-return').innerText = (kpis.return_pct >= 0 ? '+' : '') + kpis.return_pct + '%';
      
      const kpiDdLabel = document.getElementById('kpi-dd-label');
      if (kpiDdLabel) {
        kpiDdLabel.innerText = isEval ? 'Max Drawdown EOD (Límite: -4.0%)' : 'Max Drawdown Real de Cartera';
      }
      const kpiDdSub = document.getElementById('kpi-dd-sub');
      if (kpiDdSub) {
        kpiDdSub.innerText = isEval ? `Límite Fondeo: -4.00% (Margen: +${(4.0 - kpis.max_drawdown).toFixed(2)}%)` : 'Drawdown Libre de Cartera';
      }

      if (document.getElementById('badge-chart-pnl')) {
        if (isEval) {
          document.getElementById('badge-chart-pnl').innerText = `${(kpis.net_profit >= 0 ? '+' : '')}$${kpis.net_profit.toLocaleString(undefined, {minimumFractionDigits: 2})} USD · EVAL`;
          document.getElementById('badge-chart-pnl').className = 'px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 font-mono';
        } else {
          const payoutVal = (kpis.net_profit * 0.80).toLocaleString(undefined, {minimumFractionDigits: 0});
          document.getElementById('badge-chart-pnl').innerText = `+$${payoutVal} RETIRO ESTIMADO (80%)`;
          document.getElementById('badge-chart-pnl').className = 'px-2 py-0.5 rounded text-[11px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono';
        }
      }

      if (document.getElementById('chart-subtitle')) {
        if (isEval) {
          document.getElementById('chart-subtitle').innerText = `${data.account_name} · [LENTE EVALUACIÓN PROP FIRM] Target Reto +8.0% ($108k), EOD DD -4.0% y Clamp 40%`;
        } else {
          document.getElementById('chart-subtitle').innerText = `${data.account_name} · [LENTE FONDEADA & CAPITAL PROPIO] Alpha 100% Libre, Split 80/20 Payouts`;
        }
      }

      // 2. Day & Time Edge Cards
      if (document.getElementById('stat-best-dow')) document.getElementById('stat-best-dow').innerText = data.best_dow.day;
      if (document.getElementById('stat-best-dow-pnl')) document.getElementById('stat-best-dow-pnl').innerText = '+$' + data.best_dow.pnl.toLocaleString(undefined, {minimumFractionDigits: 2});
      if (document.getElementById('stat-best-hour')) document.getElementById('stat-best-hour').innerText = data.best_hour.label;
      if (document.getElementById('stat-best-hour-pnl')) document.getElementById('stat-best-hour-pnl').innerText = '+$' + data.best_hour.pnl.toLocaleString(undefined, {minimumFractionDigits: 2});
      if (document.getElementById('stat-best-day-date')) document.getElementById('stat-best-day-date').innerText = data.best_single_day.date;
      if (document.getElementById('stat-best-day-pnl')) document.getElementById('stat-best-day-pnl').innerText = '+$' + data.best_single_day.pnl.toLocaleString(undefined, {minimumFractionDigits: 2});
      if (document.getElementById('stat-best-day-sub')) document.getElementById('stat-best-day-sub').innerText = isEval ? `${data.best_single_day.day} récord (Consistencia OK)` : `${data.best_single_day.day} récord (Cosecha Alpha)`;
      if (document.getElementById('stat-worst-day-date')) document.getElementById('stat-worst-day-date').innerText = data.worst_single_day.date;
      if (document.getElementById('stat-worst-day-pnl')) document.getElementById('stat-worst-day-pnl').innerText = '$' + data.worst_single_day.pnl.toLocaleString(undefined, {minimumFractionDigits: 2});
      if (document.getElementById('stat-worst-day-sub')) document.getElementById('stat-worst-day-sub').innerText = isEval ? 'Bajo límite EOD (-$4,000)' : 'Riesgo diario controlado';
      if (document.getElementById('stat-win-streak')) document.getElementById('stat-win-streak').innerText = data.max_win_streak;
      if (document.getElementById('stat-loss-streak')) document.getElementById('stat-loss-streak').innerText = data.max_loss_streak;

      // 3. Renderizar Gráficos con Animaciones
      if (data.balance_curve) renderMainEquityChart(data.balance_curve);
      if (data.dow_distribution) renderDowChart(data.dow_distribution);
      if (data.hourly_distribution) renderHourlyChart(data.hourly_distribution);
      if (data.streaks_analysis) renderStreaksAnalysis(data.streaks_analysis, data.balance_curve);
    }

    // Cargar Historial de Operaciones"""

text = re.sub(fetch_analytics_regex, new_fetch_analytics, text, flags=re.DOTALL)
print("6. fetchAnalyticsData updated")

# 7. Update renderStreaksAnalysis mini KPIs and chip tags
old_streaks_func_start = """    function renderStreaksAnalysis(streaksData, balanceCurve) {
      if (!streaksData) return;
      cachedStreaksData = streaksData;
      cachedBalanceCurve = balanceCurve;

      const summary = streaksData.summary || {};
      const streaks = streaksData.streaks || [];

      // 1. Mini KPIs
      const elPasses = document.getElementById('streak-kpi-passes');
      const elWorstDd = document.getElementById('streak-kpi-worstdowndd');
      const elMaxUp = document.getElementById('streak-kpi-maxup');
      const elTotal = document.getElementById('streak-kpi-totaltramos');

      if (elPasses) elPasses.innerText = `${summary.challenges_passed || 0} Cuentas`;
      if (elWorstDd) elWorstDd.innerText = `${Number(summary.max_down_streak_pct || 0.0).toFixed(2)}% EOD`;
      if (elMaxUp) elMaxUp.innerText = `+${Number(summary.max_up_streak_pct || 0.0).toFixed(2)}%`;
      if (elTotal) elTotal.innerText = `${summary.total_streaks || 0} Tramos`;"""

new_streaks_func_start = """    function renderStreaksAnalysis(streaksData, balanceCurve) {
      if (!streaksData) return;
      cachedStreaksData = streaksData;
      cachedBalanceCurve = balanceCurve;

      const summary = streaksData.summary || {};
      const streaks = streaksData.streaks || [];
      const isEval = currentBifocalLens === 'EVALUATION';

      // 1. Mini KPIs
      const elPasses = document.getElementById('streak-kpi-passes');
      const elPassesLabel = document.getElementById('streak-kpi-passes-label');
      const elWorstDd = document.getElementById('streak-kpi-worstdowndd');
      const elWorstDdLabel = document.getElementById('streak-kpi-worstdowndd-label');
      const elMaxUp = document.getElementById('streak-kpi-maxup');
      const elTotal = document.getElementById('streak-kpi-totaltramos');

      if (isEval) {
        if (elPassesLabel) elPassesLabel.innerText = 'Pases Challenge (+8%)';
        if (elPasses) elPasses.innerText = `${summary.challenges_passed || 0} Fases`;
        if (elWorstDdLabel) elWorstDdLabel.innerText = 'Peor Drawdown EOD';
        if (elWorstDd) elWorstDd.innerText = `${Number(summary.max_down_streak_pct || 0.0).toFixed(2)}% EOD`;
      } else {
        if (elPassesLabel) elPassesLabel.innerText = 'Ciclos de Payout (+5%)';
        if (elPasses) elPasses.innerText = `${summary.challenges_passed || 0} Retiros`;
        if (elWorstDdLabel) elWorstDdLabel.innerText = 'Peor Corrección Libre';
        if (elWorstDd) elWorstDd.innerText = `${Number(summary.max_down_streak_pct || 0.0).toFixed(2)}% DD`;
      }
      if (elMaxUp) elMaxUp.innerText = `+${Number(summary.max_up_streak_pct || 0.0).toFixed(2)}%`;
      if (elTotal) elTotal.innerText = `${summary.total_streaks || 0} Tramos`;"""

if old_streaks_func_start in text:
    text = text.replace(old_streaks_func_start, new_streaks_func_start, 1)
    print("7. renderStreaksAnalysis mini KPIs updated")
else:
    print("7. old_streaks_func_start NOT found directly, trying regex")
    text = re.sub(
        r'function renderStreaksAnalysis\(streaksData, balanceCurve\)\s*\{.*?if \(elTotal\) elTotal\.innerText = `\$\{summary\.total_streaks \|\| 0\} Tramos`;',
        new_streaks_func_start,
        text,
        flags=re.DOTALL
    )

# 8. Update streak chips tags
old_chips_tag = """            const tag = isBull && s.challenge_passed 
              ? '<span class="streak-chip-pass">🏆 +6% PASSED</span>'
              : (!isBull && s.dd_safe ? '<span class="streak-chip-safe">🛡️ DD EOD SEGURO</span>' : '');"""

new_chips_tag = """            let tag = '';
            if (isEval) {
              tag = isBull && s.challenge_passed 
                ? '<span class="streak-chip-pass">🏆 +8% RETO PASSED</span>'
                : (!isBull && s.dd_safe ? '<span class="streak-chip-safe">🛡️ DD EOD SEGURO</span>' : '');
            } else {
              tag = isBull && s.challenge_passed 
                ? '<span class="streak-chip-pass" style="background:rgba(99,102,241,0.2);color:#a5b4fc;border:1px solid rgba(99,102,241,0.3)">💎 CICLO PAYOUT</span>'
                : (!isBull ? '<span class="streak-chip-safe">🛡️ BUFFER PRESERVADO</span>' : '');
            }"""

if old_chips_tag in text:
    text = text.replace(old_chips_tag, new_chips_tag, 1)
    print("8. streak chips tags updated")
else:
    print("8. old_chips_tag NOT found directly, trying regex")
    text = re.sub(
        r'const tag = isBull && s\.challenge_passed\s*\?\s*\'<span class="streak-chip-pass">.*?</span>\'\s*:\s*\(!isBull && s\.dd_safe \? \'<span class="streak-chip-safe">.*?</span>\' : \'\'\);',
        new_chips_tag,
        text,
        flags=re.DOTALL
    )

# 9. Update renderTradesTable
old_trade_row_pnl = """          <td class="py-2.5 px-3 text-right font-bold ${isWin ? 'text-emerald-400' : 'text-rose-400'}">
            <span class="px-2 py-0.5 rounded ${isWin ? 'bg-emerald-500/10' : 'bg-rose-500/10'} font-semibold">
              ${isWin ? '+' : ''}$${Number(t.net_pnl_usd).toFixed(2)}
            </span>
          </td>"""

new_trade_row_pnl = """          <td class="py-2.5 px-3 text-right font-bold ${isWin ? 'text-emerald-400' : 'text-rose-400'}">
            <div class="flex items-center justify-end gap-1">
              <span class="px-2 py-0.5 rounded ${isWin ? 'bg-emerald-500/10' : 'bg-rose-500/10'} font-semibold">
                ${isWin ? '+' : ''}$${Number(t.net_pnl_usd).toFixed(2)}
              </span>
              ${currentBifocalLens === 'EVALUATION' ? (
                t.clamped 
                  ? `<span class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30" title="Tope del 40% aplicado: Original $${t.original_pnl_usd}">40% CLAMP</span>`
                  : (isWin ? `<span class="px-1 py-0.5 rounded text-[8px] font-bold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20" title="Consistencia OK individual (<40%)">PASS</span>` : '')
              ) : (
                isWin ? `<span class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-indigo-500/15 text-indigo-400 border border-indigo-500/25 font-mono" title="80% Retiro Trader">80% PAYOUT: +$${(Number(t.net_pnl_usd) * 0.8).toFixed(0)}</span>` : ''
              )}
            </div>
          </td>"""

if old_trade_row_pnl in text:
    text = text.replace(old_trade_row_pnl, new_trade_row_pnl, 1)
    print("9. renderTradesTable row PnL updated")
else:
    print("9. old_trade_row_pnl NOT found directly, trying regex")
    text = re.sub(
        r'<td class="py-2\.5 px-3 text-right font-bold \$\{isWin \? \'text-emerald-400\' : \'text-rose-400\'\}">\s*<span class="px-2 py-0\.5 rounded \$\{isWin \? \'bg-emerald-500/10\' : \'bg-rose-500/10\'\} font-semibold">\s*\$\{isWin \? \'\+\' : \'\'\}\$\$\{Number\(t\.net_pnl_usd\)\.toFixed\(2\)\}\s*</span>\s*</td>',
        new_trade_row_pnl,
        text,
        flags=re.DOTALL
    )

# 10. Also update th-trades-profit text in renderTradesTable start
old_render_trades_start = """    function renderTradesTable(trades) {
      currentFilteredTrades = trades || allTrades;
      const tbody = document.getElementById('trades-table-body');"""

new_render_trades_start = """    function renderTradesTable(trades) {
      currentFilteredTrades = trades || allTrades;
      const tbody = document.getElementById('trades-table-body');
      const thProfit = document.getElementById('th-trades-profit');
      if (thProfit) {
        thProfit.innerText = currentBifocalLens === 'EVALUATION' ? 'Beneficio Neto (Consistencia 40%)' : 'Beneficio Neto (80% Payout)';
      }"""

if old_render_trades_start in text:
    text = text.replace(old_render_trades_start, new_render_trades_start, 1)
    print("10. th-trades-profit header sync updated")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("ALL index.html updates completed successfully!")
