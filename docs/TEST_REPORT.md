# Implementation and test report

Date: 14 November 2026. Scope: the specification "Finance Career Intelligence Platform", sections 1 to 19.

How to reproduce: `pytest -q` (84 tests, offline) and `python scripts/build_site.py && node tests/e2e/site.test.mjs`
(28 checks in headless Chrome). Both suites pass.

## What could and could not be tested, and why

The environment this was built in blocks outbound connections to job sites and has no GitHub credentials. That
shaped the testing:

- **Live sources were reached through a browser instead.** 21 employer boards were queried live on 13 Nov 2026 and
  their identity checked against the board's own company name. Real responses were captured, reduced to
  early-career roles in the target cities (with description excerpts) and stored in `tests/fixtures/live_capture/`.
  The Python connectors and the whole pipeline run on those responses. What is *not* proven is the Python HTTP layer
  talking to those servers directly; that happens for the first time on GitHub Actions.
- **GitHub Actions, GitHub Pages and delivery through a real mail provider were not executed.** They need your
  account and your secrets. Every command the workflows run was executed locally, the workflow files parse as valid
  YAML, the email path was exercised end to end against a real SMTP server on localhost, and the site was tested in
  a real browser from a static file server, which is what Pages is.

## Status by feature

### Implemented and tested

| Area | Evidence |
|---|---|
| Excel import | The real workbook: 3 sheets inspected, 14 of 14 columns mapped by header, 1,389 rows read, 1,286 unique companies, 0 rows dropped (`test_real_excel_imports_completely`). Shuffled columns, title rows and unknown columns handled (`test_import_reads_structure_without_fixed_positions`) |
| Company normalisation | Unique IDs, original names, categories and locations preserved next to normalised ones; "Elenco Ufficiale FINMA" and similar text is not mistaken for a URL |
| Incremental Excel update | New companies, changed fields, new offices detected; nothing deleted; no duplicates; approved additional companies and history preserved; re-import is idempotent (4 tests) |
| Additional companies | Stored separately with reason and discovery date, pending review, not monitored until approved, survive Excel imports (2 tests). 12 proposed |
| Source registry | Every company has at least one source record; "no portal on file", "awaiting analysis", "failed", "unreachable" and "monitored, no vacancies" are distinct states (5 tests) |
| Recruitment-system detection | 10 supported and 15 detect-only systems recognised from page markup; no false positive on prose (`test_ats_detection_from_page_markup`); discovery flow on recorded pages (2 tests) |
| Greenhouse connector | Real responses from 16 boards |
| SmartRecruiters connector | Real responses from 4 companies, including the detail request |
| SuccessFactors connector | Markup confirmed live on jobs.partnersgroup.com (title link, location and date cells, job-page description); parsing tested on a fixture rebuilt from that page |
| Real job collection | 34 real postings stored from 1,194 listed on the 21 boards. Filters verified on real cases: a hospitality role, a "5 to 10 years" analyst role and a compliance role are excluded; "Baar, CH" resolves to Zug; a German-language posting is flagged German required |
| Direct application links | Every stored link is the posting's own URL with its identifier, never a careers homepage; 11 were opened live (7 Greenhouse application pages, 4 Partners Group pages) and a wrong ID was confirmed to redirect elsewhere |
| Deduplication | Same role from two sources merges into one record with both sources and the official link; two requisitions with the same title on one board stay separate; the merged duplicate is not re-created. A real defect was found and fixed here: Squarepoint serves all vacancies from one page with `?gh_jid=` |
| Language extraction, German and French flags | 7 parametrised cases in English, German and French, levels (A1 to C2 or wording), evidence sentence, "market" vs language, posting language (10 tests) |
| Sector, seniority, contract, experience | 24 parametrised cases, including "Early Stage" not being an internship and "Associate" kept with a warning |
| Deadlines | Taken from structured fields or labelled sentences; ambiguous numeric dates rejected (7 cases) |
| Relevance scoring | Bounded, explained, weights sum to 100, ordering matches the brief, weights configurable, missing information listed (5 tests) |
| Job status logic | New, modified, removed after two consecutive misses, reopened; deadline-driven Closing Soon and Expired; a failing source never expires a job (4 tests) |
| Failure handling | HTTP errors, invalid payloads and a missing source do not stop the run; errors are recorded per source and shown on the Monitoring page (3 tests) |
| History | Events for every change in `data/history.json`; closed jobs kept |
| Email digest | Delivered over SMTP to a local server; content, ordering and links checked; credentials and addresses never written to disk (`test_digest_is_delivered_with_the_required_content`) |
| Duplicate notification prevention | Repeated runs send nothing; only meaningful changes and the 7-day and 48-hour windows notify again; merged records are not re-announced (5 tests) |
| Email failure isolation | Unreachable server: exit code 0, nothing marked as sent, retried next run; missing secrets: skipped cleanly; test-email procedure (3 tests) |
| Website | Dashboard, Job opportunities, job detail, Companies, Early careers, My applications, Monitoring: all render with real data, no JavaScript errors |
| Filters and sorting | Country, company, German required, search, sort by newest, company search by city, monitoring status (browser checks) |
| Application tracker | Save, status and notes persist across reload; JSON export, local reset and JSON import round-trip; network log confirms nothing leaves the browser (browser checks) |
| Responsive and themes | No horizontal overflow at 390 px; light and dark mode |
| URL re-verification | Only 404/410 on two consecutive checks closes a posting; 5xx and timeouts never do (`test_url_verification_is_conservative`) |

