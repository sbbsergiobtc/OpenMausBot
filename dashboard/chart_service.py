import os
import json
import glob
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

BASE_DIR = Path('/root/AlgrokQuant') if Path('/root/AlgrokQuant').exists() else Path(__file__).resolve().parent.parent
TRAIDING_HUB_PARQUET = Path('/root/traiding-hub/data/parquet')
LOCAL_PARQUET_CACHE = BASE_DIR / 'data/parquet_cache'


def get_available_chart_strategies() -> List[Dict[str, str]]:
    """
    Construye dinámicamente el catálogo de estrategias disponibles para TradingView
    combinando historial de backtests, Strategy Vault SQLite y fichas de librería.
    """
    catalog: List[Dict[str, str]] = []
    seen = set()

    def _add(sid: str, name: str, asset: str, tf: str, stype: str):
        if not sid or sid in seen:
            return
        seen.add(sid)
        catalog.append({
            "id": sid,
            "name": name,
            "asset": asset,
            "timeframe": tf,
            "type": stype,
        })

    # 1. Leer estrategias con histórico en full_trade_history.json
    hist_file = BASE_DIR / 'data/paper_trades/full_trade_history.json'
    if hist_file.exists():
        try:
            with open(hist_file, 'r', encoding='utf-8') as f:
                trades = json.load(f).get('trades', [])
            for t in trades:
                sid = str(t.get('strategy_id', '')).strip()
                if not sid or sid in seen:
                    continue
                is_prop = sid.startswith(('PROP', 'HYB'))
                asset = t.get('asset') or ('EUR/USD' if 'EUR' in sid else ('US500' if 'SPX' in sid else ('US100' if 'NDX' in sid else 'BTC/USDT')))
                tf = '1D' if 'SPX-005' in sid else ('4h' if 'SPX-006' in sid else ('2h' if 'NDX-005' in sid else '1h'))
                sname = t.get('strategy_name') or sid
                _add(sid, sname, asset, tf, 'Prop Firm' if is_prop else 'Capital Propio')
        except Exception:
            pass

    # 2. Leer titulares y reservas del Strategy Vault SQLite
    vault_db = BASE_DIR / 'data/strategy_vault.db'
    if vault_db.exists():
        try:
            conn = sqlite3.connect(vault_db)
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT strategy_id, asset, timeframe, desk_mode, macro_anchor, status FROM strategies ORDER BY status, strategy_id").fetchall()
            conn.close()
            for r in rows:
                sid = r['strategy_id']
                dm = str(r['desk_mode'] or 'CAPITAL_PROPIO').upper()
                sid_u = str(sid or '').upper()
                is_prop_v = False if sid_u.startswith(('CAP-', 'CRYPTO-', 'STRAT-')) else (('PROP_FIRM' in dm) or dm.startswith('PROP') or sid_u.startswith(('PROP', 'HYB')))
                stype = 'Prop Firm' if is_prop_v else 'Capital Propio'
                anchor = r['macro_anchor'] or sid
                _add(sid, f"{anchor} [{r['status']}]", r['asset'] or 'NDX', r['timeframe'] or '1h', stype)
        except Exception:
            pass

    # 2b. Leer todas las estrategias activas/shadow desde Orchestrator y Forward Test State
    for json_path in (BASE_DIR / 'data/paper_trades/regime_orchestrator_state.json', BASE_DIR / 'data/paper_trades/prop_firm_forward_test_state.json'):
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    jdata = json.load(f)
                cand_lists = []
                if 'strategies_ab_comparison' in jdata or 'strategies_ab' in jdata:
                    cand_lists.append(jdata.get('strategies_ab_comparison') or jdata.get('strategies_ab') or [])
                for b_key in ('capital_propio', 'prop_firm'):
                    if isinstance(jdata.get(b_key), dict):
                        cand_lists.append(jdata[b_key].get('active_strategies', []))
                for clist in cand_lists:
                    for s in clist:
                        if not isinstance(s, dict):
                            continue
                        sid = str(s.get('strategy_id') or s.get('id') or '').strip()
                        if not sid:
                            continue
                        dm = str(s.get('desk_mode') or s.get('branch') or 'CAPITAL_PROPIO').upper()
                        sid_u = sid.upper()
                        is_prop = False if sid_u.startswith(('CAP-', 'CRYPTO-', 'STRAT-')) else (('PROP_FIRM' in dm) or dm.startswith('PROP') or sid_u.startswith(('PROP', 'HYB')))
                        asset = str(s.get('asset') or s.get('symbol') or ('SPX' if 'SPX' in sid else ('NDX' if 'NDX' in sid else 'BTC')))
                        tf_s = str(s.get('timeframe') or s.get('tf') or ('5m RTH' if is_prop else '1h'))
                        role_lbl = s.get('role') or ('TITULAR' if sid in ('CAP-SPX-006', 'CAP-NDX-005', 'CRYPTO-BTC-001', 'PROP-FX-EUR-001') else 'SUPLENTE')
                        arch = s.get('family') or s.get('archetype') or s.get('macro_anchor') or sid
                        _add(sid, f"{arch} [{role_lbl}]", asset, tf_s, 'Prop Firm' if is_prop else 'Capital Propio')
            except Exception:
                pass

    # 3. Asegurar presencia de modelos de referencia recientes
    _add("STRAT-20261028-035", "BTC 1h Donchian + Entropía Shannon", "BTC/USDT", "1h", "Capital Propio")
    _add("STRAT-20261024-028", "SOL/USDC 5m VWAP Breakout (Hyperliquid)", "SOL/USDT", "15m", "Capital Propio")
    _add("PROP-FX-EUR-001", "EUR/USD 1h London-NY Session", "EUR/USD", "1h", "Prop Firm")
    _add("PROP-NDX-005", "NDX 2h Bollinger Mean-Reversion EOD", "NDX", "1h", "Prop Firm")
    _add("PROP-SPX-005", "SPX 1D Connors RSI2 EOD", "SPX", "1D", "Prop Firm")

    return catalog


