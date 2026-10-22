import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";
import { ProgramSearch } from "../components/program-search";
import { list, offering } from "./fixtures";

const first = {
  ...offering,
  program_name: "Kế toán mẫu B",
  offering_name: "Chương trình B",
  university_name: "Đại học Hư cấu B",
};
const second = {
  ...offering,
  program_year_id: "other",
  university_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  program_name: "Kế toán mẫu A",
  offering_name: "Chương trình A",
  university_name: "Đại học Hư cấu A",
  campus: null,
  method_codes: ["THPT", "TEST"],
};
afterEach(() => vi.unstubAllGlobals());
function input(value: string) {
  fireEvent.change(screen.getByLabelText("Tên ngành/chương trình"), {
    target: { value },
  });
}
function submit(value: string) {
  input(value);
  fireEvent.click(screen.getByRole("button", { name: "Tìm kiếm" }));
}
function year(value: string) {
  fireEvent.change(screen.getByLabelText("Năm tuyển sinh"), {
    target: { value },
  });
}
function requests() {
  return vi
    .mocked(fetch)
    .mock.calls.map(
      ([url]) => new URL(String(url), "http://localhost").searchParams,
    );
}
function ready(items = [first, second]) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async () => Response.json(list(items))),
  );
  render(<ProgramSearch initialYear="2024" />);
}

test("initial guidance uses existing default year and year changes without a submitted query never search", () => {
  ready();
  expect(screen.getByLabelText("Năm tuyển sinh")).toHaveValue("2024");
  expect(screen.getByText(/Nhập ít nhất 2 ký tự/)).toBeVisible();
  year("2026");
  expect(fetch).not.toHaveBeenCalled();
  expect(screen.queryByText(/Chưa có dữ liệu khớp/)).not.toBeInTheDocument();
});

test("button sends unchanged ke toan with limit20, renders two fictional universities and preserves year in detail links", async () => {
  ready();
  submit("ke toan");
  await screen.findByText(first.program_name);
  expect(requests()[0].get("query")).toBe("ke toan");
  expect(requests()[0].get("limit")).toBe("20");
  expect(requests()[0].get("year")).toBe("2024");
  expect(fetch).toHaveBeenCalledTimes(1);
  for (const item of [first, second]) {
    expect(
      screen.getByRole("link", { name: item.university_name }),
    ).toHaveAttribute("href", `/universities/${item.university_id}?year=2024`);
    expect(
      screen.getByText(item.offering_name, { exact: false }),
    ).toBeVisible();
  }
  expect(screen.getByText("THPT, TEST")).toBeVisible();
  expect(screen.getByText(/không xác lập.*Major/)).toBeVisible();
});

test.each(["  kế Toán  ", "x".repeat(120)])(
  "Enter preserves original valid query %s without client normalization",
  async (query) => {
    ready();
    const user = userEvent.setup();
    await user.type(
      screen.getByLabelText("Tên ngành/chương trình"),
      query + "{Enter}",
    );
    await screen.findByText(first.program_name);
    expect(requests()[0].get("query")).toBe(query);
    expect(fetch).toHaveBeenCalledTimes(1);
  },
);

test.each(["a", "  a  ", "   ", "x".repeat(121)])(
  "invalid query %s is rejected without an API request",
  (query) => {
    ready();
    submit(query);
    expect(screen.getByRole("alert")).toHaveTextContent(/2.*120/);
    expect(fetch).not.toHaveBeenCalled();
  },
);

test("typing changes only draft; each year change re-searches submitted text once, ignoring draft", async () => {
  ready();
  submit("ke toan");
  await screen.findByText(first.program_name);
  input("draft chưa gửi");
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(screen.getByText(first.program_name)).toBeVisible();
  expect(screen.getByRole("status")).toHaveTextContent("ke toan");
  year("2025");
  expect(screen.queryByText(first.program_name)).not.toBeInTheDocument();
  await screen.findByText(first.program_name);
  expect(requests().map((p) => [p.get("year"), p.get("query")])).toEqual([
    ["2024", "ke toan"],
    ["2025", "ke toan"],
  ]);
  year("2026");
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));
  expect(requests()[2].get("query")).toBe("ke toan");
  expect(screen.getByLabelText("Tên ngành/chương trình")).toHaveValue(
    "draft chưa gửi",
  );
});

test("clearing cancels a request and removes submitted query/cursor so year changes cannot revive it", async () => {
  let resolve!: (r: Response) => void;
  vi.stubGlobal(
    "fetch",
    vi.fn((_url, init) => {
      expect(init.signal.aborted).toBe(false);
      return new Promise<Response>((r) => {
        resolve = r;
      });
    }),
  );
  render(<ProgramSearch initialYear="2024" />);
  submit("ke toan");
  expect(screen.getByRole("status")).toHaveTextContent(/Đang tải/);
  const signal = vi.mocked(fetch).mock.calls[0][1]?.signal;
  input("");
  expect(signal?.aborted).toBe(true);
  year("2025");
  await act(async () =>
    resolve(
      Response.json({ ...list([first]), next_cursor: "old", has_more: true }),
    ),
  );
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(screen.queryByText(first.program_name)).not.toBeInTheDocument();
  expect(
    screen.queryByRole("button", { name: "Xem thêm" }),
  ).not.toBeInTheDocument();
  expect(screen.getByText(/Nhập ít nhất 2 ký tự/)).toBeVisible();
});

