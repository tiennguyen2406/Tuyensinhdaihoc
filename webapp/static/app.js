const $ = (s) => document.querySelector(s);
const api = async (p) => {
  const r = await fetch(p);
  if (!r.ok) { const t = await r.text(); let m = t; try { m = JSON.parse(t).detail; } catch {} throw new Error(m || r.status); }
  return r.json();
};
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmt = (x) => (x == null || x === "" ? "" : Number(x).toLocaleString("vi-VN", { maximumFractionDigits: 2 }));
const PT = { CHUAN: "", CLC: "CLC", TIEN_TIEN: "Tiên tiến", LIEN_KET: "Liên kết", TIENG_ANH: "Tiếng Anh", PHAN_HIEU: "Phân hiệu", TAI_NANG: "Tài năng" };
const uniCell = (r) => `<span title="${esc(r.uni_name)}">${esc(shortUni(r.uni_name))}</span> <span class="sub">${esc(r.uni_code)}</span>`;
const shortUni = (n) => String(n || "").replace(/^(Trường\s+)?(Đại\s+Học|Đại\s+học)\s+/i, "ĐH ").replace(/^Học\s+Viện\s+/i, "HV ");
const tag = (t) => (PT[t] ? `<span class="tag">${PT[t]}</span>` : "");
const combos = (s) => (s || "").replaceAll(";", ", ");
const fail = (out, e) => (out.innerHTML = `<div class="card empty">Lỗi: ${esc(e.message)}</div>`);
const TABS = ["uni", "major", "advice", "network"];
let META = null;

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
autocomplete($("#uni-q"), $("#uni-ac"), "/api/universities?q=",
  (u) => `<span>${esc(u.name)}</span><span class="code">${esc(u.uni_code)}${u.short_name ? " · " + esc(u.short_name) : ""}</span>`,
  (u) => { curUni = u.uni_code; $("#uni-q").value = u.name; loadUni(); });
$("#uni-year").addEventListener("change", () => curUni && loadUni());

