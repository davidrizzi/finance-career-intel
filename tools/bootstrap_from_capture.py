#!/usr/bin/env python3
"""Rebuild the initial job database from the live captures in tests/fixtures/live_capture.

The captures are real responses from employer recruitment systems, recorded on
the date in each file and reduced to early-career roles in the target cities
(with description excerpts) so they fit in the repository. This script turns
them back into the native payload shape of each system, replays them through
the real connectors and pipeline, and writes data/jobs.json.

It exists for two reasons: the offline test-suite uses the same replay, and it
gave the site real content before the first GitHub Actions run. The daily
workflow replaces these records with full, current data.

    python tools/bootstrap_from_capture.py            # writes into data/
    python tools/bootstrap_from_capture.py --replay-only DIR   # only build the replay files
"""
import argparse
import html
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAPTURES = ROOT / "tests" / "fixtures" / "live_capture"
JID_BOARDS_NOTE = "boards whose public links are '<career page>?gh_jid=<id>' (confirmed live)"


def build_replay(out: Path) -> dict:
    """Write index.json + payload files. Returns {source key: real total listed}."""
    out.mkdir(parents=True, exist_ok=True)
    index, totals, n = {}, {}, 0

    def put(key, text):
        nonlocal n
        n += 1
        name = f"r{n:03d}.txt"
        (out / name).write_text(text, encoding="utf-8")
        index[key] = {"status": 200, "file": name}

    for f in sorted(CAPTURES.glob("boards_part*.json")):
        for board in json.loads(f.read_text(encoding="utf-8")):
            ats, token = board["b"].split(":")
            totals[(ats, token)] = board["total"]
            if ats == "gh":
                jobs = []
                for j in board["jobs"]:
                    url = j["u"] + (f"?gh_jid={j['i']}" if board.get("jid") and "gh_jid" not in j["u"] else "")
                    jobs.append({"id": j["i"], "title": j["t"], "absolute_url": url, "location": {"name": j["l"]},
                                 "offices": [{"name": o} for o in j.get("o", [])], "updated_at": j["up"],
                                 "first_published": j["fp"], "application_deadline": j.get("dl"),
                                 "departments": [{"name": d} for d in j.get("dp", [])],
                                 "content": html.escape(f"<p>{html.escape(j['x'])}</p>")})
                put(f"GET https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true",
                    json.dumps({"jobs": jobs, "meta": {"total": len(jobs)}}))
            elif ats == "sr":
                api = f"https://api.smartrecruiters.com/v1/companies/{token}/postings"
                content = [{"id": j["i"], "name": j["t"], "releasedDate": j["rd"], "location": j["l"],
                            "department": {"label": j.get("dep")}, "typeOfEmployment": {"label": j.get("toe")},
                            "experienceLevel": {"label": j.get("exp")}} for j in board["jobs"]]
                put(f"GET {api}?limit=100&offset=0", json.dumps({"totalFound": len(content), "content": content}))
                for j in board["jobs"]:
                    put(f"GET {api}/{j['i']}", json.dumps({
                        "applyUrl": j["apply"], "postingUrl": j["posting"],
                        "jobAd": {"sections": {"jobDescription": {"title": "Job Description",
                                                                  "text": f"<p>{html.escape(j['x'])}</p>"}}}}))
    for f in sorted(CAPTURES.glob("successfactors_*.json")):
        cap = json.loads(f.read_text(encoding="utf-8"))
        base = cap["base"]
        totals[("successfactors", base)] = cap["total_listed"]
        rows = "".join(
            f'<tr class="data-row"><td class="colTitle"><span class="jobTitle hidden-phone">'
            f'<a class="jobTitle-link" href="{html.escape(j["u"])}">{html.escape(j["t"])}</a></span></td>'
            f'<td class="colLocation hidden-phone"><span class="jobLocation">{html.escape(j["l"])}</span></td>'
            f'<td class="colDate hidden-phone"><span class="jobDate">{html.escape(j["d"])}</span></td></tr>'
            for j in cap["jobs"])
        page = f'<html><body><table id="searchresults" class="searchResults">{rows}</table></body></html>'
        put(f"GET {base}/search/?q=&sortColumn=referencedate&sortDirection=desc&startrow=0", page)
        for j in cap["jobs"]:
            put(f"GET {base}{j['u']}",
                f'<html><body><meta itemprop="datePosted" content="{j["p"]}">'
                f'<span class="jobdescription"><p>{html.escape(j["x"])}</p></span></body></html>')
    (out / "index.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
    return totals


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--replay-only", metavar="DIR")
    args = ap.parse_args(argv)
    replay = Path(args.replay_only) if args.replay_only else ROOT / "out" / "replay"
    totals = build_replay(replay)
    if args.replay_only:
        print(f"replay written to {replay}")
        return 0
    os.environ["FCIP_HTTP_REPLAY"] = str(replay)
    sys.path.insert(0, str(ROOT))
    from fcip.companies import load_companies
    from fcip.pipeline import load_jobs, run_update, save_jobs, write_meta
    from fcip.sources import load_sources, save_sources, sync_sources
    from fcip.util import load_json, load_settings, save_json, setup_logging, DATA_DIR

    setup_logging()
    companies = load_companies()["companies"]
    sync_sources(companies)
    summary = run_update(load_settings())
    # the replay holds a reduced listing: restore the real board sizes that were observed live
    src_db = load_sources()
    for s in src_db["sources"]:
        key = {"greenhouse": ("gh", s["params"].get("token")), "smartrecruiters": ("sr", s["params"].get("token")),
               "successfactors": ("successfactors", s["params"].get("base_url"))}.get(s.get("ats"))
        if key in totals:
            s["jobs_found"] = totals[key]
            s["snapshot_note"] = "initial snapshot of 2026-11-13: early-career roles in target cities only"
    save_sources(src_db)
    db = load_jobs()
    note = "Description is an excerpt from the initial capture (2026-11-13); the full text is loaded by the first automated run"
    for j in db["jobs"]:
        if note not in j["notes"]:
            j["notes"].append(note)
    save_jobs(db)
    summary["bootstrap_note"] = ("Initial snapshot captured on 2026-11-13 from 21 live employer boards, reduced to "
                                 "early-career roles in the target cities. The first GitHub Actions run replaces it "
                                 "with the complete, current listings.")
    summary["jobs_listed"] = sum(totals.values())
    write_meta(summary, db["jobs"], companies, src_db["sources"])
    print(json.dumps({k: v for k, v in summary.items() if k != "errors"}, indent=1))
    for e in summary.get("errors", []):
        print("ERROR", e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
