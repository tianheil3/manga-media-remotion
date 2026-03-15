import {
  createSceneReviewDraft,
  hasSceneReviewValidationErrors,
  toSceneUpdatePayload,
  updateSceneReviewDraft as updateSceneDraft,
  validateSceneReviewDraft,
} from "../lib/scene-review.ts";
import { h } from "../lib/runtime-elements.ts";

export function createLoadingSceneReviewPageState() {
  return {
    scenes: [],
    drafts: [],
    isLoading: true,
    savingSceneIds: [],
    errorMessage: null,
    errorMessages: {},
    saveMessages: {},
    validationErrors: {},
  };
}

export async function loadSceneReviewPage({ api, projectId }) {
  const scenes = await api.getSceneReview(projectId);

  return {
    scenes,
    drafts: scenes.map((scene) => createSceneReviewDraft(scene)),
    isLoading: false,
    savingSceneIds: [],
    errorMessage: null,
    errorMessages: {},
    saveMessages: {},
    validationErrors: {},
  };
}

export async function saveSceneReviewDraft({ api, projectId, draft }) {
  return api.updateScene(projectId, draft.id, toSceneUpdatePayload(draft));
}

export function createSceneReviewPageActions({ api, projectId, getState, onStateChange }) {
  return {
    onSubtitleTextChange(sceneId, value) {
      const nextState = updateSceneReviewDraft(getState(), sceneId, {
        subtitleText: value,
      });
      onStateChange(nextState);
      return nextState;
    },
    onDurationMsChange(sceneId, value) {
      const nextState = updateSceneReviewDraft(getState(), sceneId, {
        durationMs: Number.parseInt(value, 10),
      });
      onStateChange(nextState);
      return nextState;
    },
    onStylePresetChange(sceneId, value) {
      const nextState = updateSceneReviewDraft(getState(), sceneId, {
        stylePreset: value,
      });
      onStateChange(nextState);
      return nextState;
    },
    async onSaveScene(sceneId) {
      const saveAttempt = startSceneReviewSave({
        api,
        projectId,
        sceneId,
        state: getState(),
      });
      onStateChange(saveAttempt.state);
      if (!saveAttempt.completion) {
        return saveAttempt.state;
      }

      const completedState = await saveAttempt.completion;
      const mergedState = mergeCompletedSceneReviewSave({
        latestState: getState(),
        sceneId,
        submittedDraft: saveAttempt.state.drafts.find((entry) => entry.id === sceneId),
        completedState,
      });
      onStateChange(mergedState);
      return mergedState;
    },
  };
}

export function updateSceneReviewDraft(state, sceneId, patch) {
  const drafts = state.drafts.map((draft) =>
    draft.id === sceneId ? updateSceneDraft(draft, patch) : draft
  );
  const draft = drafts.find((entry) => entry.id === sceneId);

  return {
    ...state,
    drafts,
    errorMessages: omitKey(state.errorMessages, sceneId),
    saveMessages: omitKey(state.saveMessages, sceneId),
    validationErrors: draft
      ? {
          ...state.validationErrors,
          [sceneId]: validateSceneReviewDraft(draft),
        }
      : state.validationErrors,
  };
}

export function startSceneReviewSave({ api, projectId, sceneId, state }) {
  const draft = state.drafts.find((entry) => entry.id === sceneId);
  if (!draft) {
    return {
      state: {
        ...state,
        errorMessages: {
          ...state.errorMessages,
          [sceneId]: "Scene review draft not found.",
        },
      },
      completion: null,
    };
  }

  const validationErrors = validateSceneReviewDraft(draft);
  if (hasSceneReviewValidationErrors(validationErrors)) {
    return {
      state: {
        ...state,
        errorMessages: {
          ...state.errorMessages,
          [sceneId]: "Fix validation errors before saving.",
        },
        validationErrors: {
          ...state.validationErrors,
          [sceneId]: validationErrors,
        },
      },
      completion: null,
    };
  }

  const nextState = {
    ...state,
    savingSceneIds: Array.from(new Set([...state.savingSceneIds, sceneId])),
    errorMessages: omitKey(state.errorMessages, sceneId),
    saveMessages: omitKey(state.saveMessages, sceneId),
    validationErrors: omitKey(state.validationErrors, sceneId),
  };

  return {
    state: nextState,
    completion: saveSceneReviewDraft({
      api,
      projectId,
      draft,
    })
      .then((scene) => ({
        ...nextState,
        scenes: nextState.scenes.map((entry) => (entry.id === scene.id ? scene : entry)),
        drafts: nextState.drafts.map((entry) =>
          entry.id === scene.id ? createSceneReviewDraft(scene) : entry
        ),
        savingSceneIds: nextState.savingSceneIds.filter((entry) => entry !== scene.id),
        saveMessages: {
          ...nextState.saveMessages,
          [scene.id]: "Scene review saved.",
        },
      }))
      .catch((error) => ({
        ...nextState,
        savingSceneIds: nextState.savingSceneIds.filter((entry) => entry !== sceneId),
        errorMessages: {
          ...nextState.errorMessages,
          [sceneId]: error instanceof Error ? error.message : String(error),
        },
      })),
  };
}

