"""Collection pipeline: fetch -> normalise -> classify -> dedupe -> status -> score -> history."""
from __future__ import annotations

import hashlib
import re
import time
from datetime import timedelta
from urllib.parse import urlparse

from . import classify, languages, scoring
from .companies import append_history, load_companies
from .geo import PRIORITY_LABEL, geo_priority, parse_location, split_locations
from .sources import load_sources, save_sources, company_monitoring_status
from .util import (DATA_DIR, Http, SourceError, days_until, html_to_text, load_json, norm_text, now_iso, parse_date,
                   save_json, short_hash, log, today)

JOBS_FILE = DATA_DIR / "jobs.json"
META_FILE = DATA_DIR / "meta.json"
MANUAL_FILE = DATA_DIR / "manual_jobs.json"

VERIFICATION_RANK = {"VERIFIED OFFICIAL": 3, "LINKEDIN ONLY": 2, "AGGREGATOR ONLY": 1, "UNVERIFIED": 0}
ACTIVE_STATUSES = ("Open", "Closing Soon", "Future Application Window", "Verification Failed")
MEANINGFUL_FIELDS = ("title", "city", "country", "deadline", "apply_url", "contract_type")
_PRIORITY_ORDER = {"high": 0, "swiss_other": 1, "medium": 2, "target_country_other_city": 3, "other": 4, "unknown": 5}


def load_jobs() -> dict:
    return load_json(JOBS_FILE, {"schema": 1, "jobs": []})


def save_jobs(db: dict) -> None:
    db["generated_at"] = now_iso()
    db["jobs"].sort(key=lambda j: (-(j.get("score") or 0), j["id"]))
    save_json(JOBS_FILE, db, compact=True)


def job_id(company_id: str, ats: str, external_id: str) -> str:
    return "j-" + short_hash(company_id, ats, external_id)


def verification_for(source: dict, url: str = "") -> str:
    if source.get("type") in ("ats", "career_site", "website"):
        return "VERIFIED OFFICIAL"
    host = urlparse(url or "").netloc.lower()
    if source.get("type") == "linkedin" or "linkedin." in host:
        return "LINKEDIN ONLY"
    if source.get("type") == "aggregator":
        return "AGGREGATOR ONLY"
    return "UNVERIFIED"


def title_prefilter(title: str, department: str, company: dict) -> tuple[bool, str | None]:
    """Cheap test on the title alone, before any detail page is requested."""
    sec = classify.classify_sector(title, "", department or "", company.get("category") or "")
    if not sec["relevant"] and sec["source"] == "title":
        return False, sec["reason"]
    sen = classify.classify_seniority(title)
    if not sen["include"]:
        return False, sen.get("reason")
    return True, None


def _pick_location(raw: dict, settings: dict) -> tuple[dict, list[dict]]:
    split = []
    for text in raw.get("locations") or []:
        split.extend(split_locations(text, raw.get("country_hint")))
    if not split:
        split = [parse_location("", raw.get("country_hint"))]
    # best geographical priority first; a named city beats a bare country
    split.sort(key=lambda p: (_PRIORITY_ORDER[geo_priority(p["city"], p["country"], settings)], p["city"] is None))
    uniq = []
    for p in split:
        if (p["city"], p["country"]) not in [(u["city"], u["country"]) for u in uniq]:
            uniq.append(p)
    return uniq[0], uniq


