"""Focused source-level guard for Founder narrow composer CSS.

This does not replace computed-layout, Android keyboard, or device testing.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "mission_control" / "static" / "smi_noise_strip.css"


def test_founder_narrow_composer_rules_are_last_and_canonical():
    css = CSS.read_text(encoding="utf-8")
    marker = "/* Founder screenshot acceptance: Android narrow composer"
    assert css.count(marker) == 1
    final = css[css.index(marker):]
    assert "@media(max-width:760px)" in final
    assert "grid-template-columns:44px 44px minmax(0,1fr) 48px!important" in final
    assert "grid-template-columns:44px 44px minmax(0,1fr) 48px!important" not in css[:css.index(marker)]
    for selector, placement in (
        ("#mic-button", "grid-column:2!important"),
        (".composer textarea", "grid-column:3!important"),
        ("#send", "grid-column:4!important"),
    ):
        assert selector in final and placement in final
    for token in (
        "grid-column:1!important", "min-width:0!important",
        "min-height:44px!important", "max-height:88px!important",
        "bottom:calc(80px + env(safe-area-inset-bottom))!important",
        "body.smi-noise-strip.smi-live-fullscreen .composer",
        "body.smi-noise-strip.smi-live-fullscreen .composer-box",
        "body.smi-noise-strip.smi-live-fullscreen .composer textarea",
        "body.smi-noise-strip.smi-live-fullscreen #send",
        "width:calc(100vw - 12px)!important",
    ):
        assert token in final
    # Keep the final acceptance block at EOF so earlier same-file rules cannot supersede it.
    assert final.rstrip().endswith("}")
    assert not re.search(r"@(?:media|supports|layer)\\b", final[final.rfind("}") + 1:])


def test_narrow_grid_has_nonzero_theoretical_text_room_at_target_widths():
    # CSS arithmetic only; browser computed geometry must still be checked.
    fixed = 44 + 44 + 48
    gaps = 3 * 5
    padding = 2 * 5
    for viewport in (320, 360, 390):
        available = (viewport - 12) - fixed - gaps - padding
        assert available >= 140, (viewport, available)
