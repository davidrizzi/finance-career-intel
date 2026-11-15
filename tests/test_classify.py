"""Acceptance tests 8-9-10-11: languages, German/French flags, scoring, geography, classification."""
import pytest

from fcip import classify, geo, scoring
from fcip.languages import analyze_languages

PAD = " You will build financial models, prepare presentations and support the team on live transactions every day."


@pytest.mark.parametrize("text,german,french", [
    ("Requirements: fluent in English and German (C1), French is a plus." + PAD, "REQUIRED", "PREFERRED"),
    ("Fluent Italian and English required; knowledge of German would be an advantage." + PAD, "PREFERRED", "NOT MENTIONED"),
    ("Languages: English, French. German not required." + PAD, "NOT REQUIRED", "REQUIRED"),
    ("Excellent written and spoken English is essential. Our team covers the German market and French clients." + PAD, "NOT MENTIONED", "NOT MENTIONED"),
    ("Strong Excel skills and an interest in private markets are expected from the successful candidate." + PAD, "NOT MENTIONED", "NOT MENTIONED"),
    ("Sehr gute Deutsch- und Englischkenntnisse. Sie unterstützen das Team bei der Analyse und wir bieten ein spannendes Umfeld mit der Möglichkeit, Verantwortung zu übernehmen und sich zu entwickeln, sowie flache Hierarchien für Ihre Karriere bei uns im Team.", "REQUIRED", "NOT MENTIONED"),
    ("Maîtrise du français et de l'anglais indispensable, l'allemand est un atout. Vous rejoignez notre équipe pour analyser des sociétés et vous préparez des présentations pour les clients de la banque dans le cadre de nos mandats.", "PREFERRED", "REQUIRED"),
])
def test_language_flags(text, german, french):
    r = analyze_languages(text)
    assert (r["german_flag"], r["french_flag"]) == (german, french)


def test_language_levels_and_evidence_are_recorded():
    r = analyze_languages("You are fluent in English (C1) and have German at B2 level; Italian is a plus." + PAD)
    by = {l["language"]: l for l in r["languages"]}
    assert by["English"]["level"] == "C1" and by["German"]["level"] == "B2"
    assert by["German"]["requirement"] == "required" and by["Italian"]["requirement"] == "preferred"
    assert "German at B2" in by["German"]["evidence"]


def test_posting_written_in_german_flags_german_even_if_not_named():
    text = ("Wir suchen einen Praktikanten für unser Team in Zürich. Sie unterstützen das Team bei der Analyse von Unternehmen "
            "und der Erstellung von Präsentationen. Sie haben ein Studium der Wirtschaftswissenschaften und wir bieten ein Umfeld mit flachen Hierarchien.")
    r = analyze_languages(text)
    assert r["description_language"] == "de" and r["german_flag"] == "REQUIRED"
    assert any("written in German" in n for n in r["notes"])


def test_no_description_means_unverified_not_english_only():
    r = analyze_languages("")
    assert r["analysed"] is False and r["german_flag"] == "NOT MENTIONED" and r["notes"]


@pytest.mark.parametrize("title,category,sector,relevant", [
    ("M&A Analyst Intern", "Boutique IB", "Mergers & Acquisitions", True),
    ("Summer Analyst 2027", "PE", "Private Equity", True),                      # inferred from company category
    ("Private Equity Internship", "Altro", "Private Equity", True),
    ("Junior Portfolio Manager", "Asset Manager", "Portfolio Management", True),
    ("Software Engineer Intern", "Hedge Fund", None, False),
    ("HR Business Partner", "Banca privata", None, False),
    ("Quantitative Developer Intern", "Hedge Fund", "Quantitative Finance", True),
    ("Receptionist", "PE", None, False),
    ("Stagista Corporate Finance", "Boutique IB", "Corporate Finance", True),
    ("Praktikant Wealth Management", "Banca privata", "Wealth Management", True),
    ("Copywriting Analyst", "Consulenza", None, False),
    ("Business Advisory Associate", "Consulenza", None, False),
    ("Transaction Services Analyst", "Consulenza", "Transaction Services", True),
    ("Relationship Banker - Wickenburg Branch", "Bulge Bracket", None, False),
])
def test_sector_classification(title, category, sector, relevant):
    r = classify.classify_sector(title, "", "", category)
    assert (r["sector"], r["relevant"]) == (sector, relevant)