def build_record(raw: dict, company: dict, source: dict, settings: dict, existing: dict | None) -> tuple[dict | None, str | None]:
    """Turn a raw posting into a job record. Returns (record, drop_reason)."""
    ts = now_iso()
    max_chars = settings.get("collection", {}).get("description_max_chars", 3500)
    desc_full = html_to_text(raw.get("description"))
    if not desc_full and existing:
        desc_full = existing.get("description") or ""
    title = re.sub(r"\s+", " ", raw["title"]).strip()
    dept = raw.get("department") or ""

    sector = classify.classify_sector(title, desc_full, dept, company.get("category") or "")
    if not sector["relevant"]:
        return None, sector["reason"]
    sen = classify.classify_seniority(title, desc_full, " ".join(x for x in (raw.get("experience_hint"), raw.get("employment_type")) if x))
    if not sen["include"]:
        return None, sen.get("reason")

    primary, all_locs = _pick_location(raw, settings)
    level = geo_priority(primary["city"], primary["country"], settings)
    if level in ("other", "target_country_other_city") and not settings.get("collection", {}).get("keep_outside_target_locations", True):
        return None, "outside target locations (keep_outside_target_locations=false)"

    lang = languages.analyze_languages(desc_full, title)
    contract = classify.classify_contract(title, desc_full, sen["seniority"], raw.get("employment_type") or "")
    visa = classify.extract_visa(desc_full)
    deadline = parse_date(raw.get("deadline"))
    deadline_source = "source field" if deadline else None
    if not deadline:
        deadline = classify.extract_deadline(desc_full)
        deadline_source = "stated in the description" if deadline else None
    future = classify.detect_future_window(title, desc_full)
    apply_url = raw.get("apply_url") or raw.get("url")
    verification = verification_for(source, apply_url)
    notes = [n for n in ([sector["reason"], sen["warning"]] + lang["notes"]) if n]
    exp = sen["experience"]

    rec = {
        "id": existing["id"] if existing else job_id(company["id"], source.get("ats") or source["type"], raw["external_id"]),
        "company": company["name"], "company_id": company["id"],
        "company_origin": "Excel" if company.get("origin") == "excel" else "Additional",
        "company_category": company.get("category_en") or company.get("category"),
        "title": title, "city": primary["city"], "country": primary["country"], "location_raw": primary["raw"] or None,
        "locations": [{"city": p["city"], "country": p["country"]} for p in all_locs][:12],
        "geo_priority": PRIORITY_LABEL[level], "geo_level": level,
        "sector": sector["sector"], "sector_source": sector["source"], "department": dept or None,
        "seniority": sen["seniority"], "seniority_warning": sen["warning"],
        "contract_type": contract, "programme_year": classify.programme_year(title),
        "published": parse_date(raw.get("published")), "deadline": deadline, "deadline_source": deadline_source,
        "experience": exp["text"] or "Not specified", "experience_min_years": exp["min"], "experience_max_years": exp["max"],
        "languages": lang["languages"], "german_flag": lang["german_flag"], "french_flag": lang["french_flag"],
        "description_language": lang["description_language"], "languages_analysed": lang["analysed"],
        "salary": raw.get("salary") or "Not specified",
        "visa_sponsorship": visa["status"], "visa_note": visa["note"],
        "apply_url": apply_url, "source_url": raw.get("url") or apply_url,
        "source_type": source.get("ats") or source["type"], "verification": verification,
        "future_window_note": future,
        "description": desc_full[:max_chars] + (" [...]" if len(desc_full) > max_chars else ""),
        "notes": notes, "external_id": raw["external_id"],
    }
    return rec, None


def _content_hash(rec: dict) -> str:
    blob = "|".join(str(rec.get(f)) for f in MEANINGFUL_FIELDS) + "|" + hashlib.sha1(
        (rec.get("description") or "").encode("utf-8")).hexdigest()
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


def compute_status(job: dict, settings: dict) -> tuple[str, str | None]:
    """Conservative status. A failing source never turns a job into Expired/Removed."""
    c = settings.get("collection", {})
    if job.get("status") == "Removed" and job.get("closed_at"):
        return "Removed", job.get("status_note")
    left = days_until(job.get("deadline"))
    if left is not None and left < 0:
        return "Expired", f"Deadline {job['deadline']} has passed"
    if job.get("verification_failures", 0) >= c.get("verification_failed_after_failures", 3):
        return "Verification Failed", "The source could not be reached on the last checks; the posting may still be open"
    if job.get("future_window_note"):
        return "Future Application Window", job["future_window_note"]
    if classify.CLOSED_TITLE_RX.search(job.get("title") or ""):
        return "Expired", "The employer's own posting says applications are closed"
    if left is not None and left <= c.get("closing_soon_days", 7):
        return "Closing Soon", f"{left} day(s) left" if left else "Closes today"
    return "Open", None


