import pandas as pd

for p in ['BTC_USDT_1h_2021_2026.parquet', 'NDX_1h_2016_2026.parquet', 'SPX_2h_2016_2026.parquet']:
    df = pd.read_parquet(f'/root/AlgrokQuant/data/parquet_cache/{p}')
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, utc=True)
    ts = [int(t.timestamp()) for t in df.index[:3]]
    dates = [pd.to_datetime(t, unit='s', utc=True).strftime('%Y-%m-%d %H:%M') for t in ts]
    print(p, "->", ts, "->", dates)
