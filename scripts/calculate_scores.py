#!/usr/bin/env python3
"""Recompute relevance scores (and statuses) for every stored job.

Run after changing weights or preferences in config/settings.json:

    python scripts/calculate_scores.py
    python scripts/calculate_scores.py --explain j-1a2b3c4d5e6f
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fcip.companies import append_history  # noqa: E402
from fcip.pipeline import load_jobs, refresh_statuses, rescore, save_jobs  # noqa: E402
from fcip.util import load_settings  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--explain", metavar="JOB_ID")
    args = ap.parse_args(argv)
    settings = load_settings()
    db = load_jobs()
    jobs = {j["id"]: j for j in db["jobs"]}
    events = []
    refresh_statuses(jobs, settings, events)
    rescore(jobs, settings)
    db["jobs"] = list(jobs.values())
    save_jobs(db)
    append_history(events)
    if args.explain:
        j = jobs.get(args.explain)
        print(json.dumps({"title": j["title"], "score": j["score"], **j["score_detail"]}, indent=1) if j else "unknown job id")
    else:
        print(f"rescored {len(jobs)} jobs; {len(events)} status change(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