def upsert(jobs: dict[str, dict], rec: dict, source: dict, events: list[dict], settings: dict) -> str:
    """Insert or update. Returns 'new' | 'modified' | 'unchanged' | 'reopened'."""
    ts = now_iso()
    cur = jobs.get(rec["id"])
    src_entry = {"source_id": source["id"], "type": source.get("ats") or source["type"], "url": rec["source_url"],
                 "verification": rec["verification"], "first_seen": ts, "last_seen": ts}
    h = _content_hash(rec)
    if cur is None:
        rec.update({"first_detected": ts, "last_checked": ts, "last_modified": ts, "content_hash": h,
                    "sources": [src_entry], "missing_checks": 0, "verification_failures": 0, "closed_at": None,
                    "aliases": []})
        rec["status"], rec["status_note"] = compute_status(rec, settings)
        jobs[rec["id"]] = rec
        events.append({"ts": ts, "type": "job_new", "job_id": rec["id"], "company_id": rec["company_id"],
                       "title": rec["title"], "city": rec["city"]})
        return "new"
    outcome = "unchanged"
    changed = [f for f in MEANINGFUL_FIELDS if cur.get(f) != rec.get(f)]
    was_closed = cur.get("status") in ("Removed",)
    keep = {k: cur.get(k) for k in ("first_detected", "sources", "aliases", "last_modified", "status", "status_note")}
    # a field the source stopped publishing is not overwritten with nothing
    for f in ("published", "description"):
        if not rec.get(f) and cur.get(f):
            rec[f] = cur[f]
    cur.update(rec)
    cur.update(keep)
    entry = next((s for s in cur["sources"] if s["source_id"] == source["id"]), None)
    if entry:
        entry.update(last_seen=ts, url=rec["source_url"])
    else:
        cur["sources"].append(src_entry)
    best = max(cur["sources"], key=lambda s: VERIFICATION_RANK.get(s.get("verification"), 0))
    cur["verification"] = best.get("verification", cur["verification"])
    cur.update(last_checked=ts, missing_checks=0, verification_failures=0)
    if h != cur.get("content_hash"):
        cur["content_hash"], cur["last_modified"] = h, ts
        outcome = "modified"
        events.append({"ts": ts, "type": "job_modified", "job_id": cur["id"], "company_id": cur["company_id"],
                       "title": cur["title"], "fields": changed or ["description"]})
        if changed:
            cur["last_meaningful_change"] = {"at": ts, "fields": changed}
    if was_closed:
        cur["closed_at"] = None
        cur["status"] = "Open"
        outcome = "reopened"
        events.append({"ts": ts, "type": "job_reopened", "job_id": cur["id"], "company_id": cur["company_id"],
                       "title": cur["title"]})
        cur["last_meaningful_change"] = {"at": ts, "fields": ["status"]}
    return outcome


def target_countries(settings: dict) -> set[str]:
    geo = settings.get("geo", {})
    return set(geo.get("high", {})) | set(geo.get("medium", {}))


def is_large_board(source: dict, settings: dict) -> bool:
    return (source.get("jobs_found") or 0) > settings.get("collection", {}).get("large_board_threshold", 300)


def outside_scope(locations: list[dict], settings: dict) -> bool:
    """True when a posting's locations are known and none is in a target country or city.

    A place the database cannot name (no city, no country) stays in scope so its
    detail page can be read. Every target city is in the alias table, so a city
    that resolves to nothing known is not a target city.
    """
    targets = target_countries(settings)
    target_cities = {c for lvl in ("high", "medium") for cities in settings.get("geo", {}).get(lvl, {}).values() for c in cities}
    known = [l for l in locations if l.get("city") or l.get("country")]
    if not known:
        return False
    return not any(l.get("country") in targets or l.get("city") in target_cities for l in known)


