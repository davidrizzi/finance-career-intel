"""City / country normalisation and geographical priority."""
from __future__ import annotations

import re

from .util import norm_text

# canonical English name -> known spellings (Italian, German, French, local)
CITY_ALIASES = {
    "Lugano": ["lugano"],
    "Zurich": ["zurich", "zurigo", "zuerich", "zurich city", "zürich"],
    "Zug": ["zug", "zugo", "baar", "cham zg"],
    "Geneva": ["geneva", "ginevra", "geneve", "genf", "carouge", "lancy"],
    "Basel": ["basel", "basilea", "bale"],
    "Bern": ["bern", "berna", "berne"],
    "Lausanne": ["lausanne", "losanna"],
    "Chiasso": ["chiasso"],
    "Bellinzona": ["bellinzona"],
    "Mendrisio": ["mendrisio"],
    "St. Gallen": ["st gallen", "san gallo", "saint gallen", "sankt gallen"],
    "Pfaeffikon": ["pfaffikon", "pfaeffikon", "freienbach"],
    "Milan": ["milan", "milano", "mailand"],
    "Rome": ["rome", "roma"],
    "Turin": ["turin", "torino"],
    "London": ["london", "londra", "londres", "city of london", "canary wharf", "mayfair"],
    "Luxembourg": ["luxembourg", "lussemburgo", "luxemburg", "luxembourg city", "luxembourg ville",
                   "senningerberg", "bertrange", "strassen", "munsbach", "kirchberg", "leudelange", "howald"],
    "Sydney": ["sydney", "north sydney", "barangaroo"],
    "Melbourne": ["melbourne", "docklands"],
    "Perth": ["perth"],
    "Dubai": ["dubai", "difc"],
    "Abu Dhabi": ["abu dhabi", "adgm"],
    "Frankfurt": ["frankfurt", "frankfurt am main", "francoforte"],
    "Paris": ["paris", "parigi"],
    "New York": ["new york", "nyc", "new york city", "manhattan"],
    "Hong Kong": ["hong kong"],
    "Singapore": ["singapore", "singapur"],
    "Madrid": ["madrid"],
    "Amsterdam": ["amsterdam"],
    "Munich": ["munich", "munchen", "muenchen", "monaco di baviera"],
    "Dublin": ["dublin", "dublino"],
    "Edinburgh": ["edinburgh"],
    "Vaduz": ["vaduz"],
    "Monaco": ["monaco", "monte carlo"],
    "Brisbane": ["brisbane"],
}

CITY_COUNTRY = {
    "Lugano": "Switzerland", "Zurich": "Switzerland", "Zug": "Switzerland", "Geneva": "Switzerland",
    "Basel": "Switzerland", "Bern": "Switzerland", "Lausanne": "Switzerland", "Chiasso": "Switzerland",
    "Bellinzona": "Switzerland", "Mendrisio": "Switzerland", "St. Gallen": "Switzerland",
    "Pfaeffikon": "Switzerland", "Milan": "Italy", "Rome": "Italy", "Turin": "Italy",
    "London": "United Kingdom", "Edinburgh": "United Kingdom", "Luxembourg": "Luxembourg",
    "Sydney": "Australia", "Melbourne": "Australia", "Perth": "Australia", "Brisbane": "Australia",
    "Dubai": "United Arab Emirates", "Abu Dhabi": "United Arab Emirates", "Frankfurt": "Germany",
    "Munich": "Germany", "Paris": "France", "New York": "United States", "Hong Kong": "Hong Kong",
    "Singapore": "Singapore", "Madrid": "Spain", "Amsterdam": "Netherlands", "Dublin": "Ireland",
    "Vaduz": "Liechtenstein", "Monaco": "Monaco",
}

COUNTRY_ALIASES = {
    "Switzerland": ["switzerland", "svizzera", "schweiz", "suisse", "ch", "che", "swiss"],
    "Italy": ["italy", "italia", "italien", "italie", "it", "ita"],
    "United Kingdom": ["united kingdom", "regno unito", "uk", "gb", "gbr", "great britain", "england",
                       "royaume uni", "vereinigtes konigreich", "scotland"],
    "Luxembourg": ["luxembourg", "lussemburgo", "luxemburg", "lu", "lux"],
    "Australia": ["australia", "au", "aus", "australien", "australie"],
    "United Arab Emirates": ["united arab emirates", "emirati arabi uniti", "uae", "ae", "are", "u a e"],
    "Germany": ["germany", "germania", "deutschland", "de", "deu", "allemagne"],
    "France": ["france", "francia", "frankreich", "fr", "fra"],
    "United States": ["united states", "usa", "us", "united states of america", "stati uniti", "u s"],
    "Spain": ["spain", "spagna", "espana", "es"],
    "Netherlands": ["netherlands", "paesi bassi", "nl", "the netherlands"],
    "Ireland": ["ireland", "irlanda", "ie"],
    "Singapore": ["singapore", "sg"],
    "Hong Kong": ["hong kong", "hk", "hong kong sar"],
    "Liechtenstein": ["liechtenstein", "li"],
    "Monaco": ["monaco", "mc"],
    "Austria": ["austria", "osterreich", "at"],
    "Belgium": ["belgium", "belgio", "be"],
    "Japan": ["japan", "giappone", "jp"],
    "Canada": ["canada", "ca"],
    "India": ["india", "in"],
    "China": ["china", "cina", "cn"],
    "Saudi Arabia": ["saudi arabia", "arabia saudita", "ksa", "sa"],
    "Qatar": ["qatar", "qa"],
    "Poland": ["poland", "polonia", "pl"],
    "Sweden": ["sweden", "svezia", "se"],
    "Denmark": ["denmark", "danimarca", "dk"],
    "Norway": ["norway", "norvegia", "no"],
    "Portugal": ["portugal", "portogallo", "pt"],
    "Jersey": ["jersey", "je"],
    "Argentina": ["argentina", "ar"], "Brazil": ["brazil", "brasil", "br"], "Mexico": ["mexico", "mx"],
    "South Korea": ["south korea", "korea", "republic of korea", "kr"], "Taiwan": ["taiwan", "tw"],
    "Philippines": ["philippines", "ph"], "Malaysia": ["malaysia", "my"], "Indonesia": ["indonesia", "id"],
    "Thailand": ["thailand", "th"], "South Africa": ["south africa", "za"], "Israel": ["israel", "il"],
    "Turkey": ["turkey", "turkiye", "tr"], "Greece": ["greece", "gr"], "Czech Republic": ["czech republic", "czechia", "cz"],
    "Hungary": ["hungary", "hu"], "Romania": ["romania", "ro"], "Finland": ["finland", "fi"], "New Zealand": ["new zealand", "nz"],
    "Bahrain": ["bahrain", "bh"], "Kuwait": ["kuwait", "kw"], "Egypt": ["egypt", "eg"],
    "Guernsey": ["guernsey", "gg"],
}

