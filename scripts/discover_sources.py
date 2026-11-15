#!/usr/bin/env python3
"""Analyse company career pages and register the recruitment systems they use.

    python scripts/discover_sources.py                 # next batch (config: discovery.max_companies_per_run)
    python scripts/discover_sources.py --limit 600     # first full pass
    python scripts/discover_sources.py --company "Partners Group" --force
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fcip.companies import load_companies  # noqa: E402
from fcip.discovery import run_discovery  # noqa: E402
from fcip.pipeline import load_jobs, write_meta  # noqa: E402
from fcip.sources import load_sources, save_sources, sync_sources  # noqa: E402
from fcip.util import load_json, load_settings, now_iso, setup_logging, DATA_DIR  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--company")
    ap.add_argument("--force", action="store_true", help="re-analyse even if checked recently")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    setup_logging(args.verbose)
    settings = load_settings()
    companies = load_companies()["companies"]
    sync_sources(companies)
    src_db = load_sources()
    stats = run_discovery(companies, src_db, settings, args.limit, args.company, args.force,
                          checkpoint=save_sources)
    save_sources(src_db)
    prev = load_json(DATA_DIR / "meta.json", {}).get("last_run") or {"started": now_iso(), "sources_ok": 0}
    write_meta(prev, load_jobs()["jobs"], companies, src_db["sources"])
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
