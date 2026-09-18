"""Canonical Founder-facing OAP Studio Intelligence contract.

Studio is the private creation and media-intelligence workspace powered by SMI.
SMI Chat may capture media and route it here; it must not duplicate Studio's media
reasoning, creation, editing or packaging engine. Studio does not expand execution,
publishing, rights, payment or distribution authority. Human Authority remains
final and external delivery stays locked until its existing proof gates pass.
The public Spot does not expose this Founder-only surface.
"""

from __future__ import annotations

from typing import Any

STUDIO_ID = "oap-studio-intelligence"
STUDIO_NAME = "OAP Studio Intelligence"
TABS = (
    "Home",
    "Projects",
    "Bring In",
    "Create",
    "Shape",
    "Intelligence",
    "Rights",
    "Release",
    "Campaign",
    "Analyse",
    "Chronicle",
)
PIPELINE = (
    "Create",
    "Shape",
    "Package",
    "Rights",
    "Release",
    "Distribute",
    "Campaign",
    "Analyse",
    "Chronicle",
)
PRIMARY_ACTIONS = (
    "New Project",
    "Bring In",
    "Capture",
    "Imagine",
    "Shape",
    "Studio Intelligence",
    "Rights",
    "Prepare Release",
    "Chronicle",
)
CREATION_MODES = (
    "Imagine",
    "Bring Alive",
    "Rework",
    "Extend",
    "Clean",
    "Reframe",
    "Restyle",
    "Build Variations",
    "Lock Look",
    "Match Scene",
)
INTELLIGENCE_ROLES = (
    "Director",
    "Producer",
    "Story Intelligence",
    "Scene Intelligence",
    "Sound Intelligence",
    "Visual Intelligence",
    "Audience Intelligence",
    "Release Intelligence",
    "Rights Intelligence",
    "Chronicle Intelligence",
)
STUDIO_COUNCIL = (
    "Director",
    "Producer",
    "Visual",
    "Sound",
    "Story",
    "Rights",
    "Release",
)
REVIEW_DEPTHS = (3, 7, 21)

MEDIA = (
    "image",
    "audio",
    "video",
    "documents",
    "music",
    "campaigns",
    "creator products",
)
CAPTURE_INPUTS = (
    "device",
    "camera",
    "voice",
    "screen",
    "image attachment",
    "audio attachment",
    "video attachment",
    "document attachment",
    "spreadsheet attachment",
    "presentation attachment",
    "url",
    "project folder",
    "OAP World",
    "The Spot",
    "Chronicle",
    "OAP Music",
    "OAP TV & Media",
    "My Shop",
    "The Link",
)
ENTRY_POINTS = (
    "SMI Chat",
    "OAP Studio Intelligence",
)
DESTINATIONS = (
    "Pulse",
    "Signal",
    "OAP TV & Media",
    "OAP Music",
    "OAP Radio",
    "OAP Player",
    "OAP Records",
    "OAP Distribution",
    "Market",
    "My Shop",
    "Chronicle",
    "The Spot",
)
OUTPUT_PACKS = (
    "Pulse Cut",
    "Signal Pack",
    "TV Master",
    "Radio Cut",
    "Music Pack",
    "Player Version",
    "Market Pack",
    "My Shop Pack",
    "Activity Pack",
    "Chronicle Master",
)
SPOT_PLACEMENT = {
    "public_surface": "OAP Studio",
    "private_engine": "OAP Studio Intelligence",
    "position": "after Activity / Adventure and before Explorer / Market",
    "public_private_boundary": "The public Spot never exposes Founder-only SMI controls.",
}


