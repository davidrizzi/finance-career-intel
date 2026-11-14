#!/usr/bin/env python3
"""Daily email digest.

    python scripts/send_notifications.py              # build + send, record what was sent
    python scripts/send_notifications.py --dry-run    # write out/digest.html, send nothing
    python scripts/send_notifications.py --test       # send a one-line test email

Configuration comes from environment variables (GitHub Actions Secrets):

    SMTP_HOST  SMTP_PORT  SMTP_USERNAME  SMTP_PASSWORD  EMAIL_TO
    optional: EMAIL_FROM (default SMTP_USERNAME), SMTP_SECURITY = starttls | ssl | none

A job is announced once. It is mentioned again only when something
meaningful changes (title, location, deadline, application link, reopening)
or when its deadline enters the 7-day and then the 48-hour window.
The history is data/notifications.json. A failed send records nothing, so
the same items are retried on the next run, and never raises: the data
update must not depend on email.
"""
import argparse
import hashlib
import html
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fcip.pipeline import load_jobs  # noqa: E402
from fcip.util import DATA_DIR, ROOT, days_until, load_json, load_settings, now_iso, save_json, setup_logging, log  # noqa: E402

NOTIF_FILE = DATA_DIR / "notifications.json"
NOTIFY_STATUSES = ("Open", "Closing Soon", "Future Application Window")
HASH_FIELDS = ("title", "city", "country", "deadline", "apply_url")


def meaningful_hash(job: dict) -> str:
    return hashlib.sha1("|".join(str(job.get(f)) for f in HASH_FIELDS).encode()).hexdigest()[:14]


def select(jobs: list[dict], state: dict, settings: dict) -> dict:
    """Split jobs into digest sections, honouring the notification history."""
    cfg = settings.get("notifications", {})
    min_score = cfg.get("min_score_for_digest", 0)
    sent = state.get("sent", {})
    sections = {"new": [], "changed": [], "closing_48h": [], "closing_7d": []}
    for job in jobs:
        if job.get("status") not in NOTIFY_STATUSES or (job.get("score") or 0) < min_score:
            continue
        if cfg.get("high_priority_only") and job.get("geo_priority") != "High":
            continue
        prev = sent.get(job["id"]) or next((sent[a] for a in job.get("aliases", []) if a in sent), None)
        left = days_until(job.get("deadline"))
        if prev is None:
            sections["new"].append(job)
            continue
        reasons = set(prev.get("reasons", []))
        if prev.get("hash") != meaningful_hash(job):
            job["_changed"] = (job.get("last_meaningful_change") or {}).get("fields") or ["details"]
            sections["changed"].append(job)
        elif left is not None and 0 <= left <= 2 and "closing_48h" not in reasons:
            sections["closing_48h"].append(job)
        elif left is not None and 2 < left <= 7 and "closing_7d" not in reasons:
            sections["closing_7d"].append(job)
    for key in sections:
        sections[key].sort(key=lambda j: (-(j.get("score") or 0), j.get("deadline") or "9999"))
    return sections


def record(sections: dict, state: dict, shown_ids: set[str]) -> None:
    """Mark everything in this digest as notified (including overflow not shown)."""
    ts = now_iso()
    sent = state.setdefault("sent", {})
    for reason, jobs in sections.items():
        for job in jobs:
            left = days_until(job.get("deadline"))
            entry = sent.setdefault(job["id"], {"first_sent": ts, "reasons": []})
            entry.update(last_sent=ts, hash=meaningful_hash(job), shown=job["id"] in shown_ids)
            tags = {reason}
            # a job first announced inside a deadline window does not need a second reminder for it
            if left is not None and 0 <= left <= 7:
                tags.add("closing_7d")
            if left is not None and 0 <= left <= 2:
                tags.add("closing_48h")
            entry["reasons"] = sorted(set(entry["reasons"]) | tags)


# ----------------------------------------------------------------- rendering
def _flag(job):
    g, f = job.get("german_flag", "NOT MENTIONED"), job.get("french_flag", "NOT MENTIONED")
    return f"German: {g.title()} · French: {f.title()}"


