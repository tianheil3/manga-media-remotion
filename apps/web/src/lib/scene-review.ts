import type { SceneReview, SceneUpdate } from "@manga/schema";

export type SceneReviewDraft = {
  id: string;
  subtitleText: string | null | undefined;
  durationMs: number;
  stylePreset: SceneUpdate["stylePreset"];
  audioActions: Array<{
    key: "replace-audio" | "skip-recording";
    label: string;
    path: string;
  }>;
};

export type SceneReviewValidationErrors = Partial<
  Record<"subtitleText" | "durationMs" | "stylePreset", string>
>;

const STYLE_PRESETS = new Set(["default", "fast", "dramatic", "calm"]);

export function createSceneReviewDraft(scene: SceneReview): SceneReviewDraft {
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
  draft: SceneReviewDraft,
  patch: Partial<Pick<SceneReviewDraft, "subtitleText" | "durationMs" | "stylePreset">>
): SceneReviewDraft {
  return {
    ...draft,
    ...patch,
  };
}

export function toSceneUpdatePayload(draft: SceneReviewDraft): SceneUpdate {
  const normalized = normalizeSceneReviewDraft(draft);

  return {
    subtitleText: normalized.subtitleText,
    durationMs: normalized.durationMs,
    stylePreset: normalized.stylePreset,
  };
}

export function validateSceneReviewDraft(draft: SceneReviewDraft): SceneReviewValidationErrors {
  const normalized = normalizeSceneReviewDraft(draft);
  const errors: SceneReviewValidationErrors = {};

  if (!Number.isInteger(normalized.durationMs) || normalized.durationMs <= 0) {
    errors.durationMs = "Duration must be a positive integer.";
  }

  if (!STYLE_PRESETS.has(normalized.stylePreset)) {
    errors.stylePreset = "Style preset is invalid.";
  }

  return errors;
}

export function hasSceneReviewValidationErrors(errors: SceneReviewValidationErrors): boolean {
  return Object.keys(errors).length > 0;
}

function normalizeSceneReviewDraft(draft: SceneReviewDraft): SceneReviewDraft {
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