def refilter_existing(jobs: dict[str, dict], companies: dict, sources: list[dict], settings: dict,
                      events: list[dict]) -> int:
    """Apply the current filters to stored records.

    A record that no longer qualifies because the FILTERS changed (not because the
    vacancy closed) is dropped from the public database; the deletion is logged in
    history.json. Records captured by hand are never touched.
    """
    src = {s["id"]: s for s in sources}
    dropped = 0
    for jid, job in list(jobs.items()):
        ats_sources = [src[s["source_id"]] for s in job.get("sources", []) if s["source_id"] in src]
        if not ats_sources:
            continue
        company = companies.get(job["company_id"], {})
        reason = None
        sec = classify.classify_sector(job["title"], job.get("description") or "", job.get("department") or "",
                                       company.get("category") or "")
        sen = classify.classify_seniority(job["title"], job.get("description") or "")
        if not sec["relevant"]:
            reason = sec["reason"]
        elif not sen["include"]:
            reason = sen.get("reason")
        elif all(is_large_board(s, settings) for s in ats_sources) and outside_scope(job.get("locations") or [], settings):
            reason = "large board: location outside the target countries"
        if reason:
            del jobs[jid]
            dropped += 1
            events.append({"ts": now_iso(), "type": "job_filtered", "job_id": jid, "company_id": job["company_id"],
                           "title": job["title"], "reason": reason})
    return dropped


def touch(job: dict, source: dict, events: list[dict]) -> None:
    """The source still lists this vacancy: refresh its check timestamps without rebuilding it."""
    ts = now_iso()
    entry = next((s for s in job["sources"] if s["source_id"] == source["id"]), None)
    if entry:
        entry["last_seen"] = ts
    job.update(last_checked=ts, missing_checks=0, verification_failures=0)
    if job.get("status") == "Removed":
        job.update(status="Open", closed_at=None, last_meaningful_change={"at": ts, "fields": ["status"]})
        events.append({"ts": ts, "type": "job_reopened", "job_id": job["id"], "company_id": job["company_id"],
                       "title": job["title"]})


def mark_missing(jobs: dict[str, dict], source: dict, seen: set[str], events: list[dict], settings: dict) -> int:
    """Jobs this (healthy) source used to list and no longer does."""
    limit = settings.get("collection", {}).get("removed_after_missing_checks", 2)
    removed, ts = 0, now_iso()
    for job in jobs.values():
        if job["id"] in seen or job.get("status") == "Removed":
            continue
        mine = [s for s in job.get("sources", []) if s["source_id"] == source["id"]]
        if not mine:
            continue
        others_alive = any(s["source_id"] != source["id"] and s.get("last_seen", "") >= job.get("last_checked", "")
                           for s in job["sources"])
        job["missing_checks"] = job.get("missing_checks", 0) + 1
        job["verification_failures"] = 0
        if job["missing_checks"] >= limit and not others_alive:
            job.update(status="Removed", closed_at=ts, last_modified=ts,
                       status_note=f"No longer listed by the source (confirmed on {job['missing_checks']} consecutive checks)")
            removed += 1
            events.append({"ts": ts, "type": "job_removed", "job_id": job["id"], "company_id": job["company_id"],
                           "title": job["title"]})
    return removed


def mark_source_failed(jobs: dict[str, dict], source: dict) -> None:
    for job in jobs.values():
        if job.get("status") == "Removed":
            continue
        if any(s["source_id"] == source["id"] for s in job.get("sources", [])):
            job["verification_failures"] = job.get("verification_failures", 0) + 1


def _url_key(url: str) -> str:
    """Comparable form of an application URL: tracking parameters dropped, job identifiers kept.

    Many employers serve every vacancy from one page and tell them apart only
    by a query parameter (Greenhouse: ?gh_jid=123), so the query string is
    part of the identity.
    """
    from urllib.parse import parse_qsl, urlencode, urlsplit
    u = urlsplit(url)
    qs = [(k, v) for k, v in parse_qsl(u.query) if not k.lower().startswith(("utm_", "source", "src", "ref"))]
    return f"{u.netloc.lower()}{u.path.rstrip('/')}?{urlencode(sorted(qs))}"


