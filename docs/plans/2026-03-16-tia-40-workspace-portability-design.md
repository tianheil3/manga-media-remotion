# TIA-40 Workspace Portability Design

**Date:** 2026-03-16

**Status:** Derived from the approved workflow design and ticket acceptance criteria

## Goal

Add a minimal, documented way to move a single `workspace/<project-id>/` project between machines without losing the files needed to resume review and rendering.

## Constraints

- Keep the project state file-backed under `workspace/<project-id>/`.
- Preserve the existing separation between OCR, reviewed text, translation/script, voice, and scene data.
- Avoid introducing database state or renderer-owned workflow logic.
- Keep the first implementation small and deterministic.

## Options Considered

### 1. Export and import the whole project directory as a portable archive

- Pros: smallest implementation, preserves all current project state, matches the existing on-disk model, works across machines because the stored paths are already relative.
- Cons: archive can include non-essential files such as cache artifacts.

### 2. Export only a curated subset of required files

- Pros: smaller archives and clearer contract.
- Cons: more logic, more risk of accidentally dropping a file needed by future review or render flows, and more likely to drift from the real workspace shape.

### 3. Add a custom manifest plus selective rebuild on import

- Pros: flexible long term.
- Cons: overbuilt for this ticket, duplicates the existing project state model, and adds restore complexity.

## Recommended Approach

Use option 1 for the initial implementation.

Export a single project workspace as a `.tar.gz` archive rooted at `<project-id>/`. Import should validate the archive structure, reject unsafe paths, require a `project.json` at the extracted project root, and fail if the destination project already exists.

This keeps the implementation aligned with the current local-first design: a portable archive is just a transport wrapper around the existing project directory.

## CLI Surface

- `python -m apps.cli.app.main export-workspace <project-id> <archive-path> --workspace-root <dir>`
- `python -m apps.cli.app.main import-workspace <archive-path> --workspace-root <dir>`

The import command should print the imported project id and destination path so users can immediately resume with `open`, `run`, API startup, or rendering commands.

## Portability Scope

The export should preserve the entire project directory, including:

- `project.json`
- `config.json`
- `images/`
- `ocr/`
- `script/`
- `audio/`
- `renders/`
- `cache/`

Preserving the full directory avoids accidental loss of resume-critical data and keeps the archive contract stable as the workspace evolves.

## Validation

- Add CLI coverage for export and import.
- Verify the imported project still passes the progress view and integrity checks.
- Update local-development docs so the flow is discoverable.
