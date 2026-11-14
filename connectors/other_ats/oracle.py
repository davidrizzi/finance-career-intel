"""Oracle Recruiting Cloud candidate-experience REST resources (used by the public career site).

params: host (e.g. xxxx.fa.em2.oraclecloud.com), site (e.g. CX_1001)
"""
from urllib.parse import quote

from connectors.base import raw_job
from fcip.util import SourceError

NAME = "oracle"
NEEDS_DETAIL = True
PAGE = 50
KEYWORDS = ["intern", "analyst", "graduate", "trainee", "summer", "off-cycle", "junior", "associate"]


def _list(http, p, keyword, offset):
    finder = (f"findReqs;siteNumber={p['site']},facetsList=LOCATIONS;TITLES;CATEGORIES;POSTING_DATES,"
              f"limit={PAGE},offset={offset},sortBy=POSTING_DATES_DESC")
    if keyword:
        finder += f",keyword={quote(chr(34) + keyword + chr(34))}"
    url = (f"https://{p['host']}/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
           f"?onlyData=true&expand=requisitionList.secondaryLocations&finder={finder}")
    data = http.get_json(url)
    items = (data or {}).get("items")
    if not items:
        raise SourceError(f"oracle: unexpected payload for {p['host']}/{p['site']}")
    return items[0]


def list_jobs(source, http, settings):
    p = source["params"]
    found = {}
    first = _list(http, p, "", 0)
    total = int(first.get("TotalJobsCount") or 0)
    plans = [""] if total <= 400 else KEYWORDS
    for kw in plans:
        offset = 0
        while offset < 400:
            block = first if (kw == "" and offset == 0) else _list(http, p, kw, offset)
            reqs = block.get("requisitionList") or []
            for r in reqs:
                rid = str(r.get("Id"))
                if rid in found:
                    continue
                locs = [r.get("PrimaryLocation")] + [s.get("Name") for s in r.get("secondaryLocations") or []]
                url = f"https://{p['host']}/hcmUI/CandidateExperience/en/sites/{p['site']}/job/{rid}"
                found[rid] = raw_job(rid, r.get("Title"), url, apply_url=url, locations=[l for l in locs if l],
                                     country_hint=r.get("PrimaryLocationCountry"), published=r.get("PostedDate"),
                                     description=r.get("ShortDescriptionStr"), detail_ref=rid)
            offset += PAGE
            if len(reqs) < PAGE:
                break
    return list(found.values())


def enrich(raw, source, http, settings):
    p = source["params"]
    finder = quote(f'ById;Id="{raw["detail_ref"]}",siteNumber={p["site"]}', safe=";=,")
    data = http.get_json(f"https://{p['host']}/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails"
                         f"?expand=all&onlyData=true&finder={finder}")
    items = (data or {}).get("items") or []
    if items:
        d = items[0]
        parts = [d.get("ExternalDescriptionStr"), d.get("ExternalResponsibilitiesStr"), d.get("ExternalQualificationsStr"),
                 d.get("CorporateDescriptionStr")]
        raw["description"] = "".join(x for x in parts if x) or raw.get("description")
        raw["employment_type"] = d.get("JobSchedule") or d.get("WorkerType")
        raw["deadline"] = d.get("ExternalPostedEndDate")
    return raw