def dedupe_across_sources(jobs: dict[str, dict], events: list[dict]) -> int:
    """Same company + title + city seen through different sources -> one record, all sources kept."""
    groups: dict[tuple, list[dict]] = {}
    for job in jobs.values():
        if job.get("status") == "Removed":
            continue
        key = (job["company_id"], norm_text(job["title"]), job.get("city") or "")
        groups.setdefault(key, []).append(job)
    by_url: dict[str, list[dict]] = {}
    for job in jobs.values():
        if job.get("apply_url") and job.get("status") != "Removed":
            by_url.setdefault(_url_key(job["apply_url"]), []).append(job)
    merged = 0
    for group in list(groups.values()) + list(by_url.values()):
        group = [g for g in group if g["id"] in jobs]
        if len(group) < 2:
            continue
        if len({s["source_id"] for g in group for s in g["sources"]}) < 2 and len({g["apply_url"] for g in group}) > 1:
            continue  # same board, different requisitions: genuinely separate vacancies
        group.sort(key=lambda g: (-VERIFICATION_RANK.get(g["verification"], 0), g["first_detected"]))
        keep = group[0]
        for dup in group[1:]:
            if dup["sources"] and keep["sources"] and {s["source_id"] for s in dup["sources"]} == {s["source_id"] for s in keep["sources"]} \
                    and dup["apply_url"] != keep["apply_url"]:
                continue
            for s in dup["sources"]:
                if not any(k["source_id"] == s["source_id"] and k["url"] == s["url"] for k in keep["sources"]):
                    keep["sources"].append(s)
            keep["aliases"] = sorted(set(keep.get("aliases", [])) | {dup["id"]} | set(dup.get("aliases", [])))
            keep["first_detected"] = min(keep["first_detected"], dup["first_detected"])
            for f in ("published", "deadline", "description"):
                if not keep.get(f) and dup.get(f):
                    keep[f] = dup[f]
            del jobs[dup["id"]]
            merged += 1
            events.append({"ts": now_iso(), "type": "job_merged", "job_id": keep["id"], "merged_id": dup["id"],
                           "title": keep["title"]})
    return merged


def rescore(jobs: dict[str, dict], settings: dict) -> None:
    for job in jobs.values():
        res = scoring.score_job(job, settings)
        job["score"] = res["score"]
        job["score_detail"] = {k: res[k] for k in ("breakdown", "positives", "negatives", "missing")}


def refresh_statuses(jobs: dict[str, dict], settings: dict, events: list[dict]) -> None:
    for job in jobs.values():
        old = job.get("status")
        job["status"], job["status_note"] = compute_status(job, settings)
        if old and old != job["status"]:
            events.append({"ts": now_iso(), "type": "job_status", "job_id": job["id"], "company_id": job["company_id"],
                           "title": job["title"], "from": old, "to": job["status"]})
            if job["status"] in ("Closing Soon", "Open") and old in ("Expired", "Removed", "Verification Failed"):
                job["last_meaningful_change"] = {"at": now_iso(), "fields": ["status"]}


