# Project Integrity Checks And Recovery Design

**Date:** 2026-03-16

**Status:** Approved for implementation in unattended ticket flow

## Goal

Help operators detect and recover from inconsistent project state under `workspace/<project-id>` without adding a database or pushing orchestration logic into Remotion.

## Problem

The current project model is file-backed, but several CLI and API call sites either:

- assume the expected JSON files exist, or
- silently treat missing files as empty state

That makes a damaged workspace look like a valid but incomplete project. It also means stale scene and voice links can survive until a later stage fails in a less actionable way.

## Constraints

- Keep the project state local-first under `workspace/<project-id>`.
- Keep OCR text, translated text, voice text, and subtitle text as separate layers.
- Keep the first implementation minimal and aligned with the existing MVP design.
- Preserve compatibility with legacy scene review payloads that may omit `voiceId`.

## Options Considered

### Option 1: Dedicated integrity service plus explicit CLI commands

Add a shared Python integrity service that inspects project files, referenced media, and scene-to-voice consistency. Expose it through a CLI check command and a CLI repair command. Reuse a narrower version of the same checks in existing CLI/API paths that currently hide missing files.

Pros:

- One source of truth for integrity logic.
- Solves both operator detection and common repair.
- Lets existing routes choose only the strictness they need.

Cons:

- Requires touching several callers to stop swallowing missing files.

### Option 2: Make `FileStore` auto-heal on read

Change the file store to create missing files or repair broken references while loading.

Pros:

- Fewer call-site changes.

Cons:

- Hides corruption instead of surfacing it.
- Mixes reads with writes.
- Does not naturally cover media/reference checks.

### Option 3: Add a project-specific doctor command only

Keep the existing workflow unchanged and add one more diagnostic CLI entrypoint.

Pros:

- Smallest code change.

Cons:

- Existing commands and routes would still silently degrade.
- Does not satisfy the need for recovery well enough.

## Decision

Use Option 1.

Add a shared integrity service, expose explicit CLI `integrity` and `repair` commands, and wire a strict subset of the checks into the existing CLI/API paths that currently hide inconsistent state.

## Integrity Model

The integrity service should classify issues into three operator-facing groups:

1. Missing project files
2. Missing media files referenced by project state
3. Broken scene or voice references

### Missing project files

The full integrity command should check for:

- `project.json`
- `config.json`
- `script/frames.json`
- `script/voices.json`
- `script/scenes.json`

`script/script.json` remains optional because it is stage-dependent.

### Missing media

The full integrity command should verify that referenced files exist for:

- `Frame.image`
- `Frame.ocr_file`
- `VoiceSegment.audio_file` when present
- `Scene.image`
- `Scene.audio` when present

### Broken scene or voice references

The integrity logic should flag:

- non-silent scenes that cannot be resolved to any voice
- scenes with a stored `voiceId` that does not exist
- scene audio values that disagree with the resolved voice audio
- scenes with missing audio even though the resolved voice has audio
- scenes with stale audio even though the resolved voice is skipped

Legacy scenes without `voiceId` are still valid if the current scene-sync rules can resolve them by audio or order.

## Repair Scope

The repair command should stay minimal and only fix common inconsistencies that are deterministic:

- recreate `config.json` from `project.json` when missing
- recreate missing `script/frames.json`, `script/voices.json`, and `script/scenes.json`
- if scenes and voices exist, resync scenes against current voices to restore `voiceId`, `audio`, `speaker`, and duration values when possible

The repair command should not fabricate missing media or reconstruct a missing `project.json`.

## Error Surfacing

The implementation should stop silently treating missing required files as empty state in selected places:

- CLI `run`
- API project detail/progress reads
- API frame review reads
- API scene reads
- API voice scene-review reads and scene updates

Those call sites should raise actionable integrity errors that point operators to the repair command.

The full media check remains explicit through the new CLI integrity command so existing lightweight API reads do not start failing just because tests omit fixture media files.

## Testing

Add tests for:

- full integrity detection of missing files, missing media, and broken scene/voice references
- CLI repair behavior for missing files and stale scene links
- CLI/API actionable errors where missing files were previously treated as empty state

Required ticket validation remains:

- `python -m pytest apps/cli/tests apps/api/tests -v`
