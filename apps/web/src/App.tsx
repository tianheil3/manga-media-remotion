import React from "react";

import { createFrameReviewDraft } from "./lib/frame-review.ts";
import { createFrameReviewPageActions, FrameReviewPage } from "./pages/FrameReviewPage.tsx";
import { PreviewPage } from "./pages/PreviewPage.tsx";
import { ProjectOverviewPage } from "./pages/ProjectOverview.tsx";
import { loadPreviewPage } from "./pages/PreviewPage.tsx";
import {
  createSceneReviewPageActions,
  loadSceneReviewPage,
  SceneReviewPage,
} from "./pages/SceneReviewPage.tsx";

const h = React.createElement;

export async function loadApp({ api, projectId, activeJobId, frameId }) {
  const [preview, framesResult, sceneReviewResult] = await Promise.all([
    loadPreviewPage({ api, projectId, activeJobId }),
    api
      .getFrames(projectId)
      .then((frames) => ({ ok: true, frames }))
      .catch((error) => ({ ok: false, error })),
    loadSceneReviewPage({ api, projectId })
      .then((sceneReview) => ({ ok: true, sceneReview }))
      .catch((error) => ({ ok: false, error })),
  ]);
  const frames = framesResult.ok ? framesResult.frames : [];
  const resolvedFrame = frameId
    ? frames.find((entry) => entry.frameId === frameId) ?? null
    : frames[0] ?? null;
  const frameReview = framesResult.ok
    ? resolvedFrame
      ? createLoadedFrameReviewState(resolvedFrame)
      : null
    : createFrameReviewErrorState(framesResult.error);
  const sceneReview = sceneReviewResult.ok
    ? sceneReviewResult.sceneReview
    : createSceneReviewErrorState(sceneReviewResult.error);

  return {
    api,
    projectId,
    ...preview,
    frameReview,
    sceneReview,
  };
}

export function App({
  api = null,
  projectId = null,
  project,
  scenes,
  activeJob,
  frameReview: initialFrameReview = null,
  sceneReview: initialSceneReview = null,
  frameReviewActions = null,
  sceneReviewActions = null,
}) {
  const [frameReview, setFrameReview] = React.useState(initialFrameReview);
  const [sceneReview, setSceneReview] = React.useState(initialSceneReview);
  const resolvedProjectId = projectId ?? project?.id ?? null;

  React.useEffect(() => {
    setFrameReview(initialFrameReview);
  }, [initialFrameReview]);

  React.useEffect(() => {
    setSceneReview(initialSceneReview);
  }, [initialSceneReview]);

  const derivedActions =
    api && resolvedProjectId
      ? createAppReviewActions({
          api,
          projectId: resolvedProjectId,
          getFrameReviewState: () => frameReview,
          setFrameReviewState: setFrameReview,
          getSceneReviewState: () => sceneReview,
          setSceneReviewState: setSceneReview,
        })
      : {
          frameReviewActions: null,
          sceneReviewActions: null,
        };

  return h(AppView, {
    project,
    scenes,
    activeJob,
    frameReview,
    sceneReview,
    frameReviewActions: frameReviewActions ?? derivedActions.frameReviewActions,
    sceneReviewActions: sceneReviewActions ?? derivedActions.sceneReviewActions,
  });
}

export function AppView({
  project,
  scenes,
  activeJob,
  frameReview = null,
  sceneReview = null,
  frameReviewActions = null,
  sceneReviewActions = null,
}) {
  return h(
    "main",
    { className: "app-shell", "data-app": "manga-video-review" },
    h("header", null, h("h1", null, project.title)),
    h(ProjectOverviewPage, { project }),
    frameReview ? h(FrameReviewPage, { ...frameReview, actions: frameReviewActions ?? undefined }) : null,
    sceneReview ? h(SceneReviewPage, { ...sceneReview, actions: sceneReviewActions ?? undefined }) : null,
    h(PreviewPage, { project, scenes, activeJob })
  );
}

export function createAppReviewActions({
  api,
  projectId,
  getFrameReviewState,
  setFrameReviewState,
  getSceneReviewState,
  setSceneReviewState,
}) {
  const frameReview = getFrameReviewState();
  const sceneReview = getSceneReviewState();

  return {
    frameReviewActions: frameReview
      && frameReview.frame
      && frameReview.draft
      ? createFrameReviewPageActions({
          api,
          projectId,
          frameId: frameReview.frame.frameId,
          getState: getFrameReviewState,
          onStateChange: setFrameReviewState,
        })
      : null,
    sceneReviewActions: sceneReview
      ? createSceneReviewPageActions({
          api,
          projectId,
          getState: getSceneReviewState,
          onStateChange: setSceneReviewState,
        })
      : null,
  };
}

function createLoadedFrameReviewState(frame) {
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

function createFrameReviewErrorState(error) {
  return {
    frame: null,
    draft: null,
    isLoading: false,
    isSaving: false,
    errorMessage: error instanceof Error ? error.message : String(error),
    saveMessage: null,
    validationErrors: {},
  };
}

function createSceneReviewErrorState(error) {
  return {
    scenes: [],
    drafts: [],
    isLoading: false,
    savingSceneIds: [],
    errorMessage: error instanceof Error ? error.message : String(error),
    errorMessages: {},
    saveMessages: {},
    validationErrors: {},
  };
}
