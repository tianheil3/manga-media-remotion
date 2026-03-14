import test from "node:test";
import assert from "node:assert/strict";

import { buildCompositionSpec } from "../src/composition-spec.ts";


test("builds renderable scene descriptors for all supported scene types", () => {
  const spec = buildCompositionSpec(
    [
      {
        id: "scene-001",
        type: "narration",
        image: "images/001.png",
        subtitleText: "Narration subtitle",
        durationMs: 1000,
        stylePreset: "default",
        transition: "cut",
      },
      {
        id: "scene-002",
        type: "dialogue",
        image: "images/002.png",
        subtitleText: "Dialogue subtitle",
        durationMs: 1200,
        stylePreset: "dramatic",
        audio: "audio/characters/scene-002.wav",
      },
      {
        id: "scene-003",
        type: "silent",
        image: "images/003.png",
        durationMs: 800,
        stylePreset: "calm",
      },
    ],
    { fps: 30 }
  );

  assert.equal(spec.durationInFrames, 90);
  assert.deepEqual(spec.scenes, [
    {
      id: "scene-001",
      template: "narration",
      fromFrame: 0,
      durationInFrames: 30,
      image: "images/001.png",
      subtitleText: "Narration subtitle",
      showSubtitles: true,
      audio: undefined,
      stylePreset: "default",
      transition: "cut",
    },
    {
      id: "scene-002",
      template: "dialogue",
      fromFrame: 30,
      durationInFrames: 36,
      image: "images/002.png",
      subtitleText: "Dialogue subtitle",
      showSubtitles: true,
      audio: "audio/characters/scene-002.wav",
      stylePreset: "dramatic",
      transition: undefined,
    },
    {
      id: "scene-003",
      template: "silent",
      fromFrame: 66,
      durationInFrames: 24,
      image: "images/003.png",
      subtitleText: undefined,
      showSubtitles: false,
      audio: undefined,
      stylePreset: "calm",
      transition: undefined,
    },
  ]);
});