@pytest.mark.parametrize("title,desc,seniority,include", [
    ("Summer Analyst 2027", "", "Summer Analyst", True),
    ("Off-Cycle Internship M&A", "", "Off-cycle", True),
    ("Graduate Analyst", "", "Graduate Programme", True),
    ("Werkstudent Corporate Finance", "", "Working Student", True),
    ("Stage - Analista M&A", "", "Internship", True),
    ("Early Stage Investment Analyst", "", "Junior / Analyst", True),           # 'stage' here is not an internship
    ("Vice President, M&A", "", "Experienced", False),
    ("Senior Analyst", "", "Experienced", False),
    ("Managing Director", "", "Experienced", False),
    ("Associate, Private Equity", "", "Ambiguous", True),                       # kept, with a warning
    ("Investment Analyst", "You have 5+ years of experience in private equity.", "Experienced", False),
    ("Investment Analyst", "1-2 years of experience in M&A is a plus.", "Junior / Analyst", True),
    ("Junior Associate", "", "Junior / Analyst", True),
    ("Head of Graduate Recruitment", "", "Graduate Programme", True),
    ("Product Manager - Global Banking Platform", "", "Experienced", False),
    ("Assistant Manager, Fund Accounting", "", "Ambiguous", True),
])
def test_seniority_classification(title, desc, seniority, include):
    r = classify.classify_seniority(title, desc)
    assert (r["seniority"], r["include"]) == (seniority, include)


def test_ambiguous_seniority_is_included_with_a_warning():
    r = classify.classify_seniority("Associate, Private Equity")
    assert r["include"] and "Associate" in r["warning"]


@pytest.mark.parametrize("text,expected", [
    ("Application deadline: 30 November 2026.", "2026-11-30"),
    ("Please apply by December 5, 2026", "2026-12-05"),
    ("Bewerbungsfrist: 15.01.2027", "2027-01-15"),
    ("Closing date 2027-02-01", "2027-02-01"),
    ("Applications close on 03/04/2027", None),             # could be 3 April or 4 March: not guessed
    ("We were founded on 12 March 1999 and met a deadline.", None),
    ("Start date: 1 March 2027", None),
])
def test_deadline_extraction_never_guesses(text, expected):
    assert classify.extract_deadline(text) == expected


def test_geography_normalisation_and_priority(settings):
    assert geo.normalize_city("Zurigo") == "Zurich" and geo.normalize_country("Svizzera") == "Switzerland"
    assert geo.parse_location("Baar, CH") == {"city": "Zug", "country": "Switzerland", "raw": "Baar, CH"}
    assert [x["city"] for x in geo.split_locations("London, Paris, Hong Kong")] == ["London", "Paris", "Hong Kong"]
    assert geo.parse_location("Springfield")["country"] is None            # unknown places are not coerced
    levels = {c: geo.geo_priority(c, k, settings) for c, k in [("Lugano", "Switzerland"), ("Milan", "Italy"), ("London", "United Kingdom"),
                                                               ("Bern", "Switzerland"), ("Rome", "Italy"), ("New York", "United States"), (None, None)]}
    assert levels == {"Lugano": "high", "Milan": "high", "London": "medium", "Bern": "swiss_other", "Rome": "target_country_other_city",
                      "New York": "other", None: "unknown"}


