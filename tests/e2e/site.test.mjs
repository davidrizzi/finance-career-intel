// End-to-end check of the built site in a real browser.
//   python scripts/build_site.py && node tests/e2e/site.test.mjs
// Needs Playwright (npm i -D playwright) and a Chrome/Chromium install.
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, resolve } from "node:path";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require("playwright")); } catch { ({ chromium } = require(process.env.PLAYWRIGHT_PATH || "/opt/npm-tools/node_modules/playwright")); }

const ROOT = resolve(process.argv[2] || "_site");
const SHOTS = process.env.SHOTS_DIR || "out/shots";
const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml" };
const server = createServer(async (req, res) => {
  const p = join(ROOT, decodeURIComponent(req.url.split("?")[0]).replace(/\/$/, "/index.html"));
  try { res.writeHead(200, { "content-type": MIME[extname(p)] || "application/octet-stream" }); res.end(await readFile(p)); }
  catch { res.writeHead(404); res.end("not found"); }
});
await new Promise((r) => server.listen(0, r));
const base = `http://localhost:${server.address().port}/`;
const results = [];
const check = (name, ok, info = "") => { results.push([name, !!ok]); console.log(`${ok ? "PASS" : "FAIL"}  ${name}${info ? "  (" + info + ")" : ""}`); };

const browser = await chromium.launch({ channel: process.env.PW_CHANNEL || "chrome", args: ["--no-sandbox"] }).catch(() => chromium.launch({ args: ["--no-sandbox"] }));
const ctx = await browser.newContext({ viewport: { width: 1360, height: 900 }, acceptDownloads: true });
const page = await ctx.newPage();
const errors = [];
const requests = [];
page.on("request", (r) => requests.push([r.method(), r.url()]));
page.on("pageerror", (e) => errors.push(String(e)));
page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
const { mkdir } = await import("node:fs/promises");
await mkdir(SHOTS, { recursive: true });
const shot = (n) => page.screenshot({ path: `${SHOTS}/${n}.png`, fullPage: false });

// dashboard
await page.goto(base);
await page.waitForSelector(".figures");
const total = Number(await page.locator(".figures b").first().textContent());
check("dashboard renders active-opportunity count", total > 0, `${total} active`);
check("dashboard lists top matches", (await page.locator(".rows li").count()) > 0);
await shot("dashboard");

// jobs: list, search, filters
await page.goto(base + "#/jobs");
await page.waitForSelector(".jobs-table tbody tr");
const rowsAll = await page.locator(".jobs-table tbody tr").count();
check("jobs table lists postings", rowsAll > 0, `${rowsAll} rows`);
check("every row has a direct application link", (await page.locator(".jobs-table a.btn.primary[href^='http']").count()) === rowsAll);
await shot("jobs");
await page.locator('input[data-f="country"][value="Switzerland"]').check();
await page.waitForTimeout(100);
const chRows = await page.locator(".jobs-table tbody tr").count();
const chText = await page.locator(".jobs-table tbody tr td[data-l='Location']").allTextContents();
check("country filter narrows to Switzerland", chRows > 0 && chRows < rowsAll && chText.every((t) => t.includes("Switzerland")), `${chRows} rows`);
check("Swiss rows carry the high-priority marker", (await page.locator(".jobs-table tbody tr.hi").count()) === chRows);
await page.click("#clear");
await page.waitForSelector(".jobs-table tbody tr");
await page.fill("#q", "Partners Group");
await page.waitForTimeout(100);
const pg = await page.locator(".jobs-table tbody tr .c").allTextContents();
check("search filters by company", pg.length > 0 && pg.every((t) => t.includes("Partners Group")), `${pg.length} rows`);
await page.fill("#q", "");
await page.locator('details:has(input[data-f="company"]) summary').click();
await page.locator('input[data-f="company"][value="Point72"]').check();
await page.waitForTimeout(100);
const p72 = await page.locator(".jobs-table tbody tr .c").allTextContents();
check("company filter works", p72.length > 0 && p72.every((t) => t.includes("Point72")));
await page.click("#clear");
await page.locator('details:has(input[data-f="german"]) summary').click();
await page.locator('input[data-f="german"][value="REQUIRED"]').check();
await page.waitForTimeout(100);
const de = await page.locator(".jobs-table tbody tr").count();
check("German-required filter returns only flagged postings", de > 0 && (await page.locator(".jobs-table tbody tr td[data-l='German'] .tag.bad").count()) === de, `${de} rows`);
await page.click("#clear");
await page.selectOption("#sort", "newest");
await page.waitForTimeout(100);
const dates = await page.locator(".jobs-table tbody tr .c-dates div[data-l='Published']").allTextContents();
const ts = dates.map((d) => Date.parse(d + " UTC")).filter((x) => !isNaN(x));
check("sort by newest orders publication dates", ts.length > 1 && ts.every((v, i) => i === 0 || ts[i - 1] >= v));
await page.selectOption("#sort", "relevance");

