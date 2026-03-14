import type { Frame, FrameReviewUpdate, ReviewBubbleInput } from "@manga/schema";

export type FrameReviewDraft = {
  frameId: string;
  bubbles: ReviewBubbleDraft[];
};

export type ReviewBubbleDraft = ReviewBubbleInput;

export function createFrameReviewDraft(frame: Frame): FrameReviewDraft {
  const bubbles =
    frame.reviewedBubbles.length > 0
      ? frame.reviewedBubbles
          .map((bubble) => ({
            sourceBubbleId: bubble.sourceBubbleId,
            textEdited: bubble.textEdited,
            order: bubble.order,
            kind: bubble.kind,
            speaker: bubble.speaker,
          }))
          .sort((left, right) => left.order - right.order)
      : frame.bubbles
          .map((bubble) => ({
            sourceBubbleId: bubble.id,
            textEdited: bubble.text,
            order: bubble.order,
            kind: "dialogue" as const,
            speaker: undefined,
          }))
          .sort((left, right) => left.order - right.order);

  return {
    frameId: frame.frameId,
    bubbles,
  };
}

export function updateReviewBubble(
  draft: FrameReviewDraft,
  sourceBubbleId: string,
  patch: Partial<ReviewBubbleDraft>
): FrameReviewDraft {
  return {
    ...draft,
    bubbles: draft.bubbles.map((bubble) =>
      bubble.sourceBubbleId === sourceBubbleId ? { ...bubble, ...patch } : bubble
    ),
  };
}

export function reorderReviewDraft(
  draft: FrameReviewDraft,
  sourceBubbleId: string,
  targetIndex: number
): FrameReviewDraft {
  const currentIndex = draft.bubbles.findIndex(
    (bubble) => bubble.sourceBubbleId === sourceBubbleId
  );
  if (currentIndex === -1) {
    return draft;
  }

  const reordered = [...draft.bubbles];
  const [movedBubble] = reordered.splice(currentIndex, 1);
  reordered.splice(targetIndex, 0, movedBubble);

  return {
    ...draft,
    bubbles: reordered.map((bubble, index) => ({
      ...bubble,
      order: index,
    })),
  };
}

export function toFrameReviewPayload(draft: FrameReviewDraft): FrameReviewUpdate {
  return {
    reviewedBubbles: draft.bubbles
      .slice()
      .sort((left, right) => left.order - right.order)
      .map((bubble) => ({
        sourceBubbleId: bubble.sourceBubbleId,
        textEdited: bubble.textEdited,
        order: bubble.order,
        kind: bubble.kind,
        ...(bubble.speaker ? { speaker: bubble.speaker } : {}),
      })),
    skip: false,
  };
}
