with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(max(0, 1505), min(len(lines), 1535)):
    print(f"{i+1}: {repr(lines[i])}")
