import re
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot")
INDEX_PATH = BASE_DIR / "dashboard" / "templates" / "index.html"

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Remove Sidebar bottom widget (lines 610-638)
sidebar_widget_pattern = r'<!-- Widget Inferior de Control Secundario -->\s*<div class="mt-8 pt-4 border-t border-\[#E6E2D8\]">.*?</div>\s*</div>\s*</aside>'
match_widget = re.search(sidebar_widget_pattern, content, re.DOTALL)
if match_widget:
    content = content[:match_widget.start()] + '</aside>' + content[match_widget.end():]
    print("Removed sidebar bottom widget!")
else:
    print("Sidebar widget pattern not matched directly, trying alternative search")
    idx_tele = content.find('<!-- Widget Inferior de Control Secundario -->')
    if idx_tele != -1:
        idx_aside = content.find('</aside>', idx_tele)
        if idx_aside != -1:
            content = content[:idx_tele] + content[idx_aside:]
            print("Removed sidebar bottom widget via string slice!")

# 2. In Cockpit General: update Header and Account cards to support CAPITAL_PROPIO vs PROP_FIRM
cockpit_start = content.find('<div id="tab-content-dashboard" class="tab-pane space-y-6">')
cockpit_end = content.find('<!-- ==================== PESTAÑA 2: FASE 1 - BACKTESTS (CALIBRACIÓN 12M) ====================')

if cockpit_start == -1 or cockpit_end == -1:
    print("Cockpit markers not found!")
    exit(1)

# Find last </div> before cockpit_end
before_end = content[:cockpit_end]
last_div_idx = before_end.rfind('</div>')

