with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\scripts\scratch_script_4.js", "r", encoding="utf-8") as f:
    text = f.read()

# Replace the broken replace(/[\n\n]+/g with replace(/\s+/g
text = text.replace("const labelText = drag.th.textContent.replace(/[\n\n]+/g, ' ').trim();", "const labelText = (drag.th.innerText || drag.th.textContent || '').trim().replace(/\\s+/g, ' ');")
# Also check if there are other occurrences
if "replace(/[" in text:
    print("Found other broken regex!")
else:
    print("No other broken regex found.")

with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\scripts\scratch_script_4.js", "w", encoding="utf-8") as f:
    f.write(text)
print("Updated scratch_script_4.js")
