import test from "node:test";
import assert from "node:assert/strict";

import {
  frameSchema,
  projectSchema,
  sceneSchema,
  voiceSchema,
} from "../src/index.ts";

test("validates a project file shape", () => {
  const parsed = projectSchema.parse({
    id: "demo-001",
    title: "Demo Project",
    sourceLanguage: "ja",
    imageDir: "images",
    createdAt: "2026-03-14T00:00:00.000Z",
    updatedAt: "2026-03-14T00:00:00.000Z",
  });

  assert.equal(parsed.id, "demo-001");
});

test("validates an OCR frame file shape", () => {
  const parsed = frameSchema.parse({
    frameId: "frame-001",
    image: "images/001.png",
    ocrFile: "ocr/001.json",
    bubbles: [
      {
        id: "bubble-001",
        text: "hello",
        bbox: { x: 1, y: 2, w: 3, h: 4 },
        order: 0,
        confidence: 0.9,
        language: "ja",
      },
    ],
    reviewedBubbles: [],
  });

  assert.equal(parsed.bubbles.length, 1);
});

test("validates a voice segment file shape", () => {
  const parsed = voiceSchema.parse({
    id: "voice-001",
    frameId: "frame-001",
    text: "Narration line",
    mode: "tts",
    role: "narrator",
    durationMs: 1200,
  });

  assert.equal(parsed.mode, "tts");
});

test("validates a scene file shape", () => {
  const parsed = sceneSchema.parse({
    id: "scene-001",
    type: "narration",
    image: "images/001.png",
    subtitleText: "Subtitle",
    durationMs: 1800,
    stylePreset: "default",
    transition: "cut",
  });

  assert.equal(parsed.type, "narration");
});

test("rejects missing required fields", () => {
  assert.throws(() => projectSchema.parse({ title: "Missing id" }));
  assert.throws(() => frameSchema.parse({ frameId: "frame-001" }));
  assert.throws(() => voiceSchema.parse({ id: "voice-001" }));
  assert.throws(() => sceneSchema.parse({ id: "scene-001" }));
});
