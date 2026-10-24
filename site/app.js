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
    const offset = Math.max(0, Number(q.get("offset") || 0)), limit = Math.max(0, Math.min(1000, q.has("limit") ? Number(q.get("limit")) : 50));
    const out = { year, method, combo, score, offset, scale: d.scale, margin, counts: {}, total: 0, rows: [] };
    if (d.scale == null) return out;
    const levels = ["Thử sức", "Vừa sức", "An toàn"], unit = d.scale / 30, cands = [];
    for (const values of d.rows) {
      if (combo && !values[d.columns.length].includes(combo.toUpperCase())) continue;
      const r = Object.fromEntries(d.columns.map((k, i) => [k, values[i]]));
      if (r.score > score + margin) continue;
      const delta = r.score - score;
      r.level = levels[delta > 0 ? 0 : delta > -unit ? 1 : 2]; cands.push(r);
    }
    cands.sort((a, b) => b.hot - a.hot); // on dinh nhu Python: cung do hot giu thu tu diem giam dan
    out.counts = Object.fromEntries(levels.map((lv) => [lv, cands.filter((r) => r.level === lv).length]));
    out.total = cands.length;
    out.rows = cands.slice(offset, offset + limit).map((r) => {
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
const comboHtml = (s) => !s ? "" : `<span class="combo-values">` + s.split(";").filter(Boolean).map((c) => `<span class="combo-code" title="${esc(META?.combo_subjects[c] || "Chưa có tên môn từ nguồn")}">${esc(c)}</span>`).join(", ") + "</span>";
const rankHtml = (u, compact = false) => u.vnur_rank == null ? `<span class="sub">Chưa có hạng</span>` : `<span class="rank-badge${u.vnur_parent ? " rank-inherited" : ""}">${compact ? `${u.vnur_rank}${u.vnur_parent ? ` (${esc(u.vnur_parent)})` : ""}` : u.vnur_parent ? `Thuộc ${esc(u.vnur_parent)} · Top ${u.vnur_rank}` : `Top ${u.vnur_rank} VNUR`}</span>`;
const DEAN_FIELDS = [["audience", "Đối tượng"], ["conditions", "Điều kiện / ngưỡng đầu vào"], ["formula", "Cách tính điểm"], ["bonus", "Điểm cộng / ưu tiên"], ["quota", "Chỉ tiêu"], ["notes", "Ghi chú"]];
const bulletList = (items) => `<ul>${items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`;
const factGroups = (fields) => DEAN_FIELDS.filter(([k]) => fields[k]?.length).map(([k, label]) => `<div class="fact-group"><h4>${label}</h4>${bulletList(fields[k])}</div>`).join("");
function deanHtml(plan, scoreYear) {
  if (!plan) return `<section class="card dean-block"><h2>Đề án tuyển sinh</h2><p class="muted">Chưa có dữ liệu đề án</p></section>`;
  const methods = plan.methods.map((m, i) => `<details class="dean-method"${i === 0 ? " open" : ""}><summary>${esc(m.name)}</summary>
    ${factGroups(m.fields) || `<p class="muted small">Bài nguồn chưa có dữ kiện chi tiết cho phương thức này.</p>`}
    ${m.shared ? `<p class="muted small">Một số quy định áp dụng chung: xem mục Quy định chung.</p>` : ""}</details>`).join("");
  const common = DEAN_FIELDS.some(([k]) => plan.common[k]?.length) ? `<details class="dean-method dean-common"><summary>Quy định chung (áp dụng cho nhiều phương thức)</summary>${factGroups(plan.common)}</details>` : "";
  const timeline = plan.timeline.length ? `<div class="fact-group"><h4>Mốc thời gian</h4><table class="timeline"><tbody>${plan.timeline.map((t) => `<tr><td class="num">${esc(t.date)}</td><td>${esc(t.event)}</td></tr>`).join("")}</tbody></table></div>` : "";
  const docs = plan.documents.length ? `<div class="fact-group"><h4>Hồ sơ</h4>${bulletList(plan.documents)}</div>` : "";
  return `<section class="card dean-block"><h2>Đề án tuyển sinh ${plan.year || ""}</h2>
    <p class="muted small">${esc(plan.province)}${plan.groups.length ? " · " + esc(plan.groups.join(", ")) : ""}${plan.year !== scoreYear ? ` · Đề án khác năm bảng điểm ${scoreYear}` : ""}</p>
    ${plan.methods_year && plan.methods_year !== plan.year ? `<p class="dean-note">Phần phương thức trong bài vẫn ghi năm ${plan.methods_year}; tiêu đề đề án ghi năm ${plan.year}.</p>` : ""}
    ${plan.quota.length ? `<div class="fact-group dean-quota"><h4>Chỉ tiêu</h4>${bulletList(plan.quota)}</div>` : ""}
    <h3>Phương thức xét tuyển</h3>
    <div class="dean-methods">${methods || `<p class="muted">Bài nguồn chưa có mục phương thức xét tuyển.</p>`}${common}</div>
    <h3>Thời gian &amp; hồ sơ</h3>
    ${timeline || docs ? `<div class="dean-time">${timeline}${docs}</div>` : `<p class="muted small">Bài nguồn chưa có dữ kiện thời gian hoặc hồ sơ.</p>`}
    <p class="dean-source muted small">Nguồn dữ kiện: <a href="${esc(plan.source_url)}" target="_blank" rel="noopener noreferrer">HOCMAI</a>, năm ${esc(plan.year ?? "")}</p></section>`;
}
const SOURCE_TYPES = { official: "Trang/đề án chính thức của trường", press: "Báo chí", aggregator: "Trang tổng hợp" };
function tuitionHtml(t) {
  if (!t) return `<section class="card tuition-card"><h2>Học phí</h2><p class="muted">Chưa có thông tin học phí</p></section>`;
  const one = t.max_mil == null || t.max_mil === t.min_mil;
  let host = "";
  try { host = new URL(t.source_url).hostname.replace(/^www\./, ""); } catch {}
  const free = t.min_mil === 0 && t.max_mil === 0;
  const label = { official: "Chính thức", press: "Báo chí", aggregator: "Tổng hợp" }[t.source_type];
  return `<section class="card tuition-card"><div class="head"><h2>Học phí</h2><span class="tuition-meta">${label ? `<span class="src-tag src-${esc(t.source_type)}">${label}</span>` : ""}<span class="muted small">Năm học ${t.year}–${t.year + 1}</span></span></div>
    <p class="tuition-range">${free ? "Miễn học phí" : `${t.max_mil == null ? "Từ " : ""}${one ? fmt(t.min_mil) : `${fmt(t.min_mil)}–${fmt(t.max_mil)}`} <span>triệu đồng/năm</span>`}</p>
    ${free ? `<p class="muted small">Theo quy định chung đối với học viên hệ quân sự/công an.</p>` : `${t.text ? `<p>${esc(t.text)}</p>` : ""}${!t.unit_note ? "" : /×|quy đổi/.test(t.unit_note) ? `<p class="tuition-convert small">Ước tính quy đổi: ${esc(t.unit_note)}</p>` : `<p class="muted small">${esc(t.unit_note)}</p>`}`}
    <p class="muted small">Nguồn: <a href="${esc(t.source_url)}" target="_blank" rel="noopener noreferrer">${esc(SOURCE_TYPES[t.source_type] || "Nguồn")}${host ? ` (${esc(host)})` : ""}</a></p></section>`;
}
// 89 truong tra tay (data/clean/tuition_extra.json): giu don vi goc, khong quy doi sang nam
const EVIDENCE = { official: "Chính thức", official_archived: "Văn bản chính thức (bản lưu)", secondary: "Tham khảo", unverified: "Chưa xác minh" };
const hostOf = (u) => { try { return new URL(u).hostname.replace(/^www\./, ""); } catch { return "nguồn"; } };
const itemRows = (items) => items.map((i) => `<tr><td>${esc(i.name)}</td><td class="num">${esc(i.amount)} ${esc(i.unit)}${i.extra ? `<div class="muted small">${esc(i.extra)}</div>` : ""}</td></tr>`).join("");
function tuitionExtraHtml(x) {
  const f = new Set(x.flags);
  const year = /^\d{4}–\d{4}$/.test(x.school_year) ? `Năm học ${x.school_year}` : x.school_year;
  const links = x.sources.slice(0, 3);
  const head = `<div class="head"><h2>Học phí</h2><span class="tuition-meta"><span class="src-tag ev-${esc(x.evidence)}">${EVIDENCE[x.evidence]}</span>${year ? `<span class="muted small">${esc(year)}</span>` : ""}</span></div>`;
  if (x.evidence === "unverified")
    return `<section class="card tuition-card tuition-extra">${head}<p>Chưa có mức học phí được xác minh</p>
      ${links.length ? `<p class="small"><a href="${esc(links[0])}" target="_blank" rel="noopener noreferrer">Xem thông báo của trường</a></p>` : ""}</section>`;
  const notes = [];
  if (f.has("nam_cu")) notes.push(`Mức học phí năm ${x.school_year}, có thể đã thay đổi`);
  if (f.has("theo_tin_chi")) notes.push("Học phí tính theo tín chỉ; tổng mỗi năm phụ thuộc số tín chỉ đăng ký");
  if (f.has("theo_hoc_ky") || f.has("theo_thang")) notes.push("Mức theo học kỳ/tháng, không phải cả năm");
  if (f.has("toan_khoa")) notes.push("Có mức tính cho toàn khoá, không phải mỗi năm");
  if (f.has("du_kien")) notes.push("Mức dự kiến, chưa phải quyết định chính thức");
  if (f.has("tam_thu")) notes.push("Mức tạm thu, có thể điều chỉnh khi có quyết định chính thức");
  if (f.has("trung_binh")) notes.push("Mức trung bình, học phí từng ngành có thể khác");
  if (f.has("chi_mot_nganh")) notes.push(x.only_major ? `Chỉ có thông tin cho ngành ${x.only_major}` : "Chỉ có thông tin cho một số ngành");
  if (f.has("co_uu_dai")) notes.push("Mức niêm yết, chưa trừ ưu đãi");
  if (x.evidence === "secondary") notes.push("Thông tin tham khảo, chưa đối chiếu văn bản gốc của trường");
  const items = x.items.length ? `<div class="fact-group"><h4>Theo ngành</h4><table class="tuition-items"><tbody>${itemRows(x.items.slice(0, 6))}</tbody></table>
    ${x.items.length > 6 ? `<details class="more-items"><summary>Xem thêm ${x.items.length - 6} dòng</summary><table class="tuition-items"><tbody>${itemRows(x.items.slice(6))}</tbody></table></details>` : ""}</div>` : "";
  return `<section class="card tuition-card tuition-extra${f.has("nam_cu") ? " tuition-old" : ""}">${head}
    <p class="${x.summary.length <= 60 ? "tuition-range" : "tuition-summary"}">${esc(x.summary)}</p>
    ${x.scope && x.scope !== x.school_year ? `<p class="muted small">Phạm vi: ${esc(x.scope)}</p>` : ""}
    ${items}
    ${notes.length ? `<ul class="tuition-notes">${notes.map((n) => `<li>${esc(n)}</li>`).join("")}</ul>` : ""}
    ${x.note ? `<p class="muted small">${esc(x.note)}</p>` : ""}
    <p class="muted small">Nguồn: ${links.map((u) => `<a href="${esc(u)}" target="_blank" rel="noopener noreferrer">${esc(hostOf(u))}</a>`).join(" · ")}</p></section>`;
}
const feeHtml = (d) => (d.tuition_extra ? tuitionExtraHtml(d.tuition_extra) : tuitionHtml(d.tuition));
const fail = (out, e) => (out.innerHTML = `<div class="card empty">Lỗi: ${esc(e.message)}</div>`);
const TABS = ["uni", "major", "advice", "network", "coverage"];
let META = null;
let UNIVERSITIES = [];

const uniNameKey = (u) => unaccent(u.name).replace(/^(truong\s+)?dai hoc\s+|^hoc vien\s+|^phan hieu\s+/, "");
// hang VNUR tang dan; truong ke thua dung o hang cua dai hoc me (cung hang: truc tiep truoc); chua xep hang cuoi, theo ten
function renderUniGrid() {
  const words = unaccent($("#uni-q").value).split(" "), province = $("#uni-province").value;
  const items = UNIVERSITIES.filter((u) => words.every((w) => u._k.includes(w)) && (!province || u.province === province));
  items.sort((a, b) => (a.vnur_rank ?? Infinity) - (b.vnur_rank ?? Infinity) || Number(!!a.vnur_parent) - Number(!!b.vnur_parent)
    || (a.vnur_parent || "").localeCompare(b.vnur_parent || "", "vi") || uniNameKey(a).localeCompare(uniNameKey(b), "vi") || a.uni_code.localeCompare(b.uni_code));
  $("#uni-count").textContent = `${items.length} trường · Xếp theo hạng VNUR 2026 tăng dần; trường thành viên đứng ở hạng của đại học mẹ (cùng hạng: hạng trực tiếp trước), rồi các trường chưa xếp hạng theo tên. Thống kê theo năm mới nhất của từng trường.`;
  $("#uni-grid").innerHTML = items.length ? items.map((u) => `<button type="button" class="uni-card" data-uni="${esc(u.uni_code)}" data-year="${u.latest_year}">
    <span class="uni-code-badge">${esc(u.uni_code)}</span><span class="uni-card-name">${esc(u.name)}</span>
    <span class="sub">${u.n_programs} mã xét tuyển · ${u.n_methods} phương thức · ${u.latest_year}</span>
    ${u.first_year > 2024 ? `<span class="sub">mới có ${u.first_year}</span>` : ""}
    <span class="sub">${esc(u.province)}</span>${u.vnur_rank != null ? rankHtml(u) : ""}</button>`).join("") : `<p class="muted">Không tìm thấy trường phù hợp.</p>`;
}
$("#uni-q").addEventListener("input", renderUniGrid);
$("#uni-province").addEventListener("change", renderUniGrid);
$("#uni-grid").addEventListener("click", (e) => {
  const card = e.target.closest("[data-uni]");
  if (card) { curUni = card.dataset.uni; $("#uni-year").value = card.dataset.year; loadUni(); }
});

function fillCombos() {
  $("#adv-combo").innerHTML = `<option value="">Mọi tổ hợp</option>` + META.combos.map((c) => `<option value="${esc(c)}">${esc(c)}${META.combo_subjects[c] ? ` (${esc(META.combo_subjects[c])})` : ""}</option>`).join("");
}

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
    out.innerHTML = `<div class="card empty">${esc(d.university.name)} chưa có dữ liệu năm ${d.year}. Năm có dữ liệu: ${d.years.join(", ") || "—"}</div>${deanHtml(d.dean, d.year)}${feeHtml(d)}`;
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
  out.innerHTML = `<div class="card">
    <div class="head"><h2>${esc(d.university.name)} <span class="sub">(${esc(d.university.uni_code)})</span></h2>
      <span class="muted small">${d.rows.length} chương trình · năm ${d.year} · <a href="${esc(d.source_url)}" target="_blank" rel="noopener">nguồn</a></span></div>
    <div class="tbl-wrap"><table class="stack">
      <thead><tr><th>Mã</th><th>Ngành / chương trình</th><th>Tổ hợp</th>${cols.map((m) => `<th class="num">${esc(m.method_name)}</th>`).join("")}</tr></thead>
      <tbody>${body}</tbody></table></div></div>${deanHtml(d.dean, d.year)}${feeHtml(d)}`;
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
  out.innerHTML = `<div class="card"><div class="head"><h2>${esc(d.major.major_name)} <span class="sub">${esc(d.major.major_code || "chưa map")}</span></h2>
    <span class="muted small">${unis} trường · ${d.rows.length} dòng · năm ${d.year}</span></div>${rawNote}${simHtml}
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
let adv = null; // { query, d (trang dau), rows (da tai) }
const ADV_LEVEL = { "Thử sức": "lvl-try", "Vừa sức": "lvl-fit", "An toàn": "lvl-safe" };
const pct = (x) => fmt(Math.round(x * 100) / 100);
const whyHtml = (r) => {
  const tip = `Độ hot ${pct(r.hot)} = 0,5 × điểm trường ${pct(r.hot_uni)} + 0,3 × điểm ngành ${pct(r.hot_major)} + 0,2 × điểm xu hướng ${pct(r.hot_trend)}`;
  return `<details class="why"><summary title="${esc(tip)}">${pct(r.hot)}</summary><span class="sub">Trường ${pct(r.hot_uni)} · Ngành ${pct(r.hot_major)} · Xu hướng ${pct(r.hot_trend)}</span></details>`;
};
$("#advice-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const out = $("#advice-out");
  out.innerHTML = `<div class="empty">Đang tải…</div>`;
  const query = new URLSearchParams({ method: $("#adv-method").value, score: $("#adv-score").value, combo: $("#adv-combo").value, year: $("#adv-year").value });
  let d;
  try { d = await api("api/advice?" + query); } catch (err) { return fail(out, err); }
  adv = { query, d, rows: d.rows };
  renderAdvice();
});
$("#advice-out").addEventListener("click", async (e) => {
  const b = e.target.closest("#adv-more");
  if (!b || !adv) return;
  b.disabled = true; b.textContent = "Đang tải…";
  const q = new URLSearchParams(adv.query); q.set("offset", adv.rows.length);
  try { adv.rows = adv.rows.concat((await api("api/advice?" + q)).rows); } catch (err) { return fail($("#advice-out"), err); }
  renderAdvice();
});
function renderAdvice() {
  const out = $("#advice-out"), { d, rows } = adv;
  if (!rows.length) { out.innerHTML = `<div class="card empty">Không có ngành phù hợp.</div>`; return; }
  const yrs = [...new Set(rows.flatMap((r) => Object.keys(r.history)))].sort();
  out.innerHTML = `<div class="card"><div class="head"><h2>${d.total} lựa chọn với ${fmt(d.score)} điểm${d.scale !== 30 ? ` <span class="sub">(thang ${fmt(d.scale)})</span>` : ""}</h2>
    <span class="muted small">Thử sức ${d.counts["Thử sức"]} · Vừa sức ${d.counts["Vừa sức"]} · An toàn ${d.counts["An toàn"]} · tham chiếu năm ${d.year} · xếp theo độ hot · đang hiện ${rows.length}/${d.total}</span></div>
    <div class="tbl-wrap"><table class="stack"><thead><tr><th>Mức</th><th>Trường</th><th>Hạng VNUR</th><th>Ngành / chương trình</th><th>Tổ hợp</th>${yrs.map((y) => `<th class="num">${y}</th>`).join("")}<th class="num">Vì sao ở đây</th></tr></thead>
    <tbody>${rows.map((r) => `<tr><td data-label="Mức"><span class="lvl ${ADV_LEVEL[r.level]}">${r.level}</span></td>
      <td data-label="Trường">${uniCell(r)}</td><td data-label="Hạng VNUR">${rankHtml(r, true)}</td><td class="main">${esc(r.program_name)}${tag(r.program_type)}${r.hot_badge ? `<span class="tag tag-hot">Ngành hot 2026</span>` : ""}</td>
      <td class="sub" data-label="Tổ hợp">${comboHtml(r.combos)}</td>
      ${yrs.map((y) => `<td class="num" data-label="${y}">${y == d.year ? `<b>${fmt(r.history[y])}</b>` : fmt(r.history[y])}</td>`).join("")}
      <td class="num" data-label="Vì sao ở đây (độ hot)">${whyHtml(r)}</td></tr>`).join("")}</tbody></table></div>
    ${rows.length < d.total ? `<p class="more"><button type="button" class="primary" id="adv-more">Xem thêm (${Math.min(50, d.total - rows.length)} dòng)</button></p>` : ""}</div>`;
}

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
  $("#net-side").innerHTML = `<h3>${esc(g.title || name)} · ${year}</h3><p class="muted">${esc(g.description || "")}</p>
    <table>${Object.entries(s).map(([k, v]) => `<tr><td>${esc(k)}</td><td class="num">${esc(v)}</td></tr>`).join("")}</table>
    ${Object.entries(g.top || {}).map(([m, rows]) => `<h3>Top ${esc(m)}</h3><table>${rows.map((r) => `<tr><td>${esc(r[0])}</td><td class="num">${esc(r[1])}</td></tr>`).join("")}</table>`).join("")}`;
}

/* ---------- init ---------- */
function tuitionCoverageHtml(d) {
  const s = META.stats, src = s.tuition_sources || { old: {}, new: {} };
  const n = (o, k) => o[k] || 0;
  const unverified = d.tuition_missing.filter((u) => u.unverified).length;
  return `<h2>Học phí</h2>
    <p><b>${s.tuition_unis}/${s.unis} trường có mức học phí</b> (${fmt(s.tuition_unis / s.unis * 100)}%).</p>
    <ul><li>Bộ đầu (${Object.values(src.old).reduce((a, b) => a + b, 0)} trường, quy về triệu đồng/năm; tín chỉ × 30, học kỳ × 2, tháng × 10 ghi ở từng thẻ): ${n(src.old, "official")} trang/đề án chính thức · ${n(src.old, "press")} báo chí · ${n(src.old, "aggregator")} trang tổng hợp.</li>
    <li>Bộ tra tay bổ sung (${Object.values(src.new).reduce((a, b) => a + b, 0)} trường, giữ đơn vị gốc, không quy đổi sang năm): ${n(src.new, "official")} chính thức · ${n(src.new, "official_archived")} văn bản chính thức (bản lưu) · ${n(src.new, "secondary")} tham khảo · ${n(src.new, "unverified")} chưa xác minh được mức tiền.</li></ul>
    <h3>${d.tuition_missing.length} trường còn thiếu mức học phí${unverified ? ` (${unverified} có thông báo nhưng chưa xác minh được số tiền)` : ""}</h3>
    <ul class="tuition-missing-list">${d.tuition_missing.map((u) => `<li>${esc(u.uni_code)} · ${esc(u.name)}${u.unverified ? ` <span class="muted small">— chưa xác minh</span>` : ""}</li>`).join("")}</ul>`;
}
async function loadCoverage() {
  const out = $("#coverage-out");
  try {
    const d = await api("api/coverage");
    out.innerHTML = `<div class="card"><p>Nguồn: <a href="${esc(d.source_url)}" target="_blank" rel="noopener">tuyensinh247</a> · Thu thập: ${esc(d.collected_from?.slice(0, 10))} đến ${esc(d.collected_to?.slice(0, 10))}.</p>
      <p>${d.universities.length} trường có điểm · ${d.missing.length} trường trong danh mục nguồn chưa có điểm trong các năm ${d.years.join(", ")}. Ô số là số dòng điểm, dấu — là chưa có dữ liệu; không có nghĩa trường không tuyển sinh.</p>
      <p>Xếp hạng: <a href="${esc(META.ranking_source.url)}" target="_blank" rel="noopener">VNUR 2026</a> · ${META.stats.ranked_unis} trường có hạng, gồm ${META.stats.inherited_unis} đơn vị kế thừa hạng đại học mẹ. Hạng 2026 dùng tham khảo cho mọi năm, không phải hạng riêng của trường thành viên.</p>
      ${tuitionCoverageHtml(d)}
      <h2>Độ hot trong tab Tư vấn</h2>
      <p><b>Độ hot = 0,5 × điểm trường + 0,3 × điểm ngành + 0,2 × điểm xu hướng</b>, mỗi phần trong khoảng 0–1; kết quả xếp từ cao xuống thấp.</p>
      <ul><li><b>Điểm trường</b>: hạng VNUR 2026 trực tiếp 1 → 1,0 … 100 → 0,01 (= (101 − hạng)/100); hạng kế thừa đại học mẹ nhân 0,8; chưa xếp hạng = 0.</li>
      <li><b>Điểm ngành</b>: percentile của mức tăng số trường mở ngành (mã ngành 7 số) từ 2024 đến 2026, lấy từ bậc của nút ngành trong mạng G1. ${META.stats.hot_majors} ngành (10% cao nhất) gắn nhãn “Ngành hot 2026”. Dòng chưa có mã ngành = 0.</li>
      <li><b>Điểm xu hướng</b>: percentile mức thay đổi điểm chuẩn 2025 → 2026 của chính chương trình (cùng trường, mã chương trình, phương thức, thang điểm), so trong cùng phương thức; thiếu một trong hai năm = 0,5.</li></ul>
      <p>Đề án: ${META.stats.dean_unis}/${META.stats.unis} trường có bài nguồn <a href="https://huongnghiep.hocmai.vn/" target="_blank" rel="noopener">HOCMAI</a>; mỗi phương thức tách thành đối tượng, điều kiện, cách tính điểm, điểm cộng, chỉ tiêu, ghi chú (gạch đầu dòng ngắn, không chép nguyên đoạn). Tỉnh/thành ưu tiên VNUR; HOCMAI bổ sung khi còn thiếu; chưa biết ghi “Khác”.</p>
      <div class="tbl-wrap"><table><thead><tr><th>Trường</th>${d.years.map((y) => `<th class="num">${y}</th>`).join("")}</tr></thead><tbody>
      ${d.universities.map((u) => `<tr><td><a href="#uni/${esc(u.uni_code)}/${d.years[0]}" data-uni="${esc(u.uni_code)}">${esc(u.uni_code)} · ${esc(u.name)}</a></td>${d.years.map((y) => `<td class="num">${u.counts[y] ? fmt(u.counts[y]) : "—"}</td>`).join("")}</tr>`).join("")}</tbody></table></div>
      <h2>${d.missing.length} trường nguồn chưa có điểm</h2><ul class="missing-list">${d.missing.map((u) => `<li>${esc(u.uni_code)} · ${esc(u.name)}</li>`).join("")}</ul></div>`;
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
  fillCombos();
  UNIVERSITIES = (await Data.searchIndex()).unis;
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