def _job(**kw):
    base = {"sector": "Mergers & Acquisitions", "sector_source": "title", "seniority": "Internship", "city": "Zurich", "country": "Switzerland",
            "contract_type": "Internship", "languages": [], "german_flag": "NOT MENTIONED", "french_flag": "NOT MENTIONED", "languages_analysed": True,
            "description": "MSc student in finance or economics. Strong Excel, valuation and financial modelling skills. " * 2,
            "published": "2026-11-01", "deadline": "2026-12-01", "verification": "VERIFIED OFFICIAL", "experience_min_years": None}
    base.update(kw)
    return base


def test_score_is_explained_and_bounded(settings):
    r = scoring.score_job(_job(), settings)
    assert 0 <= r["score"] <= 100 and set(r["breakdown"]) == {"sector", "seniority", "geography", "profile", "language", "contract"}
    assert round(sum(p["max"] for p in r["breakdown"].values())) == 100
    assert abs(sum(p["points"] for p in r["breakdown"].values()) - r["score"]) < 1
    assert r["positives"] and isinstance(r["negatives"], list) and isinstance(r["missing"], list)


def test_score_ordering_matches_the_brief(settings):
    s = lambda **kw: scoring.score_job(_job(**kw), settings)["score"]  # noqa: E731
    base = s()
    assert base > s(city="London", country="United Kingdom") > s(city="New York", country="United States")
    assert base > s(seniority="Ambiguous") and base > s(sector="Financial Consulting")
    german = [{"language": "German", "requirement": "required", "level": "C1", "evidence": "x"}]
    assert base > s(languages=german, german_flag="REQUIRED")
    assert s(experience_min_years=1) > s(experience_min_years=2, seniority="Junior / Analyst") > s(experience_min_years=4, seniority="Junior / Analyst")


def test_score_flags_missing_and_unverified_information(settings):
    r = scoring.score_job(_job(description="", deadline=None, published=None, verification="LINKEDIN ONLY", languages_analysed=False), settings)
    text = " ".join(r["missing"])
    assert "No job description" in text and "deadline" in text and "Publication date" in text and "LINKEDIN ONLY" in text


def test_weights_are_configurable(settings):
    import copy
    geo_heavy = copy.deepcopy(settings)
    geo_heavy["scoring"]["weights"] = {"sector": 5, "seniority": 5, "geography": 80, "profile": 5, "language": 0, "contract": 5}
    far = _job(city="New York", country="United States")
    assert scoring.score_job(far, geo_heavy)["score"] < scoring.score_job(far, settings)["score"]
    assert round(scoring.score_job(_job(), geo_heavy)["breakdown"]["geography"]["max"]) == 80


def test_keywords_match_whole_words_only(settings):
    r = scoring.score_job(_job(description="An excellent opportunity for an excellent communicator who writes clearly and listens actively in a busy team."), settings)
    assert not any("excel" in p.lower() and "skills" in p.lower() for p in r["positives"])


@pytest.mark.parametrize("title,desc,future", [
    ("CLOSED: Investment Group Internship (applications open December 15, 2099 – January 15, 2100)", "", True),
    ("Analyst", "Applications open on 1 March 2020 and close soon.", False),          # already open
    ("Analyst", "Applications open to all students in finance.", False),            # not a date
    ("Summer Analyst", "Applications will open in early 2099.", True),
])
def test_future_window_needs_a_date_still_ahead(title, desc, future):
    assert (classify.detect_future_window(title, desc) is not None) == future


def test_closed_title_marks_the_posting_expired(settings):
    from fcip import pipeline
    assert classify.CLOSED_TITLE_RX.search("CLOSED: Munich Internship") and not classify.CLOSED_TITLE_RX.search("Closed-end Fund Analyst")
    assert pipeline.compute_status({"title": "CLOSED: Munich Internship", "deadline": None}, settings)[0] == "Expired"
    assert pipeline.compute_status({"title": "Closed-end Fund Analyst", "deadline": None}, settings)[0] == "Open"
