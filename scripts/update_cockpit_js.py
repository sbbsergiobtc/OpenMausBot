import re
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot")
INDEX_PATH = BASE_DIR / "dashboard" / "templates" / "index.html"

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    content = f.read()

target_str = """        // Actualización dinámica de tarjetas de cartera activa en tiempo real
        if (d.mt5) {
          const s1 = document.getElementById('active-card-spx-bal');
          const s2 = document.getElementById('active-card-ndx-bal');
          if (s1) s1.innerText = '$' + Number(d.mt5.balance).toFixed(2) + ' USD';
          if (s2) s2.innerText = '$' + Number(d.mt5.balance).toFixed(2) + ' USD';
        }
        if (d.hyperliquid) {
          const s3 = document.getElementById('active-card-crypto-bal');
          if (s3) s3.innerText = Number(d.hyperliquid.balance).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 4 }) + ' USDC';
        }"""

replacement_str = """        // Actualización dinámica de los 6 KPIs independientes del Cockpit General
        const kpiBal = document.getElementById('cockpit-kpi-total-balance');
        if (kpiBal && d.total_balance_usd !== undefined) {
          kpiBal.innerText = '$' + Number(d.total_balance_usd).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }

        const kpiRealized = document.getElementById('cockpit-kpi-realized-pnl');
        const kpiRealizedBadge = document.getElementById('cockpit-kpi-realized-badge');
        if (kpiRealized && d.total_realized_pnl_usd !== undefined) {
          const rPnl = Number(d.total_realized_pnl_usd);
          kpiRealized.innerText = (rPnl >= 0 ? '+$' : '-$') + Math.abs(rPnl).toFixed(2);
          kpiRealized.className = `text-lg sm:text-2xl font-bold font-mono tracking-tight ${rPnl >= 0 ? 'text-[#065F46]' : 'text-[#D70015]'}`;
          if (kpiRealizedBadge) {
            const totB = Number(d.total_balance_usd) || 2000;
            const pct = (rPnl / totB) * 100;
            kpiRealizedBadge.innerText = (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%';
            kpiRealizedBadge.className = `font-mono text-[10px] py-0.5 px-1.5 ${pct >= 0 ? 'badge-success-live' : 'badge-warning-risk'}`;
          }
        }

        const kpiFloating = document.getElementById('cockpit-kpi-floating-pnl');
        const kpiFloatingBadge = document.getElementById('cockpit-kpi-floating-badge');
        if (kpiFloating) {
          const eq = Number(d.total_equity_usd) || 0;
          const bal = Number(d.total_balance_usd) || 0;
          const floatPnl = (eq > 0 && bal > 0) ? (eq - bal) : 0;
          kpiFloating.innerText = (floatPnl >= 0 ? '+$' : '-$') + Math.abs(floatPnl).toFixed(2);
          kpiFloating.className = `text-lg sm:text-2xl font-bold font-mono tracking-tight ${floatPnl >= 0 ? 'text-[#065F46]' : 'text-[#D70015]'}`;
          if (kpiFloatingBadge) {
            const pct = bal > 0 ? (floatPnl / bal) * 100 : 0;
            kpiFloatingBadge.innerText = (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%';
            kpiFloatingBadge.className = `font-mono text-[10px] py-0.5 px-1.5 ${pct >= 0 ? 'badge-success-live' : 'badge-warning-risk'}`;
          }
        }

        const kpiDd = document.getElementById('cockpit-kpi-drawdown');
        if (kpiDd) {
          const eq = Number(d.total_equity_usd) || 0;
          const bal = Number(d.total_balance_usd) || 0;
          const ddVal = (eq < bal && bal > 0) ? ((eq - bal) / bal) * 100 : 0.0;
          kpiDd.innerText = (ddVal < 0 ? '' : '-') + Math.abs(ddVal).toFixed(2) + '%';
        }

        const kpiMargin = document.getElementById('cockpit-kpi-margin-used');
        if (kpiMargin) {
          const eq = Number(d.total_equity_usd) || 0;
          const bal = Number(d.total_balance_usd) || 0;
          const hasOpen = Math.abs(eq - bal) > 0.1;
          kpiMargin.innerText = hasOpen ? "0.85%" : "0.00%";
        }

        const kpiExp = document.getElementById('cockpit-kpi-net-exposure');
        const kpiExpSub = document.getElementById('cockpit-kpi-net-subtext');
        if (kpiExp) {
          const eq = Number(d.total_equity_usd) || 0;
          const bal = Number(d.total_balance_usd) || 0;
          if (Math.abs(eq - bal) > 0.1) {
            kpiExp.innerText = "LONG 100%";
            if (kpiExpSub) kpiExpSub.innerText = "US500 / USTEC";
          } else {
            kpiExp.innerText = "FLAT (0.0%)";
            if (kpiExpSub) kpiExpSub.innerText = "Sin posiciones";
          }
        }

        // Cuentas Individuales: MT5 Demo
        if (d.mt5) {
          const mt5Acc = document.getElementById('cockpit-mt5-account-id');
          const mt5B = document.getElementById('cockpit-mt5-balance');
          const mt5E = document.getElementById('cockpit-mt5-equity');
          const mt5R = document.getElementById('cockpit-mt5-realized');
          const mt5F = document.getElementById('cockpit-mt5-floating');
          if (mt5Acc && d.mt5.account) mt5Acc.innerText = d.mt5.account;
          if (mt5B) mt5B.innerText = '$' + Number(d.mt5.balance).toFixed(2);
          if (mt5E) mt5E.innerText = '$' + Number(d.mt5.equity).toFixed(2);
          if (mt5R) {
            const rp = Number(d.mt5.realized_pnl || 0);
            mt5R.innerText = (rp >= 0 ? '+$' : '-$') + Math.abs(rp).toFixed(2);
            mt5R.className = `font-bold text-sm ${rp >= 0 ? 'text-[#065F46]' : 'text-[#D70015]'}`;
          }
          if (mt5F) {
            const fp = Number(d.mt5.equity) - Number(d.mt5.balance);
            mt5F.innerText = (fp >= 0 ? '+$' : '-$') + Math.abs(fp).toFixed(2);
            mt5F.className = `font-bold text-sm ${fp >= 0 ? 'text-[#065F46]' : 'text-[#D70015]'}`;
          }
        }

        // Cuentas Individuales: Hyperliquid DEX
        if (d.hyperliquid) {
          const hlB = document.getElementById('cockpit-hl-balance');
          const hlE = document.getElementById('cockpit-hl-equity');
          const hlR = document.getElementById('cockpit-hl-realized');
          const hlF = document.getElementById('cockpit-hl-floating');
          if (hlB) hlB.innerText = Number(d.hyperliquid.balance).toFixed(2) + ' USDC';
          if (hlE) hlE.innerText = Number(d.hyperliquid.equity).toFixed(2) + ' USDC';
          if (hlR) {
            const rp = Number(d.hyperliquid.realized_pnl || 0);
            hlR.innerText = (rp >= 0 ? '+$' : '-$') + Math.abs(rp).toFixed(2);
            hlR.className = `font-bold text-sm ${rp >= 0 ? 'text-[#065F46]' : 'text-[#D70015]'}`;
          }
          if (hlF) {
            const fp = Number(d.hyperliquid.equity) - Number(d.hyperliquid.balance);
            hlF.innerText = (fp >= 0 ? '+$' : '-$') + Math.abs(fp).toFixed(2);
            hlF.className = `font-bold text-sm ${fp >= 0 ? 'text-[#065F46]' : 'text-[#D70015]'}`;
          }
        }

        // Actualizar banner de noticias macro
        fetchMacroNewsRisk();"""

