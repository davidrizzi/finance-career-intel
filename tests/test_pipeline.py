"""Acceptance tests 3-7, 19: connectors, real captured postings, links, dedupe, status logic, failures."""
import json

import pytest

from conftest import BASE_ROWS, ROOT, make_excel
from fcip import companies, discovery, pipeline, sources
from fcip.ats_detect import detect_ats
from fcip.util import Http, SourceError, load_json, save_json

LONG = ("We are looking for a motivated student to join our investment team. You will build financial models in Excel, "
        "support due diligence and prepare investment memos. Fluent English required; German is a plus. ")


def add_company(name="Alpha Capital", category="PE", ats=None, params=None, status="active", origin="excel", url=None):
    db = load_json(companies.COMPANIES_FILE, {"schema": 1, "companies": []})
    cid = "c-" + name.lower().replace(" ", "-")
    db["companies"].append({"id": cid, "match_key": name.lower(), "origin": origin, "status": status, "name": name,
                            "category": category, "category_en": category, "sectors": [], "website": None, "career_url": url,
                            "offices": [{"city": "Zurich", "country": "Switzerland", "priority": "High"}], "priority": "High",
                            "junior_programmes": "yes"})
    save_json(companies.COMPANIES_FILE, db)
    if ats:
        s = load_json(sources.SOURCES_FILE, {"schema": 1, "sources": []})
        s["sources"].append(sources.blank_source(f"s-{cid[2:]}-{ats}", cid, "ats", ats=ats, params=params or {}, url=url,
                                                 method="api", origin="known", status="unverified"))
        save_json(sources.SOURCES_FILE, s)
    return cid


def jobs():
    return load_json(pipeline.JOBS_FILE)["jobs"]


def gh_payload(*items):
    return {"jobs": [{"id": i, "title": t, "absolute_url": f"https://boards.greenhouse.io/alpha/jobs/{i}", "location": {"name": loc},
                      "updated_at": "2026-11-01T10:00:00-04:00", "first_published": "2026-10-20T10:00:00-04:00",
                      "departments": [{"name": "Investments"}], "content": f"&lt;p&gt;{LONG}{extra}&lt;/p&gt;"}
                     for i, t, loc, extra in items]}


GH_URL = "GET https://boards-api.greenhouse.io/v1/boards/alpha/jobs?content=true"


# ---------------------------------------------------------------- real data
def test_real_captured_postings_flow_through_the_real_connectors(data, live_replay, settings, monkeypatch):
    """Runs Greenhouse, SmartRecruiters and SuccessFactors connectors on responses recorded live on 2026-11-13."""
    monkeypatch.setattr(sources, "KNOWN_SOURCES_FILE", ROOT / "config" / "known_sources.json")
    known = json.loads((ROOT / "config" / "known_sources.json").read_text())["sources"]
    db = {"schema": 1, "companies": []}
    save_json(companies.COMPANIES_FILE, db)
    for k in known:
        add_company(k["company"], "Hedge Fund")
    db = load_json(companies.COMPANIES_FILE)
    from fcip.util import company_match_key
    for c in db["companies"]:
        c["match_key"] = company_match_key(c["name"])
    save_json(companies.COMPANIES_FILE, db)
    assert sources.sync_sources(db["companies"])["known_attached"] == len(known) == 21
    summary = pipeline.run_update(settings)
    assert summary["sources_attempted"] == 21 and summary["sources_failed"] == 0 and summary["errors"] == []
    got = jobs()
    assert len(got) >= 30
    titles = {j["title"] for j in got}
    assert "Summer Analyst Program 2027" in titles and "6-month Internship - Private Equity Directs, Services" in titles
    # filters applied to real postings
    assert "Junior Customer Care (50%) - Hospitality & Client Dining Support" not in titles      # non-target function
    assert "Credit Analyst – European Financials" not in titles                                   # 5-10 years required
    assert "Operations Analyst – Energy Trading" not in titles                                    # 5+ years required
    assert "Trade Surveillance Analyst" not in titles
    pg = next(j for j in got if j["title"] == "Summer Analyst Program 2027")
    assert (pg["city"], pg["country"], pg["geo_priority"]) == ("Zug", "Switzerland", "High")      # 'Baar, CH'
    assert pg["seniority"] == "Summer Analyst" and pg["programme_year"] == 2027 and pg["published"] == "2026-10-20"
    assert pg["verification"] == "VERIFIED OFFICIAL" and pg["source_type"] == "successfactors"
    alix = next(j for j in got if j["title"].startswith("Praktikum im Consulting"))
    assert alix["german_flag"] == "REQUIRED" and alix["description_language"] == "de" and alix["city"] == "Zurich"
    fa = next(j for j in got if j["title"].startswith("Financial Analyst / Associate"))
    assert fa["experience_min_years"] == 2 and fa["city"] == "Milan" and "2-4 years" in fa["seniority_warning"]
    # mandatory fields present on every record; unknowns are explicit, never invented
    need = ["id", "company", "company_id", "company_origin", "company_category", "title", "city", "country", "sector", "seniority",
            "contract_type", "published", "deadline", "experience", "languages", "german_flag", "french_flag", "salary",
            "visa_sponsorship", "apply_url", "source_url", "source_type", "verification", "first_detected", "last_checked",
            "last_modified", "status", "score", "notes"]
    for j in got:
        assert all(k in j for k in need), j["title"]
        assert j["deadline"] is None and j["salary"] == "Not specified"        # none of these postings publishes either
        assert 0 <= j["score"] <= 100 and j["score_detail"]["breakdown"]


