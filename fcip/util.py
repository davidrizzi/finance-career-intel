"""Shared helpers: paths, JSON I/O, text normalisation, dates, polite HTTP."""
from __future__ import annotations

import hashlib
import html
import json
import logging
import os
import re
import time
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("FCIP_DATA_DIR", ROOT / "data"))
CONFIG_DIR = ROOT / "config"

log = logging.getLogger("fcip")


def setup_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )


# --------------------------------------------------------------------- JSON
def load_json(path: Path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: Path, obj, compact: bool = False) -> None:
    """Atomic write so a crashed run never leaves a half-written database."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        if compact:
            json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(obj, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    tmp.replace(path)


def load_settings() -> dict:
    return load_json(CONFIG_DIR / "settings.json", {})


# --------------------------------------------------------------------- time
def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> date:
    return datetime.now(timezone.utc).date()


def parse_date(value) -> str | None:
    """Return YYYY-MM-DD for the many date shapes ATS feeds use, else None.

    Never guesses: an unparseable value yields None, not an approximation.
    """
    if value in (None, "", 0):
        return None
    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 1e12:  # milliseconds
            ts /= 1000.0
        if ts < 1e9:
            return None
        return datetime.fromtimestamp(ts, timezone.utc).date().isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    s = str(value).strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            return date(int(m[1]), int(m[2]), int(m[3])).isoformat()
        except ValueError:
            return None
    for fmt in ("%d/%m/%Y", "%d.%m.%Y", "%m/%d/%Y", "%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y",
                "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def days_until(iso_day: str | None) -> int | None:
    if not iso_day:
        return None
    try:
        return (date.fromisoformat(iso_day[:10]) - today()).days
    except ValueError:
        return None


# --------------------------------------------------------------------- text
def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm_text(s) -> str:
    """Lowercase, accent-free, punctuation-free, single-spaced."""
    s = strip_accents(str(s or "")).lower()
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def slugify(s) -> str:
    return norm_text(s).replace(" ", "-")


_LEGAL_SUFFIXES = {
    "sa", "ag", "ltd", "limited", "llp", "llc", "lp", "plc", "spa", "srl", "sagl", "gmbh", "sarl",
    "s a", "s p a", "inc", "corp", "corporation", "co", "bv", "nv", "se", "pty", "pte", "sgr", "sim",
    "scf", "sca", "sicav", "kg", "cie", "and cie", "dmcc", "difc",
}


def company_match_key(name: str) -> str:
    """Identity key for a company name.

    Drops trailing legal-form tokens and a trailing parenthetical so that
    'Foo Capital SA' and 'Foo Capital' resolve to the same company.
    """
    n = norm_text(re.sub(r"\([^)]*\)\s*$", "", str(name or "")))
    tokens = n.split()
    changed = True
    while changed and len(tokens) > 1:
        changed = False
        for width in (3, 2, 1):
            if len(tokens) > width and " ".join(tokens[-width:]) in _LEGAL_SUFFIXES:
                tokens = tokens[:-width]
                changed = True
                break
    return " ".join(tokens)


def html_to_text(raw) -> str:
    """Readable plain text from an HTML fragment, keeping paragraph breaks."""
    if not raw:
        return ""
    s = html.unescape(str(raw))
    if "<" in s:
        s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
        s = re.sub(r"(?i)<\s*(br|/p|/div|/li|/h[1-6]|/tr)\s*/?>", "\n", s)
        s = re.sub(r"(?i)<\s*li[^>]*>", "\n- ", s)
        s = re.sub(r"<[^>]+>", " ", s)
        s = html.unescape(s)
    s = s.replace("\xa0", " ")
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    s = re.sub(r" ?\n ?", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def is_url(value) -> bool:
    if not isinstance(value, str):
        return False
    v = value.strip()
    if not re.match(r"^https?://", v, re.I):
        return False
    p = urlparse(v)
    return bool(p.netloc and "." in p.netloc)


def host_of(url: str) -> str:
    return urlparse(url).netloc.lower()


def short_hash(*parts) -> str:
    h = hashlib.sha1("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()
    return h[:12]


# --------------------------------------------------------------------- http
class SourceError(Exception):
    """A source could not be read. Never means 'no vacancies'."""


class Http:
    """requests wrapper with per-host rate limiting, retries and backoff.

    A replay directory (FCIP_HTTP_REPLAY) lets the pipeline run against
    recorded responses, which is how the offline test-suite exercises the
    real connector code.
    """

    def __init__(self, settings: dict | None = None, timeout: float | None = None, max_retries: int | None = None):
        import requests  # imported lazily so pure-logic tests need no network libs

        c = (settings or {}).get("collection", {})
        self.timeout = timeout or c.get("request_timeout_seconds", 25)
        self.max_retries = max_retries or c.get("max_retries", 3)
        self.min_gap = c.get("min_seconds_between_requests_per_host", 1.0)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": c.get("user_agent", "FinanceCareerIntel/1.0"),
            "Accept-Language": "en,it;q=0.8,de;q=0.6,fr;q=0.6",
        })
        self._last: dict[str, float] = {}
        self.request_count = 0
        self.replay_dir = os.environ.get("FCIP_HTTP_REPLAY")
        self._replay = None
        if self.replay_dir:
            idx = Path(self.replay_dir) / "index.json"
            self._replay = load_json(idx, {}) if idx.exists() else {}
            self.min_gap = 0

    def _throttle(self, url: str) -> None:
        host = host_of(url)
        wait = self.min_gap - (time.monotonic() - self._last.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        self._last[host] = time.monotonic()

    def _replay_lookup(self, method: str, url: str, body):
        key = f"{method} {url}"
        if body is not None:
            key += " " + json.dumps(body, sort_keys=True)
        entry = self._replay.get(key) or self._replay.get(f"{method} {url}")
        if entry is None:
            raise SourceError(f"replay: no recorded response for {key[:200]}")
        if entry.get("status", 200) >= 400:
            raise SourceError(f"HTTP {entry['status']} for {url}")
        if "file" in entry:
            return (Path(self.replay_dir) / entry["file"]).read_text(encoding="utf-8")
        return entry.get("text", "")

    def request(self, method: str, url: str, *, json_body=None, headers=None, allow_404=False) -> str | None:
        import requests

        if self._replay is not None:
            try:
                return self._replay_lookup(method, url, json_body)
            except SourceError:
                if allow_404:
                    return None
                raise
        last_err: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            self._throttle(url)
            self.request_count += 1
            try:
                r = self.session.request(method, url, json=json_body, headers=headers, timeout=self.timeout)
                if r.status_code == 404 and allow_404:
                    return None
                if r.status_code in (429, 500, 502, 503, 504):
                    retry_after = r.headers.get("Retry-After", "")
                    delay = min(float(retry_after), 60) if retry_after.isdigit() else 2 ** attempt
                    last_err = SourceError(f"HTTP {r.status_code} for {url}")
                    log.debug("retry %s in %.0fs (%s)", url, delay, r.status_code)
                    time.sleep(delay)
                    continue
                if r.status_code >= 400:
                    raise SourceError(f"HTTP {r.status_code} for {url}")
                if not r.encoding or r.encoding.lower() == "iso-8859-1":
                    r.encoding = r.apparent_encoding or "utf-8"
                return r.text
            except SourceError:
                raise
            except requests.RequestException as exc:  # network trouble: retry
                last_err = SourceError(f"{type(exc).__name__}: {str(exc)[:160]}")
                time.sleep(2 ** attempt)
        raise last_err or SourceError(f"request failed: {url}")

    def get(self, url: str, **kw) -> str | None:
        return self.request("GET", url, **kw)

    def fetch_page(self, url: str) -> tuple[str, str]:
        """GET an HTML page following redirects. Returns (text, final_url)."""
        import requests

        if self._replay is not None:
            return self._replay_lookup("GET", url, None), url
        last_err: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            self._throttle(url)
            self.request_count += 1
            try:
                r = self.session.get(url, timeout=self.timeout, allow_redirects=True,
                                     headers={"Accept": "text/html,application/xhtml+xml"})
                if r.status_code in (429, 500, 502, 503, 504):
                    last_err = SourceError(f"HTTP {r.status_code} for {url}")
                    time.sleep(2 ** attempt)
                    continue
                if r.status_code >= 400:
                    raise SourceError(f"HTTP {r.status_code} for {url}")
                if not r.encoding or r.encoding.lower() == "iso-8859-1":
                    r.encoding = r.apparent_encoding or "utf-8"
                return r.text, r.url
            except SourceError:
                raise
            except requests.RequestException as exc:
                last_err = SourceError(f"{type(exc).__name__}: {str(exc)[:160]}")
                time.sleep(2 ** attempt)
        raise last_err or SourceError(f"request failed: {url}")

    def get_json(self, url: str, **kw):
        text = self.get(url, headers={"Accept": "application/json"}, **kw)
        if text is None:
            return None
        try:
            return json.loads(text)
        except ValueError as exc:
            raise SourceError(f"invalid JSON from {url}: {exc}") from exc

    def post_json(self, url: str, body: dict, **kw):
        text = self.request("POST", url, json_body=body,
                            headers={"Accept": "application/json", "Content-Type": "application/json"}, **kw)
        if text is None:
            return None
        try:
            return json.loads(text)
        except ValueError as exc:
            raise SourceError(f"invalid JSON from {url}: {exc}") from exc
