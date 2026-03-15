import test from "node:test";
import assert from "node:assert/strict";

import {
  buildPreviewState,
  buildProjectWorkflowSummary,
  pollRenderJobUntilSettled,
  triggerRenderJobAndPoll,
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

test("builds preview failure notices from persisted render errors", () => {
  const preview = buildPreviewState({
    counts: { frames: 8, voices: 4, scenes: 2 },
    activeJob: {
      id: "render-preview-002",
      projectId: "demo-001",
      kind: "preview",
      status: "failed",
      outputFile: "renders/preview-render-preview-002.mp4",
      createdAt: "2026-03-14T00:00:00.000Z",
      updatedAt: "2026-03-14T00:00:10.000Z",
      errorMessage: "Missing script/scenes.json for render job.",
      statusPath: "/projects/demo-001/render-jobs/render-preview-002",
    },
  });

  assert.equal(preview.renderNotice.tone, "warning");
  assert.equal(
    preview.renderNotice.message,
    "Preview render failed. Missing script/scenes.json for render job."
  );
  assert.equal(preview.renderAction.enabled, true);
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

test("starts a render job and polls status updates until completion", async () => {
  const updates: string[] = [];
  const states = [
    {
      id: "render-preview-003",
      projectId: "demo-001",
      kind: "preview" as const,
      status: "running" as const,
      outputFile: "renders/preview-render-preview-003.mp4",
      createdAt: "2026-03-14T00:00:00.000Z",
      updatedAt: "2026-03-14T00:00:02.000Z",
      statusPath: "/projects/demo-001/render-jobs/render-preview-003",
    },
    {
      id: "render-preview-003",
      projectId: "demo-001",
      kind: "preview" as const,
      status: "completed" as const,
      outputFile: "renders/preview-render-preview-003.mp4",
      createdAt: "2026-03-14T00:00:00.000Z",
      updatedAt: "2026-03-14T00:00:04.000Z",
      statusPath: "/projects/demo-001/render-jobs/render-preview-003",
    },
  ];

  const settled = await triggerRenderJobAndPoll({
    projectId: "demo-001",
    kind: "preview",
    createRenderJob: async (projectId, payload) => ({
      id: "render-preview-003",
      projectId,
      kind: payload.kind,
      status: "queued",
      outputFile: "renders/preview-render-preview-003.mp4",
      createdAt: "2026-03-14T00:00:00.000Z",
      updatedAt: "2026-03-14T00:00:00.000Z",
      statusPath: "/projects/demo-001/render-jobs/render-preview-003",
    }),
    getRenderJob: async () => states.shift()!,
    wait: async () => {},
    onUpdate: (job) => {
      updates.push(job.status);
    },
  });

  assert.equal(settled.status, "completed");
  assert.deepEqual(updates, ["queued", "running", "completed"]);
});

test("starts a render job and surfaces terminal failures", async () => {
  const updates: string[] = [];
  const settled = await triggerRenderJobAndPoll({
    projectId: "demo-001",
    kind: "preview",
    createRenderJob: async (projectId, payload) => ({
      id: "render-preview-004",
      projectId,
      kind: payload.kind,
      status: "queued",
      outputFile: "renders/preview-render-preview-004.mp4",
      createdAt: "2026-03-14T00:00:00.000Z",
      updatedAt: "2026-03-14T00:00:00.000Z",
      statusPath: "/projects/demo-001/render-jobs/render-preview-004",
    }),
    getRenderJob: async () => ({
      id: "render-preview-004",
      projectId: "demo-001",
      kind: "preview",
      status: "failed",
      outputFile: "renders/preview-render-preview-004.mp4",
      createdAt: "2026-03-14T00:00:00.000Z",
      updatedAt: "2026-03-14T00:00:03.000Z",
      errorMessage: "Missing script/scenes.json for render job.",
      statusPath: "/projects/demo-001/render-jobs/render-preview-004",
    }),
    wait: async () => {},
    onUpdate: (job) => {
      updates.push(job.status);
    },
  });

  assert.equal(settled.status, "failed");
  assert.equal(settled.errorMessage, "Missing script/scenes.json for render job.");
  assert.deepEqual(updates, ["queued", "failed"]);
});
