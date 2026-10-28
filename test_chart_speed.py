import time
import numpy as np
import pandas as pd

t0 = time.time()
df = pd.read_parquet('/root/AlgrokQuant/data/parquet_cache/BTC_USDT_1h_2021_2026.parquet')
if not isinstance(df.index, pd.DatetimeIndex):
    df.index = pd.to_datetime(df.index, utc=True)
df.sort_index(inplace=True)

# Tomamos las últimas 2000 barras para el visor interactivo (rápido y fluido)
sub_df = df.iloc[-2000:].copy()
close = sub_df['close'].values.astype(float)
high = sub_df['high'].values.astype(float)
low = sub_df['low'].values.astype(float)
open_ = sub_df['open'].values.astype(float)
volume = sub_df['volume'].values.astype(float)
timestamps = (sub_df.index.astype('int64') // 10**9).values

candles = [
    {"time": int(timestamps[i]), "open": float(open_[i]), "high": float(high[i]), "low": float(low[i]), "close": float(close[i]), "volume": float(volume[i])}
    for i in range(len(close))
]

ema50 = pd.Series(close).ewm(span=50, adjust=False).mean().values
ema200 = pd.Series(close).ewm(span=200, adjust=False).mean().values
hh30 = pd.Series(high).rolling(30).max().shift(1).values

print(f"Cargadas {len(candles)} velas en {time.time() - t0:.3f} segundos.")
print("Primera vela:", candles[0])
print("Última vela:", candles[-1])
