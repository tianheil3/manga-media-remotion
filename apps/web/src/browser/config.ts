export function readInitialReviewAppConfig({ env = {}, search = "" } = {}) {
  const params = new URLSearchParams(search);

  return sanitizeReviewAppConfig({
    apiBaseUrl:
      params.get("apiBaseUrl") ?? env.MANGA_API_BASE_URL ?? env.VITE_API_BASE_URL ?? "",
    projectId: params.get("projectId") ?? "",
    frameId: params.get("frameId") ?? "",
    activeJobId: params.get("activeJobId") ?? "",
  });
}

export function buildReviewAppSearch(config) {
  const resolved = sanitizeReviewAppConfig(config);
  const params = new URLSearchParams();

  if (resolved.apiBaseUrl) {
    params.set("apiBaseUrl", resolved.apiBaseUrl);
  }
  if (resolved.projectId) {
    params.set("projectId", resolved.projectId);
  }
  if (resolved.frameId) {
    params.set("frameId", resolved.frameId);
  }
  if (resolved.activeJobId) {
    params.set("activeJobId", resolved.activeJobId);
  }

  const search = params.toString();
  return search ? `?${search}` : "";
}

export function sanitizeReviewAppConfig(config) {
  return {
    apiBaseUrl: normalizeOptionalValue(config?.apiBaseUrl, { trimTrailingSlash: true }),
    projectId: normalizeOptionalValue(config?.projectId),
    frameId: normalizeOptionalValue(config?.frameId),
    activeJobId: normalizeOptionalValue(config?.activeJobId),
  };
}

function normalizeOptionalValue(value, { trimTrailingSlash = false } = {}) {
  if (typeof value !== "string") {
    return "";
  }

  const normalized = value.trim();
  if (!normalized) {
    return "";
  }

  if (trimTrailingSlash && normalized.endsWith("/")) {
    return normalized.slice(0, -1);
  }

  return normalized;
}
