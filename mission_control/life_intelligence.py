"""Life Intelligence: real facts, real skills and real-life education.

Life Intelligence is a cross-system SMI capability used by Community Power
Education.  It separates Adult learning from Youth Club, covers practical life,
all trade families and professions, and never misrepresents OAP learning as a
regulated qualification.
"""

from __future__ import annotations

from typing import Any

LIFE_INTELLIGENCE_SECTIONS: tuple[dict[str, str], ...] = (
    {"id": "adult", "name": "Adult Life", "purpose": "Independent living, work, responsibilities and practical adult knowledge."},
    {"id": "trades", "name": "All Trades & Practical Skills", "purpose": "Discover, learn and progress through traditional, technical, creative and emerging trades."},
    {"id": "professions", "name": "Professions & Careers", "purpose": "Explain routes into regulated and professional careers without bypassing real qualifications."},
    {"id": "money", "name": "Money & Financial Life", "purpose": "Budgeting, bills, credit, debt, saving, tax basics and financial decision literacy."},
    {"id": "business", "name": "Business & Entrepreneurship", "purpose": "Starting, pricing, operating and growing a legitimate business."},
    {"id": "law", "name": "Everyday Law & Rights", "purpose": "Practical rights, contracts, consumer issues and routes to qualified legal help."},
    {"id": "wellbeing", "name": "Wellbeing", "purpose": "Healthy routines, relationships, communication and routes to appropriate support."},
    {"id": "digital", "name": "Digital, AI & Technology", "purpose": "Digital literacy, coding, AI literacy, privacy, cybersecurity and modern tools."},
    {"id": "home", "name": "Home & Independent Living", "purpose": "Renting, utilities, cooking, cleaning, repairs, first aid and household planning."},
    {"id": "parenting", "name": "Family & Caring", "purpose": "Parenting knowledge, caring responsibilities and family-life planning."},
    {"id": "earth_culture", "name": "Earth, Culture & Society", "purpose": "Geography, cultures, history, nature, civic life and real-world context."},
    {"id": "youth", "name": "Youth Club Education", "purpose": "Age-appropriate practical learning, creativity, careers and safe skill discovery."},
    {"id": "opportunity", "name": "Opportunity Pathways", "purpose": "Connect learning to mentoring, apprenticeships, The Link, Market and legitimate work."},
)

TRADE_FAMILIES: tuple[dict[str, object], ...] = (
    {"id": "construction", "name": "Construction & Building", "examples": ("bricklaying", "plastering", "roofing", "tiling", "flooring", "glazing", "scaffolding", "groundworks")},
    {"id": "carpentry", "name": "Carpentry, Joinery & Furniture", "examples": ("carpentry", "joinery", "cabinet making", "furniture making", "wood finishing")},
    {"id": "electrical", "name": "Electrical & Electronics", "examples": ("electrical installation", "electronics", "device repair", "controls", "smart-home installation")},
    {"id": "plumbing_hvac", "name": "Plumbing, Heating, Cooling & Gas", "examples": ("plumbing", "heating", "HVAC", "refrigeration", "gas engineering")},
    {"id": "fabrication", "name": "Welding, Metalwork & Fabrication", "examples": ("welding", "fabrication", "sheet metal", "machining", "blacksmithing")},
    {"id": "automotive", "name": "Automotive & Vehicle Trades", "examples": ("mechanics", "auto electrics", "bodywork", "tyres", "motorcycle repair", "bicycle repair")},
    {"id": "plant", "name": "Plant, Machinery & Industrial Maintenance", "examples": ("plant maintenance", "industrial maintenance", "machinery operation", "mechatronics")},
    {"id": "logistics", "name": "Logistics, Warehousing & Driving", "examples": ("warehousing", "courier work", "delivery", "fleet operations", "professional driving")},
    {"id": "agriculture", "name": "Agriculture, Land & Food Production", "examples": ("farming", "horticulture", "forestry", "fishing", "landscaping", "food production")},
    {"id": "food", "name": "Food, Catering & Hospitality", "examples": ("cooking", "catering", "baking", "butchery", "hospitality", "food service")},
    {"id": "fashion_beauty", "name": "Fashion, Textiles, Hair & Beauty", "examples": ("tailoring", "sewing", "fashion production", "barbering", "hairdressing", "beauty")},
    {"id": "creative", "name": "Creative & Production Trades", "examples": ("photography", "videography", "audio engineering", "music production", "printing", "signage", "stage production")},
    {"id": "jewellery_craft", "name": "Jewellery, Craft & Making", "examples": ("jewellery making", "leatherwork", "ceramics", "upholstery", "craft production")},
    {"id": "facilities", "name": "Facilities, Cleaning & Property Services", "examples": ("cleaning", "facilities management", "maintenance", "pest control", "property services")},
    {"id": "care", "name": "Care & Support Work", "examples": ("care work", "childcare", "support work", "community care")},
    {"id": "security", "name": "Security & Safety Services", "examples": ("security", "fire safety", "event safety", "site safety")},
    {"id": "digital", "name": "Digital & Computing Trades", "examples": ("web development", "software", "networking", "cybersecurity", "IT support", "data skills")},
    {"id": "future", "name": "Robotics, Drones & Digital Fabrication", "examples": ("robotics", "drones", "3D printing", "CNC", "automation", "digital fabrication")},
    {"id": "green", "name": "Green & Energy Trades", "examples": ("solar", "heat pumps", "insulation", "EV charging", "energy efficiency", "water management")},
    {"id": "marine_air", "name": "Marine, Rail & Aviation Technical Trades", "examples": ("marine engineering", "rail maintenance", "aircraft maintenance", "avionics")},
)

