import re
from pathlib import Path

tmpl_path = Path('/root/AlgrokQuant/dashboard/templates/index.html')
content = tmpl_path.read_text(encoding='utf-8')

# Backup
backup_path = Path('/root/AlgrokQuant/dashboard/templates/index.html.pre_tv')
if not backup_path.exists():
  backup_path.write_text(content, encoding='utf-8')

# 1. Agregar Lightweight Charts CDN en <head> si no está
tv_cdn = """  <!-- TradingView Lightweight Charts CDN Oficial (Canvas 60fps) -->
  <script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
</head>"""

if 'lightweight-charts' not in content:
  content = content.replace('</head>', tv_cdn)

# 2. Agregar botón en la Barra Lateral (Sidebar)
sidebar_marker = '<!-- 7. Catálogo -->'
sidebar_btn = """      <!-- TradingView Charts (Auditoría Técnica) -->
      <button onclick="switchTab('chart')" id="side-tab-chart" class="sidebar-link w-full flex items-center px-3 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800/60 transition group" title="Gráficos TradingView (Auditoría Técnica)">
        <i class="fa-solid fa-chart-line text-emerald-400 text-sm w-6 text-center flex-shrink-0 mr-2.5"></i>
        <span class="sidebar-text flex-1 text-left whitespace-nowrap">Gráficos TradingView</span>
        <span class="px-1.5 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-300 font-bold ml-1">PRO</span>
      </button>

      <!-- 7. Catálogo -->"""

if 'side-tab-chart' not in content:
  content = content.replace(sidebar_marker, sidebar_btn)

# 3. Agregar título en tabTitles
tab_title_marker = "'journal': 'Bitácora & Informes Oficiales'"
tab_title_replacement = """'journal': 'Bitácora & Informes Oficiales',
      'chart': 'Gráficos TradingView · Auditoría de Estrategias e Indicadores'"""

if "'chart':" not in content:
  content = content.replace(tab_title_marker, tab_title_replacement)

