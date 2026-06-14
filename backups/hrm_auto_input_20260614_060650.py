import json
import urllib.request
from datetime import datetime, UTC

OAP_URL = "http://127.0.0.1:5050"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:1.5b"


def fetch_page(path):
    try:
        with urllib.request.urlopen(OAP_URL + path, timeout=20) as res:
            return res.read().decode("utf-8")[:6000]
    except Exception as e:
        return f"FETCH ERROR {path}: {e}"


def ask_ollama(prompt):
    data = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req, timeout=300) as res:
        out = json.loads(res.read().decode("utf-8"))
        return out.get("response", "")


def run_once():
    pages = {
        "home": fetch_page("/"),
        "world_cup": fetch_page("//"),
        "prince_dashboard": fetch_page("/prince-dashboard"),
        "sovereign": fetch_page("/sovereign-megaverse"),
        "community": fetch_page("/community-power"),
    }

    facts = []

    home = pages.get("home", "")

    checks = [
        ("First member", "Homepage mission focuses on first member."),
        ("First business", "Homepage mission focuses on first business."),
        ("First creator", "Homepage mission focuses on first creator."),
        ("First experience", "Homepage mission focuses on first experience."),
        ("First value created", "Homepage mission focuses on first value created.")
    ]

    for needle, fact in checks:
        if needle in home:
            facts.append(fact)

    if not facts:
        facts.append("No verified homepage facts found.")

    prompt = f"""
You are OAP HRM Local Brain.

Current real date: 14 June 2026.
FIFA World Cup 2026 started on 11 June 2026 and runs to 19 July 2026.

Rules:
- Only use Verified Facts.
- Do not invent facts.
- Do not publish anything.
- Human approval before action.
- Do not invent members, staff, partners, metrics, events, webinars, social media campaigns, or results.
- If evidence is missing, say "No evidence found."
- Act as agents:
  Guardian checks risk.
  Chancellor records facts.
  Bee gives next actions.
- Keep report under 180 words.

Verified Facts:
{json.dumps(facts)}

Unverified page data ignored.

Output:
1. What OAP has learned
2. What is urgent
3. Football/World Cup next actions
4. Risks
5. Founder recommendation
"""

    response = ask_ollama(prompt)

    record = {
        "created_at": datetime.now(UTC).isoformat(),
        "source": "oap_public_pages",
        "model": MODEL,
        "facts": facts,
        "response": response
    }

    with open("hrm_auto_learnings.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    print(response)


if __name__ == "__main__":
    run_once()
