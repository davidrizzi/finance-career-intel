#!/usr/bin/env python3
"""Write docs/SOURCES.md: which sources are monitored and which need manual intervention."""
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from fcip.companies import load_companies  # noqa: E402
from fcip.sources import load_sources  # noqa: E402
from fcip.util import now_iso  # noqa: E402


def main() -> int:
    comps = {c["id"]: c for c in load_companies()["companies"]}
    srcs = load_sources()["sources"]
    by_status = defaultdict(list)
    for s in srcs:
        by_status[s["status"]].append(s)
    name = lambda s: comps[s["company_id"]]["name"]  # noqa: E731
    cities = lambda s: ", ".join(sorted({o["city"] for o in comps[s["company_id"]]["offices"] if o.get("city")}))  # noqa: E731
    out = [f"# Sources\n\nGenerated {now_iso()[:10]} by `python tools/sources_report.py`. The live view is the Monitoring page of the site.\n",
           "## Summary\n", "| Status | Sources | Meaning |", "|---|---:|---|"]
    meaning = {"ok": "Read successfully on the last run", "unverified": "Registered, not read yet", "error": "Last read failed",
               "pending_discovery": "Career page or website on file, recruitment system not analysed yet (automatic, first runs)",
               "resolved": "Career page analysed; its recruitment system is registered as a separate source",
               "unsupported": "Recruitment system recognised but has no connector: check by hand",
               "no_structured_data": "Page reachable but not machine-readable: check by hand",
               "unreachable": "Career page did not answer", "no_portal_known": "The Excel has no website or career URL for this company"}
    for st, n in Counter(s["status"] for s in srcs).most_common():
        out.append(f"| {st} | {n} | {meaning.get(st, '')} |")

    live = sorted((s for s in srcs if s.get("ats") and s["status"] in ("ok", "error", "unverified")), key=name)
    out += ["\n## Sources successfully monitored\n", "| Company | Offices | System | Board | Postings on board | Matching early-career roles | Evidence |",
            "|---|---|---|---|---:|---:|---|"]
    for s in live:
        ref = s["params"].get("token") or s["params"].get("base_url") or s["params"].get("host") or ""
        out.append(f"| {name(s)} | {cities(s)} | {s['ats']} | `{ref}` | {s.get('jobs_found', '')} | {s.get('relevant_jobs', '')} | {s.get('evidence') or ''} |")

    out += ["\n## Sources requiring manual intervention\n",
            "### A. No website or career URL in the Excel\n",
            f"{len(by_status['no_portal_known'])} companies. The Excel describes them as direct-approach firms (FINMA or ASG register entries). "
            "To monitor one, put its career page URL in the Excel column \"URL Pagina Carriere\" and re-import, or add it to `config/known_sources.json`.\n"]
    groups = defaultdict(list)
    for s in by_status["no_portal_known"]:
        c = comps[s["company_id"]]
        groups[(c["offices"][0].get("city") or "?")].append(c["name"])
    for city in sorted(groups, key=lambda k: -len(groups[k])):
        out.append(f"<details><summary>{city}: {len(groups[city])}</summary>\n\n{'; '.join(sorted(groups[city]))}\n\n</details>\n")

    out += ["### B. Recognised system without a connector, or page not machine-readable\n"]
    manual = by_status["unsupported"] + by_status["no_structured_data"] + by_status["unreachable"]
    if manual:
        out += ["| Company | Status | Detail | Link |", "|---|---|---|---|"]
        out += [f"| {name(s)} | {s['status']} | {s.get('evidence') or s.get('last_error') or ''} | {s.get('url') or ''} |" for s in sorted(manual, key=name)]
    else:
        out.append("None yet. This list fills in as the discovery step analyses career pages.\n")

    pend = sorted(by_status["pending_discovery"], key=name)
    out += [f"\n### C. Waiting for automatic analysis ({len(pend)})\n",
            "No action needed: the daily workflow analyses these pages (set the first run to 600). Listed so that nothing is silently left out.\n",
            "<details><summary>Show the list</summary>\n", "| Company | Offices | Page |", "|---|---|---|"]
    out += [f"| {name(s)} | {cities(s)} | {s.get('url') or ''} |" for s in pend]
    out.append("\n</details>\n")
    add = [c for c in comps.values() if c.get("origin") != "excel"]
    out += [f"\n### D. Additional companies awaiting your approval ({sum(1 for c in add if c.get('status') == 'pending_review')})\n",
            "| Company | Category | City | Website | Reason |", "|---|---|---|---|---|"]
    out += [f"| {c['name']} | {c.get('category') or ''} | {c['offices'][0].get('city') or ''} | {c.get('website') or ''} | {c.get('reason_for_inclusion') or ''} |"
            for c in sorted(add, key=lambda c: c["name"]) if c.get("status") == "pending_review"]
    out += ["\n### E. Sources that cannot be automated by design\n",
            "- **LinkedIn**: not polled (terms of service). Search links per company and manual capture only.",
            "- **jobs.ch, Jobup.ch, eFinancialCareers, Indeed, Karriere.ch, JobRoom**: no free public API; search links only.",
            "- **Adzuna**: official API, optional; needs your free developer key (`ADZUNA_APP_ID`, `ADZUNA_APP_KEY`).",
            "- **Taleo, iCIMS, Avature, tal.net, Umantis, Refline and similar**: detected and reported, no connector.\n"]
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "SOURCES.md").write_text("\n".join(out), encoding="utf-8")
    print(f"docs/SOURCES.md written ({len(live)} monitored, {len(by_status['no_portal_known'])} without portal, {len(pend)} pending)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
