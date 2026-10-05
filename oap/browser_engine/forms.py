"""Bounded form/control model for OAP Engine."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .dom import HIDDEN_ELEMENTS, Node
from .origin import resolve_http_url, same_origin

SUPPORTED_METHODS = frozenset({"GET", "POST"})
SUPPORTED_CONTROL_TAGS = frozenset({"input", "button", "select", "textarea"})


@dataclass(frozen=True)
class FormControl:
    tag: str
    control_type: str
    name: str
    value: str
    required: bool
    disabled: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FormModel:
    method: str
    action: str | None
    same_origin_action: bool
    controls: tuple[FormControl, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "method": self.method,
            "action": self.action,
            "same_origin_action": self.same_origin_action,
            "controls": [control.to_dict() for control in self.controls],
        }


def _control(node: Node) -> FormControl:
    input_type = node.attrs.get("type", "text").strip().lower() if node.tag == "input" else node.tag
    value = node.attrs.get("value", "")
    if node.tag in {"button", "textarea"} and not value:
        value = node.text_content()
    if input_type == "password":
        value = ""
    return FormControl(
        tag=node.tag,
        control_type=input_type,
        name=node.attrs.get("name", ""),
        value=value[:16_384],
        required="required" in node.attrs,
        disabled="disabled" in node.attrs,
    )


def extract_forms(root: Node, *, base_url: str) -> tuple[FormModel, ...]:
    forms: list[FormModel] = []
    for node in root.descendants():
        if node.tag != "form":
            continue

        raw_method = node.attrs.get("method", "GET").strip().upper() or "GET"
        method = raw_method if raw_method in SUPPORTED_METHODS else "GET"
        raw_action = node.attrs.get("action", "").strip() or base_url
        action = resolve_http_url(base_url, raw_action)

        controls: list[FormControl] = []
        for child in node.descendants():
            if child.tag in HIDDEN_ELEMENTS or child.tag not in SUPPORTED_CONTROL_TAGS:
                continue
            controls.append(_control(child))

        forms.append(
            FormModel(
                method=method,
                action=action,
                same_origin_action=bool(action and same_origin(base_url, action)),
                controls=tuple(controls),
            )
        )
    return tuple(forms)
