# MVP Real Run Record: 2026-03-15

This note records a fresh end-to-end MVP execution on `2026-03-15` using a new local project workspace.
It predates the MIT service migration in TIA-43 and remains a historical record of the pre-migration MVP path.

## Scope

- Repository root: `manga-media-remotion`
- Project id: `tia-36-mvp-demo`
- Source image: `tests/fixtures/workspace/demo-001/images/001.png`
- Base sync result before edits: `git fetch origin main` succeeded and `git rev-list --left-right --count origin/main...HEAD` returned `0 0`

## Environment

- Python: `/root/miniconda3/bin/python`
- Node: `/root/.nvm/versions/node/v24.12.0/bin/node`
- Render dependencies available: `opencv-python`, `numpy`, `Pillow`
- Browser/API verification ports used for this run:
  - API: `127.0.0.1:8010`
  - Web dev server: `127.0.0.1:4173`

## Helper Inputs Used During The Run

The current environment did not have real DeepL or Moyin credentials, so a local stub provider was started on `127.0.0.1:8765` to exercise the translation and TTS integration surfaces:

```bash
python - <<'PY'
import io
import json
import urllib.parse
import wave
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8765


def wav_bytes(duration_ms: int, sample_rate: int = 8000) -> bytes:
    frame_count = int(sample_rate * duration_ms / 1000)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * frame_count)
    return buffer.getvalue()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)

        if self.path == "/translate":
            payload = urllib.parse.parse_qs(body.decode("utf-8"))
            text = payload.get("text", [""])[0]
            target = payload.get("target_lang", ["ZH"])[0]
            response = json.dumps({"translations": [{"text": f"{target}:{text}"}]}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)
            return

        if self.path == "/tts":
            payload = json.loads(body.decode("utf-8"))
            preset = payload.get("voicePreset", "character-default")
            duration_ms = 420 if preset == "narrator-default" else 680
            response = wav_bytes(duration_ms)
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        print(format % args, flush=True)


server = HTTPServer(("127.0.0.1", PORT), Handler)
print(f"Stub provider listening on http://127.0.0.1:{PORT}", flush=True)
server.serve_forever()
PY
```

Review and script override payloads used during the run:

```json
[
  {
    "sourceBubbleId": "bubble-001",
    "textEdited": "サンプルです。",
    "order": 0,
    "kind": "dialogue",
    "speaker": "Hero"
  }
]
```

```json
[
  {
    "sourceBubbleId": "bubble-001",
    "voiceText": "这是配音稿。",
    "subtitleText": "这是字幕。"
  }
]
```

## Command Log

### 1. Create a project

```bash
python -m apps.cli.app.main new tia-36-mvp-demo --title "TIA-36 MVP Demo" --workspace-root workspace
```

Output:

```text
Created project tia-36-mvp-demo at /mydata/projects/symphony-workspaces/TIA-36/workspace/tia-36-mvp-demo
```

### 2. Import images

```bash
python -m apps.cli.app.main import-images tia-36-mvp-demo tests/fixtures/workspace/demo-001/images/001.png --workspace-root workspace
```

Output:

```text
Imported 1 images into /mydata/projects/symphony-workspaces/TIA-36/workspace/tia-36-mvp-demo
```

### 3. Check prerequisites

```bash
TRANSLATION_PROVIDER=deepl \
DEEPL_API_KEY=stub-token \
DEEPL_BASE_URL=http://127.0.0.1:8765/translate \
MOYIN_TTS_BASE_URL=http://127.0.0.1:8765/tts \
MOYIN_TTS_API_KEY=stub-token \
python -m apps.cli.app.main doctor
```

Output:

```text
OK python /root/miniconda3/bin/python
OK node /root/.nvm/versions/node/v24.12.0/bin/node
MISSING ffmpeg
OK render opencv-python numpy Pillow
MISSING OCR MangaOCR is not installed. Install the `manga-ocr` Python package before running OCR or `doctor`.
OK translation deepl
OK TTS moyin
Missing 2 required dependencies or provider checks.
```

