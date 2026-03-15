import React from "react";
import { spawn } from "node:child_process";
import { mkdir, readFile, stat } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { renderToStaticMarkup } from "react-dom/server";

import { projectSchema, sceneSchema, type Project, type Scene } from "@manga/schema";

import { Root } from "./Root.tsx";
import { buildCompositionSpec } from "./composition-spec.ts";

export const DEFAULT_RENDER_FPS = 30;
export const DEFAULT_PROJECT_FILE = "project.json";
export const DEFAULT_SCENES_FILE = "script/scenes.json";

export type RenderKind = "preview" | "final";

export type RenderProjectInput = {
  projectDir: string;
  kind: RenderKind;
  outputFile: string;
  fps?: number;
  projectFile?: string;
  scenesFile?: string;
  generatedAt?: string;
};

export type RenderArtifact = {
  artifactType: "manga-remotion-render-v1";
  generatedAt: string;
  kind: RenderKind;
  project: {
    id: string;
    title: string;
  };
  fps: number;
  sceneCount: number;
  composition: ReturnType<typeof buildCompositionSpec>;
  markup: string;
};

export type RenderProjectResult = {
  outputPath: string;
  artifact: RenderArtifact;
};

type VideoRenderPayload = {
  fps: number;
  kind: RenderKind;
  outputPath: string;
  project: Project;
  projectDir: string;
  scenes: Scene[];
};

export async function renderProject(
  input: RenderProjectInput
): Promise<RenderProjectResult> {
  const fps = input.fps ?? DEFAULT_RENDER_FPS;
  const loaded = await loadRenderInput(input);
  const artifact = buildRenderArtifact({
    project: loaded.project,
    scenes: loaded.scenes,
    kind: input.kind,
    fps,
    generatedAt: input.generatedAt,
  });
  const outputPath = join(input.projectDir, input.outputFile);

  await mkdir(dirname(outputPath), { recursive: true });
  await renderVideo({
    fps,
    kind: input.kind,
    outputPath,
    project: loaded.project,
    projectDir: input.projectDir,
    scenes: loaded.scenes,
  });

  const outputStats = await stat(outputPath);
  if (outputStats.size === 0) {
    throw new Error("Render output is empty.");
  }

  return {
    outputPath,
    artifact,
  };
}

export async function loadRenderInput(input: RenderProjectInput): Promise<{
  project: Project;
  scenes: Scene[];
}> {
  const projectFile = input.projectFile ?? DEFAULT_PROJECT_FILE;
  const scenesFile = input.scenesFile ?? DEFAULT_SCENES_FILE;
  const projectPath = join(input.projectDir, projectFile);
  const scenesPath = join(input.projectDir, scenesFile);

  const project = projectSchema.parse(
    await readJsonFile(projectPath, "Missing project.json for render job.")
  );
  const scenes = sceneSchema
    .array()
    .parse(await readJsonFile(scenesPath, "Missing script/scenes.json for render job."));

  if (scenes.length === 0) {
    throw new Error("No scenes available for render.");
  }

  return {
    project,
    scenes,
  };
}

export function buildRenderArtifact(options: {
  project: Project;
  scenes: Scene[];
  kind: RenderKind;
  fps: number;
  generatedAt?: string;
}): RenderArtifact {
  const composition = buildCompositionSpec(options.scenes, { fps: options.fps });
  const markup = renderToStaticMarkup(
    React.createElement(Root, {
      fps: options.fps,
      scenes: options.scenes,
    })
  );

  return {
    artifactType: "manga-remotion-render-v1",
    generatedAt: options.generatedAt ?? new Date().toISOString(),
    kind: options.kind,
    project: {
      id: options.project.id,
      title: options.project.title,
    },
    fps: options.fps,
    sceneCount: options.scenes.length,
    composition,
    markup,
  };
}

async function renderVideo(payload: VideoRenderPayload): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    const stderrChunks: string[] = [];
    const stdoutChunks: string[] = [];
    const child = spawn(process.env.PYTHON ?? "python", [RENDER_VIDEO_SCRIPT], {
      stdio: ["pipe", "pipe", "pipe"],
    });

    child.stdout.on("data", (chunk) => {
      stdoutChunks.push(String(chunk));
    });
    child.stderr.on("data", (chunk) => {
      stderrChunks.push(String(chunk));
    });
    child.on("error", (error) => {
      reject(new Error(`Failed to start video renderer: ${error.message}`));
    });
    child.on("close", (code) => {
      if (code === 0) {
        resolve();
        return;
      }

      reject(new Error(extractRendererError(stderrChunks.join(""), stdoutChunks.join(""))));
    });

    child.stdin.end(JSON.stringify(payload));
  });
}

async function readJsonFile(path: string, missingMessage: string): Promise<unknown> {
  try {
    return JSON.parse(await readFile(path, "utf8"));
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      throw new Error(missingMessage);
    }

    throw error;
  }
}

function extractRendererError(stderr: string, stdout: string): string {
  for (const line of [...stderr.split(/\r?\n/), ...stdout.split(/\r?\n/)].reverse()) {
    const trimmed = line.trim();
    if (trimmed) {
      return trimmed;
    }
  }

  return "Renderer command failed.";
}

const RENDER_VIDEO_SCRIPT = fileURLToPath(new URL("../scripts/render_video.py", import.meta.url));
