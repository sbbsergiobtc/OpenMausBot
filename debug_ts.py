import pandas as pd

df = pd.read_parquet('/root/AlgrokQuant/data/parquet_cache/BTC_USDT_1h_2021_2026.parquet')
timestamps = [int(ts.timestamp()) for ts in df.index]
print("First 3 timestamp seconds:", timestamps[:3])
print("Converted back to UTC:", [pd.to_datetime(t, unit='s', utc=True).strftime('%Y-%m-%d %H:%M:%S') for t in timestamps[:3]])

last_ts = timestamps[-3:]
print("Last 3 timestamp seconds:", last_ts)
print("Converted back to UTC:", [pd.to_datetime(t, unit='s', utc=True).strftime('%Y-%m-%d %H:%M:%S') for t in last_ts])