def collect_source(source: dict, company: dict, jobs: dict[str, dict], alias_index: dict[str, str], http: Http,
                   settings: dict, events: list[dict]) -> dict:
    """Run one connector end to end. Raises SourceError when the source cannot be read."""
    import connectors

    mod = connectors.get(source.get("ats") or "")
    if mod is None:
        raise SourceError(f"no connector for '{source.get('ats')}'")
    raws = mod.list_jobs(source, http, settings)
    stats = {"listed": len(raws), "relevant": 0, "new": 0, "modified": 0, "filtered": 0, "detail_failed": 0}
    source["jobs_found"] = len(raws)
    large = is_large_board(source, settings)
    budget = settings.get("collection", {}).get("max_detail_requests_per_source", 40)
    recheck_days = settings.get("collection", {}).get("detail_recheck_days", 7)
    recheck_before = (today() - timedelta(days=recheck_days)).isoformat()
    seen: set[str] = set()
    for raw in raws:
        if not raw.get("title") or not raw.get("url"):
            continue
        ok, _ = title_prefilter(raw["title"], raw.get("department") or "", company)
        if ok and large:
            ok = not outside_scope([parse_location(l, raw.get("country_hint")) for l in raw.get("locations") or []], settings)
        if not ok:
            stats["filtered"] += 1
            continue
        jid = job_id(company["id"], source.get("ats") or source["type"], raw["external_id"])
        jid = alias_index.get(jid, jid)
        existing = jobs.get(jid)
        if getattr(mod, "NEEDS_DETAIL", False) and hasattr(mod, "enrich"):
            fresh = existing is not None and existing.get("description") and \
                norm_text(existing["title"]) == norm_text(raw["title"]) and \
                (existing.get("detail_checked") or "") >= recheck_before
            if fresh or (existing is not None and existing.get("description") and budget <= 0):
                # listing confirms the vacancy is still there; detail page was read recently
                touch(existing, source, events)
                stats["relevant"] += 1
                seen.add(jid)
                continue
            if budget > 0:
                budget -= 1
                try:
                    raw = mod.enrich(raw, source, http, settings)
                    raw["_detail_ok"] = True
                except SourceError as exc:
                    stats["detail_failed"] += 1
                    log.debug("detail failed for %s: %s", raw.get("url"), exc)
                    if existing is not None:
                        touch(existing, source, events)
                        stats["relevant"] += 1
                        seen.add(jid)
                        continue
            else:
                stats["detail_deferred"] = stats.get("detail_deferred", 0) + 1
        rec, reason = build_record(raw, company, source, settings, existing)
        if rec is None:
            stats["filtered"] += 1
            if existing is not None:
                seen.add(jid)  # still listed; it simply no longer matches the filters
            continue
        rec["id"] = jid
        if raw.get("_detail_ok"):
            rec["detail_checked"] = now_iso()
        elif existing is not None and existing.get("detail_checked"):
            rec["detail_checked"] = existing["detail_checked"]
        outcome = upsert(jobs, rec, source, events, settings)
        stats["relevant"] += 1
        if outcome in stats:
            stats[outcome] += 1
        seen.add(jid)
    stats["removed"] = mark_missing(jobs, source, seen, events, settings)
    return stats


def run_update(settings: dict, only_company: str | None = None, only_ats: str | None = None,
               limit: int | None = None, http: Http | None = None) -> dict:
    """The daily job. Incremental: existing records are updated in place, history is kept."""
    started = time.time()
    http = http or Http(settings)
    companies = {c["id"]: c for c in load_companies()["companies"]}
    src_db = load_sources()
    jobs_db = load_jobs()
    jobs = {j["id"]: j for j in jobs_db["jobs"]}
    alias_index = {a: j["id"] for j in jobs.values() for a in j.get("aliases", [])}
    events: list[dict] = []
    summary = {"started": now_iso(), "sources_attempted": 0, "sources_ok": 0, "sources_failed": 0,
               "jobs_listed": 0, "new": 0, "modified": 0, "removed": 0, "errors": []}

    todo = [s for s in src_db["sources"]
            if s.get("ats") and s["status"] in ("ok", "error", "unverified")
            and companies.get(s["company_id"], {}).get("status", "active") == "active"]
    if only_company:
        key = norm_text(only_company)
        todo = [s for s in todo if key in norm_text(companies[s["company_id"]]["name"]) or s["company_id"] == only_company]
    if only_ats:
        todo = [s for s in todo if s["ats"] == only_ats]
    if limit:
        todo = todo[:limit]

    for source in todo:
        company = companies[source["company_id"]]
        source["last_attempt"] = now_iso()
        summary["sources_attempted"] += 1
        try:
            stats = collect_source(source, company, jobs, alias_index, http, settings, events)
        except SourceError as exc:
            source.update(status="error", last_error=str(exc)[:300],
                          consecutive_failures=source.get("consecutive_failures", 0) + 1)
            mark_source_failed(jobs, source)
            summary["sources_failed"] += 1
            summary["errors"].append({"source_id": source["id"], "company": company["name"], "error": str(exc)[:300]})
            log.warning("FAILED %-32s %s", company["name"][:32], exc)
            continue
        except Exception as exc:  # a connector bug must not stop the whole run
            source.update(status="error", last_error=f"{type(exc).__name__}: {str(exc)[:240]}",
                          consecutive_failures=source.get("consecutive_failures", 0) + 1)
            mark_source_failed(jobs, source)
            summary["sources_failed"] += 1
            summary["errors"].append({"source_id": source["id"], "company": company["name"],
                                      "error": f"{type(exc).__name__}: {str(exc)[:240]}"})
            log.exception("connector crashed for %s", company["name"])
            continue
        source.update(status="ok", last_success=now_iso(), last_error=None, consecutive_failures=0,
                      jobs_found=stats["listed"], relevant_jobs=stats["relevant"])
        summary["sources_ok"] += 1
        for k in ("new", "modified", "removed"):
            summary[k] += stats[k]
        summary["jobs_listed"] += stats["listed"]
        log.info("ok     %-32s %-15s listed=%-4d relevant=%-3d new=%-3d removed=%d", company["name"][:32],
                 source["ats"], stats["listed"], stats["relevant"], stats["new"], stats["removed"])

    summary["filtered_out"] = refilter_existing(jobs, companies, src_db["sources"], settings, events)
    ingest_manual_jobs(jobs, companies, settings, events)
    if not (only_company or only_ats or limit):
        summary["aggregators"] = ingest_aggregators(jobs, companies, settings, events, http)
    summary["merged"] = dedupe_across_sources(jobs, events)
    refresh_statuses(jobs, settings, events)
    rescore(jobs, settings)

    jobs_db["jobs"] = list(jobs.values())
    save_jobs(jobs_db)
    save_sources(src_db)
    append_history(events)
    summary.update(finished=now_iso(), duration_seconds=round(time.time() - started, 1),
                   http_requests=http.request_count)
    write_meta(summary, list(jobs.values()), list(companies.values()), src_db["sources"])
    return summary


