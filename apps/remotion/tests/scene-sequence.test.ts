import test from "node:test";
import assert from "node:assert/strict";

import { buildSceneSequence, getCompositionDurationInFrames } from "../src/scene-sequence.ts";


test("builds sequential frame ranges from validated scenes", () => {
  const sequence = buildSceneSequence(
    [
      {
        id: "scene-001",
        type: "narration",
        image: "images/001.png",
        subtitleText: "Intro",
        durationMs: 1000,
        stylePreset: "default",
      },
      {
        id: "scene-002",
        type: "dialogue",
        image: "images/002.png",
        subtitleText: "Reply",
        durationMs: 1550,
        stylePreset: "dramatic",
        audio: "audio/characters/scene-002.wav",
      },
    ],
    { fps: 30 }
  );

  assert.deepEqual(sequence, [
    {
      id: "scene-001",
      type: "narration",
      image: "images/001.png",
      subtitleText: "Intro",
      durationMs: 1000,
      stylePreset: "default",
      fromFrame: 0,
      durationInFrames: 30,
    },
    {
      id: "scene-002",
      type: "dialogue",
      image: "images/002.png",
      subtitleText: "Reply",
      durationMs: 1550,
      stylePreset: "dramatic",
      audio: "audio/characters/scene-002.wav",
      fromFrame: 30,
      durationInFrames: 47,
    },
  ]);
  assert.equal(getCompositionDurationInFrames(sequence), 77);
});


test("rejects invalid scene payloads before building a sequence", () => {
  assert.throws(
    () => buildSceneSequence([{ id: "scene-001" }], { fps: 30 }),
    /durationMs/
  );
});
