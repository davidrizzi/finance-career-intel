# Finance Career Intelligence

A personal recruitment monitor for finance roles. It reads the career portals of the companies in your Excel, keeps a
structured database of early-career openings, scores them against your priorities, publishes a dashboard on GitHub
Pages and emails you a daily digest. Everything runs on free GitHub infrastructure.

- **Website**: static, no build step (`frontend/`), served by GitHub Pages.
- **Automation**: GitHub Actions, once a day and on demand.
- **Database**: JSON files in `data/`, versioned in git (full history for free).
- **Collection**: Python (`connectors/`, `fcip/`, `scripts/`).
- **Your applications**: stored only in your browser, never in the repository.

## Current state

| | |
|---|---|
| Companies imported from the Excel | 1,286 unique companies from 1,389 rows (the same firm in several cities is one company with several offices) |
| Companies with a working source today | 21, each confirmed by a live request on 13 Nov 2026 (`config/known_sources.json`) |
| Jobs in the initial database | 34 real postings from those sources (see "Initial snapshot" below) |
| Companies still to analyse | 556 have a website or career page in the Excel; the discovery step identifies their recruitment system on the first runs |
| Companies with no portal in the Excel | 709, mostly trustees and small wealth managers the Excel itself marks as "direct approach". They are listed, never reported as "no vacancies" |
| Additional companies proposed | 12, all waiting for your approval |

Full detail: [docs/TEST_REPORT.md](docs/TEST_REPORT.md) and [docs/SOURCES.md](docs/SOURCES.md).

**Initial snapshot.** The build environment could not reach job sites directly, so the first database was captured
through a browser from 21 live employer boards and reduced to early-career roles in your target cities, with
description excerpts. Those reduced real responses are kept in `tests/fixtures/live_capture/` and are replayed through
the real connectors by the test-suite. The first GitHub Actions run replaces the snapshot with complete, current data.

## 1. Put it online (about 15 minutes, once)

1. **Create the repository.** On GitHub: New repository, for example `finance-career-intel`. A public repository gets
   free GitHub Pages and free Actions minutes. See "Privacy" below before choosing public.
2. **Push this folder.**
   ```bash
   cd finance-career-intel
   git init -b main
   git add -A
   git commit -m "Finance Career Intelligence: initial import"
   git remote add origin https://github.com/<you>/finance-career-intel.git
   git push -u origin main
   ```
3. **Enable Pages.** Repository > Settings > Pages > Build and deployment > Source: **GitHub Actions**.
4. **Allow the workflow to commit.** Settings > Actions > General > Workflow permissions: **Read and write permissions**.
   The Excel in `input/` is git-ignored, so it is not uploaded.
5. **Add the email secrets** (section 4). Optional: skip this and add them later, the data update works without them.
6. **Run it.** Actions > "Daily update" > Run workflow. For the very first run set "Career pages to analyse" to `600`
   so every company page is analysed at once (roughly 30 to 60 minutes). Afterwards it runs by itself every day at
   04:23 UTC.
7. Open `https://<you>.github.io/finance-career-intel/`. Optionally set a repository **variable** `SITE_URL` to that
   address (Settings > Secrets and variables > Actions > Variables) so the digest links back to the site.

## 2. What happens every day

`.github/workflows/daily_update.yml` runs these steps:

1. `scripts/discover_sources.py`: reads career pages not yet analysed and records the recruitment system each one
   links to (Workday, Greenhouse, Lever, SmartRecruiters, SuccessFactors, Oracle, Ashby, Recruitee, Personio, Workable,
   or structured data on a custom site). Systems without a connector (Taleo, iCIMS, Avature and others) are recorded
   as "manual check" with a link.
2. `scripts/update_jobs.py`: reads every working source, filters to target sectors and seniority, extracts languages,
   deadlines and experience, removes duplicates, updates statuses, scores every job and writes `data/*.json`.
3. `scripts/verify_jobs.py`: re-checks postings that do not come from a pollable board.
4. Commits the data. **This happens before any email is attempted**, so a mail problem can never lose an update.
5. `scripts/send_notifications.py`: sends the digest and records what was announced.
6. Builds and publishes the website.

Failures are isolated per source: one broken portal is logged on the Monitoring page and the rest of the run continues.

## 3. Updating the Excel

The Excel stays the master list. Whenever you have a new version:

```bash
pip install -r requirements.txt
python scripts/import_excel.py path/to/your_new_file.xlsx --dry-run   # shows what would change
python scripts/import_excel.py path/to/your_new_file.xlsx
git add data && git commit -m "Excel update" && git push
```

The importer:

- finds the company worksheet and its columns by their headers (Italian or English), wherever they are;
- recognises existing companies even if the legal form changes ("Foo SA" and "Foo" are the same company);
- adds new companies and new office locations, and logs every changed field in `data/history.json`;
- never deletes anything: a company missing from the new file is kept and flagged "not in latest Excel";
- never touches additional companies you approved, and never touches job history;
- ignores the "Stato Candidatura / Monitoraggio" column unless you set `privacy.publish_excel_monitoring_status`
  to `true`, because the repository may be public.