def test_application_links_are_direct_and_distinct(data, live_replay, settings, monkeypatch):
    test_real_captured_postings_flow_through_the_real_connectors(data, live_replay, settings, monkeypatch)
    got = jobs()
    urls = [j["apply_url"] for j in got]
    assert all(u.startswith("http") for u in urls) and len(set(urls)) == len(urls)   # one link per vacancy
    import re
    assert all(re.search(r"\d{6,}", u) for u in urls)                                 # each carries the posting's own id
    # Squarepoint serves every vacancy from one page and distinguishes them by ?gh_jid=: they must stay separate
    sq = [j for j in got if j["company"] == "Squarepoint Capital"]
    assert len(sq) == 6 and len({j["apply_url"].split("?")[0] for j in sq}) == 1
    # two different requisitions with the same title and city on the same board are two vacancies
    assert sum(1 for j in got if j["title"] == "Analyst, Technology M&A") == 2


# ---------------------------------------------------------------- other connectors (documented payload shapes)
def test_lever_ashby_recruitee_workable_personio(data, replay, settings):
    add_company("Lever Co", ats="lever", params={"token": "leverco"})
    replay("GET https://api.lever.co/v0/postings/leverco?mode=json", [
        {"id": "abc-1", "text": "Investment Analyst Intern", "hostedUrl": "https://jobs.lever.co/leverco/abc-1", "applyUrl": "https://jobs.lever.co/leverco/abc-1/apply",
         "createdAt": 1793491200000, "categories": {"location": "Zurich", "team": "Investments", "commitment": "Internship", "allLocations": ["Zurich", "London"]},
         "descriptionPlain": LONG, "lists": [{"text": "Requirements", "content": "<li>Fluent German (C1)</li>"}], "additionalPlain": "",
         "salaryRange": {"min": 3000, "max": 3500, "currency": "CHF", "interval": "per-month-salary"}}])
    add_company("Ashby Co", ats="ashby", params={"token": "ashbyco"})
    replay("GET https://api.ashbyhq.com/posting-api/job-board/ashbyco?includeCompensation=true", {"jobs": [
        {"id": "u-1", "title": "Graduate Analyst, Private Equity", "location": "London", "secondaryLocations": [{"location": "Milan"}],
         "department": "Deal Team", "employmentType": "FullTime", "publishedAt": "2026-11-02T09:00:00.000+00:00", "isListed": True,
         "jobUrl": "https://jobs.ashbyhq.com/ashbyco/u-1", "applyUrl": "https://jobs.ashbyhq.com/ashbyco/u-1/application", "descriptionHtml": f"<p>{LONG}</p>"},
        {"id": "u-2", "title": "Hidden role", "location": "London", "isListed": False, "jobUrl": "https://jobs.ashbyhq.com/ashbyco/u-2"}]})
    add_company("Recruitee Co", ats="recruitee", params={"token": "recco"})
    replay("GET https://recco.recruitee.com/api/offers/", {"offers": [
        {"id": 77, "title": "Stagista M&A", "location": "Milano, Italia", "city": "Milano", "country": "Italy", "country_code": "IT", "status": "published",
         "description": f"<p>{LONG}</p>", "requirements": "<p>Ottima conoscenza dell'inglese.</p>", "careers_url": "https://recco.recruitee.com/o/stagista-ma",
         "careers_apply_url": "https://recco.recruitee.com/o/stagista-ma/c/new", "published_at": "2026-11-03 08:00:00 UTC", "department": "M&A"}]})
    add_company("Workable Co", ats="workable", params={"token": "workco"})
    replay("GET https://apply.workable.com/api/v1/widget/accounts/workco?details=true", {"jobs": [
        {"title": "Equity Research Intern", "shortcode": "AB12", "url": "https://apply.workable.com/j/AB12", "application_url": "https://apply.workable.com/j/AB12/apply",
         "city": "Geneva", "country": "Switzerland", "department": "Research", "employment_type": "Internship", "published_on": "2026-11-04", "description": f"<p>{LONG}</p>"}]})
    add_company("Personio Co", ats="personio", params={"token": "persco", "tld": "de"})
    replay("GET https://persco.jobs.personio.de/xml", """<?xml version="1.0" encoding="UTF-8"?><workzag-jobs><position><id>501</id><office>Zug</office>
        <department>Investments</department><name>Praktikant Private Equity (m/w/d)</name><employmentType>intern</employmentType><schedule>full-time</schedule>
        <seniority>student</seniority><createdAt>2026-11-05T10:00:00+01:00</createdAt><jobDescriptions><jobDescription><name>Aufgaben</name>
        <value><![CDATA[<p>Sie unterstützen das Team bei der Analyse von Unternehmen und der Erstellung von Präsentationen für das Investmentkomitee. Wir bieten ein Umfeld mit flachen Hierarchien und der Möglichkeit, Verantwortung zu übernehmen.</p>]]></value>
        </jobDescription></jobDescriptions></position></workzag-jobs>""")
    summary = pipeline.run_update(settings)
    assert summary["sources_ok"] == 5 and summary["errors"] == []
    by = {j["source_type"]: j for j in jobs()}
    assert set(by) == {"lever", "ashby", "recruitee", "workable", "personio"}
    assert by["lever"]["apply_url"].endswith("/abc-1/apply") and by["lever"]["german_flag"] == "REQUIRED" and "CHF" in by["lever"]["salary"]
    assert by["lever"]["city"] == "Zurich" and len(by["lever"]["locations"]) == 2
    assert by["ashby"]["city"] == "Milan" and by["ashby"]["seniority"] == "Graduate Programme"        # best-priority location wins
    assert by["recruitee"]["city"] == "Milan" and by["recruitee"]["seniority"] == "Internship" and by["recruitee"]["published"] == "2026-11-03"
    assert by["workable"]["sector"] == "Equity Research" and by["workable"]["city"] == "Geneva"
    assert by["personio"]["german_flag"] == "REQUIRED" and by["personio"]["apply_url"] == "https://persco.jobs.personio.de/job/501"
    assert len(jobs()) == 5                                                                           # unlisted Ashby role skipped


