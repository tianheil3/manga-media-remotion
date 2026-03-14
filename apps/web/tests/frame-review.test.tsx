import test from "node:test";
import assert from "node:assert/strict";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import {
  FrameReviewPage,
  loadFrameReviewPage,
  saveFrameReviewDraft,
} from "../src/pages/FrameReviewPage.tsx";

test("frame review page can load review data for a frame", async () => {
  const page = await loadFrameReviewPage({
    api: {
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
      ],
    },
    projectId: "demo-001",
    frameId: "frame-001",
  });

  assert.equal(page.frame.frameId, "frame-001");
  assert.equal(page.draft.bubbles[0]?.textEdited, "edited line");
});

test("frame review page renders editable bubble content", async () => {
  const page = await loadFrameReviewPage({
    api: {
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
      ],
    },
    projectId: "demo-001",
    frameId: "frame-001",
  });

  const markup = renderToStaticMarkup(
    React.createElement(FrameReviewPage, {
      frame: page.frame,
      draft: page.draft,
    })
  );

  assert.match(markup, /edited line/);
  assert.match(markup, /Hero/);
  assert.match(markup, /dialogue/);
});

test("frame review page persists edited bubble order and kind", async () => {
  const calls = [];
  const savedFrame = await saveFrameReviewDraft({
    api: {
      updateFrameReview: async (projectId, frameId, payload) => {
        calls.push({ projectId, frameId, payload });
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
              textEdited: "narrated line",
              order: 0,
              kind: "narration",
              speaker: "Narrator",
            },
          ],
        };
      },
    },
    projectId: "demo-001",
    frameId: "frame-001",
    draft: {
      frameId: "frame-001",
      bubbles: [
        {
          sourceBubbleId: "bubble-a",
          textEdited: "narrated line",
          order: 0,
          kind: "narration",
          speaker: "Narrator",
        },
      ],
    },
  });

  assert.deepEqual(calls, [
    {
      projectId: "demo-001",
      frameId: "frame-001",
      payload: {
        reviewedBubbles: [
          {
            sourceBubbleId: "bubble-a",
            textEdited: "narrated line",
            order: 0,
            kind: "narration",
            speaker: "Narrator",
          },
        ],
        skip: false,
      },
    },
  ]);
  assert.equal(savedFrame.reviewedBubbles[0]?.kind, "narration");
});
