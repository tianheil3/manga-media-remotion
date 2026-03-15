import { parseArgs } from "node:util";

import {
  DEFAULT_PROJECT_FILE,
  DEFAULT_RENDER_FPS,
  DEFAULT_SCENES_FILE,
  renderProject,
  type RenderKind,
} from "./render-project.ts";

type CliIo = {
  stdout: (chunk: string) => void;
  stderr: (chunk: string) => void;
};

const HELP_TEXT = `Usage:
  npm run render --workspace apps/remotion -- \\
    --project-dir <workspace/project-id> \\
    --kind <preview|final> \\
    --output-file <relative-output-path> \\
    [--fps <number>] \\
    [--project-file <relative-project-file>] \\
    [--scenes-file <relative-scenes-file>]

Options:
  --project-dir   Project directory containing project.json and script/scenes.json
  --kind          Render kind: preview or final
  --output-file   Output file path relative to the project directory
  --fps           Frames per second. Defaults to ${DEFAULT_RENDER_FPS}
  --project-file  Relative project metadata path. Defaults to ${DEFAULT_PROJECT_FILE}
  --scenes-file   Relative scene data path. Defaults to ${DEFAULT_SCENES_FILE}
  --help          Print this help output
`;

export async function runCli(
  argv: string[],
  io: CliIo = {
    stdout: (chunk) => process.stdout.write(chunk),
    stderr: (chunk) => process.stderr.write(chunk),
  }
): Promise<number> {
  try {
    const { values, positionals } = parseArgs({
      args: argv,
      allowPositionals: true,
      options: {
        "project-dir": {
          type: "string",
        },
        kind: {
          type: "string",
        },
        "output-file": {
          type: "string",
        },
        fps: {
          type: "string",
        },
        "project-file": {
          type: "string",
        },
        "scenes-file": {
          type: "string",
        },
        help: {
          type: "boolean",
        },
      },
    });

    if (positionals.length > 0) {
      io.stderr(`Unexpected positional arguments: ${positionals.join(" ")}\n`);
      io.stderr(HELP_TEXT);
      return 1;
    }

    if (values.help) {
      io.stdout(HELP_TEXT);
      return 0;
    }

    const projectDir = values["project-dir"];
    const outputFile = values["output-file"];
    const kind = parseKind(values.kind);
    const fps = parseFps(values.fps);

    if (!projectDir) {
      io.stderr("Missing required flag: --project-dir\n");
      return 1;
    }

    if (!kind) {
      io.stderr("Missing or invalid flag: --kind must be preview or final\n");
      return 1;
    }

    if (!outputFile) {
      io.stderr("Missing required flag: --output-file\n");
      return 1;
    }

    if (fps === null) {
      io.stderr("--fps must be a positive integer\n");
      return 1;
    }

    const result = await renderProject({
      projectDir,
      kind,
      outputFile,
      fps,
      projectFile: values["project-file"],
      scenesFile: values["scenes-file"],
    });

    io.stdout(`${result.outputPath}\n`);
    return 0;
  } catch (error) {
    io.stderr(`${toErrorMessage(error)}\n`);
    return 1;
  }
}

function parseKind(value: string | undefined): RenderKind | null {
  if (value === "preview" || value === "final") {
    return value;
  }

  return null;
}

function parseFps(value: string | undefined): number | null {
  if (value === undefined) {
    return DEFAULT_RENDER_FPS;
  }

  const fps = Number(value);
  if (!Number.isInteger(fps) || fps <= 0) {
    return null;
  }

  return fps;
}

function toErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return String(error);
}

const invokedAsScript = process.argv[1] && import.meta.url === new URL(process.argv[1], "file:").href;

if (invokedAsScript) {
  const exitCode = await runCli(process.argv.slice(2));
  process.exitCode = exitCode;
}
