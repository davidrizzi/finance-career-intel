#!/usr/bin/env python3
"""Daily collection run: read every monitored source, update data/*.json.

    python scripts/update_jobs.py
    python scripts/update_jobs.py --company "Point72" -v
    python scripts/update_jobs.py --ats greenhouse --limit 5

Exit code is 0 even when individual sources fail: failures are recorded per
source in data/sources.json and shown on the Monitoring page.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fcip.companies import load_companies  # noqa: E402
from fcip.pipeline import run_update  # noqa: E402
from fcip.sources import sync_sources  # noqa: E402
from fcip.util import load_settings, setup_logging  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--company", help="only sources of companies whose name contains this text")
    ap.add_argument("--ats", help="only this connector")
    ap.add_argument("--limit", type=int, help="stop after N sources")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    setup_logging(args.verbose)
    sync_sources(load_companies()["companies"])
    summary = run_update(load_settings(), args.company, args.ats, args.limit)
    errors = summary.pop("errors")
    print(json.dumps(summary, indent=1))
    if errors:
        print(f"\n{len(errors)} source(s) failed (jobs from those sources keep their previous status):")
        for e in errors[:40]:
            print(f"  - {e['company']}: {e['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
