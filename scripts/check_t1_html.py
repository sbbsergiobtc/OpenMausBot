with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html", "r", encoding="utf-8") as f:
    text = f.read()

# Let's inspect Table 1 header row:
idx = text.find('id="table-portfolio"')
table_chunk = text[idx:idx+2500]
print(table_chunk[:1500])
