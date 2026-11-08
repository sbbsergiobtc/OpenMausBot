with open(r'C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('portfolio-table-tbody')
print("Index:", idx)
if idx != -1:
    print(text[max(0, idx-600):idx+200])
