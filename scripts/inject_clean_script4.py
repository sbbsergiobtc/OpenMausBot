import re

INDEX_PATH = r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\templates\index.html"
SCRIPT4_PATH = r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\scripts\scratch_script_4.js"

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    html = f.read()

with open(SCRIPT4_PATH, "r", encoding="utf-8") as f:
    clean_js = f.read()

# Replace the last inline script
pattern = re.compile(r'(<!-- =========================================================================\s*ALGROK UNIVERSAL MOTION TABLE COLUMN DRAG & REORDER ENGINE.*?<script>)(.*?)(</script>\s*</body>)', re.DOTALL)

m = pattern.search(html)
if m:
    html = html[:m.start(2)] + clean_js + html[m.end(2):]
    print("[OK] Replaced last script with clean, validated script 4!")
else:
    print("[ERROR] Could not match target script in index.html!")

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("[SUCCESS] index.html written successfully!")
