"""SAP SuccessFactors career sites (Recruiting Marketing, 'RMK').

These sites share one HTML template: the search page lists vacancies as
<a class="jobTitle-link" href="/job/...">, with jobLocation / jobDate spans,
paged through &startrow=N. Job pages carry the description in
<span class="jobdescription">. No login, no API key: this is the public site.
"""
import re
from urllib.parse import urljoin

from connectors.base import raw_job
from fcip.util import SourceError

NAME = "successfactors"
NEEDS_DETAIL = True
PAGE = 25


def list_jobs(source, http, settings):
    from bs4 import BeautifulSoup

    base = source["params"]["base_url"].rstrip("/")
    locale = source["params"].get("locale")
    out, seen, start = [], set(), 0
    while start < 1500:
        url = f"{base}/search/?q=&sortColumn=referencedate&sortDirection=desc&startrow={start}"
        if locale:
            url += f"&locale={locale}"
        html, _ = http.fetch_page(url)
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select("a.jobTitle-link")
        if start == 0 and not links and not re.search(r"jobTitle|searchResults|noresults|no-results|keine|aucun|nessun", html, re.I):
            raise SourceError(f"successfactors: {base} did not return the expected search page")
        new = 0
        for a in links:
            href = a.get("href") or ""
            m = re.search(r"/(\d{6,})/?", href)
            ext = m.group(1) if m else href
            if not href or ext in seen:
                continue
            seen.add(ext)
            new += 1
            row = a.find_parent("tr") or a.find_parent("li") or a.parent
            loc = row.select_one(".jobLocation") if row else None
            dt = row.select_one(".jobDate") if row else None
            dept = row.select_one(".jobDepartment, .jobFacility") if row else None
            full = urljoin(base + "/", href)
            out.append(raw_job(ext, a.get_text(" ", strip=True), full, apply_url=full,
                               locations=[loc.get_text(" ", strip=True)] if loc else [],
                               published=dt.get_text(" ", strip=True) if dt else None,
                               department=dept.get_text(" ", strip=True) if dept else None, detail_ref=full))
        if new == 0 or len(links) < PAGE:
            break
        start += PAGE
    return out


def enrich(raw, source, http, settings):
    from bs4 import BeautifulSoup

    html, _ = http.fetch_page(raw["detail_ref"])
    soup = BeautifulSoup(html, "html.parser")
    node = soup.select_one(".jobdescription, [itemprop=description], .job-description, #job-description")
    if node:
        raw["description"] = str(node)
    meta = soup.select_one("meta[itemprop=datePosted]")
    if meta and meta.get("content"):
        raw["published"] = meta["content"]
    return raw