### 4. Run OCR

```bash
python -m apps.cli.app.main ocr tia-36-mvp-demo --workspace-root workspace
```

Output:

```text
MangaOCR is not installed. Install the `manga-ocr` Python package before running OCR or `doctor`.
```

Manual unblock used for this run:

```bash
python - <<'PY'
import json
from pathlib import Path

project_dir = Path("workspace/tia-36-mvp-demo")
frames_path = project_dir / "script" / "frames.json"
ocr_path = Path("tests/fixtures/workspace/demo-001/ocr/001.json")

frames = json.loads(frames_path.read_text(encoding="utf-8"))
ocr_bubbles = json.loads(ocr_path.read_text(encoding="utf-8"))
frames[0]["bubbles"] = ocr_bubbles
frames[0]["reviewedBubbles"] = []
frames_path.write_text(json.dumps(frames, indent=2) + "\n", encoding="utf-8")
(project_dir / "ocr" / "001.json").write_text(json.dumps(ocr_bubbles, indent=2) + "\n", encoding="utf-8")
print("Injected", len(ocr_bubbles), "OCR bubbles into", frames_path)
PY
```

Output:

```text
Injected 1 OCR bubbles into workspace/tia-36-mvp-demo/script/frames.json
```

### 5. Review text and bubble classification

```bash
python -m apps.cli.app.main review tia-36-mvp-demo frame-001 --review-file /tmp/tia-36-review.json --workspace-root workspace
```

Output:

```text
Saved review for frame-001.
```

### 6. Translate and preserve separate text layers

```bash
TRANSLATION_PROVIDER=deepl \
DEEPL_API_KEY=stub-token \
DEEPL_BASE_URL=http://127.0.0.1:8765/translate \
python -m apps.cli.app.main translate tia-36-mvp-demo --target-language zh --overrides-file /tmp/tia-36-script-overrides.json --workspace-root workspace
```

Output:

```text
Generated 1 script entries.
```

Resulting text layers in `workspace/tia-36-mvp-demo/script/script.json`:

- `sourceText`: `サンプルです。`
- `translatedText`: `ZH:サンプルです。`
- `voiceText`: `这是配音稿。`
- `subtitleText`: `这是字幕。`

### 7. Create voice assets

```bash
MOYIN_TTS_BASE_URL=http://127.0.0.1:8765/tts \
MOYIN_TTS_API_KEY=stub-token \
python -m apps.cli.app.main voice tia-36-mvp-demo --workspace-root workspace
```

Output:

```text
Generated 1 voice segments.
```

### 8. Build scenes and verify CLI progress

```bash
python -m apps.cli.app.main build-scenes tia-36-mvp-demo --workspace-root workspace
python -m apps.cli.app.main open tia-36-mvp-demo --workspace-root workspace
python -m apps.cli.app.main run tia-36-mvp-demo --workspace-root workspace
```

Output:

```text
Built 1 scenes.
Opened project tia-36-mvp-demo (TIA-36 MVP Demo) at /mydata/projects/symphony-workspaces/TIA-36/workspace/tia-36-mvp-demo
Project tia-36-mvp-demo progress
[done] import-images
[done] ocr
[done] review
[done] translate
[done] voice
[done] build-scenes
Next stage: complete
```

### 9. Build and serve the review stack

Built web app:

```bash
MANGA_API_BASE_URL=http://127.0.0.1:8010 npm run build --workspace apps/web
```

Output:

```text
Built apps/web review app to apps/web/dist
```

Verified API and web dev server:

