"""Company database: Excel import, incremental merge, additional-company review."""
from __future__ import annotations

import re
from pathlib import Path

from .geo import normalize_city, normalize_country, geo_priority, PRIORITY_LABEL
from .util import (DATA_DIR, company_match_key, is_url, load_json, norm_text, now_iso, save_json,
                   slugify, log)

COMPANIES_FILE = DATA_DIR / "companies.json"
HISTORY_FILE = DATA_DIR / "history.json"
FOCUS_FILE = DATA_DIR / "excel_focus_notes.json"

# Header synonyms (normalised text). The importer never assumes column positions.
COLUMN_SYNONYMS = {
    "excel_id": ["id", "n", "no", "numero", "#"],
    "name": ["nome azienda", "azienda", "company", "company name", "nome", "name", "societa", "firm", "employer"],
    "city": ["citta", "city", "sede", "location", "ufficio", "office"],
    "country": ["paese", "country", "nazione", "stato"],
    "priority": ["priorita geografica", "priorita", "priority", "geographical priority", "geo priority"],
    "sectors": ["settore i principale i", "settore", "settori", "sector", "sectors", "settore principale"],
    "category": ["categoria", "category", "tipo", "type"],
    "website": ["sito web ufficiale", "sito web", "sito", "website", "official website", "url", "web"],
    "career_url": ["url pagina carriere", "pagina carriere", "carriere", "career url", "careers", "career portal",
                   "career page", "careers url", "lavora con noi"],
    "size": ["dimensione approssimativa", "dimensione", "size"],
    "junior_programmes": ["programmi intern graduate junior", "programmi junior", "junior programmes",
                          "intern programmes", "programmi"],
    "languages_typical": ["lingue tipiche offerte", "lingue", "languages"],
    "notes": ["note and requisiti specifici", "note", "notes", "requisiti", "commenti", "comments"],
    "monitoring_status": ["stato candidatura monitoraggio", "stato candidatura", "stato", "status", "monitoraggio"],
}

CATEGORY_EN = {
    "banca privata": "Private Bank", "consulenza": "Consulting", "altro": "Other", "sgr": "SGR (Asset Management Co.)",
    "pe": "Private Equity", "vc": "Venture Capital", "boutique ib": "Boutique Investment Bank",
    "asset manager": "Asset Manager", "family office": "Family Office", "hedge fund": "Hedge Fund",
    "bulge bracket": "Bulge Bracket", "big four": "Big Four",
}
PRIORITY_MAP = {"alta": "High", "high": "High", "media": "Medium", "medium": "Medium", "bassa": "Low", "low": "Low"}
YES_NO = {"si": "yes", "yes": "yes", "no": "no", "non noto": "unknown", "unknown": "unknown", "n d": "unknown", "": "unknown"}

TRACKED_FIELDS = ["name", "category", "sectors", "website", "website_note", "career_url", "career_note", "size",
                  "junior_programmes", "languages_typical", "notes"]


# ------------------------------------------------------------- reading Excel
def _map_header(header_row) -> dict[str, int]:
    mapping: dict[str, int] = {}
    cells = [norm_text(c) for c in header_row]
    for field, synonyms in COLUMN_SYNONYMS.items():
        for syn in synonyms:  # synonyms are ordered most-specific first
            if syn in cells and cells.index(syn) not in mapping.values():
                mapping[field] = cells.index(syn)
                break
    return mapping


def find_company_table(wb):
    """Locate the worksheet + header row that holds the company list.

    Picks the sheet with the most data rows whose header maps at least a
    company-name column. Returns (worksheet, header_row_index, mapping).
    """
    best = None
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(min_row=1, max_row=15, values_only=True))
        for idx, row in enumerate(rows):
            if not row or sum(1 for c in row if c not in (None, "")) < 3:
                continue
            mapping = _map_header(row)
            if "name" in mapping and len(mapping) >= 3:
                score = (len(mapping), ws.max_row)
                if best is None or score > best[0]:
                    best = (score, ws, idx, mapping, row)
                break
    if best is None:
        raise ValueError("No worksheet with a recognisable company-name column was found.")
    return best[1], best[2], best[3], best[4]


