import test from "node:test";
import assert from "node:assert/strict";

import {
  createSceneReviewDraft,
  toSceneUpdatePayload,
  updateSceneReviewDraft,
} from "../src/lib/scene-review.ts";


test("creates a scene review draft with exposed audio actions", () => {
  const draft = createSceneReviewDraft({
    id: "scene-001",
    type: "dialogue",
    image: "images/001.png",
    subtitleText: "Hello",
    audio: "audio/characters/scene-001.wav",
    durationMs: 1500,
    speaker: "Hero",
    stylePreset: "dramatic",
    audioMetadata: {
      id: "voice-script-bubble-001",
      frameId: "frame-001",
      mode: "record",
      role: "character",
      speaker: "Hero",
      audioFile: "audio/characters/scene-001.wav",
      durationMs: 1300,
      replaceAudioPath: "/projects/demo-001/voices/voice-script-bubble-001/audio",
      skipRecordingPath: "/projects/demo-001/voices/voice-script-bubble-001/skip",
    },
  });

  assert.deepEqual(draft.audioActions, [
    {
      key: "replace-audio",
      label: "Replace audio",
      path: "/projects/demo-001/voices/voice-script-bubble-001/audio",
    },
    {
      key: "skip-recording",
      label: "Skip recording",
      path: "/projects/demo-001/voices/voice-script-bubble-001/skip",
    },
  ]);
});


test("updates editable scene fields and serializes an update payload", () => {
  const initial = createSceneReviewDraft({
    id: "scene-001",
    type: "narration",
    image: "images/001.png",
    subtitleText: "Original subtitle",
    durationMs: 1400,
    stylePreset: "default",
    audioMetadata: null,
  });

  const updated = updateSceneReviewDraft(initial, {
    subtitleText: "Edited subtitle",
    durationMs: 1800,
    stylePreset: "calm",
  });

  assert.deepEqual(toSceneUpdatePayload(updated), {
    subtitleText: "Edited subtitle",
    durationMs: 1800,
    stylePreset: "calm",
  });
});

test("preserves raw subtitle draft input while normalizing the scene update payload", () => {
  const initial = createSceneReviewDraft({
    id: "scene-001",
    type: "narration",
    image: "images/001.png",
    subtitleText: "Original subtitle",
    durationMs: 1400,
    stylePreset: "default",
    audioMetadata: null,
  });

  const updated = updateSceneReviewDraft(initial, {
    subtitleText: " ",
  });

  assert.equal(updated.subtitleText, " ");
  assert.deepEqual(toSceneUpdatePayload(updated), {
    subtitleText: null,
    durationMs: 1400,
    stylePreset: "default",
  });
});
