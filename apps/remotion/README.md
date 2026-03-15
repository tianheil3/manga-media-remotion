# @manga/remotion

`apps/remotion` is the renderer boundary for the manga video workflow. The package owns scene-data validation, composition building, and the runnable CLI used by the API render-job layer.

## Runtime Scripts

- `npm run render --workspace apps/remotion -- --help`
- `npm run render:preview --workspace apps/remotion -- --project-dir <dir> --output-file <path>`
- `npm run render:final --workspace apps/remotion -- --project-dir <dir> --output-file <path>`

## API Invocation Contract

The API render-job layer should invoke the package through this CLI:

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

## Stable Failure Messages

The API layer should treat these renderer failures as stable:

- `Missing project.json for render job.`
- `Missing script/scenes.json for render job.`
- `No scenes available for render.`
- `Render output is empty.`

## Output Shape

The current runtime writes a deterministic JSON render artifact to the requested output path. The artifact includes:

- render kind
- project identity
- scene count
- composition metadata
- rendered markup from `Root`

This keeps the renderer package runnable today while preserving a stable contract for a future Remotion media-export implementation.
