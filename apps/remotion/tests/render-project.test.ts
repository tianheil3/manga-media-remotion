import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { runCli } from "../src/cli.ts";
import { renderProject } from "../src/render-project.ts";

function createProjectFixture() {
  const projectDir = mkdtempSync(join(tmpdir(), "manga-remotion-render-"));
  mkdirSync(join(projectDir, "script"), { recursive: true });
  writeFileSync(
    join(projectDir, "project.json"),
    JSON.stringify(
      {
        id: "demo-001",
        title: "Project demo-001",
        sourceLanguage: "ja",
        imageDir: "images",
        createdAt: "2026-03-15T00:00:00.000Z",
        updatedAt: "2026-03-15T00:00:00.000Z",
      },
      null,
      2
    ) + "\n",
    "utf8"
  );
  writeFileSync(
    join(projectDir, "script", "scenes.json"),
    JSON.stringify(
      [
        {
          id: "scene-001",
          type: "narration",
          image: "images/001.png",
          subtitleText: "Opening line",
          durationMs: 1000,
          stylePreset: "default",
        },
      ],
      null,
      2
    ) + "\n",
    "utf8"
  );

  return projectDir;
}

test("renderProject writes a deterministic render artifact from project scene data", async () => {
  const projectDir = createProjectFixture();

  const result = await renderProject({
    projectDir,
    kind: "preview",
    outputFile: "renders/preview-render-preview-001.mp4",
  });

  assert.equal(
    result.outputPath,
    join(projectDir, "renders", "preview-render-preview-001.mp4")
  );

  const artifact = JSON.parse(readFileSync(result.outputPath, "utf8"));
  assert.equal(artifact.artifactType, "manga-remotion-render-v1");
  assert.equal(artifact.kind, "preview");
  assert.equal(artifact.project.id, "demo-001");
  assert.equal(artifact.sceneCount, 1);
  assert.equal(artifact.composition.durationInFrames, 30);
  assert.match(artifact.markup, /data-scene-type="narration"/);
});

test("runCli prints renderer help without requiring render arguments", async () => {
  const stdout: string[] = [];
  const stderr: string[] = [];

  const exitCode = await runCli(["--help"], {
    stdout: (chunk) => stdout.push(chunk),
    stderr: (chunk) => stderr.push(chunk),
  });

  assert.equal(exitCode, 0);
  assert.equal(stderr.join(""), "");
  assert.match(stdout.join(""), /Usage:/);
  assert.match(stdout.join(""), /--project-dir/);
  assert.match(stdout.join(""), /--kind/);
  assert.match(stdout.join(""), /--output-file/);
});
