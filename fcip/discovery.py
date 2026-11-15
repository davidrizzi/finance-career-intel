"""Career-portal analysis: find each company's recruitment system from its own pages."""
from __future__ import annotations

from datetime import timedelta

import connectors
from connectors import career_websites
from .ats_detect import CAREER_LINK_RX, VACANCY_LINK_RX, detect_ats, find_links
from .sources import ats_source_id, blank_source
from .util import Http, SourceError, now_iso, today, log

MAX_ATS_PER_COMPANY = 2


def _analyse(url: str, http: Http):
    html, final = http.fetch_page(url)
    return html, final, detect_ats(html, final), bool(career_websites.extract_jobpostings(html))


def discover_source(source: dict, company: dict, http: Http, settings: dict) -> list[dict]:
    """Analyse one career page / website. Mutates `source`; returns new ATS sources to register."""
    ts = now_iso()
    source["last_attempt"] = ts
    source["discovery_checked"] = ts
    try:
        html, final, dets, has_jsonld = _analyse(source["url"], http)
    except SourceError as exc:
        # a dead career link in the Excel: look for the careers page from the official website instead
        site = company.get("website")
        if source["type"] == "career_site" and site and site.rstrip("/") != source["url"].rstrip("/"):
            try:
                home, home_final = http.fetch_page(site)
                links = find_links(home, home_final, CAREER_LINK_RX, limit=3)
                for link in links:
                    try:
                        html, final, dets, has_jsonld = _analyse(link, http)
                        source["career_url_detected"] = final
                        source["evidence"] = f"Career URL in the Excel failed ({str(exc)[:60]}); careers page found on {site}"
                        break
                    except SourceError:
                        continue
                else:
                    raise exc
            except SourceError:
                source.update(status="unreachable", last_error=str(exc)[:300],
                              consecutive_failures=source.get("consecutive_failures", 0) + 1)
                return []
        else:
            source.update(status="unreachable", last_error=str(exc)[:300],
                          consecutive_failures=source.get("consecutive_failures", 0) + 1)
            return []
    source.update(last_error=None, consecutive_failures=0)
    evidence_page = final
    if not dets and not has_jsonld:
        rx = CAREER_LINK_RX if source["type"] == "website" else VACANCY_LINK_RX
        for link in find_links(html, final, rx, limit=3):
            try:
                h2, f2, d2, j2 = _analyse(link, http)
            except SourceError:
                continue
            if source["type"] == "website" and not source.get("career_url_detected") and CAREER_LINK_RX.search(link):
                source["career_url_detected"] = f2
            if d2 or j2:
                html, final, dets, has_jsonld, evidence_page = h2, f2, d2, j2, f2
                break

    new_sources = []
    usable = [d for d in dets if connectors.get(d["ats"]) and not d.get("incomplete")]
    for d in usable[:MAX_ATS_PER_COMPANY]:
        token = d["params"].get("token") or d["params"].get("site") or d["params"].get("base_url") or ""
        sid = ats_source_id(company["id"], d["ats"], f"{d['params'].get('host', '')}{token}")
        new_sources.append(blank_source(
            sid, company["id"], "ats", ats=d["ats"], params=d["params"], method="api", origin="detected",
            status="unverified", url=evidence_page,
            evidence=f"'{d['evidence']}' found on {evidence_page} on {ts[:10]}"))
    if new_sources:
        source.update(status="resolved", ats=new_sources[0]["ats"], last_success=ts,
                      evidence=f"Recruitment system identified: {', '.join(s['ats'] for s in new_sources)}"
                               + (f" ({source['evidence']})" if source.get("career_url_detected") and source.get("evidence") else ""))
        return new_sources
    if has_jsonld:
        source.update(status="unverified", ats="jsonld", method="jsonld", last_success=ts,
                      url=evidence_page if source["type"] == "career_site" else source["url"],
                      evidence=f"schema.org JobPosting data found on {evidence_page}")
        if source["type"] == "website":
            source["params"] = {"start": evidence_page}
        return []
    if dets:
        d = dets[0]
        source.update(status="unsupported", ats=d["ats"], last_success=ts,
                      evidence=f"{d['ats']} detected ('{d['evidence']}') on {evidence_page}: no automated connector, check manually")
        return []
    # last resort: vacancy pages linked from the career page that publish structured data
    try:
        probe = dict(source, url=final)
        saved = career_websites.MAX_PAGES
        career_websites.MAX_PAGES = 6
        try:
            found = career_websites.list_jobs(probe, http, settings)
        finally:
            career_websites.MAX_PAGES = saved
    except SourceError:
        found = []
    if found:
        source.update(status="unverified", ats="jsonld", method="jsonld", last_success=ts, url=final,
                      evidence=f"schema.org JobPosting data on vacancy pages linked from {final}")
    else:
        source.update(status="no_structured_data", ats=None, last_success=ts,
                      evidence=f"{final} is reachable but exposes no ATS or structured vacancy data: check manually")
    return []


def run_discovery(companies: list[dict], src_db: dict, settings: dict, limit: int | None = None,
                  only_company: str | None = None, force: bool = False, http: Http | None = None) -> dict:
    from .util import norm_text

    http = http or Http(settings)
    cfg = settings.get("discovery", {})
    limit = limit or cfg.get("max_companies_per_run", 200)
    stale = (today() - timedelta(days=cfg.get("recheck_after_days", 30))).isoformat()
    retry = (today() - timedelta(days=5)).isoformat()
    comp = {c["id"]: c for c in companies}
    by_id = {s["id"]: s for s in src_db["sources"]}

    def due(s):
        if s["type"] not in ("career_site", "website") or not s.get("url"):
            return False
        if comp.get(s["company_id"], {}).get("status", "active") != "active":
            return False
        if force or s["status"] == "pending_discovery":
            return True
        checked = (s.get("discovery_checked") or "")[:10]
        if s["status"] == "unreachable":
            return checked < retry
        return s["status"] in ("no_structured_data", "unsupported", "resolved") and checked < stale

    todo = [s for s in src_db["sources"] if due(s)]
    if only_company:
        key = norm_text(only_company)
        todo = [s for s in todo if key in norm_text(comp[s["company_id"]]["name"])]
    order = {"High": 0, "Medium": 1}
    todo.sort(key=lambda s: (s["status"] != "pending_discovery", order.get(comp[s["company_id"]].get("priority"), 2),
                             comp[s["company_id"]].get("junior_programmes") != "yes", s["id"]))
    stats = {"analysed": 0, "ats_found": 0, "jsonld": 0, "unsupported": 0, "no_structured_data": 0, "unreachable": 0,
             "remaining": max(0, len(todo) - limit)}
    for s in todo[:limit]:
        c = comp[s["company_id"]]
        new = discover_source(s, c, http, settings)
        stats["analysed"] += 1
        for ns in new:
            if ns["id"] not in by_id:
                by_id[ns["id"]] = ns
                src_db["sources"].append(ns)
        key = "ats_found" if new else {"unverified": "jsonld", "resolved": "ats_found"}.get(s["status"], s["status"])
        stats[key] = stats.get(key, 0) + 1
        log.info("%-34s %-18s %s", c["name"][:34], s["status"], (s.get("evidence") or s.get("last_error") or "")[:90])
    return stats
