const STYLE_PRESETS = new Set(["default", "fast", "dramatic", "calm"]);

export function createSceneReviewDraft(scene) {
  return {
    id: scene.id,
    subtitleText: scene.subtitleText,
    durationMs: scene.durationMs,
    stylePreset: scene.stylePreset,
    audioActions: scene.audioMetadata
      ? [
          {
            key: "replace-audio",
            label: "Replace audio",
            path: scene.audioMetadata.replaceAudioPath,
          },
          {
            key: "skip-recording",
            label: "Skip recording",
            path: scene.audioMetadata.skipRecordingPath,
          },
        ]
      : [],
  };
}

export function updateSceneReviewDraft(
  draft,
  patch
) {
  return {
    ...draft,
    ...patch,
  };
}

export function toSceneUpdatePayload(draft) {
  const normalized = normalizeSceneReviewDraft(draft);

  return {
    subtitleText: normalized.subtitleText,
    durationMs: normalized.durationMs,
    stylePreset: normalized.stylePreset,
  };
}

export function validateSceneReviewDraft(draft) {
  const normalized = normalizeSceneReviewDraft(draft);
  const errors = {};

  if (!Number.isInteger(normalized.durationMs) || normalized.durationMs <= 0) {
    errors.durationMs = "Duration must be a positive integer.";
  }

  if (!STYLE_PRESETS.has(normalized.stylePreset)) {
    errors.stylePreset = "Style preset is invalid.";
  }

  return errors;
}

export function hasSceneReviewValidationErrors(errors) {
  return Object.keys(errors).length > 0;
}

function normalizeSceneReviewDraft(draft) {
  const subtitleText =
    typeof draft.subtitleText === "string" && draft.subtitleText.trim().length === 0
      ? null
      : draft.subtitleText;

  return {
    ...draft,
    subtitleText,
    durationMs: Math.trunc(draft.durationMs),
  };
}
