# -*- coding: utf-8 -*-
import re
import sys

def build_template():
    with open('/root/AlgrokQuant/dashboard/templates/index.html.bak_pre_warm_ui', 'r', encoding='utf-8') as f:
        orig = f.read()

    tab_start_idx = orig.find('<div id="tab-content-dashboard"')
    tab_end_idx = orig.find('</main>')
    
    if tab_start_idx == -1 or tab_end_idx == -1:
        raise ValueError("Could not locate tab content bounds")
        
    tab_panes_html = orig[tab_start_idx:tab_end_idx]
    scripts_html = orig[tab_end_idx + 7:]

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

      <!-- ==================== GRID DE TARJETAS DE ESTRATEGIAS (100% Coherentes & Homogéneas) ==================== -->
      <div>
        <div class="flex items-center justify-between mb-3 px-1">
          <span class="overline-text">CARTERA ACTIVA EN TIEMPO REAL</span>
          <span class="badge-neutral-soft font-mono">7 ESTRATEGIAS DESPLEGADAS</span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

          <!-- Tarjeta 1: S&P 500 (Capital Propio) -->
          <div class="strategy-card">
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
          <div class="strategy-card">
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
          <div class="strategy-card">
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
          <div class="strategy-card">
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
          <div class="strategy-card">
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
          <div class="strategy-card">
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

  <!-- Lógica de Sincronización del Sidebar Único & Segmented Control -->
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

    // Enganche para sincronizar estado visual del menú lateral único
    const origSwitchTab = window.switchTab;
    window.switchTab = function(tabId) {{
      // Actualizar botones del Sidebar
      document.querySelectorAll('.sidebar-link').forEach(el => {{
        el.className = 'sidebar-link';
      }});
      const sideBtn = document.getElementById('side-tab-' + tabId);
      if (sideBtn) {{
        sideBtn.className = 'sidebar-link active';
      }}

      // Llamar a la función original de navegación
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
    print("SUCCESS: Clean Coherent Warm Minimalist UI with Single Lateral Menu written to index.html!")
