"""Recruitee public offers API: GET https://{token}.recruitee.com/api/offers/"""
from connectors.base import raw_job
from fcip.util import SourceError

NAME = "recruitee"
NEEDS_DETAIL = False


def list_jobs(source, http, settings):
    token = source["params"]["token"]
    data = http.get_json(f"https://{token}.recruitee.com/api/offers/")
    if not isinstance(data, dict) or "offers" not in data:
        raise SourceError(f"recruitee: unexpected payload for '{token}'")
    out = []
    for j in data["offers"]:
        if j.get("status") not in (None, "published"):
            continue
        loc = j.get("location") or ", ".join(x for x in (j.get("city"), j.get("country")) if x)
        out.append(raw_job(
            j["id"], j.get("title"), j.get("careers_url"), apply_url=j.get("careers_apply_url") or j.get("careers_url"),
            locations=[loc] if loc else [], country_hint=j.get("country_code") or j.get("country"),
            description=(j.get("description") or "") + (j.get("requirements") or ""),
            published=j.get("published_at") or j.get("created_at"), department=j.get("department"),
            employment_type=j.get("employment_type_code"), experience_hint=j.get("experience_code")))
    return out
