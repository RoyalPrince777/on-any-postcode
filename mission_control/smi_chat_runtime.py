"""Grounded OAP Mind runtime facade.

The existing governed chat runtime remains the single implementation. This facade
adds a verified-evidence contract around provider generation without changing
identity, permission, HRM, Judgement, Aegis or Human Authority boundaries.
"""
from __future__ import annotations

from collections.abc import Callable

from . import smi_chat_grounded as _grounded
from . import smi_chat_runtime_core as _core
from .smi_chat_runtime_core import *  # noqa: F401,F403

_ORIGINAL_PROVIDER = _core._provider


def _grounded_provider(
    message: str,
    image_data: str = "",
    history: list[dict[str, str]] | None = None,
    brain: dict | None = None,
    adaptive_memory: list[str] | None = None,
    media: dict | None = None,
    *,
    code_mode: bool = False,
    on_delta: Callable[[str], None] | None = None,
) -> str:
    return _grounded.grounded_provider(
        _ORIGINAL_PROVIDER,
        _core.health,
        message,
        image_data,
        history,
        brain,
        adaptive_memory,
        media,
        code_mode=code_mode,
        on_delta=on_delta,
    )


# chat()/chat_events() resolve _provider from the core module at runtime, so the
# provider path is upgraded once without duplicating the governed chat logic.
_core._provider = _grounded_provider
