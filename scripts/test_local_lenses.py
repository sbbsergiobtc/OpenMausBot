import urllib.request
import json
import pandas as pd
import numpy as np

# Simulate calling get_analytics with lens=EVALUATION vs lens=FUNDED
import os, sys
sys.path.append(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot")

from dashboard.backend import get_analytics

eval_res = get_analytics(filter='PROP-NDX-005', lens='EVALUATION')
funded_res = get_analytics(filter='PROP-NDX-005', lens='FUNDED')

print("=== PROP-NDX-005 ===")
print("Evaluation Net Profit:", eval_res['kpis']['net_profit'])
print("Funded Net Profit:", funded_res['kpis']['net_profit'])
print("Evaluation Final Bal:", eval_res['kpis']['final_balance'])
print("Funded Final Bal:", funded_res['kpis']['final_balance'])

# Let's test with a filter that has an outlier: PORT-NDX-SPX
eval_port = get_analytics(filter='PORT-NDX-SPX', lens='EVALUATION')
funded_port = get_analytics(filter='PORT-NDX-SPX', lens='FUNDED')

print("\n=== PORT-NDX-SPX ===")
print("Evaluation Net Profit:", eval_port['kpis']['net_profit'])
print("Funded Net Profit:", funded_port['kpis']['net_profit'])
print("Evaluation Max DD:", eval_port['kpis']['max_drawdown'], "%")
print("Funded Max DD:", funded_port['kpis']['max_drawdown'], "%")
print("Evaluation Streaks Count:", len(eval_port['streaks_analysis']['streaks']))
print("Funded Streaks Count:", len(funded_port['streaks_analysis']['streaks']))
print("Verification complete!")