GENERATION_TOOLS = (
    {"name": "Imagine", "input": "text", "output": "image", "purpose": "Create a new visual from an idea."},
    {"name": "Bring Alive", "input": "image", "output": "video", "purpose": "Add motion, camera movement, expression and atmosphere."},
    {"name": "Scene Builder", "input": "text", "output": "video", "purpose": "Build an approved scene card, then generate a controlled scene."},
    {"name": "Rework", "input": "image", "output": "image", "purpose": "Transform or redesign an existing image."},
    {"name": "Motion Rework", "input": "video", "output": "video", "purpose": "Change style, pacing, setting, framing or look of existing footage."},
    {"name": "Voice Build", "input": "text", "output": "speech", "purpose": "Prepare narration, dialogue and voiceover."},
    {"name": "Sound Build", "input": "text", "output": "audio", "purpose": "Prepare ambience, effects and non-song sound design."},
    {"name": "Music Build", "input": "text", "output": "music", "purpose": "Prepare original music concepts, instrumentals, stings and themes."},
    {"name": "Speak It", "input": "audio", "output": "text", "purpose": "Transcript, captions and searchable dialogue."},
    {"name": "See It", "input": "video", "output": "text", "purpose": "Scene description, highlights, chapters and summaries."},
    {"name": "Visual Read", "input": "image", "output": "text", "purpose": "Describe, classify and understand imagery."},
    {"name": "Sequence Builder", "input": "multiple_images", "output": "video", "purpose": "Build continuity, transitions, timing, camera direction and soundtrack across images."},
    {"name": "Build From Sketch", "input": "sketch", "output": "image", "purpose": "Create a finished image while preserving composition."},
    {"name": "Turn Around", "input": "image", "output": "multi_angle_reference", "purpose": "Prepare front, back, side, three-quarter and product-spin references."},
    {"name": "Find The Moment", "input": "video", "output": "highlights", "purpose": "Find strongest moments and build highlight outputs."},
    {"name": "Break It Down", "input": "long_video", "output": "multi_format_short_content", "purpose": "Turn a long master into short-form OAP outputs."},
    {"name": "Visualise Sound", "input": "audio", "output": "video", "purpose": "Create lyric, music, story, caption or podcast visuals."},
    {"name": "Voice Shape", "input": "voice", "output": "voice", "purpose": "Clean, enhance, translate, dub and reshape approved voice."},
    {"name": "Sound Scene", "input": "text", "output": "sfx", "purpose": "Prepare environment and scene sound effects."},
    {"name": "Speak Scene", "input": "image_or_video_plus_audio", "output": "dialogue_video", "purpose": "Lip sync, dialogue replacement, multi-speaker scenes and dubbing with consent gates."},
    {"name": "Music Video Builder", "input": "image_or_images_plus_music", "output": "music_video", "purpose": "Lay picture to music with beat-aware motion, scenes, transitions and continuity."},
)

IMAGINE_CONTROLS = (
    "Subject", "Place", "Time", "Mood", "Camera", "Lighting", "Composition",
    "Clothing", "Colours", "Texture", "Era", "Weather", "Aspect Ratio", "OAP Look",
)
IMAGINE_ACTIONS = (
    "Make Realistic", "Make Cinematic", "Make Poster", "Make Cover",
    "Make Product Shot", "Make Story Card", "Make Thumbnail",
    "Make Transparent", "Build Variations",
)
MOTION_TYPES = (
    "Camera Move", "Subject Move", "Environment Move", "Expression", "Wind",
    "Crowd", "Vehicle", "Water", "Light", "Weather",
)
CAMERA_MOVES = (
    "Push In", "Pull Out", "Pan", "Tilt", "Orbit", "Track", "Handheld", "Static", "Drone Feel",
)
MOTION_STRENGTH = ("Still", "Gentle", "Natural", "Strong", "Dramatic")
CONSISTENCY_LOCKS = (
    "Keep Face", "Keep Clothes", "Keep Logo", "Lock Background",
    "Lock Character", "Lock Product", "Identity Lock", "Product Lock", "World Lock",
)
SCENE_TYPES = (
    "Film Scene", "Music Visual", "Advert", "Documentary", "News Piece",
    "Promo", "Story", "Product Demo", "Event Intro",
)
REWORK_ACTIONS = (
    "Replace Object", "Remove Object", "Change Clothing", "Change Background",
    "Change Weather", "Change Time of Day", "Change Camera Angle",
    "Change Art Direction", "Improve Quality", "Extend Frame",
    "Restore Image", "Clean Image",
)
MOTION_REWORK_ACTIONS = (
    "Restyle Video", "Change Background", "Reframe Vertical / Horizontal",
    "Clean Footage", "Stabilise", "Remove Object", "Replace Object",
    "Change Weather", "Change Lighting", "Slow Motion", "Speed Ramp",
    "Colour Match", "Scene Match", "Select Scene", "Rework Scene Only",
)
UNIVERSAL_CONTROLS = (
    "Identity", "Motion", "Camera", "World", "Look", "Sound",
    "Length", "Ratio", "Quality", "Freedom",
)
ASPECT_RATIOS = ("9:16", "16:9", "1:1", "4:5", "5:4", "3:2", "2:3", "Custom")
VIDEO_DURATIONS = ("10s", "30s", "1m", "2m", "Scene", "Film")
LONG_FORM_RULE = "Longer outputs must be built as approved scenes, then assembled into a master."
VARIATION_ACTIONS = ("Variation A", "Variation B", "Variation C", "Variation D", "Compare", "Pick Best", "Mix Best", "Rework")
MUSIC_VIDEO_TYPES = (
    "Cover Visual", "Lyric Video", "Performance Visual", "Story Music Video",
    "Mood Visual", "Promo Clip", "Full Music Video",
)
MUSIC_VIDEO_MOTION = (
    "Still", "Gentle", "Natural", "Strong", "Cinematic", "Performance", "Dream", "Hype",
)
CHRONICLE_GENERATION_FIELDS = (
    "input", "settings", "source assets", "generated result", "rights status",
    "creator", "timestamp", "chosen version",
)
GENERATION_COUNCIL = (
    "Director", "Visual", "Story", "Continuity", "Rights", "Release", "Guardian",
)
GENERATION_GOVERNANCE = {
    "scene_card_required_for_text_to_video": True,
    "real_person_identity_transform_requires_consent": True,
    "voice_clone_requires_consent": True,
    "commercial_music_release_requires_rights_provenance": True,
    "generation_history_to_chronicle": True,
    "automatic_publication_allowed": False,
    "human_authority_final": True,
}

