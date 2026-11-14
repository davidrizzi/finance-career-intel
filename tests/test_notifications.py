"""Acceptance tests 17-18: email digest, real SMTP delivery to a local server, no duplicate notifications."""
import email
import socket
from datetime import timedelta

import pytest

from conftest import load_script
from fcip import pipeline
from fcip.util import load_json, save_json, today

notif = load_script("send_notifications")


def job(i, title="Private Equity Intern", score=80, deadline=None, status="Open", **kw):
    j = {"id": f"j-{i}", "title": title, "company": "Alpha Capital", "city": "Zurich", "country": "Switzerland", "contract_type": "Internship",
         "verification": "VERIFIED OFFICIAL", "german_flag": "PREFERRED", "french_flag": "NOT MENTIONED", "score": score, "status": status,
         "deadline": deadline, "apply_url": f"https://alpha.example/jobs/{i}", "geo_priority": "High", "aliases": []}
    j.update(kw)
    return j


def in_days(n):
    return (today() + timedelta(days=n)).isoformat()


@pytest.fixture
def env(data, monkeypatch):
    monkeypatch.setattr(notif, "NOTIF_FILE", data / "notifications.json")
    monkeypatch.setattr(notif, "DATA_DIR", data)
    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_SECURITY", "EMAIL_TO", "EMAIL_FROM", "SITE_URL"):
        monkeypatch.delenv(k, raising=False)
    save_json(data / "meta.json", {"last_successful_update": "2026-11-14T04:30:00Z", "last_run": {"sources_attempted": 21, "sources_failed": 0}})

    def set_jobs(jobs):
        save_json(pipeline.JOBS_FILE, {"jobs": jobs})
    return set_jobs


@pytest.fixture
def smtp(monkeypatch):
    """A real SMTP server on localhost that keeps what it receives."""
    from aiosmtpd.controller import Controller

    class Box:
        def __init__(self):
            self.messages = []

        async def handle_DATA(self, server, session, envelope):
            self.messages.append((envelope.mail_from, envelope.rcpt_tos, email.message_from_bytes(envelope.content)))
            return "250 OK"

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    box = Box()
    ctl = Controller(box, hostname="127.0.0.1", port=port)
    ctl.start()
    monkeypatch.setenv("SMTP_HOST", "127.0.0.1")
    monkeypatch.setenv("SMTP_PORT", str(port))
    monkeypatch.setenv("SMTP_USERNAME", "digest@example.org")
    monkeypatch.setenv("SMTP_PASSWORD", "app-password-not-a-real-one")
    monkeypatch.setenv("SMTP_SECURITY", "none")
    monkeypatch.setenv("EMAIL_TO", "me@example.org")
    yield box
    ctl.stop()


def body(msg, kind):
    part = next(p for p in msg.walk() if p.get_content_type() == kind)
    return part.get_payload(decode=True).decode()


def test_digest_is_delivered_with_the_required_content(env, smtp):
    env([job(1, score=91), job(2, "Summer Analyst 2027", score=88, deadline=in_days(5)), job(3, "M&A Analyst", score=70, deadline=in_days(1)),
         job(4, "Low match", score=20), job(5, "Closed role", status="Removed")])
    assert notif.main([]) == 0
    (sender, rcpts, msg), = smtp.messages
    assert rcpts == ["me@example.org"] and sender == "digest@example.org"
    assert msg["Subject"].startswith("Finance careers: 3 new")
    html, text = body(msg, "text/html"), body(msg, "text/plain")
    for needle in ("Private Equity Intern", "Alpha Capital", "Zurich", "Internship", "Verified Official", "German: Preferred", "French: Not Mentioned",
                   "https://alpha.example/jobs/1", "Apply / view posting"):
        assert needle in html
    assert "Low match" not in html and "Closed role" not in html             # below the score threshold / not open
    assert text.index("Private Equity Intern") < text.index("Summer Analyst 2027") < text.index("M&A Analyst")   # sorted by score
    state = load_json(notif.NOTIF_FILE)
    assert set(state["sent"]) == {"j-1", "j-2", "j-3"} and state["log"][-1]["sent"] is True
    assert "app-password" not in (notif.NOTIF_FILE).read_text() and "me@example.org" not in (notif.NOTIF_FILE).read_text()


