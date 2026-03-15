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

export function createApiClient(options = {}) {
  const fetchImpl = options.fetchImpl ?? fetch;
  const baseUrl = normalizeBaseUrl(options.baseUrl);

  return {
    listProjects: () =>
      requestJson(fetchImpl, `${baseUrl}/projects`, {}, projectSummarySchema.array()),
    getProject: (projectId) =>
      requestJson(fetchImpl, `${baseUrl}/projects/${projectId}`, {}, projectDetailSchema),
    getScenes: (projectId) =>
      requestJson(fetchImpl, `${baseUrl}/projects/${projectId}/scenes`, {}, sceneReviewSchema.array()),
    getFrames: (projectId) =>
      requestJson(fetchImpl, `${baseUrl}/projects/${projectId}/frames`, {}, frameSchema.array()),
    updateFrameReview: (projectId, frameId, payload) =>
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
    getSceneReview: (projectId) =>
      requestJson(
        fetchImpl,
        `${baseUrl}/projects/${projectId}/scene-review`,
        {},
        sceneReviewSchema.array()
      ),
    updateScene: (projectId, sceneId, payload) =>
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
    createRenderJob: (projectId, payload) =>
      requestJson(
        fetchImpl,
        `${baseUrl}/projects/${projectId}/render-jobs`,
        {
          method: "POST",
          headers: jsonHeaders(),
          body: JSON.stringify(renderJobRequestSchema.parse(payload)),
        },
        renderJobSchema
      ).then((job) => resolveRenderJobUrls(job, baseUrl)),
    getRenderJob: (projectId, jobId) =>
      requestJson(
        fetchImpl,
        `${baseUrl}/projects/${projectId}/render-jobs/${jobId}`,
        {},
        renderJobSchema
      ).then((job) => resolveRenderJobUrls(job, baseUrl)),
  };
}

async function requestJson(
  fetchImpl,
  url,
  init,
  schema
) {
  const response = await fetchImpl(url, init);
  if (!response.ok) {
    throw new Error(`${init.method ?? "GET"} ${url} failed with ${response.status}`);
  }

  return schema.parse(await response.json());
}

function normalizeBaseUrl(baseUrl) {
  if (!baseUrl) {
    return "";
  }

  return baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl;
}

function resolveRenderJobUrls(job, baseUrl) {
  return {
    ...job,
    outputFile: resolveApiUrl(job.outputFile, baseUrl),
    statusPath: resolveApiUrl(job.statusPath, baseUrl),
  };
}

function resolveApiUrl(path, baseUrl) {
  if (!path || !baseUrl || hasProtocol(path)) {
    return path;
  }

  if (path.startsWith("/")) {
    return `${baseUrl}${path}`;
  }

  return `${baseUrl}/${path}`;
}

function hasProtocol(path) {
  return /^[a-zA-Z][a-zA-Z\d+\-.]*:/.test(path);
}

function jsonHeaders() {
  return {
    "content-type": "application/json",
  };
}