async function loadUni() {
  const out = $("#uni-out");
  out.innerHTML = `<div class="empty">Đang tải…</div>`;
  let d;
  try { d = await api(`/api/universities/${encodeURIComponent(curUni)}/scores?year=${$("#uni-year").value}`); } catch (e) { return fail(out, e); }
  location.hash = `uni/${curUni}/${d.year}`;
  $("#uni-q").value = d.university.name;
  if (!d.rows.length) {
    out.innerHTML = `<div class="card empty">${esc(d.university.name)} chưa có dữ liệu năm ${d.year}. Năm có dữ liệu: ${d.years.join(", ") || "—"}</div>`;
    return;
  }
  const cols = d.methods;
  const more = (r, m) => r.scores[m + "_more"] || [];
  const cell = (c) => !c ? "" : `${fmt(c.score)}${c.equiv != null ? `<span class="eq">≈ ${fmt(c.equiv)}/30</span>` : ""}`;
  const body = d.rows.map((r) => `<tr>
      <td class="code" data-label="Mã">${esc(r.program_code)}</td>
      <td class="prog main">${esc(r.program_name)}${tag(r.program_type)}${r.notes.length ? `<div class="sub">${esc(r.notes.join(" · "))}</div>` : ""}</td>
      <td class="combo" data-label="Tổ hợp">${esc(combos(r.combos))}</td>
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
      <tbody>${body}</tbody><tfoot>${foot}</tfoot></table></div></div>`;
}

/* ---------- 1b. theo nganh (hoac ten chuong trinh goc chua map) ---------- */
let curMajor = null; // {code} hoac {name}
autocomplete($("#major-q"), $("#major-ac"), "/api/majors?q=",
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
    ? `/api/majors/${encodeURIComponent(code)}/scores?year=${year}&method=${method}`
    : `/api/programs/scores?name=${encodeURIComponent(name)}&year=${year}&method=${method}`;
  let d;
  try { d = await api(url); } catch (e) { return fail(out, e); }
  location.hash = code ? `major/${code}/${d.year}` : `major/~${encodeURIComponent(name)}/${d.year}`;
  $("#major-q").value = d.major.major_name;
  const rawNote = d.major.unmapped ? `<p class="muted small">Tên chương trình gốc, chưa gán mã ngành chuẩn — chỉ gồm các dòng chưa map${d.years ? ` (năm có dữ liệu: ${d.years.join(", ")})` : ""}.</p>` : "";
  if (!d.rows.length) { out.innerHTML = `<div class="card empty">Chưa có dữ liệu cho ${code ? "ngành" : "chương trình"} này năm ${d.year}.${rawNote}</div>`; return; }
  const unis = new Set(d.rows.map((r) => r.uni_code)).size;
  const sim = code ? await api(`/api/majors/${encodeURIComponent(code)}/similar?year=${d.year}`).catch(() => []) : [];
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
      <td class="sub" data-label="Tổ hợp">${esc(combos(r.combos))}</td>
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
  const q = new URLSearchParams({ method: $("#adv-method").value, score: $("#adv-score").value, combo: $("#adv-combo").value, year: $("#adv-year").value });
  let d;
  try { d = await api("/api/advice?" + q); } catch (err) { return fail(out, err); }
  if (!d.rows.length) { out.innerHTML = `<div class="card empty">Không có ngành phù hợp.</div>`; return; }
  const yrs = [...new Set(d.rows.flatMap((r) => Object.keys(r.history)))].sort();
  const cls = { "Thử sức": "lvl-try", "Vừa sức": "lvl-fit", "An toàn": "lvl-safe" };
  const shown = (l) => d.rows.filter((r) => r.level === l).length;
  const cnt = (l) => (shown(l) < d.counts[l] ? `${shown(l)}/${d.counts[l]}` : `${d.counts[l]}`);
  setExport("advice", `tu-van-${slug(d.method)}-${d.score}${d.combo ? "-" + d.combo : ""}-${d.year}.csv`,
    ["Mức", "Mã trường", "Trường", "Mã chương trình", "Ngành / chương trình", "Mã ngành", "Tổ hợp", "Thang", ...yrs.map((y) => `Điểm ${y}`)],
    d.rows.map((r) => [r.level, r.uni_code, r.uni_name, r.program_code, r.program_name, r.major_code, combos(r.combos), r.scale_max, ...yrs.map((y) => r.history[y])]));
  out.innerHTML = `<div class="card"><div class="head"><h2>${d.total} lựa chọn với ${fmt(d.score)} điểm${d.scale !== 30 ? ` <span class="sub">(thang ${fmt(d.scale)})</span>` : ""}</h2>
    <span class="muted small">Thử sức ${cnt("Thử sức")} · Vừa sức ${cnt("Vừa sức")} · An toàn ${cnt("An toàn")} · tham chiếu năm ${d.year}${d.rows.length < d.total ? ` · hiện ${d.rows.length} dòng sát điểm nhất` : ""} ${csvBtn("advice")}</span></div>
    <div class="tbl-wrap"><table class="stack"><thead><tr><th>Mức</th><th>Trường</th><th>Ngành / chương trình</th><th>Tổ hợp</th>${yrs.map((y) => `<th class="num">${y}</th>`).join("")}</tr></thead>
    <tbody>${d.rows.map((r) => `<tr><td data-label="Mức"><span class="lvl ${cls[r.level]}">${r.level}</span></td>
      <td data-label="Trường">${uniCell(r)}</td><td class="main">${esc(r.program_name)}${tag(r.program_type)}</td>
      <td class="sub" data-label="Tổ hợp">${esc(combos(r.combos))}</td>
      ${yrs.map((y) => `<td class="num" data-label="${y}">${y == d.year ? `<b>${fmt(r.history[y])}</b>` : fmt(r.history[y])}</td>`).join("")}</tr>`).join("")}</tbody></table></div></div>`;
});

/* ---------- 3. mang SNA ---------- */
let netLoaded = false, netObj = null;
async function loadNetworkList() {
  if (netLoaded) return; netLoaded = true;
  let names;
  try { names = await api("/api/network"); } catch (e) { netLoaded = false; return fail($("#net-canvas"), e); }
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
  try { g = await api(`/api/network/${name}?year=${year}`); } catch (e) { $("#net-side").innerHTML = `<p class="muted">Lỗi: ${esc(e.message)}</p>`; return; }
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
(async function init() {
  try { META = await api("/api/meta"); } catch (e) { $("#stats").textContent = "Lỗi: " + e.message; return; }
  const yearOpts = META.years.map((y) => `<option>${y}</option>`).join("");
  ["#uni-year", "#major-year", "#adv-year"].forEach((s) => ($(s).innerHTML = yearOpts));
  const mOpts = META.methods.map((m) => `<option value="${m.method}">${esc(m.method_name)}</option>`).join("");
  $("#major-method").insertAdjacentHTML("beforeend", mOpts);
  $("#adv-method").innerHTML = mOpts;
  $("#major-method").value = "THPT";
  $("#adv-combo").insertAdjacentHTML("beforeend", META.combos.map((c) => `<option>${c}</option>`).join(""));
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
