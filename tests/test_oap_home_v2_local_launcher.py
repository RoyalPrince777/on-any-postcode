"""Home V2 local launcher must remain explicit and loopback-only."""
import ast
import os
import subprocess
import sys
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


def test_direct_termux_script_launch_finds_repo_app_without_pythonpath(tmp_path):
    """Direct CLI launch must work even when cwd is the scripts directory."""
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / LAUNCHER.name).write_text(LAUNCHER.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "app.py").write_text(
        'class App:\n'
        '    def run(self, **kwargs):\n'
        '        print("LOCAL_LAUNCH_OK", kwargs["host"], kwargs["port"], kwargs["debug"])\n'
        'app = App()\n',
        encoding="utf-8",
    )
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("OAP_HOME_V2_HOST", None)
    result = subprocess.run(
        [sys.executable, str(scripts / LAUNCHER.name)],
        cwd=scripts,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "LOCAL_LAUNCH_OK 127.0.0.1 5050 False" in result.stdout


def test_direct_launcher_refuses_lan_bind(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / LAUNCHER.name).write_text(LAUNCHER.read_text(encoding="utf-8"), encoding="utf-8")
    env = os.environ.copy()
    env["OAP_HOME_V2_HOST"] = "0.0.0.0"
    result = subprocess.run(
        [sys.executable, str(scripts / LAUNCHER.name)],
        cwd=scripts,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode != 0
    assert "loopback-only host required" in result.stderr
