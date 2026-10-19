import type { Filters } from "./contracts";

export function filtersFrom(params: URLSearchParams): Filters {
  return {
    year: params.get("year") ?? "2024",
    query: params.get("query") ?? "",
    method: params.get("method") ?? "",
    campus: params.get("campus") ?? "",
  };
}
export function filterQuery(filters: Filters): string {
  const params = new URLSearchParams({ year: filters.year });
  for (const key of ["query", "method", "campus"] as const) {
    if (filters[key]) params.set(key, filters[key]);
  }
  return params.toString();
}
