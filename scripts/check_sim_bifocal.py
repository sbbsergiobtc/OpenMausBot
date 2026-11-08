import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\jev\simulator.py", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('def generate_bifocal_backtest_report')
print(text[idx:idx+2500])
