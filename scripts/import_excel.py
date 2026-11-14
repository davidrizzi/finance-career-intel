#!/usr/bin/env python3
"""Import or update the company database from an Excel workbook.

    python scripts/import_excel.py input/companies.xlsx            # merge
    python scripts/import_excel.py input/companies.xlsx --dry-run  # report only

Safe to re-run with every new Excel version: nothing is deleted, no
duplicates are created, job history and approved additional companies stay.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fcip.companies import import_excel, load_companies  # noqa: E402
from fcip.sources import sync_sources  # noqa: E402
from fcip.util import load_settings, setup_logging  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("excel", nargs="?", help="path to the .xlsx (default: newest file in input/)")
    ap.add_argument("--dry-run", action="store_true", help="show what would change, write nothing")
    ap.add_argument("--json", action="store_true", help="print the full report as JSON")
    args = ap.parse_args(argv)
    setup_logging()
    path = Path(args.excel) if args.excel else None
    if path is None:
        cands = sorted(Path(__file__).resolve().parent.parent.joinpath("input").glob("*.xlsx"),
                       key=lambda p: p.stat().st_mtime)
        if not cands:
            ap.error("no Excel file given and none found in input/")
        path = cands[-1]
    report = import_excel(path, load_settings(), dry_run=args.dry_run)
    if not args.dry_run:
        report["sources"] = sync_sources(load_companies()["companies"])
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
        return 0
    print(f"\nExcel import {'(dry run) ' if args.dry_run else ''}- {report['file']}")
    print(f"  worksheet used        : {report['sheet']}  (sheets: {', '.join(s['title'] for s in report['sheets'])})")
    print(f"  columns recognised    : {len(report['column_mapping'])}  unmapped: {report['unmapped_columns'] or 'none'}")
    print(f"  Excel rows            : {report['excel_rows']}")
    print(f"  unique companies      : {report['unique_companies_in_excel']}")
    print(f"  new companies         : {len(report['new'])}")
    print(f"  modified companies    : {len(report['modified'])}")
    print(f"  new office locations  : {len(report['new_offices'])}")
    print(f"  unchanged             : {report['unchanged']}")
    print(f"  kept but not in file  : {len(report['not_in_this_excel'])}")
    print(f"  total in database     : {report['total_companies']}")
    for m in report["modified"][:15]:
        print(f"    ~ {m['name']}: {', '.join(m['changes'])}")
    if "sources" in report:
        print(f"  source registry       : {report['sources']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