# 4. Agregar el contenedor del tab de TradingView antes de </main>
chart_pane_html = """
    <!-- ==================== TAB: TRADINGVIEW CHARTING & AUDIT ==================== -->
    <div id="tab-content-chart" class="tab-pane hidden space-y-6">
      
      <!-- Barra Superior de Control y Filtros -->
      <div class="bg-dark-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          
          <!-- Selector de Estrategia -->
          <div class="flex flex-wrap items-center gap-3">
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <i class="fa-solid fa-robot text-cyan-400"></i> Estrategia:
              </span>
              <select id="tv-strategy-select" onchange="changeTvStrategy(this.value)" class="bg-slate-800 border border-slate-700 text-white rounded-xl px-3 py-2 text-xs font-mono font-semibold focus:outline-none focus:border-cyan-400 cursor-pointer">
                <option value="STRAT-20261028-035">STRAT-20261028-035 (BTC Donchian + Entropía)</option>
              </select>
            </div>

            <!-- Badges Informativos del Activo -->
            <div class="flex items-center gap-2">
              <span id="tv-badge-asset" class="px-2.5 py-1 rounded-lg text-xs font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono">BTC/USDT</span>
              <span id="tv-badge-tf" class="px-2 py-1 rounded-lg text-xs font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20 font-mono">1h</span>
              <span id="tv-badge-type" class="px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Capital Propio</span>
            </div>
          </div>

          <!-- Navegador de Operaciones (Jump to Trade) -->
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
              <i class="fa-solid fa-crosshairs text-rose-400"></i> Operación:
            </span>
            <div class="flex items-center bg-slate-800/80 border border-slate-700 rounded-xl p-1 gap-1">
              <button onclick="navigateTvTrade(-1)" class="px-2 py-1 hover:bg-slate-700 rounded text-slate-300 hover:text-white text-xs transition" title="Operación Anterior">
                <i class="fa-solid fa-chevron-left"></i>
              </button>
              <select id="tv-trade-select" onchange="jumpToTvTrade(this.value)" class="bg-transparent text-white text-xs font-mono font-medium focus:outline-none px-2 py-1 cursor-pointer">
                <option value="">Seleccionar Trade...</option>
              </select>
              <button onclick="navigateTvTrade(1)" class="px-2 py-1 hover:bg-slate-700 rounded text-slate-300 hover:text-white text-xs transition" title="Siguiente Operación">
                <i class="fa-solid fa-chevron-right"></i>
              </button>
            </div>

            <button onclick="resetTvChartZoom()" class="px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white transition flex items-center gap-1.5" title="Restablecer vista a las últimas velas">
              <i class="fa-solid fa-expand text-slate-400"></i> Reset
            </button>
          </div>

        </div>

        <!-- Leyenda Activa de Indicadores Superpuestos -->
        <div id="tv-indicators-legend" class="mt-4 pt-3 border-t border-slate-800 flex flex-wrap items-center gap-3 text-xs">
          <span class="text-slate-400 text-[11px] uppercase font-bold tracking-wider">Indicadores Activos:</span>
          <div id="tv-indicator-badges" class="flex flex-wrap gap-2 items-center">
            <!-- Renderizado dinámicamente -->
          </div>
        </div>
      </div>

      <!-- Contenedor Principal de Gráficos TradingView -->
      <div class="bg-dark-900 border border-slate-800 rounded-2xl p-4 shadow-2xl relative overflow-hidden">
        
        <!-- Estado de Carga -->
        <div id="tv-loading-overlay" class="absolute inset-0 bg-dark-950/80 backdrop-blur-sm z-30 flex flex-col items-center justify-center gap-3">
          <div class="w-8 h-8 border-3 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
          <p class="text-xs font-mono text-cyan-300">Cargando velas OHLCV e indicadores TradingView...</p>
        </div>

        <!-- Gráfico 1: Velas Principales + Overlays (EMA, Donchian, Bollinger, SL/TP) -->
        <div class="relative">
          <div class="flex justify-between items-center mb-2 px-1">
            <span class="text-xs font-mono font-bold text-slate-300 flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> Gráfico de Precios & Overlays (Velas OHLCV)
            </span>
            <span id="tv-hover-info" class="text-xs font-mono text-slate-400">Pasa el cursor por las velas</span>
          </div>
          <div id="tv-main-chart-container" class="w-full h-[480px] bg-dark-950 rounded-xl overflow-hidden border border-slate-800/80"></div>
        </div>

        <!-- Gráfico 2: Sub-Panel Osciladores (Entropía de Shannon / CMF / RSI / Volumen) -->
        <div class="mt-3 pt-3 border-t border-slate-800/80">
          <div class="flex justify-between items-center mb-1.5 px-1">
            <span id="tv-subchart-title" class="text-xs font-mono font-bold text-slate-400 flex items-center gap-1.5">
              <i class="fa-solid fa-wave-square text-rose-400"></i> Sub-Panel de Régimen (Entropía de Shannon & Flujo)
            </span>
            <span class="text-[11px] font-mono text-slate-500">Escala de tiempo sincronizada 1:1 con el precio</span>
          </div>
          <div id="tv-sub-chart-container" class="w-full h-[180px] bg-dark-950 rounded-xl overflow-hidden border border-slate-800/80"></div>
        </div>

      </div>

      <!-- Inspector Detallado de Operación Seleccionada -->
      <div id="tv-trade-inspector" class="bg-dark-900 border border-slate-800 rounded-2xl p-5 shadow-xl hidden">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
          <div class="flex items-center gap-3">
            <div id="tv-inspect-icon" class="w-10 h-10 rounded-xl flex items-center justify-center text-lg font-bold"></div>
            <div>
              <div class="flex items-center gap-2">
                <h4 id="tv-inspect-id" class="text-sm font-bold text-white font-mono">TR-001</h4>
                <span id="tv-inspect-type" class="px-2 py-0.5 rounded text-[11px] font-bold font-mono">LONG</span>
                <span id="tv-inspect-badge" class="px-2 py-0.5 rounded text-[11px] font-bold font-mono">WIN</span>
              </div>
              <p id="tv-inspect-timing" class="text-xs text-slate-400 font-mono mt-0.5"></p>
            </div>
          </div>
          <div class="flex items-center gap-4 text-right">
            <div>
              <p class="text-[11px] text-slate-400 font-mono uppercase">Rentabilidad Neta</p>
              <p id="tv-inspect-pnl" class="text-lg font-bold font-mono">+1.56%</p>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div class="bg-slate-800/50 p-3 rounded-xl border border-slate-800">
            <p class="text-[11px] text-slate-400 font-mono uppercase">Precio Entrada</p>
            <p id="tv-inspect-entry" class="text-sm font-bold text-white font-mono mt-0.5">$65,923.21</p>
          </div>
          <div class="bg-slate-800/50 p-3 rounded-xl border border-slate-800">
            <p class="text-[11px] text-slate-400 font-mono uppercase">Precio Salida</p>
            <p id="tv-inspect-exit" class="text-sm font-bold text-white font-mono mt-0.5">$66,953.61</p>
          </div>
          <div class="bg-slate-800/50 p-3 rounded-xl border border-slate-800">
            <p class="text-[11px] text-rose-400 font-mono uppercase flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span> Stop Loss
            </p>
            <p id="tv-inspect-sl" class="text-sm font-bold text-rose-300 font-mono mt-0.5">$65,408.01</p>
          </div>
          <div class="bg-slate-800/50 p-3 rounded-xl border border-slate-800">
            <p class="text-[11px] text-emerald-400 font-mono uppercase flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Take Profit
            </p>
            <p id="tv-inspect-tp" class="text-sm font-bold text-emerald-300 font-mono mt-0.5">$66,953.61</p>
          </div>
        </div>
      </div>

    </div>
"""

