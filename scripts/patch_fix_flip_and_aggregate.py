from pathlib import Path

BASE_DIR = Path(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot")
INDEX_PATH = BASE_DIR / "dashboard" / "templates" / "index.html"

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Target the harmful overwriting block inside fetchTelemetry
bad_block = """        latestTelemetryData = d;
        updateCockpitKPIs(currentDeskMode);

        // Actualización dinámica de los 6 KPIs independientes del Cockpit General
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
        }"""

clean_block = """        latestTelemetryData = d;
        updateCockpitKPIs(currentDeskMode);"""

content_norm = content.replace("\r\n", "\n")
bad_norm = bad_block.replace("\r\n", "\n")
clean_norm = clean_block.replace("\r\n", "\n")

if bad_norm in content_norm:
    content_norm = content_norm.replace(bad_norm, clean_norm)
    content = content_norm
    print("Harmful overwriting block removed from fetchTelemetry!")
else:
    print("bad_block not found directly, searching snippet...")
    idx1 = content_norm.find("latestTelemetryData = d;\n        updateCockpitKPIs(currentDeskMode);")
    idx2 = content_norm.find("// Cuentas Individuales: MT5 Demo", idx1)
    if idx1 != -1 and idx2 != -1:
        content_norm = content_norm[:idx1] + "latestTelemetryData = d;\n        updateCockpitKPIs(currentDeskMode);\n\n        " + content_norm[idx2:]
        content = content_norm
        print("Harmful overwriting block removed via index slicing!")
    else:
        print("Could not find boundaries for removal!")
        exit(1)

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated index.html successfully!")
