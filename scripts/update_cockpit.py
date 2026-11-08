import re
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot")
INDEX_PATH = BASE_DIR / "dashboard" / "templates" / "index.html"

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    content = f.read()

start_marker = '<div id="tab-content-dashboard" class="tab-pane space-y-6">'
end_marker = '<!-- ==================== PESTAÑA 2: FASE 1 - BACKTESTS (CALIBRACIÓN 12M) ===================='

pos_start = content.find(start_marker)
pos_end = content.find(end_marker)

if pos_start == -1 or pos_end == -1:
    print("Markers not found!")
    exit(1)

before_end = content[:pos_end]
last_div_idx = before_end.rfind('</div>')

new_inner_html = """

          <!-- ==================== HEADER EJECUTIVO & CONTROLES GLOBALES ==================== -->
          <div class="p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <span class="badge-brand-indigo font-mono">COCKPIT GENERAL</span>
                <span id="cockpit-sync-badge" class="badge-success-live font-mono">● CUENTAS CONECTADAS</span>
                <span id="cockpit-news-badge" class="badge-neutral-soft font-mono"><i class="fa-solid fa-newspaper mr-1 text-[#3C45A5]"></i>FILTRO NOTICIAS: ±5 MIN</span>
              </div>
              <h1 class="text-xl sm:text-2xl font-bold text-[#1D1D1F] tracking-tight">Monitoreo Unificado de Cartera</h1>
              <p class="text-xs text-[#6E6E73]">Supervisión consolidada de capital en Forward Test: IC Markets (MT5 Prop Firm) y Hyperliquid (Crypto DEX).</p>
            </div>
            <!-- Acciones de Intervención Operativa & Gestor de Cuentas -->
            <div class="flex items-center gap-2.5 shrink-0 flex-wrap">
              <button onclick="toggleAccountsManagerModal()" class="btn-secondary whitespace-nowrap cursor-pointer text-xs flex items-center gap-1.5" title="Gestionar Cuentas Conectadas y Fases de Fondeo">
                <i class="fa-solid fa-building-columns text-[#3C45A5]"></i> Cuentas & Fases
              </button>
              <button onclick="toggleRiskAuditModal()" class="btn-secondary whitespace-nowrap cursor-pointer text-xs flex items-center gap-1.5" title="Ver auditoría de drawdown multianual">
                <i class="fa-solid fa-shield-halved text-[#3C45A5]"></i> Auditoría Riesgo
              </button>
              <button onclick="triggerEmergencyKillSwitch()" id="btn-kill-switch" class="px-4 py-2 rounded-lg bg-[#D70015] hover:bg-[#B50012] text-white text-xs font-bold font-mono flex items-center gap-2 transition shadow-xs cursor-pointer whitespace-nowrap" title="Desconexión preventiva y pausa de todos los bots">
                <i class="fa-solid fa-hand text-white"></i> PAUSA PREVENTIVA
              </button>
            </div>
          </div>

          <!-- ==================== 6 TARJETAS DE KPI INDEPENDIENTES (APPLE / LINEAR STYLE) ==================== -->
          <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3.5 sm:gap-4">
            
            <!-- KPI 1: Balance Total en Forward Test -->
            <div class="p-4 sm:p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs flex flex-col justify-between hover:border-[#D1D1D6] transition">
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-[11px] uppercase tracking-wider font-semibold text-[#6E6E73] truncate">Balance Total FT</span>
                  <div class="h-6 w-6 rounded-lg bg-[#EEF2FF] flex items-center justify-center text-[#3C45A5] shrink-0">
                    <i class="fa-solid fa-wallet text-[11px]"></i>
                  </div>
                </div>
                <div class="text-lg sm:text-2xl font-bold font-mono text-[#1D1D1F] tracking-tight" id="cockpit-kpi-total-balance">$1,998.09</div>
              </div>
              <div class="mt-3 pt-2.5 border-t border-[#F2F2F7] flex items-center justify-between text-[11px]">
                <span class="text-[#86868B] font-medium">Suma Cuentas FT</span>
                <span class="badge-brand-indigo font-mono text-[10px] py-0.5 px-1.5">MT5 + DEX</span>
              </div>
            </div>

            <!-- KPI 2: PnL Realizado Total -->
            <div class="p-4 sm:p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs flex flex-col justify-between hover:border-[#D1D1D6] transition">
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-[11px] uppercase tracking-wider font-semibold text-[#6E6E73] truncate">PnL Realizado</span>
                  <div class="h-6 w-6 rounded-lg bg-[#F2F2F7] flex items-center justify-center text-[#1D1D1F] shrink-0">
                    <i class="fa-solid fa-scale-balanced text-[11px]"></i>
                  </div>
                </div>
                <div class="text-lg sm:text-2xl font-bold font-mono text-[#D70015] tracking-tight" id="cockpit-kpi-realized-pnl">-$1.91</div>
              </div>
              <div class="mt-3 pt-2.5 border-t border-[#F2F2F7] flex items-center justify-between text-[11px]">
                <span class="text-[#86868B] font-medium">Trades cerrados</span>
                <span id="cockpit-kpi-realized-badge" class="badge-warning-risk font-mono text-[10px] py-0.5 px-1.5">-0.10%</span>
              </div>
            </div>

            <!-- KPI 3: PnL Flotante Total -->
            <div class="p-4 sm:p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs flex flex-col justify-between hover:border-[#D1D1D6] transition">
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-[11px] uppercase tracking-wider font-semibold text-[#6E6E73] truncate">PnL Flotante</span>
                  <div class="h-6 w-6 rounded-lg bg-[#FEF2F2] flex items-center justify-center text-[#D70015] shrink-0">
                    <i class="fa-solid fa-chart-line text-[11px]"></i>
                  </div>
                </div>
                <div class="text-lg sm:text-2xl font-bold font-mono text-[#D70015] tracking-tight" id="cockpit-kpi-floating-pnl">-$4.58</div>
              </div>
              <div class="mt-3 pt-2.5 border-t border-[#F2F2F7] flex items-center justify-between text-[11px]">
                <span class="text-[#86868B] font-medium">Posiciones vivas</span>
                <span id="cockpit-kpi-floating-badge" class="badge-neutral-soft font-mono text-[10px] py-0.5 px-1.5">-0.23%</span>
              </div>
            </div>

            <!-- KPI 4: Drawdown Cartera -->
            <div class="p-4 sm:p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs flex flex-col justify-between hover:border-[#D1D1D6] transition">
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-[11px] uppercase tracking-wider font-semibold text-[#6E6E73] truncate">Drawdown Cartera</span>
                  <div class="h-6 w-6 rounded-lg bg-[#FEF2F2] flex items-center justify-center text-[#D70015] shrink-0">
                    <i class="fa-solid fa-arrow-trend-down text-[11px]"></i>
                  </div>
                </div>
                <div class="text-lg sm:text-2xl font-bold font-mono text-[#D70015] tracking-tight" id="cockpit-kpi-drawdown">-0.23%</div>
              </div>
              <div class="mt-3 pt-2.5 border-t border-[#F2F2F7] flex items-center justify-between text-[11px]">
                <span class="text-[#86868B] font-medium">Límite máx</span>
                <span class="text-[#D70015] font-mono font-semibold text-[11px]">-5.00%</span>
              </div>
            </div>

            <!-- KPI 5: Margen Utilizado -->
            <div class="p-4 sm:p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs flex flex-col justify-between hover:border-[#D1D1D6] transition">
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-[11px] uppercase tracking-wider font-semibold text-[#6E6E73] truncate">Margen Utilizado</span>
                  <div class="h-6 w-6 rounded-lg bg-[#ECFDF5] flex items-center justify-center text-[#065F46] shrink-0">
                    <i class="fa-solid fa-gauge text-[11px]"></i>
                  </div>
                </div>
                <div class="text-lg sm:text-2xl font-bold font-mono text-[#1D1D1F] tracking-tight" id="cockpit-kpi-margin-used">0.85%</div>
              </div>
              <div class="mt-3 pt-2.5 border-t border-[#F2F2F7] flex items-center justify-between text-[11px]">
                <span class="text-[#86868B] font-medium">Apalancamiento</span>
                <span class="badge-success-live font-mono text-[10px] py-0.5 px-1.5">Seguro</span>
              </div>
            </div>

            <!-- KPI 6: Exposición Neta -->
            <div class="p-4 sm:p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs flex flex-col justify-between hover:border-[#D1D1D6] transition">
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-[11px] uppercase tracking-wider font-semibold text-[#6E6E73] truncate">Exposición Neta</span>
                  <div class="h-6 w-6 rounded-lg bg-[#EEF2FF] flex items-center justify-center text-[#3C45A5] shrink-0">
                    <i class="fa-solid fa-arrows-split-up-and-left text-[11px]"></i>
                  </div>
                </div>
                <div class="text-lg sm:text-2xl font-bold font-mono text-[#3C45A5] tracking-tight" id="cockpit-kpi-net-exposure">LONG 100%</div>
              </div>
              <div class="mt-3 pt-2.5 border-t border-[#F2F2F7] flex items-center justify-between text-[11px]">
                <span class="text-[#86868B] font-medium">Dirección</span>
                <span class="badge-neutral-soft font-mono text-[10px] py-0.5 px-1.5" id="cockpit-kpi-net-subtext">US500 / USTEC</span>
              </div>
            </div>

          </div>

          <!-- ==================== CUENTAS ACTIVAS EN TIEMPO REAL (MT5 + HYPERLIQUID) ==================== -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
            
            <!-- TARJETA CUENTA 1: IC MARKETS MT5 DEMO (PROP FIRM FORWARD TEST) -->
            <div class="p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs space-y-4 hover:border-[#D1D1D6] transition">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <div class="h-10 w-10 rounded-xl bg-[#EEF2FF] border border-[#E0E7FF] flex items-center justify-center text-[#3C45A5]">
                    <i class="fa-solid fa-building-columns text-base"></i>
                  </div>
                  <div>
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-bold text-[#1D1D1F]">IC Markets · MT5 Demo</span>
                      <span id="cockpit-mt5-status-badge" class="badge-success-live font-mono text-[10px]">● CONECTADA</span>
                    </div>
                    <div class="text-[11px] text-[#6E6E73] font-mono">Cuenta <span id="cockpit-mt5-account-id">53120791</span> · ICMarketsSC-Demo</div>
                  </div>
                </div>
                <button onclick="switchTab('forward')" class="btn-secondary text-[11px] py-1.5 px-3 flex items-center gap-1 cursor-pointer">
                  <span>Ver Forward</span>
                  <i class="fa-solid fa-arrow-right text-[10px]"></i>
                </button>
              </div>

              <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 bg-[#FAFAFC] p-3.5 rounded-xl border border-[#E5E5EA] text-xs font-mono">
                <div>
                  <span class="text-[10px] text-[#86868B] block uppercase tracking-wider mb-0.5">Balance</span>
                  <span id="cockpit-mt5-balance" class="font-bold text-[#1D1D1F] text-sm">$984.53</span>
                </div>
                <div>
                  <span class="text-[10px] text-[#86868B] block uppercase tracking-wider mb-0.5">Equity</span>
                  <span id="cockpit-mt5-equity" class="font-bold text-[#1D1D1F] text-sm">$979.95</span>
                </div>
                <div>
                  <span class="text-[10px] text-[#86868B] block uppercase tracking-wider mb-0.5">PnL Realizado</span>
                  <span id="cockpit-mt5-realized" class="font-bold text-[#D70015] text-sm">-$15.47</span>
                </div>
                <div>
                  <span class="text-[10px] text-[#86868B] block uppercase tracking-wider mb-0.5">PnL Flotante</span>
                  <span id="cockpit-mt5-floating" class="font-bold text-[#D70015] text-sm">-$4.58</span>
                </div>
              </div>

              <div class="flex items-center justify-between text-xs text-[#6E6E73] pt-1">
                <span class="flex items-center gap-1.5">
                  <i class="fa-solid fa-shield-halved text-[#3C45A5] text-xs"></i>
                  <span>Riesgo Dinámico Compuesto 1.5%</span>
                </span>
                <span class="font-mono text-[11px] text-[#1D1D1F] font-semibold">US500 · USTEC · EURUSD</span>
              </div>
            </div>

            <!-- TARJETA CUENTA 2: HYPERLIQUID TESTNET (CRYPTO DEX) -->
            <div class="p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs space-y-4 hover:border-[#D1D1D6] transition">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <div class="h-10 w-10 rounded-xl bg-[#ECFDF5] border border-[#A7F3D0] flex items-center justify-center text-[#065F46]">
                    <i class="fa-brands fa-ethereum text-base"></i>
                  </div>
                  <div>
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-bold text-[#1D1D1F]">Hyperliquid L1 Testnet</span>
                      <span id="cockpit-hl-status-badge" class="badge-success-live font-mono text-[10px]">● SYNCD</span>
                    </div>
                    <div class="text-[11px] text-[#6E6E73] font-mono">DEX Perpetuos · Arbitrum L1</div>
                  </div>
                </div>
                <button onclick="switchTab('forward')" class="btn-secondary text-[11px] py-1.5 px-3 flex items-center gap-1 cursor-pointer">
                  <span>Ver Forward</span>
                  <i class="fa-solid fa-arrow-right text-[10px]"></i>
                </button>
              </div>

              <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 bg-[#FAFAFC] p-3.5 rounded-xl border border-[#E5E5EA] text-xs font-mono">
                <div>
                  <span class="text-[10px] text-[#86868B] block uppercase tracking-wider mb-0.5">Balance</span>
                  <span id="cockpit-hl-balance" class="font-bold text-[#1D1D1F] text-sm">1,013.56 USDC</span>
                </div>
                <div>
                  <span class="text-[10px] text-[#86868B] block uppercase tracking-wider mb-0.5">Equity</span>
                  <span id="cockpit-hl-equity" class="font-bold text-[#1D1D1F] text-sm">1,013.56 USDC</span>
                </div>
                <div>
                  <span class="text-[10px] text-[#86868B] block uppercase tracking-wider mb-0.5">PnL Realizado</span>
                  <span id="cockpit-hl-realized" class="font-bold text-[#065F46] text-sm">+$13.56</span>
                </div>
                <div>
                  <span class="text-[10px] text-[#86868B] block uppercase tracking-wider mb-0.5">PnL Flotante</span>
                  <span id="cockpit-hl-floating" class="font-bold text-[#1D1D1F] text-sm">$0.00</span>
                </div>
              </div>

              <div class="flex items-center justify-between text-xs text-[#6E6E73] pt-1">
                <span class="flex items-center gap-1.5">
                  <i class="fa-solid fa-bolt text-[#065F46] text-xs"></i>
                  <span>STRAT-FAST-035 (BTC 1h)</span>
                </span>
                <span class="font-mono text-[11px] text-[#1D1D1F] font-semibold">14 bps Taker + Funding 1h</span>
              </div>
            </div>

          </div>

          <!-- ==================== BANNER INTEGRADO: FILTRO DE NOTICIAS MACRO (±5 MIN) ==================== -->
          <div id="cockpit-news-risk-banner" class="p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div class="flex items-start sm:items-center gap-3.5">
              <div class="h-10 w-10 rounded-xl bg-[#EEF2FF] border border-[#E0E7FF] flex items-center justify-center text-[#3C45A5] shrink-0 mt-0.5 sm:mt-0">
                <i class="fa-solid fa-newspaper text-base"></i>
              </div>
              <div class="space-y-0.5">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="text-xs font-bold text-[#1D1D1F]">Filtro de Riesgo Macro (ForexFactory / FairEconomy)</span>
                  <span id="cockpit-news-state-badge" class="badge-success-live font-mono text-[10px]">● OPERATIVA PERMITIDA</span>
                </div>
                <p class="text-xs text-[#6E6E73]">
                  Protección institucional estricta: Se prohíbe abrir órdenes y se rechaza ejecución <strong class="text-[#1D1D1F]">5 min antes y 5 min después</strong> de eventos macro High Impact (USD / EUR).
                </p>
              </div>
            </div>
            <div class="flex items-center gap-3 shrink-0 bg-[#FAFAFC] px-3.5 py-2 rounded-xl border border-[#E5E5EA] text-xs font-mono">
              <div class="text-right">
                <div class="text-[10px] text-[#86868B] uppercase">Próximo Evento High Impact</div>
                <div id="cockpit-news-next-event" class="font-bold text-[#1D1D1F]">Sin eventos inmediatos (&gt;6h)</div>
              </div>
              <div class="h-7 w-7 rounded-lg bg-[#EBF5FB] flex items-center justify-center text-[#3C45A5]">
                <i class="fa-solid fa-clock text-xs"></i>
              </div>
            </div>
          </div>

          <!-- ==================== MARCO DE PRESERVACIÓN DE CAPITAL E INFRAESTRUCTURA ==================== -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="rounded-2xl p-5 border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs space-y-3">
              <div class="flex items-center justify-between border-b border-[#F2F2F7] pb-2">
                <h3 class="text-xs font-bold text-[#1D1D1F] uppercase tracking-wider flex items-center">
                  <i class="fa-solid fa-shield-halved text-[#D70015] mr-2"></i> Marco de Preservación de Capital
                </h3>
                <span class="badge-success-live font-mono">ACTIVO</span>
              </div>
              <div class="space-y-2 text-xs font-mono">
                <div class="flex justify-between p-2.5 rounded-lg bg-[#FAFAFC] border border-[#E5E5EA]">
                  <span class="text-[#6E6E73]">Prop Firm Challenge ($100k):</span>
                  <span class="text-[#1D1D1F] font-bold">EOD DD &le; 3.5% | Pérdida Diaria &le; 2.0%</span>
                </div>
                <div class="flex justify-between p-2.5 rounded-lg bg-[#FAFAFC] border border-[#E5E5EA]">
                  <span class="text-[#6E6E73]">Crypto Propio (Hyperliquid):</span>
                  <span class="text-[#1D1D1F] font-bold">Retorno &ge; 30% Anual | Superar Buy & Hold</span>
                </div>
                <div class="flex justify-between p-2.5 rounded-lg bg-[#FAFAFC] border border-[#E5E5EA]">
                  <span class="text-[#6E6E73]">Fricciones Modeladas:</span>
                  <span class="text-[#065F46] font-bold">0.4 - 1.5 pts + 0.14% round-trip</span>
                </div>
              </div>
            </div>

            <div class="rounded-2xl p-5 border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs space-y-3">
              <div class="flex items-center justify-between border-b border-[#F2F2F7] pb-2">
                <h3 class="text-xs font-bold text-[#1D1D1F] uppercase tracking-wider flex items-center">
                  <i class="fa-solid fa-network-wired text-[#3C45A5] mr-2"></i> Infraestructura de Ejecución
                </h3>
                <span class="badge-brand-indigo font-mono">2 CUENTAS SYNC</span>
              </div>
              <div class="space-y-2 text-xs font-mono">
                <div class="flex justify-between p-2.5 rounded-lg bg-[#FAFAFC] border border-[#E5E5EA]">
                  <span class="text-[#6E6E73]">Daemons Prop Firm:</span>
                  <span class="text-[#1D1D1F] font-bold">PROP-NDX-005 (2h) & PROP-SPX-005 (1D)</span>
                </div>
                <div class="flex justify-between p-2.5 rounded-lg bg-[#FAFAFC] border border-[#E5E5EA]">
                  <span class="text-[#6E6E73]">Daemons Crypto Paper:</span>
                  <span class="text-[#1D1D1F] font-bold">STRAT-FAST-035 (BTC 1h)</span>
                </div>
                <div class="flex justify-between p-2.5 rounded-lg bg-[#FAFAFC] border border-[#E5E5EA]">
                  <span class="text-[#6E6E73]">Supervisión:</span>
                  <span class="text-[#065F46] font-bold">Enjambre OpenMausBot 24/7 (systemd)</span>
                </div>
              </div>
            </div>
          </div>
"""

# Reconstruct file with new inner HTML
modified_content = content[:pos_start + len(start_marker)] + new_inner_html + "\n\n      " + content[last_div_idx:]

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(modified_content)

print("Cockpit HTML successfully updated!")
