import re
import os

BACKEND_PATH = r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py"
INDEX_PATH = r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html"

# 1. Update backend.py
with open(BACKEND_PATH, "r", encoding="utf-8") as f:
    backend_code = f.read()

# Modify get_analytics signature to accept lens
backend_code = re.sub(
    r'def get_analytics\(filter:\s*str\s*=\s*Query\([\'"]ALL[\'"]\)\):',
    r'def get_analytics(filter: str = Query("ALL"), lens: str = Query("EVALUATION")):',
    backend_code
)

# Apply 40% clamp in get_analytics if lens == 'EVALUATION'
clamp_logic_analytics = """    df = pd.DataFrame(subset)
    bifocal_data = compute_bifocal_metrics(df, initial_balance)

    # Si la lente activa es EVALUACIÓN: aplicar clamp de consistencia del 40% a todas las métricas
    if lens.upper() == 'EVALUATION' and not df.empty:
        raw_pnls = [float(p) for p in df['net_pnl_usd'].values]
        total_raw_profit = sum(p for p in raw_pnls if p > 0)
        consistency_cap = total_raw_profit * 0.40 if total_raw_profit > 0 else 999999.0
        clamped_pnls = [round(min(p, consistency_cap), 2) if p > 0 else p for p in raw_pnls]
        df['net_pnl_usd'] = clamped_pnls"""

# Replace the df initialization in get_analytics
old_df_init = "df = pd.DataFrame(subset)\n    bifocal_data = compute_bifocal_metrics(df, initial_balance)"
if old_df_init in backend_code:
    backend_code = backend_code.replace(old_df_init, clamp_logic_analytics, 1)
    print("[OK] Injected dynamic lens clamp into get_analytics in backend.py")
else:
    # Look for bifocal_data line
    backend_code = re.sub(
        r'bifocal_data\s*=\s*compute_bifocal_metrics\(df,\s*initial_balance\)',
        clamp_logic_analytics.replace("df = pd.DataFrame(subset)\n    ", ""),
        backend_code
    )
    print("[OK] Injected dynamic lens clamp via regex in backend.py")

# Modify get_trade_history signature to accept lens
backend_code = re.sub(
    r'def get_trade_history\(filter:\s*str\s*=\s*Query\([\'"]ALL[\'"]\)\):',
    r'def get_trade_history(filter: str = Query("ALL"), lens: str = Query("EVALUATION")):',
    backend_code
)

# Apply clamp in get_trade_history
clamp_trades_target = "enriched = enrich_trades_data(trades)"
clamp_trades_replacement = """# Si la lente activa es EVALUACIÓN: clampear trades que superen el 40% de consistencia
        if lens.upper() == 'EVALUATION' and len(trades) > 0:
            tot_p = sum(float(t.get('net_pnl_usd', 0)) for t in trades if float(t.get('net_pnl_usd', 0)) > 0)
            c_cap = tot_p * 0.40 if tot_p > 0 else 999999.0
            for t in trades:
                raw_p = float(t.get('net_pnl_usd', 0))
                if raw_p > c_cap:
                    t['clamped'] = True
                    t['original_pnl_usd'] = raw_p
                    t['net_pnl_usd'] = round(c_cap, 2)
                    t['profit_loss'] = round(c_cap, 2)
                else:
                    t['clamped'] = False

        enriched = enrich_trades_data(trades)"""

if clamp_trades_target in backend_code and "lens.upper() == 'EVALUATION'" not in backend_code[backend_code.find("def get_trade_history"):backend_code.find("def get_trade_history")+3000]:
    backend_code = backend_code.replace(clamp_trades_target, clamp_trades_replacement, 1)
    print("[OK] Injected dynamic lens clamp into get_trade_history in backend.py")

with open(BACKEND_PATH, "w", encoding="utf-8") as f:
    f.write(backend_code)

print("[SUCCESS] backend.py updated!")

# 2. Update index.html
with open(INDEX_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# Update fetchAnalyticsData to pass lens
html = re.sub(
    r'/api/analytics\?filter=\$\{encodeURIComponent\(filter\)\}',
    r'/api/analytics?filter=${encodeURIComponent(filter)}&lens=${encodeURIComponent(currentBifocalLens)}',
    html
)

# Update fetchTradeHistory to pass lens
html = re.sub(
    r'/api/trade_history\?filter=\$\{encodeURIComponent\(filter\)\}',
    r'/api/trade_history?filter=${encodeURIComponent(filter)}&lens=${encodeURIComponent(currentBifocalLens)}',
    html
)

# Update switchBifocalLens in index.html
new_switch_fn = """let currentBifocalLens = 'EVALUATION';

    function switchBifocalLens(lens) {
      currentBifocalLens = lens;
      const bEval = document.getElementById('btn-lens-eval');
      const bFunded = document.getElementById('btn-lens-funded');

      if (bEval && bFunded) {
        if (lens === 'EVALUATION') {
          bEval.className = 'segmented-pill active flex-1 sm:flex-initial';
          bFunded.className = 'segmented-pill flex-1 sm:flex-initial';
        } else {
          bEval.className = 'segmented-pill flex-1 sm:flex-initial';
          bFunded.className = 'segmented-pill active flex-1 sm:flex-initial';
        }
      }

      // Re-consultar analíticas e historial completos con la lente seleccionada
      if (typeof fetchAnalyticsData === 'function') {
        fetchAnalyticsData(currentAccountFilter);
      }
      if (typeof fetchTradeHistory === 'function') {
        fetchTradeHistory(currentAccountFilter);
      }
    }"""

old_switch_pattern = re.compile(r'let currentBifocalLens = [\'"]EVALUATION[\'"];\s*function switchBifocalLens\(lens\) \{.*?renderBifocalUI\(\);\s*\}', re.DOTALL)
if old_switch_pattern.search(html):
    html = old_switch_pattern.sub(new_switch_fn, html, count=1)
    print("[OK] Updated switchBifocalLens in index.html to reload analytics & trade history")

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("[SUCCESS] index.html updated!")
