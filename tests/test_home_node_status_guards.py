"""Regression checks for Home Node status fail-closed state handling."""
from __future__ import annotations

import ast
from pathlib import Path


def test_home_node_status_guards_json_shape_and_pid_types() -> None:
    source = Path("scripts/oap_home_node_status.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "isinstance"
        and node.args
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "loaded"
        for node in ast.walk(tree)
    )
    assert 'isinstance(pid, bool)' in source
    assert 'pid.isdecimal()' in source


def test_home_node_heartbeat_freshness_boundaries() -> None:
    source = Path("scripts/oap_home_node_status.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    fn = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "_recent_state")
    namespace = {"time": __import__("time")}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "<heartbeat>", "exec"), namespace)
    recent = namespace["_recent_state"]
    assert recent(100, now=100)
    assert recent(85, now=100)
    assert not recent(84.9, now=100)
    assert not recent(101, now=100)
    assert not recent(None, now=100)
    assert not recent(True, now=100)
    assert not recent("100", now=100)
    assert 'snapshot["supervisor_heartbeat_recent"]' in source
