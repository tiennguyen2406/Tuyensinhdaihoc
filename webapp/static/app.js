const $ = (s) => document.querySelector(s);
const readJson = async (p) => {
  const r = await fetch(p);
  if (!r.ok) { const t = await r.text(); let m = t; try { m = JSON.parse(t).detail; } catch {} throw new Error(m || r.status); }
  return r.json();
};
const unaccent = (s) => String(s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase().replace(/\s+/g, " ").trim();
const Data = {
  static: document.documentElement.dataset.mode === "static",
  cache: new Map(),
  file(p) {
    if (!this.cache.has(p)) this.cache.set(p, readJson(p).catch((e) => { this.cache.delete(p); throw e; }));
    return this.cache.get(p);
  },
  async init() {
    if (!this.static) {
      try { this.meta = await readJson("api/meta"); return; } catch { this.static = true; }
    }
    this.meta = await this.file("data/meta.json");
  },
  async searchIndex() {
    if (!this.static) return this.file("api/search-index");
    const [unis, majors] = await Promise.all([this.file("data/universities.json"), this.file("data/majors.json")]);
    return { unis, ...majors };
  },
  rank(items, q, limit) {
    const key = unaccent(q), words = key.split(" ");
    if (!key) return [];
    return items.filter((i) => words.every((w) => i._k.includes(w))).sort((a, b) =>
      Number(!a._k.startsWith(key)) - Number(!b._k.startsWith(key)) || (b.n_rows ?? b.n_unis ?? 0) - (a.n_rows ?? a.n_unis ?? 0)
    ).slice(0, limit).map(({ _k, file, ...item }) => item);
  },
  filterAdvice(d, q) {
    const year = Number(q.get("year")), method = q.get("method"), score = Number(q.get("score")), combo = q.get("combo") || "";
    const margin = q.has("margin") ? Number(q.get("margin")) : (d.scale == null ? null : d.scale / 30);
    const sort = q.get("sort") || "rank";
    const out = { year, method, combo, score, sort, scale: d.scale, margin, counts: {}, total: 0, rows: [] };
    if (d.scale == null) return out;
    const levels = ["Thử sức", "Vừa sức", "An toàn"], groups = levels.map(() => []), unit = d.scale / 30;
    for (const values of d.rows) {
      if (combo && !values[d.columns.length].includes(combo.toUpperCase())) continue;
      const r = Object.fromEntries(d.columns.map((k, i) => [k, values[i]]));
      if (r.score > score + margin) continue;
      const delta = r.score - score, level = delta > 0 ? 0 : delta > -unit ? 1 : 2;
      r.level = levels[level]; groups[level].push(r);
    }
    if (sort === "rank") groups.forEach((g) => g.sort((a, b) =>
      Number(a.vnur_rank == null) - Number(b.vnur_rank == null) || (a.vnur_rank ?? 0) - (b.vnur_rank ?? 0) || Number(!!a.vnur_parent) - Number(!!b.vnur_parent) || b.score - a.score
    ));
    const take = [0, 0, 0];
    let left = q.has("limit") ? Number(q.get("limit")) : 300;
    while (left > 0 && groups.some((g, i) => take[i] < g.length)) {
      groups.forEach((g, i) => { if (left > 0 && take[i] < g.length) { take[i]++; left--; } });
    }
    out.counts = Object.fromEntries(levels.map((lv, i) => [lv, groups[i].length]));
    out.total = groups.reduce((n, g) => n + g.length, 0);
    out.rows = groups.flatMap((g, i) => g.slice(0, take[i])).map((r) => {
      const h = d.histories[JSON.stringify([r.uni_code, r.program_code])] || {};
      return { ...r, history: { ...(h[combo.toUpperCase()] || {}), [year]: r.score } };
    });
    return out;
  },
  async request(p) {
    await this.ready;
    const [path, query] = p.split("?"), q = new URLSearchParams(query), parts = path.split("/");
    if (path === "api/meta") return this.meta;
    if (path === "api/universities" || path === "api/majors") {
      const idx = await this.searchIndex(), term = q.get("q"), limit = Number(q.get("limit") || 15);
      if (path === "api/universities") return this.rank(idx.unis, term, limit);
      const found = this.rank(idx.majors, term, limit);
      return [...found, ...this.rank(idx.programs, term, found.length ? Math.min(5, limit) : limit)];
    }
    if (!this.static) return readJson(p);
    const year = q.get("year");
    if (path === "api/coverage") return this.file("data/coverage.json");
    if (path === "api/network") return this.file("data/network.json");
    if (parts[1] === "network") return this.file(`data/network/${parts[2]}_${year}.json`);
    if (parts[1] === "universities") return this.file(`data/uni/${parts[2]}_${year}.json`);
    if (parts[3] === "similar") {
      const d = await this.file(`data/network/similar_majors_${year}.json`);
      return (d[decodeURIComponent(parts[2])] || []).map(([major_code, major_name, jaccard]) => ({ major_code, major_name, jaccard }));
    }
    if (parts[1] === "majors" || parts[1] === "programs") {
      let file = `data/major/${parts[2]}_${year}.json`;
      if (parts[1] === "programs") {
        const idx = await this.searchIndex(), program = idx.programs.find((p) => p.program_name === q.get("name"));
        if (!program) throw new Error("Không tìm thấy chương trình");
        file = `data/program/${program.file}_${year}.json`;
      }
      const d = await this.file(file), method = q.get("method");
      return method ? { ...d, rows: d.rows.filter((r) => r.method === method) } : d;
    }
    if (path === "api/advice") return this.filterAdvice(await this.file(`data/advice/${q.get("method")}_${year}.json`), q);
    throw new Error("Không tìm thấy dữ liệu");
  },
};
Data.ready = Data.init();
const api = (p) => Data.request(p);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmt = (x) => (x == null || x === "" ? "" : Number(x).toLocaleString("vi-VN", { maximumFractionDigits: 2 }));
const PT = { CHUAN: "", CLC: "CLC", TIEN_TIEN: "Tiên tiến", LIEN_KET: "Liên kết", TIENG_ANH: "Tiếng Anh", PHAN_HIEU: "Phân hiệu", TAI_NANG: "Tài năng" };
const uniCell = (r) => `<span title="${esc(r.uni_name)}">${esc(shortUni(r.uni_name))}</span> <span class="sub">${esc(r.uni_code)}</span>`;
const shortUni = (n) => String(n || "").replace(/^(Trường\s+)?(Đại\s+Học|Đại\s+học)\s+/i, "ĐH ").replace(/^Học\s+Viện\s+/i, "HV ");
const tag = (t) => (PT[t] ? `<span class="tag">${PT[t]}</span>` : "");
const combos = (s) => (s || "").replaceAll(";", ", ");
const comboHtml = (s) => !s ? "" : `<span class="combo-values">` + s.split(";").filter(Boolean).map((c) => `<span class="combo-code" title="${esc(META?.combo_subjects[c] || "Chưa có tên môn từ nguồn")}">${esc(c)}</span>`).join(", ") + "</span>";
const rankHtml = (u, compact = false) => u.vnur_rank == null ? `<span class="sub">Chưa có hạng</span>` : `<span class="rank-badge${u.vnur_parent ? " rank-inherited" : ""}">${compact ? `${u.vnur_rank}${u.vnur_parent ? ` (${esc(u.vnur_parent)})` : ""}` : u.vnur_parent ? `Thuộc ${esc(u.vnur_parent)} · Top ${u.vnur_rank}` : `Top ${u.vnur_rank} VNUR`}</span>`;
function deanHtml(plan, scoreYear) {
  if (!plan) return `<section class="card dean-block"><h2>Đề án tuyển sinh</h2><p class="muted">Chưa có dữ liệu đề án</p></section>`;
  const bullets = (title, items) => items.length ? `<h4>${title}</h4><ul>${items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : "";
  return `<section class="card dean-block"><h2>Đề án tuyển sinh ${plan.year || ""}</h2>
    <p class="muted small">${esc(plan.province)}${plan.groups.length ? " · " + esc(plan.groups.join(", ")) : ""}${plan.year !== scoreYear ? ` · Đề án khác năm bảng điểm ${scoreYear}` : ""}</p>
    ${plan.methods_year && plan.methods_year !== plan.year ? `<p class="dean-note">Phần phương thức trong bài vẫn ghi năm ${plan.methods_year}; tiêu đề đề án ghi năm ${plan.year}.</p>` : ""}
    <div class="dean-methods">${plan.methods.map((m) => `<article class="dean-method"><h3>${esc(m.name)}</h3><p>${esc(m.summary)}</p></article>`).join("") || `<p class="muted">Chưa có dữ kiện phương thức để tóm tắt; xem bài gốc.</p>`}</div>
    <h3>Thời gian &amp; hồ sơ</h3>${bullets("Mốc thời gian", plan.timeline)}${bullets("Giấy tờ", plan.documents)}
    ${!plan.timeline.length && !plan.documents.length ? `<p class="muted small">Chưa có dữ kiện thời gian hoặc giấy tờ trong mục này của bài nguồn.</p>` : ""}
    <a class="dean-link" href="${esc(plan.source_url)}" target="_blank" rel="noopener noreferrer">Xem đề án đầy đủ tại HOCMAI</a>
    <p class="muted small">Nguồn: HOCMAI, tóm tắt dữ kiện. Điều kiện đầy đủ và các diện đặc thù: xem bài gốc.</p></section>`;
}
const fail = (out, e) => (out.innerHTML = `<div class="card empty">Lỗi: ${esc(e.message)}</div>`);
const TABS = ["uni", "major", "advice", "network", "coverage"];
let META = null;
let UNIVERSITIES = [];

const uniNameKey = (u) => unaccent(u.name).replace(/^(truong\s+)?dai hoc\s+|^hoc vien\s+|^phan hieu\s+/, "");
function renderUniGrid() {
  const words = unaccent($("#uni-q").value).split(" "), letter = $("#uni-letter").value, province = $("#uni-province").value;
  const items = UNIVERSITIES.filter((u) => words.every((w) => u._k.includes(w)) && (!letter || uniNameKey(u).startsWith(letter)) && (!province || u.province === province));
  items.sort((a, b) => ($("#uni-sort").value === "rank" ? (a.vnur_rank ?? Infinity) - (b.vnur_rank ?? Infinity) || Number(!!a.vnur_parent) - Number(!!b.vnur_parent) : 0) || uniNameKey(a).localeCompare(uniNameKey(b), "vi") || a.uni_code.localeCompare(b.uni_code));
  $("#uni-count").textContent = `${items.length} trường · Thống kê theo năm mới nhất của từng trường. Bộ lọc chữ cái bỏ tiền tố Trường Đại học / Đại học / Học viện.`;
  $("#uni-grid").innerHTML = items.length ? items.map((u) => `<button type="button" class="uni-card" data-uni="${esc(u.uni_code)}" data-year="${u.latest_year}">
    <span class="uni-code-badge">${esc(u.uni_code)}</span><span class="uni-card-name">${esc(u.name)}</span>
    <span class="sub">${u.n_programs} mã xét tuyển · ${u.n_methods} phương thức · ${u.latest_year}</span>
    ${u.first_year > 2024 ? `<span class="sub">mới có ${u.first_year}</span>` : ""}
    <span class="sub">${esc(u.province)}</span>${u.vnur_rank != null ? rankHtml(u) : ""}</button>`).join("") : `<p class="muted">Không tìm thấy trường phù hợp.</p>`;
}
$("#uni-q").addEventListener("input", renderUniGrid);
["#uni-letter", "#uni-province", "#uni-sort"].forEach((s) => $(s).addEventListener("change", renderUniGrid));
$("#uni-grid").addEventListener("click", (e) => {
  const card = e.target.closest("[data-uni]");
  if (card) { curUni = card.dataset.uni; $("#uni-year").value = card.dataset.year; loadUni(); }
});

function filterCombos() {
  const words = unaccent($("#adv-combo-search").value).split(" "), chosen = $("#adv-combo").value;
  const items = META.combos.filter((c) => words.every((w) => unaccent(`${c} ${META.combo_subjects[c] || ""}`).includes(w)));
  $("#adv-combo").innerHTML = `<option value="">Mọi tổ hợp</option>` + items.map((c) => `<option value="${esc(c)}">${esc(c)}${META.combo_subjects[c] ? ` (${esc(META.combo_subjects[c])})` : ""}</option>`).join("");
  $("#adv-combo").value = items.includes(chosen) ? chosen : "";
}
$("#adv-combo-search").addEventListener("input", () => META && filterCombos());

/* ---------- xuat CSV (dung tu du lieu, khong doc lai HTML) ---------- */
const EXPORTS = {};
const csvBtn = (id) => `<button type="button" class="btn-csv" data-csv="${id}">Xuất CSV</button>`;
const setExport = (id, filename, header, rows) => (EXPORTS[id] = { filename, header, rows });
const slug = (s) => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[đĐ]/g, "d").replace(/[^A-Za-z0-9]+/g, "-").replace(/^-|-$/g, "").toLowerCase();
function csvCell(v) {
  let s = v == null ? "" : String(v);
  if (/^[=+@\t\r]/.test(s) || (/^-/.test(s) && isNaN(s))) s = "'" + s; // chan cong thuc khi mo bang Excel
  return /[",\r\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s;
}
function downloadCsv(x) {
  const text = "﻿" + [x.header, ...x.rows].map((r) => r.map(csvCell).join(",")).join("\r\n");
  const url = URL.createObjectURL(new Blob([text], { type: "text/csv;charset=utf-8" }));
  const a = Object.assign(document.createElement("a"), { href: url, download: x.filename });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
document.addEventListener("click", (e) => { const b = e.target.closest("[data-csv]"); if (b && EXPORTS[b.dataset.csv]) downloadCsv(EXPORTS[b.dataset.csv]); });

/* ---------- tabs ---------- */
document.querySelectorAll(".tabs button").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));
function showTab(t) {
  if (!TABS.includes(t)) t = "uni";
  document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("active", b.dataset.tab === t));
  document.querySelectorAll(".tab").forEach((s) => s.classList.toggle("active", s.id === "tab-" + t));
  if (t === "network") loadNetworkList();
  if (t === "coverage") loadCoverage();
  history.replaceState(null, "", "#" + t);
}

/* ---------- autocomplete ---------- */
function autocomplete(input, list, url, render, onPick) {
  let timer, items = [], sel = -1, seq = 0;
  const close = () => { list.style.display = "none"; sel = -1; };
  const draw = () => {
    list.innerHTML = items.map((it, i) => `<li class="${i === sel ? "sel" : ""}" data-i="${i}">${render(it)}</li>`).join("");
    list.style.display = items.length ? "block" : "none";
  };
  input.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      const my = ++seq, q = input.value.trim();
      let res = [];
      try { res = q ? await api(url + encodeURIComponent(q)) : []; } catch { res = []; }
      if (my !== seq) return; // da co lan go moi hon -> bo ket qua cu
      items = res; sel = -1; draw();
    }, 150);
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown") { sel = Math.min(sel + 1, items.length - 1); draw(); e.preventDefault(); }
    else if (e.key === "ArrowUp") { sel = Math.max(sel - 1, 0); draw(); e.preventDefault(); }
    else if (e.key === "Enter") { e.preventDefault(); const it = items[sel >= 0 ? sel : 0]; if (it) { onPick(it); close(); } }
    else if (e.key === "Escape") close();
  });
  list.addEventListener("mousedown", (e) => { const li = e.target.closest("li"); if (li) { onPick(items[+li.dataset.i]); close(); } });
  input.addEventListener("blur", () => setTimeout(close, 150));
}

/* ---------- 1a. theo truong ---------- */
let curUni = null;
autocomplete($("#uni-q"), $("#uni-ac"), "api/universities?q=",
  (u) => `<span>${esc(u.name)}</span><span class="code">${esc(u.uni_code)}${u.short_name ? " · " + esc(u.short_name) : ""}</span>`,
  (u) => { curUni = u.uni_code; $("#uni-q").value = u.name; loadUni(); });
$("#uni-year").addEventListener("change", () => curUni && loadUni());

async function loadUni() {
  const out = $("#uni-out");
  out.innerHTML = `<div class="empty">Đang tải…</div>`;
  let d;
  try { d = await api(`api/universities/${encodeURIComponent(curUni)}/scores?year=${$("#uni-year").value}`); } catch (e) { return fail(out, e); }
  location.hash = `uni/${curUni}/${d.year}`;
  $("#uni-q").value = d.university.name;
  renderUniGrid();
  if (!d.rows.length) {
    out.innerHTML = `<div class="card empty">${esc(d.university.name)} chưa có dữ liệu năm ${d.year}. Năm có dữ liệu: ${d.years.join(", ") || "—"}</div>${deanHtml(d.dean, d.year)}`;
    return;
  }
  const cols = d.methods;
  const more = (r, m) => r.scores[m + "_more"] || [];
  const cell = (c) => !c ? "" : `${fmt(c.score)}${c.equiv != null ? `<span class="eq">≈ ${fmt(c.equiv)}/30</span>` : ""}`;
  const body = d.rows.map((r) => `<tr>
      <td class="code" data-label="Mã">${esc(r.program_code)}</td>
      <td class="prog main">${esc(r.program_name)}${tag(r.program_type)}${r.notes.length ? `<div class="sub">${esc(r.notes.join(" · "))}</div>` : ""}</td>
      <td class="combo" data-label="Tổ hợp">${comboHtml(r.combos)}</td>
      ${cols.map((m) => `<td class="num" data-label="${esc(m.method_name)}">${cell(r.scores[m.method])}${more(r, m.method).map((c) => `<span class="eq">${fmt(c.score)}</span>`).join("")}</td>`).join("")}
    </tr>`).join("");
  const t = d.tuition;
  const foot = `<tr><td colspan="${3 + cols.length}">Học phí${t ? ` năm học ${t.year}–${t.year + 1}: ${esc(t.text || (fmt(t.min_mil) + "–" + fmt(t.max_mil) + " triệu đồng/năm"))} <a href="${esc(t.source_url)}" target="_blank" rel="noopener">nguồn</a>` : ": chưa có dữ liệu"}</td></tr>`;
  const scoreTxt = (r, m) => [r.scores[m.method], ...more(r, m.method)].filter(Boolean).map((c) => c.score).join(" | ");
  setExport("uni", `diem-chuan-${slug(d.university.uni_code)}-${d.year}.csv`,
    ["Mã trường", "Năm", "Mã chương trình", "Ngành / chương trình", "Mã ngành", "Loại", "Tổ hợp", ...cols.map((m) => m.method_name), "Ghi chú"],
    d.rows.map((r) => [d.university.uni_code, d.year, r.program_code, r.program_name, r.major_code, PT[r.program_type] || "Chuẩn",
      combos(r.combos), ...cols.map((m) => scoreTxt(r, m)), r.notes.join(" · ")]));
  out.innerHTML = `<div class="card">
    <div class="head"><h2>${esc(d.university.name)} <span class="sub">(${esc(d.university.uni_code)})</span></h2>
      <span class="muted small">${d.rows.length} chương trình · năm ${d.year} · <a href="${esc(d.source_url)}" target="_blank" rel="noopener">nguồn</a> ${csvBtn("uni")}</span></div>
    <div class="tbl-wrap"><table class="stack">
      <thead><tr><th>Mã</th><th>Ngành / chương trình</th><th>Tổ hợp</th>${cols.map((m) => `<th class="num">${esc(m.method_name)}</th>`).join("")}</tr></thead>
      <tbody>${body}</tbody><tfoot>${foot}</tfoot></table></div></div>${deanHtml(d.dean, d.year)}`;
  out.scrollIntoView({ block: "start" });
}

/* ---------- 1b. theo nganh (hoac ten chuong trinh goc chua map) ---------- */
let curMajor = null; // {code} hoac {name}
autocomplete($("#major-q"), $("#major-ac"), "api/majors?q=",
  (m) => m.kind === "program"
    ? `<span>${esc(m.program_name)} <span class="tag tag-raw">chưa map</span></span><span class="code">${m.n_unis} trường · ${m.n_rows} dòng</span>`
    : `<span>${esc(m.major_name)}</span><span class="code">${esc(m.major_code)} · ${m.n_unis} trường</span>`,
  (m) => {
    curMajor = m.kind === "program" ? { name: m.program_name } : { code: m.major_code };
    $("#major-q").value = m.kind === "program" ? m.program_name : m.major_name;
    loadMajor();
  });
["#major-year", "#major-method"].forEach((s) => $(s).addEventListener("change", () => curMajor && loadMajor()));

async function loadMajor() {
  const out = $("#major-out");
  out.innerHTML = `<div class="empty">Đang tải…</div>`;
  const year = $("#major-year").value, method = $("#major-method").value;
  const { code, name } = curMajor;
  const url = code
    ? `api/majors/${encodeURIComponent(code)}/scores?year=${year}&method=${method}`
    : `api/programs/scores?name=${encodeURIComponent(name)}&year=${year}&method=${method}`;
  let d;
  try { d = await api(url); } catch (e) { return fail(out, e); }
  location.hash = code ? `major/${code}/${d.year}` : `major/~${encodeURIComponent(name)}/${d.year}`;
  $("#major-q").value = d.major.major_name;
  const rawNote = d.major.unmapped ? `<p class="muted small">Tên chương trình gốc, chưa gán mã ngành chuẩn — chỉ gồm các dòng chưa map${d.years ? ` (năm có dữ liệu: ${d.years.join(", ")})` : ""}.</p>` : "";
  if (!d.rows.length) { out.innerHTML = `<div class="card empty">Chưa có dữ liệu cho ${code ? "ngành" : "chương trình"} này năm ${d.year}.${rawNote}</div>`; return; }
  const unis = new Set(d.rows.map((r) => r.uni_code)).size;
  const sim = code ? await api(`api/majors/${encodeURIComponent(code)}/similar?year=${d.year}`).catch(() => []) : [];
  const simHtml = sim.length ? `<div class="chips"><span class="muted small">Ngành tương tự (mạng G3):</span>${sim.map((x) =>
    `<button type="button" class="chip" data-code="${esc(x.major_code)}" data-name="${esc(x.major_name)}" title="Jaccard ${x.jaccard}">${esc(x.major_name)}</button>`).join("")}</div>` : "";
  setExport("major", `nganh-${slug(code || name)}-${d.year}.csv`,
    ["Mã trường", "Trường", "Mã chương trình", "Chương trình", "Mã ngành", "Loại", "Phương thức", "Tổ hợp", "Điểm chuẩn", "Thang", "Năm"],
    d.rows.map((r) => [r.uni_code, r.uni_name, r.program_code, r.program_name, r.major_code, PT[r.program_type] || "Chuẩn",
      r.method_name, combos(r.combos), r.score, r.scale_max, d.year]));
  out.innerHTML = `<div class="card"><div class="head"><h2>${esc(d.major.major_name)} <span class="sub">${esc(d.major.major_code || "chưa map")}</span></h2>
    <span class="muted small">${unis} trường · ${d.rows.length} dòng · năm ${d.year} ${csvBtn("major")}</span></div>${rawNote}${simHtml}
    <div class="tbl-wrap"><table class="stack"><thead><tr><th>Trường</th><th>Chương trình</th><th>Phương thức</th><th>Tổ hợp</th><th class="num">Điểm chuẩn</th></tr></thead>
    <tbody>${d.rows.map((r) => `<tr><td class="main">${uniCell(r)}</td>
      <td data-label="Chương trình">${esc(r.program_name)}${tag(r.program_type)}</td><td class="sub" data-label="Phương thức">${esc(r.method_name)}</td>
      <td class="sub" data-label="Tổ hợp">${comboHtml(r.combos)}</td>
      <td class="num" data-label="Điểm chuẩn">${fmt(r.score)}<span class="sub"> /${r.scale_max ?? "?"}</span></td></tr>`).join("")}</tbody></table></div></div>`;
}

$("#major-out").addEventListener("click", (e) => {
  const b = e.target.closest(".chip[data-code]");
  if (b) { curMajor = { code: b.dataset.code }; $("#major-q").value = b.dataset.name; loadMajor(); }
});

/* ---------- 2. tu van ---------- */
$("#advice-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const out = $("#advice-out");
  out.innerHTML = `<div class="empty">Đang tải…</div>`;
  const q = new URLSearchParams({ method: $("#adv-method").value, score: $("#adv-score").value, combo: $("#adv-combo").value, year: $("#adv-year").value, sort: $("#adv-sort").value });
  let d;
  try { d = await api("api/advice?" + q); } catch (err) { return fail(out, err); }
  if (!d.rows.length) { out.innerHTML = `<div class="card empty">Không có ngành phù hợp.</div>`; return; }
  const yrs = [...new Set(d.rows.flatMap((r) => Object.keys(r.history)))].sort();
  const cls = { "Thử sức": "lvl-try", "Vừa sức": "lvl-fit", "An toàn": "lvl-safe" };
  const shown = (l) => d.rows.filter((r) => r.level === l).length;
  const cnt = (l) => (shown(l) < d.counts[l] ? `${shown(l)}/${d.counts[l]}` : `${d.counts[l]}`);
  setExport("advice", `tu-van-${slug(d.method)}-${d.score}${d.combo ? "-" + d.combo : ""}-${d.year}.csv`,
    ["Mức", "Mã trường", "Trường", "Hạng VNUR", "Đại học mẹ", "Mã chương trình", "Ngành / chương trình", "Mã ngành", "Tổ hợp", "Thang", ...yrs.map((y) => `Điểm ${y}`)],
    d.rows.map((r) => [r.level, r.uni_code, r.uni_name, r.vnur_rank, r.vnur_parent, r.program_code, r.program_name, r.major_code, combos(r.combos), r.scale_max, ...yrs.map((y) => r.history[y])]));
  out.innerHTML = `<div class="card"><div class="head"><h2>${d.total} lựa chọn với ${fmt(d.score)} điểm${d.scale !== 30 ? ` <span class="sub">(thang ${fmt(d.scale)})</span>` : ""}</h2>
    <span class="muted small">Thử sức ${cnt("Thử sức")} · Vừa sức ${cnt("Vừa sức")} · An toàn ${cnt("An toàn")} · tham chiếu năm ${d.year} · theo ${d.sort === "rank" ? "xếp hạng trường" : "điểm"}${d.rows.length < d.total ? ` · hiện ${d.rows.length} dòng` : ""} ${csvBtn("advice")}</span></div>
    <div class="tbl-wrap"><table class="stack"><thead><tr><th>Mức</th><th>Trường</th><th>Hạng VNUR</th><th>Ngành / chương trình</th><th>Tổ hợp</th>${yrs.map((y) => `<th class="num">${y}</th>`).join("")}</tr></thead>
    <tbody>${d.rows.map((r) => `<tr><td data-label="Mức"><span class="lvl ${cls[r.level]}">${r.level}</span></td>
      <td data-label="Trường">${uniCell(r)}</td><td data-label="Hạng VNUR">${rankHtml(r, true)}</td><td class="main">${esc(r.program_name)}${tag(r.program_type)}</td>
      <td class="sub" data-label="Tổ hợp">${comboHtml(r.combos)}</td>
      ${yrs.map((y) => `<td class="num" data-label="${y}">${y == d.year ? `<b>${fmt(r.history[y])}</b>` : fmt(r.history[y])}</td>`).join("")}</tr>`).join("")}</tbody></table></div></div>`;
});

/* ---------- 3. mang SNA ---------- */
let netLoaded = false, netObj = null;
async function loadNetworkList() {
  if (netLoaded) return; netLoaded = true;
  let names;
  try { names = await api("api/network"); } catch (e) { netLoaded = false; return fail($("#net-canvas"), e); }
  const sel = $("#net-name");
  if (!names.length) { $("#net-canvas").innerHTML = `<div class="empty">Chưa có dữ liệu mạng. Chạy: python -m sna.build</div>`; return; }
  const NAMES = { g1_uni_major: "G1 · Trường – Ngành", g2_uni_uni: "G2 · Trường – Trường", g3_major_major: "G3 · Ngành – Ngành", g4_competition: "G4 · Cạnh tranh (có hướng)" };
  const label = (n) => { const i = n.lastIndexOf("_"); return `${NAMES[n.slice(0, i)] || n.slice(0, i)} — ${n.slice(i + 1)}`; };
  names.sort((a, b) => b.slice(-4).localeCompare(a.slice(-4)) || a.localeCompare(b));
  sel.innerHTML = names.map((n) => `<option value="${n}">${label(n)}</option>`).join("");
  sel.value = names.find((n) => n.startsWith("g2_uni_uni")) || names[0];
  sel.addEventListener("change", drawNetwork);
  drawNetwork();
}
async function drawNetwork() {
  const [name, year] = (() => { const v = $("#net-name").value; const i = v.lastIndexOf("_"); return [v.slice(0, i), v.slice(i + 1)]; })();
  let g;
  try { g = await api(`api/network/${name}?year=${year}`); } catch (e) { $("#net-side").innerHTML = `<p class="muted">Lỗi: ${esc(e.message)}</p>`; return; }
  const palette = ["#1f5eff", "#e8590c", "#2b8a3e", "#c2255c", "#7048e8", "#0c8599", "#e67700", "#5c940d", "#862e9c", "#495057"];
  const linked = new Set(g.edges.flatMap((e) => [e.source, e.target]));
  g.nodes = g.nodes.filter((n) => linked.has(n.id));
  const maxS = Math.max(...g.nodes.map((n) => n.size || 1));
  const nodes = g.nodes.map((n) => ({ id: n.id, label: n.label, value: n.size || 1, title: `${n.label}\n${Object.entries(n.metrics || {}).map(([k, v]) => `${k}: ${v}`).join("\n")}`,
    color: n.group != null ? palette[n.group % palette.length] : (n.kind === "major" ? "#e8590c" : "#1f5eff"), shape: n.kind === "major" ? "diamond" : "dot",
    font: { size: (n.size || 1) > maxS * 0.3 ? 14 : 0 } }));
  const edges = g.edges.map((e) => ({ from: e.source, to: e.target, value: e.weight || 1, arrows: g.directed ? "to" : undefined, color: { opacity: 0.25 } }));
  if (netObj) netObj.destroy();
  netObj = new vis.Network($("#net-canvas"), { nodes, edges }, {
    physics: { solver: "forceAtlas2Based", stabilization: { iterations: 250 } },
    nodes: { scaling: { min: 4, max: 40 } }, edges: { scaling: { min: 0.5, max: 4 }, smooth: false }, interaction: { hover: true, tooltipDelay: 80 } });
  const s = g.summary || {};
  const metricRows = (n) => [n.id, n.label, n.kind || "", n.group ?? "", n.size ?? "", ...Object.values(n.metrics || {})];
  const metricKeys = Object.keys(g.nodes.find((n) => n.metrics)?.metrics || {});
  setExport("net-summary", `mang-${slug(name)}-${year}-tong-quan.csv`, ["Mục", "Chỉ số", "Giá trị"],
    [...Object.entries(s).map(([k, v]) => ["Tổng quan", k, v]),
     ...Object.entries(g.top || {}).flatMap(([m, rows]) => rows.map((r) => [`Top ${m}`, r[0], r[1]]))]);
  setExport("net-nodes", `mang-${slug(name)}-${year}-nut.csv`, ["id", "Tên", "Loại", "Nhóm", "Kích thước", ...metricKeys], g.nodes.map(metricRows));
  $("#net-side").innerHTML = `<h3>${esc(g.title || name)} · ${year}</h3><p class="muted">${esc(g.description || "")}</p>
    <p>${csvBtn("net-summary")} ${csvBtn("net-nodes").replace("Xuất CSV", "CSV các nút")}</p>
    <table>${Object.entries(s).map(([k, v]) => `<tr><td>${esc(k)}</td><td class="num">${esc(v)}</td></tr>`).join("")}</table>
    ${Object.entries(g.top || {}).map(([m, rows]) => `<h3>Top ${esc(m)}</h3><table>${rows.map((r) => `<tr><td>${esc(r[0])}</td><td class="num">${esc(r[1])}</td></tr>`).join("")}</table>`).join("")}`;
}

/* ---------- init ---------- */
async function loadCoverage() {
  const out = $("#coverage-out");
  try {
    const d = await api("api/coverage");
    out.innerHTML = `<div class="card"><p>Nguồn: <a href="${esc(d.source_url)}" target="_blank" rel="noopener">tuyensinh247</a> · Thu thập: ${esc(d.collected_from?.slice(0, 10))} đến ${esc(d.collected_to?.slice(0, 10))}.</p>
      <p>${d.universities.length} trường có điểm · ${d.missing.length} trường trong danh mục nguồn chưa có điểm trong các năm ${d.years.join(", ")}. Ô số là số dòng điểm, dấu — là chưa có dữ liệu; không có nghĩa trường không tuyển sinh.</p>
      <p>Xếp hạng: <a href="${esc(META.ranking_source.url)}" target="_blank" rel="noopener">VNUR 2026</a> · ${META.stats.ranked_unis} trường có hạng, gồm ${META.stats.inherited_unis} đơn vị kế thừa hạng đại học mẹ. Hạng 2026 dùng tham khảo cho mọi năm, không phải hạng riêng của trường thành viên.</p>
      <p>Đề án: ${META.stats.dean_unis}/${META.stats.unis} trường có bài nguồn <a href="https://huongnghiep.hocmai.vn/" target="_blank" rel="noopener">HOCMAI</a>, chỉ tóm tắt dữ kiện. Tỉnh/thành ưu tiên VNUR; HOCMAI bổ sung khi còn thiếu; chưa biết ghi “Khác”.</p>
      <div class="tbl-wrap"><table><thead><tr><th>Trường</th>${d.years.map((y) => `<th class="num">${y}</th>`).join("")}</tr></thead><tbody>
      ${d.universities.map((u) => `<tr><td><a href="#uni/${esc(u.uni_code)}/${d.years[0]}" data-uni="${esc(u.uni_code)}">${esc(u.uni_code)} · ${esc(u.name)}</a></td>${d.years.map((y) => `<td class="num">${u.counts[y] ? fmt(u.counts[y]) : "—"}</td>`).join("")}</tr>`).join("")}</tbody></table></div>
      <h2>${d.missing.length} trường nguồn chưa có điểm</h2><ul>${d.missing.map((u) => `<li>${esc(u.uni_code)} · ${esc(u.name)}</li>`).join("")}</ul></div>`;
  } catch (e) { fail(out, e); }
}
$("#coverage-out").addEventListener("click", (e) => {
  const a = e.target.closest("[data-uni]");
  if (a) {
    e.preventDefault();
    $("#uni-year").value = a.hash.split("/")[2];
    showTab("uni"); curUni = a.dataset.uni; loadUni();
  }
});

(async function init() {
  try { META = await api("api/meta"); } catch (e) { $("#stats").textContent = "Lỗi: " + e.message; return; }
  const yearOpts = META.years.map((y) => `<option>${y}</option>`).join("");
  ["#uni-year", "#major-year", "#adv-year"].forEach((s) => ($(s).innerHTML = yearOpts));
  const mOpts = META.methods.map((m) => `<option value="${m.method}">${esc(m.method_name)}</option>`).join("");
  $("#major-method").insertAdjacentHTML("beforeend", mOpts);
  $("#adv-method").innerHTML = mOpts;
  $("#major-method").value = "THPT";
  filterCombos();
  UNIVERSITIES = (await Data.searchIndex()).unis;
  $("#uni-letter").insertAdjacentHTML("beforeend", [...new Set(UNIVERSITIES.map((u) => uniNameKey(u)[0]))].sort().map((c) => `<option value="${esc(c)}">${esc(c.toUpperCase())}</option>`).join(""));
  $("#uni-province").insertAdjacentHTML("beforeend", [...new Set(UNIVERSITIES.map((u) => u.province))].sort((a, b) => a.localeCompare(b, "vi")).map((p) => `<option>${esc(p)}</option>`).join(""));
  renderUniGrid();
  const st = META.stats;
  $("#stats").textContent = `${st.rows.toLocaleString("vi-VN")} điểm chuẩn · ${st.unis} trường · ${st.majors} ngành · năm ${META.years.slice().reverse().join(", ")}`;
  const [tab, code, year] = location.hash.slice(1).split("/");
  if (tab) showTab(tab);
  if (year && META.years.includes(+year)) ["#uni-year", "#major-year"].forEach((s) => ($(s).value = year));
  if (tab === "uni" && code) { curUni = code; $("#uni-q").value = code; loadUni(); }
  if (tab === "major" && code) {
    curMajor = code.startsWith("~") ? { name: decodeURIComponent(code.slice(1)) } : { code };
    $("#major-q").value = curMajor.name || code;
    loadMajor();
  }
})();
