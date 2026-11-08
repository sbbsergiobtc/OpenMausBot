import re
import os

BACKEND_PATH = r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py"
INDEX_PATH = r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html"
RISK_RULES_PATH = r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\config\risk_rules.yaml"

# 1. Update config/risk_rules.yaml with the 5 min news policy
if not os.path.exists("config"):
    os.makedirs("config")

with open(RISK_RULES_PATH, "r", encoding="utf-8") if os.path.exists(RISK_RULES_PATH) else open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\scripts\check_diffs_vps.py") as f:
    # We will read or create config/risk_rules.yaml
    pass

risk_policy_yaml = """# =====================================================================
# REGLA SUPREMA DE NOTICIAS DE ALTO IMPACTO (DIRECTIVA MANDATORIA SERGIO)
# =====================================================================
news_trading_policy:
  allow_news_trading: false
  blackout_window_minutes_before: 5
  blackout_window_minutes_after: 5
  high_impact_events:
    - "FOMC / Fed Rate Decision"
    - "CPI (Consumer Price Index)"
    - "NFP (Non-Farm Payrolls)"
    - "PPI / PCE Core Inflation"
    - "Interest Rate Decisions"
"""

if os.path.exists(RISK_RULES_PATH):
    with open(RISK_RULES_PATH, "r", encoding="utf-8") as f:
        rc = f.read()
    if "news_trading_policy:" not in rc:
        with open(RISK_RULES_PATH, "a", encoding="utf-8") as f:
            f.write("\n" + risk_policy_yaml)
        print("[OK] risk_rules.yaml updated with 5 min news policy")
    else:
        print("[INFO] news_trading_policy already in risk_rules.yaml")
else:
    with open(RISK_RULES_PATH, "w", encoding="utf-8") as f:
        f.write(risk_policy_yaml)
    print("[OK] Created config/risk_rules.yaml with news policy")

# 2. Patch backend.py to add bifocal analytics calculation
with open(BACKEND_PATH, "r", encoding="utf-8") as f:
    backend_code = f.read()

bifocal_calc_code = """
def compute_bifocal_metrics(df_subset, initial_balance=100000.0):
    if df_subset.empty:
        return {}

    raw_pnls = [float(p) for p in df_subset['net_pnl_usd'].values]
    total_raw_profit = sum(p for p in raw_pnls if p > 0)
    consistency_cap_per_trade = total_raw_profit * 0.40 if total_raw_profit > 0 else 999999.0

    clamped_pnls = []
    clamped_count = 0
    consistency_penalty_usd = 0.0

    for p in raw_pnls:
        if p > consistency_cap_per_trade:
            clamped_pnls.append(consistency_cap_per_trade)
            consistency_penalty_usd += (p - consistency_cap_per_trade)
            clamped_count += 1
        else:
            clamped_pnls.append(p)

    eval_net_profit = sum(clamped_pnls)
    eval_final_balance = initial_balance + eval_net_profit

    # Curva evaluacion con clamp
    eval_curve = []
    bal = initial_balance
    peak = initial_balance
    eval_max_dd = 0.0
    for i, p in enumerate(clamped_pnls):
        bal += p
        if bal > peak:
            peak = bal
        dd = ((peak - bal) / peak) * 100.0 if peak > 0 else 0.0
        if dd > eval_max_dd:
            eval_max_dd = dd
        eval_curve.append({
            'timestamp': str(df_subset.iloc[i].get('exit_time', ''))[:19],
            'balance': round(bal, 2),
            'dd': round(dd, 2),
            'pnl': round(p, 2)
        })

    # Monte Carlo Pass Rate
    np.random.seed(42)
    mc_iterations = 500
    target_profit = initial_balance * 0.08
    max_allowed_dd_usd = initial_balance * 0.04
    pass_count = 0

    if len(clamped_pnls) > 0:
        for _ in range(mc_iterations):
            shuffled = np.random.choice(clamped_pnls, size=len(clamped_pnls), replace=True)
            mc_bal = initial_balance
            mc_peak = initial_balance
            failed = False
            passed = False
            for mp in shuffled:
                mc_bal += mp
                if mc_bal > mc_peak:
                    mc_peak = mc_bal
                if (mc_peak - mc_bal) >= max_allowed_dd_usd:
                    failed = True
                    break
                if (mc_bal - initial_balance) >= target_profit:
                    passed = True
                    break
            if passed and not failed:
                pass_count += 1

    pass_rate_pct = round((pass_count / mc_iterations) * 100.0, 1)

    # Lente Fondeada
    funded_net_profit = sum(raw_pnls)
    funded_final_balance = initial_balance + funded_net_profit
    months = max(1.0, len(df_subset) / 5.0)
    monthly_payout = (funded_net_profit / months) * 0.80

    funded_curve = []
    bal_f = initial_balance
    peak_f = initial_balance
    funded_max_dd = 0.0
    for i, p in enumerate(raw_pnls):
        bal_f += p
        if bal_f > peak_f:
            peak_f = bal_f
        dd = ((peak_f - bal_f) / peak_f) * 100.0 if peak_f > 0 else 0.0
        if dd > funded_max_dd:
            funded_max_dd = dd
        funded_curve.append({
            'timestamp': str(df_subset.iloc[i].get('exit_time', ''))[:19],
            'balance': round(bal_f, 2),
            'dd': round(dd, 2),
            'pnl': round(p, 2)
        })

    return {
        'evaluation_view': {
            'target_profit_target_usd': target_profit,
            'pass_rate_monte_carlo': pass_rate_pct,
            'clamped_trades_count': clamped_count,
            'consistency_penalty_usd': round(consistency_penalty_usd, 2),
            'max_drawdown_pct': round(eval_max_dd, 2),
            'net_profit_usd': round(eval_net_profit, 2),
            'final_balance': round(eval_final_balance, 2),
            'status': 'PASS CERTIFIED' if pass_rate_pct >= 70.0 and eval_max_dd <= 4.0 else 'IN PROGRESS',
            'curve': eval_curve
        },
        'funded_view': {
            'total_uncapped_alpha_usd': round(funded_net_profit, 2),
            'final_balance': round(funded_final_balance, 2),
            'max_drawdown_pct': round(funded_max_dd, 2),
            'estimated_months': round(months, 1),
            'monthly_payout_projection_usd': round(monthly_payout, 2),
            'profit_split_pct': 80.0,
            'curve': funded_curve
        }
    }
"""

if "def compute_bifocal_metrics(" not in backend_code:
    # Insert compute_bifocal_metrics right before get_analytics
    backend_code = backend_code.replace("def get_analytics(", bifocal_calc_code + "\n\ndef get_analytics(", 1)
    print("[OK] Inserted compute_bifocal_metrics in backend.py")

# Ensure get_analytics returns 'bifocal_report'
if "'bifocal_report':" not in backend_code:
    backend_code = backend_code.replace(
        "return {\n        'account_name': account_name,",
        "bifocal_data = compute_bifocal_metrics(df, initial_balance)\n    return {\n        'account_name': account_name,\n        'bifocal_report': bifocal_data,",
        1
    )
    print("[OK] Hooked bifocal_report into get_analytics response in backend.py")

with open(BACKEND_PATH, "w", encoding="utf-8") as f:
    f.write(backend_code)

print("[SUCCESS] backend.py updated with Bifocal Analytics API!")
