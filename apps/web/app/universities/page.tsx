import { Catalog } from "../../components/catalog";
import { filtersFrom } from "../../lib/filters";
import { loadServerCatalog } from "../../lib/server-api";
import { CatalogError } from "../../lib/api";
import type { CatalogData } from "../../lib/contracts";

export const dynamic = "force-dynamic";
export default async function Universities({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const filters = filtersFrom(
    new URLSearchParams(
      Object.entries(params).flatMap(([key, value]) =>
        typeof value === "string" ? [[key, value]] : [],
      ),
    ),
  );
  let initial: CatalogData | null = null;
  let initialError = "";
  try {
    initial = await loadServerCatalog(filters);
  } catch (error) {
    initialError =
      error instanceof CatalogError
        ? error.message
        : "Không thể tải dữ liệu. Vui lòng thử lại.";
  }
  return (
    <Catalog
      key={JSON.stringify(filters)}
      initial={initial}
      initialFilters={filters}
      initialError={initialError}
    />
  );
}