function mergeCompletedSceneReviewSave({
  latestState,
  sceneId,
  submittedDraft,
  completedState,
}) {
  const errorMessage = completedState.errorMessages[sceneId];
  if (errorMessage) {
    return {
      ...latestState,
      savingSceneIds: latestState.savingSceneIds.filter((entry) => entry !== sceneId),
      errorMessages: {
        ...omitKey(latestState.errorMessages, sceneId),
        [sceneId]: errorMessage,
      },
      saveMessages: omitKey(latestState.saveMessages, sceneId),
    };
  }

  const savedScene = completedState.scenes.find((entry) => entry.id === sceneId);
  const savedDraft = completedState.drafts.find((entry) => entry.id === sceneId);
  const latestDraft = latestState.drafts.find((entry) => entry.id === sceneId);
  const shouldRefreshDraft =
    savedDraft &&
    latestDraft &&
    submittedDraft &&
    areSceneReviewDraftsEquivalent(latestDraft, submittedDraft);

  return {
    ...latestState,
    scenes: savedScene
      ? latestState.scenes.map((entry) => (entry.id === sceneId ? savedScene : entry))
      : latestState.scenes,
    drafts:
      savedDraft && shouldRefreshDraft
        ? latestState.drafts.map((entry) => (entry.id === sceneId ? savedDraft : entry))
        : latestState.drafts,
    savingSceneIds: latestState.savingSceneIds.filter((entry) => entry !== sceneId),
    errorMessages: omitKey(latestState.errorMessages, sceneId),
    saveMessages: {
      ...omitKey(latestState.saveMessages, sceneId),
      [sceneId]: completedState.saveMessages[sceneId] ?? "Scene review saved.",
    },
    validationErrors: shouldRefreshDraft
      ? omitKey(latestState.validationErrors, sceneId)
      : latestState.validationErrors,
  };
}

function areSceneReviewDraftsEquivalent(left, right) {
  return JSON.stringify(left) === JSON.stringify(right);
}

export function SceneReviewPage({
  scenes,
  drafts,
  isLoading = false,
  savingSceneIds = [],
  errorMessage = null,
  errorMessages = {},
  saveMessages = {},
  validationErrors = {},
  actions = {},
}) {
  if (isLoading) {
    return h("section", { className: "scene-review-page", "data-page": "scene-review" }, h("p", { "data-review-state": "loading" }, "Loading scene review..."));
  }

  if (errorMessage) {
    return h(
      "section",
      { className: "scene-review-page", "data-page": "scene-review" },
      h("h2", null, "Scene review"),
      h("p", { "data-review-state": "error" }, errorMessage)
    );
  }

  const draftById = new Map(drafts.map((draft) => [draft.id, draft]));

  return h(
    "section",
    { className: "scene-review-page", "data-page": "scene-review" },
    h("h2", null, "Scene review"),
    h(
      "ol",
      { "data-scene-review-list": "true" },
      ...scenes.map((scene) => {
        const draft = draftById.get(scene.id);
        return h(
          "li",
          { key: scene.id, "data-scene-id": scene.id },
          h("strong", null, scene.id),
          savingSceneIds.includes(scene.id)
            ? h("p", { "data-review-state": "saving" }, "Saving scene review...")
            : null,
          errorMessages[scene.id]
            ? h("p", { "data-review-state": "error" }, errorMessages[scene.id])
            : null,
          saveMessages[scene.id]
            ? h("p", { "data-review-state": "saved" }, saveMessages[scene.id])
            : null,
          draft
            ? h("textarea", {
                name: `subtitleText-${scene.id}`,
                value: draft.subtitleText ?? "",
                readOnly: actions.onSubtitleTextChange ? undefined : true,
                onChange: actions.onSubtitleTextChange
                  ? (event) =>
                      actions.onSubtitleTextChange(scene.id, event.target.value)
                  : undefined,
              })
            : null,
          validationErrors[scene.id]?.subtitleText
            ? h("p", { "data-error-field": "subtitleText" }, validationErrors[scene.id].subtitleText)
            : null,
          draft
            ? h("input", {
                type: "number",
                name: `durationMs-${scene.id}`,
                value: toNumericInputValue(draft.durationMs),
                readOnly: actions.onDurationMsChange ? undefined : true,
                onChange: actions.onDurationMsChange
                  ? (event) =>
                      actions.onDurationMsChange(scene.id, event.target.value)
                  : undefined,
              })
            : null,
          validationErrors[scene.id]?.durationMs
            ? h("p", { "data-error-field": "durationMs" }, validationErrors[scene.id].durationMs)
            : null,
          draft
            ? h("select", {
                name: `stylePreset-${scene.id}`,
                value: draft.stylePreset,
                disabled: actions.onStylePresetChange ? undefined : true,
                onChange: actions.onStylePresetChange
                  ? (event) =>
                      actions.onStylePresetChange(scene.id, event.target.value)
                  : undefined,
              },
              h("option", { value: "default" }, "default"),
              h("option", { value: "fast" }, "fast"),
              h("option", { value: "dramatic" }, "dramatic"),
              h("option", { value: "calm" }, "calm"))
            : null,
          validationErrors[scene.id]?.stylePreset
            ? h("p", { "data-error-field": "stylePreset" }, validationErrors[scene.id].stylePreset)
            : null,
          draft
            ? h(
                "ul",
                null,
                ...draft.audioActions.map((action) =>
                  h("li", { key: action.key }, `${action.label}: ${action.path}`)
                )
              )
            : null,
          h(
            "button",
            {
              type: "button",
              disabled: savingSceneIds.includes(scene.id),
              onClick: actions.onSaveScene
                ? () => actions.onSaveScene(scene.id)
                : undefined,
            },
            "Save scene"
          )
        );
      })
    )
  );
}

function omitKey(record, key) {
  const { [key]: _removed, ...rest } = record;
  return rest;
}

function toNumericInputValue(value) {
  return Number.isFinite(value) ? value : "";
}
