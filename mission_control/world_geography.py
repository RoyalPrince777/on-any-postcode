"""Bounded OAP geography reference for public Earth-level grouping.

Country labels remain owned by their upstream source. This module only maps
known country/territory names into OAP's seven canonical continent/region
buckets so public views can group source-backed records without geocoding,
precise location lookup, or network calls. Unknown labels fail closed as
unclassified.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

OAP_CONTINENT_ORDER: tuple[str, ...] = (
    "Africa",
    "Europe",
    "Asia",
    "North America",
    "South America",
    "Caribbean",
    "Oceania",
)

_COUNTRIES_BY_CONTINENT: dict[str, tuple[str, ...]] = {
    "Africa": (
        "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi",
        "Cabo Verde", "Cape Verde", "Cameroon", "Central African Republic", "Chad",
        "Comoros", "Congo", "Republic of the Congo", "Democratic Republic of the Congo",
        "DR Congo", "DRC", "Cote d'Ivoire", "Ivory Coast", "Djibouti", "Egypt",
        "Equatorial Guinea", "Eritrea", "Eswatini", "Swaziland", "Ethiopia", "Gabon",
        "Gambia", "The Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Kenya", "Lesotho",
        "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania", "Mauritius",
        "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Rwanda",
        "Sao Tome and Principe", "Senegal", "Seychelles", "Sierra Leone", "Somalia",
        "South Africa", "South Sudan", "Sudan", "Tanzania", "United Republic of Tanzania",
        "Togo", "Tunisia", "Uganda", "Zambia", "Zimbabwe", "Western Sahara", "Mayotte",
        "Reunion",
    ),
    "Europe": (
        "Albania", "Andorra", "Austria", "Belarus", "Belgium", "Bosnia and Herzegovina",
        "Bosnia", "Bulgaria", "Croatia", "Czechia", "Czech Republic", "Denmark", "Estonia",
        "Finland", "France", "Germany", "Greece", "Holy See", "Vatican City", "Hungary",
        "Iceland", "Ireland", "Italy", "Latvia", "Liechtenstein", "Lithuania", "Luxembourg",
        "Malta", "Moldova", "Republic of Moldova", "Monaco", "Montenegro", "Netherlands",
        "North Macedonia", "Macedonia", "Norway", "Poland", "Portugal", "Romania", "Russia",
        "Russian Federation", "San Marino", "Serbia", "Slovakia", "Slovenia", "Spain", "Sweden",
        "Switzerland", "Ukraine", "United Kingdom", "UK", "England", "Scotland", "Wales",
        "Northern Ireland", "Gibraltar", "Isle of Man", "Jersey", "Guernsey", "Faroe Islands",
        "Kosovo",
    ),
    "Asia": (
        "Afghanistan", "Armenia", "Azerbaijan", "Bahrain", "Bangladesh", "Bhutan", "Brunei",
        "Brunei Darussalam", "Cambodia", "China", "Cyprus", "Georgia", "India", "Indonesia",
        "Iran", "Islamic Republic of Iran", "Iraq", "Israel", "Japan", "Jordan", "Kazakhstan",
        "Kuwait", "Kyrgyzstan", "Laos", "Lao People's Democratic Republic", "Lebanon", "Malaysia",
        "Maldives", "Mongolia", "Myanmar", "Burma", "Nepal", "North Korea",
        "Democratic People's Republic of Korea", "South Korea", "Republic of Korea", "Oman",
        "Pakistan", "Palestine", "State of Palestine", "Philippines", "Qatar", "Saudi Arabia",
        "Singapore", "Sri Lanka", "Syria", "Syrian Arab Republic", "Taiwan", "Tajikistan",
        "Thailand", "Timor-Leste", "East Timor", "Turkiye", "Turkey", "Turkmenistan",
        "United Arab Emirates", "UAE", "Uzbekistan", "Vietnam", "Viet Nam", "Yemen",
        "Hong Kong", "Macao", "Macau",
    ),
    "North America": (
        "Canada", "United States", "United States of America", "USA", "US", "Mexico", "Belize",
        "Costa Rica", "El Salvador", "Guatemala", "Honduras", "Nicaragua", "Panama", "Greenland",
        "Bermuda", "Saint Pierre and Miquelon",
    ),
    "South America": (
        "Argentina", "Bolivia", "Bolivia Plurinational State of", "Brazil", "Chile", "Colombia",
        "Ecuador", "Guyana", "Paraguay", "Peru", "Suriname", "Uruguay", "Venezuela",
        "Venezuela Bolivarian Republic of", "Falkland Islands", "French Guiana",
    ),
    "Caribbean": (
        "Antigua and Barbuda", "Bahamas", "Barbados", "Cuba", "Dominica", "Dominican Republic",
        "Grenada", "Haiti", "Jamaica", "Saint Kitts and Nevis", "Saint Lucia",
        "Saint Vincent and the Grenadines", "Trinidad and Tobago", "Aruba", "Bonaire",
        "Sint Eustatius and Saba", "Curacao", "Guadeloupe", "Martinique", "Montserrat",
        "Puerto Rico", "Saint Barthelemy", "Saint Martin", "Sint Maarten", "Turks and Caicos Islands",
        "British Virgin Islands", "Virgin Islands British", "US Virgin Islands", "Virgin Islands US",
        "Cayman Islands", "Anguilla",
    ),
    "Oceania": (
        "Australia", "Fiji", "Kiribati", "Marshall Islands", "Micronesia",
        "Federated States of Micronesia", "Nauru", "New Zealand", "Palau", "Papua New Guinea",
        "Samoa", "Solomon Islands", "Tonga", "Tuvalu", "Vanuatu", "American Samoa",
        "Cook Islands", "French Polynesia", "Guam", "New Caledonia", "Niue",
        "Northern Mariana Islands", "Tokelau", "Wallis and Futuna",
    ),
}

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _normalise_country(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    ascii_text = "".join(char for char in text if not unicodedata.combining(char))
    ascii_text = ascii_text.casefold().replace("&", " and ")
    return " ".join(_NON_ALNUM.sub(" ", ascii_text).split())


_COUNTRY_TO_CONTINENT = {
    _normalise_country(country): continent
    for continent, countries in _COUNTRIES_BY_CONTINENT.items()
    for country in countries
}


def continent_for_country(country: object) -> str | None:
    """Return an OAP continent/region for a known source country label."""

    key = _normalise_country(country)
    return _COUNTRY_TO_CONTINENT.get(key) if key else None


def continents_for_countries(countries: Iterable[object]) -> tuple[str, ...]:
    """Return unique mapped continents in canonical OAP order."""

    found = {continent_for_country(country) for country in countries}
    return tuple(continent for continent in OAP_CONTINENT_ORDER if continent in found)


def reference_status() -> dict[str, object]:
    """Return redacted metadata; no location or source record is read here."""

    return {
        "continent_order": OAP_CONTINENT_ORDER,
        "known_country_aliases": len(_COUNTRY_TO_CONTINENT),
        "network_lookup": False,
        "precise_location": False,
        "unknown_labels_fail_closed": True,
    }
