with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py", "r", encoding="utf-8") as f:
    text = f.read()

# Let's inspect where compute_bifocal_metrics is in backend.py
idx = text.find('compute_bifocal_metrics')
print(text[max(0, idx-200):idx+300])