No code changes are needed when you add companies. By default `input/*.xlsx` is git-ignored so the workbook itself
stays on your computer. If you prefer to upload it and let GitHub import it, remove those two lines from `.gitignore`
and push the file to `input/`: the "Import Excel" workflow does the rest.

To attach a recruitment system by hand (for a company whose page cannot be analysed automatically), add an entry to
`config/known_sources.json`:

```json
{"company": "Exact Name From Excel", "ats": "greenhouse", "token": "boardname", "evidence": "where you saw it"}
```

## 4. Email digest

The digest uses plain SMTP, so any provider works. Two free options, checked in November 2026:

| Provider | Free allowance | Settings |
|---|---|---|
| Gmail (recommended, simplest) | 500 messages a day on a personal account | host `smtp.gmail.com`, port `587`, username = your address, password = a 16-character **App Password** (Google Account > Security > 2-Step Verification must be on > App passwords) |
| Brevo | 300 emails a day, no card required | host `smtp-relay.brevo.com`, port `587`, username = your Brevo login, password = the SMTP key from the Brevo dashboard |

One digest a day is far below both limits. Add these under Settings > Secrets and variables > Actions > **Secrets**:

| Secret | Example |
|---|---|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USERNAME` | `you@gmail.com` |
| `SMTP_PASSWORD` | the app password or SMTP key |
| `EMAIL_TO` | where the digest should arrive (comma-separated for several) |
| `EMAIL_FROM` | optional, defaults to `SMTP_USERNAME` |
| `SMTP_SECURITY` | optional: `starttls` (default), `ssl` (port 465) or `none` |

**Test it:** Actions > Daily update > Run workflow > tick "Send a test email". Locally:

```bash
export SMTP_HOST=smtp.gmail.com SMTP_PORT=587 SMTP_USERNAME=you@gmail.com SMTP_PASSWORD='xxxx xxxx xxxx xxxx' EMAIL_TO=you@gmail.com
python scripts/send_notifications.py --test       # one-line test message
python scripts/send_notifications.py --dry-run    # writes out/digest.html, sends nothing
```

Rules the digest follows:

- a job is announced once; it comes back only if its title, location, deadline or application link changes, if it
  reopens, or when its deadline enters the 7-day and then the 48-hour window;
- history is `data/notifications.json` (job IDs and timestamps only, no addresses);
- an empty digest is not sent unless `notifications.send_empty_digest` is `true`;
- `notifications.min_score_for_digest` (default 45) and `max_jobs_in_digest` (default 40) keep it readable;
- if sending fails nothing is marked as sent, so the same items go out with the next run.

## 5. Companies that are not in your Excel

Additional companies are stored with `origin: "additional"` and are never mixed into the Excel list. They start as
**pending review** and are not monitored until you approve them.

```bash
python scripts/manage_companies.py list
python scripts/manage_companies.py approve "Capvis"
python scripts/manage_companies.py reject "Leonteq"
python scripts/manage_companies.py add --name "X Capital" --category PE --country Switzerland --city Zurich \
    --website https://x.example --reason "why it is relevant"
