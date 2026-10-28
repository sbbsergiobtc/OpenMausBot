from pathlib import Path

tmpl_path = Path('/root/AlgrokQuant/dashboard/templates/index.html')
content = tmpl_path.read_text(encoding='utf-8')

old_js_start = "<!-- ============================================================================== -->\n  <!-- CONTROLADOR TRADINGVIEW LIGHTWEIGHT CHARTS (DESK CUANTITATIVO ALGROKQUANT) -->"

new_js = """<!-- ============================================================================== -->
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
      setTimeout(() => {
        resizeTvCharts();
      }, 100);
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
          vertLines: { color: 'rgba(30, 41, 59, 0.35)' },
          horzLines: { color: 'rgba(30, 41, 59, 0.35)' }
        },
        crosshair: {
          mode: LightweightCharts.CrosshairMode.Normal,
          vertLine: { color: '#475569', width: 1, style: 3, labelBackgroundColor: '#1e293b' },
          horzLine: { color: '#475569', width: 1, style: 3, labelBackgroundColor: '#1e293b' }
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
        hoverEl.innerHTML = `<span class="text-slate-400">${dateStr}</span> · O: <span class="text-white">${data.open.toFixed(2)}</span> H: <span class="text-emerald-400">${data.high.toFixed(2)}</span> L: <span class="text-rose-400">${data.low.toFixed(2)}</span> C: <span class="text-white font-bold">${data.close.toFixed(2)}</span>`;
      });

      // Manejo responsive
      const resizeObserver = new ResizeObserver(entries => {
        if (!entries || entries.length === 0) return;
        resizeTvCharts();
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
      Object.values(tvOverlaySeries).forEach(item => {
        if (item && item.series) tvMainChart.removeSeries(item.series);
      });
      tvOverlaySeries = {};

      // Limpiar series anteriores de Osciladores
      Object.values(tvOscillatorSeries).forEach(item => {
        if (item && item.series) tvSubChart.removeSeries(item.series);
      });
      tvOscillatorSeries = {};

      // Limpiar PriceLines
      clearActivePriceLines();

      // 3. Cargar Velas
      tvCandleSeries.setData(data.candles);

      // 4. Cargar Overlays (LÍNEAS FINAS 1PX Y CONMUTABLES CON UN CLIC)
      const badgesContainer = document.getElementById('tv-indicator-badges');
      if (badgesContainer) badgesContainer.innerHTML = '';

      data.overlays.forEach(ov => {
        const series = tvMainChart.addLineSeries({
          color: ov.color,
          lineWidth: 1, // LÍNEA FINA Y LIMPIA (1px)
          lineStyle: ov.lineStyle || 0,
          title: ov.name
        });
        series.setData(ov.data);
        tvOverlaySeries[ov.id] = { series: series, visible: true };

        // Badge interactivo para ocultar/mostrar con un clic
        if (badgesContainer) {
          const badge = document.createElement('button');
          badge.id = `tv-badge-${ov.id}`;
          badge.onclick = () => toggleTvOverlay(ov.id);
          badge.className = 'px-2 py-0.5 rounded text-[11px] font-mono font-bold border flex items-center gap-1.5 transition cursor-pointer hover:brightness-125';
          badge.style.borderColor = ov.color + '40';
          badge.style.backgroundColor = ov.color + '15';
          badge.style.color = ov.color;
          badge.title = 'Click para ocultar o mostrar';
          badge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full" style="background-color: ${ov.color}"></span> ${ov.name}`;
          badgesContainer.appendChild(badge);
        }
      });

      // 5. Cargar Osciladores en Sub-Panel (LÍNEAS FINAS 1PX)
      const subTitle = document.getElementById('tv-subchart-title');
      if (data.oscillators && data.oscillators.length > 0) {
        const mainOsc = data.oscillators[0];
        if (subTitle) {
          subTitle.innerHTML = `<i class="fa-solid fa-wave-square text-rose-400"></i> ${mainOsc.name}`;
        }

        data.oscillators.forEach(osc => {
          const oscSeries = tvSubChart.addLineSeries({
            color: osc.color,
            lineWidth: 1, // LÍNEA FINA 1PX
            title: osc.name
          });
          oscSeries.setData(osc.data);
          tvOscillatorSeries[osc.id] = { series: oscSeries, visible: true };

          // Añadir líneas de umbral si tiene (también finas y discretas)
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

      // 6. Cargar Marcadores de Trades
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

      // Vista general adaptada
      resizeTvCharts();
      tvMainChart.timeScale().fitContent();
      tvSubChart.timeScale().fitContent();

      if (data.trades && data.trades.length > 0) {
        selectTvTrade(0, false);
      } else {
        const inspector = document.getElementById('tv-trade-inspector');
        if (inspector) inspector.classList.add('hidden');
      }
    }

    // Conmutar Visibilidad de Indicadores Individuales
    function toggleTvOverlay(ovId) {
      const item = tvOverlaySeries[ovId];
      if (!item) return;
      item.visible = !item.visible;
      item.series.applyOptions({ visible: item.visible });

      const badge = document.getElementById(`tv-badge-${ovId}`);
      if (badge) {
        if (item.visible) {
          badge.style.opacity = '1';
          badge.style.textDecoration = 'none';
        } else {
          badge.style.opacity = '0.35';
          badge.style.textDecoration = 'line-through';
        }
      }
    }

    // Seleccionar una Operación (Líneas finas de SL y TP)
    function selectTvTrade(idx, shouldZoom = true) {
      if (!tvCurrentData || !tvCurrentData.trades || !tvCurrentData.trades[idx]) return;
      const t = tvCurrentData.trades[idx];
      tvCurrentTradeIdx = parseInt(idx);

      const tradeSelect = document.getElementById('tv-trade-select');
      if (tradeSelect) tradeSelect.value = idx;

      clearActivePriceLines();

      if (t.sl_price) {
        const slLine = tvCandleSeries.createPriceLine({
          price: t.sl_price,
          color: '#ef4444',
          lineWidth: 1, // LÍNEA FINA 1PX
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
          lineWidth: 1, // LÍNEA FINA 1PX
          lineStyle: 2,
          axisLabelVisible: true,
          title: `TP: $${t.tp_price.toLocaleString()}`
        });
        tvActivePriceLines.push(tpLine);
      }

      if (t.entry_price) {
        const entryLine = tvCandleSeries.createPriceLine({
          price: t.entry_price,
          color: '#38bdf8',
          lineWidth: 1, // LÍNEA FINA 1PX
          lineStyle: 3,
          axisLabelVisible: true,
          title: `ENTRADA: $${t.entry_price.toLocaleString()}`
        });
        tvActivePriceLines.push(entryLine);
      }

      if (shouldZoom) {
        const fromTime = t.entry_time - (3600 * 48);
        const toTime = t.exit_time + (3600 * 72);
        tvMainChart.timeScale().setVisibleRange({ from: fromTime, to: toTime });
      }

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
      clearActivePriceLines();
    }

    function clearActivePriceLines() {
      if (tvCandleSeries && tvActivePriceLines.length > 0) {
        tvActivePriceLines.forEach(pl => tvCandleSeries.removePriceLine(pl));
        tvActivePriceLines = [];
      }
    }

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

    const prevSwitchTab = window.switchTab;
    window.switchTab = function(tabId) {
      if (typeof prevSwitchTab === 'function') prevSwitchTab(tabId);
      if (tabId === 'chart') {
        loadTradingViewTab();
      }
    };
  </script>
"""

if old_js_start in content:
  idx = content.find(old_js_start)
  content = content[:idx] + new_js
  tmpl_path.write_text(content, encoding='utf-8')
  print("templates/index.html actualizado con líneas finas y botones conmutadores!")
else:
  print("No se encontró el marcador old_js_start")
