// Synthetic HTTP responses for isolated browser tests. No database connection.
import { createServer } from "node:http";
import { list, source, university } from "./fixtures.ts";

const offering = {
  program_id: "44444444-4444-4444-8444-444444444444",
  program_name: "Y khoa",
  program_year_id: "55555555-5555-4555-8555-555555555555",
  offering_code: "YK24",
  offering_name: "Y khoa tiêu chuẩn",
  year: 2024,
  university_id: university.id,
  university_name: university.name,
  campus: "Cơ sở 1",
  track: null,
  language: "Tiếng Việt",
  major_id: null,
  major_name: null,
  method_codes: ["THPT"],
  cutoff_count: 1,
  tuition: null,
  scholarships: null,
  sources: [source],
};
const cutoff = {
  id: "66666666-6666-4666-8666-666666666666",
  program_id: offering.program_id,
  program_year_id: offering.program_year_id,
  university_id: university.id,
  program_name: offering.program_name,
  offering_code: offering.offering_code,
  offering_name: offering.offering_name,
  campus: offering.campus,
  year: 2024,
  method: {
    id: "77777777-7777-4777-8777-777777777777",
    code: "THPT",
    name: "Thi tốt nghiệp THPT",
  },
  score: "27.50",
  max_score: "30.00",
  scale: {
    id: "88888888-8888-4888-8888-888888888888",
    code: "THPT30",
    exam_version: "2024",
    min_score: "0",
    max_score: "30",
    basis_description: "Tổng ba môn theo nguồn",
  },
  basis_version: "2024-v1",
  scope: {
    id: "99999999-9999-4999-8999-999999999999",
    combination_id: null,
    combination_status: "aggregate",
    round_key: "1",
    population_key: "all",
    condition_text: "TTNV = 1",
    conditions: { op: "eq", field: "TTNV", value: 1 },
    aggregation_basis: "all_combinations",
  },
  revision: 1,
  verification_status: "verified",
  computation_status: "unavailable_aggregate_scope",
  sources: [source],
  source_published_at: "2024-08-20T00:00:00Z",
  effective_from: null,
  updated_at: "2024-08-21T00:00:00Z",
};
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
  const empty = year !== 2024 || query === "none";
  const envelope = list([]);
  envelope.coverage.year = year;
  envelope.coverage.canonical_cutoff_count = empty ? 0 : 1;
  envelope.coverage.university_count = empty ? 0 : 1;
  envelope.coverage.program_count = empty ? 0 : 1;
  envelope.coverage.offering_count = empty ? 0 : 1;
  let payload;
  if (url.pathname === "/api/v1/universities")
    payload = {
      ...envelope,
      items: empty
        ? []
        : [
            {
              ...university,
              name: query === "new" ? "Trường kết quả mới" : university.name,
            },
          ],
    };
  else if (url.pathname === `/api/v1/universities/${university.id}`)
    payload = {
      ...envelope,
      item: { ...university, methods: [cutoff.method], selected_year: year },
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