def test_workday_and_smartrecruiters_fetch_detail_pages_once(data, replay, settings):
    add_company("Workday Co", ats="workday", params={"host": "wdco.wd3.myworkdayjobs.com", "tenant": "wdco", "site": "Careers"})
    base = "https://wdco.wd3.myworkdayjobs.com/wday/cxs/wdco/Careers"
    body = lambda off: json.dumps({"appliedFacets": {}, "limit": 20, "offset": off, "searchText": ""}, sort_keys=True)  # noqa: E731
    listing = {"total": 3, "jobPostings": [
        {"title": "Off-Cycle Analyst, M&A", "externalPath": "/job/Zurich/Off-Cycle-Analyst_R-100", "locationsText": "2 Locations", "postedOn": "Posted 3 Days Ago", "bulletFields": ["R-100"]},
        {"title": "Senior Director, Tax", "externalPath": "/job/Zurich/Director_R-101", "locationsText": "Zurich", "bulletFields": ["R-101"]},
        {"title": "Software Engineer", "externalPath": "/job/London/SWE_R-102", "locationsText": "London", "bulletFields": ["R-102"]}]}
    replay(f"POST {base}/jobs {body(0)}", listing)
    replay(f"GET {base}/job/Zurich/Off-Cycle-Analyst_R-100", {"jobPostingInfo": {
        "title": "Off-Cycle Analyst, M&A", "jobDescription": f"<p>{LONG} Application deadline: 30 November 2026.</p>", "location": "Zurich", "additionalLocations": ["Geneva"],
        "startDate": "2026-11-01", "timeType": "Full time", "jobReqId": "R-100", "country": {"descriptor": "Switzerland"},
        "externalUrl": "https://wdco.wd3.myworkdayjobs.com/Careers/job/Zurich/Off-Cycle-Analyst_R-100"}})
    summary = pipeline.run_update(settings)
    assert summary["errors"] == []
    (job,) = jobs()                                      # the director and the engineer never trigger a detail request
    assert job["city"] == "Zurich" and len(job["locations"]) == 2 and job["published"] == "2026-11-01"
    assert job["deadline"] == "2026-11-30" and job["deadline_source"] == "stated in the description"
    assert job["seniority"] == "Off-cycle" and job["apply_url"].endswith("Off-Cycle-Analyst_R-100")
    # second run: the detail page is NOT in the replay any more, yet nothing changes ("2 Locations" must not overwrite Zurich)
    idx = json.loads((replay.dir / "index.json").read_text())
    idx.pop(f"GET {base}/job/Zurich/Off-Cycle-Analyst_R-100")
    (replay.dir / "index.json").write_text(json.dumps(idx))
    summary = pipeline.run_update(settings)
    assert summary["modified"] == 0 and summary["errors"] == []
    assert jobs()[0]["city"] == "Zurich" and jobs()[0]["deadline"] == "2026-11-30"


