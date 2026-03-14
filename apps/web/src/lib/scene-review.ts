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
  return {
    subtitleText: draft.subtitleText,
    durationMs: draft.durationMs,
    stylePreset: draft.stylePreset,
  };
}
