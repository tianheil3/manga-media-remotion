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

test("renderProject writes a real MP4 while returning render metadata", async () => {
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

  const outputBytes = readFileSync(result.outputPath);
  assert.equal(outputBytes.toString("ascii", 4, 8), "ftyp");

  assert.equal(result.artifact.artifactType, "manga-remotion-render-v1");
  assert.equal(result.artifact.kind, "preview");
  assert.equal(result.artifact.project.id, "demo-001");
  assert.equal(result.artifact.sceneCount, 1);
  assert.equal(result.artifact.composition.durationInFrames, 30);
  assert.match(result.artifact.markup, /data-scene-type="narration"/);
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