def test_generic_career_site_reads_only_structured_data(data, replay, settings):
    cid = add_company("Jsonld Co", category="Boutique IB", url="https://jsonld.example/careers")
    s = load_json(sources.SOURCES_FILE, {"schema": 1, "sources": []})
    s["sources"].append(sources.blank_source("s-jsonld-site", cid, "career_site", ats="jsonld", url="https://jsonld.example/careers", method="jsonld", status="unverified"))
    save_json(sources.SOURCES_FILE, s)
    replay("GET https://jsonld.example/careers", '<html><a href="/careers/analyst-intern">Analyst Intern</a><a href="/about">About</a><a href="/careers/team">Our team</a></html>')
    posting = {"@context": "https://schema.org", "@type": "JobPosting", "title": "M&A Analyst Intern", "datePosted": "2026-11-06", "validThrough": "2026-12-15T23:59",
               "employmentType": "INTERN", "identifier": {"@type": "PropertyValue", "value": "JL-9"}, "description": f"<p>{LONG}</p>",
               "jobLocation": {"@type": "Place", "address": {"addressLocality": "Milano", "addressCountry": "IT"}},
               "baseSalary": {"@type": "MonetaryAmount", "currency": "EUR", "value": {"@type": "QuantitativeValue", "value": 1200, "unitText": "MONTH"}}}
    replay("GET https://jsonld.example/careers/analyst-intern", f'<html><script type="application/ld+json">{json.dumps(posting)}</script></html>')
    replay("GET https://jsonld.example/careers/team", "<html><h1>Our team: analysts wanted, apply now!</h1></html>")   # prose is never turned into a posting
    pipeline.run_update(settings)
    (job,) = jobs()
    assert job["title"] == "M&A Analyst Intern" and job["city"] == "Milan" and job["deadline"] == "2026-12-15" and job["deadline_source"] == "source field"
    assert job["salary"] == "1200 EUR per month" and job["apply_url"] == "https://jsonld.example/careers/analyst-intern"


