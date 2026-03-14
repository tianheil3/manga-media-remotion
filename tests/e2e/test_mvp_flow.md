# Manual MVP Flow

## Prerequisites

- Python dependencies for the CLI and API are installed.
- `manga-ocr` is installed if OCR will be exercised.
- `MOYIN_TTS_BASE_URL` and `MOYIN_TTS_API_KEY` are configured if real TTS will be exercised.
- Frontend and Remotion dependencies are available if preview or render stages will be exercised.

## Manual Steps

1. Create a workspace project with the CLI.
2. Import one or more manga images.
3. Run OCR and inspect the generated `ocr/` outputs.
4. Review or edit the extracted text.
5. Translate script text and generate or record voice assets.
6. Build `script/scenes.json`.
7. Start any available preview stack.
8. Trigger a render and confirm output artifacts land under `renders/`.

## Notes

If any prerequisite is unavailable in the current environment, document the blocker in the verification log and treat the run as a documented skip rather than a silent failure.
