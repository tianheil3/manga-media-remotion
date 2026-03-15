import test from "node:test";
import assert from "node:assert/strict";

import {
  createFrameReviewDraft,
  reorderReviewDraft,
  toFrameReviewPayload,
  updateReviewBubble,
} from "../src/lib/frame-review.ts";


test("creates a draft from OCR bubbles when reviewed text does not exist yet", () => {
  const draft = createFrameReviewDraft({
    frameId: "frame-001",
    image: "images/001.png",
    ocrFile: "ocr/001.json",
    bubbles: [
      {
        id: "bubble-a",
        text: "A",
        bbox: { x: 10, y: 10, w: 10, h: 10 },
        order: 1,
        confidence: 0.9,
        language: "ja",
      },
      {
        id: "bubble-b",
        text: "B",
        bbox: { x: 20, y: 10, w: 10, h: 10 },
        order: 0,
        confidence: 0.8,
        language: "ja",
      },
    ],
    reviewedBubbles: [],
  });

  assert.deepEqual(draft.bubbles, [
    {
      sourceBubbleId: "bubble-b",
      textEdited: "B",
      order: 0,
      kind: "dialogue",
      speaker: undefined,
    },
    {
      sourceBubbleId: "bubble-a",
      textEdited: "A",
      order: 1,
      kind: "dialogue",
      speaker: undefined,
    },
  ]);
});

test("creates a draft that keeps unreviewed OCR bubbles alongside reviewed ones", () => {
  const draft = createFrameReviewDraft({
    frameId: "frame-001",
    image: "images/001.png",
    ocrFile: "ocr/001.json",
    bubbles: [
      {
        id: "bubble-a",
        text: "A",
        bbox: { x: 10, y: 10, w: 10, h: 10 },
        order: 0,
        confidence: 0.9,
        language: "ja",
      },
      {
        id: "bubble-b",
        text: "B",
        bbox: { x: 20, y: 10, w: 10, h: 10 },
        order: 1,
        confidence: 0.8,
        language: "ja",
      },
    ],
    reviewedBubbles: [
      {
        id: "review-bubble-a",
        sourceBubbleId: "bubble-a",
        textOriginal: "A",
        textEdited: "Edited A",
        order: 0,
        kind: "narration",
        speaker: "Narrator",
      },
    ],
  });

  assert.deepEqual(draft.bubbles, [
    {
      sourceBubbleId: "bubble-a",
      textEdited: "Edited A",
      order: 0,
      kind: "narration",
      speaker: "Narrator",
    },
    {
      sourceBubbleId: "bubble-b",
      textEdited: "B",
      order: 1,
      kind: "dialogue",
      speaker: undefined,
    },
  ]);
});

test("preserves raw draft text while trimming review payload serialization", () => {
  const initial = createFrameReviewDraft({
    frameId: "frame-001",
    image: "images/001.png",
    ocrFile: "ocr/001.json",
    bubbles: [
      {
        id: "bubble-a",
        text: "A",
        bbox: { x: 10, y: 10, w: 10, h: 10 },
        order: 0,
        confidence: 0.9,
        language: "ja",
      },
    ],
    reviewedBubbles: [],
  });

  const updated = updateReviewBubble(initial, "bubble-a", {
    textEdited: "Narration line ",
    speaker: "Narrator ",
  });

  assert.equal(updated.bubbles[0]?.textEdited, "Narration line ");
  assert.equal(updated.bubbles[0]?.speaker, "Narrator ");
  assert.deepEqual(toFrameReviewPayload(updated), {
    reviewedBubbles: [
      {
        sourceBubbleId: "bubble-a",
        textEdited: "Narration line",
        order: 0,
        kind: "dialogue",
        speaker: "Narrator",
      },
    ],
    skip: false,
  });
});


test("updates and reorders review bubbles before serializing the api payload", () => {
  const initial = createFrameReviewDraft({
    frameId: "frame-001",
    image: "images/001.png",
    ocrFile: "ocr/001.json",
    bubbles: [
      {
        id: "bubble-a",
        text: "A",
        bbox: { x: 10, y: 10, w: 10, h: 10 },
        order: 0,
        confidence: 0.9,
        language: "ja",
      },
      {
        id: "bubble-b",
        text: "B",
        bbox: { x: 20, y: 10, w: 10, h: 10 },
        order: 1,
        confidence: 0.8,
        language: "ja",
      },
    ],
    reviewedBubbles: [],
  });

  const updated = updateReviewBubble(initial, "bubble-a", {
    textEdited: "Narration line",
    kind: "narration",
    speaker: "Narrator",
  });
  const reordered = reorderReviewDraft(updated, "bubble-a", 1);

  assert.deepEqual(toFrameReviewPayload(reordered), {
    reviewedBubbles: [
      {
        sourceBubbleId: "bubble-b",
        textEdited: "B",
        order: 0,
        kind: "dialogue",
      },
      {
        sourceBubbleId: "bubble-a",
        textEdited: "Narration line",
        order: 1,
        kind: "narration",
        speaker: "Narrator",
      },
    ],
    skip: false,
  });
});
