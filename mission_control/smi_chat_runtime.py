"""Grounded Personal SMI runtime facade.

The governed chat runtime remains the single implementation. Generation is routed
through the OAP-owned local-first inference gateway, then bounded by the verified
evidence contract. Identity, permission, HRM, Judgement, Aegis, Living Kernel and
Human Authority boundaries are unchanged.
"""
from __future__ import annotations

from collections.abc import Callable

from . import oap_inference_gateway as _inference
from . import smi_chat_grounded as _grounded
from . import smi_chat_runtime_core as _core
from .smi_chat_runtime_core import *  # noqa: F401,F403

_COMPATIBILITY_ENGINE = _core._provider


def health() -> dict:
    """Return core SMI health plus truthful Home Node inference certification."""
    snapshot = dict(_core.health())
    snapshot["inference"] = _inference.status(probe=True)
    return snapshot


def _gateway_provider(
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
    return _inference.generate(
        _COMPATIBILITY_ENGINE,
        message,
        image_data,
        history,
        brain,
        adaptive_memory,
        media,
        code_mode=code_mode,
        on_delta=on_delta,
    )


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
        _gateway_provider,
        health,
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
# provider path is upgraded once without duplicating governed chat logic.
_core._provider = _grounded_provider
