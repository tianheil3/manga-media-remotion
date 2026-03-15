import test from "node:test";
import assert from "node:assert/strict";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { App, loadApp } from "../src/App.tsx";
import {
  loadPreviewPage,
  PreviewPage,
  triggerPreviewRender,
} from "../src/pages/PreviewPage.tsx";
import { ProjectOverviewPage } from "../src/pages/ProjectOverview.tsx";

const project = {
  id: "demo-001",
  title: "Demo Project",
  progress: {
    images: true,
    ocr: true,
    review: false,
    translation: false,
    voice: false,
    scenes: true,
  },
  counts: {
    frames: 6,
    voices: 2,
    scenes: 3,
  },
};

const scenes = [
  {
    id: "scene-001",
    type: "narration",
    image: "images/001.png",
    subtitleText: "Opening line",
    durationMs: 1000,
    stylePreset: "default",
  },
];

test("project overview renders workflow sections and next-stage guidance", () => {
  const markup = renderToStaticMarkup(
    React.createElement(ProjectOverviewPage, {
      project,
    })
  );

  assert.match(markup, /Demo Project/);
  assert.match(markup, /Images/);
  assert.match(markup, /Review text/);
  assert.match(markup, /Next stage/);
});

test("preview page mounts a preview container and shows render progress", () => {
  const markup = renderToStaticMarkup(
    React.createElement(PreviewPage, {
      project,
      scenes,
      activeJob: {
        id: "render-preview-001",
        projectId: "demo-001",
        kind: "preview",
        status: "running",
        outputFile: "renders/preview.mp4",
        createdAt: "2026-03-14T00:00:00.000Z",
        updatedAt: "2026-03-14T00:00:01.000Z",
        statusPath: "/projects/demo-001/render-jobs/render-preview-001",
      },
    })
  );

  assert.match(markup, /data-preview-container="mounted"/);
  assert.match(markup, /Preview render is running\./);
  assert.match(markup, /Opening line/);
  assert.match(markup, /data-duration-in-frames="30"/);
  assert.match(markup, /data-scene-type="narration"/);
});

test("preview page shows persisted render failures", () => {
  const markup = renderToStaticMarkup(
    React.createElement(PreviewPage, {
      project,
      scenes,
      activeJob: {
        id: "render-preview-001",
        projectId: "demo-001",
        kind: "preview",
        status: "failed",
        outputFile: "renders/preview.mp4",
        createdAt: "2026-03-14T00:00:00.000Z",
        updatedAt: "2026-03-14T00:00:01.000Z",
        errorMessage: "Missing script/scenes.json",
        statusPath: "/projects/demo-001/render-jobs/render-preview-001",
      },
    })
  );

  assert.match(markup, /Preview render failed\./);
  assert.match(markup, /Missing script\/scenes\.json/);
});

test("preview page loader fetches project scene data and active render jobs", async () => {
  const calls = [];
  const preview = await loadPreviewPage({
    api: {
      getProject: async (projectId) => {
        calls.push(["project", projectId]);
        return project;
      },
      getScenes: async (projectId) => {
        calls.push(["scenes", projectId]);
        return scenes;
      },
      getRenderJob: async (projectId, jobId) => {
        calls.push(["job", projectId, jobId]);
        return {
          id: jobId,
          projectId,
          kind: "preview",
          status: "running",
          outputFile: "renders/preview.mp4",
          createdAt: "2026-03-14T00:00:00.000Z",
          updatedAt: "2026-03-14T00:00:01.000Z",
          statusPath: `/projects/${projectId}/render-jobs/${jobId}`,
        };
      },
    },
    projectId: "demo-001",
    activeJobId: "render-preview-001",
  });

  assert.deepEqual(calls, [
    ["project", "demo-001"],
    ["scenes", "demo-001"],
    ["job", "demo-001", "render-preview-001"],
  ]);
  assert.equal(preview.project.id, "demo-001");
  assert.equal(preview.scenes[0]?.id, "scene-001");
  assert.equal(preview.activeJob?.id, "render-preview-001");
});