def ingest_manual_jobs(jobs: dict, companies: dict, settings: dict, events: list[dict]) -> int:
    """Postings captured by hand (e.g. seen on LinkedIn). Labelled by where they came from."""
    manual = load_json(MANUAL_FILE, {"jobs": []})
    from .util import company_match_key
    by_key = {c.get("match_key") or company_match_key(c["name"]): c for c in companies.values()}
    n = 0
    for m in manual.get("jobs", []):
        company = by_key.get(company_match_key(m.get("company", "")))
        if not company or not m.get("title") or not m.get("url"):
            continue
        host = urlparse(m["url"]).netloc.lower()
        stype = "linkedin" if "linkedin." in host else "aggregator" if m.get("via") == "aggregator" else "manual"
        source = {"id": f"manual-{stype}", "type": stype, "ats": None}
        raw = {"external_id": short_hash(m["url"]), "title": m["title"], "url": m["url"], "apply_url": m["url"],
               "locations": [m["location"]] if m.get("location") else [], "country_hint": None,
               "description": m.get("description"), "published": m.get("published"), "deadline": m.get("deadline"),
               "department": None, "employment_type": m.get("contract"), "experience_hint": None, "salary": None}
        jid = job_id(company["id"], stype, raw["external_id"])
        rec, _ = build_record(raw, company, source, settings, jobs.get(jid))
        if rec is None:
            continue
        rec["id"] = jid
        upsert(jobs, rec, source, events, settings)
        n += 1
    return n


