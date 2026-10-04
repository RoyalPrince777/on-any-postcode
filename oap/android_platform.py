"""Machine-readable truth boundary for OAP Android generations."""
from __future__ import annotations

GENERATION_0 = {
    "name": "OAP Android Host",
    "status": "ACTIVE_REFERENCE",
    "kernel": "Android/Linux upstream host",
    "framework": "Android upstream host",
    "renderer": "Android System WebView",
    "oap_owned": (
        "OAP World application shell",
        "OAP Browser product layer",
        "OAP service integration",
        "OAP security policy",
    ),
}

GENERATION_1 = {
    "name": "OAP Android Distribution",
    "status": "ARCHITECTURE_ONLY",
    "upstream_base": "AOSP-compatible Android open-source base",
    "oap_owned_target": (
        "build configuration",
        "system image composition",
        "launcher/front door",
        "OAP Browser integration",
        "privacy defaults",
        "update policy",
        "recovery policy",
        "OAP services",
        "Guardian policy",
        "SMI integration",
    ),
    "still_requires_upstream_or_vendor_support": (
        "Linux kernel/board support",
        "bootloader support",
        "GPU/display drivers",
        "radio/modem firmware",
        "camera/sensor drivers",
        "device-specific HALs",
    ),
}

GENERATION_2 = {
    "name": "OAP Device Platform",
    "status": "FUTURE",
    "goal": "OAP-controlled OS image on explicitly supported hardware with verified boot, signed updates and recovery.",
}


def status() -> dict[str, object]:
    return {
        "generation_0": GENERATION_0,
        "generation_1": GENERATION_1,
        "generation_2": GENERATION_2,
        "custom_android_os_exists": False,
        "oap_rendering_engine_standards_complete": False,
    }
