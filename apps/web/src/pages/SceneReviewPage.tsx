import React from "react";

import { createSceneReviewDraft, toSceneUpdatePayload } from "../lib/scene-review.ts";

const h = React.createElement;

export async function loadSceneReviewPage({ api, projectId }) {
  const scenes = await api.getSceneReview(projectId);

  return {
    scenes,
    drafts: scenes.map((scene) => createSceneReviewDraft(scene)),
  };
}

export async function saveSceneReviewDraft({ api, projectId, draft }) {
  return api.updateScene(projectId, draft.id, toSceneUpdatePayload(draft));
}

export function SceneReviewPage({ scenes, drafts }) {
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
          draft ? h("p", null, draft.subtitleText ?? "No subtitle") : null,
          draft ? h("p", null, `${draft.durationMs}ms`) : null,
          draft ? h("p", null, draft.stylePreset) : null,
          draft
            ? h(
                "ul",
                null,
                ...draft.audioActions.map((action) =>
                  h("li", { key: action.key }, `${action.label}: ${action.path}`)
                )
              )
            : null
        );
      })
    )
  );
}
