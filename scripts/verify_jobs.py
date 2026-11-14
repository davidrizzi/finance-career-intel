#!/usr/bin/env python3
"""Re-check that open postings are still reachable at their application URL.

Listing-based sources are already verified on every collection run (a job
that disappears from a healthy board is closed after two consecutive
checks). This script adds a direct URL check, mainly for postings that do
not come from a pollable board (manual / LinkedIn / aggregator captures).

    python scripts/verify_jobs.py            # non-board postings only
    python scripts/verify_jobs.py --all      # every open posting (slow)

Conservative by design: only an explicit 404/410 counts as "gone", and only
after two consecutive checks. Timeouts and 5xx never close a job.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fcip.companies import append_history  # noqa: E402
from fcip.pipeline import ACTIVE_STATUSES, load_jobs, refresh_statuses, save_jobs  # noqa: E402
from fcip.util import Http, load_settings, now_iso, setup_logging, log  # noqa: E402


def check_url(http: Http, url: str) -> str:
    """'ok' | 'gone' | 'unknown'"""
    import requests
    try:
        http._throttle(url)
        r = http.session.get(url, timeout=http.timeout, allow_redirects=True, stream=True)
        code = r.status_code
        r.close()
    except requests.RequestException:
        return "unknown"
    if code in (404, 410):
        return "gone"
    return "ok" if code < 400 else "unknown"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, default=300)
    args = ap.parse_args(argv)
    setup_logging()
    settings = load_settings()
    http = Http(settings)
    db = load_jobs()
    jobs = {j["id"]: j for j in db["jobs"]}
    events, ts, n = [], now_iso(), 0
    for job in jobs.values():
        if job.get("status") not in ACTIVE_STATUSES or not job.get("apply_url"):
            continue
        if not args.all and job.get("verification") == "VERIFIED OFFICIAL":
            continue
        if n >= args.limit:
            break
        n += 1
        result = check_url(http, job["apply_url"])
        job["last_url_check"] = {"at": ts, "result": result}
        if result == "ok":
            job.update(last_checked=ts, url_gone_checks=0, verification_failures=0)
        elif result == "gone":
            job["url_gone_checks"] = job.get("url_gone_checks", 0) + 1
            if job["url_gone_checks"] >= 2:
                job.update(status="Removed", closed_at=ts, last_modified=ts,
                           status_note="Application page returned 'not found' on two consecutive checks")
                events.append({"ts": ts, "type": "job_removed", "job_id": job["id"], "company_id": job["company_id"],
                               "title": job["title"], "reason": "url gone"})
        else:
            job["verification_failures"] = job.get("verification_failures", 0) + 1
        log.info("%-8s %s", result, job["apply_url"][:100])
    refresh_statuses(jobs, settings, events)
    db["jobs"] = list(jobs.values())
    save_jobs(db)
    append_history(events)
    print(f"checked {n} posting(s); {sum(1 for e in events if e['type'] == 'job_removed')} closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
