"""Test harness: every test gets its own empty data directory and offline HTTP replay."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fcip import companies, pipeline, sources, util  # noqa: E402


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / ("tools" if name.startswith("bootstrap") else "scripts") / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def settings():
    return util.load_settings()


@pytest.fixture
def data(tmp_path, monkeypatch):
    """Point every module at a temporary data/ and config/known_sources.json."""
    d = tmp_path / "data"
    d.mkdir()
    monkeypatch.setattr(util, "DATA_DIR", d)
    monkeypatch.setattr(companies, "COMPANIES_FILE", d / "companies.json")
    monkeypatch.setattr(companies, "HISTORY_FILE", d / "history.json")
    monkeypatch.setattr(companies, "FOCUS_FILE", d / "excel_focus_notes.json")
    monkeypatch.setattr(sources, "SOURCES_FILE", d / "sources.json")
    known = tmp_path / "known_sources.json"
    known.write_text('{"sources": []}')
    monkeypatch.setattr(sources, "KNOWN_SOURCES_FILE", known)
    monkeypatch.setattr(pipeline, "JOBS_FILE", d / "jobs.json")
    monkeypatch.setattr(pipeline, "META_FILE", d / "meta.json")
    monkeypatch.setattr(pipeline, "MANUAL_FILE", d / "manual_jobs.json")
    monkeypatch.delenv("ADZUNA_APP_ID", raising=False)
    monkeypatch.delenv("ADZUNA_APP_KEY", raising=False)
    return d


HEADERS = ["ID", "Nome Azienda", "Città", "Paese", "Priorità Geografica", "Settore/i Principale/i", "Categoria",
           "Sito Web Ufficiale", "URL Pagina Carriere", "Dimensione Approssimativa", "Programmi Intern/Graduate/Junior",
           "Lingue Tipiche Offerte", "Note & Requisiti Specifici", "Stato Candidatura / Monitoraggio"]


def make_excel(path, rows, headers=HEADERS, title_rows=0, sheet="Database Aziende"):
    import openpyxl
    wb = openpyxl.Workbook()
    summary = wb.active
    summary.title = "Dashboard & Riepilogo"
    summary.append(["DASHBOARD"])
    ws = wb.create_sheet(sheet)
    for _ in range(title_rows):
        ws.append(["Some title above the table"])
    ws.append(headers)
    for r in rows:
        ws.append(r)
    focus = wb.create_sheet("Focus Junior & Boutique")
    focus.append(["FOCUS TARGET"])
    focus.append(["Classificazione Target", "Nome Azienda / Cluster", "Città", "Paese", "Categoria", "Dettaglio Operativo"])
    focus.append(["1. Priorità Alta", "Alpha / Beta", "Zugo", "Svizzera", "PE", "Summer Analyst e Off-Cycle (6 mesi)"])
    wb.save(path)
    return path


BASE_ROWS = [
    [1, "Alpha Capital SA", "Lugano", "Svizzera", "Alta", "Private Equity; Advisory", "PE", "https://alpha.example/", "https://alpha.example/careers", "Boutique", "Sì", "Italiano; Inglese", "Stage semestrali", "Priorità candidatura"],
    [2, "Beta Bank", "Zurigo", "Svizzera", "Alta", "Wealth Management", "Banca privata", "https://beta.example/", "https://beta.example/jobs", "Grande", "Sì", "Tedesco; Inglese", "Graduate programme", "Da monitorare"],
    [3, "Beta Bank", "Londra", "Regno Unito", "Media", "Investment Banking", "Banca privata", "https://beta.example/", "https://beta.example/jobs", "Grande", "Sì", "Inglese", "London office", "Da monitorare"],
    [4, "Gamma Trustee Sagl", "Lugano", "Svizzera", "Alta", "Family Office", "Family Office", "Elenco Ufficiale FINMA", "Approccio diretto / Autocandidatura", "Boutique indipendente", "Non noto", "Italiano", "Censita FINMA", "Da monitorare"],
    [5, "Delta Advisory", "Milano", "Italia", "Alta", "M&A", "Boutique IB", "https://delta.example", "N/D", "Boutique", "No", "Italiano; Inglese", None, "Scartata"],
]


@pytest.fixture
def excel(tmp_path):
    return make_excel(tmp_path / "companies_v1.xlsx", BASE_ROWS)


@pytest.fixture
def replay(tmp_path, monkeypatch):
    """Write recorded responses and switch fcip.util.Http to replay mode. Returns an add(key, payload) helper."""
    rdir = tmp_path / "replay"
    rdir.mkdir()
    index = {}

    def add(key, payload, status=200):
        name = f"f{len(index):03d}.txt"
        (rdir / name).write_text(payload if isinstance(payload, str) else json.dumps(payload), encoding="utf-8")
        index[key] = {"status": status, "file": name}
        (rdir / "index.json").write_text(json.dumps(index))

    (rdir / "index.json").write_text("{}")
    monkeypatch.setenv("FCIP_HTTP_REPLAY", str(rdir))
    add.dir = rdir
    return add


@pytest.fixture
def live_replay(tmp_path, monkeypatch):
    """The reduced real responses captured on 2026-11-13, rebuilt into native payloads."""
    boot = load_script("bootstrap_from_capture")
    rdir = tmp_path / "live"
    totals = boot.build_replay(rdir)
    monkeypatch.setenv("FCIP_HTTP_REPLAY", str(rdir))
    return totals