test("year switch aborts old search and rejects stale response even if transport ignores cancellation", async () => {
  const pending: Array<(r: Response) => void> = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(() => new Promise<Response>((r) => pending.push(r))),
  );
  render(<ProgramSearch initialYear="2024" />);
  submit("ke toan");
  year("2025");
  expect(vi.mocked(fetch).mock.calls[0][1]?.signal?.aborted).toBe(true);
  await act(async () => pending[1](Response.json(list([second]))));
  await act(async () => pending[0](Response.json(list([first]))));
  expect(screen.queryByText(first.program_name)).not.toBeInTheDocument();
  expect(screen.getByText(second.program_name)).toBeVisible();
  expect(
    screen.getByRole("link", { name: second.university_name }),
  ).toHaveAttribute("href", `/universities/${second.university_id}?year=2025`);
});

test("pagination sends API cursor, retains API order and does not deduplicate rows", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValueOnce(
        Response.json({
          ...list([first, second]),
          has_more: true,
          next_cursor: "opaque-2",
        }),
      )
      .mockResolvedValueOnce(Response.json(list([first]))),
  );
  render(<ProgramSearch initialYear="2024" />);
  submit("ke toan");
  fireEvent.click(await screen.findByRole("button", { name: "Xem thêm" }));
  await waitFor(() => expect(screen.getAllByRole("article")).toHaveLength(3));
  expect(
    screen
      .getAllByRole("article")
      .map((a) => within(a).getByRole("heading").textContent),
  ).toEqual([first.program_name, second.program_name, first.program_name]);
  expect(requests()[1].get("cursor")).toBe("opaque-2");
  expect(requests()[1].get("limit")).toBe("20");
});

test("a new submission clears results and resets pagination", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValueOnce(
        Response.json({ ...list([first]), has_more: true, next_cursor: "old" }),
      )
      .mockResolvedValueOnce(Response.json(list([second]))),
  );
  render(<ProgramSearch initialYear="2024" />);
  submit("old query");
  await screen.findByText(first.program_name);
  submit("new query");
  expect(screen.queryByText(first.program_name)).not.toBeInTheDocument();
  await screen.findByText(second.program_name);
  expect(requests()[1].has("cursor")).toBe(false);
});

test.each(["409", "version mismatch"])(
  "%s restarts from page1 without mixing dataset versions or using draft",
  async (kind) => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(
          Response.json({
            ...list([first]),
            has_more: true,
            next_cursor: "old",
          }),
        )
        .mockResolvedValueOnce(
          kind === "409"
            ? Response.json(
                { detail: { code: "DATASET_CHANGED" } },
                { status: 409 },
              )
            : Response.json({ ...list([first]), dataset_version: 1043 }),
        )
        .mockResolvedValueOnce(
          Response.json({ ...list([second]), dataset_version: 1043 }),
        ),
    );
    render(<ProgramSearch initialYear="2024" />);
    submit("ke toan");
    await screen.findByText(first.program_name);
    input("draft");
    fireEvent.click(screen.getByRole("button", { name: "Xem thêm" }));
    await screen.findByText(second.program_name);
    expect(screen.queryByText(first.program_name)).not.toBeInTheDocument();
    expect(requests()[2].has("cursor")).toBe(false);
    expect(requests()[2].get("query")).toBe("ke toan");
    expect(screen.getByText("1043").closest("p")).toHaveTextContent(
      /Phiên bản dữ liệu: 1043/,
    );
  },
);

test("persistent409 restarts at most once, then exposes a retry instead of looping", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue(
        Response.json({ detail: { code: "DATASET_CHANGED" } }, { status: 409 }),
      ),
  );
  render(<ProgramSearch initialYear="2024" />);
  submit("ke toan");
  expect(await screen.findByRole("alert")).toHaveTextContent(
    /Dữ liệu đã thay đổi/,
  );
  expect(fetch).toHaveBeenCalledTimes(2);
});

test("API empty differs from guidance; failure is visible and retry uses submitted context", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockRejectedValueOnce(new TypeError("offline"))
      .mockResolvedValueOnce(Response.json(list([]))),
  );
  render(<ProgramSearch initialYear="2024" />);
  submit("ke toan");
  expect(await screen.findByRole("alert")).toHaveTextContent(
    /Không thể tải dữ liệu/,
  );
  input("draft");
  fireEvent.click(screen.getByRole("button", { name: "Thử lại" }));
  expect(await screen.findByText(/Chưa có dữ liệu khớp/)).toBeVisible();
  expect(
    screen.getByText(/Chưa có dữ liệu khớp.*không có nghĩa.*không tuyển sinh/),
  ).toBeVisible();
  expect(requests()[1].get("query")).toBe("ke toan");
});
