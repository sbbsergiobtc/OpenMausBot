import json

path = '/root/.openmausbot/routines.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

new_prompt = """Ejecuta el ciclo diario autónomo del enjambre AlgrokQuant bajo la gobernanza oficial LESSON-20261028-014 y la arquitectura JevScreener 5+1:
1. StratFinder e Ideator formulan 2-3 hipótesis de mercado con edge económico fundamentado (Crypto BTC/ETH/SOL o Índices CME Globex NDX/SPX en 1h/2h/1D). PROHIBIDO reversión rápida en 15m con alto turnover y comisiones taker. Generan fichas en /library/ideas/.
2. CoderQuant traduce las hipótesis a código vectorial con VectorBT. PROHIBIDO limitarse a un único valor fijo arbitrario o a solo 12 meses. OBLIGATORIO:
   a) Explorar mesetas paramétricas de robustez (Parameter Plateau) barriendo un grid de 200-500 combinaciones en NumPy.
   b) Evaluar en los 3 Horizontes Temporales de gobernanza: Táctico (1-2 años), Cíclico Swing (3-5 años) y Macro Estructural (10 años Parquet en /data/parquet_cache/).
   c) Fricciones reales de mercado (14 bps Hyperliquid o spread/slippage CFD) y sizing dinámico porcentual (0.50% - 1.50% equity). Prohibidos dólares fijos.
3. JevScreener filtra deterministamente: descarta correlaciones > 0.80, exige Max DD <= 20.0% (<= 3.5% Prop Firm), Profit Factor >= 1.30, total trades >= 30, Stagnation Days <= 45d y degradación OOS R/DD < 40%.
4. Auditor y Skeptic auditan estabilidad fuera de muestra (WFM OOS), consistencia de rachas por activo y estrés macro.
5. Si una estrategia supera la batería de meseta y gobernanza, se cataloga en /library/strategies/ como APROBADA y se promueve a forward test. Si falla, se documenta la lección en /library/lessons/.
6. Nexus envía el informe consolidado con las métricas multianuales y estado de la cartera."""

updated = False
for r in data.get('routines', []):
    if r.get('id') == 'd7442499-ec81-4573-b684-1275063a13dd':
        r['prompt'] = new_prompt
        updated = True
        print('Routine prompt updated successfully')

if updated:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print('File routines.json saved successfully')
else:
    print('Routine id not found!')