def read_excel(path: Path) -> dict:
    import openpyxl

    wb = openpyxl.load_workbook(path, data_only=True, read_only=False)
    ws, header_idx, mapping, header = find_company_table(wb)
    extra_cols = {i: str(h).strip() for i, h in enumerate(header) if h and i not in mapping.values()}
    rows = []
    for r_idx, row in enumerate(ws.iter_rows(min_row=header_idx + 2, values_only=True), start=header_idx + 2):
        if not row or not any(c not in (None, "") for c in row):
            continue

        def cell(field):
            i = mapping.get(field)
            v = row[i] if i is not None and i < len(row) else None
            return str(v).strip() if v not in (None, "") else ""

        name = cell("name")
        if not name:
            continue
        rec = {f: cell(f) for f in COLUMN_SYNONYMS}
        rec["row"] = r_idx
        rec["extra"] = {h: str(row[i]).strip() for i, h in extra_cols.items() if i < len(row) and row[i] not in (None, "")}
        rows.append(rec)

    focus = []
    for other in wb.worksheets:
        if other.title == ws.title:
            continue
        table = [r for r in other.iter_rows(values_only=True) if r and any(c not in (None, "") for c in r)]
        hdr_i = next((i for i, r in enumerate(table) if sum(1 for c in r if c not in (None, "")) >= 4), None)
        if hdr_i is None:
            continue
        hdr = [str(c).strip() if c else "" for c in table[hdr_i]]
        hn = [norm_text(h) for h in hdr]
        if not any("dettaglio" in h or "detail" in h or "note" in h for h in hn):
            continue  # summary/dashboard sheets carry no row-level information
        for r in table[hdr_i + 1:]:
            item = {hdr[i]: str(c).strip() for i, c in enumerate(r) if c not in (None, "") and i < len(hdr) and hdr[i]}
            if len(item) >= 3:
                focus.append({"sheet": other.title, **item})
    return {
        "sheet": ws.title, "header_row": header_idx + 1, "mapping": {k: header[v] for k, v in mapping.items()},
        "unmapped_columns": list(extra_cols.values()), "rows": rows, "focus": focus,
        "sheets": [{"title": s.title, "rows": s.max_row, "cols": s.max_column} for s in wb.worksheets],
    }


# ------------------------------------------------------------- normalising
def _split_list(value: str) -> list[str]:
    return [p.strip() for p in re.split(r"[;|]", value or "") if p.strip()]


def _office(rec: dict, settings: dict) -> dict:
    city = normalize_city(rec["city"]) or (rec["city"] or None)
    country = normalize_country(rec["country"]) or (rec["country"] or None)
    excel_priority = PRIORITY_MAP.get(norm_text(rec["priority"]))
    computed = PRIORITY_LABEL[geo_priority(city, country, settings)]
    office = {
        "city": city, "country": country,
        "city_original": rec["city"] or None, "country_original": rec["country"] or None,
        "priority": excel_priority or computed,
        "priority_original": rec["priority"] or None,
        "name_original": rec["name"],
        "category_original": rec["category"] or None,
    }
    try:
        office["excel_id"] = int(float(rec["excel_id"])) if rec["excel_id"] else None
    except ValueError:
        office["excel_id"] = rec["excel_id"]
    return office


def _incoming_company(rec: dict, settings: dict) -> dict:
    website = rec["website"] if is_url(rec["website"]) else None
    career = rec["career_url"] if is_url(rec["career_url"]) else None
    comp = {
        "name": rec["name"],
        "category": rec["category"] or None,
        "category_en": CATEGORY_EN.get(norm_text(rec["category"]), rec["category"] or None),
        "sectors": _split_list(rec["sectors"]),
        "website": website,
        "website_note": None if website else (rec["website"] or None),
        "career_url": career,
        "career_note": None if career else (rec["career_url"] or None),
        "size": rec["size"] or None,
        "junior_programmes": YES_NO.get(norm_text(rec["junior_programmes"]), "unknown"),
        "languages_typical": _split_list(rec["languages_typical"]),
        "notes": rec["notes"] or None,
        "offices": [_office(rec, settings)],
    }
    if settings.get("privacy", {}).get("publish_excel_monitoring_status"):
        comp["excel_monitoring_status"] = rec["monitoring_status"] or None
    if rec.get("extra"):
        comp["extra"] = rec["extra"]
    return comp


def _best_priority(offices) -> str:
    order = {"High": 0, "Medium": 1, "Low": 2, "Other": 3, "Unknown": 4}
    return min((o.get("priority") or "Unknown" for o in offices), key=lambda p: order.get(p, 9), default="Unknown")


