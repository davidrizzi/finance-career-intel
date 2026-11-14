"""Transparent, deterministic relevance score (0-100) with an explanation.

Weights and preference tables live in config/settings.json > scoring.
Nothing is excluded by score: it only ranks.
"""
from __future__ import annotations

import re

from .geo import geo_priority

CEFR = {"none": 0, "a1": 1, "a2": 2, "b1": 3, "b2": 4, "c1": 5, "c2": 6, "native": 6}
_WORD_LEVEL = [(r"native|mother|muttersprach|madrelingua|maternelle|bilingu", 6),
               (r"fluen|verhandlungssicher|fliessend|flie.end|courant|proficien|excellent|sehr gute|ottim", 5),
               (r"business|advanced|very good|professional|gute kenntnisse|buona", 4),
               (r"intermediate|working knowledge|conversational|good", 3), (r"basic|grundkenntnisse|notions|base", 2)]


def _required_level(level: str | None) -> int:
    """CEFR rank a posting asks for; 4 (B2) when a language is required with no level given."""
    if not level:
        return 4
    low = level.lower()
    m = re.match(r"([abc][12])", low)
    if m:
        return CEFR[m.group(1)]
    for rx, val in _WORD_LEVEL:
        if re.search(rx, low):
            return val
    return 4


def _has(text: str, keyword: str) -> bool:
    """Whole-word match, so 'excel' does not fire on 'excellent'."""
    return re.search(rf"(?<![a-z0-9]){re.escape(keyword.lower())}(?![a-z0-9])", text) is not None


def _candidate_level(candidate: dict, lang: str) -> int:
    return CEFR.get(str(candidate.get("languages", {}).get(lang, "none")).lower(), 0)


def score_job(job: dict, settings: dict) -> dict:
    sc = settings.get("scoring", {})
    weights = sc.get("weights", {})
    cand = settings.get("candidate", {})
    total_w = sum(weights.values()) or 100
    pos: list[str] = []
    neg: list[str] = []
    missing: list[str] = []
    parts: dict[str, dict] = {}

    def put(key, frac, note):
        w = weights.get(key, 0) * 100.0 / total_w
        parts[key] = {"points": round(w * max(0.0, min(1.0, frac)), 1), "max": round(w, 1), "note": note}

    # 1 sector
    sector = job.get("sector")
    pref = sc.get("sector_preferences", {})
    frac = pref.get(sector, 0.4) if sector else 0.3
    if job.get("sector_source") == "company category":
        frac *= 0.85
        missing.append("Sector inferred from the company's category, not stated in the posting")
    put("sector", frac, sector or "Unknown")
    (pos if frac >= 0.8 else neg if frac < 0.6 else []).append(
        f"Sector: {sector}" if frac >= 0.8 else f"Sector is a weaker fit: {sector or 'unknown'}")

    # 2 seniority / experience
    sen = job.get("seniority") or "Ambiguous"
    frac = sc.get("seniority_scores", {}).get(sen, 0.5)
    exp_min = job.get("experience_min_years")
    if exp_min is not None:
        if exp_min >= 3:
            frac = min(frac, 0.15)
            neg.append(f"Asks for {exp_min}+ years of experience")
        elif exp_min == 2:
            frac = min(frac, 0.7)
            neg.append("Asks for about 2 years of experience (upper end of the target range)")
        else:
            pos.append(f"Experience required: {exp_min} year(s) or less")
    elif sen not in ("Internship", "Summer Analyst", "Off-cycle", "Working Student", "Graduate Programme", "Trainee"):
        missing.append("Years of experience not specified")
    put("seniority", frac, sen)
    if frac >= 0.85:
        pos.append(f"Seniority: {sen}")
    if job.get("seniority_warning"):
        neg.append(job["seniority_warning"])

    # 3 geography
    level = geo_priority(job.get("city"), job.get("country"), settings)
    frac = settings.get("geo", {}).get("scores", {}).get(level, 0.2)
    where = ", ".join(x for x in (job.get("city"), job.get("country")) if x) or "location unknown"
    put("geography", frac, where)
    if level in ("high", "swiss_other"):
        pos.append(f"High-priority location: {where}")
    elif level == "medium":
        pos.append(f"Target location (medium priority): {where}")
    elif level == "unknown":
        missing.append("Location not specified")
    else:
        neg.append(f"Outside target locations: {where}")

    # 4 academic / professional profile
    desc = (job.get("description") or "").lower()
    if len(desc) < 80:
        put("profile", 0.5, "no description to compare")
        missing.append("No job description: profile fit not assessed")
    else:
        deg = [k for k in cand.get("degree_keywords", []) if _has(desc, k)]
        skills = [k for k in cand.get("skill_keywords", []) if _has(desc, k)]
        blockers = [k for k in cand.get("blockers", []) if _has(desc, k)]
        frac = 0.35 + min(len(deg), 3) * 0.1 + min(len(skills), 5) * 0.07
        if blockers:
            frac = min(frac, 0.25)
            neg.append("Requirement that may not be met: " + ", ".join(blockers))
        put("profile", frac, f"{len(deg)} degree / {len(skills)} skill keywords matched")
        if skills:
            pos.append("Skills mentioned that match the profile: " + ", ".join(sorted(set(skills))[:6]))
        if not deg and not skills:
            neg.append("No overlap found between the posting and the profile keywords")

    # 5 languages
    frac, lang_notes = 1.0, []
    if not job.get("languages_analysed", True) or (not job.get("languages") and len(desc) < 80):
        frac = 0.6
        missing.append("Language requirements not verified")
    else:
        for item in job.get("languages", []):
            lang, req = item["language"], item["requirement"]
            have, need = _candidate_level(cand, lang), _required_level(item.get("level"))
            if req == "required":
                if have >= need:
                    lang_notes.append(f"{lang} required (met)")
                elif have >= need - 1 and have > 0:
                    frac = min(frac, 0.6)
                    neg.append(f"{lang} required{' (' + item['level'] + ')' if item.get('level') else ''}: slightly above current level")
                elif have > 0:
                    frac = min(frac, 0.3)
                    neg.append(f"{lang} required{' (' + item['level'] + ')' if item.get('level') else ''}: above current level")
                else:
                    frac = min(frac, 0.1)
                    neg.append(f"{lang} required: not spoken")
            elif req == "preferred" and have < need - 1:
                frac = min(frac, 0.8)
                neg.append(f"{lang} preferred (not required)")
        if not job.get("languages"):
            frac = 0.85
            missing.append("No language requirement stated in the posting")
        elif frac == 1.0:
            pos.append("Language requirements met: " + (", ".join(lang_notes) or "none beyond English/Italian"))
    put("language", frac, f"German {job.get('german_flag', 'NOT MENTIONED')}, French {job.get('french_flag', 'NOT MENTIONED')}")

    # 6 contract
    contract = job.get("contract_type") or "Not specified"
    frac = sc.get("contract_scores", {}).get(contract, 0.5)
    put("contract", frac, contract)
    if contract == "Not specified":
        missing.append("Contract type not specified")
    elif frac >= 0.85:
        pos.append(f"Contract: {contract}")
    else:
        neg.append(f"Contract: {contract}")

    for field, label in (("published", "Publication date"), ("deadline", "Application deadline")):
        if not job.get(field):
            missing.append(f"{label} not published by the source")
    if job.get("verification") != "VERIFIED OFFICIAL":
        missing.append(f"Not confirmed on the employer's own portal ({job.get('verification', 'UNVERIFIED')})")

    return {"score": int(round(sum(p["points"] for p in parts.values()))), "breakdown": parts,
            "positives": pos, "negatives": neg, "missing": missing}
