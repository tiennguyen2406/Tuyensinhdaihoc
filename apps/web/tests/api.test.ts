import { afterEach, expect, test, vi } from "vitest";
import { CatalogError, loadCatalog } from "../lib/api";
import { list, university } from "./fixtures";

afterEach(() => vi.unstubAllGlobals());

test("publication between detail requests rejects the whole screen instead of mixing versions", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) =>
      Response.json(
        url.includes(`/universities/${university.id}`)
          ? { ...list([]), item: university }
          : { ...list([]), dataset_version: 1043 },
      ),
    ),
  );
  await expect(
    loadCatalog(
      "/api/catalog",
      { year: "2024", query: "", method: "", campus: "" },
      university.id,
    ),
  ).rejects.toMatchObject({ status: 409 });
});

test("detail filters reach offerings and cutoffs without unsupported summary or cutoff query params", async () => {
  const requests: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      requests.push(url);
      return Response.json(
        url.includes(`/universities/${university.id}`)
          ? { ...list([]), item: university }
          : list([]),
      );
    }),
  );
  await loadCatalog(
    "/api/catalog",
    { year: "2025", query: "Y", method: "THPT", campus: "CS1" },
    university.id,
  );
  expect(requests).toEqual([
    `/api/catalog/universities/${university.id}?year=2025`,
    `/api/catalog/programs?year=2025&query=Y&method=THPT&campus=CS1&university_id=${university.id}`,
    `/api/catalog/cutoffs?year=2025&method=THPT&campus=CS1&university_id=${university.id}`,
  ]);
});

test("a dataset conflict is surfaced for restart instead of returning old results", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      Response.json({ detail: { code: "DATASET_CHANGED" } }, { status: 409 }),
    ),
  );
  await expect(
    loadCatalog("/api/catalog", {
      year: "2024",
      query: "",
      method: "",
      campus: "",
    }),
  ).rejects.toMatchObject({ status: 409 });
  expect(new CatalogError(409).message).toContain("trang đầu");
});
