"""Connector contract.

A connector module exposes:

    NAME: str                      registry key, equal to source["ats"]
    list_jobs(source, http, settings) -> list[dict]     raw postings (cheap)
    enrich(raw, source, http, settings) -> dict         optional detail fetch
    NEEDS_DETAIL: bool             True when list_jobs carries no description

Raw posting keys (all optional except external_id, title, url):
    external_id, title, url, apply_url, locations (list[str]), country_hint,
    description (html or text), published, updated, deadline, department,
    employment_type, experience_hint, salary, detail_ref

Connectors raise fcip.util.SourceError when the source cannot be read. They
must never return an empty list to signal a failure: an empty list means
"the board is reachable and currently lists no vacancies".
"""
from __future__ import annotations


def raw_job(external_id, title, url, **kw) -> dict:
    job = {"external_id": str(external_id), "title": (title or "").strip(), "url": url, "apply_url": None,
           "locations": [], "country_hint": None, "description": None, "published": None, "updated": None,
           "deadline": None, "department": None, "employment_type": None, "experience_hint": None,
           "salary": None, "detail_ref": None}
    job.update(kw)
    job["locations"] = [str(x).strip() for x in (job["locations"] or []) if x and str(x).strip()]
    return job
