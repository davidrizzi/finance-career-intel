"""Source registry: one or more monitored sources per company (data/sources.json)."""
from __future__ import annotations

from .util import CONFIG_DIR, DATA_DIR, company_match_key, load_json, now_iso, save_json, log

SOURCES_FILE = DATA_DIR / "sources.json"
KNOWN_SOURCES_FILE = CONFIG_DIR / "known_sources.json"

# statuses that mean "we can read vacancies from here"
COLLECTABLE = {"ok", "error", "unverified"}
STATUS_LABEL = {
    "ok": "Monitored", "error": "Check failed", "unverified": "Not yet checked",
    "pending_discovery": "Career page not yet analysed", "unsupported": "ATS detected, manual check",
    "no_structured_data": "Reachable, not machine-readable", "unreachable": "Career page unreachable",
    "no_portal_known": "No career portal in database", "disabled": "Disabled",
}


def load_sources() -> dict:
    return load_json(SOURCES_FILE, {"schema": 1, "sources": []})


def save_sources(db: dict) -> None:
    db["generated_at"] = now_iso()
    db["sources"].sort(key=lambda s: s["id"])
    save_json(SOURCES_FILE, db)


def blank_source(sid, company_id, stype, **kw) -> dict:
    src = {"id": sid, "company_id": company_id, "type": stype, "ats": None, "url": None, "params": {},
           "method": None, "origin": None, "status": "pending_discovery", "last_attempt": None,
           "last_success": None, "last_error": None, "consecutive_failures": 0, "jobs_found": None,
           "relevant_jobs": None, "evidence": None}
    src.update(kw)
    return src


def ats_source_id(company_id: str, ats: str, token: str) -> str:
    from .util import slugify
    return f"s-{company_id[2:]}-{ats}-{slugify(token)[:40]}"


def sync_sources(companies: list[dict]) -> dict:
    """Make sure every company is represented in the registry.

    * career URL in the Excel  -> 'career_site' source awaiting ATS detection
    * only a website           -> 'website' source (discovery looks for a careers link)
    * neither                  -> explicit 'none' source, so 'no portal known'
                                  is never mistaken for 'no vacancies'
    Existing sources keep their check history. Known/verified ATS endpoints
    from config/known_sources.json are attached to the matching company.
    """
    db = load_sources()
    by_id = {s["id"]: s for s in db["sources"]}
    stats = {"added": 0, "updated": 0, "known_attached": 0}
    for c in companies:
        cid = c["id"]
        base_id = f"s-{cid[2:]}-site"
        cur = by_id.get(base_id)
        if c.get("career_url"):
            want = dict(type="career_site", url=c["career_url"], method="detect", origin=c.get("origin", "excel"))
        elif c.get("website"):
            want = dict(type="website", url=c["website"], method="detect", origin=c.get("origin", "excel"))
        else:
            want = dict(type="none", url=None, method="none", origin=c.get("origin", "excel"),
                        status="no_portal_known", evidence=c.get("career_note") or c.get("website_note"))
        if cur is None:
            by_id[base_id] = blank_source(base_id, cid, want.pop("type"), **want)
            stats["added"] += 1
        elif cur.get("url") != want.get("url") or cur.get("type") != want["type"]:
            # Excel corrected the URL: re-run detection, keep the audit trail
            cur.update(want)
            if want["type"] != "none":
                cur.update(status="pending_discovery", last_error=None, consecutive_failures=0)
            stats["updated"] += 1

    known = load_json(KNOWN_SOURCES_FILE, {"sources": []})
    by_key = {c.get("match_key") or company_match_key(c["name"]): c for c in companies}
    for k in known.get("sources", []):
        comp = by_key.get(company_match_key(k.get("company", "")))
        if comp is None:
            log.warning("known_sources.json: company %r is not in the database, entry skipped", k.get("company"))
            continue
        token = k.get("token") or k.get("url") or ""
        sid = ats_source_id(comp["id"], k["ats"], token)
        if sid not in by_id:
            by_id[sid] = blank_source(sid, comp["id"], "ats", ats=k["ats"], url=k.get("url"),
                                      params=k.get("params") or ({"token": k["token"]} if k.get("token") else {}),
                                      method="api", origin="known", status="unverified",
                                      evidence=k.get("evidence"))
            stats["known_attached"] += 1
    valid = {c["id"] for c in companies}
    db["sources"] = [s for s in by_id.values() if s["company_id"] in valid]
    save_sources(db)
    return stats


def company_monitoring_status(sources: list[dict]) -> str:
    """Roll a company's sources up into one honest label."""
    st = {s["status"] for s in sources}
    if "ok" in st:
        return "monitored"
    if "error" in st:
        return "failed"
    if "unverified" in st or "pending_discovery" in st:
        return "pending"
    if "unsupported" in st or "no_structured_data" in st:
        return "manual_check"
    if "unreachable" in st:
        return "unreachable"
    return "no_portal"
