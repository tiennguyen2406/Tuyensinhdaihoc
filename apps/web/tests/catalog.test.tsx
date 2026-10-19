import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { Catalog } from "../components/catalog";
import { university, list, source, cutoff, offering } from "./fixtures";

afterEach(() => vi.unstubAllGlobals());

test("partial year remains partial in the list despite verified cutoff facts", () => {
  render(
    <Catalog
      initial={{
        universities: list([{ ...university, data_status: "partial" }]),
      }}
      initialFilters={{ year: "2024", query: "", method: "", campus: "" }}
    />,
  );
  const card = screen.getByRole("article");
  expect(
    within(card).getByText(/Trạng thái năm: Đã thu thập một phần/),
  ).toBeVisible();
  expect(
    within(card).getByText("Mốc điểm").nextElementSibling,
  ).toHaveTextContent("1");
  expect(
    within(card).queryByText(/Trạng thái năm: Đã xác minh/),
  ).not.toBeInTheDocument();
});

test("detail separates partial year from its verified cutoff and preserves exact score and TTNV", () => {
  render(
    <Catalog
      universityId={university.id}
      initial={{
        university: {
          ...list([]),
          item: { ...university, data_status: "partial" },
        },
        offerings: list([offering]),
        cutoffs: list([cutoff]),
      }}
      initialFilters={{ year: "2024", query: "", method: "", campus: "" }}
    />,
  );
  expect(
    within(screen.getByRole("region", { name: "Thông tin trường" })).getByText(
      /Trạng thái năm: Đã thu thập một phần/,
    ),
  ).toBeVisible();
  expect(screen.getByText(/Xác minh: verified/)).toBeVisible();
  expect(screen.getByRole("cell", { name: "27.50 / 30.00" })).toBeVisible();
  expect(screen.getByText("TTNV = 1")).toBeVisible();
});

test.each([
  ["unknown", "Chưa xác định"],
  ["partial", "Đã thu thập một phần"],
  ["published", "Đã công bố"],
  ["verified", "Đã xác minh"],
  ["not_collected", "Chưa thu thập năm này"],
] as const)(
  "year status %s comes from the year row even without cutoff facts",
  (data_status, label) => {
    render(
      <Catalog
        initial={{
          universities: list([{ ...university, data_status, cutoff_count: 0 }]),
        }}
        initialFilters={{ year: "2024", query: "", method: "", campus: "" }}
      />,
    );
    const card = screen.getByRole("article");
    expect(within(card).getByText(`Trạng thái năm: ${label}`)).toBeVisible();
    if (data_status === "verified")
      expect(
        within(card).getByText(/không khẳng định đã thu thập đầy đủ/),
      ).toBeVisible();
  },
);

test("coverage reports candidate year statuses independently of zero filtered cutoff facts", () => {
  const data = list<typeof university>([]);
  data.coverage.admission_year_status_counts = {
    unknown: 2,
    partial: 3,
    published: 1,
    verified: 4,
    not_collected: 5,
  };
  render(
    <Catalog
      initial={{ universities: data }}
      initialFilters={{ year: "2024", query: "", method: "THPT", campus: "" }}
    />,
  );
  const coverage = screen.getByRole("group", {
    name: "Trạng thái năm của các trường trong phạm vi tra cứu",
  });
  for (const label of [
    "Chưa xác định: 2",
    "Đã thu thập một phần: 3",
    "Đã công bố: 1",
    "Đã xác minh: 4",
    "Chưa thu thập năm này: 5",
  ])
    expect(within(coverage).getByText(label)).toBeVisible();
  expect(
    within(coverage).getByText(
      /Độc lập với bộ lọc phương thức, cơ sở và số mốc điểm chuẩn/,
    ),
  ).toBeVisible();
  expect(
    screen.getByText(/0 mốc điểm chuẩn trong phạm vi dữ liệu/),
  ).toBeVisible();
});

