with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('df = pd.DataFrame(subset)')
print(text[idx-50:idx+400])
