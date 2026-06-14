import re

with open("app.py", "r", encoding="utf-8") as f:
    code = f.read()

routes = re.findall(r"@app\.route\(['\"]([^'\"]+)", code)

print("\n=== OAP ROUTES ===\n")

for r in sorted(set(routes)):
    print(r)

print(f"\nTotal Routes: {len(set(routes))}")

