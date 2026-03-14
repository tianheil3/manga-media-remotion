import test from "node:test";
import assert from "node:assert/strict";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import {
  SceneReviewPage,
  loadSceneReviewPage,
  saveSceneReviewDraft,
} from "../src/pages/SceneReviewPage.tsx";

test("scene review page can load scenes and audio metadata", async () => {
  const page = await loadSceneReviewPage({
    api: {
      getSceneReview: async () => [
        {
          id: "scene-001",
          type: "dialogue",
          image: "images/001.png",
          subtitleText: "edited subtitle",
          audio: "audio/001.wav",
          durationMs: 1200,
          stylePreset: "dramatic",
          audioMetadata: {
            id: "voice-001",
            frameId: "frame-001",
            mode: "tts",
            role: "character",
            audioFile: "audio/001.wav",
            durationMs: 1200,
            replaceAudioPath: "/replace",
            skipRecordingPath: "/skip",
          },
        },
      ],
    },
    projectId: "demo-001",
  });

  assert.equal(page.scenes.length, 1);
  assert.equal(page.drafts[0]?.stylePreset, "dramatic");
});

test("scene review page renders subtitle duration and audio actions", async () => {
  const page = await loadSceneReviewPage({
    api: {
      getSceneReview: async () => [
        {
          id: "scene-001",
          type: "dialogue",
          image: "images/001.png",
          subtitleText: "edited subtitle",
          audio: "audio/001.wav",
          durationMs: 1200,
          stylePreset: "dramatic",
          audioMetadata: {
            id: "voice-001",
            frameId: "frame-001",
            mode: "tts",
            role: "character",
            audioFile: "audio/001.wav",
            durationMs: 1200,
            replaceAudioPath: "/replace",
            skipRecordingPath: "/skip",
          },
        },
      ],
    },
    projectId: "demo-001",
  });

  const markup = renderToStaticMarkup(
    React.createElement(SceneReviewPage, {
      scenes: page.scenes,
      drafts: page.drafts,
    })
  );

  assert.match(markup, /edited subtitle/);
  assert.match(markup, /1200ms/);
  assert.match(markup, /Replace audio/);
});

test("scene review page persists subtitle duration and style edits", async () => {
  const calls = [];
  const savedScene = await saveSceneReviewDraft({
    api: {
      updateScene: async (projectId, sceneId, payload) => {
        calls.push({ projectId, sceneId, payload });
        return {
          id: sceneId,
          type: "dialogue",
          image: "images/001.png",
          subtitleText: payload.subtitleText,
          durationMs: payload.durationMs,
          stylePreset: payload.stylePreset,
          audioMetadata: null,
        };
      },
    },
    projectId: "demo-001",
    draft: {
      id: "scene-001",
      subtitleText: "short subtitle",
      durationMs: 900,
      stylePreset: "fast",
      audioActions: [],
    },
  });

  assert.deepEqual(calls, [
    {
      projectId: "demo-001",
      sceneId: "scene-001",
      payload: {
        subtitleText: "short subtitle",
        durationMs: 900,
        stylePreset: "fast",
      },
    },
  ]);
  assert.equal(savedScene.durationMs, 900);
});
