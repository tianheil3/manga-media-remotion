# Manga Video Workflow Design

**Date:** 2026-03-14

**Status:** Approved

## Goal

Build a single-user workflow for manga commentary shorts that starts from manga images and produces a previewable Remotion video. The first version should provide a CLI-first production flow, a basic web review interface, and a stable render pipeline.

## Product Shape

The system is split into two user-facing layers and one render layer:

- `CLI production layer`: import manga images, run OCR, review text, translate, create voice assets, and generate structured project data.
- `Web review layer`: inspect OCR results, adjust reviewed text and scene metadata, preview the video, and trigger renders.
- `Remotion render layer`: read normalized scene data and produce previews and final outputs.

The product is not a full video editor in the first version. It is a guided production tool with light editing and stable rendering.

## User Goals

- Import existing manga images and preserve editable ordering.
- Recognize Japanese text using MangaOCR.
- Sort text using manga reading order: right to left, top to bottom.
- Allow review, correction, reordering, and type classification of OCR output.
- Support original Japanese text, Chinese translation, English translation, or mixed review flow.
- Generate voice assets using either TTS or user-recorded audio.
- Distinguish narrator voice from character dialogue voice.
- Handle textless panels as fixed-duration scenes.
- Produce a Remotion-ready timeline and provide basic web preview.

## Scope

### Included in MVP

- Python CLI for project initialization and guided processing.
- Manga image import.
- MangaOCR text extraction.
- OCR review and editable ordering.
- Translation stage with editable output.
- Voice generation workflow for narrator and character lines.
- TTS support and local recording support in CLI.
- Remotion preview and render pipeline.
- FastAPI backend and basic React web review UI.

### Deferred

- Full timeline editor.
- Browser-based recording.
- Multi-user collaboration.
- Database-first architecture.
- LLM-directed scene composition.
- Advanced effects such as lip sync, bubble tracking, or complex motion graphics.

## Recommended Architecture

### Primary Stack

- `Python`: CLI, FastAPI backend, OCR integration, audio tooling, project orchestration.
- `React`: web review interface.
- `Node.js + Remotion`: preview and final rendering.

### Rationale

Python is the best fit for MangaOCR, local recording workflows, and pipeline orchestration. Remotion should remain isolated in the JavaScript runtime where it is strongest. The bridge between them should be file-based project data, not ad hoc runtime coupling.

## System Modules

### `cli-app`

Responsibilities:

- Create and open projects.
- Import and reorder images.
- Run OCR.
- Guide user review and corrections.
- Trigger translation.
- Trigger TTS or capture local audio recordings.
- Generate normalized project files and scene timelines.

### `api-server`

Responsibilities:

- Serve project metadata and project files through HTTP APIs.
- Support lightweight editing from the web UI.
- Trigger Remotion preview and render jobs.
- Expose job status and file locations.

### `web-review`

Responsibilities:

- Show project status.
- Review OCR results by frame.
- Review and adjust scene text, audio, and durations.
- Preview the generated Remotion composition.

### `remotion-renderer`

Responsibilities:

- Consume normalized `scenes.json`.
- Render preview and export outputs.
- Keep rendering concerns isolated from OCR, translation, and audio generation logic.

## Project Data Model

The workflow must preserve multiple layers of text because OCR source text, translated text, voice text, and subtitle text are not the same thing.

### OCR Layer

```ts
type OcrBubble = {
  id: string;
  text: string;
  bbox: {x: number; y: number; w: number; h: number};
  order: number;
  confidence: number;
  language: "ja" | "zh" | "en";
};
```

### Reviewed Layer

```ts
type ReviewedBubble = {
  id: string;
  sourceBubbleId: string;
  textOriginal: string;
  textEdited: string;
  order: number;
  kind: "dialogue" | "narration" | "sfx" | "ignore";
  speaker?: string;
};
```

### Voice Layer

```ts
type VoiceSegment = {
  id: string;
  frameId: string;
  text: string;
  mode: "tts" | "record" | "skip";
  role: "narrator" | "character";
  speaker?: string;
  voicePreset?: string;
  audioFile?: string;
  transcript?: string;
  durationMs?: number;
};
```

