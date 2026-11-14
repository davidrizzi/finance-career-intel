// Finance Career Intelligence: single-page front end (no build step, no dependencies).
import { createStore, STATUSES } from "./store.js";
import { ACTIVE, countBy, daysSince, daysUntil, esc, filterJobs, reweight, safeUrl, sortJobs } from "./logic.js";

const store = createStore(window.localStorage);
const main = document.getElementById("main");
const S = { meta: null, jobs: [], settings: {}, companies: null, sources: null, focus: null, loaded: false };
const PAGE = 50;
const CRITERIA = ["sector", "seniority", "geography", "profile", "language", "contract"];
const CRIT_LABEL = { sector: "Sector", seniority: "Seniority", geography: "Location", profile: "Profile fit", language: "Languages", contract: "Contract" };

// ------------------------------------------------------------------ helpers
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const fmtDate = (iso) => {
  if (!iso) return "";
  const d = new Date(iso.length <= 10 ? iso + "T00:00:00Z" : iso);
  return isNaN(d) ? esc(iso) : d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
};
const fmtStamp = (iso) => {
  if (!iso) return "never";
  const d = new Date(iso);
  return d.toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
};
const getJSON = async (path) => {
  const r = await fetch(path, { cache: "no-cache" });
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.json();
};
let toastTimer;
function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), 2600);
}
const where = (j) => [j.city, j.country].filter(Boolean).join(", ") || "Location not specified";
const isHi = (j) => j.geo_priority === "High";
const link = (url, text, cls = "") => {
  const u = safeUrl(url);
  return u ? `<a class="${cls}" href="${esc(u)}" target="_blank" rel="noopener noreferrer">${esc(text)}</a>` : "";
};

function scoreHTML(j) {
  const b = (j.score_detail || {}).breakdown || {};
  const segs = CRITERIA.map((k) => {
    const p = b[k];
    const f = p && p.max ? Math.max(0, Math.min(1, p.points / p.max)) : 0;
    return `<i style="--f:${f.toFixed(2)}" title="${esc(CRIT_LABEL[k])}: ${p ? p.points : 0} of ${p ? p.max : 0}"></i>`;
  }).join("");
  return `<span class="score" title="Match score ${j._score} of 100. Bars: ${CRITERIA.map((k) => CRIT_LABEL[k]).join(", ")}"><b>${j._score}</b><span class="spec" aria-hidden="true">${segs}</span></span>`;
}
const VERIF = { "VERIFIED OFFICIAL": ["ok", "Verified official"], "LINKEDIN ONLY": ["warn", "LinkedIn only"], "AGGREGATOR ONLY": ["warn", "Aggregator only"], "UNVERIFIED": ["bad", "Unverified"] };
const verifTag = (j) => { const [c, t] = VERIF[j.verification] || VERIF.UNVERIFIED; return `<span class="tag ${c}">${t}</span>`; };
const FLAG = { REQUIRED: ["bad", "required"], PREFERRED: ["warn", "preferred"], "NOT REQUIRED": ["ok", "not required"], "NOT MENTIONED": ["line", "not mentioned"] };
const flagTag = (lang, v) => { const [c, t] = FLAG[v] || FLAG["NOT MENTIONED"]; const txt = lang ? `${lang} ${t}` : t[0].toUpperCase() + t.slice(1); return `<span class="tag ${c}">${txt}</span>`; };
const STATUS_CLASS = { Open: "ok", "Closing Soon": "warn", "Future Application Window": "info", Expired: "line", Removed: "line", "Verification Failed": "bad" };
const statusTag = (j) => `<span class="tag ${STATUS_CLASS[j.status] || "line"}">${esc(j.status)}</span>`;
function deadlineText(j) {
  if (!j.deadline) return `<span class="muted">Not published</span>`;
  const d = daysUntil(j.deadline);
  const extra = d === null ? "" : d < 0 ? " (passed)" : d === 0 ? " (today)" : d <= 7 ? ` (${d} d left)` : "";
  return `<span class="${d !== null && d >= 0 && d <= 7 ? "tag warn" : ""}">${fmtDate(j.deadline)}${extra}</span>`;
}
const trackTag = (id) => { const s = store.statusOf(id); return s === "New" ? "" : `<span class="tag info">${esc(s)}</span>`; };

function applyWeights() {
  const w = store.pref("weights", null);
  for (const j of S.jobs) j._score = w ? reweight(j, w) : (j.score || 0);
}
function refreshNav() {
  const n = store.count();
  $("#nav-apps").textContent = n ? String(n) : "";
}

// ------------------------------------------------------------------ data
async function boot() {
  try {
    const [meta, jobs, settings] = await Promise.all([
      getJSON("data/meta.json"), getJSON("data/jobs.json"), getJSON("config/settings.json").catch(() => ({})),
    ]);
    S.meta = meta; S.jobs = jobs.jobs || []; S.settings = settings; S.loaded = true;
    applyWeights();
    $("#stamp").textContent = "Updated " + fmtStamp(meta.last_successful_update);
  } catch (err) {
    main.innerHTML = `<div class="panel"><h1>The job database could not be loaded</h1><p class="muted">${esc(err.message)}</p>
      <p>If you opened this file directly from disk, serve the folder instead: <code>python scripts/build_site.py &amp;&amp; python -m http.server -d _site</code>. On GitHub Pages, check that the "Daily update" workflow has completed at least once.</p></div>`;
    return;
  }
  refreshNav();
  window.addEventListener("hashchange", route);
  route();
}
const lazy = async (key, path) => { if (!S[key]) S[key] = await getJSON(path); return S[key]; };

// ------------------------------------------------------------------ router
const routes = { dashboard: viewDashboard, jobs: viewJobs, job: viewJob, companies: viewCompanies, early: viewEarly, applications: viewApplications, monitoring: viewMonitoring };
function route() {
  const [, name = "dashboard", arg] = location.hash.split("/");
  const view = routes[name] || viewDashboard;
  $$(".nav a").forEach((a) => a.toggleAttribute("aria-current", false));
  const navKey = name === "job" ? "jobs" : (routes[name] ? name : "dashboard");
  const cur = $(`.nav a[data-nav="${navKey}"]`);
  if (cur) cur.setAttribute("aria-current", "page");
  window.scrollTo(0, 0);
  Promise.resolve(view(arg ? decodeURIComponent(arg) : undefined)).catch((err) => {
    main.innerHTML = `<div class="panel"><h1>This page could not be shown</h1><p class="muted">${esc(err.message)}</p></div>`;
  });
}

