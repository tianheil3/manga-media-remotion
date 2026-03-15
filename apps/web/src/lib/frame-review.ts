import type { Frame, FrameReviewUpdate, ReviewBubbleInput } from "@manga/schema";

export type FrameReviewDraft = {
  frameId: string;
  bubbles: ReviewBubbleDraft[];
};

export type ReviewBubbleDraft = ReviewBubbleInput;
export type ReviewBubbleValidationErrors = Partial<
  Record<"textEdited" | "order" | "kind" | "speaker", string>
>;
export type FrameReviewValidationErrors = Record<string, ReviewBubbleValidationErrors>;

const REVIEW_KINDS = new Set(["dialogue", "narration", "sfx", "ignore"]);

export function createFrameReviewDraft(frame: Frame): FrameReviewDraft {
  const reviewedBySourceBubbleId = new Map(
    frame.reviewedBubbles.map((bubble) => [bubble.sourceBubbleId, bubble])
  );
  const bubbles = [
    ...frame.bubbles.map((bubble) => {
      const reviewedBubble = reviewedBySourceBubbleId.get(bubble.id);
      if (reviewedBubble) {
        return {
          sourceBubbleId: reviewedBubble.sourceBubbleId,
          textEdited: reviewedBubble.textEdited,
          order: reviewedBubble.order,
          kind: reviewedBubble.kind,
          speaker: reviewedBubble.speaker,
        };
      }

      return {
        sourceBubbleId: bubble.id,
        textEdited: bubble.text,
        order: bubble.order,
        kind: "dialogue" as const,
        speaker: undefined,
      };
    }),
    ...frame.reviewedBubbles
      .filter((bubble) => !frame.bubbles.some((entry) => entry.id === bubble.sourceBubbleId))
      .map((bubble) => ({
        sourceBubbleId: bubble.sourceBubbleId,
        textEdited: bubble.textEdited,
        order: bubble.order,
        kind: bubble.kind,
        speaker: bubble.speaker,
      })),
  ].sort((left, right) => left.order - right.order);

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
  const bubbles = draft.bubbles.map((bubble) =>
    bubble.sourceBubbleId === sourceBubbleId ? { ...bubble, ...patch } : bubble
  );

  return {
    ...draft,
    bubbles: sortReviewBubbles(bubbles),
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
    bubbles: sortReviewBubbles(
      reordered.map((bubble, index) => ({
        ...bubble,
        order: index,
      }))
    ),
  };
}

export function toFrameReviewPayload(draft: FrameReviewDraft): FrameReviewUpdate {
  return {
    reviewedBubbles: draft.bubbles
      .slice()
      .sort((left, right) => left.order - right.order)
      .map((bubble) => normalizeReviewBubble(bubble))
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

export function validateFrameReviewDraft(draft: FrameReviewDraft): FrameReviewValidationErrors {
  const errors: FrameReviewValidationErrors = {};
  const bubblesByOrder = new Map<number, string[]>();

  for (const bubble of draft.bubbles) {
    const normalized = normalizeReviewBubble(bubble);
    const bubbleErrors: ReviewBubbleValidationErrors = {};

    if (normalized.kind !== "ignore" && normalized.textEdited.length === 0) {
      bubbleErrors.textEdited = "Edited text is required.";
    }

    if (!Number.isInteger(normalized.order) || normalized.order < 0) {
      bubbleErrors.order = "Order must be a non-negative integer.";
    } else {
      const matches = bubblesByOrder.get(normalized.order) ?? [];
      matches.push(normalized.sourceBubbleId);
      bubblesByOrder.set(normalized.order, matches);
    }

    if (!REVIEW_KINDS.has(normalized.kind)) {
      bubbleErrors.kind = "Kind is invalid.";
    }

    if (Object.keys(bubbleErrors).length > 0) {
      errors[bubble.sourceBubbleId] = bubbleErrors;
    }
  }

  for (const [, bubbleIds] of bubblesByOrder) {
    if (bubbleIds.length < 2) {
      continue;
    }

    for (const bubbleId of bubbleIds) {
      errors[bubbleId] = {
        ...errors[bubbleId],
        order: "Each bubble order must be unique.",
      };
    }
  }

  return errors;
}

export function hasFrameReviewValidationErrors(errors: FrameReviewValidationErrors): boolean {
  return Object.keys(errors).length > 0;
}

function normalizeReviewBubble(bubble: ReviewBubbleDraft): ReviewBubbleDraft {
  return {
    ...bubble,
    textEdited: bubble.textEdited.trim(),
    speaker: bubble.speaker?.trim() ? bubble.speaker.trim() : undefined,
  };
}

function sortReviewBubbles(bubbles: ReviewBubbleDraft[]): ReviewBubbleDraft[] {
  return bubbles.slice().sort((left, right) => {
    if (left.order !== right.order) {
      return left.order - right.order;
    }

    return left.sourceBubbleId.localeCompare(right.sourceBubbleId);
  });
}
