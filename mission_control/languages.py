"""Local-first public language learning for OAP World.

The first release is deliberately static and read-only. It does not create
learner profiles, retain progress, record speech, translate conversations or
call a third-party language provider. Phase two may connect reviewed learning
tools to Link Up, but only after separate privacy, safeguarding and accuracy
approval.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any
from urllib.parse import urlsplit


CONTINENTS: tuple[dict[str, Any], ...] = (
    {
        "id": "africa",
        "name": "Africa",
        "icon": "🌍",
        "description": "Start with Akan roots and explore living languages across Africa.",
        "languages": (
            "Akan (Twi)",
            "Swahili",
            "Yoruba",
            "Zulu",
            "Amharic",
            "Arabic",
        ),
        "featured_lesson_id": "africa-akan-twi",
    },
    {
        "id": "asia",
        "name": "Asia",
        "icon": "🌏",
        "description": "Explore scripts, sounds and everyday respect across Asia.",
        "languages": (
            "Hindi",
            "Mandarin Chinese",
            "Bengali",
            "Japanese",
            "Korean",
            "Urdu",
            "Tamil",
        ),
        "featured_lesson_id": "asia-japanese",
    },
    {
        "id": "europe",
        "name": "Europe",
        "icon": "🌍",
        "description": "Build practical conversation across European language families.",
        "languages": (
            "English",
            "Spanish",
            "French",
            "Portuguese",
            "German",
            "Italian",
            "Polish",
        ),
        "featured_lesson_id": "europe-spanish",
    },
    {
        "id": "north-america",
        "name": "North America",
        "icon": "🌎",
        "description": "Learn across Caribbean, Indigenous and continental communities.",
        "languages": (
            "English",
            "Spanish",
            "French",
            "Haitian Creole",
            "Nahuatl",
            "Inuktitut",
        ),
        "featured_lesson_id": "north-america-haitian-creole",
    },
    {
        "id": "south-america",
        "name": "South America",
        "icon": "🌎",
        "description": "Connect with major and Indigenous languages across South America.",
        "languages": (
            "Spanish",
            "Portuguese",
            "Quechua",
            "Guaraní",
            "Aymara",
        ),
        "featured_lesson_id": "south-america-portuguese",
    },
    {
        "id": "oceania",
        "name": "Oceania",
        "icon": "🌏",
        "description": "Respect Pacific language revival, identity and community knowledge.",
        "languages": (
            "Māori",
            "Samoan",
            "Tongan",
            "Fijian",
            "Tok Pisin",
            "Bislama",
        ),
        "featured_lesson_id": "oceania-maori",
    },
    {
        "id": "antarctica",
        "name": "Antarctica",
        "icon": "🧊",
        "description": (
            "Antarctica has no permanent resident language community; this path "
            "focuses on clear international research communication."
        ),
        "languages": (
            "International field English",
            "Spanish",
            "French",
            "Russian",
        ),
        "featured_lesson_id": "antarctica-field-english",
    },
)


STARTER_LESSONS: tuple[dict[str, Any], ...] = (
    {
        "id": "africa-akan-twi",
        "continent_id": "africa",
        "language": "Akan (Twi)",
        "lang": "tw",
        "native_name": "Twi",
        "title": "Greetings and identity",
        "intro": "Begin with respectful everyday phrases rooted in Akan community life.",
        "phrases": (
            {"phrase": "Maakye", "meaning": "Good morning"},
            {"phrase": "Medaase", "meaning": "Thank you"},
            {"phrase": "Me din de …", "meaning": "My name is …"},
        ),
    },
    {
        "id": "asia-japanese",
        "continent_id": "asia",
        "language": "Japanese",
        "lang": "ja",
        "native_name": "日本語",
        "title": "Polite first connections",
        "intro": "Practise a greeting, gratitude and a simple learning statement.",
        "phrases": (
            {"phrase": "こんにちは", "romanisation": "Konnichiwa", "meaning": "Hello"},
            {
                "phrase": "ありがとうございます",
                "romanisation": "Arigatō gozaimasu",
                "meaning": "Thank you",
            },
            {
                "phrase": "日本語を勉強しています",
                "romanisation": "Nihongo o benkyō shiteimasu",
                "meaning": "I am studying Japanese",
            },
        ),
    },
    {
        "id": "europe-spanish",
        "continent_id": "europe",
        "language": "Spanish",
        "lang": "es",
        "native_name": "Español",
        "title": "Start a conversation",
        "intro": "Use three clear phrases for greeting, gratitude and learning.",
        "phrases": (
            {"phrase": "Hola", "meaning": "Hello"},
            {"phrase": "Gracias", "meaning": "Thank you"},
            {"phrase": "Estoy aprendiendo español", "meaning": "I am learning Spanish"},
        ),
    },
    {
        "id": "north-america-haitian-creole",
        "continent_id": "north-america",
        "language": "Haitian Creole",
        "lang": "ht",
        "native_name": "Kreyòl ayisyen",
        "title": "Everyday connection",
        "intro": "Begin with widely used Haitian Creole phrases for a friendly exchange.",
        "phrases": (
            {"phrase": "Bonjou", "meaning": "Hello / good morning"},
            {"phrase": "Mèsi", "meaning": "Thank you"},
            {"phrase": "M ap aprann kreyòl", "meaning": "I am learning Creole"},
        ),
    },
    {
        "id": "south-america-portuguese",
        "continent_id": "south-america",
        "language": "Portuguese",
        "lang": "pt-BR",
        "native_name": "Português",
        "title": "A first Brazilian Portuguese exchange",
        "intro": "Practise a greeting, gratitude and a learning statement.",
        "phrases": (
            {"phrase": "Olá", "meaning": "Hello"},
            {"phrase": "Obrigado / Obrigada", "meaning": "Thank you"},
            {
                "phrase": "Estou aprendendo português",
                "meaning": "I am learning Portuguese",
            },
        ),
    },
    {
        "id": "oceania-maori",
        "continent_id": "oceania",
        "language": "Māori",
        "lang": "mi",
        "native_name": "Te reo Māori",
        "title": "Language, respect and connection",
        "intro": "Begin with phrases that recognise people and the living language.",
        "phrases": (
            {"phrase": "Kia ora", "meaning": "Hello / be well"},
            {"phrase": "Ngā mihi", "meaning": "Thanks / acknowledgements"},
            {
                "phrase": "Kei te ako au i te reo Māori",
                "meaning": "I am learning the Māori language",
            },
        ),
    },
    {
        "id": "antarctica-field-english",
        "continent_id": "antarctica",
        "language": "International field English",
        "lang": "en",
        "native_name": "Clear field communication",
        "title": "Safety-first research communication",
        "intro": (
            "Use short, unambiguous English phrases in an international field setting. "
            "This is not presented as a native Antarctic language."
        ),
        "phrases": (
            {"phrase": "Hello", "meaning": "Open communication clearly"},
            {"phrase": "Thank you", "meaning": "Acknowledge help"},
            {"phrase": "Safety check complete", "meaning": "Confirm a bounded safety step"},
        ),
    },
)


CONJUGATION_DRILLS: tuple[dict[str, Any], ...] = (
    {
        "id": "english-learn",
        "language": "English",
        "verb": "to learn",
        "tense": "Simple present",
        "forms": (
            ("I", "learn"),
            ("you", "learn"),
            ("he / she / it", "learns"),
            ("we", "learn"),
            ("you all", "learn"),
            ("they", "learn"),
        ),
    },
    {
        "id": "spanish-aprender",
        "language": "Spanish",
        "verb": "aprender",
        "tense": "Present indicative",
        "forms": (
            ("yo", "aprendo"),
            ("tú", "aprendes"),
            ("él / ella", "aprende"),
            ("nosotros / nosotras", "aprendemos"),
            ("ustedes", "aprenden"),
            ("ellos / ellas", "aprenden"),
        ),
    },
    {
        "id": "french-apprendre",
        "language": "French",
        "verb": "apprendre",
        "tense": "Présent",
        "forms": (
            ("je", "j’apprends"),
            ("tu", "apprends"),
            ("il / elle", "apprend"),
            ("nous", "apprenons"),
            ("vous", "apprenez"),
            ("ils / elles", "apprennent"),
        ),
    },
    {
        "id": "portuguese-aprender",
        "language": "Portuguese",
        "verb": "aprender",
        "tense": "Presente do indicativo",
        "forms": (
            ("eu", "aprendo"),
            ("tu", "aprendes"),
            ("ele / ela", "aprende"),
            ("nós", "aprendemos"),
            ("vocês", "aprendem"),
            ("eles / elas", "aprendem"),
        ),
    },
)


SOUTH_LONDON_RESOURCES: tuple[dict[str, str], ...] = (
    {
        "borough": "Lewisham",
        "name": "Adult Learning Lewisham",
        "purpose": "Council language and ESOL courses, including beginner options.",
        "url": "https://lewisham.gov.uk/myservices/education/adult",
    },
    {
        "borough": "Lambeth",
        "name": "Lambeth ESOL support",
        "purpose": "Council directory for English classes and community support.",
        "url": "https://www.lambeth.gov.uk/libraries-archives/libraries-opening-hours/english-speakers-other-languages-esol-support",
    },
    {
        "borough": "Southwark",
        "name": "Learning in libraries",
        "purpose": "Library ESOL classes and conversation practice across Southwark.",
        "url": "https://www.southwark.gov.uk/culture-and-sport/libraries/library-services/learning-libraries",
    },
    {
        "borough": "Croydon",
        "name": "Croydon adult education courses",
        "purpose": "Council adult learning across languages, ESOL and bilingual skills.",
        "url": "https://www.croydon.gov.uk/schools-and-education/university-adult-and-further-education/adult-education-courses",
    },
)


PUBLIC_BOUNDARY: dict[str, bool] = {
    "stores_progress": False,
    "records_audio": False,
    "uses_precise_location": False,
    "calls_translation_provider": False,
    "connects_to_link_up": False,
}

RESOURCE_REVIEWED_ON = "2026-08-28"
EXPECTED_CONTINENT_IDS = {
    "africa",
    "asia",
    "europe",
    "north-america",
    "south-america",
    "oceania",
    "antarctica",
}
ALLOWED_RESOURCE_HOSTS = {
    "lewisham.gov.uk",
    "www.lambeth.gov.uk",
    "www.southwark.gov.uk",
    "www.croydon.gov.uk",
}


def validate_language_hub(
    continents: Iterable[Mapping[str, Any]] = CONTINENTS,
    lessons: Iterable[Mapping[str, Any]] = STARTER_LESSONS,
    drills: Iterable[Mapping[str, Any]] = CONJUGATION_DRILLS,
    resources: Iterable[Mapping[str, str]] = SOUTH_LONDON_RESOURCES,
) -> dict[str, Any]:
    """Reject incomplete, duplicated or externally unsafe public learning data."""

    continent_items = tuple(continents)
    lesson_items = tuple(lessons)
    drill_items = tuple(drills)
    resource_items = tuple(resources)
    continent_ids = [str(item.get("id", "")) for item in continent_items]
    lesson_ids = [str(item.get("id", "")) for item in lesson_items]
    drill_ids = [str(item.get("id", "")) for item in drill_items]
    errors: list[str] = []

    if set(continent_ids) != EXPECTED_CONTINENT_IDS or len(continent_ids) != 7:
        errors.append("The language selector must contain exactly seven continents")
    for label, values in (
        ("continent", continent_ids),
        ("lesson", lesson_ids),
        ("drill", drill_ids),
    ):
        if len(values) != len(set(values)):
            errors.append(f"Duplicate {label} IDs")

    lesson_by_id = {str(item.get("id", "")): item for item in lesson_items}
    lesson_continent_ids = [
        str(item.get("continent_id", "")) for item in lesson_items
    ]
    lesson_scope_errors = (
        len(lesson_items) != 7,
        set(lesson_continent_ids) != EXPECTED_CONTINENT_IDS,
        len(lesson_continent_ids) != len(set(lesson_continent_ids)),
    )
    if any(lesson_scope_errors):
        errors.append("Every continent must have exactly one starter lesson")
    for continent in continent_items:
        featured_id = str(continent.get("featured_lesson_id", ""))
        featured = lesson_by_id.get(featured_id)
        if featured is None or featured.get("continent_id") != continent.get("id"):
            errors.append(f"Missing featured lesson for {continent.get('id')}")
        if not tuple(continent.get("languages", ())):
            errors.append(f"Missing language catalogue for {continent.get('id')}")

    for lesson in lesson_items:
        if len(tuple(lesson.get("phrases", ()))) != 3:
            errors.append(f"Starter lesson must contain three phrases: {lesson.get('id')}")
        if not str(lesson.get("lang", "")).strip():
            errors.append(f"Starter lesson requires a language code: {lesson.get('id')}")

    if len(drill_items) != 4:
        errors.append("The first release must contain four conjugation drills")
    for drill in drill_items:
        if len(tuple(drill.get("forms", ()))) != 6:
            errors.append(f"Conjugation drill must contain six forms: {drill.get('id')}")

    if len(resource_items) != 4:
        errors.append("The first release must contain four South London resources")

    for resource in resource_items:
        parsed = urlsplit(str(resource.get("url", "")))
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_RESOURCE_HOSTS:
            errors.append(f"Unapproved South London resource: {resource.get('name')}")

    if any(PUBLIC_BOUNDARY.values()):
        errors.append("The first language release must remain local-first and read-only")

    return {
        "passed": not errors,
        "errors": errors,
        "checks": {
            "continents": len(continent_items),
            "starter_lessons": len(lesson_items),
            "conjugation_drills": len(drill_items),
            "south_london_resources": len(resource_items),
            "external_runtime_calls": 0,
        },
    }


def _copy_phrase(phrase: Mapping[str, str]) -> dict[str, str]:
    return {key: str(value) for key, value in phrase.items()}


def _copy_lesson(lesson: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": str(lesson["id"]),
        "continent_id": str(lesson["continent_id"]),
        "language": str(lesson["language"]),
        "lang": str(lesson["lang"]),
        "native_name": str(lesson["native_name"]),
        "title": str(lesson["title"]),
        "intro": str(lesson["intro"]),
        "phrases": tuple(_copy_phrase(item) for item in lesson["phrases"]),
    }


def get_public_language_hub(
    continent_id: object = None,
    lesson_id: object = None,
    drill_id: object = None,
) -> dict[str, Any]:
    """Return a bounded public projection selected only from canonical IDs."""

    continents = {item["id"]: item for item in CONTINENTS}
    lessons = {item["id"]: item for item in STARTER_LESSONS}
    drills = {item["id"]: item for item in CONJUGATION_DRILLS}

    selected_lesson = lessons.get(str(lesson_id or ""))
    selected_continent = continents.get(str(continent_id or ""))
    if selected_lesson is not None:
        selected_continent = continents[selected_lesson["continent_id"]]
    if selected_continent is None:
        selected_continent = continents["africa"]
    if selected_lesson is None or selected_lesson["continent_id"] != selected_continent["id"]:
        selected_lesson = lessons[selected_continent["featured_lesson_id"]]

    selected_drill = drills.get(str(drill_id or ""), drills["english-learn"])

    return {
        "continents": tuple(
            {
                "id": str(item["id"]),
                "name": str(item["name"]),
                "icon": str(item["icon"]),
                "description": str(item["description"]),
                "languages": tuple(str(value) for value in item["languages"]),
                "featured_lesson_id": str(item["featured_lesson_id"]),
            }
            for item in CONTINENTS
        ),
        "lessons": tuple(_copy_lesson(item) for item in STARTER_LESSONS),
        "selected_continent": {
            "id": str(selected_continent["id"]),
            "name": str(selected_continent["name"]),
            "icon": str(selected_continent["icon"]),
            "description": str(selected_continent["description"]),
            "languages": tuple(str(value) for value in selected_continent["languages"]),
        },
        "selected_lesson": _copy_lesson(selected_lesson),
        "drills": tuple(
            {
                "id": str(item["id"]),
                "language": str(item["language"]),
                "verb": str(item["verb"]),
            }
            for item in CONJUGATION_DRILLS
        ),
        "selected_drill": {
            "id": str(selected_drill["id"]),
            "language": str(selected_drill["language"]),
            "verb": str(selected_drill["verb"]),
            "tense": str(selected_drill["tense"]),
            "forms": tuple(
                {"subject": str(subject), "form": str(form)}
                for subject, form in selected_drill["forms"]
            ),
        },
        "resources": tuple(dict(item) for item in SOUTH_LONDON_RESOURCES),
        "resources_reviewed_on": RESOURCE_REVIEWED_ON,
        "phase_two_active": False,
    }