// ------------------------------------------------------------------ dashboard
function jobRow(j, right) {
  return `<li class="${isHi(j) ? "hi" : ""}">${scoreHTML(j)}
    <div><a class="t" href="#/job/${esc(j.id)}">${esc(j.title)}</a><span class="s">${esc(j.company)}, ${esc(where(j))} ${trackTag(j.id)}</span></div>
    <div class="r">${right}</div></li>`;
}
function bars(pairs, hiFn = () => false, max = 8) {
  if (!pairs.length) return `<p class="empty">No data yet.</p>`;
  const top = pairs.slice(0, max), peak = top[0][1] || 1;
  return `<ul class="bars">${top.map(([k, n]) => `<li class="${hiFn(k) ? "hi" : ""}"><span class="lbl" title="${esc(k)}">${esc(k)}</span>
    <span class="track"><span class="fill" style="width:${Math.round((n / peak) * 100)}%"></span></span><span class="n">${n}</span></li>`).join("")}</ul>`;
}
function viewDashboard() {
  const active = S.jobs.filter((j) => ACTIVE.includes(j.status));
  const t = S.meta.totals || {}, cov = S.meta.coverage || {};
  const fresh = active.filter((j) => { const d = daysSince((j.first_detected || "").slice(0, 10)); return d !== null && d <= 7; });
  const closing = active.filter((j) => { const d = daysUntil(j.deadline); return d !== null && d >= 0 && d <= 7; });
  const prioritised = sortJobs(active, "relevance").sort((a, b) => (isHi(b) - isHi(a)) || (b._score - a._score));
  const recent = sortJobs(active, "detected").sort((a, b) => (b.first_detected || "").slice(0, 10).localeCompare((a.first_detected || "").slice(0, 10)) || (isHi(b) - isHi(a)) || (b._score - a._score));
  const deadlines = sortJobs(active.filter((j) => { const d = daysUntil(j.deadline); return d !== null && d >= 0; }), "deadline");
  const hiCountries = Object.keys((S.settings.geo || {}).high || { Switzerland: 1, Italy: 1 });
  const note = (S.meta.last_run || {}).bootstrap_note;
  const failed = (S.meta.last_run || {}).sources_failed || 0;
  main.innerHTML = `
    <div class="page-head"><div><h1>Dashboard</h1>
      <p>Last successful update ${esc(fmtStamp(S.meta.last_successful_update))}. Swiss and Milan roles are listed first and carry a red edge.</p></div>
      <a class="btn primary" href="#/jobs">Browse all opportunities</a></div>
    ${note ? `<div class="banner">${esc(note)}</div>` : ""}
    ${failed ? `<div class="banner warn">${failed} source(s) could not be read on the last run. Their postings keep their previous status. <a href="#/monitoring">See which ones</a></div>` : ""}
    <div class="figures">
      <div><b>${active.length}</b><span><a href="#/jobs">active opportunities</a></span></div>
      <div><b>${fresh.length}</b><span>new in the last 7 days</span></div>
      <div><b>${closing.length}</b><span>closing within 7 days</span></div>
      <div><b>${cov.monitored || 0}</b><span><a href="#/monitoring">companies monitored</a> of ${t.companies || 0}</span></div>
      <div><b>${t.companies_with_active_jobs || 0}</b><span>companies with active vacancies</span></div>
      <div><b>${active.filter(isHi).length}</b><span>in Switzerland or Milan</span></div>
    </div>
    <div class="grid g2">
      <section class="panel"><h2>Top matches</h2>
        ${prioritised.length ? `<ul class="rows">${prioritised.slice(0, 8).map((j) => jobRow(j, esc(j.seniority || ""))).join("")}</ul>` : `<p class="empty">No active opportunities yet. They appear after the first collection run.</p>`}</section>
      <section class="panel"><h2>Recently detected</h2>
        ${recent.length ? `<ul class="rows">${recent.slice(0, 8).map((j) => jobRow(j, "Detected " + fmtDate(j.first_detected))).join("")}</ul>` : `<p class="empty">Nothing detected yet.</p>`}</section>
    </div>
    <div class="grid g3" style="margin-top:16px">
      <section class="panel"><h2>By country</h2>${bars(countBy(active, (j) => j.country || "Not specified"), (k) => hiCountries.includes(k))}</section>
      <section class="panel"><h2>By sector</h2>${bars(countBy(active, (j) => j.sector))}</section>
      <section class="panel"><h2>By contract type</h2>${bars(countBy(active, (j) => j.contract_type))}</section>
    </div>
    <section class="panel" style="margin-top:16px"><h2>Upcoming deadlines</h2>
      ${deadlines.length ? `<ul class="rows">${deadlines.slice(0, 10).map((j) => jobRow(j, deadlineText(j))).join("")}</ul>`
        : `<p class="empty">None of the active postings publishes an application deadline. Many employers recruit on a rolling basis, so apply early.</p>`}</section>`;
}

// ------------------------------------------------------------------ jobs
const FILTER_DEFS = [
  ["priority", "Geographical priority", (j) => j.geo_priority],
  ["country", "Country", (j) => j.country || "Unknown"],
  ["city", "City", (j) => j.city || "Unknown"],
  ["sector", "Sector", (j) => j.sector],
  ["seniority", "Seniority", (j) => j.seniority],
  ["contract", "Contract type", (j) => j.contract_type],
  ["german", "German", (j) => j.german_flag],
  ["french", "French", (j) => j.french_flag],
  ["verification", "Verification", (j) => j.verification],
  ["origin", "Company list", (j) => j.company_origin],
  ["category", "Company category", (j) => j.company_category || "Unknown"],
  ["company", "Company", (j) => j.company],
  ["status", "Posting status", (j) => j.status],
];
const NICE = { REQUIRED: "Required", PREFERRED: "Preferred", "NOT REQUIRED": "Not required", "NOT MENTIONED": "Not mentioned",
  "VERIFIED OFFICIAL": "Verified official", "LINKEDIN ONLY": "LinkedIn only", "AGGREGATOR ONLY": "Aggregator only", UNVERIFIED: "Unverified",
  Excel: "Excel companies", Additional: "Additional companies" };
const blankFilter = () => ({ q: "", sort: "relevance", page: 1, minScore: 0, recentDays: 0, showClosed: false });
let F = Object.assign(blankFilter(), store.pref("jobFilter", {}));

