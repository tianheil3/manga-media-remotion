import test from "node:test";
import assert from "node:assert/strict";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { AppView, createAppReviewActions, loadApp } from "../src/App.tsx";
import { FrameReviewPage } from "../src/pages/FrameReviewPage.tsx";
import {
  loadPreviewPage,
  PreviewPage,
  triggerPreviewRender,
} from "../src/pages/PreviewPage.tsx";
import { ProjectOverviewPage } from "../src/pages/ProjectOverview.tsx";
import { SceneReviewPage } from "../src/pages/SceneReviewPage.tsx";
import { findElement } from "./test-tree.ts";

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
    React.createElement(AppView, {
      project,
      scenes,
      activeJob: null,
    })
  );

  assert.match(markup, /Workflow overview/);
  assert.match(markup, /Preview/);
});

test("app shell forwards review action props to review pages", () => {
  const frameReviewActions = {
    onBubbleTextEditedChange() {},
    onBubbleOrderChange() {},
    onBubbleKindChange() {},
    onBubbleSpeakerChange() {},
    onSave() {},
  };
  const sceneReviewActions = {
    onSubtitleTextChange() {},
    onDurationMsChange() {},
    onStylePresetChange() {},
    onSaveScene() {},
  };
  const previewActions = {
    onTriggerRender() {},
  };

  const tree = AppView({
    project,
    scenes,
    activeJob: null,
    frameReview: {
      frame: { frameId: "frame-001" },
      draft: {
        frameId: "frame-001",
        bubbles: [
          {
            sourceBubbleId: "bubble-a",
            textEdited: "edited line",
            order: 0,
            kind: "dialogue",
            speaker: "Hero",
          },
        ],
      },
    },
    sceneReview: {
      scenes: [
        {
          id: "scene-001",
          type: "dialogue",
          image: "images/001.png",
          subtitleText: "edited subtitle",
          durationMs: 1200,
          stylePreset: "dramatic",
          audioMetadata: null,
        },
      ],
      drafts: [
        {
          id: "scene-001",
          subtitleText: "edited subtitle",
          durationMs: 1200,
          stylePreset: "dramatic",
          audioActions: [],
        },
      ],
    },
    frameReviewActions,
    sceneReviewActions,
    previewActions,
  });

  const frameReviewElement = findElement(
    tree,
    (node) => node.type === FrameReviewPage
  );
  const sceneReviewElement = findElement(
    tree,
    (node) => node.type === SceneReviewPage
  );
  const previewElement = findElement(tree, (node) => node.type === PreviewPage);

  assert.equal(frameReviewElement.type, FrameReviewPage);
  assert.equal(frameReviewElement.props.actions, frameReviewActions);
  assert.equal(sceneReviewElement.type, SceneReviewPage);
  assert.equal(sceneReviewElement.props.actions, sceneReviewActions);
  assert.equal(previewElement.type, PreviewPage);
  assert.equal(previewElement.props.actions, previewActions);
});

test("app loader fetches frame review and scene review data for the shell", async () => {
  const calls = [];
  const api = {
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
    };
  const loaded = await loadApp({
    api,
    projectId: "demo-001",
  });

  assert.deepEqual(calls, [
    ["project", "demo-001"],
    ["scenes", "demo-001"],
    ["frames", "demo-001"],
    ["scene-review", "demo-001"],
  ]);
  assert.equal(loaded.api, api);
  assert.equal(loaded.projectId, "demo-001");
  assert.equal(loaded.frameReview?.frame.frameId, "frame-001");
  assert.equal(loaded.frameReview?.isLoading, false);
  assert.equal(loaded.frameReview?.errorMessage, null);
  assert.equal(loaded.sceneReview?.scenes[0]?.id, "scene-001");
});

test("app loader surfaces frame review load errors without dropping the rest of the shell", async () => {
  const loaded = await loadApp({
    api: {
      getProject: async () => project,
      getScenes: async () => scenes,
      getRenderJob: async () => null,
      getFrames: async () => {
        throw new Error("frame load failed");
      },
      getSceneReview: async () => [
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
      ],
    },
    projectId: "demo-001",
  });

  const markup = renderToStaticMarkup(React.createElement(AppView, loaded));

  assert.match(markup, /frame load failed/);
  assert.match(markup, /Scene review/);
});

