// Pure helpers: filtering, sorting, date maths, score re-weighting. No DOM access.
export const ACTIVE = ["Open", "Closing Soon", "Future Application Window", "Verification Failed"];
const DAY = 86400000;

export const daysUntil = (iso, now = new Date()) => {
  if (!iso) return null;
  const d = new Date(iso.slice(0, 10) + "T00:00:00Z");
  const t = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  return Math.round((d - t) / DAY);
};
export const daysSince = (iso, now = new Date()) => { const d = daysUntil(iso, now); return d === null ? null : -d; };

// Score with the visitor's own weights, derived from the published breakdown.
export function reweight(job, weights) {
  const b = job.score_detail && job.score_detail.breakdown;
  if (!weights || !b) return job.score || 0;
  const total = Object.values(weights).reduce((a, x) => a + Number(x || 0), 0) || 1;
  let sum = 0;
  for (const [k, part] of Object.entries(b)) {
    const frac = part.max ? part.points / part.max : 0;
    sum += frac * (Number(weights[k] || 0) / total) * 100;
  }
  return Math.round(sum);
}

const has = (list, v) => !list || !list.length || list.includes(v);

export function filterJobs(jobs, f, ctx = {}) {
  const q = (f.q || "").trim().toLowerCase();
  const terms = q ? q.split(/\s+/) : [];
  const now = ctx.now || new Date();
  return jobs.filter((j) => {
    if (!f.showClosed && !ACTIVE.includes(j.status)) return false;
    if (!has(f.country, j.country || "Unknown")) return false;
    if (!has(f.city, j.city || "Unknown")) return false;
    if (!has(f.priority, j.geo_priority)) return false;
    if (!has(f.company, j.company)) return false;
    if (!has(f.category, j.company_category || "Unknown")) return false;
    if (!has(f.sector, j.sector)) return false;
    if (!has(f.seniority, j.seniority)) return false;
    if (!has(f.contract, j.contract_type)) return false;
    if (!has(f.verification, j.verification)) return false;
    if (!has(f.origin, j.company_origin)) return false;
    if (!has(f.status, j.status)) return false;
    if (f.german && f.german.length && !f.german.includes(j.german_flag)) return false;
    if (f.french && f.french.length && !f.french.includes(j.french_flag)) return false;
    if (f.minScore && (j._score ?? j.score ?? 0) < f.minScore) return false;
    if (f.recentDays) {
      const ref = j.published || (j.first_detected || "").slice(0, 10);
      const age = daysSince(ref, now);
      if (age === null || age > f.recentDays) return false;
    }
    if (f.tracked && f.tracked.length && ctx.statusOf && !f.tracked.includes(ctx.statusOf(j.id))) return false;
    if (terms.length) {
      const hay = `${j.title} ${j.company} ${j.city || ""} ${j.country || ""} ${j.sector || ""} ${j.department || ""}`.toLowerCase();
      if (!terms.every((t) => hay.includes(t))) return false;
    }
    return true;
  });
}

const PRIORITY_RANK = { High: 0, Medium: 1, Other: 2, Unknown: 3 };
export function sortJobs(jobs, key) {
  const score = (j) => j._score ?? j.score ?? 0;
  const cmp = {
    relevance: (a, b) => score(b) - score(a) || (PRIORITY_RANK[a.geo_priority] ?? 9) - (PRIORITY_RANK[b.geo_priority] ?? 9),
    // by publication date, newest first; postings without one go last (ordered by when they were detected)
    newest: (a, b) => (!!b.published - !!a.published) || (b.published || "").localeCompare(a.published || "")
      || (b.first_detected || "").localeCompare(a.first_detected || "") || score(b) - score(a),
    detected: (a, b) => (b.first_detected || "").localeCompare(a.first_detected || "") || score(b) - score(a),
    deadline: (a, b) => (a.deadline || "9999").localeCompare(b.deadline || "9999") || score(b) - score(a),
    company: (a, b) => a.company.localeCompare(b.company) || score(b) - score(a),
    priority: (a, b) => (PRIORITY_RANK[a.geo_priority] ?? 9) - (PRIORITY_RANK[b.geo_priority] ?? 9) || score(b) - score(a),
  }[key] || (() => 0);
  return [...jobs].sort(cmp);
}

export function countBy(items, fn) {
  const m = new Map();
  for (const it of items) { const k = fn(it) ?? "Unknown"; m.set(k, (m.get(k) || 0) + 1); }
  return [...m.entries()].sort((a, b) => b[1] - a[1]);
}

export const safeUrl = (u) => (typeof u === "string" && /^https?:\/\//i.test(u) ? u : null);
export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
