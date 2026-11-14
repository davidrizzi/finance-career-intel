#!/usr/bin/env python3
"""Assemble the static website into _site/ (what GitHub Pages serves).

    python scripts/build_site.py
    python -m http.server 8000 -d _site     # then open http://localhost:8000

Copies frontend/ and the public JSON databases. Only files meant for
publication are included: no notification history, no Excel, no secrets.
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DATA = ["meta.json", "jobs.json", "companies.json", "sources.json", "excel_focus_notes.json"]


def main() -> int:
    out = ROOT / "_site"
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT / "frontend", out)
    (out / "data").mkdir()
    (out / "config").mkdir()
    for name in PUBLIC_DATA:
        src = ROOT / "data" / name
        if not src.exists():
            print(f"warning: data/{name} is missing; run scripts/import_excel.py and scripts/update_jobs.py first")
            continue
        data = json.loads(src.read_text(encoding="utf-8"))
        (out / "data" / name).write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    settings = json.loads((ROOT / "config" / "settings.json").read_text(encoding="utf-8"))
    public = {"geo": settings.get("geo", {}), "scoring": {"weights": settings.get("scoring", {}).get("weights", {})}}
    (out / "config" / "settings.json").write_text(json.dumps(public), encoding="utf-8")
    (out / ".nojekyll").write_text("")
    size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    print(f"_site built: {sum(1 for f in out.rglob('*') if f.is_file())} files, {size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