test("app loader surfaces scene review load errors without dropping frame review", async () => {
  const loaded = await loadApp({
    api: {
      getProject: async () => project,
      getScenes: async () => scenes,
      getRenderJob: async () => null,
      getFrames: async () => [
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
          reviewedBubbles: [],
        },
      ],
      getSceneReview: async () => {
        throw new Error("scene load failed");
      },
    },
    projectId: "demo-001",
  });

  const markup = renderToStaticMarkup(React.createElement(AppView, loaded));

  assert.match(markup, /scene load failed/);
  assert.match(markup, /Frame review/);
});

test("app review actions write through setter callbacks for mounted state", async () => {
  const calls = [];
  let frameReview = {
    frame: {
      frameId: "frame-001",
      image: "images/001.png",
      ocrFile: "ocr/001.json",
      bubbles: [],
      reviewedBubbles: [],
    },
    draft: {
      frameId: "frame-001",
      bubbles: [
        {
          sourceBubbleId: "bubble-a",
          textEdited: "draft line",
          order: 0,
          kind: "dialogue",
          speaker: "Hero",
        },
      ],
    },
    isLoading: false,
    isSaving: false,
    errorMessage: null,
    saveMessage: null,
    validationErrors: {},
  };
  let sceneReview = {
    scenes: [
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
    ],
    drafts: [
      {
        id: "scene-001",
        subtitleText: "edited subtitle",
        durationMs: 1200,
        stylePreset: "dramatic",
        audioActions: [],
      },
    ],
    isLoading: false,
    savingSceneIds: [],
    errorMessages: {},
    saveMessages: {},
    validationErrors: {},
  };

  const { frameReviewActions, sceneReviewActions } = createAppReviewActions({
    api: {
      updateFrameReview: async (projectId, frameId, payload) => {
        calls.push(["frame-save", projectId, frameId, payload]);
        return {
          frameId,
          image: "images/001.png",
          ocrFile: "ocr/001.json",
          bubbles: [],
          reviewedBubbles: [
            {
              id: "review-a",
              sourceBubbleId: "bubble-a",
              textOriginal: "raw line",
              textEdited: "saved line",
              order: 1,
              kind: "narration",
              speaker: "Narrator",
            },
          ],
        };
      },
      updateScene: async (projectId, sceneId, payload) => {
        calls.push(["scene-save", projectId, sceneId, payload]);
        return {
          id: sceneId,
          type: "dialogue",
          image: "images/001.png",
          subtitleText: "saved subtitle",
          durationMs: 1800,
          stylePreset: "calm",
          audioMetadata: null,
        };
      },
    },
    projectId: "demo-001",
    getFrameReviewState: () => frameReview,
    setFrameReviewState: (nextState) => {
      frameReview = nextState;
    },
    getSceneReviewState: () => sceneReview,
    setSceneReviewState: (nextState) => {
      sceneReview = nextState;
    },
  });

  frameReviewActions.onBubbleTextEditedChange("bubble-a", "edited in app");
  sceneReviewActions.onStylePresetChange("scene-001", "fast");

  assert.equal(frameReview.draft.bubbles[0]?.textEdited, "edited in app");
  assert.equal(sceneReview.drafts[0]?.stylePreset, "fast");

  await frameReviewActions.onSave();
  await sceneReviewActions.onSaveScene("scene-001");

  assert.equal(frameReview.saveMessage, "Frame review saved.");
  assert.equal(frameReview.draft.bubbles[0]?.textEdited, "saved line");
  assert.equal(sceneReview.saveMessages["scene-001"], "Scene review saved.");
  assert.equal(sceneReview.drafts[0]?.subtitleText, "saved subtitle");
  assert.deepEqual(calls, [
    [
      "frame-save",
      "demo-001",
      "frame-001",
      {
        reviewedBubbles: [
          {
            sourceBubbleId: "bubble-a",
            textEdited: "edited in app",
            order: 0,
            kind: "dialogue",
            speaker: "Hero",
          },
        ],
        skip: false,
      },
    ],
    [
      "scene-save",
      "demo-001",
      "scene-001",
      {
        subtitleText: "edited subtitle",
        durationMs: 1200,
        stylePreset: "fast",
      },
    ],
  ]);
});

