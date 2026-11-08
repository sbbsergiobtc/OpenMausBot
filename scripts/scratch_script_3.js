
    // Conmutador interactivo entre Capital Propio y Fondeo (Prop Firm)
    function switchDeskMode(mode) {
      currentDeskMode = mode;
      const bCap = document.getElementById('seg-btn-cap-propio');
      const bProp = document.getElementById('seg-btn-prop-firm');
      if (mode === 'CAPITAL_PROPIO') {
        if (bCap) bCap.className = 'segmented-pill active flex-1';
        if (bProp) bProp.className = 'segmented-pill flex-1';
      } else {
        if (bProp) bProp.className = 'segmented-pill active flex-1';
        if (bCap) bCap.className = 'segmented-pill flex-1';
      }

      // 1. Filtrar las tarjetas y filas de cartera activa superior
      let visibleCount = 0;
      document.querySelectorAll('.strategy-card[data-desk]').forEach(el => {
        if (el.getAttribute('data-desk') === mode) {
          el.style.display = 'flex';
          visibleCount++;
        } else {
          el.style.display = 'none';
        }
      });
      document.querySelectorAll('.strategy-row[data-desk]').forEach(el => {
        if (el.getAttribute('data-desk') === mode) {
          el.style.display = '';
        } else {
          el.style.display = 'none';
        }
      });
      const countBadge = document.getElementById('portfolio-count-badge');
      if (countBadge) {
        countBadge.innerText = (mode === 'CAPITAL_PROPIO') 
          ? `${visibleCount} ESTRATEGIAS CAPITAL PROPIO` 
          : `${visibleCount} ESTRATEGIAS FONDEO (PROP FIRM)`;
      }

    // Segregación estricta del selector de Backtest según Mesa Operativa
    function updateAccountSelectorOptions(mode) {
      const bFilter = document.getElementById('account-selector');
      if (!bFilter) return;

      if (mode === 'PROP_FIRM') {
        bFilter.innerHTML = `
          <option value="PORT-NDX-SPX" selected>🏆 Cartera Combinada Sprint (NDX-005 + SPX-005 · 62 Trades · Target en 18 Días)</option>
          <option value="PROP-NDX-005">🏛️ Nasdaq 100 2h Bollinger Dip (PROP-NDX-005 · 30 Trades · Target en 21 Días)</option>
          <option value="PROP-SPX-005">🏛️ S&P 500 1D Connors RSI2 (PROP-SPX-005 · 32 Trades · Target en 28 Días)</option>
          <option value="PROP-NDX-006">🏛️ Nasdaq 100 1h Bollinger Dip (PROP-NDX-006 · 63 Trades · Target en 32 Días)</option>
          <option value="PROP-FX-EUR-001">💶 EUR/USD 1h London-NY (PROP-FX-EUR-001 · 120 Trades)</option>
          <option value="HYB-NDX-BOL-LINE-48-2.0-3.0">⚡ NDX Híbrido Linear Decay 2.0/3.0 (Futuros/CFD · 43 Trades · Target en 25 Días)</option>
          <option value="HYB-NDX-BOL-LINE-48-2.0-4.0">⚡ NDX Híbrido Linear Decay 2.0/4.0 (Futuros/CFD · 43 Trades · Target en 25 Días)</option>
          <option value="HYB-NDX-BOL-LINE-48-2.5-3.0">⚡ NDX Híbrido Linear Decay 2.5/3.0 (Prop Firm · 43 Trades · Target en 29 Días)</option>
          <option value="HYB-NDX-BOL-LINE-48-2.5-4.0">⚡ NDX Híbrido Linear Decay 2.5/4.0 (Prop Firm · 43 Trades · Target en 29 Días)</option>
          <option value="HYB-NDX-BOL-LINE-48-2.5-2.0">⚡ NDX Híbrido Linear Decay 2.5/2.0 (Prop Firm · 43 Trades · Target en 29 Días)</option>
          <option value="ALL_PROP">🏛️ Consolidado Fondeo (Cartera Completa · 460 Trades)</option>
        `;
        bFilter.value = 'PORT-NDX-SPX';
      } else {
        bFilter.innerHTML = `
          <option value="CAP-SPX-006" selected>📊 S&P 500 4h Bollinger Dip (Capital Propio TradFi · 318 Trades)</option>
          <option value="CAP-NDX-005">📈 Nasdaq 100 2h Bollinger Dip (Capital Propio TradFi · 365 Trades)</option>
          <option value="STRAT-FAST-035">⚡ Bitcoin 1h Shannon Entropy (Capital Propio DEX · 262 Trades)</option>
          <option value="CRYPTO-HL">⚡ Crypto Paper Hyperliquid (1.000 USDC · Testnet Activo)</option>
          <option value="ALL_CAP">💼 Consolidado Capital Propio (TradFi + DEX · 945 Trades)</option>
        `;
        bFilter.value = 'CAP-SPX-006';
      }
    }

      // 2. Sincronizar selector de Backtests con segregación estricta por Mesa
      updateAccountSelectorOptions(mode);
      if (typeof onAccountFilterChange === 'function') {
        onAccountFilterChange();
      }

      // 2b. Sincronizar filtro en Contraste Tri-Faceta
      const tfFilter = document.getElementById('tf-segment-filter');
      if (tfFilter) {
        tfFilter.value = (mode === 'CAPITAL_PROPIO') ? 'Capital Propio (TradFi)' : 'Prop Firm';
        if (typeof filterTriFacetTable === 'function') {
          filterTriFacetTable();
        }
      }

      // 2c. Sincronizar filtro en Catálogo de Modelos
      const catFilter = document.getElementById('strategy-filter-cat');
      if (catFilter) {
        catFilter.value = (mode === 'CAPITAL_PROPIO') ? 'crypto_fast' : 'prop_firm';
        if (typeof filterStrategies === 'function') {
          filterStrategies();
        }
      }

      // 3. Filtrar catálogo de TradingView
      if (typeof fetchTvStrategyCatalog === 'function') {
        fetchTvStrategyCatalog(mode);
      }

      // 4. Sincronizar foco visual en Forward Test (ambas tarjetas permanecen activas y 100% visibles)
      const ftPfCard = document.getElementById('ft-propfirm-card');
      const ftHlCard = document.getElementById('ft-hyperliquid-card');
      if (ftPfCard && ftHlCard) {
        ftPfCard.style.opacity = '1';
        ftHlCard.style.opacity = '1';
        if (mode === 'CAPITAL_PROPIO') {
          ftHlCard.classList.add('ring-2', 'ring-amber-400/40');
          ftPfCard.classList.remove('ring-2', 'ring-cyan-400/40');
        } else {
          ftPfCard.classList.add('ring-2', 'ring-cyan-400/40');
          ftHlCard.classList.remove('ring-2', 'ring-amber-400/40');
        }
      }

      // 5. Sincronizar Curva de Rentabilidad en Forward Test según el modo activo (Capital Propio vs Fondeo)
      if (typeof setFtCurveSegment === 'function') {
        if (mode === 'PROP_FIRM') {
          setFtCurveSegment('PF');
        } else {
          setFtCurveSegment('REAL');
        }
      }

      // 6. Sincronizar Tabla de Estrategias Desplegadas en Forward Test
      if (typeof renderActiveForwardStrategies === 'function') {
        renderActiveForwardStrategies();
      }

      // 7. Sincronizar Tarjeta de Métricas y Órdenes en Vivo de Forward Test
      if (typeof updateForwardDeskCardAndOrders === 'function') {
        updateForwardDeskCardAndOrders(cachedForwardStateData);
      }

      // 8. Sincronizar Historial de Operaciones Forward Test según Mesa
      if (typeof setFtTradeFilter === 'function') {
        setFtTradeFilter(currentFtTradeFilter);
      }

      // 9. Sincronizar Tabla de Cartera Activa del Cockpit General (16 Estrategias)
      if (typeof renderCockpitPortfolioTable === 'function') {
        renderCockpitPortfolioTable();
      }
    }

    // =========================================================================
    // CONMUTADOR DE VISTA DE CARTERA (TABLA DENSA vs CUADRÍCULA)
    // =========================================================================
    function setPortfolioView(view) {
      const tableView = document.getElementById('portfolio-table-view');
      const gridView = document.getElementById('portfolio-grid-view');
      const btnTable = document.getElementById('view-toggle-table');
      const btnGrid = document.getElementById('view-toggle-grid');

      if (view === 'grid') {
        if (tableView) tableView.classList.add('hidden');
        if (gridView) gridView.classList.remove('hidden');
        if (btnGrid) {
          btnGrid.className = 'px-2.5 py-1 rounded text-xs font-bold font-mono transition flex items-center gap-1.5 bg-[#FFFFFF] text-[#181A20] shadow-xs';
          const iconG = btnGrid.querySelector('i');
          if (iconG) iconG.className = 'fa-solid fa-grip text-[#3C45A5]';
        }
        if (btnTable) {
          btnTable.className = 'px-2.5 py-1 rounded text-xs font-bold font-mono transition flex items-center gap-1.5 text-[#55544E] hover:text-[#181A20]';
          const iconT = btnTable.querySelector('i');
          if (iconT) iconT.className = 'fa-solid fa-table-list text-[#55544E]';
        }
      } else {
        if (tableView) tableView.classList.remove('hidden');
        if (gridView) gridView.classList.add('hidden');
        if (btnTable) {
          btnTable.className = 'px-2.5 py-1 rounded text-xs font-bold font-mono transition flex items-center gap-1.5 bg-[#FFFFFF] text-[#181A20] shadow-xs';
          const iconT = btnTable.querySelector('i');
          if (iconT) iconT.className = 'fa-solid fa-table-list text-[#3C45A5]';
        }
        if (btnGrid) {
          btnGrid.className = 'px-2.5 py-1 rounded text-xs font-bold font-mono transition flex items-center gap-1.5 text-[#55544E] hover:text-[#181A20]';
          const iconG = btnGrid.querySelector('i');
          if (iconG) iconG.className = 'fa-solid fa-grip text-[#55544E]';
        }
      }
      try { localStorage.setItem('algrok_portfolio_view', view); } catch (e) {}
    }

    // Inicializar preferencia de vista
    try {
      const savedView = localStorage.getItem('algrok_portfolio_view') || 'table';
      setPortfolioView(savedView);
    } catch (e) {}

    // Protocolo de Pausa Preventiva Global (Kill-Switch)
    function triggerEmergencyKillSwitch() {
      const confirmed = confirm('⚠️ ATENCIÓN: PROTOCOLO DE INTERVENCIÓN OPERATIVA\n\n¿Deseas activar la PAUSA PREVENTIVA global de todas las estrategias activas?\n\n- Se congelará la apertura de nuevas posiciones.\n- Se mantendrán los stop-loss y take-profit existentes en broker.\n- El enjambre pasará a modo de monitoreo pasivo.');
      if (confirmed) {
        const btn = document.getElementById('btn-kill-switch');
        if (btn) {
          btn.innerHTML = '<i class="fa-solid fa-check"></i> PAUSA ACTIVADA';
          btn.className = 'px-3.5 py-2 rounded-lg bg-amber-600 text-white text-xs font-bold font-mono flex items-center gap-1.5 shadow-sm';
        }
        alert('✅ Pausa preventiva activada con éxito. Enjambre en modo seguro.');
      }
    }

    // Modal de Auditoría de Riesgo
    function toggleRiskAuditModal() {
      if (typeof switchTab === 'function') {
        switchTab('risk');
      }
    }

    // Enganche para sincronizar estado visual del menú lateral único y visibilidad de cartera
    const origSwitchTab = window.switchTab;
    window.switchTab = function(tabId) {
      // Actualizar botones del Sidebar
      document.querySelectorAll('.sidebar-link').forEach(el => {
        el.className = 'sidebar-link';
      });
      const sideBtn = document.getElementById('side-tab-' + tabId);
      if (sideBtn) {
        sideBtn.className = 'sidebar-link active';
      }

      // VISIBILIDAD DE CARTERA ACTIVA: Exclusiva del Cockpit General ('dashboard')
      const activePortfolio = document.getElementById('active-portfolio-section');
      if (activePortfolio) {
        if (tabId === 'dashboard') {
          activePortfolio.style.display = 'block';
        } else {
          activePortfolio.style.display = 'none';
        }
      }

      // Cargar TradingView automáticamente al entrar en la pestaña 'chart'
      if (tabId === 'chart') {
        if (typeof loadTradingViewTab === 'function') {
          loadTradingViewTab();
        }
      }

      // Llamar a la función original de navegación
      if (typeof origSwitchTab === 'function') {
        origSwitchTab(tabId);
      }
    };

    function triggerSyncEffect() {
      const icon = document.getElementById('tele-refresh-icon');
      if (icon) {
        icon.classList.add('fa-spin');
        setTimeout(() => icon.classList.remove('fa-spin'), 1000);
      }
    }

    // Inicialización al cargar la página
    document.addEventListener('DOMContentLoaded', () => {
      // Activar filtrado inicial por Capital Propio
      if (typeof switchDeskMode === 'function') {
        switchDeskMode('CAPITAL_PROPIO');
      }
      if (typeof fetchRegimeOrchestratorData === 'function') {
        fetchRegimeOrchestratorData(false);
      }
      if (typeof fetchForwardState === 'function') {
        fetchForwardState();
      }
    });
  
    // =========================================================================
    // DOUBLE Q-LEARNING TABULAR MATRIX & TRIPLE BOOK BENCHMARK (10 REGIMES)
    // =========================================================================
    let cachedQLearningData = null;
    let currentQLPolicyDesk = 'PROP_FIRM';
    let currentQLGuardian = 'GREEN';

    async function fetchQLearningMatrixData(forceRefresh = false) {
      const icon = document.getElementById('ql-refresh-icon');
      if (icon && forceRefresh) icon.classList.add('fa-spin');
      try {
        const res = await fetch('/api/q_learning_matrix');
        if (!res.ok) return;
        const data = await res.json();
        cachedQLearningData = data;
        renderQLearningUI(data);
        if (typeof fetchLibroCTelemetry === 'function') fetchLibroCTelemetry();
        if (typeof renderLiveAssetsHUD === 'function' && typeof cachedOrchestratorData !== 'undefined') renderLiveAssetsHUD(cachedOrchestratorData, data);
        if (typeof runQSimulation === 'function') runQSimulation();
      } catch (e) {
        console.error('Error fetching Q-Learning Matrix:', e);
      } finally {
        if (icon && forceRefresh) setTimeout(() => icon.classList.remove('fa-spin'), 600);
      }
    }

    function setQLearningPolicyDesk(desk) {
      currentQLPolicyDesk = desk;
      document.getElementById('btn-ql-desk-prop')?.classList.toggle('active', desk === 'PROP_FIRM');
      document.getElementById('btn-ql-desk-cap')?.classList.toggle('active', desk === 'CAPITAL_PROPIO');
      if (cachedQLearningData) renderQLearningUI(cachedQLearningData);
    }

    function setQLearningGuardianFilter(guard) {
      currentQLGuardian = guard;
      document.getElementById('btn-ql-guard-green')?.classList.toggle('active', guard === 'GREEN');
      document.getElementById('btn-ql-guard-amber')?.classList.toggle('active', guard === 'AMBER');
      if (cachedQLearningData) renderQLearningUI(cachedQLearningData);
    }

    function renderQLearningUI(data) {
      if (!data || !data.policies) return;
      const desk = currentQLPolicyDesk;
      const pol = data.policies[desk] || {};
      const oos = pol.oos_triple_book_benchmark || {};
      const catalog = data.regime_10_catalog || {};
      
      const b = document.getElementById('ql-last-update-badge');
      if (b) b.innerText = 'Actualizado: ' + (data.updated_at_utc || 'En vivo');

      const alphaBanner = document.getElementById('ql-alpha-banner');
      if (alphaBanner) {
        const alphaVsHeur = Number(oos.q_learning_alpha_vs_heuristic_pct || 0).toFixed(2);
        const calmarC = oos.book_c_qlearning ? Number(oos.book_c_qlearning.calmar_eod_ratio).toFixed(2) : '--';
        alphaBanner.innerText = `+${alphaVsHeur}% Alfa vs Heurístico · Calmar EOD: ${calmarC}`;
      }

      const cardsContainer = document.getElementById('ql-triple-book-cards');
      if (cardsContainer) {
        const bA = oos.book_a_unfiltered || {};
        const bB = oos.book_b_heuristic || {};
        const bC = oos.book_c_qlearning || {};

        cardsContainer.innerHTML = `
          <div class="glass-card rounded-2xl p-4 space-y-2 border border-[#E5E5EA]">
            <div class="flex items-center justify-between">
              <span class="overline-text">LIBRO A · SIN FILTRO (100% AUTÓNOMO)</span>
              <span class="badge-neutral-soft font-mono">${bA.trades_executed || 0} Trades</span>
            </div>
            <div class="text-xl font-bold font-mono text-[#181A20]">+${Number(bA.net_roi_pct || 0).toFixed(2)}% ROI</div>
            <div class="grid grid-cols-2 gap-2 text-xs font-mono pt-2 border-t border-[#F2F2F7]">
              <div><span class="text-[#6E6E73] block">Max EOD DD:</span><strong class="text-[#B45309]">${Number(bA.max_eod_dd_pct || 0).toFixed(2)}%</strong></div>
              <div><span class="text-[#6E6E73] block">Calmar Ratio:</span><strong>${Number(bA.calmar_eod_ratio || 0).toFixed(2)}</strong></div>
            </div>
            <div class="text-[11px] font-mono text-[#6E6E73] pt-1">Whipsaws Evitados: <strong>${bA.whipsaws_avoided || 0}</strong></div>
          </div>

          <div class="glass-card rounded-2xl p-4 space-y-2 border border-[#E5E5EA]">
            <div class="flex items-center justify-between">
              <span class="overline-text text-[#3C45A5]">LIBRO B · HEURÍSTICO CONVENCIONAL</span>
              <span class="badge-brand-indigo font-mono">${bB.trades_executed || 0} Trades</span>
            </div>
            <div class="text-xl font-bold font-mono text-[#065F46]">+${Number(bB.net_roi_pct || 0).toFixed(2)}% ROI</div>
            <div class="grid grid-cols-2 gap-2 text-xs font-mono pt-2 border-t border-[#F2F2F7]">
              <div><span class="text-[#6E6E73] block">Max EOD DD:</span><strong class="text-[#065F46]">${Number(bB.max_eod_dd_pct || 0).toFixed(2)}%</strong></div>
              <div><span class="text-[#6E6E73] block">Calmar Ratio:</span><strong>${Number(bB.calmar_eod_ratio || 0).toFixed(2)}</strong></div>
            </div>
            <div class="text-[11px] font-mono text-[#6E6E73] pt-1">Whipsaws Evitados: <strong>${bB.whipsaws_avoided || 0}</strong></div>
          </div>

          <div class="glass-card rounded-2xl p-4 space-y-2 border-2 border-[#3C45A5] bg-[#F8F9FE]">
            <div class="flex items-center justify-between">
              <span class="overline-text text-[#3C45A5] font-bold">LIBRO C · DOUBLE Q-LEARNING TABULAR</span>
              <span class="badge-success-live font-mono">${bC.trades_executed || 0} Trades</span>
            </div>
            <div class="text-xl font-bold font-mono text-[#3C45A5]">+${Number(bC.net_roi_pct || 0).toFixed(2)}% ROI</div>
            <div class="grid grid-cols-2 gap-2 text-xs font-mono pt-2 border-t border-[#E5E5EA]">
              <div><span class="text-[#6E6E73] block">Max EOD DD:</span><strong class="text-[#065F46]">${Number(bC.max_eod_dd_pct || 0).toFixed(2)}%</strong></div>
              <div><span class="text-[#6E6E73] block">Calmar Ratio:</span><strong class="text-[#3C45A5]">${Number(bC.calmar_eod_ratio || 0).toFixed(2)}</strong></div>
            </div>
            <div class="flex items-center justify-between text-[11px] font-mono pt-1">
              <span class="text-[#065F46] font-bold"><i class="fa-solid fa-check"></i> Whipsaws: ${bC.whipsaws_avoided || 0}</span>
              <span class="px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 font-bold border border-purple-200">
                ${bC.consistency_40pct_early_clamps || 0} Clamps 40% TP
              </span>
            </div>
          </div>
        `;
      }

      const matrixTbody = document.getElementById('ql-matrix-tbody');
      if (matrixTbody) {
        const rows = (currentQLGuardian === 'GREEN') ? (pol.readable_10x3_green || []) : (pol.readable_10x3_amber || []);
        matrixTbody.innerHTML = rows.map(r => {
          const regMeta = catalog[String(r.regime_id)] || {};
          const arch = r.archetypes || {};
          
          const formatActionCellContent = (cellData) => {
            if (!cellData) return '<div class="py-2 text-center text-slate-400">--</div>';
            const mult = Number(cellData.multiplier || 0);
            const qVal = Number(cellData.q_value || 0).toFixed(3);
            const visits = cellData.visits || 0;
            
            let badgeClass = 'bg-[#FAFAFC] text-[#6E6E73] border-[#E5E5EA]';
            let clampIndicator = '';
            if (mult >= 1.25) {
              badgeClass = 'bg-purple-100 text-purple-800 border-purple-300 font-bold';
              if (desk === 'PROP_FIRM') {
                clampIndicator = '<span class="block text-[9px] text-purple-600 font-semibold uppercase">Clamp 40% Armado</span>';
              }
            } else if (mult >= 1.0) {
              badgeClass = 'bg-emerald-100 text-emerald-800 border-emerald-300 font-bold';
            } else if (mult >= 0.75) {
              badgeClass = 'bg-blue-100 text-blue-800 border-blue-300 font-semibold';
            } else if (mult >= 0.50) {
              badgeClass = 'bg-amber-100 text-amber-800 border-amber-300 font-semibold';
            } else {
              badgeClass = 'bg-rose-100 text-rose-800 border-rose-300 font-bold';
            }
            
            return `
              <div class="py-1 px-2 text-center whitespace-nowrap">
                <span class="inline-block px-2 py-0.5 rounded text-xs border ${badgeClass}">
                  ${cellData.action_label || (mult.toFixed(2) + 'x')}
                </span>
                ${clampIndicator}
                <div class="text-[10px] text-[#6E6E73] mt-0.5">
                  <span>Q: ${qVal}</span> · <span class="text-[#86868B]">${visits} v</span>
                </div>
              </div>
            `;
          };

          return `
            <tr class="hover:bg-[#F5EFE6]/40 transition">
              <td class="py-2.5 px-3 whitespace-nowrap">
                <div class="font-bold text-[#181A20]">${r.regime_code}</div>
                <div class="text-[11px] text-[#3C45A5] font-semibold">${r.regime_label}</div>
              </td>
              <td class="py-2.5 px-3 text-[11px] text-[#6E6E73] font-mono">
                ${regMeta.description || regMeta.macro_regime || 'Detección Numba JIT'}
              </td>
              <td class="cursor-pointer hover:bg-slate-100/60 transition" onclick="openQExplainModal(${r.regime_id}, 'TREND_FOLLOWING')" title="Click para ver explicabilidad Q-Learning">
                ${formatActionCellContent(arch['TREND_FOLLOWING'])}
              </td>
              <td class="cursor-pointer hover:bg-slate-100/60 transition" onclick="openQExplainModal(${r.regime_id}, 'MEAN_REVERSION')" title="Click para ver explicabilidad Q-Learning">
                ${formatActionCellContent(arch['MEAN_REVERSION'])}
              </td>
              <td class="cursor-pointer hover:bg-slate-100/60 transition" onclick="openQExplainModal(${r.regime_id}, 'VOLATILITY_BREAKOUT')" title="Click para ver explicabilidad Q-Learning">
                ${formatActionCellContent(arch['VOLATILITY_BREAKOUT'])}
              </td>
            </tr>
          `;
        }).join('');
      }
    }

  
    // =========================================================================
    // FASE 3: EXPLAINABILITY, WHAT-IF SIMULATOR & ACTION STREAM TELEMETRY
    // =========================================================================

    async function fetchLibroCTelemetry() {
      try {
        const res = await fetch('/api/libro_c_telemetry?limit=30');
        if (!res.ok) return;
        const data = await res.json();
        renderLibroCTelemetryUI(data);
      } catch (e) {
        console.error('Error fetching Libro C telemetry:', e);
      }
    }

    function renderLibroCTelemetryUI(data) {
      const container = document.getElementById('ql-telemetry-stream');
      const badge = document.getElementById('ql-telemetry-badge');
      if (!container) return;
      const events = data.events || [];
      if (badge) badge.innerText = `● ${events.length} Eventos`;

      if (events.length === 0) {
        container.innerHTML = '<div class="text-center py-4 text-[#86868B]">Sin eventos recientes de Libro C. Monitor en espera...</div>';
        return;
      }

      container.innerHTML = events.map(ev => {
        let evColor = 'text-slate-700 bg-slate-50 border-slate-200';
        let icon = 'fa-circle-info text-blue-500';
        if (ev.event_type === 'TRADE_OPENED') {
          evColor = 'text-emerald-800 bg-emerald-50/70 border-emerald-200';
          icon = 'fa-arrow-trend-up text-emerald-600';
        } else if (ev.event_type === 'TRADE_CLOSED') {
          const pnl = Number(ev.details?.pnl_usd || 0);
          evColor = pnl >= 0 ? 'text-emerald-800 bg-emerald-50/70 border-emerald-200' : 'text-rose-800 bg-rose-50/70 border-rose-200';
          icon = pnl >= 0 ? 'fa-circle-check text-emerald-600' : 'fa-circle-xmark text-rose-600';
        } else if (ev.event_type === 'TRADE_BLOCKED_BY_Q') {
          evColor = 'text-amber-800 bg-amber-50/70 border-amber-200';
          icon = 'fa-hand text-amber-600';
        } else if (ev.event_type === 'EARLY_TP_CLAMPED' || ev.event_type === 'TRADE_BLOCKED_BY_CONSISTENCY_40') {
          evColor = 'text-purple-800 bg-purple-50/70 border-purple-200';
          icon = 'fa-shield text-purple-600';
        }

        const timeShort = (ev.timestamp_utc || '').split(' ')[1] || ev.timestamp_utc;
        const detailsStr = Object.entries(ev.details || {}).map(([k, v]) => `${k}=${v}`).join(' · ');

        return `
          <div class="p-2 rounded-lg border ${evColor} flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-[11px]">
            <div class="flex items-center gap-2">
              <i class="fa-solid ${icon}"></i>
              <strong class="font-bold text-[#181A20]">${ev.symbol}</strong>
              <span class="px-1.5 py-0.2 rounded bg-white/80 border text-[10px] font-semibold">${ev.event_type}</span>
              <span class="text-[#6E6E73]">${ev.regime_code} · ${ev.action_multiplier}x</span>
            </div>
            <div class="flex items-center gap-2 text-[#6E6E73] text-[10px]">
              <span class="truncate max-w-xs" title="${detailsStr}">${detailsStr}</span>
              <span class="font-bold text-[#181A20] shrink-0">${timeShort}</span>
            </div>
          </div>
        `;
      }).join('');
    }

    async function openQExplainModal(regimeId, archetype) {
      const modal = document.getElementById('q-explain-modal');
      const body = document.getElementById('modal-q-body');
      const title = document.getElementById('modal-q-title');
      if (!modal || !body) return;
      modal.classList.remove('hidden');

      if (title) title.innerText = `Explicabilidad Q: Régimen S${regimeId} × ${archetype}`;
      body.innerHTML = '<div class="text-center py-6 text-slate-400"><i class="fa-solid fa-spinner fa-spin"></i> Evaluando matriz Q...</div>';

      try {
        const desk = currentQLPolicyDesk || 'PROP_FIRM';
        const guard = currentQLGuardian || 'GREEN';
        const res = await fetch(`/api/q_explain?desk_mode=${desk}&regime_id=${regimeId}&archetype=${archetype}&guardian=${guard}`);
        if (!res.ok) throw new Error('API Error');
        const d = await res.json();

        const distBars = (d.actions_distribution || []).map(act => {
          const isOptimal = (act.multiplier === d.optimal_multiplier);
          const barColor = isOptimal ? 'bg-[#3C45A5]' : 'bg-slate-300';
          const maxQ = Math.max(...d.actions_distribution.map(a => Math.abs(a.q_value || 0)), 1.0);
          const pct = Math.min(100, Math.max(10, Math.round((Math.max(0, act.q_value) / maxQ) * 100)));

          return `
            <div class="space-y-1 text-xs font-mono">
              <div class="flex justify-between items-center text-[11px]">
                <span class="${isOptimal ? 'font-bold text-[#3C45A5]' : 'text-slate-600'}">${act.action_label} ${isOptimal ? '★ Óptima' : ''}</span>
                <span class="text-slate-500">Q: ${act.q_value} (${act.visits} visitas)</span>
              </div>
              <div class="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div class="${barColor} h-2 rounded-full transition-all" style="width: ${pct}%"></div>
              </div>
            </div>
          `;
        }).join('');

        body.innerHTML = `
          <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1 font-mono text-xs">
            <div class="font-bold text-slate-800">${d.regime_code} · ${d.regime_label}</div>
            <div class="text-[11px] text-slate-500">${d.regime_description}</div>
            <div class="flex items-center gap-2 pt-1 text-[11px]">
              <span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold">Acción: ${d.optimal_multiplier}x</span>
              <span class="text-slate-500">Visitas acumuladas: ${d.total_visits}</span>
            </div>
          </div>

          <div class="space-y-2 pt-1">
            <div class="overline-text">DISTRIBUCIÓN DE Q-VALUES (QA, QB)</div>
            <div class="space-y-2">
              ${distBars}
            </div>
          </div>

          <div class="p-3 rounded-xl bg-[#F8F9FE] border border-[#3C45A5]/20 space-y-1">
            <div class="overline-text text-[#3C45A5]">JUSTIFICACIÓN CUANTITATIVA CAUSAL</div>
            <p class="text-xs text-slate-700 leading-relaxed">${d.quantitative_justification}</p>
          </div>
        `;
      } catch (err) {
        body.innerHTML = `<div class="p-3 text-xs text-rose-600 bg-rose-50 rounded-lg">Error cargando explicabilidad: ${err.message}</div>`;
      }
    }

    function closeQExplainModal() {
      const modal = document.getElementById('q-explain-modal');
      if (modal) modal.classList.add('hidden');
    }

    async function runQSimulation() {
      const adx = parseFloat(document.getElementById('sim-input-adx')?.value || 28);
      const ker = parseFloat(document.getElementById('sim-input-ker')?.value || 0.42);
      const hnorm = parseFloat(document.getElementById('sim-input-hnorm')?.value || 0.68);
      const hurst = parseFloat(document.getElementById('sim-input-hurst')?.value || 0.62);
      const atr = parseFloat(document.getElementById('sim-input-atr')?.value || 45);

      document.getElementById('sim-val-adx').innerText = adx.toFixed(1);
      document.getElementById('sim-val-ker').innerText = ker.toFixed(2);
      document.getElementById('sim-val-hnorm').innerText = hnorm.toFixed(2);
      document.getElementById('sim-val-hurst').innerText = hurst.toFixed(2);
      document.getElementById('sim-val-atr').innerText = `${atr.toFixed(0)}%`;

      const desk = currentQLPolicyDesk || 'PROP_FIRM';
      const guard = currentQLGuardian || 'GREEN';

      try {
        const res = await fetch(`/api/simulate_q_action?desk_mode=${desk}&adx=${adx}&ker=${ker}&h_norm=${hnorm}&hurst=${hurst}&atr_pctile=${atr}&guardian=${guard}`);
        if (!res.ok) return;
        const d = await res.json();
        const container = document.getElementById('sim-results-container');
        if (!container) return;

        const acts = d.actions || {};
        const tfAct = acts['TREND_FOLLOWING']?.q_lot_multiplier ?? 1.0;
        const mrAct = acts['MEAN_REVERSION']?.q_lot_multiplier ?? 1.0;
        const boAct = acts['VOLATILITY_BREAKOUT']?.q_lot_multiplier ?? 1.0;

        container.innerHTML = `
          <div class="bg-white p-2.5 rounded-lg border border-[#E5E5EA]">
            <span class="text-[10px] text-[#6E6E73] block">Régimen Clasificado:</span>
            <strong class="text-xs text-[#3C45A5] font-mono">${d.regime_code}</strong>
            <span class="text-[10px] text-[#6E6E73] block truncate">${d.regime_label}</span>
          </div>
          <div class="bg-white p-2.5 rounded-lg border border-[#E5E5EA] text-center">
            <span class="text-[10px] text-[#6E6E73] block">Trend Following:</span>
            <strong class="text-sm font-mono ${tfAct >= 1.0 ? 'text-[#065F46]' : (tfAct > 0 ? 'text-[#B45309]' : 'text-[#D70015]')}">${tfAct.toFixed(2)}x</strong>
          </div>
          <div class="bg-white p-2.5 rounded-lg border border-[#E5E5EA] text-center">
            <span class="text-[10px] text-[#6E6E73] block">Mean Reversion:</span>
            <strong class="text-sm font-mono ${mrAct >= 1.0 ? 'text-[#065F46]' : (mrAct > 0 ? 'text-[#B45309]' : 'text-[#D70015]')}">${mrAct.toFixed(2)}x</strong>
          </div>
          <div class="bg-white p-2.5 rounded-lg border border-[#E5E5EA] text-center">
            <span class="text-[10px] text-[#6E6E73] block">Volatility Breakout:</span>
            <strong class="text-sm font-mono ${boAct >= 1.0 ? 'text-[#065F46]' : (boAct > 0 ? 'text-[#B45309]' : 'text-[#D70015]')}">${boAct.toFixed(2)}x</strong>
          </div>
        `;
      } catch (e) {
        console.error('Error running Q simulation:', e);
      }
    }

    function renderLiveAssetsHUD(orchData, qData) {
      const container = document.getElementById('ql-live-assets-hud');
      if (!container || !orchData || !orchData.regimes_by_asset) return;

      const assets = Object.values(orchData.regimes_by_asset);
      const desk = currentQLPolicyDesk || 'PROP_FIRM';

      container.innerHTML = assets.map(a => {
        const rId = a.regime_id_10 ?? 6;
        const rCode = a.sub_regime_10 || `S${rId}`;
        const mult = (rId === 0 || rId === 1) ? 1.25 : ((rId === 8 || rId === 9) ? 0.0 : (a.lot_multiplier || 1.0));
        const isClamp = (desk === 'PROP_FIRM' && mult >= 1.25);

        let colorCls = 'border-slate-200 bg-white text-slate-800';
        if (mult >= 1.25) colorCls = 'border-purple-200 bg-purple-50 text-purple-900';
        else if (mult >= 1.0) colorCls = 'border-emerald-200 bg-emerald-50 text-emerald-900';
        else if (mult > 0) colorCls = 'border-amber-200 bg-amber-50 text-amber-900';
        else colorCls = 'border-rose-200 bg-rose-50 text-rose-900';

        return `
          <div class="p-2.5 rounded-xl border ${colorCls} space-y-1 font-mono">
            <div class="flex items-center justify-between text-xs">
              <strong class="font-bold text-[#181A20]">${a.asset}</strong>
              <span class="px-1.5 py-0.2 rounded text-[10px] font-bold ${mult >= 1.0 ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-700'}">${mult.toFixed(2)}x</span>
            </div>
            <div class="text-[10px] text-[#6E6E73] truncate" title="${rCode}">${rCode}</div>
            ${isClamp ? '<div class="text-[9px] text-purple-700 font-bold uppercase">40% Clamp OK</div>' : '<div class="text-[9px] text-slate-400">Neutral Sizing</div>'}
          </div>
        `;
      }).join('');
    }

  