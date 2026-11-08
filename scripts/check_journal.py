with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\library\journal\PROP_FIRM_SPRINT_JOURNAL.md", "r", encoding="utf-8") as f:
    text = f.read()

print("Journal length:", len(text))
print("Last 1500 chars of journal:")
print(text[-1500:])
