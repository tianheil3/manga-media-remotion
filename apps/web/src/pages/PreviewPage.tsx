import React from "react";

import { VideoComposition } from "../../../remotion/src/VideoComposition.tsx";
import { buildPreviewState } from "../lib/workflow.ts";

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

export async function triggerPreviewRender({ api, projectId, kind = "preview" }) {
  return api.createRenderJob(projectId, { kind });
}
