import React from "react";

import { createFrameReviewDraft, toFrameReviewPayload } from "../lib/frame-review.ts";

const h = React.createElement;

export async function loadFrameReviewPage({ api, projectId, frameId }) {
  const frames = await api.getFrames(projectId);
  const frame = frames.find((entry) => entry.frameId === frameId);
  if (!frame) {
    throw new Error(`Frame ${frameId} not found`);
  }

  return {
    frame,
    draft: createFrameReviewDraft(frame),
  };
}

export async function saveFrameReviewDraft({ api, projectId, frameId, draft }) {
  return api.updateFrameReview(projectId, frameId, toFrameReviewPayload(draft));
}

export function FrameReviewPage({ frame, draft }) {
  return h(
    "section",
    { className: "frame-review-page", "data-page": "frame-review" },
    h("h2", null, "Frame review"),
    h("p", null, frame.frameId),
    h(
      "ol",
      { "data-bubble-list": "true" },
      ...draft.bubbles.map((bubble) =>
        h(
          "li",
          {
            key: bubble.sourceBubbleId,
            "data-bubble-id": bubble.sourceBubbleId,
            "data-bubble-kind": bubble.kind,
          },
          h("span", null, bubble.textEdited),
          " ",
          h("span", null, bubble.kind),
          bubble.speaker ? h("span", null, ` ${bubble.speaker}`) : null
        )
      )
    )
  );
}
