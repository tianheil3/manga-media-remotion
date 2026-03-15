import test from "node:test";
import assert from "node:assert/strict";

import { createBrowserApiClient } from "../src/browser/api-client.ts";

test("browser api client resolves render job urls against the configured api base url", async () => {
  const client = createBrowserApiClient({
    baseUrl: "http://127.0.0.1:8000/",
    fetchImpl: async () =>
      new Response(
        JSON.stringify({
          id: "render-preview-001",
          projectId: "demo-001",
          kind: "preview",
          status: "completed",
          outputFile: "/projects/demo-001/media/renders/preview.mp4",
          createdAt: "2026-03-15T00:00:00.000Z",
          updatedAt: "2026-03-15T00:00:03.000Z",
          statusPath: "/projects/demo-001/render-jobs/render-preview-001",
        }),
        {
          status: 200,
          headers: { "content-type": "application/json" },
        }
      ),
  });

  const job = await client.getRenderJob("demo-001", "render-preview-001");

  assert.equal(
    job.outputFile,
    "http://127.0.0.1:8000/projects/demo-001/media/renders/preview.mp4"
  );
  assert.equal(
    job.statusPath,
    "http://127.0.0.1:8000/projects/demo-001/render-jobs/render-preview-001"
  );
});
