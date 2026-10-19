import { expect, test } from "@playwright/test";

test("SSR search → university → offering cutoff, source and equality conditions", async ({
  page,
  request,
}) => {
  const response = await request.get("/universities?year=2024");
  expect(await response.text()).toContain("Trường Tổng hợp Mẫu");
  await page.goto(
    "/universities?year=2024&method=THPT&campus=C%C6%A1+s%E1%BB%9F+1",
  );
  await page.getByRole("link", { name: /Trường Tổng hợp Mẫu/ }).click();
  await expect(page).toHaveURL(/year=2024.*method=THPT.*campus=/);
  await expect(
    page.getByRole("heading", { name: "Y khoa tiêu chuẩn", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Xem bảng điểm chuẩn", exact: true })
    .click();
  await expect(page).toHaveURL(/#cutoffs-title$/);
  await expect(
    page.getByRole("heading", {
      name: "Điểm chuẩn theo Offering",
      exact: true,
    }),
  ).toBeInViewport();
  await expect(
    page.getByText("Đang tải dữ liệu…", { exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("cell", { name: /^27\.50 \/ 30\.00/ }),
  ).toBeVisible();
  await expect(page.getByText("TTNV = 1", { exact: true })).toBeVisible();
  await expect(
    page.getByText("Tổng ba môn theo nguồn", { exact: true }),
  ).toBeHidden();
  await page
    .getByText("Thang điểm và điều kiện nguồn", { exact: true })
    .press("Enter");
  await expect(
    page.getByText("Tổng ba môn theo nguồn", { exact: true }),
  ).toBeVisible();
  await page
    .getByText("Thang điểm và điều kiện nguồn", { exact: true })
    .press("Enter");
  await expect(
    page.getByText(/TTNV chỉ áp dụng khi điểm xét tuyển bằng điểm chuẩn/),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: /Thông báo tuyển sinh mẫu/ }).first(),
  ).toHaveAttribute("href", "https://example.edu.vn/admissions");
  await expect(page.getByText(/Học phí.*chưa có dữ liệu/)).toBeVisible();
  expect(
    await page
      .locator("body")
      .evaluate((el) => el.scrollWidth <= window.innerWidth),
  ).toBe(true);
});

test("year URL, empty/error/retry and browser back keep current results", async ({
  page,
}) => {
  await page.goto("/universities?year=2024");
  await page.getByLabel("Năm tuyển sinh").selectOption("2026");
  await expect(page).toHaveURL(/year=2026/);
  await expect(page.getByText(/Chưa có dữ liệu đã thu thập/)).toBeVisible();
  await page.getByLabel("Năm tuyển sinh").selectOption("2024");
  await page.getByLabel("Tên hoặc mã trường").fill("error");
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "Không thể tải dữ liệu",
  );
  await page.getByLabel("Tên hoặc mã trường").fill("");
  await expect(
    page.getByRole("link", { name: /Trường Tổng hợp Mẫu/ }),
  ).toBeVisible();
  await page.getByLabel("Tên hoặc mã trường").fill("old");
  await expect(
    page.getByRole("link", { name: /Trường Tổng hợp Mẫu/ }),
  ).toHaveCount(0);
  await page.waitForTimeout(300);
  await page.getByLabel("Tên hoặc mã trường").fill("new");
  await expect(
    page.getByRole("link", { name: /Trường kết quả mới/ }),
  ).toBeVisible();
  await page.waitForTimeout(900);
  await expect(
    page.getByRole("link", { name: /Trường Tổng hợp Mẫu/ }),
  ).toHaveCount(0);
  await page.getByLabel("Tên hoặc mã trường").focus();
  await page.keyboard.press("Tab");
  await expect(page.getByLabel("Mã phương thức")).toBeFocused();
  await page.getByRole("link", { name: /Trường kết quả mới/ }).click();
  await expect(
    page.getByRole("heading", { name: "Trường Tổng hợp Mẫu", exact: true }),
  ).toBeVisible();
  await page.goBack();
  await expect(page.getByLabel("Tên hoặc mã trường")).toHaveValue("new");
  await expect(
    page.getByRole("link", { name: /Trường kết quả mới/ }),
  ).toBeVisible();
});

test("proxy rejects arbitrary destination paths", async ({ request }) => {
  expect((await request.get("/api/catalog/private?year=2024")).status()).toBe(
    404,
  );
  expect(
    (await request.get("/api/catalog/universities?year=2024")).status(),
  ).toBe(200);
});