if 'id="tab-content-chart"' not in content:
  content = content.replace('  </main>', chart_pane_html + '\n  </main>')

# 5. Agregar el código JavaScript del controlador de TradingView al final de los scripts
tv_js_code = """
  <!-- ============================================================================== -->
  <!-- CONTROLADOR TRADINGVIEW LIGHTWEIGHT CHARTS (DESK CUANTITATIVO ALGROKQUANT) -->
  <!-- ============================================================================== -->
  <script>
    let tvMainChart = null;
    let tvSubChart = null;
    let tvCandleSeries = null;
    let tvVolumeSeries = null;
    let tvOverlaySeries = {};
    let tvOscillatorSeries = {};
    let tvActivePriceLines = [];
    let tvCurrentData = null;
    let tvCurrentTradeIdx = -1;
    let tvInitialized = false;

    // Inicializar y cargar catálogo al abrir la pestaña
    async function loadTradingViewTab() {
      if (!tvInitialized) {
        initTvChartInstances();
        await fetchTvStrategyCatalog();
        tvInitialized = true;
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

      // 1. Crear Gráfico Principal
      tvMainChart = LightweightCharts.createChart(mainContainer, {
        ...chartOptions,
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
        hoverEl.innerHTML = `<span class="text-slate-400">${dateStr}</span> · O: <span class="text-white">${data.open.toFixed(2)}</span> H: <span class="text-emerald-400">${data.high.toFixed(2)}</span> L: <span class="text-rose-400">${data.low.toFixed(2)}</span> C: <span class="text-white font-bold">${data.close.toFixed(2)}</span>`;
      });

      // Manejo responsive
      const resizeObserver = new ResizeObserver(entries => {
        if (!entries || entries.length === 0) return;
        const { width } = entries[0].contentRect;
        if (tvMainChart) tvMainChart.applyOptions({ width });
        if (tvSubChart) tvSubChart.applyOptions({ width });
      });
      resizeObserver.observe(mainContainer);
    }

    // Cargar Catálogo de Estrategias en el Dropdown
    async function fetchTvStrategyCatalog() {
      try {
        const res = await fetch('/api/chart_strategies');
        if (!res.ok) return;
        const strats = await res.json();
        const select = document.getElementById('tv-strategy-select');
        if (!select) return;

        select.innerHTML = '';
        strats.forEach(s => {
          const opt = document.createElement('option');
          opt.value = s.id;
          opt.innerText = `${s.id} · ${s.name}`;
          select.appendChild(opt);
        });

        if (strats.length > 0) {
          changeTvStrategy(strats[0].id);
        }
      } catch (err) {
        console.error('Error cargando catálogo TradingView:', err);
      }
    }

    // Cambiar de Estrategia
    async function changeTvStrategy(stratId) {
      const overlay = document.getElementById('tv-loading-overlay');
      if (overlay) overlay.classList.remove('hidden');

      try {
        const res = await fetch(`/api/chart/${stratId}?bars=1500`);
        if (!res.ok) throw new Error('Error al obtener datos de velas e indicadores');
        const data = await res.json();
        tvCurrentData = data;
        renderTvChartData(data);
      } catch (err) {
        console.error('Error cargando gráfico:', err);
        alert('No se pudo cargar el gráfico: ' + err.message);
      } finally {
        if (overlay) overlay.classList.add('hidden');
      }
    }

    // Renderizar velas, overlays, osciladores y marcadores
    function renderTvChartData(data) {
      if (!tvMainChart || !tvSubChart) return;

      // 1. Actualizar Badges
      const bAsset = document.getElementById('tv-badge-asset');
      const bTf = document.getElementById('tv-badge-tf');
      const bType = document.getElementById('tv-badge-type');
      if (bAsset) bAsset.innerText = data.asset;
      if (bTf) bTf.innerText = data.timeframe;
      if (bType) {
        bType.innerText = data.type === 'prop_firm' ? 'Prop Firm EOD' : 'Capital Propio';
        bType.className = data.type === 'prop_firm' 
          ? 'px-2.5 py-1 rounded-lg text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20'
          : 'px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
      }

      // 2. Limpiar series anteriores de Overlays
      Object.values(tvOverlaySeries).forEach(s => tvMainChart.removeSeries(s));
      tvOverlaySeries = {};

      // Limpiar series anteriores de Osciladores
      Object.values(tvOscillatorSeries).forEach(s => tvSubChart.removeSeries(s));
      tvOscillatorSeries = {};

      // Limpiar PriceLines
      clearActivePriceLines();

      // 3. Cargar Velas
      tvCandleSeries.setData(data.candles);

      // 4. Cargar Overlays (EMA, Donchian, Bollinger)
      const badgesContainer = document.getElementById('tv-indicator-badges');
      if (badgesContainer) badgesContainer.innerHTML = '';

      data.overlays.forEach(ov => {
        const series = tvMainChart.addLineSeries({
          color: ov.color,
          lineWidth: ov.lineWidth || 2,
          lineStyle: ov.lineStyle || 0,
          title: ov.name
        });
        series.setData(ov.data);
        tvOverlaySeries[ov.id] = series;

        // Añadir badge a la leyenda
        if (badgesContainer) {
          const badge = document.createElement('span');
          badge.className = 'px-2 py-0.5 rounded text-[11px] font-mono font-bold border flex items-center gap-1.5';
          badge.style.borderColor = ov.color + '40';
          badge.style.backgroundColor = ov.color + '15';
          badge.style.color = ov.color;
          badge.innerHTML = `<span class="w-2 h-2 rounded-full" style="background-color: ${ov.color}"></span> ${ov.name}`;
          badgesContainer.appendChild(badge);
        }
      });

      // 5. Cargar Osciladores en Sub-Panel
      const subTitle = document.getElementById('tv-subchart-title');
      if (data.oscillators && data.oscillators.length > 0) {
        const mainOsc = data.oscillators[0];
        if (subTitle) {
          subTitle.innerHTML = `<i class="fa-solid fa-wave-square text-rose-400"></i> ${mainOsc.name}`;
        }

        data.oscillators.forEach(osc => {
          const oscSeries = tvSubChart.addLineSeries({
            color: osc.color,
            lineWidth: osc.lineWidth || 2,
            title: osc.name
          });
          oscSeries.setData(osc.data);
          tvOscillatorSeries[osc.id] = oscSeries;

          // Añadir líneas de umbral si tiene
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

      // 6. Cargar Marcadores de Trades (BUY / SELL / EXIT)
      if (data.markers && data.markers.length > 0) {
        tvCandleSeries.setMarkers(data.markers);
      } else {
        tvCandleSeries.setMarkers([]);
      }

      // 7. Poblar Selector de Trades
      const tradeSelect = document.getElementById('tv-trade-select');
      if (tradeSelect) {
        tradeSelect.innerHTML = '<option value="">Seleccionar Trade...</option>';
        data.trades.forEach((t, idx) => {
          const opt = document.createElement('option');
          opt.value = idx;
          const icon = t.result === 'WIN' ? '🟢' : '🔴';
          opt.innerText = `${icon} ${t.id}: ${t.type} @ $${t.entry_price.toLocaleString()} (${t.pnl_pct > 0 ? '+' : ''}${t.pnl_pct}%)`;
          tradeSelect.appendChild(opt);
        });
      }

      // Ajustar vista general
      tvMainChart.timeScale().fitContent();
      tvSubChart.timeScale().fitContent();

      // Si hay trades, seleccionar el primero para inspección
      if (data.trades && data.trades.length > 0) {
        jumpToTvTrade(0);
      } else {
        const inspector = document.getElementById('tv-trade-inspector');
        if (inspector) inspector.classList.add('hidden');
      }
    }

    // Saltar a una Operación Específica (Dibuja SL, TP y Enfoca la Vela)
    function jumpToTvTrade(idx) {
      if (!tvCurrentData || !tvCurrentData.trades || !tvCurrentData.trades[idx]) return;
      const t = tvCurrentData.trades[idx];
      tvCurrentTradeIdx = parseInt(idx);

      // Actualizar select si fue llamado programáticamente
      const tradeSelect = document.getElementById('tv-trade-select');
      if (tradeSelect) tradeSelect.value = idx;

      // 1. Dibujar líneas de Stop Loss y Take Profit
      clearActivePriceLines();

      if (t.sl_price) {
        const slLine = tvCandleSeries.createPriceLine({
          price: t.sl_price,
          color: '#ef4444',
          lineWidth: 2,
          lineStyle: 2,
          axisLabelVisible: true,
          title: `SL: $${t.sl_price.toLocaleString()}`
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
          title: `TP: $${t.tp_price.toLocaleString()}`
        });
        tvActivePriceLines.push(tpLine);
      }

      // Línea de Entrada
      if (t.entry_price) {
        const entryLine = tvCandleSeries.createPriceLine({
          price: t.entry_price,
          color: '#38bdf8',
          lineWidth: 1.5,
          lineStyle: 3,
          axisLabelVisible: true,
          title: `ENTRADA: $${t.entry_price.toLocaleString()}`
        });
        tvActivePriceLines.push(entryLine);
      }

      // 2. Hacer Zoom alrededor del Trade
      const fromTime = t.entry_time - (3600 * 24); // 24 horas antes
      const toTime = t.exit_time + (3600 * 36);    // 36 horas después
      tvMainChart.timeScale().setVisibleRange({ from: fromTime, to: toTime });

      // 3. Actualizar Tarjeta de Inspección de Trade
      const inspector = document.getElementById('tv-trade-inspector');
      if (inspector) {
        inspector.classList.remove('hidden');
        document.getElementById('tv-inspect-id').innerText = t.id;
        
        const typeEl = document.getElementById('tv-inspect-type');
        typeEl.innerText = t.type;
        typeEl.className = t.type === 'LONG' 
          ? 'px-2 py-0.5 rounded text-[11px] font-bold font-mono bg-emerald-500/20 text-emerald-300' 
          : 'px-2 py-0.5 rounded text-[11px] font-bold font-mono bg-rose-500/20 text-rose-300';

        const badgeEl = document.getElementById('tv-inspect-badge');
        badgeEl.innerText = t.result;
        badgeEl.className = t.result === 'WIN'
          ? 'px-2 py-0.5 rounded text-[11px] font-bold font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
          : 'px-2 py-0.5 rounded text-[11px] font-bold font-mono bg-rose-500/20 text-rose-400 border border-rose-500/30';

        const iconEl = document.getElementById('tv-inspect-icon');
        iconEl.innerHTML = t.result === 'WIN' ? '<i class="fa-solid fa-trophy text-emerald-400"></i>' : '<i class="fa-solid fa-shield-halved text-rose-400"></i>';
        iconEl.className = t.result === 'WIN' 
          ? 'w-10 h-10 rounded-xl flex items-center justify-center text-lg font-bold bg-emerald-500/10 border border-emerald-500/20'
          : 'w-10 h-10 rounded-xl flex items-center justify-center text-lg font-bold bg-rose-500/10 border border-rose-500/20';

        const dEntry = new Date(t.entry_time * 1000).toLocaleString('es-ES', { dateStyle: 'short', timeStyle: 'short' });
        const dExit = new Date(t.exit_time * 1000).toLocaleString('es-ES', { dateStyle: 'short', timeStyle: 'short' });
        document.getElementById('tv-inspect-timing').innerText = `Entrada: ${dEntry} → Salida: ${dExit} (${t.duration_bars} barras)`;

        const pnlEl = document.getElementById('tv-inspect-pnl');
        pnlEl.innerText = (t.pnl_pct > 0 ? '+' : '') + t.pnl_pct.toFixed(2) + '%';
        pnlEl.className = t.pnl_pct > 0 ? 'text-lg font-bold font-mono text-emerald-400' : 'text-lg font-bold font-mono text-rose-400';

        document.getElementById('tv-inspect-entry').innerText = '$' + t.entry_price.toLocaleString();
        document.getElementById('tv-inspect-exit').innerText = '$' + t.exit_price.toLocaleString();
        document.getElementById('tv-inspect-sl').innerText = t.sl_price ? '$' + t.sl_price.toLocaleString() : 'N/A';
        document.getElementById('tv-inspect-tp').innerText = t.tp_price ? '$' + t.tp_price.toLocaleString() : 'N/A';
      }
    }

    // Navegar anterior / siguiente trade
    function navigateTvTrade(direction) {
      if (!tvCurrentData || !tvCurrentData.trades || tvCurrentData.trades.length === 0) return;
      let nextIdx = tvCurrentTradeIdx + direction;
      if (nextIdx < 0) nextIdx = tvCurrentData.trades.length - 1;
      if (nextIdx >= tvCurrentData.trades.length) nextIdx = 0;
      jumpToTvTrade(nextIdx);
    }

    // Restablecer zoom
    function resetTvChartZoom() {
      if (tvMainChart) tvMainChart.timeScale().fitContent();
      if (tvSubChart) tvSubChart.timeScale().fitContent();
      clearActivePriceLines();
    }

    function clearActivePriceLines() {
      if (tvCandleSeries && tvActivePriceLines.length > 0) {
        tvActivePriceLines.forEach(pl => tvCandleSeries.removePriceLine(pl));
        tvActivePriceLines = [];
      }
    }

    // Función global para abrir cualquier estrategia en TradingView desde otras pestañas
    function openStrategyInChart(strategyId) {
      switchTab('chart');
      setTimeout(() => {
        const select = document.getElementById('tv-strategy-select');
        if (select) {
          select.value = strategyId;
          changeTvStrategy(strategyId);
        }
      }, 150);
    }

    // Enlazar evento al cambiar de tab para inicializar el chart si se selecciona
    const originalSwitchTab = window.switchTab;
    window.switchTab = function(tabId) {
      if (typeof originalSwitchTab === 'function') originalSwitchTab(tabId);
      if (tabId === 'chart') {
        loadTradingViewTab();
      }
    };
  </script>
"""

if 'CONTROLADOR TRADINGVIEW' not in content:
  content = content + '\n' + tv_js_code

tmpl_path.write_text(content, encoding='utf-8')
print("templates/index.html actualizado con TradingView exitosamente!")
