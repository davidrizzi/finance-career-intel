"""Acceptance tests 1-2: Excel import, validation, incremental updates, additional companies."""
import json
from pathlib import Path

import pytest

from conftest import BASE_ROWS, HEADERS, ROOT, make_excel
from fcip import companies, sources
from fcip.util import company_match_key, load_json


def db():
    return load_json(companies.COMPANIES_FILE)["companies"]


def test_import_reads_structure_without_fixed_positions(data, tmp_path, settings):
    # shuffled columns, a title row above the header, and an unknown extra column
    order = [1, 6, 2, 3, 8, 7, 0, 4, 5, 9, 10, 11, 12, 13]
    headers = [HEADERS[i] for i in order] + ["Contatto"]
    rows = [[r[i] for i in order] + ["someone"] for r in BASE_ROWS]
    path = make_excel(tmp_path / "shuffled.xlsx", rows, headers, title_rows=2, sheet="Elenco")
    report = companies.import_excel(path, settings)
    assert report["sheet"] == "Elenco" and report["excel_rows"] == 5
    assert report["unique_companies_in_excel"] == 4            # Beta Bank appears twice (two cities)
    assert report["unmapped_columns"] == ["Contatto"]
    alpha = next(c for c in db() if c["name"] == "Alpha Capital SA")
    assert alpha["career_url"] == "https://alpha.example/careers" and alpha["extra"] == {"Contatto": "someone"}


def test_company_records_are_valid_and_normalised(data, excel, settings):
    companies.import_excel(excel, settings)
    rows = db()
    assert len({c["id"] for c in rows}) == len(rows) == 4
    beta = next(c for c in rows if c["name"] == "Beta Bank")
    assert [(o["city"], o["country"], o["priority"]) for o in beta["offices"]] == [
        ("Zurich", "Switzerland", "High"), ("London", "United Kingdom", "Medium")]
    assert beta["offices"][0]["city_original"] == "Zurigo" and beta["category"] == "Banca privata"  # originals kept
    assert beta["category_en"] == "Private Bank" and beta["priority"] == "High"
    gamma = next(c for c in rows if c["name"].startswith("Gamma"))
    assert gamma["website"] is None and gamma["website_note"] == "Elenco Ufficiale FINMA"   # text is not a URL
    assert gamma["career_note"] == "Approccio diretto / Autocandidatura"
    assert all("excel_monitoring_status" not in c for c in rows)     # personal column not published by default
    assert all(c["origin"] == "excel" and c["status"] == "active" for c in rows)
    focus = load_json(companies.FOCUS_FILE)
    assert focus["items"] and focus["items"][0]["Città"] == "Zugo"


def test_every_company_gets_a_source_and_no_portal_is_explicit(data, excel, settings):
    companies.import_excel(excel, settings)
    sources.sync_sources(db())
    src = load_json(sources.SOURCES_FILE)["sources"]
    by = {s["company_id"]: s for s in src}
    assert len(src) == 4
    assert by["c-alpha-capital"]["type"] == "career_site" and by["c-alpha-capital"]["status"] == "pending_discovery"
    assert by["c-delta-advisory"]["type"] == "website"
    assert by["c-gamma-trustee"]["type"] == "none" and by["c-gamma-trustee"]["status"] == "no_portal_known"


def test_reimport_is_idempotent(data, excel, settings):
    companies.import_excel(excel, settings)
    before = json.dumps(db(), sort_keys=True)
    report = companies.import_excel(excel, settings)
    assert report["new"] == [] and report["modified"] == [] and report["unchanged"] == 4
    after = db()
    assert len(after) == 4
    strip = lambda rows: json.dumps([{k: v for k, v in c.items() if k != "last_imported"} for c in rows], sort_keys=True)  # noqa: E731
    assert strip(json.loads(before)) == strip(after)


