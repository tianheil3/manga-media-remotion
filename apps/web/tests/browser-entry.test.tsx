import test from "node:test";
import assert from "node:assert/strict";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { AppView } from "../src/App.tsx";
import {
  buildReviewAppSearch,
  readInitialReviewAppConfig,
} from "../src/browser/config.ts";
import { ReviewAppView } from "../src/browser/ReviewApp.tsx";
import { loadReviewShell } from "../src/browser/runtime.ts";

const project = {
  id: "demo-001",
  title: "Demo Project",
  progress: {
    images: true,
    ocr: true,
    review: true,
    translation: true,
    voice: true,
    scenes: true,
  },
  counts: {
    frames: 3,
    voices: 2,
    scenes: 1,
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

test("browser config reads env defaults and URL overrides", () => {
  const config = readInitialReviewAppConfig({
    env: {
      VITE_API_BASE_URL: "http://127.0.0.1:8000/",
    },
    search:
      "?apiBaseUrl=http%3A%2F%2F127.0.0.1%3A9000%2F&projectId=demo-002&frameId=frame-003&activeJobId=job-004",
  });

  assert.deepEqual(config, {
    apiBaseUrl: "http://127.0.0.1:9000",
    projectId: "demo-002",
    frameId: "frame-003",
    activeJobId: "job-004",
  });
});

test("browser config serializes only non-empty runtime values", () => {
  const search = buildReviewAppSearch({
    apiBaseUrl: "http://127.0.0.1:8000/",
    projectId: "demo-001",
    frameId: "",
    activeJobId: "",
  });

  assert.equal(search, "?apiBaseUrl=http%3A%2F%2F127.0.0.1%3A8000&projectId=demo-001");
});

test("review shell loader creates an API client with the configured base url", async () => {
  const calls = [];
  const api = { tag: "api" };
  const loaded = {
    api,
    projectId: "demo-001",
    project,
    scenes,
    activeJob: null,
    frameReview: null,
    sceneReview: null,
  };

  const result = await loadReviewShell({
    config: {
      apiBaseUrl: "http://127.0.0.1:8000/",
      projectId: "demo-001",
      frameId: "frame-003",
      activeJobId: "job-004",
    },
    createApiClient: ({ baseUrl }) => {
      calls.push(["createApiClient", baseUrl]);
      return api;
    },
    loadApp: async (input) => {
      calls.push(["loadApp", input]);
      return loaded;
    },
  });

  assert.deepEqual(calls, [
    ["createApiClient", "http://127.0.0.1:8000"],
    [
      "loadApp",
      {
        api,
        projectId: "demo-001",
        frameId: "frame-003",
        activeJobId: "job-004",
      },
    ],
  ]);
  assert.equal(result.project.id, "demo-001");
});

test("review app view renders the loaded review shell", () => {
  const markup = renderToStaticMarkup(
    React.createElement(ReviewAppView, {
      config: {
        apiBaseUrl: "http://127.0.0.1:8000",
        projectId: "demo-001",
        frameId: "",
        activeJobId: "",
      },
      status: "loaded",
      errorMessage: null,
      onConfigChange() {},
      onSubmit() {},
      shellElement: React.createElement(AppView, {
        project,
        scenes,
        activeJob: null,
        frameReview: null,
        sceneReview: null,
      }),
    })
  );

  assert.match(markup, /Review app/);
  assert.match(markup, /API base URL/);
  assert.match(markup, /Workflow overview/);
  assert.match(markup, /Preview/);
});

test("review app view renders runtime load failures without crashing", () => {
  const markup = renderToStaticMarkup(
    React.createElement(ReviewAppView, {
      config: {
        apiBaseUrl: "http://127.0.0.1:8000",
        projectId: "demo-001",
        frameId: "",
        activeJobId: "",
      },
      status: "error",
      errorMessage: "GET /projects/demo-001 failed with 404",
      onConfigChange() {},
      onSubmit() {},
      shellElement: null,
    })
  );

  assert.match(markup, /GET \/projects\/demo-001 failed with 404/);
  assert.match(markup, /Load project/);
});
