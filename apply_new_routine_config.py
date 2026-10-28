import json

path = '/root/.openmausbot/routines.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

new_prompt = """Ejecuta el ciclo de investigación y desarrollo cuantitativo del enjambre AlgrokQuant bajo la gobernanza oficial LESSON-20261028-017 y arquitectura JevScreener 5+1:

1. RAMA 1 - CUENTAS FONDEADAS (PROP FIRM: FUTUROS & FOREX):
   a) Universo: Índices CME Globex (NDX, SPX) y Cruces Forex (FX).
   b) Regla Fundamental de Riesgo: Drawdown evaluado exclusivamente a CIERRE DE DÍA (End of Day / EOD Drawdown). Prohibido cálculo por trailing intradía.
   c) Futuros (Cuentas 50k, 100k, 150k):
      - Target de Beneficio: 6.0%.
      - Max EOD Drawdown Maestro: <= 3.0% (Apto universalmente para 150k [3%], 100k [3.5%] y 50k [4%]).
      - Regla de Consistencia: Máximo 40% del profit total generado en un único día.
      - Max Daily Loss: Control estricto de pérdida máxima intradiaria.
      - "Cajón de Estrategias por Régimen": No forzar 10 años continuos ciegos. Diseñar estrategias tácticas cortas especializadas condicionadas a filtros de régimen (Tendencial Fuerte, Rango/Compresión, o Expansión de Volatilidad) usando el histórico de 10 años Parquet (/data/parquet_cache/).
   d) Forex: Target de Beneficio: 8.0% | Max EOD Drawdown: <= 8.0% | Consistencia: 40% | Max Daily Loss.

2. RAMA 2 - CAPITAL PROPIO (TRACK FAST: CRIPTO & ÍNDICES):
   a) Universo: Criptomonedas (BTC, ETH, SOL) e Índices (NDX, SPX).
   b) Rentabilidad Mínima Exigida: CAGR >= 30.0% anual neta (tras comisiones taker de 14 bps y slippage).
   c) Benchmark Pasivo: Retorno obligatoriamente SUPERIOR a Buy & Hold del activo en todo el backtest y en la fase Out-of-Sample (OOS).
   d) Techo de Drawdown Máximo: Max DD <= 20.0% con dimensionamiento dinámico de riesgo (0.50% - 1.50% equity vía ATR).

3. METODOLOGÍA VECTORIAL Y AUDITORÍA DETERMINISTA:
   a) CoderQuant explora obligatoriamente Mesetas Paramétricas (Parameter Plateau) barriendo rejillas de 200-500 combinaciones en VectorBT/NumPy en CPU. Prohibido optimizar a un único punto aislado.
   b) JevScreener filtra: correlación < 0.80, Profit Factor >= 1.50, mínimo 30-50 operaciones y degradación OOS < 40%.
   c) Auditor y Skeptic ejecutan Walk-Forward (IS vs OOS de 24 meses) y Test de Estrés Monte Carlo (1.000 iteraciones con shock de fricción 3x).
   d) Las estrategias aprobadas se catalogan en /library/strategies/ como APROBADA y se promueven a forward test. Las rechazadas documentan su fallo en /library/lessons/.
   e) Nexus emite el resumen de la sesión con métricas multianuales y actualización de estado."""

target_id = 'd7442499-ec81-4573-b684-1275063a13dd'
updated = False

for r in data.get('routines', []):
    if r.get('id') == target_id:
        r['name'] = 'Investigación Cuantitativa Tri-Diaria AlgrokQuant (Prop Firm EOD & Capital Propio)'
        r['prompt'] = new_prompt
        r['schedule'] = {
            'type': 'cron',
            'expression': '0 8,14,20 * * *',
            'timeZone': 'Europe/Madrid'
        }
        updated = True
        print(f"Rutina {target_id} actualizada exitosamente.")
        print(f"Nuevo Schedule: {r['schedule']}")

if updated:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("routines.json guardado con éxito en disco.")
else:
    print(f"ERROR: No se encontró la rutina con ID {target_id}")
