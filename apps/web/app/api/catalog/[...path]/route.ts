import { apiRoot } from "../../../../lib/server-api";

const eligible =
  /^(universities(?:\/[0-9a-f-]{36}(?:\/admission-years)?)?|programs(?:\/[0-9a-f-]{36})?|cutoffs|advice\/cutoffs|data-coverage|sources\/[0-9a-f-]{36})$/i;

export async function GET(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const path = (await context.params).path.join("/");
  if (!eligible.test(path))
    return Response.json({ detail: "Not found" }, { status: 404 });
  try {
    const upstream = await fetch(
      `${apiRoot()}/${path}${new URL(request.url).search}`,
      { cache: "no-store", signal: request.signal, redirect: "error" },
    );
    return new Response(upstream.body, {
      status: upstream.status,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return Response.json(
      { detail: "Catalog unavailable" },
      { status: 502, headers: { "Cache-Control": "no-store" } },
    );
  }
}
