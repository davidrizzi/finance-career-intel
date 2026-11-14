"""SmartRecruiters Posting API (public, documented).

GET https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=100&offset=N
GET https://api.smartrecruiters.com/v1/companies/{token}/postings/{id}
"""
from connectors.base import raw_job
from fcip.util import SourceError

NAME = "smartrecruiters"
NEEDS_DETAIL = True
API = "https://api.smartrecruiters.com/v1/companies"


def list_jobs(source, http, settings):
    token = source["params"]["token"]
    out, offset = [], 0
    while True:
        data = http.get_json(f"{API}/{token}/postings?limit=100&offset={offset}")
        if not isinstance(data, dict) or "content" not in data:
            raise SourceError(f"smartrecruiters: unexpected payload for '{token}'")
        for j in data["content"]:
            loc = j.get("location") or {}
            label = ", ".join(x for x in (loc.get("city"), loc.get("region"), (loc.get("country") or "").upper()) if x)
            out.append(raw_job(
                j["id"], j.get("name"), f"https://jobs.smartrecruiters.com/{token}/{j['id']}",
                locations=[label] if label else [], country_hint=(loc.get("country") or "").upper() or None,
                published=j.get("releasedDate"), department=(j.get("department") or {}).get("label"),
                employment_type=(j.get("typeOfEmployment") or {}).get("label"),
                experience_hint=(j.get("experienceLevel") or {}).get("label"),
                detail_ref=f"{API}/{token}/postings/{j['id']}"))
        offset += 100
        if offset >= int(data.get("totalFound") or 0) or not data["content"] or offset >= 3000:
            break
    return out


def enrich(raw, source, http, settings):
    d = http.get_json(raw["detail_ref"])
    sections = ((d.get("jobAd") or {}).get("sections") or {})
    html = "".join(f"<h3>{s.get('title', '')}</h3>{s.get('text', '')}" for s in sections.values() if isinstance(s, dict))
    raw["description"] = html or None
    raw["apply_url"] = d.get("applyUrl") or d.get("postingUrl") or raw["url"]
    raw["url"] = d.get("postingUrl") or raw["url"]
    return raw