ACTIVATION_PROMPT = (
    "OAP Studio Intelligence mode. Help me create, edit, package, check rights, "
    "prepare publishing, distribution, campaign and analysis for: "
)


def status() -> dict[str, Any]:
    """Return the secret-free Studio contract for the Founder workbench."""

    return {
        "id": STUDIO_ID,
        "name": STUDIO_NAME,
        "ready": True,
        "powered_by": "SMI",
        "tabs": list(TABS),
        "pipeline": list(PIPELINE),
        "primary_actions": list(PRIMARY_ACTIONS),
        "creation_modes": list(CREATION_MODES),
        "intelligence_roles": list(INTELLIGENCE_ROLES),
        "studio_council": list(STUDIO_COUNCIL),
        "review_depths": list(REVIEW_DEPTHS),
        "media": list(MEDIA),
        "capture_inputs": list(CAPTURE_INPUTS),
        "entry_points": list(ENTRY_POINTS),
        "destinations": list(DESTINATIONS),
        "output_packs": list(OUTPUT_PACKS),
        "spot_placement": dict(SPOT_PLACEMENT),
        "generation_tools": [dict(item) for item in GENERATION_TOOLS],
        "imagine_controls": list(IMAGINE_CONTROLS),
        "imagine_actions": list(IMAGINE_ACTIONS),
        "motion_types": list(MOTION_TYPES),
        "camera_moves": list(CAMERA_MOVES),
        "motion_strength": list(MOTION_STRENGTH),
        "consistency_locks": list(CONSISTENCY_LOCKS),
        "scene_types": list(SCENE_TYPES),
        "rework_actions": list(REWORK_ACTIONS),
        "motion_rework_actions": list(MOTION_REWORK_ACTIONS),
        "universal_controls": list(UNIVERSAL_CONTROLS),
        "aspect_ratios": list(ASPECT_RATIOS),
        "video_durations": list(VIDEO_DURATIONS),
        "long_form_rule": LONG_FORM_RULE,
        "variation_actions": list(VARIATION_ACTIONS),
        "music_video_types": list(MUSIC_VIDEO_TYPES),
        "music_video_motion": list(MUSIC_VIDEO_MOTION),
        "chronicle_generation_fields": list(CHRONICLE_GENERATION_FIELDS),
        "generation_council": list(GENERATION_COUNCIL),
        "generation_governance": dict(GENERATION_GOVERNANCE),
        "activation_prompt": ACTIVATION_PROMPT,
        "mode": "Founder creation workspace; recommendation and preparation only",
        "purpose": (
            "Canonical OAP media intelligence for creating, analysing and preparing OAP-owned "
            "media, releases, campaigns and creator products before governed publishing or distribution."
        ),
        "alignment": {
            "smi_chat_is_entry_surface": True,
            "studio_is_canonical_media_engine": True,
            "duplicate_studio_engine_allowed": False,
            "capture_does_not_grant_execution": True,
            "one_source_many_outputs": True,
            "studio_creates_destinations_publish": True,
            "public_studio_private_intelligence_separated": True,
        },
        "governance": {
            "human_authority_final": True,
            "rights_proof_required": True,
            "external_distribution_locked_until_proof": True,
            "payment_authority_granted": False,
            "publishing_authority_granted": False,
            "execution_authority_granted": False,
        },
    }
