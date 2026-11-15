"""Deterministic classification: sector, seniority, contract, experience, deadline, visa.

Everything here is rule based (no AI calls). Rules read the job title first and
the description second. When a rule cannot decide, the result says so
("Ambiguous", "Not specified") instead of guessing.
"""
from __future__ import annotations

import re
from datetime import date

from .util import norm_text, parse_date

# ------------------------------------------------------------------ sectors
# Order matters: the first rule that matches the title wins.
SECTOR_RULES: list[tuple[str, str]] = [
    ("Mergers & Acquisitions", r"\bm ?(&|and) ?a\b|mergers? (and|&) acquisitions?|fusioni e acquisizioni|fusions[- ]acquisitions"),
    ("Private Equity", r"private equity|buy-?outs?|growth equity|private markets?|private (debt|credit)|direct lending|"
                       r"infrastructure (invest|equity|fund)|secondaries|co-?invest|fund of funds|portfolio compan"),
    ("Venture Capital", r"venture capital|\bvc\b|\bventures?\b|early[- ]stage|seed (fund|invest)|start-?up invest"),
    ("Investment Banking", r"investment bank|\bibd\b|\becm\b|\bdcm\b|capital markets|leveraged finance|\blevfin\b|"
                           r"debt advisory|equity advisory|coverage|origination|banca d.affari|\bcib\b|"
                           r"corporate (&|and) investment bank|sponsor(s)? group|financial institutions group|\bfig\b|"
                           r"syndicate|structured finance|project finance"),
    ("Equity Research", r"equity research|sell[- ]side|research (analyst|associate).*(equit|stock)|analista equity"),
    ("Hedge Funds", r"hedge funds?|long[/ -]short|multi[- ]strateg|global macro|event[- ]driven|pod\b"),
    ("Quantitative Finance", r"\bquant|systematic|algorithmic|\btrad(er|ing)\b|derivatives?|structur(ing|ed products)|"
                             r"market[- ]mak|execution|volatility|pricing|financial engineer|risk (analytics|modell?ing)"),
    ("Portfolio Management", r"portfolio manage|gestione (di |dei )?portafogl|portfoliomanage|gestion de portefeuille|"
                             r"\bportfolio\b|asset allocation|multi[- ]asset|fixed income|\bequities\b|\bcredit\b"),
    ("Transaction Services", r"transaction (services|advisory|support|diligence)|due diligence|deal advisory|\bdeals\b|"
                             r"financial due|\btas\b|\bfdd\b"),
    ("Valuation", r"valuations?\b|valutazion|bewertung|\bmodell?ing\b|business modell?ing"),
    ("Corporate Finance", r"corporate finance|finanza (aziendale|straordinaria)|corporate development|"
                          r"corporate advisory|finance d.entreprise"),
    ("Financial Advisory", r"financial advis|restructuring|turnaround|special situations|strategic advis|"
                           r"debt (advis|restructur)|\badvisory\b|consulenza finanziaria"),
    ("Investment Research", r"investment research|credit research|macro(economic)? research|fund research|"
                            r"manager (research|selection)|\bresearch\b|ricerca|\bstrategist\b|investment strategy"),
    ("Family Offices", r"family office"),
    ("Wealth Management", r"wealth manage|private bank|relationship manage|client advis|gestione patrimoniale|"
                          r"verm.gensverwalt|gestion de fortune|private wealth|investment advis|consulente (finanziario|patrimoniale)|"
                          r"private client|\buhnw|\bhnw|kundenberat|wealth plann|investment counsel"),
    ("Alternative Investments", r"alternative invest|\balternatives\b|real estate (invest|private|fund|equity)|"
                                r"real assets|commodit|digital assets?|crypto"),
    ("Fund Management", r"fund manage|\bmanco\b|\baifm\b|fund (structuring|governance|oversight)|fondsmanage|gestion de fonds"),
    ("Asset Management", r"asset manage|\bsgr\b|gestione del risparmio|verm.gensverwaltung|institutional (clients|sales)|"
                         r"\betf\b|product specialist|investment solutions|investment (product|specialist)|sustainable invest|\besg\b"),
    ("Investment Management", r"investment manage|investment (analyst|associate|team|professional|intern|officer)|"
                              r"\binvestments?\b|analista (finanziario|investimenti)|anlage|investissement"),
    ("Financial Consulting", r"financial (services )?consult|strategy consult|management consult|"
                             r"consult(ant|ing).*(financ|bank|strateg)|strateg(y|ic) (analyst|associate)|business analyst"),
]
_SECTOR_RX = [(name, re.compile(rx, re.I)) for name, rx in SECTOR_RULES]

