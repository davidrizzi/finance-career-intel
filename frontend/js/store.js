// Personal application tracker. Everything here lives in this browser only
// (localStorage). Nothing is sent to GitHub or anywhere else.
export const STATUSES = ["New", "Saved", "To Apply", "Applied", "Online Assessment", "Interview", "Rejected", "Offer", "Withdrawn"];
export const KEY = "fcip.applications.v1";
const PREFS = "fcip.prefs.v1";

export function createStore(storage) {
  const read = (k, fallback) => {
    try { const v = JSON.parse(storage.getItem(k)); return v && typeof v === "object" ? v : fallback; }
    catch { return fallback; }
  };
  let apps = read(KEY, {});
  let prefs = read(PREFS, {});
  const persist = () => storage.setItem(KEY, JSON.stringify(apps));

  const snapshot = (job) => job ? {
    title: job.title, company: job.company, city: job.city || null, country: job.country || null,
    apply_url: job.apply_url || null, deadline: job.deadline || null,
  } : {};

  return {
    all: () => apps,
    get: (id) => apps[id] || null,
    statusOf: (id) => (apps[id] && apps[id].status) || "New",
    count: () => Object.keys(apps).length,
    // Create or update an entry. `job` refreshes the stored snapshot so the
    // entry stays readable even after the posting leaves the public database.
    set(id, patch, job) {
      const now = new Date().toISOString();
      const cur = apps[id] || { status: "Saved", created: now, notes: "", applied_date: "", interview_date: "", outcome: "" };
      if (patch.status && !STATUSES.includes(patch.status)) throw new Error("Unknown status: " + patch.status);
      const next = { ...cur, ...patch, updated: now };
      if (job) next.job = { ...(cur.job || {}), ...snapshot(job) };
      if (patch.status === "Applied" && !next.applied_date) next.applied_date = now.slice(0, 10);
      apps[id] = next;
      persist();
      return next;
    },
    remove(id) { delete apps[id]; persist(); },
    reset() { apps = {}; persist(); },
    exportJSON() {
      return JSON.stringify({ format: "fcip-applications", version: 1, exported: new Date().toISOString(), applications: apps }, null, 1);
    },
    // mode "merge": imported entries win only when they are newer. mode "replace": overwrite everything.
    importJSON(text, mode = "merge") {
      const data = JSON.parse(text);
      if (!data || data.format !== "fcip-applications" || typeof data.applications !== "object") {
        throw new Error("This file is not an application backup exported from this site.");
      }
      let added = 0, updated = 0, skipped = 0;
      const incoming = data.applications;
      if (mode === "replace") apps = {};
      for (const [id, entry] of Object.entries(incoming)) {
        if (!entry || !STATUSES.includes(entry.status)) { skipped++; continue; }
        if (!apps[id]) { apps[id] = entry; added++; }
        else if ((entry.updated || "") > (apps[id].updated || "")) { apps[id] = entry; updated++; }
        else skipped++;
      }
      persist();
      return { added, updated, skipped };
    },
    pref: (k, fallback) => (k in prefs ? prefs[k] : fallback),
    setPref(k, v) { prefs[k] = v; storage.setItem(PREFS, JSON.stringify(prefs)); },
  };
}