new_cockpit_html = """

          <!-- ==================== HEADER EJECUTIVO & CONTROLES GLOBALES ==================== -->
          <div class="p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <span id="cockpit-desk-badge" class="badge-brand-indigo font-mono">CAPITAL PROPIO</span>
                <span id="cockpit-sync-badge" class="badge-success-live font-mono">● 2 CUENTAS CONECTADAS</span>
                <span id="cockpit-news-badge" class="badge-neutral-soft font-mono"><i class="fa-solid fa-newspaper mr-1 text-[#3C45A5]"></i>FILTRO NOTICIAS: ±5 MIN</span>
              </div>
              <h1 class="text-xl sm:text-2xl font-bold text-[#1D1D1F] tracking-tight" id="cockpit-header-title">Monitoreo Unificado · Capital Propio</h1>
              <p class="text-xs text-[#6E6E73]" id="cockpit-header-desc">Supervisión consolidada de capital propio en Forward Test: IC Markets (MT5 $1,000) y Hyperliquid (Crypto DEX 1,000 USDC).</p>
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
                <span class="text-[#86868B] font-medium" id="cockpit-kpi-total-sublabel">Suma Cuentas FT</span>
                <span id="cockpit-kpi-total-subtext" class="badge-brand-indigo font-mono text-[10px] py-0.5 px-1.5">MT5 + DEX</span>
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
                <span class="text-[#86868B] font-medium" id="cockpit-kpi-drawdown-label">Límite máx</span>
                <span class="text-[#D70015] font-mono font-semibold text-[11px]" id="cockpit-kpi-drawdown-limit">-5.00%</span>
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
                <span id="cockpit-kpi-margin-badge" class="badge-success-live font-mono text-[10px] py-0.5 px-1.5">Seguro</span>
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

          <!-- ==================== CUENTAS ACTIVAS: MODO CAPITAL PROPIO ==================== -->
          <div id="cockpit-accounts-cap-propio" class="grid grid-cols-1 lg:grid-cols-2 gap-5">
            
            <!-- TARJETA CUENTA 1: IC MARKETS MT5 DEMO (CAPITAL PROPIO TRADFI) -->
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

          <!-- ==================== CUENTAS ACTIVAS: MODO FONDEO (PROP FIRM) ==================== -->
          <div id="cockpit-accounts-prop-firm" class="grid grid-cols-1 lg:grid-cols-2 gap-5 hidden">
            
            <!-- TARJETA CUENTA 1: CHALLENGE $100K EVALUATION (PROP FIRM MAESTRA) -->
            <div class="p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs space-y-4 hover:border-[#D1D1D6] transition">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <div class="h-10 w-10 rounded-xl bg-[#EEF2FF] border border-[#E0E7FF] flex items-center justify-center text-[#3C45A5]">
                    <i class="fa-solid fa-trophy text-base"></i>
                  </div>
                  <div>
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-bold text-[#1D1D1F]">Prop Firm Challenge · $100k</span>
                      <span class="badge-success-live font-mono text-[10px]">● EVALUATION (FASE 1)</span>
                    </div>
                    <div class="text-[11px] text-[#6E6E73] font-mono">ICMarketsSC / Rithmic CME · Target +10.0%</div>
                  </div>
                </div>
                <button onclick="switchTab('forward')" class="btn-secondary text-[11px] py-1.5 px-3 flex items-center gap-1 cursor-pointer">
                  <span>Ver Fondeo</span>
                  <i class="fa-solid fa-arrow-right text-[10px]"></i>
                </button>
              </div>

              <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 bg-[#FAFAFC] p-3.5 rounded-xl border border-[#E5E5EA] text-xs font-mono">
                <div>
                  <span class="text-[10px] text-[#86868B] block uppercase tracking-wider mb-0.5">Balance</span>
                  <span id="cockpit-pf-balance" class="font-bold text-[#1D1D1F] text-sm">$100,002.01</span>
                </div>
                <div>
                  <span class="text-[10px] text-[#86868B] block uppercase tracking-wider mb-0.5">Equity EOD</span>
                  <span id="cockpit-pf-equity" class="font-bold text-[#1D1D1F] text-sm">$100,002.01</span>
                </div>
                <div>
                  <span class="text-[10px] text-[#86868B] block uppercase tracking-wider mb-0.5">PnL Realizado</span>
                  <span id="cockpit-pf-realized" class="font-bold text-[#065F46] text-sm">+$2.01</span>
                </div>
                <div>
                  <span class="text-[10px] text-[#86868B] block uppercase tracking-wider mb-0.5">EOD Drawdown</span>
                  <span id="cockpit-pf-dd" class="font-bold text-[#065F46] text-sm">0.00%</span>
                </div>
              </div>

              <div class="flex items-center justify-between text-xs text-[#6E6E73] pt-1">
                <span class="flex items-center gap-1.5">
                  <i class="fa-solid fa-shield-halved text-[#3C45A5] text-xs"></i>
                  <span>Regla 40% Consistencia & EOD DD &le; 3.5%</span>
                </span>
                <span class="font-mono text-[11px] text-[#1D1D1F] font-semibold">20 Modelos Incubando</span>
              </div>
            </div>

            <!-- TARJETA CUENTA 2: LIBRO VIRTUAL MULTI-ESTRATEGIA (INCUBACIÓN PROP FIRM) -->
            <div class="p-5 rounded-2xl border border-[#E5E5EA] bg-[#FFFFFF] shadow-xs space-y-4 hover:border-[#D1D1D6] transition">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <div class="h-10 w-10 rounded-xl bg-[#F2F2F7] border border-[#E5E5EA] flex items-center justify-center text-[#1D1D1F]">
                    <i class="fa-solid fa-microchip text-base"></i>
                  </div>
                  <div>
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-bold text-[#1D1D1F]">Enjambre de Simulación CME / CFD</span>
                      <span class="badge-brand-indigo font-mono text-[10px]">● VIRTUAL BOOKS</span>
                    </div>
                    <div class="text-[11px] text-[#6E6E73] font-mono">Spreads en vivo + Slippage 0.4-1.5 pts</div>
                  </div>
                </div>
                <button onclick="switchTab('orchestrator')" class="btn-secondary text-[11px] py-1.5 px-3 flex items-center gap-1 cursor-pointer">
                  <span>Orquestador</span>
                  <i class="fa-solid fa-arrow-right text-[10px]"></i>
                </button>
              </div>

              <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 bg-[#FAFAFC] p-3.5 rounded-xl border border-[#E5E5EA] text-xs font-mono">
                <div>
                  <span class="text-[10px] text-[#86868B] block uppercase tracking-wider mb-0.5">Asignación Base</span>
                  <span class="font-bold text-[#1D1D1F] text-sm">$1,000 / mod</span>
                </div>
                <div>
                  <span class="text-[10px] text-[#86868B] block uppercase tracking-wider mb-0.5">Riesgo / Trade</span>
                  <span class="font-bold text-[#1D1D1F] text-sm">1.0% ($10 USD)</span>
                </div>
                <div>
                  <span class="text-[10px] text-[#86868B] block uppercase tracking-wider mb-0.5">Guardián MC</span>
                  <span class="font-bold text-[#065F46] text-sm">Vigilancia P95</span>
                </div>
                <div>
                  <span class="text-[10px] text-[#86868B] block uppercase tracking-wider mb-0.5">Blackout Macro</span>
                  <span class="font-bold text-[#065F46] text-sm">&plusmn;5 min Activo</span>
                </div>
              </div>

              <div class="flex items-center justify-between text-xs text-[#6E6E73] pt-1">
                <span class="flex items-center gap-1.5">
                  <i class="fa-solid fa-network-wired text-[#3C45A5] text-xs"></i>
                  <span>PROP-NDX-005 · PROP-SPX-005 · EURUSD</span>
                </span>
                <span class="font-mono text-[11px] text-[#1D1D1F] font-semibold">CME Globex + LMAX</span>
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
"""

