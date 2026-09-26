"""Single first-party Music Civilization readiness coordinator.

This module composes existing OAP Music, Radio, Records, Live and Universal
Player contracts. It never upgrades a missing proof into permission and never
claims public playback, broadcasting or external distribution.
"""
from __future__ import annotations

from collections.abc import Mapping

from . import entertainment_catalogue, live_music_core, radio_core, records_core


def readiness(
    *,
    music_gate: object,
    radio_state: object = None,
    live_state: object = None,
    records_state: object = None,
    recovery_state: object = None,
) -> dict[str, object]:
    music = music_gate if isinstance(music_gate, Mapping) else {}
    radio = radio_state if isinstance(radio_state, Mapping) else {}
    live = live_state if isinstance(live_state, Mapping) else {}
    records = records_state if isinstance(records_state, Mapping) else {}
    recovery = recovery_state if isinstance(recovery_state, Mapping) else {}

    private_music_ready = music.get("private_handoff_ready") is True
    recovery_verified = recovery.get("readback_verified") is True
    radio_stopped = radio.get("stopped") is not False
    live_stopped = live.get("stopped") is not False

    return {
        "organ": "OAP Music Civilization",
        "music_private_handoff_ready": private_music_ready,
        "recovery_readback_verified": recovery_verified,
        "records_private_archive_ready": bool(
            private_music_ready and recovery_verified
        ),
        "radio_private_rotation_ready": bool(
            private_music_ready and recovery_verified and not radio_stopped
        ),
        "live_private_handoff_ready": bool(
            private_music_ready and recovery_verified and not live_stopped
        ),
        "radio_stopped": radio_stopped,
        "live_stopped": live_stopped,
        "records_receipt_present": bool(records.get("records_receipt_id")),
        "player": entertainment_catalogue.universal_player_contract(),
        "public_playback_enabled": False,
        "public_radio_enabled": False,
        "public_live_enabled": False,
        "external_distribution_enabled": False,
        "payment_execution_enabled": False,
        "human_authority_final": True,
    }


def contracts() -> dict[str, object]:
    return {
        "organ": "OAP Music Civilization",
        "music": entertainment_catalogue.universal_player_contract(),
        "radio": radio_core.radio_contract(),
        "records": records_core.records_contract(),
        "live": live_music_core.live_contract(),
        "one_player": True,
        "duplicate_media_engine_created": False,
        "public_execution_enabled": False,
        "human_authority_final": True,
    }