def test_no_duplicate_notifications(env, smtp):
    env([job(1), job(2, "Summer Analyst 2027")])
    notif.main([])
    notif.main([])
    notif.main([])
    assert len(smtp.messages) == 1                                           # nothing new: nothing sent (empty digests disabled)
    assert load_json(notif.NOTIF_FILE)["log"][-1]["note"].startswith("nothing to report")


def test_only_meaningful_changes_notify_again(env, smtp):
    env([job(1, deadline=in_days(40))])
    notif.main([])
    env([job(1, deadline=in_days(40), description="reworded text", score=83)])    # cosmetic change
    notif.main([])
    assert len(smtp.messages) == 1
    env([job(1, deadline=in_days(20), last_meaningful_change={"at": "x", "fields": ["deadline"]})])
    notif.main([])
    assert len(smtp.messages) == 2 and "1 updated" in smtp.messages[1][2]["Subject"]
    assert "Changed: deadline" in body(smtp.messages[1][2], "text/html")
    notif.main([])
    assert len(smtp.messages) == 2


def test_deadline_reminders_fire_once_per_window(env, smtp):
    env([job(1, deadline=in_days(30))])
    notif.main([])
    env([job(1, deadline=in_days(30))])
    for _ in range(2):
        notif.main([])
    assert len(smtp.messages) == 1
    state = load_json(notif.NOTIF_FILE)
    j = job(1, deadline=in_days(6))
    state["sent"]["j-1"]["hash"] = notif.meaningful_hash(j)                  # same deadline, time has passed
    save_json(notif.NOTIF_FILE, state)
    env([j])
    notif.main([]); notif.main([])
    assert len(smtp.messages) == 2 and "closing this week" in smtp.messages[1][2]["Subject"]
    j = job(1, deadline=in_days(1))
    state = load_json(notif.NOTIF_FILE)
    state["sent"]["j-1"]["hash"] = notif.meaningful_hash(j)
    save_json(notif.NOTIF_FILE, state)
    env([j])
    notif.main([]); notif.main([])
    assert len(smtp.messages) == 3 and "closing in 48h" in smtp.messages[2][2]["Subject"]


def test_email_failure_is_contained_and_retried(env, monkeypatch):
    env([job(1)])
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        dead = s.getsockname()[1]
    for k, v in {"SMTP_HOST": "127.0.0.1", "SMTP_PORT": str(dead), "SMTP_USERNAME": "u", "SMTP_PASSWORD": "p", "SMTP_SECURITY": "none", "EMAIL_TO": "me@example.org"}.items():
        monkeypatch.setenv(k, v)
    assert notif.main([]) == 0                                               # never fails the workflow
    state = load_json(notif.NOTIF_FILE)
    assert state["sent"] == {} and "error" in state["log"][-1] and state["log"][-1]["sent"] is False
    assert notif.main(["--strict"]) == 1
    assert len(notif.select(load_json(pipeline.JOBS_FILE)["jobs"], state, {"notifications": {}})["new"]) == 1   # still pending


def test_missing_secrets_skip_the_digest_without_marking_anything_sent(env):
    env([job(1)])
    assert notif.main([]) == 0
    state = load_json(notif.NOTIF_FILE)
    assert state["sent"] == {} and "not configured" in state["log"][-1]["note"]
    assert notif.main(["--test"]) == 1


def test_test_email_procedure(env, smtp):
    assert notif.main(["--test"]) == 0
    assert smtp.messages[0][2]["Subject"] == "Finance Career Intelligence: test email"
    assert not (notif.NOTIF_FILE).exists()                                   # a test changes no state


def test_first_digest_is_capped_but_everything_is_marked(env, smtp, monkeypatch):
    env([job(i, f"Analyst Intern {i}", score=60 + i % 30) for i in range(70)])
    notif.main([])
    html = body(smtp.messages[0][2], "text/html")
    assert html.count("Apply / view posting") == 40 and "30 more in this section" in html
    assert len(load_json(notif.NOTIF_FILE)["sent"]) == 70
    notif.main([])
    assert len(smtp.messages) == 1


def test_merged_job_is_not_announced_twice(env, smtp):
    env([job(1)])
    notif.main([])
    env([job(9, aliases=["j-1"], apply_url="https://alpha.example/jobs/1")])   # record j-1 was merged into j-9, same vacancy
    notif.main([])
    assert len(smtp.messages) == 1