test("hash-only navigation keeps current results instead of triggering a filter reload", () => {
  window.history.replaceState(null, "", "/universities?year=2024");
  render(
    <Catalog
      initial={{ universities: list([university]) }}
      initialFilters={{ year: "2024", query: "", method: "", campus: "" }}
    />,
  );
  act(() => {
    window.history.replaceState(
      null,
      "",
      "/universities?year=2024#cutoffs-title",
    );
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  expect(
    screen.getByRole("link", { name: /Trường Tổng hợp Mẫu/ }),
  ).toBeVisible();
  expect(screen.queryByText("Đang tải dữ liệu…")).not.toBeInTheDocument();
});

test("source links are deduplicated with long locators collapsed and release UUID omitted", () => {
  const data = list([
    {
      ...university,
      sources: [
        { ...source, locator: "LONG CSS LOCATOR" },
        { ...source, locator: "SECOND LOCATOR" },
      ],
    },
  ]);
  data.release = { id: "release-private-identity", version: 3 };
  render(
    <Catalog
      initial={{ universities: data }}
      initialFilters={{ year: "2024", query: "", method: "", campus: "" }}
    />,
  );
  expect(
    screen.getAllByRole("link", { name: /Thông báo tuyển sinh mẫu/ }),
  ).toHaveLength(1);
  expect(screen.getByText("LONG CSS LOCATOR")).not.toBeVisible();
  expect(
    screen.queryByText(/release-private-identity/),
  ).not.toBeInTheDocument();
  fireEvent.click(screen.getByText("Vị trí trong nguồn"));
  expect(screen.getByText("LONG CSS LOCATOR")).toBeVisible();
  expect(screen.getByText("SECOND LOCATOR")).toBeVisible();
});

test("pagination appends current results but rejects a different dataset version", async () => {
  const initial = {
    ...list([university]),
    next_cursor: "page-2",
    has_more: true,
  };
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValueOnce(
        Response.json({
          ...list([{ ...university, id: "second", name: "Trường thứ hai" }]),
          next_cursor: "page-3",
          has_more: true,
        }),
      )
      .mockResolvedValueOnce(
        Response.json({
          ...list([
            { ...university, id: "third", name: "Trường phiên bản khác" },
          ]),
          dataset_version: 1043,
        }),
      ),
  );
  render(
    <Catalog
      initial={{ universities: initial }}
      initialFilters={{ year: "2024", query: "", method: "", campus: "" }}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "Xem thêm" }));
  expect(
    await screen.findByRole("link", { name: /Trường thứ hai/ }),
  ).toBeVisible();
  expect(
    screen.getByRole("link", { name: /Trường Tổng hợp Mẫu/ }),
  ).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Xem thêm" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("trang đầu");
  expect(
    screen.queryByRole("link", { name: /Trường phiên bản khác/ }),
  ).not.toBeInTheDocument();
});

test("clears previous results immediately and ignores an old response even when abort is ignored", async () => {
  const pending: Array<{
    resolve: (value: Response) => void;
    signal?: AbortSignal | null;
  }> = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(
      (_url: string, init?: RequestInit) =>
        new Promise<Response>((resolve) =>
          pending.push({ resolve, signal: init?.signal }),
        ),
    ),
  );
  render(
    <Catalog
      initial={{ universities: list([university]) }}
      initialFilters={{ year: "2024", query: "", method: "", campus: "" }}
    />,
  );
  expect(
    screen.getByRole("link", { name: /Trường Tổng hợp Mẫu/ }),
  ).toBeVisible();
  fireEvent.change(screen.getByLabelText("Tên hoặc mã trường"), {
    target: { value: "old" },
  });
  expect(
    screen.queryByRole("link", { name: /Trường Tổng hợp Mẫu/ }),
  ).not.toBeInTheDocument();
  await waitFor(() => expect(pending).toHaveLength(1));
  fireEvent.change(screen.getByLabelText("Tên hoặc mã trường"), {
    target: { value: "new" },
  });
  await waitFor(() => expect(pending).toHaveLength(2));
  expect(pending[0].signal?.aborted).toBe(true);
  await act(async () =>
    pending[1].resolve(
      Response.json(list([{ ...university, name: "Kết quả mới" }])),
    ),
  );
  expect(
    await screen.findByRole("link", { name: /Kết quả mới/ }),
  ).toBeVisible();
  await act(async () =>
    pending[0].resolve(
      Response.json(list([{ ...university, name: "Kết quả cũ" }])),
    ),
  );
  expect(
    screen.queryByRole("link", { name: /Kết quả cũ/ }),
  ).not.toBeInTheDocument();
  expect(window.location.search).toContain("query=new");
});

test("shows unavailable year as uncollected data and recovers from a request error", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValueOnce(
        Response.json({ detail: "error" }, { status: 503 }),
      )
      .mockResolvedValueOnce(Response.json(list([]))),
  );
  render(
    <Catalog
      initial={{ universities: list([university]) }}
      initialFilters={{ year: "2024", query: "", method: "", campus: "" }}
    />,
  );
  fireEvent.change(screen.getByLabelText("Năm tuyển sinh"), {
    target: { value: "2026" },
  });
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Không thể tải dữ liệu",
  );
  fireEvent.click(screen.getByRole("button", { name: "Thử lại" }));
  expect(await screen.findByText(/Chưa có dữ liệu đã thu thập/)).toBeVisible();
  expect(
    screen.getByText(/không có nghĩa trường không tuyển sinh/),
  ).toBeVisible();
});