# Adjacent finance functions: kept (lower sector score) rather than dropped.
GENERAL_FINANCE_RX = re.compile(
    r"risk|treasury|fund (account|admin|operations|services)|middle office|back office|operations analyst|"
    r"financ(e|ial) (analyst|controller|planning|reporting|control)|\bfp&a\b|controlling|controller|"
    r"credit (analyst|officer|risk)|corporate banking|lending|loan|securities services|custody|depositary|"
    r"product control|client (services|onboarding)|business development|investor relations|sales|"
    r"\banalyst\b|\banalista\b|\banalyste\b|financ|bank|finanz|finanza", re.I)

# Functions outside the target sectors. A hit on the title drops the job
# unless the title also carries an unmistakable front-office finance signal.
NON_TARGET_RX = re.compile(
    r"software|developer|entwickler|sviluppatore|\bengineer|devops|\bsre\b|\bit\b|\bict\b|informati[ck]|"
    r"cyber|infosec|information security|network|system admin|help ?desk|service desk|cloud|data engineer|"
    r"\bux\b|\bui\b|designer|graphic|human resources|\bhr\b|recruit|talent acquisition|people (partner|operations)|"
    r"legal|lawyer|paralegal|counsel|jurist|avvocat|rechtsanw|attorney|company secretar|"
    r"marketing|communications|social media|content|brand|event(s)? (manager|coordinator)|"
    r"reception|office (manager|assistant|administrator)|executive assistant|personal assistant|\bpa\b|secretar|"
    r"segretari|assistenz|sekret|team assistant|administrative assistant|facilit|payroll|bookkeep|procurement|"
    r"customer (service|support|care)|client service representative|surveillance|call cent|"
    r"copywrit|supply chain|logistics|\bevents? (intern|assistant|executive|specialist|coordinator)|"
    r"health ?(&|and) ?benefits|personal insurance|insurance sales|claims|"
    r"\bbranch\b|teller|relationship banker|associate banker|daily banking|consumer banking|retail banking|"
    r"mortgage|product owner|scrum|chef\b|cook|driver|cleaner|housekeep|concierge|nurse|"
    r"compliance|\bkyc\b|\baml\b|financial crime|internal audit|\baudit|\btax\b|steuer|fiscal|"
    r"accountant|accounts (payable|receivable)|contabil|buchhalt|comptab", re.I)
STRONG_FINANCE_TITLE_RX = re.compile(
    r"\bquant|invest|m ?& ?a\b|private equity|corporate finance|trading|trader|portfolio|"
    r"equity research|valuation|transaction|capital markets|wealth|asset manage|fund manage", re.I)

CATEGORY_SECTOR = {
    "boutique ib": "Investment Banking", "bulge bracket": "Investment Banking", "pe": "Private Equity",
    "vc": "Venture Capital", "hedge fund": "Hedge Funds", "asset manager": "Asset Management",
    "sgr": "Asset Management", "family office": "Family Offices", "banca privata": "Wealth Management",
    "consulenza": "Financial Consulting", "big four": "Financial Advisory",
    "private equity": "Private Equity", "venture capital": "Venture Capital", "private bank": "Wealth Management",
    "boutique investment bank": "Investment Banking", "consulting": "Financial Consulting",
}


CONSULTING_CATEGORIES = {"consulenza", "consulting", "big four", "financial consulting"}
FINANCE_TITLE_RX = re.compile(
    r"financ|deal|transaction|valuation|m ?(&|and) ?a\b|merger|acquisition|banking|\bbank|capital|invest|"
    r"restructur|private equity|\bfund|wealth|asset|treasury|credit|corporate development|due diligence|"
    r"\bfs\b|insurance (&|and) asset|economic|strategy (&|and) transactions|turnaround", re.I)


