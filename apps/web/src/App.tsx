import React from "react";

import { createFrameReviewDraft } from "./lib/frame-review.ts";
import { FrameReviewPage } from "./pages/FrameReviewPage.tsx";
import { PreviewPage } from "./pages/PreviewPage.tsx";
import { ProjectOverviewPage } from "./pages/ProjectOverview.tsx";
import { loadPreviewPage } from "./pages/PreviewPage.tsx";
import { SceneReviewPage, loadSceneReviewPage } from "./pages/SceneReviewPage.tsx";

const h = React.createElement;

export async function loadApp({ api, projectId, activeJobId, frameId }) {
  const [preview, frames, sceneReview] = await Promise.all([
    loadPreviewPage({ api, projectId, activeJobId }),
    api.getFrames(projectId),
    loadSceneReviewPage({ api, projectId }),
  ]);
  const resolvedFrameId = frameId ?? frames[0]?.frameId;
  const frame = resolvedFrameId ? frames.find((entry) => entry.frameId === resolvedFrameId) ?? null : null;

  return {
    ...preview,
    frameReview: frame ? { frame, draft: createFrameReviewDraft(frame) } : null,
    sceneReview,
  };
}

export function App({ project, scenes, activeJob, frameReview = null, sceneReview = null }) {
  return h(
    "main",
    { className: "app-shell", "data-app": "manga-video-review" },
    h("header", null, h("h1", null, project.title)),
    h(ProjectOverviewPage, { project }),
    frameReview ? h(FrameReviewPage, frameReview) : null,
    sceneReview ? h(SceneReviewPage, sceneReview) : null,
    h(PreviewPage, { project, scenes, activeJob })
  );
}
