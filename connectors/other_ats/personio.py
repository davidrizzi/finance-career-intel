"""Personio public XML feed: GET https://{token}.jobs.personio.{de|com}/xml"""
import xml.etree.ElementTree as ET

from connectors.base import raw_job
from fcip.util import SourceError

NAME = "personio"
NEEDS_DETAIL = False


def list_jobs(source, http, settings):
    p = source["params"]
    host = f"{p['token']}.jobs.personio.{p.get('tld', 'de')}"
    text = http.get(f"https://{host}/xml")
    try:
        root = ET.fromstring(text.encode("utf-8"))
    except ET.ParseError as exc:
        raise SourceError(f"personio: invalid XML from {host}: {exc}") from exc
    out = []
    for pos in root.iter("position"):
        g = lambda tag: (pos.findtext(tag) or "").strip() or None  # noqa: E731
        desc = "".join(f"<h3>{(d.findtext('name') or '').strip()}</h3>{d.findtext('value') or ''}"
                       for d in pos.iter("jobDescription"))
        offices = [g("office")] + [(o.text or "").strip() for o in pos.iter("additionalOffice")]
        url = f"https://{host}/job/{g('id')}"
        out.append(raw_job(g("id"), g("name"), url, apply_url=url, locations=[o for o in offices if o],
                           description=desc, published=g("createdAt"), department=g("department"),
                           employment_type=" ".join(x for x in (g("employmentType"), g("schedule")) if x) or None,
                           experience_hint=" ".join(x for x in (g("seniority"), g("yearsOfExperience")) if x) or None))
    return out
