with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find('function renderMainEquityChart')
print(text[idx:idx+1800])
