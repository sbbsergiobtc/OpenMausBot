from pathlib import Path

tmpl_path = Path('/root/AlgrokQuant/dashboard/templates/index.html')
content = tmpl_path.read_text(encoding='utf-8')

# 1. Agregar estilos CSS para selects oscuros personalizados antes de </style>
select_css = """
    /* ==================== SELECTS DESPLEGABLES DARK THEME ==================== */
    select.dark-custom-select,
    #tv-trade-select,
    #tv-strategy-select {
      background-color: #0d1322 !important;
      color: #f1f5f9 !important;
      border: 1px solid rgba(255, 255, 255, 0.15) !important;
      border-radius: 0.75rem !important;
      padding: 0.45rem 2.2rem 0.45rem 0.85rem !important;
      appearance: none;
      -webkit-appearance: none;
      -moz-appearance: none;
      background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2338bdf8' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e") !important;
      background-repeat: no-repeat !important;
      background-position: right 0.75rem center !important;
      background-size: 0.85rem !important;
      outline: none !important;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4) !important;
      color-scheme: dark !important;
    }
    select.dark-custom-select:hover,
    #tv-trade-select:hover,
    #tv-strategy-select:hover {
      border-color: rgba(56, 189, 248, 0.6) !important;
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.2) !important;
    }
    select.dark-custom-select option,
    #tv-trade-select option,
    #tv-strategy-select option {
      background-color: #090d16 !important;
      color: #f8fafc !important;
      padding: 10px 14px !important;
      font-size: 12px !important;
      font-family: 'JetBrains Mono', monospace !important;
    }
    select.dark-custom-select option:checked,
    #tv-trade-select option:checked,
    select.dark-custom-select option:hover,
    #tv-trade-select option:hover {
      background-color: #1e293b !important;
      color: #38bdf8 !important;
    }
"""

if '/* ==================== SELECTS DESPLEGABLES DARK THEME ==================== */' not in content:
  content = content.replace('  </style>', select_css + '\n  </style>')

# 2. Actualizar HTML del selector de operaciones y de estrategia
old_trade_container = """            <div class="flex items-center bg-slate-800/80 border border-slate-700 rounded-xl p-1 gap-1">
              <button onclick="navigateTvTrade(-1)" class="px-2 py-1 hover:bg-slate-700 rounded text-slate-300 hover:text-white text-xs transition" title="Operación Anterior">
                <i class="fa-solid fa-chevron-left"></i>
              </button>
              <select id="tv-trade-select" onchange="jumpToTvTrade(this.value)" class="bg-transparent text-white text-xs font-mono font-medium focus:outline-none px-2 py-1 cursor-pointer">
                <option value="">Seleccionar Trade...</option>
              </select>
              <button onclick="navigateTvTrade(1)" class="px-2 py-1 hover:bg-slate-700 rounded text-slate-300 hover:text-white text-xs transition" title="Siguiente Operación">
                <i class="fa-solid fa-chevron-right"></i>
              </button>
            </div>"""

new_trade_container = """            <div class="flex items-center bg-slate-900 border border-slate-700 rounded-xl p-1 gap-1.5 shadow-md">
              <button onclick="navigateTvTrade(-1)" class="w-7 h-7 flex items-center justify-center hover:bg-slate-800 rounded-lg text-slate-300 hover:text-cyan-400 text-xs transition" title="Operación Anterior">
                <i class="fa-solid fa-chevron-left text-[11px]"></i>
              </button>
              <select id="tv-trade-select" onchange="jumpToTvTrade(this.value)" class="dark-custom-select text-xs font-mono font-medium min-w-[280px] max-w-[360px] cursor-pointer">
                <option value="">Seleccionar Operación...</option>
              </select>
              <button onclick="navigateTvTrade(1)" class="w-7 h-7 flex items-center justify-center hover:bg-slate-800 rounded-lg text-slate-300 hover:text-cyan-400 text-xs transition" title="Siguiente Operación">
                <i class="fa-solid fa-chevron-right text-[11px]"></i>
              </button>
            </div>"""

if old_trade_container in content:
  content = content.replace(old_trade_container, new_trade_container)

# 3. Actualizar el selector de estrategia con dark-custom-select
old_strat_select = '<select id="tv-strategy-select" onchange="changeTvStrategy(this.value)" class="bg-slate-800 border border-slate-700 text-white rounded-xl px-3 py-2 text-xs font-mono font-semibold focus:outline-none focus:border-cyan-400 cursor-pointer">'
new_strat_select = '<select id="tv-strategy-select" onchange="changeTvStrategy(this.value)" class="dark-custom-select text-xs font-mono font-semibold cursor-pointer max-w-[380px] truncate">'

if old_strat_select in content:
  content = content.replace(old_strat_select, new_strat_select)

# 4. Asegurar que en JS las opciones se agreguen con texto descriptivo y limpio
old_js_poblar = """      // 7. Poblar Selector de Trades
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
      }"""

new_js_poblar = """      // 7. Poblar Selector de Trades
      const tradeSelect = document.getElementById('tv-trade-select');
      if (tradeSelect) {
        tradeSelect.innerHTML = '<option value="">Seleccionar Operación...</option>';
        data.trades.forEach((t, idx) => {
          const opt = document.createElement('option');
          opt.value = idx;
          const icon = t.result === 'WIN' ? '🟢' : '🔴';
          const pnlStr = (t.pnl_pct > 0 ? '+' : '') + t.pnl_pct.toFixed(2) + '%';
          opt.innerText = `${icon} ${t.id} · ${t.type} @ $${t.entry_price.toLocaleString()} (${pnlStr})`;
          tradeSelect.appendChild(opt);
        });
      }"""

if old_js_poblar in content:
  content = content.replace(old_js_poblar, new_js_poblar)

tmpl_path.write_text(content, encoding='utf-8')
print("templates/index.html actualizado con estilo oscuro para selects!")
