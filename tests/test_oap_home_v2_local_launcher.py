"""Home V2 local launcher must remain explicit and loopback-only."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "oap_home_v2_local.py"


def test_home_v2_launcher_is_loopback_only_without_debug():
    source = LAUNCHER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    runs = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run"
    ]
    assert len(runs) == 1
    kwargs = {kw.arg: kw.value for kw in runs[0].keywords}
    assert ast.literal_eval(kwargs["host"]) == "127.0.0.1"
    assert ast.literal_eval(kwargs["port"]) == 5050
    assert ast.literal_eval(kwargs["debug"]) is False
    assert ast.literal_eval(kwargs["use_reloader"]) is False


def test_home_v2_launcher_is_not_started_on_import():
    tree = ast.parse(LAUNCHER.read_text(encoding="utf-8"))
    assert any(
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "__name__"
        for node in tree.body
    )