```

Or without a terminal: Actions > "Review additional company" > Run workflow.

Twelve are proposed now (`tools/seed_additional_companies.py`). If you add the optional Adzuna key (section 6),
employers that advertise a matching early-career role in a target city and are not in your database are proposed
automatically, with the posting that triggered it as the reason.

## 6. LinkedIn and job boards

- **LinkedIn is not polled.** Its terms prohibit automated collection and it offers no public jobs API, so the
  platform does not scrape it, log in to it or work around its protections. Instead every company on the Companies
  page has a one-click LinkedIn search link, and a posting you find yourself can be recorded:
  ```bash
  python scripts/add_manual_job.py --company "Lazard" --title "Off-Cycle Analyst" \
      --url "https://www.linkedin.com/jobs/view/123" --location Milan
  ```
  It is labelled **LinkedIn only** until the same role appears on the employer's portal; then the two records merge
  and the label becomes **Verified official**.
- **jobs.ch, Jobup.ch, eFinancialCareers, Indeed, Karriere.ch, JobRoom** publish no free public API and restrict
  automated collection. They are available as search links (`connectors/aggregators`), not scraped.
- **Adzuna** has an official API with a free developer key and covers Switzerland, Italy, the UK and Australia. It is
  optional: add the secrets `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` to enable it. Its postings are labelled
  **Aggregator only**. This connector follows Adzuna's documented API but has not been run with a real key.

## 7. Configuration (`config/settings.json`)

| Section | What you can change |
|---|---|
| `geo` | Which cities are high or medium priority, and the location score for each level |
| `scoring.weights` | The six weights (sector 25, seniority 20, geography 20, profile 15, language 10, contract 10) |
| `scoring.sector_preferences` | How much you like each sector, 0 to 1 |
| `candidate` | Your languages (CEFR level), degree and skill keywords, and hard blockers |
| `collection` | Politeness (delay per host, retries, timeout), when a missing job counts as removed, description length |
| `notifications` | Minimum score, cap, empty digests, high-priority-only |

After changing weights run `python scripts/calculate_scores.py` (the daily run also does it). You can also try your
own weights directly on the website (Monitoring page): that only affects your browser.

The score is rule based and fully explained on each job page: points per criterion, what counts in favour, possible
drawbacks, and what could not be verified. No AI service is called anywhere.

## 8. How to read the data

**Verification**

| Label | Meaning |
|---|---|
| Verified official | Read from the employer's own career portal or recruitment system |
| LinkedIn only | Recorded from LinkedIn, not yet seen on the employer's portal |
| Aggregator only | Seen on a job board only |
| Unverified | Not enough information |

**Status**

| Status | Rule |
|---|---|
| Open | Listed by a source that answered on the last run |
| Closing Soon | Published deadline within 7 days |
| Future Application Window | The posting itself says applications open later |
| Expired | Published deadline has passed |
| Removed | No longer listed, confirmed on two consecutive successful checks. The record is kept |
| Verification Failed | The source could not be reached three times in a row. The job is not assumed closed |

Fields the source does not publish are shown as "Not specified", "Unknown" or "Not published". Deadlines are taken
from a structured field or from an explicitly labelled sentence; ambiguous numeric dates are not guessed.

**German and French flags**: Required, Preferred, Not required, Not mentioned. The clause that led to the flag is
shown on the job page. A posting written in German is flagged "German required" even if it does not say so.

**Files**

| File | Content |
|---|---|
| `data/companies.json` | Normalised company database (Excel and additional) |
| `data/sources.json` | Source registry: URL, type, recruitment system, last attempt, last success, errors |
| `data/jobs.json` | Every job ever detected, including closed ones |
| `data/history.json` | Event log: jobs new / modified / removed / reopened, company changes, imports |
| `data/notifications.json` | What the digest already announced |
| `data/meta.json` | Last run and coverage counters for the dashboard |
| `data/manual_jobs.json` | Postings you recorded by hand |

## 9. Your application tracker

Saved jobs, statuses (New, Saved, To Apply, Applied, Online Assessment, Interview, Rejected, Offer, Withdrawn),
dates, outcome and notes are kept in your browser's local storage. That means:

- nothing personal is ever sent to GitHub or stored in the repository;
- the data belongs to one browser on one device. It does **not** sync to your phone or to another browser;
- use **Export backup** on the My applications page to move it, and **Import backup** on the other device;
- clearing the browser's site data deletes it, so export a backup now and then.

## 10. Run it on your computer

```bash
pip install -r requirements-dev.txt
python scripts/update_jobs.py --company "Point72" -v     # one company, verbose
python scripts/discover_sources.py --limit 20
python scripts/build_site.py && python -m http.server 8000 -d _site
pytest -q                                                 # 84 offline tests
node tests/e2e/site.test.mjs                              # 28 browser checks (needs Playwright)
```

## 11. Limits worth knowing

- **GitHub Actions**: free for public repositories on standard runners. Scheduled runs can start late at busy times.
  GitHub switches off schedules in public repositories after 60 days without repository activity; the daily data
  commit normally keeps the repository active, and if a schedule is ever disabled you re-enable it in the Actions tab.
- **Coverage grows over the first runs.** Until a company's career page has been analysed it shows as "awaiting
  analysis". Pages that need JavaScript to show any content, or that sit behind a bot check, end up as "manual check".
- **Classification is rule based.** Titles such as "Associate" are kept with a warning rather than dropped. A few
  technology or operations roles at trading firms pass the sector filter; use the filters or the score to hide them.
- **Detail budgets.** For systems that need one request per posting (Workday, SmartRecruiters, SuccessFactors,
  Oracle) at most 40 new detail pages per source are read per run; the rest follow on the next runs.

## 12. Privacy and security

- No credentials are stored in the repository. SMTP and API keys live in GitHub Secrets only.
- `data/` contains only publishable information: company names, public postings, check results.
- A public repository makes your company list and notes column visible to anyone who finds it. If you would rather
  keep it private, GitHub Pages on a private repository needs a paid GitHub plan (check whether GitHub's student
  benefits cover it for you).
- `config/settings.json > candidate` holds language levels and generic keywords. Keep it generic.

## Repository layout

```
config/       settings.json, known_sources.json
connectors/   greenhouse, lever, ashby, smartrecruiters, workday, successfactors,
              other_ats (recruitee, personio, workable, oracle), career_websites (JSON-LD),
              linkedin_permitted (links and manual capture only), aggregators (Adzuna, link builders)
data/         JSON databases
fcip/         core library: companies, sources, discovery, classify, languages, scoring, pipeline
frontend/     index.html, css/, js/ (app.js, logic.js, store.js)
scripts/      import_excel, discover_sources, update_jobs, verify_jobs, calculate_scores,
              send_notifications, manage_companies, add_manual_job, build_site
tests/        pytest suite, browser tests, live captures
tools/        bootstrap_from_capture, seed_additional_companies, sources_report
.github/workflows/  daily_update, pages, tests, import_excel, review_company
```
