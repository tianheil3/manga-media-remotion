import test from "node:test";
import assert from "node:assert/strict";

import {
  buildPreviewState,
  buildProjectWorkflowSummary,
  pollRenderJobUntilSettled,
} from "../src/lib/workflow.ts";


test("builds ordered workflow sections and next-stage guidance from project progress", () => {
  const summary = buildProjectWorkflowSummary({
    id: "demo-001",
    title: "Demo Project",
    progress: {
      images: true,
      ocr: true,
      review: true,
      translation: false,
      voice: false,
      scenes: false,
    },
    counts: {
      frames: 8,
      voices: 0,
      scenes: 0,
    },
  });

  assert.deepEqual(
    summary.sections.map((section) => ({
      key: section.key,
      done: section.done,
      count: section.count,
    })),
    [
      { key: "images", done: true, count: 8 },
      { key: "ocr", done: true, count: 8 },
      { key: "review", done: true, count: 8 },
      { key: "translation", done: false, count: 0 },
      { key: "voice", done: false, count: 0 },
      { key: "scenes", done: false, count: 0 },
    ]
  );
  assert.equal(summary.nextStage.key, "translation");
  assert.equal(summary.nextStage.actionLabel, "Run translation");
});


test("builds preview state from scenes and render jobs", () => {
  const preview = buildPreviewState({
    counts: { frames: 8, voices: 4, scenes: 2 },
    activeJob: {
      id: "render-preview-001",
      projectId: "demo-001",
      kind: "preview",
      status: "running",
      outputFile: "renders/preview-render-preview-001.mp4",
      createdAt: "2026-03-14T00:00:00.000Z",
      updatedAt: "2026-03-14T00:00:10.000Z",
      statusPath: "/projects/demo-001/render-jobs/render-preview-001",
    },
  });

  assert.equal(preview.canMountPlayer, true);
  assert.equal(preview.renderNotice.tone, "info");
  assert.equal(preview.renderNotice.message, "Preview render is running.");
  assert.equal(preview.renderAction.enabled, false);
});


test("polls render jobs until a terminal state is reached", async () => {
  const seenJobIds: string[] = [];
  const states = [
    {
      id: "render-preview-001",
      projectId: "demo-001",
      kind: "preview" as const,
      status: "queued" as const,
      outputFile: "renders/preview-render-preview-001.mp4",
      createdAt: "2026-03-14T00:00:00.000Z",
      updatedAt: "2026-03-14T00:00:00.000Z",
      statusPath: "/projects/demo-001/render-jobs/render-preview-001",
    },
    {
      id: "render-preview-001",
      projectId: "demo-001",
      kind: "preview" as const,
      status: "running" as const,
      outputFile: "renders/preview-render-preview-001.mp4",
      createdAt: "2026-03-14T00:00:00.000Z",
      updatedAt: "2026-03-14T00:00:03.000Z",
      statusPath: "/projects/demo-001/render-jobs/render-preview-001",
    },
    {
      id: "render-preview-001",
      projectId: "demo-001",
      kind: "preview" as const,
      status: "completed" as const,
      outputFile: "renders/preview-render-preview-001.mp4",
      createdAt: "2026-03-14T00:00:00.000Z",
      updatedAt: "2026-03-14T00:00:08.000Z",
      statusPath: "/projects/demo-001/render-jobs/render-preview-001",
    },
  ];
  let delayCalls = 0;

  const settled = await pollRenderJobUntilSettled({
    projectId: "demo-001",
    jobId: "render-preview-001",
    getRenderJob: async (projectId, jobId) => {
      assert.equal(projectId, "demo-001");
      seenJobIds.push(jobId);
      return states.shift()!;
    },
    wait: async () => {
      delayCalls += 1;
    },
  });

  assert.equal(settled.status, "completed");
  assert.equal(delayCalls, 2);
  assert.deepEqual(seenJobIds, [
    "render-preview-001",
    "render-preview-001",
    "render-preview-001",
  ]);
});