function viewJobs() {
  const base = F.showClosed ? S.jobs : S.jobs.filter((j) => ACTIVE.includes(j.status));
  const groups = FILTER_DEFS.map(([key, label, fn]) => {
    const opts = countBy(base, fn);
    if (key === "priority") opts.sort((a, b) => ["High", "Medium", "Other", "Unknown"].indexOf(a[0]) - ["High", "Medium", "Other", "Unknown"].indexOf(b[0]));
    const sel = F[key] || [];
    return `<details ${sel.length || ["priority", "country", "sector"].includes(key) ? "open" : ""}><summary><span>${label}${sel.length ? `<span class="active-n">${sel.length} selected</span>` : ""}</span></summary>
      <div class="opts">${opts.map(([v, n]) => `<label class="opt"><input type="checkbox" data-f="${key}" value="${esc(v)}" ${sel.includes(v) ? "checked" : ""}><span>${esc(NICE[v] || v)}</span><em>${n}</em></label>`).join("")}</div></details>`;
  }).join("");
  main.innerHTML = `
    <div class="page-head"><div><h1>Job opportunities</h1><p id="jobs-sub"></p></div></div>
    <div class="toolbar">
      <input type="search" id="q" placeholder="Search title, company, city or sector" value="${esc(F.q)}" aria-label="Search opportunities">
      <label class="small" style="margin:0" for="sort">Sort by</label>
      <select id="sort" aria-label="Sort by">
        ${[["relevance", "Relevance"], ["newest", "Newest published"], ["detected", "Recently detected"], ["deadline", "Deadline"], ["priority", "Geographical priority"], ["company", "Company"]].map(([v, l]) => `<option value="${v}" ${F.sort === v ? "selected" : ""}>${l}</option>`).join("")}
      </select>
      <button class="btn filters-toggle" id="ftoggle" type="button" aria-expanded="false">Filters</button>
      <button class="btn" id="clear" type="button">Clear filters</button>
    </div>
    <div class="jobs-layout">
      <aside class="panel filters" id="filters" aria-label="Filters">
        <details open><summary><span>Match score and recency</span></summary><div class="opts" style="max-height:none">
          <label for="minScore">Minimum score: <b id="minScoreV">${F.minScore}</b></label>
          <input type="range" id="minScore" min="0" max="95" step="5" value="${F.minScore}" style="width:100%">
          <label for="recent" style="margin-top:8px">Published or detected within</label>
          <select id="recent" style="width:100%">${[[0, "Any time"], [3, "3 days"], [7, "7 days"], [14, "14 days"], [30, "30 days"]].map(([v, l]) => `<option value="${v}" ${Number(F.recentDays) === v ? "selected" : ""}>${l}</option>`).join("")}</select>
          <label class="opt" style="margin-top:8px"><input type="checkbox" id="closed" ${F.showClosed ? "checked" : ""}><span>Include expired and removed postings</span></label>
        </div></details>
        ${groups}
      </aside>
      <section><div id="results"></div></section>
    </div>`;
  const rerender = (resetPage = true) => { if (resetPage) F.page = 1; store.setPref("jobFilter", F); renderJobResults(); };
  $("#q").addEventListener("input", (e) => { F.q = e.target.value; rerender(); });
  $("#sort").addEventListener("change", (e) => { F.sort = e.target.value; rerender(); });
  $("#minScore").addEventListener("input", (e) => { F.minScore = Number(e.target.value); $("#minScoreV").textContent = F.minScore; rerender(); });
  $("#recent").addEventListener("change", (e) => { F.recentDays = Number(e.target.value); rerender(); });
  $("#closed").addEventListener("change", (e) => { F.showClosed = e.target.checked; store.setPref("jobFilter", F); viewJobs(); });
  $("#clear").addEventListener("click", () => { F = blankFilter(); store.setPref("jobFilter", F); viewJobs(); });
  $("#ftoggle").addEventListener("click", (e) => { const open = $("#filters").classList.toggle("open"); e.currentTarget.setAttribute("aria-expanded", String(open)); });
  $("#filters").addEventListener("change", (e) => {
    const key = e.target.dataset.f;
    if (!key) return;
    F[key] = $$(`input[data-f="${key}"]:checked`).map((i) => i.value);
    rerender();
  });
  renderJobResults();
}

function renderJobResults() {
  const list = sortJobs(filterJobs(S.jobs, F, { statusOf: store.statusOf }), F.sort);
  const pages = Math.max(1, Math.ceil(list.length / PAGE));
  F.page = Math.min(F.page, pages);
  const slice = list.slice((F.page - 1) * PAGE, F.page * PAGE);
  $("#jobs-sub").textContent = `${list.length} of ${S.jobs.filter((j) => F.showClosed || ACTIVE.includes(j.status)).length} postings shown`;
  const res = $("#results");
  if (!list.length) {
    res.innerHTML = `<div class="panel"><p class="empty">No posting matches these filters. Clear a filter or lower the minimum score.</p></div>`;
    return;
  }
  res.innerHTML = `<div class="table-wrap"><table class="jobs-table">
    <thead><tr><th>Match</th><th>Role and company</th><th>Location</th><th>Sector</th><th>Contract</th><th>Published / deadline</th><th>German</th><th><span class="sr">Actions</span></th></tr></thead>
    <tbody>${slice.map((j) => `<tr class="${isHi(j) ? "hi" : ""}">
      <td class="c-score">${scoreHTML(j)}</td>
      <td class="c-role"><a class="t" href="#/job/${esc(j.id)}">${esc(j.title)}</a><div class="c">${esc(j.company)}</div>
        <div class="tags">${verifTag(j)} ${j.company_origin === "Additional" ? '<span class="tag line">Additional company</span>' : ""} ${j.status !== "Open" ? statusTag(j) : ""} ${trackTag(j.id)}</div></td>
      <td data-l="Location">${esc(where(j))}${(j.locations || []).length > 1 ? ` <span class="muted">+${j.locations.length - 1}</span>` : ""}</td>
      <td data-l="Sector">${esc(j.sector || "")}</td>
      <td data-l="Contract">${esc(j.contract_type || "")}</td>
      <td class="c-dates"><div data-l="Published">${j.published ? fmtDate(j.published) : '<span class="muted">Unknown</span>'}</div><div data-l="Deadline">${deadlineText(j)}</div></td>
      <td data-l="German">${flagTag("", j.german_flag)}</td>
      <td class="c-act nowrap">${link(j.apply_url, "Apply", "btn sm primary")} <button class="btn sm" type="button" data-save="${esc(j.id)}" aria-pressed="${store.statusOf(j.id) !== "New"}">${store.statusOf(j.id) === "New" ? "Save" : "Saved"}</button></td>
    </tr>`).join("")}</tbody></table></div>
    <div class="pager"><span>Page ${F.page} of ${pages}</span><span>
      <button class="btn sm" type="button" id="prev" ${F.page <= 1 ? "disabled" : ""}>Previous</button>
      <button class="btn sm" type="button" id="next" ${F.page >= pages ? "disabled" : ""}>Next</button></span></div>`;
  $("#prev").addEventListener("click", () => { F.page--; renderJobResults(); window.scrollTo(0, 0); });
  $("#next").addEventListener("click", () => { F.page++; renderJobResults(); window.scrollTo(0, 0); });
  $$("[data-save]", res).forEach((b) => b.addEventListener("click", () => {
    const j = S.jobs.find((x) => x.id === b.dataset.save);
    if (store.statusOf(j.id) === "New") { store.set(j.id, { status: "Saved" }, j); toast("Saved to My applications"); }
    else { store.remove(j.id); toast("Removed from My applications"); }
    refreshNav(); renderJobResults();
  }));
}

