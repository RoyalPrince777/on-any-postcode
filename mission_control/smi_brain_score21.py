"""Founder-only SMI Brain 21-point philosophy score.

This score keeps three truths separate:
- Evidence score: what has real proof now.
- Simulation score: what War Room can safely simulate now.
- Philosophy score: whether the Mind/Body/Soul doctrine is complete.

It does not execute, approve, deploy, write receipts, dispatch, spend, or track.
"""
from __future__ import annotations

from typing import Any

SCORE_BLOCKS: tuple[dict[str, object], ...] = (
    {
        "id": "evidence",
        "label": "Evidence score",
        "score": 3,
        "max_score": 7,
        "signal": "yellow",
        "meaning": "Real proof currently covers name, role and protocol mapping only.",
        "passed": (
            "Named",
            "Role defined",
            "Protocol mapped",
        ),
        "needed": (
            "Agent/tool runner proof",
            "HRM/Neon receipt proof",
            "Live War Room proof",
            "Matrix learning proof",
        ),
    },
    {
        "id": "simulation",
        "label": "Simulation score",
        "score": 7,
        "max_score": 7,
        "signal": "green",
        "meaning": "War Room can model the complete 7/7 path safely without granting execution.",
        "passed": (
            "Named in simulation",
            "Role defined in simulation",
            "Protocol mapped in simulation",
            "Agent/tool path simulated",
            "Receipt path simulated",
            "Live proof path simulated",
            "Matrix learning path simulated",
        ),
        "needed": (),
    },
    {
        "id": "philosophy",
        "label": "Philosophy / depth score",
        "score": 7,
        "max_score": 7,
        "signal": "green",
        "meaning": "The 7/7/7 Mind Body Soul doctrine is complete as a governing philosophy.",
        "passed": (
            "Mind 1-7 locked",
            "Body 8-14 locked",
            "Soul 15-21 locked",
            "21 Laws locked",
            "21 Signals locked",
            "Final Judges locked",
            "Founder Authority final locked",
        ),
        "needed": (),
    },
)

BRAIN_PART_NAMES: tuple[str, ...] = (
    "Left Hemisphere",
    "Right Hemisphere",
    "Frontal Lobe",
    "Parietal Lobe",
    "Temporal Lobe",
    "Occipital Lobe",
    "Prefrontal Cortex",
    "Corpus Callosum",
    "Thalamus",
    "Hypothalamus",
    "Hippocampus",
    "Amygdala",
    "Cerebellum",
    "Brainstem",
)


def score21_status() -> dict[str, Any]:
    """Return the 3 + 7 + 7 = 17/21 War Room philosophy score."""

    current = sum(int(block["score"]) for block in SCORE_BLOCKS)
    possible = sum(int(block["max_score"]) for block in SCORE_BLOCKS)
    return {
        "name": "SMI Brain 21 Score",
        "formula": "Evidence 3/7 + Simulation 7/7 + Philosophy 7/7 = 17/21",
        "current": current,
        "possible": possible,
        "percentage": round((current / possible) * 100, 1),
        "signal": "yellow",
        "real_green": False,
        "blocks": SCORE_BLOCKS,
        "applies_to": BRAIN_PART_NAMES,
        "status_meaning": {
            "evidence_3_7": "Real proof is still 3/7 until live runners, HRM/Neon receipts and Matrix learning proof exist.",
            "simulation_7_7": "War Room simulation covers the full 7/7 path for all 14 brain parts.",
            "philosophy_7_7": "The Mind Body Soul 7/7/7 doctrine is complete as a governing rule set.",
            "score_17_21": "The whole system philosophy is mostly formed, but not full real green.",
        },
        "locked_boundary": {
            "no_fake_green": True,
            "no_execution_granted": True,
            "no_self_approval": True,
            "public_private_separation": True,
            "founder_authority_final": True,
        },
        "next_to_21": (
            "Move Evidence from 3/7 to 7/7 with agent/tool runners, HRM/Neon receipts, "
            "live War Room proof and Matrix learning proof."
        ),
    }