test("app shell renders overview and preview sections together", () => {
  const markup = renderToStaticMarkup(
    React.createElement(App, {
      project,
      scenes,
      activeJob: null,
    })
  );

  assert.match(markup, /Workflow overview/);
  assert.match(markup, /Preview/);
});

test("app loader fetches frame review and scene review data for the shell", async () => {
  const calls = [];
  const loaded = await loadApp({
    api: {
      getProject: async (projectId) => {
        calls.push(["project", projectId]);
        return project;
      },
      getScenes: async (projectId) => {
        calls.push(["scenes", projectId]);
        return scenes;
      },
      getRenderJob: async () => null,
      getFrames: async (projectId) => {
        calls.push(["frames", projectId]);
        return [
          {
            frameId: "frame-001",
            image: "images/001.png",
            ocrFile: "ocr/001.json",
            bubbles: [
              {
                id: "bubble-a",
                text: "raw line",
                bbox: { x: 0, y: 0, w: 10, h: 10 },
                order: 0,
                confidence: 0.9,
                language: "ja",
              },
            ],
            reviewedBubbles: [
              {
                id: "review-a",
                sourceBubbleId: "bubble-a",
                textOriginal: "raw line",
                textEdited: "edited line",
                order: 0,
                kind: "dialogue",
                speaker: "Hero",
              },
            ],
          },
        ];
      },
      getSceneReview: async (projectId) => {
        calls.push(["scene-review", projectId]);
        return [
          {
            id: "scene-001",
            type: "dialogue",
            image: "images/001.png",
            subtitleText: "edited subtitle",
            audio: "audio/001.wav",
            durationMs: 1200,
            stylePreset: "dramatic",
            audioMetadata: null,
          },
        ];
      },
    },
    projectId: "demo-001",
  });

  assert.deepEqual(calls, [
    ["project", "demo-001"],
    ["scenes", "demo-001"],
    ["frames", "demo-001"],
    ["scene-review", "demo-001"],
  ]);
  assert.equal(loaded.frameReview?.frame.frameId, "frame-001");
  assert.equal(loaded.sceneReview?.scenes[0]?.id, "scene-001");
});

test("preview page can trigger preview renders and poll job updates", async () => {
  const calls = [];
  const updates = [];
  const states = [
    {
      id: "render-preview-002",
      projectId: "demo-001",
      kind: "preview",
      status: "running",
      outputFile: "renders/preview.mp4",
      createdAt: "2026-03-14T00:00:00.000Z",
      updatedAt: "2026-03-14T00:00:02.000Z",
      statusPath: "/projects/demo-001/render-jobs/render-preview-002",
    },
    {
      id: "render-preview-002",
      projectId: "demo-001",
      kind: "preview",
      status: "completed",
      outputFile: "renders/preview.mp4",
      createdAt: "2026-03-14T00:00:00.000Z",
      updatedAt: "2026-03-14T00:00:03.000Z",
      statusPath: "/projects/demo-001/render-jobs/render-preview-002",
    },
  ];
  const api = {
    createRenderJob: async (projectId, payload) => {
      calls.push({ projectId, payload });
      return {
        id: "render-preview-002",
        projectId,
        kind: payload.kind,
        status: "queued",
        outputFile: "renders/preview.mp4",
        createdAt: "2026-03-14T00:00:00.000Z",
        updatedAt: "2026-03-14T00:00:00.000Z",
        statusPath: `/projects/${projectId}/render-jobs/render-preview-002`,
      };
    },
    getRenderJob: async (projectId, jobId) => {
      calls.push({ projectId, jobId });
      return states.shift();
    },
  };

  const job = await triggerPreviewRender({
    api,
    projectId: "demo-001",
    onJobUpdate: (nextJob) => {
      updates.push(nextJob.status);
    },
    wait: async () => {},
  });

  assert.deepEqual(calls, [
    {
      projectId: "demo-001",
      payload: { kind: "preview" },
    },
    {
      projectId: "demo-001",
      jobId: "render-preview-002",
    },
    {
      projectId: "demo-001",
      jobId: "render-preview-002",
    },
  ]);
  assert.deepEqual(updates, ["queued", "running", "completed"]);
  assert.equal(job.status, "completed");
});
