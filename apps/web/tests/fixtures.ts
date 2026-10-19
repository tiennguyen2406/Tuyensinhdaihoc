import type { ListEnvelope, University } from "../lib/contracts";

export const source = {
  snapshot_id: "11111111-1111-4111-8111-111111111111",
  source_id: "22222222-2222-4222-8222-222222222222",
  title: "Thông báo tuyển sinh mẫu",
  url: "https://example.edu.vn/admissions",
  locator: "Trang 2",
  source_type: "official",
};
export const university: University = {
  id: "33333333-3333-4333-8333-333333333333",
  name: "Trường Tổng hợp Mẫu",
  code: "MAU",
  slug: "truong-mau",
  province: null,
  type: null,
  selected_year: 2024,
  data_status: "verified",
  program_count: 1,
  offering_count: 1,
  cutoff_count: 1,
  updated_at: "2024-08-21T00:00:00Z",
  sources: [source],
};
export function list<T>(items: T[]): ListEnvelope<T> {
  return {
    items,
    next_cursor: null,
    has_more: false,
    dataset_version: 1042,
    contract_version: "catalog/1",
    release: null,
    warnings: ["Dữ liệu nội bộ chưa đầy đủ."],
    coverage: {
      year: 2024,
      canonical_cutoff_count: items.length,
      university_count: items.length,
      program_count: items.length,
      offering_count: items.length,
      disputed_cutoff_count: 0,
      available_years: [2024],
      missing_years: [2025, 2026],
      tuition_status: "not_available_in_slice",
      scholarship_status: "not_available_in_slice",
      computation_unavailable_count: 0,
    },
  };
}