def _merge_rows(a: dict, b: dict) -> None:
    """Fold a second Excel row for the same company (another city) into `a`."""
    for o in b["offices"]:
        if not any(x["city"] == o["city"] and x["country"] == o["country"] for x in a["offices"]):
            a["offices"].append(o)
    if len(b["name"]) < len(a["name"]):
        a["name"] = b["name"]  # 'Point72' rather than 'Point72 (Sydney office)'; every row's own name stays on its office
    for f in ("website", "career_url", "size", "notes", "category", "category_en"):
        if not a.get(f) and b.get(f):
            a[f] = b[f]
    if a.get("website"):
        a["website_note"] = None
    if a.get("career_url"):
        a["career_note"] = None
    for f in ("sectors", "languages_typical"):
        for v in b.get(f, []):
            if v not in a[f]:
                a[f].append(v)
    if b.get("category") and b["category"] != a.get("category"):
        cats = a.setdefault("categories_all", [a.get("category")])
        if b["category"] not in cats:
            cats.append(b["category"])
    if a["junior_programmes"] != "yes" and b["junior_programmes"] == "yes":
        a["junior_programmes"] = "yes"
    if b.get("notes") and b["notes"] != a.get("notes") and b["notes"] not in (a.get("notes") or ""):
        a["notes"] = f"{a['notes']} || {b['notes']}" if a.get("notes") else b["notes"]


# ------------------------------------------------------------- merging
def load_companies() -> dict:
    return load_json(COMPANIES_FILE, {"schema": 1, "companies": []})


def append_history(events: list[dict]) -> None:
    if not events:
        return
    hist = load_json(HISTORY_FILE, {"schema": 1, "events": []})
    hist["events"].extend(events)
    save_json(HISTORY_FILE, hist, compact=True)


def _new_id(key: str, taken: set[str]) -> str:
    base = "c-" + (slugify(key) or "company")[:48]
    cid, n = base, 2
    while cid in taken:
        cid, n = f"{base}-{n}", n + 1
    taken.add(cid)
    return cid


def import_excel(path: Path, settings: dict, dry_run: bool = False) -> dict:
    """Merge an Excel version into data/companies.json. Returns a report dict.

    Guarantees: no duplicates, nothing deleted, additional (non-Excel)
    companies untouched, every field change logged in history.json.
    """
    parsed = read_excel(path)
    ts = now_iso()
    incoming: dict[str, dict] = {}
    for rec in parsed["rows"]:
        comp = _incoming_company(rec, settings)
        key = company_match_key(comp["name"])
        if not key:
            continue
        if key in incoming:
            _merge_rows(incoming[key], comp)
        else:
            incoming[key] = comp

    db = load_companies()
    companies = db["companies"]
    by_key: dict[str, dict] = {}
    for c in companies:
        by_key[c.get("match_key") or company_match_key(c["name"])] = c
        for alias in c.get("aliases", []):
            by_key.setdefault(company_match_key(alias), c)
    taken = {c["id"] for c in companies}

    report = {"file": Path(path).name, "sheet": parsed["sheet"], "sheets": parsed["sheets"],
              "column_mapping": parsed["mapping"], "unmapped_columns": parsed["unmapped_columns"],
              "excel_rows": len(parsed["rows"]), "unique_companies_in_excel": len(incoming),
              "new": [], "modified": [], "new_offices": [], "unchanged": 0, "promoted_from_additional": [],
              "not_in_this_excel": []}
    events = []
    for key, inc in incoming.items():
        cur = by_key.get(key)
        if cur is None:
            comp = {"id": _new_id(key, taken), "match_key": key, "origin": "excel", "status": "active", **inc,
                    "priority": _best_priority(inc["offices"]), "in_latest_excel": True,
                    "first_imported": ts, "last_imported": ts, "last_modified": ts}
            companies.append(comp)
            by_key[key] = comp
            report["new"].append(comp["name"])
            events.append({"ts": ts, "type": "company_added", "company_id": comp["id"], "name": comp["name"],
                           "origin": "excel"})
            continue
        changes = {}
        if cur.get("origin") != "excel":
            report["promoted_from_additional"].append(cur["name"])
            changes["origin"] = [cur.get("origin"), "excel"]
            cur["origin"], cur["status"] = "excel", "active"
        for f in TRACKED_FIELDS:
            new, old = inc.get(f), cur.get(f)
            if f == "name" and new != old:
                aliases = cur.setdefault("aliases", [])
                if old and old not in aliases:
                    aliases.append(old)
            # An empty Excel cell never wipes information already on file.
            if new in (None, "", []) and old not in (None, "", []):
                if f in ("website_note", "career_note"):
                    cur[f] = None
                continue
            if new != old:
                changes[f] = [old, new]
                cur[f] = new
        cur["category_en"] = inc.get("category_en") or cur.get("category_en")
        for o in inc["offices"]:
            match = next((x for x in cur["offices"] if x["city"] == o["city"] and x["country"] == o["country"]), None)
            if match is None:
                cur["offices"].append(o)
                report["new_offices"].append(f"{cur['name']}: {o['city']}")
                changes.setdefault("offices_added", []).append(o["city"])
            else:
                if match.get("priority") != o.get("priority"):
                    changes[f"priority[{o['city']}]"] = [match.get("priority"), o.get("priority")]
                match.update(o)
        cur["priority"] = _best_priority(cur["offices"])
        cur["in_latest_excel"] = True
        cur["last_imported"] = ts
        if "excel_monitoring_status" in inc:
            cur["excel_monitoring_status"] = inc["excel_monitoring_status"]
        else:
            cur.pop("excel_monitoring_status", None)
        if changes:
            cur["last_modified"] = ts
            report["modified"].append({"name": cur["name"], "changes": changes})
            events.append({"ts": ts, "type": "company_modified", "company_id": cur["id"], "name": cur["name"],
                           "changes": changes})
        else:
            report["unchanged"] += 1

    seen_ids = {by_key[k]["id"] for k in incoming}
    for c in companies:
        if c.get("origin") == "excel" and c["id"] not in seen_ids:
            if c.get("in_latest_excel", True):
                events.append({"ts": ts, "type": "company_absent_from_excel", "company_id": c["id"], "name": c["name"]})
            c["in_latest_excel"] = False  # kept and still monitored; never deleted
            report["not_in_this_excel"].append(c["name"])

    companies.sort(key=lambda c: norm_text(c["name"]))
    db.update({"schema": 1, "generated_at": ts, "last_excel_import": {"file": Path(path).name, "at": ts,
                                                                      "rows": len(parsed["rows"])}})
    report["total_companies"] = len(companies)
    if not dry_run:
        save_json(COMPANIES_FILE, db)
        save_json(FOCUS_FILE, {"source_file": Path(path).name, "imported_at": ts, "items": parsed["focus"]})
        events.append({"ts": ts, "type": "excel_import", "file": Path(path).name, "new": len(report["new"]),
                       "modified": len(report["modified"]), "new_offices": len(report["new_offices"]),
                       "total": len(companies)})
        append_history(events)
        log.info("companies.json written: %d companies", len(companies))
    return report