content = content[:cockpit_start + len('<div id="tab-content-dashboard" class="tab-pane space-y-6">')] + new_cockpit_html + "\n\n      " + content[last_div_idx:]
print("Cockpit HTML updated with bifocal support and removed bottom text cards!")

# 3. Update JavaScript: updateCockpitKPIs(mode) and switchDeskMode(mode)
js_update_cockpit = """
    let latestTelemetryData = null;

    function updateCockpitKPIs(deskMode) {
      const mode = deskMode || currentDeskMode || 'CAPITAL_PROPIO';
      const d = latestTelemetryData;
      if (!d) return;

      const deskData = (d.desks && d.desks[mode]) ? d.desks[mode] : null;

      // Update Header
      const headerTitle = document.getElementById('cockpit-header-title');
      const headerDesc = document.getElementById('cockpit-header-desc');
      const deskBadge = document.getElementById('cockpit-desk-badge');
      const syncBadge = document.getElementById('cockpit-sync-badge');

      if (mode === 'CAPITAL_PROPIO') {
        if (headerTitle) headerTitle.innerText = 'Monitoreo Unificado · Capital Propio';
        if (headerDesc) headerDesc.innerText = 'Supervisión consolidada de capital propio en Forward Test: IC Markets (MT5 $1,000) y Hyperliquid (Crypto DEX 1,000 USDC).';
        if (deskBadge) {
          deskBadge.innerText = 'CAPITAL PROPIO';
          deskBadge.className = 'badge-brand-indigo font-mono';
        }
        if (syncBadge) {
          syncBadge.innerText = '● 2 CUENTAS SYNC';
          syncBadge.className = 'badge-success-live font-mono';
        }
        // Account sections toggle
        const capSec = document.getElementById('cockpit-accounts-cap-propio');
        const propSec = document.getElementById('cockpit-accounts-prop-firm');
        if (capSec) capSec.classList.remove('hidden');
        if (propSec) propSec.classList.add('hidden');
      } else {
        if (headerTitle) headerTitle.innerText = 'Monitoreo Unificado · Cuentas de Fondeo';
        if (headerDesc) headerDesc.innerText = 'Supervisión de cuenta evaluativa Prop Firm: Challenge $100,000 USD (Futuros CME Globex & CFDs).';
        if (deskBadge) {
          deskBadge.innerText = 'CUENTAS DE FONDEO';
          deskBadge.className = 'badge-brand-indigo font-mono';
        }
        if (syncBadge) {
          syncBadge.innerText = '● CHALLENGE $100K ACTIVO';
          syncBadge.className = 'badge-success-live font-mono';
        }
        // Account sections toggle
        const capSec = document.getElementById('cockpit-accounts-cap-propio');
        const propSec = document.getElementById('cockpit-accounts-prop-firm');
        if (capSec) capSec.classList.add('hidden');
        if (propSec) propSec.classList.remove('hidden');
      }

      // Values from deskData or fallbacks
      const balVal = deskData ? deskData.total_balance_usd : (mode === 'CAPITAL_PROPIO' ? d.total_balance_usd : 100002.01);
      const rPnlVal = deskData ? deskData.total_realized_pnl_usd : (mode === 'CAPITAL_PROPIO' ? d.total_realized_pnl_usd : 2.01);
      const fPnlVal = deskData ? deskData.total_floating_pnl_usd : (mode === 'CAPITAL_PROPIO' ? (Number(d.total_equity_usd) - Number(d.total_balance_usd)) : 0.0);
      const ddVal = deskData ? deskData.drawdown_pct : 0.0;
      const marginVal = deskData ? deskData.margin_used_pct : 0.0;
      const expVal = deskData ? deskData.net_exposure : 'FLAT (0.0%)';
      const expSub = deskData ? deskData.net_subtext : (mode === 'CAPITAL_PROPIO' ? 'US500 / USTEC' : 'Futuros CME & CFDs');
      const subBadgeText = deskData ? deskData.sub_badge : (mode === 'CAPITAL_PROPIO' ? 'MT5 + DEX' : 'Challenge $100k');
      const riskLimitVal = deskData ? deskData.risk_limit_val : (mode === 'CAPITAL_PROPIO' ? '-5.00%' : '-3.50%');
      const riskLimitLabel = deskData ? deskData.risk_limit_label : (mode === 'CAPITAL_PROPIO' ? 'Límite máx' : 'Límite EOD');

      // 1. Balance Total FT
      const kpiBal = document.getElementById('cockpit-kpi-total-balance');
      const kpiSubText = document.getElementById('cockpit-kpi-total-subtext');
      if (kpiBal) kpiBal.innerText = '$' + Number(balVal).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      if (kpiSubText) kpiSubText.innerText = subBadgeText;

      // 2. PnL Realizado Total
      const kpiRealized = document.getElementById('cockpit-kpi-realized-pnl');
      const kpiRealizedBadge = document.getElementById('cockpit-kpi-realized-badge');
      if (kpiRealized) {
        const rPnl = Number(rPnlVal);
        kpiRealized.innerText = (rPnl >= 0 ? '+$' : '-$') + Math.abs(rPnl).toFixed(2);
        kpiRealized.className = `text-lg sm:text-2xl font-bold font-mono tracking-tight ${rPnl >= 0 ? 'text-[#065F46]' : 'text-[#D70015]'}`;
        if (kpiRealizedBadge) {
          const totB = Number(balVal) || 100000;
          const pct = (rPnl / totB) * 100;
          kpiRealizedBadge.innerText = (pct >= 0 ? '+' : '') + pct.toFixed(pct > 0.01 || pct < -0.01 ? 2 : 3) + '%';
          kpiRealizedBadge.className = `font-mono text-[10px] py-0.5 px-1.5 ${pct >= 0 ? 'badge-success-live' : 'badge-warning-risk'}`;
        }
      }

      // 3. PnL Flotante Total
      const kpiFloating = document.getElementById('cockpit-kpi-floating-pnl');
      const kpiFloatingBadge = document.getElementById('cockpit-kpi-floating-badge');
      if (kpiFloating) {
        const floatPnl = Number(fPnlVal);
        kpiFloating.innerText = (floatPnl >= 0 ? '+$' : '-$') + Math.abs(floatPnl).toFixed(2);
        kpiFloating.className = `text-lg sm:text-2xl font-bold font-mono tracking-tight ${floatPnl >= 0 ? 'text-[#065F46]' : 'text-[#D70015]'}`;
        if (kpiFloatingBadge) {
          const totB = Number(balVal) || 100000;
          const pct = totB > 0 ? (floatPnl / totB) * 100 : 0;
          kpiFloatingBadge.innerText = (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%';
          kpiFloatingBadge.className = `font-mono text-[10px] py-0.5 px-1.5 ${pct >= 0 ? 'badge-success-live' : 'badge-warning-risk'}`;
        }
      }

      // 4. Drawdown Cartera
      const kpiDd = document.getElementById('cockpit-kpi-drawdown');
      const kpiDdLabel = document.getElementById('cockpit-kpi-drawdown-label');
      const kpiDdLimit = document.getElementById('cockpit-kpi-drawdown-limit');
      if (kpiDd) {
        const dVal = Number(ddVal);
        kpiDd.innerText = (dVal <= 0 ? '' : '-') + Math.abs(dVal).toFixed(2) + '%';
      }
      if (kpiDdLabel) kpiDdLabel.innerText = riskLimitLabel;
      if (kpiDdLimit) kpiDdLimit.innerText = riskLimitVal;

      // 5. Margen Utilizado
      const kpiMargin = document.getElementById('cockpit-kpi-margin-used');
      if (kpiMargin) kpiMargin.innerText = Number(marginVal).toFixed(2) + '%';

      // 6. Exposición Neta
      const kpiExp = document.getElementById('cockpit-kpi-net-exposure');
      const kpiExpSub = document.getElementById('cockpit-kpi-net-subtext');
      if (kpiExp) kpiExp.innerText = expVal;
      if (kpiExpSub) kpiExpSub.innerText = expSub;
    }
    window.updateCockpitKPIs = updateCockpitKPIs;
"""

