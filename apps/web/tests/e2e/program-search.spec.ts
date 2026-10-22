import { expect, test } from "@playwright/test";
import { list, offering, university } from "../fixtures";

test("program search: keyboard submit, draft/year context, two fictional schools and 360px layout", async ({
  page,
}, testInfo) => {
  const requests: URL[] = [];
  await page.route("**/api/catalog/programs?*", async (route) => {
    const url = new URL(route.request().url());
    requests.push(url);
    const year = Number(url.searchParams.get("year"));
    await route.fulfill({
      json: list([
        {
          ...offering,
          year,
          program_name: "Kế toán mẫu B",
          offering_name: "Kế toán thử nghiệm B",
          university_name: "Đại học Hư cấu B",
        },
        {
          ...offering,
          year,
          program_year_id: "other",
          university_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
          program_name: "Kế toán mẫu A",
          offering_name: "Kế toán thử nghiệm A",
          university_name: "Đại học Hư cấu A",
          campus: null,
        },
      ]),
    });
  });
  await page.goto("/universities?year=2024");
  await page
    .getByRole("navigation", { name: "Tra cứu tuyển sinh" })
    .getByRole("link", { name: "Ngành/chương trình" })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Tra cứu ngành/chương trình",
      exact: true,
    }),
  ).toBeVisible();
  expect(requests).toHaveLength(0);
  const searchForm = page.getByRole("search");
  const query = searchForm.getByLabel("Tên ngành/chương trình");
  await query.fill("ke toan");
  await query.press("Enter");
  await expect(page.getByRole("article")).toHaveCount(2);
  expect(requests[0].searchParams.get("query")).toBe("ke toan");
  expect(requests[0].searchParams.get("limit")).toBe("20");
  await expect(page.getByRole("article").getByRole("heading")).toHaveText([
    "Kế toán mẫu B",
    "Kế toán mẫu A",
  ]);
  await query.fill("draft chưa gửi");
  await expect(page.getByRole("status")).toContainText("ke toan");
  await searchForm.getByLabel("Năm tuyển sinh").selectOption("2025");
  await expect(
    page.getByRole("link", { name: "Đại học Hư cấu B", exact: true }),
  ).toHaveAttribute("href", `/universities/${university.id}?year=2025`);
  expect(requests).toHaveLength(2);
  expect(requests[1].searchParams.get("query")).toBe("ke toan");
  await page.setViewportSize({ width: 360, height: 780 });
  expect(
    await page
      .locator("body")
      .evaluate((el) => el.scrollWidth <= window.innerWidth),
  ).toBe(true);
  await page.screenshot({
    path: testInfo.outputPath("majors-360.png"),
    fullPage: true,
  });
  await query.fill("");
  await searchForm.getByLabel("Năm tuyển sinh").selectOption("2026");
  await expect(page.getByRole("article")).toHaveCount(0);
  expect(requests).toHaveLength(2);
});
