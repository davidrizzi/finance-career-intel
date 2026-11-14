#!/usr/bin/env python3
"""Review companies that are not in the Excel ("ADDITIONAL COMPANIES").

    python scripts/manage_companies.py list                 # pending review
    python scripts/manage_companies.py approve "Company"    # start monitoring it
    python scripts/manage_companies.py reject  "Company"    # keep on file, never monitor
    python scripts/manage_companies.py add --name "X Capital" --category "PE" --country Switzerland \
        --city Zurich --website https://x.com --careers https://x.com/careers --reason "why it is relevant"

Approved additional companies survive every later Excel import. They are
never written into the Excel list: origin stays 'additional'.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fcip.companies import add_additional_company, load_companies, set_company_status  # noqa: E402
from fcip.sources import sync_sources  # noqa: E402
from fcip.util import load_settings  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    for name in ("approve", "reject", "requeue"):
        sp = sub.add_parser(name)
        sp.add_argument("company", help="company id or name")
    add = sub.add_parser("add")
    for f in ("name", "category", "country", "city", "reason"):
        add.add_argument(f"--{f}", required=True)
    add.add_argument("--website", default="")
    add.add_argument("--careers", default="")
    add.add_argument("--approve", action="store_true", help="add as active instead of pending review")
    args = ap.parse_args(argv)

    if args.cmd == "list":
        rows = [c for c in load_companies()["companies"] if c.get("origin") != "excel"]
        for c in sorted(rows, key=lambda c: c.get("status", "")):
            o = c["offices"][0] if c.get("offices") else {}
            print(f"[{c.get('status', '?'):14}] {c['name']:<40} {c.get('category') or '-':<18} {o.get('city') or '-'}"
                  f"  ({c.get('reason_for_inclusion') or ''})")
        print(f"\n{len(rows)} additional compan(ies); {sum(1 for c in rows if c.get('status') == 'pending_review')} pending review")
        return 0
    if args.cmd == "add":
        c = add_additional_company(args.name, args.category, args.country, args.city, args.website, args.careers,
                                   args.reason, load_settings(), "active" if args.approve else "pending_review",
                                   "manual")
        print("already in the database, nothing added" if c is None else f"added {c['id']} ({c['status']})")
    else:
        status = {"approve": "active", "reject": "rejected", "requeue": "pending_review"}[args.cmd]
        c = set_company_status(args.company, status)
        print("company not found" if c is None else f"{c['name']}: status -> {status}")
    sync_sources(load_companies()["companies"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
