with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py", "r", encoding="utf-8") as f:
    text = f.read()

# Extract compute_bifocal_metrics definition
start_fn = text.find('def compute_bifocal_metrics(')
end_fn = text.find('\n\ndef get_analytics(')
fn_body = text[start_fn:end_fn]

# Remove it from between @app.get and def get_analytics
text = text[:start_fn] + text[end_fn+2:]

# Now place fn_body BEFORE @app.get("/api/analytics")
route_idx = text.find('@app.get("/api/analytics")')
text = text[:route_idx] + fn_body + "\n\n" + text[route_idx:]

with open(r"C:\Users\Sergio\Documents\Antigravity\OpenMausBot\dashboard\backend.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Fixed route decorator in backend.py!")
