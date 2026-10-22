"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { CatalogError, fetchJson } from "../lib/api";
import type { ListEnvelope, Offering } from "../lib/contracts";
import { MetadataNotice } from "./catalog";
import { YearSelector } from "./year-selector";

type Context = { year: string; query: string };
type Results = ListEnvelope<Offering>;

export function ProgramSearch({ initialYear }: { initialYear: string }) {
  const [year, setYear] = useState(initialYear);
  const [draft, setDraft] = useState("");
  const [submitted, setSubmitted] = useState<string | null>(null);
  const [validation, setValidation] = useState("");
  const [notice, setNotice] = useState("");
  const [state, setState] = useState<{
    data: Results | null;
    pending: boolean;
    error: string;
  }>({ data: null, pending: false, error: "" });
  const generation = useRef(0);
  const controller = useRef<AbortController | null>(null);

  function invalidate() {
    generation.current += 1;
    controller.current?.abort();
  }

  useEffect(
    () => () => {
      generation.current += 1;
      controller.current?.abort();
    },
    [],
  );

  async function search(
    context: Context,
    previous?: Results,
    canRestart = true,
  ): Promise<void> {
    invalidate();
    const identity = generation.current;
    const request = new AbortController();
    controller.current = request;
    setState({ data: previous ?? null, pending: true, error: "" });
    const params = new URLSearchParams({ ...context, limit: "20" });
    if (previous?.next_cursor) params.set("cursor", previous.next_cursor);
    try {
      const next = await fetchJson<Results>(
        `/api/catalog/programs?${params}`,
        request.signal,
      );
      if (identity !== generation.current || request.signal.aborted) return;
      if (previous && previous.dataset_version !== next.dataset_version)
        throw new CatalogError(409);
      setState({
        data: {
          ...next,
          items: previous ? [...previous.items, ...next.items] : next.items,
        },
        pending: false,
        error: "",
      });
    } catch (error) {
      if (identity !== generation.current || request.signal.aborted) return;
      if (error instanceof CatalogError && error.status === 409 && canRestart) {
        setNotice("Dữ liệu đã thay đổi. Kết quả được tải lại từ trang đầu.");
        return search(context, undefined, false);
      }
      setState({
        data: null,
        pending: false,
        error:
          error instanceof CatalogError
            ? error.message
            : "Không thể tải dữ liệu. Vui lòng thử lại.",
      });
    }
  }

  function reset() {
    invalidate();
    setSubmitted(null);
    setValidation("");
    setNotice("");
    setState({ data: null, pending: false, error: "" });
  }

  function changeYear(next: string) {
    if (next === year) return;
    invalidate();
    setYear(next);
    setNotice("");
    setState({ data: null, pending: false, error: "" });
    if (submitted !== null) void search({ year: next, query: submitted });
  }

  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">TRA CỨU THEO TÊN · NỘI BỘ DEV</p>
        <h1>Tra cứu ngành/chương trình</h1>
        <p>
          Tìm chương trình theo tên xuyên các trường trong dữ liệu đã công bố.
          Tên giống nhau không xác lập một Major chuẩn dùng chung.
        </p>
      </div>
      <form
        className="filters"
        role="search"
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          if (draft.trim().length < 2 || draft.length > 120) {
            setValidation(
              "Nhập từ 2 đến 120 ký tự; không tính khoảng trắng đầu/cuối cho độ dài tối thiểu.",
            );
            return;
          }
          setValidation("");
          setNotice("");
          setSubmitted(draft);
          void search({ year, query: draft });
        }}
      >
        <YearSelector value={year} onChange={changeYear} />
        <label>
          Tên ngành/chương trình
          <input
            type="search"
            maxLength={120}
            autoComplete="off"
            value={draft}
            aria-invalid={!!validation}
            aria-describedby="program-query-help"
            onChange={(event) => {
              setDraft(event.target.value);
              setValidation("");
              if (event.target.value === "") reset();
            }}
            placeholder="Ví dụ: ke toan"
          />
        </label>
        <button type="submit">Tìm kiếm</button>
      </form>
      <p id="program-query-help" className="muted">
        Nhập ít nhất 2 ký tự, tối đa 120; bấm Tìm kiếm hoặc Enter. Gõ thêm chưa
        thay đổi truy vấn đã gửi.
      </p>
      {validation && (
        <p role="alert" className="error">
          {validation}
        </p>
      )}
      <aside className="notice">
        Chỉ hiển thị Offering có mốc điểm chuẩn trong catalog hiện tại. Không có
        kết quả không có nghĩa trường không tuyển sinh; chưa bao phủ toàn bộ
        chương trình.
      </aside>
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="status"
      >
        {submitted !== null && (
          <>
            Năm {year} · Truy vấn đã gửi: “{submitted}”
            {state.pending
              ? " · Đang tải dữ liệu…"
              : state.data
                ? ` · ${state.data.items.length} kết quả đã tải`
                : ""}
          </>
        )}
      </div>
      {notice && <p className="notice">{notice}</p>}
      {state.error && (
        <div role="alert" className="error">
          <p>{state.error}</p>
          <button
            type="button"
            onClick={() => {
              if (submitted !== null) void search({ year, query: submitted });
            }}
          >
            Thử lại
          </button>
        </div>
      )}
      <div aria-busy={state.pending}>
        {state.data && (
          <>
            <MetadataNotice metadata={state.data} />
            {state.data.items.length === 0 ? (
              <p className="empty">
                Chưa có dữ liệu khớp truy vấn đã gửi trong năm {year}. Dữ liệu
                còn thiếu; không có nghĩa trường không tuyển sinh.
              </p>
            ) : (
              <section
                aria-label="Kết quả ngành/chương trình"
                className="offering-grid program-results"
              >
                {state.data.items.map((item, index) => (
                  <article
                    className="offering-card"
                    key={`${item.program_year_id}:${index}`}
                  >
                    <Link
                      prefetch={false}
                      href={`/universities/${encodeURIComponent(item.university_id)}?year=${year}`}
                    >
                      {item.university_name}
                    </Link>
                    <h2>{item.program_name}</h2>
                    <dl>
                      <div>
                        <dt>Offering</dt>
                        <dd>
                          {item.offering_name} · {item.offering_code}
                        </dd>
                      </div>
                      <div>
                        <dt>Năm</dt>
                        <dd>{item.year}</dd>
                      </div>
                      <div>
                        <dt>Cơ sở</dt>
                        <dd>{item.campus ?? "Chưa có dữ liệu"}</dd>
                      </div>
                      <div>
                        <dt>Mã phương thức</dt>
                        <dd>
                          {item.method_codes.length
                            ? item.method_codes.join(", ")
                            : "Chưa có dữ liệu"}
                        </dd>
                      </div>
                      <div>
                        <dt>Số mốc điểm chuẩn</dt>
                        <dd>{item.cutoff_count}</dd>
                      </div>
                    </dl>
                  </article>
                ))}
              </section>
            )}
            {state.data.has_more && state.data.next_cursor && (
              <button
                className="load-more"
                type="button"
                disabled={state.pending}
                onClick={() => {
                  if (submitted !== null && state.data)
                    void search({ year, query: submitted }, state.data);
                }}
              >
                Xem thêm
              </button>
            )}
          </>
        )}
      </div>
    </>
  );
}
