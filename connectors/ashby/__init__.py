"""Ashby public job-board API (documented).

GET https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true
"""
from connectors.base import raw_job
from fcip.util import SourceError

NAME = "ashby"
NEEDS_DETAIL = False


def list_jobs(source, http, settings):
    token = source["params"]["token"]
    data = http.get_json(f"https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true")
    if not isinstance(data, dict) or "jobs" not in data:
        raise SourceError(f"ashby: unexpected payload for '{token}'")
    out = []
    for j in data["jobs"]:
        if j.get("isListed") is False:
            continue
        locs = [j.get("location")] + [s.get("location") for s in j.get("secondaryLocations") or []]
        addr = ((j.get("address") or {}).get("postalAddress") or {})
        comp = (j.get("compensation") or {}).get("compensationTierSummary")
        out.append(raw_job(
            j["id"], j.get("title"), j.get("jobUrl"), apply_url=j.get("applyUrl") or j.get("jobUrl"),
            locations=[l for l in locs if l], country_hint=addr.get("addressCountry"),
            description=j.get("descriptionHtml") or j.get("descriptionPlain"), published=j.get("publishedAt"),
            department=j.get("department") or j.get("team"), employment_type=j.get("employmentType"),
            salary=comp or None))
    return out
