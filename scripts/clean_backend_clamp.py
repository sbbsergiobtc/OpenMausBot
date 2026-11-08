with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Remove misplaced block before return
bad_block = """        bifocal_data = compute_bifocal_metrics(df, initial_balance)

    # Si la lente activa es EVALUACIÓN: aplicar clamp de consistencia del 40% a todas las métricas
    if lens.upper() == 'EVALUATION' and not df.empty:
        raw_pnls = [float(p) for p in df['net_pnl_usd'].values]
        total_raw_profit = sum(p for p in raw_pnls if p > 0)
        consistency_cap = total_raw_profit * 0.40 if total_raw_profit > 0 else 999999.0
        clamped_pnls = [round(min(p, consistency_cap), 2) if p > 0 else p for p in raw_pnls]
        df['net_pnl_usd'] = clamped_pnls"""

text = text.replace(bad_block, "")

# 2. Insert correct block right after df = pd.DataFrame(subset)
good_block = """    df = pd.DataFrame(subset)
    bifocal_data = compute_bifocal_metrics(df, initial_balance)

    # Si la lente activa es EVALUACIÓN: aplicar clamp de consistencia del 40% a todas las métricas
    if lens.upper() == 'EVALUATION' and not df.empty:
        raw_pnls = [float(p) for p in df['net_pnl_usd'].values]
        total_raw_profit = sum(p for p in raw_pnls if p > 0)
        consistency_cap = total_raw_profit * 0.40 if total_raw_profit > 0 else 999999.0
        clamped_pnls = [round(min(p, consistency_cap), 2) if p > 0 else p for p in raw_pnls]
        df['net_pnl_usd'] = clamped_pnls"""

text = text.replace("    df = pd.DataFrame(subset)", good_block, 1)

with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py", "w", encoding="utf-8") as f:
    f.write(text)

print("[OK] Cleaned and placed clamp correctly in backend.py!")
