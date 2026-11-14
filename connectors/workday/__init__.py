"""Workday candidate-experience endpoints (the same JSON the public career site loads).

POST https://{host}/wday/cxs/{tenant}/{site}/jobs      {"limit":20,"offset":0,"searchText":"","appliedFacets":{}}
GET  https://{host}/wday/cxs/{tenant}/{site}{externalPath}

Large tenants are queried with early-career search terms instead of paging
through thousands of unrelated requisitions.
"""
import re

from connectors.base import raw_job
from fcip.util import SourceError

NAME = "workday"
NEEDS_DETAIL = True
PAGE = 20
FULL_SCAN_LIMIT = 300
SEARCH_TERMS = ["intern", "internship", "analyst", "graduate", "trainee", "summer", "off-cycle", "junior",
                "associate", "stage", "praktikum", "working student", "placement"]


def _base(p):
    return f"https://{p['host']}/wday/cxs/{p['tenant']}/{p['site']}"


def _page(http, p, offset, text=""):
    data = http.post_json(f"{_base(p)}/jobs", {"appliedFacets": {}, "limit": PAGE, "offset": offset, "searchText": text})
    if not isinstance(data, dict) or "jobPostings" not in data:
        raise SourceError(f"workday: unexpected payload for {p['host']}/{p['site']}")
    return data


def _collect(http, p, text, found, cap):
    offset, total = 0, None
    while True:
        data = _page(http, p, offset, text)
        if total is None:
            total = int(data.get("total") or 0)  # Workday only reports the total on the first page
        for j in data["jobPostings"]:
            path = j.get("externalPath")
            if not path or path in found:
                continue
            req = next((b for b in j.get("bulletFields") or [] if re.match(r"^[A-Za-z_-]*\d+", str(b))), None)
            found[path] = raw_job(
                req or path.rsplit("/", 1)[-1], j.get("title"), f"https://{p['host']}/{p['site']}{path}",
                locations=[j["locationsText"]] if j.get("locationsText") else [],
                detail_ref=f"{_base(p)}{path}")
        offset += PAGE
        if offset >= min(total, cap) or not data["jobPostings"]:
            return total


def list_jobs(source, http, settings):
    p = source["params"]
    found: dict = {}
    first = _page(http, p, 0)
    total = int(first.get("total") or 0)
    if total <= FULL_SCAN_LIMIT:
        _collect(http, p, "", found, FULL_SCAN_LIMIT)
    else:
        for term in SEARCH_TERMS:
            _collect(http, p, term, found, 200)
    return list(found.values())


def enrich(raw, source, http, settings):
    info = (http.get_json(raw["detail_ref"]) or {}).get("jobPostingInfo") or {}
    raw["description"] = info.get("jobDescription")
    locs = [info.get("location")] + list(info.get("additionalLocations") or [])
    if any(locs):
        raw["locations"] = [l for l in locs if l]
    raw["country_hint"] = (info.get("country") or {}).get("descriptor")
    raw["published"] = info.get("startDate")
    raw["deadline"] = info.get("endDate")
    raw["employment_type"] = info.get("timeType")
    raw["url"] = info.get("externalUrl") or raw["url"]
    raw["apply_url"] = raw["url"]
    return raw
