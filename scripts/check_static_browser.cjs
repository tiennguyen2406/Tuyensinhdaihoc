/* Edge headless regression: Node + the existing @playwright/test installation.
 * Run: node scripts/check_static_browser.cjs
 */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const net = require("node:net");
const { spawn } = require("node:child_process");
const { chromium } = require("../apps/web/node_modules/@playwright/test");

const root = path.resolve(__dirname, "..");
const scratch = path.join(os.tmpdir(), "eduradar-pages-check");
const screenshots = path.join(scratch, "screenshots");
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
      for (const gone of ["#uni-letter", "#uni-sort", "#adv-sort", "#adv-combo-search", "[data-csv]", ".btn-csv"]) assert.equal(await page.locator(gone).count(), 0, gone);
      assert.doesNotMatch(await page.locator("body").innerText(), /Xuất CSV|Mọi chữ cái|Tên A–Z/);
      // One ordering by VNUR rank: inherited members sit at their parent's rank (direct first on ties), unranked last.
      const keys = await page.evaluate(() => [...document.querySelectorAll(".uni-card")].map((c) => {
        const b = c.querySelector(".rank-badge");
        return b ? [+b.textContent.match(/Top (\d+)/)[1], b.classList.contains("rank-inherited") ? 1 : 0] : [Infinity, 2];
      }));
      assert.deepEqual(keys, [...keys].sort((a, b) => a[0] - b[0] || a[1] - b[1]));
      assert.match(await page.locator(".uni-card").first().innerText(), /Top 1\b/);
      const firstUnranked = keys.findIndex((k) => k[0] === Infinity);
      assert.ok(keys.findIndex((k) => k[1] === 0) < keys.slice(0, firstUnranked).map((k) => k[1]).lastIndexOf(1), "inherited and direct ranks interleave");
      assert.ok(await page.evaluate(() => UNIVERSITIES.some((u) => u.province_source === "HOCMAI")));
      assert.ok(await page.evaluate(() => UNIVERSITIES.every((u) => u.province !== "Khác")));
      assert.match(await page.locator("#data-updated").innerText(), /Dữ liệu cập nhật ngày \d{2}\/\d{2}\/\d{4}/);
      await page.locator("#uni-province").selectOption("Thành phố Hà Nội");
      assert.ok(await page.locator('.uni-card[data-uni="BKA"]').count());
      await page.locator("#uni-q").fill("BKA");
      assert.equal(await page.locator(".uni-card").count(), 1);
      assert.match(await page.locator(".uni-card").innerText(), /mã xét tuyển.*phương thức/);
      await page.locator('.uni-card[data-uni="BKA"]').click();
      await page.locator("#uni-out tbody tr").first().waitFor();
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
      // Hand-researched tuition (tuition_extra.json): keep the source unit, flag-driven notes.
      const EXTRA = {
        DBG: [/350\.000 – 370\.000 đ\/tín chỉ/, /tổng mỗi năm phụ thuộc số tín chỉ đăng ký/, /Mức học phí năm 2024–2025, có thể đã thay đổi/],
        DCA: [/Theo ngành/iu, /Mức niêm yết, chưa trừ ưu đãi/, /Xem thêm 5 dòng/],
        DLH: [/18 – 30 triệu đ\/học kỳ/, /Mức theo học kỳ\/tháng, không phải cả năm/],
        DLS: [/Khoảng 23,6 triệu đ\/năm/, /dự kiến/i],
        DVP: [/Chỉ có thông tin cho ngành Dược học/],
        DBH: [/Chưa có mức học phí được xác minh/, /Xem thông báo của trường/],
        NTS: [/28–32 triệu đồng\/năm/, /không ghi đơn vị trong nguồn/],
        HHA: [/gần 700\.000/, /942\.000 đ\/tín chỉ/, /1\.413\.000 đ\/tín chỉ/],
        MDA: [/513\.100–635\.900 đồng\/tín chỉ/, /miễn học phí năm 2026–2027/i],
        KTA: [/1\.600\.000 đồng\/tín chỉ/, /DEEA 75/],
        DVB: [/60\.000\.000 đ\/toàn khóa/, /480\.000 đ\/tín chỉ/],
        TDB: [/596\.666 đ\/tín chỉ/, /17\.900\.000 đ\/năm/],
      };
      for (const code of ["BKA", "QHI", "IUH", "BVS", "DBD", ...Object.keys(EXTRA)]) {
        if (code !== "BKA") {
          await page.locator("#uni-q").fill(code);
          await page.locator("#uni-ac li").first().waitFor({ state: "visible" });
          await page.locator("#uni-ac li").first().click();
        }
        await page.locator("#uni-out .dean-block").waitFor();
        const plan = page.locator("#uni-out .dean-block");
        if (code === "BVS" || /Chưa có dữ liệu đề án/.test(await plan.innerText())) {
          assert.match(await plan.innerText(), /Chưa có dữ liệu đề án/);
          assert.equal(await plan.locator("a").count(), 0);
        } else {
          const open = await plan.locator("details.dean-method").evaluateAll((ds) => ds.filter((d) => !d.classList.contains("dean-common")).map((d) => d.open));
          assert.ok(open.length >= 2 && open[0] && open.slice(1).every((x) => !x), `${code} first method open, others collapsed`);
          assert.ok(await plan.locator("details.dean-method[open] .fact-group h4").count(), `${code} labelled groups`);
          assert.match(await plan.innerText(), /đối tượng|điều kiện \/ ngưỡng đầu vào|cách tính điểm|điểm cộng \/ ưu tiên|chỉ tiêu|ghi chú/iu);
          assert.match(await plan.locator(".dean-source").innerText(), /^Nguồn dữ kiện: HOCMAI, năm 20\d\d$/);
          assert.equal(await plan.locator(".dean-source a").getAttribute("target"), "_blank");
          assert.match(await plan.locator(".dean-source a").getAttribute("href"), /^https:\/\/huongnghiep.hocmai.vn\/de-an\//);
          assert.equal(await plan.locator(".dean-link").count(), 0);
          assert.doesNotMatch(await plan.innerText(), /Xem đề án đầy đủ|Danh sách ngành đào tạo|Giới thiệu trường/);
          await plan.locator("details.dean-method").evaluateAll((ds) => ds.forEach((d) => (d.open = true)));
          assert.ok((await plan.locator(".fact-group li").allTextContents()).every((s) => s.length <= 241));
          await plan.locator("details.dean-method").evaluateAll((ds) => ds.forEach((d, i) => (d.open = i === 0)));
        }
        const tuition = page.locator("#uni-out .dean-block + .tuition-card");
        assert.equal(await tuition.count(), 1, `${code} tuition card right under the plan`);
        const tuitionText = await tuition.innerText();
        if (EXTRA[code]) {
          for (const re of EXTRA[code]) assert.match(tuitionText, re, `${code} tuition ${re}`);
          assert.match(await tuition.locator(".src-tag").innerText(), /^(Chính thức|Văn bản chính thức \(bản lưu\)|Tham khảo|Chưa xác minh)$/i, `${code} evidence label`);
          if (!["NTS", "KTA"].includes(code)) assert.doesNotMatch(tuitionText, /triệu đồng\/năm/, `${code} not forced into a yearly range`);
          const links = await tuition.locator("a").evaluateAll((as) => as.map((a) => a.target));
          assert.ok(links.length >= 1 && links.length <= 3 && links.every((t) => t === "_blank"), `${code} 1-3 source links in new tab`);
          assert.equal(await tuition.evaluate((el) => el.classList.contains("tuition-old")), ["DBG", "HHA"].includes(code), `${code} amber border only for old years`);
          if (code === "DBH") assert.doesNotMatch(tuitionText, /\d\.\d{3}|triệu/, "unverified shows no amount");
          if (code === "DCA") {
            assert.equal(await tuition.locator(".fact-group > table.tuition-items tr").count(), 6);
            assert.equal(await tuition.locator("details.more-items").evaluate((d) => d.open), false);
          }
        } else assert.match(tuitionText, /triệu đồng\/năm|Miễn học phí|Chưa có thông tin học phí/);
        if (code === "DBD") assert.match(tuitionText, /Ước tính quy đổi: .*tín chỉ × 30/);
        if (!EXTRA[code] && !/Chưa có thông tin học phí/.test(tuitionText)) {
          assert.match(await tuition.locator(".src-tag").innerText(), /^(Chính thức|Báo chí|Tổng hợp)$/, `${code} source label`);
          assert.match(tuitionText, /Năm học 20\d\d–20\d\d/);
        }
        await plan.scrollIntoViewIfNeeded();
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        await page.screenshot({ path: path.join(screenshots, `${mode}-dean-${code}-${width}.png`) });
        await tuition.scrollIntoViewIfNeeded();
        await page.screenshot({ path: path.join(screenshots, `${mode}-tuition-${code}-${width}.png`) });
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
      for (const year of ["2026", "2025", "2024"]) for (const method of ["THPT", "HOCBA", "DGNL_HCM"]) {
        await page.locator("#adv-year").selectOption(year);
        await page.locator("#adv-method").selectOption(method);
        const choices = await page.evaluate(() => ({
          actual: [...document.querySelector("#adv-combo").options].slice(1).map((o) => o.value),
          expected: (META.combo_usage[document.querySelector("#adv-year").value]?.[document.querySelector("#adv-method").value] || []).map((r) => r.combo),
          labels: [...document.querySelector("#adv-combo").options].map((o) => o.textContent)
        }));
        assert.deepEqual(choices.actual, choices.expected);
        assert.ok(choices.labels.every((label) => !label.includes("nguồn có nhiều định nghĩa")));
      }
      await page.locator("#adv-year").selectOption("2026");
      await page.locator("#adv-method").selectOption("THPT");
      assert.equal(await page.locator('#adv-combo option[value="A00"]').textContent(), "A00 (Toán, Vật lí, Hóa học)");
      await page.locator("#adv-combo").selectOption("A00");
      await page.locator("#adv-score").fill("24");
      await page.locator("#advice-form button[type=submit]").click();
      await page.locator("#advice-out tbody tr").first().waitFor();
      assert.equal(await page.locator("#advice-out tbody tr").count(), 50);
      const levels = await page.locator("#advice-out .lvl").allTextContents();
      assert.equal(levels.length, 50);
      assert.ok(levels.every((l) => ["Thử sức", "Vừa sức", "An toàn"].includes(l)));
      const hots = await page.locator("#advice-out .why summary").allTextContents();
      const num = (x) => Number(x.replace(",", "."));
      assert.ok(hots.every((h, i) => i === 0 || num(hots[i - 1]) >= num(h)), "hot descending");
      assert.match(await page.locator("#advice-out .why summary").first().getAttribute("title"), /0,5 × điểm trường .* \+ 0,3 × điểm ngành .* \+ 0,2 × điểm xu hướng/);
      assert.ok(await page.locator("#advice-out .tag-hot").count(), "Ngành hot 2026 badge");
      assert.match(await page.locator("#advice-out .head").innerText(), /xếp theo độ hot · đang hiện 50\//);
      await page.screenshot({ path: path.join(screenshots, `${mode}-advice-${width}.png`) });
      await page.locator("#adv-more").click();
      await page.waitForFunction(() => document.querySelectorAll("#advice-out tbody tr").length === 100);
      assert.match(await page.locator("#advice-out .head").innerText(), /đang hiện 100\//);

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
      assert.match(await page.locator("#coverage-out").innerText(), /Dữ liệu cập nhật ngày \d{2}\/\d{2}\/\d{4}/);
      assert.equal(await page.locator("#coverage-out tbody tr").count(), 292);
      assert.equal(await page.locator("#coverage-out .missing-list li").count(), 15);
      assert.match(await page.locator("#coverage-out").innerText(), /285\/292 trường có mức học phí/);
      assert.equal(await page.locator("#coverage-out .tuition-missing-list li").count(), 7);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.evaluate(() => { document.querySelector("#uni-year").value = "2024"; });
      await page.locator('#coverage-out [data-uni="BKA"]').click();
      await page.locator("#uni-out tbody tr").first().waitFor();
      assert.equal(await page.locator("#uni-year").inputValue(), "2026", "Coverage link opens its stated year");

      // Full JSON equality with live FastAPI, including ties and combo-specific history.
      const cases = [
        "api/meta", "api/universities/BKA/scores?year=2026",
        "api/universities/NTH/scores?year=2026", "api/universities/BVS/scores?year=2026",
        "api/universities/DCA/scores?year=2026", "api/universities/DBH/scores?year=2026", "api/coverage",
        "api/majors/7480201/scores?year=2025&method=THPT",
        "api/majors/7480201/scores?year=2025",
        "api/majors/7480201/similar?year=2025", "api/network/g2_uni_uni?year=2026",
        "api/universities?q=bach%20khoa", "api/majors?q=cong%20nghe%20thong%20tin",
        "api/advice?method=THPT&score=24&combo=A00&year=2026",
        "api/advice?method=THPT&score=24&combo=A00&year=2026&offset=50",
        "api/advice?method=THPT&score=24&combo=A00&year=2026&offset=3050&limit=100",
        "api/advice?method=THPT&score=24&year=2026&limit=1000",
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
      results.push({ mode, width, tabs: 5, coverage: true, parity: cases.length, consoleErrors: 0, httpErrors: 0 });
      console.log(`PASS ${mode} ${width}px: five tabs, rank grid, plans/tuition, hot advice, ${cases.length} API comparisons, no console/HTTP errors`);
      await page.close();
    }
    fs.writeFileSync(path.join(scratch, "results.json"), JSON.stringify(results, null, 2));
  } finally {
    if (browser) await browser.close();
    children.forEach((p) => p.kill());
  }
})().catch((e) => { console.error(e); process.exitCode = 1; });
