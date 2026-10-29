# -*- coding: utf-8 -*-
import re
import sys
from pathlib import Path

def build_template():
    with open('/root/AlgrokQuant/dashboard/templates/index.html.bak_pre_warm_ui', 'r', encoding='utf-8', errors='ignore') as f:
        orig = f.read()

    tab_start_idx = orig.find('<div id="tab-content-dashboard"')
    tab_end_idx = orig.find('</main>')
    
    if tab_start_idx == -1 or tab_end_idx == -1:
        raise ValueError("Could not locate tab content bounds")
        
    tab_panes_html = orig[tab_start_idx:tab_end_idx]
    scripts_html = orig[tab_end_idx + 7:]

    # =========================================================================
    # REEMPLAZO 1: Formato y Acabado Cálido de las 2 tarjetas de Forward Test
    # =========================================================================
    pattern_box_1 = re.compile(
        r'<div class="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2 text-xs font-mono">\s*'
        r'<div class="flex justify-between items-center text-slate-300">\s*'
        r'<span>Posici.*?n Flotante Actual:</span>\s*'
        r'<span class="px-2 py-0\.5 rounded bg-slate-800 text-slate-400 font-bold" id="ft-pf-floating-pos">.*?</span>\s*'
        r'</div>\s*'
        r'<div class="flex justify-between items-center text-slate-400 text-\[11px\]">\s*'
        r'<span>Stop Loss Calibrado:</span>\s*'
        r'<span class="text-slate-400" id="ft-pf-floating-sl">.*?</span>\s*'
        r'</div>\s*'
        r'<div class="flex justify-between items-center text-slate-400 text-\[11px\]">\s*'
        r'<span>Estado de la Operativa:</span>\s*'
        r'<span class="text-cyan-300" id="ft-pf-floating-status">.*?</span>\s*'
        r'</div>\s*'
        r'</div>',
        re.DOTALL
    )

    replacement_box_1 = """<div class="p-3.5 rounded-xl bg-[#FAF7F2] border border-[#E6E2D8] space-y-2.5 text-xs font-mono">
            <div class="flex justify-between items-center text-[#4A4944]">
              <span class="font-medium">Posición Flotante Actual:</span>
              <span class="px-2.5 py-1 rounded-md bg-[#EAE5DC] text-[#181A20] font-bold border border-[#DDD7CD]" id="ft-pf-floating-pos">NINGUNA (Flat / 100% Liquidez)</span>
            </div>
            <div class="flex justify-between items-center text-[#6E6D68] text-[11px]">
              <span>Stop Loss Calibrado:</span>
              <span class="text-[#181A20] font-bold" id="ft-pf-floating-sl">N/A (Sin posición abierta)</span>
            </div>
            <div class="flex justify-between items-center text-[#6E6D68] text-[11px]">
              <span>Estado de la Operativa:</span>
              <span class="text-[#5865F2] font-semibold flex items-center gap-1.5" id="ft-pf-floating-status"><span class="w-1.5 h-1.5 rounded-full bg-[#10b981] animate-pulse inline-block"></span> Escaneando señales de entrada en tiempo real (CME Abierto)</span>
            </div>
          </div>"""

    tab_panes_html = pattern_box_1.sub(replacement_box_1, tab_panes_html)

    # Tarjeta 2: Hyperliquid Testnet (Estrategia Activa info box)
    pattern_box_2 = re.compile(
        r'<div class="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2 text-xs font-mono">\s*'
        r'<div class="flex justify-between items-center text-slate-300">\s*'
        r'<span>Estrategia Activa Principal:</span>\s*'
        r'<span class="text-cyan-300 font-bold">STRAT-028 \(SOL 5m VWAP\)</span>\s*'
        r'</div>\s*'
        r'<div class="flex justify-between items-center text-slate-400 text-\[11px\]">\s*'
        r'<span>Ejecu.*?n:</span>\s*'
        r'<span class="text-emerald-400">Microestructura de comisiones 0\.14% verificada</span>\s*'
        r'</div>\s*'
        r'<div class="flex justify-between items-center text-slate-400 text-\[11px\]">\s*'
        r'<span>Feed de .*?rdenes:</span>\s*'
        r'<span class="text-slate-300">Websockets Hyperliquid en l.*?nea</span>\s*'
        r'</div>\s*'
        r'</div>',
        re.DOTALL
    )

    replacement_box_2 = """<div class="p-3.5 rounded-xl bg-[#FAF7F2] border border-[#E6E2D8] space-y-2.5 text-xs font-mono">
            <div class="flex justify-between items-center text-[#4A4944]">
              <span class="font-medium">Estrategia Activa Principal:</span>
              <span class="px-2.5 py-1 rounded-md bg-[#EEF2FF] text-[#3730A3] font-bold border border-[#C7D2FE]">STRAT-028 (SOL 5m VWAP)</span>
            </div>
            <div class="flex justify-between items-center text-[#6E6D68] text-[11px]">
              <span>Ejecución:</span>
              <span class="text-[#065F46] font-semibold">Microestructura de comisiones 0.14% verificada</span>
            </div>
            <div class="flex justify-between items-center text-[#6E6D68] text-[11px]">
              <span>Feed de Órdenes:</span>
              <span class="text-[#181A20] font-semibold flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-[#10b981] inline-block"></span> Websockets Hyperliquid en línea</span>
            </div>
          </div>"""

    tab_panes_html = pattern_box_2.sub(replacement_box_2, tab_panes_html)

    # Identificadores para interacción de Forward Test con el selector de Capital Propio vs Fondeo
    tab_panes_html = tab_panes_html.replace(
        '<div class="glass-card rounded-2xl p-5 space-y-4 border-l-4 border-cyan-400 motion-sweep stagger-2 shimmer-active">',
        '<div id="ft-propfirm-card" class="glass-card rounded-2xl p-5 space-y-4 border-l-4 border-cyan-400 motion-sweep stagger-2 shimmer-active" style="transition: all 0.3s ease;">'
    )
    tab_panes_html = tab_panes_html.replace(
        '<div class="glass-card rounded-2xl p-5 space-y-4 border-l-4 border-amber-400 motion-sweep stagger-3 shimmer-active">',
        '<div id="ft-hyperliquid-card" class="glass-card rounded-2xl p-5 space-y-4 border-l-4 border-amber-400 motion-sweep stagger-3 shimmer-active" style="transition: all 0.3s ease;">'
    )

    # Actualización en JS de la función fetchForwardState para badges y estado cálidos
    pattern_js_dynamic = re.compile(
        r'if \(posEl\) posEl\.innerHTML = `<span class="px-2 py-0\.5 rounded bg-purple-500/20 text-purple-300 font-bold">\$\{sym\} \$\{pos\.side \|\| \'LONG\'\} \(\$\{Number\(pos\.shares\)\.toFixed\(2\)\} sh @ \$\$\{Number\(pos\.entry_price\)\.toFixed\(2\)\}\)</span>`;\s*'
        r'if \(slEl\) slEl\.innerText = \'\$\' \+ Number\(pos\.sl_price\)\.toFixed\(2\) \+ \' USD\';\s*'
        r'if \(statusEl\) statusEl\.innerHTML = \'<span class="text-emerald-400 font-bold">Posici.*?n viva en mercado.*?</span>\';\s*'
        r'\} else \{\s*'
        r'if \(posEl\) posEl\.innerHTML = \'<span class="px-2 py-0\.5 rounded bg-slate-800 text-slate-400 font-bold">NINGUNA \(Flat / 100% Liquidez\)</span>\';\s*'
        r'if \(slEl\) slEl\.innerText = \'N/A \(Sin posici.*?n abierta\)\';\s*'
        r'if \(statusEl\) statusEl\.innerHTML = \'<span class="text-cyan-400">Escaneando se.*?ales de entrada en tiempo real \(CME Abierto\)</span>\';\s*'
        r'\}',
        re.DOTALL
    )

    replacement_js_dynamic = """if (posEl) posEl.innerHTML = `<span class="px-2.5 py-1 rounded-md bg-[#EEF2FF] text-[#3730A3] font-bold border border-[#C7D2FE]">${sym} ${pos.side || 'LONG'} (${Number(pos.shares).toFixed(2)} sh @ $${Number(pos.entry_price).toFixed(2)})</span>`;
            if (slEl) slEl.innerText = '$' + Number(pos.sl_price).toFixed(2) + ' USD';
            if (statusEl) statusEl.innerHTML = '<span class="text-[#065F46] font-bold flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-[#10b981] animate-pulse inline-block"></span> Posición viva en mercado — Gestión activa de SL</span>';
          } else {
            if (posEl) posEl.innerHTML = '<span class="px-2.5 py-1 rounded-md bg-[#EAE5DC] text-[#181A20] font-bold border border-[#DDD7CD]">NINGUNA (Flat / 100% Liquidez)</span>';
            if (slEl) slEl.innerText = 'N/A (Sin posición abierta)';
            if (statusEl) statusEl.innerHTML = '<span class="text-[#5865F2] font-semibold flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-[#10b981] animate-pulse inline-block"></span> Escaneando señales de entrada en tiempo real (CME Abierto)</span>';
          }"""

    scripts_html = pattern_js_dynamic.sub(replacement_js_dynamic, scripts_html)

    # =========================================================================
    # REEMPLAZO 2: Nueva Estructura HTML para la pestaña TradingView
    # (TradingView Pro con Herramientas de Dibujo + Auditoría Algorítmica)
    # =========================================================================
    chart_tab_start = tab_panes_html.find('<div id="tab-content-chart"')
    if chart_tab_start != -1:
        tab_panes_before_chart = tab_panes_html[:chart_tab_start]
    else:
        tab_panes_before_chart = tab_panes_html

    new_chart_tab_html = """    <!-- ==================== TAB: TRADINGVIEW CHARTING & AUDIT ==================== -->
    <div id="tab-content-chart" class="tab-pane hidden space-y-6">
      
      <!-- Barra Superior de Control, Filtros y Conmutador de Modos -->
      <div class="bg-card border border-borderWarm rounded-2xl p-5 shadow-sm space-y-4">
        
        <!-- Fila 1: Título y Selector de Modo de Gráfico -->
        <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-3 border-b border-borderWarm">
          <div>
            <div class="overline-text">ESTACIÓN DE ANÁLISIS TÉCNICO Y AUDITORÍA</div>
            <h3 class="text-base font-bold text-txtPrimary flex items-center gap-2 mt-0.5">
              <i class="fa-solid fa-chart-candlestick text-[#5865F2]"></i> Gráficos TradingView & Auditoría de Modelos
            </h3>
          </div>

          <!-- Selector de Modo: Pro con herramientas de dibujo vs Auditoría Cuantitativa -->
          <div class="segmented-control">
            <button id="tv-mode-btn-pro" onclick="setTvDisplayMode('PRO')" class="segmented-pill active">
              <i class="fa-solid fa-pen-ruler text-[11px] text-[#5865F2]"></i>
              <span>TradingView Pro (Herramientas de Dibujo)</span>
            </button>
            <button id="tv-mode-btn-audit" onclick="setTvDisplayMode('AUDIT')" class="segmented-pill">
              <i class="fa-solid fa-microchip text-[11px]"></i>
              <span>Auditoría Algorítmica (Trades & Reglas)</span>
            </button>
          </div>
        </div>

        <!-- Fila 2: Selectores de Estrategia, Operación y Controles -->
        <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          
          <!-- Selector de Estrategia -->
          <div class="flex flex-wrap items-center gap-3">
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold text-txtSecondary uppercase tracking-wider flex items-center gap-1.5">
                <i class="fa-solid fa-robot text-[#5865F2]"></i> Estrategia:
              </span>
              <select id="tv-strategy-select" onchange="changeTvStrategy(this.value)" class="text-xs font-mono font-semibold cursor-pointer max-w-[380px] truncate px-3 py-1.5 rounded-lg border border-borderWarm bg-surface text-txtPrimary focus:border-[#5865F2] outline-none shadow-sm">
                <!-- Se poblará dinámicamente con todas las estrategias según modo -->
              </select>
            </div>

            <!-- Badges Informativos del Activo -->
            <div class="flex items-center gap-2">
              <span id="tv-badge-asset" class="badge-brand-indigo font-mono">BTC/USDT</span>
              <span id="tv-badge-tf" class="badge-neutral-soft font-mono">1h</span>
              <span id="tv-badge-type" class="badge-success-live">Capital Propio</span>
            </div>
          </div>

          <!-- Navegador de Operaciones (Jump to Trade) -->
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs font-bold text-txtSecondary uppercase tracking-wider flex items-center gap-1">
              <i class="fa-solid fa-crosshairs text-rose-500"></i> Operación:
            </span>
            <div class="flex items-center bg-[#EAE5DC]/60 border border-borderWarm rounded-xl p-1 gap-1.5">
              <button onclick="navigateTvTrade(-1)" class="w-7 h-7 flex items-center justify-center hover:bg-white rounded-lg text-txtSecondary hover:text-txtPrimary text-xs transition shadow-xs" title="Operación Anterior">
                <i class="fa-solid fa-chevron-left text-[11px]"></i>
              </button>
              <select id="tv-trade-select" onchange="jumpToTvTrade(this.value)" class="text-xs font-mono font-medium min-w-[280px] max-w-[360px] cursor-pointer px-2 py-1 rounded bg-white border border-borderWarm text-txtPrimary outline-none">
                <option value="">Seleccionar Operación...</option>
              </select>
              <button onclick="navigateTvTrade(1)" class="w-7 h-7 flex items-center justify-center hover:bg-white rounded-lg text-txtSecondary hover:text-txtPrimary text-xs transition shadow-xs" title="Siguiente Operación">
                <i class="fa-solid fa-chevron-right text-[11px]"></i>
              </button>
            </div>

            <button onclick="resetTvChartZoom()" class="px-3 py-1.5 rounded-xl text-xs font-bold bg-[#EAE5DC] hover:bg-[#E2DCD2] border border-borderWarm text-txtPrimary transition flex items-center gap-1.5" title="Restablecer zoom al contenido completo">
              <i class="fa-solid fa-expand text-txtSecondary"></i> Reset
            </button>
          </div>

        </div>

        <!-- Leyenda Activa de Indicadores Superpuestos -->
        <div id="tv-indicators-legend" class="pt-2 border-t border-borderWarm flex flex-wrap items-center justify-between gap-3 text-xs">
          <div class="flex flex-wrap items-center gap-2">
            <span class="overline-text text-[10px]">Indicadores Activos:</span>
            <div id="tv-indicator-badges" class="flex flex-wrap gap-2 items-center"></div>
          </div>
          <span class="text-[11px] text-txtSecondary font-medium" id="tv-sync-note">
            <i class="fa-solid fa-circle-check text-emerald-600 mr-1"></i> Sincronizado con base de datos cuantitativa en tiempo real
          </span>
        </div>

      </div>

      <!-- ==================== VISTA 1: TRADINGVIEW PRO (HERRAMIENTAS OFICIALES DE DIBUJO) ==================== -->
      <div id="tv-mode-pro-container" class="space-y-4">
        <div class="bg-card border border-borderWarm rounded-2xl p-4 shadow-sm relative overflow-hidden">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3 px-1 text-xs">
            <div class="flex items-center gap-2 text-txtPrimary font-medium">
              <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span class="font-bold">Barra Lateral de Herramientas de Dibujo Activa</span>
              <span class="text-txtSecondary">·</span>
              <span class="text-txtSecondary">Líneas de tendencia, canales, retrocesos Fibonacci, pincel, textos y reglas</span>
            </div>
            <div class="flex items-center gap-2 text-txtSecondary text-[11px]">
              <i class="fa-solid fa-circle-info text-[#5865F2]"></i>
              <span>Personaliza colores de velas, fondo y escalas con clic derecho &rarr; Configuración</span>
            </div>
          </div>

          <!-- Contenedor Oficial del Widget TradingView con Barra de Herramientas de Dibujo -->
          <div id="tv-pro-widget-container" class="w-full h-[650px] rounded-xl overflow-hidden border border-borderWarm bg-[#131722]">
            <!-- Inyectado vía TradingView.widget -->
          </div>
        </div>
      </div>

      <!-- ==================== VISTA 2: AUDITORÍA CUANTITATIVA (LIGHTWEIGHT CHARTS + MARCADORES) ==================== -->
      <div id="tv-mode-audit-container" class="space-y-4 hidden">
        
        <!-- Barra de Herramientas de Edición Rápida y Personalización de Colores -->
        <div class="bg-card border border-borderWarm rounded-xl p-3 shadow-sm flex flex-wrap items-center justify-between gap-3 text-xs">
          <div class="flex items-center gap-3 flex-wrap">
            <span class="overline-text">HERRAMIENTAS DE EDICIÓN:</span>
            
            <button onclick="addTvHorizontalLine()" class="px-2.5 py-1 rounded-lg bg-surface border border-borderWarm hover:bg-[#EAE5DC] text-txtPrimary font-medium flex items-center gap-1.5 transition shadow-xs" title="Añadir nivel de precio o soporte/resistencia">
              <i class="fa-solid fa-ruler-horizontal text-[#5865F2]"></i> + Línea Horizontal
            </button>

            <button onclick="clearTvCustomLines()" class="px-2.5 py-1 rounded-lg bg-surface border border-borderWarm hover:bg-rose-50 text-rose-600 font-medium flex items-center gap-1.5 transition shadow-xs" title="Eliminar líneas personalizadas">
              <i class="fa-solid fa-eraser"></i> Limpiar Líneas
            </button>
          </div>

          <div class="flex items-center gap-4 flex-wrap">
            <div class="flex items-center gap-1.5 text-txtSecondary font-medium">
              <span>Vela Alcista:</span>
              <input type="color" id="tv-candle-color-up" value="#10b981" onchange="applyTvCustomColors()" class="w-6 h-6 rounded cursor-pointer border border-borderWarm p-0" title="Color de velas alcistas">
            </div>

            <div class="flex items-center gap-1.5 text-txtSecondary font-medium">
              <span>Vela Bajista:</span>
              <input type="color" id="tv-candle-color-down" value="#ef4444" onchange="applyTvCustomColors()" class="w-6 h-6 rounded cursor-pointer border border-borderWarm p-0" title="Color de velas bajistas">
            </div>

            <div class="flex items-center gap-1.5 text-txtSecondary font-medium">
              <span>Fondo Gráfico:</span>
              <select id="tv-chart-bg-theme" onchange="toggleTvChartTheme(this.value)" class="text-xs px-2 py-0.5 rounded border border-borderWarm bg-surface text-txtPrimary font-medium">
                <option value="dark">Oscuro (#090D16)</option>
                <option value="light">Marfil Cálido (#FAF7F2)</option>
              </select>
            </div>
          </div>
        </div>

        <div class="bg-card border border-borderWarm rounded-2xl p-4 shadow-sm relative overflow-hidden">
          
          <!-- Estado de Carga -->
          <div id="tv-loading-overlay" class="absolute inset-0 bg-surface/85 backdrop-blur-sm z-30 flex flex-col items-center justify-center gap-3">
            <div class="w-8 h-8 border-3 border-[#5865F2] border-t-transparent rounded-full animate-spin"></div>
            <p class="text-xs font-mono text-[#5865F2] font-semibold">Cargando velas OHLCV e indicadores TradingView...</p>
          </div>

          <!-- Gráfico 1: Velas Principales + Overlays -->
          <div class="relative">
            <div class="flex justify-between items-center mb-2 px-1">
              <span class="text-xs font-mono font-bold text-txtPrimary flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> Gráfico de Precios & Overlays (Velas OHLCV)
              </span>
              <span id="tv-hover-info" class="text-xs font-mono text-txtSecondary">Pasa el cursor por las velas</span>
            </div>
            <div id="tv-main-chart-container" class="w-full h-[480px] bg-[#090d16] rounded-xl overflow-hidden border border-borderWarm"></div>
          </div>

          <!-- Gráfico 2: Sub-Panel Osciladores -->
          <div class="mt-3 pt-3 border-t border-borderWarm">
            <div class="flex justify-between items-center mb-1.5 px-1">
              <span id="tv-subchart-title" class="text-xs font-mono font-bold text-txtPrimary flex items-center gap-1.5">
                <i class="fa-solid fa-wave-square text-rose-500"></i> Sub-Panel de Régimen (Entropía de Shannon & Flujo)
              </span>
              <span class="text-[11px] font-mono text-txtSecondary">Escala de tiempo sincronizada 1:1 con el precio</span>
            </div>
            <div id="tv-sub-chart-container" class="w-full h-[180px] bg-[#090d16] rounded-xl overflow-hidden border border-borderWarm"></div>
          </div>

        </div>

        <!-- Inspector Detallado de Operación Seleccionada -->
        <div id="tv-trade-inspector" class="bg-card border border-borderWarm rounded-2xl p-5 shadow-sm hidden">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-borderWarm pb-4 mb-4">
            <div class="flex items-center gap-3">
              <div id="tv-inspect-icon" class="w-10 h-10 rounded-xl flex items-center justify-center text-lg font-bold"></div>
              <div>
                <div class="flex items-center gap-2">
                  <h4 id="tv-inspect-id" class="text-sm font-bold text-txtPrimary font-mono">TR-001</h4>
                  <span id="tv-inspect-type" class="px-2 py-0.5 rounded text-[11px] font-bold font-mono">LONG</span>
                  <span id="tv-inspect-badge" class="px-2 py-0.5 rounded text-[11px] font-bold font-mono">WIN</span>
                </div>
                <p id="tv-inspect-timing" class="text-xs text-txtSecondary font-mono mt-0.5"></p>
              </div>
            </div>
            <div class="flex items-center gap-4 text-right">
              <div>
                <p class="overline-text text-[10px]">Rentabilidad Neta</p>
                <p id="tv-inspect-pnl" class="text-lg font-bold font-mono text-emerald-600">+1.56%</p>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div class="bg-[#FAF7F2] p-3 rounded-xl border border-borderWarm">
              <p class="overline-text text-[10px]">Precio Entrada</p>
              <p id="tv-inspect-entry" class="text-sm font-bold text-txtPrimary font-mono mt-0.5">$65,923.21</p>
            </div>
            <div class="bg-[#FAF7F2] p-3 rounded-xl border border-borderWarm">
              <p class="overline-text text-[10px]">Precio Salida</p>
              <p id="tv-inspect-exit" class="text-sm font-bold text-txtPrimary font-mono mt-0.5">$66,953.61</p>
            </div>
            <div class="bg-[#FAF7F2] p-3 rounded-xl border border-borderWarm">
              <p class="overline-text text-[10px]">Stop Loss</p>
              <p id="tv-inspect-sl" class="text-sm font-bold text-rose-600 font-mono mt-0.5">$64,800.00</p>
            </div>
            <div class="bg-[#FAF7F2] p-3 rounded-xl border border-borderWarm">
              <p class="overline-text text-[10px]">Take Profit</p>
              <p id="tv-inspect-tp" class="text-sm font-bold text-emerald-600 font-mono mt-0.5">$68,500.00</p>
            </div>
          </div>
        </div>

      </div>

    </div>
"""

    tab_panes_html = tab_panes_before_chart + new_chart_tab_html

    # Reemplazo 2b: Enjambre subtitle y tabla de catálogo headers
    tab_panes_html = tab_panes_html.replace(
        'con motor <strong class="text-brand-300">Gemini 3.8 Flash High</strong> (sin límites de tokens ni costes de X/Grok).',
        'con arquitectura optimizada: <strong class="text-amber-500 font-bold">Gemini 3.8 Flash High</strong> (Razonamiento & Cuant) y <strong class="text-emerald-500 font-bold">Gemini 3.8 Flash Low</strong> (Supervisión & Ejecución).'
    )
    tab_panes_html = tab_panes_html.replace(
        '<th class="py-3 px-4 text-right">Acción</th>',
        '<th class="py-3 px-4 text-center">Ver Ficha</th>'
    )

    # =========================================================================
    # REEMPLAZO 3: Script Completo del Controlador TradingView & Segmented Desk
    # =========================================================================
    tv_script_marker = scripts_html.find('let tvMainChart = null')
    if tv_script_marker != -1:
        script_tag_start = scripts_html.rfind('<script', 0, tv_script_marker)
        comment_marker = scripts_html.rfind('<!-- ===', 0, script_tag_start)
        cut_point = comment_marker if comment_marker != -1 else script_tag_start
        scripts_before_tv = scripts_html[:cut_point]
    else:
        scripts_before_tv = scripts_html

    # Reemplazo 2c: Motor badge en tarjetas de enjambre
    old_roster_engine = re.compile(
        r'<div class="flex justify-between text-slate-500">\s*'
        r'<span>Motor:</span>\s*'
        r'<span class="text-brand-300 font-bold">\$\{agent\.engine\}</span>\s*'
        r'</div>'
    )
    new_roster_engine = """<div class="flex justify-between items-center text-slate-500 pt-1">
                <span>Motor:</span>
                ${(agent.engine || '').includes('High')
                  ? `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30 whitespace-nowrap"><i class="fa-solid fa-brain mr-1 text-[9px]"></i>${agent.engine}</span>`
                  : `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 whitespace-nowrap"><i class="fa-solid fa-bolt mr-1 text-[9px]"></i>${agent.engine}</span>`
                }
              </div>"""
    scripts_before_tv = old_roster_engine.sub(new_roster_engine, scripts_before_tv)

    # Reemplazo 2d: renderStrategiesTable en Catálogo de Modelos (Linaje continuo, Pendiente limpio, Ver Ficha botón)
    old_render_strat = re.compile(
        r'function renderStrategiesTable\(strategies\)\s*\{[\s\S]*?tbody\.appendChild\(tr\);\s*\}\);\s*\}',
        re.DOTALL
    )
    new_render_strat = """function renderStrategiesTable(strategies) {
      const tbody = document.getElementById('strategies-table-body');
      tbody.innerHTML = '';
      strategies.forEach((s, index) => {
        const rawStatus = (s.status || '').toUpperCase();
        const isApproved = rawStatus.includes('APROBADA');
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-900/40 transition motion-sweep';
        const delay = Math.min((index + 1) * 0.02, 0.4);
        tr.style.animationDelay = delay + 's';

        // Badge de Linaje / Origen: SIEMPRE continuo en una sola línea (whitespace-nowrap)
        const isHybrid = s.source_type === 'HYBRID_VECTORBT';
        const provenanceBadge = isHybrid
          ? `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap bg-purple-500/15 text-purple-300 border border-purple-500/30" title="Exploración en meseta paramétrica VectorBT"><i class="fa-solid fa-microchip text-[11px]"></i> Híbrido VectorBT</span>`
          : `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap bg-cyan-500/15 text-cyan-300 border border-cyan-500/30" title="Lógica heurística cualitativa de agente"><i class="fa-solid fa-brain text-[11px]"></i> Agente Heurístico</span>`;

        // Métricas OOS y Estancamiento
        const oosInfo = s.oos_r_dd ? `
          <div class="flex items-center space-x-1.5 whitespace-nowrap">
            <span class="text-white font-bold">${s.oos_r_dd.oos_r_dd}</span>
            <span class="text-[10px] ${s.oos_r_dd.degradation_pct < -30 ? 'text-amber-400' : 'text-emerald-400'} font-mono">(${s.oos_r_dd.degradation_pct}%)</span>
          </div>
        ` : `<span class="text-slate-500">-</span>`;

        const stagInfo = s.stagnation_days ? `
          <span class="text-slate-300 font-mono font-medium whitespace-nowrap">${s.stagnation_days}d</span>
        ` : `<span class="text-slate-500">-</span>`;

        // Badge de Estado: "Pendiente" o "Aprobada" limpio sin sufijos ni guiones
        const statusBadge = isApproved
          ? `<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 inline-block"></span>Aprobada</span>`
          : `<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap bg-amber-500/15 text-amber-400 border border-amber-500/30"><span class="w-1.5 h-1.5 rounded-full bg-amber-400 mr-1.5 inline-block"></span>Pendiente</span>`;

        tr.innerHTML = `
          <td class="py-3 px-4 font-bold text-white whitespace-nowrap">${s.id}</td>
          <td class="py-3 px-4 whitespace-nowrap"><span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-bold">${s.asset}</span> <span class="text-slate-400 text-[11px]">${s.timeframe}</span></td>
          <td class="py-3 px-4 whitespace-nowrap">${provenanceBadge}</td>
          <td class="py-3 px-4 text-emerald-400 font-bold whitespace-nowrap">${s.win_rate}%</td>
          <td class="py-3 px-4 text-white whitespace-nowrap">${s.profit_factor}</td>
          <td class="py-3 px-4 whitespace-nowrap">${oosInfo}</td>
          <td class="py-3 px-4 whitespace-nowrap">${stagInfo}</td>
          <td class="py-3 px-4 text-slate-300 whitespace-nowrap">${s.max_dd}%</td>
          <td class="py-3 px-4 whitespace-nowrap">${statusBadge}</td>
          <td class="py-3 px-4 text-center whitespace-nowrap">
            <button onclick="viewStrategy('${s.id}')" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#FAF7F2] text-[#181A20] hover:bg-[#EAE5DC] transition border border-[#D5D0C5] shadow-xs cursor-pointer font-sans">
              <i class="fa-solid fa-file-lines text-xs text-brand-600"></i> Ver Ficha
            </button>
          </td>
        `;
        tbody.appendChild(tr);
      });
    }"""
    scripts_before_tv = old_render_strat.sub(new_render_strat, scripts_before_tv)

    full_tv_and_desk_script = """  <!-- ============================================================================== -->
  <!-- CONTROLADOR TRADINGVIEW PRO & AUDITORÍA CUANTITATIVA (ALGROKQUANT) -->
  <!-- ============================================================================== -->
  <script>
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

      if (mode === 'PRO') {
        if (proBtn) proBtn.className = 'segmented-pill active';
        if (auditBtn) auditBtn.className = 'segmented-pill';
        if (proCont) proCont.classList.remove('hidden');
        if (auditCont) auditCont.classList.add('hidden');
        const strat = tvStrategiesCatalog.find(s => s.id === tvCurrentStrategyId);
        loadTvProWidget(resolveTvSymbol(tvCurrentStrategyId, strat ? strat.asset : ''));
      } else {
        if (auditBtn) auditBtn.className = 'segmented-pill active';
        if (proBtn) proBtn.className = 'segmented-pill';
        if (auditCont) auditCont.classList.remove('hidden');
        if (proCont) proCont.classList.add('hidden');
        if (!tvMainChart) {
          initTvChartInstances();
        }
        if (tvCurrentStrategyId) {
          changeTvStrategy(tvCurrentStrategyId);
        }
        setTimeout(resizeTvCharts, 120);
      }
    }

    // 2. Cargar Widget Oficial de TradingView con Barra de Herramientas de Dibujo Completa
    function loadTvProWidget(symbol) {
      const container = document.getElementById('tv-pro-widget-container');
      if (!container) return;
      container.innerHTML = '';
      try {
        if (typeof TradingView !== 'undefined') {
          new TradingView.widget({
            "autosize": true,
            "symbol": symbol || "BINANCE:BTCUSDT",
            "interval": "60",
            "timezone": "Europe/Madrid",
            "theme": "dark",
            "style": "1",
            "locale": "es",
            "toolbar_bg": "#131722",
            "enable_publishing": false,
            "allow_symbol_change": true,
            "hide_side_toolbar": false, // ACTIVA LA BARRA LATERAL DE HERRAMIENTAS DE DIBUJO
            "withdateranges": true,
            "hide_top_toolbar": false,
            "save_image": true,
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
      try {
        const res = await fetch('/api/chart_strategies');
        if (!res.ok) return;
        tvStrategiesCatalog = await res.json();
        
        const desk = filterDesk || currentDeskMode;
        const select = document.getElementById('tv-strategy-select');
        if (!select) return;

        let filtered = tvStrategiesCatalog;
        if (desk === 'CAPITAL_PROPIO') {
          filtered = tvStrategiesCatalog.filter(s => 
            (s.type && s.type.toLowerCase().includes('capital propio')) ||
            s.id.startsWith('STRAT-') || s.id.startsWith('CAP-')
          );
        } else if (desk === 'PROP_FIRM') {
          filtered = tvStrategiesCatalog.filter(s => 
            (s.type && s.type.toLowerCase().includes('prop firm')) ||
            s.id.startsWith('PROP-')
          );
        }

        if (filtered.length === 0) filtered = tvStrategiesCatalog;

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
      } catch (err) {
        console.error('Error cargando catálogo TradingView:', err);
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
        const res = await fetch(`/api/chart/${stratId}?bars=1500`);
        if (!res.ok) throw new Error('Error al obtener datos de velas e indicadores');
        const data = await res.json();
        tvCurrentData = data;
        renderTvChartData(data);
      } catch (err) {
        console.error('Error cargando gráfico:', err);
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
            badge.className = 'px-2 py-0.5 rounded text-[11px] font-mono font-bold border flex items-center gap-1.5';
            badge.style.borderColor = ov.color + '40';
            badge.style.backgroundColor = ov.color + '15';
            badge.style.color = ov.color;
            badge.innerHTML = `<span class="w-2 h-2 rounded-full" style="background-color: ${ov.color}"></span> ${ov.name}`;
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
      clearActivePriceLines();
    }

    function clearActivePriceLines() {
      if (tvCandleSeries && tvActivePriceLines.length > 0) {
        tvActivePriceLines.forEach(pl => tvCandleSeries.removePriceLine(pl));
        tvActivePriceLines = [];
      }
    }

    // 9. Herramientas de Edición Interactiva (Líneas Horizontales y Colores)
    function addTvHorizontalLine() {
      if (!tvCandleSeries) return;
      const lastClose = (tvCurrentData && tvCurrentData.candles && tvCurrentData.candles.length > 0)
        ? tvCurrentData.candles[tvCurrentData.candles.length - 1].close
        : 0;
      const priceStr = prompt("Introduce el nivel de precio para la línea de soporte/resistencia:", lastClose);
      if (!priceStr) return;
      const price = parseFloat(priceStr);
      if (isNaN(price)) return;
      const pl = tvCandleSeries.createPriceLine({
        price: price,
        color: '#f59e0b',
        lineWidth: 2,
        lineStyle: 0,
        axisLabelVisible: true,
        title: 'NIVEL: $' + price.toLocaleString()
      });
      tvCustomPriceLines.push(pl);
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

    function toggleTvChartTheme(theme) {
      const bg = theme === 'light' ? '#FAF7F2' : '#090d16';
      const text = theme === 'light' ? '#181A20' : '#94a3b8';
      const grid = theme === 'light' ? 'rgba(230, 226, 216, 0.6)' : 'rgba(30, 41, 59, 0.4)';
      if (tvMainChart) {
        tvMainChart.applyOptions({
          layout: { background: { color: bg }, textColor: text },
          grid: { vertLines: { color: grid }, horzLines: { color: grid } }
        });
      }
      if (tvSubChart) {
        tvSubChart.applyOptions({
          layout: { background: { color: bg }, textColor: text },
          grid: { vertLines: { color: grid }, horzLines: { color: grid } }
        });
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
  </script>

  <!-- ============================================================================== -->
  <!-- CONTROLADOR DEL SIDEBAR Y SELECTOR DE CAPITAL PROPIO VS FONDEO -->
  <!-- ============================================================================== -->
  <script>
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

      // 1. Filtrar las tarjetas de cartera activa superior
      let visibleCount = 0;
      document.querySelectorAll('.strategy-card[data-desk]').forEach(el => {
        if (el.getAttribute('data-desk') === mode) {
          el.style.display = 'flex';
          visibleCount++;
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

      // 2. Filtrar o sincronizar selector en Backtests si existe
      const bFilter = document.getElementById('account-filter-select');
      if (bFilter) {
        bFilter.value = (mode === 'CAPITAL_PROPIO') ? 'CRYPTO-HL' : 'PROP-NDX-005';
        if (typeof onAccountFilterChange === 'function') {
          onAccountFilterChange();
        }
      }

      // 3. Filtrar catálogo de TradingView
      if (typeof fetchTvStrategyCatalog === 'function') {
        fetchTvStrategyCatalog(mode);
      }

      // 4. Sincronizar foco visual en Forward Test
      const ftPfCard = document.getElementById('ft-propfirm-card');
      const ftHlCard = document.getElementById('ft-hyperliquid-card');
      if (ftPfCard && ftHlCard) {
        if (mode === 'CAPITAL_PROPIO') {
          ftHlCard.style.opacity = '1';
          ftPfCard.style.opacity = '0.45';
        } else {
          ftPfCard.style.opacity = '1';
          ftHlCard.style.opacity = '0.45';
        }
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

      // VISIBILIDAD DE CARTERA ACTIVA: Solo en Cockpit General ('dashboard') y Forward Tests en Vivo ('forward')
      const activePortfolio = document.getElementById('active-portfolio-section');
      if (activePortfolio) {
        if (tabId === 'dashboard' || tabId === 'forward') {
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
    });
  </script>

</body>
</html>
"""

    scripts_html = scripts_before_tv + full_tv_and_desk_script

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ALGROK QUANT · Institutional Quantitative Desk</title>

  <!-- Google Fonts: Plus Jakarta Sans & JetBrains Mono -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">

  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          colors: {{
            canvas: '#F5EFE6',
            sidebar: '#EFECE6',
            surface: '#FDFDFB',
            card: '#FFFFFF',
            muted: '#EAE5DC',
            primary: '#181A20',
            brand: '#5865F2',
            warning: '#C86D3B',
            borderWarm: '#E6E2D8',
            borderDashed: '#B5B2A8',
            txtPrimary: '#181A20',
            txtSecondary: '#6E6D68',
            txtMuted: '#9E9C94',
          }},
          fontFamily: {{
            sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
            mono: ['"JetBrains Mono"', 'monospace']
          }}
        }}
      }}
    }}
  </script>

  <!-- ApexCharts & Marked.js CDN -->
  <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

  <!-- FontAwesome 6 Pro Icons -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

  <style>
    /* ==========================================================================
       WARM MINIMALIST & TACTILE UI - PALETA Y ALTO CONTRASTE
       ========================================================================== */
    :root {{
      --canvas-bg: #F5EFE6;
      --sidebar-bg: #EFECE6;
      --main-surface: #FDFDFB;
      --card-surface: #FFFFFF;
      --surface-muted: #EAE5DC;
      --primary-accent: #181A20;
      --brand-accent: #5865F2;
      --warning-text: #9A3412;
      --text-primary: #181A20;
      --text-secondary: #4A4944;
      --text-muted: #7E7C74;
      --border-solid: #E6E2D8;
      --border-dashed: #B5B2A8;
      --shadow-shell: 0 20px 50px rgba(24, 26, 32, 0.08);
      --shadow-card: 0 4px 14px rgba(24, 26, 32, 0.04);
      --font-sans: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    body {{
      background-color: var(--canvas-bg);
      color: var(--text-primary);
      font-family: var(--font-sans);
      margin: 0;
      padding: 0;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }}

    /* Tipografía y Escala */
    .overline-text {{
      font-size: 10px;
      text-transform: uppercase;
      font-weight: 700;
      letter-spacing: 0.08em;
      color: #6E6D68;
    }}

    h1.panel-title {{
      font-size: 22px;
      font-weight: 700;
      line-height: 1.2;
      color: var(--text-primary);
      letter-spacing: -0.02em;
    }}

    h2.card-title {{
      font-size: 15px;
      font-weight: 700;
      color: var(--text-primary);
      font-feature-settings: "tnum";
      font-variant-numeric: tabular-nums;
    }}

    .hero-metric {{
      font-size: 24px;
      font-weight: 800;
      color: var(--text-primary);
      font-feature-settings: "tnum";
      font-variant-numeric: tabular-nums;
      letter-spacing: -0.03em;
    }}

    .body-btn-text {{
      font-size: 13px;
      font-weight: 600;
    }}

    .caption-detail {{
      font-size: 11px;
      font-weight: 500;
      color: var(--text-secondary);
    }}

    /* Menú Lateral: Enlaces de Navegación con Alto Contraste */
    .sidebar-link {{
      color: #181A20 !important;
      font-weight: 600 !important;
      font-size: 13px !important;
      transition: all 0.2s ease;
      border: 1px solid transparent;
      border-radius: 10px;
      text-decoration: none;
      display: flex;
      align-items: center;
      width: 100%;
      padding: 9px 12px;
      background: transparent;
      cursor: pointer;
    }}

    .sidebar-link:hover {{
      background-color: #E2DCD2 !important;
      color: #181A20 !important;
    }}

    .sidebar-link.active {{
      background-color: var(--primary-accent) !important;
      color: #FFFFFF !important;
      box-shadow: 0 4px 12px rgba(24, 26, 32, 0.15) !important;
    }}

    .sidebar-link.active i {{
      color: #5865F2 !important;
    }}

    /* Tarjetas Uniformes y Coherentes (100% Homogéneas) */
    .strategy-card {{
      background: var(--card-surface);
      border: 1px solid var(--border-solid);
      border-radius: 16px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-height: 154px;
      box-shadow: var(--shadow-card);
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .strategy-card:hover {{
      border-color: var(--primary-accent);
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(24, 26, 32, 0.08);
    }}

    /* Sistema de Badges con Contraste AAA / AA Riguroso */
    .badge-solid-dark {{
      background-color: #181A20 !important;
      color: #FFFFFF !important;
      border: 1px solid #181A20 !important;
      font-weight: 700;
      font-size: 10px;
      padding: 2px 8px;
      border-radius: 6px;
      letter-spacing: 0.02em;
    }}

    .badge-brand-indigo {{
      background-color: #EEF2FF !important;
      color: #3730A3 !important;
      border: 1px solid #C7D2FE !important;
      font-weight: 700;
      font-size: 10px;
      padding: 2px 8px;
      border-radius: 6px;
    }}

    .badge-success-live {{
      background-color: #ECFDF5 !important;
      color: #065F46 !important;
      border: 1px solid #A7F3D0 !important;
      font-weight: 700;
      font-size: 10px;
      padding: 2px 8px;
      border-radius: 6px;
    }}

    .badge-warning-risk {{
      background-color: #FFF7ED !important;
      color: #9A3412 !important;
      border: 1px solid #FED7AA !important;
      font-weight: 700;
      font-size: 10px;
      padding: 2px 8px;
      border-radius: 6px;
    }}

    .badge-neutral-soft {{
      background-color: #F3EFEA !important;
      color: #181A20 !important;
      border: 1px solid #DDD7CD !important;
      font-weight: 700;
      font-size: 10px;
      padding: 2px 8px;
      border-radius: 6px;
    }}

    /* Segmented Control */
    .segmented-control {{
      background: var(--surface-muted);
      border-radius: 12px;
      padding: 4px;
      display: flex;
      gap: 4px;
    }}

    .segmented-pill {{
      padding: 6px 12px;
      border-radius: 9px;
      font-size: 12px;
      font-weight: 600;
      color: #4A4944;
      transition: all 0.2s ease;
      cursor: pointer;
      border: none;
      background: transparent;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }}

    .segmented-pill.active {{
      background: var(--card-surface);
      color: var(--text-primary);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
    }}

    /* Botón CTA Principal */
    .cta-primary-btn {{
      background: var(--primary-accent);
      color: #FFFFFF;
      border-radius: 9999px;
      font-size: 13px;
      font-weight: 600;
      padding: 10px 20px;
      border: none;
      cursor: pointer;
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      box-shadow: 0 4px 12px rgba(24, 26, 32, 0.12);
    }}

    .cta-primary-btn:hover {{
      background: #2b2e38;
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba(24, 26, 32, 0.18);
    }}

    /* Normalización global para tablas y contenido heredado */
    .glass-card, .tab-pane .glass-card {{
      background: var(--card-surface) !important;
      border: 1px solid var(--border-solid) !important;
      border-radius: 16px !important;
      box-shadow: var(--shadow-card) !important;
      color: var(--text-primary) !important;
    }}

    .bg-dark-950, .bg-dark-950\\/60, .bg-dark-950\\/80, .bg-dark-950\\/90 {{
      background-color: var(--surface-muted) !important;
      color: var(--text-primary) !important;
    }}

    .bg-dark-900, .bg-dark-900\\/60, .bg-dark-900\\/80, .bg-dark-900\\/90 {{
      background-color: var(--card-surface) !important;
      border-color: var(--border-solid) !important;
      color: var(--text-primary) !important;
    }}

    /* Eliminación total de fondos oscuros / inacabados heredados */
    .bg-slate-900, .bg-slate-900\\/60, .bg-slate-900\\/80, .bg-slate-900\\/90, .bg-slate-900\\/40, .bg-slate-900\\/70 {{
      background-color: #FAF7F2 !important;
      border-color: var(--border-solid) !important;
      color: var(--text-primary) !important;
    }}

    .bg-slate-800, .bg-slate-800\\/60, .bg-slate-800\\/80, .bg-slate-800\\/90 {{
      background-color: #EAE5DC !important;
      border-color: var(--border-solid) !important;
      color: var(--text-primary) !important;
    }}

    .border-slate-800, .border-slate-800\\/80, .border-slate-800\\/90, .border-slate-700 {{
      border-color: var(--border-solid) !important;
    }}

    .text-white {{
      color: var(--text-primary) !important;
    }}

    .text-slate-400, .text-slate-300, .text-slate-500 {{
      color: var(--text-secondary) !important;
    }}

    .text-cyan-400, .text-cyan-300, .text-brand-500, .text-brand-600 {{
      color: var(--brand-accent) !important;
    }}

    .text-emerald-400, .text-emerald-300 {{
      color: #065F46 !important;
    }}

    .text-rose-400, .text-rose-300 {{
      color: #9A3412 !important;
    }}

    table thead {{
      background-color: var(--sidebar-bg) !important;
      color: var(--text-primary) !important;
      border-color: var(--border-solid) !important;
    }}

    table tbody tr {{
      border-color: var(--border-solid) !important;
      background-color: var(--card-surface) !important;
      color: var(--text-primary) !important;
    }}

    table tbody tr:hover {{
      background-color: #FAF7F2 !important;
    }}

    select, input, textarea {{
      background-color: var(--card-surface) !important;
      color: var(--text-primary) !important;
      border: 1px solid var(--border-solid) !important;
      border-radius: 10px !important;
    }}

    select:focus, input:focus, textarea:focus {{
      border-color: var(--brand-accent) !important;
      outline: none !important;
      box-shadow: 0 0 0 3px rgba(88, 101, 242, 0.15) !important;
    }}
  </style>

  <!-- TradingView Official Advanced Charts Script -->
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>

  <!-- TradingView Lightweight Charts CDN Oficial -->
  <script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
</head>

<body class="p-2 sm:p-5 lg:p-8">

  <!-- ==========================================================================
       APP SHELL PRINCIPAL (Max-width 1240px, centrado, radius 24px, sombra suave)
       ========================================================================== -->
  <div class="max-w-[1240px] mx-auto rounded-[24px] shadow-[0_20px_50px_rgba(24,26,32,0.08)] overflow-hidden border border-[#E6E2D8] bg-[#FDFDFB] flex flex-col lg:grid lg:grid-cols-[280px_1fr] min-h-[92vh]">

    <!-- ==================== SIDEBAR IZQUIERDO (#EFECE6, padding 24px) ==================== -->
    <aside class="bg-[#EFECE6] p-6 border-b lg:border-b-0 lg:border-r border-[#E6E2D8] flex flex-col justify-between select-none">
      
      <div>
        <!-- Logo en contenedor cuadrado blanco (40x40px, radius 12px) + Cabecera -->
        <div class="flex items-center space-x-3.5 mb-6">
          <div class="w-10 h-10 rounded-[12px] bg-[#FFFFFF] border border-[#E6E2D8] flex items-center justify-center shadow-sm flex-shrink-0">
            <i class="fa-solid fa-chart-line text-[#5865F2] text-lg"></i>
          </div>
          <div>
            <div class="overline-text">MESA INSTITUCIONAL</div>
            <h1 class="panel-title">ALGROK <span class="text-[#5865F2]">QUANT</span></h1>
          </div>
        </div>

        <!-- Segmented Control de 2 opciones (Capital Propio vs Fondeo Prop Firm) -->
        <div class="segmented-control mb-6">
          <button id="seg-btn-cap-propio" onclick="switchDeskMode('CAPITAL_PROPIO')" class="segmented-pill active flex-1">
            <i class="fa-solid fa-gem text-[10px] text-[#5865F2]"></i> Capital Propio
          </button>
          <button id="seg-btn-prop-firm" onclick="switchDeskMode('PROP_FIRM')" class="segmented-pill flex-1">
            <i class="fa-solid fa-building-columns text-[10px]"></i> Fondeo
          </button>
        </div>

        <!-- Menú Lateral: ÚNICA navegación de toda la plataforma -->
        <div class="overline-text px-1 mb-2">MÓDULOS DE OPERACIÓN</div>
        <nav class="space-y-1" id="sidebar-nav">
          
          <button onclick="switchTab('dashboard')" id="side-tab-dashboard" class="sidebar-link active">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span>Cockpit General</span>
          </button>

          <button onclick="switchTab('backtests')" id="side-tab-backtests" class="sidebar-link">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span>1. Backtests (Multi-Horizonte)</span>
          </button>

          <button onclick="switchTab('forward')" id="side-tab-forward" class="sidebar-link">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span>2. Forward Tests (En Vivo)</span>
          </button>

          <button onclick="switchTab('tri_facet')" id="side-tab-tri_facet" class="sidebar-link">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span>3. Contraste Tri-Faceta</span>
          </button>

          <button onclick="switchTab('roster')" id="side-tab-roster" class="sidebar-link">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span>Enjambre (10 Agentes)</span>
          </button>

          <button onclick="switchTab('lab')" id="side-tab-lab" class="sidebar-link">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span>Creación & Lab (VectorBT)</span>
          </button>

          <button onclick="switchTab('chart')" id="side-tab-chart" class="sidebar-link">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span>Gráficos TradingView</span>
          </button>

          <button onclick="switchTab('strategies')" id="side-tab-strategies" class="sidebar-link">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span>Catálogo de Modelos</span>
          </button>

          <button onclick="switchTab('config')" id="side-tab-config" class="sidebar-link">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span>Reglas de Riesgo</span>
          </button>

          <button onclick="switchTab('journal')" id="side-tab-journal" class="sidebar-link">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span>Bitácora & Informes</span>
          </button>

        </nav>
      </div>

      <!-- Widget Inferior de Control Secundario -->
      <div class="mt-8 pt-4 border-t border-[#E6E2D8]">
        <div class="bg-[#FFFFFF] border border-[#E6E2D8] rounded-[16px] p-4 shadow-sm space-y-3">
          <div class="flex items-center justify-between">
            <span class="overline-text">TELEMETRÍA EN VIVO</span>
            <span class="badge-success-live">CONECTADO</span>
          </div>
          
          <div class="space-y-1.5 text-xs font-mono">
            <div class="flex justify-between items-center text-[#4A4944]">
              <span>IC Markets MT5:</span>
              <span class="font-bold text-[#181A20]" id="tele-mt5-bal">$999.51 USD</span>
            </div>
            <div class="flex justify-between items-center text-[#4A4944]">
              <span>Hyperliquid DEX:</span>
              <span class="font-bold text-[#181A20]" id="tele-hl-bal">1,000.66 USDC</span>
            </div>
            <div class="pt-1.5 border-t border-[#E6E2D8] flex justify-between items-center">
              <span class="text-[11px] font-semibold text-[#181A20]">Total Consolidado:</span>
              <span class="text-[14px] font-bold text-[#181A20] tabular-nums" id="tele-total-bal">$2,000.17 USD</span>
            </div>
          </div>

          <button onclick="fetchTelemetry(); triggerSyncEffect();" class="cta-primary-btn w-full">
            <i class="fa-solid fa-arrows-rotate text-[11px]" id="tele-refresh-icon"></i>
            <span>Sincronizar Telemetría</span>
          </button>
        </div>
      </div>

    </aside>

    <!-- ==================== MAIN CONTENT SURFACE (#FDFDFB, padding 24px) ==================== -->
    <main class="bg-[#FDFDFB] p-4 sm:p-6 lg:p-7 flex flex-col space-y-6 overflow-x-hidden">

      <!-- ==================== HEADER SUPERIOR DEL ÁREA DE CONTENIDO ==================== -->
      <header class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#E6E2D8]">
        <div>
          <div class="overline-text">MESA CUANTITATIVA INSTITUCIONAL</div>
          <h2 class="text-lg sm:text-xl font-bold text-[#181A20] tracking-tight" id="current-tab-title">Cockpit General · AlgrokQuant</h2>
        </div>

        <div class="flex items-center space-x-3">
          <div class="text-right hidden sm:block">
            <p class="text-xs text-[#181A20] font-bold font-mono" id="live-clock">--:--:-- UTC</p>
            <p class="text-[11px] text-[#065F46] font-semibold flex items-center justify-end">
              <span class="w-1.5 h-1.5 rounded-full bg-[#065F46] mr-1 animate-pulse"></span> Feed Activo (12ms)
            </p>
          </div>
          <button onclick="fetchCurrentDashboard()" class="p-2 text-[#181A20] hover:bg-[#EAE5DC] rounded-lg transition border border-[#E6E2D8]" title="Refrescar datos">
            <i class="fa-solid fa-rotate text-sm" id="refresh-icon"></i>
          </button>
        </div>
      </header>

      <!-- ==================== GRID DE TARJETAS DE ESTRATEGIAS / CUENTAS ACTIVAS ==================== -->
      <!-- Control de visibilidad: Solo se muestra en Cockpit General y Forward Tests en Vivo -->
      <div id="active-portfolio-section">
        <div class="flex items-center justify-between mb-3 px-1">
          <span class="overline-text">CARTERA ACTIVA EN TIEMPO REAL</span>
          <span id="portfolio-count-badge" class="badge-neutral-soft font-mono">3 ESTRATEGIAS CAPITAL PROPIO</span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

          <!-- Tarjeta 1: S&P 500 (Capital Propio) -->
          <div class="strategy-card" data-desk="CAPITAL_PROPIO">
            <div class="flex items-start justify-between">
              <div>
                <span class="text-xs font-bold text-[#5865F2] font-mono">US500</span>
                <h3 class="card-title mt-0.5">CAP-SPX-006</h3>
              </div>
              <span class="badge-brand-indigo">IC MARKETS MT5</span>
            </div>

            <div class="my-3 py-2 border-y border-[#E6E2D8]/60 space-y-1 text-xs">
              <div class="flex justify-between text-[#4A4944]">
                <span>Marco Temporal:</span>
                <strong class="text-[#181A20] font-mono">4 Horas (Swing)</strong>
              </div>
              <div class="flex justify-between text-[#4A4944]">
                <span>Gestión de Riesgo:</span>
                <strong class="text-[#181A20] font-mono">1.50% Compuesto</strong>
              </div>
              <div class="flex justify-between text-[#4A4944]">
                <span>Cartera Asignada:</span>
                <strong class="text-[#181A20]">Capital Propio</strong>
              </div>
            </div>

            <div class="flex items-center justify-between pt-1">
              <span class="badge-success-live">● EN EJECUCIÓN</span>
              <span class="text-[11px] font-mono font-bold text-[#181A20]">$999.51 USD</span>
            </div>
          </div>

          <!-- Tarjeta 2: Nasdaq 100 (Capital Propio) -->
          <div class="strategy-card" data-desk="CAPITAL_PROPIO">
            <div class="flex items-start justify-between">
              <div>
                <span class="text-xs font-bold text-[#5865F2] font-mono">USTEC</span>
                <h3 class="card-title mt-0.5">CAP-NDX-005</h3>
              </div>
              <span class="badge-brand-indigo">IC MARKETS MT5</span>
            </div>

            <div class="my-3 py-2 border-y border-[#E6E2D8]/60 space-y-1 text-xs">
              <div class="flex justify-between text-[#4A4944]">
                <span>Marco Temporal:</span>
                <strong class="text-[#181A20] font-mono">2 Horas (Intradía)</strong>
              </div>
              <div class="flex justify-between text-[#4A4944]">
                <span>Gestión de Riesgo:</span>
                <strong class="text-[#181A20] font-mono">1.50% Compuesto</strong>
              </div>
              <div class="flex justify-between text-[#4A4944]">
                <span>Cartera Asignada:</span>
                <strong class="text-[#181A20]">Capital Propio</strong>
              </div>
            </div>

            <div class="flex items-center justify-between pt-1">
              <span class="badge-success-live">● EN EJECUCIÓN</span>
              <span class="text-[11px] font-mono font-bold text-[#181A20]">$999.51 USD</span>
            </div>
          </div>

          <!-- Tarjeta 3: BTC Cripto Perpetuos (Hyperliquid) -->
          <div class="strategy-card" data-desk="CAPITAL_PROPIO">
            <div class="flex items-start justify-between">
              <div>
                <span class="text-xs font-bold text-[#5865F2] font-mono">BTC/USDT</span>
                <h3 class="card-title mt-0.5">CRYPTO-BTC-001</h3>
              </div>
              <span class="badge-brand-indigo">HYPERLIQUID L1</span>
            </div>

            <div class="my-3 py-2 border-y border-[#E6E2D8]/60 space-y-1 text-xs">
              <div class="flex justify-between text-[#4A4944]">
                <span>Marco Temporal:</span>
                <strong class="text-[#181A20] font-mono">1 Hora (Trend)</strong>
              </div>
              <div class="flex justify-between text-[#4A4944]">
                <span>Proveedor Cripto:</span>
                <strong class="text-[#181A20]">DEX L1 Nativo</strong>
              </div>
              <div class="flex justify-between text-[#4A4944]">
                <span>Cartera Asignada:</span>
                <strong class="text-[#181A20]">Capital Propio</strong>
              </div>
            </div>

            <div class="flex items-center justify-between pt-1">
              <span class="badge-success-live">● EN EJECUCIÓN</span>
              <span class="text-[11px] font-mono font-bold text-[#181A20]">1,000.66 USDC</span>
            </div>
          </div>

          <!-- Tarjeta 4: Forex EUR/USD (Fondeo Prop Firm) -->
          <div class="strategy-card" data-desk="PROP_FIRM" style="display: none;">
            <div class="flex items-start justify-between">
              <div>
                <span class="text-xs font-bold text-[#5865F2] font-mono">EURUSD</span>
                <h3 class="card-title mt-0.5">PROP-FX-EUR-001</h3>
              </div>
              <span class="badge-brand-indigo">IC MARKETS MT5</span>
            </div>

            <div class="my-3 py-2 border-y border-[#E6E2D8]/60 space-y-1 text-xs">
              <div class="flex justify-between text-[#4A4944]">
                <span>Marco Temporal:</span>
                <strong class="text-[#181A20] font-mono">1 Hora (Forex)</strong>
              </div>
              <div class="flex justify-between text-[#4A4944]">
                <span>Gestión de Riesgo:</span>
                <strong class="text-[#181A20] font-mono">1.00% Protegido</strong>
              </div>
              <div class="flex justify-between text-[#4A4944]">
                <span>Límite Drawdown:</span>
                <strong class="text-[#9A3412]">Máximo 4.0% EOD</strong>
              </div>
            </div>

            <div class="flex items-center justify-between pt-1">
              <span class="badge-warning-risk">● CONTROL DE RIESGO</span>
              <span class="text-[11px] font-mono font-bold text-[#181A20]">Pase Fondeo</span>
            </div>
          </div>

          <!-- Tarjeta 5: S&P 500 Breakout (Fondeo Prop Firm) -->
          <div class="strategy-card" data-desk="PROP_FIRM" style="display: none;">
            <div class="flex items-start justify-between">
              <div>
                <span class="text-xs font-bold text-[#5865F2] font-mono">US500</span>
                <h3 class="card-title mt-0.5">PROP-SPX-005</h3>
              </div>
              <span class="badge-brand-indigo">IC MARKETS MT5</span>
            </div>

            <div class="my-3 py-2 border-y border-[#E6E2D8]/60 space-y-1 text-xs">
              <div class="flex justify-between text-[#4A4944]">
                <span>Marco Temporal:</span>
                <strong class="text-[#181A20] font-mono">1 Día (Causal)</strong>
              </div>
              <div class="flex justify-between text-[#4A4944]">
                <span>Gestión de Riesgo:</span>
                <strong class="text-[#181A20] font-mono">1.00% Fondeo</strong>
              </div>
              <div class="flex justify-between text-[#4A4944]">
                <span>Cartera Asignada:</span>
                <strong class="text-[#181A20]">Prop Firm Sprint</strong>
              </div>
            </div>

            <div class="flex items-center justify-between pt-1">
              <span class="badge-success-live">● EN EJECUCIÓN</span>
              <span class="text-[11px] font-mono font-bold text-[#181A20]">1 Lote / Base</span>
            </div>
          </div>

          <!-- Tarjeta 6: Nasdaq 100 ORB (Fondeo Prop Firm) -->
          <div class="strategy-card" data-desk="PROP_FIRM" style="display: none;">
            <div class="flex items-start justify-between">
              <div>
                <span class="text-xs font-bold text-[#5865F2] font-mono">USTEC</span>
                <h3 class="card-title mt-0.5">PROP-NDX-006</h3>
              </div>
              <span class="badge-brand-indigo">IC MARKETS MT5</span>
            </div>

            <div class="my-3 py-2 border-y border-[#E6E2D8]/60 space-y-1 text-xs">
              <div class="flex justify-between text-[#4A4944]">
                <span>Marco Temporal:</span>
                <strong class="text-[#181A20] font-mono">30 Min (Apertura)</strong>
              </div>
              <div class="flex justify-between text-[#4A4944]">
                <span>Gestión de Riesgo:</span>
                <strong class="text-[#181A20] font-mono">1.00% Fondeo</strong>
              </div>
              <div class="flex justify-between text-[#4A4944]">
                <span>Cartera Asignada:</span>
                <strong class="text-[#181A20]">Prop Firm Sprint</strong>
              </div>
            </div>

            <div class="flex items-center justify-between pt-1">
              <span class="badge-success-live">● EN EJECUCIÓN</span>
              <span class="text-[11px] font-mono font-bold text-[#181A20]">1 Lote / Base</span>
            </div>
          </div>

        </div>
      </div>

      <!-- ==================== CONTENEDORES DE PESTAÑAS OPERATIVAS ==================== -->
      <div id="tabs-wrapper" class="w-full">
{tab_panes_html}
      </div>

    </main>

  </div>

  <!-- SCRIPT COMPLETO DE LÓGICA DE NEGOCIO Y RENDERIZADO -->
{scripts_html}

</body>
</html>
'''
    return html

if __name__ == '__main__':
    res = build_template()
    out_path = Path('/root/AlgrokQuant/dashboard/templates/index.html')
    with open(out_path, 'w', encoding='utf-8') as out:
        out.write(res)
    print("SUCCESS: Clean Coherent Warm Minimalist UI with TradingView Pro & Desk Sync written to index.html!")
