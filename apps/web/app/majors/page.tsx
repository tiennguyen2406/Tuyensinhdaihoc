import { ProgramSearch } from "../../components/program-search";
import { filtersFrom } from "../../lib/filters";

export default async function Majors({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const filters = filtersFrom(
    new URLSearchParams(
      typeof params.year === "string" ? { year: params.year } : {},
    ),
  );
  return <ProgramSearch key={filters.year} initialYear={filters.year} />;
}