# ------------------------------------------------------------- additional companies
def add_additional_company(name, category, country, city, website, career_url, reason, settings,
                           status="pending_review", discovery_source=None) -> dict | None:
    """Register a company found outside the Excel. Stored separately via origin='additional'."""
    db = load_companies()
    key = company_match_key(name)
    for c in db["companies"]:
        if (c.get("match_key") or company_match_key(c["name"])) == key:
            return None  # already known (Excel or additional): no duplicate
    ts = now_iso()
    city_n = normalize_city(city) or city
    country_n = normalize_country(country) or country
    comp = {
        "id": _new_id(key, {c["id"] for c in db["companies"]}), "match_key": key, "origin": "additional",
        "status": status, "name": name, "category": category, "category_en": CATEGORY_EN.get(norm_text(category), category),
        "sectors": [], "website": website if is_url(website) else None, "website_note": None,
        "career_url": career_url if is_url(career_url) else None, "career_note": None, "size": None,
        "junior_programmes": "unknown", "languages_typical": [], "notes": None,
        "offices": [{"city": city_n, "country": country_n, "city_original": city, "country_original": country,
                     "priority": PRIORITY_LABEL[geo_priority(city_n, country_n, settings)], "excel_id": None}],
        "priority": PRIORITY_LABEL[geo_priority(city_n, country_n, settings)],
        "reason_for_inclusion": reason, "discovery_date": ts[:10], "discovery_source": discovery_source,
        "in_latest_excel": False, "first_imported": ts, "last_imported": ts, "last_modified": ts,
    }
    db["companies"].append(comp)
    db["companies"].sort(key=lambda c: norm_text(c["name"]))
    save_json(COMPANIES_FILE, db)
    append_history([{"ts": ts, "type": "company_added", "company_id": comp["id"], "name": name,
                     "origin": "additional", "status": status}])
    return comp


def set_company_status(company_ref: str, status: str) -> dict | None:
    """Approve / reject / re-queue an additional company (by id or name)."""
    assert status in ("active", "pending_review", "rejected")
    db = load_companies()
    key = company_match_key(company_ref)
    for c in db["companies"]:
        if c["id"] == company_ref or (c.get("match_key") or company_match_key(c["name"])) == key:
            old = c.get("status")
            c["status"] = status
            c["last_modified"] = now_iso()
            if status == "active":
                c["approved_at"] = now_iso()[:10]
            save_json(COMPANIES_FILE, db)
            append_history([{"ts": now_iso(), "type": "company_status", "company_id": c["id"], "name": c["name"],
                             "changes": {"status": [old, status]}}])
            return c
    return None
