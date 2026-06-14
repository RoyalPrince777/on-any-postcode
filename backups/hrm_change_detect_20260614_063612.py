import json
import urllib.request
from datetime import datetime, UTC

OAP_URL = "http://127.0.0.1:5050"

def fetch_page(path):
    try:
        with urllib.request.urlopen(OAP_URL + path, timeout=20) as res:
            return res.read().decode("utf-8")[:6000]
    except Exception as e:
        return f"FETCH ERROR ({path}): {e}"

def run_once():
    home = fetch_page("/")

    facts = []
    for text in ["First member", "First business", "First creator", "First experience", "First value created"]:
        if text in home:
            facts.append(f"Homepage mission includes: {text}.")

    if not facts:
        facts.append("No verified homepage facts found.")

    report = f"""1. What OAP has learned
- {chr(10).join(facts)}

2. What is urgent
- Build proof for the first member, business, creator, experience, and value created.
- Do not claim members, partners, events, or campaigns until verified.

3. Football/World Cup next actions
- FIFA World Cup 2026 started on 11 June 2026 and runs to 19 July 2026.
- No verified OAP World Cup activity found yet.
- Next safe action: create verified OAP World Cup content or experience records.

4. Risks
- AI can invent facts if allowed to write freely.
- OAP is still early-stage and needs verified records before expansion.

5. Founder recommendation
- Focus on first real records before public claims.
- Keep human approval before action.
"""

    record = {
        "created_at": datetime.now(UTC).isoformat(),
        "source": "oap_public_pages",
        "model": "python_fact_report_v0.2",
        "facts": facts,
        "response": report
    }

    with open("hrm_auto_learnings.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    print(report)

if __name__ == "__main__":
    run_once()
