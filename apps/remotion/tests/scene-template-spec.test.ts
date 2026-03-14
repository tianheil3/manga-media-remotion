import test from "node:test";
import assert from "node:assert/strict";

import { buildSceneTemplateSpec } from "../src/scene-template-spec.ts";


test("builds stable template specs for narration dialogue and silent scenes", () => {
  assert.deepEqual(
    buildSceneTemplateSpec({
      id: "scene-001",
      type: "narration",
      image: "images/001.png",
      subtitleText: "Narration subtitle",
      durationMs: 1200,
      stylePreset: "default",
    }),
    {
      template: "narration",
      motion: "pan",
      subtitles: {
        visible: true,
        text: "Narration subtitle",
        position: "bottom-center",
      },
    }
  );

  assert.deepEqual(
    buildSceneTemplateSpec({
      id: "scene-002",
      type: "dialogue",
      image: "images/002.png",
      subtitleText: "Dialogue subtitle",
      durationMs: 1400,
      stylePreset: "dramatic",
    }),
    {
      template: "dialogue",
      motion: "zoom-in",
      subtitles: {
        visible: true,
        text: "Dialogue subtitle",
        position: "bottom-center",
      },
    }
  );

  assert.deepEqual(
    buildSceneTemplateSpec({
      id: "scene-003",
      type: "silent",
      image: "images/003.png",
      durationMs: 900,
      stylePreset: "calm",
    }),
    {
      template: "silent",
      motion: "none",
      subtitles: {
        visible: false,
        text: undefined,
        position: "hidden",
      },
    }
  );
});


test("respects explicit camera motion from the scene file", () => {
  assert.equal(
    buildSceneTemplateSpec({
      id: "scene-004",
      type: "dialogue",
      image: "images/004.png",
      subtitleText: "Override",
      durationMs: 1100,
      stylePreset: "default",
      cameraMotion: "zoom-out",
    }).motion,
    "zoom-out"
  );
});