def _row_html(job, site_url):
    e = html.escape
    where = ", ".join(x for x in (job.get("city"), job.get("country")) if x) or "Location not specified"
    deadline = f"Deadline {job['deadline']}" if job.get("deadline") else "No deadline published"
    changed = f"<div style='color:#8a5a00;font-size:12px'>Changed: {e(', '.join(job['_changed']))}</div>" if job.get("_changed") else ""
    detail = f" · <a href='{e(site_url.rstrip('/'))}/#/job/{e(job['id'])}' style='color:#5b6b7f'>details</a>" if site_url else ""
    return (
        "<tr><td style='padding:12px 0;border-bottom:1px solid #e6e9ee'>"
        f"<div style='font-size:15px;font-weight:600;color:#10233f'>{e(job['title'])}</div>"
        f"<div style='font-size:13px;color:#33475f;margin:2px 0'>{e(job['company'])} · {e(where)} · {e(job.get('contract_type') or 'Not specified')}</div>"
        f"<div style='font-size:12px;color:#5b6b7f'>{e(job.get('verification', 'UNVERIFIED').title())} · {e(_flag(job))} · {e(deadline)}</div>"
        f"{changed}"
        f"<div style='font-size:13px;margin-top:6px'><a href='{e(job.get('apply_url') or '')}' style='color:#0b5cab;font-weight:600'>Apply / view posting</a>{detail}</div>"
        "</td><td style='padding:12px 0 12px 12px;border-bottom:1px solid #e6e9ee;vertical-align:top;text-align:right'>"
        f"<span style='display:inline-block;min-width:34px;padding:4px 6px;border-radius:4px;background:#10233f;color:#fff;font-size:13px;font-weight:600;text-align:center'>{job.get('score', 0)}</span>"
        "</td></tr>")


def _row_text(job):
    where = ", ".join(x for x in (job.get("city"), job.get("country")) if x) or "Location not specified"
    lines = [f"[{job.get('score', 0):>3}] {job['title']}",
             f"      {job['company']} | {where} | {job.get('contract_type') or 'Not specified'}",
             f"      {job.get('verification', 'UNVERIFIED')} | {_flag(job)} | deadline: {job.get('deadline') or 'not published'}"]
    if job.get("_changed"):
        lines.append(f"      changed: {', '.join(job['_changed'])}")
    lines.append(f"      {job.get('apply_url')}")
    return "\n".join(lines)


TITLES = {"new": "New opportunities", "closing_48h": "Closing within 48 hours", "closing_7d": "Closing within 7 days",
          "changed": "Updated postings"}
ORDER = ("closing_48h", "new", "closing_7d", "changed")


def render(sections: dict, settings: dict, meta: dict) -> tuple[str, str, str, set[str]]:
    cfg = settings.get("notifications", {})
    cap = cfg.get("max_jobs_in_digest", 40)
    site = cfg.get("site_url") or os.environ.get("SITE_URL", "")
    counts = {k: len(v) for k, v in sections.items()}
    total = sum(counts.values())
    subject = f"Finance careers: {counts['new']} new"
    if counts["closing_48h"]:
        subject += f", {counts['closing_48h']} closing in 48h"
    if counts["closing_7d"]:
        subject += f", {counts['closing_7d']} closing this week"
    if counts["changed"]:
        subject += f", {counts['changed']} updated"
    if total == 0:
        subject = "Finance careers: nothing new today"
    shown: set[str] = set()
    h = ["<div style='font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;max-width:640px;margin:0 auto;color:#10233f'>",
         "<div style='padding:18px 0;border-bottom:2px solid #10233f'><div style='font-size:18px;font-weight:700'>Finance Career Intelligence</div>",
         f"<div style='font-size:12px;color:#5b6b7f'>Daily digest · {now_iso()[:10]} · last successful update {html.escape(str(meta.get('last_successful_update') or 'n/a'))}</div></div>"]
    t = [f"FINANCE CAREER INTELLIGENCE - daily digest {now_iso()[:10]}", ""]
    budget = cap
    for key in ORDER:
        jobs = sections[key]
        if not jobs:
            continue
        take = jobs[:max(budget, 0)]
        budget -= len(take)
        h.append(f"<h2 style='font-size:14px;letter-spacing:.04em;text-transform:uppercase;color:#5b6b7f;margin:24px 0 4px'>{TITLES[key]} ({len(jobs)})</h2>")
        h.append("<table role='presentation' width='100%' cellspacing='0' cellpadding='0'>")
        t += [f"== {TITLES[key].upper()} ({len(jobs)}) ==", ""]
        for job in take:
            shown.add(job["id"])
            h.append(_row_html(job, site))
            t += [_row_text(job), ""]
        h.append("</table>")
        if len(jobs) > len(take):
            more = f"{len(jobs) - len(take)} more in this section are on the website."
            h.append(f"<div style='font-size:12px;color:#5b6b7f;padding:8px 0'>{more}</div>")
            t += [more, ""]
    if total == 0:
        h.append("<p style='font-size:14px'>No new, updated or closing opportunities since the last digest.</p>")
        t.append("No new, updated or closing opportunities since the last digest.")
    failed = (meta.get("last_run") or {}).get("sources_failed", 0)
    foot = f"Sources checked: {(meta.get('last_run') or {}).get('sources_attempted', 'n/a')}, failed: {failed}."
    if site:
        foot += f" Dashboard: {site}"
    h.append(f"<div style='font-size:12px;color:#5b6b7f;margin-top:24px;padding-top:12px;border-top:1px solid #e6e9ee'>{html.escape(foot)}<br>Scores are rule based (config/settings.json). Always confirm details on the employer's page before applying.</div></div>")
    t += ["--", foot]
    return subject, "\n".join(h), "\n".join(t), shown