# ---------------------------------------------------------------- ATS identification
def test_ats_detection_from_page_markup():
    html = ('<a href="https://boards.greenhouse.io/acmecap/jobs/123">Apply</a><iframe src="https://jobs.lever.co/acme-eu"></iframe>'
            '<a href="https://acme.wd3.myworkdayjobs.com/en-US/External_Careers/job/x">x</a><a href="https://jobs.smartrecruiters.com/AcmeGroup/1">y</a>'
            '<a href="https://acme.jobs.personio.de/job/1">z</a><a href="https://jobs.ashbyhq.com/acme">a</a><a href="https://acme.taleo.net/careersection">t</a>'
            '<a href="https://hcm.fa.em2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/requisitions">o</a>')
    found = {d["ats"]: d["params"] for d in detect_ats(html, "https://acme.example/careers")}
    assert found["greenhouse"] == {"token": "acmecap"} and found["lever"] == {"token": "acme-eu"}
    assert found["workday"] == {"host": "acme.wd3.myworkdayjobs.com", "tenant": "acme", "site": "External_Careers"}
    assert found["smartrecruiters"] == {"token": "AcmeGroup"} and found["personio"] == {"token": "acme", "tld": "de"}
    assert found["oracle"] == {"host": "hcm.fa.em2.oraclecloud.com", "site": "CX_1001"} and "taleo" in found and "ashby" in found
    assert detect_ats("<p>We use greenhouse gases responsibly.</p>", "https://x.example") == []
    sf = detect_ats('<a class="jobTitle-link" href="/job/x/123456/">x</a>', "https://jobs.bank.example/search/")
    assert sf[0]["ats"] == "successfactors" and sf[0]["params"] == {"base_url": "https://jobs.bank.example"}


def test_discovery_registers_what_the_career_page_proves(data, excel, replay, settings):
    companies.import_excel(excel, settings)
    comps = load_json(companies.COMPANIES_FILE)["companies"]
    sources.sync_sources(comps)
    replay("GET https://alpha.example/careers", '<html><a href="/careers/open">Open positions</a></html>')
    replay("GET https://alpha.example/careers/open", '<html><a href="https://job-boards.eu.greenhouse.io/alphacap/jobs/1">Analyst</a></html>')
    replay("GET https://beta.example/jobs", '<html><a href="https://beta.taleo.net/careersection/2/jobsearch.ftl">Search jobs</a></html>')
    replay("GET https://delta.example", "<html><p>Boutique advisory firm.</p></html>")
    src_db = sources.load_sources()
    stats = discovery.run_discovery(comps, src_db, settings, limit=50)
    by = {s["id"]: s for s in src_db["sources"]}
    assert stats["analysed"] == 3 and stats["ats_found"] == 1
    new = by["s-alpha-capital-greenhouse-alphacap"]
    assert new["ats"] == "greenhouse" and new["params"] == {"token": "alphacap", "region": "eu"} and new["status"] == "unverified"
    assert "alpha.example/careers/open" in new["evidence"]
    assert by["s-alpha-capital-site"]["status"] == "resolved"
    assert by["s-beta-bank-site"]["status"] == "unsupported" and by["s-beta-bank-site"]["ats"] == "taleo"   # detected, honest about no connector
    assert by["s-delta-advisory-site"]["status"] == "no_structured_data"
    assert by["s-gamma-trustee-site"]["status"] == "no_portal_known"                                        # untouched