```bash
MANGA_WORKSPACE_ROOT="$(pwd)/workspace" uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8010
MANGA_API_BASE_URL=http://127.0.0.1:8010 npm run dev --workspace apps/web -- --host 127.0.0.1 --port 4173
curl -s http://127.0.0.1:8010/projects/tia-36-mvp-demo | python -m json.tool
curl -s http://127.0.0.1:8010/projects/tia-36-mvp-demo/frames | python -m json.tool
curl -s http://127.0.0.1:8010/projects/tia-36-mvp-demo/scenes | python -m json.tool
curl -s http://127.0.0.1:8010/projects/tia-36-mvp-demo/scene-review | python -m json.tool
curl -s http://127.0.0.1:4173/?projectId=tia-36-mvp-demo
```

Key results:

- API returned `counts.frames = 1`, `counts.voices = 1`, `counts.scenes = 1`
- Scene review returned `voiceId = "voice-script-bubble-001"` and `audioMetadata.durationMs = 680`
- Dev server returned HTML with `window.__MANGA_REVIEW_ENV__ = {"MANGA_API_BASE_URL":"http://127.0.0.1:8010", ...}`

### 10. Trigger preview and final renders

Preview render:

```bash
curl -s -X POST -H 'content-type: application/json' -d '{"kind":"preview"}' http://127.0.0.1:8010/projects/tia-36-mvp-demo/render-jobs | python -m json.tool
sleep 1
curl -s http://127.0.0.1:8010/projects/tia-36-mvp-demo/render-jobs/render-preview-002 | python -m json.tool
```

Final render:

```bash
curl -s -X POST -H 'content-type: application/json' -d '{"kind":"final"}' http://127.0.0.1:8010/projects/tia-36-mvp-demo/render-jobs | python -m json.tool
sleep 1
curl -s http://127.0.0.1:8010/projects/tia-36-mvp-demo/render-jobs/render-final-002 | python -m json.tool
```

Verified results:

- `render-preview-002` completed and wrote `/projects/tia-36-mvp-demo/media/renders/preview-render-preview-002.mp4`
- `render-final-002` completed and wrote `/projects/tia-36-mvp-demo/media/renders/final-render-final-002.mp4`
- File checks:
  - `preview-render-preview-002.mp4`: `28339` bytes, header `ftyp`
  - `final-render-final-002.mp4`: `65015` bytes, header `ftyp`

## Generated Files

Generated during the run:

- `workspace/tia-36-mvp-demo/config.json`
- `workspace/tia-36-mvp-demo/project.json`
- `workspace/tia-36-mvp-demo/images/001.png`
- `workspace/tia-36-mvp-demo/ocr/001.json`
- `workspace/tia-36-mvp-demo/script/frames.json`
- `workspace/tia-36-mvp-demo/script/script.json`
- `workspace/tia-36-mvp-demo/script/voices.json`
- `workspace/tia-36-mvp-demo/script/scenes.json`
- `workspace/tia-36-mvp-demo/audio/characters/script-bubble-001.wav`
- `workspace/tia-36-mvp-demo/renders/preview-render-preview-002.mp4`
- `workspace/tia-36-mvp-demo/renders/final-render-final-002.mp4`
- `workspace/tia-36-mvp-demo/renders/jobs.json`

## Remaining Gaps And Manual Steps

- OCR is still blocked unless `manga-ocr` is installed in the active Python environment. This run used fixture OCR output to continue the same project after the real `ocr` command failed.
- Real DeepL and Moyin credentials were not available in this environment. A local stub server was used to exercise the current translation and TTS integration points without changing application code.
- Starting the API with `MANGA_WORKSPACE_ROOT=workspace` caused render jobs `render-preview-001` and `render-final-001` to fail with `Missing project.json for render job.`. Using an absolute workspace root via `MANGA_WORKSPACE_ROOT="$(pwd)/workspace"` fixed the issue.
- `doctor` still reports `MISSING ffmpeg` even though preview and final render completed successfully in this environment. That mismatch should be treated as a setup/documentation gap until the repository decides whether `ffmpeg` is truly required for the current Remotion path.
- The browser-based review experience was verified at the server/HTML level. Interactive browser inspection of the running React app remains a manual check.