### Implemented but not fully tested

| Area | What is missing |
|---|---|
| Lever, Ashby, Workday, Recruitee, Personio, Workable, generic JSON-LD connectors | Tested against payloads written from each system's public documentation, not against live responses. None of the 21 confirmed companies uses them. Expect to see them exercised once discovery has analysed more career pages |
| Oracle Recruiting connector | Written from knowledge of the public endpoints; no test at all |
| Career-page discovery at scale | Logic tested on recorded pages; the pass over the 556 pages in your Excel has not run |
| Adzuna connector | Ingestion logic tested with a stub; the API call has not been made (needs a key) |
| GitHub Actions workflows | Valid YAML, each command run locally; not executed on GitHub |
| GitHub Pages publication | Site build tested locally in a browser; not published |
| Email through Gmail or Brevo | Same code path as the tested local delivery; needs your secrets. Use the "Send a test email" option on the first run |

### Partially implemented

| Area | State |
|---|---|
| Official career portal for every company | 573 companies have a website or career URL in the Excel and are queued for analysis. 709 have none (the Excel marks them as direct approach): the platform does not search the web for their sites, because guessing a domain would be inventing data. Add the URL to the Excel when you want one monitored |
| Recruitment system for every company | 21 confirmed (16 Greenhouse, 4 SmartRecruiters, 1 SuccessFactors). The rest is identified by the discovery step as it runs |
| Initial job database | Real but partial: early-career roles in target cities from 21 boards, with description excerpts. Postings outside the target cities and full descriptions arrive with the first automated run |
| "Future Application Window" | Detected only when the posting itself says applications open later. Recruiting calendars that are published as prose pages (not postings) are not parsed; the Early careers page shows your Excel's own cycle notes for those |
| Salary and visa sponsorship | Salary only from structured fields; visa from an explicit sentence, quoted. Most postings publish neither |

### Not implemented

| Area | Reason |
|---|---|
| Connectors for Taleo, iCIMS, Avature, tal.net, Umantis, Refline | No stable public feed without a session or bot checks. They are detected and listed for manual checking |
| Approving companies from the website itself | The site is static and has no write access to the repository. Approval is one command or one click in the Actions tab |
| Cross-device sync of the tracker | By design: personal data stays in the browser. JSON backup moves it |

### Blocked by external limitations

| Area | Limitation |
|---|---|
| Automated LinkedIn monitoring | LinkedIn's terms prohibit scraping and there is no public jobs API. Search links and manual capture, labelled "LinkedIn only", are provided instead |
| jobs.ch, Jobup.ch, eFinancialCareers, Indeed, Karriere.ch, JobRoom | No free public API; automated collection is restricted by their terms. Search links only |
| Deployment | Needs your GitHub account: create the repository, push, enable Pages, add secrets (README section 1) |

## The 20 acceptance tests

| # | Test | Result |
|---|---|---|
| 1 | Import the original Excel | Passed (real file) |
| 2 | Validate all company records | Passed |
| 3 | Identify official career portals | Partial: 573 from the Excel, verified live for 21 |
| 4 | Identify available ATS systems | Partial: 21 confirmed live; detection tested offline |
| 5 | Collect real job postings from working sources | Passed for 21 sources (browser capture) |
| 6 | Validate direct application links | Passed structurally for all 34; 11 opened live |
| 7 | Deduplication | Passed |
| 8 | Language extraction | Passed |
| 9 | German and French flags | Passed |
| 10 | Relevance scoring | Passed |
| 11 | Geographical filters | Passed |
| 12 | Company filters | Passed |
| 13 | Saved jobs | Passed |
| 14 | Application status persistence | Passed |
| 15 | JSON export and import | Passed |
| 16 | GitHub Actions execution | Not run (needs your account) |
| 17 | Daily email delivery | Passed against a local SMTP server; not through an external provider |
| 18 | Duplicate notification prevention | Passed |
| 19 | Failure handling | Passed |
| 20 | GitHub Pages publication | Not run (needs your account); site verified locally |

## Known weaknesses found while testing on real data

- At quantitative trading firms, technology and operations graduate roles whose titles contain "trading" or "quant"
  pass the sector filter (for example "Graduate Trading Applications Specialist"). They are real early-career roles
  but may not be what you want; the Sector and Company filters hide them.
- Programme restrictions written only in the description are not interpreted. Partners Group's "Summer Analyst
  Program 2027" is addressed to female candidates; the platform shows the text but does not flag it.
- Several firms keep evergreen postings open for years (one Squarepoint role was first published in 2020). The
  publication date is reported as the source gives it.
- Greenhouse answers a deleted posting's URL with a redirect to the board, not a 404, so `verify_jobs.py` cannot
  detect removal from the URL alone. Board-based jobs are closed by the listing check instead, which does not have
  this problem.
