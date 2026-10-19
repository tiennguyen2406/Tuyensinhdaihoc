import "server-only";
import { loadCatalog } from "./api";
import type { Filters } from "./contracts";

export function apiRoot(): string {
  const configured = new URL(
    process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000",
  );
  if (
    !["http:", "https:"].includes(configured.protocol) ||
    configured.username ||
    configured.password ||
    configured.search ||
    configured.hash ||
    configured.pathname !== "/"
  ) {
    throw new Error(
      "API_INTERNAL_URL must be an HTTP origin without credentials, query or path.",
    );
  }
  return `${configured.origin}/api/v1`;
}

export function loadServerCatalog(filters: Filters, universityId?: string) {
  return loadCatalog(apiRoot(), filters, universityId);
}