# Replace in fetchTelemetry to save latestTelemetryData and call updateCockpitKPIs(currentDeskMode)
tele_patch_target = """        // Actualización dinámica de los 6 KPIs independientes del Cockpit General
        const kpiBal = document.getElementById('cockpit-kpi-total-balance');"""

tele_patch_replacement = """        latestTelemetryData = d;
        updateCockpitKPIs(currentDeskMode);

        // Actualización dinámica de los 6 KPIs independientes del Cockpit General
        const kpiBal = document.getElementById('cockpit-kpi-total-balance');"""

if tele_patch_target in content:
    content = content.replace(tele_patch_target, tele_patch_replacement)
    print("Patched fetchTelemetry with latestTelemetryData & updateCockpitKPIs!")

# Add updateCockpitKPIs function before switchDeskMode
if "function updateCockpitKPIs" not in content:
    content = content.replace("function switchDeskMode(mode) {", js_update_cockpit + "\n    function switchDeskMode(mode) {")
    print("Added updateCockpitKPIs function!")

# In switchDeskMode, call updateCockpitKPIs(mode)
switch_desk_target = "    function switchDeskMode(mode) {\n      currentDeskMode = mode;"
switch_desk_replacement = "    function switchDeskMode(mode) {\n      currentDeskMode = mode;\n      updateCockpitKPIs(mode);"

if switch_desk_target in content:
    content = content.replace(switch_desk_target, switch_desk_replacement)
    print("Added updateCockpitKPIs(mode) call inside switchDeskMode!")

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated index.html completely!")