def ingest_aggregators(jobs: dict, companies: dict, settings: dict, events: list[dict], http: Http) -> dict:
    """Optional third-party search (Adzuna). Two jobs:

    * postings of known companies are added as 'AGGREGATOR ONLY' (and merged with
      the official record when the employer's own portal lists the same role);
    * employers that are NOT in the database but advertise a matching early-career
      role in a target city are proposed as ADDITIONAL COMPANIES with status
      'pending_review'. They are not monitored until approved.
    """
    from connectors.aggregators import adzuna
    from .companies import add_additional_company
    from .util import company_match_key

    if not adzuna.enabled():
        return {"adzuna": "not configured (optional): set ADZUNA_APP_ID and ADZUNA_APP_KEY to enable"}
    try:
        raws = adzuna.search(http, settings)
    except SourceError as exc:
        log.warning("adzuna failed: %s", exc)
        return {"adzuna": f"failed: {str(exc)[:200]}"}
    by_key = {c.get("match_key") or company_match_key(c["name"]): c for c in companies.values()}
    source = {"id": "agg-adzuna", "type": "aggregator", "ats": None}
    seen, stats = set(), {"listed": len(raws), "matched_known": 0, "proposed_companies": 0, "stored": 0}
    for raw in raws:
        name = (raw.get("company_name") or "").strip()
        key = company_match_key(name)
        if not key or not raw.get("title") or not raw.get("url"):
            continue
        company = by_key.get(key)
        if company is None:
            sec = classify.classify_sector(raw["title"], "", "", "")
            sen = classify.classify_seniority(raw["title"])
            loc = parse_location((raw.get("locations") or [""])[0], raw.get("country_hint"))
            if not (sec["relevant"] and sec["source"] == "title" and sen["include"] and sen["seniority"] != "Ambiguous"
                    and geo_priority(loc["city"], loc["country"], settings) in ("high", "medium", "swiss_other")):
                continue
            company = add_additional_company(
                name, "To be classified", loc["country"], loc["city"], "", "",
                f"Advertised '{raw['title'][:80]}' in {loc['city'] or loc['country']} (seen on Adzuna)", settings,
                "pending_review", "adzuna")
            if company is None:
                continue
            companies[company["id"]] = company
            by_key[key] = company
            stats["proposed_companies"] += 1
        else:
            stats["matched_known"] += 1
        if company.get("status") == "rejected":
            continue
        jid = job_id(company["id"], "adzuna", raw["external_id"])
        rec, _ = build_record(raw, company, source, settings, jobs.get(jid))
        if rec is None:
            continue
        rec["id"] = jid
        upsert(jobs, rec, source, events, settings)
        seen.add(jid)
        stats["stored"] += 1
    mark_missing(jobs, source, seen, events, settings)
    return {"adzuna": stats}


def write_meta(summary: dict, jobs: list[dict], companies: list[dict], sources: list[dict]) -> None:
    """Small file the dashboard loads first: last run, coverage counters, per-company roll-up."""
    by_company: dict[str, list[dict]] = {}
    for s in sources:
        by_company.setdefault(s["company_id"], []).append(s)
    active = [j for j in jobs if j.get("status") in ACTIVE_STATUSES]
    with_jobs = {j["company_id"] for j in active}
    coverage = {"monitored": 0, "failed": 0, "pending": 0, "manual_check": 0, "unreachable": 0, "no_portal": 0,
                "not_approved": 0}
    per_company = {}
    for c in companies:
        st = company_monitoring_status(by_company.get(c["id"], []))
        if c.get("status", "active") != "active":
            st = "not_approved"  # additional company awaiting review (or rejected): never polled
        coverage[st] += 1
        srcs = by_company.get(c["id"], [])
        ok_dates = [s["last_success"] for s in srcs if s.get("last_success")]
        ats = sorted({s["ats"] for s in srcs if s.get("ats") and s["ats"] != "jsonld"})
        per_company[c["id"]] = {"monitoring": st, "ats": ats, "last_success": max(ok_dates) if ok_dates else None,
                                "active_jobs": sum(1 for j in active if j["company_id"] == c["id"])}
    prev = load_json(META_FILE, {})
    last_ok = summary.get("finished") if summary.get("sources_ok") else prev.get("last_successful_update")
    meta = {
        "schema": 1, "generated_at": now_iso(), "last_run": summary,
        "last_successful_update": last_ok,
        "totals": {"companies": len(companies),
                   "companies_excel": sum(1 for c in companies if c.get("origin") == "excel"),
                   "companies_additional": sum(1 for c in companies if c.get("origin") != "excel"),
                   "companies_pending_review": sum(1 for c in companies if c.get("status") == "pending_review"),
                   "jobs_total": len(jobs), "jobs_active": len(active),
                   "companies_with_active_jobs": len(with_jobs),
                   "monitored_without_jobs": sum(1 for cid, v in per_company.items()
                                                 if v["monitoring"] == "monitored" and cid not in with_jobs)},
        "coverage": coverage, "companies": per_company,
        "linkedin": {"automated": False,
                     "note": "LinkedIn is not polled automatically (terms of service). Search links and manual capture only."},
    }
    save_json(META_FILE, meta, compact=True)