def test_unreachable_career_page_is_a_failure_not_an_empty_board(data, excel, replay, settings):
    companies.import_excel(excel, settings)
    comps = load_json(companies.COMPANIES_FILE)["companies"]
    sources.sync_sources(comps)
    src_db = sources.load_sources()
    discovery.run_discovery(comps, src_db, settings, only_company="Alpha")
    s = next(x for x in src_db["sources"] if x["id"] == "s-alpha-capital-site")
    assert s["status"] == "unreachable" and s["last_error"] and s["consecutive_failures"] == 1
    assert sources.company_monitoring_status([s]) == "unreachable"


# ---------------------------------------------------------------- dedupe
def test_same_role_from_two_sources_becomes_one_record(data, replay, settings):
    add_company("Alpha Capital", ats="greenhouse", params={"token": "alpha"})
    replay(GH_URL, gh_payload((1, "Private Equity Analyst Intern", "Zurich, Switzerland", "")))
    save_json(pipeline.MANUAL_FILE, {"jobs": [{"company": "Alpha Capital", "title": "Private Equity Analyst Intern", "location": "Zurich",
                                               "url": "https://www.linkedin.com/jobs/view/999"}]})
    summary = pipeline.run_update(settings)
    (job,) = jobs()
    assert summary["merged"] == 1 and len(job["sources"]) == 2 and job["verification"] == "VERIFIED OFFICIAL"
    assert job["apply_url"].startswith("https://boards.greenhouse.io/")          # the employer's link is kept, not LinkedIn's
    assert len(job["aliases"]) == 1
    pipeline.run_update(settings)                                                # the merged duplicate is not re-created
    assert len(jobs()) == 1 and len(jobs()[0]["sources"]) == 2


def test_linkedin_only_posting_is_labelled(data, settings):
    add_company("Alpha Capital")
    save_json(pipeline.MANUAL_FILE, {"jobs": [{"company": "Alpha Capital", "title": "Off-Cycle Analyst", "location": "Lugano",
                                               "url": "https://www.linkedin.com/jobs/view/123"}]})
    pipeline.run_update(settings)
    (job,) = jobs()
    assert job["verification"] == "LINKEDIN ONLY" and job["city"] == "Lugano"
    assert any("LINKEDIN ONLY" in m for m in job["score_detail"]["missing"])


# ---------------------------------------------------------------- status logic and failures
def test_job_lifecycle_new_modified_removed_reopened(data, replay, settings):
    add_company("Alpha Capital", ats="greenhouse", params={"token": "alpha"})
    replay(GH_URL, gh_payload((1, "Private Equity Intern", "Zurich", ""), (2, "Summer Analyst 2027", "Lugano", "")))
    assert pipeline.run_update(settings)["new"] == 2
    first = {j["external_id"]: j["first_detected"] for j in jobs()}
    replay(GH_URL, gh_payload((1, "Private Equity Intern", "Geneva", ""), (2, "Summer Analyst 2027", "Lugano", "")))   # location changed
    s = pipeline.run_update(settings)
    assert (s["new"], s["modified"]) == (0, 1)
    j1 = next(j for j in jobs() if j["external_id"] == "1")
    assert j1["city"] == "Geneva" and j1["last_meaningful_change"]["fields"] == ["city"] and j1["first_detected"] == first["1"]
    replay(GH_URL, gh_payload((2, "Summer Analyst 2027", "Lugano", "")))        # job 1 disappears
    pipeline.run_update(settings)
    assert next(j for j in jobs() if j["external_id"] == "1")["status"] == "Open"          # one miss is not enough
    assert pipeline.run_update(settings)["removed"] == 1
    gone = next(j for j in jobs() if j["external_id"] == "1")
    assert gone["status"] == "Removed" and gone["closed_at"] and len(jobs()) == 2          # history kept
    replay(GH_URL, gh_payload((1, "Private Equity Intern", "Geneva", ""), (2, "Summer Analyst 2027", "Lugano", "")))
    pipeline.run_update(settings)
    assert next(j for j in jobs() if j["external_id"] == "1")["status"] == "Open"
    types = [e["type"] for e in load_json(companies.HISTORY_FILE)["events"]]
    assert {"job_new", "job_modified", "job_removed", "job_reopened"} <= set(types)


