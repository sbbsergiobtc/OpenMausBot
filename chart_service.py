import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

BASE_DIR = Path('/root/AlgrokQuant')
PARQUET_DIR = BASE_DIR / 'data/parquet_cache'

def get_available_chart_strategies() -> List[Dict[str, str]]:
    return [
        {
            "id": "STRAT-20261028-035",
            "name": "BTC 1h Donchian + Entropía Shannon (Long Only) - Aprobada 5 Años",
            "asset": "BTC/USDT",
            "timeframe": "1h",
            "type": "Fast / Capital Propio"
        },
        {
            "id": "PROP-NDX-005",
            "name": "NDX 1h Bollinger Mean-Reversion EOD - Prop Firm",
            "asset": "NDX",
            "timeframe": "1h",
            "type": "Prop Firm"
        },
        {
            "id": "PROP-SPX-005",
            "name": "SPX 2h Bollinger Mean-Reversion EOD - Prop Firm",
            "asset": "SPX",
            "timeframe": "2h",
            "type": "Prop Firm"
        },
        {
            "id": "STRAT-20261021-018",
            "name": "BTC 1h Breakout Entropía de Shannon (Gen-2.5)",
            "asset": "BTC/USDT",
            "timeframe": "1h",
            "type": "Fast / Capital Propio"
        },
        {
            "id": "STRAT-20261024-022",
            "name": "BTC 1h Rolling VWAP Institutional - Aprobada",
            "asset": "BTC/USDT",
            "timeframe": "1h",
            "type": "Fast / Capital Propio"
        }
    ]

