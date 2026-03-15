import {
  createFrameReviewDraft,
  hasFrameReviewValidationErrors,
  toFrameReviewPayload,
  updateReviewBubble,
  validateFrameReviewDraft,
} from "../lib/frame-review.ts";
import { h } from "../lib/runtime-elements.ts";

export function createLoadingFrameReviewPageState() {
  return {
    frame: null,
    draft: null,
    isLoading: true,
    isSaving: false,
    errorMessage: null,
    saveMessage: null,
    validationErrors: {},
  };
}

export async function loadFrameReviewPage({ api, projectId, frameId }) {
  const frames = await api.getFrames(projectId);
  const frame = frames.find((entry) => entry.frameId === frameId);
  if (!frame) {
    throw new Error(`Frame ${frameId} not found`);
  }

  return {
    frame,
    draft: createFrameReviewDraft(frame),
    isLoading: false,
    isSaving: false,
    errorMessage: null,
    saveMessage: null,
    validationErrors: {},
  };
}

export async function saveFrameReviewDraft({ api, projectId, frameId, draft }) {
  return api.updateFrameReview(projectId, frameId, toFrameReviewPayload(draft));
}

export function createFrameReviewPageActions({
  api,
  projectId,
  frameId,
  getState,
  onStateChange,
}) {
  return {
    onBubbleTextEditedChange(sourceBubbleId, value) {
      const nextState = editFrameReviewBubble(getState(), sourceBubbleId, {
        textEdited: value,
      });
      onStateChange(nextState);
      return nextState;
    },
    onBubbleOrderChange(sourceBubbleId, value) {
      const nextState = editFrameReviewBubble(getState(), sourceBubbleId, {
        order: Number.parseInt(value, 10),
      });
      onStateChange(nextState);
      return nextState;
    },
    onBubbleKindChange(sourceBubbleId, value) {
      const nextState = editFrameReviewBubble(getState(), sourceBubbleId, {
        kind: value,
      });
      onStateChange(nextState);
      return nextState;
    },
    onBubbleSpeakerChange(sourceBubbleId, value) {
      const nextState = editFrameReviewBubble(getState(), sourceBubbleId, {
        speaker: value,
      });
      onStateChange(nextState);
      return nextState;
    },
    async onSave() {
      const saveAttempt = startFrameReviewSave({
        api,
        projectId,
        frameId,
        state: getState(),
      });
      onStateChange(saveAttempt.state);
      if (!saveAttempt.completion) {
        return saveAttempt.state;
      }

      const completedState = await saveAttempt.completion;
      const mergedState = mergeCompletedFrameReviewSave({
        latestState: getState(),
        submittedDraft: saveAttempt.state.draft,
        completedState,
      });
      onStateChange(mergedState);
      return mergedState;
    },
  };
}

export function editFrameReviewBubble(
  state,
  sourceBubbleId,
  patch,
) {
  if (!state.draft) {
    return state;
  }

  const draft = updateReviewBubble(state.draft, sourceBubbleId, patch);

  return {
    ...state,
    draft,
    errorMessage: null,
    saveMessage: null,
    validationErrors: validateFrameReviewDraft(draft),
  };
}

export function startFrameReviewSave({ api, projectId, frameId, state }) {
  if (!state.draft) {
    return {
      state: {
        ...state,
        errorMessage: "No frame review is loaded.",
      },
      completion: null,
    };
  }

  const validationErrors = validateFrameReviewDraft(state.draft);
  if (hasFrameReviewValidationErrors(validationErrors)) {
    return {
      state: {
        ...state,
        validationErrors,
        errorMessage: "Fix validation errors before saving.",
      },
      completion: null,
    };
  }

  const nextState = {
    ...state,
    isSaving: true,
    errorMessage: null,
    saveMessage: null,
    validationErrors: {},
  };

  return {
    state: nextState,
    completion: saveFrameReviewDraft({
      api,
      projectId,
      frameId,
      draft: state.draft,
    })
      .then((frame) => ({
        frame,
        draft: createFrameReviewDraft(frame),
        isLoading: false,
        isSaving: false,
        errorMessage: null,
        saveMessage: "Frame review saved.",
        validationErrors: {},
      }))
      .catch((error) => ({
        ...nextState,
        isSaving: false,
        errorMessage: error instanceof Error ? error.message : String(error),
        saveMessage: null,
      })),
  };
}

function mergeCompletedFrameReviewSave({
  latestState,
  submittedDraft,
  completedState,
}) {
  if (completedState.errorMessage) {
    return {
      ...latestState,
      isLoading: false,
      isSaving: false,
      errorMessage: completedState.errorMessage,
      saveMessage: null,
    };
  }

  const shouldRefreshDraft =
    latestState.draft &&
    submittedDraft &&
    areFrameReviewDraftsEquivalent(latestState.draft, submittedDraft);

  return {
    ...latestState,
    frame: completedState.frame,
    draft: shouldRefreshDraft ? completedState.draft : latestState.draft,
    isLoading: false,
    isSaving: false,
    errorMessage: null,
    saveMessage: completedState.saveMessage,
    validationErrors: shouldRefreshDraft ? {} : latestState.validationErrors,
  };
}

