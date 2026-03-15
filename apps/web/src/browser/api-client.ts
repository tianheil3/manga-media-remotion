export function createBrowserApiClient(options = {}) {
  const fetchImpl = options.fetchImpl ?? fetch;
  const baseUrl = normalizeBaseUrl(options.baseUrl);

  return {
    listProjects: () => requestJson(fetchImpl, `${baseUrl}/projects`, {}),
    getProject: (projectId) => requestJson(fetchImpl, `${baseUrl}/projects/${projectId}`, {}),
    getScenes: (projectId) => requestJson(fetchImpl, `${baseUrl}/projects/${projectId}/scenes`, {}),
    getFrames: (projectId) => requestJson(fetchImpl, `${baseUrl}/projects/${projectId}/frames`, {}),
    updateFrameReview: (projectId, frameId, payload) =>
      requestJson(fetchImpl, `${baseUrl}/projects/${projectId}/frames/${frameId}/review`, {
        method: "PUT",
        headers: jsonHeaders(),
        body: JSON.stringify(payload),
      }),
    getSceneReview: (projectId) =>
      requestJson(fetchImpl, `${baseUrl}/projects/${projectId}/scene-review`, {}),
    updateScene: (projectId, sceneId, payload) =>
      requestJson(fetchImpl, `${baseUrl}/projects/${projectId}/scenes/${sceneId}`, {
        method: "PUT",
        headers: jsonHeaders(),
        body: JSON.stringify(payload),
      }),
    createRenderJob: (projectId, payload) =>
      requestJson(fetchImpl, `${baseUrl}/projects/${projectId}/render-jobs`, {
        method: "POST",
        headers: jsonHeaders(),
        body: JSON.stringify(payload),
      }),
    getRenderJob: (projectId, jobId) =>
      requestJson(fetchImpl, `${baseUrl}/projects/${projectId}/render-jobs/${jobId}`, {}),
  };
}

async function requestJson(fetchImpl, url, init) {
  const response = await fetchImpl(url, init);
  if (!response.ok) {
    throw new Error(`${init.method ?? "GET"} ${url} failed with ${response.status}`);
  }

  return response.json();
}

function normalizeBaseUrl(baseUrl) {
  if (!baseUrl) {
    return "";
  }

  return baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl;
}

function jsonHeaders() {
  return {
    "content-type": "application/json",
  };
}
