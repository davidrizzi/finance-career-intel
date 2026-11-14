"""Adzuna job-search API (official, free developer key).

Enabled only when ADZUNA_APP_ID and ADZUNA_APP_KEY are set (GitHub Secrets).
Covers Switzerland, Italy, United Kingdom and Australia; Luxembourg and the
UAE are not offered by Adzuna.

GET https://api.adzuna.com/v1/api/jobs/{country}/search/{page}
"""
import os
from urllib.parse import urlencode

from connectors.base import raw_job
from fcip.util import SourceError

NAME = "adzuna"
NEEDS_DETAIL = False
COUNTRIES = {"ch": "Switzerland", "it": "Italy", "gb": "United Kingdom", "au": "Australia"}
CITIES = {"ch": ["Lugano", "Zurich", "Zug", "Geneva"], "it": ["Milano"], "gb": ["London"],
          "au": ["Sydney", "Melbourne", "Perth"]}
WHAT_OR = "intern internship analyst graduate trainee stage praktikum junior"
WHAT_FIN = ["investment banking", "private equity", "M&A", "asset management", "corporate finance", "wealth management"]


def enabled() -> bool:
    return bool(os.environ.get("ADZUNA_APP_ID") and os.environ.get("ADZUNA_APP_KEY"))


def search(http, settings, max_pages: int = 1) -> list[dict]:
    """Return raw postings (with company name) across the target cities."""
    if not enabled():
        raise SourceError("adzuna: ADZUNA_APP_ID / ADZUNA_APP_KEY not configured")
    out, seen = [], set()
    for cc, cities in CITIES.items():
        for city in cities:
            for topic in WHAT_FIN:
                for page in range(1, max_pages + 1):
                    qs = urlencode({"app_id": os.environ["ADZUNA_APP_ID"], "app_key": os.environ["ADZUNA_APP_KEY"],
                                    "results_per_page": 50, "what": topic, "what_or": WHAT_OR, "where": city,
                                    "max_days_old": 30, "sort_by": "date", "content-type": "application/json"})
                    data = http.get_json(f"https://api.adzuna.com/v1/api/jobs/{cc}/search/{page}?{qs}")
                    results = (data or {}).get("results")
                    if results is None:
                        raise SourceError(f"adzuna: unexpected payload for {cc}/{city}")
                    for r in results:
                        if r["id"] in seen:
                            continue
                        seen.add(r["id"])
                        loc = (r.get("location") or {}).get("display_name")
                        salary = None
                        if r.get("salary_min") and str(r.get("salary_is_predicted", "0")) != "1":
                            salary = f"{r['salary_min']:,.0f}-{r.get('salary_max', r['salary_min']):,.0f} (as listed by Adzuna)"
                        job = raw_job(r["id"], r.get("title"), r.get("redirect_url"), apply_url=r.get("redirect_url"),
                                      locations=[loc] if loc else [city], country_hint=COUNTRIES[cc],
                                      description=r.get("description"), published=r.get("created"),
                                      employment_type=" ".join(x for x in (r.get("contract_time"), r.get("contract_type")) if x) or None,
                                      salary=salary)
                        job["company_name"] = (r.get("company") or {}).get("display_name")
                        out.append(job)
                    if len(results) < 50:
                        break
    return out
