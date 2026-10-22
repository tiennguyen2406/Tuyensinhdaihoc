import { afterEach, expect, test, vi } from "vitest";

vi.mock("server-only", () => ({}));
import { GET } from "../app/api/catalog/[...path]/route";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

test("proxy forwards only the exact advice path, preserving decimal query and no-store", async () => {
  vi.stubEnv("API_INTERNAL_URL", "http://127.0.0.1:8000");
  const requests: string[] = [];
  vi.stubGlobal("fetch", async (url: string, init: RequestInit) => {
    requests.push(url);
    expect(init.cache).toBe("no-store");
    expect(init.redirect).toBe("error");
    return Response.json({
      items: [],
      status: "unsupported",
      dataset_version: 3,
    });
  });
  const response = await GET(
    new Request(
      "http://localhost/api/catalog/advice/cutoffs?year=2026&score=25.99999",
    ),
    { params: Promise.resolve({ path: ["advice", "cutoffs"] }) },
  );
  expect(response.status).toBe(200);
  expect(requests).toEqual([
    "http://127.0.0.1:8000/api/v1/advice/cutoffs?year=2026&score=25.99999",
  ]);
  expect(response.headers.get("Cache-Control")).toBe("no-store");
  expect(await response.json()).toMatchObject({
    status: "unsupported",
    dataset_version: 3,
  });
});

test.each([
  ["advice", "options"],
  ["advice", "cutoffs", "extra"],
  ["advice", "https://example.invalid"],
  ["https://example.invalid"],
  ["..", "advice", "cutoffs"],
])(
  "proxy rejects unlisted path %j before contacting upstream",
  async (...path) => {
    vi.stubGlobal("fetch", () => {
      throw new Error("Không được gọi upstream");
    });
    const response = await GET(
      new Request("http://localhost/api/catalog/invalid"),
      {
        params: Promise.resolve({ path }),
      },
    );
    expect(response.status).toBe(404);
  },
);