### Render Layer

```ts
type Scene = {
  id: string;
  type: "narration" | "dialogue" | "silent";
  image: string;
  subtitleText?: string;
  audio?: string;
  durationMs: number;
  speaker?: string;
  stylePreset: "default" | "fast" | "dramatic" | "calm";
  cameraMotion?: "none" | "pan" | "zoom-in" | "zoom-out";
  transition?: "cut" | "fade" | "slide";
};
```

## Project Layout

```text
project-root/
  apps/
    cli/
    api/
    web/
    remotion/
  packages/
    schema/
    shared/
  workspace/
    <project-id>/
      project.json
      config.json
      images/
      ocr/
      script/
      audio/
      renders/
      cache/
```

Single project layout:

```text
workspace/demo-001/
  project.json
  config.json
  images/
    001.png
    002.png
  ocr/
    001.json
    002.json
  script/
    frames.json
    scenes.json
    voices.json
  audio/
    narration/
    characters/
    recorded/
  renders/
    preview.mp4
  cache/
```

## CLI Workflow

The CLI should be guided by a primary command such as `manga-video run`, with subcommands available to rerun individual stages.

### Entry Commands

- `manga-video new`
- `manga-video open <project-id>`
- `manga-video doctor`
- `manga-video run`

### Guided Stages

1. Import images.
2. Run OCR.
3. Review OCR output.
4. Translate and normalize script text.
5. Choose voice generation mode.
6. Generate TTS or capture recordings.
7. Build scene timeline.
8. Launch web preview.

### CLI Interaction Rules

- Every stage can be skipped.
- Every skipped stage remains editable later.
- Project progress is derived from files on disk, not session memory.
- `run` is the guided default, but stages like `ocr`, `review`, and `voice` can be rerun independently.

### Recording Interaction

For the MVP, stable recording is more important than perfect push-to-talk. The first version should allow start/stop recording with the space key or equivalent toggled control. A true hold-to-record mode can be added later if terminal handling proves reliable enough.

## OCR and Review Rules

- MangaOCR processes imported images.
- Initial bubble ordering follows manga reading order: right to left, then top to bottom.
- Users can correct text, reorder bubbles, relabel bubble type, assign speakers, or ignore entries.
- OCR review must remain editable even when users choose to skip quickly.

## Translation and Script Normalization

The system must keep separate values for:

- OCR source text
- reviewed text
- translated text
- voice script text
- subtitle text

Translation output should be editable before voice generation. Voice text should prioritize natural spoken pacing over literal OCR fidelity.

## Voice Strategy

Recommended default:

- Narration uses one stable narrator voice.
- Character dialogue uses a separate voice family.
- Textless panels become silent scenes with fixed default duration.

Supported voice modes:

- `tts`
- `record`
- `skip`

The system should support TTS integration with Moyin and local recording with automatic transcription for review.

## Web MVP

The web UI should focus on review and preview, not complex editing.

### Pages

- Project overview
- Frame review
- Scene and audio review
- Video preview

### Capabilities

- Inspect OCR output and reviewed text.
- Modify text and metadata.
- Inspect generated audio and durations.
- Preview the Remotion composition.
- Trigger preview and final render jobs.

## Remotion Design

Remotion should render a small, stable set of scene types:

- `narration`
- `dialogue`
- `silent`

The timeline should be driven primarily by audio duration. Silent scenes use default durations until manually adjusted.

The first version should include:

- Manga image display
- basic camera motion
- subtitle overlays
- simple transitions

It should avoid advanced animation features in the MVP.

## Delivery Strategy

### Phase 1

Complete the end-to-end path from manga images to preview video using OCR, manual review, TTS, Remotion rendering, and minimal web preview.

### Phase 2

Add translation workflow, local recording mode, scene editing, and audio replacement.

### Phase 3

Add rule-based style presets, scene heuristics, and improved timing logic.

### Phase 4

Expand the web UI into a stronger editing surface.

## Constraints and Notes

- The current directory is not a git repository, so this design cannot be committed yet.
- The brainstorming skill normally expects a worktree and a commit; that is blocked by the current repository state.
- The design assumes local-first project storage for simplicity and recoverability.
