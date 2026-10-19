export interface Source {
  snapshot_id: string;
  source_id: string;
  title: string | null;
  url: string;
  locator: string | null;
  source_type: string;
}
export interface Coverage {
  year: number;
  canonical_cutoff_count: number;
  university_count: number;
  program_count: number;
  offering_count: number;
  disputed_cutoff_count: number;
  available_years: number[];
  missing_years: number[];
  tuition_status: "not_available_in_slice";
  scholarship_status: "not_available_in_slice";
  computation_unavailable_count: number;
}
export interface Metadata {
  dataset_version: number;
  coverage: Coverage;
  warnings: string[];
  release: { id: string; version: number } | null;
  contract_version: string;
}
export interface ListEnvelope<T> extends Metadata {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
}
export interface DetailEnvelope<T> extends Metadata {
  item: T;
}
export interface Method {
  id: string;
  code: string;
  name: string;
}
export interface University {
  id: string;
  name: string;
  code: string;
  slug: string;
  province: string | null;
  type: string | null;
  selected_year: number;
  data_status: string;
  program_count: number;
  offering_count: number;
  cutoff_count: number;
  updated_at: string;
  sources: Source[];
  methods?: Method[];
}
export interface Offering {
  program_id: string;
  program_name: string;
  program_year_id: string;
  offering_code: string;
  offering_name: string;
  year: number;
  university_id: string;
  university_name: string;
  campus: string | null;
  track: string | null;
  language: string | null;
  major_id: string | null;
  major_name: string | null;
  method_codes: string[];
  cutoff_count: number;
  tuition: null;
  scholarships: null;
  sources: Source[];
}
export interface Cutoff {
  id: string;
  program_id: string;
  program_year_id: string;
  university_id: string;
  program_name: string;
  offering_code: string;
  offering_name: string;
  campus: string | null;
  year: number;
  method: Method;
  score: string;
  max_score: string;
  scale: {
    id: string;
    code: string;
    exam_version: string | null;
    min_score: string;
    max_score: string;
    basis_description: string;
  };
  basis_version: string | null;
  scope: {
    id: string;
    combination_id: string | null;
    combination_status: string | null;
    round_key: string;
    population_key: string;
    condition_text: string;
    conditions: Record<string, unknown> | null;
    aggregation_basis: string | null;
  };
  revision: number;
  verification_status: string;
  computation_status: string;
  sources: Source[];
  source_published_at: string | null;
  effective_from: string | null;
  updated_at: string;
}
export interface Filters {
  year: string;
  query: string;
  method: string;
  campus: string;
}
export interface CatalogData {
  universities?: ListEnvelope<University>;
  university?: DetailEnvelope<University>;
  offerings?: ListEnvelope<Offering>;
  cutoffs?: ListEnvelope<Cutoff>;
}
