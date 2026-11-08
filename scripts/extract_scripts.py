import re

with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Extract scripts
scripts = re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', content, re.DOTALL)
print(f"Found {len(scripts)} inline script blocks.")

for i, s in enumerate(scripts):
    filename = f"scripts/scratch_script_{i+1}.js"
    with open(filename, "w", encoding="utf-8") as sf:
        sf.write(s)
    print(f"Wrote script {i+1} ({len(s)} chars)")
