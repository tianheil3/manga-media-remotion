import test from "node:test";
import assert from "node:assert/strict";

import { createApiClient } from "../src/lib/api.ts";


test("lists projects through the web api client", async () => {
  const calls: Array<{ url: string; init?: RequestInit }> = [];
  const client = createApiClient({
    baseUrl: "http://localhost:8000",
    fetchImpl: async (url, init) => {
      calls.push({ url: String(url), init });
      return new Response(
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
      );
    },
  });

  const projects = await client.listProjects();

  assert.equal(calls[0]?.url, "http://localhost:8000/projects");
  assert.equal(projects[0]?.progress.review, true);
});


test("updates frame review and triggers preview renders through the web api client", async () => {
  const calls: Array<{ url: string; init?: RequestInit }> = [];
  const responses = [
    new Response(
      JSON.stringify({
        frameId: "frame-001",
        image: "images/001.png",
        ocrFile: "ocr/001.json",
        bubbles: [],
        reviewedBubbles: [
          {
            id: "review-bubble-a",
            sourceBubbleId: "bubble-a",
            textOriginal: "raw",
            textEdited: "edited",
            order: 0,
            kind: "dialogue",
            speaker: "Hero",
          },
        ],
      }),
      { status: 200, headers: { "content-type": "application/json" } }
    ),
    new Response(
      JSON.stringify({
        id: "render-preview-001",
        projectId: "demo-001",
        kind: "preview",
        status: "queued",
        outputFile: "renders/preview-render-preview-001.mp4",
        createdAt: "2026-03-14T00:00:00.000Z",
        updatedAt: "2026-03-14T00:00:00.000Z",
        statusPath: "/projects/demo-001/render-jobs/render-preview-001",
      }),
      { status: 200, headers: { "content-type": "application/json" } }
    ),
  ];

  const client = createApiClient({
    fetchImpl: async (url, init) => {
      calls.push({ url: String(url), init });
      return responses.shift() as Response;
    },
  });

  const frame = await client.updateFrameReview("demo-001", "frame-001", {
    reviewedBubbles: [
      {
        sourceBubbleId: "bubble-a",
        textEdited: "edited",
        order: 0,
        kind: "dialogue",
        speaker: "Hero",
      },
    ],
    skip: false,
  });
  const renderJob = await client.createRenderJob("demo-001", { kind: "preview" });

  assert.equal(calls[0]?.url, "/projects/demo-001/frames/frame-001/review");
  assert.equal(calls[0]?.init?.method, "PUT");
  assert.match(String(calls[0]?.init?.body), /"textEdited":"edited"/);
  assert.equal(frame.reviewedBubbles[0]?.speaker, "Hero");
  assert.equal(calls[1]?.url, "/projects/demo-001/render-jobs");
  assert.equal(calls[1]?.init?.method, "POST");
  assert.equal(renderJob.status, "queued");
});


test("updates frame review through the web api client when the saved speaker is cleared", async () => {
  const calls: Array<{ url: string; init?: RequestInit }> = [];
  const client = createApiClient({
    fetchImpl: async (url, init) => {
      calls.push({ url: String(url), init });
      return new Response(
        JSON.stringify({
          frameId: "frame-001",
          image: "images/001.png",
          ocrFile: "ocr/001.json",
          bubbles: [],
          reviewedBubbles: [
            {
              id: "review-bubble-a",
              sourceBubbleId: "bubble-a",
              textOriginal: "raw",
              textEdited: "edited",
              order: 0,
              kind: "dialogue",
              speaker: null,
            },
          ],
        }),
        { status: 200, headers: { "content-type": "application/json" } }
      );
    },
  });

  const frame = await client.updateFrameReview("demo-001", "frame-001", {
    reviewedBubbles: [
      {
        sourceBubbleId: "bubble-a",
        textEdited: "edited",
        order: 0,
        kind: "dialogue",
      },
    ],
    skip: false,
  });

  assert.equal(calls[0]?.url, "/projects/demo-001/frames/frame-001/review");
  assert.equal(frame.reviewedBubbles[0]?.speaker, null);
});


test("loads preview scenes through the web api client", async () => {
  const calls: Array<{ url: string; init?: RequestInit }> = [];
  const client = createApiClient({
    baseUrl: "http://localhost:8000",
    fetchImpl: async (url, init) => {
      calls.push({ url: String(url), init });
      return new Response(
        JSON.stringify([
          {
            id: "scene-001",
            type: "dialogue",
            image: "images/001.png",
            subtitleText: "subtitle",
            audio: "audio/001.wav",
            durationMs: 1000,
            stylePreset: "default",
            transition: "cut",
          },
        ]),
        {
          status: 200,
          headers: { "content-type": "application/json" },
        }
      );
    },
  });

  const scenes = await client.getScenes("demo-001");

  assert.equal(calls[0]?.url, "http://localhost:8000/projects/demo-001/scenes");
  assert.equal(scenes[0]?.subtitleText, "subtitle");
});


