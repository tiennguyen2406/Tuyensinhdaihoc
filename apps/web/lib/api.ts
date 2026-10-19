import type { CatalogData, Filters } from "./contracts";
import { filterQuery } from "./filters";

export class CatalogError extends Error {
  constructor(public status: number) {
    super(
      status === 409
        ? "Dữ liệu đã thay đổi. Hãy tải lại từ trang đầu."
        : status === 404
          ? "Không tìm thấy trường trong dữ liệu năm đã chọn."
          : status === 422
            ? "Bộ lọc không hợp lệ. Chọn năm 2024–2026 và kiểm tra mã phương thức."
            : "Không thể tải dữ liệu. Vui lòng thử lại.",
    );
  }
}

export async function fetchJson<T>(
  url: string,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(url, { cache: "no-store", signal });
  if (!response.ok) throw new CatalogError(response.status);
  return response.json() as Promise<T>;
}

export async function loadCatalog(
  root: string,
  filters: Filters,
  universityId?: string,
  signal?: AbortSignal,
): Promise<CatalogData> {
  const params = new URLSearchParams(filterQuery(filters));
  if (!universityId)
    return {
      universities: await fetchJson(`${root}/universities?${params}`, signal),
    };
  const detailParams = new URLSearchParams({ year: filters.year });
  params.set("university_id", universityId);
  const cutoffParams = new URLSearchParams(params);
  cutoffParams.delete("query");
  const [university, offerings, cutoffs] = await Promise.all([
    fetchJson<NonNullable<CatalogData["university"]>>(
      `${root}/universities/${encodeURIComponent(universityId)}?${detailParams}`,
      signal,
    ),
    fetchJson<NonNullable<CatalogData["offerings"]>>(
      `${root}/programs?${params}`,
      signal,
    ),
    fetchJson<NonNullable<CatalogData["cutoffs"]>>(
      `${root}/cutoffs?${cutoffParams}`,
      signal,
    ),
  ]);
  if (
    university.dataset_version !== offerings.dataset_version ||
    university.dataset_version !== cutoffs.dataset_version
  ) {
    throw new CatalogError(409);
  }
  return { university, offerings, cutoffs };
}
