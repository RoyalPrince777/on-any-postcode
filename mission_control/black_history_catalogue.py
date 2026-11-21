"""Review-only Black History catalogue; no automatic publication or geographic claims."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

_ENTRIES: tuple[dict[str, Any], ...] = (
    {
        "entry_id": "bh-cape-uprising-1808",
        "title": "The Cape uprising against slavery (1808)",
        "period": "October 1808",
        "date_precision": "month",
        "date_uncertainty": "Sources differ on whether events began 25 or 27 October.",
        "place": "Cape Colony (present-day South Africa)",
        "coordinates": None,
        "claim_status": "disputed",
        "summary": (
            "Enslaved people and Khoekhoe labourers organised a march towards "
            "Cape Town in October 1808. Colonial forces stopped it near Salt River."
        ),
        "sources": (
            {
                "publisher": "South African History Online",
                "url": "https://sahistory.org.za/article/louis-van-mauritius-and-slave-revolt-1808",
            },
            {
                "publisher": "Cape Town Museum",
                "url": "https://www.capetownmuseum.org.za/they-built-this-city/louis-of-mauritius",
            },
        ),
        "rights": "Links only; no reproduced source images or full articles.",
        "review_status": "editorial_hold",
    },
)


def review_entries() -> list[dict[str, Any]]:
    """Return independent copies; never silently promote drafts to publication."""
    return deepcopy(list(_ENTRIES))


def catalogue_status() -> dict[str, Any]:
    return {
        "component": "OAP Black History Intelligence / Chronicle",
        "publication_enabled": False,
        "review_only": True,
        "entries": review_entries(),
    }
