/* Edge headless regression: Node + the existing @playwright/test installation.
 * Run: node scripts/check_static_browser.cjs
 */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const net = require("node:net");
const { spawn } = require("node:child_process");
const { chromium } = require("../apps/web/node_modules/@playwright/test");

const root = path.resolve(__dirname, "..");
const scratch = path.join(root, "_to_delete", "pages-check");
const screenshots = path.join(root, "docs", "reports", "dean-20261024");
const python = path.join(root, ".venv", "Scripts", "python.exe");
const children = [];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function freePort() {
  const server = net.createServer();
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  const port = server.address().port;
  await new Promise((r) => server.close(r));
  return port;
}
function run(args) {
  const p = spawn(python, args, { cwd: root, windowsHide: true, stdio: "ignore" });
  children.push(p);
  p.on("error", (e) => console.error(e));
}
async function json(url) {
  const r = await fetch(url);
  assert.equal(r.status, 200, url);
  return r.json();
}
async function waitServer(url) {
  for (let i = 0; i < 100; i++) {
    try { if ((await fetch(url)).ok) return; } catch {}
    await sleep(100);
  }
  throw new Error(`Server unavailable: ${url}`);
}

(async () => {
  fs.mkdirSync(scratch, { recursive: true });
  fs.mkdirSync(screenshots, { recursive: true });
  const link = path.join(scratch, "Tuyensinhdaihoc");
  if (!fs.existsSync(link)) fs.symlinkSync(path.join(root, "site"), link, "junction");
  assert.equal(fs.realpathSync(link), fs.realpathSync(path.join(root, "site")));
  const staticPort = await freePort(), apiPort = await freePort();
  run(["-m", "http.server", String(staticPort), "--bind", "127.0.0.1", "--directory", scratch]);
  run(["-m", "uvicorn", "webapp.main:app", "--host", "127.0.0.1", "--port", String(apiPort)]);
  const base = `http://127.0.0.1:${staticPort}/Tuyensinhdaihoc/`;
  const live = `http://127.0.0.1:${apiPort}/`;
  let browser;
  const results = [];
  try {
    await Promise.all([waitServer(base), waitServer(live + "api/meta")]);
    browser = await chromium.launch({ channel: "msedge", headless: true });
    for (const mode of ["static", "api"]) for (const width of [375, 1280]) {
      const page = await browser.newPage({ viewport: { width, height: 900 }, deviceScaleFactor: 1 });
      const errors = [], badResponses = [], failedRequests = [], requests = [];
      page.on("pageerror", (e) => errors.push(e.message));
      page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
      page.on("response", (r) => { if (r.status() >= 400) badResponses.push(`${r.status()} ${r.url()}`); });
      page.on("requestfailed", (r) => failedRequests.push(`${r.url()} ${r.failure()?.errorText}`));
      page.on("request", (r) => requests.push(r.url()));
      await page.goto(mode === "static" ? base : live);
      await page.waitForFunction(() => document.querySelector("#uni-year").options.length === 3);
      await page.waitForFunction(() => document.querySelectorAll(".uni-card").length === 292);
      assert.equal(await page.evaluate(() => Data.static), mode === "static");
      assert.equal(await page.locator("#uni-grid").evaluate((e) => getComputedStyle(e).gridTemplateColumns.split(" ").length), width === 375 ? 1 : 3);
      await page.screenshot({ path: path.join(screenshots, `${mode}-grid-${width}.png`) });
      await page.locator("#uni-sort").selectOption("rank");
      assert.match(await page.locator(".uni-card").first().innerText(), /Thuộc ĐHQG HN · Top 1/);
      assert.equal(await page.locator(".uni-card").first().locator(".rank-inherited").count(), 1);
      assert.ok(await page.evaluate(() => UNIVERSITIES.some((u) => u.province_source === "HOCMAI")));
      await page.locator("#uni-province").selectOption("Thành phố Hà Nội");
      await page.locator("#uni-letter").selectOption("b");
      assert.ok(await page.locator('.uni-card[data-uni="BKA"]').count());
      await page.locator("#uni-q").fill("BKA");
      assert.equal(await page.locator(".uni-card").count(), 1);
      assert.match(await page.locator(".uni-card").innerText(), /mã xét tuyển.*phương thức/);
      await page.locator('.uni-card[data-uni="BKA"]').click();
      await page.locator("#uni-out tbody tr").first().waitFor();
      await page.locator("#uni-letter").selectOption("");
      await page.locator("#uni-province").selectOption("");

      // Exercise autocomplete, year changes, and actual renderers at both sizes.
      await page.locator("#uni-q").fill("BKA");
      await page.locator("#uni-ac li").first().waitFor({ state: "visible" });
      await page.locator("#uni-ac li").first().click();
      await page.locator("#uni-out tbody tr").first().waitFor();
      assert.match(await page.locator("#uni-out").innerText(), /BKA/);
      assert.equal(await page.locator("#uni-year").inputValue(), "2026");
      await page.screenshot({ path: path.join(screenshots, `${mode}-uni-${width}.png`) });
      assert.match(await page.locator('#uni-out .combo-code').first().getAttribute("title"), /Toán|Ngữ văn/);
      for (const code of ["BKA", "NTH", "BVS"]) {
        if (code !== "BKA") {
          await page.locator("#uni-q").fill(code);
          await page.locator("#uni-ac li").first().waitFor({ state: "visible" });
          await page.locator("#uni-ac li").first().click();
        }
        await page.locator("#uni-out .dean-block").waitFor();
        const plan = page.locator("#uni-out .dean-block");
        if (code === "BVS") {
          assert.match(await plan.innerText(), /Chưa có dữ liệu đề án/);
          assert.equal(await plan.locator("a").count(), 0);
        } else {
          assert.ok(await plan.locator(".dean-method").count());
          assert.match(await plan.innerText(), /Nguồn: HOCMAI, tóm tắt dữ kiện/);
          assert.equal(await plan.locator(".dean-link").getAttribute("target"), "_blank");
          assert.match(await plan.locator(".dean-link").getAttribute("href"), /^https:\/\/huongnghiep.hocmai.vn\/de-an\//);
          assert.ok((await plan.locator(".dean-method p").allTextContents()).every((s) => s.length <= 300));
          assert.doesNotMatch(await plan.innerText(), /Danh sách ngành đào tạo|Giới thiệu trường/);
        }
        await plan.scrollIntoViewIfNeeded();
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        await page.screenshot({ path: path.join(screenshots, `${mode}-dean-${code}-${width}.png`) });
      }

      await page.locator('[data-tab="major"]').click();
      await page.locator("#major-year").selectOption("2025");
      await page.locator("#major-q").fill("7480201");
      await page.locator("#major-ac li").first().waitFor({ state: "visible" });
      await page.locator("#major-ac li").first().click();
      await page.locator("#major-out tbody tr").first().waitFor();
      assert.match(await page.locator("#major-out").innerText(), /7480201/);
      await page.screenshot({ path: path.join(screenshots, `${mode}-major-${width}.png`) });

      await page.locator('[data-tab="advice"]').click();
      await page.locator("#adv-method").selectOption("THPT");
      await page.locator("#adv-combo-search").fill("tin hoc");
      assert.equal(await page.locator('#adv-combo option[value="A00"]').count(), 0);
      assert.ok(await page.locator('#adv-combo option[value="X02"]').count());
      assert.ok(await page.locator('#adv-combo option[value="TH6"]').count());
      await page.locator("#adv-combo-search").fill("a00");
      assert.equal(await page.locator('#adv-combo option[value="A00"]').textContent(), "A00 (Toán, Vật lí, Hóa học)");
      await page.locator("#adv-combo").selectOption("A00");
      await page.locator("#adv-score").fill("24");
      await page.locator("#advice-form button[type=submit]").click();
      await page.locator("#advice-out tbody tr").first().waitFor();
      const levels = await page.locator("#advice-out .lvl").allTextContents();
      assert.deepEqual([...new Set(levels)], ["Thử sức", "Vừa sức", "An toàn"]);
      assert.equal(await page.locator("#adv-sort").inputValue(), "rank");
      assert.ok(await page.locator('#advice-out [data-label="Hạng VNUR"] .rank-badge').count());
      assert.match(await page.locator("#advice-out").innerText(), /1 \(ĐHQG HN\)/);
      await page.screenshot({ path: path.join(screenshots, `${mode}-advice-${width}.png`) });
      await page.locator("#adv-sort").selectOption("score");
      await page.locator("#advice-form button[type=submit]").click();
      await page.waitForFunction(() => document.querySelector("#advice-out .head")?.textContent.includes("theo điểm"));

      await page.locator('[data-tab="network"]').click();
      await page.waitForFunction(() => document.querySelector("#net-name").value === "g2_uni_uni_2026");
      await page.locator("#net-side table").first().waitFor();
      await page.waitForFunction(() => netObj && netObj.body.nodeIndices.length > 0);
      // Freeze the force layout for a deterministic screenshot; convergence is not a UI check.
      await page.evaluate(() => { netObj.stopSimulation(); netObj.fit({ animation: false }); });
      assert.ok(await page.locator("#net-canvas canvas").count());
      await page.screenshot({ path: path.join(screenshots, `${mode}-network-${width}.png`) });

      await page.locator('[data-tab="coverage"]').click();
      await page.locator("#coverage-out tbody tr").first().waitFor();
      assert.equal(await page.locator("#coverage-out tbody tr").count(), 292);
      assert.equal(await page.locator("#coverage-out li").count(), 15);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.evaluate(() => { document.querySelector("#uni-year").value = "2024"; });
      await page.locator('#coverage-out [data-uni="BKA"]').click();
      await page.locator("#uni-out tbody tr").first().waitFor();
      assert.equal(await page.locator("#uni-year").inputValue(), "2026", "Coverage link opens its stated year");

      // Full JSON equality with live FastAPI, including ties and combo-specific history.
      const cases = [
        "api/meta", "api/universities/BKA/scores?year=2026",
        "api/universities/NTH/scores?year=2026", "api/universities/BVS/scores?year=2026",
        "api/majors/7480201/scores?year=2025&method=THPT",
        "api/majors/7480201/scores?year=2025",
        "api/majors/7480201/similar?year=2025", "api/network/g2_uni_uni?year=2026",
        "api/universities?q=bach%20khoa", "api/majors?q=cong%20nghe%20thong%20tin",
        "api/advice?method=THPT&score=24&combo=A00&year=2026",
        "api/advice?method=THPT&score=24&combo=A00&year=2026&sort=score",
        "api/advice?method=THPT&score=24&year=2026&sort=rank&limit=1000",
        "api/advice?method=THPT&score=24&year=2025",
        "api/advice?method=THPT&score=24&combo=a00&year=2024&limit=17",
        "api/advice?method=DGNL_HCM&score=900&year=2026",
        "api/advice?method=DGNL_HN&score=100&combo=A00&year=2025",
        "api/advice?method=HOCBA&score=25&year=2024&margin=0.5",
        "api/advice?method=KETHOP&score=24&year=2026",
        "api/advice?method=THPT&score=0&year=2026",
      ];
      const program = await page.evaluate(async () => (await Data.searchIndex()).programs[0]);
      cases.push(`api/programs/scores?name=${encodeURIComponent(program.program_name)}&year=2026`);
      for (const endpoint of cases) {
        const expected = await json(live + endpoint);
        const actual = await page.evaluate((p) => api(p), endpoint);
        assert.deepEqual(actual, expected, `${width}px ${endpoint}`);
      }
      const accented = await page.evaluate(async () => {
        const a = await api("api/universities?q=bách%20khoa"), b = await api("api/universities?q=bach%20khoa");
        return JSON.stringify(a) === JSON.stringify(b);
      });
      assert.ok(accented, "Accent-insensitive search");
      assert.deepEqual(errors, [], "Console/page errors");
      assert.deepEqual(badResponses, [], "HTTP errors");
      assert.deepEqual(failedRequests, [], "Failed requests");
      assert.ok(requests.every((u) => u.startsWith(mode === "static" ? base : live)), "All requests stay under the project subpath");
      if (mode === "static") assert.ok(requests.every((u) => !u.includes("/api/")), "Static mode makes no API probes");
      results.push({ mode, width, tabs: 4, coverage: true, parity: cases.length, consoleErrors: 0, httpErrors: 0 });
      console.log(`PASS ${mode} ${width}px: four tabs, catalog/subjects/rank, ${cases.length} API comparisons, no console/HTTP errors`);
      await page.close();
    }
    fs.writeFileSync(path.join(scratch, "results.json"), JSON.stringify(results, null, 2));
  } finally {
    if (browser) await browser.close();
    children.forEach((p) => p.kill());
  }
})().catch((e) => { console.error(e); process.exitCode = 1; });