test("app preview actions trigger preview renders and keep active job state current", async () => {
  const calls = [];
  const updates = [];
  let activeJob = null;
  const queuedJob = {
    id: "render-preview-002",
    projectId: "demo-001",
    kind: "preview",
    status: "queued",
    outputFile: "http://127.0.0.1:8000/projects/demo-001/media/renders/preview.mp4",
    createdAt: "2026-03-15T00:00:00.000Z",
    updatedAt: "2026-03-15T00:00:00.000Z",
    statusPath: "http://127.0.0.1:8000/projects/demo-001/render-jobs/render-preview-002",
  };
  const polledJobs = [
    {
      ...queuedJob,
      status: "running",
      updatedAt: "2026-03-15T00:00:02.000Z",
    },
    {
      ...queuedJob,
      status: "completed",
      updatedAt: "2026-03-15T00:00:04.000Z",
    },
  ];

  const { previewActions } = createAppReviewActions({
    api: {
      createRenderJob: async (projectId, payload) => {
        calls.push(["create", projectId, payload]);
        return queuedJob;
      },
      getRenderJob: async (projectId, jobId) => {
        calls.push(["poll", projectId, jobId]);
        return polledJobs.shift();
      },
    },
    projectId: "demo-001",
    getFrameReviewState: () => null,
    setFrameReviewState() {},
    getSceneReviewState: () => null,
    setSceneReviewState() {},
    getActiveJob: () => activeJob,
    setActiveJob: (nextJob) => {
      activeJob = nextJob;
      updates.push(nextJob.status);
    },
  });

  assert.equal(typeof previewActions?.onTriggerRender, "function");

  const settledJob = await previewActions.onTriggerRender();

  assert.equal(settledJob.status, "completed");
  assert.equal(activeJob?.status, "completed");
  assert.deepEqual(updates, ["queued", "running", "completed"]);
  assert.deepEqual(calls, [
    ["create", "demo-001", { kind: "preview" }],
    ["poll", "demo-001", "render-preview-002"],
    ["poll", "demo-001", "render-preview-002"],
  ]);
});

test("app loader ignores stale frame ids instead of throwing", async () => {
  const loaded = await loadApp({
    api: {
      getProject: async () => project,
      getScenes: async () => scenes,
      getRenderJob: async () => null,
      getFrames: async () => [
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
          reviewedBubbles: [],
        },
      ],
      getSceneReview: async () => [
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
      ],
    },
    projectId: "demo-001",
    frameId: "missing-frame",
  });

  assert.equal(loaded.frameReview, null);
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

test("preview page renders a completed artifact link and trigger callback when actions are provided", async () => {
  const calls = [];
  const completedJob = {
    id: "render-preview-003",
    projectId: "demo-001",
    kind: "preview",
    status: "completed",
    outputFile: "http://127.0.0.1:8000/projects/demo-001/media/renders/preview.mp4",
    createdAt: "2026-03-15T00:00:00.000Z",
    updatedAt: "2026-03-15T00:00:04.000Z",
    statusPath: "http://127.0.0.1:8000/projects/demo-001/render-jobs/render-preview-003",
  };

  const tree = PreviewPage({
    project,
    scenes,
    activeJob: completedJob,
    actions: {
      onTriggerRender: async () => {
        calls.push("triggered");
      },
    },
  });
  const button = findElement(
    tree,
    (node) => node.type === "button" && node.props.children === "Trigger preview render"
  );

  await button.props.onClick();

  const markup = renderToStaticMarkup(
    React.createElement(PreviewPage, {
      project,
      scenes,
      activeJob: completedJob,
      actions: {
        onTriggerRender() {},
      },
    })
  );

  assert.deepEqual(calls, ["triggered"]);
  assert.match(markup, /Open render artifact/);
  assert.match(
    markup,
    /http:\/\/127\.0\.0\.1:8000\/projects\/demo-001\/media\/renders\/preview\.mp4/
  );
});
