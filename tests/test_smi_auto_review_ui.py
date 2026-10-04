from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "mission_control" / "static" / "smi_chat_final.js"
RUNTIME = ROOT / "mission_control" / "smi_chat_runtime_core.py"


def test_smi_page_renders_server_generated_auto_vote_board():
    text = JS.read_text(encoding="utf-8")
    for marker in (
        "SMI AUTO · Evidence Vote Board",
        "smi-auto-review-card",
        "result.auto_review",
        "result.active_reviewers",
        "Votes advise only; they grant no authority.",
    ):
        assert marker in text


def test_smi_runtime_routes_auto_mode_and_named_reviewers():
    text = RUNTIME.read_text(encoding="utf-8")
    for marker in (
        '"SMI_AUTO"',
        'smi_auto_review.selected_roles',
        'brain["active_reviewers"]',
        'smi_auto_review.build_vote_board',
        '"auto_review": auto_review',
    ):
        assert marker in text
