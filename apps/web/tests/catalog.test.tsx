import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { Catalog } from "../components/catalog";
import { university, list, source } from "./fixtures";

afterEach(() => vi.unstubAllGlobals());

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
