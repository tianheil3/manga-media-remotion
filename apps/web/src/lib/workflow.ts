import type { ProjectDetail, RenderJob } from "@manga/schema";

const WORKFLOW_STAGES = [
  { key: "images", label: "Images", actionLabel: "Import images" },
  { key: "ocr", label: "OCR", actionLabel: "Run OCR" },
  { key: "review", label: "Review", actionLabel: "Review text" },
  { key: "translation", label: "Translation", actionLabel: "Run translation" },
  { key: "voice", label: "Voice", actionLabel: "Generate voice" },
  { key: "scenes", label: "Scenes", actionLabel: "Build scenes" },
] as const;

type WorkflowStageKey = (typeof WORKFLOW_STAGES)[number]["key"];

export function buildProjectWorkflowSummary(project: ProjectDetail) {
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

export function buildPreviewState(input: {
  counts: Pick<ProjectDetail["counts"], "scenes" | "voices" | "frames">;
  activeJob?: RenderJob | null;
}) {
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

export async function pollRenderJobUntilSettled(input: {
  projectId: string;
  jobId: string;
  getRenderJob: (projectId: string, jobId: string) => Promise<RenderJob>;
  wait: () => Promise<void>;
  onUpdate?: (job: RenderJob) => void;
}) {
  for (;;) {
    const job = await input.getRenderJob(input.projectId, input.jobId);
    input.onUpdate?.(job);
    if (isTerminalStatus(job.status)) {
      return job;
    }

    await input.wait();
  }
}

export async function triggerRenderJobAndPoll(input: {
  projectId: string;
  kind: RenderJob["kind"];
  createRenderJob: (
    projectId: string,
    payload: { kind: RenderJob["kind"] }
  ) => Promise<RenderJob>;
  getRenderJob: (projectId: string, jobId: string) => Promise<RenderJob>;
  wait: () => Promise<void>;
  onUpdate?: (job: RenderJob) => void;
}) {
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
  key: WorkflowStageKey,
  counts: Pick<ProjectDetail["counts"], "frames" | "voices" | "scenes">
): number {
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
  canMountPlayer: boolean,
  activeJob: RenderJob | null
): { tone: "info" | "success" | "warning"; message: string } {
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

function isTerminalStatus(status: RenderJob["status"]): boolean {
  return status === "completed" || status === "failed";
}
