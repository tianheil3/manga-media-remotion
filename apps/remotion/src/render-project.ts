import React from "react";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
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

export async function renderProject(
  input: RenderProjectInput
): Promise<RenderProjectResult> {
  const loaded = await loadRenderInput(input);
  const artifact = buildRenderArtifact({
    project: loaded.project,
    scenes: loaded.scenes,
    kind: input.kind,
    fps: input.fps ?? DEFAULT_RENDER_FPS,
    generatedAt: input.generatedAt,
  });
  const outputPath = join(input.projectDir, input.outputFile);
  const payload = JSON.stringify(artifact, null, 2) + "\n";

  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, payload, "utf8");

  if (payload.trim().length === 0) {
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
