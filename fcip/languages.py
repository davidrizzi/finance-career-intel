"""Language-requirement extraction (English, German, French, Italian, ...).

For each language named in a posting we decide REQUIRED / PREFERRED /
NOT REQUIRED from the wording of the clause that names it, and keep that
clause as evidence. A posting that never names a language yields
NOT MENTIONED: English is never assumed to be sufficient.
"""
from __future__ import annotations

import re

from .util import strip_accents

LANGS = {
    "German": r"german|deutsch(kenntnisse)?|tedesc[oa]|allemand|swiss[- ]german|schweizerdeutsch",
    "French": r"french|francais|franzosisch|frances[ei]",
    "Italian": r"italian|italiano|italienisch|italien(?:ne)?\b",
    "English": r"english|englisch|inglese|anglais",
    "Spanish": r"spanish|spagnolo|spanisch|espagnol",
    "Luxembourgish": r"luxembourgish|luxemburgisch|lussemburghese|luxembourgeois",
    "Arabic": r"arabic|arabo|arabisch|arabe\b",
    "Mandarin": r"mandarin|chinese|cinese|chinesisch|chinois",
    "Dutch": r"dutch|olandese|niederlandisch|neerlandais",
    "Portuguese": r"portuguese|portoghese|portugiesisch|portugais",
    "Russian": r"russian|russo\b|russisch|russe\b",
}
_LANG_RX = {k: re.compile(rf"(?<![a-z])({v})(?![a-z])", re.I) for k, v in LANGS.items()}
_ANY_LANG = re.compile("|".join(f"(?:{v})" for v in LANGS.values()), re.I)

_NOT_REQ = re.compile(r"(not|no|kein|keine|non|pas)\s+(\w+\s+){0,3}?(required|needed|necessary|mandatory|a must|erforderlich|"
                      r"notwendig|richiest[oa]|necessari[oa]|requis|necessaire)|"
                      r"(is|are|ist|e)\s+not\s+(a\s+)?(requirement|must|prerequisite)", re.I)
_PREF = re.compile(r"prefer|\bplus\b|advantag|\basset\b|desirable|desired|nice[- ]to[- ]have|beneficial|bonus|ideally|"
                   r"would be (a|an|great|helpful)|welcome|appreciated|von vorteil|vorteil|wunschenswert|gerne|"
                   r"gradit[oa]|preferibil|preferenzial|titolo preferenziale|costituisce|un atout|souhait|apprecie|"
                   r"additional languages?|other languages?|further languages?|another language|second language|"
                   r"any other|optional|helpful|is a benefit|considered a", re.I)
_REQ = re.compile(r"fluen|proficien|native|mother tongue|must|required|requirement|essential|mandatory|excellent|strong|"
                  r"very good|good (command|knowledge)|business[- ]level|professional (level|working)|command of|"
                  r"written and (spoken|oral)|spoken and written|verbal and written|verhandlungssicher|fliessend|flie.end|"
                  r"sehr gute|gute kenntnisse|stilsicher|muttersprach|ottim[ao]|fluente|madrelingua|padronanza|"
                  r"buona conoscenza|conoscenza (dell|della|del)|courant|maitrise|indispensable|imperatif|bilingu|"
                  r"necessar|obbligatori|zwingend|erforderlich|voraussetzung|\b[abc][12]\b|need to|you (speak|are)|"
                  r"speaker|sprechend|sprachig|parlant|speaking", re.I)
_LEVEL_CEFR = re.compile(r"\b([ABC][12])(?:\s*[-/]\s*([ABC][12]))?\b")
_LEVEL_WORDS = re.compile(r"native( speaker| level)?|mother tongue|bilingual|business[- ]fluent|fluent|fluency|proficient|"
                          r"proficiency|advanced|intermediate|basic( knowledge)?|working knowledge|conversational|"
                          r"verhandlungssicher|fliessend|flie.end|muttersprache|sehr gute kenntnisse|gute kenntnisse|"
                          r"grundkenntnisse|madrelingua|fluente|ottima conoscenza|buona conoscenza|conoscenza base|"
                          r"courant|langue maternelle|bilingue|notions", re.I)

_STOP = {
    "de": {"und", "der", "die", "das", "mit", "fur", "sie", "wir", "ist", "eine", "einen", "nicht", "sowie", "bei", "oder", "ihre", "unser", "auf", "den", "von", "zu", "im"},
    "fr": {"les", "des", "et", "vous", "nous", "une", "pour", "dans", "avec", "est", "sur", "votre", "notre", "aux", "du", "au", "en", "qui", "que"},
    "it": {"il", "di", "che", "per", "con", "una", "del", "della", "gli", "nel", "sono", "alla", "dei", "delle", "le", "si", "da", "nella", "ed", "piu"},
    "en": {"the", "and", "of", "to", "with", "you", "our", "for", "will", "are", "in", "is", "we", "as", "on", "be", "your", "an", "or", "this"},
}
_LANG_NAME = {"de": "German", "fr": "French", "it": "Italian", "en": "English"}


