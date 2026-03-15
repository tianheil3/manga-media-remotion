const REVIEW_KINDS = new Set(["dialogue", "narration", "sfx", "ignore"]);

export function createFrameReviewDraft(frame) {
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
          kind: "dialogue",
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
  draft,
  sourceBubbleId,
  patch
) {
  const bubbles = draft.bubbles.map((bubble) =>
    bubble.sourceBubbleId === sourceBubbleId ? { ...bubble, ...patch } : bubble
  );

  return {
    ...draft,
    bubbles: sortReviewBubbles(bubbles),
  };
}

export function reorderReviewDraft(
  draft,
  sourceBubbleId,
  targetIndex
) {
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

export function toFrameReviewPayload(draft) {
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

export function validateFrameReviewDraft(draft) {
  const errors = {};
  const bubblesByOrder = new Map();

  for (const bubble of draft.bubbles) {
    const normalized = normalizeReviewBubble(bubble);
    const bubbleErrors = {};

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

export function hasFrameReviewValidationErrors(errors) {
  return Object.keys(errors).length > 0;
}

function normalizeReviewBubble(bubble) {
  return {
    ...bubble,
    textEdited: bubble.textEdited.trim(),
    speaker: bubble.speaker?.trim() ? bubble.speaker.trim() : undefined,
  };
}

function sortReviewBubbles(bubbles) {
  return bubbles.slice().sort((left, right) => {
    if (left.order !== right.order) {
      return left.order - right.order;
    }

    return left.sourceBubbleId.localeCompare(right.sourceBubbleId);
  });
}