def test_source_failure_never_expires_jobs(data, replay, settings):
    add_company("Alpha Capital", ats="greenhouse", params={"token": "alpha"})
    replay(GH_URL, gh_payload((1, "Private Equity Intern", "Zurich", "")))
    pipeline.run_update(settings)
    replay(GH_URL, "Service Unavailable", status=503)
    for n in (1, 2):
        s = pipeline.run_update(settings)
        assert s["sources_failed"] == 1 and s["errors"][0]["company"] == "Alpha Capital"
        assert jobs()[0]["status"] == "Open" and jobs()[0]["verification_failures"] == n
    pipeline.run_update(settings)
    assert jobs()[0]["status"] == "Verification Failed" and "may still be open" in jobs()[0]["status_note"]
    src = load_json(sources.SOURCES_FILE)["sources"][0]
    assert src["status"] == "error" and src["consecutive_failures"] == 3 and "503" in src["last_error"] and src["last_success"]
    meta = load_json(pipeline.META_FILE)
    assert meta["coverage"]["failed"] == 1 and meta["coverage"]["monitored"] == 0
    replay(GH_URL, gh_payload((1, "Private Equity Intern", "Zurich", "")))
    pipeline.run_update(settings)
    assert jobs()[0]["status"] == "Open" and jobs()[0]["verification_failures"] == 0


def test_one_broken_source_does_not_stop_the_others(data, replay, settings, monkeypatch):
    add_company("Alpha Capital", ats="greenhouse", params={"token": "alpha"})
    add_company("Broken Co", ats="lever", params={"token": "broken"})
    add_company("Garbage Co", ats="ashby", params={"token": "garbage"})
    replay(GH_URL, gh_payload((1, "Private Equity Intern", "Zurich", "")))
    replay("GET https://api.ashbyhq.com/posting-api/job-board/garbage?includeCompensation=true", "<html>not json</html>")
    s = pipeline.run_update(settings)
    assert s["sources_ok"] == 1 and s["sources_failed"] == 2 and len(jobs()) == 1
    assert {e["company"] for e in s["errors"]} == {"Broken Co", "Garbage Co"}
    meta = load_json(pipeline.META_FILE)
    assert meta["last_successful_update"] and meta["totals"]["jobs_active"] == 1


def test_empty_board_is_monitored_with_no_vacancies_not_a_failure(data, replay, settings):
    add_company("Alpha Capital", ats="greenhouse", params={"token": "alpha"})
    replay(GH_URL, {"jobs": []})
    s = pipeline.run_update(settings)
    src = load_json(sources.SOURCES_FILE)["sources"][0]
    assert s["sources_ok"] == 1 and src["status"] == "ok" and src["jobs_found"] == 0
    meta = load_json(pipeline.META_FILE)
    assert meta["coverage"]["monitored"] == 1 and meta["totals"]["monitored_without_jobs"] == 1


def test_deadline_drives_closing_soon_and_expired(settings):
    from datetime import timedelta
    from fcip.util import today
    mk = lambda d: {"deadline": (today() + timedelta(days=d)).isoformat()}  # noqa: E731
    assert pipeline.compute_status(mk(30), settings)[0] == "Open"
    assert pipeline.compute_status(mk(5), settings)[0] == "Closing Soon"
    assert pipeline.compute_status(mk(0), settings)[0] == "Closing Soon"
    assert pipeline.compute_status(mk(-1), settings)[0] == "Expired"
    assert pipeline.compute_status({"deadline": None, "future_window_note": "Applications open in January"}, settings)[0] == "Future Application Window"
    assert pipeline.compute_status({"deadline": None}, settings)[0] == "Open"


