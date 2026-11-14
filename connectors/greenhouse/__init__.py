"""Greenhouse Job Board API (public, documented, no authentication).

GET https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true
"""
from connectors.base import raw_job
from fcip.util import SourceError

NAME = "greenhouse"
NEEDS_DETAIL = False


def board_url(params: dict) -> str:
    host = "job-boards.eu.greenhouse.io" if params.get("region") == "eu" else "boards.greenhouse.io"
    return f"https://{host}/{params['token']}"


def list_jobs(source, http, settings):
    token = source["params"]["token"]
    data = http.get_json(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true")
    if not isinstance(data, dict) or "jobs" not in data:
        raise SourceError(f"greenhouse: unexpected payload for board '{token}'")
    out = []
    for j in data["jobs"]:
        locs = [(j.get("location") or {}).get("name")]
        locs += [o.get("location") or o.get("name") for o in j.get("offices") or []]
        pay = j.get("pay_input_ranges") or []
        salary = None
        if pay and pay[0].get("min_cents") and pay[0].get("max_cents"):
            p = pay[0]
            salary = f"{p['min_cents'] / 100:,.0f}-{p['max_cents'] / 100:,.0f} {p.get('currency_type', '')}".strip()
        out.append(raw_job(
            j["id"], j.get("title"), j.get("absolute_url"), apply_url=j.get("absolute_url"),
            locations=list(dict.fromkeys(l for l in locs if l)), description=j.get("content"),
            published=j.get("first_published"), updated=j.get("updated_at"),
            department=", ".join(d["name"] for d in j.get("departments") or [] if d.get("name")) or None,
            salary=salary))
    return out
