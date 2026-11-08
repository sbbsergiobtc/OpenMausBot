with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\scripts\scratch_script_4.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(max(0, 245), min(len(lines), 265)):
    print(f"{i+1}: {repr(lines[i])}")