_CITY_LOOKUP = {a: c for c, aliases in CITY_ALIASES.items() for a in aliases}
_COUNTRY_LOOKUP = {a: c for c, aliases in COUNTRY_ALIASES.items() for a in aliases}
# Two-letter codes are only trusted when they stand alone as a token.
_SHORT_COUNTRY = {a for a in _COUNTRY_LOOKUP if len(a) <= 3}
# Swiss canton codes that ATS feeds append to city names.
_CANTON_CITY = {"zh": "Zurich", "zg": "Zug", "ge": "Geneva", "ti": None, "bs": "Basel", "vd": None, "be": None}


def normalize_city(raw) -> str | None:
    key = norm_text(raw)
    if not key:
        return None
    if key in _CITY_LOOKUP:
        return _CITY_LOOKUP[key]
    return None


def normalize_country(raw) -> str | None:
    key = norm_text(raw)
    if not key:
        return None
    return _COUNTRY_LOOKUP.get(key)


def parse_location(raw, country_hint=None) -> dict:
    """Best-effort split of an ATS location string into canonical city/country.

    Unknown places are returned verbatim in `city` (never coerced to a target
    city) with `country` None unless a country token is present.
    """
    text = str(raw or "").strip()
    out = {"city": None, "country": normalize_country(country_hint) if country_hint else None, "raw": text}
    if not text:
        return out
    flat = norm_text(text)
    # longest alias first so 'new york city' beats 'york'
    for alias in sorted(_CITY_LOOKUP, key=len, reverse=True):
        if re.search(rf"(?<![a-z]){re.escape(alias)}(?![a-z])", flat):
            out["city"] = _CITY_LOOKUP[alias]
            break
    parts = [p.strip() for p in re.split(r"[,;/|()\-–]+", text) if p.strip()]
    if not out["country"]:
        for p in reversed(parts):
            c = normalize_country(p)
            if c and (norm_text(p) not in _SHORT_COUNTRY or len(parts) > 1 or p.isupper()):
                out["country"] = c
                break
    if out["city"] and not out["country"]:
        out["country"] = CITY_COUNTRY.get(out["city"])
    if not out["city"] and parts:
        first = parts[0]
        if normalize_country(first) is None and not re.search(r"remote|hybrid|multiple|various", first, re.I):
            out["city"] = first[:60]
    return out


def split_locations(raw, country_hint=None) -> list[dict]:
    """One entry per place in strings such as 'London, Paris, Hong Kong' or 'Zurich; Geneva'.

    'Baar, CH' or 'London, England, United Kingdom' stay a single place.
    """
    text = str(raw or "").strip()
    if not text:
        return []
    pieces = [p.strip() for p in re.split(r"\s*[;|]\s*|\s+/\s+|\s+(?:or|and|&)\s+", text) if p.strip()]
    out = []
    for piece in pieces:
        tokens = [t.strip() for t in piece.split(",") if t.strip()]
        cities = [t for t in tokens if normalize_city(t)]
        if len(tokens) > 1 and len(cities) >= 2:
            # a list of cities: any other token is a further (unknown) city, never a country
            out.extend(parse_location(t, None if normalize_city(t) else country_hint) if normalize_city(t)
                       else {"city": t[:60], "country": normalize_country(t), "raw": t} for t in tokens)
        else:
            out.append(parse_location(piece, country_hint))
    for o in out:
        if o["city"] and normalize_country(o["city"]) and not normalize_city(o["city"]):
            o["city"] = None  # the token was a country name
    return out


def geo_priority(city, country, settings: dict) -> str:
    """'high' | 'swiss_other' | 'medium' | 'target_country_other_city' | 'other' | 'unknown'."""
    geo = settings.get("geo", {})
    if not city and not country:
        return "unknown"
    for level in ("high", "medium"):
        for ctry, cities in geo.get(level, {}).items():
            if city in cities and (country in (None, ctry)):
                return level
    if country == "Switzerland":
        return "swiss_other"
    target_countries = set(geo.get("high", {})) | set(geo.get("medium", {}))
    if country in target_countries:
        return "target_country_other_city"
    return "other"


PRIORITY_LABEL = {
    "high": "High", "swiss_other": "High", "medium": "Medium",
    "target_country_other_city": "Other", "other": "Other", "unknown": "Unknown",
}
