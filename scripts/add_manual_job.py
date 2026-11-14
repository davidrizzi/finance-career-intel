#!/usr/bin/env python3
"""Record a posting you found yourself (for example on LinkedIn).

    python scripts/add_manual_job.py --company "Lazard" --title "Off-Cycle Analyst" \
        --url "https://www.linkedin.com/jobs/view/123" --location "Milan" [--deadline 2027-01-31]

It is stored in data/manual_jobs.json and appears on the site after the next
update, labelled LINKEDIN ONLY (linkedin.com URLs) or UNVERIFIED, until the
same role is found on the employer's portal.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fcip.pipeline import MANUAL_FILE  # noqa: E402
from fcip.util import load_json, now_iso, save_json  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for f in ("company", "title", "url"):
        ap.add_argument(f"--{f}", required=True)
    for f in ("location", "deadline", "published", "contract", "description"):
        ap.add_argument(f"--{f}")
    ap.add_argument("--via", choices=["aggregator"], help="set when the URL is a job board other than LinkedIn")
    args = ap.parse_args(argv)
    db = load_json(MANUAL_FILE, {"jobs": []})
    if any(j["url"] == args.url for j in db["jobs"]):
        print("already recorded")
        return 0
    db["jobs"].append({k: v for k, v in vars(args).items() if v} | {"added": now_iso()})
    save_json(MANUAL_FILE, db)
    print(f"recorded; {len(db['jobs'])} manual posting(s) on file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
