"""Lever Postings API (public, documented).

GET https://api.lever.co/v0/postings/{token}?mode=json   (EU: api.eu.lever.co)
"""
from connectors.base import raw_job
from fcip.util import SourceError

NAME = "lever"
NEEDS_DETAIL = False


def list_jobs(source, http, settings):
    p = source["params"]
    host = "api.eu.lever.co" if p.get("region") == "eu" else "api.lever.co"
    data = http.get_json(f"https://{host}/v0/postings/{p['token']}?mode=json")
    if not isinstance(data, list):
        raise SourceError(f"lever: unexpected payload for '{p['token']}'")
    out = []
    for j in data:
        cat = j.get("categories") or {}
        locs = cat.get("allLocations") or [cat.get("location")]
        parts = [j.get("description") or j.get("descriptionPlain") or ""]
        for lst in j.get("lists") or []:
            parts.append(f"<p>{lst.get('text', '')}</p><ul>{lst.get('content', '')}</ul>")
        parts.append(j.get("additional") or j.get("additionalPlain") or "")
        sr = j.get("salaryRange") or {}
        salary = None
        if sr.get("min") and sr.get("max"):
            salary = f"{sr['min']:,.0f}-{sr['max']:,.0f} {sr.get('currency', '')} {('per ' + sr['interval']) if sr.get('interval') else ''}".strip()
        out.append(raw_job(
            j["id"], j.get("text"), j.get("hostedUrl"), apply_url=j.get("applyUrl") or j.get("hostedUrl"),
            locations=[l for l in locs if l], country_hint=j.get("country"), description="\n".join(parts),
            published=j.get("createdAt"), department=cat.get("department") or cat.get("team"),
            employment_type=cat.get("commitment"), salary=salary))
    return out