# ----------------------------------------------------------------- sending
def smtp_config() -> dict | None:
    env = os.environ
    need = ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "EMAIL_TO")
    if not all(env.get(k) for k in need):
        return None
    port = int(env.get("SMTP_PORT") or 587)
    return {"host": env["SMTP_HOST"], "port": port, "user": env["SMTP_USERNAME"], "password": env["SMTP_PASSWORD"],
            "to": [a.strip() for a in env["EMAIL_TO"].split(",") if a.strip()],
            "from": env.get("EMAIL_FROM") or env["SMTP_USERNAME"],
            "security": (env.get("SMTP_SECURITY") or ("ssl" if port == 465 else "starttls")).lower()}


def send(cfg: dict, subject: str, body_html: str, body_text: str) -> None:
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, cfg["from"], ", ".join(cfg["to"])
    msg["Date"], msg["Message-ID"] = formatdate(localtime=False), make_msgid(domain="fcip.local")
    msg.set_content(body_text)
    msg.add_alternative(body_html, subtype="html")
    if cfg["security"] == "ssl":
        server = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=30, context=ssl.create_default_context())
    else:
        server = smtplib.SMTP(cfg["host"], cfg["port"], timeout=30)
    with server:
        if cfg["security"] == "starttls":
            server.starttls(context=ssl.create_default_context())
        if cfg["user"] and cfg["security"] != "none":
            server.login(cfg["user"], cfg["password"])
        server.send_message(msg)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="render to out/ and exit; nothing sent or recorded")
    ap.add_argument("--test", action="store_true", help="send a test message to check the SMTP settings")
    ap.add_argument("--strict", action="store_true", help="exit 1 when sending fails (default: exit 0)")
    args = ap.parse_args(argv)
    setup_logging()
    settings = load_settings()
    cfg = smtp_config()

    if args.test:
        if cfg is None:
            print("Missing SMTP settings. Required: SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_TO")
            return 1
        try:
            send(cfg, "Finance Career Intelligence: test email",
                 "<p>The SMTP settings work. Daily digests will arrive at this address.</p>",
                 "The SMTP settings work. Daily digests will arrive at this address.")
        except Exception as exc:  # report, never print credentials
            print(f"Test email FAILED: {type(exc).__name__}: {exc}")
            return 1
        print(f"Test email sent to {len(cfg['to'])} recipient(s).")
        return 0

    state = load_json(NOTIF_FILE, {"schema": 1, "sent": {}, "log": []})
    meta = load_json(DATA_DIR / "meta.json", {})
    sections = select(load_jobs()["jobs"], state, settings)
    total = sum(len(v) for v in sections.values())
    subject, body_html, body_text, shown = render(sections, settings, meta)
    counts = {k: len(v) for k, v in sections.items()}

    if args.dry_run:
        out = ROOT / "out"
        out.mkdir(exist_ok=True)
        (out / "digest.html").write_text(body_html, encoding="utf-8")
        (out / "digest.txt").write_text(body_text, encoding="utf-8")
        print(f"dry run: {subject}\n{counts}\nwritten to out/digest.html and out/digest.txt")
        return 0

    entry = {"ts": now_iso(), "counts": counts, "sent": False}
    if total == 0 and not settings.get("notifications", {}).get("send_empty_digest", False):
        entry["note"] = "nothing to report; empty digests are disabled"
        log.info(entry["note"])
    elif cfg is None:
        entry["note"] = "SMTP secrets not configured; digest skipped (nothing recorded as sent)"
        log.warning(entry["note"])
    else:
        try:
            send(cfg, subject, body_html, body_text)
            entry.update(sent=True, subject=subject)
            record(sections, state, shown)
            log.info("digest sent: %s", subject)
        except Exception as exc:
            entry["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
            log.error("digest NOT sent: %s", entry["error"])
    state.setdefault("log", []).append(entry)
    state["log"] = state["log"][-400:]
    save_json(NOTIF_FILE, state, compact=True)
    return 1 if (args.strict and entry.get("error")) else 0


if __name__ == "__main__":
    raise SystemExit(main())
