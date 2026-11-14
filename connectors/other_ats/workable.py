"""Workable public widget API: GET https://apply.workable.com/api/v1/widget/accounts/{token}?details=true"""
from connectors.base import raw_job
from fcip.util import SourceError

NAME = "workable"
NEEDS_DETAIL = False


def list_jobs(source, http, settings):
    token = source["params"]["token"]
    data = http.get_json(f"https://apply.workable.com/api/v1/widget/accounts/{token}?details=true")
    if not isinstance(data, dict) or "jobs" not in data:
        raise SourceError(f"workable: unexpected payload for '{token}'")
    out = []
    for j in data["jobs"]:
        loc = ", ".join(x for x in (j.get("city"), j.get("state"), j.get("country")) if x)
        out.append(raw_job(j.get("shortcode") or j.get("id"), j.get("title"), j.get("url") or j.get("shortlink"),
                           apply_url=j.get("application_url") or j.get("url"), locations=[loc] if loc else [],
                           country_hint=j.get("country"), description=j.get("description"),
                           published=j.get("published_on") or j.get("created_at"), department=j.get("department"),
                           employment_type=j.get("employment_type"), experience_hint=j.get("experience")))
    return out
