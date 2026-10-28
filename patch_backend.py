from pathlib import Path

backend_path = Path('/root/AlgrokQuant/dashboard/backend.py')
content = backend_path.read_text(encoding='utf-8')

backup_path = Path('/root/AlgrokQuant/dashboard/backend.py.prechart')
if not backup_path.exists():
  backup_path.write_text(content, encoding='utf-8')

chart_code = """
# ==============================================================================
# TRADINGVIEW CHARTING & INDICATOR AUDIT ENDPOINTS
# ==============================================================================
from dashboard.chart_service import get_available_chart_strategies, build_chart_payload

@app.get("/api/chart_strategies")
def get_chart_strategies_endpoint():
    \"\"\"Devuelve el catálogo de estrategias disponibles para visualización TradingView.\"\"\"
    return get_available_chart_strategies()

@app.get("/api/chart/{strategy_id}")
def get_chart_endpoint(strategy_id: str, bars: int = Query(1500)):
    \"\"\"
    Devuelve velas OHLCV, indicadores overlay (EMA, Donchian, Bollinger),
    osciladores (Shannon Entropy, CMF, RSI) y marcadores de entrada/salida (SL/TP).
    \"\"\"
    try:
        return build_chart_payload(strategy_id, window_bars=bars)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':"""

if "get_chart_strategies_endpoint" not in content:
  if "if __name__ == '__main__':" in content:
    content = content.replace("if __name__ == '__main__':", chart_code)
    backend_path.write_text(content, encoding='utf-8')
    print("backend.py parcheado con endpoints de TradingView exitosamente.")
  else:
    print("ERROR: no se encontró 'if __name__ == '__main__':'")
else:
  print("Endpoints de TradingView ya existían en backend.py.")