def classify_sector(title: str, description: str = "", department: str = "", company_category: str = "") -> dict:
    """Return {'sector', 'source', 'relevant', 'reason'}.

    relevant=False means the role is outside the target sectors and is not stored.
    """
    title = title or ""
    head = f"{title} | {department or ''}"
    if norm_text(company_category) in CONSULTING_CATEGORIES and not FINANCE_TITLE_RX.search(head) \
            and not STRONG_FINANCE_TITLE_RX.search(title):
        # consulting and audit firms hire for every industry: keep only finance practices
        return {"sector": None, "source": "title", "relevant": False,
                "reason": "consulting role without a finance practice in the title"}
    non_target = NON_TARGET_RX.search(title)
    strong = STRONG_FINANCE_TITLE_RX.search(title)
    if non_target and not strong:
        return {"sector": None, "source": "title", "relevant": False,
                "reason": f"non-target function ('{non_target.group(0).strip()}')"}
    for name, rx in _SECTOR_RX:
        if rx.search(title):
            return {"sector": name, "source": "title", "relevant": True, "reason": None}
    for name, rx in _SECTOR_RX:
        if department and rx.search(department):
            return {"sector": name, "source": "department", "relevant": True, "reason": None}
    intro = (description or "")[:1500]
    hits = [(len(rx.findall(intro)), name) for name, rx in _SECTOR_RX]
    best = max(hits, default=(0, None))
    if best[0] >= 2:
        return {"sector": best[1], "source": "description", "relevant": True, "reason": None}
    cat = CATEGORY_SECTOR.get(norm_text(company_category))
    if GENERAL_FINANCE_RX.search(head):
        if cat and re.search(r"\banal[iy]st|\bintern|stage|trainee|graduate|praktik|associate", head, re.I):
            return {"sector": cat, "source": "company category", "relevant": True,
                    "reason": "sector inferred from the company's category, not stated in the posting"}
        return {"sector": "Finance (general)", "source": "title", "relevant": True, "reason": None}
    if cat and re.search(r"\bintern|stage\b|stagiaire|trainee|graduate|praktik|tirocin|working student|werkstudent",
                         head, re.I):
        return {"sector": cat, "source": "company category", "relevant": True,
                "reason": "sector inferred from the company's category, not stated in the posting"}
    return {"sector": None, "source": None, "relevant": False, "reason": "no target-sector signal in title or description"}


# ------------------------------------------------------------------ seniority
_SENIOR_RX = re.compile(
    r"\b(senior|sr|director|vice[- ]president|vp|svp|evp|avp|managing director|md|head|chief|principal|partner|"
    r"lead|executive director|leiter(in)?|responsabile|direttore|directeur|directrice|teamleiter|experienced|"
    r"expert|specialist senior|c[efo]o)\b", re.I)
_MANAGER_RX = re.compile(r"\b(manager|gestore|g[ée]rant|gestionnaire)\b", re.I)
_SENIORITY_RULES = [
    ("Summer Analyst", r"summer (analyst|associate|intern|internship|program|programme|vacation)|vacationer|"
                       r"spring (week|insight|intern)|summer \d{4}|\d{4} summer"),
    ("Off-cycle", r"off[- ]?cycle|industrial placement|placement year|long[- ]term intern|6[- ]month intern"),
    ("Working Student", r"working student|werkstudent|student job|studentische|[ée]tudiant|studente lavoratore"),
    ("Internship", r"\binterns?\b|internship|(?<!early[ -])(?<!late[ -])(?<!growth[ -])(?<!seed[ -])(?<!later[ -])\bstage\b|"
                   r"stagiaire|stagista|tirocin|praktik|stagiair"),
    ("Graduate Programme", r"graduate (programme|program|scheme|analyst|trainee|rotation|talent|hire)|\bgraduates?\b|"
                           r"grad (program|scheme)|new grad|absolvent|neolaureat|jeune dipl|career ?start|campus|"
                           r"trainee program|early careers? program"),
    ("Trainee", r"trainee|apprenti|lehrstelle|\bv\.?i\.?e\b|volontariat"),
    ("Entry-level", r"entry[- ]level|early[- ]career|berufseinsteig|einsteiger|d[ée]butant|first job|0 ?(-|to) ?[12] years"),
    ("Junior / Analyst", r"junior|\bjr\b|\banalyst\b|analista|analyste"),
]
_SENIORITY_RX = [(n, re.compile(rx, re.I)) for n, rx in _SENIORITY_RULES]

