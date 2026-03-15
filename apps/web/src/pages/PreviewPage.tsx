import React from "react";

import { VideoComposition } from "../../../remotion/src/VideoComposition.tsx";
import { buildPreviewState, triggerRenderJobAndPoll } from "../lib/workflow.ts";

const h = React.createElement;

export async function loadPreviewPage({ api, projectId, activeJobId }) {
  const [project, scenes, activeJob] = await Promise.all([
    api.getProject(projectId),
    api.getScenes(projectId),
    activeJobId ? api.getRenderJob(projectId, activeJobId) : Promise.resolve(null),
  ]);

  return {
    project,
    scenes,
    activeJob,
  };
}

export function PreviewPage({ project, scenes, activeJob }) {
  const preview = buildPreviewState({
    counts: project.counts,
    activeJob,
  });

  return h(
    "section",
    { className: "preview-page", "data-page": "preview" },
    h("h2", null, "Preview"),
    h(
      "div",
      {
        "data-preview-container": preview.canMountPlayer ? "mounted" : "empty",
      },
      preview.canMountPlayer
        ? h(VideoComposition, { scenes })
        : h("p", null, "No scenes yet.")
    ),
    h("p", { "data-render-notice": preview.renderNotice.tone }, preview.renderNotice.message),
    h(
      "button",
      {
        type: "button",
        disabled: !preview.renderAction.enabled,
      },
      "Trigger preview render"
    )
  );
}

export async function triggerPreviewRender({
  api,
  projectId,
  kind = "preview",
  onJobUpdate = () => {},
  wait = defaultWait,
}) {
  return triggerRenderJobAndPoll({
    projectId,
    kind,
    createRenderJob: (nextProjectId, payload) => api.createRenderJob(nextProjectId, payload),
    getRenderJob: (nextProjectId, jobId) => api.getRenderJob(nextProjectId, jobId),
    wait,
    onUpdate: onJobUpdate,
  });
}

function defaultWait() {
  return new Promise((resolve) => {
    setTimeout(resolve, 1000);
  });
}