def test_incremental_update_adds_modifies_and_never_deletes(data, excel, tmp_path, settings):
    companies.import_excel(excel, settings)
    sources.sync_sources(db())
    extra = companies.add_additional_company("Omega Partners", "PE", "Switzerland", "Zug", "https://omega.example",
                                             "https://omega.example/careers", "Zug buy-out fund", settings)
    companies.set_company_status(extra["id"], "active")
    v2 = [list(r) for r in BASE_ROWS if r[1] != "Delta Advisory"]              # Delta dropped from the Excel
    v2[0][8] = "https://alpha.example/join-us"                                   # corrected career URL
    v2[0][1] = "Alpha Capital"                                                   # legal suffix removed: same company
    v2.append([9, "Beta Bank", "Ginevra", "Svizzera", "Alta", "Wealth Management", "Banca privata", "https://beta.example/", "https://beta.example/jobs", "Grande", "Sì", "Francese", "Geneva desk", "Da monitorare"])
    v2.append([10, "Epsilon Ventures", "Milano", "Italia", "Alta", "Venture Capital", "VC", "https://epsilon.example", "https://epsilon.example/careers", "Boutique", "Sì", "Italiano", None, "Da monitorare"])
    report = companies.import_excel(make_excel(tmp_path / "v2.xlsx", v2), settings)
    assert report["new"] == ["Epsilon Ventures"]
    assert report["new_offices"] == ["Beta Bank: Geneva"]
    assert any(m["name"] == "Alpha Capital" and "career_url" in m["changes"] for m in report["modified"])
    assert report["not_in_this_excel"] == ["Delta Advisory"]
    rows = {c["name"]: c for c in db()}
    assert len(rows) == 6                                                        # 4 + additional + new; nothing deleted, no duplicate
    assert rows["Delta Advisory"]["in_latest_excel"] is False and rows["Delta Advisory"]["status"] == "active"
    assert rows["Alpha Capital"]["id"] == "c-alpha-capital" and "Alpha Capital SA" in rows["Alpha Capital"]["aliases"]
    assert rows["Omega Partners"]["origin"] == "additional" and rows["Omega Partners"]["status"] == "active"
    history = load_json(companies.HISTORY_FILE)["events"]
    assert {"company_added", "company_modified", "company_absent_from_excel", "excel_import"} <= {e["type"] for e in history}
    stats = sources.sync_sources(db())
    alpha_src = next(s for s in load_json(sources.SOURCES_FILE)["sources"] if s["company_id"] == "c-alpha-capital")
    assert alpha_src["url"] == "https://alpha.example/join-us" and stats["updated"] >= 1


def test_empty_excel_cell_never_wipes_known_information(data, excel, tmp_path, settings):
    companies.import_excel(excel, settings)
    v2 = [list(r) for r in BASE_ROWS]
    v2[0][8] = None
    companies.import_excel(make_excel(tmp_path / "v2.xlsx", v2), settings)
    assert next(c for c in db() if c["id"] == "c-alpha-capital")["career_url"] == "https://alpha.example/careers"


def test_additional_companies_are_separate_and_need_approval(data, excel, settings):
    companies.import_excel(excel, settings)
    c = companies.add_additional_company("Zeta Family Office", "Family Office", "Svizzera", "Lugano", "https://zeta.example",
                                         "https://zeta.example/careers", "Lugano multi-family office", settings)
    assert c["origin"] == "additional" and c["status"] == "pending_review" and c["discovery_date"]
    assert c["offices"][0]["country"] == "Switzerland" and c["reason_for_inclusion"]
    assert companies.add_additional_company("Alpha Capital", "PE", "Switzerland", "Lugano", "", "", "dup", settings) is None
    assert companies.add_additional_company("Zeta Family Office SA", "FO", "Switzerland", "Lugano", "", "", "dup", settings) is None
    companies.import_excel(excel, settings)                                      # a later Excel import keeps it
    assert next(x for x in db() if x["name"] == "Zeta Family Office")["status"] == "pending_review"
    assert companies.set_company_status("Zeta Family Office", "active")["status"] == "active"


def test_match_key_ignores_legal_form_and_case():
    assert company_match_key("BELVOIR CAPITAL AG") == company_match_key("Belvoir Capital AG") == "belvoir capital"
    assert company_match_key("Lombard Odier (UK)") == "lombard odier"
    assert company_match_key("Pictet & Cie Group SCA") == "pictet and cie group"


REAL = sorted((ROOT / "input").glob("*.xlsx"))


@pytest.mark.skipif(not REAL, reason="the real Excel is kept out of the repository (input/ is git-ignored)")
def test_real_excel_imports_completely(data, settings):
    report = companies.import_excel(REAL[-1], settings)
    rows = db()
    assert report["excel_rows"] == sum(len(c["offices"]) for c in rows)          # no Excel row silently dropped
    assert len({c["id"] for c in rows}) == len(rows) == report["unique_companies_in_excel"]
    assert all(c["name"] and c["offices"] and c["category"] for c in rows)
    assert report["unmapped_columns"] == []
