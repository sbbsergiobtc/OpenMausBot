with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\scripts\scratch_script_4.js", "r", encoding="utf-8") as f:
    text = f.read()

print("Length of script 4:", len(text))
# Check onGlobalPointerMove, onHeaderPointerDown, updateDropTarget, reorderColumn, applyOrderToTable
print("Has onHeaderPointerDown:", "onHeaderPointerDown" in text)
print("Has onGlobalPointerMove:", "onGlobalPointerMove" in text)
print("Has onGlobalPointerUp:", "onGlobalPointerUp" in text)
print("Has reorderColumn:", "reorderColumn" in text)
