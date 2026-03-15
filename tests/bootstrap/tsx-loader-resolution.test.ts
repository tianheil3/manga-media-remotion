import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, readFile, writeFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { createApiClient } from "../../apps/web/src/lib/api.ts";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "..", "..");

test("tsx loader resolves repo-local web test dependencies", async () => {
  const client = createApiClient({
    fetchImpl: async () =>
      new Response(
        JSON.stringify([
          {
            id: "demo-001",
            title: "Demo Project",
            progress: {
              images: true,
              ocr: true,
              review: true,
              translation: false,
              voice: false,
              scenes: false,
            },
          },
        ]),
        {
          status: 200,
          headers: { "content-type": "application/json" },
        }
      ),
  });

  const projects = await client.listProjects();
  const markup = renderToStaticMarkup(
    React.createElement("section", { "data-resolution": "ok" }, "resolved")
  );

  assert.equal(projects[0]?.id, "demo-001");
  assert.match(markup, /data-resolution="ok"/);
  assert.match(markup, /resolved/);
});

test("tsx loader prefers real packages when they are available", async () => {
  const tempDir = await mkdtemp(path.join(os.tmpdir(), "tsx-loader-resolution-"));
  const reactDir = path.join(tempDir, "node_modules", "react");
  const resultFile = path.join(tempDir, "result.txt");
  await mkdir(reactDir, { recursive: true });
  await writeFile(
    path.join(reactDir, "package.json"),
    JSON.stringify({
      name: "react",
      type: "module",
      exports: "./index.js",
    }),
    "utf8"
  );
  await writeFile(
    path.join(reactDir, "index.js"),
    'export default { realMarker: "real-react" }; export const createElement = () => "real";\n',
    "utf8"
  );

  const result = spawnSync(
    "bash",
    [
      "-lc",
      'cd "$TEMP_DIR" && node --import "$REPO_ROOT/tools/register-tsx.mjs" --input-type=module -e \'import { writeFileSync } from "node:fs"; import React from "react"; writeFileSync(process.env.RESULT_FILE, React.realMarker ?? "shim-react");\'',
    ],
    {
      encoding: "utf8",
      env: {
        ...process.env,
        REPO_ROOT: repoRoot,
        RESULT_FILE: resultFile,
        TEMP_DIR: tempDir,
      },
    }
  );

  assert.equal(result.status, 0, result.stderr);
  assert.equal(await readFile(resultFile, "utf8"), "real-react");
});
