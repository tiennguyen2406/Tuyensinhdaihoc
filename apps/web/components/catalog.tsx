"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import type {
  CatalogData,
  Cutoff,
  Filters,
  ListEnvelope,
  Metadata,
  Offering,
  Source,
  University,
} from "../lib/contracts";
import { CatalogError, fetchJson, loadCatalog } from "../lib/api";
import { filterQuery, filtersFrom } from "../lib/filters";

export function Catalog(props: {
  initial: CatalogData | null;
  initialFilters: Filters;
  universityId?: string;
  initialError?: string;
}) {
  const { universityId } = props;
  const [filters, setFilters] = useState(props.initialFilters);
  const [revision, setRevision] = useState(0);
  const [state, setState] = useState({
    data: props.initial,
    error: props.initialError ?? "",
    pending: false,
  });
  const [paging, setPaging] = useState("");
  const generation = useRef(0);
  const activeFilterQuery = useRef(filterQuery(props.initialFilters));
  const controllers = useRef(new Set<AbortController>());

  function change(next: Filters, writeUrl = true) {
    activeFilterQuery.current = filterQuery(next);
    generation.current += 1;
    controllers.current.forEach((controller) => controller.abort());
    setFilters(next);
    setState({ data: null, error: "", pending: true });
    setPaging("");
    setRevision((value) => value + 1);
    if (writeUrl)
      window.history.replaceState(
        null,
        "",
        `${window.location.pathname}?${filterQuery(next)}`,
      );
  }

  useEffect(() => {
    const onPopState = () => {
      const next = filtersFrom(new URLSearchParams(window.location.search));
      if (filterQuery(next) !== activeFilterQuery.current) change(next, false);
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    if (revision === 0) return;
    const controller = new AbortController();
    const activeControllers = controllers.current;
    activeControllers.add(controller);
    const identity = generation.current;
    const timer = window.setTimeout(() => {
      loadCatalog("/api/catalog", filters, universityId, controller.signal)
        .then((data) => {
          if (identity === generation.current && !controller.signal.aborted)
            setState({ data, error: "", pending: false });
        })
        .catch((error) => {
          if (identity === generation.current && !controller.signal.aborted)
            setState({ data: null, error: message(error), pending: false });
        })
        .finally(() => activeControllers.delete(controller));
    }, 180);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
      activeControllers.delete(controller);
    };
  }, [filters, universityId, revision]);

  async function more(key: "universities" | "offerings" | "cutoffs") {
    const previous = state.data?.[key];
    if (!previous?.next_cursor) return;
    const controller = new AbortController();
    controllers.current.add(controller);
    const identity = generation.current;
    setPaging(key);
    const params = new URLSearchParams(filterQuery(filters));
    if (universityId) params.set("university_id", universityId);
    if (key === "cutoffs") params.delete("query");
    params.set("cursor", previous.next_cursor);
    try {
      const next = await fetchJson<
        ListEnvelope<University | Offering | Cutoff>
      >(
        `/api/catalog/${key === "offerings" ? "programs" : key}?${params}`,
        controller.signal,
      );
      if (identity !== generation.current || controller.signal.aborted) return;
      if (next.dataset_version !== previous.dataset_version)
        throw new CatalogError(409);
      setState((current) => ({
        ...current,
        error: "",
        data: current.data
          ? {
              ...current.data,
              [key]: { ...next, items: [...previous.items, ...next.items] },
            }
          : null,
      }));
    } catch (error) {
      if (identity === generation.current && !controller.signal.aborted)
        setState((current) => ({ ...current, error: message(error) }));
    } finally {
      controllers.current.delete(controller);
      if (identity === generation.current) setPaging("");
    }
  }

  const data = state.data;
  const metadata = data?.universities ?? data?.offerings;
  const title =
    data?.university?.item.name ??
    (universityId ? "Chi tiết trường" : "Tra cứu trường đại học");
  const detailFilters = { ...filters, query: "" };
  return (
    <>
      {universityId && (
        <Link
          prefetch={false}
          className="back"
          href={`/universities?${filterQuery(detailFilters)}`}
        >
          ← Danh sách trường
        </Link>
      )}
      <div className="page-heading">
        <p className="eyebrow">DỮ LIỆU TUYỂN SINH · NỘI BỘ DEV</p>
        <h1>{title}</h1>
        <p>Tra cứu thông tin và điểm chuẩn đã được xác minh theo từng năm.</p>
      </div>
      <form
        className="filters"
        role="search"
        onSubmit={(event) => {
          event.preventDefault();
          change(filters);
        }}
      >
        <label>
          Năm tuyển sinh
          <select
            value={filters.year}
            onChange={(event) =>
              change({ ...filters, year: event.target.value })
            }
          >
            {!["2024", "2025", "2026"].includes(filters.year) && (
              <option value={filters.year}>
                {filters.year} — không hỗ trợ
              </option>
            )}
            <option value="2024">2024</option>
            <option value="2025">2025</option>
            <option value="2026">2026</option>
          </select>
        </label>
        {!universityId && (
          <label>
            Tên hoặc mã trường
            <input
              type="search"
              value={filters.query}
              onChange={(event) =>
                change({ ...filters, query: event.target.value })
              }
              placeholder="Nhập tên, mã hoặc tên gọi đã duyệt"
              autoComplete="off"
            />
          </label>
        )}
        <label>
          Mã phương thức
          <input
            value={filters.method}
            onChange={(event) =>
              change({ ...filters, method: event.target.value })
            }
            placeholder="Ví dụ: THPT"
            list="method-options"
          />
        </label>
        <datalist id="method-options">
          {data?.university?.item.methods?.map((method) => (
            <option key={method.id} value={method.code}>
              {method.name}
            </option>
          ))}
        </datalist>
        <label>
          Cơ sở
          <input
            value={filters.campus}
            onChange={(event) =>
              change({ ...filters, campus: event.target.value })
            }
            placeholder="Tên cơ sở"
          />
        </label>
        <button className="secondary" type="submit">
          Tải lại
        </button>
      </form>
      <aside className="notice">
        Dữ liệu nội bộ chưa đầy đủ. Thông tin dùng để tra cứu nguồn, không đánh
        giá hay bảo đảm trúng tuyển.
      </aside>
      <div aria-live="polite" aria-atomic="true" className="status">
        {state.pending
          ? "Đang tải dữ liệu…"
          : metadata
            ? `Năm ${filters.year} · ${metadata.coverage.canonical_cutoff_count} mốc điểm chuẩn trong phạm vi dữ liệu`
            : ""}
      </div>
      {state.error && (
        <div className="error" role="alert">
          <p>{state.error}</p>
          <button type="button" onClick={() => change(filters)}>
            Thử lại
          </button>
        </div>
      )}
      <div aria-busy={state.pending}>
        {metadata && <MetadataNotice metadata={metadata} />}
        {data?.universities && (
          <section aria-label="Kết quả trường đại học">
            {data.universities.items.length === 0 ? (
              <Empty />
            ) : (
              <div className="university-grid">
                {data.universities.items.map((item) => (
                  <article className="university-card" key={item.id}>
                    <div className="card-kicker">
                      {item.code ?? "Chưa có mã"}{" "}
                      <span>Năm {item.selected_year}</span>
                    </div>
                    <h2>
                      <a
                        href={`/universities/${item.id}?${filterQuery(detailFilters)}`}
                      >
                        {item.name}
                      </a>
                    </h2>
                    <p className="muted">
                      {[item.province, item.type].filter(Boolean).join(" · ") ||
                        "Chưa có thông tin địa phương / loại hình"}
                    </p>
                    <dl className="counts">
                      <div>
                        <dt>Chương trình</dt>
                        <dd>{item.program_count}</dd>
                      </div>
                      <div>
                        <dt>Offering</dt>
                        <dd>{item.offering_count}</dd>
                      </div>
                      <div>
                        <dt>Mốc điểm</dt>
                        <dd>{item.cutoff_count}</dd>
                      </div>
                    </dl>
                    <Sources sources={item.sources} />
                  </article>
                ))}
              </div>
            )}
            <More
              envelope={data.universities}
              pending={paging !== ""}
              onClick={() => more("universities")}
            />
          </section>
        )}
        {data?.university && (
          <>
            <section className="summary" aria-label="Thông tin trường">
              <p>
                <strong>{data.university.item.code}</strong> · Năm{" "}
                {data.university.item.selected_year}
              </p>
              <Sources sources={data.university.item.sources} />
            </section>
            <section aria-labelledby="offerings-title">
              <h2 id="offerings-title">Chương trình tuyển sinh (Offering)</h2>
              <p className="muted">
                Mỗi Offering là một phiên bản tuyển sinh theo năm; chương trình
                gốc có định danh riêng.
              </p>
              {data.offerings?.items.length === 0 ? (
                <Empty />
              ) : (
                <div className="offering-grid">
                  {data.offerings?.items.map((item) => (
                    <article
                      className="offering-card"
                      key={item.program_year_id}
                    >
                      <p className="eyebrow">
                        {item.offering_code ?? "Chưa có mã Offering"} ·{" "}
                        {item.year}
                      </p>
                      <h3>{item.offering_name}</h3>
                      <p>{item.program_name}</p>
                      <dl>
                        <div>
                          <dt>Cơ sở</dt>
                          <dd>{item.campus ?? "Chưa có dữ liệu"}</dd>
                        </div>
                        <div>
                          <dt>Ngành</dt>
                          <dd>{item.major_name ?? "Chưa có dữ liệu"}</dd>
                        </div>
                        <div>
                          <dt>Ngôn ngữ / hệ</dt>
                          <dd>
                            {[item.language, item.track]
                              .filter(Boolean)
                              .join(" / ") || "Chưa có dữ liệu"}
                          </dd>
                        </div>
                        <div>
                          <dt>Phương thức</dt>
                          <dd>
                            {item.method_codes.join(", ") || "Chưa có dữ liệu"}
                          </dd>
                        </div>
                      </dl>
                      <p className="muted">
                        Học phí / học bổng: chưa có dữ liệu trong phạm vi này.
                      </p>
                      <p>
                        {item.cutoff_count} mốc điểm chuẩn ·{" "}
                        <a href="#cutoffs-title">Xem bảng điểm chuẩn</a>
                      </p>
                      <Sources sources={item.sources} />
                    </article>
                  ))}
                </div>
              )}
              {data.offerings && (
                <More
                  envelope={data.offerings}
                  pending={paging !== ""}
                  onClick={() => more("offerings")}
                />
              )}
            </section>
            <section aria-labelledby="cutoffs-title">
              <h2 id="cutoffs-title" tabIndex={-1}>
                Điểm chuẩn theo Offering
              </h2>
              <p className="notice">
                Điều kiện TTNV chỉ áp dụng khi điểm xét tuyển bằng điểm chuẩn;
                xem nguyên văn và phạm vi của từng dòng.
              </p>
              {data.cutoffs &&
                data.offerings &&
                data.cutoffs.dataset_version !==
                  data.offerings.dataset_version && (
                  <p role="alert" className="error">
                    Các phần dữ liệu thuộc phiên bản khác nhau. Tải lại để xem
                    phiên bản hiện hành.
                  </p>
                )}
              {data.cutoffs?.items.length === 0 ? (
                <Empty />
              ) : (
                <div
                  className="table-scroll"
                  role="region"
                  aria-label="Bảng điểm chuẩn, có thể cuộn ngang"
                  tabIndex={0}
                >
                  <table>
                    <caption>
                      Điểm và điều kiện được giữ theo nguồn · Năm {filters.year}
                    </caption>
                    <thead>
                      <tr>
                        <th scope="col">Offering / phương thức</th>
                        <th scope="col">Điểm chuẩn / thang</th>
                        <th scope="col">Cơ sở tính / điều kiện</th>
                        <th scope="col">Nguồn</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.cutoffs?.items.map((item) => (
                        <tr key={item.id}>
                          <th scope="row">
                            {item.offering_name}
                            <small>
                              {item.offering_code} ·{" "}
                              {item.campus ?? "Cơ sở chưa có dữ liệu"}
                            </small>
                            <small>
                              {item.method.name} ({item.method.code})
                            </small>
                          </th>
                          <td className="score">
                            {item.score} /{" "}
                            {item.max_score ?? item.scale.max_score ?? "—"}
                          </td>
                          <td>
                            <p>
                              {item.scope.condition_text ??
                                "Không có điều kiện văn bản"}
                            </p>
                            <details>
                              <summary>Thang điểm và điều kiện nguồn</summary>
                              <p>{item.scale.basis_description}</p>
                              <small>
                                Thang: {item.scale.code} ·{" "}
                                {item.scale.min_score}–{item.scale.max_score} ·
                                Phiên bản kỳ thi:{" "}
                                {item.scale.exam_version ?? "—"}
                              </small>
                              <small>
                                Basis: {item.basis_version ?? "—"} ·{" "}
                                {item.scope.aggregation_basis ?? "—"}
                              </small>
                              <pre>
                                {JSON.stringify(item.scope.conditions, null, 2)}
                              </pre>
                              <small>
                                Tổ hợp: {item.scope.combination_status} · Đợt:{" "}
                                {item.scope.round_key ?? "—"} · Đối tượng:{" "}
                                {item.scope.population_key ?? "—"}
                              </small>
                            </details>
                            {item.computation_status ===
                              "unavailable_aggregate_scope" && (
                              <p className="muted">
                                Phạm vi tổng hợp: không có phép tính đánh giá
                                riêng cho hồ sơ.
                              </p>
                            )}
                          </td>
                          <td>
                            <Sources sources={item.sources} />
                            <small>
                              Xác minh: {item.verification_status} · Bản sửa{" "}
                              {item.revision}
                            </small>
                            <small>
                              Công bố:{" "}
                              {item.source_published_at ?? "Chưa có ngày"}
                            </small>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {data.cutoffs && (
                <>
                  <MetadataNotice metadata={data.cutoffs} />
                  <More
                    envelope={data.cutoffs}
                    pending={paging !== ""}
                    onClick={() => more("cutoffs")}
                  />
                </>
              )}
            </section>
          </>
        )}
      </div>
    </>
  );
}

function message(error: unknown) {
  return error instanceof CatalogError
    ? error.message
    : "Không thể tải dữ liệu. Vui lòng thử lại.";
}
function Empty() {
  return (
    <div className="empty">
      <h3>Chưa có dữ liệu đã thu thập / xác minh phù hợp</h3>
      <p>
        Kết quả trống không có nghĩa trường không tuyển sinh. Thử thay đổi bộ
        lọc hoặc kiểm tra nguồn chính thức.
      </p>
    </div>
  );
}
function More({
  envelope,
  pending,
  onClick,
}: {
  envelope: ListEnvelope<unknown>;
  pending: boolean;
  onClick: () => void;
}) {
  return envelope.has_more ? (
    <button
      type="button"
      className="load-more"
      disabled={pending}
      onClick={onClick}
    >
      {pending ? "Đang tải…" : "Xem thêm"}
    </button>
  ) : null;
}
function MetadataNotice({ metadata }: { metadata: Metadata }) {
  return (
    <div className="metadata">
      <p>
        Phiên bản dữ liệu: <code>{metadata.dataset_version}</code>
        {metadata.release
          ? ` · Release ${metadata.release.version}`
          : " · Chưa gắn release cho phiên bản này"}
      </p>
      {metadata.warnings.map((warning, index) => (
        <p key={index}>{warning}</p>
      ))}
    </div>
  );
}
function Sources({ sources }: { sources: Source[] }) {
  const groups = new Map<string, Source[]>();
  for (const source of sources) {
    const key = source.url || source.snapshot_id;
    groups.set(key, [...(groups.get(key) ?? []), source]);
  }
  return (
    <div className="sources">
      <span>Nguồn: </span>
      {sources.length
        ? [...groups.entries()].map(([key, references]) => {
            const source = references[0];
            let safe = false;
            try {
              safe = ["http:", "https:"].includes(
                new URL(source.url ?? "").protocol,
              );
            } catch {}
            const label = source.title ?? "Tài liệu nguồn";
            return (
              <div key={key}>
                {safe ? (
                  <a href={source.url!} target="_blank" rel="noreferrer">
                    {label}
                    <span className="sr-only"> (mở tab mới)</span>
                  </a>
                ) : (
                  label
                )}
                {references.some((reference) => reference.locator) && (
                  <details>
                    <summary>Vị trí trong nguồn</summary>
                    {[
                      ...new Set(
                        references
                          .map((reference) => reference.locator)
                          .filter(Boolean),
                      ),
                    ].map((locator) => (
                      <p key={locator}>{locator}</p>
                    ))}
                  </details>
                )}
              </div>
            );
          })
        : "Chưa có liên kết công khai"}
    </div>
  );
}
