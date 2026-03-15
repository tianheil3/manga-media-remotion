const WORKFLOW_STAGES = [
  { key: "images", label: "Images", actionLabel: "Import images" },
  { key: "ocr", label: "OCR", actionLabel: "Run OCR" },
  { key: "review", label: "Review", actionLabel: "Review text" },
  { key: "translation", label: "Translation", actionLabel: "Run translation" },
  { key: "voice", label: "Voice", actionLabel: "Generate voice" },
  { key: "scenes", label: "Scenes", actionLabel: "Build scenes" },
] ;

export function buildProjectWorkflowSummary(project) {
  const sections = WORKFLOW_STAGES.map((stage) => ({
    ...stage,
    done: project.progress[stage.key],
    count: stageCount(stage.key, project.counts),
  }));

  return {
    sections,
    nextStage:
      sections.find((section) => !section.done) ?? {
        key: "complete",
        label: "Complete",
        actionLabel: "Open preview",
        done: true,
        count: project.counts.scenes,
      },
  };
}

export function buildPreviewState(input) {
  const canMountPlayer = input.counts.scenes > 0;
  const activeJob = input.activeJob ?? null;

  return {
    canMountPlayer,
    renderAction: {
      enabled: activeJob === null || isTerminalStatus(activeJob.status),
    },
    renderNotice: previewNotice(canMountPlayer, activeJob),
  };
}

export async function pollRenderJobUntilSettled(input) {
  for (;;) {
    const job = await input.getRenderJob(input.projectId, input.jobId);
    input.onUpdate?.(job);
    if (isTerminalStatus(job.status)) {
      return job;
    }

    await input.wait();
  }
}

export async function triggerRenderJobAndPoll(input) {
  const createdJob = await input.createRenderJob(input.projectId, { kind: input.kind });
  input.onUpdate?.(createdJob);
  if (isTerminalStatus(createdJob.status)) {
    return createdJob;
  }

  return pollRenderJobUntilSettled({
    projectId: input.projectId,
    jobId: createdJob.id,
    getRenderJob: input.getRenderJob,
    wait: input.wait,
    onUpdate: input.onUpdate,
  });
}

function stageCount(
  key,
  counts
) {
  if (key === "voice") {
    return counts.voices;
  }
  if (key === "scenes") {
    return counts.scenes;
  }
  if (key === "translation") {
    return 0;
  }
  return counts.frames;
}

function previewNotice(
  canMountPlayer,
  activeJob
) {
  if (!canMountPlayer) {
    return {
      tone: "warning",
      message: "Build scenes before opening the preview.",
    };
  }

  if (activeJob === null) {
    return {
      tone: "info",
      message: "Preview is ready.",
    };
  }

  if (activeJob.status === "queued") {
    return {
      tone: "info",
      message: "Preview render is queued.",
    };
  }

  if (activeJob.status === "running") {
    return {
      tone: "info",
      message: "Preview render is running.",
    };
  }

  if (activeJob.status === "completed") {
    return {
      tone: "success",
      message: "Preview render completed.",
    };
  }

  return {
    tone: "warning",
    message: activeJob.errorMessage
      ? `Preview render failed. ${activeJob.errorMessage}`
      : "Preview render failed.",
  };
}

function isTerminalStatus(status) {
  return status === "completed" || status === "failed";
}
