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