_YEARS = r"(?:years?|yrs?|ann[oi]|jahre?n?|ans?|ann[ée]es?)"
_NUM = r"(?P<a>\d{1,2})\s*(?P<plus>\+|plus)?\s*(?:(?:-|–|—|to|bis|a|à)\s*(?P<b>\d{1,2})\s*)?\+?\s*"
_EXP_RX = re.compile(
    _NUM + _YEARS + r"['’]?\s*(?:of |di |d['’]|an |von )?"
    r"(?:[A-Za-zäöüéè&/\-]+,?\s){0,6}?(?:experience|esperienza|berufserfahrung|erfahrung|exp[ée]rience)", re.I)
_EXP_RX2 = re.compile(
    r"(?:experience|esperienza|erfahrung|exp[ée]rience)\s*(?:of|di|von|de)?\s*(?:at least|minimum|min\.?|almeno|mindestens|au moins)?\s*"
    + _NUM + _YEARS, re.I)
# "3-5 years post-university", "2+ years post-qualification"
_EXP_RX3 = re.compile(_NUM + _YEARS + r"['’]?\s*(?:post[- ]?(?:university|graduat\w*|qualif\w*|degree)|pqe|in a similar role|"
                      r"in (?:a|an) [a-z ]{3,30} role)", re.I)


def extract_experience(text: str) -> dict:
    """Years of experience demanded. {'min','max','text'}; all None when not stated."""
    best = None
    for rx in (_EXP_RX, _EXP_RX2, _EXP_RX3):
        for m in rx.finditer(text or ""):
            a = int(m.group("a"))
            b = int(m.group("b")) if m.group("b") else None
            if a >= 15 or (b is not None and b > 20):
                continue  # "30 years of experience serving clients" describes the firm, not the role
            cand = {"min": a, "max": b, "text": re.sub(r"\s+", " ", text[max(0, m.start() - 30): m.end() + 10]).strip()}
            if best is None or a < best["min"]:
                best = cand
    return best or {"min": None, "max": None, "text": None}


def classify_seniority(title: str, description: str = "", ats_hint: str = "") -> dict:
    """Return {'seniority','include','warning','experience':{min,max,text}}."""
    title = title or ""
    hay = f"{title} {ats_hint or ''}"
    exp = extract_experience(description or "")
    label = next((n for n, rx in _SENIORITY_RX if rx.search(hay)), None)
    senior = _SENIOR_RX.search(title)
    warning = None

    if label in ("Summer Analyst", "Off-cycle", "Working Student", "Internship", "Graduate Programme", "Trainee",
                 "Entry-level"):
        include = True  # explicit early-career marker beats everything else in the title
    elif senior:
        return {"seniority": "Experienced", "include": False, "warning": None, "experience": exp,
                "reason": f"senior title ('{senior.group(0)}')"}
    elif label == "Junior / Analyst":
        include = True
    elif re.search(r"\bassociate\b", title, re.I):
        label, include = "Ambiguous", True
        warning = "'Associate' title: seniority differs by firm (entry-level at some, 3+ years at others)"
    elif _MANAGER_RX.search(title):
        if re.search(r"assistant manager|junior|trainee|graduate", title, re.I):
            label, include = "Ambiguous", True
            warning = "'Manager' in title: check the experience required"
        else:
            return {"seniority": "Experienced", "include": False, "warning": None, "experience": exp,
                    "reason": "'Manager' title: experienced role"}
    else:
        for n, rx in _SENIORITY_RX[:7]:
            if rx.search((description or "")[:1200]):
                label = n
                break
        if label:
            include = True
        else:
            label, include = "Ambiguous", True
            warning = "Seniority not stated in the title"

    if exp["min"] is not None:
        if exp["min"] >= 3 and label not in ("Summer Analyst", "Off-cycle", "Internship", "Working Student",
                                             "Graduate Programme", "Trainee"):
            return {"seniority": "Experienced", "include": False, "warning": None, "experience": exp,
                    "reason": f"requires {exp['min']}+ years of experience"}
        if exp["min"] == 2 or (exp["max"] and exp["max"] > 2):
            warning = (warning + "; " if warning else "") + f"asks for {exp['text']}"
        if label == "Ambiguous" and exp["min"] <= 2 and (exp["max"] or 0) <= 2:
            label, warning = "Entry-level", None
    return {"seniority": label, "include": include, "warning": warning, "experience": exp, "reason": None}