def build_chart_payload(strat_id: str, window_bars: int = 1500) -> Dict[str, Any]:
    strat_upper = strat_id.upper()
    
    # 1. Determinar activo y archivo parquet
    if 'NDX' in strat_upper or 'PROP-NDX' in strat_upper or '038' in strat_upper or '039' in strat_upper:
        parquet_path = PARQUET_DIR / 'NDX_1h_2016_2026.parquet'
        asset = 'NDX (Nasdaq 100)'
        tf = '1h'
        strat_type = 'prop_firm'
    elif 'SPX' in strat_upper or 'PROP-SPX' in strat_upper or '040' in strat_upper or '041' in strat_upper:
        parquet_path = PARQUET_DIR / 'SPX_2h_2016_2026.parquet'
        asset = 'SPX (S&P 500)'
        tf = '2h'
        strat_type = 'prop_firm'
    else:
        parquet_path = PARQUET_DIR / 'BTC_USDT_1h_2021_2026.parquet'
        asset = 'BTC/USDT'
        tf = '1h'
        strat_type = 'capital_propio'
        
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet {parquet_path} no encontrado")
        
    df = pd.read_parquet(parquet_path)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, utc=True)
    df.sort_index(inplace=True)
    
    # Filtrar últimas N barras para fluidez
    if len(df) > window_bars:
        df_window = df.iloc[-window_bars:].copy()
    else:
        df_window = df.copy()
        
    close = df_window['close'].values.astype(float)
    high = df_window['high'].values.astype(float)
    low = df_window['low'].values.astype(float)
    open_ = df_window['open'].values.astype(float)
    volume = df_window['volume'].values.astype(float)
    
    # CONVERSIÓN CORRECTA A SEGUNDOS UNIX EPOCH
    timestamps = [int(ts.timestamp()) for ts in df_window.index]
    n = len(close)
    
    # 2. Generar Velas OHLCV
    candles = []
    volume_series = []
    for i in range(n):
        t = timestamps[i]
        candles.append({
            "time": t,
            "open": round(float(open_[i]), 2),
            "high": round(float(high[i]), 2),
            "low": round(float(low[i]), 2),
            "close": round(float(close[i]), 2)
        })
        volume_series.append({
            "time": t,
            "value": round(float(volume[i]), 2),
            "color": "#22c55e" if close[i] >= open_[i] else "#ef4444"
        })
        
    # 3. Indicadores Superpuestos (Líneas finas de 1px con colores profesionales)
    s_close = pd.Series(close)
    ema50 = s_close.ewm(span=50, adjust=False).mean().values
    ema200 = s_close.ewm(span=200, adjust=False).mean().values
    
    overlays = [
        {
            "id": "ema50",
            "name": "EMA 50",
            "color": "#38bdf8", # Cyan
            "lineWidth": 1,     # Línea fina elegante 1px
            "data": [{"time": timestamps[i], "value": round(float(ema50[i]), 2)} for i in range(n)]
        },
        {
            "id": "ema200",
            "name": "EMA 200",
            "color": "#f59e0b", # Ámbar
            "lineWidth": 1,     # Línea fina elegante 1px
            "data": [{"time": timestamps[i], "value": round(float(ema200[i]), 2)} for i in range(n)]
        }
    ]
    
    # Indicadores específicos según la estrategia
    oscillators = []
    
    if '035' in strat_upper or '018' in strat_upper or 'ENTROPY' in strat_upper:
        # Donchian 30
        hh30 = pd.Series(high).rolling(30).max().shift(1).values
        overlays.append({
            "id": "donchian30",
            "name": "Donchian High (30h)",
            "color": "#10b981", # Verde esmeralda
            "lineWidth": 1,     # Línea fina 1px
            "lineStyle": 2,     # Discontinua sutil
            "data": [{"time": timestamps[i], "value": round(float(hh30[i]), 2)} for i in range(30, n) if not np.isnan(hh30[i])]
        })
        
        # Sub-panel 1: Entropía de Shannon
        log_ret = np.zeros(n)
        log_ret[1:] = np.log(close[1:] / close[:-1])
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
            "name": "Entropía de Shannon (48h)",
            "color": "#f43f5e", # Rose
            "lineWidth": 1,     # Fina 1px
            "thresholds": [
                {"value": 0.72, "color": "#ef4444", "title": "Máx 0.72"}
            ],
            "data": [{"time": timestamps[i], "value": round(float(h_norm[i]), 3)} for i in range(window_ent, n) if not np.isnan(h_norm[i])]
        })
        
        # Sub-panel 2: Chaikin Money Flow (CMF 20)
        mfm = ((close - low) - (high - close)) / (high - low + 1e-9)
        mfv = mfm * volume
        sum_mfv = pd.Series(mfv).rolling(20).sum().values
        sum_vol = pd.Series(volume).rolling(20).sum().values
        cmf20 = sum_mfv / (sum_vol + 1e-9)
        oscillators.append({
            "id": "cmf20",
            "name": "Chaikin Money Flow (20)",
            "color": "#06b6d4",
            "lineWidth": 1,     # Fina 1px
            "thresholds": [
                {"value": 0.05, "color": "#22c55e", "title": "Flow +0.05"},
                {"value": 0.0, "color": "#64748b", "title": "0"}
            ],
            "data": [{"time": timestamps[i], "value": round(float(cmf20[i]), 3)} for i in range(20, n) if not np.isnan(cmf20[i])]
        })
    else:
        # Bollinger Bands para Prop Firm Mean-Reversion
        sma20 = s_close.rolling(20).mean().values
        std20 = s_close.rolling(20).std().values
        bb_upper = sma20 + 2.0 * std20
        bb_lower = sma20 - 2.0 * std20
        
        overlays.append({
            "id": "bb_upper",
            "name": "Bollinger Upper (20, 2)",
            "color": "#a855f7",
            "lineWidth": 1,     # Fina 1px
            "data": [{"time": timestamps[i], "value": round(float(bb_upper[i]), 2)} for i in range(20, n) if not np.isnan(bb_upper[i])]
        })
        overlays.append({
            "id": "bb_lower",
            "name": "Bollinger Lower (20, 2)",
            "color": "#a855f7",
            "lineWidth": 1,     # Fina 1px
            "data": [{"time": timestamps[i], "value": round(float(bb_lower[i]), 2)} for i in range(20, n) if not np.isnan(bb_lower[i])]
        })
        
        # Sub-panel: RSI 14
        delta = s_close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1.0 / 14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / 14, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-9)
        rsi14 = 100 - (100 / (1 + rs)).values
        
        oscillators.append({
            "id": "rsi14",
            "name": "RSI (14)",
            "color": "#818cf8",
            "lineWidth": 1,     # Fina 1px
            "thresholds": [
                {"value": 70.0, "color": "#ef4444", "title": "70"},
                {"value": 30.0, "color": "#22c55e", "title": "30"}
            ],
            "data": [{"time": timestamps[i], "value": round(float(rsi14[i]), 2)} for i in range(14, n) if not np.isnan(rsi14[i])]
        })
        
    # 4. Obtener Operaciones (Trades) y Marcadores
    trades = []
    markers = []
    
    hist_file = BASE_DIR / 'data/paper_trades/full_trade_history.json'
    trade_list = []
    if hist_file.exists():
        try:
            with open(hist_file, 'r', encoding='utf-8') as f:
                hist_data = json.load(f)
            raw_trades = hist_data.get('trades', [])
            trade_list = [t for t in raw_trades if t.get('strategy_id', '').upper() == strat_upper]
        except Exception:
            trade_list = []
            
    if not trade_list and ('035' in strat_upper or 'BTC' in strat_upper):
        tr = np.maximum(high - low, np.maximum(np.abs(high - np.roll(close, 1)), np.abs(low - np.roll(close, 1))))
        tr[0] = high[0] - low[0]
        atr14 = pd.Series(tr).ewm(alpha=1.0 / 14, adjust=False).mean().values
        body_ratio = np.abs(close - open_) / (high - low + 1e-9)
        vol_ma24 = pd.Series(volume).rolling(24).mean().values
        rvol24 = volume / (vol_ma24 + 1e-9)
        ema200_slope = np.zeros(n)
        ema200_slope[5:] = (ema200[5:] - ema200[:-5]) / ema200[:-5]
        
        long_cond = (
            (h_norm < 0.72) &
            (ema50 > ema200) &
            (close > ema50) &
            (ema200_slope > 0) &
            (cmf20 > 0.05) &
            (rvol24 >= 1.20) &
            (close > open_) &
            (body_ratio >= 0.50) &
            (close > hh30)
        )
        
        in_pos = False
        trade_id = 1
        entry_p = 0.0
        sl_p = 0.0
        tp_p = 0.0
        entry_idx = 0
        
        for i in range(50, n):
            if not in_pos and long_cond[i - 1]:
                in_pos = True
                entry_idx = i
                entry_p = float(open_[i])
                cur_atr = float(atr14[i - 1])
                sl_p = round(entry_p - 2.0 * cur_atr, 2)
                tp_p = round(entry_p + 4.0 * cur_atr, 2)
                
                markers.append({
                    "time": timestamps[i],
                    "position": "belowBar",
                    "color": "#22c55e",
                    "shape": "arrowUp",
                    "text": f"BUY #{trade_id} @ ${entry_p:,.2f}",
                    "size": 1.5
                })
            elif in_pos:
                hit_tp = high[i] >= tp_p
                hit_sl = low[i] <= sl_p
                
                if hit_tp or hit_sl or (i - entry_idx >= 72):
                    exit_p = tp_p if hit_tp else (sl_p if hit_sl else float(close[i]))
                    pnl_pct = ((exit_p - entry_p) / entry_p) * 100.0
                    is_win = pnl_pct > 0
                    
                    markers.append({
                        "time": timestamps[i],
                        "position": "aboveBar",
                        "color": "#10b981" if is_win else "#ef4444",
                        "shape": "arrowDown",
                        "text": f"EXIT #{trade_id}: {pnl_pct:+.2f}%",
                        "size": 1.2
                    })
                    
                    trades.append({
                        "id": f"TR-{trade_id:03d}",
                        "type": "LONG",
                        "entry_time": timestamps[entry_idx],
                        "entry_price": round(entry_p, 2),
                        "exit_time": timestamps[i],
                        "exit_price": round(exit_p, 2),
                        "sl_price": sl_p,
                        "tp_price": tp_p,
                        "pnl_pct": round(pnl_pct, 2),
                        "result": "WIN" if is_win else "LOSS",
                        "duration_bars": i - entry_idx
                    })
                    in_pos = False
                    trade_id += 1

    markers.sort(key=lambda x: x['time'])
    
    return {
        "strategy_id": strat_id,
        "asset": asset,
        "timeframe": tf,
        "type": strat_type,
        "total_candles": len(candles),
        "candles": candles,
        "volume": volume_series,
        "overlays": overlays,
        "oscillators": oscillators,
        "trades": trades,
        "markers": markers
    }