def detect_text_language(text: str) -> str:
    """'en' | 'de' | 'fr' | 'it' | 'unknown' from stop-word frequencies."""
    words = re.findall(r"[a-z]+", strip_accents(text or "").lower())
    if len(words) < 25:
        return "unknown"
    scores = {lang: sum(1 for w in words if w in sw) for lang, sw in _STOP.items()}
    lang, top = max(scores.items(), key=lambda kv: kv[1])
    second = sorted(scores.values())[-2]
    if top < len(words) * 0.06 or top < second * 1.25:
        return "unknown"
    return lang


def _clauses(sentence: str) -> list[str]:
    return [c.strip() for c in re.split(r";|,| – | - |\bwhile\b|\bwhereas\b|\bbut\b|\bwhilst\b|\bmentre\b|\bw.hrend\b|\btandis\b", sentence) if c.strip()]


def _level(text: str) -> str | None:
    m = _LEVEL_CEFR.search(text)
    if m:
        return m.group(1) + (f"-{m.group(2)}" if m.group(2) else "")
    m = _LEVEL_WORDS.search(text)
    return m.group(0).lower() if m else None


def _two_langs(text: str) -> bool:
    return len({k for k, rx in _LANG_RX.items() if rx.search(text)}) > 1


def _level_near(clause: str, m: re.Match) -> str | None:
    """Level attached to one language when a clause names several ('English (C1) and German at B2')."""
    others = [x for x in _ANY_LANG.finditer(clause) if x.start() != m.start()]
    nxt = min((x.start() for x in others if x.start() > m.end()), default=len(clause))
    prev = max((x.end() for x in others if x.end() <= m.start()), default=0)
    after = _level(clause[m.end():nxt])
    if after:
        return after
    # "fluent English and German": a level word before the first language applies to the list
    return _level(clause[prev:m.start()]) or (_level(clause[:m.start()]) if prev else None)


def analyze_languages(description: str, title: str = "") -> dict:
    """Return languages[], german_flag, french_flag, description_language, notes[]."""
    raw = description or ""
    notes: list[str] = []
    if len(raw.strip()) < 80:
        return {"languages": [], "german_flag": "NOT MENTIONED", "french_flag": "NOT MENTIONED",
                "description_language": "unknown", "analysed": False,
                "notes": ["No job description available: language requirements could not be checked"]}
    text = strip_accents(raw)
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+|•|·|\*", text) if s.strip()]
    found: dict[str, dict] = {}
    rank = {"not_required": 0, "preferred": 1, "required": 2}
    for sent in sentences:
        if not _ANY_LANG.search(sent):
            continue
        clauses = _clauses(sent)
        for lang, rx in _LANG_RX.items():
            if not rx.search(sent):
                continue
            clause = next((c for c in clauses if rx.search(c)), sent)
            # "German market", "French clients" describe coverage, not a language skill
            m = rx.search(clause)
            after = clause[m.end(): m.end() + 30].lower()
            if re.match(r"[- ]?(market|client|compan|equit|bank|law|regulat|tax|team|office|desk|entity|gaap|business(?!\s*(level|fluent)))", after.strip()):
                if not re.search(r"speak|language|fluen|sprach|lingua|langue|kenntnis", clause, re.I):
                    continue
            inferred = False
            if _NOT_REQ.search(clause) and not _REQ.search(_NOT_REQ.sub(" ", clause)):
                req = "not_required"
            elif _PREF.search(clause):
                req = "preferred"
            elif _REQ.search(clause):
                req = "required"
            else:
                # no qualifier in the clause: look at the rest of the sentence
                tail = sent[sent.find(clause) + len(clause):] if clause in sent else ""
                if _PREF.search(tail[:60]) and not _REQ.search(clause):
                    req = "preferred"
                elif _REQ.search(sent):
                    req = "required"
                elif _PREF.search(sent):
                    req = "preferred"
                else:
                    req, inferred = "required", True
            level = _level_near(clause, m) or (_level(sent) if len(clauses) == 1 and not _two_langs(sent) else None)
            evidence = re.sub(r"\s+", " ", sent)[:220]
            prev = found.get(lang)
            if prev is None or rank[req] > rank[prev["requirement"]]:
                found[lang] = {"language": lang, "requirement": req, "level": level, "evidence": evidence,
                               "inferred": inferred}
            elif prev and not prev.get("level") and level and rank[req] == rank[prev["requirement"]]:
                prev["level"] = level

    doc_lang = detect_text_language(raw)
    if doc_lang in ("de", "fr", "it"):
        name = _LANG_NAME[doc_lang]
        if name not in found or found[name]["requirement"] != "required":
            found[name] = {"language": name, "requirement": "required", "level": None, "inferred": True,
                           "evidence": f"The posting itself is written in {name}"}
            notes.append(f"{name} flagged as required because the posting is written in {name}")
    for item in found.values():
        if item.get("inferred") and not item["evidence"].startswith("The posting"):
            notes.append(f"{item['language']} listed without a qualifier: treated as required")

    def flag(lang):
        item = found.get(lang)
        if not item:
            return "NOT MENTIONED"
        return {"required": "REQUIRED", "preferred": "PREFERRED", "not_required": "NOT REQUIRED"}[item["requirement"]]

    order = ["English", "Italian", "German", "French"]
    langs = sorted(found.values(), key=lambda x: (order.index(x["language"]) if x["language"] in order else 9, x["language"]))
    return {"languages": langs, "german_flag": flag("German"), "french_flag": flag("French"),
            "description_language": doc_lang, "analysed": True, "notes": notes}
