import json
import time
import urllib.request
from datetime import datetime

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

    prompt = f"""
You are OAP HRM Local Brain.

Read these public OAP pages and create a short HRM learning note.

Rules:
- Do not invent facts.
- Do not publish anything.
- Human approval before action.
- Focus on football urgency, World Cup readiness, bugs, next actions.

Data:
{json.dumps(pages)[:12000]}

Output:
1. What OAP has learned
2. What is urgent
3. Football/World Cup next actions
4. Risks
5. Founder recommendation
"""

    response = ask_ollama(prompt)

    record = {
        "created_at": datetime.utcnow().isoformat(),
        "source": "oap_public_pages",
        "model": MODEL,
        "response": response
    }

    with open("hrm_auto_learnings.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    print(response)

if __name__ == "__main__":
    run_once()
