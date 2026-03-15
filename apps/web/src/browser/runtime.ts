import { loadApp } from "../App.tsx";
import { createBrowserApiClient as createApiClient } from "./api-client.ts";
import { sanitizeReviewAppConfig } from "./config.ts";

export async function loadReviewShell({
  config,
  createApiClient: createApiClientImpl = createApiClient,
  loadApp: loadAppImpl = loadApp,
}) {
  const request = sanitizeReviewAppConfig(config);
  if (!request.projectId) {
    throw new Error("Project ID is required.");
  }

  const api = createApiClientImpl({
    baseUrl: request.apiBaseUrl,
  });

  return loadAppImpl({
    api,
    projectId: request.projectId,
    frameId: request.frameId || undefined,
    activeJobId: request.activeJobId || undefined,
  });
}