# ------------------------------------------------------------------ contract
_CONTRACT_RULES = [
    ("Fixed-term", r"fixed[- ]term|temporary|befristet|tempo determinato|\bcdd\b|maternity cover|"
                   r"\b(6|9|12|18|24)[- ]months? (contract|ftc)|\bftc\b|contractor|interim"),
    ("Part-time", r"part[- ]time|teilzeit|tempo parziale|temps partiel"),
    ("Full-time", r"full[- ]time|permanent|vollzeit|unbefristet|tempo indeterminato|\bcdi\b|festanstellung|"
                  r"temps plein|regular"),
]


def classify_contract(title: str, description: str, seniority: str, ats_type: str = "") -> str:
    if seniority in ("Internship", "Summer Analyst", "Off-cycle"):
        return "Internship"
    if seniority == "Working Student":
        return "Working student"
    if seniority == "Graduate Programme":
        return "Graduate programme"
    if seniority == "Trainee":
        return "Apprenticeship / Trainee"
    head = f"{title} {ats_type or ''}"
    if re.search(r"\bintern(ship)?\b|praktikum|stagiaire|tirocinio", head, re.I):
        return "Internship"
    for hay in (head, (description or "")[:2500]):
        for label, rx in _CONTRACT_RULES:
            if re.search(rx, hay, re.I):
                return label
    return "Not specified"


# ------------------------------------------------------------------ deadline
_MONTHS = {m: i for i, names in enumerate([
    (), ("january", "jan", "gennaio", "januar", "janvier"), ("february", "feb", "febbraio", "februar", "fevrier"),
    ("march", "mar", "marzo", "marz", "maerz", "mars"), ("april", "apr", "aprile", "avril"),
    ("may", "maggio", "mai"), ("june", "jun", "giugno", "juni", "juin"), ("july", "jul", "luglio", "juli", "juillet"),
    ("august", "aug", "agosto", "aout"), ("september", "sep", "sept", "settembre", "septembre"),
    ("october", "oct", "ottobre", "oktober", "octobre"), ("november", "nov", "novembre"),
    ("december", "dec", "dicembre", "dezember", "decembre")]) for m in names}
_DEADLINE_LABEL = (r"(?:application deadline|deadline for applications?|apply (?:by|before)|closing date|"
                   r"applications? (?:close|closes|closing|must be (?:received|submitted) by|are open until|open until|"
                   r"accepted until|due)(?: on| by)?|deadline|bewerbungsfrist|bewerbungsschluss|bewerbung bis|"
                   r"termine (?:per le |di )?(?:candidature|presentazione)|scadenza(?: candidature| bando)?|candidature entro(?: il)?|"
                   r"date limite(?: de candidature)?|cl[oô]ture des candidatures)")
_DATE_PART = (r"(?P<d1>\d{1,2})(?:st|nd|rd|th|\.)?\s+(?P<m1>[A-Za-zéûä]{3,10})\.?,?\s+(?P<y1>20\d{2})"
              r"|(?P<m2>[A-Za-zéûä]{3,10})\.?\s+(?P<d2>\d{1,2})(?:st|nd|rd|th)?,?\s+(?P<y2>20\d{2})"
              r"|(?P<d3>\d{1,2})\.(?P<m3>\d{1,2})\.(?P<y3>20\d{2})"
              r"|(?P<y4>20\d{2})-(?P<m4>\d{2})-(?P<d4>\d{2})"
              r"|(?P<d5>\d{1,2})/(?P<m5>\d{1,2})/(?P<y5>20\d{2})")
_DEADLINE_RX = re.compile(_DEADLINE_LABEL + r"\s*(?:is|:|-|–|on|by)?\s*(?:the\s+)?(?:" + _DATE_PART + ")", re.I)


def extract_deadline(text: str) -> str | None:
    """Deadline stated in free text, only when introduced by an explicit label.

    Numeric dd/mm vs mm/dd dates that could be read both ways are rejected.
    """
    from .util import strip_accents

    m = _DEADLINE_RX.search(strip_accents(text or ""))
    if not m:
        return None
    g = m.groupdict()
    try:
        if g["y1"]:
            mo = _MONTHS.get(g["m1"].lower())
            return date(int(g["y1"]), mo, int(g["d1"])).isoformat() if mo else None
        if g["y2"]:
            mo = _MONTHS.get(g["m2"].lower())
            return date(int(g["y2"]), mo, int(g["d2"])).isoformat() if mo else None
        if g["y3"]:
            return date(int(g["y3"]), int(g["m3"]), int(g["d3"])).isoformat()
        if g["y4"]:
            return date(int(g["y4"]), int(g["m4"]), int(g["d4"])).isoformat()
        if g["y5"]:
            d, mo = int(g["d5"]), int(g["m5"])
            if d > 12 >= mo:
                return date(int(g["y5"]), mo, d).isoformat()
            return None  # ambiguous or US-style: do not guess
    except (ValueError, TypeError):
        return None
    return None


