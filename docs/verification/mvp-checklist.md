# MVP Release Readiness Checklist

Use [docs/setup/operator-runbook.md](../setup/operator-runbook.md) as the command reference for the operator path.

This checklist is the release-readiness gate for the current MVP before handoff.

## Readiness Checks

1. project creation: create a project with the CLI and confirm `workspace/<project-id>/` is created with `project.json`, `config.json`, and `script/*.json`.
2. import images into the project workspace and confirm the expected files appear under `images/`.
3. run OCR for imported frames and confirm `ocr/*.json` plus `script/frames.json` both contain bubble data.
4. review text and bubble classifications while keeping reviewed text separate from raw OCR text.
5. translate reviewed text and confirm `script/script.json` preserves separate source, translated, voice, and subtitle text layers.
6. create voice assets through TTS or documented local recovery steps, then confirm `script/voices.json` and `audio/` match.
7. build scenes from reviewed frames and voice outputs, then confirm `script/scenes.json` is render-ready.
8. preview the generated scene timeline through the API or web review surface and confirm scene/audio metadata is stable.
9. render a preview output and confirm the job reaches `completed` with a playable artifact under `renders/`.
10. trigger a final render and confirm the final render artifact exists under `workspace/<project-id>/renders/`.

## Release Readiness Checklist

- Run `python -m apps.cli.app.main doctor` and record any missing dependencies or provider checks.
- Run `python -m apps.cli.app.main run <project-id> --workspace-root workspace` and confirm it reports `Next stage: complete`.
- Run `python -m apps.cli.app.main integrity <project-id> --workspace-root workspace` and confirm it prints `Project integrity OK.`
- Verify the API is started with an absolute `MANGA_WORKSPACE_ROOT` before render-job testing.
- Verify `/projects/<project-id>`, `/projects/<project-id>/frames`, `/projects/<project-id>/scene-review`, and `/projects/<project-id>/render-jobs/<job-id>` all return the expected project data.
- Verify the operator followed the recovery notes for any OCR, translation, TTS, media generation, or render job failure instead of silently skipping a broken stage.
- Record the exact commands used, generated artifact paths, and any manual recovery steps in the handoff note.

Latest verified run record:

- `2026-03-15`: `docs/verification/mvp-real-run-2026-03-15.md`

Use the latest run record as a baseline example, not as a substitute for the current operator handoff verification.