ACADEMY_NAME = "OAP Academy"

LEARNING_PATH: tuple[str, ...] = (
    "Discover",
    "Understand",
    "Practise",
    "Apply",
    "Build",
    "Master",
    "Teach",
)

ACADEMY_ROOMS: tuple[dict[str, str], ...] = (
    {"id":"life","name":"Life Lab","purpose":"Money, housing, food, paperwork and independent living."},
    {"id":"trade","name":"Trade Lab","purpose":"Trades, tools, repair, construction and practical making."},
    {"id":"digital","name":"Digital Lab","purpose":"Computing, AI, cybersecurity, coding and digital creation."},
    {"id":"world","name":"World Room","purpose":"Geography, cultures, travel, languages and global systems."},
    {"id":"rights","name":"Rights Room","purpose":"Rights, law, government, justice and anti-exploitation."},
    {"id":"health","name":"Health Room","purpose":"Body, wellbeing, safety, first aid and health literacy."},
    {"id":"business","name":"Business Room","purpose":"Work, careers, entrepreneurship, sales, finance and economics."},
    {"id":"creative","name":"Creative Studio","purpose":"Music, film, design, writing, fashion and photography."},
    {"id":"nature","name":"Nature Room","purpose":"Animals, plants, farming, environment, land and survival."},
    {"id":"science","name":"Science Lab","purpose":"Physics, chemistry, biology, engineering, space and invention."},
    {"id":"communication","name":"Communication Room","purpose":"Languages, writing, speaking, relationships and negotiation."},
    {"id":"challenge","name":"Challenge Room","purpose":"Cross-subject missions, projects, teamwork and problem-solving."},
)

CLASS_MODES = ("Together", "By Age", "By Level", "Adaptive")

UNIVERSAL_ADAPTATION = (
    "age_stage",
    "culture",
    "language",
    "location",
    "ability_accessibility",
    "belief_worldview",
    "learning_mode",
    "economic_context",
    "experience_level",
    "safety_level",
)

GOVERNANCE: dict[str, object] = {
    "community_power_owner": True,
    "adult_youth_separated": True,
    "youth_safeguarding_required": True,
    "regulated_work_requires_real_qualification": True,
    "oap_course_equals_professional_licence": False,
    "unsafe_unsupervised_practice_allowed": False,
    "human_authority_final": True,
}


def validate_life_intelligence() -> dict[str, Any]:
    section_ids = [item["id"] for item in LIFE_INTELLIGENCE_SECTIONS]
    trade_ids = [str(item["id"]) for item in TRADE_FAMILIES]
    errors: list[str] = []
    if len(section_ids) != len(set(section_ids)):
        errors.append("Duplicate Life Intelligence sections")
    if len(trade_ids) != len(set(trade_ids)):
        errors.append("Duplicate trade families")
    if "adult" not in section_ids or "youth" not in section_ids:
        errors.append("Adult and Youth Club education must remain distinct")
    if not GOVERNANCE["regulated_work_requires_real_qualification"]:
        errors.append("Regulated work must retain real qualification boundaries")
    if GOVERNANCE["oap_course_equals_professional_licence"]:
        errors.append("OAP learning must not impersonate professional licensing")
    if GOVERNANCE["unsafe_unsupervised_practice_allowed"]:
        errors.append("Unsafe unsupervised practical work must remain blocked")
    if len(LEARNING_PATH) != 7 or LEARNING_PATH[-1] != "Teach":
        errors.append("Academy learning path must keep seven stages ending in Teach")
    if len(ACADEMY_ROOMS) != 12 or len({item["id"] for item in ACADEMY_ROOMS}) != 12:
        errors.append("Academy must keep twelve unique major learning rooms")
    if CLASS_MODES != ("Together", "By Age", "By Level", "Adaptive"):
        errors.append("Academy class modes drifted")
    return {
        "passed": not errors,
        "errors": errors,
        "sections": len(section_ids),
        "trade_families": len(trade_ids),
        "academy_rooms": len(ACADEMY_ROOMS),
        "learning_stages": len(LEARNING_PATH),
    }


def life_intelligence_status() -> dict[str, Any]:
    validation = validate_life_intelligence()
    return {
        "name": "Life Intelligence",
        "academy_name": ACADEMY_NAME,
        "tagline": "Real facts. Real skills. Real life.",
        "kind": "cross_system_capability",
        "architecture_passed": validation["passed"],
        "sections": tuple(dict(item) for item in LIFE_INTELLIGENCE_SECTIONS),
        "trade_families": tuple(dict(item) for item in TRADE_FAMILIES),
        "learning_path": LEARNING_PATH,
        "academy_rooms": tuple(dict(item) for item in ACADEMY_ROOMS),
        "class_modes": CLASS_MODES,
        "default_class_mode": "Adaptive",
        "universal_adaptation": UNIVERSAL_ADAPTATION,
        "library_relationship": "Library=Know; Academy=Learn & Do",
        "youth_club_relationship": "age-safe doorway into the same Academy",
        "governance": dict(GOVERNANCE),
        "community_power_connection": "education",
        "earth_intelligence_connection": "real_place_and_culture_context",
        "language_intelligence_connection": "learning_and_work_language",
        "movement_intelligence_connection": "travel_work_and_logistics_context",
        "credential_runtime_ready": False,
        "apprenticeship_runtime_ready": False,
        "market_opportunity_runtime_ready": False,
        "human_authority_final": True,
        "can_execute": False,
        "truth_boundary": (
            "Life Intelligence defines the complete practical learning architecture. "
            "Real qualifications, supervised hazardous practice, apprenticeships and paid "
            "opportunities remain dependent on certified external or OAP-governed evidence."
        ),
    }
