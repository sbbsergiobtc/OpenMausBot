import pandas as pd
import numpy as np

df = pd.read_parquet('/root/AlgrokQuant/data/parquet_cache/BTC_USDT_1h_2021_2026.parquet')
if not isinstance(df.index, pd.DatetimeIndex):
    df.index = pd.to_datetime(df.index, utc=True)
df.sort_index(inplace=True)

close = df['close']

def get_stats(s, name):
    ret = (s.iloc[-1] / s.iloc[0] - 1.0) * 100.0
    cummax = s.cummax()
    dd = ((s - cummax) / cummax).min() * 100.0
    calmar = abs(ret / dd) if dd != 0 else np.nan
    print(f"{name}:")
    print(f"  Rango:       {s.index[0].strftime('%Y-%m-%d')} (${s.iloc[0]:.2f}) -> {s.index[-1].strftime('%Y-%m-%d')} (${s.iloc[-1]:.2f})")
    print(f"  Retorno B&H: {ret:+.2f}%")
    print(f"  Max DD B&H:  {dd:.2f}%")
    print(f"  Calmar B&H:  {calmar:.2f}")

print("=" * 60)
print("BENCHMARK BUY & HOLD DE BITCOIN (PARQUET 2021-2026):")
print("=" * 60)
get_stats(close, "TOTAL 5 AÑOS (2021-2026)")
is_close = close[close.index < pd.Timestamp('2024-10-01', tz='UTC')]
get_stats(is_close, "IN-SAMPLE (3 AÑOS: 2021-2024)")
oos_close = close[close.index >= pd.Timestamp('2024-10-01', tz='UTC')]
get_stats(oos_close, "OUT-OF-SAMPLE (2 AÑOS: 2024-2026)")
print("=" * 60)