def test_pending_and_rejected_companies_are_not_monitored(data, replay, settings):
    add_company("Pending Co", ats="greenhouse", params={"token": "alpha"}, status="pending_review", origin="additional")
    replay(GH_URL, gh_payload((1, "Private Equity Intern", "Zurich", "")))
    s = pipeline.run_update(settings)
    assert s["sources_attempted"] == 0 and jobs() == []
    companies.set_company_status("c-pending-co", "active")
    assert pipeline.run_update(settings)["new"] == 1 and jobs()[0]["company_origin"] == "Additional"


def test_aggregator_proposes_unknown_employers_for_review(data, settings, monkeypatch):
    from connectors.aggregators import adzuna
    from connectors.base import raw_job
    add_company("Alpha Capital")
    def fake_search(http, settings, max_pages=1):
        a = raw_job("1", "M&A Analyst Intern", "https://adzuna.example/1", apply_url="https://adzuna.example/1", locations=["Zurich"], country_hint="Switzerland", description=LONG)
        a["company_name"] = "Alpha Capital AG"                       # known company, legal suffix differs
        b = raw_job("2", "Private Equity Summer Analyst", "https://adzuna.example/2", apply_url="https://adzuna.example/2", locations=["Lugano"], country_hint="Switzerland", description=LONG)
        b["company_name"] = "Newfound Partners"
        c = raw_job("3", "Warehouse Operative", "https://adzuna.example/3", locations=["Lugano"], country_hint="Switzerland")
        c["company_name"] = "Logistics SA"
        return [a, b, c]
    monkeypatch.setattr(adzuna, "enabled", lambda: True)
    monkeypatch.setattr(adzuna, "search", fake_search)
    s = pipeline.run_update(settings)
    assert s["aggregators"]["adzuna"] == {"listed": 3, "matched_known": 1, "proposed_companies": 1, "stored": 2}
    comps = {c["name"]: c for c in load_json(companies.COMPANIES_FILE)["companies"]}
    new = comps["Newfound Partners"]
    assert new["origin"] == "additional" and new["status"] == "pending_review" and "Adzuna" in new["reason_for_inclusion"]
    assert "Logistics SA" not in comps
    assert all(j["verification"] == "AGGREGATOR ONLY" for j in jobs()) and len(jobs()) == 2


def test_url_verification_is_conservative(data, settings, monkeypatch):
    """verify_jobs.py: only an explicit 404/410, twice in a row, closes a posting; errors never do."""
    import http.server
    import threading
    from conftest import load_script

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response({"/ok": 200, "/gone": 404, "/busy": 503}.get(self.path, 404))
            self.end_headers()

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    mk = lambda i, path: {"id": f"j-{i}", "company_id": "c-x", "title": f"T{i}", "status": "Open", "verification": "LINKEDIN ONLY",  # noqa: E731
                          "apply_url": base + path, "deadline": None, "sources": []}
    save_json(pipeline.JOBS_FILE, {"jobs": [mk(1, "/ok"), mk(2, "/gone"), mk(3, "/busy")]})
    verify = load_script("verify_jobs")
    monkeypatch.setitem(settings["collection"], "min_seconds_between_requests_per_host", 0)
    monkeypatch.setattr(verify, "load_settings", lambda: settings)
    verify.main([])
    st = {j["id"]: j for j in jobs()}
    assert st["j-1"]["status"] == "Open" and st["j-2"]["status"] == "Open" and st["j-3"]["verification_failures"] == 1
    verify.main([])
    st = {j["id"]: j for j in jobs()}
    assert st["j-2"]["status"] == "Removed" and "two consecutive checks" in st["j-2"]["status_note"]
    assert st["j-3"]["status"] == "Open" and st["j-1"]["url_gone_checks"] == 0
    srv.shutdown()
