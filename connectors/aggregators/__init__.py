"""Third-party recruitment sources.

Automated: Adzuna (official API with a free developer key; optional).
Link-only: jobs.ch, Jobup.ch, eFinancialCareers, Indeed, Karriere.ch, JobRoom.
Those sites publish no free public API and their terms restrict automated
collection, so the platform builds search links for them instead of scraping.

Every posting that comes from here is labelled 'AGGREGATOR ONLY' until the
same role is confirmed on the employer's own portal.
"""
from urllib.parse import quote_plus

from . import adzuna  # noqa: F401

LINK_ONLY = {
    "jobs.ch": "https://www.jobs.ch/en/vacancies/?term={q}",
    "Jobup.ch": "https://www.jobup.ch/en/jobs/?term={q}",
    "eFinancialCareers": "https://www.efinancialcareers.com/jobs?q={q}",
    "Indeed": "https://www.indeed.com/jobs?q={q}",
    "Karriere.ch": "https://www.karriere.ch/jobs?q={q}",
    "JobRoom (SECO)": "https://www.job-room.ch/job-search?query-values={q}",
}


def search_links(company: str) -> dict[str, str]:
    q = quote_plus(company)
    return {name: tpl.format(q=q) for name, tpl in LINK_ONLY.items()}