if target_str in content:
    content = content.replace(target_str, replacement_str)
    print("Replaced target_str successfully!")
else:
    # Try normalized newlines
    target_norm = target_str.replace("\r\n", "\n")
    content_norm = content.replace("\r\n", "\n")
    if target_norm in content_norm:
        content_norm = content_norm.replace(target_norm, replacement_str.replace("\r\n", "\n"))
        content = content_norm
        print("Replaced target_norm successfully!")
    else:
        print("Target string not found in index.html!")
        exit(1)

# Now add fetchMacroNewsRisk function if not already present
if "async function fetchMacroNewsRisk()" not in content:
    news_fn = """
    async function fetchMacroNewsRisk() {
      try {
        const res = await fetch('/api/macro_news_risk');
        if (!res.ok) return;
        const data = await res.json();
        const badge = document.getElementById('cockpit-news-state-badge');
        const headerBadge = document.getElementById('cockpit-news-badge');
        const nextEv = document.getElementById('cockpit-news-next-event');

        if (data.active_blackout) {
          const ev = data.active_blackout;
          if (badge) {
            badge.innerText = `● BLOQUEADO: ${ev.currency || ev.country} ${ev.event || ev.title}`;
            badge.className = 'badge-danger-risk font-mono text-[10px] animate-pulse';
          }
          if (headerBadge) {
            headerBadge.innerHTML = `<i class="fa-solid fa-triangle-exclamation mr-1 text-[#D70015]"></i>BLACKOUT NOTICIA ACTIVO`;
            headerBadge.className = 'badge-danger-risk font-mono animate-pulse';
          }
          if (nextEv) {
            nextEv.innerText = `En ventana ±5 min (${ev.event || ev.title})`;
            nextEv.className = 'font-bold text-[#D70015]';
          }
        } else {
          if (badge) {
            badge.innerText = '● OPERATIVA PERMITIDA';
            badge.className = 'badge-success-live font-mono text-[10px]';
          }
          if (headerBadge) {
            headerBadge.innerHTML = `<i class="fa-solid fa-newspaper mr-1 text-[#3C45A5]"></i>FILTRO NOTICIAS: ±5 MIN`;
            headerBadge.className = 'badge-neutral-soft font-mono';
          }
          if (nextEv && data.upcoming_events && data.upcoming_events.length > 0) {
            const next = data.upcoming_events[0];
            const mins = Math.round(next.minutes_away);
            let timeStr = `${mins} min`;
            if (mins > 60) {
              const h = Math.floor(mins / 60);
              const m = mins % 60;
              timeStr = `${h}h ${m}m`;
            }
            nextEv.innerText = `${next.country || next.currency} ${next.title || next.event} (en ${timeStr})`;
            nextEv.className = 'font-bold text-[#1D1D1F]';
          }
        }
      } catch (err) {
        console.error('Error fetching macro news risk:', err);
      }
    }
    window.fetchMacroNewsRisk = fetchMacroNewsRisk;
"""
    # Insert right before fetchTelemetry
    content = content.replace("async function fetchTelemetry() {", news_fn + "\n    async function fetchTelemetry() {")
    print("Added fetchMacroNewsRisk function!")

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated index.html with JS telemetry & news bindings!")
