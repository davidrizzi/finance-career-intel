"""Recognise which recruitment system a career page uses, from its HTML and URL.

Detection is evidence based: an ATS is recorded only when the page itself
links to or embeds it. Nothing is guessed from the company name.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

_BAD_TOKENS = {"embed", "v1", "jobs", "job", "careers", "www", "api", "boards", "js", "static", "assets", "search",
               "cdn", "app", "apply", "help", "support", "docs", "blog", "info", "en", "de", "fr", "it"}

# (ats, regex, builder(match) -> params)
_PATTERNS = [
    ("greenhouse", r"(?:boards|job-boards)(\.eu)?\.greenhouse\.io/(?:embed/job_board(?:/js)?\?for=)?([A-Za-z0-9_]+)",
     lambda m: {"token": m.group(2), **({"region": "eu"} if m.group(1) else {})}),
    ("greenhouse", r"boards-api\.greenhouse\.io/v1/boards/([A-Za-z0-9_]+)", lambda m: {"token": m.group(1)}),
    ("lever", r"jobs\.(eu\.)?lever\.co/([A-Za-z0-9_.-]+)",
     lambda m: {"token": m.group(2), **({"region": "eu"} if m.group(1) else {})}),
    ("ashby", r"jobs\.ashbyhq\.com/([A-Za-z0-9_.%-]+)", lambda m: {"token": m.group(1)}),
    ("smartrecruiters", r"(?:jobs|careers)\.smartrecruiters\.com/(?:oneclick-ui/company/)?([A-Za-z0-9_-]+)",
     lambda m: {"token": m.group(1)}),
    ("workday", r"https?://([a-z0-9-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:wday/cxs/[^/]+/)?(?:[a-z]{2}-[A-Za-z]{2}/)?([A-Za-z0-9_-]+)",
     lambda m: {"host": f"{m.group(1)}.{m.group(2)}.myworkdayjobs.com", "tenant": m.group(1), "site": m.group(3)}),
    ("recruitee", r"https?://([a-z0-9-]+)\.recruitee\.com", lambda m: {"token": m.group(1)}),
    ("personio", r"https?://([a-z0-9-]+)\.jobs\.personio\.(de|com)", lambda m: {"token": m.group(1), "tld": m.group(2)}),
    ("workable", r"apply\.workable\.com/([a-z0-9-]+)", lambda m: {"token": m.group(1)}),
    ("oracle", r"https?://([a-z0-9.-]+\.oraclecloud\.com)/hcmUI/CandidateExperience/[a-zA-Z_-]+/sites/([A-Za-z0-9_-]+)",
     lambda m: {"host": m.group(1), "site": m.group(2)}),
    # detected but not collected automatically
    ("taleo", r"https?://([a-z0-9-]+)\.taleo\.net", lambda m: {"token": m.group(1)}),
    ("icims", r"https?://([a-z0-9-]+)\.icims\.com", lambda m: {"token": m.group(1)}),
    ("avature", r"https?://([a-z0-9-]+)\.avature\.net", lambda m: {"token": m.group(1)}),
    ("talnet", r"https?://([a-z0-9-]+)\.tal\.net", lambda m: {"token": m.group(1)}),
    ("umantis", r"https?://([a-z0-9-]+)\.umantis\.com", lambda m: {"token": m.group(1)}),
    ("refline", r"https?://[a-z0-9.-]*refline\.ch/(\d+)", lambda m: {"token": m.group(1)}),
    ("teamtailor", r"https?://([a-z0-9-]+)\.teamtailor\.com", lambda m: {"token": m.group(1)}),
    ("bamboohr", r"https?://([a-z0-9-]+)\.bamboohr\.com", lambda m: {"token": m.group(1)}),
    ("jobvite", r"jobs\.jobvite\.com/([A-Za-z0-9_-]+)", lambda m: {"token": m.group(1)}),
    ("softgarden", r"https?://([a-z0-9-]+)\.softgarden\.io", lambda m: {"token": m.group(1)}),
    ("prospective", r"https?://[a-z0-9.-]*prospective\.ch", lambda m: {}),
    ("dvinci", r"https?://([a-z0-9-]+)\.dvinci(?:-easy)?\.(?:com|de)", lambda m: {"token": m.group(1)}),
    ("phenom", r"cdn\.phenompeople\.com", lambda m: {}),
    ("eightfold", r"https?://([a-z0-9-]+)\.eightfold\.ai", lambda m: {"token": m.group(1)}),
    ("cornerstone", r"https?://([a-z0-9-]+)\.csod\.com", lambda m: {"token": m.group(1)}),
]
_RX = [(a, re.compile(rx, re.I), fn) for a, rx, fn in _PATTERNS]

_SF_RX = re.compile(r"career\d*\.successfactors\.(?:eu|com)|rmkcdn\.successfactors\.com|jobTitle-link|"
                    r"class=\"[^\"]*jobdescription|successfactors", re.I)
CAREER_LINK_RX = re.compile(r"career|karriere|jobs?\b|join[- ]us|work[- ]with[- ]us|working[- ]at|lavora[- ]con[- ]noi|carrier[ae]|"
                            r"opportunit|stellen|offene|emploi|recrutement|rejoignez|vacanc|talent|people", re.I)
VACANCY_LINK_RX = re.compile(r"open (positions|roles|vacancies)|current (vacancies|openings|opportunities)|"
                             r"(view|see|search|browse|all|explore) (all )?(open )?(jobs|roles|positions|vacancies|opportunities|openings)|"
                             r"job (search|openings|opportunities|board|portal)|offene stellen|stellenangebote|posizioni aperte|"
                             r"offerte di lavoro|offres d.emploi|postes ouverts|apply (now|here|online)|vacancies|"
                             r"students|graduates|early careers?|internships?", re.I)


def detect_ats(html: str, page_url: str = "") -> list[dict]:
    """All ATS fingerprints on a page: [{'ats','params','evidence'}], most specific first."""
    hay = f"{page_url}\n{html or ''}"
    out, seen = [], set()
    for ats, rx, build in _RX:
        for m in rx.finditer(hay):
            params = build(m)
            token = str(params.get("token") or params.get("site") or "").lower()
            if "token" in params and (token in _BAD_TOKENS or len(token) < 2):
                continue
            key = (ats, tuple(sorted(params.items())))
            if key in seen:
                continue
            seen.add(key)
            out.append({"ats": ats, "params": params, "evidence": m.group(0)[:160]})
    if not any(d["ats"] == "successfactors" for d in out) and _SF_RX.search(hay):
        host = urlparse(page_url)
        if re.search(r"jobTitle-link|rmkcdn", hay) and host.netloc:
            out.append({"ats": "successfactors", "params": {"base_url": f"{host.scheme}://{host.netloc}"},
                        "evidence": "SuccessFactors career-site markup on " + host.netloc})
        else:
            m = re.search(r"https?://([a-z0-9.-]+)/(?:search/?\?|job/)", hay)
            out.append({"ats": "successfactors", "params": {}, "evidence": "SuccessFactors reference on page",
                        "incomplete": True})
    return out


def find_links(html: str, page_url: str, rx: re.Pattern, limit: int = 4) -> list[str]:
    """Anchors whose text or href matches rx, same registrable site or a known ATS host."""
    out = []
    for m in re.finditer(r"<a\b[^>]*href=[\"']([^\"'#]+)[\"'][^>]*>(.*?)</a>", html or "", re.I | re.S):
        href, text = m.group(1), re.sub(r"<[^>]+>", " ", m.group(2))
        if href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        if rx.search(text) or rx.search(href):
            full = urljoin(page_url, href)
            if full not in out and full.rstrip("/") != page_url.rstrip("/"):
                out.append(full)
        if len(out) >= limit:
            break
    return out
