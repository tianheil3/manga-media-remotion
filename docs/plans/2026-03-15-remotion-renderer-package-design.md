# Remotion Renderer Package Design

**Date:** 2026-03-15

**Status:** Approved from ticket scope and existing workflow design

## Goal

Turn `apps/remotion` from a test-only scene component package into a runnable renderer boundary that the product workflow can invoke through a stable CLI contract.

## Scope

- Add a stable renderer entrypoint inside `apps/remotion`.
- Add runtime scripts for preview and final render modes.
- Keep render concerns inside the renderer package and keep workflow orchestration in Python.
- Document the CLI contract the API render-job layer should call.

## Recommended Approach

### Option 1: Direct Python-owned artifact generation

Keep the Python API layer generating output files itself and only reuse small helpers from `apps/remotion`.

Trade-off:
- Minimal code movement.
- Fails the ticket goal because `apps/remotion` still is not the runnable renderer boundary.

### Option 2: Package-owned renderer entrypoint

Add a TypeScript renderer entrypoint in `apps/remotion` that reads normalized project data, validates it, builds the composition spec, renders deterministic markup, and writes the render artifact to the requested output path. The API render-job layer shells into this package through a documented CLI.

Trade-off:
- Slightly more plumbing.
- Gives the product workflow a stable renderer contract now and keeps future media-render work isolated in one package.

### Option 3: Full Remotion media export now

Pull in full Remotion runtime dependencies and switch immediately to video export.

Trade-off:
- Best long-term direction.
- Not practical in the current repository state because the package does not yet depend on Remotion runtime tooling and the ticket scope only requires a runnable renderer package and contract.

## Decision

Use Option 2.

`apps/remotion` will own:

- project/scenes loading and validation
- composition building
- renderer artifact generation
- CLI argument parsing and help output

The API layer will own:

- render job creation and persistence
- subprocess orchestration
- job status and error propagation

## Renderer Contract

The stable CLI contract is:

```bash
npm run render --workspace apps/remotion -- \
  --project-dir <workspace/project-id> \
  --kind <preview|final> \
  --output-file <relative-output-path> \
  [--fps <number>] \
  [--project-file <relative-project-file>] \
  [--scenes-file <relative-scenes-file>]
```

Defaults:

- `--fps 30`
- `--project-file project.json`
- `--scenes-file script/scenes.json`

Failure messages should stay stable for the API layer:

- `Missing project.json for render job.`
- `Missing script/scenes.json for render job.`
- `No scenes available for render.`
- `Render output is empty.`

## Data Flow

1. The API layer creates a render job and chooses the output file path.
2. The API layer invokes the renderer CLI with `project.json`, `scenes.json`, render `kind`, and output path.
3. The renderer validates input data through shared schema helpers.
4. The renderer builds composition metadata and deterministic markup from `Root`.
5. The renderer writes the artifact to the requested output path.
6. The API layer persists success or failure on the job record.

## Testing

- Add renderer entrypoint tests in `apps/remotion`.
- Keep the existing remotion component/composition tests green.
- Update render job tests so they assert the API layer now receives package-owned render artifacts instead of API-generated placeholder files.
