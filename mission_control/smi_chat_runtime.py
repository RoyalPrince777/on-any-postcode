"""Grounded Personal SMI runtime facade.

The governed chat runtime remains the single implementation. Generation is routed
through the OAP-owned local-first inference gateway, then bounded by the verified
evidence contract. Identity, permission, HRM, Judgement, Aegis, Living Kernel and
Human Authority boundaries are unchanged.
"""
from __future__ import annotations

import queue
import threading
from collections.abc import Callable, Iterator

from . import oap_inference_gateway as _inference
from . import smi_chat_grounded as _grounded
from . import smi_chat_runtime_core as _core
from .smi_chat_runtime_core import *

# Explicit compatibility exports for existing diagnostics/tests. Production chat
# still routes through _core._provider, which is replaced with _grounded_provider
# below; this raw provider alias is not the production routing path.
urlrequest = _core.urlrequest
_provider = _core._provider
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


# chat()/other imported core functions resolve _provider from the core module at
# runtime, so production generation is upgraded once without duplicating chat logic.
_core._provider = _grounded_provider


def chat_events(
    message: object,
    identity_id: str,
    display_name: object,
    conversation_id: object = None,
    image_data: object = None,
    attachment: object = None,
    *,
    code_mode: bool = False,
) -> Iterator[dict]:
    """Facade-safe SSE bridge that calls the public facade ``chat`` symbol.

    Keeping this small bridge here preserves monkeypatch/caller compatibility while
    the canonical chat implementation and all governance remain in the core module.
    """

    event_queue: queue.Queue[dict] = queue.Queue(maxsize=256)

    def emit(item: dict) -> None:
        event_queue.put(item, timeout=60)

    def worker() -> None:
        try:
            result = chat(
                message,
                identity_id,
                display_name,
                conversation_id,
                image_data,
                attachment,
                code_mode=code_mode,
                on_event=emit,
            )
            emit({"type": "complete", "result": result})
        except (TypeError, ValueError) as exc:
            code = "rate_limited" if str(exc) == "chat_rate_limit" else "invalid_request"
            message_text = (
                "Too many SMI requests. Wait one minute and try again."
                if code == "rate_limited"
                else str(exc)[:120]
            )
            emit({"type": "error", "code": code, "message": message_text})
        except PermissionError:
            emit({
                "type": "error",
                "code": "permission_denied",
                "message": "REQUEST_RECOMMENDATION permission required.",
            })
        except RuntimeError:
            emit({
                "type": "error",
                "code": "provider_unavailable",
                "message": "SMI is temporarily unavailable. No completion was recorded.",
            })
        except Exception:  # noqa: BLE001 -- final thread boundary must fail closed
            emit({
                "type": "error",
                "code": "internal_error",
                "message": "The governed request did not complete safely.",
            })
        finally:
            event_queue.put({"type": "_done"})

    threading.Thread(target=worker, name="oap-smi-stream-facade", daemon=True).start()
    while True:
        try:
            item = event_queue.get(timeout=15)
        except queue.Empty:
            yield {"type": "heartbeat", "status": "working"}
            continue
        if item.get("type") == "_done":
            return
        yield item