def _load_asset_dataframe(asset_folder: str, preferred_tf: str = '1h', window_bars: int = 1500) -> pd.DataFrame:
    """
    Carga velas reales desde /root/traiding-hub/data/parquet/<ASSET>/<TF>/year=*/...
    y remuestrea dinámicamente al timeframe solicitado si no existe pre-agregado.
    """
    tf_norm = (preferred_tf or '1h').strip()
    tf_lower = tf_norm.lower()

    # Mapeo a regla de pandas resample
    resample_map = {
        '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min',
        '1h': '1h', '2h': '2h', '4h': '4h', '1d': '1D', 'd': '1D'
    }
    pandas_rule = resample_map.get(tf_lower, '1h')

    asset_root = TRAIDING_HUB_PARQUET / asset_folder
    if not asset_root.exists():
        # Fallback cache local si existiera
        if LOCAL_PARQUET_CACHE.exists():
            matches = sorted(LOCAL_PARQUET_CACHE.glob(f"{asset_folder}*.parquet"))
            if matches:
                df = pd.read_parquet(matches[0])
                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index, utc=True)
                return df.sort_index().iloc[-window_bars:].copy()
        raise FileNotFoundError(f"Directorio Parquet {asset_root} no encontrado")

    # Usar 1h únicamente si está actualizado hasta 2026; de lo contrario usar 5m (siempre actualizado hasta 2026)
    has_recent_1h = (asset_root / '1h' / 'year=2026').exists()
    use_1h = tf_lower in ('1h', '2h', '4h', '1d', 'd') and has_recent_1h
    source_tf_dir = asset_root / ('1h' if use_1h else ('5m' if (asset_root / '5m').exists() else '1h'))
    if not source_tf_dir.exists():
        subdirs = [d for d in asset_root.iterdir() if d.is_dir()]
        if not subdirs:
            raise FileNotFoundError(f"Sin particiones de timeframe en {asset_root}")
        source_tf_dir = subdirs[0]

    # Leer los años más recientes (máx 2 años en 5m ~ 150k velas; suficiente para 1500+ velas de 4h/1h/15m)
    year_dirs = sorted(source_tf_dir.glob("year=*"), reverse=True)
    parquet_files: List[str] = []
    max_years = 4 if use_1h else (3 if tf_lower in ('1d', 'd') else 2)
    for yd in year_dirs[:max_years]:
        direct = yd / 'data.parquet'
        if direct.exists():
            parquet_files.append(str(direct))
        else:
            parquet_files.extend(sorted(glob.glob(str(yd / '**/*.parquet'), recursive=True)))

    if not parquet_files:
        parquet_files = sorted(glob.glob(str(source_tf_dir / '**/*.parquet'), recursive=True))[-12:]

    if not parquet_files:
        raise FileNotFoundError(f"Sin ficheros parquet en {source_tf_dir}")

    dfs = [pd.read_parquet(fp) for fp in parquet_files]
    has_ts_col = any(c in dfs[0].columns for c in ('timestamp', 'datetime', 'date', 'time', 'ts'))
    raw_df = pd.concat(dfs, ignore_index=has_ts_col)

    # Normalizar columna de tiempo sin caer en RangeIndex ns epoch 1970
    ts_col_name = next((c for c in ('timestamp', 'datetime', 'date', 'time', 'ts') if c in raw_df.columns), None)
    if ts_col_name:
        ts_col = raw_df[ts_col_name]
        if pd.api.types.is_numeric_dtype(ts_col):
            med = float(ts_col.dropna().iloc[0]) if len(ts_col.dropna()) > 0 else 0.0
            unit = 'ms' if med > 1e11 else ('s' if med > 1e8 else None)
            raw_df['datetime'] = pd.to_datetime(ts_col, unit=unit, utc=True)
        else:
            raw_df['datetime'] = pd.to_datetime(ts_col, utc=True)
        raw_df = raw_df.drop_duplicates(subset=['datetime']).sort_values('datetime').set_index('datetime')
    elif isinstance(raw_df.index, pd.DatetimeIndex):
        if raw_df.index.tz is None:
            raw_df.index = raw_df.index.tz_localize('UTC')
        raw_df = raw_df[~raw_df.index.duplicated(keep='last')].sort_index()
    else:
        raise ValueError(f"El parquet en {source_tf_dir} no tiene columna temporal válida: {list(raw_df.columns)}")

    # Resample al timeframe solicitado
    if not (use_1h and tf_lower == '1h'):
        agg_dict = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}
        if 'volume' in raw_df.columns:
            agg_dict['volume'] = 'sum'
        raw_df = raw_df.resample(pandas_rule).agg(agg_dict).dropna(subset=['open', 'high', 'low', 'close'])

    if 'volume' not in raw_df.columns:
        raw_df['volume'] = 0.0

    if len(raw_df) > window_bars:
        raw_df = raw_df.iloc[-window_bars:].copy()

    return raw_df


