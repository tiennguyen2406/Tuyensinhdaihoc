import { Catalog } from "../../../components/catalog";
import { filtersFrom } from "../../../lib/filters";
import { loadServerCatalog } from "../../../lib/server-api";
import { CatalogError } from "../../../lib/api";
import type { CatalogData } from "../../../lib/contracts";

export const dynamic = "force-dynamic";
export default async function UniversityDetail({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const [{ id }, query] = await Promise.all([params, searchParams]);
  const filters = filtersFrom(
    new URLSearchParams(
      Object.entries(query).flatMap(([key, value]) =>
        typeof value === "string" ? [[key, value]] : [],
      ),
    ),
  );
  let initial: CatalogData | null = null;
  let initialError = "";
  try {
    initial = await loadServerCatalog(filters, id);
  } catch (error) {
    initialError =
      error instanceof CatalogError
        ? error.message
        : "Không thể tải dữ liệu. Vui lòng thử lại.";
  }
  return (
    <Catalog
      key={`${id}-${JSON.stringify(filters)}`}
      initial={initial}
      initialFilters={filters}
      universityId={id}
      initialError={initialError}
    />
  );
}
