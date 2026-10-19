// Synthetic HTTP responses for isolated browser tests. No database connection.
import { createServer } from "node:http";
import { cutoff, list, offering, university } from "./fixtures.ts";

createServer(async (req, res) => {
  const url = new URL(req.url, "http://127.0.0.1:3801");
  const year = Number(url.searchParams.get("year") || 2024);
  const query = url.searchParams.get("query");
  res.setHeader("Content-Type", "application/json");
  if (url.pathname === "/health") return res.end('{"status":"ok"}');
  if (query === "error") {
    res.statusCode = 503;
    return res.end('{"detail":"Synthetic unavailable"}');
  }
  if (query === "old") await new Promise((resolve) => setTimeout(resolve, 800));
  const candidate = query !== "none";
  const empty = year !== 2024 || !candidate;
  const dataStatus =
    year === 2024 ? "partial" : year === 2025 ? "unknown" : "not_collected";
  const yearUniversity = {
    ...university,
    selected_year: year,
    data_status: dataStatus,
    program_count: empty ? 0 : 1,
    offering_count: empty ? 0 : 1,
    cutoff_count: empty ? 0 : 1,
  };
  const envelope = list([]);
  envelope.coverage.year = year;
  envelope.coverage.canonical_cutoff_count = empty ? 0 : 1;
  envelope.coverage.university_count = empty ? 0 : 1;
  envelope.coverage.program_count = empty ? 0 : 1;
  envelope.coverage.offering_count = empty ? 0 : 1;
  envelope.coverage.admission_year_status_counts[dataStatus] = candidate
    ? 1
    : 0;
  let payload;
  if (url.pathname === "/api/v1/universities")
    payload = {
      ...envelope,
      items:
        !candidate ||
        (empty &&
          (url.searchParams.has("method") || url.searchParams.has("campus")))
          ? []
          : [
              {
                ...yearUniversity,
                name: query === "new" ? "Trường kết quả mới" : university.name,
              },
            ],
    };
  else if (url.pathname === `/api/v1/universities/${university.id}`)
    payload = {
      ...envelope,
      item: { ...yearUniversity, methods: empty ? [] : [cutoff.method] },
    };
  else if (url.pathname === "/api/v1/programs")
    payload = { ...envelope, items: empty ? [] : [offering] };
  else if (url.pathname === "/api/v1/cutoffs")
    payload = { ...envelope, items: empty ? [] : [cutoff] };
  else {
    res.statusCode = 404;
    payload = { detail: "not found" };
  }
  res.end(JSON.stringify(payload));
}).listen(3801, "127.0.0.1");
