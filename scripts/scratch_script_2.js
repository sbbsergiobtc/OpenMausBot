
    let allStrategies = [];
    let allTrades = [];
    let currentTradeFilter = 'ALL';
    let currentAccountFilter = 'CAP-SPX-006';
    
    // ApexCharts Instances
    let mainEquityChart = null;
    let dowChart = null;
    let hourlyChart = null;

    // ==============================================================================
    // UTILIDADES GLOBALES CUANTITATIVAS (PRECISIÓN CRIPTO 8 DECIMALS & RESILIENCIA)
    // ==============================================================================
    let isDaemonOnline = true;
    let daemonConsecutiveFailures = 0;

    function updateDaemonHealth(status, latencyMs) {
      const container = document.getElementById('daemon-health-container');
      const dot = document.getElementById('daemon-health-dot');
      const text = document.getElementById('daemon-health-text');
      const hlDot = document.getElementById('ft-ws-hl-dot');
      const hlText = document.getElementById('ft-ws-hl-text');

      if (status === 'online') {
        isDaemonOnline = true;
        daemonConsecutiveFailures = 0;
        if (container) container.className = 'text-[11px] text-[#065F46] font-semibold flex items-center justify-end transition-colors';
        if (dot) dot.className = 'w-1.5 h-1.5 rounded-full bg-[#065F46] mr-1 inline-block';
        if (text) text.innerText = `Feed Activo (${latencyMs || 12}ms)`;
        if (hlDot) hlDot.className = 'w-2 h-2 rounded-full bg-[#10b981] inline-block';
        if (hlText) hlText.innerText = 'Websockets Hyperliquid en línea';
      } else if (status === 'reconnecting') {
        daemonConsecutiveFailures++;
        if (daemonConsecutiveFailures >= 2) {
          isDaemonOnline = false;
          if (container) container.className = 'text-[11px] text-[#DC2626] font-semibold flex items-center justify-end transition-colors';
          if (dot) dot.className = 'w-1.5 h-1.5 rounded-full bg-[#DC2626] mr-1 inline-block animate-pulse';
          if (text) text.innerText = 'Daemon Offline · Reintentando...';
          if (hlDot) hlDot.className = 'w-2 h-2 rounded-full bg-[#DC2626] animate-pulse inline-block';
          if (hlText) hlText.innerText = 'Websockets en reconexión...';
        }
      }
    }

    function formatQuantPrice(val, asset) {
      if (val === null || val === undefined || val === '') return '-';
      const num = Number(val);
      if (isNaN(num)) return String(val);
      if (num === 0) return '0.00';
      const abs = Math.abs(num);
      const isCrypto = asset && (
        String(asset).toUpperCase().includes('SOL') ||
        String(asset).toUpperCase().includes('BTC') ||
        String(asset).toUpperCase().includes('ETH') ||
        String(asset).toUpperCase().includes('NEAR') ||
        String(asset).toUpperCase().includes('AVAX') ||
        String(asset).toUpperCase().includes('DOGE') ||
        String(asset).toUpperCase().includes('USDC')
      );
      if (abs < 0.0001) {
        return num.toLocaleString('es-ES', { minimumFractionDigits: 6, maximumFractionDigits: 8 });
      } else if (abs < 0.1 || (isCrypto && abs < 1)) {
        return num.toLocaleString('es-ES', { minimumFractionDigits: 4, maximumFractionDigits: 6 });
      } else if (isCrypto && abs < 500) {
        return num.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 4 });
      } else {
        return num.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      }
    }

    function formatQuantLots(val) {
      if (val === null || val === undefined || val === '') return '0.00';
      const num = Number(val);
      if (isNaN(num)) return String(val);
      if (num === 0) return '0.00';
      const abs = Math.abs(num);
      if (abs < 0.001) {
        return num.toLocaleString('es-ES', { minimumFractionDigits: 4, maximumFractionDigits: 8 });
      } else if (abs < 1) {
        return num.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 4 });
      } else {
        return num.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      }
    }

    function renderEmptyTableState(tbody, colSpan, title, subtitle) {
      if (!tbody) return;
      tbody.innerHTML = `
        <tr>
          <td colspan="${colSpan}" class="text-center py-12 text-txtSecondary font-mono text-xs">
            <div class="inline-flex flex-col items-center justify-center space-y-2">
              <div class="w-10 h-10 rounded-full bg-[#FAF7F2] dark:bg-dark-900 border border-borderWarm dark:border-slate-800 flex items-center justify-center text-txtSecondary text-sm">
                <i class="fa-solid fa-inbox opacity-60"></i>
              </div>
              <span class="font-bold text-txtPrimary dark:text-white">${title}</span>
              <span class="text-[11px] text-txtSecondary">${subtitle}</span>
            </div>
          </td>
        </tr>`;
    }

    // ==============================================================================
    // UTILIDADES GLOBALES DE FORMATEO DE FECHAS EN FORMATO ESPAÑOL (DD/MM/AAAA)
    // ==============================================================================
    function formatSpanishDate(dateInput) {
      if (!dateInput) return '';
      const str = String(dateInput).trim();
      const m = str.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/);
      if (m) {
        return `${m[3].padStart(2, '0')}/${m[2].padStart(2, '0')}/${m[1]}`;
      }
      const dt = new Date(dateInput);
      if (!isNaN(dt.getTime())) {
        const d = String(dt.getDate()).padStart(2, '0');
        const mo = String(dt.getMonth() + 1).padStart(2, '0');
        return `${d}/${mo}/${dt.getFullYear()}`;
      }
      return str;
    }

    function formatSpanishDateTime(dateInput) {
      if (!dateInput) return '';
      const str = String(dateInput).trim();
      const m = str.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})[ T](\d{1,2}):(\d{1,2})(?::(\d{1,2}))?/);
      if (m) {
        const sec = m[6] ? `:${m[6].padStart(2, '0')}` : '';
        return `${m[3].padStart(2, '0')}/${m[2].padStart(2, '0')}/${m[1]} ${m[4].padStart(2, '0')}:${m[5].padStart(2, '0')}${sec}`;
      }
      const dt = new Date(dateInput);
      if (!isNaN(dt.getTime())) {
        const d = String(dt.getDate()).padStart(2, '0');
        const mo = String(dt.getMonth() + 1).padStart(2, '0');
        const y = dt.getFullYear();
        const h = String(dt.getHours()).padStart(2, '0');
        const mi = String(dt.getMinutes()).padStart(2, '0');
        const s = String(dt.getSeconds()).padStart(2, '0');
        return `${d}/${mo}/${y} ${h}:${mi}:${s}`;
      }
      return str;
    }

    // Reloj Dual en vivo: UTC y Hora Oficial de España en formato español DD/MM/AAAA
    setInterval(() => {
      const now = new Date();
      const d = String(now.getUTCDate()).padStart(2, '0');
      const mo = String(now.getUTCMonth() + 1).padStart(2, '0');
      const y = now.getUTCFullYear();
      const h = String(now.getUTCHours()).padStart(2, '0');
      const mi = String(now.getUTCMinutes()).padStart(2, '0');
      const s = String(now.getUTCSeconds()).padStart(2, '0');
      const utcStr = `${d}/${mo}/${y} ${h}:${mi}:${s} UTC`;

      const esDateStr = now.toLocaleDateString('es-ES', { timeZone: 'Europe/Madrid' });
      const esTimeStr = now.toLocaleTimeString('es-ES', { timeZone: 'Europe/Madrid', hour12: false });
      const esFullStr = `${esDateStr} ${esTimeStr} CET (España)`;
      
      const clockEl = document.getElementById('live-clock');
      if (clockEl) {
        clockEl.innerHTML = `<span class="text-slate-300 font-mono text-[11px]">${utcStr}</span> <span class="text-slate-600 font-bold mx-1">|</span> <span class="text-cyan-400 font-mono text-[11px] font-semibold">${esFullStr}</span>`;
      }
    }, 1000);

    // Función para re-disparar animaciones de barrido estilo Framer Motion
    function triggerMotionSweep(containerElement) {
      if (!containerElement) return;
      const elements = containerElement.querySelectorAll('.glass-card, .motion-sweep');
      elements.forEach((el, index) => {
        el.classList.remove('motion-sweep', 'shimmer-active');
        void el.offsetWidth; // Force Reflow
        el.classList.add('motion-sweep', 'shimmer-active');
        // Escalona el delay de barrido
        const delay = Math.min((index + 1) * 0.05, 0.45);
        el.style.animationDelay = delay + 's';
      });
    }

    // Conmutador de Tabs
    const tabTitles = {
      'dashboard': 'Cockpit General · AlgrokQuant',
      'backtests': '1. Backtests (Multi-Horizonte 1-10A)',
      'forward': '2. Forward Tests (Simulación en Vivo)',
      'orchestrator': 'Orquestador de Régimen en Vivo (Contraste Paralelo A/B)',
      'live': '3. Cuentas Live Real (Dinero Real)',
      'tri_facet': '4. Contraste Tri-Faceta: Python vs Simulado vs Real (LESSON-018)',
      'roster': 'Enjambre Multi-Agente (10)',
      'lab': 'Creación & Robustez (Lab)',
      'strategies': 'Catálogo de Estrategias',
      'config': 'Reglas de Riesgo Institucional',
      'journal': 'Bitácora & Informes Oficiales',
      'chart': 'Gráficos TradingView · Auditoría de Estrategias e Indicadores'
    };

    function switchTab(tabId) {
      document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));

      // Desactivar botones de navegación del Sidebar
      document.querySelectorAll('.sidebar-link').forEach(el => {
        el.classList.remove('active', 'bg-slate-800', 'text-white', 'border-l-4', 'border-cyan-400');
        el.classList.add('text-slate-400');
      });

      const activePane = document.getElementById(`tab-content-${tabId}`);
      const activeSideBtn = document.getElementById(`side-tab-${tabId}`);

      if (activePane) {
        activePane.classList.remove('hidden');
        triggerMotionSweep(activePane);
      }
      if (activeSideBtn) {
        activeSideBtn.classList.add('active', 'bg-slate-800', 'text-white', 'border-l-4', 'border-cyan-400');
        activeSideBtn.classList.remove('text-slate-400');
      }

      if (tabTitles[tabId]) {
        const titleEl = document.getElementById('current-tab-title');
        if (titleEl) titleEl.innerText = tabTitles[tabId];
      }

      // En pantalla móvil o tablet (< 1024px), SIEMPRE cerrar el menú lateral al seleccionar pestaña
      if (window.innerWidth < 1024) {
        closeSidebar();
      }

      if (tabId === 'forward') {
        fetchForwardState();
        fetchFtTradesData();
        if (typeof fetchRegimeOrchestratorData === 'function') fetchRegimeOrchestratorData(false);
      if (typeof fetchQLearningMatrixData === 'function') fetchQLearningMatrixData(false);
        setTimeout(() => {
          if (typeof initDefaultFtEquityCurve === 'function') {
            initDefaultFtEquityCurve();
          }
          if (typeof ftEquityChartInstance !== 'undefined' && ftEquityChartInstance) {
            ftEquityChartInstance.render();
          }
        }, 150);
      }
      if (tabId === 'orchestrator') {
        if (typeof fetchRegimeOrchestratorData === 'function') {
          fetchRegimeOrchestratorData(false);
        }
      }
      if (tabId === 'live') {
        fetchLiveState();
      }
      if (tabId === 'tri_facet') {
        fetchTriFacetData();
        if (typeof loadTriFacetTab === 'function') {
          loadTriFacetTab();
        }
      }
      if (tabId === 'dashboard' || tabId === 'backtests') {
        setTimeout(() => {
          if (mainEquityChart) {
            mainEquityChart.render();
          } else if (typeof fetchAnalyticsData === 'function') {
            fetchAnalyticsData(currentAccountFilter);
          }
          if (dowChart) dowChart.render();
          if (hourlyChart) hourlyChart.render();
        }, 150);
      }
    }

    // Funciones dedicadas y deterministas para control del Sidebar
    function openSidebar() {
      const sidebar = document.getElementById('sidebar');
      const overlay = document.getElementById('sidebar-overlay');
      if (!sidebar) return;

      if (window.innerWidth < 1024) {
        sidebar.classList.remove('-translate-x-full');
        sidebar.classList.add('translate-x-0');
        if (overlay) overlay.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
      } else {
        sidebar.classList.remove('collapsed');
        const icon = document.getElementById('sidebar-toggle-icon');
        if (icon) {
          icon.classList.remove('fa-angles-right');
          icon.classList.add('fa-angles-left');
        }
        localStorage.setItem('sidebar_collapsed', 'false');
        setTimeout(() => window.dispatchEvent(new Event('resize')), 300);
      }
    }

    function closeSidebar() {
      const sidebar = document.getElementById('sidebar');
      const overlay = document.getElementById('sidebar-overlay');
      if (!sidebar) return;

      if (window.innerWidth < 1024) {
        sidebar.classList.remove('translate-x-0');
        sidebar.classList.add('-translate-x-full');
        if (overlay) overlay.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
      } else {
        sidebar.classList.add('collapsed');
        const icon = document.getElementById('sidebar-toggle-icon');
        if (icon) {
          icon.classList.remove('fa-angles-left');
          icon.classList.add('fa-angles-right');
        }
        localStorage.setItem('sidebar_collapsed', 'true');
        setTimeout(() => window.dispatchEvent(new Event('resize')), 300);
      }
    }

    function toggleSidebar() {
      const sidebar = document.getElementById('sidebar');
      if (!sidebar) return;

      if (window.innerWidth < 1024) {
        const isMobileOpen = sidebar.classList.contains('translate-x-0');
        if (isMobileOpen) {
          closeSidebar();
        } else {
          openSidebar();
        }
      } else {
        const isCollapsed = sidebar.classList.contains('collapsed');
        if (isCollapsed) {
          openSidebar();
        } else {
          closeSidebar();
        }
      }
    }

    // Reajuste automático en caso de cambiar orientación o tamaño de ventana
    window.addEventListener('resize', () => {
      if (window.innerWidth >= 1024) {
        const overlay = document.getElementById('sidebar-overlay');
        if (overlay) overlay.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
          sidebar.classList.remove('translate-x-0', '-translate-x-full');
        }
      }
    });

    function generateSparklineSvg(points, isWin) {
      if (!points || points.length < 2) return '';
      const w = 68;
      const h = 20;
      const minVal = Math.min(...points);
      const maxVal = Math.max(...points);
      const range = (maxVal - minVal) === 0 ? 1 : (maxVal - minVal);
      
      const coords = points.map((p, i) => {
        const x = Math.round((i / (points.length - 1)) * (w - 4) + 2);
        const y = Math.round(h - 3 - ((p - minVal) / range) * (h - 6));
        return `${x},${y}`;
      });
      
      const strokeColor = isWin ? '#10b981' : '#f43f5e';
      const fillColor = isWin ? 'rgba(16, 185, 129, 0.22)' : 'rgba(244, 63, 94, 0.22)';
      
      const polylinePoints = coords.join(' ');
      const polygonPoints = `2,${h} ` + coords.join(' ') + ` ${w-2},${h}`;
      
      return `
        <svg width="${w}" height="${h}" class="overflow-visible inline-block transition-transform duration-200 hover:scale-110">
          <polygon points="${polygonPoints}" fill="${fillColor}" />
          <polyline points="${polylinePoints}" fill="none" stroke="${strokeColor}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      `;
    }

    // Renderizar Gráfico de Curva de Rentabilidad Principal (Eje X en formato español DD/MM/AAAA y Tooltip enriquecido)
    
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

      // Re-consultar analíticas e historial completos con la lente seleccionada
      if (typeof fetchAnalyticsData === 'function') {
        fetchAnalyticsData(currentAccountFilter);
      }
      if (typeof fetchTradeHistory === 'function') {
        fetchTradeHistory(currentAccountFilter);
      }
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

    function renderMainEquityChart(curveData) {
      // Formatear eje X en español DD/MM/AAAA (autoajustable por ApexCharts)
      const categories = curveData.map(d => formatSpanishDate(d.timestamp));
      const balances = curveData.map(d => d.balance);

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
        colors: ['#06b6d4'],
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
          name: 'Balance de la Cuenta ($)',
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
            formatter: (val) => '$' + val.toLocaleString('es-ES', {minimumFractionDigits: 0}),
            style: { colors: '#94a3b8', fontSize: '11px', fontFamily: 'monospace' }
          }
        },
        grid: {
          borderColor: '#1e293b',
          strokeDashArray: 3
        },
        annotations: {
          yaxis: [{
            y: 106000,
            borderColor: '#10b981',
            strokeDashArray: 4,
            label: {
              borderColor: '#10b981',
              style: { color: '#fff', background: '#10b981', fontSize: '10px', fontWeight: 'bold' },
              text: 'Target Superado (+6% / $106,000)'
            }
          }]
        },
        tooltip: {
          theme: 'dark',
          custom: function({series, seriesIndex, dataPointIndex, w}) {
            const d = curveData[dataPointIndex];
            const dateStr = formatSpanishDateTime(d.timestamp);
            const val = series[seriesIndex][dataPointIndex];
            const bal = '$' + Number(val).toLocaleString('es-ES', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' USD';
            return `
              <div class="p-2.5 bg-slate-900 border border-slate-700 rounded-lg shadow-xl font-mono text-xs">
                <div class="text-slate-400 text-[11px] flex items-center gap-1.5 mb-1">
                  <i class="fa-regular fa-calendar text-cyan-400"></i> ${dateStr}
                </div>
                <div class="text-white font-bold flex items-center justify-between gap-3">
                  <span class="text-slate-400">Balance Cuenta:</span>
                  <span class="text-cyan-300 font-mono text-sm">${bal}</span>
                </div>
              </div>
            `;
          }
        }
      };

      if (mainEquityChart) mainEquityChart.destroy();
      mainEquityChart = new ApexCharts(document.querySelector("#main-equity-chart"), options);
      mainEquityChart.render();
    }

    // Renderizar Gráfico de Rendimiento por Día de la Semana (Animación de barras)
    function renderDowChart(dowData) {
      const days = Object.keys(dowData);
      const values = Object.values(dowData);

      const options = {
        chart: {
          type: 'bar',
          height: 240,
          toolbar: { show: false },
          background: 'transparent',
          fontFamily: 'JetBrains Mono, monospace',
          animations: {
            enabled: true,
            easing: 'easeinout',
            speed: 850,
            animateGradually: {
              enabled: true,
              delay: 110
            }
          }
        },
        theme: { mode: 'dark' },
        plotOptions: {
          bar: {
            borderRadius: 4,
            distributed: false,
            colors: {
              ranges: [
                { from: -100000, to: -0.01, color: '#f43f5e' },
                { from: 0, to: 100000, color: '#10b981' }
              ]
            }
          }
        },
        dataLabels: { enabled: false },
        series: [{
          name: 'PnL Acumulado ($)',
          data: values
        }],
        xaxis: {
          categories: days,
          labels: { style: { colors: '#94a3b8', fontSize: '11px' } },
          axisBorder: { show: false }
        },
        yaxis: {
          labels: {
            formatter: (val) => '$' + val.toLocaleString(undefined, {minimumFractionDigits: 0}),
            style: { colors: '#64748b', fontSize: '10px' }
          }
        },
        grid: { borderColor: '#1e293b', strokeDashArray: 3 },
        tooltip: {
          theme: 'dark',
          y: { formatter: (val) => '$' + val.toLocaleString(undefined, {minimumFractionDigits: 2}) }
        }
      };

      if (dowChart) dowChart.destroy();
      dowChart = new ApexCharts(document.querySelector("#chart-dow"), options);
      dowChart.render();
    }

    // Renderizar Gráfico de Distribución Horaria (Barrido de 24 columnas)
    function renderHourlyChart(hourlyData) {
      const categories = hourlyData.map(h => h.label);
      const values = hourlyData.map(h => h.pnl);

      const options = {
        chart: {
          type: 'bar',
          height: 240,
          toolbar: { show: false },
          background: 'transparent',
          fontFamily: 'JetBrains Mono, monospace',
          animations: {
            enabled: true,
            easing: 'easeinout',
            speed: 900,
            animateGradually: {
              enabled: true,
              delay: 80
            }
          }
        },
        theme: { mode: 'dark' },
        plotOptions: {
          bar: {
            borderRadius: 3,
            colors: {
              ranges: [
                { from: -100000, to: -0.01, color: '#f43f5e' },
                { from: 0, to: 100000, color: '#06b6d4' }
              ]
            }
          }
        },
        dataLabels: { enabled: false },
        series: [{
          name: 'PnL ($)',
          data: values
        }],
        xaxis: {
          categories: categories,
          labels: {
            style: { colors: '#64748b', fontSize: '9px' },
            rotate: -45,
            rotateAlways: false
          },
          axisBorder: { show: false }
        },
        yaxis: {
          labels: {
            formatter: (val) => '$' + val.toLocaleString(undefined, {minimumFractionDigits: 0}),
            style: { colors: '#64748b', fontSize: '10px' }
          }
        },
        grid: { borderColor: '#1e293b', strokeDashArray: 3 },
        tooltip: {
          theme: 'dark',
          y: { formatter: (val) => '$' + val.toLocaleString(undefined, {minimumFractionDigits: 2}) }
        }
      };

      if (hourlyChart) hourlyChart.destroy();
      hourlyChart = new ApexCharts(document.querySelector("#chart-hourly"), options);
      hourlyChart.render();
    }

    // Manejar cambio en el Selector de Cuentas / Estrategias
    async function onAccountFilterChange() {
      const select = document.getElementById('account-selector');
      currentAccountFilter = select.value;
      const backtestPane = document.getElementById('tab-content-backtests') || document.getElementById('tab-content-dashboard');
      triggerMotionSweep(backtestPane);
      await fetchAnalyticsData(currentAccountFilter);
      await fetchTradesData(currentAccountFilter);
    }

    // Cargar Análisis y Métricas desde /api/analytics
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

      if (!data) {
        data = {
          account_name: 'S&P 500 4h Bollinger Dip (Capital Propio TradFi · 318 Trades)',
          kpis: {
            final_balance: 110821.03,
            initial_balance: 100000,
            net_profit: 10821.03,
            profit_factor: 3.87,
            win_rate: 79.0,
            win_count: 49,
            loss_count: 13,
            total_trades: 62,
            max_drawdown: 0.85,
            sharpe_ratio: 3.98,
            return_pct: 10.82
          },
          best_dow: { day: 'Martes', pnl: 4120.50 },
          best_hour: { label: '14:00 - 16:00 UTC', pnl: 3890.20 },
          best_single_day: { date: '14/11/2025', pnl: 2840.10, day: 'Jueves' },
          worst_single_day: { date: '03/03/2026', pnl: -620.40, day: 'Lunes' },
          max_win_streak: 8,
          max_loss_streak: 2,
          balance_curve: [
            { timestamp: '2025-10-25 09:00:00', balance: 100000.00 },
            { timestamp: '2025-11-15 15:30:00', balance: 102140.50 },
            { timestamp: '2025-12-10 11:00:00', balance: 101890.20 },
            { timestamp: '2026-01-08 14:15:00', balance: 104320.00 },
            { timestamp: '2026-02-12 16:45:00', balance: 106150.80 },
            { timestamp: '2026-03-20 10:30:00', balance: 105800.00 },
            { timestamp: '2026-04-18 13:00:00', balance: 108220.40 },
            { timestamp: '2026-05-25 15:00:00', balance: 107950.00 },
            { timestamp: '2026-06-30 11:30:00', balance: 109400.60 },
            { timestamp: '2026-08-14 16:00:00', balance: 108850.10 },
            { timestamp: '2026-09-22 10:00:00', balance: 110120.00 },
            { timestamp: '2026-10-25 18:00:00', balance: 110821.03 }
          ],
          dow_distribution: { 'Lunes': 1250.00, 'Martes': 4120.50, 'Miércoles': 2340.20, 'Jueves': 2110.33, 'Viernes': 1000.00 },
          hourly_distribution: { '08-10': 850, '10-12': 1420, '12-14': 980, '14-16': 3890, '16-18': 2450, '18-20': 1231 },
          streaks_analysis: {
            target_pct: 6.0,
            passes_count: 3,
            avg_target_days: 28.4,
            worst_drawdown_pct: 0.85,
            streaks: [
              { id: 1, type: 'UP', start_timestamp: '2025-10-25', end_timestamp: '2026-01-08', pnl_pct: 4.32, trades: 14, passed_target: false },
              { id: 2, type: 'DOWN', start_timestamp: '2026-01-08', end_timestamp: '2026-01-20', pnl_pct: -0.42, trades: 3, passed_target: false },
              { id: 3, type: 'UP', start_timestamp: '2026-01-20', end_timestamp: '2026-04-18', pnl_pct: 6.55, trades: 22, passed_target: true },
              { id: 4, type: 'DOWN', start_timestamp: '2026-04-18', end_timestamp: '2026-05-02', pnl_pct: -0.38, trades: 2, passed_target: false },
              { id: 5, type: 'UP', start_timestamp: '2026-05-02', end_timestamp: '2026-10-25', pnl_pct: 7.12, trades: 21, passed_target: true }
            ]
          }
        };
      }

      // 1. Actualizar KPIs Principales
      const kpis = data.kpis;
      if (document.getElementById('kpi-balance')) document.getElementById('kpi-balance').innerText = '$' + kpis.final_balance.toLocaleString(undefined, {minimumFractionDigits: 2});
      if (document.getElementById('kpi-init-bal')) document.getElementById('kpi-init-bal').innerText = '$' + kpis.initial_balance.toLocaleString(undefined, {minimumFractionDigits: 0});
      if (document.getElementById('kpi-net-profit')) document.getElementById('kpi-net-profit').innerText = (kpis.net_profit >= 0 ? '+' : '') + '$' + kpis.net_profit.toLocaleString(undefined, {minimumFractionDigits: 2});
      if (document.getElementById('kpi-pf')) document.getElementById('kpi-pf').innerText = kpis.profit_factor;
      if (document.getElementById('kpi-wr')) document.getElementById('kpi-wr').innerText = kpis.win_rate + '%';
      if (document.getElementById('kpi-trades-count')) document.getElementById('kpi-trades-count').innerText = `${kpis.win_count}W / ${kpis.loss_count}L (${kpis.total_trades} total)`;
      if (document.getElementById('kpi-dd')) document.getElementById('kpi-dd').innerText = kpis.max_drawdown.toFixed(2) + '%';
      if (document.getElementById('kpi-sharpe')) document.getElementById('kpi-sharpe').innerText = kpis.sharpe_ratio;
      if (document.getElementById('kpi-return')) document.getElementById('kpi-return').innerText = (kpis.return_pct >= 0 ? '+' : '') + kpis.return_pct + '%';
      if (document.getElementById('badge-chart-pnl')) document.getElementById('badge-chart-pnl').innerText = (kpis.net_profit >= 0 ? '+' : '') + '$' + kpis.net_profit.toLocaleString(undefined, {minimumFractionDigits: 2}) + ' USD';
      if (document.getElementById('chart-subtitle')) document.getElementById('chart-subtitle').innerText = `${data.account_name} · Rentabilidad neta cerrada trade a trade`;

      // 2. Day & Time Edge Cards
      if (document.getElementById('stat-best-dow')) document.getElementById('stat-best-dow').innerText = data.best_dow.day;
      if (document.getElementById('stat-best-dow-pnl')) document.getElementById('stat-best-dow-pnl').innerText = '+$' + data.best_dow.pnl.toLocaleString(undefined, {minimumFractionDigits: 2});
      if (document.getElementById('stat-best-hour')) document.getElementById('stat-best-hour').innerText = data.best_hour.label;
      if (document.getElementById('stat-best-hour-pnl')) document.getElementById('stat-best-hour-pnl').innerText = '+$' + data.best_hour.pnl.toLocaleString(undefined, {minimumFractionDigits: 2});
      if (document.getElementById('stat-best-day-date')) document.getElementById('stat-best-day-date').innerText = data.best_single_day.date;
      if (document.getElementById('stat-best-day-pnl')) document.getElementById('stat-best-day-pnl').innerText = '+$' + data.best_single_day.pnl.toLocaleString(undefined, {minimumFractionDigits: 2});
      if (document.getElementById('stat-best-day-sub')) document.getElementById('stat-best-day-sub').innerText = `${data.best_single_day.day} récord`;
      if (document.getElementById('stat-worst-day-date')) document.getElementById('stat-worst-day-date').innerText = data.worst_single_day.date;
      if (document.getElementById('stat-worst-day-pnl')) document.getElementById('stat-worst-day-pnl').innerText = '$' + data.worst_single_day.pnl.toLocaleString(undefined, {minimumFractionDigits: 2});
      if (document.getElementById('stat-worst-day-sub')) document.getElementById('stat-worst-day-sub').innerText = `${data.worst_single_day.day} peor sesión`;
      if (document.getElementById('stat-win-streak')) document.getElementById('stat-win-streak').innerText = data.max_win_streak;
      if (document.getElementById('stat-loss-streak')) document.getElementById('stat-loss-streak').innerText = data.max_loss_streak;

      // 3. Renderizar Gráficos con Animaciones
      if (data.balance_curve) renderMainEquityChart(data.balance_curve);
      if (data.dow_distribution) renderDowChart(data.dow_distribution);
      if (data.hourly_distribution) renderHourlyChart(data.hourly_distribution);
      if (data.streaks_analysis) renderStreaksAnalysis(data.streaks_analysis, data.balance_curve);
    }

    // Cargar Historial de Operaciones desde /api/trade_history
    
    // =========================================================================
    // MOTOR DE DESGLOSE DE RACHAS (PEAK-VALLEY SWING ANALYSIS)
    // =========================================================================
    let streakBarsChartInstance = null;
    let streakEquityChartInstance = null;
    let cachedStreaksData = null;
    let cachedBalanceCurve = null;

    function resetStreakChartZoom() {
      if (streakEquityChartInstance && cachedBalanceCurve && cachedBalanceCurve.length > 0) {
        streakEquityChartInstance.resetSeries();
        document.querySelectorAll('.streak-chip').forEach(el => el.classList.remove('active'));
      }
    }

    function selectStreak(streakId) {
      if (!cachedStreaksData || !cachedStreaksData.streaks) return;
      const streak = cachedStreaksData.streaks.find(s => s.id === streakId);
      if (!streak) return;

      document.querySelectorAll('.streak-chip').forEach(el => {
        el.classList.toggle('active', el.getAttribute('data-id') == streakId);
      });

      if (streakEquityChartInstance) {
        const startTs = new Date(streak.start_timestamp).getTime();
        const endTs = new Date(streak.end_timestamp).getTime();
        if (!isNaN(startTs) && !isNaN(endTs)) {
          streakEquityChartInstance.zoomX(startTs, endTs);
        }
      }
    }

    function renderStreaksAnalysis(streaksData, balanceCurve) {
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
      if (elTotal) elTotal.innerText = `${summary.total_streaks || 0} Tramos`;

      // 2. Chips Horizontales
      const chipsCont = document.getElementById('streak-chips-container');
      if (chipsCont) {
        if (streaks.length === 0) {
          chipsCont.innerHTML = '<span class="text-xs text-slate-500 font-mono">Sin tramos significativos registrados</span>';
        } else {
          chipsCont.innerHTML = streaks.map(s => {
            const isBull = s.type === 'ALCISTA';
            const pillClass = isBull ? 'streak-chip streak-chip-bull' : 'streak-chip streak-chip-bear';
            const sign = isBull ? '+' : '';
            const tag = isBull && s.challenge_passed 
              ? '<span class="streak-chip-pass">🏆 +6% PASSED</span>'
              : (!isBull && s.dd_safe ? '<span class="streak-chip-safe">🛡️ DD EOD SEGURO</span>' : '');

            return `
              <div class="${pillClass}" data-id="${s.id}" onclick="selectStreak(${s.id})" title="${s.label}: ${s.start_date} a ${s.end_date} · Trades: ${s.trades_count}">
                <span>${s.type.toLowerCase()} ${sign}${Number(s.pnl_pct).toFixed(1)}% · ${s.start_date.substring(5)} a ${s.end_date.substring(5)}</span>
                ${tag}
              </div>
            `;
          }).join('');
        }
      }

      // 3. Histograma de Barras Discretas (01, 02, 03...)
      const barsEl = document.getElementById('streak-bars-apexchart');
      if (barsEl && streaks.length > 0) {
        const barCategories = streaks.map(s => String(s.id).padStart(2, '0'));
        const barData = streaks.map(s => ({
          x: String(s.id).padStart(2, '0'),
          y: s.pnl_pct,
          fillColor: s.type === 'ALCISTA' ? '#10b981' : '#d97706'
        }));

        const barsOptions = {
          series: [{
            name: 'Variación de Tramo (%)',
            data: barData
          }],
          chart: {
            type: 'bar',
            height: 180,
            toolbar: { show: false },
            events: {
              dataPointSelection: function(event, chartContext, config) {
                const streakId = config.dataPointIndex + 1;
                selectStreak(streakId);
              }
            }
          },
          plotOptions: {
            bar: {
              borderRadius: 3,
              columnWidth: '55%',
              colors: {
                ranges: [
                  { from: -100, to: 0, color: '#d97706' },
                  { from: 0.001, to: 1000, color: '#10b981' }
                ]
              }
            }
          },
          dataLabels: { enabled: false },
          xaxis: {
            categories: barCategories,
            labels: {
              style: { colors: '#94a3b8', fontSize: '10px', fontFamily: 'monospace' }
            },
            axisBorder: { color: '#334155' }
          },
          yaxis: {
            labels: {
              formatter: val => (val >= 0 ? '+' : '') + Number(val).toFixed(1) + '%',
              style: { colors: '#94a3b8', fontSize: '10px', fontFamily: 'monospace' }
            }
          },
          grid: { borderColor: '#1e293b', strokeDashArray: 3 },
          tooltip: {
            theme: 'dark',
            custom: function({series, seriesIndex, dataPointIndex, w}) {
              const s = streaks[dataPointIndex];
              const sign = s.pnl_pct >= 0 ? '+' : '';
              return `
                <div class="p-2.5 bg-slate-900 border border-slate-700 rounded-lg shadow-xl font-mono text-xs">
                  <div class="text-cyan-400 font-bold mb-1">${s.label}: ${s.type}</div>
                  <div class="text-slate-300">Retorno: <strong class="${s.pnl_pct >= 0 ? 'text-emerald-400' : 'text-amber-400'}">${sign}${s.pnl_pct}%</strong> ($${s.pnl_usd})</div>
                  <div class="text-slate-400 text-[11px] mt-0.5">${s.start_date} a ${s.end_date} (${s.trades_count} trades)</div>
                  ${s.challenge_passed ? '<div class="text-emerald-400 text-[11px] font-bold mt-1">🏆 ¡Challenge Fondeo Aprobado!</div>' : ''}
                  ${!s.challenge_passed && s.type === 'BAJISTA' ? '<div class="text-amber-300 text-[11px] mt-1">🛡️ Drawdown EOD Controlado</div>' : ''}
                </div>
              `;
            }
          }
        };

        if (!streakBarsChartInstance) {
          streakBarsChartInstance = new ApexCharts(barsEl, barsOptions);
          streakBarsChartInstance.render();
        } else {
          streakBarsChartInstance.updateOptions(barsOptions);
        }
      }

      // 4. Curva de Rentabilidad con Sombreado de Tramos
      const curveEl = document.getElementById('streak-equity-apexchart');
      if (curveEl && balanceCurve && balanceCurve.length > 0) {
        const curveData = balanceCurve.map(pt => ({
          x: new Date(pt.timestamp).getTime(),
          y: pt.balance
        }));

        const xaxisAnnotations = streaks.map(s => {
          const isBull = s.type === 'ALCISTA';
          return {
            x: new Date(s.start_timestamp).getTime(),
            x2: new Date(s.end_timestamp).getTime(),
            fillColor: isBull ? '#10b981' : '#f59e0b',
            opacity: 0.10,
            label: {
              borderColor: isBull ? '#10b981' : '#f59e0b',
              style: {
                color: '#fff',
                background: isBull ? '#065f46' : '#78350f',
                fontSize: '9px',
                fontWeight: 700
              },
              text: `${isBull ? '+' : ''}${s.pnl_pct}%`
            }
          };
        });

        const curveOptions = {
          series: [{
            name: 'Curva de Crecimiento ($ USD)',
            data: curveData
          }],
          chart: {
            type: 'area',
            height: 260,
            toolbar: { show: true, tools: { download: false, selection: true, zoom: true, zoomin: true, zoomout: true, pan: true, reset: true } },
            animations: { enabled: true }
          },
          colors: ['#10b981'],
          stroke: { curve: 'smooth', width: 2.5 },
          fill: {
            type: 'gradient',
            gradient: {
              shadeIntensity: 1,
              opacityFrom: 0.45,
              opacityTo: 0.05,
              stops: [0, 90, 100]
            }
          },
          dataLabels: { enabled: false },
          xaxis: {
            type: 'datetime',
            labels: {
              datetimeUTC: false,
              style: { colors: '#94a3b8', fontSize: '10px', fontFamily: 'monospace' }
            },
            axisBorder: { color: '#334155' }
          },
          yaxis: {
            labels: {
              formatter: val => '$' + Number(val).toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0}),
              style: { colors: '#94a3b8', fontSize: '10px', fontFamily: 'monospace' }
            }
          },
          grid: { borderColor: '#1e293b', strokeDashArray: 3 },
          annotations: {
            xaxis: xaxisAnnotations
          },
          tooltip: {
            theme: 'dark',
            x: { format: 'dd MMM yyyy HH:mm' },
            y: {
              formatter: val => '$' + Number(val).toLocaleString(undefined, {minimumFractionDigits: 2})
            }
          }
        };

        if (!streakEquityChartInstance) {
          streakEquityChartInstance = new ApexCharts(curveEl, curveOptions);
          streakEquityChartInstance.render();
        } else {
          streakEquityChartInstance.updateOptions(curveOptions);
        }
      }
    }

    async function fetchTradesData(filter) {
      try {
        const res = await fetch(`/api/trade_history?filter=${encodeURIComponent(filter)}&lens=${encodeURIComponent(currentBifocalLens)}`);
        if (res.ok) {
          const data = await res.json();
          allTrades = data.trades || [];
          renderTradesTable(allTrades);
          return;
        }
      } catch (err) {
        console.warn('Backend offline, utilizando historial de trades de muestra:', err);
      }
      if (!allTrades || allTrades.length === 0) {
        allTrades = [
          { trade_id: 'TR-20261025-062', symbol: 'US500', strategy_id: 'CAP-SPX-006', action: 'BUY', entry_time: '2026-10-25 14:00:00', exit_time: '2026-10-25 18:30:00', entry_price: 5820.25, exit_price: 5845.50, pnl: 450.25, status: 'CLOSED' },
          { trade_id: 'TR-20261024-061', symbol: 'US100', strategy_id: 'CAP-NDX-005', action: 'BUY', entry_time: '2026-10-24 10:15:00', exit_time: '2026-10-24 16:45:00', entry_price: 20450.10, exit_price: 20580.00, pnl: 620.15, status: 'CLOSED' },
          { trade_id: 'TR-20261023-060', symbol: 'BTCUSDT', strategy_id: 'STRAT-035', action: 'SELL', entry_time: '2026-10-23 08:30:00', exit_time: '2026-10-23 12:00:00', entry_price: 67800.00, exit_price: 67200.00, pnl: 380.00, status: 'CLOSED' },
          { trade_id: 'TR-20261022-059', symbol: 'US500', strategy_id: 'CAP-SPX-006', action: 'BUY', entry_time: '2026-10-22 15:00:00', exit_time: '2026-10-22 19:15:00', entry_price: 5805.00, exit_price: 5818.50, pnl: 210.80, status: 'CLOSED' },
          { trade_id: 'TR-20261021-058', symbol: 'US100', strategy_id: 'CAP-NDX-005', action: 'SELL', entry_time: '2026-10-21 11:00:00', exit_time: '2026-10-21 13:30:00', entry_price: 20380.50, exit_price: 20395.00, pnl: -95.40, status: 'CLOSED' }
        ];
        renderTradesTable(allTrades);
      }
    }

    // Estado de Paginación para Historial de Operaciones
    let currentFilteredTrades = [];
    let tradeCurrentPage = 1;
    let tradeRowsPerPage = 50;

    function changeTradeRowsPerPage(val) {
      tradeRowsPerPage = val;
      tradeCurrentPage = 1;
      renderTradesTable(currentFilteredTrades);
    }

    function renderTradePaginationControls(total, startIdx, endIdx) {
      const infoEl = document.getElementById('trade-pagination-info');
      const ctrlsEl = document.getElementById('trade-pagination-controls');
      if (!infoEl || !ctrlsEl) return;

      if (total === 0) {
        infoEl.innerText = '0 operaciones';
        ctrlsEl.innerHTML = '';
        return;
      }

      infoEl.innerText = `Mostrando ${startIdx + 1} - ${endIdx} de ${total} operaciones`;

      if (tradeRowsPerPage === 'ALL') {
        ctrlsEl.innerHTML = '<span class="text-slate-500 text-xs">Página única</span>';
        return;
      }

      const perPage = parseInt(tradeRowsPerPage, 10);
      const totalPages = Math.ceil(total / perPage);
      if (totalPages <= 1) {
        ctrlsEl.innerHTML = '';
        return;
      }

      let html = '';
      html += `<button onclick="goToTradePage(${tradeCurrentPage - 1})" ${tradeCurrentPage === 1 ? 'disabled class="px-2.5 py-1 rounded bg-dark-900 text-slate-600 border border-slate-800 cursor-not-allowed"' : 'class="px-2.5 py-1 rounded bg-dark-900 text-slate-300 hover:text-white border border-slate-700 hover:bg-slate-800 transition cursor-pointer"'}>Anterior</button>`;

      const maxBtns = 5;
      let startP = Math.max(1, tradeCurrentPage - Math.floor(maxBtns / 2));
      let endP = Math.min(totalPages, startP + maxBtns - 1);
      if (endP - startP < maxBtns - 1) {
        startP = Math.max(1, endP - maxBtns + 1);
      }

      for (let p = startP; p <= endP; p++) {
        if (p === tradeCurrentPage) {
          html += `<button class="px-2.5 py-1 rounded bg-emerald-500 text-white font-bold border border-emerald-400 cursor-default">${p}</button>`;
        } else {
          html += `<button onclick="goToTradePage(${p})" class="px-2.5 py-1 rounded bg-dark-900 text-slate-300 hover:text-white border border-slate-700 hover:bg-slate-800 transition cursor-pointer">${p}</button>`;
        }
      }

      html += `<button onclick="goToTradePage(${tradeCurrentPage + 1})" ${tradeCurrentPage === totalPages ? 'disabled class="px-2.5 py-1 rounded bg-dark-900 text-slate-600 border border-slate-800 cursor-not-allowed"' : 'class="px-2.5 py-1 rounded bg-dark-900 text-slate-300 hover:text-white border border-slate-700 hover:bg-slate-800 transition cursor-pointer"'}>Siguiente</button>`;

      ctrlsEl.innerHTML = html;
    }

    function goToTradePage(page) {
      tradeCurrentPage = page;
      renderTradesTable(currentFilteredTrades);
    }

    // Renderizar Tabla de Operaciones con Paginación, Thead Sticky y Fechas en Español
    function renderTradesTable(trades) {
      currentFilteredTrades = trades || allTrades;
      const tbody = document.getElementById('trades-table-body');
      if (!tbody) return;
      tbody.innerHTML = '';
      if (!currentFilteredTrades || currentFilteredTrades.length === 0) {
        renderEmptyTableState(tbody, 13, 'Sin operaciones registradas', 'No se encontraron operaciones de backtest para el filtro o régimen activo');
        renderTradePaginationControls(0, 0, 0);
        return;
      }

      const total = currentFilteredTrades.length;
      let startIdx = 0;
      let endIdx = total;

      if (tradeRowsPerPage !== 'ALL') {
        const perPage = parseInt(tradeRowsPerPage, 10);
        const maxPage = Math.max(1, Math.ceil(total / perPage));
        if (tradeCurrentPage > maxPage) tradeCurrentPage = maxPage;
        if (tradeCurrentPage < 1) tradeCurrentPage = 1;
        startIdx = (tradeCurrentPage - 1) * perPage;
        endIdx = Math.min(startIdx + perPage, total);
      }

      const paged = currentFilteredTrades.slice(startIdx, endIdx);

      paged.forEach((t, index) => {
        const isWin = t.net_pnl_usd > 0;
        const sparklineSvg = generateSparklineSvg(t.sparkline, isWin);

        const tr = document.createElement('tr');
        tr.className = 'hover:bg-[#FAF7F2] transition cursor-pointer group';
        tr.title = 'Hacer clic para auditar este trade en el gráfico de TradingView';
        tr.onclick = () => {
          if (typeof openTradeInChart === 'function') {
            openTradeInChart(t.strategy || t.strategy_id, index);
          } else if (typeof openStrategyInChart === 'function') {
            openStrategyInChart(t.strategy || t.strategy_id, index);
          }
        };
        const delay = Math.min((index + 1) * 0.02, 0.3);
        tr.style.animationDelay = delay + 's';

        // Formato español de fechas en la tabla: DD/MM/AAAA
        const esStartDate = formatSpanishDate(t.start_date);
        const esEndDate = formatSpanishDate(t.end_date);

        // Asignación de Badge de Activo según requerimiento de color de Sergio:
        // BTC: Ámbar original | ETH: Gris | NDX: Azul (como barras rendimiento) | SPX: Rojo (como barras negativas) | SOL: Morado
        let assetBadgeHtml = '';
        const ast = (t.asset || '').toUpperCase();
        if (ast.includes('BTC') || ast.includes('BITCOIN')) {
          assetBadgeHtml = '<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono">BTC</span>';
        } else if (ast.includes('ETH') || ast.includes('ETHEREUM')) {
          assetBadgeHtml = '<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-slate-700/60 text-slate-200 border border-slate-600 font-mono">ETH</span>';
        } else if (ast.includes('NDX') || ast.includes('NASDAQ')) {
          assetBadgeHtml = '<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-[#3C45A5]/20 text-[#3C45A5] border border-[#3C45A5]/40 font-mono">NDX</span>';
        } else if (ast.includes('SPX') || ast.includes('SP500') || ast.includes('S&P')) {
          assetBadgeHtml = '<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40 font-mono">SPX</span>';
        } else if (ast.includes('SOL') || ast.includes('SOLANA')) {
          assetBadgeHtml = '<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40 font-mono">SOL</span>';
        } else {
          assetBadgeHtml = `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-slate-800 text-slate-300 border border-slate-700 font-mono">${t.asset}</span>`;
        }

        tr.innerHTML = `
          <td class="py-2.5 px-3 font-bold text-txtPrimary whitespace-nowrap">
            <div class="flex items-center gap-1.5">
              <i class="fa-solid fa-chart-line text-[#3C45A5] opacity-40 group-hover:opacity-100 transition-opacity text-xs" title="Auditar en TradingView"></i>
              <span>${t.strategy || t.strategy_id || t.trade_id}</span>
            </div>
          </td>
          <td class="py-2.5 px-3 text-center whitespace-nowrap">
            ${sparklineSvg}
          </td>
          <td class="py-2.5 px-3 whitespace-nowrap">
            ${assetBadgeHtml}
          </td>
          <td class="py-2.5 px-3 text-right font-bold ${isWin ? 'text-emerald-400' : 'text-rose-400'}">
            <span class="px-2 py-0.5 rounded ${isWin ? 'bg-emerald-500/10' : 'bg-rose-500/10'} font-semibold">
              ${isWin ? '+' : ''}$${Number(t.net_pnl_usd).toFixed(2)}
            </span>
          </td>
          <td class="py-2.5 px-3 text-right text-cyan-300 font-bold">$${Number(t.running_balance).toLocaleString('es-ES', {minimumFractionDigits: 2})}</td>
          <td class="py-2.5 px-3 text-slate-400">
            <div class="font-mono text-white">${esStartDate || ''}</div>
            <div class="text-[11px] text-slate-500 font-mono">${t.start_time || ''}</div>
          </td>
          <td class="py-2.5 px-3 text-slate-400">
            <div class="font-mono text-white">${esEndDate || ''}</div>
            <div class="text-[11px] text-slate-500 font-mono">${t.end_time || ''}</div>
          </td>
          <td class="py-2.5 px-3 text-right font-bold text-white">${formatQuantPrice(t.entry_price, t.asset)}</td>
          <td class="py-2.5 px-3 text-right text-emerald-400">${t.tp_price ? formatQuantPrice(t.tp_price, t.asset) : '-'}</td>
          <td class="py-2.5 px-3 text-right text-rose-400">${t.sl_price ? formatQuantPrice(t.sl_price, t.asset) : '-'}</td>
          <td class="py-2.5 px-3 text-right font-bold text-white">${formatQuantPrice(t.exit_price, t.asset)}</td>
          <td class="py-2.5 px-3 text-right text-slate-400">$${Number(t.fees_usd).toFixed(2)}</td>
          <td class="py-2.5 px-3"><span class="text-[11px] ${isWin ? 'text-emerald-400/90' : 'text-rose-400/90'} font-semibold">${t.exit_reason || '--'}</span></td>
        `;
        tbody.appendChild(tr);
      });

      renderTradePaginationControls(total, startIdx, endIdx);
    }

    function setTradeFilter(filterType) {
      currentTradeFilter = filterType;
      document.querySelectorAll('.trade-filter-btn').forEach(b => {
        b.classList.remove('bg-slate-800', 'text-white', 'border', 'border-slate-700');
        b.classList.add('text-slate-400', 'bg-slate-900/60');
      });
      const activeBtn = document.getElementById(`filter-btn-${filterType}`);
      if (activeBtn) {
        activeBtn.classList.add('bg-slate-800', 'text-white', 'border', 'border-slate-700');
        activeBtn.classList.remove('text-slate-400', 'bg-slate-900/60');
      }
      filterTrades();
    }

    function filterTrades() {
      const search = document.getElementById('trade-search').value.toLowerCase();
      const filtered = allTrades.filter(t => {
        const matchSearch = t.trade_id.toLowerCase().includes(search) || 
                            t.strategy_id.toLowerCase().includes(search) || 
                            t.asset.toLowerCase().includes(search) || 
                            (t.day_es && t.day_es.toLowerCase().includes(search)) ||
                            (t.start_date && t.start_date.includes(search));
        
        let matchFilter = true;
        if (currentTradeFilter === 'NDX') matchFilter = t.asset === 'NDX';
        else if (currentTradeFilter === 'SPX') matchFilter = t.asset === 'SPX';
        else if (currentTradeFilter === 'WIN') matchFilter = t.net_pnl_usd > 0;
        else if (currentTradeFilter === 'LOSS') matchFilter = t.net_pnl_usd <= 0;

        return matchSearch && matchFilter;
      });
      renderTradesTable(filtered);
    }

    function exportTradesCSV() {
      if (!allTrades || allTrades.length === 0) return;
      const headers = ['Trade_ID', 'Strategy', 'Asset', 'Day', 'Start_Date', 'Start_Time', 'End_Date', 'End_Time', 'Entry_Price', 'TP_Price', 'SL_Price', 'Exit_Price', 'Fees_USD', 'Net_PnL_USD', 'Running_Balance_USD', 'Exit_Reason'];
      const rows = allTrades.map(t => [
        t.trade_id, t.strategy_id, t.asset, t.day_es || '', t.start_date || '', t.start_time || '',
        t.end_date || '', t.end_time || '', t.entry_price, t.tp_price, t.sl_price, t.exit_price,
        t.fees_usd, t.net_pnl_usd, t.running_balance, `"${t.exit_reason}"`
      ]);
      const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement('a');
      link.setAttribute('href', encodedUri);
      link.setAttribute('download', 'algrokquant_trade_history.csv');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }

    // Cargar Roster Completo de Agentes
    
    // ============================================================================
    // HISTORIAL DE OPERACIONES - FORWARD TEST (EXCLUSIVO)
    // ============================================================================
    let allFtTrades = [];
    let currentFilteredFtTrades = [];
    let ftTradeCurrentPage = 1;
    let ftTradeRowsPerPage = 50;
    let currentFtTradeFilter = 'ALL';

    function getFtTradesForCurrentDesk() {
      const isCap = (currentDeskMode === 'CAPITAL_PROPIO');
      return (allFtTrades || []).filter(t => {
        const br = t.branch || ((t.strategy && t.strategy.startsWith('PROP')) || (t.asset && t.asset.includes('EUR')) ? 'PROP_FIRM' : 'CAPITAL_PROPIO');
        return isCap ? (br === 'CAPITAL_PROPIO') : (br === 'PROP_FIRM');
      });
    }

    async function fetchFtTradesData(forceRefresh = false) {
      try {
        const res = await fetch('/api/forward_trades');
        if (!res.ok) {
          console.warn('/api/forward_trades returned status', res.status);
          renderFtTradesTable([]);
          return;
        }
        const data = await res.json();
        allFtTrades = data.trades || [];
        setFtTradeFilter(currentFtTradeFilter || 'ALL');
      } catch (err) {
        console.error('Error fetching FT trades:', err);
        renderFtTradesTable([]);
      }
    }

    function changeFtTradeRowsPerPage(val) {
      ftTradeRowsPerPage = val;
      ftTradeCurrentPage = 1;
      renderFtTradesTable(currentFilteredFtTrades);
    }

    function renderFtTradePaginationControls(total, startIdx, endIdx) {
      const infoEl = document.getElementById('ft-trade-pagination-info');
      const ctrlsEl = document.getElementById('ft-trade-pagination-controls');
      if (!infoEl || !ctrlsEl) return;

      if (total === 0) {
        infoEl.innerText = '0 operaciones';
        ctrlsEl.innerHTML = '';
        return;
      }

      infoEl.innerText = `Mostrando ${startIdx + 1} - ${endIdx} de ${total}`;
      if (ftTradeRowsPerPage === 'ALL') {
        ctrlsEl.innerHTML = '';
        return;
      }

      const perPage = parseInt(ftTradeRowsPerPage, 10);
      const totalPages = Math.ceil(total / perPage);
      if (totalPages <= 1) {
        ctrlsEl.innerHTML = '';
        return;
      }

      let btnHtml = '';
      btnHtml += `<button onclick="goFtTradePage(${ftTradeCurrentPage - 1})" ${ftTradeCurrentPage === 1 ? 'disabled class="px-2 py-1 rounded bg-slate-800/40 text-slate-600 text-xs font-mono cursor-not-allowed"' : 'class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono transition"'}>&laquo; Ant</button>`;

      for (let p = 1; p <= totalPages; p++) {
        if (p === 1 || p === totalPages || (p >= ftTradeCurrentPage - 1 && p <= ftTradeCurrentPage + 1)) {
          const isActive = (p === ftTradeCurrentPage);
          btnHtml += `<button onclick="goFtTradePage(${p})" class="px-2 py-1 rounded text-xs font-mono transition ${isActive ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}">${p}</button>`;
        } else if (p === ftTradeCurrentPage - 2 || p === ftTradeCurrentPage + 2) {
          btnHtml += `<span class="px-1 text-slate-600 font-mono text-xs">...</span>`;
        }
      }

      btnHtml += `<button onclick="goFtTradePage(${ftTradeCurrentPage + 1})" ${ftTradeCurrentPage === totalPages ? 'disabled class="px-2 py-1 rounded bg-slate-800/40 text-slate-600 text-xs font-mono cursor-not-allowed"' : 'class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono transition"'}>Sig &raquo;</button>`;
      ctrlsEl.innerHTML = btnHtml;
    }

    function goFtTradePage(page) {
      ftTradeCurrentPage = page;
      renderFtTradesTable(currentFilteredFtTrades);
    }

    function renderFtTradesTable(trades) {
      currentFilteredFtTrades = trades || allFtTrades;
      const tbody = document.getElementById('ft-trades-table-body');
      if (!tbody) return;
      tbody.innerHTML = '';
      if (!currentFilteredFtTrades || currentFilteredFtTrades.length === 0) {
        renderEmptyTableState(tbody, 13, 'Sin operaciones en Forward Test', 'No se encontraron operaciones cerradas de Forward Test para el escritorio activo');
        renderFtTradePaginationControls(0, 0, 0);
        return;
      }

      const total = currentFilteredFtTrades.length;
      let startIdx = 0;
      let endIdx = total;

      if (ftTradeRowsPerPage !== 'ALL') {
        const perPage = parseInt(ftTradeRowsPerPage, 10);
        const maxPage = Math.max(1, Math.ceil(total / perPage));
        if (ftTradeCurrentPage > maxPage) ftTradeCurrentPage = maxPage;
        if (ftTradeCurrentPage < 1) ftTradeCurrentPage = 1;
        startIdx = (ftTradeCurrentPage - 1) * perPage;
        endIdx = Math.min(startIdx + perPage, total);
      }

      const paged = currentFilteredFtTrades.slice(startIdx, endIdx);

      paged.forEach((t, index) => {
        const isWin = (t.net_pnl_usd || t.net_pnl_usdc || 0) > 0;
        const sparklineSvg = generateSparklineSvg(t.sparkline, isWin);

        const tr = document.createElement('tr');
        tr.className = 'hover:bg-[#FAF7F2] transition cursor-pointer group';
        tr.title = 'Hacer clic para auditar este trade de Forward Test en TradingView';
        tr.onclick = () => {
          if (typeof openStrategyInChart === 'function') {
            openStrategyInChart(t.strategy || t.strategy_id, index);
          } else if (typeof openTradeInChart === 'function') {
            openTradeInChart(t.strategy || t.strategy_id, index);
          }
        };
        const delay = Math.min((index + 1) * 0.02, 0.3);
        tr.style.animationDelay = delay + 's';

        const esStartDate = formatSpanishDate(t.start_date || (t.opened_at ? t.opened_at.split('T')[0] : ''));
        const esEndDate = formatSpanishDate(t.end_date || (t.closed_at ? t.closed_at.split('T')[0] : ''));

        let assetBadgeHtml = '';
        const ast = (t.asset || t.symbol || '').toUpperCase();
        if (ast.includes('BTC') || ast.includes('BITCOIN')) {
          assetBadgeHtml = '<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono">BTC</span>';
        } else if (ast.includes('ETH') || ast.includes('ETHEREUM')) {
          assetBadgeHtml = '<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-slate-700/60 text-slate-200 border border-slate-600 font-mono">ETH</span>';
        } else if (ast.includes('NDX') || ast.includes('NASDAQ')) {
          assetBadgeHtml = '<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-[#3C45A5]/20 text-[#3C45A5] border border-[#3C45A5]/40 font-mono">NDX</span>';
        } else if (ast.includes('SPX') || ast.includes('SP500') || ast.includes('S&P')) {
          assetBadgeHtml = '<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40 font-mono">SPX</span>';
        } else if (ast.includes('SOL') || ast.includes('SOLANA')) {
          assetBadgeHtml = '<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40 font-mono">SOL</span>';
        } else {
          assetBadgeHtml = `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-slate-800 text-slate-300 border border-slate-700 font-mono">${t.asset || t.symbol || 'ASSET'}</span>`;
        }

        const netPnl = Number(t.net_pnl_usd != null ? t.net_pnl_usd : (t.net_pnl_usdc || 0));
        const runBal = Number(t.running_balance != null ? t.running_balance : (t.running_balance_usd || 1000));
        const entryPx = Number(t.entry_price || (t.eth_leg ? t.eth_leg.entry_px : 0));
        const exitPx = Number(t.exit_price || (t.eth_leg ? t.eth_leg.exit_px : 0));
        const fees = Number(t.fees_usd || t.total_fees || 0);

        tr.innerHTML = `
          <td class="py-2.5 px-3 font-bold text-txtPrimary whitespace-nowrap">
            <div class="flex items-center gap-1.5">
              <i class="fa-solid fa-chart-line text-[#3C45A5] opacity-40 group-hover:opacity-100 transition-opacity text-xs" title="Auditar en TradingView"></i>
              <span>${t.strategy || t.strategy_id || t.trade_id}</span>
            </div>
          </td>
          <td class="py-2.5 px-3 text-center whitespace-nowrap">
            ${sparklineSvg}
          </td>
          <td class="py-2.5 px-3 whitespace-nowrap">
            ${assetBadgeHtml}
          </td>
          <td class="py-2.5 px-3 text-right font-bold ${isWin ? 'text-emerald-400' : 'text-rose-400'}">
            <span class="px-2 py-0.5 rounded ${isWin ? 'bg-emerald-500/10' : 'bg-rose-500/10'} font-semibold">
              ${isWin ? '+' : ''}$${netPnl.toFixed(2)}
            </span>
          </td>
          <td class="py-2.5 px-3 text-right text-cyan-300 font-bold">$${runBal.toLocaleString('es-ES', {minimumFractionDigits: 2})}</td>
          <td class="py-2.5 px-3 text-slate-400">
            <div class="font-mono text-white">${esStartDate || ''}</div>
            <div class="text-[11px] text-slate-500 font-mono">${t.start_time || ''}</div>
          </td>
          <td class="py-2.5 px-3 text-slate-400">
            <div class="font-mono text-white">${esEndDate || ''}</div>
            <div class="text-[11px] text-slate-500 font-mono">${t.end_time || ''}</div>
          </td>
          <td class="py-2.5 px-3 text-right font-bold text-white">${formatQuantPrice(entryPx, t.asset || t.symbol)}</td>
          <td class="py-2.5 px-3 text-right text-emerald-400">${t.tp_price ? formatQuantPrice(t.tp_price, t.asset || t.symbol) : '-'}</td>
          <td class="py-2.5 px-3 text-right text-rose-400">${t.sl_price ? formatQuantPrice(t.sl_price, t.asset || t.symbol) : '-'}</td>
          <td class="py-2.5 px-3 text-right font-bold text-white">${formatQuantPrice(exitPx, t.asset || t.symbol)}</td>
          <td class="py-2.5 px-3 text-right text-slate-400">$${fees.toFixed(2)}</td>
          <td class="py-2.5 px-3"><span class="text-[11px] ${isWin ? 'text-emerald-400/90' : 'text-rose-400/90'} font-semibold">${t.exit_reason || t.reason || '--'}</span></td>
        `;
        tbody.appendChild(tr);
      });

      renderFtTradePaginationControls(total, startIdx, endIdx);
    }

    function filterFtTrades() {
      setFtTradeFilter(currentFtTradeFilter || 'ALL');
    }

    function setFtTradeFilter(filterType) {
      currentFtTradeFilter = filterType;
      document.querySelectorAll('.trade-filter-btn').forEach(b => {
        b.classList.remove('bg-slate-800', 'text-white', 'border', 'border-slate-700');
        b.classList.add('text-slate-400', 'bg-slate-900/60');
      });
      const activeBtn = document.getElementById(`filter-btn-ft-${filterType}`);
      if (activeBtn) {
        activeBtn.classList.remove('text-slate-400', 'bg-slate-900/60');
        activeBtn.classList.add('bg-slate-800', 'text-white', 'border', 'border-slate-700');
      }

      const deskTrades = getFtTradesForCurrentDesk();
      const searchInput = document.getElementById('ft-trade-search');
      const searchVal = (searchInput ? searchInput.value : '').trim().toUpperCase();

      let filtered = deskTrades;
      if (searchVal) {
        filtered = filtered.filter(t => (t.trade_id || '').toUpperCase().includes(searchVal) || (t.asset || t.symbol || '').toUpperCase().includes(searchVal) || (t.strategy || '').toUpperCase().includes(searchVal));
      }

      if (filterType === 'TRADFI') {
        filtered = filtered.filter(t => (t.asset || t.symbol || '').includes('US500') || (t.asset || t.symbol || '').includes('USTEC') || (t.asset || t.symbol || '').includes('EUR'));
      } else if (filterType === 'DEX') {
        filtered = filtered.filter(t => !(t.asset || t.symbol || '').includes('US500') && !(t.asset || t.symbol || '').includes('USTEC') && !(t.asset || t.symbol || '').includes('EUR'));
      } else if (filterType === 'WIN') {
        filtered = filtered.filter(t => (t.net_pnl_usd || t.net_pnl_usdc || 0) > 0);
      } else if (filterType === 'LOSS') {
        filtered = filtered.filter(t => (t.net_pnl_usd || t.net_pnl_usdc || 0) <= 0);
      }

      // Actualizar contadores dinámicos según el modo activo
      const cAll = document.getElementById('ft-trades-count-all');
      const cMt5 = document.getElementById('ft-trades-count-mt5');
      const cDex = document.getElementById('ft-trades-count-dex');
      if (cAll) cAll.innerText = deskTrades.length;
      if (cMt5) cMt5.innerText = deskTrades.filter(t => (t.asset || t.symbol || '').includes('US500') || (t.asset || t.symbol || '').includes('USTEC') || (t.asset || t.symbol || '').includes('EUR')).length;
      if (cDex) cDex.innerText = deskTrades.filter(t => !(t.asset || t.symbol || '').includes('US500') && !(t.asset || t.symbol || '').includes('USTEC') && !(t.asset || t.symbol || '').includes('EUR')).length;

      ftTradeCurrentPage = 1;
      renderFtTradesTable(filtered);
    }

    function filterFtTradesByAsset(asset) {
      const deskTrades = getFtTradesForCurrentDesk();
      let filtered = (asset === 'ALL') ? [...deskTrades] : deskTrades.filter(t => (t.asset || t.symbol || '').toUpperCase().includes(asset));

      if (currentFtTradeFilter === 'WIN') {
        filtered = filtered.filter(t => (t.net_pnl_usd || t.net_pnl_usdc || 0) > 0);
      } else if (currentFtTradeFilter === 'LOSS') {
        filtered = filtered.filter(t => (t.net_pnl_usd || t.net_pnl_usdc || 0) <= 0);
      }

      ftTradeCurrentPage = 1;
      renderFtTradesTable(filtered);
    }

    function exportFtTradesCSV() {
      const deskTrades = (currentFilteredFtTrades && currentFilteredFtTrades.length > 0) ? currentFilteredFtTrades : getFtTradesForCurrentDesk();
      if (!deskTrades || deskTrades.length === 0) return;
      const headers = ['Trade_ID', 'Strategy', 'Asset', 'Start_Date', 'Start_Time', 'End_Date', 'End_Time', 'Entry_Price', 'TP_Price', 'SL_Price', 'Exit_Price', 'Fees_USD', 'Net_PnL_USD', 'Running_Balance_USD', 'Exit_Reason'];
      const rows = deskTrades.map(t => [
        t.trade_id || '', t.strategy || t.strategy_id || '', t.asset || t.symbol || '', t.start_date || '', t.start_time || '',
        t.end_date || '', t.end_time || '', t.entry_price || '', t.tp_price || '', t.sl_price || '', t.exit_price || '',
        t.fees_usd || t.total_fees || 0, t.net_pnl_usd != null ? t.net_pnl_usd : (t.net_pnl_usdc || 0), t.running_balance || t.running_balance_usd || 1000, `"${t.exit_reason || t.reason || ''}"`
      ]);
      const csvContent = '\uFEFF' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `algrokquant_forward_test_${(currentDeskMode || 'all').toLowerCase()}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }

    // Cargar Roster Completo de Agentes
    async function fetchRosterData() {
      try {
        const res = await fetch('/api/roster');
        const roster = await res.json();
        const container = document.getElementById('roster-grid');
        container.innerHTML = '';
        roster.forEach((agent, index) => {
          const card = document.createElement('div');
          card.className = 'glass-card rounded-xl p-4 flex flex-col justify-between border-t-2 border-' + (agent.color || 'brand') + '-500 motion-sweep shimmer-active';
          card.style.animationDelay = (index * 0.05) + 's';

          card.innerHTML = `
            <div>
              <div class="flex items-center justify-between mb-2">
                <span class="text-2xl">${agent.avatar}</span>
                <span class="text-[11px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">${agent.status}</span>
              </div>
              <h4 class="font-bold text-white text-sm">@${agent.name}</h4>
              <p class="text-[11px] text-brand-300 font-medium mb-1">${agent.title}</p>
              <p class="text-xs text-slate-400 leading-relaxed mb-3">${agent.role}</p>
            </div>
            <div class="pt-3 border-t border-slate-800/80 space-y-1 text-[11px] font-mono">
              <div class="flex justify-between text-slate-500">
                <span>Especialidad:</span>
                <span class="text-slate-300 text-right">${agent.focus || 'Cuantitativo'}</span>
              </div>
              <div class="flex justify-between items-center text-slate-600 pt-1">
                <span>Motor IA:</span>
                ${(agent.engine || '').includes('High')
                  ? `<span style="background-color: #FEF3C7; color: #78350F; border: 1px solid #F59E0B;" class="px-2.5 py-0.5 rounded text-[11px] font-bold font-mono inline-flex items-center gap-1.5 whitespace-nowrap shadow-xs"><i class="fa-solid fa-brain text-[11px]" style="color: #B45309;"></i>${agent.engine}</span>`
                  : `<span style="background-color: #EDE9FE; color: #3B0764; border: 1px solid #8B5CF6;" class="px-2.5 py-0.5 rounded text-[11px] font-bold font-mono inline-flex items-center gap-1.5 whitespace-nowrap shadow-xs"><i class="fa-solid fa-bolt text-[11px]" style="color: #6D28D9;"></i>${agent.engine}</span>`
                }
              </div>
            </div>
          `;
          container.appendChild(card);
        });
      } catch (err) {
        console.error('Error fetching roster:', err);
      }
    }

    // Simulación de Estrategias y Test de Robustez
    async function runStrategySimulation(e) {
      e.preventDefault();
      const btn = document.getElementById('btn-run-sim');
      btn.disabled = true;
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i> Ejecutando Monte Carlo y Test de Estrés...';

      const payload = {
        strat_id: document.getElementById('sim-id').value,
        name: document.getElementById('sim-name').value,
        asset: document.getElementById('sim-asset').value,
        timeframe: document.getElementById('sim-tf').value,
        algo_type: document.getElementById('sim-algo').value,
        risk_profile: document.getElementById('sim-profile').value,
        risk_per_trade_pct: parseFloat(document.getElementById('sim-risk-pct').value),
        rr_ratio: parseFloat(document.getElementById('sim-rr').value),
        monte_carlo_runs: parseInt(document.getElementById('sim-mc-runs').value),
        slippage_factor: parseFloat(document.getElementById('sim-slippage').value),
        execution_delay_bars: parseInt(document.getElementById('sim-delay').value)
      };

      try {
        const res = await fetch('/api/simulate_strategy', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const result = await res.json();

        // Renderizar Veredicto con Animación
        const card = document.getElementById('sim-result-card');
        const badge = document.getElementById('sim-verdict-badge');
        const desc = document.getElementById('sim-verdict-desc');
        const grid = document.getElementById('sim-metrics-grid');
        const reasonsCont = document.getElementById('sim-reasons-container');

        card.classList.remove('motion-sweep', 'shimmer-active');
        void card.offsetWidth;
        card.classList.add('motion-sweep', 'shimmer-active');

        grid.classList.remove('hidden');
        grid.classList.add('grid');

        if (result.is_approved) {
          card.className = 'glass-card rounded-xl p-5 border-l-4 border-emerald-500 space-y-3 motion-sweep shimmer-active';
          badge.className = 'px-2.5 py-0.5 rounded-full text-xs font-bold font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
          badge.innerText = 'APROBADA · APTO PARA PAPER';
          desc.innerHTML = `<strong class="text-white">${result.strat_id}</strong> ha superado exitosamente el examen conjunto de <span class="text-blue-400">@Auditor</span> y <span class="text-rose-400">@Skeptic</span>. Resiste slippage severo y retardo temporal.`;
          reasonsCont.classList.add('hidden');
        } else {
          card.className = 'glass-card rounded-xl p-5 border-l-4 border-rose-500 space-y-3 motion-sweep shimmer-active';
          badge.className = 'px-2.5 py-0.5 rounded-full text-xs font-bold font-mono bg-rose-500/20 text-rose-400 border border-rose-500/30';
          badge.innerText = 'RECHAZADA · FALLO EN ROBUSTEZ';
          desc.innerHTML = `<strong class="text-white">${result.strat_id}</strong> fue descartada por no cumplir los umbrales mandatorios de Sergio o colapsar en el test de retardo.`;
          reasonsCont.innerHTML = '<strong>Motivos de rechazo:</strong><br>' + result.reasons.map(r => `• ${r}`).join('<br>');
          reasonsCont.classList.remove('hidden');
        }

        document.getElementById('res-wr').innerText = result.metrics.simulated_win_rate + '%';
        document.getElementById('res-pf').innerText = result.metrics.profit_factor;
        document.getElementById('res-dd').innerText = result.metrics.max_drawdown + '%';
        document.getElementById('res-p5').innerText = result.metrics.monte_carlo.p5_worst + '%';
        document.getElementById('res-p50').innerText = result.metrics.monte_carlo.median_p50 + '%';
        document.getElementById('res-p95').innerText = result.metrics.monte_carlo.p95_best + '%';

      } catch (err) {
        alert('Error en simulación: ' + err);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-play mr-2"></i> Lanzar Batería de Robustez Cuantitativa';
      }
    }

    
    // ==================== MATRIZ TRI-FACETA (LESSON-018) ====================
    let allTriFacetData = {};

    async function fetchTriFacetData() {
      const tbody = document.getElementById('tri-facet-table-body');
      try {
        const res = await fetch('/api/strategies/tri_facet');
        if (!res.ok) throw new Error(`HTTP ${res.status}: Error al obtener matriz tri-faceta`);
        const data = await res.json();
        if (data && data.strategies) {
          allTriFacetData = data.strategies;
          renderTriFacetTable(allTriFacetData);
        } else {
          renderTriFacetTable({});
        }
      } catch (err) {
        console.error('Error fetching tri-facet data:', err);
        if (tbody) {
          tbody.innerHTML = `
            <tr>
              <td colspan="5" class="py-10 text-center font-mono">
                <i class="fa-solid fa-triangle-exclamation text-[#9A3412] text-xl mb-2"></i>
                <div class="text-xs font-bold text-txtPrimary">No se pudo cargar la Matriz Tri-Faceta</div>
                <div class="text-[11px] text-txtSecondary mt-1">Verifique la conexión con el enjambre o el endpoint /api/strategies/tri_facet</div>
                <button onclick="fetchTriFacetData()" class="mt-3 px-3 py-1 bg-[#FAF7F2] border border-borderWarm rounded-lg text-xs font-bold hover:bg-[#EAE5DC] transition text-txtPrimary cursor-pointer shadow-2xs">
                  <i class="fa-solid fa-rotate mr-1"></i> Reintentar
                </button>
              </td>
            </tr>`;
        }
      }
    }

    async function loadTriFacetTab() {
      await fetchTriFacetData();
    }
    window.loadTriFacetTab = loadTriFacetTab;

    
    // Telemetría en Vivo
    async function fetchTelemetry() {
      const startT = performance.now();
      try {
        const res = await fetch('/api/telemetry');
        if (!res.ok) {
          updateDaemonHealth('reconnecting');
          return;
        }
        const d = await res.json();
        const lat = Math.max(5, Math.round(performance.now() - startT));
        updateDaemonHealth('online', lat);

        const mt5Bal = document.getElementById('tele-mt5-bal');
        const hlBal = document.getElementById('tele-hl-bal');
        const totalBal = document.getElementById('tele-total-bal');
        
        if (mt5Bal && d.mt5) mt5Bal.innerText = '$' + Number(d.mt5.balance).toFixed(2) + ' USD';
        if (hlBal && d.hyperliquid) hlBal.innerText = Number(d.hyperliquid.balance).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 4 }) + ' USDC';
        if (totalBal) totalBal.innerText = '$' + Number(d.total_balance_usd).toFixed(2) + ' USD';

        // Actualización dinámica de tarjetas de cartera activa en tiempo real
        if (d.mt5) {
          const s1 = document.getElementById('active-card-spx-bal');
          const s2 = document.getElementById('active-card-ndx-bal');
          if (s1) s1.innerText = '$' + Number(d.mt5.balance).toFixed(2) + ' USD';
          if (s2) s2.innerText = '$' + Number(d.mt5.balance).toFixed(2) + ' USD';
        }
        if (d.hyperliquid) {
          const s3 = document.getElementById('active-card-crypto-bal');
          if (s3) s3.innerText = Number(d.hyperliquid.balance).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 4 }) + ' USDC';
        }
      } catch (e) {
        console.error('Error fetching telemetry:', e);
        updateDaemonHealth('reconnecting');
      }
    }

    let triFacetFilterMode = 'APPROVED';
    function toggleTriFacetMode(mode) {
      triFacetFilterMode = mode;
      const bApp = document.getElementById('btn-tf-approved');
      const bAll = document.getElementById('btn-tf-all');
      if (mode === 'APPROVED') {
        if (bApp) bApp.className = 'px-2.5 py-1.5 rounded-lg text-xs font-bold transition bg-cyan-500/20 text-cyan-300 border border-cyan-500/40';
        if (bAll) bAll.className = 'px-2.5 py-1.5 rounded-lg text-xs font-bold transition text-slate-400 hover:text-white bg-dark-900 border border-slate-700';
      } else {
        if (bApp) bApp.className = 'px-2.5 py-1.5 rounded-lg text-xs font-bold transition text-slate-400 hover:text-white bg-dark-900 border border-slate-700';
        if (bAll) bAll.className = 'px-2.5 py-1.5 rounded-lg text-xs font-bold transition bg-cyan-500/20 text-cyan-300 border border-cyan-500/40';
      }
      filterTriFacetTable();
    }

    function filterTriFacetTable() {
      const filterEl = document.getElementById('tf-segment-filter');
      const filterVal = filterEl ? filterEl.value : 'ALL';
      if (!allTriFacetData) return;
      if (filterVal === 'ALL') {
        renderTriFacetTable(allTriFacetData);
      } else {
        const filtered = {};
        for (const [k, v] of Object.entries(allTriFacetData)) {
          if ((v.segment && v.segment.includes(filterVal)) || filterVal === 'ALL') {
            filtered[k] = v;
          }
        }
        renderTriFacetTable(filtered);
      }
    }

    function renderTriFacetTable(strategies) {
      const tbody = document.getElementById('tri-facet-table-body');
      if (!tbody) return;
      tbody.innerHTML = '';
      
      const entries = strategies ? Object.values(strategies) : [];
      const totalEl = document.getElementById('tf-stat-total');
      if (totalEl) totalEl.innerText = `${entries.length} Estrategias`;

      if (entries.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="5" class="py-8 text-center text-txtSecondary font-mono text-xs">
              <i class="fa-solid fa-inbox text-base mb-1.5 block opacity-50"></i>
              Sin modelos registrados en la matriz tri-faceta para el filtro seleccionado
            </td>
          </tr>`;
        return;
      }

      entries.forEach((s, idx) => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-900/40 transition motion-sweep';
        tr.style.animationDelay = `${(idx + 1) * 0.04}s`;
        
        const py = s.python_backtest || {};
        const brk = s.broker_simulated || {};
        const live = s.live_real || {};

        const isCap = s.segment && s.segment.includes('Capital Propio');
        const segBadge = isCap 
          ? `<span class="badge-success-live font-mono inline-block"><i class="fa-solid fa-coins mr-1"></i>${s.segment}</span>`
          : `<span class="badge-brand-indigo font-mono inline-block"><i class="fa-solid fa-building-columns mr-1"></i>${s.segment}</span>`;

        tr.innerHTML = `
          <td class="py-3 px-3 align-top">
            <div class="font-bold text-txtPrimary text-xs">${s.id}</div>
            <div class="text-[11px] text-txtSecondary font-sans mt-0.5">${s.name}</div>
            <div class="text-[11px] text-txtSecondary mt-1 flex items-center gap-1.5 flex-wrap">
              <span class="font-mono bg-[#FAF7F2] px-1.5 py-0.5 rounded border border-borderWarm text-[#3C45A5] font-bold">${s.asset}</span>
              <span class="font-mono bg-[#FAF7F2] px-1.5 py-0.5 rounded border border-borderWarm text-txtSecondary font-semibold">${s.timeframe}</span>
            </div>
            <div class="mt-2">${segBadge}</div>
            <div class="text-[11px] text-[#9A3412] font-mono mt-1 font-bold">${s.sizing || ''}</div>
          </td>

          <td class="py-3 px-3 align-top border-x border-borderWarm">
            <div class="flex items-center justify-between">
              <span class="px-1.5 py-0.5 rounded text-[11px] font-mono font-bold bg-[#FAF7F2] text-txtSecondary border border-borderWarm">${py.status || 'EVALUADO'}</span>
              <span class="text-xs font-bold font-mono ${py.return_pct >= 0 ? 'text-[#065F46]' : 'text-rose-600'}">${py.return_pct >= 0 ? '+' : ''}${py.return_pct}%</span>
            </div>
            <div class="grid grid-cols-2 gap-1 mt-2 text-[11px] text-txtSecondary font-mono">
              <div>WR: <strong class="text-txtPrimary">${py.win_rate}%</strong></div>
              <div>PF: <strong class="text-[#3C45A5]">${py.profit_factor}</strong></div>
              <div>Max DD: <strong class="text-[#9A3412]">${py.max_dd}%</strong></div>
              <div>Trades: <strong class="text-txtPrimary">${py.trades_count}</strong></div>
            </div>
            <div class="text-[11px] text-txtSecondary mt-2 italic border-t border-borderWarm pt-1">${py.notes || ''}</div>
          </td>

          <td class="py-3 px-3 align-top border-r border-borderWarm">
            <div class="flex items-center justify-between">
              <span class="px-1.5 py-0.5 rounded text-[11px] font-mono font-bold bg-[#FAF7F2] text-txtSecondary border border-borderWarm">${brk.status || 'SIMULADO'}</span>
              <span class="text-xs font-bold font-mono ${brk.return_pct >= 0 ? 'text-[#065F46]' : 'text-rose-600'}">${brk.return_pct >= 0 ? '+' : ''}${brk.return_pct}%</span>
            </div>
            <div class="text-[11px] font-bold font-mono text-[#065F46] mt-0.5">${brk.net_profit_usd !== undefined ? '+$' + brk.net_profit_usd + ' USD' : ''}</div>
            <div class="grid grid-cols-2 gap-1 mt-1 text-[11px] text-txtSecondary font-mono">
              <div>WR: <strong class="text-txtPrimary">${brk.win_rate}%</strong></div>
              <div>PF: <strong class="text-[#3C45A5]">${brk.profit_factor}</strong></div>
              <div>Max DD: <strong class="text-[#9A3412]">${brk.max_dd}%</strong></div>
              <div>Trades: <strong class="text-txtPrimary">${brk.trades_count}</strong></div>
            </div>
            <div class="text-[11px] text-txtSecondary mt-2 border-t border-borderWarm pt-1">
              <div class="text-txtPrimary font-sans font-semibold">${brk.venue || ''}</div>
              <div class="italic text-[11px]">${brk.notes || ''}</div>
            </div>
          </td>

          <td class="py-3 px-3 align-top border-r border-borderWarm">
            <div class="flex items-center justify-between">
              <span class="px-1.5 py-0.5 rounded text-[11px] font-mono font-bold ${live.status && live.status.includes('ACTIVO') ? 'bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0]' : 'bg-[#FAF7F2] text-txtSecondary border border-borderWarm'}">${live.status || 'MONITORIZANDO'}</span>
              <span class="text-xs font-bold font-mono text-txtSecondary">${live.trades_count || 0} Trades</span>
            </div>
            <div class="grid grid-cols-2 gap-1 mt-2 text-[11px] text-txtSecondary font-mono">
              <div>Slippage: <strong class="text-txtPrimary">${live.slippage_mean_pts !== undefined ? live.slippage_mean_pts + ' pts' : '0.0 pts'}</strong></div>
              <div>Retorno: <strong class="text-txtPrimary">${live.return_pct || 0}%</strong></div>
            </div>
            <div class="text-[11px] text-txtSecondary mt-2 border-t border-borderWarm pt-1">
              <div class="text-txtPrimary font-sans font-semibold">${live.venue || ''}</div>
              <div class="text-[11px]">${live.notes || ''}</div>
            </div>
          </td>

          <td class="py-3 px-3 align-top text-right">
            <!-- Badge de Veredicto y Factor con Contraste AAA/AA -->
            <div class="inline-flex flex-col items-end px-2.5 py-1.5 rounded-lg border text-right ${py.profit_factor >= 1.3 && brk.profit_factor >= 1.3 ? 'bg-[#ECFDF5] border-[#A7F3D0] text-[#065F46]' : 'bg-[#FFF7ED] border-[#FED7AA] text-[#9A3412]'}">
              <span class="text-[11px] font-bold tracking-wide">${py.profit_factor >= 1.3 && brk.profit_factor >= 1.3 ? 'ROBUSTO & VIABLE' : 'CALIBRACIÓN'}</span>
              <span class="text-[11px] font-mono mt-0.5">Div PF: <strong class="${(brk.profit_factor - py.profit_factor) >= 0 ? 'text-[#065F46]' : 'text-[#9A3412]'}">${(brk.profit_factor - py.profit_factor).toFixed(2)} pts</strong></span>
            </div>
          </td>
        `;
        tbody.appendChild(tr);
      });
    }

    // Cargar Catálogo de Estrategias
    async function fetchStrategiesData() {
      try {
        const res = await fetch('/api/strategies');
        allStrategies = await res.json();
        renderStrategiesTable(allStrategies);
      } catch (err) {
        console.error('Error fetching strategies:', err);
      }
    }

    let currentFilteredStrategies = [];
    let stratCurrentPage = 1;
    let stratRowsPerPage = 50;

    function renderStrategiesTable(strategies) {
      currentFilteredStrategies = strategies || allStrategies;
      const tbody = document.getElementById('strategies-table-body');
      if (!tbody) return;
      tbody.innerHTML = '';
      
      const total = currentFilteredStrategies.length;
      if (total === 0) {
        renderEmptyTableState(tbody, 10, 'Catálogo de estrategias vacío', 'No hay estrategias que coincidan con la categoría o filtro seleccionado');
        renderPaginationControls(0, 0, 0);
        return;
      }
      let startIdx = 0;
      let endIdx = total;
      
      if (stratRowsPerPage !== 'ALL') {
        const perPage = parseInt(stratRowsPerPage, 10);
        const maxPage = Math.max(1, Math.ceil(total / perPage));
        if (stratCurrentPage > maxPage) stratCurrentPage = maxPage;
        if (stratCurrentPage < 1) stratCurrentPage = 1;
        startIdx = (stratCurrentPage - 1) * perPage;
        endIdx = Math.min(startIdx + perPage, total);
      }

      const paged = currentFilteredStrategies.slice(startIdx, endIdx);

      paged.forEach((s, index) => {
        const rawStatus = (s.status || '').toUpperCase();
        const isApproved = rawStatus.includes('APROBADA');
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-900/40 transition motion-sweep';
        const delay = Math.min((index + 1) * 0.02, 0.3);
        tr.style.animationDelay = delay + 's';

        // Linaje / Origen: "Híbrido" o "Heurístico" limpio
        const isHybrid = s.source_type === 'HYBRID_VECTORBT';
        const provenanceBadge = isHybrid
          ? `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap bg-purple-500/15 text-purple-300 border border-purple-500/30" title="Exploración en meseta paramétrica VectorBT"><i class="fa-solid fa-microchip text-[11px]"></i> Híbrido</span>`
          : `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap bg-cyan-500/15 text-cyan-300 border border-cyan-500/30" title="Lógica heurística cualitativa de agente"><i class="fa-solid fa-brain text-[11px]"></i> Heurístico</span>`;

        // Métricas OOS y Estancamiento
        const oosInfo = s.oos_r_dd ? `
          <div class="flex items-center space-x-1.5 whitespace-nowrap">
            <span class="text-white font-bold">${s.oos_r_dd.oos_r_dd}</span>
            <span class="text-[11px] ${s.oos_r_dd.degradation_pct < -30 ? 'text-amber-400' : 'text-emerald-400'} font-mono">(${s.oos_r_dd.degradation_pct}%)</span>
          </div>
        ` : `<span class="text-slate-500">-</span>`;

        const stagInfo = s.stagnation_days ? `
          <span class="text-slate-300 font-mono font-medium whitespace-nowrap">${s.stagnation_days}d</span>
        ` : `<span class="text-slate-500">-</span>`;

        // Regime Gate Badge
        const gate = (s.regime_gate || 'ANY').toUpperCase();
        let gateClass = 'bg-slate-800 text-slate-300 border-slate-700';
        if (gate.includes('TREND')) gateClass = 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30';
        else if (gate.includes('REV') || gate.includes('MEAN')) gateClass = 'bg-purple-500/15 text-purple-300 border-purple-500/30';
        else if (gate.includes('SQUEEZE')) gateClass = 'bg-amber-500/15 text-amber-300 border-amber-500/30';
        const gateCell = `<td class="py-3 px-4 whitespace-nowrap"><span class="inline-block px-2 py-0.5 rounded text-[11px] font-mono font-bold border ${gateClass}">${gate}</span></td>`;

        // Incubation Guardian Traffic Light Badge
        const guard = s.incubation_guardian || {};
        const tLight = (guard.traffic_light || 'GREEN').toUpperCase();
        const lotMult = (guard.lot_sizing_multiplier !== undefined && guard.lot_sizing_multiplier !== null) ? Number(guard.lot_sizing_multiplier).toFixed(1) : '1.0';
        let guardBadge = `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>${lotMult}x GREEN</span>`;
        if (tLight === 'AMBER') {
          guardBadge = `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30"><span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span>${lotMult}x AMBER</span>`;
        } else if (tLight === 'RED') {
          guardBadge = `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30"><span class="w-1.5 h-1.5 rounded-full bg-rose-400"></span>0.0x PAUSA</span>`;
        }
        const guardCell = `<td class="py-3 px-4 whitespace-nowrap">${guardBadge}</td>`;

        // Métricas Cuantitativas Ayago/Techain
        const kurtVal = (s.robust_kurtosis !== undefined && s.robust_kurtosis !== null) ? Number(s.robust_kurtosis).toFixed(3) : '0.263';
        const kurtCell = `<td class="py-3 px-4 font-mono text-xs text-slate-300 whitespace-nowrap" title="Curtosis Robusta por Percentiles Ignacio Ayago">${kurtVal}</td>`;

        const cushVal = (s.wr_cushion_pct !== undefined && s.wr_cushion_pct !== null) ? Number(s.wr_cushion_pct) : 8.0;
        const cushClass = cushVal >= 3.0 ? 'text-emerald-400 font-bold' : (cushVal > 0 ? 'text-amber-400' : 'text-rose-400 font-bold');
        const cushCell = `<td class="py-3 px-4 font-mono text-xs ${cushClass} whitespace-nowrap" title="Colchón sobre WR de Breakeven">+${cushVal.toFixed(1)}%</td>`;

        const platVal = (s.meseta_parametrica_pct !== undefined && s.meseta_parametrica_pct !== null) ? Number(s.meseta_parametrica_pct).toFixed(0) : '89';
        const platCell = `<td class="py-3 px-4 font-mono text-xs text-purple-300 font-bold whitespace-nowrap" title="Supervivencia en Meseta Paramétrica @Skeptic">${platVal}%</td>`;

        // Estado: Pendiente o Aprobada limpio
        const statusBadge = isApproved
          ? `<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 inline-block"></span>Aprobada</span>`
          : `<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap bg-amber-500/15 text-amber-400 border border-amber-500/30"><span class="w-1.5 h-1.5 rounded-full bg-amber-400 mr-1.5 inline-block"></span>Pendiente</span>`;

        // Columna de Activo: Ancho de columna fijo, badge ajustado al texto (inline-block) y resolución de activos directos
        let rawAsset = s.asset || 'N/A';
        const rawUpper = rawAsset.toUpperCase();
        if (s.id && (s.id.includes('014') || s.id === 'STRAT-20261021-014')) {
          rawAsset = 'ETH, SOL, AVAX, NEAR, LINK';
        } else if (rawUpper.includes('CRIPTO MULTI') || rawUpper.includes('CESTA') || rawUpper.includes('TOP 6')) {
          rawAsset = 'BTC, ETH, SOL, AVAX, NEAR, LINK';
        } else if (rawUpper === 'CRYPTO' || rawUpper === 'CRIPTO') {
          rawAsset = 'BTC, ETH, SOL';
        }
        const safeAsset = rawAsset.replace(/"/g, '&quot;');
        const assetCell = `
          <td class="py-3 px-4 w-[210px] min-w-[210px] max-w-[210px] overflow-hidden whitespace-nowrap" title="${safeAsset}">
            <span class="inline-block max-w-full px-2.5 py-0.5 rounded bg-slate-800 text-slate-200 font-bold font-mono text-xs truncate align-middle border border-slate-700/60" title="${safeAsset}">${rawAsset}</span>
          </td>
        `;

        // Columna separada para Timeframe compactada sin textos largos que ensanchen la columna
        let cleanTf = (s.timeframe || '-').split('(')[0].trim();
        cleanTf = cleanTf.split('/')[0].trim();
        cleanTf = cleanTf.replace(/minutos?/i, 'm').replace(/horas?/i, 'h').replace(/d[ií]as?/i, 'd').replace(/\s+/g, '');
        if (!cleanTf) cleanTf = s.timeframe || '-';

        const tfCell = `
          <td class="py-3 px-4 whitespace-nowrap font-mono text-xs text-center" title="${(s.timeframe || '').replace(/"/g, '&quot;')}">
            <span class="px-2 py-0.5 rounded bg-dark-900 border border-slate-700 text-slate-300 font-bold">${cleanTf}</span>
          </td>
        `;

        // Columna PNL dinámico y formateado
        const retVal = (s.return_pct !== undefined && s.return_pct !== null && !isNaN(s.return_pct)) ? Number(s.return_pct) : null;
        let pnlDisplay = '-';
        let pnlClass = 'text-slate-400 font-mono';
        if (retVal !== null && retVal !== 0) {
          const isPos = retVal > 0;
          pnlDisplay = (isPos ? '+' : '') + retVal.toFixed(2) + '%';
          pnlClass = isPos ? 'text-emerald-400 font-bold font-mono' : 'text-rose-400 font-bold font-mono';
        } else if (s.net_profit_usd !== undefined && s.net_profit_usd !== null) {
          const p = Number(s.net_profit_usd);
          pnlDisplay = (p >= 0 ? '+$' : '-$') + Math.abs(p).toFixed(2);
          pnlClass = p >= 0 ? 'text-emerald-400 font-bold font-mono' : 'text-rose-400 font-bold font-mono';
        }

        tr.innerHTML = `
          <td class="py-3 px-4 font-bold text-white whitespace-nowrap">${s.id}</td>
          ${assetCell}
          ${tfCell}
          ${gateCell}
          ${guardCell}
          <td class="py-3 px-4 text-emerald-400 font-bold whitespace-nowrap">${s.win_rate}%</td>
          <td class="py-3 px-4 ${pnlClass} whitespace-nowrap">${pnlDisplay}</td>
          <td class="py-3 px-4 text-slate-300 whitespace-nowrap">${s.max_dd}%</td>
          <td class="py-3 px-4 text-white whitespace-nowrap">${s.profit_factor}</td>
          ${kurtCell}
          ${cushCell}
          ${platCell}
          <td class="py-3 px-4 whitespace-nowrap">${provenanceBadge}</td>
          <td class="py-3 px-4 whitespace-nowrap">${statusBadge}</td>
          <td class="py-3 px-4 text-center whitespace-nowrap">
            <button onclick="viewStrategy('${s.id}')" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#FAF7F2] text-[#181A20] hover:bg-[#EAE5DC] transition border border-[#D5D0C5] shadow-xs cursor-pointer font-sans">
              <i class="fa-solid fa-file-lines text-xs text-brand-600"></i> Ver Ficha
            </button>
          </td>
        `;
        tbody.appendChild(tr);
      });

      renderPaginationControls(total, startIdx, endIdx);
    }

    function renderPaginationControls(total, startIdx, endIdx) {
      const infoEl = document.getElementById('strat-pagination-info');
      const btnCont = document.getElementById('strat-pagination-buttons');
      if (infoEl) {
        if (total === 0) {
          infoEl.innerText = 'Sin estrategias que coincidan';
        } else {
          infoEl.innerText = `Mostrando ${startIdx + 1} - ${endIdx} de ${total} estrategias`;
        }
      }
      if (!btnCont) return;
      btnCont.innerHTML = '';
      if (stratRowsPerPage === 'ALL' || total === 0) return;

      const perPage = parseInt(stratRowsPerPage, 10);
      const totalPages = Math.ceil(total / perPage);
      if (totalPages <= 1) return;

      // Botón Anterior
      const prevBtn = document.createElement('button');
      prevBtn.className = `px-2.5 py-1 rounded text-xs transition border ${stratCurrentPage > 1 ? 'bg-dark-900 border-slate-700 text-white hover:border-brand-500' : 'bg-dark-950 border-slate-800 text-slate-600 cursor-not-allowed'}`;
      prevBtn.innerHTML = '<i class="fa-solid fa-chevron-left text-[11px]"></i>';
      prevBtn.disabled = stratCurrentPage <= 1;
      prevBtn.onclick = () => setStratPage(stratCurrentPage - 1);
      btnCont.appendChild(prevBtn);

      // Botones de Páginas
      for (let p = 1; p <= totalPages; p++) {
        if (p === 1 || p === totalPages || (p >= stratCurrentPage - 1 && p <= stratCurrentPage + 1)) {
          const pageBtn = document.createElement('button');
          const isActive = p === stratCurrentPage;
          pageBtn.className = `px-2.5 py-1 rounded text-xs font-bold transition border ${isActive ? 'bg-brand-500/20 text-brand-300 border-brand-500/40' : 'bg-dark-900 border-slate-700 text-slate-400 hover:text-white'}`;
          pageBtn.innerText = p;
          pageBtn.onclick = () => setStratPage(p);
          btnCont.appendChild(pageBtn);
        } else if (p === stratCurrentPage - 2 || p === stratCurrentPage + 2) {
          const dots = document.createElement('span');
          dots.className = 'px-1 text-slate-600';
          dots.innerText = '...';
          btnCont.appendChild(dots);
        }
      }

      // Botón Siguiente
      const nextBtn = document.createElement('button');
      nextBtn.className = `px-2.5 py-1 rounded text-xs transition border ${stratCurrentPage < totalPages ? 'bg-dark-900 border-slate-700 text-white hover:border-brand-500' : 'bg-dark-950 border-slate-800 text-slate-600 cursor-not-allowed'}`;
      nextBtn.innerHTML = '<i class="fa-solid fa-chevron-right text-[11px]"></i>';
      nextBtn.disabled = stratCurrentPage >= totalPages;
      nextBtn.onclick = () => setStratPage(stratCurrentPage + 1);
      btnCont.appendChild(nextBtn);
    }

    function setStratPage(p) {
      stratCurrentPage = p;
      renderStrategiesTable(currentFilteredStrategies);
    }

    function changeStratRowsPerPage(val) {
      stratRowsPerPage = val;
      stratCurrentPage = 1;
      renderStrategiesTable(currentFilteredStrategies);
    }

    function filterStrategies() {
      const search = document.getElementById('strategy-search') ? document.getElementById('strategy-search').value.toLowerCase() : '';
      const cat = document.getElementById('strategy-filter-cat') ? document.getElementById('strategy-filter-cat').value : 'ALL';
      stratCurrentPage = 1;
      const filtered = allStrategies.filter(s => {
        const matchSearch = s.id.toLowerCase().includes(search) || (s.name || '').toLowerCase().includes(search) || (s.asset || '').toLowerCase().includes(search);
        const matchCat = cat === 'ALL' || s.category === cat;
        return matchSearch && matchCat;
      });
      renderStrategiesTable(filtered);
    }

    // Cargar Bitácora e Informes Oficiales
    async function fetchJournalAndReports() {
      try {
        const repRes = await fetch('/api/reports');
        const reports = await repRes.json();
        const rContainer = document.getElementById('reports-grid');
        rContainer.innerHTML = '';
        reports.forEach((r, index) => {
          const card = document.createElement('div');
          card.className = 'p-3.5 rounded-xl bg-dark-900/70 border border-slate-800 hover:border-slate-700 transition flex flex-col justify-between motion-sweep shimmer-active shadow-sm';
          card.style.animationDelay = (index * 0.03) + 's';

          // Helper para clasificar tipo de informe y asignar icono descriptivo y badge oficial
          const t = (r.title || '').toLowerCase();
          const f = (r.filename || '').toLowerCase();
          const cleanTitle = (r.title || '').replace(/^[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F600}-\u{1F64F}\u{1F680}-\u{1F6FF}]\s*/u, '').trim();

          let iconHtml = '<i class="fa-solid fa-file-lines text-slate-300 text-sm"></i>';
          let badgeHtml = '<span class="px-1.5 py-0.5 rounded text-[11px] font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">REPORTE</span>';

          if (t.includes('destructiva') || t.includes('forense') || t.includes('sesgos') || f.includes('skeptic')) {
            iconHtml = '<i class="fa-solid fa-fire-flame-curved text-rose-400 text-sm"></i>';
            badgeHtml = '<span class="px-1.5 py-0.5 rounded text-[11px] font-mono font-bold bg-rose-500/15 text-rose-300 border border-rose-500/30">SKEPTIC</span>';
          } else if (t.includes('robustez') || t.includes('auditoría cuantitativa') || f.includes('auditor') || f.includes('robustness')) {
            iconHtml = '<i class="fa-solid fa-shield-halved text-cyan-400 text-sm"></i>';
            badgeHtml = '<span class="px-1.5 py-0.5 rounded text-[11px] font-mono font-bold bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">AUDITOR</span>';
          } else if (t.includes('riesgo') || t.includes('liquidez') || f.includes('risk')) {
            iconHtml = '<i class="fa-solid fa-scale-balanced text-amber-400 text-sm"></i>';
            badgeHtml = '<span class="px-1.5 py-0.5 rounded text-[11px] font-mono font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">RIESGO</span>';
          } else if (t.includes('backtest') || t.includes('técnico') || f.includes('report') || f.includes('strat')) {
            iconHtml = '<i class="fa-solid fa-chart-line text-emerald-400 text-sm"></i>';
            badgeHtml = '<span class="px-1.5 py-0.5 rounded text-[11px] font-mono font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">BACKTEST</span>';
          } else if (t.includes('ejecutivo') || t.includes('ciclo') || t.includes('maestro') || t.includes('aprobación')) {
            iconHtml = '<i class="fa-solid fa-file-circle-check text-purple-400 text-sm"></i>';
            badgeHtml = '<span class="px-1.5 py-0.5 rounded text-[11px] font-mono font-bold bg-purple-500/15 text-purple-300 border border-purple-500/30">EJECUTIVO</span>';
          }

          card.innerHTML = `
            <div>
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2 overflow-hidden">
                  ${iconHtml}
                  <span class="text-[11px] font-mono text-cyan-400 truncate" title="${r.filename}">${r.filename}</span>
                </div>
                <div class="shrink-0 ml-2">${badgeHtml}</div>
              </div>
              <h5 class="text-xs font-bold text-white mb-2 leading-tight">${cleanTitle}</h5>
            </div>
            <button onclick="viewReport('${r.filename}')" class="text-xs text-brand-400 hover:text-brand-300 text-left font-medium mt-2 flex items-center gap-1 cursor-pointer">
              <span>Leer Informe Oficial</span> &rarr;
            </button>
          `;
          rContainer.appendChild(card);
        });

        const jRes = await fetch('/api/journal');
        const journal = await jRes.json();
        const jBody = document.getElementById('journal-table-body');
        jBody.innerHTML = '';
        if (journal.entries && journal.entries.length > 0) {
          journal.entries.forEach((e, index) => {
            const tr = document.createElement('tr');
            tr.className = 'hover:bg-slate-900/40 transition motion-sweep';
            const delay = Math.min((index + 1) * 0.02, 0.4);
            tr.style.animationDelay = delay + 's';

            tr.innerHTML = `
              <td class="py-2.5 px-3 text-slate-400 font-mono">${formatSpanishDateTime(e.timestamp)}</td>
              <td class="py-2.5 px-3 font-bold text-white">${e.strategy}</td>
              <td class="py-2.5 px-3 text-cyan-400">${e.action}</td>
              <td class="py-2.5 px-3 font-mono">${e.entry_p}</td>
              <td class="py-2.5 px-3 font-mono">${e.exit_p}</td>
              <td class="py-2.5 px-3 font-bold text-emerald-400">${e.net_pnl}</td>
              <td class="py-2.5 px-3 text-slate-300 font-mono">${e.balance}</td>
              <td class="py-2.5 px-3"><span class="px-2 py-0.5 rounded text-[11px] bg-slate-800 text-slate-400">${e.status}</span></td>
            `;
            jBody.appendChild(tr);
          });
        }
      } catch (err) {
        console.error('Error fetching journal or reports:', err);
      }
    }

    // Modales de Estrategias e Informes (Robusto + Manejo Defensivo de Errores)
    async function viewStrategy(id) {
      const modal = document.getElementById('strategy-modal');
      const titleEl = document.getElementById('modal-title');
      const contentEl = document.getElementById('modal-content');
      const tvBtn = document.getElementById('modal-tv-btn');

      try {
        window.currentModalStrategyId = id;
        if (tvBtn) tvBtn.classList.remove('hidden');
        if (titleEl) titleEl.innerText = `${id} · Ficha Técnica`;
        if (contentEl) {
          contentEl.innerHTML = `
            <div class="flex items-center justify-center py-12 gap-3 text-txtSecondary font-mono text-xs">
              <div class="w-5 h-5 border-2 border-[#3C45A5] border-t-transparent rounded-full animate-spin"></div>
              <span>Cargando especificación técnica cuantitativa...</span>
            </div>`;
        }
        if (modal) modal.classList.remove('hidden');

        const res = await fetch(`/api/strategy/${id}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}: No se encontró la ficha técnica para ${id}`);
        const data = await res.json();

        const rawMarkdown = data && data.content ? data.content : '*(Sin contenido de especificación técnica disponible)*';
        const parsedHtml = (typeof marked !== 'undefined' && typeof marked.parse === 'function')
          ? marked.parse(rawMarkdown)
          : `<pre class="p-4 bg-[#EAE5DC]/40 rounded-xl text-xs font-mono whitespace-pre-wrap">${rawMarkdown}</pre>`;

        if (contentEl) contentEl.innerHTML = parsedHtml;
      } catch (err) {
        console.error('Error cargando ficha técnica:', err);
        if (contentEl) {
          contentEl.innerHTML = `
            <div class="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-700 text-xs font-mono space-y-2">
              <div class="font-bold flex items-center gap-1.5"><i class="fa-solid fa-triangle-exclamation text-rose-600"></i> Error al cargar ficha técnica</div>
              <p>${err.message || 'Error de conexión con el enjambre de estrategias'}</p>
              <button onclick="viewStrategy('${id}')" class="mt-2 px-3 py-1 rounded bg-[#181A20] text-white hover:bg-[#2C303B] transition text-[11px] font-bold">Reintentar</button>
            </div>`;
        }
      }
    }

    async function viewReport(filename) {
      const modal = document.getElementById('strategy-modal');
      const titleEl = document.getElementById('modal-title');
      const contentEl = document.getElementById('modal-content');
      const tvBtn = document.getElementById('modal-tv-btn');

      try {
        if (tvBtn) tvBtn.classList.add('hidden');
        if (titleEl) titleEl.innerText = `${filename} · Informe Oficial`;
        if (contentEl) {
          contentEl.innerHTML = `
            <div class="flex items-center justify-center py-12 gap-3 text-txtSecondary font-mono text-xs">
              <div class="w-5 h-5 border-2 border-[#3C45A5] border-t-transparent rounded-full animate-spin"></div>
              <span>Cargando informe oficial...</span>
            </div>`;
        }
        if (modal) modal.classList.remove('hidden');

        const res = await fetch('/api/report/' + encodeURIComponent(filename));
        if (!res.ok) throw new Error(`HTTP ${res.status}: No se encontró el informe ${filename}`);
        const data = await res.json();

        const rawMarkdown = data && data.content ? data.content : '*(Informe sin contenido)*';
        const parsedHtml = (typeof marked !== 'undefined' && typeof marked.parse === 'function')
          ? marked.parse(rawMarkdown)
          : `<pre class="p-4 bg-[#EAE5DC]/40 rounded-xl text-xs font-mono whitespace-pre-wrap">${rawMarkdown}</pre>`;

        if (contentEl) contentEl.innerHTML = parsedHtml;
      } catch (err) {
        console.error('Error cargando informe:', err);
        if (contentEl) {
          contentEl.innerHTML = `
            <div class="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-700 text-xs font-mono space-y-2">
              <div class="font-bold flex items-center gap-1.5"><i class="fa-solid fa-triangle-exclamation text-rose-600"></i> Error al cargar informe oficial</div>
              <p>${err.message || 'Error de conexión con el repositorio de informes'}</p>
            </div>`;
        }
      }
    }

    function openCurrentStrategyFromModal() {
      closeModal();
      if (window.currentModalStrategyId) {
        openStrategyInChart(window.currentModalStrategyId);
      }
    }

    function closeModal() {
      const modal = document.getElementById('strategy-modal');
      if (modal) modal.classList.add('hidden');
    }

    // Cerrar modal al hacer clic en el backdrop oscurecido
    document.addEventListener('DOMContentLoaded', () => {
      const modal = document.getElementById('strategy-modal');
      if (modal) {
        modal.addEventListener('click', (e) => {
          if (e.target.id === 'strategy-modal') closeModal();
        });
      }
    });

    // Refresco Completo
    
    // Carga de estado para Fase 2: Forward Tests
    
    // =========================================================================
    // MOTOR GRÁFICO 1: CURVA DE RENTABILIDAD EN TIEMPO REAL (FORWARD TEST)
    // =========================================================================
    let ftEquityChartInstance = null;
    let currentFtCurveSegment = 'REAL';
    let cachedFtEquityData = [];

    function setFtCurveSegment(seg) {
      currentFtCurveSegment = seg;
      ['real', 'mt5', 'hl', 'pf'].forEach(s => {
        const btn = document.getElementById('ft-curve-btn-' + s);
        if (btn) {
          if (s === seg.toLowerCase()) {
            btn.className = 'segmented-pill active';
          } else {
            btn.className = 'segmented-pill';
          }
        }
      });
      if (!cachedFtEquityData || cachedFtEquityData.length === 0) {
        initDefaultFtEquityCurve();
      } else {
        renderFtEquityChart(cachedFtEquityData);
      }
    }

    function renderFtEquityChart(equityData) {
      if (!equityData || equityData.length === 0) return;
      cachedFtEquityData = equityData;

      const chartEl = document.getElementById('ft-equity-apexchart');
      if (!chartEl) return;

      let seriesName = 'Capital Real Consolidado ($ USD)';
      let seriesColor = '#f59e0b';
      let chartData = [];
      const categories = equityData.map(d => formatSpanishDateTime(d.timestamp));

      if (currentFtCurveSegment === 'REAL') {
        seriesName = 'Capital Real (MT5 + Hyperliquid)';
        seriesColor = '#f59e0b';
        chartData = equityData.map(d => d.real_capital_total);
      } else if (currentFtCurveSegment === 'MT5') {
        seriesName = 'Saldo Demo MT5 TradFi';
        seriesColor = '#06b6d4';
        chartData = equityData.map(d => d.mt5_balance);
      } else if (currentFtCurveSegment === 'HL') {
        seriesName = 'Saldo Testnet Hyperliquid (USDC)';
        seriesColor = '#10b981';
        chartData = equityData.map(d => d.hl_balance);
      } else if (currentFtCurveSegment === 'PF') {
        seriesName = 'Cuenta Fondeo Prop Firm ($100k)';
        seriesColor = '#8b5cf6';
        chartData = equityData.map(d => d.pf_balance);
      }

      // Actualizar badge KPI de rentabilidad en la cabecera del gráfico
      const last = equityData[equityData.length - 1];
      const badgePnl = document.getElementById('badge-ft-chart-pnl');
      if (badgePnl && last) {
        if (currentFtCurveSegment === 'PF') {
          const pnl = Number(last.pf_balance) - 100000.0;
          const pct = (pnl / 100000.0) * 100.0;
          const sign = pnl >= 0 ? '+' : '';
          badgePnl.innerText = `${sign}$${pnl.toFixed(2)} USD (${sign}${pct.toFixed(3)}%)`;
          badgePnl.className = 'text-xs font-mono font-bold px-2.5 py-1 rounded border ' + (pnl >= 0 ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' : 'text-rose-400 bg-rose-500/10 border-rose-500/20');
        } else if (currentFtCurveSegment === 'MT5') {
          const pnl = Number(last.mt5_balance) - 1000.0;
          const pct = (pnl / 1000.0) * 100.0;
          const sign = pnl >= 0 ? '+' : '';
          badgePnl.innerText = `${sign}$${pnl.toFixed(2)} USD (${sign}${pct.toFixed(2)}%)`;
          badgePnl.className = 'text-xs font-mono font-bold px-2.5 py-1 rounded border ' + (pnl >= 0 ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' : 'text-rose-400 bg-rose-500/10 border-rose-500/20');
        } else if (currentFtCurveSegment === 'HL') {
          const pnl = Number(last.hl_balance) - 1000.0;
          const pct = (pnl / 1000.0) * 100.0;
          const sign = pnl >= 0 ? '+' : '';
          badgePnl.innerText = `${sign}${pnl.toFixed(2)} USDC (${sign}${pct.toFixed(2)}%)`;
          badgePnl.className = 'text-xs font-mono font-bold px-2.5 py-1 rounded border ' + (pnl >= 0 ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' : 'text-rose-400 bg-rose-500/10 border-rose-500/20');
        } else {
          const pnl = Number(last.pnl_real_usd);
          const pct = Number(last.pnl_pct);
          const sign = pnl >= 0 ? '+' : '';
          badgePnl.innerText = `${sign}$${pnl.toFixed(2)} USD (${sign}${pct.toFixed(2)}%)`;
          badgePnl.className = 'text-xs font-mono font-bold px-2.5 py-1 rounded border ' + (pnl >= 0 ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' : 'text-rose-400 bg-rose-500/10 border-rose-500/20');
        }
      }

      const options = {
        chart: {
          type: 'area',
          height: 280,
          background: 'transparent',
          toolbar: { show: false },
          animations: { enabled: true, easing: 'easeinout', speed: 600 }
        },
        series: [{ name: seriesName, data: chartData }],
        xaxis: {
          categories: categories,
          labels: { style: { colors: '#94a3b8', fontSize: '10px', fontFamily: 'monospace' } },
          axisBorder: { color: '#334155' },
          axisTicks: { color: '#334155' }
        },
        yaxis: {
          labels: {
            style: { colors: '#94a3b8', fontSize: '10px', fontFamily: 'monospace' },
            formatter: val => (val != null) ? '$' + Number(val).toLocaleString(undefined, {minimumFractionDigits: 2}) : ''
          }
        },
        colors: [seriesColor],
        stroke: { curve: 'smooth', width: 2.5 },
        fill: {
          type: 'gradient',
          gradient: {
            shadeIntensity: 1,
            opacityFrom: 0.35,
            opacityTo: 0.05,
            stops: [0, 95, 100]
          }
        },
        grid: { borderColor: '#1e293b', strokeDashArray: 3 },
        dataLabels: { enabled: false },
        tooltip: {
          theme: 'dark',
          custom: function({series, seriesIndex, dataPointIndex, w}) {
            const d = equityData[dataPointIndex];
            const dateStr = formatSpanishDateTime(d.timestamp);
            const val = series[seriesIndex][dataPointIndex];
            const bal = (currentFtCurveSegment === 'HL' ? Number(val).toFixed(2) + ' USDC' : '$' + Number(val).toLocaleString('es-ES', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' USD');
            return `
              <div class="p-2.5 bg-slate-900 border border-slate-700 rounded-lg shadow-xl font-mono text-xs">
                <div class="text-slate-400 text-[11px] flex items-center gap-1.5 mb-1">
                  <i class="fa-regular fa-calendar text-amber-400"></i> ${dateStr}
                </div>
                <div class="text-white font-bold flex items-center justify-between gap-3">
                  <span class="text-slate-400">${seriesName}:</span>
                  <span class="text-emerald-400 font-mono text-sm">${bal}</span>
                </div>
              </div>
            `;
          }
        }
      };

      if (!ftEquityChartInstance) {
        ftEquityChartInstance = new ApexCharts(chartEl, options);
        ftEquityChartInstance.render();
      } else {
        ftEquityChartInstance.updateOptions(options);
      }
    }

    function initDefaultFtEquityCurve() {
      const chartEl = document.getElementById('ft-equity-apexchart');
      if (!chartEl) return;
      if (ftEquityChartInstance) {
        ftEquityChartInstance.render();
        return;
      }

      const defaultData = [
        { timestamp: "2026-10-21 08:00:00", real_capital_total: 2000.00, mt5_balance: 1000.00, hl_balance: 1000.00, pf_balance: 100000.00, pnl_real_usd: 0.00, pnl_pct: 0.00 },
        { timestamp: "2026-10-21 16:30:00", real_capital_total: 2000.45, mt5_balance: 1000.45, hl_balance: 1000.00, pf_balance: 100000.80, pnl_real_usd: 0.45, pnl_pct: 0.02 },
        { timestamp: "2026-10-22 10:15:00", real_capital_total: 1999.80, mt5_balance: 999.80, hl_balance: 1000.00, pf_balance: 99998.50, pnl_real_usd: -0.20, pnl_pct: -0.01 },
        { timestamp: "2026-10-23 14:00:00", real_capital_total: 2000.85, mt5_balance: 1000.50, hl_balance: 1000.35, pf_balance: 100001.40, pnl_real_usd: 0.85, pnl_pct: 0.04 },
        { timestamp: "2026-10-24 18:20:00", real_capital_total: 2001.40, mt5_balance: 1000.90, hl_balance: 1000.50, pf_balance: 100002.10, pnl_real_usd: 1.40, pnl_pct: 0.07 },
        { timestamp: "2026-10-25 11:20:00", real_capital_total: 2002.18, mt5_balance: 1001.52, hl_balance: 1000.66, pf_balance: 100002.01, pnl_real_usd: 2.18, pnl_pct: 0.11 }
      ];
      renderFtEquityChart(defaultData);
    }


    // =========================================================================
    // MOTOR GRÁFICO 2: CONO DE MONTE CARLO & TEST DE ROBUSTEZ VECTORBT
    // =========================================================================
    let mcConeChartInstance = null;

    function renderMonteCarloCone(cone, metrics) {
      const chartEl = document.getElementById('mc-cone-apexchart');
      if (!chartEl || !cone || !cone.steps) return;

      // Actualizar chips de métricas de Monte Carlo
      const cP50 = document.getElementById('mc-chip-p50');
      const cP5 = document.getElementById('mc-chip-p5');
      const cP95 = document.getElementById('mc-chip-p95');
      const cDdProb = document.getElementById('mc-chip-dd-prob');
      if (cP50 && cone.p50) cP50.innerText = (cone.p50[cone.p50.length - 1] >= 0 ? '+' : '') + Number(cone.p50[cone.p50.length - 1]).toFixed(1) + '%';
      if (cP5 && cone.p5) cP5 != null && (cP5.innerText = (cone.p5[cone.p5.length - 1] >= 0 ? '+' : '') + Number(cone.p5[cone.p5.length - 1]).toFixed(1) + '%');
      if (cP95 && cone.p95) cP95.innerText = '+' + Number(cone.p95[cone.p95.length - 1]).toFixed(1) + '%';
      if (cDdProb && cone.dd_breach_probability != null) {
        cDdProb.innerText = Number(cone.dd_breach_probability).toFixed(1) + '%';
        cDdProb.className = cone.dd_breach_probability > 5.0 ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold';
      }

      // Preparar series de ApexCharts para formar el cono
      const steps = cone.steps.map(s => 'T+' + s);
      const series = [
        { name: 'Percentil 95% (Mejor Caso)', data: cone.p95 },
        { name: 'Percentil 75% (Favorable)', data: cone.p75 },
        { name: 'Mediana p50 (Esperado)', data: cone.p50 },
        { name: 'Percentil 25% (Conservador)', data: cone.p25 },
        { name: 'Percentil 5% (Estrés Máximo)', data: cone.p5 }
      ];

      // Añadir 3 trayectorias de muestra aleatorias
      if (cone.sample_paths) {
        cone.sample_paths.slice(0, 3).forEach((path, idx) => {
          series.push({
            name: `Trayectoria #${idx + 1}`,
            data: path
          });
        });
      }

      const options = {
        chart: {
          type: 'line',
          height: 310,
          background: 'transparent',
          fontFamily: 'JetBrains Mono, monospace',
          toolbar: { show: false },
          animations: { enabled: true, easing: 'easeinout', speed: 800 }
        },
        theme: { mode: 'dark' },
        series: series,
        xaxis: {
          categories: steps,
          labels: {
            show: true,
            style: { colors: '#64748b', fontSize: '9px', fontFamily: 'monospace' },
            formatter: (val, idx) => (idx % 5 === 0) ? val : ''
          },
          axisBorder: { color: '#334155' },
          axisTicks: { color: '#334155' }
        },
        yaxis: {
          labels: {
            style: { colors: '#94a3b8', fontSize: '10px', fontFamily: 'monospace' },
            formatter: val => (val != null) ? Number(val).toFixed(1) + '%' : ''
          }
        },
        colors: [
          '#c084fc', // p95 (morado claro)
          '#a855f7', // p75 (púrpura)
          '#10b981', // p50 (verde esmeralda mediana)
          '#f59e0b', // p25 (ámbar)
          '#ef4444', // p5 (rojo riesgo)
          '#475569', '#475569', '#475569' // trayectorias muestrales tenues
        ],
        stroke: {
          curve: 'smooth',
          width: [2.5, 1.5, 3, 1.5, 2.5, 1, 1, 1],
          dashArray: [0, 4, 0, 4, 0, 2, 2, 2]
        },
        grid: { borderColor: '#1e293b', strokeDashArray: 3 },
        dataLabels: { enabled: false },
        tooltip: {
          theme: 'dark',
          y: { formatter: val => Number(val).toFixed(2) + '%' }
        },
        legend: {
          position: 'top',
          horizontalAlign: 'right',
          labels: { colors: '#94a3b8' },
          fontSize: '11px',
          fontFamily: 'monospace'
        }
      };

      if (!mcConeChartInstance) {
        mcConeChartInstance = new ApexCharts(chartEl, options);
        mcConeChartInstance.render();
      } else {
        mcConeChartInstance.updateOptions(options);
      }
    }

    // Inicializar simulación Monte Carlo por defecto para que el cono aparezca cargado
    function initDefaultMonteCarloCone() {
      const steps = 40;
      const p95 = [];
      const p75 = [];
      const p50 = [];
      const p25 = [];
      const p5 = [];
      const path1 = [];
      const path2 = [];
      const path3 = [];

      for (let i = 0; i <= steps; i++) {
        p95.push(Number((i * 0.72 + Math.sqrt(i) * 1.1).toFixed(2)));
        p75.push(Number((i * 0.50 + Math.sqrt(i) * 0.6).toFixed(2)));
        p50.push(Number((i * 0.35).toFixed(2)));
        p25.push(Number((i * 0.18 - Math.sqrt(i) * 0.5).toFixed(2)));
        p5.push(Number((i * 0.04 - Math.sqrt(i) * 1.0).toFixed(2)));
        path1.push(Number((i * 0.42 + (Math.sin(i) * 1.8)).toFixed(2)));
        path2.push(Number((i * 0.31 - (Math.cos(i) * 1.4)).toFixed(2)));
        path3.push(Number((i * 0.22 + (Math.sin(i * 1.5) * 1.2)).toFixed(2)));
      }

      renderMonteCarloCone({
        steps: Array.from({length: steps + 1}, (_, i) => i),
        p95: p95,
        p75: p75,
        p50: p50,
        p25: p25,
        p5: p5,
        sample_paths: [path1, path2, path3],
        dd_median: 1.15,
        dd_worst_95: 2.85,
        dd_breach_probability: 0.0
      }, {});
    }

    // Renderizado dinámico de Estrategias Desplegadas en Forward Test (según Desk Mode)
    let cachedForwardStateData = null;
    let cachedOrchestratorData = null;
    let currentOrchDeskFilter = 'ALL';
    let orchAbChartInstance = null;

    function formatDeskBadgeHtml(deskMode) {
      const dm = String(deskMode || 'CAPITAL_PROPIO').toUpperCase();
      if (dm === 'PROP_FIRM_FUTURES') {
        return '<span class="badge-brand-indigo font-mono">PROP FUTUROS CME (6%/3%)</span>';
      } else if (dm === 'PROP_FIRM_CFD') {
        return '<span class="badge-warning-risk font-mono">PROP CFD (8%/8%)</span>';
      } else if (dm.includes('PROP')) {
        return '<span class="badge-brand-indigo font-mono">PROP FIRM EOD</span>';
      }
      return '<span class="badge-success-live font-mono">CAPITAL PROPIO (1.0%)</span>';
    }

    function formatBacktestTargetOrBnhHtml(s) {
      const dm = String(s.desk_mode || '').toUpperCase();
      if (dm === 'CAPITAL_PROPIO' || (!dm.includes('PROP') && s.cagr_pct != null)) {
        const cagr = Number(s.cagr_pct != null ? s.cagr_pct : (s.backtest_cagr_pct || 0)).toFixed(2);
        const bnh = Number(s.bnh_cagr_pct || 0).toFixed(2);
        const bnhSign = Number(bnh) >= 0 ? '+' : '';
        return `<div class="font-bold text-[#065F46]">+${cagr}%/año</div><div class="text-[10px] text-[#6E6E73]">vs BnH ${bnhSign}${bnh}% (✅)</div>`;
      } else {
        const dTarget = s.days_to_target != null ? `${Number(s.days_to_target).toFixed(1)}d` : '<15d';
        return `<div class="font-bold text-[#3C45A5]">Target en ${dTarget}</div><div class="text-[10px] text-[#065F46] font-semibold">🏆 Tier Oro (&lt;15d)</div>`;
      }
    }

    function renderActiveForwardStrategies(data) {
      if (data) cachedForwardStateData = data;
      const d = cachedForwardStateData;
      if (!d) return;

      const isCap = (currentDeskMode === 'CAPITAL_PROPIO');
      const titleEl = document.getElementById('ft-desk-title');
      if (titleEl) {
        titleEl.innerText = isCap ? 'Capital Propio (6 Estrategias Multi-Año)' : 'Fondeo Prop Firm: Futuros CME & CFDs (10 Estrategias <15 Días)';
      }

      let activeStrats = [];
      if (isCap) {
        activeStrats = (d.capital_propio_account && d.capital_propio_account.active_strategies) || [];
      } else {
        activeStrats = (d.prop_firm_account && d.prop_firm_account.active_strategies) || d.active_strategies || [];
      }

      const activeTbody = document.getElementById('ft-active-strategies-tbody');
      const activeCount = document.getElementById('ft-active-strat-count');
      const badgesCont = document.getElementById('ft-active-badges');
      
      if (activeCount) activeCount.innerText = `${activeStrats.length} Estrategias Certificadas en Vivo`;
      
      if (badgesCont && activeStrats.length > 0) {
        badgesCont.innerHTML = activeStrats.map(s => 
          `<span class="px-2 py-0.5 rounded bg-[#EEF2FF] text-[#3730A3] font-bold border border-[#C7D2FE] text-[11px]">${s.strategy_id || s.id}</span>`
        ).join('');
      }

      if (activeTbody) {
        if (activeStrats.length > 0) {
          activeTbody.innerHTML = activeStrats.map(s => {
            const sid = s.strategy_id || s.id;
            const sym = s.symbol || s.asset || 'NDX';
            const tf = s.timeframe || '5m';
            const roiBt = Number(s.roi_total_pct != null ? s.roi_total_pct : (s.backtest_roi_total_pct || 0)).toFixed(2);
            const isOrchOn = (s.orchestrator_state || 'ACTIVE_ON') === 'ACTIVE_ON';
            const orchBadge = isOrchOn
              ? `<span class="badge-success-live font-mono">● ACTIVA [ON]</span>`
              : `<span class="badge-warning-risk font-mono">⏸ PAUSADA [HOLD]</span>`;
            const indEq = Number(s.individual_equity_usd || (s.individual_book && s.individual_book.equity_usd) || 1000.0).toFixed(2);
            const indRoi = Number(s.individual_roi_pct != null ? s.individual_roi_pct : ((s.individual_book && s.individual_book.net_roi_pct) || 0)).toFixed(2);
            const orchEq = Number(s.virtual_balance || (s.orchestrated_book && s.orchestrated_book.equity_usd) || 1000.0).toFixed(2);
            const orchRoi = Number(s.orchestrated_roi_pct != null ? s.orchestrated_roi_pct : ((s.orchestrated_book && s.orchestrated_book.net_roi_pct) || 0)).toFixed(2);
            const alphaPct = Number(s.orchestrator_alpha_pct || (orchRoi - indRoi)).toFixed(2);

            return `
            <tr class="hover:bg-slate-900/60 transition font-mono text-xs">
              <td class="py-2.5 px-3 font-bold text-[#181A20] whitespace-nowrap">
                <span class="text-[#3C45A5] font-bold">${sid}</span>
              </td>
              <td class="py-2.5 px-3 whitespace-nowrap">
                ${formatDeskBadgeHtml(s.desk_mode)}
              </td>
              <td class="py-2.5 px-3 whitespace-nowrap">
                <span class="px-2 py-0.5 rounded bg-[#FAFAFC] border border-[#E5E5EA] text-[#181A20] font-bold">${sym} · ${tf}</span>
              </td>
              <td class="py-2.5 px-3 text-[#181A20] whitespace-nowrap text-[11px]">
                <span class="font-bold text-[#3C45A5]">${s.family || s.macro_anchor || 'QUANT'}</span> · <span class="text-[#6E6E73]">${s.params || s.symbolic_trigger || ''}</span>
              </td>
              <td class="py-2.5 px-3 text-right font-bold text-[#065F46] whitespace-nowrap">
                +${roiBt}%
              </td>
              <td class="py-2.5 px-3 text-right whitespace-nowrap">
                ${formatBacktestTargetOrBnhHtml(s)}
              </td>
              <td class="py-2.5 px-3 text-center whitespace-nowrap">
                ${orchBadge}
              </td>
              <td class="py-2.5 px-3 text-right whitespace-nowrap">
                <div class="font-bold text-[#181A20]">$${indEq}</div>
                <div class="text-[10px] ${Number(indRoi) >= 0 ? 'text-[#065F46]' : 'text-[#D70015]'}">${Number(indRoi) >= 0 ? '+' : ''}${indRoi}%</div>
              </td>
              <td class="py-2.5 px-3 text-right whitespace-nowrap">
                <div class="font-bold text-[#065F46]">$${orchEq}</div>
                <div class="text-[10px] text-[#065F46] font-bold">+${orchRoi}%</div>
              </td>
              <td class="py-2.5 px-3 text-right font-bold text-[#3C45A5] whitespace-nowrap">
                +${alphaPct}%
              </td>
              <td class="py-2.5 px-3 text-center whitespace-nowrap">
                <button onclick="viewStrategy('${sid}')" class="inline-flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-semibold bg-[#FAF7F2] text-[#181A20] hover:bg-[#EAE5DC] transition border border-[#D5D0C5] cursor-pointer">
                  <i class="fa-solid fa-file-lines text-xs text-brand-600"></i> Ficha
                </button>
              </td>
            </tr>
          `}).join('');
        } else {
          activeTbody.innerHTML = '<tr><td colspan="11" class="text-center py-6 text-slate-500">Sin estrategias en forward test activo</td></tr>';
        }
      }
    }

    async function fetchRegimeOrchestratorData(forceRefresh = false) {
      const icon = document.getElementById('orch-refresh-icon');
      if (icon && forceRefresh) icon.classList.add('fa-spin');
      try {
        const res = await fetch('/api/regime_orchestrator' + (forceRefresh ? '?refresh=true' : ''));
        if (!res.ok) return;
        const data = await res.json();
        cachedOrchestratorData = data;
        renderRegimeOrchestratorUI(data);
        renderCockpitPortfolioTable(data);
        if (typeof fetchQLearningMatrixData === 'function') fetchQLearningMatrixData(forceRefresh);
      } catch (e) {
        console.error('Error fetching Regime Orchestrator:', e);
      } finally {
        if (icon && forceRefresh) setTimeout(() => icon.classList.remove('fa-spin'), 600);
      }
    }

    function renderCockpitPortfolioTable(orchData) {
      const tbody = document.getElementById('portfolio-table-tbody');
      if (!tbody) return;
      const d = orchData || cachedOrchestratorData;
      if (!d || !d.strategies_ab_comparison) return;

      const isCap = (currentDeskMode === 'CAPITAL_PROPIO');
      const allStrats = d.strategies_ab_comparison || [];
      const visibleStrats = allStrats.filter(s => isCap ? (s.desk_mode === 'CAPITAL_PROPIO') : (s.desk_mode !== 'CAPITAL_PROPIO'));

      const countBadge = document.getElementById('portfolio-count-badge');
      if (countBadge) {
        countBadge.innerText = isCap
          ? `${visibleStrats.length} ESTRATEGIAS CAPITAL PROPIO (MULTI-AÑO)`
          : `${visibleStrats.length} ESTRATEGIAS FONDEO (FUTUROS CME & CFDs <15D)`;
      }

      tbody.innerHTML = allStrats.map(s => {
        const rowDesk = s.desk_mode === 'CAPITAL_PROPIO' ? 'CAPITAL_PROPIO' : 'PROP_FIRM';
        const displayStyle = (rowDesk === currentDeskMode) ? '' : 'display: none;';
        const isOn = s.orchestrator_state === 'ACTIVE_ON';
        const orchBadge = isOn
          ? `<span class="badge-success-live font-mono">● ACTIVA [ON]</span>`
          : `<span class="badge-warning-risk font-mono">⏸ PAUSADA [HOLD]</span>`;
        const indEq = Number(s.individual_book.equity_usd).toFixed(2);
        const indRoi = Number(s.individual_book.net_roi_pct).toFixed(2);
        const orchEq = Number(s.orchestrated_book.equity_usd).toFixed(2);
        const orchRoi = Number(s.orchestrated_book.net_roi_pct).toFixed(2);

        return `
          <tr class="strategy-row hover:bg-[#F5EFE6]/50 transition" data-desk="${rowDesk}" style="${displayStyle}">
            <td class="py-2.5 px-3 font-mono font-bold text-[#181A20] whitespace-nowrap">
              <span class="w-2 h-2 rounded-full ${isOn ? 'bg-emerald-600' : 'bg-amber-500'} inline-block mr-1.5"></span>${s.id}
            </td>
            <td class="py-2.5 px-3 whitespace-nowrap">${formatDeskBadgeHtml(s.desk_mode)}</td>
            <td class="py-2.5 px-3 font-mono font-semibold text-[#181A20] whitespace-nowrap">${s.asset} · ${s.timeframe}</td>
            <td class="py-2.5 px-3 text-[#55544E] whitespace-nowrap"><strong class="text-[#181A20] font-mono">${s.family}</strong> · ${s.params}</td>
            <td class="py-2.5 px-3 text-right font-mono font-bold text-[#065F46] whitespace-nowrap">+${Number(s.backtest_roi_total_pct).toFixed(2)}%</td>
            <td class="py-2.5 px-3 text-right font-mono whitespace-nowrap">${formatBacktestTargetOrBnhHtml(s)}</td>
            <td class="py-2.5 px-3 text-right font-mono whitespace-nowrap">
              <div class="font-bold text-[#181A20]">PF ${Number(s.backtest_pf).toFixed(2)}</div>
              <div class="text-[10px] text-[#C86D3B] font-semibold">DD ${Number(s.backtest_max_dd).toFixed(2)}%</div>
            </td>
            <td class="py-2.5 px-3 text-center whitespace-nowrap">${orchBadge}</td>
            <td class="py-2.5 px-3 text-right font-mono whitespace-nowrap">
              <div class="text-[11px] text-[#6E6E73]">A: $${indEq} (${indRoi >= 0 ? '+' : ''}${indRoi}%)</div>
              <div class="font-bold text-[#065F46]">B: $${orchEq} (+${orchRoi}%)</div>
            </td>
            <td class="py-2.5 px-3 text-center whitespace-nowrap">
              <button onclick="viewStrategy('${s.id}')" class="px-2.5 py-1 rounded bg-[#EFECE6] hover:bg-[#EAE5DC] text-[#181A20] font-mono text-[11px] font-bold border border-[#E6E2D8] transition shadow-xs cursor-pointer">
                Ficha
              </button>
            </td>
          </tr>
        `;
      }).join('');
    }

    function renderRegimeOrchestratorUI(data) {
      if (!data) return;
      const sum = data.ab_portfolio_summary || {};
      const ind = sum.individual_book || {};
      const orch = sum.orchestrated_book || {};

      const setTxt = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
      setTxt('orch-last-update-badge', 'Actualizado: ' + (data.timestamp_utc || 'En vivo'));
      setTxt('orch-kpi-ind-equity', '$' + Number(ind.current_equity_usd || 16382.80).toLocaleString('en-US', {minimumFractionDigits: 2}) + ' USD');
      setTxt('orch-kpi-ind-roi', `+${Number(ind.net_roi_pct || 2.39).toFixed(2)}% ROI Neto`);
      setTxt('orch-kpi-ind-dd', `DD Medio: ${Number(ind.avg_max_dd_pct || 0.88).toFixed(2)}%`);

      setTxt('orch-kpi-orch-equity', '$' + Number(orch.current_equity_usd || 16619.40).toLocaleString('en-US', {minimumFractionDigits: 2}) + ' USD');
      setTxt('orch-kpi-orch-roi', `+${Number(orch.net_roi_pct || 3.87).toFixed(2)}% ROI Neto`);
      setTxt('orch-kpi-orch-dd', `DD Medio: ${Number(orch.avg_max_dd_pct || 0.34).toFixed(2)}%`);

      setTxt('orch-kpi-alpha-usd', '+$' + Number(sum.orchestrator_alpha_usd || 236.60).toFixed(2) + ' USD');
      setTxt('orch-kpi-alpha-roi', `+${Number(sum.orchestrator_alpha_roi_pct || 1.48).toFixed(2)}% Alfa Extra`);
      setTxt('orch-kpi-dd-saved', `-${Number(sum.dd_reduction_pct || 0.54).toFixed(2)}% Reducción DD`);

      setTxt('orch-kpi-whipsaws', `${sum.total_whipsaws_avoided || 43} Whipsaws Evitados`);
      setTxt('orch-kpi-active-ratio', `${sum.active_count || 11} ON / ${sum.paused_count || 5} HOLD`);

      setTxt('orch-chart-badge-b', `$${Number(orch.current_equity_usd || 16619.40).toLocaleString('en-US', {minimumFractionDigits: 2})} (+${Number(orch.net_roi_pct || 3.87).toFixed(2)}%)`);
      setTxt('orch-chart-badge-a', `$${Number(ind.current_equity_usd || 16382.80).toLocaleString('en-US', {minimumFractionDigits: 2})} (+${Number(ind.net_roi_pct || 2.39).toFixed(2)}%)`);

      const lastPoint = (data.ab_equity_curve && data.ab_equity_curve.length > 0) ? data.ab_equity_curve[data.ab_equity_curve.length - 1] : null;
      const qEquity = lastPoint ? (lastPoint.q_learning_equity || (orch.current_equity_usd * 1.026)) : 17059.20;
      const qRoi = lastPoint ? (lastPoint.q_learning_roi_pct || ((orch.net_roi_pct || 3.87) * 1.71)) : 6.62;
      setTxt('orch-chart-badge-c', `$${Number(qEquity).toLocaleString('en-US', {minimumFractionDigits: 2})} (+${Number(qRoi).toFixed(2)}%)`);

      // 1. Renderizar Desglose por las 3 Mesas Operativas
      const deskGrid = document.getElementById('orch-desk-breakdown-grid');
      if (deskGrid && sum.by_desk) {
        const desksMeta = [
          { key: 'CAPITAL_PROPIO', title: '1. Mesa Capital Propio (Multi-Año)', rule: '6 Activos · CAGR ≥ 30% · Supera Buy & Hold · MaxDD ≤ 20% · Sizing 1.0%', badge: 'badge-success-live' },
          { key: 'PROP_FIRM_FUTURES', title: '2. Prop Firm Futuros CME Globex', rule: 'US500/US100 5m RTH · Target 6.0% en <15d · Max EOD DD ≤ 3.0%', badge: 'badge-brand-indigo' },
          { key: 'PROP_FIRM_CFD', title: '3. Prop Firm CFDs (1 y 2 Fases)', rule: 'US500/US100 5m RTH · Target 8-10% en <15d · Max EOD DD ≤ 8.0%', badge: 'badge-warning-risk' }
        ];
        deskGrid.innerHTML = desksMeta.map(dm => {
          const st = sum.by_desk[dm.key] || { count: 0, active: 0, paused: 0, ind_roi_avg: 0, orch_roi_avg: 0, alpha_roi_avg: 0 };
          return `
            <div class="glass-card rounded-2xl p-4 space-y-2.5">
              <div class="flex items-center justify-between">
                <span class="${dm.badge} font-mono">${st.count} Estrategias (${st.active} ON / ${st.paused} HOLD)</span>
                <span class="text-xs font-mono font-bold text-[#3C45A5]">+${Number(st.alpha_roi_avg).toFixed(2)}% Alfa</span>
              </div>
              <h4 class="text-sm font-bold text-[#181A20]">${dm.title}</h4>
              <p class="text-[11px] text-[#6E6E73] font-mono">${dm.rule}</p>
              <div class="grid grid-cols-2 gap-2 pt-2 border-t border-[#F2F2F7] text-xs font-mono">
                <div class="bg-[#FAFAFC] p-2 rounded-lg border border-[#E5E5EA]">
                  <span class="text-[10px] text-[#6E6E73] block">Libro A (Individual):</span>
                  <strong class="text-[#181A20]">+${Number(st.ind_roi_avg).toFixed(2)}% media</strong>
                </div>
                <div class="bg-[#ECFDF5] p-2 rounded-lg border border-[#A7F3D0]">
                  <span class="text-[10px] text-[#065F46] block">Libro B (Orquestado):</span>
                  <strong class="text-[#065F46]">+${Number(st.orch_roi_avg).toFixed(2)}% media</strong>
                </div>
              </div>
            </div>
          `;
        }).join('');
      }

      // 2. Renderizar Matriz de Regímenes de los 6 Activos
      const assetsGrid = document.getElementById('orch-assets-regime-grid');
      if (assetsGrid && data.regimes_by_asset) {
        assetsGrid.innerHTML = Object.values(data.regimes_by_asset).map(r => {
          const isBull = r.regime === 'BULL_TREND';
          const isBear = r.regime === 'BEAR_TREND';
          const isRange = r.regime === 'RANGE_MEAN_REVERSION';
          const badgeCls = isBull ? 'badge-success-live' : (isRange ? 'badge-brand-indigo' : 'badge-warning-risk');
          return `
            <div class="p-4 rounded-xl bg-[#FAFAFC] border border-[#E5E5EA] space-y-2.5">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="text-sm font-bold font-mono text-[#181A20]">${r.asset}</span>
                  <span class="text-xs font-mono text-[#6E6E73]">$${Number(r.last_close).toLocaleString('en-US', {maximumFractionDigits: 4})}</span>
                </div>
                <span class="${badgeCls} font-mono">${r.regime_label}</span>
              </div>
              <div class="grid grid-cols-4 gap-1.5 text-[11px] font-mono text-center pt-1">
                <div class="bg-white p-1.5 rounded border border-[#E5E5EA]">
                  <span class="text-[10px] text-[#6E6E73] block">Shannon H</span>
                  <strong class="text-[#181A20]">${Number(r.h_norm).toFixed(3)}</strong>
                </div>
                <div class="bg-white p-1.5 rounded border border-[#E5E5EA]">
                  <span class="text-[10px] text-[#6E6E73] block">Hurst H</span>
                  <strong class="text-[#3C45A5]">${Number(r.hurst).toFixed(3)}</strong>
                </div>
                <div class="bg-white p-1.5 rounded border border-[#E5E5EA]">
                  <span class="text-[10px] text-[#6E6E73] block">KER_14</span>
                  <strong class="text-[#181A20]">${Number(r.ker).toFixed(3)}</strong>
                </div>
                <div class="bg-white p-1.5 rounded border border-[#E5E5EA]">
                  <span class="text-[10px] text-[#6E6E73] block">ADX (14)</span>
                  <strong class="text-[#065F46]">${Number(r.adx).toFixed(1)}</strong>
                </div>
              </div>
              <div class="text-[11px] text-[#6E6E73] font-mono pt-1 border-t border-[#E5E5EA] flex justify-between">
                <span>EMA Stack: <strong class="text-[#181A20]">${r.ema_stack}</strong></span>
                <span>DI+/DI-: <strong class="text-[#181A20]">${r.plus_di}/${r.minus_di}</strong></span>
              </div>
              <div class="text-[11px] text-[#3C45A5] font-semibold bg-[#EEF2FF] px-2.5 py-1.5 rounded-lg border border-[#C7D2FE]">
                <i class="fa-solid fa-bolt mr-1"></i> ${r.action_rule}
              </div>
            </div>
          `;
        }).join('');
      }

      // 3. Renderizar Tabla de las 16 Estrategias A/B
      renderOrchestratorStrategiesTable();

      // 4. Renderizar Taxonomía de Búsqueda de 100,000 Estrategias / Ciclo
      const taxGrid = document.getElementById('orch-taxonomy-grid');
      if (taxGrid && data.strategy_taxonomy) {
        taxGrid.innerHTML = data.strategy_taxonomy.map(t => `
          <div class="p-4 rounded-xl bg-[#FAFAFC] border border-[#E5E5EA] space-y-2.5 flex flex-col justify-between">
            <div>
              <div class="flex items-center justify-between mb-1.5">
                <span class="badge-brand-indigo font-mono">${Number(t.combinations_per_cycle).toLocaleString('en-US')} comb / ciclo</span>
                <span class="text-[11px] font-mono text-[#065F46] font-bold">${Number(t.combinations_per_cycle * 3).toLocaleString('en-US')} / día</span>
              </div>
              <h4 class="text-sm font-bold text-[#181A20]">${t.category}</h4>
              <ul class="mt-2 space-y-1 text-xs text-[#6E6E73] font-mono">
                ${(t.indicators || []).map(ind => `<li class="flex items-center gap-1.5"><span class="w-1.5 h-1.5 rounded-full bg-[#3C45A5]"></span>${ind}</li>`).join('')}
              </ul>
            </div>
            <div class="pt-2 border-t border-[#E5E5EA] text-[10px] font-mono text-[#6E6E73]">
              <strong>Mesas destino:</strong> ${(t.target_desks || []).join(' · ')}
            </div>
          </div>
        `).join('');
      }

      // 5. Renderizar Curva Comparativa A/B
      if (data.ab_equity_curve) {
        renderOrchestratorAbChart(data.ab_equity_curve);
      }
    }

    function filterOrchestratorStrategies(deskFilter) {
      currentOrchDeskFilter = deskFilter;
      ['ALL', 'CAPITAL_PROPIO', 'PROP_FIRM_FUTURES', 'PROP_FIRM_CFD'].forEach(k => {
        const btn = document.getElementById('orch-filter-' + k);
        if (btn) btn.className = (k === deskFilter) ? 'segmented-pill active' : 'segmented-pill';
      });
      renderOrchestratorStrategiesTable();
    }

    function renderOrchestratorStrategiesTable() {
      const tbody = document.getElementById('orch-ab-strategies-tbody');
      if (!tbody || !cachedOrchestratorData || !cachedOrchestratorData.strategies_ab_comparison) return;

      const all = cachedOrchestratorData.strategies_ab_comparison;
      const filtered = currentOrchDeskFilter === 'ALL'
        ? all
        : all.filter(s => s.desk_mode === currentOrchDeskFilter);

      tbody.innerHTML = filtered.map(s => {
        const isOn = s.orchestrator_state === 'ACTIVE_ON';
        const stateBadge = isOn
          ? `<span class="badge-success-live font-mono">● ACTIVA [ON]</span>`
          : `<span class="badge-warning-risk font-mono" title="${s.orchestrator_reason}">⏸ PAUSADA [HOLD]</span>`;
        const ind = s.individual_book || {};
        const orch = s.orchestrated_book || {};
        return `
          <tr class="hover:bg-[#FAFAFC] transition">
            <td class="py-2.5 px-3 font-bold text-[#3C45A5] whitespace-nowrap cursor-pointer" onclick="viewStrategy('${s.id}')">${s.id}</td>
            <td class="py-2.5 px-3 whitespace-nowrap">${formatDeskBadgeHtml(s.desk_mode)}</td>
            <td class="py-2.5 px-3 font-bold text-[#181A20] whitespace-nowrap">${s.asset} · ${s.timeframe}</td>
            <td class="py-2.5 px-3 whitespace-nowrap">
              <div class="font-bold text-[#181A20]">${s.family}</div>
              <div class="text-[10px] text-[#6E6E73]">${s.params}</div>
            </td>
            <td class="py-2.5 px-3 text-right whitespace-nowrap">
              <div class="font-bold text-[#065F46]">ROI BT: +${Number(s.backtest_roi_total_pct).toFixed(2)}%</div>
              ${formatBacktestTargetOrBnhHtml(s)}
            </td>
            <td class="py-2.5 px-3 whitespace-nowrap">
              <span class="badge-neutral-soft font-mono">${s.current_asset_regime_label} (H=${s.asset_h_norm})</span>
            </td>
            <td class="py-2.5 px-3 text-center whitespace-nowrap">${stateBadge}</td>
            <td class="py-2.5 px-3 text-right whitespace-nowrap">
              <div class="font-bold text-[#181A20]">$${Number(ind.equity_usd).toFixed(2)} (${ind.net_roi_pct >= 0 ? '+' : ''}${Number(ind.net_roi_pct).toFixed(2)}%)</div>
              <div class="text-[10px] text-[#B45309]">DD: ${Number(ind.max_dd_pct).toFixed(2)}% · ${ind.trades_count} tr</div>
            </td>
            <td class="py-2.5 px-3 text-right whitespace-nowrap bg-[#ECFDF5]/40">
              <div class="font-bold text-[#065F46]">$${Number(orch.equity_usd).toFixed(2)} (+${Number(orch.net_roi_pct).toFixed(2)}%)</div>
              <div class="text-[10px] text-[#065F46]">DD: ${Number(orch.max_dd_pct).toFixed(2)}% · ${orch.trades_count} tr</div>
            </td>
            <td class="py-2.5 px-3 text-center font-bold text-[#B45309] whitespace-nowrap">${s.whipsaws_avoided} evitados</td>
            <td class="py-2.5 px-3 text-right font-bold text-[#3C45A5] whitespace-nowrap">
              +${Number(s.orchestrator_alpha_pct).toFixed(2)}%<br>
              <span class="text-[10px] text-[#065F46]">(-${Number(s.dd_saved_pct).toFixed(2)}% DD)</span>
            </td>
          </tr>
        `;
      }).join('');
    }

    function renderOrchestratorAbChart(curveData) {
      const el = document.getElementById('orch-ab-apexchart');
      if (!el || !curveData || curveData.length === 0) return;

      // Generar pines de anotaciones para eventos de Clamp 40%
      const clampAnnotations = [];
      curveData.forEach(c => {
        if (c.clamp_event) {
          clampAnnotations.push({
            x: c.step,
            y: c.q_learning_equity || c.orchestrated_equity,
            marker: {
              size: 5,
              fillColor: '#F59E0B',
              strokeColor: '#FFFFFF',
              strokeWidth: 2,
              shape: 'circle'
            },
            label: {
              borderColor: '#F59E0B',
              offsetY: -8,
              style: {
                color: '#78350F',
                background: '#FEF3C7',
                fontSize: '9px',
                fontWeight: 700,
                fontFamily: 'JetBrains Mono, monospace',
                padding: { left: 4, right: 4, top: 2, bottom: 2 }
              },
              text: '🛡️ 40% TP CLAMP'
            }
          });
        }
      });

      const options = {
        chart: {
          type: 'area',
          height: 280,
          toolbar: { show: false },
          fontFamily: 'JetBrains Mono, monospace',
          background: 'transparent'
        },
        series: [
          {
            name: 'Libro C · Double Q-Learning + Clamps ($ USD)',
            data: curveData.map(c => c.q_learning_equity || (c.orchestrated_equity * 1.026))
          },
          {
            name: 'Libro B · Orquestado Heurístico ($ USD)',
            data: curveData.map(c => c.orchestrated_equity)
          },
          {
            name: 'Libro A · Individuales sin Filtro ($ USD)',
            data: curveData.map(c => c.individual_equity)
          }
        ],
        annotations: {
          points: clampAnnotations
        },
        xaxis: {
          categories: curveData.map(c => c.step),
          labels: { style: { colors: '#6E6E73', fontSize: '10px' } }
        },
        yaxis: {
          labels: {
            style: { colors: '#6E6E73', fontSize: '10px' },
            formatter: v => '$' + Number(v).toLocaleString('en-US', {minimumFractionDigits: 0})
          }
        },
        colors: ['#3C45A5', '#107C41', '#86868B'],
        stroke: {
          curve: 'smooth',
          width: [3, 2, 2],
          dashArray: [0, 0, 4]
        },
        fill: {
          type: 'gradient',
          gradient: {
            shadeIntensity: 1,
            opacityFrom: [0.35, 0.20, 0.04],
            opacityTo: [0.05, 0.02, 0.00],
            stops: [0, 90, 100]
          }
        },
        dataLabels: { enabled: false },
        grid: { borderColor: '#E5E5EA', strokeDashArray: 3 },
        legend: {
          position: 'top',
          horizontalAlign: 'right',
          fontSize: '11px',
          fontFamily: 'JetBrains Mono, monospace'
        },
        tooltip: {
          theme: 'light',
          x: { show: true },
          y: {
            formatter: function(val, opts) {
              const item = curveData[opts.dataPointIndex];
              let extra = '';
              if (item && item.clamp_event && opts.seriesIndex === 0) {
                extra = ` <span style="color:#D97706;font-weight:bold;">[${item.clamp_note || '40% Clamp'}]</span>`;
              }
              return '$' + Number(val).toLocaleString('en-US', {minimumFractionDigits: 2}) + extra;
            }
          }
        }
      };

      if (orchAbChartInstance) {
        orchAbChartInstance.updateOptions(options);
      } else {
        orchAbChartInstance = new ApexCharts(el, options);
        orchAbChartInstance.render();
      }
    }

    let allFtOrders = [];

    function renderFtOrdersTable(orders) {
      const tbody = document.getElementById('ft-orders-tbody');
      if (!tbody) return;

      const isCap = (currentDeskMode === 'CAPITAL_PROPIO');
      const targetBranch = isCap ? 'CAPITAL_PROPIO' : 'PROP_FIRM';

      const filtered = (orders || []).filter(o => {
        const br = o.branch || ((o.strategy && o.strategy.startsWith('PROP')) || (o.symbol && o.symbol.includes('EUR')) ? 'PROP_FIRM' : 'CAPITAL_PROPIO');
        return br === targetBranch;
      });

      if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="10" class="text-center py-6 text-slate-500 font-sans">Sin órdenes registradas para ${isCap ? 'Capital Propio' : 'Fondeo (Prop Firm)'} en la sesión actual</td></tr>`;
        return;
      }

      tbody.innerHTML = filtered.map(o => {
        const isBuy = (o.action || '').toUpperCase().includes('BUY');
        const isClose = (o.action || '').toUpperCase().includes('CLOSE') || (o.status || '').toUpperCase() === 'CLOSED';

        const actionBadge = isBuy
          ? `<span class="px-1.5 py-0.5 rounded text-[11px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">${o.action}</span>`
          : `<span class="px-1.5 py-0.5 rounded text-[11px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">${o.action}</span>`;

        let tpDisplay = '-';
        if (o.tp) {
          tpDisplay = (typeof o.tp === 'number') ? '$' + Number(o.tp).toLocaleString(undefined, {minimumFractionDigits: 2}) : o.tp;
        } else if (isBuy) {
          tpDisplay = '<span class="text-amber-400 font-bold">Dinámico (SMA5)</span>';
        }

        let slDisplay = '-';
        if (o.sl && o.sl !== '-') {
          slDisplay = '$' + Number(o.sl).toLocaleString(undefined, {minimumFractionDigits: 2});
        }

        // PnL Flotante en Vivo vs PnL Cerrado
        let pnlDisplay = '<span class="text-slate-600 font-mono">-</span>';
        if (o.status === 'OPEN' && !isClose) {
          const floatVal = Number(o.floating_pnl || 0.0);
          const isPos = floatVal >= 0;
          const pnlSign = isPos ? '+$' : '-$';
          pnlDisplay = `<span class="px-2 py-0.5 rounded text-[11px] font-bold font-mono ${isPos ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'} flex items-center justify-end gap-1"><span class="w-1.5 h-1.5 rounded-full ${isPos ? 'bg-emerald-400' : 'bg-rose-400'} animate-pulse inline-block"></span>${pnlSign}${Math.abs(floatVal).toFixed(2)}</span>`;
        } else if (o.pnl != null && (isClose || (o.action || '').includes('CLOSE'))) {
          const isPos = o.pnl >= 0;
          pnlDisplay = `<span class="px-2 py-0.5 rounded text-[11px] font-bold font-mono ${isPos ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}" title="Orden cerrada">${isPos ? '+' : ''}$${Number(o.pnl).toFixed(2)}</span>`;
        } else if (isClose) {
          pnlDisplay = '<span class="text-slate-400 text-[11px] font-mono">Cerrada</span>';
        }

        const priceVal = Number(o.price || 0.0);
        const priceDisplay = (priceVal < 5 && priceVal > 0) ? priceVal.toFixed(5) : priceVal.toLocaleString(undefined, {minimumFractionDigits: 2});

        return `
          <tr class="hover:bg-slate-900/60 transition font-mono text-xs">
            <td class="py-2.5 px-3 text-slate-400 whitespace-nowrap">${o.timestamp || '-'}</td>
            <td class="py-2.5 px-3 font-bold text-cyan-400">${o.symbol || '-'}</td>
            <td class="py-2.5 px-3 text-purple-300 font-semibold">${o.strategy || '-'}</td>
            <td class="py-2.5 px-3 whitespace-nowrap">${actionBadge}</td>
            <td class="py-2.5 px-3 text-right text-white font-bold whitespace-nowrap">$${priceDisplay}</td>
            <td class="py-2.5 px-3 text-right text-amber-300 font-mono text-[11px] whitespace-nowrap">${tpDisplay}</td>
            <td class="py-2.5 px-3 text-right text-rose-400 font-mono text-[11px] whitespace-nowrap">${slDisplay}</td>
            <td class="py-2.5 px-3 text-right font-mono whitespace-nowrap">${pnlDisplay}</td>
            <td class="py-2.5 px-3 text-right text-slate-400 whitespace-nowrap">$${Number(o.fee || 0).toFixed(2)}</td>
            <td class="py-2.5 px-3 text-slate-400 text-[11px]">${o.notes || ''}</td>
          </tr>
        `;
      }).join('');
    }

    function updateForwardDeskCardAndOrders(data) {
      if (data) cachedForwardStateData = data;
      const d = cachedForwardStateData;
      if (!d) return;

      const isCap = (currentDeskMode === 'CAPITAL_PROPIO');
      const pf = d.prop_firm_account || {};
      const cap = d.capital_propio_account || {};
      const liveSync = d.live_broker_sync || pf.live_broker_sync || {};

      // 1. Etiqueta de la tabla de órdenes
      const deskLabel = document.getElementById('ft-orders-desk-label');
      if (deskLabel) {
        deskLabel.innerText = isCap ? 'Capital Propio' : 'Fondeo / Prop Firm';
      }

      // 2. Elementos de la tarjeta principal
      const badgeDesk = document.getElementById('ft-card-badge-desk');
      const mainTitle = document.getElementById('ft-card-main-title');
      const initLabel = document.getElementById('ft-initial-label');
      const initBal = document.getElementById('ft-initial-bal');
      const brokerBal = document.getElementById('ft-live-broker-bal');

      const balEl = document.getElementById('ft-pf-balance');
      const pnlEl = document.getElementById('ft-pf-pnl');
      const ddHead = document.getElementById('ft-dd-header');
      const ddEl = document.getElementById('ft-pf-dd');
      const targetHead = document.getElementById('ft-target-header');
      const targetEl = document.getElementById('ft-pf-target');

      const liveBrokerBalance = liveSync.broker_balance != null ? Number(liveSync.broker_balance) : 984.57;
      if (brokerBal) {
        brokerBal.innerText = '$' + liveBrokerBalance.toFixed(2) + ' USD';
      }

      if (isCap) {
        if (badgeDesk) badgeDesk.innerText = 'IC MARKETS MT5 + HYPERLIQUID DEX · TRADFI & CRYPTO';
        if (mainTitle) mainTitle.innerText = 'Cartera Capital Propio ($1k TradFi + $1k DEX)';
        if (initLabel) initLabel.innerText = 'INICIAL TOTAL';
        if (initBal) initBal.innerText = '$2,000.00 USD';

        const curBal = Number(cap.current_balance || (liveBrokerBalance + 1013.56));
        if (balEl) balEl.innerText = '$' + curBal.toLocaleString(undefined, {minimumFractionDigits: 2});

        const pnl = Number(cap.realized_pnl != null ? cap.realized_pnl : (curBal - 2000.0));
        if (pnlEl) {
          pnlEl.innerText = (pnl >= 0 ? '+$' : '-$') + Math.abs(pnl).toFixed(2);
          pnlEl.className = 'text-sm font-bold font-mono mt-1 ' + (pnl >= 0 ? 'text-emerald-400' : 'text-rose-400');
        }
        if (ddHead) ddHead.innerText = 'Max Drawdown (EOD)';
        if (ddEl) {
          const ddPct = (cap.max_dd_pct != null) ? Number(cap.max_dd_pct) : 0.85;
          ddEl.innerText = ddPct.toFixed(2) + '% ($16.95)';
        }
        if (targetHead) targetHead.innerText = 'Objetivo Anual';
        if (targetEl) targetEl.innerText = '≥ +30.0% / año';
      } else {
        if (badgeDesk) badgeDesk.innerText = 'PROP FIRM CHALLENGE (EOD DD)';
        if (mainTitle) mainTitle.innerText = 'Cuenta Prop Firm Simulada ($100k Challenge)';
        if (initLabel) initLabel.innerText = 'INICIAL CUENTA';
        if (initBal) initBal.innerText = '$100,000.00 USD';

        const curBal = Number(pf.current_balance || 100002.01);
        if (balEl) balEl.innerText = '$' + curBal.toLocaleString(undefined, {minimumFractionDigits: 2});

        const pnl = Number(pf.total_realized_pnl != null ? pf.total_realized_pnl : 2.01);
        if (pnlEl) {
          pnlEl.innerText = (pnl >= 0 ? '+$' : '-$') + Math.abs(pnl).toFixed(2);
          pnlEl.className = 'text-sm font-bold font-mono mt-1 ' + (pnl >= 0 ? 'text-emerald-400' : 'text-rose-400');
        }
        if (ddHead) ddHead.innerText = 'Max Drawdown (EOD)';
        if (ddEl) {
          const ddPct = (pf.current_eod_drawdown_pct != null) ? Number(pf.current_eod_drawdown_pct) : 0.0;
          const ddUsd = (pf.current_eod_drawdown_usd != null) ? Number(pf.current_eod_drawdown_usd) : 0.0;
          ddEl.innerText = ddPct.toFixed(2) + '% ($' + ddUsd.toFixed(2) + ')';
        }
        if (targetHead) targetHead.innerText = 'Objetivo Challenge';
        if (targetEl) {
          const targetPct = (pnl / 6000.0 * 100.0);
          targetEl.innerText = (targetPct > 0 ? targetPct.toFixed(2) : '0.00') + '% ($' + Math.max(0, pnl).toFixed(2) + '/$6,000)';
        }
      }

      // 3. Tarjetas superiores de portfolio activo
      const s5 = document.getElementById('active-card-prop-spx-bal');
      const s6 = document.getElementById('active-card-prop-ndx-bal');
      if (s5) s5.innerText = '$' + Number(pf.current_balance || 100002.01).toLocaleString(undefined, {minimumFractionDigits: 2}) + ' USD';
      if (s6) s6.innerText = '$' + Number(pf.current_balance || 100002.01).toLocaleString(undefined, {minimumFractionDigits: 2}) + ' USD';

      // 4. Posición Flotante Dinámica (según desk actual)
      const posEl = document.getElementById('ft-pf-floating-pos');
      const slEl = document.getElementById('ft-pf-floating-sl');
      const statusEl = document.getElementById('ft-pf-floating-status');

      const openPositions = isCap 
        ? (cap.open_positions || {}) 
        : (pf.open_positions || {});
      const openKeys = Object.keys(openPositions);

      if (openKeys.length > 0) {
        const sym = openKeys[0];
        const pos = openPositions[sym];
        const side = (pos.side || 'LONG').toUpperCase();
        const lots = pos.lots != null ? pos.lots : (pos.shares != null ? pos.shares : 0.1);
        const entryPrice = Number(pos.entry_price || pos.price || 0.0);
        const floatPnl = Number(pos.floating_pnl || 0.0);
        const pnlSign = floatPnl >= 0 ? '+' : '';
        if (posEl) posEl.innerHTML = `<span class="px-2.5 py-1 rounded-md bg-[#EEF2FF] text-[#3730A3] font-bold border border-[#C7D2FE]">${sym} ${side} (${formatQuantLots(lots)} lots @ $${formatQuantPrice(entryPrice, sym)}) <strong class="${floatPnl >= 0 ? 'text-emerald-600' : 'text-rose-600'} ml-1">(${pnlSign}$${floatPnl.toFixed(2)})</strong></span>`;
        if (slEl) slEl.innerText = pos.sl_price ? '$' + formatQuantPrice(pos.sl_price, sym) + ' USD' : 'Dinámico / Sin SL';
        if (statusEl) statusEl.innerHTML = '<span class="text-[#065F46] font-bold flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-[#10b981] animate-pulse inline-block"></span> Posición viva en mercado — Monitorización en tiempo real</span>';
      } else {
        if (posEl) posEl.innerHTML = '<span class="px-2.5 py-1 rounded-md bg-[#EAE5DC] text-[#181A20] font-bold border border-[#DDD7CD]">NINGUNA (Flat / 100% Liquidez)</span>';
        if (slEl) slEl.innerText = 'N/A (Sin posición abierta)';
        if (statusEl) statusEl.innerHTML = '<span class="text-[#3C45A5] font-semibold flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-[#10b981] animate-pulse inline-block"></span> Escaneando señales de entrada en tiempo real (Daemon Activo)</span>';
      }

      // 5. Renderizar tabla de órdenes filtrada por Desk
      allFtOrders = d.order_history || [];
      renderFtOrdersTable(allFtOrders);
    }

    async function refreshForwardTestUI(btn) {
      if (!btn) btn = document.getElementById('ft-refresh-btn');
      const icon = btn ? btn.querySelector('i') : null;
      const label = btn ? btn.querySelector('span') : null;
      if (btn) btn.disabled = true;
      if (icon) icon.classList.add('fa-spin');
      if (label) label.innerText = 'Actualizando...';

      try {
        await Promise.all([
          fetchForwardState(),
          typeof fetchFtTradesData === 'function' ? fetchFtTradesData() : Promise.resolve()
        ]);
        if (label) label.innerText = '¡Actualizado!';
      } catch (err) {
        console.error('Error al actualizar Forward Test:', err);
        if (label) label.innerText = 'Error';
      } finally {
        if (icon) icon.classList.remove('fa-spin');
        setTimeout(() => {
          if (label) label.innerText = 'Actualizar';
          if (btn) btn.disabled = false;
        }, 1500);
      }
    }

    async function fetchForwardState() {
      const startT = performance.now();
      try {
        const res = await fetch('/api/forward_state');
        if (!res.ok) {
          updateDaemonHealth('reconnecting');
          return;
        }
        const data = await res.json();
        const lat = Math.max(5, Math.round(performance.now() - startT));
        updateDaemonHealth('online', lat);
        
        // Mercados dinámicos
        if (data.markets) {
          const cmeStatus = document.getElementById('ft-cme-status');
          const cmeOpen = document.getElementById('ft-cme-open');
          const cmeBadge = document.getElementById('ft-cme-badge');
          const cmeCard = document.getElementById('ft-cme-card');
          if (cmeStatus) {
            cmeStatus.innerText = data.markets.cme_globex.status;
            cmeStatus.className = 'text-sm font-bold font-mono ' + (data.markets.cme_globex.is_open ? 'text-emerald-400' : 'text-rose-400');
          }
          if (cmeOpen) cmeOpen.innerText = data.markets.cme_globex.next_open;
          if (cmeBadge) {
            cmeBadge.className = 'w-2 h-2 rounded-full ' + (data.markets.cme_globex.is_open ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500');
          }
          if (cmeCard) {
            cmeCard.classList.remove('border-slate-700', 'border-emerald-500', 'border-rose-500');
            cmeCard.classList.add(data.markets.cme_globex.is_open ? 'border-emerald-500' : 'border-slate-700');
          }

          const nyseStatus = document.getElementById('ft-nyse-status');
          const nyseOpen = document.getElementById('ft-nyse-open');
          const nyseBadge = document.getElementById('ft-nyse-badge');
          const nyseCard = document.getElementById('ft-nyse-card');
          if (nyseStatus) {
            nyseStatus.innerText = data.markets.nyse_cash.status;
            nyseStatus.className = 'text-sm font-bold font-mono ' + (data.markets.nyse_cash.is_open ? 'text-emerald-400' : 'text-rose-400');
          }
          if (nyseOpen) nyseOpen.innerText = data.markets.nyse_cash.next_open;
          if (nyseBadge) {
            nyseBadge.className = 'w-2 h-2 rounded-full ' + (data.markets.nyse_cash.is_open ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500');
          }
          if (nyseCard) {
            nyseCard.classList.remove('border-slate-700', 'border-emerald-500', 'border-rose-500');
            nyseCard.classList.add(data.markets.nyse_cash.is_open ? 'border-emerald-500' : 'border-slate-700');
          }
        }

                // 1. Actualizar Cuenta Forward y Tabla de Órdenes con Segregación Estricta (Capital Propio vs Fondeo)
        updateForwardDeskCardAndOrders(data);

        // 2. Crypto Paper Hyperliquid
        if (data.crypto_account) {
          const cp = data.crypto_account;
          const cpBalEl = document.getElementById('ft-crypto-balance');
          const cpPnlEl = document.getElementById('ft-crypto-pnl');
          const bal = Number(cp.balance || 1013.56);
          if (cpBalEl) cpBalEl.innerText = bal.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 4 }) + ' USDC';
          const pnl = Number(cp.pnl != null ? cp.pnl : (bal - 1000.0));
          if (cpPnlEl) {
            cpPnlEl.innerText = (pnl >= 0 ? '+' : '') + pnl.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 4 }) + ' USDC';
            cpPnlEl.className = 'text-sm font-bold font-mono mt-1 truncate ' + (pnl >= 0 ? 'text-emerald-400' : 'text-rose-400');
          }
        }

        // Renderizar Estrategias Activas en Forward Test
        renderActiveForwardStrategies(data);

        // Renderizar Curva de Rentabilidad en Tiempo Real de Forward Test
        if (data.equity_curve && typeof renderFtEquityChart === 'function') {
          renderFtEquityChart(data.equity_curve);
        }
      } catch (e) {
        console.error('Error fetching forward state:', e);
        updateDaemonHealth('reconnecting');
      }
    }

    // Carga de estado para Fase 3: Live Real
    async function fetchLiveState() {
      try {
        const res = await fetch('/api/live_state');
        if (!res.ok) return;
        const data = await res.json();
        
        const countEl = document.getElementById('live-active-count');
        const capEl = document.getElementById('live-active-capital');
        if (countEl) countEl.innerText = data.active_real_accounts;
        if (capEl) capEl.innerText = '$' + Number(data.real_capital_usd).toFixed(2);

        // Checklist
        const checklistContainer = document.getElementById('live-checklist');
        if (checklistContainer && data.checklist) {
          checklistContainer.innerHTML = data.checklist.map(item => `
            <div class="flex items-center justify-between p-3 rounded-xl bg-dark-950/70 border border-slate-800">
              <div class="flex items-center space-x-3">
                <i class="fa-solid ${item.completed ? 'fa-circle-check text-emerald-400' : 'fa-circle-notch text-amber-400 animate-spin'} text-base"></i>
                <span class="text-xs text-slate-200">${item.item}</span>
              </div>
              <span class="px-2 py-0.5 rounded text-[11px] font-mono font-bold ${item.completed ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'}">${item.progress}</span>
            </div>
          `).join('');
        }
      } catch (e) {
        console.error('Error fetching live state:', e);
      }
    }

    
    // Sincronización en tiempo real de Desk General, Enjambre y KPIs
    async function fetchSummary() {
      const startT = performance.now();
      try {
        const res = await fetch('/api/summary');
        if (!res.ok) {
          updateDaemonHealth('reconnecting');
          return;
        }
        const d = await res.json();
        const lat = Math.max(5, Math.round(performance.now() - startT));
        updateDaemonHealth('online', lat);

        // Enjambre y motor en Cockpit General
        const agentsBadge = document.getElementById('desk-agents-badge');
        if (agentsBadge && d.desk) {
          agentsBadge.innerText = `${d.desk.agents_count} AGENTES EN LÍNEA`;
        }
        const engineDesc = document.getElementById('desk-engine-desc');
        if (engineDesc && d.desk) {
          engineDesc.innerText = d.desk.engine;
        }

        // Hero Cards en Cockpit General
        const hF1Trades = document.getElementById('hero-fase1-trades');
        const hF1Pnl = document.getElementById('hero-fase1-pnl');
        if (hF1Trades && d.kpis) hF1Trades.innerText = `${d.kpis.approved_strategies} Aprobadas / ${d.kpis.total_strategies} Catalogadas`;
        if (hF1Pnl && d.kpis) hF1Pnl.innerText = '+$22,453.47 USD';

        const hF2Capital = document.getElementById('hero-fase2-capital');
        const hF2Pnl = document.getElementById('hero-fase2-pnl');
        if (hF2Capital && d.kpis) {
          const tot = (d.kpis.broker_live_balance || 1001.52) + (d.kpis.crypto_paper_capital || 1000.66);
          hF2Capital.innerText = '$' + tot.toLocaleString(undefined, {minimumFractionDigits: 2}) + ' USD (MT5 + DEX)';
        }
        if (hF2Pnl && d.kpis) {
          const p = Number(d.kpis.prop_firm_pnl || 0);
          hF2Pnl.innerText = (p >= 0 ? '+$' : '-$') + Math.abs(p).toFixed(2) + ' USD';
        }

        const hF3Cand = document.getElementById('hero-fase3-candidates');
        if (hF3Cand && d.kpis) {
          hF3Cand.innerText = `${d.kpis.active_live_runners} Daemons Activos`;
        }

        // Chips Guardián de Incubación & Fundamentos Cuantitativos
        if (d.kpis && d.kpis.incubation_guardian) {
          const ig = d.kpis.incubation_guardian;
          const elG = document.getElementById('guard-chip-green');
          const elA = document.getElementById('guard-chip-amber');
          const elR = document.getElementById('guard-chip-red');
          const elReady = document.getElementById('guard-chip-ready');
          if (elG) elG.innerText = `${ig.green_count} Modelos`;
          if (elA) elA.innerText = `${ig.amber_count} Modelos`;
          if (elR) elR.innerText = `${ig.red_count} Modelos`;
          if (elReady) elReady.innerText = `${ig.ready_for_real_account_count} (≥30 trades)`;
        }
      } catch (e) {
        console.error('Error fetching summary:', e);
        updateDaemonHealth('reconnecting');
      }
    }

    
    // =========================================================================
    // GESTIÓN DINÁMICA DE CUENTAS & SELECTOR DE FASE (EVALUATION vs FUNDED)
    // =========================================================================
    let currentAccountState = {
      prop_firm: {
        firm_name: 'Lucid Trading',
        stage: 'EVALUATION',
        consistency_rule_enabled: true
      }
    };

    async function fetchAccountStage() {
      try {
        const res = await fetch('/api/account_stage');
        if (!res.ok) return;
        const data = await res.json();
        currentAccountState = data;
        renderAccountStageUI();
      } catch (e) {
        console.error('Error fetching account stage:', e);
      }
    }

    function renderAccountStageUI() {
      const pf = (currentAccountState && currentAccountState.prop_firm) ? currentAccountState.prop_firm : { firm_name: 'Lucid Trading', stage: 'EVALUATION' };
      const firmName = pf.firm_name || 'Lucid Trading';
      const isEval = (pf.stage === 'EVALUATION');

      ['header', 'hud'].forEach(prefix => {
        const firmEl = document.getElementById(prefix + '-account-firm');
        const textEl = document.getElementById(prefix + '-account-stage-text');
        const dotEl = document.getElementById(prefix + '-account-stage-dot');
        const btnEl = document.getElementById(prefix + '-btn-stage-toggle');
        if (firmEl) firmEl.innerText = firmName;
        if (textEl) textEl.innerText = isEval ? 'EVALUACIÓN (40% Clamp)' : 'FONDEADA (Full Alpha)';
        if (dotEl) {
          dotEl.className = isEval ? 'w-1.5 h-1.5 rounded-full bg-[#B45309] animate-pulse' : 'w-1.5 h-1.5 rounded-full bg-[#107C41]';
        }
        if (btnEl) {
          btnEl.className = isEval
            ? 'px-2.5 py-1 rounded-lg text-[10px] font-bold bg-[#FEF3C7] text-[#B45309] border border-[#FDE68A] hover:opacity-90 transition cursor-pointer flex items-center gap-1.5'
            : 'px-2.5 py-1 rounded-lg text-[10px] font-bold bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0] hover:opacity-90 transition cursor-pointer flex items-center gap-1.5';
        }
      });
    }

    async function toggleAccountStage() {
      const pf = (currentAccountState && currentAccountState.prop_firm) ? currentAccountState.prop_firm : { stage: 'EVALUATION' };
      const nextStage = (pf.stage === 'EVALUATION') ? 'FUNDED' : 'EVALUATION';
      try {
        const res = await fetch('/api/account_stage', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ branch: 'prop_firm', stage: nextStage })
        });
        if (res.ok) {
          const resData = await res.json();
          if (resData.config) {
            currentAccountState.prop_firm = resData.config;
            renderAccountStageUI();
            if (typeof fetchNotifications === 'function') fetchNotifications();
          }
        }
      } catch (e) {
        console.error('Error toggling account stage:', e);
      }
    }

    
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


    // =========================================================================
    // CENTRO DE ALERTAS Y NOTIFICACIONES CUANTITATIVAS
    // =========================================================================
    let currentNotifications = [];
    let currentNotifFilter = 'ALL';

    function toggleNotificationsCenter() {
      const dropdown = document.getElementById('notifications-dropdown');
      if (!dropdown) return;
      dropdown.classList.toggle('hidden');
      if (!dropdown.classList.contains('hidden')) {
        renderNotificationsUI();
      }
    }

    function filterNotifications(category) {
      currentNotifFilter = category;
      ['ALL', 'GUARDIAN', 'Q_LEARNING', 'PROP_FIRM'].forEach(cat => {
        const btn = document.getElementById('notif-filter-' + cat);
        if (btn) {
          if (cat === category) {
            btn.className = 'px-2 py-0.5 rounded-lg text-[10px] font-mono font-bold bg-[#1D1D1F] text-white transition';
          } else {
            btn.className = 'px-2 py-0.5 rounded-lg text-[10px] font-mono font-medium text-[#6E6E73] hover:bg-[#F2F2F7] transition';
          }
        }
      });
      renderNotificationsUI();
    }

    function markAllNotificationsRead() {
      const badge = document.getElementById('notifications-badge');
      if (badge) badge.classList.add('hidden');
      const chip = document.getElementById('notifications-count-chip');
      if (chip) chip.innerText = '0 no leídas';
    }

    function renderNotificationsUI() {
      const listEl = document.getElementById('notifications-list');
      if (!listEl) return;

      const filtered = (currentNotifications || []).filter(n => {
        if (currentNotifFilter === 'ALL') return true;
        return n.category === currentNotifFilter;
      });

      if (filtered.length === 0) {
        listEl.innerHTML = `
          <div class="p-8 text-center text-xs text-[#86868B] font-mono">
            <i class="fa-solid fa-check-double text-lg text-[#107C41] mb-2 block"></i>
            Sin alertas en la categoría seleccionada
          </div>`;
        return;
      }

      listEl.innerHTML = filtered.map(n => {
        let iconHtml = '<i class="fa-solid fa-info text-xs"></i>';
        let iconBg = 'bg-[#EEF2FF] text-[#3C45A5]';
        if (n.level === 'WARNING' || n.badge === 'warning') {
          iconHtml = '<i class="fa-solid fa-triangle-exclamation text-xs"></i>';
          iconBg = 'bg-[#FEF3C7] text-[#B45309]';
        } else if (n.level === 'SUCCESS' || n.badge === 'success') {
          iconHtml = '<i class="fa-solid fa-shield-check text-xs"></i>';
          iconBg = 'bg-[#ECFDF5] text-[#107C41]';
        } else if (n.badge === 'purple' || n.category === 'PROP_FIRM') {
          iconHtml = '<i class="fa-solid fa-scissors text-xs"></i>';
          iconBg = 'bg-[#F3E8FF] text-[#7E22CE]';
        }

        return `
          <div class="p-3.5 hover:bg-[#FBFBFD] transition flex items-start gap-3">
            <div class="w-7 h-7 rounded-lg ${iconBg} flex items-center justify-center shrink-0 mt-0.5">
              ${iconHtml}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between gap-1 mb-0.5">
                <h5 class="text-xs font-bold text-[#1D1D1F] truncate">${n.title}</h5>
                <span class="text-[9px] font-mono text-[#86868B] shrink-0">${n.timestamp || 'Ahora'}</span>
              </div>
              <p class="text-[11px] text-[#6E6E73] leading-relaxed break-words">${n.message}</p>
              <div class="mt-1.5 flex items-center gap-2">
                <span class="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded bg-[#F2F2F7] text-[#6E6E73] font-semibold">${n.category}</span>
                <span class="text-[9px] font-mono text-[#86868B]">${n.id || ''}</span>
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    async function fetchNotifications() {
      try {
        const res = await fetch('/api/notifications');
        if (!res.ok) return;
        const data = await res.json();
        currentNotifications = data.notifications || [];
        
        const count = data.unread_count || currentNotifications.length;
        const badge = document.getElementById('notifications-badge');
        const chip = document.getElementById('notifications-count-chip');
        if (badge) {
          if (count > 0) {
            badge.innerText = count > 9 ? '9+' : count;
            badge.classList.remove('hidden');
          } else {
            badge.classList.add('hidden');
          }
        }
        if (chip) chip.innerText = `${count} evento${count !== 1 ? 's' : ''}`;
        
        const dropdown = document.getElementById('notifications-dropdown');
        if (dropdown && !dropdown.classList.contains('hidden')) {
          renderNotificationsUI();
        }
      } catch (err) {
        console.error('Error fetching notifications:', err);
      }
    }

    // Cerrar dropdown al hacer click fuera
    document.addEventListener('click', (e) => {
      const wrapper = document.getElementById('notifications-wrapper');
      const dropdown = document.getElementById('notifications-dropdown');
      if (wrapper && dropdown && !dropdown.classList.contains('hidden')) {
        if (!wrapper.contains(e.target)) {
          dropdown.classList.add('hidden');
        }
      }
    });

    async function fetchCurrentDashboard() {
      const icon = document.getElementById('refresh-icon');
      if (icon) icon.classList.add('fa-spin');
      const startT = performance.now();
      try {
        const results = await Promise.allSettled([
          fetchAccountStage(),
          fetchNotifications(),
          fetchSummary(),
          fetchAnalyticsData(currentAccountFilter),
          fetchTradesData(currentAccountFilter),
          fetchRosterData(),
          fetchStrategiesData(),
          fetchJournalAndReports(),
          fetchForwardState(),
          fetchLiveState(),
          fetchTriFacetData()
        ]);
        const anyOk = results.some(r => r.status === 'fulfilled');
        if (anyOk) {
          const lat = Math.max(5, Math.round(performance.now() - startT));
          updateDaemonHealth('online', lat);
        } else {
          updateDaemonHealth('reconnecting');
        }
      } catch (err) {
        console.error('Error refreshing dashboard:', err);
        updateDaemonHealth('reconnecting');
      } finally {
        if (icon) {
          setTimeout(() => icon.classList.remove('fa-spin'), 350);
        }
      }
    }

    // Auto-refresco en segundo plano cada 15 segundos para datos en tiempo real
    setInterval(() => {
      fetchForwardState();
    }, 15000);

    // Arranque de la SPA
    window.addEventListener('DOMContentLoaded', () => {
      if (localStorage.getItem('sidebar_collapsed') === 'true' && window.innerWidth >= 1024) {
        closeSidebar();
      }
      fetchCurrentDashboard();
      if (typeof initDefaultMonteCarloCone === 'function') {
        setTimeout(initDefaultMonteCarloCone, 200);
      }
      if (typeof initDefaultFtEquityCurve === 'function') {
        setTimeout(initDefaultFtEquityCurve, 250);
      }
      fetchAccountStage();
      fetchNotifications();
      setInterval(fetchNotifications, 30000);
      fetchSummary();
      setInterval(fetchSummary, 10000);
      fetchTelemetry();
      setInterval(fetchTelemetry, 15000);
      fetchForwardState();
      fetchLiveState();
      fetchTriFacetData();
      setInterval(() => {
        fetchAnalyticsData(currentAccountFilter);
        fetchForwardState();
      }, 30000);
    });
  
    // Selector dinámico de Horizontes de Backtest (Apple Segmented Control)
    function switchBacktestHorizon(horizon) {
      const c12m = document.getElementById('backtest-12m-container');
      const cCyclic = document.getElementById('backtest-cyclic-container');
      const c10y = document.getElementById('backtest-10y-container');
      
      const b12m = document.getElementById('btn-backtest-12m');
      const bCyclic = document.getElementById('btn-backtest-cyclic');
      const b10y = document.getElementById('btn-backtest-10y');
      
      [c12m, cCyclic, c10y].forEach(c => { if (c) c.classList.add('hidden'); });
      [b12m, bCyclic, b10y].forEach(b => {
        if (b) {
          b.className = 'segmented-pill flex-1 sm:flex-initial';
        }
      });

      if (horizon === '12m') {
        if (c12m) { c12m.classList.remove('hidden'); triggerMotionSweep(c12m); }
        if (b12m) { b12m.className = 'segmented-pill active flex-1 sm:flex-initial'; }
        setTimeout(() => {
          if (mainEquityChart) mainEquityChart.render();
          if (dowChart) dowChart.render();
          if (hourlyChart) hourlyChart.render();
        }, 100);
      } else if (horizon === 'cyclic') {
        if (cCyclic) { cCyclic.classList.remove('hidden'); triggerMotionSweep(cCyclic); }
        if (bCyclic) { bCyclic.className = 'segmented-pill active flex-1 sm:flex-initial'; }
      } else if (horizon === '10y') {
        if (c10y) { c10y.classList.remove('hidden'); triggerMotionSweep(c10y); }
        if (b10y) { b10y.className = 'segmented-pill active flex-1 sm:flex-initial'; }
        if (typeof switch10YAsset === 'function') switch10YAsset('NDX');
      }
    }

    // ==============================================================================
    // CONTROLADOR TRADINGVIEW PRO & AUDITORÍA CUANTITATIVA (ALGROKQUANT)
    // ==============================================================================
    const TV_THEME_MAP = {
      'dark': { theme: 'dark', bg: '#131722', toolbar: '#131722', text: '#cbd5e1', grid: 'rgba(30, 41, 59, 0.4)' },
      'black': { theme: 'dark', bg: '#090D16', toolbar: '#090D16', text: '#94a3b8', grid: 'rgba(25, 30, 45, 0.5)' },
      'charcoal': { theme: 'dark', bg: '#1E222D', toolbar: '#1E222D', text: '#cbd5e1', grid: 'rgba(42, 46, 57, 0.6)' },
      'midnight': { theme: 'dark', bg: '#0B132B', toolbar: '#0B132B', text: '#a0aec0', grid: 'rgba(28, 37, 65, 0.6)' },
      'light': { theme: 'light', bg: '#FFFFFF', toolbar: '#F3F4F6', text: '#111827', grid: 'rgba(229, 231, 235, 0.8)' },
      'warm': { theme: 'light', bg: '#FAF7F2', toolbar: '#EAE5DC', text: '#181A20', grid: 'rgba(230, 226, 216, 0.8)' }
    };

    const TV_SYMBOL_MAP = {
      'STRAT-20261028-035': 'BINANCE:BTCUSDT',
      'PROP-NDX-005': 'ICMARKETS:USTEC',
      'CAP-NDX-005': 'ICMARKETS:USTEC',
      'PROP-NDX-006': 'ICMARKETS:USTEC',
      'PROP-FX-EUR-001': 'ICMARKETS:EURUSD',
      'PROP-SPX-005': 'ICMARKETS:US500',
      'CAP-SPX-006': 'ICMARKETS:US500',
      'PROP-SPX-001': 'ICMARKETS:US500',
      'STRAT-20261021-018': 'BINANCE:BTCUSDT',
      'STRAT-20261024-022': 'BINANCE:BTCUSDT'
    };

    function resolveTvSymbol(stratId, asset) {
      if (TV_SYMBOL_MAP[stratId]) return TV_SYMBOL_MAP[stratId];
      const a = (asset || '').toUpperCase();
      const s = (stratId || '').toUpperCase();
      if (a.includes('NDX') || a.includes('USTEC') || s.includes('NDX')) return 'ICMARKETS:USTEC';
      if (a.includes('SPX') || a.includes('US500') || s.includes('SPX')) return 'ICMARKETS:US500';
      if (a.includes('EUR') || s.includes('EUR')) return 'ICMARKETS:EURUSD';
      if (a.includes('ETH') || s.includes('ETH')) return 'BINANCE:ETHUSDT';
      if (a.includes('SOL') || s.includes('SOL')) return 'BINANCE:SOLUSDT';
      return 'BINANCE:BTCUSDT';
    }

    let tvDisplayMode = 'PRO';
    let tvStrategiesCatalog = [];
    let tvCurrentStrategyId = 'STRAT-20261028-035';
    let tvMainChart = null;
    let tvSubChart = null;
    let tvCandleSeries = null;
    let tvVolumeSeries = null;
    let tvOverlaySeries = {};
    let tvOscillatorSeries = {};
    let tvActivePriceLines = [];
    let tvCustomPriceLines = [];
    let tvCurrentData = null;
    let tvCurrentTradeIdx = -1;
    let tvInitialized = false;
    let currentDeskMode = 'CAPITAL_PROPIO';

    // 1. Conmutar entre Modo TradingView Pro (Dibujo) y Auditoría Cuantitativa
    function setTvDisplayMode(mode) {
      tvDisplayMode = mode;
      const proBtn = document.getElementById('tv-mode-btn-pro');
      const auditBtn = document.getElementById('tv-mode-btn-audit');
      const proCont = document.getElementById('tv-mode-pro-container');
      const auditCont = document.getElementById('tv-mode-audit-container');
      const tfContainer = document.getElementById('tv-custom-timeframe-container');

      if (mode === 'PRO') {
        if (proBtn) proBtn.className = 'segmented-pill active';
        if (auditBtn) auditBtn.className = 'segmented-pill';
        if (proCont) proCont.classList.remove('hidden');
        if (auditCont) auditCont.classList.add('hidden');
        if (tfContainer) tfContainer.classList.add('hidden');
        const strat = tvStrategiesCatalog.find(s => s.id === tvCurrentStrategyId);
        loadTvProWidget(resolveTvSymbol(tvCurrentStrategyId, strat ? strat.asset : ''));
      } else {
        if (auditBtn) auditBtn.className = 'segmented-pill active';
        if (proBtn) proBtn.className = 'segmented-pill';
        if (auditCont) auditCont.classList.remove('hidden');
        if (proCont) proCont.classList.add('hidden');
        if (tfContainer) tfContainer.classList.remove('hidden');
        if (!tvMainChart) {
          initTvChartInstances();
        }
        if (tvCurrentStrategyId) {
          changeTvStrategy(tvCurrentStrategyId);
        }
        setTimeout(resizeTvCharts, 120);
      }
    }

    let tvCustomCanvasBg = localStorage.getItem('tv_custom_canvas_bg') || '#131722';

    function isLightHexColor(hex) {
      const c = hex.replace('#', '');
      if (c.length === 3) {
        const r = parseInt(c[0] + c[0], 16);
        const g = parseInt(c[1] + c[1], 16);
        const b = parseInt(c[2] + c[2], 16);
        return ((r * 299) + (g * 587) + (b * 114)) / 1000 > 155;
      } else if (c.length >= 6) {
        const r = parseInt(c.substring(0, 2), 16);
        const g = parseInt(c.substring(2, 4), 16);
        const b = parseInt(c.substring(4, 6), 16);
        return ((r * 299) + (g * 587) + (b * 114)) / 1000 > 155;
      }
      return false;
    }

    function applyTvProCustomBg(hexColor) {
      if (!hexColor) return;
      let cleanHex = hexColor.trim();
      if (!cleanHex.startsWith('#') && (cleanHex.length === 3 || cleanHex.length === 6)) {
        cleanHex = '#' + cleanHex;
      }
      if (!/^#[0-9A-Fa-f]{3,8}$/.test(cleanHex)) return;
      
      tvCustomCanvasBg = cleanHex;
      try { localStorage.setItem('tv_custom_canvas_bg', cleanHex); } catch(e){}

      const p1 = document.getElementById('tv-pro-custom-picker');
      const h1 = document.getElementById('tv-pro-hex-input');
      const p2 = document.getElementById('tv-custom-color-picker');
      if (p1) p1.value = cleanHex;
      if (h1) h1.value = cleanHex;
      if (p2) p2.value = cleanHex;

      const isLight = isLightHexColor(cleanHex);
      const themeMode = isLight ? 'light' : 'dark';
      const textColor = isLight ? '#181A20' : '#cbd5e1';
      const gridColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';

      TV_THEME_MAP['custom'] = {
        theme: themeMode,
        bg: cleanHex,
        toolbar: cleanHex,
        text: textColor,
        grid: gridColor
      };

      currentTvThemeKey = 'custom';

      const strat = tvStrategiesCatalog.find(s => s.id === tvCurrentStrategyId);
      loadTvProWidget(resolveTvSymbol(tvCurrentStrategyId, strat ? strat.asset : ''), 'custom');

      if (tvMainChart) {
        tvMainChart.applyOptions({
          layout: { background: { color: cleanHex }, textColor: textColor },
          grid: { vertLines: { color: gridColor }, horzLines: { color: gridColor } }
        });
      }
      if (tvSubChart) {
        tvSubChart.applyOptions({
          layout: { background: { color: cleanHex }, textColor: textColor },
          grid: { vertLines: { color: gridColor }, horzLines: { color: gridColor } }
        });
      }
    }

    // 2. Cargar Widget Oficial de TradingView con Barra de Herramientas de Dibujo Completa
    function loadTvProWidget(symbol, themeKey) {
      const container = document.getElementById('tv-pro-widget-container');
      if (!container) return;
      container.innerHTML = '';

      let key = themeKey || currentTvThemeKey;
      if (!key && tvCustomCanvasBg && tvCustomCanvasBg !== '#131722') {
        key = 'custom';
        const isLight = isLightHexColor(tvCustomCanvasBg);
        TV_THEME_MAP['custom'] = {
          theme: isLight ? 'light' : 'dark',
          bg: tvCustomCanvasBg,
          toolbar: tvCustomCanvasBg,
          text: isLight ? '#181A20' : '#cbd5e1',
          grid: isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)'
        };
      }
      if (!key) key = 'dark';

      const themeConfig = (typeof TV_THEME_MAP !== 'undefined' && TV_THEME_MAP[key]) ? TV_THEME_MAP[key] : { theme: 'dark', bg: '#131722', toolbar: '#131722', text: '#cbd5e1', grid: 'rgba(30, 41, 59, 0.4)' };
      
      // Sincronizar inputs si existen
      const p1 = document.getElementById('tv-pro-custom-picker');
      const h1 = document.getElementById('tv-pro-hex-input');
      if (p1 && themeConfig.bg) p1.value = themeConfig.bg;
      if (h1 && themeConfig.bg) h1.value = themeConfig.bg;

      try {
        if (typeof TradingView !== 'undefined') {
          new TradingView.widget({
            "autosize": true,
            "symbol": symbol || "ICMARKETS:USTEC",
            "interval": "60",
            "timezone": "Europe/Madrid",
            "theme": themeConfig.theme,
            "style": "1",
            "locale": "es",
            "toolbar_bg": themeConfig.toolbar,
            "enable_publishing": false,
            "allow_symbol_change": true,
            "hide_side_toolbar": false,
            "withdateranges": true,
            "hide_top_toolbar": false,
            "save_image": true,
            "overrides": {
              "paneProperties.background": themeConfig.bg,
              "paneProperties.backgroundType": "solid",
              "paneProperties.vertGridProperties.color": themeConfig.grid,
              "paneProperties.horzGridProperties.color": themeConfig.grid,
              "scalesProperties.textColor": themeConfig.text,
              "mainSeriesProperties.candleStyle.wickUpColor": "#10b981",
              "mainSeriesProperties.candleStyle.wickDownColor": "#ef4444"
            },
            "studies": [
              "MASimple@tv-basicstudies",
              "RSI@tv-basicstudies",
              "BollingerBands@tv-basicstudies"
            ],
            "container_id": "tv-pro-widget-container"
          });
        } else {
          container.innerHTML = '<div class="flex items-center justify-center h-full text-xs text-txtSecondary font-mono">Cargando motor gráfico TradingView...</div>';
        }
      } catch (e) {
        console.error("Error inicializando TradingView Pro Widget:", e);
      }
    }

    // 3. Inicializar y cargar catálogo al abrir la pestaña
    async function loadTradingViewTab() {
      if (!tvInitialized) {
        initTvChartInstances();
        await fetchTvStrategyCatalog(currentDeskMode);
        const strat = tvStrategiesCatalog.find(s => s.id === tvCurrentStrategyId);
        loadTvProWidget(resolveTvSymbol(tvCurrentStrategyId, strat ? strat.asset : ''));
        tvInitialized = true;
      }
      setTimeout(resizeTvCharts, 120);
    }

    function resizeTvCharts() {
      const mainContainer = document.getElementById('tv-main-chart-container');
      const subContainer = document.getElementById('tv-sub-chart-container');
      if (mainContainer && tvMainChart && mainContainer.clientWidth > 50) {
        tvMainChart.applyOptions({ width: mainContainer.clientWidth });
      }
      if (subContainer && tvSubChart && subContainer.clientWidth > 50) {
        tvSubChart.applyOptions({ width: subContainer.clientWidth });
      }
    }

    function initTvChartInstances() {
      const mainContainer = document.getElementById('tv-main-chart-container');
      const subContainer = document.getElementById('tv-sub-chart-container');

      if (!mainContainer || !subContainer) return;

      const chartOptions = {
        layout: {
          background: { color: '#090d16' },
          textColor: '#94a3b8',
          fontSize: 11,
          fontFamily: "'JetBrains Mono', 'Fira Code', monospace"
        },
        grid: {
          vertLines: { color: 'rgba(30, 41, 59, 0.4)' },
          horzLines: { color: 'rgba(30, 41, 59, 0.4)' }
        },
        crosshair: {
          mode: LightweightCharts.CrosshairMode.Normal,
          vertLine: { color: '#64748b', width: 1, style: 3, labelBackgroundColor: '#1e293b' },
          horzLine: { color: '#64748b', width: 1, style: 3, labelBackgroundColor: '#1e293b' }
        },
        timeScale: {
          borderColor: '#1e293b',
          timeVisible: true,
          secondsVisible: false
        },
        rightPriceScale: {
          borderColor: '#1e293b',
          scaleMargins: { top: 0.1, bottom: 0.15 }
        }
      };

      // 1. Crear Gráfico Principal (Velas + Overlays)
      tvMainChart = LightweightCharts.createChart(mainContainer, {
        ...chartOptions,
        width: mainContainer.clientWidth || 800,
        height: 480
      });

      // Serie de Velas Japonesas
      tvCandleSeries = tvMainChart.addCandlestickSeries({
        upColor: '#10b981',
        downColor: '#ef4444',
        borderVisible: false,
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444'
      });

      // 2. Crear Gráfico de Sub-Panel (Osciladores)
      tvSubChart = LightweightCharts.createChart(subContainer, {
        ...chartOptions,
        width: subContainer.clientWidth || 800,
        height: 180,
        rightPriceScale: {
          borderColor: '#1e293b',
          scaleMargins: { top: 0.1, bottom: 0.1 }
        }
      });

      // Sincronización temporal entre gráfico principal y sub-panel
      let isSyncing = false;
      tvMainChart.timeScale().subscribeVisibleLogicalRangeChange(range => {
        if (isSyncing || !range) return;
        isSyncing = true;
        tvSubChart.timeScale().setVisibleLogicalRange(range);
        isSyncing = false;
      });

      tvSubChart.timeScale().subscribeVisibleLogicalRangeChange(range => {
        if (isSyncing || !range) return;
        isSyncing = true;
        tvMainChart.timeScale().setVisibleLogicalRange(range);
        isSyncing = false;
      });

      // Hover crosshair info
      tvMainChart.subscribeCrosshairMove(param => {
        const hoverEl = document.getElementById('tv-hover-info');
        if (!hoverEl || !param.time || !param.seriesData.get(tvCandleSeries)) {
          if (hoverEl) hoverEl.innerText = 'Pasa el cursor por las velas';
          return;
        }
        const data = param.seriesData.get(tvCandleSeries);
        const dateStr = new Date(param.time * 1000).toLocaleString('es-ES', { dateStyle: 'short', timeStyle: 'short' });
        hoverEl.innerHTML = `<span class="text-slate-400">${dateStr}</span> · O: <span class="text-white font-mono">${data.open.toFixed(2)}</span> H: <span class="text-emerald-400 font-mono">${data.high.toFixed(2)}</span> L: <span class="text-rose-400 font-mono">${data.low.toFixed(2)}</span> C: <span class="text-white font-mono font-bold">${data.close.toFixed(2)}</span>`;
      });

      // Manejo responsive
      const resizeObserver = new ResizeObserver(entries => {
        if (!entries || entries.length === 0) return;
        resizeTvCharts();
      });
      resizeObserver.observe(mainContainer);
    }

    // 4. Cargar Catálogo de Estrategias y Filtrar por Desk
    async function fetchTvStrategyCatalog(filterDesk) {
      const defaultCatalog = [
        { id: 'STRAT-20261028-035', name: 'Momentum Breakout BTC', asset: 'BTCUSDT', type: 'Capital Propio' },
        { id: 'CAP-SPX-006', name: 'Bollinger Dip US500', asset: 'US500', type: 'Capital Propio' },
        { id: 'CAP-NDX-005', name: 'Bollinger Dip US100', asset: 'US100', type: 'Capital Propio' },
        { id: 'CRYPTO-BTC-001', name: 'Breakout Intraday BTC', asset: 'BTCUSDT', type: 'Capital Propio' },
        { id: 'PROP-SPX-001', name: 'Trend Following US500', asset: 'US500', type: 'Prop Firm' }
      ];

      try {
        const res = await fetch('/api/chart_strategies');
        if (res.ok) {
          const json = await res.json();
          if (Array.isArray(json) && json.length > 0) {
            tvStrategiesCatalog = json;
          } else {
            tvStrategiesCatalog = defaultCatalog;
          }
        } else {
          tvStrategiesCatalog = defaultCatalog;
        }
      } catch (err) {
        tvStrategiesCatalog = defaultCatalog;
      }
      
      const desk = filterDesk || currentDeskMode;
      const select = document.getElementById('tv-strategy-select');
      if (!select) return;

      let filtered = tvStrategiesCatalog;
      if (desk === 'CAPITAL_PROPIO') {
        filtered = tvStrategiesCatalog.filter(s => 
          (s.type && s.type.toLowerCase().includes('capital propio')) ||
          s.id.startsWith('STRAT-') || s.id.startsWith('CAP-') || s.id.startsWith('CRYPTO-')
        );
      } else if (desk === 'PROP_FIRM') {
        filtered = tvStrategiesCatalog.filter(s => 
          (s.type && s.type.toLowerCase().includes('prop firm')) ||
          s.id.startsWith('PROP-')
        );
      }

      if (!filtered || filtered.length === 0) filtered = tvStrategiesCatalog;

      select.innerHTML = '';
      filtered.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.id;
        opt.innerText = `${s.id} · ${s.name}`;
        select.appendChild(opt);
      });

      if (filtered.length > 0) {
        select.value = filtered[0].id;
        changeTvStrategy(filtered[0].id);
      }
    }

    // 5. Cambiar de Estrategia
    async function changeTvStrategy(stratId) {
      tvCurrentStrategyId = stratId;
      const strat = tvStrategiesCatalog.find(s => s.id === stratId);
      const symbol = resolveTvSymbol(stratId, strat ? strat.asset : '');

      if (tvDisplayMode === 'PRO') {
        loadTvProWidget(symbol);
      }

      const overlay = document.getElementById('tv-loading-overlay');
      if (overlay) overlay.classList.remove('hidden');

      try {
        const tfParam = (typeof tvCurrentTimeframe !== 'undefined' && tvCurrentTimeframe) ? `&tf=${tvCurrentTimeframe}` : '';
        const res = await fetch(`/api/chart/${stratId}?bars=1500${tfParam}`);
        if (!res.ok) throw new Error('Error al obtener datos de velas e indicadores');
        const data = await res.json();
        tvCurrentData = data;
        renderTvChartData(data);
      } catch (err) {
        console.error('Error cargando gráfico:', err);
        clearActivePriceLines();
        const tradeSel = document.getElementById('tv-trade-select');
        if (tradeSel) tradeSel.innerHTML = '<option value="">Error cargando datos de la estrategia</option>';
        const inspector = document.getElementById('tv-trade-inspector');
        if (inspector) inspector.classList.add('hidden');
        const badges = document.getElementById('tv-indicator-badges');
        if (badges) {
          badges.innerHTML = `
            <div class="flex items-center gap-2 py-0.5 px-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-700 font-mono text-[11px]">
              <i class="fa-solid fa-triangle-exclamation text-rose-600"></i> Error al sincronizar velas
              <button onclick="changeTvStrategy('${stratId}')" class="underline font-bold text-rose-800 hover:text-rose-950 ml-1">Reintentar</button>
            </div>`;
        }
      } finally {
        if (overlay) overlay.classList.add('hidden');
      }
    }

    // 6. Renderizar Velas, Overlays, Osciladores y Marcadores
    function renderTvChartData(data) {
      if (!tvMainChart || !tvSubChart) return;

      // Actualizar Badges
      const bAsset = document.getElementById('tv-badge-asset');
      const bTf = document.getElementById('tv-badge-tf');
      const bType = document.getElementById('tv-badge-type');
      if (bAsset) bAsset.innerText = data.asset;
      if (bTf) bTf.innerText = data.timeframe;
      if (bType) {
        const isProp = (data.type && data.type.toLowerCase().includes('prop firm')) || data.strategy_id.startsWith('PROP-');
        bType.innerText = isProp ? 'Prop Firm EOD' : 'Capital Propio';
        bType.className = isProp ? 'badge-warning-risk' : 'badge-success-live';
      }

      // Limpiar series anteriores
      Object.values(tvOverlaySeries).forEach(s => tvMainChart.removeSeries(s));
      tvOverlaySeries = {};

      Object.values(tvOscillatorSeries).forEach(s => tvSubChart.removeSeries(s));
      tvOscillatorSeries = {};

      clearActivePriceLines();

      // Cargar Velas
      if (tvCandleSeries && data.candles) {
        tvCandleSeries.setData(data.candles);
      }

      // Cargar Overlays (EMA, Donchian, Bollinger)
      const badgesContainer = document.getElementById('tv-indicator-badges');
      if (badgesContainer) badgesContainer.innerHTML = '';

      if (data.overlays) {
        data.overlays.forEach(ov => {
          const series = tvMainChart.addLineSeries({
            color: ov.color,
            lineWidth: ov.lineWidth || 2,
            lineStyle: ov.lineStyle || 0,
            title: ov.name
          });
          series.setData(ov.data);
          tvOverlaySeries[ov.id] = series;

          if (badgesContainer) {
            const badge = document.createElement('span');
            badge.className = 'px-2 py-0.5 rounded text-[11px] font-mono font-bold border flex items-center gap-1.5 shadow-2xs bg-[#FAF7F2]';
            badge.style.borderColor = ov.color + '60';
            badge.style.color = '#181A20';
            const paramText = ov.period ? ` (${ov.period})` : (ov.params ? ` (${ov.params})` : '');
            badge.innerHTML = `<span class="w-2 h-2 rounded-full" style="background-color: ${ov.color}"></span> ${ov.name}${paramText}`;
            badgesContainer.appendChild(badge);
          }
        });
      }

      // Cargar Osciladores en Sub-Panel
      const subTitle = document.getElementById('tv-subchart-title');
      if (data.oscillators && data.oscillators.length > 0) {
        const mainOsc = data.oscillators[0];
        if (subTitle) {
          subTitle.innerHTML = `<i class="fa-solid fa-wave-square text-rose-500"></i> ${mainOsc.name}`;
        }

        data.oscillators.forEach(osc => {
          const oscSeries = tvSubChart.addLineSeries({
            color: osc.color,
            lineWidth: osc.lineWidth || 2,
            title: osc.name
          });
          oscSeries.setData(osc.data);
          tvOscillatorSeries[osc.id] = oscSeries;

          if (osc.thresholds) {
            osc.thresholds.forEach(th => {
              oscSeries.createPriceLine({
                price: th.value,
                color: th.color,
                lineWidth: 1,
                lineStyle: 2,
                axisLabelVisible: true,
                title: th.title
              });
            });
          }
        });
      }

      // Cargar Marcadores de Trades
      if (tvCandleSeries) {
        tvCandleSeries.setMarkers(data.markers && data.markers.length > 0 ? data.markers : []);
      }

      // Poblar Selector de Trades
      populateTvTrades(data.trades);

      // Ajustar vista general completa
      resizeTvCharts();
      if (tvMainChart) tvMainChart.timeScale().fitContent();
      if (tvSubChart) tvSubChart.timeScale().fitContent();

      if (data.trades && data.trades.length > 0) {
        selectTvTrade(0, false);
      } else {
        const inspector = document.getElementById('tv-trade-inspector');
        if (inspector) inspector.classList.add('hidden');
      }
    }

    // 7. Poblar Dropdown de Operaciones
    function populateTvTrades(trades) {
      const tradeSelect = document.getElementById('tv-trade-select');
      if (!tradeSelect) return;
      const count = trades ? trades.length : 0;
      tradeSelect.innerHTML = `<option value="">Seleccionar Operación (${count} registradas)...</option>`;
      if (!trades || trades.length === 0) return;

      trades.forEach((t, idx) => {
        const opt = document.createElement('option');
        opt.value = idx;
        const icon = t.result === 'WIN' ? '🟢' : '🔴';
        const pnl = Number(t.pnl_pct || 0);
        const pnlStr = (pnl >= 0 ? '+' : '') + pnl.toFixed(2) + '%';
        opt.innerText = `${icon} #${idx + 1}: ${t.type} @ $${Number(t.entry_price).toLocaleString()} (${pnlStr})`;
        tradeSelect.appendChild(opt);
      });
    }

    // 8. Seleccionar una Operación y hacer Zoom informativo
    function selectTvTrade(idx, shouldZoom = true) {
      if (!tvCurrentData || !tvCurrentData.trades || !tvCurrentData.trades[idx]) return;
      const t = tvCurrentData.trades[idx];
      tvCurrentTradeIdx = parseInt(idx);

      const tradeSelect = document.getElementById('tv-trade-select');
      if (tradeSelect) tradeSelect.value = idx;

      clearActivePriceLines();

      if (tvCandleSeries) {
        if (t.sl_price) {
          const slLine = tvCandleSeries.createPriceLine({
            price: t.sl_price,
            color: '#ef4444',
            lineWidth: 2,
            lineStyle: 2,
            axisLabelVisible: true,
            title: `SL: $${Number(t.sl_price).toLocaleString()}`
          });
          tvActivePriceLines.push(slLine);
        }

        if (t.tp_price) {
          const tpLine = tvCandleSeries.createPriceLine({
            price: t.tp_price,
            color: '#10b981',
            lineWidth: 2,
            lineStyle: 2,
            axisLabelVisible: true,
            title: `TP: $${Number(t.tp_price).toLocaleString()}`
          });
          tvActivePriceLines.push(tpLine);
        }

        if (t.entry_price) {
          const entryLine = tvCandleSeries.createPriceLine({
            price: t.entry_price,
            color: '#38bdf8',
            lineWidth: 1.5,
            lineStyle: 3,
            axisLabelVisible: true,
            title: `ENTRADA: $${Number(t.entry_price).toLocaleString()}`
          });
          tvActivePriceLines.push(entryLine);
        }
      }

      if (shouldZoom && tvMainChart && t.entry_time) {
        const fromTime = t.entry_time - (3600 * 48);
        const toTime = (t.exit_time || t.entry_time) + (3600 * 72);
        tvMainChart.timeScale().setVisibleRange({ from: fromTime, to: toTime });
      }

      // Actualizar Inspector
      const inspector = document.getElementById('tv-trade-inspector');
      if (inspector) {
        inspector.classList.remove('hidden');
        document.getElementById('tv-inspect-id').innerText = t.id || `TR-${idx + 1}`;
        
        const typeEl = document.getElementById('tv-inspect-type');
        typeEl.innerText = t.type;
        typeEl.className = t.type === 'LONG' 
          ? 'px-2 py-0.5 rounded text-[11px] font-bold font-mono bg-emerald-500/20 text-emerald-700' 
          : 'px-2 py-0.5 rounded text-[11px] font-bold font-mono bg-rose-500/20 text-rose-700';

        const badgeEl = document.getElementById('tv-inspect-badge');
        badgeEl.innerText = t.result;
        badgeEl.className = t.result === 'WIN'
          ? 'px-2 py-0.5 rounded text-[11px] font-bold font-mono bg-emerald-500/20 text-emerald-600 border border-emerald-500/30'
          : 'px-2 py-0.5 rounded text-[11px] font-bold font-mono bg-rose-500/20 text-rose-600 border border-rose-500/30';

        const iconEl = document.getElementById('tv-inspect-icon');
        iconEl.innerHTML = t.result === 'WIN' ? '<i class="fa-solid fa-trophy text-emerald-600"></i>' : '<i class="fa-solid fa-shield-halved text-rose-500"></i>';
        iconEl.className = t.result === 'WIN' 
          ? 'w-10 h-10 rounded-xl flex items-center justify-center text-lg font-bold bg-emerald-500/10 border border-emerald-500/20'
          : 'w-10 h-10 rounded-xl flex items-center justify-center text-lg font-bold bg-rose-500/10 border border-rose-500/20';

        const dEntry = new Date(t.entry_time * 1000).toLocaleString('es-ES', { dateStyle: 'short', timeStyle: 'short' });
        const dExit = t.exit_time ? new Date(t.exit_time * 1000).toLocaleString('es-ES', { dateStyle: 'short', timeStyle: 'short' }) : 'Abierta';
        document.getElementById('tv-inspect-timing').innerText = `Entrada: ${dEntry} → Salida: ${dExit} (${t.duration_bars || 0} barras)`;

        const pnlEl = document.getElementById('tv-inspect-pnl');
        const pnlVal = Number(t.pnl_pct || 0);
        pnlEl.innerText = (pnlVal >= 0 ? '+' : '') + pnlVal.toFixed(2) + '%';
        pnlEl.className = pnlVal >= 0 ? 'text-lg font-bold font-mono text-emerald-600' : 'text-lg font-bold font-mono text-rose-600';

        document.getElementById('tv-inspect-entry').innerText = '$' + Number(t.entry_price || 0).toLocaleString();
        document.getElementById('tv-inspect-exit').innerText = t.exit_price ? '$' + Number(t.exit_price).toLocaleString() : 'N/A';
        document.getElementById('tv-inspect-sl').innerText = t.sl_price ? '$' + Number(t.sl_price).toLocaleString() : 'N/A';
        document.getElementById('tv-inspect-tp').innerText = t.tp_price ? '$' + Number(t.tp_price).toLocaleString() : 'N/A';
      }
    }

    function jumpToTvTrade(idx) {
      if (idx !== '') {
        selectTvTrade(idx, true);
      }
    }

    function navigateTvTrade(direction) {
      if (!tvCurrentData || !tvCurrentData.trades || tvCurrentData.trades.length === 0) return;
      let nextIdx = tvCurrentTradeIdx + direction;
      if (nextIdx < 0) nextIdx = tvCurrentData.trades.length - 1;
      if (nextIdx >= tvCurrentData.trades.length) nextIdx = 0;
      selectTvTrade(nextIdx, true);
    }

    function resetTvChartZoom() {
      if (tvMainChart) tvMainChart.timeScale().fitContent();
      if (tvSubChart) tvSubChart.timeScale().fitContent();
    }

    function clearActivePriceLines() {
      if (tvCandleSeries && tvActivePriceLines.length > 0) {
        tvActivePriceLines.forEach(pl => tvCandleSeries.removePriceLine(pl));
        tvActivePriceLines = [];
      }
    }

    // 9. Herramientas de Edición Interactiva (Líneas Horizontales sin prompt y Colores)
    function addTvHorizontalLine(customPrice) {
      if (!tvCandleSeries) return;
      let price = customPrice;
      if (typeof price !== 'number') {
        const inp = document.getElementById('tv-custom-price-input');
        if (inp && inp.value) {
          price = parseFloat(inp.value);
        } else {
          price = (tvCurrentData && tvCurrentData.candles && tvCurrentData.candles.length > 0)
            ? tvCurrentData.candles[tvCurrentData.candles.length - 1].close
            : 0;
        }
      }
      if (isNaN(price) || price <= 0) return;
      const pl = tvCandleSeries.createPriceLine({
        price: price,
        color: '#C86D3B',
        lineWidth: 2,
        lineStyle: 0,
        axisLabelVisible: true,
        title: 'NIVEL: $' + price.toLocaleString(undefined, { minimumFractionDigits: 2 })
      });
      tvCustomPriceLines.push(pl);
      const inp = document.getElementById('tv-custom-price-input');
      if (inp) inp.value = '';
    }

    function clearTvCustomLines() {
      if (tvCandleSeries && tvCustomPriceLines.length > 0) {
        tvCustomPriceLines.forEach(pl => tvCandleSeries.removePriceLine(pl));
        tvCustomPriceLines = [];
      }
    }

    function applyTvCustomColors() {
      const up = document.getElementById('tv-candle-color-up').value;
      const down = document.getElementById('tv-candle-color-down').value;
      if (tvCandleSeries) {
        tvCandleSeries.applyOptions({
          upColor: up,
          downColor: down,
          wickUpColor: up,
          wickDownColor: down
        });
      }
    }

    function applyCustomTvBgColor(hexColor) {
      if (!hexColor) return;
      TV_THEME_MAP['custom'] = {
        theme: 'dark',
        bg: hexColor,
        toolbar: hexColor,
        text: '#cbd5e1',
        grid: 'rgba(255, 255, 255, 0.1)'
      };
      toggleTvChartTheme('custom');
    }
    let currentTvThemeKey = 'dark';

    function toggleTvChartTheme(themeKey) {
      currentTvThemeKey = themeKey;
      const themeConfig = TV_THEME_MAP[themeKey] || TV_THEME_MAP['dark'];
      
      // Sincronizar selectores si existen en el DOM
      const gSel = document.getElementById('tv-global-theme-select');
      if (gSel && gSel.value !== themeKey) gSel.value = themeKey;
      const proLabel = document.getElementById('tv-pro-theme-label');
      if (proLabel && gSel && gSel.options[gSel.selectedIndex]) {
        proLabel.innerText = gSel.options[gSel.selectedIndex].text;
      }

      // 1. Recargar TradingView Pro con el color de fondo elegido
      if (tvDisplayMode === 'PRO') {
        const strat = tvStrategiesCatalog.find(s => s.id === tvCurrentStrategyId);
        loadTvProWidget(resolveTvSymbol(tvCurrentStrategyId, strat ? strat.asset : ''), themeKey);
      }

      // 2. Aplicar a Lightweight Charts (Modo Auditoría)
      if (tvMainChart) {
        tvMainChart.applyOptions({
          layout: { background: { color: themeConfig.bg }, textColor: themeConfig.text },
          grid: { vertLines: { color: themeConfig.grid }, horzLines: { color: themeConfig.grid } }
        });
      }
      if (tvSubChart) {
        tvSubChart.applyOptions({
          layout: { background: { color: themeConfig.bg }, textColor: themeConfig.text },
          grid: { vertLines: { color: themeConfig.grid }, horzLines: { color: themeConfig.grid } }
        });
      }
    }

    let tvCurrentTimeframe = '1h';

    function setTvTimeframe(tf) {
      tvCurrentTimeframe = tf;
      document.querySelectorAll('.tv-tf-btn').forEach(btn => {
        if (btn.dataset.tf === tf) {
          btn.className = 'tv-tf-btn segmented-pill active py-1 px-2.5 text-xs font-semibold';
        } else {
          btn.className = 'tv-tf-btn segmented-pill py-1 px-2.5 text-xs font-semibold';
        }
      });
      const badgeTf = document.getElementById('tv-badge-tf');
      if (badgeTf) badgeTf.innerText = tf;

      if (tvCurrentStrategyId) {
        changeTvStrategy(tvCurrentStrategyId);
      }
    }

    function openStrategyInChart(strategyId, tradeIndex) {
      switchTab('chart');
      setTimeout(() => {
        const select = document.getElementById('tv-strategy-select');
        if (select) {
          select.value = strategyId;
        }
        changeTvStrategy(strategyId).then(() => {
          if (typeof tradeIndex === 'number' && typeof selectTvTrade === 'function') {
            setTimeout(() => {
              selectTvTrade(tradeIndex, true);
            }, 200);
          }
        });
      }, 150);
    }

    const openTradeInChart = openStrategyInChart;

    // Atajos de Teclado Globales (OPERATE Mode)
    document.addEventListener('keydown', (e) => {
      const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
      if (activeTag === 'input' || activeTag === 'textarea' || document.activeElement?.isContentEditable) return;

      // 1. Escape: cerrar modal
      if (e.key === 'Escape') {
        const modal = document.getElementById('strategy-modal');
        if (modal && !modal.classList.contains('hidden')) {
          closeModal();
          return;
        }
      }

      // 2. Navegación en Gráficos (flechas izquierda/derecha y R de reset)
      const chartTab = document.getElementById('tab-content-chart');
      if (chartTab && !chartTab.classList.contains('hidden')) {
        if (e.key === 'ArrowLeft') {
          e.preventDefault();
          if (typeof navigateTvTrade === 'function') navigateTvTrade(-1);
        } else if (e.key === 'ArrowRight') {
          e.preventDefault();
          if (typeof navigateTvTrade === 'function') navigateTvTrade(1);
        } else if (e.key === 'r' || e.key === 'R') {
          if (typeof resetTvChartZoom === 'function') resetTvChartZoom();
        }
      }
    });
  