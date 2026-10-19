import { expect, test } from "vitest";
import { filtersFrom, filterQuery } from "../lib/filters";

test("defaults only missing year and preserves supported URL filters", () => {
  expect(
    filtersFrom(new URLSearchParams("query=Y&method=THPT&campus=North")),
  ).toEqual({
    year: "2024",
    query: "Y",
    method: "THPT",
    campus: "North",
  });
  expect(
    filterQuery({
      year: "2026",
      query: "Y khoa",
      method: "THPT",
      campus: "Cơ sở 2",
    }),
  ).toBe("year=2026&query=Y+khoa&method=THPT&campus=C%C6%A1+s%E1%BB%9F+2");
});

test("does not silently replace an unsupported year with another year's data", () => {
  expect(filtersFrom(new URLSearchParams("year=2023")).year).toBe("2023");
});