test("loads frames with cleared reviewed speakers through the web api client", async () => {
  const client = createApiClient({
    fetchImpl: async () =>
      new Response(
        JSON.stringify([
          {
            frameId: "frame-001",
            image: "images/001.png",
            ocrFile: "ocr/001.json",
            bubbles: [],
            reviewedBubbles: [
              {
                id: "review-bubble-a",
                sourceBubbleId: "bubble-a",
                textOriginal: "raw",
                textEdited: "edited",
                order: 0,
                kind: "dialogue",
                speaker: null,
              },
            ],
          },
        ]),
        {
          status: 200,
          headers: { "content-type": "application/json" },
        }
      ),
  });

  const frames = await client.getFrames("demo-001");

  assert.equal(frames[0]?.reviewedBubbles[0]?.speaker, null);
});


test("loads scene payloads with null optional fields through the web api client", async () => {
  const client = createApiClient({
    fetchImpl: async () =>
      new Response(
        JSON.stringify([
          {
            id: "scene-001",
            type: "dialogue",
            image: "images/001.png",
            subtitleText: "subtitle",
            voiceId: "voice-001",
            audio: null,
            durationMs: 1000,
            speaker: null,
            stylePreset: "default",
            cameraMotion: null,
            transition: null,
          },
        ]),
        {
          status: 200,
          headers: { "content-type": "application/json" },
        }
      ),
  });

  const scenes = await client.getScenes("demo-001");

  assert.equal(scenes[0]?.audio, null);
  assert.equal((scenes[0] as { voiceId?: string | null } | undefined)?.voiceId, "voice-001");
  assert.equal(scenes[0]?.speaker, null);
  assert.equal(scenes[0]?.cameraMotion, null);
  assert.equal(scenes[0]?.transition, null);
});


test("updates scenes through the web api client when the saved subtitle is cleared", async () => {
  const calls: Array<{ url: string; init?: RequestInit }> = [];
  const client = createApiClient({
    fetchImpl: async (url, init) => {
      calls.push({ url: String(url), init });
      return new Response(
        JSON.stringify({
          id: "scene-001",
          type: "dialogue",
          image: "images/001.png",
          subtitleText: null,
          audio: null,
          durationMs: 1000,
          speaker: null,
          stylePreset: "default",
          audioMetadata: null,
          cameraMotion: null,
          transition: null,
        }),
        {
          status: 200,
          headers: { "content-type": "application/json" },
        }
      );
    },
  });

  const scene = await client.updateScene("demo-001", "scene-001", {
    subtitleText: null,
    durationMs: 1000,
    stylePreset: "default",
  });

  assert.equal(calls[0]?.url, "/projects/demo-001/scenes/scene-001");
  assert.equal(calls[0]?.init?.method, "PUT");
  assert.match(String(calls[0]?.init?.body), /"subtitleText":null/);
  assert.equal(scene.subtitleText, null);
  assert.equal(scene.audio, null);
  assert.equal(scene.speaker, null);
  assert.equal(scene.cameraMotion, null);
  assert.equal(scene.transition, null);
});


test("loads scene review payloads when audio metadata contains null optional fields", async () => {
  const client = createApiClient({
    fetchImpl: async () =>
      new Response(
        JSON.stringify([
          {
            id: "scene-001",
            type: "dialogue",
            image: "images/001.png",
            subtitleText: "subtitle",
            audio: null,
            durationMs: 1000,
            speaker: null,
            stylePreset: "default",
            cameraMotion: null,
            transition: null,
            audioMetadata: {
              id: "voice-001",
              frameId: "frame-001",
              mode: "skip",
              role: "character",
              speaker: null,
              audioFile: null,
              durationMs: null,
              replaceAudioPath: "/projects/demo-001/voices/voice-001/audio",
              skipRecordingPath: "/projects/demo-001/voices/voice-001/skip",
            },
          },
        ]),
        {
          status: 200,
          headers: { "content-type": "application/json" },
        }
      ),
  });

  const scenes = await client.getSceneReview("demo-001");

  assert.equal(scenes[0]?.audioMetadata?.speaker, null);
  assert.equal(scenes[0]?.audioMetadata?.audioFile, null);
  assert.equal(scenes[0]?.audioMetadata?.durationMs, null);
});


test("updates scenes through the web api client when audio metadata contains null optional fields", async () => {
  const client = createApiClient({
    fetchImpl: async () =>
      new Response(
        JSON.stringify({
          id: "scene-001",
          type: "dialogue",
          image: "images/001.png",
          subtitleText: "subtitle",
          audio: null,
          durationMs: 1000,
          speaker: null,
          stylePreset: "default",
          cameraMotion: null,
          transition: null,
          audioMetadata: {
            id: "voice-001",
            frameId: "frame-001",
            mode: "skip",
            role: "character",
            speaker: null,
            audioFile: null,
            durationMs: null,
            replaceAudioPath: "/projects/demo-001/voices/voice-001/audio",
            skipRecordingPath: "/projects/demo-001/voices/voice-001/skip",
          },
        }),
        {
          status: 200,
          headers: { "content-type": "application/json" },
        }
      ),
  });

  const scene = await client.updateScene("demo-001", "scene-001", {
    subtitleText: "subtitle",
    durationMs: 1000,
    stylePreset: "default",
  });

  assert.equal(scene.audioMetadata?.speaker, null);
  assert.equal(scene.audioMetadata?.audioFile, null);
  assert.equal(scene.audioMetadata?.durationMs, null);
});