function areFrameReviewDraftsEquivalent(left, right) {
  return JSON.stringify(left) === JSON.stringify(right);
}

export function FrameReviewPage({
  frame,
  draft,
  isLoading = false,
  isSaving = false,
  errorMessage = null,
  saveMessage = null,
  validationErrors = {},
  actions = {},
}) {
  if (isLoading) {
    return h("section", { className: "frame-review-page", "data-page": "frame-review" }, h("p", { "data-review-state": "loading" }, "Loading frame review..."));
  }

  if (errorMessage && (!frame || !draft)) {
    return h(
      "section",
      { className: "frame-review-page", "data-page": "frame-review" },
      h("h2", null, "Frame review"),
      h("p", { "data-review-state": "error" }, errorMessage)
    );
  }

  if (!frame || !draft) {
    return h("section", { className: "frame-review-page", "data-page": "frame-review" }, h("p", { "data-review-state": "empty" }, "Frame review unavailable."));
  }

  return h(
    "section",
    { className: "frame-review-page", "data-page": "frame-review" },
    h("h2", null, "Frame review"),
    h("p", null, frame.frameId),
    isSaving ? h("p", { "data-review-state": "saving" }, "Saving frame review...") : null,
    errorMessage ? h("p", { "data-review-state": "error" }, errorMessage) : null,
    saveMessage ? h("p", { "data-review-state": "saved" }, saveMessage) : null,
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
          h("label", null, "Edited text"),
          h("textarea", {
            name: `textEdited-${bubble.sourceBubbleId}`,
            value: bubble.textEdited,
            readOnly: actions.onBubbleTextEditedChange ? undefined : true,
            onChange: actions.onBubbleTextEditedChange
              ? (event) =>
                  actions.onBubbleTextEditedChange(
                    bubble.sourceBubbleId,
                    event.target.value
                  )
              : undefined,
          }),
          validationErrors[bubble.sourceBubbleId]?.textEdited
            ? h("p", { "data-error-field": "textEdited" }, validationErrors[bubble.sourceBubbleId].textEdited)
            : null,
          h("label", null, "Order"),
          h("input", {
            type: "number",
            name: `order-${bubble.sourceBubbleId}`,
            value: toNumericInputValue(bubble.order),
            readOnly: actions.onBubbleOrderChange ? undefined : true,
            onChange: actions.onBubbleOrderChange
              ? (event) =>
                  actions.onBubbleOrderChange(
                    bubble.sourceBubbleId,
                    event.target.value
                  )
              : undefined,
          }),
          validationErrors[bubble.sourceBubbleId]?.order
            ? h("p", { "data-error-field": "order" }, validationErrors[bubble.sourceBubbleId].order)
            : null,
          h("label", null, "Kind"),
          h("select", {
            name: `kind-${bubble.sourceBubbleId}`,
            value: bubble.kind,
            disabled: actions.onBubbleKindChange ? undefined : true,
            onChange: actions.onBubbleKindChange
              ? (event) =>
                  actions.onBubbleKindChange(
                    bubble.sourceBubbleId,
                    event.target.value
                  )
              : undefined,
          },
          h("option", { value: "dialogue" }, "dialogue"),
          h("option", { value: "narration" }, "narration"),
          h("option", { value: "sfx" }, "sfx"),
          h("option", { value: "ignore" }, "ignore")),
          validationErrors[bubble.sourceBubbleId]?.kind
            ? h("p", { "data-error-field": "kind" }, validationErrors[bubble.sourceBubbleId].kind)
            : null,
          h("label", null, "Speaker"),
          h("input", {
            type: "text",
            name: `speaker-${bubble.sourceBubbleId}`,
            value: bubble.speaker ?? "",
            readOnly: actions.onBubbleSpeakerChange ? undefined : true,
            onChange: actions.onBubbleSpeakerChange
              ? (event) =>
                  actions.onBubbleSpeakerChange(
                    bubble.sourceBubbleId,
                    event.target.value
                  )
              : undefined,
          }),
          validationErrors[bubble.sourceBubbleId]?.speaker
            ? h("p", { "data-error-field": "speaker" }, validationErrors[bubble.sourceBubbleId].speaker)
            : null
        )
      )
    ),
    h(
      "button",
      {
        type: "button",
        disabled: isSaving,
        onClick: actions.onSave ? () => actions.onSave() : undefined,
      },
      "Save frame review"
    )
  );
}

function toNumericInputValue(value) {
  return Number.isFinite(value) ? value : "";
}