def build_chart_payload(strat_id: str, window_bars: int = 1500, timeframe: Optional[str] = None) -> Dict[str, Any]:
    strat_upper = strat_id.upper()

    # 1. Determinar activo, carpeta parquet y timeframe por defecto
    if 'EUR' in strat_upper or 'FX-EUR' in strat_upper:
        asset_folder = 'EUR_USD'
        asset = 'EUR/USD'
        default_tf = '1h'
        strat_type = 'prop_firm'
        price_decimals = 5
    elif 'NDX' in strat_upper or 'NQ' in strat_upper or '038' in strat_upper or '039' in strat_upper:
        asset_folder = 'NDX'
        asset = 'NDX (Nasdaq 100)'
        default_tf = '2h' if '005' in strat_upper else '1h'
        strat_type = 'prop_firm' if ('PROP' in strat_upper or 'HYB' in strat_upper or 'FUT' in strat_upper) else 'capital_propio'
        price_decimals = 2
    elif 'SPX' in strat_upper or 'ES' in strat_upper or '040' in strat_upper or '041' in strat_upper:
        asset_folder = 'SPX'
        asset = 'SPX (S&P 500)'
        default_tf = '4h' if 'CAP-SPX-006' in strat_upper else ('1D' if 'PROP-SPX-005' in strat_upper else '1h')
        strat_type = 'prop_firm' if ('PROP' in strat_upper or 'FUT' in strat_upper) else 'capital_propio'
        price_decimals = 2
    elif 'ETH' in strat_upper:
        asset_folder = 'ETH_USDT'
        asset = 'ETH/USDT'
        default_tf = '1h'
        strat_type = 'capital_propio'
        price_decimals = 2
    elif 'SOL' in strat_upper or '028' in strat_upper:
        asset_folder = 'SOL_USDT'
        asset = 'SOL/USDT'
        default_tf = '15m'
        strat_type = 'capital_propio'
        price_decimals = 3
    else:
        asset_folder = 'BTC_USDT'
        asset = 'BTC/USDT'
        default_tf = '1h'
        strat_type = 'capital_propio'
        price_decimals = 2

    effective_tf = timeframe.strip() if timeframe else default_tf
    df_window = _load_asset_dataframe(asset_folder, preferred_tf=effective_tf, window_bars=window_bars)

    close = df_window['close'].values.astype(float)
    high = df_window['high'].values.astype(float)
    low = df_window['low'].values.astype(float)
    open_ = df_window['open'].values.astype(float)
    volume = df_window['volume'].values.astype(float)

    timestamps = [int(ts.timestamp()) for ts in df_window.index]
    n = len(close)

    # 2. Generar Velas OHLCV
    candles = []
    volume_series = []
    for i in range(n):
        t = timestamps[i]
        candles.append({
            "time": t,
            "open": round(float(open_[i]), price_decimals),
            "high": round(float(high[i]), price_decimals),
            "low": round(float(low[i]), price_decimals),
            "close": round(float(close[i]), price_decimals),
        })
        volume_series.append({
            "time": t,
            "value": round(float(volume[i]), 2),
            "color": "#22c55e" if close[i] >= open_[i] else "#ef4444",
        })

    # 3. Indicadores Superpuestos
    s_close = pd.Series(close)
    ema50 = s_close.ewm(span=50, adjust=False).mean().values
    ema200 = s_close.ewm(span=200, adjust=False).mean().values

    overlays = [
        {
            "id": "ema50",
            "name": "EMA 50",
            "color": "#38bdf8",
            "lineWidth": 1,
            "data": [{"time": timestamps[i], "value": round(float(ema50[i]), price_decimals)} for i in range(n)],
        },
        {
            "id": "ema200",
            "name": "EMA 200",
            "color": "#f59e0b",
            "lineWidth": 1,
            "data": [{"time": timestamps[i], "value": round(float(ema200[i]), price_decimals)} for i in range(n)],
        },
    ]

    oscillators = []

    if '035' in strat_upper or '018' in strat_upper or 'ENTROPY' in strat_upper or 'DONCHIAN' in strat_upper:
        hh30 = pd.Series(high).rolling(30).max().shift(1).values
        overlays.append({
            "id": "donchian30",
            "name": "Donchian High (30)",
            "color": "#10b981",
            "lineWidth": 1,
            "lineStyle": 2,
            "data": [{"time": timestamps[i], "value": round(float(hh30[i]), price_decimals)} for i in range(30, n) if not np.isnan(hh30[i])],
        })

        log_ret = np.zeros(n)
        safe_ratio = np.where(close[:-1] > 0, close[1:] / close[:-1], 1.0)
        log_ret[1:] = np.log(np.clip(safe_ratio, 1e-6, 1e6))
        window_ent = 48
        bins = 10
        max_ent = np.log2(bins)
        h_norm = np.zeros(n)
        for i in range(window_ent, n):
            w = log_ret[i - window_ent + 1 : i + 1]
            counts, _ = np.histogram(w, bins=bins)
            probs = counts / float(window_ent)
            probs = probs[probs > 0]
            h_norm[i] = -np.sum(probs * np.log2(probs)) / max_ent

        oscillators.append({
            "id": "shannon_entropy",
            "name": "Entropía de Shannon (48)",
            "color": "#f43f5e",
            "lineWidth": 1,
            "thresholds": [{"value": 0.72, "color": "#ef4444", "title": "Máx 0.72"}],
            "data": [{"time": timestamps[i], "value": round(float(h_norm[i]), 3)} for i in range(window_ent, n) if not np.isnan(h_norm[i])],
        })

        mfm = ((close - low) - (high - close)) / (high - low + 1e-9)
        mfv = mfm * volume
        cmf20 = pd.Series(mfv).rolling(20).sum().values / (pd.Series(volume).rolling(20).sum().values + 1e-9)
        oscillators.append({
            "id": "cmf20",
            "name": "Chaikin Money Flow (20)",
            "color": "#06b6d4",
            "lineWidth": 1,
            "thresholds": [{"value": 0.05, "color": "#22c55e", "title": "Flow +0.05"}, {"value": 0.0, "color": "#64748b", "title": "0"}],
            "data": [{"time": timestamps[i], "value": round(float(cmf20[i]), 3)} for i in range(20, n) if not np.isnan(cmf20[i])],
        })
    else:
        sma20 = s_close.rolling(20).mean().values
        std20 = s_close.rolling(20).std().values
        bb_upper = sma20 + 2.0 * std20
        bb_lower = sma20 - 2.0 * std20

        overlays.append({
            "id": "bb_upper",
            "name": "Bollinger Upper (20, 2)",
            "color": "#a855f7",
            "lineWidth": 1,
            "data": [{"time": timestamps[i], "value": round(float(bb_upper[i]), price_decimals)} for i in range(20, n) if not np.isnan(bb_upper[i])],
        })
        overlays.append({
            "id": "bb_lower",
            "name": "Bollinger Lower (20, 2)",
            "color": "#a855f7",
            "lineWidth": 1,
            "data": [{"time": timestamps[i], "value": round(float(bb_lower[i]), price_decimals)} for i in range(20, n) if not np.isnan(bb_lower[i])],
        })

        delta = s_close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1.0 / 14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / 14, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-9)
        rsi14 = (100 - (100 / (1 + rs))).values

        oscillators.append({
            "id": "rsi14",
            "name": "RSI (14)",
            "color": "#818cf8",
            "lineWidth": 1,
            "thresholds": [{"value": 70.0, "color": "#ef4444", "title": "70"}, {"value": 30.0, "color": "#22c55e", "title": "30"}],
            "data": [{"time": timestamps[i], "value": round(float(rsi14[i]), 2)} for i in range(14, n) if not np.isnan(rsi14[i])],
        })

    # 4. Obtener Operaciones reales desde full_trade_history.json y forward closed_trades
    trades = []
    markers = []
    min_ts = timestamps[0] if timestamps else 0
    max_ts = timestamps[-1] if timestamps else 0

    trade_list = []
    hist_file = BASE_DIR / 'data/paper_trades/full_trade_history.json'
    if hist_file.exists():
        try:
            with open(hist_file, 'r', encoding='utf-8') as f:
                raw_trades = json.load(f).get('trades', [])
            trade_list.extend([t for t in raw_trades if str(t.get('strategy_id', '')).upper() == strat_upper])
        except Exception:
            pass

    pf_file = BASE_DIR / 'data/paper_trades/prop_firm_forward_test_state.json'
    if pf_file.exists():
        try:
            with open(pf_file, 'r', encoding='utf-8') as f:
                pf_st = json.load(f)
            for branch in ('prop_firm', 'capital_propio'):
                for ct in pf_st.get(branch, {}).get('closed_trades', []):
                    if str(ct.get('strategy_id', ct.get('strategy', ''))).upper() == strat_upper:
                        trade_list.append(ct)
        except Exception:
            pass

    for idx, t in enumerate(trade_list):
        try:
            e_time = int(pd.to_datetime(t.get('entry_time'), utc=True).timestamp())
            x_time = int(pd.to_datetime(t.get('exit_time'), utc=True).timestamp())
            e_price = float(t.get('entry_price', 0))
            x_price = float(t.get('exit_price', 0))
            # Soportar return_pct, pnl_pct o calcular desde net_pnl_usd
            pnl_pct = t.get('return_pct') if t.get('return_pct') is not None else t.get('pnl_pct')
            if pnl_pct is None:
                net_usd = float(t.get('net_pnl_usd') or t.get('net_pnl') or t.get('pnl_usd') or 0.0)
                pnl_pct = ((x_price - e_price) / e_price * 100.0) if e_price > 0 else net_usd
            pnl = float(pnl_pct)
            sl_val = t.get('sl_price') if t.get('sl_price') is not None else t.get('stop_loss')
            tp_val = t.get('tp_price') if t.get('tp_price') is not None else t.get('take_profit')
            is_long = str(t.get('direction') or t.get('side') or 'BUY').upper() in ['BUY', 'LONG']

            # Añadir marcadores si caen en la ventana de velas cargada
            if min_ts <= e_time <= max_ts or min_ts <= x_time <= max_ts or not candles:
                markers.append({
                    "time": e_time,
                    "position": "belowBar" if is_long else "aboveBar",
                    "color": "#ffffff",
                    "shape": "arrowUp" if is_long else "arrowDown",
                    "text": f"{'BUY' if is_long else 'SELL'} #{idx+1} @ {e_price:.{price_decimals}f}",
                    "size": 1.5,
                })
                markers.append({
                    "time": x_time,
                    "position": "aboveBar" if is_long else "belowBar",
                    "color": "#10b981" if pnl > 0 else "#ef4444",
                    "shape": "arrowDown" if is_long else "arrowUp",
                    "text": f"EXIT #{idx+1}: {pnl:+.2f}%",
                    "size": 1.2,
                })

            trades.append({
                "id": t.get('trade_id') or t.get('id') or f"TR-{idx+1:03d}",
                "type": "LONG" if is_long else "SHORT",
                "entry_time": e_time,
                "entry_price": round(e_price, price_decimals),
                "exit_time": x_time,
                "exit_price": round(x_price, price_decimals),
                "sl_price": round(float(sl_val), price_decimals) if sl_val else None,
                "tp_price": round(float(tp_val), price_decimals) if tp_val else None,
                "pnl_pct": round(pnl, 2),
                "result": "WIN" if pnl > 0 else "LOSS",
                "duration_bars": int(t.get('duration_bars', max(1, (x_time - e_time) // 3600))),
            })
        except Exception:
            continue

    markers.sort(key=lambda x: x['time'])

    return {
        "strategy_id": strat_id,
        "asset": asset,
        "timeframe": effective_tf,
        "type": strat_type,
        "total_candles": len(candles),
        "candles": candles,
        "volume": volume_series,
        "overlays": overlays,
        "oscillators": oscillators,
        "trades": trades,
        "markers": markers,
    }