// ------------------------------------------------------------------ job detail
function trackerForm(id, job) {
  const a = store.get(id) || { status: "New", notes: "", applied_date: "", interview_date: "", outcome: "" };
  return `<section class="panel" id="tracker"><h2>My application</h2>
    <div class="field"><label for="t-status">Status</label><select id="t-status" style="width:100%">${STATUSES.map((s) => `<option ${a.status === s ? "selected" : ""}>${s}</option>`).join("")}</select></div>
    <div class="field-row"><div class="field"><label for="t-applied">Applied on</label><input type="date" id="t-applied" value="${esc(a.applied_date || "")}" style="width:100%"></div>
      <div class="field"><label for="t-interview">Interview on</label><input type="date" id="t-interview" value="${esc(a.interview_date || "")}" style="width:100%"></div></div>
    <div class="field"><label for="t-outcome">Outcome</label><input type="text" id="t-outcome" value="${esc(a.outcome || "")}" placeholder="e.g. second round, offer declined" style="width:100%"></div>
    <div class="field"><label for="t-notes">Notes</label><textarea id="t-notes" placeholder="Contacts, referral, what to prepare">${esc(a.notes || "")}</textarea></div>
    <div class="toolbar" style="margin:0"><button class="btn primary" type="button" id="t-save">Save changes</button>
      ${store.get(id) ? `<button class="btn danger" type="button" id="t-del">Remove from my list</button>` : ""}</div>
    <p class="small muted" style="margin:10px 0 0">Stored in this browser only. Export a backup from My applications.</p></section>`;
}
function bindTracker(id, job, after) {
  $("#t-save").addEventListener("click", () => {
    let status = $("#t-status").value;
    if (status === "New") status = "Saved";
    store.set(id, { status, applied_date: $("#t-applied").value, interview_date: $("#t-interview").value, outcome: $("#t-outcome").value.trim(), notes: $("#t-notes").value }, job);
    refreshNav(); toast("Saved"); after();
  });
  const del = $("#t-del");
  if (del) del.addEventListener("click", () => { store.remove(id); refreshNav(); toast("Removed from My applications"); after(); });
}

