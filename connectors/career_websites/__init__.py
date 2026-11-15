"""Generic connector for custom career websites.

Reads only what the employer publishes as schema.org JobPosting structured
data (JSON-LD), on the career page itself and on up to MAX_PAGES job pages
linked from it. No heuristics on free HTML: a page without structured data
yields nothing and is reported as 'not machine-readable', so no posting is
ever invented from a navigation link.
"""
import json
import re
from urllib.parse import urljoin, urlparse

from connectors.base import raw_job
from fcip.util import SourceError, short_hash

NAME = "jsonld"
NEEDS_DETAIL = False
MAX_PAGES = 25
JOB_LINK_RX = re.compile(r"/(jobs?|careers?|karriere|stellen|vacanc|opening|position|posizioni|offene|emploi|offres?|"
                         r"lavora|opportunit|requisition|posting)[^\s\"'#]*", re.I)


def extract_jobpostings(html: str) -> list[dict]:
    out = []
    for m in re.finditer(r"<script[^>]+application/ld\+json[^>]*>(.*?)</script>", html or "", re.I | re.S):
        try:
            data = json.loads(m.group(1).strip())
        except ValueError:
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, dict):
                t = node.get("@type")
                if t == "JobPosting" or (isinstance(t, list) and "JobPosting" in t):
                    out.append(node)
                stack.extend(v for k, v in node.items() if k in ("@graph", "itemListElement", "item", "mainEntity"))
    return out


def _locations(jp: dict) -> tuple[list[str], str | None]:
    locs, country = [], None
    jl = jp.get("jobLocation") or []
    for loc in jl if isinstance(jl, list) else [jl]:
        addr = (loc or {}).get("address") if isinstance(loc, dict) else None
        if isinstance(addr, dict):
            c = addr.get("addressCountry")
            c = c.get("name") if isinstance(c, dict) else c
            label = ", ".join(str(x) for x in (addr.get("addressLocality"), addr.get("addressRegion"), c) if x)
            if label:
                locs.append(label)
            country = country or c
        elif isinstance(addr, str):
            locs.append(addr)
    return locs, country


def to_raw(jp: dict, page_url: str) -> dict | None:
    title = jp.get("title") or jp.get("name")
    if not title:
        return None
    url = jp.get("url") or page_url
    ident = jp.get("identifier")
    ident = ident.get("value") if isinstance(ident, dict) else ident
    locs, country = _locations(jp)
    salary = None
    bs = jp.get("baseSalary")
    if isinstance(bs, dict):
        v = bs.get("value")
        if isinstance(v, dict) and (v.get("value") or v.get("minValue")):
            amount = v.get("value") or f"{v.get('minValue')}-{v.get('maxValue')}"
            salary = f"{amount} {bs.get('currency', '')} {('per ' + v['unitText'].lower()) if v.get('unitText') else ''}".strip()
    et = jp.get("employmentType")
    return raw_job(ident or short_hash(url, title), title, urljoin(page_url, url), apply_url=urljoin(page_url, url),
                   locations=locs, country_hint=country, description=jp.get("description"),
                   published=jp.get("datePosted"), deadline=jp.get("validThrough"),
                   employment_type=", ".join(et) if isinstance(et, list) else et, salary=salary)


def list_jobs(source, http, settings):
    start = source["url"]
    html, final = http.fetch_page(start)
    found: dict[str, dict] = {}
    for jp in extract_jobpostings(html):
        raw = to_raw(jp, final)
        if raw:
            found[raw["url"]] = raw
    host = urlparse(final).netloc
    links = []
    for href in re.findall(r"href=[\"']([^\"'#]+)[\"']", html):
        full = urljoin(final, href)
        if urlparse(full).netloc == host and JOB_LINK_RX.search(urlparse(full).path) and full.rstrip("/") != final.rstrip("/"):
            if full not in links:
                links.append(full)
    # deeper paths first: they are the individual vacancy pages
    links.sort(key=lambda u: -urlparse(u).path.count("/"))
    errors = 0
    max_pages = source.get("_max_pages", MAX_PAGES)
    for link in links[:max_pages]:
        try:
            page, page_final = http.fetch_page(link)
        except SourceError:
            errors += 1
            continue
        for jp in extract_jobpostings(page):
            raw = to_raw(jp, page_final)
            if raw:
                found.setdefault(raw["url"], raw)
    if not found and links and errors == len(links[:max_pages]):
        raise SourceError(f"career site: every linked job page failed to load ({errors})")
    return list(found.values())
