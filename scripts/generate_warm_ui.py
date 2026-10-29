import re
import os

def build_template():
    # Read original file from VPS or local
    with open('/root/AlgrokQuant/dashboard/templates/index.html.bak_pre_warm_ui', 'r', encoding='utf-8') as f:
        orig = f.read()

    # Extract all tab-panes: from the first tab-content to the end of main
    # Tab panes start at <div id="tab-content-dashboard"
    # and end right before </main>
    tab_start_idx = orig.find('<div id="tab-content-dashboard"')
    tab_end_idx = orig.find('</main>')
    
    if tab_start_idx == -1 or tab_end_idx == -1:
        raise ValueError("Could not locate tab content bounds")
        
    tab_panes_html = orig[tab_start_idx:tab_end_idx]

    # Extract all <script> blocks that are at the bottom (after </main>)
    scripts_html = orig[tab_end_idx + 7:]

    # Now let's build the brand new Warm Minimalist & Tactile UI HTML
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
       WARM MINIMALIST & TACTILE UI - DESIGN SYSTEM TOKENS
       ========================================================================== */
    :root {{
      --canvas-bg: #F5EFE6;
      --sidebar-bg: #EFECE6;
      --main-surface: #FDFDFB;
      --card-surface: #FFFFFF;
      --surface-muted: #EAE5DC;
      --closed-pattern: repeating-linear-gradient(-45deg, #EAE5DC, #EAE5DC 6px, #E2DDD3 6px, #E2DDD3 8px);
      --primary-accent: #181A20;
      --brand-accent: #5865F2;
      --warning-text: #C86D3B;
      --text-primary: #181A20;
      --text-secondary: #6E6D68;
      --text-muted: #9E9C94;
      --border-solid: #E6E2D8;
      --border-dashed: #B5B2A8;
      --shadow-shell: 0 20px 50px rgba(24, 26, 32, 0.08);
      --shadow-card: 0 4px 12px rgba(24, 26, 32, 0.04);
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

    /* Tipografía y Escala Oficial */
    .overline-text {{
      font-size: 10px;
      text-transform: uppercase;
      font-weight: 700;
      letter-spacing: 0.08em;
      color: var(--text-muted);
    }}

    h1.panel-title {{
      font-size: 22px;
      font-weight: 700;
      line-height: 1.2;
      color: var(--text-primary);
      letter-spacing: -0.02em;
    }}

    h2.card-title {{
      font-size: 16px;
      font-weight: 700;
      font-feature-settings: "tnum";
      font-variant-numeric: tabular-nums;
      color: var(--text-primary);
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
      font-weight: 400;
      color: var(--text-secondary);
    }}

    /* Bloques Squircle (24x24px, radius 8px) */
    .squircle-block {{
      width: 24px;
      height: 24px;
      border-radius: 8px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      transition: all 0.2s ease;
    }}

    .squircle-free {{
      background: transparent;
      border: 1.5px dashed var(--border-dashed);
    }}

    .squircle-occupied {{
      background: var(--primary-accent);
      box-shadow: 0 1px 3px rgba(24, 26, 32, 0.2);
    }}

    .squircle-selected {{
      background: var(--brand-accent);
      box-shadow: 0 2px 6px rgba(88, 101, 242, 0.35);
    }}

    /* Tarjetas de Contenido (Cards) */
    .tactile-card {{
      min-height: 150px;
      padding: 18px;
      border-radius: 16px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      border: 1px solid var(--border-solid);
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      position: relative;
    }}

    .tactile-card-active {{
      background: var(--card-surface);
      box-shadow: var(--shadow-card);
    }}

    .tactile-card-active:hover {{
      border-color: var(--primary-accent);
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(24, 26, 32, 0.08);
    }}

    .tactile-card-urgent {{
      background: var(--card-surface);
      box-shadow: var(--shadow-card);
      border-color: rgba(200, 109, 59, 0.4);
    }}

    .tactile-card-urgent:hover {{
      border-color: var(--warning-text);
      transform: translateY(-2px);
    }}

    .tactile-card-muted {{
      background: var(--surface-muted);
      border-color: var(--border-solid);
    }}

    .tactile-card-closed {{
      background: var(--closed-pattern);
      border-color: var(--border-solid);
      opacity: 0.78;
    }}

    /* Segmented Control (Pills) */
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
      color: var(--text-secondary);
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

    /* Barra Superior de Pestañas (Top Tabs) */
    .top-tabs-bar {{
      background: var(--sidebar-bg);
      border-radius: 16px;
      padding: 4px;
      display: flex;
      gap: 4px;
      overflow-x: auto;
      scrollbar-width: none;
    }}

    .top-tabs-bar::-webkit-scrollbar {{
      display: none;
    }}

    .top-tab-item {{
      padding: 8px 14px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      border: none;
      background: transparent;
      white-space: nowrap;
      flex-shrink: 0;
    }}

    .top-tab-item.active {{
      background: var(--primary-accent);
      color: #FFFFFF;
      box-shadow: 0 4px 14px rgba(24, 26, 32, 0.15);
    }}

    .top-tab-item.active .tab-title {{
      color: #FFFFFF;
    }}

    .top-tab-item.active .tab-sub {{
      color: rgba(255, 255, 255, 0.65);
    }}

    .top-tab-item.active .tab-badge {{
      background: rgba(255, 255, 255, 0.15);
      color: #FFFFFF;
    }}

    .top-tab-item:not(.active):hover {{
      background: rgba(255, 255, 255, 0.5);
      color: var(--text-primary);
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

    /* Overrides de adaptabilidad para elementos preexistentes */
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
      color: #059669 !important;
    }}

    .text-rose-400, .text-rose-300 {{
      color: var(--warning-text) !important;
    }}

    /* Tablas con fondo claro de alto contraste */
    table thead {{
      background-color: var(--sidebar-bg) !important;
      color: var(--text-primary) !important;
      border-color: var(--border-solid) !important;
    }}

    table tbody tr {{
      border-color: var(--border-solid) !important;
      background-color: var(--card-surface);
      color: var(--text-primary);
    }}

    table tbody tr:hover {{
      background-color: #FAF7F2 !important;
    }}

    /* Inputs y selects */
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

  <!-- TradingView Lightweight Charts CDN Oficial -->
  <script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
</head>

<body class="p-2 sm:p-5 lg:p-8">

  <!-- ==========================================================================
       APP SHELL PRINCIPAL (Max-width 1240px, centrado, radius 24px, sombra suave)
       ========================================================================== -->
  <div class="max-w-[1240px] mx-auto rounded-[24px] shadow-[0_20px_50px_rgba(24,26,32,0.08)] overflow-hidden border border-[#E6E2D8] bg-[#FDFDFB] flex flex-col lg:grid lg:grid-cols-[280px_1fr] min-h-[92vh]">

    <!-- ==================== SIDEBAR IZQUIERDO (#EFECE6, padding 24px) ==================== -->
    <aside class="bg-[#EFECE6] p-6 border-b lg:border-b-0 lg:border-r border-[#E6E2D8] flex flex-col justify-between">
      
      <!-- Bloque Superior: Logo + Encabezado + Segmented Control + Menú -->
      <div>
        
        <!-- Logo en contenedor cuadrado blanco (40x40px, radius 12px) + Títulos -->
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

        <!-- Navegación con Viñetas de Diamante (#5865F2) -->
        <div class="overline-text px-1 mb-2">MÓDULOS DEL DESK</div>
        <nav class="space-y-1" id="sidebar-nav">
          
          <button onclick="switchTab('dashboard')" id="side-tab-dashboard" class="sidebar-link active w-full flex items-center px-3 py-2 rounded-[10px] body-btn-text text-white bg-[#181A20] shadow-sm transition group">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span class="flex-1 text-left whitespace-nowrap">Cockpit General</span>
          </button>

          <button onclick="switchTab('backtests')" id="side-tab-backtests" class="sidebar-link w-full flex items-center px-3 py-2 rounded-[10px] body-btn-text text-[#6E6D68] hover:text-[#181A20] hover:bg-[#EAE5DC]/60 transition group">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span class="flex-1 text-left whitespace-nowrap">1. Backtests (Multi-Horizonte)</span>
          </button>

          <button onclick="switchTab('forward')" id="side-tab-forward" class="sidebar-link w-full flex items-center px-3 py-2 rounded-[10px] body-btn-text text-[#6E6D68] hover:text-[#181A20] hover:bg-[#EAE5DC]/60 transition group">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span class="flex-1 text-left whitespace-nowrap">2. Forward Tests (En Vivo)</span>
          </button>

          <button onclick="switchTab('tri_facet')" id="side-tab-tri_facet" class="sidebar-link w-full flex items-center px-3 py-2 rounded-[10px] body-btn-text text-[#6E6D68] hover:text-[#181A20] hover:bg-[#EAE5DC]/60 transition group">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span class="flex-1 text-left whitespace-nowrap">3. Contraste Tri-Faceta</span>
          </button>

          <button onclick="switchTab('roster')" id="side-tab-roster" class="sidebar-link w-full flex items-center px-3 py-2 rounded-[10px] body-btn-text text-[#6E6D68] hover:text-[#181A20] hover:bg-[#EAE5DC]/60 transition group">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span class="flex-1 text-left whitespace-nowrap">Enjambre (10 Agentes)</span>
          </button>

          <button onclick="switchTab('lab')" id="side-tab-lab" class="sidebar-link w-full flex items-center px-3 py-2 rounded-[10px] body-btn-text text-[#6E6D68] hover:text-[#181A20] hover:bg-[#EAE5DC]/60 transition group">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span class="flex-1 text-left whitespace-nowrap">Creación & Lab (VectorBT)</span>
          </button>

          <button onclick="switchTab('chart')" id="side-tab-chart" class="sidebar-link w-full flex items-center px-3 py-2 rounded-[10px] body-btn-text text-[#6E6D68] hover:text-[#181A20] hover:bg-[#EAE5DC]/60 transition group">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span class="flex-1 text-left whitespace-nowrap">Gráficos TradingView</span>
          </button>

          <button onclick="switchTab('strategies')" id="side-tab-strategies" class="sidebar-link w-full flex items-center px-3 py-2 rounded-[10px] body-btn-text text-[#6E6D68] hover:text-[#181A20] hover:bg-[#EAE5DC]/60 transition group">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span class="flex-1 text-left whitespace-nowrap">Catálogo de Modelos</span>
          </button>

          <button onclick="switchTab('config')" id="side-tab-config" class="sidebar-link w-full flex items-center px-3 py-2 rounded-[10px] body-btn-text text-[#6E6D68] hover:text-[#181A20] hover:bg-[#EAE5DC]/60 transition group">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span class="flex-1 text-left whitespace-nowrap">Reglas de Riesgo</span>
          </button>

          <button onclick="switchTab('journal')" id="side-tab-journal" class="sidebar-link w-full flex items-center px-3 py-2 rounded-[10px] body-btn-text text-[#6E6D68] hover:text-[#181A20] hover:bg-[#EAE5DC]/60 transition group">
            <i class="fa-solid fa-diamond text-[8px] text-[#5865F2] mr-2.5"></i>
            <span class="flex-1 text-left whitespace-nowrap">Bitácora & Informes</span>
          </button>

        </nav>
      </div>

      <!-- Widget Inferior de Control Secundario (Caja con borde #E6E2D8 y botón CTA #181A20) -->
      <div class="mt-8 pt-4 border-t border-[#E6E2D8]">
        <div class="bg-[#FFFFFF] border border-[#E6E2D8] rounded-[16px] p-4 shadow-sm space-y-3">
          <div class="flex items-center justify-between">
            <span class="overline-text">TELEMETRÍA EN VIVO</span>
            <span class="w-2 h-2 rounded-full bg-[#10b981] animate-pulse"></span>
          </div>
          
          <div class="space-y-1.5 text-xs font-mono">
            <div class="flex justify-between items-center text-[#6E6D68]">
              <span>IC Markets MT5:</span>
              <span class="font-bold text-[#181A20]" id="tele-mt5-bal">$999.51 USD</span>
            </div>
            <div class="flex justify-between items-center text-[#6E6D68]">
              <span>Hyperliquid DEX:</span>
              <span class="font-bold text-[#181A20]" id="tele-hl-bal">1,000.66 USDC</span>
            </div>
            <div class="pt-1 border-t border-[#E6E2D8] flex justify-between items-center">
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

      <!-- ==================== BARRA SUPERIOR DE PESTAÑAS (Top Tabs) ==================== -->
      <div class="top-tabs-bar">
        
        <button onclick="switchTab('dashboard')" id="top-tab-dashboard" class="top-tab-item active">
          <div class="text-left">
            <div class="tab-title text-[13px] font-bold">Cockpit</div>
            <div class="tab-sub text-[11px] font-normal">Visión Global</div>
          </div>
          <span class="tab-badge px-2 py-0.5 rounded-full text-[10px] font-bold font-mono">7 STRATS</span>
        </button>

        <button onclick="switchTab('backtests')" id="top-tab-backtests" class="top-tab-item">
          <div class="text-left">
            <div class="tab-title text-[13px] font-bold text-[#181A20]">Backtests</div>
            <div class="tab-sub text-[11px] text-[#9E9C94] font-normal">1-10 Años</div>
          </div>
          <span class="tab-badge px-2 py-0.5 rounded-full text-[10px] font-bold font-mono bg-[#EAE5DC] text-[#6E6D68]">1.1k TR</span>
        </button>

        <button onclick="switchTab('forward')" id="top-tab-forward" class="top-tab-item">
          <div class="text-left">
            <div class="tab-title text-[13px] font-bold text-[#181A20]">Forward Tests</div>
            <div class="tab-sub text-[11px] text-[#9E9C94] font-normal">En Directo</div>
          </div>
          <span class="tab-badge px-2 py-0.5 rounded-full text-[10px] font-bold font-mono bg-[#EAE5DC] text-[#6E6D68]">LIVE</span>
        </button>

        <button onclick="switchTab('tri_facet')" id="top-tab-tri_facet" class="top-tab-item">
          <div class="text-left">
            <div class="tab-title text-[13px] font-bold text-[#181A20]">Tri-Faceta</div>
            <div class="tab-sub text-[11px] text-[#9E9C94] font-normal">3 Capas</div>
          </div>
          <span class="tab-badge px-2 py-0.5 rounded-full text-[10px] font-bold font-mono bg-[#EAE5DC] text-[#6E6D68]">L-018</span>
        </button>

        <button onclick="switchTab('roster')" id="top-tab-roster" class="top-tab-item">
          <div class="text-left">
            <div class="tab-title text-[13px] font-bold text-[#181A20]">Enjambre</div>
            <div class="tab-sub text-[11px] text-[#9E9C94] font-normal">Multi-Agente</div>
          </div>
          <span class="tab-badge px-2 py-0.5 rounded-full text-[10px] font-bold font-mono bg-[#EAE5DC] text-[#6E6D68]">10 AGY</span>
        </button>

        <button onclick="switchTab('lab')" id="top-tab-lab" class="top-tab-item">
          <div class="text-left">
            <div class="tab-title text-[13px] font-bold text-[#181A20]">Creación</div>
            <div class="tab-sub text-[11px] text-[#9E9C94] font-normal">VectorBT Lab</div>
          </div>
          <span class="tab-badge px-2 py-0.5 rounded-full text-[10px] font-bold font-mono bg-[#EAE5DC] text-[#6E6D68]">PARQUET</span>
        </button>

        <button onclick="switchTab('chart')" id="top-tab-chart" class="top-tab-item">
          <div class="text-left">
            <div class="tab-title text-[13px] font-bold text-[#181A20]">TradingView</div>
            <div class="tab-sub text-[11px] text-[#9E9C94] font-normal">Auditoría Técnica</div>
          </div>
          <span class="tab-badge px-2 py-0.5 rounded-full text-[10px] font-bold font-mono bg-[#EAE5DC] text-[#6E6D68]">CANVAS</span>
        </button>

        <button onclick="switchTab('strategies')" id="top-tab-strategies" class="top-tab-item">
          <div class="text-left">
            <div class="tab-title text-[13px] font-bold text-[#181A20]">Catálogo</div>
            <div class="tab-sub text-[11px] text-[#9E9C94] font-normal">Aprobadas</div>
          </div>
          <span class="tab-badge px-2 py-0.5 rounded-full text-[10px] font-bold font-mono bg-[#EAE5DC] text-[#6E6D68]">CAT</span>
        </button>

        <button onclick="switchTab('config')" id="top-tab-config" class="top-tab-item">
          <div class="text-left">
            <div class="tab-title text-[13px] font-bold text-[#181A20]">Riesgo</div>
            <div class="tab-sub text-[11px] text-[#9E9C94] font-normal">Gobernanza</div>
          </div>
          <span class="tab-badge px-2 py-0.5 rounded-full text-[10px] font-bold font-mono bg-[#EAE5DC] text-[#6E6D68]">RISK</span>
        </button>

        <button onclick="switchTab('journal')" id="top-tab-journal" class="top-tab-item">
          <div class="text-left">
            <div class="tab-title text-[13px] font-bold text-[#181A20]">Bitácora</div>
            <div class="tab-sub text-[11px] text-[#9E9C94] font-normal">Informes</div>
          </div>
          <span class="tab-badge px-2 py-0.5 rounded-full text-[10px] font-bold font-mono bg-[#EAE5DC] text-[#6E6D68]">DOCS</span>
        </button>

      </div>

      <!-- ==================== GRID DE TARJETAS TÁCTILES (3 cols x 2 rows, gap 14px) ==================== -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-[14px]">

        <!-- Tarjeta 1: S&P 500 (Activa) -->
        <div class="tactile-card tactile-card-active">
          <div class="flex items-center justify-between">
            <h2 class="card-title">CAP-SPX-006 · 4h</h2>
            <i class="fa-solid fa-chart-line text-[#5865F2] text-sm"></i>
          </div>
          <div class="flex items-center gap-2 my-3">
            <span class="squircle-block squircle-occupied" title="Slot Ocupado"></span>
            <span class="squircle-block squircle-occupied" title="Slot Ocupado"></span>
            <span class="squircle-block squircle-occupied" title="Slot Ocupado"></span>
            <span class="squircle-block squircle-occupied" title="Slot Ocupado"></span>
            <span class="squircle-block squircle-selected" title="Seleccionado por Usuario"></span>
          </div>
          <div>
            <div class="body-btn-text text-[#181A20]">ACTIVO · IC MARKETS MT5</div>
            <div class="caption-detail">Capital Propio · Riesgo 1.50% Compuesto</div>
          </div>
        </div>

        <!-- Tarjeta 2: Nasdaq 100 (Activa) -->
        <div class="tactile-card tactile-card-active">
          <div class="flex items-center justify-between">
            <h2 class="card-title">CAP-NDX-005 · 2h</h2>
            <i class="fa-solid fa-bolt text-[#5865F2] text-sm"></i>
          </div>
          <div class="flex items-center gap-2 my-3">
            <span class="squircle-block squircle-occupied" title="Slot Ocupado"></span>
            <span class="squircle-block squircle-occupied" title="Slot Ocupado"></span>
            <span class="squircle-block squircle-occupied" title="Slot Ocupado"></span>
            <span class="squircle-block squircle-selected" title="Seleccionado por Usuario"></span>
            <span class="squircle-block squircle-free" title="Slot Libre"></span>
          </div>
          <div>
            <div class="body-btn-text text-[#181A20]">ACTIVO · IC MARKETS MT5</div>
            <div class="caption-detail">Capital Propio · Riesgo 1.50% Compuesto</div>
          </div>
        </div>

        <!-- Tarjeta 3: BTC Cripto DEX (Activa) -->
        <div class="tactile-card tactile-card-active">
          <div class="flex items-center justify-between">
            <h2 class="card-title">CRYPTO-BTC-001 · 1h</h2>
            <i class="fa-brands fa-bitcoin text-[#5865F2] text-sm"></i>
          </div>
          <div class="flex items-center gap-2 my-3">
            <span class="squircle-block squircle-occupied" title="Slot Ocupado"></span>
            <span class="squircle-block squircle-occupied" title="Slot Ocupado"></span>
            <span class="squircle-block squircle-occupied" title="Slot Ocupado"></span>
            <span class="squircle-block squircle-occupied" title="Slot Ocupado"></span>
            <span class="squircle-block squircle-occupied" title="Slot Ocupado"></span>
          </div>
          <div>
            <div class="body-btn-text text-[#181A20]">EJECUCIÓN HYPERLIQUID L1</div>
            <div class="caption-detail">Proveedor Cripto Nativo · 1,000.66 USDC</div>
          </div>
        </div>

        <!-- Tarjeta 4: Forex EUR/USD (Urgencia / EOD Control) -->
        <div class="tactile-card tactile-card-urgent">
          <div class="flex items-center justify-between">
            <h2 class="card-title">PROP-FX-EUR-001 · 1h</h2>
            <i class="fa-solid fa-triangle-exclamation text-[#C86D3B] text-sm"></i>
          </div>
          <div class="flex items-center gap-2 my-3">
            <span class="squircle-block squircle-occupied" title="Slot Ocupado"></span>
            <span class="squircle-block squircle-occupied" title="Slot Ocupado"></span>
            <span class="squircle-block squircle-free" title="Slot Libre"></span>
            <span class="squircle-block squircle-free" title="Slot Libre"></span>
            <span class="squircle-block squircle-free" title="Slot Libre"></span>
          </div>
          <div>
            <div class="body-btn-text text-[#C86D3B]">CONTROL EOD DRAWDOWN</div>
            <div class="caption-detail">Fondeo · Límite Máximo Drawdown 4.0%</div>
          </div>
        </div>

        <!-- Tarjeta 5: Laboratorio VectorBT (Surface Muted) -->
        <div class="tactile-card tactile-card-muted">
          <div class="flex items-center justify-between">
            <h2 class="card-title text-[#181A20]">LAB & ROBUSTEZ</h2>
            <i class="fa-solid fa-flask text-[#6E6D68] text-sm"></i>
          </div>
          <div class="flex items-center gap-2 my-3">
            <span class="squircle-block squircle-occupied" title="Slot Ocupado"></span>
            <span class="squircle-block squircle-free" title="Slot Libre"></span>
            <span class="squircle-block squircle-free" title="Slot Libre"></span>
            <span class="squircle-block squircle-free" title="Slot Libre"></span>
            <span class="squircle-block squircle-free" title="Slot Libre"></span>
          </div>
          <div>
            <div class="body-btn-text text-[#181A20]">MOTOR PARQUET CAUSAL</div>
            <div class="caption-detail">1,127 Trades Históricos Verificados</div>
          </div>
        </div>

        <!-- Tarjeta 6: Futuros CME Globex (Bloqueada / Cerrada) -->
        <div class="tactile-card tactile-card-closed">
          <div class="flex items-center justify-between">
            <h2 class="card-title text-[#6E6D68]">CME GLOBEX DIRECT</h2>
            <i class="fa-solid fa-lock text-[#9E9C94] text-sm"></i>
          </div>
          <div class="flex items-center gap-2 my-3">
            <span class="squircle-block squircle-free" title="Slot Bloqueado"></span>
            <span class="squircle-block squircle-free" title="Slot Bloqueado"></span>
            <span class="squircle-block squircle-free" title="Slot Bloqueado"></span>
            <span class="squircle-block squircle-free" title="Slot Bloqueado"></span>
            <span class="squircle-block squircle-free" title="Slot Bloqueado"></span>
          </div>
          <div>
            <div class="body-btn-text text-[#6E6D68]">FASE EN INCUBACIÓN</div>
            <div class="caption-detail">DMA Direct Market Access en Espera</div>
          </div>
        </div>

      </div>

      <!-- ==================== FOOTER DE LEYENDA (Flex space-between) ==================== -->
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-2 pb-4 border-b border-[#E6E2D8] text-xs">
        <div class="flex items-center gap-2 text-[#6E6D68]">
          <span class="w-2 h-2 rounded-full bg-[#10b981]"></span>
          <span class="font-medium text-[#181A20]">Sistema Operativo</span>
          <span>·</span>
          <span>Latencia: <strong class="text-[#181A20] font-mono">12ms</strong></span>
          <span>·</span>
          <span>IC Markets Demo SC + Hyperliquid L1</span>
        </div>
        
        <!-- Leyenda de Bloques Squircle -->
        <div class="flex items-center gap-4 text-[#6E6D68] text-[11px]">
          <div class="flex items-center gap-1.5">
            <span class="squircle-block squircle-free !w-3.5 !h-3.5 !rounded-[4px]"></span>
            <span>Libre</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span class="squircle-block squircle-occupied !w-3.5 !h-3.5 !rounded-[4px]"></span>
            <span>Ocupado</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span class="squircle-block squircle-selected !w-3.5 !h-3.5 !rounded-[4px]"></span>
            <span>Seleccionado</span>
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

  <!-- Lógica de Sincronización de Top Tabs & Segmented Control -->
  <script>
    function switchDeskMode(mode) {{
      const bCap = document.getElementById('seg-btn-cap-propio');
      const bProp = document.getElementById('seg-btn-prop-firm');
      if (mode === 'CAPITAL_PROPIO') {{
        if (bCap) bCap.className = 'segmented-pill active flex-1';
        if (bProp) bProp.className = 'segmented-pill flex-1';
      }} else {{
        if (bProp) bProp.className = 'segmented-pill active flex-1';
        if (bCap) bCap.className = 'segmented-pill flex-1';
      }}
    }}

    // Enganche para sincronizar pestañas superiores con el menú lateral
    const origSwitchTab = window.switchTab;
    window.switchTab = function(tabId) {{
      // Actualizar botones del Sidebar
      document.querySelectorAll('.sidebar-link').forEach(el => {{
        el.className = 'sidebar-link w-full flex items-center px-3 py-2 rounded-[10px] body-btn-text text-[#6E6D68] hover:text-[#181A20] hover:bg-[#EAE5DC]/60 transition group';
      }});
      const sideBtn = document.getElementById('side-tab-' + tabId);
      if (sideBtn) {{
        sideBtn.className = 'sidebar-link active w-full flex items-center px-3 py-2 rounded-[10px] body-btn-text text-white bg-[#181A20] shadow-sm transition group';
      }}

      // Actualizar Top Tabs
      document.querySelectorAll('.top-tab-item').forEach(el => {{
        el.classList.remove('active');
        const title = el.querySelector('.tab-title');
        const sub = el.querySelector('.tab-sub');
        const badge = el.querySelector('.tab-badge');
        if (title) title.className = 'tab-title text-[13px] font-bold text-[#181A20]';
        if (sub) sub.className = 'tab-sub text-[11px] text-[#9E9C94] font-normal';
        if (badge) badge.className = 'tab-badge px-2 py-0.5 rounded-full text-[10px] font-bold font-mono bg-[#EAE5DC] text-[#6E6D68]';
      }});
      const topBtn = document.getElementById('top-tab-' + tabId);
      if (topBtn) {{
        topBtn.classList.add('active');
        const title = topBtn.querySelector('.tab-title');
        const sub = topBtn.querySelector('.tab-sub');
        const badge = topBtn.querySelector('.tab-badge');
        if (title) title.className = 'tab-title text-[13px] font-bold text-white';
        if (sub) sub.className = 'tab-sub text-[11px] text-slate-300 font-normal';
        if (badge) badge.className = 'tab-badge px-2 py-0.5 rounded-full text-[10px] font-bold font-mono bg-white/20 text-white';
      }}

      // Llamar a la lógica original de conmutación de paneles
      if (typeof origSwitchTab === 'function') {{
        origSwitchTab(tabId);
      }}
    }};

    function triggerSyncEffect() {{
      const icon = document.getElementById('tele-refresh-icon');
      if (icon) {{
        icon.classList.add('fa-spin');
        setTimeout(() => icon.classList.remove('fa-spin'), 1000);
      }}
    }}
  </script>

</body>
</html>
'''
    return html

if __name__ == '__main__':
    res = build_template()
    with open('/root/AlgrokQuant/dashboard/templates/index.html', 'w', encoding='utf-8') as out:
        out.write(res)
    print("SUCCESS: Warm Minimalist & Tactile UI written to index.html!")