// save a job, persistence across reload
await page.waitForSelector("[data-save]");
const firstTitle = (await page.locator(".jobs-table tbody tr a.t").first().textContent()).trim();
await page.locator("[data-save]").first().click();
check("saving a job updates the navigation counter", (await page.locator("#nav-apps").textContent()) === "1");
await page.locator(".jobs-table tbody tr a.t").first().click();
await page.waitForSelector("#tracker");
check("detail view shows score explanation", (await page.locator(".crit").count()) === 6);
check("detail view has a prominent apply button", (await page.locator("a.btn.primary.big[href^='http']").count()) === 1);
await shot("detail");
await page.selectOption("#t-status", "Interview");
await page.fill("#t-interview", "2026-12-01");
await page.fill("#t-notes", "Spoke to the recruiter at the campus event.");
await page.click("#t-save");
await page.reload();
await page.waitForSelector("#tracker");
check("status persists after reload", (await page.inputValue("#t-status")) === "Interview");
check("notes persist after reload", (await page.inputValue("#t-notes")).includes("campus event"));
await page.goto(base + "#/applications");
await page.waitForSelector(".app");
check("My applications lists the tracked job under its status", (await page.locator(".board h2").first().textContent()).startsWith("Interview") && (await page.locator(".app a.t").first().textContent()).trim() === firstTitle);
await shot("applications");

// export, reset, import
const [download] = await Promise.all([page.waitForEvent("download"), page.click("#exp")]);
const backupPath = await download.path();
const backup = JSON.parse(await readFile(backupPath, "utf8"));
check("JSON export contains the tracked application", backup.format === "fcip-applications" && Object.keys(backup.applications).length === 1);
await page.click("#reset"); await page.click("#reset");
await page.waitForSelector(".board .empty");
check("local reset clears all applications", (await page.evaluate(() => Object.keys(JSON.parse(localStorage.getItem("fcip.applications.v1"))).length)) === 0);
await page.setInputFiles("#imp", backupPath);
await page.waitForSelector(".app");
check("JSON import restores the application with its notes", (await page.locator(".app textarea").first().inputValue()).includes("campus event"));
const outbound = requests.filter(([m, u]) => m !== "GET" || (!u.startsWith(base) && !u.startsWith("blob:") && !u.startsWith("data:")));
check("tracker data never leaves the browser (only GET requests for the site's own files)", outbound.length === 0, outbound.slice(0, 2).join(" "));

// companies, early careers, monitoring
await page.goto(base + "#/companies");
await page.waitForSelector("#cres table");
check("company directory loads", (await page.locator("#cres tbody tr").count()) === 50);
await page.fill("#cq", "Lugano");
await page.waitForTimeout(150);
check("company search by city works", (await page.locator("#cres tbody tr").count()) > 0 && (await page.locator("#cres tbody tr td:nth-child(3)").first().textContent()).includes("Lugano"));
await page.fill("#cq", "");
await page.selectOption("#c-mon", "monitored");
await page.waitForTimeout(150);
check("monitoring-status filter works", (await page.locator("#cres tbody tr .tag.ok").count()) === (await page.locator("#cres tbody tr").count()));
await shot("companies");
await page.goto(base + "#/early");
await page.waitForSelector("h1");
check("early careers page separates announced from open programmes", (await page.locator("main h2").allTextContents()).some((t) => t.startsWith("Announced, not yet open")));
await shot("early");
await page.goto(base + "#/monitoring");
await page.waitForSelector(".figures");
check("monitoring page shows coverage and source tables", (await page.locator("main table").count()) >= 1);
await shot("monitoring");

// dark mode + mobile
await page.click("#theme");
check("theme toggle switches mode", ["dark", "light"].includes(await page.evaluate(() => document.documentElement.dataset.theme)));
await page.goto(base + "#/jobs"); await page.waitForSelector(".jobs-table tbody tr"); await shot("jobs-dark");
await page.click("#theme");
await page.setViewportSize({ width: 390, height: 800 });
await page.goto(base + "#/jobs"); await page.waitForSelector(".jobs-table tbody tr");
const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
check("mobile layout has no horizontal overflow", !overflow);
await shot("jobs-mobile");
await page.goto(base + "#/dashboard"); await page.waitForSelector(".figures"); await shot("dashboard-mobile");

check("no JavaScript errors during the whole run", errors.length === 0, errors.slice(0, 3).join(" | "));
await browser.close(); server.close();
const failed = results.filter(([, ok]) => !ok);
console.log(`\n${results.length - failed.length}/${results.length} checks passed`);
process.exit(failed.length ? 1 : 0);