function viewJob(id) {
  const j = S.jobs.find((x) => x.id === id || (x.aliases || []).includes(id));
  if (!j) {
    const a = store.get(id);
    main.innerHTML = `<div class="panel"><h1>This posting is no longer in the public database</h1>
      ${a && a.job ? `<p>${esc(a.job.title)} at ${esc(a.job.company)}. Your notes are still in <a href="#/applications">My applications</a>.</p>` : `<p class="muted">It may have been merged with another record. <a href="#/jobs">Back to all opportunities</a></p>`}</div>`;
    return;
  }
  const d = j.score_detail || { breakdown: {}, positives: [], negatives: [], missing: [] };
  const langs = (j.languages || []).map((l) => `<li><b>${esc(l.language)}</b>: ${esc(l.requirement.replace("_", " "))}${l.level ? `, level ${esc(l.level)}` : ""}<br><span class="muted">"${esc(l.evidence)}"</span></li>`).join("");
  const list = (items) => items && items.length ? `<ul class="explain">${items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : `<p class="small muted">None.</p>`;
  main.innerHTML = `
    <p class="small"><a href="#/jobs">All opportunities</a></p>
    <div class="detail-head ${isHi(j) ? "hi" : ""}">
      <h1>${esc(j.title)}</h1>
      <p style="font-size:17px;margin:2px 0 10px">${esc(j.company)} <span class="muted">${esc(where(j))}</span></p>
      <p>${statusTag(j)} ${verifTag(j)} ${flagTag("German", j.german_flag)} ${flagTag("French", j.french_flag)} <span class="tag">${esc(j.geo_priority)} priority</span> ${j.company_origin === "Additional" ? '<span class="tag line">Additional company</span>' : '<span class="tag line">Excel company</span>'}</p>
      ${j.status_note ? `<p class="small muted">${esc(j.status_note)}</p>` : ""}
      <div class="toolbar" style="margin:14px 0 0">${link(j.apply_url, "Apply on the employer's site", "btn primary big") || '<span class="muted">No application link published</span>'}
        ${j.source_url && j.source_url !== j.apply_url ? link(j.source_url, "View original posting", "btn") : ""}</div>
    </div>
    <div class="detail"><div class="stack">
      <section class="panel"><h2>Posting details</h2><dl class="kv">
        <dt>Company</dt><dd>${esc(j.company)} <span class="muted">(${esc(j.company_category || "category unknown")})</span></dd>
        <dt>Location</dt><dd>${esc(where(j))}${(j.locations || []).length > 1 ? `<br><span class="muted small">Also: ${esc(j.locations.slice(1).map((l) => [l.city, l.country].filter(Boolean).join(", ")).join("; "))}</span>` : ""}</dd>
        <dt>Sector</dt><dd>${esc(j.sector || "Unknown")}${j.sector_source === "company category" ? ' <span class="muted small">(inferred from the company category)</span>' : ""}</dd>
        <dt>Seniority</dt><dd>${esc(j.seniority || "Unknown")}${j.seniority_warning ? `<br><span class="tag warn" style="white-space:normal">${esc(j.seniority_warning)}</span>` : ""}</dd>
        <dt>Contract type</dt><dd>${esc(j.contract_type || "Not specified")}</dd>
        <dt>Experience</dt><dd>${esc(j.experience || "Not specified")}</dd>
        <dt>Published</dt><dd>${j.published ? fmtDate(j.published) : "Unknown"}</dd>
        <dt>Application deadline</dt><dd>${deadlineText(j)}${j.deadline_source ? ` <span class="muted small">(${esc(j.deadline_source)})</span>` : ""}</dd>
        <dt>Salary</dt><dd>${esc(j.salary || "Not specified")}</dd>
        <dt>Visa sponsorship</dt><dd>${esc(j.visa_sponsorship || "Not specified")}${j.visa_note ? `<br><span class="muted small">"${esc(j.visa_note)}"</span>` : ""}</dd>
        <dt>Department</dt><dd>${esc(j.department || "Not specified")}</dd>
        <dt>First detected</dt><dd>${fmtDate(j.first_detected)}</dd>
        <dt>Last checked</dt><dd>${fmtDate(j.last_checked)}</dd>
        <dt>Last modified</dt><dd>${fmtDate(j.last_modified)}</dd>
        <dt>Job ID</dt><dd>${esc(j.id)} <span class="muted">(source reference ${esc(j.external_id || "n/a")})</span></dd>
      </dl></section>
      <section class="panel"><h2>Languages</h2>
        ${langs ? `<ul class="explain">${langs}</ul>` : `<p class="small muted">${j.languages_analysed === false ? "No description was available, so language requirements could not be checked." : "The posting does not name any language requirement. That does not mean English alone is enough."}</p>`}</section>
      <section class="panel"><h2>Description</h2>${j.description ? `<div class="desc">${esc(j.description)}</div>` : `<p class="muted">The source did not provide a description.</p>`}</section>
      <section class="panel"><h2>Sources</h2><dl class="kv">
        ${(j.sources || []).map((s) => `<dt>${esc(s.type)}</dt><dd>${link(s.url, s.url) || esc(s.url || "")}<br><span class="muted small">${esc((VERIF[s.verification] || ["", s.verification || ""])[1])}, first seen ${fmtDate(s.first_seen)}, last seen ${fmtDate(s.last_seen)}</span></dd>`).join("")}
      </dl>${(j.notes || []).length ? `<h3>Notes</h3>${list(j.notes)}` : ""}</section>
    </div><div class="stack">
      <section class="panel"><h2>Match score: ${j._score} of 100</h2>
        ${CRITERIA.map((k) => { const p = d.breakdown[k] || { points: 0, max: 0, note: "" }; return `<div class="crit"><span>${CRIT_LABEL[k]}</span><span class="track"><span class="fill" style="width:${p.max ? Math.round((p.points / p.max) * 100) : 0}%"></span></span><span class="nowrap">${p.points} / ${p.max}</span><small>${esc(p.note || "")}</small></div>`; }).join("")}
        ${store.pref("weights", null) ? `<p class="small muted">Total uses your own weights from Monitoring. Points shown are the published defaults.</p>` : ""}
        <h3>In favour</h3>${list(d.positives)}<h3>Possible drawbacks</h3>${list(d.negatives)}<h3>Missing or unverified</h3>${list(d.missing)}</section>
      ${trackerForm(j.id, j)}
    </div></div>`;
  bindTracker(j.id, j, () => viewJob(id));
}

// ------------------------------------------------------------------ companies
const MON = { monitored: ["ok", "Monitored"], failed: ["bad", "Check failed"], pending: ["info", "Awaiting analysis"], manual_check: ["warn", "Manual check"], unreachable: ["bad", "Portal unreachable"], no_portal: ["line", "No portal on file"], not_approved: ["warn", "Not monitored until approved"] };
let CF = { q: "", origin: "", category: "", country: "", mon: "", page: 1 };
async function viewCompanies() {
  main.innerHTML = `<p class="loading">Loading the company directory…</p>`;
  const db = await lazy("companies", "data/companies.json");
  const comps = db.companies;
  const per = S.meta.companies || {};
  const uniq = (fn) => [...new Set(comps.flatMap(fn).filter(Boolean))].sort();
  const pending = comps.filter((c) => c.status === "pending_review");
  main.innerHTML = `
    <div class="page-head"><div><h1>Companies</h1><p>${comps.length} companies: ${comps.filter((c) => c.origin === "excel").length} from your Excel, ${comps.filter((c) => c.origin !== "excel").length} additional${pending.length ? ` (${pending.length} awaiting your review)` : ""}.</p></div></div>
    <div class="toolbar">
      <input type="search" id="cq" placeholder="Search company or city" value="${esc(CF.q)}" aria-label="Search companies">
      <select id="c-origin" aria-label="Company list"><option value="">Excel and additional</option><option value="excel">Excel companies</option><option value="additional">Additional companies</option><option value="pending">Awaiting review</option></select>
      <select id="c-category" aria-label="Category"><option value="">All categories</option>${uniq((c) => [c.category_en]).map((v) => `<option>${esc(v)}</option>`).join("")}</select>
      <select id="c-country" aria-label="Country"><option value="">All countries</option>${uniq((c) => c.offices.map((o) => o.country)).map((v) => `<option>${esc(v)}</option>`).join("")}</select>
      <select id="c-mon" aria-label="Monitoring status"><option value="">Any monitoring status</option>${Object.entries(MON).map(([k, v]) => `<option value="${k}">${v[1]}</option>`).join("")}<option value="jobs">With active vacancies</option></select>
    </div><div id="cres"></div>`;
  for (const [id, key] of [["c-origin", "origin"], ["c-category", "category"], ["c-country", "country"], ["c-mon", "mon"]]) {
    $("#" + id).value = CF[key];
    $("#" + id).addEventListener("change", (e) => { CF[key] = e.target.value; CF.page = 1; draw(); });
  }
  $("#cq").addEventListener("input", (e) => { CF.q = e.target.value; CF.page = 1; draw(); });
  function draw() {
    const q = CF.q.trim().toLowerCase();
    const list = comps.filter((c) => {
      const m = per[c.id] || {};
      if (CF.origin === "pending" ? c.status !== "pending_review" : CF.origin && c.origin !== CF.origin) return false;
      if (CF.category && c.category_en !== CF.category) return false;
      if (CF.country && !c.offices.some((o) => o.country === CF.country)) return false;
      if (CF.mon === "jobs" ? !m.active_jobs : CF.mon && m.monitoring !== CF.mon) return false;
      if (q && !`${c.name} ${c.offices.map((o) => o.city).join(" ")} ${(c.aliases || []).join(" ")}`.toLowerCase().includes(q)) return false;
      return true;
    }).sort((a, b) => ((per[b.id] || {}).active_jobs || 0) - ((per[a.id] || {}).active_jobs || 0) || a.name.localeCompare(b.name));
    const pages = Math.max(1, Math.ceil(list.length / PAGE));
    CF.page = Math.min(CF.page, pages);
    const slice = list.slice((CF.page - 1) * PAGE, CF.page * PAGE);
    $("#cres").innerHTML = !list.length ? `<div class="panel"><p class="empty">No company matches. Clear the search or a filter.</p></div>` : `
      <div class="table-wrap"><table><thead><tr><th>Company</th><th>Category</th><th>Offices</th><th>Website and career portal</th><th>Recruitment system</th><th>Active</th><th>Last successful check</th><th>Monitoring</th></tr></thead><tbody>
      ${slice.map((c) => { const m = per[c.id] || { monitoring: "no_portal", ats: [] }; const [cls, lbl] = MON[m.monitoring] || MON.no_portal; const hi = c.priority === "High";
        return `<tr class="${hi ? "hi" : ""}"><td><span class="t">${esc(c.name)}</span><div>${c.origin === "excel" ? '<span class="tag line">Excel</span>' : `<span class="tag info">Additional</span>${c.status === "pending_review" ? ' <span class="tag warn">Awaiting review</span>' : c.status === "rejected" ? ' <span class="tag line">Rejected</span>' : ""}`}${c.junior_programmes === "yes" ? ' <span class="tag">Junior programmes</span>' : ""}</div>
          ${c.reason_for_inclusion ? `<div class="small muted">${esc(c.reason_for_inclusion)} (found ${esc(c.discovery_date || "")})</div>` : ""}</td>
          <td>${esc(c.category_en || c.category || "")}</td>
          <td>${esc([...new Set(c.offices.map((o) => o.city))].filter(Boolean).join(", "))}<div class="muted">${esc([...new Set(c.offices.map((o) => o.country))].filter(Boolean).join(", "))}</div></td>
          <td>${link(c.website, "Website") || `<span class="muted">${esc(c.website_note || "Not on file")}</span>`}<br>${link(c.career_url, "Career portal") || `<span class="muted">${esc(c.career_note || "Not on file")}</span>`}
            <br><a class="small" target="_blank" rel="noopener noreferrer" href="https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(c.name)}&f_E=1%2C2&sortBy=DD">Search LinkedIn</a></td>
          <td>${esc((m.ats || []).join(", ") || "Unknown")}</td>
          <td>${m.active_jobs ? `<a href="#/jobs" data-company="${esc(c.name)}"><b>${m.active_jobs}</b></a>` : "0"}</td>
          <td class="nowrap">${m.last_success ? fmtDate(m.last_success) : '<span class="muted">Never</span>'}</td>
          <td><span class="tag ${cls}">${lbl}</span></td></tr>`; }).join("")}
      </tbody></table></div>
      <div class="pager"><span>${list.length} companies, page ${CF.page} of ${pages}</span><span>
        <button class="btn sm" type="button" id="cprev" ${CF.page <= 1 ? "disabled" : ""}>Previous</button>
        <button class="btn sm" type="button" id="cnext" ${CF.page >= pages ? "disabled" : ""}>Next</button></span></div>`;
    const p = $("#cprev"), n = $("#cnext");
    if (p) p.addEventListener("click", () => { CF.page--; draw(); window.scrollTo(0, 0); });
    if (n) n.addEventListener("click", () => { CF.page++; draw(); window.scrollTo(0, 0); });
    $$("[data-company]").forEach((a) => a.addEventListener("click", () => { F = Object.assign(blankFilter(), { company: [a.dataset.company] }); store.setPref("jobFilter", F); }));
  }
  draw();
}

// ------------------------------------------------------------------ early careers
async function viewEarly() {
  const focus = await lazy("focus", "data/excel_focus_notes.json").catch(() => ({ items: [] }));
  const active = S.jobs.filter((j) => ACTIVE.includes(j.status));
  const groups = [["Summer Analyst", "Summer analyst and spring programmes"], ["Off-cycle", "Off-cycle and long internships"], ["Graduate Programme", "Graduate programmes"], ["Internship", "Other internships"], ["Working Student", "Working student roles"], ["Trainee", "Trainee and apprenticeship roles"]];
  const future = active.filter((j) => j.status === "Future Application Window");
  const open = active.filter((j) => j.status !== "Future Application Window");
  const deadlines = sortJobs(open.filter((j) => groups.some(([k]) => k === j.seniority) && daysUntil(j.deadline) !== null && daysUntil(j.deadline) >= 0), "deadline");
  const section = ([key, title]) => {
    const list = sortJobs(open.filter((j) => j.seniority === key), "priority");
    if (!list.length) return "";
    return `<section class="panel"><h2>${title} <span class="muted" style="font-weight:400">${list.length} open now</span></h2>
      <ul class="rows">${list.slice(0, 25).map((j) => jobRow(j, (j.programme_year ? `${j.programme_year} intake, ` : "") + (j.deadline ? "deadline " + fmtDate(j.deadline) : "no deadline published"))).join("")}</ul></section>`;
  };
  const cols = focus.items.length ? Object.keys(focus.items[0]).filter((k) => k !== "sheet") : [];
  main.innerHTML = `
    <div class="page-head"><div><h1>Early careers</h1><p>Programmes that are open now are listed separately from application windows that have only been announced.</p></div></div>
    <div class="stack">
      <section class="panel"><h2>Announced, not yet open</h2>
        ${future.length ? `<ul class="rows">${future.map((j) => jobRow(j, esc(j.status_note || ""))).join("")}</ul>` : `<p class="empty">No employer currently announces a future application window on a monitored portal.</p>`}</section>
      <section class="panel"><h2>Upcoming programme deadlines</h2>
        ${deadlines.length ? `<ul class="rows">${deadlines.slice(0, 15).map((j) => jobRow(j, deadlineText(j))).join("")}</ul>` : `<p class="empty">No open programme publishes a deadline. Most of these recruit on a rolling basis.</p>`}</section>
      ${groups.map(section).join("") || `<section class="panel"><p class="empty">No early-career programme is open on the monitored portals right now.</p></section>`}
      ${focus.items.length ? `<section class="panel"><h2>Recruiting cycles noted in your Excel</h2>
        <p class="small muted">From the worksheet "${esc(focus.items[0].sheet)}" of ${esc(focus.source_file || "your Excel")}. These are your own notes, not live postings.</p>
        <div class="table-wrap" style="border:0"><table><thead><tr>${cols.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead>
        <tbody>${focus.items.map((r) => `<tr>${cols.map((c) => `<td>${esc(r[c] || "")}</td>`).join("")}</tr>`).join("")}</tbody></table></div></section>` : ""}
    </div>`;
}

// ------------------------------------------------------------------ applications
function viewApplications() {
  const apps = store.all();
  const ids = Object.keys(apps);
  const byId = new Map(S.jobs.map((j) => [j.id, j]));
  const order = STATUSES.filter((s) => s !== "New");
  const row = (id) => {
    const a = apps[id], j = byId.get(id), info = j || a.job || {};
    const dl = (j && j.deadline) || (a.job && a.job.deadline);
    const left = daysUntil(dl);
    return `<div class="app" data-id="${esc(id)}">
      <div><a class="t" href="#/job/${esc(id)}" style="font-weight:700;color:var(--ink)">${esc(info.title || "Posting")}</a>
        <div class="small muted">${esc(info.company || "")}${info.city ? ", " + esc(info.city) : ""}${!j ? ' <span class="tag line">no longer listed</span>' : j.status !== "Open" ? " " + statusTag(j) : ""}</div>
        <div class="small">${dl ? `Deadline ${fmtDate(dl)}${left !== null && left >= 0 && left <= 7 ? ` <span class="tag warn">${left} d left</span>` : ""}` : '<span class="muted">No deadline published</span>'} ${link(info.apply_url, "Apply", "")}</div></div>
      <div><label>Status</label><select data-k="status">${order.map((s) => `<option ${a.status === s ? "selected" : ""}>${s}</option>`).join("")}</select></div>
      <div><label>Applied on</label><input type="date" data-k="applied_date" value="${esc(a.applied_date || "")}"></div>
      <div><label>Interview on</label><input type="date" data-k="interview_date" value="${esc(a.interview_date || "")}"></div>
      <div><label>&nbsp;</label><button class="btn sm danger" type="button" data-del>Remove</button></div>
      <input type="text" data-k="outcome" value="${esc(a.outcome || "")}" placeholder="Outcome" aria-label="Outcome" style="grid-column:1/3">
      <textarea data-k="notes" placeholder="Notes" aria-label="Notes">${esc(a.notes || "")}</textarea></div>`;
  };
  main.innerHTML = `
    <div class="page-head"><div><h1>My applications</h1><p>${ids.length} tracked. Everything on this page is stored in this browser on this device only: it is never uploaded, and it does not sync to your phone or another browser. Use the backup to move it.</p></div>
      <div class="toolbar" style="margin:0"><button class="btn" id="exp" type="button">Export backup (JSON)</button>
        <label class="btn" style="margin:0;color:var(--ink)" for="imp">Import backup</label><input type="file" id="imp" accept="application/json,.json" hidden>
        <button class="btn danger" id="reset" type="button">Delete all local data</button></div></div>
    <div class="board">${ids.length ? order.map((s) => { const list = ids.filter((id) => apps[id].status === s).sort((a, b) => (apps[b].updated || "").localeCompare(apps[a].updated || ""));
      return list.length ? `<h2>${s}<span class="muted" style="font-weight:400">${list.length}</span></h2>${list.map(row).join("")}` : ""; }).join("")
      : `<div class="panel"><p class="empty">Nothing saved yet. Open <a href="#/jobs">Job opportunities</a> and choose Save on a posting to start tracking it.</p></div>`}</div>`;
  $$(".app").forEach((el) => {
    const id = el.dataset.id;
    $$("[data-k]", el).forEach((inp) => inp.addEventListener("change", () => {
      store.set(id, { [inp.dataset.k]: inp.value }, byId.get(id));
      toast("Saved");
      if (inp.dataset.k === "status") viewApplications();
    }));
    $("[data-del]", el).addEventListener("click", () => { store.remove(id); refreshNav(); toast("Removed from My applications"); viewApplications(); });
  });
  $("#exp").addEventListener("click", () => {
    const blob = new Blob([store.exportJSON()], { type: "application/json" });
    const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: `applications-backup-${new Date().toISOString().slice(0, 10)}.json` });
    document.body.append(a); a.click(); a.remove(); URL.revokeObjectURL(a.href);
    toast("Backup exported");
  });
  $("#imp").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try { const r = store.importJSON(await file.text(), "merge"); toast(`Imported: ${r.added} added, ${r.updated} updated, ${r.skipped} unchanged`); }
    catch (err) { toast("Import failed: " + err.message); }
    refreshNav(); viewApplications();
  });
  let armed = false;
  $("#reset").addEventListener("click", (e) => {
    if (!armed) { armed = true; e.currentTarget.textContent = "Click again to delete everything"; setTimeout(() => { armed = false; const b = $("#reset"); if (b) b.textContent = "Delete all local data"; }, 4000); return; }
    store.reset(); refreshNav(); toast("All local application data deleted"); viewApplications();
  });
}

// ------------------------------------------------------------------ monitoring / settings
async function viewMonitoring() {
  main.innerHTML = `<p class="loading">Loading source coverage…</p>`;
  const [srcDb, compDb] = await Promise.all([lazy("sources", "data/sources.json"), lazy("companies", "data/companies.json")]);
  const name = new Map(compDb.companies.map((c) => [c.id, c.name]));
  const t = S.meta.totals || {}, cov = S.meta.coverage || {}, run = S.meta.last_run || {};
  const sources = srcDb.sources;
  const failed = sources.filter((s) => s.status === "error" || s.status === "unreachable");
  const live = sources.filter((s) => s.ats && ["ok", "error", "unverified"].includes(s.status));
  const manual = sources.filter((s) => ["unsupported", "no_structured_data"].includes(s.status));
  const w = store.pref("weights", null) || (S.settings.scoring || {}).weights || {};
  const custom = !!store.pref("weights", null);
  main.innerHTML = `
    <div class="page-head"><div><h1>Monitoring and settings</h1><p>Which companies are actually being read, which are not, and why. A company without vacancies is never the same thing as a company whose portal could not be read.</p></div></div>
    ${run.bootstrap_note ? `<div class="banner">${esc(run.bootstrap_note)}</div>` : ""}
    <div class="figures">
      <div><b>${t.companies || 0}</b><span>companies in the database</span></div>
      <div><b>${cov.monitored || 0}</b><span>read successfully</span></div>
      <div><b>${t.companies_with_active_jobs || 0}</b><span>with active opportunities</span></div>
      <div><b>${t.monitored_without_jobs || 0}</b><span>read, no matching vacancy</span></div>
      <div><b>${(cov.failed || 0) + (cov.unreachable || 0)}</b><span>portal unavailable or failed</span></div>
      <div><b>${(cov.pending || 0) + (cov.manual_check || 0)}</b><span>awaiting analysis or manual check</span></div>
    </div>
    <div class="grid g2">
      <section class="panel"><h2>Last run</h2><dl class="kv">
        <dt>Last successful update</dt><dd>${esc(fmtStamp(S.meta.last_successful_update))}</dd>
        <dt>Last attempt</dt><dd>${esc(fmtStamp(run.finished || run.started))}</dd>
        <dt>Sources attempted</dt><dd>${run.sources_attempted ?? 0} (${run.sources_ok ?? 0} ok, ${run.sources_failed ?? 0} failed)</dd>
        <dt>Postings read</dt><dd>${run.jobs_listed ?? 0}</dd>
        <dt>New, modified, removed</dt><dd>${run.new ?? 0}, ${run.modified ?? 0}, ${run.removed ?? 0}</dd>
        <dt>No portal on file</dt><dd>${cov.no_portal || 0} companies (the Excel lists them for direct approach)</dd>
        <dt>Additional, awaiting approval</dt><dd>${cov.not_approved || 0} companies <a href="#/companies" id="go-pending">review them</a></dd>
        ${run.aggregators ? `<dt>Job boards</dt><dd>${esc(typeof run.aggregators.adzuna === "string" ? "Adzuna: " + run.aggregators.adzuna : "Adzuna: " + JSON.stringify(run.aggregators.adzuna))}</dd>` : ""}
      </dl></section>
      <section class="panel"><h2>Coverage by recruitment system</h2>${bars(countBy(live, (s) => s.ats === "jsonld" ? "career site (structured data)" : s.ats), () => false, 12)}
        <h3>LinkedIn</h3><p class="small muted">${esc((S.meta.linkedin || {}).note || "")} Each company in the directory has a LinkedIn search link; a posting you find there can be added with scripts/add_manual_job.py and is labelled LinkedIn only.</p></section>
    </div>
    <section class="panel" style="margin-top:16px"><h2>Sources that failed <span class="muted" style="font-weight:400">${failed.length}</span></h2>
      ${failed.length ? `<div class="table-wrap" style="border:0"><table><thead><tr><th>Company</th><th>Source</th><th>Error</th><th>Failures in a row</th><th>Last success</th></tr></thead><tbody>
        ${failed.slice(0, 200).map((s) => `<tr><td>${esc(name.get(s.company_id) || s.company_id)}</td><td>${esc(s.ats || s.type)}<br>${link(s.url, "open") || ""}</td><td>${esc(s.last_error || "")}</td><td>${s.consecutive_failures || 0}</td><td class="nowrap">${s.last_success ? fmtDate(s.last_success) : "Never"}</td></tr>`).join("")}</tbody></table></div>`
        : `<p class="empty">Every source that was attempted on the last run answered.</p>`}</section>
    <section class="panel" style="margin-top:16px"><h2>Sources read on the last run <span class="muted" style="font-weight:400">${live.length}</span></h2>
      <div class="table-wrap" style="border:0"><table><thead><tr><th>Company</th><th>System</th><th>Status</th><th>Postings on board</th><th>Matching</th><th>Last success</th><th>Evidence</th></tr></thead><tbody>
      ${live.sort((a, b) => (b.relevant_jobs || 0) - (a.relevant_jobs || 0)).slice(0, 300).map((s) => `<tr><td>${esc(name.get(s.company_id) || s.company_id)}</td><td>${esc(s.ats)}</td><td><span class="tag ${s.status === "ok" ? "ok" : s.status === "error" ? "bad" : "info"}">${s.status === "ok" ? "Read" : s.status === "error" ? "Failed" : "Not yet read"}</span></td><td>${s.jobs_found ?? ""}</td><td>${s.relevant_jobs ?? ""}</td><td class="nowrap">${s.last_success ? fmtDate(s.last_success) : "Never"}</td><td class="small muted">${esc(s.evidence || "")}</td></tr>`).join("")}</tbody></table></div></section>
    ${manual.length ? `<section class="panel" style="margin-top:16px"><h2>Check by hand <span class="muted" style="font-weight:400">${manual.length}</span></h2><p class="small muted">The career page answers, but it cannot be read automatically.</p>
      <div class="table-wrap" style="border:0"><table><thead><tr><th>Company</th><th>Why</th><th></th></tr></thead><tbody>${manual.slice(0, 300).map((s) => `<tr><td>${esc(name.get(s.company_id) || "")}</td><td class="small">${esc(s.evidence || "")}</td><td>${link(s.url, "Open career page")}</td></tr>`).join("")}</tbody></table></div></section>` : ""}
    <section class="panel" style="margin-top:16px"><h2>Scoring weights</h2>
      <p class="small muted">The published scores use the weights in config/settings.json. You can try your own here: they are applied in this browser only${custom ? " (currently active)" : ""}.</p>
      <div class="grid g3">${CRITERIA.map((k) => `<div><label for="w-${k}">${CRIT_LABEL[k]}: <b id="wv-${k}">${Number(w[k] || 0)}</b></label><input type="range" id="w-${k}" data-w="${k}" min="0" max="50" step="5" value="${Number(w[k] || 0)}" style="width:100%"></div>`).join("")}</div>
      <div class="toolbar" style="margin:12px 0 0"><button class="btn primary" id="w-save" type="button">Apply my weights</button><button class="btn" id="w-reset" type="button">Use the published weights</button></div></section>`;
  const gp = $("#go-pending"); if (gp) gp.addEventListener("click", () => { CF = { q: "", origin: "pending", category: "", country: "", mon: "", page: 1 }; });
  $$("[data-w]").forEach((r) => r.addEventListener("input", () => { $("#wv-" + r.dataset.w).textContent = r.value; }));
  $("#w-save").addEventListener("click", () => { const nw = {}; $$("[data-w]").forEach((r) => { nw[r.dataset.w] = Number(r.value); }); store.setPref("weights", nw); applyWeights(); toast("Your weights are applied"); viewMonitoring(); });
  $("#w-reset").addEventListener("click", () => { store.setPref("weights", null); applyWeights(); toast("Published weights restored"); viewMonitoring(); });
}

// ------------------------------------------------------------------ theme
$("#theme").addEventListener("click", () => {
  const cur = document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const next = cur === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  store.setPref("theme", next);
});

boot();
