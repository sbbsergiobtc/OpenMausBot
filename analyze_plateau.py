import pandas as pd

df = pd.read_csv('strat_035_plateau_exploration.csv')
approved = df[df['passes_governance'] == True]

print('=== TOP 8 APROBADAS POR GOBERNANZA (MAX DD <= 20%, PF >= 1.30, TRADES >= 30) ===')
print(approved[['combo_id', 'mode', 'tot_return_pct', 'ann_cagr_pct', 'max_dd_pct', 'profit_factor', 'win_rate_pct', 'trades', 'stagnation_days']].head(8).to_string())

print('\n=== TOTAL APROBADAS ===')
print(f"{len(approved)} de {len(df)} combinaciones ({len(approved)/len(df)*100:.1f}%) cumplen estrictamente la gobernanza multianual.")

print('\n=== COMPARATIVA LONG ONLY VS LONG SHORT ===')
print(df.groupby('mode')[['tot_return_pct', 'max_dd_pct', 'profit_factor']].mean().round(2))

print('\n=== SENSIBILIDAD A VENTANA DONCHIAN ===')
print(df.groupby('dw')[['tot_return_pct', 'max_dd_pct', 'profit_factor']].mean().round(2))

print('\n=== SENSIBILIDAD A STOP LOSS MULTIPLIER ===')
print(df.groupby('sl_mult')[['tot_return_pct', 'max_dd_pct', 'profit_factor']].mean().round(2))

print('\n=== SENSIBILIDAD A TAKE PROFIT MULTIPLIER ===')
print(df.groupby('tp_mult')[['tot_return_pct', 'max_dd_pct', 'profit_factor']].mean().round(2))