_MONTH_NAMES = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
_FUTURE_RX = re.compile(
    r"applications? (?:will )?(?:open|opens|opening|re-?open)s?(?: on| in| from| between| as of)?\s+(?P<when>[^.\n)]{3,60})|"
    r"(?:not yet open|opening soon|register your interest|expression of interest|coming soon)", re.I)
_WHEN_DATE = re.compile(rf"(?P<m>{_MONTH_NAMES})\.?\s+(?P<d>\d{{1,2}})(?:st|nd|rd|th)?,?\s+(?P<y>20\d{{2}})|"
                        rf"(?P<d2>\d{{1,2}})(?:st|nd|rd|th)?\s+(?P<m2>{_MONTH_NAMES})\.?,?\s+(?P<y2>20\d{{2}})|"
                        rf"(?P<m3>{_MONTH_NAMES})\s+(?P<y3>20\d{{2}})", re.I)


def _when_start(text: str) -> date | None:
    m = _WHEN_DATE.search(text or "")
    if not m:
        return None
    g = m.groupdict()
    try:
        if g["y"]:
            return date(int(g["y"]), _MONTHS[g["m"][:3].lower()], int(g["d"]))
        if g["y2"]:
            return date(int(g["y2"]), _MONTHS[g["m2"][:3].lower()], int(g["d2"]))
        return date(int(g["y3"]), _MONTHS[g["m3"][:3].lower()], 1)
    except (KeyError, ValueError):
        return None


def detect_future_window(title: str, description: str) -> str | None:
    """Return the quoted wording when a posting announces an application window that has not opened yet.

    An announced opening date that is already past is not a future window.
    """
    from .util import today as _today

    for m in _FUTURE_RX.finditer(f"{title}\n{(description or '')[:3000]}"):
        when = m.group("when")
        if when is not None:
            if not re.match(rf"\s*(?:the\s+)?(?:\d|{_MONTH_NAMES}|early|mid|late|spring|summer|autumn|fall|winter|q[1-4])", when, re.I):
                continue  # "applications open to all students" is not a date
            start = _when_start(when)
            if start is not None and start <= _today():
                continue
        return re.sub(r"\s+", " ", m.group(0)).strip()[:120]
    return None


CLOSED_TITLE_RX = re.compile(r"^\W*closed\b(?!-)|\(closed\)|\bclosed\s*:|\bclosed\s+[-–]\s|applications? (?:are |now )?closed", re.I)


# ------------------------------------------------------------------ visa
_VISA_RX = re.compile(r"[^.\n]*(visa|sponsorship|work permit|right to work|eligib(le|ility) to work|"
                      r"work authori[sz]ation|permesso di lavoro|arbeitsbewilligung|arbeitserlaubnis|"
                      r"permis de travail)[^.\n]*", re.I)


def extract_visa(description: str) -> dict:
    m = _VISA_RX.search(description or "")
    if not m:
        return {"status": "Not specified", "note": None}
    sentence = re.sub(r"\s+", " ", m.group(0)).strip()[:240]
    low = sentence.lower()
    if re.search(r"(no|not|unable|cannot|can't|does not|do not|without).{0,50}sponsor|must (already )?(have|hold|possess).{0,40}(right|permit|authori)", low):
        status = "Not offered"
    elif re.search(r"sponsorship (is |may be )?(available|provided|offered|possible)|will sponsor|we sponsor|can sponsor", low):
        status = "Available"
    else:
        status = "Mentioned (see note)"
    return {"status": status, "note": sentence}


def programme_year(title: str) -> int | None:
    m = re.search(r"\b(20[2-3]\d)\b", title or "")
    return int(m.group(1)) if m else None


__all__ = ["classify_sector", "classify_seniority", "classify_contract", "extract_experience",
           "extract_deadline", "detect_future_window", "extract_visa", "programme_year", "parse_date"]
