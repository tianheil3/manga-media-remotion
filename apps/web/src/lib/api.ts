import {
  frameReviewUpdateSchema,
  frameSchema,
  projectDetailSchema,
  projectSummarySchema,
  renderJobRequestSchema,
  renderJobSchema,
  sceneReviewSchema,
  sceneUpdateSchema,
} from "@manga/schema";

type FetchLike = typeof fetch;

type ApiClientOptions = {
  baseUrl?: string;
  fetchImpl?: FetchLike;
};

export function createApiClient(options: ApiClientOptions = {}) {
  const fetchImpl = options.fetchImpl ?? fetch;
  const baseUrl = normalizeBaseUrl(options.baseUrl);

  return {
    listProjects: () =>
      requestJson(fetchImpl, `${baseUrl}/projects`, {}, projectSummarySchema.array()),
    getProject: (projectId: string) =>
      requestJson(fetchImpl, `${baseUrl}/projects/${projectId}`, {}, projectDetailSchema),
    getScenes: (projectId: string) =>
      requestJson(fetchImpl, `${baseUrl}/projects/${projectId}/scenes`, {}, sceneReviewSchema.array()),
    getFrames: (projectId: string) =>
      requestJson(fetchImpl, `${baseUrl}/projects/${projectId}/frames`, {}, frameSchema.array()),
    updateFrameReview: (projectId: string, frameId: string, payload: unknown) =>
      requestJson(
        fetchImpl,
        `${baseUrl}/projects/${projectId}/frames/${frameId}/review`,
        {
          method: "PUT",
          headers: jsonHeaders(),
          body: JSON.stringify(frameReviewUpdateSchema.parse(payload)),
        },
        frameSchema
      ),
    getSceneReview: (projectId: string) =>
      requestJson(
        fetchImpl,
        `${baseUrl}/projects/${projectId}/scene-review`,
        {},
        sceneReviewSchema.array()
      ),
    updateScene: (projectId: string, sceneId: string, payload: unknown) =>
      requestJson(
        fetchImpl,
        `${baseUrl}/projects/${projectId}/scenes/${sceneId}`,
        {
          method: "PUT",
          headers: jsonHeaders(),
          body: JSON.stringify(sceneUpdateSchema.parse(payload)),
        },
        sceneReviewSchema
      ),
    createRenderJob: (projectId: string, payload: unknown) =>
      requestJson(
        fetchImpl,
        `${baseUrl}/projects/${projectId}/render-jobs`,
        {
          method: "POST",
          headers: jsonHeaders(),
          body: JSON.stringify(renderJobRequestSchema.parse(payload)),
        },
        renderJobSchema
      ),
    getRenderJob: (projectId: string, jobId: string) =>
      requestJson(
        fetchImpl,
        `${baseUrl}/projects/${projectId}/render-jobs/${jobId}`,
        {},
        renderJobSchema
      ),
  };
}

async function requestJson<T>(
  fetchImpl: FetchLike,
  url: string,
  init: RequestInit,
  schema: { parse(value: unknown): T }
): Promise<T> {
  const response = await fetchImpl(url, init);
  if (!response.ok) {
    throw new Error(`${init.method ?? "GET"} ${url} failed with ${response.status}`);
  }

  return schema.parse(await response.json());
}

function normalizeBaseUrl(baseUrl: string | undefined): string {
  if (!baseUrl) {
    return "";
  }

  return baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl;
}

function jsonHeaders(): HeadersInit {
  return {
    "content-type": "application/json",
  };
}
